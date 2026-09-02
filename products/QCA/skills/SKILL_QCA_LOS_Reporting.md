# SKILL: QCA — LOS, Ad-Hoc Reporting & JEA Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Cost Accounting (QCA) — upstream oil-&-gas joint-interest accounting in the myQuorum / On Demand Upstream suite
**Scope:** The QCA reporting & allocation back-end — **Lease Operating Statement (LOS)** (the `LOSDD_IMP` → `LOSLOAD` import/load pipeline that builds the LOS tables, and the LOS002/LOS003/QP086 reports off them), **Ad-Hoc Reporting** (QQM universes, AFE/JIB/check-register reports, AP/AR check forms, workflow-inbox notifications), and **Journal Entry Allocations (JEA)** (the JE Subledger → GL export: `JEGLEXPORT`, `COREIMPJE`, GL025/GL095).
**Sibling modules (fix upstream first):** the LOS *number* is sourced from **QRA** (revenue/production) and **QCFS** (financials/trial balance) and joint-interest splits from **QCFS JIB**. When the LOS or a report shows the *wrong amount* (not a crash), the data is almost always correct-but-duplicated/missing upstream in QRA/QCFS/JIB — fix that, then re-run `LOSDD_IMP`+`LOSLOAD`. This skill covers the QCA-side import, load, report, and JE-export layer.

> **Evidence base:** 377 closed QCA cases in categories LOS (131) + Ad-Hoc Reporting (220) + JEA (26). Root-cause split: (blank) 108, **Customer Error 103**, Customer Cancelled 52, **Software Defect 46**, Training 44, **Application Configuration 29**, Performance 19, Platform 17, others. This skill mines the **76 actionable** cases (Software Defect 46 + Application Configuration 29 + ChangeConfig 1) for fix recipes (38 had a usable subject/resolution), plus ~60 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — LOSDD_IMP / LOSLOAD batch failures (HIGHEST FREQUENCY)](#4-cluster-a--losdd_imp--losload-batch-failures)
5. [Cluster B — LOS report shows $0 / wrong / duplicated values](#5-cluster-b--los-report-shows-0--wrong--duplicated-values)
6. [Cluster C — LOS scheduled jobs not running](#6-cluster-c--los-scheduled-jobs-not-running)
7. [Cluster D — JEA → GL export not journalizing (JEGLEXPORT / COREIMPJE)](#7-cluster-d--jea--gl-export-not-journalizing)
8. [Cluster E — AFE / JIB / check-register report accuracy & access](#8-cluster-e--afe--jib--check-register-report-accuracy--access)
9. [Cluster F — Workflow inbox / approval / notification defects](#9-cluster-f--workflow-inbox--approval--notification-defects)
10. [Known ADO Items](#10-known-ado-items)
11. [Diagnostic SQL](#11-diagnostic-sql)
12. [Expected-Behavior / User-Education FAQ](#12-expected-behavior--user-education-faq)
13. [Key Code, Processes & Repos](#13-key-code-processes--repos)
14. [Escalation Guidance](#14-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| `LOSDD_IMP` fails in a **registered SQL** (`Sel_PRDN_VOL`, `Sel_Intfc_Trans…`, `m_sel_prdn_vol failed`) | Underlying **view defect** (column not resolving, bad join) introduced by a patch/upgrade | PQID + the **exact registered-SQL name** in the error; **§4** (view fix, usually a patch) |
| `LOSDD_IMP` gets an **ODBC error** on a scheduled run | Custom **ODBC SQL driver whitelist** left over from an old build, blocking the driver | §4 — run `05_RemoveCustom_OBDC_SQL_DRIVER_WHITELIST.sql` (25-01053798) |
| `LOSLOAD` **Stopped Processing on Error (SPE)** / generic error since a patch | **Qpec command timeout** — FULL refresh updating tens of millions of rows exceeds default timeout | §4 — raise `Command Timeout` in `QPEC.ini` (24-00977217), then re-run FULL |
| LOS report shows **$0** for revenue/production, or pulls **no recent months** | (a) data-fix not applied with the code-fix on a patch; (b) the LOS process isn't scheduled/never ran | §5 / §6 — was the data fix applied? Did `LOSDD_IMP`+`LOSLOAD` complete? |
| LOS report **duplicated** (2x–6x revenue/volume for a month) | **Duplicate rows upstream** (QRA/QCFS/JIB intercompany) pulled into LOS tables | §5 — dedup upstream, then re-run LOSDD_IMP/LOSLOAD; verify in QTRAN_LOS_* |
| LOS report **values wrong after V16→V17 upgrade** | Client **custom object/view override** differs from the new core view | §5 — compare custom vs core view; adopt core or update the custom (24-00990633) |
| `LOSDD_IMP` / `LOSLOAD` **scheduled job not running** (no error, just stale data) | Schedule **disabled** (cutover sets all jobs disabled) or schedule definition wrong | §6 — re-enable / fix the schedule definition (24-00941672, 23-00929627) |
| `QTRAN_LOS_CUSTOM_SL` (or other LOS table) **blank/empty** | The custom-SL load step never ran — jobs disabled post-migration, or upstream blank | §6 / §4 (24-00941672, 23-00916360) |
| JE Allocation batches **post in QCA but never reach the GL** (`JEGLEXPORT` "succeeds" but **no GL095 batch**) | Export query's **IN clause contains a NULL** (PropNo/ToProspectNo/OriginalProspectNo) → records skipped | §7 — code fix to filter NULLs (25-01022443 / ADO #1732583) |
| `COREIMPJE` **times out** moving records to JEA | C# builds a giant **`IN` clause** for a large leaseholder list | §7 — code fix (22-00664869 / ADO #1374842); interim: purge `SEXTN_CORE_INTFC_JE` |
| AFE01 / AFE report **overhead doubled / inaccurate** | Config — JIB capital overheads flowing to AFE *and* being charged | §8 — turn off JIB capital overheads to AFE (25-01025890) |
| QQM "JIB Subject Area" / universe **missing** for a user | QQM **universe security** not granted | §8 — grant the QJIB universe security in PRD (24-00941372) |
| Check Register / AP061 check run **print/number error** | Check **form** not deployed / SSRS permission / starting check numbers not set | §8 — deploy check form + SSRS perms; set AP & revenue starting check numbers |
| AFE inbox **wrong route preview** / WF_QUEUE email **hyperlink cut off** / invoice **stuck in no-one's inbox** | Workflow/notification **defect** | §9 — patch/hotfix; stuck items cleared by script |

---

## 2. Pipeline & Concepts

```
QRA (revenue/production)  +  QCFS (financials / trial-balance / JIB splits)
      │
      ▼  STRAN_CORE_INTFC  (core interface staging)
   LOSDD_IMP   ── import/distribute ──►  QTRAN_LOS_RAW_DATA
      │                                  QTRAN_LOS_FINANCIAL_SL
      ▼                                  QTRAN_LOS_PRDN_SL
   LOSLOAD     ── load/aggregate ─────►  QTRAN_LOS_CUSTOM_SL   ──►  LOS002 / LOS003 / QP086 reports
                                                                    (Gross LOS, Net LOS)

JE Allocations:  JB200 Allocation Group → post → QTRAN_JE_SUBLEDGER
      │ COREIMPJE  (move core JE records into the JEA module)
      ▼ JEGLEXPORT (stage billable JE entries → SSTAG_CORE_INTFC → QCFS GL095 batch → JIB billing)
```

### Key terms (QCA / upstream-accounting vocabulary)
- **LOS** = Lease Operating Statement — the per-lease/property revenue-&-expense report. **Gross LOS** (operator's 100% view) vs **Net LOS** (the operator's working-interest net) are produced by different views and break independently (Gross & Net are separate cases in 25-01003756 / 24-00990633).
- **`LOSDD_IMP`** = "LOS Data Distribution Import" — the batch that moves `STRAN_CORE_INTFC` data into the `QTRAN_LOS_*` tables via a chain of **registered SQL** statements (e.g. `Sel_PRDN_VOL`, `Sel_Intfc_Trans…`). A failing registered SQL = a bad underlying **view** (most common LOS defect).
- **`LOSLOAD`** = the load/aggregate step that populates `QTRAN_LOS_CUSTOM_SL` (the report source). Runs as a parent/child process (`QPSQcaLOSLoadChild`); a **FULL** refresh re-loads from "beginning of time" and can take *days* on large clients.
- **`QTRAN_LOS_*` tables** = `QTRAN_LOS_RAW_DATA`, `QTRAN_LOS_FINANCIAL_SL`, `QTRAN_LOS_PRDN_SL`, `QTRAN_LOS_CUSTOM_SL`. If a report is blank/wrong, check which of these is empty/duplicated — it tells you which step failed. `_CUSTOM_SL` empty = `LOSLOAD` didn't finish; `_RAW`/`_FINANCIAL`/`_PRDN` empty = `LOSDD_IMP` didn't finish.
- **AFE** = Authorization For Expenditure (capital project). **JIB** = Joint Interest Billing. **Capital overhead** = an overhead load JIB applies; if it's *also* pushed to the AFE you double-count (25-01025890).
- **JEA** = Journal Entry Allocations — the QCA sub-ledger that splits/allocates JE amounts by working interest and exports them to the GL. **JB200** = Allocation Group setup screen; **GL025** = JE upload; **GL095** = GL batch (the JIB-billable result).
- **`QTRAN_JE_SUBLEDGER`** = the JEA subledger table; its key fields **PropNo / ToProspectNo / OriginalProspectNo** must be non-NULL or the GL export silently skips them (25-01022443).
- **`JEGLEXPORT`** = process that stages billable JE entries into **`SSTAG_CORE_INTFC`** → QCFS GL batch. **`COREIMPJE`** = process that imports core JE records into the JEA module (stages into `SEXTN_CORE_INTFC_JE`).
- **QQM** = Quorum Query Manager — the ad-hoc reporting / universe layer (e.g. the **QJIB** universe / "JIB Subject Area"). Missing data on a QQM report is usually **universe security**, not a defect.
- **Qpec / QPEC.ini** = the batch execution engine config; `Command Timeout` there bounds how long a single SQL statement may run (the LOSLOAD-FULL timeout lever, 24-00977217).
- **Registered SQL** = named SQL fragments a process runs; the error message names the failing one (e.g. `Sel_PRDN_VOL`) — that's your pointer to the broken view/proc.

---

## 3. Decision Tree

```
QCA LOS / Reporting / JEA case
│
├─ A batch failed? (LOSDD_IMP / LOSLOAD / JEGLEXPORT / COREIMPJE)  → GET PQID + EXACT STEP/REGISTERED-SQL NAME + ERROR
│   ├─ LOSDD_IMP fails in a registered SQL (Sel_PRDN_VOL / Sel_Intfc_Trans / m_sel_prdn_vol)  → §4 (view defect → patch)
│   ├─ LOSDD_IMP "ODBC error"                                                                  → §4 (remove custom ODBC driver whitelist)
│   ├─ LOSLOAD SPE / timeout on FULL refresh (huge row counts)                                 → §4 (raise QPEC.ini Command Timeout)
│   ├─ JEGLEXPORT "succeeds" but no GL095 batch                                                → §7 (NULL in IN-clause; code fix)
│   └─ COREIMPJE times out                                                                     → §7 (IN-clause build; code fix; purge SEXTN_CORE_INTFC_JE)
│
├─ Report output wrong (process didn't crash)?
│   ├─ $0 / no recent months                          → §5 (data fix missing, or LOSDD_IMP+LOSLOAD never completed → §6)
│   ├─ Duplicated 2x–6x                                → §5 (dedup UPSTREAM in QRA/QCFS/JIB intercompany, then re-run)
│   ├─ Wrong after V16→V17 upgrade                     → §5 (custom view vs core view drift)
│   ├─ AFE overhead doubled / report inaccurate        → §8 (config: JIB capital overhead → AFE)
│   └─ QQM universe / subject area missing for a user  → §8 (universe security)
│
├─ LOS data stale / table blank but no error?         → §6 (scheduled job disabled or schedule definition wrong; cutover disables all jobs)
│
├─ Check run / AP / AR / check-register print or number issue?  → §8 (deploy check form + SSRS perms; set starting check numbers)
│
├─ AFE inbox wrong route / WF email hyperlink / invoice/voucher stuck or won't approve?  → §9 (workflow defect → patch; stuck items → script)
│
└─ "How do I…", audit, "why no data", JIB-close warning, allocation-group save once, locks  → §12 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — LOSDD_IMP / LOSLOAD batch failures

**The single largest actionable LOS signature.** The LOS build is a two-stage batch (`LOSDD_IMP` then `LOSLOAD`); both fail in recognizable ways, and *most* failures trace to an underlying **view/registered-SQL defect** that ships fixed in a patch, or to an **environment/timeout** lever.

### A1 — `LOSDD_IMP` fails in a registered SQL (view defect) — the recurring defect
**Symptom (verbatim):** `LOSDD_IMP pqid: 10184112 has failed with error in registered sql Sel_PRDN_VOL` (25-01040307); `m_sel_prdn_vol failed` (22-00544985); `2025.04: LOSDD_IMP erroring … registered SQL name is 'Sel_Intfc_Trans…'` (ADO #1721401).
**Root cause:** an underlying **view** behind the named registered SQL is broken — a column not resolving (e.g. `UPDT_DT` column "not working", 22-00544985) or a bad join after an upgrade. Found first while testing **Gross LOS**, then the same break hits **Net LOS** (25-01040307).
**Fix:** the view is corrected and shipped on a **patch** (25-01040307 → Patch 8; 22-00544985 "fixed a view"). The C++ extract lives in `Quorum.Upstream.QCA.ClassicBatch/QPDllCostAcctgLOS/QSQL_QcaLOSExtract.cpp`; the registered SQL/views are in `<CLIENT>.Upstream.QCA.Database` and the metadata `QARCH_SQL.json`. **Recipe:** get the **exact registered-SQL name** from the error, confirm whether it's Gross or Net path, check the named view in the client DB repo, and confirm the target patch/build contains the fix.

### A2 — `LOSDD_IMP` ODBC error
**Symptom:** scheduled `LOSDD_IMP` gets an **ODBC error** (25-01053798, critical, blocking upgrade testing).
**Root cause:** a leftover **custom ODBC SQL driver whitelist** restricting the allowed driver.
**Fix:** run **`05_RemoveCustom_OBDC_SQL_DRIVER_WHITELIST.sql`** (the exact resolution script on 25-01053798) to drop the custom whitelist so the standard driver is used.

### A3 — `LOSLOAD` Stopped-Processing-on-Error / timeout on FULL refresh
**Symptom:** `LOSLOAD` run as a **FULL refresh** ends in SPE with a generic message; SQL trace shows one statement updating **~25 million rows** across three large updates (24-00977217).
**Root cause:** the build doesn't support that data volume in the default time → a **Qpec command timeout**.
**Fix (immediate):** raise **`Command Timeout` in `QPEC.ini`** (set to ~5 hours on 24-00977217), then re-run `LOSLOAD` FULL — it completes. **Long-term:** later versions optimize this; recommend the upgrade. Note a FULL `LOSLOAD` re-loads from "beginning of time" and legitimately runs **hours to days** (the 25-01003756 reload ran ~2 days) — long ≠ broken.

**Fix recipe (Cluster A):**
1. Get **PQID + exact step / registered-SQL name + error text** (double-click the failing batch-message row).
2. Registered-SQL name in the error (`Sel_PRDN_VOL`, `Sel_Intfc_Trans…`) → **view defect**, confirm Gross vs Net, check the patch (A1).
3. "ODBC error" → run the **driver-whitelist removal script** (A2).
4. SPE/timeout on a FULL refresh of a large client → **raise `QPEC.ini` Command Timeout**, re-run FULL (A3).
5. After any LOSDD_IMP fix, **`LOSDD_IMP` must complete before `LOSLOAD`** — re-run in order; a half-completed/cancelled prior run is itself a common cause (24-00946713).

---

## 5. Cluster B — LOS report shows $0 / wrong / duplicated values

The report didn't crash; the numbers are wrong. The pattern is almost always **upstream data + a missing data-fix or a custom-view drift**, not a report-rendering bug.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Gross Accounting LOS shows **$0** for total revenue & production (Dec-23→present) | A core bug corrupted QRA data; client took the **software fix but not the paired data fix** | Apply the **data fix in QRA**, then re-run `LOSDD_IMP` (~2h) + `LOSLOAD` FULL (~2 days, expected) | 25-01003756 |
| LOS report **not populating amounts** after V16→V17 upgrade | Client used a **custom object/view override** for the QRA production portion; the custom view differs from the new **core** v17 view | Compare custom vs core view; either update the custom view or adopt core | 24-00990633 |
| **Net LOS** duplicating QCFS trial-balance amounts for certain months | **Duplicated rows** upstream pulled into the LOS tables | Remove the duplicate data (data scripts), re-run; same dedup applied across V16 and V17 | 24-00990633, 25-01003756 |
| LOS data **duplicated ~5x** for Nov/Dec (recurring, prior 22-00668079) | Duplicate revenue rows in the LOS table; resolving fully needed code + client metadata + registered-SQL changes (deemed **out of scope** for the client's build) | Dedup data; full fix OOS without code/metadata work | 23-00884375 |
| Custom LOS changes needed | Client-specific LOS customization | Delivered via **ADO 102203** | 22-00655389 |

**Key insight:** when LOS shows **$0 / missing**, the data-fix half of a patch usually wasn't applied (25-01003756) — software fix alone is not enough. When LOS is **duplicated (2x–6x)**, the duplication is **upstream** (QRA revenue rows, QCFS trial-balance, or **intercompany on Gross** — 25-01051608); dedup there and re-run `LOSDD_IMP`+`LOSLOAD`. When LOS is **wrong only after a V16→V17 upgrade**, suspect a **custom view vs core view** drift (24-00990633). Verify which `QTRAN_LOS_*` table is empty/duplicated to localize the failing stage (see §2 and §11).

---

## 6. Cluster C — LOS scheduled jobs not running

LOS data goes stale with **no error** — the import/load simply isn't firing on schedule. This is **Application Configuration**, not a defect.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| 2 LOS processes not running on the nightly schedule | Schedule **definition** wrong | **Updated the schedule definition** | 23-00929627 |
| `QTRAN_LOS_CUSTOM_SL` blank in QCloud; `LOSLOAD` "doesn't seem to be working" | **During cutover, all scheduled jobs are set to 'disabled'** | Run the **post-migration script to enable all jobs**; review the job list with the client | 24-00941672, 25-01046718 |
| `QTRAN_LOS_CUSTOM_SL` empty in LIV environment | Same family — load step not running in that environment | Re-enable / re-run the LOS load in that env | 23-00916360 |
| V17-upgrade LOS not pulling recent months | LOS **process not scheduled to run**; once enabled it ran but then hit the §4 view defect | Enable the process; the subsequent failure was the LOSDD_IMP view bug (→ 25-01040307, Patch 8) | 25-01038970 |

**Fix recipe:** if LOS is stale with no batch error, check the **schedule** first. After any **cutover/migration/DB refresh**, *all* scheduled jobs default to **disabled** (24-00941672) — run the post-migration enable script and walk the job list with the client. If a table like `QTRAN_LOS_CUSTOM_SL` is blank, confirm the corresponding step is both **scheduled and enabled** before assuming a load defect.

---

## 7. Cluster D — JEA → GL export not journalizing

The JEA module posts in QCA but the entries **never reach the GL** for JIB billing. Two distinct, confirmed **code defects**.

### D1 — `JEGLEXPORT` "succeeds" but no GL095 batch (NULL in IN-clause) — the headline JEA defect
**Symptom (25-01022443, MEW):** `JEGLEXPORT` completes successfully, but **no batches are created in GL095**; expected behaviour is billable JE entries get staged into `SSTAG_CORE_INTFC` and interfaced into QCFS as GL batches. Reproducible in QPRD, not QTST.
**Root cause:** the export builds an **`IN` clause from three `QTRAN_JE_SUBLEDGER` columns — `PropNo`, `ToProspectNo`, `OriginalProspectNo`** — and requires **no NULLs**; when at least one value is NULL the records are **not selected**, so the inserts into `SSTAG_CORE_INTFC` silently never happen and the process still "completes."
**Fix:** code change to the **Export method of `JESubledgerExsport.cs`** to **filter out NULLs** that participate in the IN clause. Validated; packaged for the next hotfix. → **ADO #1732583 / #1735315** (both Closed).

### D2 — `COREIMPJE` times out importing core JE records
**Symptom:** `COREIMPJE` (moves core JE records into the JEA module) **times out every run** (22-00664869, MEW).
**Root cause:** the C# builds a giant **`IN` clause from a large leaseholder list** (same anti-pattern family as D1).
**Fix:** code fix → **ADO #1374842 / #1414114** ("COREIMPJE — Timeout Due to Building 'IN' Clause with Large List (Leaseholder)", Closed). **Interim unblock observed:** the **`SEXTN_CORE_INTFC_JE` extension table was purged** (22-00664869 resolution) so the stuck staging set is cleared before re-run.

### D3 — JEA setup / upload config
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Required fields in **GL025** halting JE upload | Required-field config on the JE upload screen | Confirmed correct setup ("correct") | 25-01008582 |
| Errors during **Allocation Group (JB200)** setup — `FORCE_PROCESS_RERUN` business-rule exception on save | **Timing/state-specific** condition at save; not reproducible after recreate | Recreated the allocation group successfully; no persistent defect | 25-01059858 |
| JB200 Allocation Group import (JBIMPAGH) fails; rows stuck in `JBSTG_ALLOC_GRP`, not in `JBONL_ALLOC_GRP` (so not on JB200 screen) | **Import XLSX had invalid properties** → process failed mid-stage | Correct the import file (Customer Error) | 26-01092387 |

**Fix recipe (Cluster D):** for "JE posts in QCA but nothing in the GL," check `JEGLEXPORT` first — pull `QTRAN_JE_SUBLEDGER` for the batch and look for **NULL `PROP_NO` / `TO_PROSPECT_NO` / `ORIGINAL_PROSPECT_NO`** (D1, the IN-clause NULL trap); confirm the build has the `JESubledgerExsport.cs` NULL-filter fix (#1732583). For `COREIMPJE` timeouts, it's the large-IN-clause defect (#1374842) — interim, purge `SEXTN_CORE_INTFC_JE` and re-run. JB200 save errors are usually **not** persistent defects (25-01059858) or are a **bad import file** (26-01092387).

---

## 8. Cluster E — AFE / JIB / check-register report accuracy & access

The "Ad-Hoc Reporting" actionable cases are dominated by **report config / security / form deployment** — rarely engine defects.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **AFE01** report inaccurate — overhead being **doubled** | JIB **capital overheads** flowing to the AFE in addition to being charged | **Turn off** JIB capital overheads from going to AFE (config) | 25-01025890 |
| **QQM "JIB Subject Area" (QJIB universe) missing** for a user | QQM **universe security** not granted in PRD | QQM provides the required user security for the **QJIB universe**; user re-tests | 24-00941372 |
| AFE reports **access** for a named user | User not in the reports security group | Add user to the **AFE REPORTS** group | 23-00913941 |
| **AP061 Check Run Creation** print error | Check **form** not deployed to PRD + SSRS permissions | **Deploy the check form to PRD and adjust SSRS permissions** | 23-00907242 |
| **Check Register** report issues | Starting check numbers not configured | **Add AP and revenue starting check numbers** | 23-00907337 |
| **JB350** JIB error message | The **registered SQL** behind JB350 wasn't joining properly | **Edit the registered SQL** to pull correct results / fix the tiers | 22-00660632 |
| `JIB Run — Well Volume Completion Load` error | Could not be replicated | Awaiting client PRD access (no fix without repro) | 22-00685691 |
| Load `FMOG_Budget_Plan` (budget table) | One-off data load | **Ran script to load** the quarter's budget | 22-00819861 |

**Fix recipe:** AFE/report **inaccuracy** → check the **overhead / capital-overhead-to-AFE** config first (25-01025890). **Missing report data or "subject area missing"** in QQM → **universe security** (24-00941372) or a **reports security group** (23-00913941), not a defect. **Check-run print/number** issues → **deploy the SSRS check form + permissions** and **set starting check numbers** (23-00907242, 23-00907337). A JIB report returning wrong/no rows can be a **registered-SQL join** bug fixable in client metadata (22-00660632).

---

## 9. Cluster F — Workflow inbox / approval / notification defects

A scattered but real set of **Software Defects** in the AFE/invoice **workflow & notification** layer that surface as "report/inbox" cases. Most are fixed in a hotfix; the immediate unblock for stuck items is a **status-reset script**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **AFE Inbox shows wrong Route Preview** | Route-preview defect | Provided the **Jan-2022 Patch for 2020.03** (#21-00215794) | 22-00669760 |
| **WF_QUEUE notification email** inbox **hyperlink cut off** when comments exist | Email-link truncation defect | Fixed in **UPS 2020.09.41 Hotfix** (user opted for next GA) | 22-00830683 |
| **Invoice stuck in no-one's inbox** | Workflow-routing defect | **Script** to reroute (run after UAT refresh); long-term replicate | 22-00819224 |
| **Error on invoice approval** / **Approval Error** (stuck vouchers & AFEs) | Batch/voucher in a bad status | **Script** to set batches/vouchers to **Draft** and reprocess; remove stuck inbox items | 22-00547184, 22-00523372 |
| **Reclass voucher attachment** issue | Attachment-handling defect | (resolution not captured — pattern unclear from mined cases) | 22-00547148 |
| **Rebill with prepay** involved | Rebill/prepay calculation defect | Fix in the **December hotfix for 2020.09** | 22-00831167 |
| MEW upgrade: **missing QCA batch processes** in myQuorum | Upgrade packaging gap | (resolution not captured; treat as upgrade-packaging follow-up) | 22-00659964 |
| Nightly schedule **didn't run during an environment outage** | Jobs missed while env down | **Script to reprocess** the failed/missed jobs | 22-00654690 |

**Fix recipe:** AFE/invoice **workflow** defects (wrong route preview, stuck inbox, approval errors) are mostly **hotfix-delivered**; the **immediate unblock** is a **script to reset voucher/AFE/batch status to Draft (or reroute) and reprocess** (22-00547184, 22-00523372, 22-00819224), then confirm the permanent fix's patch. Notification-email cosmetic bugs (hyperlink cutoff) are low-priority hotfixes (22-00830683).

---

## 10. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1732583** | Bug / **Closed** | MEW — Journal Allocation Batches Not Getting Journalized After Posting (JEGLEXPORT) | §7 D1 | 25-01022443 |
| **#1735315** | Bug / **Closed** | MEW — Failed to Stage Journal Allocation Batches After Posting (JEGLEXPORT) | §7 D1 | 25-01022443 |
| **#1374842 / #1414114** | Bug / **Closed** | MEW Upgrade — COREIMPJE Timeout Due to Building "IN" Clause with Large List (Leaseholder) | §7 D2 | 22-00664869 |
| **#1721401** | Bug / **Closed** | 2025.04 — LOSDD_IMP erroring; registered SQL `Sel_Intfc_Trans…` "Can't update batch" | §4 A1 | 25-01040307 (Patch 8) |
| **#1679797** | Bug / **Closed** | CEN/Permian — LOSDD_IMP job failing PRD | §4 A1 | 25-01038970 / 25-01040307 |
| **#1685518** | Bug / **Closed** | 2024.10 — LOSDD Import process failing with DB-related errors | §4 A1 | — |
| **#1712620** | Bug / **Closed** | CEN — LOSDD_IMP in WCP status | §4 A1 | — |
| **#1797306** | Bug / **Closed** | APH — Values in LOS report are not correct | §5 | — |
| **#1786273** | Bug / **Closed** | REPU 2024.10 — Process LOSLOAD Errors with "Parameters are Incorrect" | §4 A3 | — |
| **#1790224** | Requirement / **Proposed** | UPS CORE_REL — Hide Columns in LOS Report | §5 (enhancement) | — |
| **#102203** | (legacy) | Custom LOS changes (GLE/Pioneer client-specific) | §5 | 22-00655389 |
| **#21-00215794** | Patch (Jan-2022 for 2020.03) | AFE Inbox wrong Route Preview | §9 | 22-00669760 |

> Several actionable cases were dispositioned **operationally** with no single product WI: ODBC driver-whitelist removal script `05_RemoveCustom_OBDC_SQL_DRIVER_WHITELIST.sql` (25-01053798), `QPEC.ini` Command-Timeout raise for LOSLOAD-FULL (24-00977217), QRA data-fix + LOSDD/LOSLOAD reload for $0 LOS (25-01003756), post-migration "enable all jobs" script (24-00941672), `SEXTN_CORE_INTFC_JE` purge for COREIMPJE (22-00664869), and stuck-voucher/AFE Draft-reset scripts (22-00547184, 22-00523372). Confirm exact build/patch in `Quorum.Upstream.QCA.ReleaseNotes` when stating fix availability.

---

## 11. Diagnostic SQL

> **Caveat:** QCA on QCloud runs on **SQL Server**; per-client DBs are named like `<CLIENT>_<ENV>_UPS_QCA` (e.g. `RLY_LIV_UPS_QCA`) with schemas under `ESUITE_Q<CLIENT>`. Table/column names below come from case repro text and code search — **verify against the client DB before scripting**, and always run a verify-SELECT before any UPDATE/DELETE inside a transaction.

```sql
-- A. Which LOS stage failed? Check row counts across the LOS tables for a month (§2/§5)
--    _RAW/_FINANCIAL/_PRDN empty  => LOSDD_IMP didn't finish.  _CUSTOM_SL empty => LOSLOAD didn't finish.
SELECT 'RAW'       AS tbl, COUNT(*) cnt FROM QTRAN_LOS_RAW_DATA      WHERE ACCTG_MTH = '<ACCTG_MTH>'
UNION ALL SELECT 'FINANCIAL_SL', COUNT(*) FROM QTRAN_LOS_FINANCIAL_SL WHERE ACCTG_MTH = '<ACCTG_MTH>'
UNION ALL SELECT 'PRDN_SL',      COUNT(*) FROM QTRAN_LOS_PRDN_SL      WHERE ACCTG_MTH = '<ACCTG_MTH>'
UNION ALL SELECT 'CUSTOM_SL',    COUNT(*) FROM QTRAN_LOS_CUSTOM_SL    WHERE ACCTG_MTH = '<ACCTG_MTH>';

-- B. LOS duplication check (the 2x-6x revenue/volume pattern, §5) — duplicates usually arrive from upstream
SELECT PROP_NO, ACCTG_MTH, TRANS_TYPE, COUNT(*) dup_ct, SUM(AMT) tot_amt
FROM   QTRAN_LOS_CUSTOM_SL
WHERE  ACCTG_MTH = '<ACCTG_MTH>'
GROUP BY PROP_NO, ACCTG_MTH, TRANS_TYPE
HAVING COUNT(*) > 1
ORDER BY dup_ct DESC;

-- C. Did the LOS source rows even reach the core interface? (the "data on STRAN_CORE_INTFC but not in QTRAN_LOS_*" pattern, 24-00946713)
SELECT TRANS_TYPE, COUNT(*) FROM STRAN_CORE_INTFC WHERE ACCTG_MTH = '<ACCTG_MTH>' GROUP BY TRANS_TYPE;

-- D. JEA GL-export NULL-IN-clause trap (§7 D1) — the JEGLEXPORT silent-skip cause
SELECT BATCH_ID, COUNT(*) total,
       SUM(CASE WHEN PROP_NO IS NULL THEN 1 ELSE 0 END)              null_prop,
       SUM(CASE WHEN TO_PROSPECT_NO IS NULL THEN 1 ELSE 0 END)       null_to_prospect,
       SUM(CASE WHEN ORIGINAL_PROSPECT_NO IS NULL THEN 1 ELSE 0 END) null_orig_prospect
FROM   QTRAN_JE_SUBLEDGER
WHERE  BATCH_ID = '<BATCH_ID>' AND GL_POSTED_IND = 0
GROUP BY BATCH_ID;
-- Any non-zero null_* column => records will be skipped by JEGLEXPORT until the IN-clause NULL-filter fix (#1732583).

-- E. Did JEGLEXPORT stage anything into the core interface for the batch? (§7)
SELECT COUNT(*) FROM SSTAG_CORE_INTFC WHERE BATCH_ID = '<BATCH_ID>';   -- 0 with a "successful" run => the silent-skip

-- F. Scheduled-job status (the "disabled after cutover" cause, §6) — confirm enabled before assuming a load defect
--    Job/schedule metadata table name varies by build; look for the LOSDD_IMP / LOSLOAD definitions and an ENABLED/STATUS flag.
SELECT JOB_NM, SCHEDULE_DEFN, ENABLED_IND, LAST_RUN_DT
FROM   <scheduled-job/definition table>
WHERE  JOB_NM IN ('LOSDD_IMP','LOSLOAD');

-- G. Find the failing batch step + error by Process Queue ID
--    Get PQID from the user (e.g. 10184112) and read the batch message/log for that PQID + the named registered SQL.
```

---

## 12. Expected-Behavior / User-Education FAQ

~44 Training + ~103 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "LOS report missing data / blank for an accounting month" | The **`LOSDD_IMP` then `LOSLOAD` must both complete** for that month; a run that couldn't get the lock or was cancelled leaves the LOS tables short. Re-run both in order. | 24-00946713, 22-00582865 |
| "Gross/Net LOS values are duplicated / disparities vs our books" | **Upstream duplication** (initial QCFS import, **intercompany on Gross**, LOS330 dup records) — not a report bug; dedup the source then re-run. | 25-01051608, 24-00991389, 26-01084814 |
| "LOS Report Error" on run | A transaction in **Financial Subledger Inquiry (LOS310) had a NULL accounting month**; populate the accounting month and re-run. | 26-01083441 |
| "JBR025 / JBR055 / QP086 reports show no data" | Run the prerequisite step first (e.g. **Compute Vehicle Costs**, or run the LOS scheduled processes manually) — the report only shows data after its feeder process runs. | 22-00653735, 22-00582865 |
| "Copy with Header doesn't bring the header into Excel" | Use **'Export Selection'** when you need selected rows *with* the header; "Copy with Header" behaves differently by design. | 25-01026223 |
| "No values for Batch Userkey / picklist empty" | The report/picklist is tied to **JE Allocation functionality the client isn't using** — expected to be empty. | 25-01009391 |
| "AFE01 / report overhead looks doubled" | Check whether **JIB capital overhead is configured to flow to the AFE** (config), then it's expected; turn it off if not wanted (cross-ref §8). | 25-01025890 |
| "How does an AFE tied to a Cost Allocation work?" / asset-subledger removal / report page count | Education — assets only leave the subledger by **netting basis & accumulated depreciation to zero**; cost-allocation behaviour walked through. | 22-00577283, 22-00678294 |
| "Process stuck / lag time / lock won't release / UAT slow" | Usually **volume or a lock**, not a defect — wait for completion or **release the lock**; many "stuck" reports clear themselves. | 22-00646324, 22-00646207, 22-00512789, 22-00809155 |
| "JIB close warning — invalid service date / property allocation / non-op diff" | **Setup warnings**, not failures — fix the setup (service date, JE journal definitions for operated vs non-op, clear CTF failures). | 22-00629307, 22-00640006, 22-00629302 |
| "Need an AFE/voucher scripted back to Open/Estimate/Draft" | Operational **status-reset script** (often flagged out-of-scope); not a product fix. | 22-00624089, 22-00512757, 22-00632370 |
| "Where do I find report X / screen list / app version?" | Education — point to **Available Reports**, screen inventory/user guides, or the assembly-version steps. | 22-00512759, 22-00639558, 22-00653916 |
| "Scheduled QQM reports not emailing" | The recipient **email address** needs to be a valid (e.g. corporate) address. | 22-00584906 |

**Tell-tale it's user/expected:** an LOS number that's "wrong" because of **upstream duplication or a NULL accounting month**; a report empty because its **feeder process hasn't run** or the **feature isn't licensed/used**; a "stuck" process that is really a **lock or volume** wait; a JIB-close **warning** vs an error; or a request to **script a status back** (out-of-scope operational, not a defect). Verify the **LOSDD_IMP/LOSLOAD completion, upstream QRA/QCFS/JIB data, and feeder-process/schedule** before treating a report case as a defect.

---

## 13. Key Code, Processes & Repos

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **`LOSDD_IMP`** | Import core-interface data → `QTRAN_LOS_*` tables via registered SQL | Fails in a named registered SQL (`Sel_PRDN_VOL`, `Sel_Intfc_Trans…`) = view defect (§4 A1) |
| **`LOSLOAD`** | Load/aggregate → `QTRAN_LOS_CUSTOM_SL` (report source) | Parent/child (`QPSQcaLOSLoadChild`); FULL refresh = hours-to-days; timeout via `QPEC.ini` (§4 A3) |
| **`JEGLEXPORT`** | Stage billable JE entries → `SSTAG_CORE_INTFC` → QCFS GL095 batch | NULL in IN-clause silently skips (§7 D1) |
| **`COREIMPJE`** | Import core JE records → JEA module (stages `SEXTN_CORE_INTFC_JE`) | Large-IN-clause timeout (§7 D2) |
| **`JBIMPAGH` / JB200** | Import / maintain Allocation Groups | Bad import XLSX → rows stuck in `JBSTG_ALLOC_GRP` (§7 D3) |
| **`AP061` / Check Run / Check Register** | AP/revenue check printing | SSRS form + permissions + starting check numbers (§8) |

### Code locations (confirmed via ADO code search)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `QSQL_QcaLOSExtract.cpp` (registered-SQL `Sel_PRDN_VOL` extract) | `Quorum.Upstream.QCA.ClassicBatch /QPDllCostAcctgLOS/` | §4 A1 |
| `QPSQcaLOSLoadChild.cpp` (LOSLOAD child) | `Quorum.Upstream.QCA.ClassicBatch /QPDllCostAcctgLOS/` | §4 A3 |
| `QSQL_QcaLOSAriesPreCalc.cpp` (client LOS pre-calc, MEW) | `MEW.Upstream.QCA.ClassicBatch /QPDllCostAcctgLOS_MEW/` | §4/§5 (client override) |
| `USP_CUSTLOS_REMOVE_DUPL.sql` (LOS de-dup proc) | `<CLIENT>.Upstream.ESuite.Database /…/ESUITE_Q<CLIENT>/Procedures/` | §5 dedup |
| `QARCH_SQL.json` (registered SQL / view definitions) | `<CLIENT>.Upstream.Metadata /STANDARD <ver>/` | §4 A1 / §8 (JB350) |
| `JESubledgerExsport.cs` (JEGLEXPORT export method — NULL-filter fix) | `Quorum.Upstream.QCA.Batch` (managed JEA export) | §7 D1 (#1732583) |

### Repos (QCA / upstream)
- **`Quorum.Upstream.QCA.ClassicBatch`** — C++ LOS/JE batch (`QPDllCostAcctgLOS`: extract, LOSLOAD child).
- **`Quorum.Upstream.QCA.Batch`** — managed (C#) batch incl. JEA export (`JESubledgerExsport.cs`).
- **`Quorum.Upstream.QCA.Database` / `.Web` / `.ClassicGUI` / `.ReleaseNotes`** — core QCA DB objects, screens (JB200/GL025/GL095), release notes (confirm patch/fix availability here).
- **`Quorum.Upstream.Reports`** + **`Quorum.Upstream.QCA.Database`** — LOS/AFE/JIB/check report definitions.
- **`<CLIENT>.Upstream.QCA.Database`, `<CLIENT>.Upstream.Metadata` (`QARCH_SQL.json`), `<CLIENT>.Upstream.ESuite.Database`, `<CLIENT>.Upstream.Reports`** — per-client overrides (MEW, REP/REPU, PER/Permian, CEN, GEC, RLY, GLE, APH…). **Always check the client repo/schema first** — LOS views, registered SQL, dedup procs, and check forms are frequently client-specific.
- Cross-module data sources: **`Quorum.Upstream.QRA.*`** (revenue/production, the $0/duplication source) and **`Quorum.Upstream.QCFS.*`** (financials/trial-balance/JIB).

---

## 14. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **registered SQL / view** behind `LOSDD_IMP` is broken (`Sel_PRDN_VOL`, `Sel_Intfc_Trans…`) — typically patched (25-01040307/#1721401, 22-00544985, #1679797/#1685518/#1712620). Provide the **exact registered-SQL name + PQID + Gross/Net path**.
- `JEGLEXPORT` "succeeds" with **no GL095 batch** — the NULL-in-IN-clause defect (`JESubledgerExsport.cs`, 25-01022443/#1732583); or `COREIMPJE` **timeout** (large IN clause, 22-00664869/#1374842).
- An **LOS report value is provably wrong on correct inputs** (#1797306 APH) or a **workflow** defect (AFE route preview 22-00669760, WF email hyperlink 22-00830683, invoice-stuck 22-00819224, rebill-with-prepay 22-00831167).
- Provide: **PQID + failing step / registered-SQL name + exact error**, client + accounting month + Gross/Net, the property/batch, and a repro. Confirm fix availability in **`Quorum.Upstream.QCA.ReleaseNotes`** and the linked WI's target build. **Note:** a code fix often needs a paired **data fix** — confirm both were applied (25-01003756).

**Handle as Configuration / Cloud Ops when:**
- LOS **scheduled job disabled** (post-cutover all jobs disabled — run the enable script) or **schedule definition** wrong (24-00941672, 23-00929627, 25-01046718).
- `LOSDD_IMP` **ODBC error** → run `05_RemoveCustom_OBDC_SQL_DRIVER_WHITELIST.sql` (25-01053798).
- `LOSLOAD` **FULL-refresh timeout** on a large client → raise **`QPEC.ini` Command Timeout** (24-00977217).
- **AFE overhead doubled** → toggle JIB-capital-overhead-to-AFE (25-01025890); **QQM universe / report security** (24-00941372, 23-00913941); **check form + SSRS perms + starting check numbers** (23-00907242, 23-00907337); **JB350 registered-SQL** join fix in metadata (22-00660632).

**Data fix / script (operational) when:**
- LOS **duplicated** (dedup upstream QRA/QCFS/JIB, then re-run LOSDD_IMP/LOSLOAD — 24-00990633, 23-00884375); LOS **$0** (apply the **QRA data fix**, reload — 25-01003756); **NULL accounting month** on a LOS310 transaction (26-01083441).
- **Stuck** vouchers/AFEs/invoices → reset status to **Draft** / reroute and reprocess (22-00547184, 22-00523372, 22-00819224); **missed jobs** during an outage → reprocess script (22-00654690); **`SEXTN_CORE_INTFC_JE` purge** to unblock COREIMPJE (22-00664869). Always verify-SELECT in a transaction.

**Handle as Training / Expected behavior (no fix):** see §12 — LOS "missing/duplicated" that is really upstream data or an incomplete LOSDD_IMP/LOSLOAD run; reports empty because a **feeder process** hasn't run or the **feature isn't used**; "stuck"/lag that is a **lock or volume** wait; JIB-close **warnings**; "script my AFE/voucher back" out-of-scope requests; and "how does it work / where is report X" questions. Verify **LOSDD_IMP/LOSLOAD completion, upstream data, and feeder-process/schedule** before treating it as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 377 closed QCA SF cases in categories LOS (131) + Ad-Hoc Reporting (220) + JEA (26) — 76 actionable (Software Defect 46 + Application Configuration 29 + ChangeConfig 1), 38 with usable resolutions mined for fix recipes, plus ~60 Training/Customer-Error cases for the FAQ. ADO work items #1732583, #1735315, #1374842/#1414114, #1721401, #1679797, #1685518, #1712620, #1797306, #1786273, #1790224.*
*Companion: SKILL_QCA_* (other QCA category groups), REPO_INVENTORY / CONFIG_REFERENCE (Upstream Assistant project).*
