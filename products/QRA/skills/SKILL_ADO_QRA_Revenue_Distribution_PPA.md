# SKILL: QRA Revenue Distribution / PPA — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps bugs (Closed/Resolved) under Area Path `QuorumSoftware\Engineering\Financials` | **Product:** Quorum Upstream Accounting — **QRA** (Revenue Accounting), with the **JIB owner/property allocation** engine that physically performs revenue/cost distribution (lives in QCA Cost Accounting).

**Use When:** an Upstream client reports a revenue-distribution / owner-allocation / property-allocation / JIB billing / suspense-release / prior-period (PPA/rebill) problem and you need to know *(a)* whether it is a known product defect, *(b)* the root cause and the fix, and *(c)* whether the client's build already contains the fix. This is an **ADO-mined** companion to the SF-case skills — every claim below cites a real ADO Bug # observed during mining.

> **CRITICAL SCOPE / OVERLAP NOTE.** My assigned slice is "QRA / Revenue_Distribution_PPA," but the actual **defect mass for revenue/cost distribution in the Financials area lives in JIB (Joint Interest Billing)** — Owner Allocation, Rebill Owner Allocation, Property Allocation, Prepare-JE/Invoice splitting — which is built in the **QCA Cost-Accounting** repos (`Quorum.Upstream.QCA.ClassicBatch`, `Quorum.Upstream.QCA.Database`), not QRA. Pure **QRA-branded** bugs are comparatively few and skew toward **Exago reports, BA/1099 setup, GL/voucher staging into QCFS, and check-write/suspense**, and a large share of those are **Rejected / Duplicate / config**, not code. Both families are documented here; each section is labelled with the owning module. Treat "QRA revenue distribution" symptoms as *first* a JIB-allocation question.

> **Evidence base:** WIQL over Financials Bugs (Closed/Resolved) whose title contains revenue / VL100 / BKRVNU / RDCALC / PPA / prior period / contractual allocation / market group / owner pay / SOD / suspense / impairment (+ a tighter QRA pass adding QRA / owner allocation / JIB / suspense / royalty / severance / distribution). The broad title filter is *noisy*: most title-matches are QCFS/QCA **attachment, ACH, AFE, document-management, and AP-voucher GL-distribution UI** bugs that are unrelated to QRA revenue — those are excluded here. ~36 bugs deep-read across the clusters below.

---

## TABLE OF CONTENTS
1. [Quick Triage](#1-quick-triage)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Owner/Rebill Allocation child-split count (too many / one too few children)](#4-cluster-a)
5. [Cluster B — Owner Allocation memory exhaustion (32-bit QPEC / $0 explosion / rebill-to-inception)](#5-cluster-b)
6. [Cluster C — Property Allocation split datatype (1 child short)](#6-cluster-c)
7. [Cluster D — Owner-Allocation correctness: $0-exclude, Hold status, prepayment](#7-cluster-d)
8. [Cluster E — QRA Exago / Close-Summary reports](#8-cluster-e)
9. [Cluster F — QRA setup / BA / 1099 / GL revenue-account / suspense labels](#9-cluster-f)
10. [Cluster G — QRA→QCFS GL & voucher staging (revenue not hitting GL/AR)](#10-cluster-g)
11. [Cluster H — JIB netting / I-C invoices / check-write to QRA](#11-cluster-h)
12. [Cluster I — JIB DOI / direct-bill / JB005 process-sequence](#12-cluster-i)
13. [Fix-Version Matrix](#13-fix-version-matrix)
14. [Diagnostic Pointers (SQL & tables)](#14-diagnostic-pointers)
15. [Escalation Guidance](#15-escalation-guidance)
16. [Repos & Code Map](#16-repos--code-map)

---

## 1. Quick Triage

| Symptom (what the user/QA reports) | Likely cluster | First check |
|---|---|---|
| JIB process launches **way more child jobs than needed** ("warning: too many children"), most do nothing | **A** | Split stored procs `USP_JIB_*_SPLIT`; child count vs `PROC_GRP_SEQ_NO` stamping |
| **Owner Allocation throws Out-of-Memory / memory exception** on a child job | **B** | JIB slice config (`SUGG_SLICE_*`), `JBCDE_BUSINESS_SEGMENT` metadata profile, $0/rebill-to-inception blow-ups |
| **Property Allocation processes one less child** than expected | **C** | `QPSJIBPropAllocSplitter.cpp` long-vs-double cast (fixed) |
| Owner allocation **writes a $0 OA-exclude record** / **billing status shows N instead of H** / prepayment **rogue transactions** | **D** | OA exclude/hold logic; prepayment subledger (often data/cancelled-archive collateral) |
| **QRA Exago report wrong/blank** (Revenue Close Summary, Closing Summary, Income Analysis) | **E** | Report formula (`TRIM` on close-status), env Exago connection setup |
| **BA005 1099 checkbox ≠ DB** / GL013 revenue account exception / BA JIB **suspense labels duplicated** | **F** | Config (1099 address-level), code-gen validation message, label-to-column wiring |
| **QRA revenue data in `STRAN_*` not reaching the GL / AR** after import cycle | **G** | `QCFSIMPCYC` / batch creation in QCFS; usually REV-side script, verify before escalating |
| JIB invoices **not tying to QCFS**, I/C offset / "Could Not Post" GL-distribution error | **H** | Offset/control account setup (MINRLSE), custom code-block import |
| JB020 "not an effective JIB DOI" on a valid record; JB005 process sequence/rolling errors | **I** | DOI effective-date validation; JB005 process-step list / `m_INS_SEXT_C` save |

---

## 2. Pipeline & Concepts

```
[AP Vouchers / Journal Entries booked to a PROPERTY with a JIB DOI]
      │
      ▼  COST SUBLEDGER LOAD (JBTRN_COST_SUBLEDGER)
      ▼  PROPERTY ALLOCATION  (split: QPSJIBPropAllocSplitter; AL = allocation-type property)
      ▼  OWNER ALLOCATION  (JBOWNALLOC → JBOAMAIN → JBOACHILD child jobs; JBTRN_OWNER_ALLOC)
      ▼  REBILL OWNER ALLOCATION  (JBREBILL — reverses & re-bills prior periods = the "PPA"/prior-period path)
      ▼  PREPARE JE / MIN-HOLD  (JBJEMINHLD; JBTRN_PREPARE_JE; BILLING_STATUS H=Hold/N/R=Rebill)
      ▼  INVOICE PREPARATION  (JBINVMNPRC; JBSTG_INVOICE)
      │
      ├──► QCFS  (AR invoices, GL — QRA/JIB results post via QCFSIMPCYC / batches)
      └──► QRA   (revenue distribution, check-write, suspense, Exago Close reports)
```

### Key terms
- **JIB** = Joint Interest Billing. The engine that **distributes** booked property charges down to owners (Owner Allocation) and rebills prior periods (Rebill Owner Allocation). It is the de-facto revenue/cost **distribution** engine; built in **QCA**, consumed by QRA/QCFS.
- **Owner Allocation (JBOWNALLOC / JBOAMAIN / JBOACHILD)** — splits property-level amounts to interest owners. Runs as a **master + child jobs** on QPEC; child count is determined by **split stored procedures**.
- **Rebill Owner Allocation (JBREBILL)** — reverse + re-bill prior periods. This is the **prior-period adjustment (PPA / rebill)** path. "Rebill back to inception" is the classic memory-blowup trigger (Cluster B).
- **Property Allocation** — allocates to the property/AL level before owner allocation. **AL** = allocation-type property; `PROPERTY_TYPE='AL'`.
- **Split stored procs** — `USP_JIB_PREPARE_JE_SPLIT`, `USP_JIB_STAGE_INVOICE_SPLIT`, `USP_JIB_OWNER_ALLOC_STAGE_SPLIT`, `USP_JIB_PRE_JOURNAL_SPLIT`, helper `USP_CALC_SPLIT_VALUES_BY_KEY`. They stamp `PROC_GRP_SEQ_NO` and return the **# of child jobs** to launch.
- **Slice config** — `JB_OWNERALLOC#SUGG_NO_QPEC`, `SUGG_SLICE_MAX_SIZE`, `SUGG_SLICE_MIN_SIZE`, `QPEC_MASTER_PROCESS#CONCURRENT_CHILD_PROCESS_LIMIT_JBOACHILD`. Lives in `QARCH_CNFG_CTRL` (layered: core / ENV / client — **never edit the core layer in a client env**).
- **BILLING_STATUS** on `JBTRN_OWNER_ALLOC` / `JBTRN_PREPARE_JE`: `H` = Hold, `N` = normal, `R` = rebill. Hold is set in the `QPSJIBOAPreJEMinHld` step.
- **PPA (here)** = prior-period adjustment via Rebill — *not* the TIPS "PPA" plant-product allocation. Don't confuse with TIPS skills.
- **QRA Exago reports** — Revenue Close Summary / Closing Summary / Income Analysis, driven by views like `QRA_CLOSE_CALENDAR_VW`, table `GONL_ACCTG_MTH` (`ACCTG_CLOSE_STATUS_CD`).
- **QPEC** = the batch processing engine (child job executor). Memory limits matter because the classic batch is **32-bit** (Cluster B).

---

## 3. Decision Tree

```
QRA / revenue-distribution case
│
├─ Is a BATCH PROCESS misbehaving (Owner/Rebill/Property Allocation, Invoice Prep)?
│   ├─ Too many child jobs / "too many children" warning  → §4 (split-proc count: USP_JIB_*_SPLIT)
│   ├─ Out-of-memory / memory exception on a child        → §5 (slice config + JBCDE metadata profile; rebill-to-inception / $0 explosion)
│   ├─ One child too FEW (property alloc)                  → §6 (QPSJIBPropAllocSplitter long-vs-double — fixed 22.06)
│   └─ Wrong OUTPUT (status/exclude/prepayment), not a crash → §7
│
├─ Is it a QRA REPORT?  → §8 (Exago: trailing-space close status; missing env connection — usually report/config, not engine)
│
├─ Is it SETUP / SCREEN (BA005 1099, GL013 revenue acct, BA suspense labels)?  → §9 (config or validation-message; many Rejected)
│
├─ Did revenue data NOT reach GL / AR / QCFS?  → §10 (QCFSIMPCYC batch creation; usually REV-side script — verify before code)
│
├─ JIB not tying to QCFS / I-C "Could Not Post" / check-write to QRA?  → §11 (offset/control account setup)
│
└─ Can't save DOI / JB005 sequence / rolling error?  → §12
```

---

## 4. Cluster A — Owner/Rebill Allocation child-split count (too many children) — **JIB / QCA**

**Symptom:** A JIB allocation process (Owner Allocation `JBOWNALLOC`, Rebill `JBREBILL`, or Invoice Prep `JBINVMNPRC`) launches **far more child jobs than there is work for** — e.g. *25 unique groups stamped but 163 child jobs launched, most doing nothing* — sometimes raising a "too many children" warning. Performance and QPEC contention suffer.

**Root cause:** The split stored procedures sized the child count purely from **total record count ÷ recommended chunk size** (e.g. 4,053,411 ÷ 25,000 = 163) but the work is then **grouped by `BA_NO`/`BA_SUB`** which must stay together. A single large BA throws the real group count far below the naive split count. The fix uses **`SEQ_NO % @I_GRP_CNT`** to stamp `PROC_GRP_SEQ_NO` reliably and **returns the true group count** from `USP_CALC_SPLIT_VALUES_BY_KEY`.

**Fix:**
- **#1367134** (Closed, it 21.18) — "170 - Rebill Owner Allocation — Split procedures bug fixes": corrected `USP_JIB_PREPARE_JE_SPLIT` and `USP_JIB_STAGE_INVOICE_SPLIT` to return the correct split count (comments-only cleanup of `USP_JIB_EXPORT_VALIDATION`, `USP_JIB_PRE_JOURNAL_SPLIT`). PRs 54934 / 57026 / 57770.
- **#1416291** (Closed, it 22.03) — "JBREBILL and JBOWNALLOC Child Split Stamping — `USP_JIB_OWNER_ALLOC_STAGE_SPLIT`": ported the same `1 + SEQ_NO % @I_GRP_CNT` stamping + `RETURN(@I_GRP_CNT)` pattern to the owner-alloc split proc (called from `QPSJIBOwnerAllocationMain.cpp`, step `JBOAMAIN`). PR 65240. *Tags note it was NOT auto-ported to 2024.10/2025.04 — verify on those trains.*
- **#1367142** (Closed, it 21.14) — related Rebill temp-table fix (see §5).
- **#1389411** (**Rejected**) — proposed adding `PROCESS_QUEUE_ID` to a sub-select in `QSQL_JIBOwnerAllocation.cpp` (`m_SEL_OwnerAllocStageSvcDt`) to keep the temp table from "exploding"; not actioned.

**Workaround:** none clean; the proc fix is the answer. If on an old build, confirm the env has the **latest version of `USP_JIB_OWNER_ALLOC_STAGE_SPLIT` / `USP_JIB_STAGE_INVOICE_SPLIT`** (Jimmy Bidwell noted NWD v17 still had the *old* syntax). Compare proc text in `Quorum.Upstream.QCA.Database` against the client schema.

**Bug IDs:** #1367134, #1416291, #1367142 (related), #1389411 (rejected). **Linked SF:** none stated (internal stress-testing items).

---

## 5. Cluster B — Owner Allocation memory exhaustion (32-bit QPEC) — **JIB / QCA**

**Symptom:** Owner Allocation (or Rebill) **child job dies with an Out-of-Memory / memory exception**; classic case throws on the first `.InsertEmptyRow()` after ~3.4 GB.

**Root causes seen (two distinct):**
1. **Mis-sized / single child job due to bad metadata** (#129108, Closed/Verified): the real cause was **`JBCDE_BUSINESS_SEGMENT` pointing at the wrong metadata profile** (should be `QCCI` for CCI) — so the split config wasn't read and **only one child job launched**, loading everything into one 32-bit QPEC. **Fix = correct the `METADATA_PROFILE` in `JBCDE_BUSINESS_SEGMENT`** (config, not code). Raising `SUGG_SLICE_MAX_SIZE` 1000→2000 did **not** help and was explicitly *not* recommended.
2. **Genuine data volume blow-up** (#1368892, Closed it 21.18; #1697053 PNR): **rebill back to inception** on many wells × few owners creates **millions of transactions**, ~70% of them **$0**, exhausting the 32-bit process. Mitigations: set global config `JBINVOICES#JBTRN_INVOICE_DETAIL = ADOBATCH`; lower the slice size; and the **suppress-$0** enhancement (#1575653) so $0 invoices/OA rows aren't created.

**Fix / availability:**
- #129108 — config fix (metadata profile); no build.
- #1368892 — split/handling fixes (it 21.18).
- #1697053 (**Rejected**) — request to **port-back** JIB perf/memory improvements (#1329945, #1575653 $0-suppression, #1674444/#1668557/#1671175/#1673334 split-length, #1669718/#1669716/#1669632) to **Pioneer v16**. Engineering declined a full port-back as throwaway work for a client with no upgrade plan; only **#1703886** was delivered via Patch. **Lesson:** the perf/memory fixes exist in current trains (≈v17 / 2021.10+); old-build clients get one-off patches, not the full set.

**Workaround:** (a) verify `JBCDE_BUSINESS_SEGMENT` metadata profile first; (b) lower `SUGG_SLICE_MAX_SIZE` and raise `SUGG_NO_QPEC` so each child loads less; (c) set `JBTRN_INVOICE_DETAIL=ADOBATCH`; (d) avoid rebill-to-inception on huge well sets — scope the rebill period.

**Bug IDs:** #129108, #1368892, #1697053 (rejected port-back), related #1575653 / #1329945. **Linked SF:** PNR (Pioneer) memory failures referenced in #1697053; no SF # in title.

---

## 6. Cluster C — Property Allocation split datatype (one child short) — **JIB / QCA**

**Symptom:** Property Allocation **processes one fewer child record than it should** (e.g. expected 8 splits, got 7); a sliver of cost-subledger lines never allocate.

**Root cause:** In **`QPSJIBPropAllocSplitter.cpp`**, the split-count variable was changed to **`long`** during the datatype upgrade (to allow identity values above INT). Dividing a `long` by an `int` truncated *before* the `ceil()`, so `ceil(records/chunk)` rounded **down**: e.g. value that should round to 8 came out 7. **Fix = revert that variable to `double`** so `ceil` rounds correctly.

**Fix:** **#1446592** (Closed, it 22.06) — PRs 67695 / 67696 / 67697, fix script `1446592_InsertCtfData.sql`. Engineering flagged this as a notable bug to also fix directly in client v16 branches (Pioneer/PNR) ahead of GA — so a client on a custom older branch may need the cherry-pick confirmed.

**Workaround:** none; it is a precision bug. Re-run property allocation after the fix.

**Bug IDs:** #1446592. **Linked SF:** none (found in stress testing).

---

## 7. Cluster D — Owner-Allocation correctness: $0-exclude, Hold status, prepayment — **JIB / QCA**

| Issue | Root cause | Fix / state | Bug | SF |
|---|---|---|---|---|
| Owner Allocation still writes an **OA-exclude record for a $0-resolved owner** even after $0-suppression was added | #1575653 stopped writing the OA row but **`InsertNewOwnerExclude()`** still wrote the exclude row; same $0 check needed before writing exclude | **Code fix** (Closed, it **25.06**); PR 108014 + commit | #1716693 | — |
| **JB330 billing status shows `N` instead of `H` (Hold)** after Owner Allocation | Hold is set in `QPSJIBOAPreJEMinHld` by selecting `JBTRN_OWNER_ALLOC` where `SPECIAL_HANDLING_ID NOT IN (2,3,4)`, `DEL_INT_OWNR_FLAG<>'Y'`, `PREPAY_IND='N'`; for the QA record the criteria legitimately excluded it. Largely a **test-data / test-case** issue, not a confirmed engine defect | Closed it **23.06** (regression test item) | #1589739 | — |
| **Prepayment subledger creating "rogue" transactions** during JIB (JB330/JB340 don't tie; a 3/1 entry "from the GL" not in the JE) | Collateral of a **cancelled archive job** re-importing old data (Update Date matched the bad import date) | **Duplicate** of #1657661 (scripts tracked there); not a standalone code fix | #1659695 | 24-00953070 |

**Key insight:** the one clear *code* defect here is **#1716693** ($0 exclude-row written despite $0-suppression) — fixed 25.06. The Hold-status and prepayment items resolved as test-data / cancelled-archive collateral. When a client says "owner allocation results look wrong," separate **(a) a genuine $0/exclude/Hold logic bug** from **(b) a re-import / cancelled-job data artifact** before escalating.

**Bug IDs:** #1716693 (code, 25.06), #1589739 (test-data, 23.06), #1659695 (dup → #1657661). **Linked SF:** 24-00953070.

---

## 8. Cluster E — QRA Exago / Close-Summary reports — **QRA (report layer)**

| Issue | Root cause | Fix / state | Bug | Train |
|---|---|---|---|---|
| **Revenue Close Summary** report always shows "Booking Closed? = Yes" | `GONL_ACCTG_MTH.ACCTG_CLOSE_STATUS_CD` stores **`'O '`/`'C '` with a trailing space**; formula `=IF({...BOOKING_CLOSE_CD}='O',...)` never matched | **Report fix**: wrap in `TRIM(...)` (Closed, it 22.08, tag 2022.04 QA); PRs 68280/68580 | #1449118 | 2022.04 |
| Revenue Close Summary throws **DBConnect Exception** on Run | Test env was **missing the `QRAExagoDataHelper` connection setup** ("we never released QRA with Exago support, so it missed the post-refresh process") | **Env/config** — add the connection in a maintenance window (Closed, it 21.22) | #1404377 | env-only |
| QRA **Income Analysis Report (RPT_ESR015)** fails — "Could not create report" | (report repository/setup) | Closed, it 21.12 (tag 2021.09) | #1355530 | 2021.09 |
| QRA **Revenue Closing Summary** report issue | report | Closed | #1449118 (same family) | |

**Key insight:** QRA report defects are **report-formula / env-connection** issues, not revenue-engine bugs. Check for **trailing-space comparisons** (`TRIM`) and **missing Exago connection setup** in the target environment before suspecting the data.

**Bug IDs:** #1449118, #1404377, #1355530. **Linked SF:** none in titles.

---

## 9. Cluster F — QRA setup / BA / 1099 / GL revenue-account / suspense labels — **QRA / Core setup**

| Issue | Root cause | Fix / state | Bug |
|---|---|---|---|
| **BA005 1099 checkbox ≠ `QCTRL_BA_ADDRESS_QRA.BA_1099_IND`** | The 1099 indicator must be **enabled at the address level**; once address-level config was enabled it matched | **Rejected / config** ("working as expected after enabling address-level config") | #1096612 |
| **GL013 — application exception when adding a revenue account** | Code-gen validation throws a raw exception when required fields (e.g. **QRA Code Type**, only required when "Visible to QRA" is checked) are blank — screen can't pre-validate without duplicating code-gen rules | **Code fix** to surface a friendlier message (Closed, it 23.07); PRs 83021/83028. Screen `QFrmUpstreamFD_AccountMaintenance` | #1588160 |
| **BA Address → JIB tab: min/max suspense labels duplicated/wrong** (Web vs Classic) | Web labels for *Minimum Suspense — Normal/Rebill* were duplicated and not tied to the right `JBONL_BA_ADDRESS_JIB` columns | **Code fix** (Closed, it 24.07); PRs 95328/95331/95409 | #1653282 |
| QRA classic screen popup / process types not visible on **QP043** | QRA classic process-launcher screen | Closed, it 25.12 (tag not 2026.04 Ups) | #1733284 |
| QRA Event DLL not updated by **QUpdater** | deploy/updater issue | Closed, it 21.15 (Debt/Untestable) | #1360293 |
| **PII obfuscation sanitization scripts failed for entire QRA database** (invalid column) | bad column ref in the sanitization script | Closed/Verified, it 25.16 | #1745028 |
| `USP_TRUNCATE_JBTRN_JIB_JOURNAL` **missing during 2025.04 deployment** | deployment packaging gap | Closed/Verified, it 25.16 | #1746136 |

**Key insight:** this cluster is mostly **config (1099 address-level), validation-message polish, label-to-column wiring, and deployment/updater gaps** — low-risk, train-tagged. The 1099 mismatch (#1096612) is the classic "looks like a defect, is actually config."

**Bug IDs:** #1096612 (rejected/config), #1588160 (23.07), #1653282 (24.07), #1733284 (25.12), #1360293 (21.15), #1745028/#1746136 (25.16).

---

## 10. Cluster G — QRA → QCFS GL & voucher staging (revenue not hitting GL/AR) — **QRA/QCFS boundary**

**Symptom:** QRA revenue data sits in **`STRAN_CORE_INTFC` / `STRAN_*`** but **never appears in the GL** (and/or AR) after the import cycle; "QRA vouchers missing data."

**Root cause / disposition:** **#1422077** ("QRA Vouchers Missing Data — CO 200 Nov 2021", SF **22-00217199**) was driven from `QCFSIMPCYC` not creating a QCFS batch for some STRAN records. After investigation it was **only an issue on the REV side** — Engineering verified STRAN records *did* reach GL and AR after re-stage, and the case was **Rejected** (no core code change). A restage **script** was the contingency if needed.

**Key insight:** "revenue in STRAN but not in GL" is **usually a REV-side staging/script issue**, not a core defect. **Verify the STRAN→GL→AR path with the diagnostic SELECTs (below) and rule out a missing QCFS batch before escalating.** Engineering's pattern here is to re-stage, not to patch.

**Bug IDs:** #1422077 (Rejected). **Linked SF:** 22-00217199.

---

## 11. Cluster H — JIB netting / I-C invoices / check-write to QRA — **JIB ↔ QCFS/QRA**

| Issue | Root cause | Fix / state | Bug | SF |
|---|---|---|---|---|
| **JIB invoices not tying to QCFS** (AR076/AR085/AR173 wrong) | The **MINRLSE→MINRLSE offset account** was set up as a **Control Account** in QCFS, which **blocks imports**; needed a proper **JIB AR Suspense** offset account | **Rejected** (setup recommendation — find/create a JIB AR Suspense account, fix offset on the event/keyword) | #106653 | — |
| **JIB netting — JE Post button disabled** on JE100 (expected enabled) | Test-env config: `OIEXPORT` not set up for all business units; after config, export-to-QRA + pre-checkwrite worked but JE100 query still empty — **test-case/data** issue, left for re-review | Closed it 23.16 (regression test item, no clear code fix) | #1589796 | — |
| **I/C invoices "Could Not Post" — GL distribution / account error** | Collateral from #1547557; custom code-block rows for I/C offset lines + ADP import file placement | **Code fix** (Closed it 23.21); related to ADPUPLOAD staging | #1625232 | — |

**Key insight:** the "not tying" / netting items are dominated by **offset/control-account setup** (MINRLSE → JIB AR Suspense) and **import file placement**, not engine math. Check the **event/keyword offset account** and whether it is a QCFS **Control Account** (which blocks import) first.

**Bug IDs:** #106653 (rejected/setup), #1589796 (23.16 test-data), #1625232 (23.21 code). **Linked SF:** none in titles.

---

## 12. Cluster I — JIB DOI / direct-bill / JB005 process-sequence — **JIB / QCA**

| Issue | Root cause | Fix / state | Bug |
|---|---|---|---|
| **JB020 "not an effective JIB DOI"** validation error on a valid record | DOI effective-date validation rejecting a record whose process period/accounting date matched the current JB005 period | **Code fix** (Closed, it 21.18, tag 2021.10 QA); PR 57865 | #1382019 |
| **Direct Bill not supported for Property-Allocation properties** | When direct-billing to an AL (property-allocation) property the specified owner is **not carried through** owner allocation; no validation blocks it | **Rejected** ("Recommend Close") — treated as unsupported behavior / enhancement, not a fixed defect | #1638771 |
| **JB200 Allocation Definition — hidden, required field** blocks save | screen metadata (required field hidden) | Closed, it 26.05 (QA Approved SUP) | #1782975 |
| JB005 **process sequence changed / not same as CORE_SUP**; new JIB process added | 2024.10 JIB process re-sequencing | Closed it 24.21 (Rejected — expected for new flow) | #1685018 |
| JB005 **rolling error** (long-term fix) | rolling of the Process-of-JIB screen | Closed it 25.12 | #1725253 |
| JB005 **Initiate Billing Cycle failing** — error in registered SQL `m_INS_SEXT_C...` / Finalize-and-Post failing | save/registered-SQL defects in the JB005 flow | #1793723 (Closed it 26.07); #1684125 (Finalize & Post fail, Closed it 24.18) | #1793723, #1684125 |

**Key insight:** **Direct-bill to a property-allocation (AL) property is effectively unsupported** (#1638771 rejected) — set that expectation. Genuine JB005 code fixes (DOI validation #1382019; Initiate-Billing SQL #1793723; Finalize/Post #1684125) are train-tagged.

**Bug IDs:** #1382019 (21.18), #1638771 (rejected), #1782975 (26.05), #1685018 (24.21), #1725253 (25.12), #1793723 (26.07), #1684125 (24.18).

---

## 13. Fix-Version Matrix

> **Build-train mapping (from iteration paths + release tags observed):** Quorum Upstream uses 2-week sprint iterations `YY.NN` that roll into yearly release trains. Tag evidence: `21.18`→"2021.10 QA"; `22.08`→"2022.04 QA"; `23.x`→"2023.04"; `24.18/24.21`→2024.10; `25.06/25.12/25.16`→2025.04; `26.05/26.07`→2026.04. **No `Microsoft.VSTS.Build.IntegrationBuild` value was populated on any of these bugs** — fixed-in is inferred from the **iteration path / release tag**, so confirm the exact build/patch in the Upstream release notes before quoting it to a client.

| Bug | Symptom | State / Reason | Fixed-in (iteration → train) | Repo / artifact | SF case |
|---|---|---|---|---|---|
| #1367134 | Rebill/Owner alloc split count too high | Closed / RFQA | 21.18 → 2021.10 | QCA.Database (`USP_JIB_PREPARE_JE_SPLIT`,`USP_JIB_STAGE_INVOICE_SPLIT`) PR 54934/57026/57770 | — |
| #1367142 | Rebill temp-table created twice | Closed / RFQA | 21.14 → 2021.10 | QCA.ClassicBatch `QPSJIBRebillReversal.cpp` PR 54992 | — |
| #1416291 | Owner-alloc split stamping (`% I_GRP_CNT`) | Closed / RFQA | 22.03 → 2022.04 | QCA.Database `USP_JIB_OWNER_ALLOC_STAGE_SPLIT` PR 65240 (**not auto-ported to 2024.10/2025.04**) | — |
| #1389411 | sub-select missing PROCESS_QUEUE_ID | **Rejected** | — | (not actioned) | — |
| #129108 | OOM Owner Allocation (1 child) | Closed / Verified | config fix (Sprint 65) | `JBCDE_BUSINESS_SEGMENT` metadata profile | — |
| #1368892 | OOM Rebill child jobs | Closed / RFQA | 21.18 → 2021.10 | QCA (slice/handling) | — |
| #1697053 | port-back JIB perf to PNR v16 | **Rejected** | only #1703886 via Patch | — | PNR |
| #1446592 | Property alloc 1 child short | Closed / RFQA | 22.06 → 2022.04 | QCA.ClassicBatch `QPSJIBPropAllocSplitter.cpp` (long→double) PR 67695-7 | — |
| #1716693 | $0 OA-exclude row written | Closed / RFQA | **25.06 → 2025.04** | QCA `InsertNewOwnerExclude()` PR 108014 | — |
| #1589739 | JB330 status N not H | Closed / RFQA | 23.06 → 2023.04 (test-data) | `QPSJIBOAPreJEMinHld` | — |
| #1659695 | prepayment rogue txns | Closed / **Duplicate** (#1657661) | — | data/script | 24-00953070 |
| #1449118 | Rev Close Summary always "Yes" | Closed / RFQA | 22.08 → 2022.04 | Exago `QRA_CLOSE_CALENDAR_VW` TRIM PR 68280/68580 | — |
| #1404377 | Rev Close Summary DBConnect err | Closed / RFQA | 21.22 (env) | add `QRAExagoDataHelper` connection | — |
| #1355530 | Income Analysis RPT_ESR015 fail | Closed / RFQA | 21.12 → 2021.09 | report repo | — |
| #1096612 | BA005 1099 ≠ DB | Closed / **Rejected** (config) | — | enable address-level 1099 config | — |
| #1588160 | GL013 revenue-acct exception | Closed / RFQA | 23.07 → 2023.04 | `QFrmUpstreamFD_AccountMaintenance` PR 83021/83028 | — |
| #1653282 | BA JIB suspense labels duplicated | Closed / RFQA | 24.07 → 2024.10 | Web BA address-JIB labels PR 95328/95331/95409 | — |
| #1422077 | QRA revenue STRAN→GL missing | Closed / **Rejected** (REV-side) | — | restage script | 22-00217199 |
| #106653 | JIB invoices not tying to QCFS | Closed / **Rejected** (setup) | — | MINRLSE offset → JIB AR Suspense acct | — |
| #1589796 | JIB netting JE Post disabled | Closed / RFQA | 23.16 (test-data) | OIEXPORT config | — |
| #1625232 | I/C invoices Could-Not-Post | Closed / RFQA | 23.21 → 2023.04 | ADPUPLOAD / custom code-block | — |
| #1382019 | JB020 "not an effective JIB DOI" | Closed / RFQA | 21.18 → 2021.10 | DOI eff-date validation PR 57865 | — |
| #1638771 | Direct-bill to property alloc | Closed / **Rejected** (unsupported) | — | — | — |
| #1782975 | JB200 hidden required field | Closed / Acceptance | 26.05 → 2026.04 | screen metadata | — |
| #1685018 | JB005 process sequence changed | Closed / **Rejected** (expected) | 24.21 | — | — |
| #1725253 | JB005 rolling error long-term | Closed / RFQA | 25.12 → 2025.04 | — | 25-01013387 |
| #1684125 | JB005 Finalize & Post fail | Closed / RFQA | 24.18 → 2024.10 | — | — |
| #1793723 | JB005 Initiate Billing SQL fail | Closed / RFQA | 26.07 → 2026.04 | registered SQL `m_INS_SEXT_C` | — |
| #1745028 | QRA PII sanitization script fail | Closed / Verified | 25.16 → 2025.04 | sanitization script | — |
| #1746136 | `USP_TRUNCATE_JBTRN_JIB_JOURNAL` missing deploy | Closed / Verified | 25.16 → 2025.04 | QCA.Database deploy | — |

---

## 14. Diagnostic Pointers

> SQL Server (Upstream is MSSQL: `*_HD_UPS_*`, `*UPS_QCA` DBs). Verify table/column names against the client schema; run SELECTs before any write.

```sql
-- A. Child-split mismatch (§4): groups stamped vs child jobs launched
SELECT PROC_GRP_SEQ_NO, COUNT(*) FROM JBTRN_PREPARE_JE        -- or JBSTG_OWNER_ALLOC / JBSTG_INVOICE
WHERE PROCESS_QUEUE_ID = <master_pqid> GROUP BY PROC_GRP_SEQ_NO ORDER BY PROC_GRP_SEQ_NO;
SELECT PROCESS_QUEUE_ID, PROCESS_ID, PARAM_DESCR_LIST FROM QARCH_QUEU_PROCESS
WHERE MASTER_PROCESS_QUEUE_ID = <master_pqid> AND PROCESS_ID IN ('JBOACHILD','JBJEMINHLD') ORDER BY PROCESS_QUEUE_ID DESC;

-- B. OOM root cause (§5): did only ONE child launch? + verify metadata profile
SELECT CHILD_PROCESS_COUNT, * FROM QARCH_QUEU_PROCESS WHERE PROCESS_ID IN ('JBOWNALLOC','JBREBILL') ORDER BY QUEUE_DT DESC;
SELECT METADATA_PROFILE, * FROM JBCDE_BUSINESS_SEGMENT;     -- e.g. CCI must be QCCI
SELECT * FROM QARCH_META_MOD_DEFINE WHERE METADATA_PROFILE = '<profile>';
-- slice config (note the LAYER — never edit core in a client env):
SELECT USER_ID, UPDT_DT, * FROM QARCH_CNFG_CTRL WHERE KEY_NM LIKE '%SUGG%' AND KEY_GRP_NM LIKE 'JB%' ORDER BY UPDT_DT DESC;

-- D. Owner-alloc Hold logic (§7): why a row didn't get H
SELECT OA_ID, BA_NO, BA_SUB, BILLING_STATUS, BILLING_OWNER_AMOUNT, SPECIAL_HANDLING_ID, DEL_INT_OWNR_FLAG, PREPAY_IND
FROM JBTRN_OWNER_ALLOC WHERE PROCESS_PERIOD = '<yyyy-mm-01>' AND SYSTEM_SOURCE = 'OA' ORDER BY BA_NO;
-- Hold expected when SPECIAL_HANDLING_ID NOT IN (2,3,4) AND DEL_INT_OWNR_FLAG<>'Y' AND PREPAY_IND='N'

-- E. Exago Rev Close Summary trailing space (§8)
SELECT ACCTG_CLOSE_STATUS_CD, LEN(ACCTG_CLOSE_STATUS_CD) FROM GONL_ACCTG_MTH;  -- 'O '/'C ' -> formula needs TRIM

-- F. 1099 mismatch (§9)
SELECT BA_1099_IND, * FROM QCTRL_BA_ADDRESS_QRA WHERE BA_NO LIKE '%<owner>%';
SELECT * FROM JBONL_BA_ADDRESS_JIB;   -- suspense label-to-column wiring (#1653282)

-- G. QRA revenue STRAN -> GL/AR (§10)
SELECT * FROM STRAN_CORE_INTFC WHERE PROCESS_QUEUE_ID = <qcfsimpcyc_pqid>;  -- in STRAN but no GL batch = REV-side restage

-- Long-running SQL trace for any JIB process
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = <pqid> ORDER BY DURATION_MSEC DESC;
```

**Always capture:** the JIB process step (JBOWNALLOC / JBREBILL / JBOAMAIN / JBOACHILD / JBINVMNPRC), the **master** Process Queue ID (not a child's), and the exact error.

---

## 15. Escalation Guidance

**Is it fixed in the client build?** All fixed-in versions in this skill are inferred from **iteration path / release tag** (the `IntegrationBuild` field was empty on every bug). To answer "is it in their build":
1. Map the bug's iteration `YY.NN` to the train (table §13): 21.x→2021.x, 22.x→2022.04, 23.x→2023.04, 24.18/24.21→2024.10, 25.06/25.12/25.16→2025.04, 26.05/26.07→2026.04.
2. If the client is **on or after** that train, the fix should be present — **confirm in the Upstream release notes / the linked PR's target branch**.
3. **Watch the port-back trap:** #1416291 is tagged *"Not 2024.10 Ups; Not 2025.04 Ups"* — a fix can exist on an older train yet **not** be auto-carried forward. For old custom client branches (e.g. Pioneer v16), expect a **one-off Patch** of selected items, not the whole set (#1697053).

**Route to Engineering (real code defect) when:**
- Child-split count wrong from a stored proc (#1367134/#1416291) — get the master PQID + `PROC_GRP_SEQ_NO` group counts vs child count.
- Property allocation one child short (#1446592) — `QPSJIBPropAllocSplitter.cpp`.
- $0 OA-exclude row (#1716693); GL013 validation exception (#1588160); BA suspense labels (#1653282); JB020 DOI validation (#1382019); JB005 Initiate/Finalize SQL (#1793723/#1684125).
- Provide: process step + master PQID + exact error, client + DB + process period, and the `QARCH_QFCBATCH_SQL_TRACE` rows.

**Handle as Config / Cloud Ops (no code) when:**
- OOM because of wrong `JBCDE_BUSINESS_SEGMENT` metadata profile or slice config (#129108) — fix the **client/ENV layer**, never core.
- BA005 1099 not matching (enable **address-level** 1099 config, #1096612).
- Missing Exago env connection `QRAExagoDataHelper` (#1404377).
- MINRLSE offset using a QCFS **Control Account** that blocks import — point it at a **JIB AR Suspense** account (#106653).

**Likely Rejected / Expected / data-artifact (set expectations, don't over-escalate):**
- "Revenue in STRAN not in GL" → usually a **REV-side restage** (#1422077).
- Prepayment "rogue" transactions → **cancelled-archive re-import** collateral (#1659695 → #1657661).
- **Direct-bill to a property-allocation (AL) property** → unsupported (#1638771).
- JB330 status N-not-H / JIB netting JE-Post / JB005 re-sequence → often **test-data / expected new-flow** (#1589739, #1589796, #1685018).

**Important classification caveat:** "QRA revenue distribution" symptoms almost always resolve into **JIB allocation (QCA) engine** or **config**, not a QRA-branded code path. Confirm whether the client is asking about *allocation/rebill* (→ §4-§7, QCA) vs *QRA reports/setup/check-write/suspense* (→ §8-§9) before searching.

---

## 16. Repos & Code Map

| Area | Repo | Notable symbols (from these bugs) |
|---|---|---|
| JIB allocation C++ batch (the distribution engine) | **`Quorum.Upstream.QCA.ClassicBatch`** | `QPSJIBRebillReversal.cpp` (#1367142), `QPSJIBPropAllocSplitter.cpp` (#1446592), `QPSJIBOwnerAllocation.cpp` / `QPSJIBOwnerAllocationMain.cpp` (#129108/#1416291), `QPDllCostAcctgJIB/QSQL_JIBOwnerAllocation.cpp` (#1389411) |
| JIB stored procs (split/stamp) | **`Quorum.Upstream.QCA.Database`** (SqlServer) | `USP_JIB_PREPARE_JE_SPLIT`, `USP_JIB_STAGE_INVOICE_SPLIT`, `USP_JIB_OWNER_ALLOC_STAGE_SPLIT`, `USP_JIB_PRE_JOURNAL_SPLIT`, `USP_CALC_SPLIT_VALUES_BY_KEY`, `USP_TRUNCATE_JBTRN_JIB_JOURNAL` (#1746136) |
| QRA / upstream screens (Classic & Web) | `Quorum.Upstream.QRA.*` / shared Financials screen layer | `QFrmUpstreamFD_AccountMaintenance` (GL013, #1588160); BA005 / BA address-JIB labels (#1653282); QP043 (#1733284) |
| Reports | Exago report layer | `QRA_CLOSE_CALENDAR_VW`, Revenue Close/Closing Summary, Income Analysis `RPT_ESR015` (#1449118/#1404377/#1355530) |

**Process steps to recognize:** `JBOWNALLOC`, `JBREBILL`, `JBOAMAIN`, `JBOACHILD`, `JBJEMINHLD`, `QPSJIBOAPreJEMinHld`, `JBINVMNPRC`, `QCFSIMPCYC`, `ADPUPLOAD`, `OIEXPORT`. **Screens:** JB005 (process driver), JB020 (drilling OH / DOI), JB200 (allocation definition), JB300 (rebill request), JB310 (OA exclude), JB330/JB340 (owner alloc / subledger detail), GL013 (account maint), BA005 (BA maint), QP043/QP073 (process launchers).

---

*Skill created 2026-06-14. Source: ADO Financials Bugs (Closed/Resolved); ~36 deep-read across clusters. Fixed-in versions inferred from iteration path + release tag (IntegrationBuild empty on all). Companion: REPO_INVENTORY / CONFIG_REFERENCE in the Upstream ADO Assistant dir; cross-ref the QCA cost-accounting skill — the revenue/cost distribution engine is shared. ADO is read-only; nothing in ADO was modified.*
