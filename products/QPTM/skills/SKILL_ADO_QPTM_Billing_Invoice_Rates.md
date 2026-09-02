# SKILL: QPTM Billing / Invoice / Rates — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management)
**Source:** Azure DevOps **Bugs** (Closed/Resolved) under `Engineering\Energy Transportation` and `Engineering\Maintenance\Midstream and Transportation`, area = **Billing / Invoice / Rates**. Read-only mining of work-item Description, ReproSteps, linked PRs, and the full dev **comment thread** (where root cause + fix decision live).
**Use When:** an L4 case touches QPTM **billing invoice generation** (BLINVGEN / PANIGHTLY), **rate maintenance / rate resolution**, **capacity-release / offer / award rate generation**, **invoice group / TSP billing config**, **invoice screens & reports** (SOA, Invoice Documents, Billing Voucher), **cash-out imbalance billing**, or **invoice/rate sequence-limit failures** — and you want to know if the symptom is a *known* defect, what the root cause was, whether a fix exists, and which release it landed in.

> **Evidence base:** WIQL matched **732** Bug work items on the functional terms (Invoice, billing, BLINVGEN, rate, SOA, invoice group, charge, cashout, PANIGHTLY, rate schedule) across both area branches. The Maintenance branch is **mixed QPTM+TIPS**; after dropping items whose titles are clearly TIPS (Settlement Invoice (108), Fixed Fuels, Division Order, gathering settlement statement, UDEF, plant statement) and QLNG/cargo-scheduling items, **~600** are QPTM billing/invoice/rate-relevant. **47** representative bugs were deep-read (Description + ReproSteps + comment thread + PRs) across the clusters below. Every root-cause/fix claim cites the ADO bug ID and, where present, the linked SF case (`YY-0xxxxxxx`) and PR numbers. **`Microsoft.VSTS.Build.IntegrationBuild` is empty on essentially every item** — fixed-in-release is inferred from iteration path (YY.NN), release/QA tags, and the merge comments; such values are marked **(inferred — confirm in release notes)**.

> **Overlap caveat:** several "invoice" defects in the Maintenance branch are actually **TIPS gathering settlement** (one-to-many join showing a fee Nx, GST-twice, value_core_hist reversal, SP_QTIP_PL_STMT_RPT). Those are flagged in §11 and belong to the TIPS Invoice/Billing skill, not QPTM. When the symptom mentions **meters / plants / producers / settlement statement / QFAIM / value_core**, it is TIPS, not QPTM.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — BLINVGEN / PANIGHTLY batch failures](#4-cluster-a--blinvgen--panightly-batch-failures)
5. [Cluster B — Invoice/Rate SEQUENCE limit exhaustion (Int32)](#5-cluster-b--invoicerate-sequence-limit-exhaustion-int32)
6. [Cluster C — Rate Maintenance / Rate Resolution](#6-cluster-c--rate-maintenance--rate-resolution)
7. [Cluster D — Capacity Release / Offer / Award rate generation](#7-cluster-d--capacity-release--offer--award-rate-generation)
8. [Cluster E — Invoice calculation wrong (tripled / credit / mismatch / rounding)](#8-cluster-e--invoice-calculation-wrong)
9. [Cluster F — PPA generation on billing](#9-cluster-f--ppa-generation-on-billing)
10. [Cluster G — Invoice Group / TSP Billing Configuration](#10-cluster-g--invoice-group--tsp-billing-configuration)
11. [Cluster H — Invoice reports blank / duplicated / report failures](#11-cluster-h--invoice-reports-blank--duplicated--report-failures)
12. [Cluster I — Cash-out imbalance billing (INCUVCALC)](#12-cluster-i--cash-out-imbalance-billing-incuvcalc)
13. [FIX-VERSION MATRIX](#13-fix-version-matrix)
14. [Diagnostic Pointers (SQL & logs)](#14-diagnostic-pointers)
15. [Escalation Guidance](#15-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check / cluster |
|---|---|---|
| BLINVGEN / PANIGHTLY **"Stopped Processing on Error"** with `ERROR SETTING VALUE FOR COLUMN INVOICE_INPUT_ID` or `Value was either too large or too small for an Int32` | **Sequence exhaustion** — `BLTRAN_INVOICE_INPUT.INVOICE_INPUT_ID` / `BLTRAN_INVOICE_RATE.INVOICE_RATE_ID` in `QTRAN_SEQ` near 2,147,483,647 | §5 — `SELECT * FROM QTRAN_SEQ WHERE LAST_NO >= 2000000000` |
| BLINVGEN fails on `PK_BLSTAG_INVOICE_CTR_DT` PK violation; deleting the staging rows doesn't help | Bad **contract time-slice** (single-day slice added after a longer slice) | §4 — combine/extend the time slice, re-run alloc/inv/billing (#1773883) |
| BLINVGEN/BLINGVGEN1 fails at **BLQTYGATH** with a formula error | **`&gt;` escape char** in a formula created from Web bleeding into Classic | §4 — fix the formula in Classic (`>`); cherry-pick web escape fix (#1633605) |
| BLINVGEN runs **4–12 hours**, stuck on BLINVCLNUP / a SELECT-INTO insert | Oracle picking a bad plan; query needs `/*+ NO_QUERY_TRANSFORMATION */` hint; or CPU contention | §4 — DBA: explain plan, gather stats; recurs ~every 4–6 months (#1641239, #1610212) |
| Rate **tripled** on flex/reservation charges; Invoice Sub-Detail shows 3 identical rate rows | Core+client billing-detail defect | §8 — re-run BLINVGEN after fix; QTR-style hotfix (#1632428) |
| Invoice Header / Detail / Billing Voucher / SOA differ by **$0.01** (or qty mismatch) | **Rounding inconsistency** (banker's vs round-half-up) in `QPipelineRoundingMgr` for Currency/tax | §8 — rounding fix family (#1674944, #1652371, #1559943) |
| Overrun TOC gives a **credit** when allocated qty is **under** contract MDQ | Below-MDQ treated as negative overrun; code inserts on either Eng/Vol qty positive | §8 — fixed develop/2025.10/2025.04; workaround `IIF(OVRRF<0,0,OVRRF)` (#1770399) |
| "Multiple Rate IDs" on Rate Resolution report; can't find the dup | Path location lives in **two overlapping location groups** | §6 — config/data, not a defect (#1631007) |
| Rate Maintenance **duplicate error** when end-dating an open-ended time slice | Validation bug `QPTMValidationRateMaintenance012_GenChkDuplicateError` | §6 — fixed 2023.04 (#1651264) |
| Award generates **COM + REST/RESC** rates (wrong set) on Reservation/Volumetric offer | **TOC – Object Setup** rules missing/not excluding rate types | §7 — config (#1430622, #1376378) |
| Replacement contract not in invoice group after **web** award (works in Classic) | Web award skips invoice-group assign (Classic runs BLKINVGRP) | §7 — fixed 2021.10; workaround run BLKINVGRP (#1394171) |
| Web Rate **delete** doesn't generate PPAs (Classic does) | PPA triggers only on Add/Modify, not Delete, in Web | §6/§9 — end-date or zero the rate instead (#1745668) |
| Lump-sum charge **prebilled** for future production months | `BLSTAG_INVOICE_CTR_DT` holds pre-paid rows for open-ended lump sum | §8 — lump-sum SQL fix prod_mth ≤ acctg_mth (#1670549) |
| Invoice Documents / BLRX report **blank** though invoice data exists | Report defaulting **PRE** invoice status, or end-dated BA address seq, or missing `IN_FOOTER_EMAIL` param | §11 (#1607181, #1645926) |
| Invoice **duplicated** Nx on the report | **Multiple invoice-copy contacts** on the invoice group (working as designed) | §11 — one copy contact per group (#571372) |
| Cash-Out Imbalance not tying out / INCUVCALC won't run | Client-specific (ENT/GNP) cash-out unrealized-value calc; migrated to core | §12 (#1675211) |

---

## 2. Pipeline & Concepts

```
[Nominations] → ALALLOCATE (allocation) → INACCTACCM (acctg accumulation) → [Rate Maintenance / Capacity-Release rates]
      │
      ▼  BILLING INVOICE GENERATION (BLINVGEN)  — steps: BLQTYGATH (qty gather) → rate resolution → BILINVPRE/BLINVCLNUP → doc generation
[BLTRAN_INVOICE_INPUT → BLTRAN_INVOICE_RATE → BLTRAN_INVOICE_SUB_DTL → BLTRAN_INVOICE_DTL → BLTRAN_INVOICE_HDR]
      │                                                          │
      ├──► PPA (Prior Period Adjustment) regen on rate/timeslice change
      └──► REPORT staging (BLRPTS_00_INVOICE_CONTROL, BLRPTS_10_INVOICE_DOC_MAIN/_SUM/_IMB_DTL) → Crystal reports (BLR_00, BLRX_00, Billing Voucher, SOA, Invoice Documents)
```
- **PANIGHTLY / PANIGHTLY3** = the nightly scheduled batch chain (per TSP) that runs Measurement→Allocation→Inventory→**BLINVGEN**. A failure on the BLINVGEN step stops the whole nightly close. The unit of diagnosis is the **PQID (Process Queue ID) + the failing step name + the exact ORA/COM error**.
- **BLINVGEN** = Billing Invoice Generation. Sub-steps seen in failures: `BLQTYGATH` (quantity gather), `BILINVPRE`, `BLINVCLNUP` (cleanup). Run with **Invoice Status = Preliminary/Final**, an **Accounting Month**, and an **Invoice Group ID**.
- **TOC** = Type Of Charge (RESC/RESCF reservation, COM commodity, REST reservation surcharge, INCRF/INCSP incremental reservation, OFNRD overrun, PROC, etc.). **TOC – Object Setup** + **Type of Charge Setup** drive which rate types are generated/billed — a frequent *config* root cause.
- **Rate resolution** = matching a nominated path to a `BLTRAN_INVOICE_RATE` via Rate Maintenance (Rate ID, Rate/Contract Assoc, Locations, Matrix tabs) + location groups. "Multiple Rate IDs" = ambiguous overlapping location-group membership.
- **Capacity Release** = Offer → Bid → **CRBIDEVAL** (bid evaluation) → Award → **Replacement Contract** generation, then those contracts must be linked to an **Invoice Group** (Classic auto-runs **BLKINVGRP**; web historically did not).
- **PPA** = Prior Period Adjustment. Editing a rate/time-slice for a closed month *should* generate PPA events to re-bill; over- or under-triggering PPAs is a recurring billing complaint.
- **Sequence** = `QTRAN_SEQ` per-TSP integer counters for staging-table PKs. Staging tables purge on a short cycle (ARCH_7_DAY) but the counter only climbs → it can hit the **Int32 max (2,147,483,647)** and crash billing (§5).
- **Key tables:** `BLTRAN_INVOICE_INPUT/_RATE/_SUB_DTL/_DTL/_HDR` (live), `BLSTAG_INVOICE_CTR_DT` (lump-sum/prebill staging), `BLRPTS_*` (report staging), `CRCTRL_OFFER_*` / `QVPCAPRELOFFER_DETAIL` (capacity release), `QCTRL_RATE_SCH` (rate schedules).
- **Code repos:** `Quorum.QPTM.ClassicBatch` (C++ BLINVGEN/billing), `Quorum.QPTM.Web` / `.Web.Controllers` (Rate Maintenance, RFS Wizard, Invoice Maintenance — C# validators like `QPTMValidationRateMaintenance012_*`), `Quorum.QPTM.Metadata` (report params, process steps), and **client overrides** `<CLIENT>.QPTM.ClassicBatch / .Web / .Metadata / .Application.QPEC` (TEP, XCL, HPE, QTR, ETC, GNP/ENT, HEP, TGL…). **Always check the client repo/layer** — many fixes are client-specific or require re-consuming the latest `Quorum.QPTM.ClassicBatch` into the client batch repo (#1632428).

---

## 3. Decision Tree

```
QPTM billing/invoice/rate case
│
├─ A batch process crashed? (BLINVGEN / PANIGHTLY) → GET PQID + STEP + EXACT ORA/COM ERROR
│   ├─ "...INVOICE_INPUT_ID" / "too large/small for Int32" / max-seq notice  → §5 SEQUENCE limit (script: add to archive def + reset QTRAN_SEQ)
│   ├─ PK violation PK_BLSTAG_INVOICE_CTR_DT                                  → §4 bad contract time-slice (#1773883)
│   ├─ Formula error at BLQTYGATH (stray &gt;)                                → §4 fix formula in Classic (#1633605)
│   ├─ Runs 4–12h / stuck on BLINVCLNUP                                       → §4 perf: explain plan, NO_QUERY_TRANSFORMATION hint, CPU (#1641239,#1610212,#1364166)
│   └─ "Continue Process On Failed Execute Is FALSE" in beta/RELQA            → §10 missing TSP Billing Config / invoice group for payment term (#1792423)
│
├─ Invoice number/value WRONG (process didn't crash)?
│   ├─ Rate tripled / duplicate rate rows                                     → §8 (#1632428)
│   ├─ Header vs Detail vs Voucher vs SOA differ by pennies / qty             → §8 rounding family (#1674944,#1652371,#1559943)
│   ├─ Overrun TOC credit when under MDQ                                      → §8 (#1770399; workaround IIF(OVRRF<0,0,OVRRF))
│   ├─ Lump-sum prebilled future months                                      → §8 (#1670549)
│   ├─ "Multiple Rate IDs" on Rate Resolution                                → §6 overlapping location groups (config) (#1631007)
│   └─ Reservation FTS month→daily conversion wrong                          → §8 (#1413101; config GROUP_BY_RATE_ID_QTY)
│
├─ Rate Maintenance / Rate Schedule screen?
│   ├─ Duplicate error end-dating open-ended slice                            → §6 (#1651264)
│   ├─ Web delete doesn't make PPAs / save/import errors                      → §6 (#1745668,#1645355) — end-date instead
│   └─ Rate-schedule precision overflow (14,7) / picklist returns nothing     → §6 (#1781738 enhancement; #1697677 data)
│
├─ Capacity Release / Offer / Award / RFS?
│   ├─ Wrong rate set (COM/REST/RESC) on award                                → §7 TOC–Object Setup config (#1430622,#1376378)
│   ├─ Replacement K not in invoice group after web award                     → §7 (#1394171; run BLKINVGRP)
│   ├─ Replacement K wrong dates / PAL rates disappear / dup fuel rate        → §7 (#1492803,#1655024,#1771559)
│   └─ INCRF incremental reservation not billing for repl K                   → §7 (#1416770)
│
├─ Report blank / duplicated / fails?
│   ├─ Blank though data exists                                               → §11 (#1607181 PRE status/footer param; #1645926 end-dated BA addr)
│   ├─ Duplicated Nx                                                          → §11 multiple copy contacts (config) (#571372)
│   └─ Crystal/logo/format                                                    → §11
│
└─ Cash-out imbalance not tying out / INCUVCALC                               → §12 (#1675211 ENT/GNP→core)
```

---

## 4. Cluster A — BLINVGEN / PANIGHTLY batch failures

**The dominant operational signature.** PANIGHTLY (the nightly per-TSP chain) or a manual BLINVGEN "Stops Processing on Error." Get **PQID + failing step + exact ORA/COM error** first.

### A1 — Sequence exhaustion (most common hard failure) → see **§5** (its own cluster, very repeatable).

### A2 — PK constraint violation from a bad contract time-slice
- **Bug #1773883** (HPE, SF 25-01062471): BLINVGEN fails at **BILINVPRE** with `violation of PRIMARY KEY 'PK_BLSTAG_INVOICE_CTR_DT'`. Deleting the staging rows did **not** fix it.
- **Root cause:** a one-day contract time-slice (12/17–12/17) was added *after* a longer slice (12/18–12/31) with identical terms; billing chokes on the single-day slice.
- **Fix / workaround (data/config):** delete the one-day slice in **Classic** (Web won't allow the delete) and **extend** the longer slice back to cover the day (12/17–12/31), then re-run allocations → inventory → billing. Worked in HPE prod. No code change. *Note the dev aside:* the "can't delete contract in Web" bug is fixed in 2024.04 and older — another reason to upgrade.

### A3 — Formula `&gt;` escape character from Web breaks Classic billing
- **Bug #1633605** (TEC/TECO, SF 23-00931079): BLINVGEN/BLINGVGEN1 fails at **BLQTYGATH** quantity-gathering on a **formula error**; failing since Nov-4.
- **Root cause:** a formula **created in Web** stored the HTML escape `&gt;` instead of `>`; Classic batch couldn't parse it. Does not happen in 2023.04.
- **Fix:** short-term — correct the formula in **Classic** to a real `>`; long-term — cherry-pick the Web escape-handling fix back to 2021.04 (separate WI). 

### A4 — Long runtime / hang (performance, recurring)
- **Bug #1641239** (QTR/Mountain West, SF 24-00938219): BLINVGEN runs **12 hours**, stuck on **BLINVCLNUP**. Recurs ~every 4–6 months. **Root cause:** Oracle optimizer occasionally picks a bad plan for an INSERT…SELECT; adding `/*+ NO_QUERY_TRANSFORMATION */` to that query made it run in **3 minutes**. Engineering treated it as a DBA/stats issue (gather stats, check locks/AWR); the hint change was *not* productized. **Workaround:** DBA gather stats / add the hint; closed without a code fix.
- **Bug #1610212** (XCL, SF 23-00909829): PANIGHTLY ran 9–10h then failed on BLINVGEN; partly **user error** (ran TSP 100 PANIGHTLY by accident) + connection drop. No code fix.
- **Bug #1364166** (ONK, SF 21-00197817): PANIGHTLY "Stops Processing on Error" at **Greater of Overrun TOC** step. Suspected **CPU contention** on segregated processes — recommendation to raise QPEC server CPUs to 6; never definitively root-caused, eventually closed (no recurrence). Not a code bug.

### A5 — SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` at Generate Documents (LPS/PAL statements)
- **Bug #1836277** (EQC/EQT, SF 26-01106039): BLINVGEN "Run All PPAs" crashes in registered SQL `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY` → "PAL statement records were not successfully inserted." Net effect: LPS-F PPAs complete the whole lifecycle but **no billing adjustment generates** (client entered manual LGAs as workaround). **Open, NO fixed-in version** (Proposed as of 2026-08-14).
- **Root cause:** QPTM build **3.1.00.0069** drop scripts removed CORE table `BLSTAG_PAL_EXT` while CORE `QPSGenerateDocuments.cpp` still injects `LEFT OUTER JOIN BLSTAG_PAL_EXT` when `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` is true (missing-key default TRUE) and TSP key `INV_DOC_PAL_STMT`=DAY. No CREATE DDL survives in any repo; writer exists only at DTE/QLNG → any non-DTE 0069+ instance with PAL statements is exposed.
- **Fix / workaround (ops, no code):** per **WI #1836679** precedent — script the object from an instance that has it (fixed DEV or DTE; do NOT hand-build DDL), create in affected envs, rerun "Run All PPAs" for affected months (PEX rows appear in `BLTRAN_INVOICE_GEN_QTY`), reverse the manual LGAs. Empty table = complete fix (LEFT OUTER, only `EXT_DAY_COUNT` read). ⚠️ Guarded 0069 drop script re-drops on baseline re-run — permanent CORE DDL restore required (ride Bug #1836277). See SKILL_Billing.md §4.4 for the full recipe.

**Fix recipe:** (1) PQID + step + ORA/COM error. (2) Map to A1–A5. (3) Sequence error → §5 script. (4) PK_BLSTAG_INVOICE_CTR_DT → fix the contract time-slice. (5) Formula error at BLQTYGATH → fix the formula in Classic. (6) Runaway runtime → DBA explain-plan/stats; the hint trick is the known mitigation, not a shipped fix. (7) SQL 208 on `BLSTAG_PAL_EXT` → A5 ops DDL deploy.

---

## 5. Cluster B — Invoice/Rate SEQUENCE limit exhaustion (Int32)

**A distinct, highly repeatable hard-stop on older builds.** Billing staging tables purge on a short cycle, but their `QTRAN_SEQ` counters only ever climb and can hit the **Int32 maximum 2,147,483,647**, after which BLINVGEN throws `ERROR SETTING VALUE FOR COLUMN <col> FOR PRIMARY TABLE <table>` or `Value was either too large or too small for an Int32`.

| Bug | Client / SF | Sequence | Notes |
|---|---|---|---|
| **#1607556** | TEP/Tallgrass, 23-00907641 | `BLTRAN_INVOICE_INPUT.INVOICE_INPUT_ID` (TSP 302) | First documented; jump in PRD. PRs 86236/86358/87868 = core **Archive Definition** change (add table to ARCH_7_DAY) + client sequence reset. |
| **#1639324** | XCL/Xcel, 24-00936702 | `BLTRAN_INVOICE_INPUT.INVOICE_INPUT_ID` (+ `ALSTAG_ALLOC.ALLOC_NO`) | PR 93244; resolved via QARCHIVE setup. Allocation seq (`ALSTAG_ALLOC.ALLOC_NO`) tracked separately (#1642856) — older build lacks the "larger ALLOC_NO" feature. |
| **#1728741** | XCL/Xcel | `BLTRAN_INVOICE_RATE.INVOICE_RATE_ID` | LAST_NO at 2,116,672,095 vs max 2,147,465,034 → billing failed in PRD. This sequence was **not** covered by the earlier long-term fixes. Script resets LAST_NO to 1. |
| **#1575542** | XCL/Xcel, 23-00881662 | multiple billing **and** allocation seqs | Same family + a reverted ALALLOCATE core change; XCL on an older build missing the seq-prevention fixes. |
| **#1665295** | TEP/TIGT, 24-00957495 | `BLRPTS_10_INVOICE_DOC_IMB_DTL` identity | "Generate Documents Error: too large/small for Int32" — same root cause on a **report-staging** identity column; added table to ARCH (RPTS_CORE) + `DBCC CHECKIDENT(...,RESEED,1)` after purge. |

- **Long-term fixes referenced:** **#1384511**, **#1572396**, **#1600044** (prevent / widen / reset). They did **not** cover every sequence — `BLTRAN_INVOICE_RATE.INVOICE_RATE_ID` slipped through (#1728741) and report-staging identities (#1665295) are separate.
- **Operational fix recipe (the repeatable one):**
  1. `SELECT * FROM QTRAN_SEQ WHERE LAST_NO >= 2000000000;` (and `QARCH_TRAN_SEQ`) to find which sequence is near max.
  2. Ensure the staging table is in the short-cycle **Archive Definition** (e.g. `ARCH_7_DAY`); run the purge (`QPTM_PRG`) so live rows are gone.
  3. **Reset** the counter: `UPDATE QTRAN_SEQ SET LAST_NO = 1 WHERE SEQ_NM = '<table>.<col>' AND TSP_NO = '<tsp>';` (MSSQL identity: `DBCC CHECKIDENT('<table>', RESEED, 1)` after deleting old rows). Safe because the table purges, so old/new numbers won't collide.
  4. **Confirm the client build has #1384511/#1572396/#1600044** — older builds will keep recurring (XCL hit it repeatedly). On SQL Server, dev suggested trying the `UTIL_RESEED_IDENTITIES` stored proc.
- **Escalation:** if the client is on a build *without* these fixes, the permanent answer is **upgrade**; until then schedule a proactive reset (XCL got ~6 months of runway per reset). Always verify-SELECT and wrap scripts in a transaction.

---

## 6. Cluster C — Rate Maintenance / Rate Resolution

| Issue | Root cause | Fix / disposition | Bug / SF |
|---|---|---|---|
| **Rate Maintenance "Duplicate error"** when end-dating an open-ended (…–12/31/9000) time slice or creating the next slice | Validator `QPTMValidationRateMaintenance012_GenChkDuplicateError.cs` flagged a real overlap with **other** rates (not self-overlap) — but the screen behaved as a bug for the legitimate split | **Code fix** (Web) PRs 95107/95171/95172/95173. Fixed **2023.04** hotfix *(inferred from comments)* | #1651264 / HPE 24-00947028 |
| **"Multiple Rate IDs"** on the Rate Resolution report; BLINVGEN completes with warnings | The nominated **path's locations belong to two overlapping location groups** (e.g. ALL_QPC_LOC and OFF-SYSTEM - OTPL), so >1 rate detail resolves | **Config/data — NOT a defect.** Client adjusted the Rate ID / location-group membership so only one rate resolves | #1631007 / QTR 23-00927199 |
| **Web rate DELETE doesn't generate PPAs** (Classic does) | PPA logic in Web only fires on **Add/Modify**, not **Delete**; Classic goes straight into the PPA flow | **No code change shipped.** Guidance: **end-date** or **zero out** the rate (both trigger PPAs) instead of deleting; "block delete of in-use rates" proposed for a future release | #1745668 / HPE 25-01025418 |
| Rate/Contract Assoc tab **import-from-Excel** save throws `RateTosTocRuleXRef.TosCode` error | Test/data issue — can't save the same contract twice w/o different amendment seq; not reproducible with a single valid contract | Closed working-as-expected after retest | #1645355 |
| Rate Schedule **FIXED_FEE arithmetic overflow** (value > precision/scale `14,7`) | Column precision limit | **Enhancement, will-not-fix** (risk/testing footprint). Workaround: CCT that multiplies/divides by 20 (#1781738, EQC 26-01079515) | #1781738 |
| Rate Schedule **picklist returns no records** though DB has data (Schedule ID AGDHH) | Bad `QCTRL_RATE_SCH` data — `PROD_CD`/`PROD_GRP_CD` mismatch (extra `PROD_CD='NA'` rows) | **Data cleanup script** (delete the bad PROD_CD rows, set PROD_CD='NA' where group is NA) | #1697677 / CCI 24-00988456 |
| TEP "Erroneous Charges" — path not pulling correct rate / can't charge INCSP TOC | Rate/location-path setup on the contract (fixed $0.00 path on the rate) | Investigated as **config/data**; L4 Learn | #1648338 / TEP 23-00934451 |

> **Pattern:** the recurring *true defect* here is the **Rate Maintenance duplicate-error** when timeslicing open-ended rates (#1651264). The frequent *non-defects* are **overlapping location groups** ("Multiple Rate IDs", config) and **Web-vs-Classic behavior gaps** (delete→PPA, save/import) where the answer is end-date/zero the rate or fix the data. `QCTRL_RATE_SCH` precision/picklist issues are gathering-side rate-schedule data (verify it isn't a TIPS rate schedule).

---

## 7. Cluster D — Capacity Release / Offer / Award rate generation

Offer → Bid → **CRBIDEVAL** → Award → **Replacement Contract** → invoice-group link → billing. Most defects are **config (TOC – Object Setup / Type of Charge Setup)** or **Web-vs-Classic parity**.

| Issue | Root cause | Fix / disposition | Bug / SF |
|---|---|---|---|
| Awarding a **Reservation** offer generates **REST *and* COM** rates (and Volumetric generates RESC+COM) — wrong rate set | **Type of Charge Setup** had no rule for the TOC type (e.g. COM) excluding the Reservation Charge rate type | **Config:** add the TOC rule excluding the wrong rate type; then Reservation→REST only, Volumetric→COM only | #1430622, #1376378 |
| After **web** award, replacement contract is **not added to an invoice group** (Classic adds it) | Web award path didn't run the invoice-group assignment that Classic does | **Code fix** PR 62261, fixed **2021.10** *(inferred)*. **Workaround:** run **BLKINVGRP** for that contract | #1394171 |
| Replacement contract generated with **incorrect (original) dates** when copying an offer | Stale **seasonal dates** on copied offer detail (`CRCTRL_OFFER_DTL`) when `USE_SEASNL_DATES=0`; Details tab cleared on header-date change | **Code fix** PR 71377 (~**22.15 / 2022.10** *(inferred)*) — when `USE_SEASNL_DATES=0` always match detail seasonal dates to offer header releasing dates. Config-gated by `USE_SEASNL_DATES` / `CAPACITY_RELEASE.USE_AUTO_POPULATE_SEASNL_DATES` | #1492803 / TEP |
| **PAL requested rates disappear** on RFS Wizard (PAL tab) after Next/Save/Validate | Client (QTR) was running **core** `RFSWizardV2` not `QTRRFSWizardV2` after upgrade; `PALRequestedRatesGridUpdate` not overridden | **Code fix** PRs 95406/95407/95478/95479/95567 — made `PALRequestedRatesGridUpdate` virtual in core and overrode in QTR controller (client-specific) | #1655024 / QTR 24-00947894 |
| **INCRF** incremental-reservation TOC not billing for a **CR replacement contract** | A stale **INCSP** rate had the cross-zone path; TOC resolved as primary→secondary zone and skipped | Resolved by **removing** the 955215 contract from the 11174 INCSP rate (data/config) | #1416770 / TEP RC2 |
| `USE_TSP_TOS_CTR_PREFIX=true` — Cap-Rel replacement contracts **not** generated with TSP_TOS prefix | There is **no batch (C++) support** for this config in Capacity Release (only Contract Maintenance / RFS C# gen) | **Enhancement / backlog** (#1659750) — never worked for Cap Rel | #1653116 / GBG 23-00922106 |
| **Web allows** Cap-Rel replacement contracts to have >1 fuel Rate ID with same eff dates (Classic blocks) | Web validation gap; Classic errors as expected; downstream rate use will error | Web-only gap → core backlog (duplicate of **#1799752**); HPE out of support → upgrade | #1771559 / 25-01056308 |
| Cap-Rel Offer **Max Tariff Rate** blank / **Market-Based-Rate-Indicator** forces Yes (Classic) | Could not resolve a max tariff rate (config) / not reproducible | **Rejected** — config (#1551398, #1551416) | #1551398, #1551416 |
| TEP **Preliminary Cashout** absent from TPC invoice (RPT_BLR_00) | `BLRPTS_10_INVOICE_DOC_IS.TIER_DTL_ID_ONE..FIVE` never populated; Crystal sub-report inner-joins on them → no rows. Code wrote default tiers in `QPSGenerateDocuments::DetermineDefaultTierRanges` but skipped the real tiers in `DetermineTierRanges` (lines 1591–1643) | **Code fix** PRs 77967/79456/79457 (~**2022.10/2023.04** *(inferred)*) | #1524951 / TEP |

> **Pattern:** wrong-rate-on-award is almost always **TOC – Object Setup / Type of Charge Setup** config. Replacement-contract date/group/PAL issues are **Web-vs-Classic parity** code fixes (often client-specific, requiring the client to use *their* `<CLIENT>RFSWizardV2`/controller). `USE_TSP_TOS_CTR_PREFIX` and the web dup-fuel-rate gap are **known backlog/enhancements**, not hotfixes.

---

## 8. Cluster E — Invoice calculation wrong

The "the number is wrong" cluster (process didn't crash). Highest-business-impact (FERC compliance).

| Issue | Root cause | Fix + fixed-in-build | Bug / SF |
|---|---|---|---|
| **Rate tripled** on flex/reservation charges — Invoice Sub-Detail has 3 identical rate+qty rows for gas days | Core+client billing-detail generation defect (duplicate detail rows for replacement-contract reservation flex) | **Code fix** PRs 91279/91280/92059/92060/92061. Merged **2022.10, 2023.04, develop**; delivered via **QTR hotfix** — requires consuming **`Quorum.QPTM.ClassicBatch 17.27.19-beta.1`** into `QTR.QPTM.ClassicBatch`. Workaround: re-run BLINVGEN after fix | #1632428 / QTR 23-00929118 |
| Invoice **Header / Detail / Billing Voucher / SOA** differ by **$0.01**; tax rounds differently | **Rounding inconsistency** — `QPipelineRoundingMgr::Round` / `RoundDown(...,Currency)` appears to do **banker's rounding** on tax/amount columns (`TAX_TRANS_AMT` vs `TAX_TRANS_AMT_UNROUNDED`) instead of round-half-up | **Core hotfix** PRs 101466/101728/101888/101994/102089/102090, iter **24.21** (~**2024.10** *(inferred)*). Later re-opened for WWM over half-even at the 3rd decimal (0.015→0.01 vs 0.02) — confirm the rounding rule in the target build | #1674944 / TGL 24-00965437, 22-00823331 |
| Invoice **Sub-Detail vs Header-by-Contract/TOS** screens show different totals/qty (FERC) | Same penny-mismatch family; ETC's "Penny Mismatch" change had to be partially backed out and the 3 contracts isolated into their own invoice group | **Code fix** PRs 94942/95011/95033/95034/95035 (delivered to TEP/ETC ~early 2024). Cross-refs ETC #1559943 | #1652371 / TEP 24-00948061; #1559943 / ETC 22-00293099 |
| **Overrun TOC** (OFNRD / `OVRRF` charge basis) gives a **credit** when allocated qty is **below** contract MDQ | Code intentionally inserts overrun when **either** `TotalOverrunEngQty` **or** `TotalOverrunVolQty` is positive; below-MDQ produces a negative EngQty but positive VolQty → writes a credit | **Code fix** PRs 121830/121895/122014 — fixed in **develop, 2025.10, 2025.04**. **Workaround:** formula-aggregate charge basis `IIF(OVRRF < 0, 0, OVRRF)` | #1770399 / ETC 25-01058130 |
| **Lump-sum** charge **prebilled** for future production months | `BLSTAG_INVOICE_CTR_DT` (lump-sum rate staging) holds pre-paid rows for current acctg month; an **open-ended** lump-sum rate is billed for future prod months | **Code fix** PRs 102415/102416/102417 — lump-sum SQL changed to pull rates only where **`prod_mth <= acctg_mth`** (~2024.10/24.21+ *(inferred)*). Also driven by a pre-pay flag on TOS/Charge Basis Maintenance | #1670549 / 24-00953508 |
| Reservation **not charging correctly for FTS** — wrong **month→daily** rate conversion | RESC and RESCF TOCs got grouped under a **single invoice detail** post-v17 (vs separate pre-v17), inflating the calc factor (#sub-details/days ratio) in `ComputeCalcFactor()` | **Code fix** PRs 63528–64484; new config **`BILLING / GROUP_BY_RATE_ID_QTY`** to restore RATE_HDR_ID grouping. Fixed **QPTM 2021.12** | #1413101 / TEP |
| Full **MDQ amount** for releasing shipper wrong on invoice (190k vs 200k) | Value fetched from `BLTRAN_INVOICE_DTL.ENG_QTY` (LINE_NO=2); tied to a capacity-release-with-virtual-locations collateral issue | Long-term = deploy the patch fixing release submission with virtual locations; interim = edit bills/recall releases | #1770922 / HEP 25-01059318 |

> **Key insight:** the recurring *defect family* is **rounding / duplicate-detail / grouping** in the C++ billing-detail generator (`QPipelineRoundingMgr`, invoice-sub-detail roll-up, `ComputeCalcFactor`). When a client says "the invoice/SOA/voucher don't match each other," check for a **penny rounding** difference (banker's vs half-up) first, then **duplicate detail rows**. The **overrun-credit-under-MDQ** (#1770399) and **lump-sum-prebill** (#1670549) are clean, recently-fixed logic bugs with documented workarounds.

---

## 9. Cluster F — PPA generation on billing

| Issue | Root cause | Fix / disposition | Bug / SF |
|---|---|---|---|
| **882 false PPA events** triggered by adding a time-slice to a rate (closed months end-dated with no material change) | PPA fired on a pure end-date with no value change | **Code fix** (Web) PRs 35382/35383/39610 — PPA only fires on a *true* change to closed-month dates/values. Fixed **2020.03** (+ related #204170). **Workaround:** leave the PPAs unapproved → they drop at month close | #205930 / 20-00081696 |
| Web rate **delete** doesn't generate PPAs (Classic does) | PPA triggers on Add/Modify only in Web | See §6 — end-date/zero the rate (#1745668) | #1745668 |
| **Tax PPA** not generated correctly (no reversal in tax table) — broke in v17 | `tax_basis_lv_id` was dropped from v16→v17 conversion data for a period, so reversal rows weren't created | **Code/data fix** (Sprint 68, ~2019/2020.03) — must include `tax_basis_lv_id` in any v16→v17 conversion | #116266 |
| BLH PPA charges generated then **auto-reversed without restating** | Not reproducible against a restore point; cache reset + reprocess clears it | **Rejected/blocked** (could not reproduce); logged fresh as #1725310 | #1685500 / BLH 24-00973258 |

> **Pattern:** over-triggering PPAs on no-op time-slices was a real fixed defect (#205930); the **web-delete-no-PPA** parity gap is unfixed (end-date/zero instead). "PPA reversed without restating" cases that vanish on a restore-point/cache-reset are usually **environment/cache**, not a product defect.

---

## 10. Cluster G — Invoice Group / TSP Billing Configuration

| Issue | Root cause | Fix / disposition | Bug / SF |
|---|---|---|---|
| Invoice Generation **fails** "Continue Process On Failed Execute Is FALSE" (beta/RELQA) | **Missing TSP Billing Configuration** record / no invoice group for the payment term **X10 (10th of Following Month)** | **Config:** add TSP Billing Config for the TSP eff 1/1/2020–12/31/9000 with payment term X10 and ensure an invoice group exists for X10; PR 126464 for the test/data. Fixed **2026.04 / 26.08** | #1792423 |
| Replacement contract **not linked** to invoice group after web award | See §7 — run **BLKINVGRP** | #1394171 |
| TSP Billing Config / Invoice Group / Invoice Message screen defects (Web V2UI): documents not checked after save, contact-id picklists empty, "Wire ABA Number" drops leading 0, 1000-char/1-message-per-TSP validation | Web screen/metadata defects (beta-testing finds) | Various small Web/metadata fixes, fixed in their iteration release | #1537642, #1539417, #1351096, #1627186, #1368661, #1391894, #874578 |

> **Pattern:** "Invoice Generation just fails / no invoices" with no ORA error in a fresh env is frequently a **TSP Billing Configuration / invoice-group / payment-term setup gap**, not a code bug (#1792423). The bulk of Invoice-Group/TSP-Billing items are **Web V2UI beta-testing screen defects**, fixed per release.

---

## 11. Cluster H — Invoice reports blank / duplicated / report failures

| Issue | Root cause | Fix / disposition | Bug / SF |
|---|---|---|---|
| **BLRX_00EX** (external export) report blank though invoice data exists | (1) **`IN_FOOTER_EMAIL`** param was added only to BLR_00 not BLRX_00 by an earlier footer enhancement (#1582676); (2) report defaulted invoice status to **PRE** for a past month → no data | **Metadata/code fix** PRs 86497/86583/86793/86891/86892 — add the param, **unhide** the invoice-status param (default ignored). Cherry-picked to **hotfix/17.25.7, hotfix/17.26.1, develop** | #1607181 / HPE 23-00907163 (TEP twin #1605657) |
| **Billing Invoice Documents** report blank for one month (BLRPTS_10_INVOICE_DOC_MAIN empty) | **End-dated BA Address Seq 1** for the BA; a new time-slice (seq 2) was created but contacts still pointed at the old primary BP address → insert into the report-staging table returned no rows | **Data fix:** update the contacts' Primary BP Address (Contacts Mass Change). Debug via `QARCH_QFCBATCH_SQL_TRACE` → `SQLID_INS_SEL_INVOICE_DOC_MAIN` | #1645926 / CHN 24-00942687 |
| Invoice **duplicated Nx** on BLR_00 | **Multiple invoice-copy contacts** on the invoice group → report join (`BLRPTS_00_INVOICE_CONTROL` ↔ `BLRPTS_10_INVOICE_DOC_MAIN`) emits one copy per contact | **Working as designed** — use **one copy contact** per invoice group, re-run billing. Roadmap item for multi-contact delivery | #571372 / WWM 21-00104563 |
| Invoice Documents Report **billed volume tripling** with a **sliding-scale** rate | The report view logs the *entire* set of rate-determination calculations, not just the volume the rate applied to | Duplicate of **#1733867** | #1731417 / HEP |
| Various Crystal/QGM report failures, logos, formatting, "report execution duplicate pages", PDF formatting | Report-file / metadata / Crystal issues | Per-report fixes (see Fix-Version Matrix entries) | #1731725, #1709468, #1670573, #246299/#1096182 (PPA Charge Summary) |

> **TIPS-overlap report items (DROP for QPTM — these are gathering settlement):** PROC fee shown **4×** from a one-to-many join in the *settlement statement* proc (**#220366**, ALT Harmattan), **GST line twice** on the QFAIM statement (**#235946**, TERV), **reversal fuel charge twice** in `invoice_create`/`value_core` Oracle proc (**#129305**, MFC/QGM), and **SP_QTIP_PL_STMT_RPT ORA-01722** from bad `QCTRL_ALLOC_PDA` whitespace (**#1748237**, MER — gathering invoice gen). Route these to the **TIPS Invoice/Billing** skill.

---

## 12. Cluster I — Cash-out imbalance billing (INCUVCALC)

- **Bug #1675211** (GNP/Genesis, SF 24-00967726, **Critical post-go-live**): **Rate Resolution Error — Cash Out Imbalance not tying out**, blocking shipper payments at month close.
- **Root cause:** the cash-out **unrealized-value** calculation (`INCUVCALC` step under the `ALLOC_CUV` process) lived only in **client-specific** ENT/GNP DLLs (`QPDllPipelineMgrIN_ENT`, `QPipelineMgrSharedLib_ENT`) and used a client-only table `QPTM_TRAN_AL_LAUF`. Genesis's environment couldn't run it correctly after the v17 re-implementation.
- **Fix:** large multi-PR effort to **migrate the INCUVCALC code + the `QPTM_TRAN_AL_LAUF` table into core** (PRs 100511–102459, 30+ commits) so both core and ENT/GNP can run it; interim emergency workaround was hand-built ENT DLLs dropped into the client CI (tracked on **#1675109**) — **wiped out by any intervening hotfix**, so the long-term core fix had to ship before any patch. Delivered via Genesis hotfix (~2023.04/2024 era). 
- **Escalation note:** if a client takes a hotfix *before* the core INCUVCALC fix, cash-out breaks again — verify the build contains the core migration.

---

## 13. FIX-VERSION MATRIX

> IntegrationBuild is empty on all of these; **Fixed-in** is from iteration/tags/merge-comments. **(inf)** = inferred, confirm in `Quorum.QPTM.ReleaseNotes` / the linked hotfix branch.

| Bug | Symptom (abbrev) | State | Fixed-in (release / PR) | Client / SF case |
|---|---|---|---|---|
| **#1607556** | Seq exhaustion INVOICE_INPUT_ID | Closed/Verified | core Archive-Def + client seq reset; PRs 86236/86358/87868; **2023.04 + develop** (inf) | TEP / 23-00907641 |
| **#1639324** | Seq exhaustion INVOICE_INPUT_ID/ALLOC_NO | Closed/Verified | PR 93244 + QARCHIVE setup | XCL / 24-00936702 |
| **#1728741** | Seq exhaustion INVOICE_RATE_ID | Closed/Acceptance | seq reset script; long-term gap vs #1384511/#1572396/#1600044 | XCL |
| **#1665295** | Seq exhaustion report-staging (Int32) | Closed | add to RPTS_CORE archive + RESEED | TEP / 24-00957495 |
| **#1773883** | PK_BLSTAG_INVOICE_CTR_DT on BLINVGEN | Closed | data: fix single-day contract time-slice | HPE / 25-01062471 |
| **#1633605** | Formula `&gt;` breaks BLQTYGATH | Closed/Verified | fix formula in Classic; cherry-pick web escape fix to 2021.04 | TEC / 23-00931079 |
| **#1641239** | BLINVGEN 12h on BLINVCLNUP | Closed/Rejected | no code fix; DBA stats / `NO_QUERY_TRANSFORMATION` hint | QTR / 24-00938219 |
| **#1632428** | Rate tripled on flex charges | Closed | PRs 91279–92061; **2022.10, 2023.04, develop**; QTR hotfix needs ClassicBatch 17.27.19-beta.1 | QTR / 23-00929118 |
| **#1674944** | $0.01 Header/Detail/Voucher rounding | Closed | PRs 101466–102090; iter **24.21 ≈ 2024.10** (inf) | TGL / 24-00965437, 22-00823331 |
| **#1652371** | Sub-Detail vs Header/TOS mismatch | Closed/Verified | PRs 94942–95035; early-2024 hotfix | TEP / 24-00948061 |
| **#1559943** | SOA vs Invoice Summary mismatch (penny) | Closed | ETC "Penny Mismatch"; partially backed out under #1652371 | ETC / 22-00293099 |
| **#1770399** | Overrun TOC credit under MDQ | Closed/Acceptance | PRs 121830/121895/122014; **develop, 2025.10, 2025.04** | ETC / 25-01058130 |
| **#1670549** | Lump-sum prebilled future months | Closed | PRs 102415–102417; lump-sum SQL prod_mth≤acctg_mth (~2024.10, inf) | 24-00953508 |
| **#1413101** | FTS reservation month→daily conv | Closed | PRs 63528–64484; config GROUP_BY_RATE_ID_QTY; **QPTM 2021.12** | TEP |
| **#1394171** | Repl K not in invoice group (web award) | Closed | PR 62261; **2021.10** (inf); workaround BLKINVGRP | core beta |
| **#1492803** | Repl K wrong dates (copy offer) | Closed | PR 71377; **~22.15/2022.10** (inf); USE_SEASNL_DATES gated | TEP |
| **#1655024** | PAL rates disappear (RFS Wizard) | Closed/Acceptance | PRs 95406–95567; QTR-specific (virtual PALRequestedRatesGridUpdate) | QTR / 24-00947894 |
| **#1651264** | Rate Maint duplicate error (timeslice) | Closed | PRs 95107–95173; **2023.04** hotfix (inf) | HPE / 24-00947028 |
| **#1524951** | Prelim Cashout absent from TPC invoice | Closed/Acceptance | PRs 77967/79456/79457; tier-range code (~2022.10/2023.04 inf) | TEP |
| **#1607181** | BLRX_00EX report blank | Closed | PRs 86497–86892; hotfix/17.25.7, 17.26.1, develop | HPE / 23-00907163 |
| **#205930** | False PPA events on no-op timeslice | Closed/Verified | PRs 35382/35383/39610; **2020.03** | TEC / 20-00081696 |
| **#1745668** | Web rate delete → no PPA | Closed/Acceptance | no code fix; end-date/zero the rate | HPE / 25-01025418 |
| **#116266** | Tax PPA reversal not captured (v17) | Closed | Sprint 68 (~2019/2020.03); include tax_basis_lv_id in conversion | Tauber |
| **#1675211** | Cash-out imbalance not tying (INCUVCALC) | Closed | PRs 100511–102459; ENT/GNP→core migration; Genesis hotfix | GNP / 24-00967726 |
| **#1792423** | Invoice Gen fails (Continue=FALSE) | Closed | PR 126464; config TSP Billing/X10 invoice group; **2026.04/26.08** | core beta |
| **#1430622 / #1376378** | Award wrong rate set (COM/REST) | Closed | config — Type of Charge Setup rule | core / TestRail |
| **#1631007** | "Multiple Rate IDs" rate resolution | Closed/Verified | config — overlapping location groups | QTR / 23-00927199 |
| **#1697677** | Rate Schedule picklist empty (AGDHH) | Closed/Rejected | data cleanup `QCTRL_RATE_SCH` PROD_CD | CCI / 24-00988456 |
| **#1781738** | Rate Schedule fee precision overflow (14,7) | Closed/Rejected | enhancement, will-not-fix; CCT ÷/×20 workaround | EQC / 26-01079515 |
| **#571372** | Invoice duplicated Nx | Closed/Rejected | working-as-designed; one copy contact/group | WWM / 21-00104563 |

---

## 14. Diagnostic Pointers

> SQL Server **and** Oracle clients (per-client schemas). **Verify-SELECT first; wrap DML in a transaction.** Table/column names are from repro text & code search — confirm against the client schema.

```sql
-- A. Sequence exhaustion (§5) — which QTRAN_SEQ counter is near Int32 max (2,147,483,647)?
SELECT * FROM QTRAN_SEQ      WHERE LAST_NO >= 2000000000 ORDER BY LAST_NO DESC;
SELECT * FROM QARCH_TRAN_SEQ WHERE LAST_NO >= 2000000000 ORDER BY LAST_NO DESC;
-- Reset after the staging table has purged (table must be in the short-cycle Archive Definition):
-- UPDATE QTRAN_SEQ SET LAST_NO = 1 WHERE SEQ_NM = 'BLTRAN_INVOICE_INPUT.INVOICE_INPUT_ID' AND TSP_NO = '<tsp>';
-- MSSQL identity:  DBCC CHECKIDENT('BLRPTS_10_INVOICE_DOC_IMB_DTL', RESEED, 1);

-- B. Duplicate invoice rate/detail rows (§8 tripled rate) — expect 1 row per gas day/TOC/path
SELECT ACTIVITY_DT, TOC_CD, RATE, ENG_QTY, COUNT(*) dup_ct
FROM   BLTRAN_INVOICE_SUB_DTL
WHERE  TSP_NO = <tsp> AND ACCTG_MTH = '<mth>' AND CTR_NO = '<ctr>'
GROUP BY ACTIVITY_DT, TOC_CD, RATE, ENG_QTY HAVING COUNT(*) > 1;

-- C. Rounding mismatch (§8 penny) — compare rounded vs unrounded
SELECT INVOICE_SUB_DTL_ID, ACTIVITY_DT, BASE_TRANS_AMT, BASE_TRANS_AMT_UNROUNDED,
       TAX_TRANS_AMT, TAX_TRANS_AMT_UNROUNDED
FROM   BLTRAN_INVOICE_SUB_DTL_TAX_VW
WHERE  TSP_NO = <tsp> AND ACCTG_MTH = '<mth>';
-- Reconcile SOA vs SUM report staging:
SELECT ACCTG_MTH, TSP_NO, INVOICE_GRP_ID, SUM(PPA_AMT+CURRENT_AMT) trans_amt
FROM   BLRPTS_10_INVOICE_DOC_SUM WHERE TSP_NO=<tsp> AND ACCTG_MTH='<mth>' GROUP BY ACCTG_MTH,TSP_NO,INVOICE_GRP_ID;

-- D. Report staging empty though invoice exists (§11) — is DOC_MAIN populated?
SELECT COUNT(*) FROM BLRPTS_10_INVOICE_DOC_MAIN WHERE TSP_NO=<tsp> AND ACCTG_MTH='<mth>';
-- In a DEBUG billing run, find the insert SQL:
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE STATEMENT LIKE '%INVOICE_DOC_MAIN%';  -- e.g. SQLID_INS_SEL_INVOICE_DOC_MAIN

-- E. Lump-sum prebill (§8) — pre-paid rows for future prod months
SELECT * FROM BLSTAG_INVOICE_CTR_DT WHERE TSP_NO=<tsp> AND CTR_NO='<ctr>' AND PROD_MTH > ACCTG_MTH;

-- F. "Multiple Rate IDs" (§6) — a path's locations in >1 location group / overlapping rate details
SELECT RATE_DTL_ID, EFF_DT_FROM, EFF_DT_TO, LOC_ID_1, LOC_GRP_ID_1, LOC_ID_2, LOC_GRP_ID_2
FROM   <rate detail table> WHERE RATE_HDR_ID = <rate id> AND TSP_NO = <tsp>;

-- G. Rate Schedule picklist empty (§6) — PROD_CD vs PROD_GRP_CD drift
SELECT SCH_ID, PROD_CD, PROD_GRP_CD, EFF_DT_FROM FROM QCTRL_RATE_SCH WHERE SCH_ID='<id>';
```

**Always get from the user for a batch failure:** TSP, Accounting Month, Invoice Group, Invoice Status (Pre/Final), the **PQID**, the **failing step name** (BLQTYGATH / BILINVPRE / BLINVCLNUP / Generate Documents), and the **exact ORA/COM error**. Re-run in **debug** to populate `QARCH_QFCBATCH_SQL_TRACE`.

---

## 15. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A billing **calculation** is provably wrong on correct inputs: tripled rate (#1632428), penny/rounding mismatch across screens/reports (#1674944/#1652371/#1559943), overrun-credit-under-MDQ (#1770399), lump-sum prebill (#1670549), FTS month→daily (#1413101), false PPA on no-op timeslice (#205930), cash-out not tying (#1675211).
- A **screen/validator parity** bug between Web and Classic: Rate Maintenance duplicate error (#1651264), PAL rates disappear (#1655024), web award not linking invoice group (#1394171).
- A **report** returns blank for a real reason (param/status/metadata): BLRX_00EX (#1607181).
- Provide: **PQID + failing step + exact ORA/COM error**, TSP + acctg month + invoice group, contract/Rate ID, and a repro (debug run + walkthrough). Confirm fix availability + target build in `Quorum.QPTM.ReleaseNotes` and the linked hotfix branch; many fixes are **client-specific** and require re-consuming `Quorum.QPTM.ClassicBatch` into `<CLIENT>.QPTM.ClassicBatch`.

**Handle as Cloud Ops / DBA (operational, no code):**
- **Sequence exhaustion** (§5): add the staging table to the Archive Definition, purge, reset `QTRAN_SEQ` — but **verify the client build has #1384511/#1572396/#1600044**, else it recurs (upgrade is the permanent fix).
- **BLINVGEN runaway runtime** (§4): DBA explain-plan / gather stats / `NO_QUERY_TRANSFORMATION` hint; CPU contention on segregated processes (#1364166).

**Handle as Configuration / Data (no code):**
- **TOC – Object Setup / Type of Charge Setup** rules for award rate generation (#1430622/#1376378).
- **TSP Billing Configuration / invoice-group / payment-term** gap when Invoice Gen just fails (#1792423).
- **Overlapping location groups** → "Multiple Rate IDs" (#1631007).
- **Bad contract time-slice** (single-day) → PK_BLSTAG_INVOICE_CTR_DT (#1773883); **formula `&gt;`** from web → fix in Classic (#1633605); **end-dated BA address seq** → Contacts Mass Change (#1645926); **`QCTRL_RATE_SCH`** PROD_CD drift (#1697677).
- **Web parity gaps with a config answer:** rate delete → end-date/zero the rate (#1745668).

**Handle as Expected-Behavior / Enhancement (no fix):**
- Invoice **duplicated** = multiple copy contacts (one per group) (#571372).
- Rate-schedule **fee precision** (14,7) overflow — enhancement, won't-fix; ÷/×20 CCT workaround (#1781738).
- `USE_TSP_TOS_CTR_PREFIX` for Cap Rel and web dup-fuel-rate — backlog/enhancement (#1653116, #1771559).

**DROP / re-route (TIPS, not QPTM):** settlement-statement one-to-many fee joins (#220366), QFAIM statement GST-twice (#235946), `invoice_create`/`value_core` reversal-twice (#129305), `SP_QTIP_PL_STMT_RPT` gathering invoice (#1748237). These belong to the TIPS Invoice/Billing skill.

---

*Skill created: 2026-06-14. Source: ADO QPTM Bugs (Closed/Resolved), areas Energy Transportation + Maintenance\Midstream and Transportation, Billing/Invoice/Rates. 732 WIQL matches (~600 QPTM-relevant after dropping TIPS/QLNG), 47 deep-read. IntegrationBuild empty on all — fixed-in-release inferred from iteration path (YY.NN), QA/release tags, and merge comments; confirm in Quorum.QPTM.ReleaseNotes. Companion: SKILL_ADO_QPTM_* (other functional areas), REPO_INVENTORY, CONFIG_REFERENCE.*
