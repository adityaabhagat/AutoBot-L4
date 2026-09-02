# SKILL: QRA Tax / 1099 / Regulatory — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps Financials bugs (read-only mining)
**Product family:** Quorum Upstream Accounting — **QRA** (Revenue Accounting), **QCFS** (Financial Accounting / AP & 1099), with crossover into QCA depreciation. ADO Area Path **`QuorumSoftware\Engineering\Financials`** (and sub-areas `\Committed Backlog`, `\Customer Service`, `\Maintenance and Overhead`, `\…\Performance`).
**Scope:** The **1099 / tax-withholding / regulatory reporting** pipeline — the QCFS **1099 process chain** (`QSTG1099OV` → `INT1099STG` → `INT1099EXP`/`QSTG1099EX`), the **AP043 / AP151 / AP170** configuration & override screens, **BA005 / eSuite BA Tax-ID** master setup, **AP061** automatic tax withholding, and **PII / Tax-ID sanitization**.

> **Use When:** an Upstream client (QCFS/QRA) reports a 1099 process failing or timing out, wrong/missing 1099 box amounts, wrong form type (MISC vs NEC), AP151 cross-reference ignored, tax withholding not flowing to box 4, a BA 1099 flag/Tax-ID that won't save, or a Tax-ID sanitization gap — and you need the known ADO root cause, the fix, and which build it landed in.

> **Evidence base:** 31 Closed/Resolved Financials bugs matched on title terms (severance, sev tax, tax, 1099, ONRR, production tax, NAUPA, TONL_TAX, TRSEV). **All 31 are 1099 / withholding-tax / tax-ID** items — the severance/ONRR/NAUPA/TONL_TAX/TRSEV terms returned **zero** hits (see Notes). 20 were deep-read for root cause (description + repro + dev comments + linked PR/commit); the remaining 11 are cosmetic/duplicate/by-design QP073 items skimmed by description. Every root-cause and build claim below cites a real ADO bug ID and, where present, the linked PR/commit and the dev comment that states the target release.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [The 1099 Pipeline & Key Objects](#2-the-1099-pipeline--key-objects)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — `QSTG1099OV` override SQL: timeouts & out-of-memory](#4-cluster-a)
5. [Cluster B — `QSTG1099OV` override SQL: wrong amounts / cartesian / re-run corruption](#5-cluster-b)
6. [Cluster C — AP151 cross-reference & form-type (MISC/NEC) mapping](#6-cluster-c)
7. [Cluster D — `INT1099STG` consolidation / export format](#7-cluster-d)
8. [Cluster E — Automatic tax withholding → 1099 box 4 (AP043/AP061)](#8-cluster-e)
9. [Cluster F — BA 1099 flag & Tax-ID master (BA005 / eSuite BA / PII)](#9-cluster-f)
10. [Cluster G — QP073 process-launcher: inactive process & cosmetic text](#10-cluster-g)
11. [Cluster H — QCA depreciation tax/book duplication (adjacent area)](#11-cluster-h)
12. [Fix-Version Matrix](#12-fix-version-matrix)
13. [Diagnostic Pointers](#13-diagnostic-pointers)
14. [Escalation Guidance](#14-escalation-guidance)
15. [Key Code, Processes & Repos](#15-key-code-processes--repos)

---

## 1. Quick Triage Table

| Symptom (what the client reports) | Likely cluster / cause | First check |
|---|---|---|
| `QSTG1099OV` (1099 A/P / Payables Override) **times out** — "Timeout expired… Call to … `QPS1099Override_QSTG` failed" | §4 — heavy override SQL; **not yet hotfixable (has DB changes)** | Confirm `COMMAND_TIMEOUT_SECONDS`; raise it as stop-gap; long-term re-write is develop-only (#1638333) |
| 1099 **box amounts wrong / inflated** ($51,880 in a box that paid $1,800), totals carry across vouchers, voided check doubles a box | §5 — cartesian join / wrong account / running totals not reset in `Override1099QSTG.cs` | Was a **voided check** or a **re-run with overrides** involved? (#237859, #246560) |
| AP151 **cross-reference (Xref 1099 Misc) ignored** — amount lands on default form/box from AP043 instead of the Xref box | §6 — override process not honoring AP151; wrong (offset) account joined | Verify AP151 row uses a **paid** account/BU that actually appears on the 1099 (#231528) |
| **MISC / NEC missing** from Form Type Override dropdown (AP170); form type wrong on output | §6 — metadata (Code Table 63011) lost in refresh | Re-apply the AP170 form-type metadata (#196711) |
| `INT1099STG` **fails to insert** into `SSTAG_1099_MISC` (SQL syntax error) | §7 — missing quote around `ALT_ST` in the consolidate-insert when >1 row per key | Does the client have >1 QRA row per key (TIN/PTIN/ACCT_NO/ST/FORM_TYPE)? (#237658) |
| 1099 export file is **CSV when it should be tab-delimited** | §7 — export definition flipped to CSV during NEC work | Check ImpExp `1099MISCINT` def (#237740) |
| **Tax withholding not on the 1099** (box 4) for owners without a Tax ID | §8 — withholding-to-box mapping gap; global-config stop-gap added | AP043 tax-withholding box config; withhold only when BA has **no** Tax ID (#1392112, #1651177) |
| **Cannot void** a check run created before the withholding enhancement ("Specified cast is not valid") | §8 — new withholding column null on old rows | DB backfill of `TAXWITHHOLDINGAMT` (#106595) |
| BA **1099 flag won't save** on BA005 / flag ≠ `BA_1099_IND` in DB / Tax-ID field read-only in Web | §9 — `PUBBA` cast error; address-vs-BA level config; security object | Producer Type CP and `ALLOW 1099 FOR CORPORATION`? Web Tax-ID = security (#1319075, #1096612, #1552782) |
| Tax-ID columns **not sanitized** by PII scrubbing | §9 — sanitization missed some TAX_ID columns (QCFS & QRA) | Re-run after fix; verify QRA tables too (#1706954) |
| QCFS 1099 amount **wrong when multiple invoices paid in one check** | §5 (core 1099 calc) | Patched broadly; confirm client got the patch (#76822, #105822) |

---

## 2. The 1099 Pipeline & Key Objects

```
[AP vouchers + checks]              [QRA 1099 staging: RSTG_1099_MISC / RRPT_1099_MISC]
        │                                          │
        ▼  QSTG1099OV  (1099 Payables Override)     │
[QSTG_1099_MISC_OVR  +  AP170 review/override grid] │   ← AP043 default box/form, AP151 Xref by account
        │                                          │
        └──────────────►  INT1099STG  ◄────────────┘   (consolidate QCFS + QRA → SSTAG_1099_MISC)
                              │
                              ▼  INT1099EXP / QSTG1099EX
                       [1099 export file (tab-delimited) → IRS/IRIS]
```

### Key terms (Quorum Upstream vocabulary)
- **QSTG1099OV / QSTG1099OVR** = "1099 Payables Override" batch step. Reads paid AP, applies AP043 defaults + AP151 cross-references, and stages rows (with any user overrides) into **`QSTG_1099_MISC_OVR`** for review on **AP170**. This is the single most defect-prone step (Clusters A & B). Code: `Override1099QSTG.cs` / `QPS1099Override_QSTG.cs` in **Quorum.Upstream.QCFS.Web** (`Quorum.QCFS.BS`).
- **INT1099STG** = "Integrated 1099 Export (STAGING)" — merges QCFS and QRA 1099 data into the shared **`SSTAG_1099_MISC`** table.
- **INT1099EXP / QSTG1099EX** = the export step that writes the staged data to a file (ImpExp ID `1099MISCINT`). `QSTG1099EX` is a **deprecated** step that should be hidden/removed.
- **AP043** = Accounts Payable Configuration (Global) — defines the **Default 1099 Form** (MISC/NEC) and the **Federal/State default box** (`IDIRS_1099_FORM_BOXFED` / `IDIRS_1099_FORM_BOXSTATE`); per §8 it is also where the global **tax-withholding box** is configured.
- **AP151** = Xref 1099 Misc — by **account** overrides the form + box (and "Exclude State?") that a payment maps to.
- **AP170** = 1099 Payables Override screen — the review grid over `QSTG_1099_MISC_OVR`, including the **Form Type Override** dropdown (MISC/NEC).
- **AP061** = Check Run Creation — where **Automatic Tax Withholding** amount is calculated/displayed; posts to `BATCHCHECKRUNDETAIL.TAXWITHHOLDINGAMT`.
- **BA005** = Business Associate maintenance — the **1099 indicator** flag (`BA_1099_IND` in `QCTRL_BA_ADDRESS_QRA`); the eSuite Web BA screen has the **Tax IDs** tab (`SCTRL_BA_TAX_ID`, masked via security object `UNMASKTAXID`).
- **PTIN/TIN/ACCT_NO/ALT_ST/FORM_TYPE** = the natural key used to consolidate 1099 rows; the alternate key `AK1_SSTAG_1099_MISC` includes `FORM_TYPE` (added for MISC vs NEC).
- **QP073** = the Classic Process Launcher screen that fronts all the above processes.

---

## 3. Decision Tree

```
QRA/QCFS 1099 or tax case
│
├─ Process CRASHES / TIMES OUT?
│   ├─ QSTG1099OV "Timeout expired … QPS1099Override_QSTG failed"        → §4 (raise COMMAND_TIMEOUT_SECONDS; long-term re-write #1638333, develop-only)
│   ├─ QSTG1099OV "out of memory"                                        → §4 (32-bit QPEC limit; convert to segregated process — open follow-up)
│   ├─ QSTG1099EX "Process ID … is inactive" / process shouldn't be there→ §10 (deprecated step; remove from QARCH_CTRL_PROCESS_TYPE, #200838/#226253)
│   ├─ QSTG1099OV "Error converting data type varchar to numeric" / stuck QUE → §10 (left Execution Server = Current Machine; blank it, #198847)
│   └─ INT1099STG insert fails (bad SQL)                                 → §7 (missing quote around ALT_ST when >1 row/key, #237658)
│
├─ Process RUNS but the NUMBERS / BOXES are wrong?
│   ├─ Amount inflated / totals carry across vouchers / voided check doubles → §5 (cartesian join / running totals / offset account in Override1099QSTG.cs)
│   ├─ AP151 Xref ignored, lands on AP043 default box/form               → §6 (#231528 — verify the Xref account is actually paid)
│   ├─ MISC/NEC missing from dropdown or wrong form type                 → §6 (metadata Code Table 63011, #196711)
│   ├─ Tax withholding not in box 4                                      → §8 (#1392112)
│   └─ Multiple invoices in one check → wrong 1099                       → §5 (#76822/#105822 — confirm the patch reached this client)
│
├─ EXPORT file wrong?  CSV instead of tab-delimited                      → §7 (#237740)
│
├─ MASTER DATA won't save / display?
│   ├─ BA005 1099 flag won't save / flag ≠ BA_1099_IND                   → §9 (PUBBA cast error #1319075; address-level config #1096612)
│   ├─ eSuite Web BA Tax-ID field read-only                              → §9 (security object UNMASKTAXID, #1552782)
│   └─ Tax-ID not sanitized by PII job                                   → §9 (#1706954 — check QRA tables too)
│
└─ Depreciation/asset lines doubled with TAX + BOOK schedules            → §11 (QCA FA070 multi-join, #110529 — adjacent, not 1099)
```

---

## 4. Cluster A — `QSTG1099OV` override SQL: timeouts & out-of-memory

**The dominant operational signature for large clients (EQT, Mewbourne).** The 1099 Payables Override SQL is heavy and degrades badly with data volume / tax-year size.

**Symptom (verbatim, #1638333):**
```
Timeout expired. The timeout period elapsed prior to completion of the operation or the server is not responding.
Call to C# Batch Process Step Object Quorum.QCFS.QCFSBatchCore.QPS1099Override_QSTG failed Execute
```

**Root causes & history:**
- **#241162 (Mewbourne, 2020):** a query rewrite in `QSTG1099OVR` (called from `Override1099QSTG.cs`) regressed from ~16 min to ~2 hrs. MEW had added **custom indexes** internally; engineering also logged a **core DB index** ticket (#241918). Fixed by query change.
- **#99687 (310486, Maintenance):** `QSTG1099EX` export timing out — fix in the maintenance branch; tied to core DB SIR 179261.
- **#1638333 (EQT, 2024 tax year — "Long Term Fix"):** clients raised `COMMAND_TIMEOUT_SECONDS` (3600 → 7200) as a stop-gap and *still* timed out after 6 hrs (then completed in ~1.25 hrs on a later attempt — i.e. server/contention dependent). Engineering wrote a **re-written main override query** (PR #104911 → `develop`, plus DB PR #104989) and a recommended **index change** as a workaround. **Because the fix includes DB changes it was NOT hotfixed** — closed as develop-only ("could be patched to other clients… but it does include DB changes").

**Fix / fixed-in-build:**
- Long-term re-write **merged to `develop` 2025-01-15** (iteration **25.02**), PRs **#104911** (Quorum.Upstream.QCFS.Web) + **#104989** (Quorum.Upstream.Database). No back-patch — clients on older releases get only the index + timeout workaround.
- A separate follow-up was raised to **convert `QPS1099Override_QSTG` to a segregated process** so it is not bound by the **32-bit QPEC memory limit** (MEW hit "out of memory"); also a MEW conversion item #1640014.

**Workaround (stop-gap, no code):** raise `COMMAND_TIMEOUT_SECONDS` for the QPEC; apply the recommended index on the override query; run off-peak; if "out of memory," restart the QPECs (resets starting memory) and retry.

**Bug IDs:** #1638333 (EQT, Closed/Acceptance, 25.02), #241162 (MEW, Closed, 20.23), #99687 (Maint, Closed). **Linked SF case:** #1638333 → SF Case `500UG000000q2CK` (EQT). Related internal: #1633446, #1640014, #241918, #1707633.

---

## 5. Cluster B — `QSTG1099OV` override SQL: wrong amounts / cartesian / re-run corruption

Same `Override1099QSTG.cs` process, but here it **completes with wrong numbers** rather than crashing. This is a recurring **Software Defect** family.

| Bug | Symptom | Root cause | Fix |
|---|---|---|---|
| **#237859** (Closed, 20.21) | Voided check involved → duplicate/incorrect pay amounts in some boxes | **Invalid join → cartesian** in the payables query during the override process when a voided check is present | Corrected join; pushed Develop 2020.03 (17.19.7) & 2020.09 (17.21.1). *(Copied from #237740.)* |
| **#246560** (Closed, 21.01) | Re-running `QSTG1099OV` with AP170 overrides **switches/overwrites BA names** between override lines → duplicate-key errors in `INT1099STG` | An **inconsistent UPDATE statement** for the address override in `QSTG_1099_MISC_OVR`: it should set the row to its override else to itself, but the logic was unreliable (pre-existing, exposed by the form enhancement) | Fixed UPDATE; pushed to develop + 2020.03/2019.05; patched MEW (changeset 219483). Original issue #129586. |
| **#202615** + **#231528** (Closed, 20.11 / 20.19) | After AP151 Xref, box totals **carry/accumulate across vouchers** ($51,880 where only $1,800 paid); also Box 7 affected | Process joined to the **offset account, not the expense account**, and **running totals were not reset** between vouchers (a section of joins from the deprecated `ConsolidateQSTG` SQL was missing) | Re-added the account joins + reset logic in `Override1099QSTG.cs` (see §6 — same fix). |
| **#76822 / #105822** (Closed, Maintenance) | **QCFS 1099 incorrect when multiple invoices are paid in a single check** | Core 1099 calc defect (NetSuite 308043) | Patched broadly via maintenance; **#105822 = the same defect at Northwoods**, which had not received the original patch (packaged to NWD client branch). |

**Insight:** when an override produces **wrong box amounts**, the cause is almost always in the payables join inside `Override1099QSTG.cs` — a **cartesian** (voided check, #237859), the **wrong account** (offset vs expense, #231528/#202615), **un-reset running totals**, or an **unreliable override UPDATE** (#246560). Ask first: *was a voided check involved? was the process re-run with overrides? are multiple invoices on one check?*

**Bug IDs:** #237859, #246560, #202615, #231528, #76822, #105822. Linked SF/NetSuite: #76822 → NetSuite 308043; #105822 → Northwoods (NetSuite 358164). Related internal: #129586, #202321.

---

## 6. Cluster C — AP151 cross-reference & form-type (MISC/NEC) mapping

How the override maps a payment to the correct **form (MISC/NEC)** and **box** via AP043 defaults + AP151 cross-references.

| Bug | Symptom | Root cause | Fix |
|---|---|---|---|
| **#231528** (Closed, 20.19) | AP151 Xref **not observed** — amount uses AP043 default form/box (e.g. lands on NEC Box 1 instead of MISC Box 3) | Override process ignored AP151; and when it did map, it pulled the **offset account** and **accumulated totals** across lines | Honor AP151 by expense account; reset per-voucher; `Override1099QSTG.cs`. Core DB #232115. |
| **#196711** (Closed) | **MISC and NEC missing** from the AP170 Form Type Override dropdown | Dropdown driven by **metadata Code Table 63011**, lost on environment refresh | Re-apply the metadata (not a code bug) |
| **#202615** (Closed, 20.11) | "Xref disregarded, wrong BOX# in DB" | **Not bonafide** — tester misunderstood AP151 (the box you specify *receives* the federal value); must test with a **paid** BU/account | By-design; education. Use BU 200 / Account 3100-1000 in CORE_TST |

**Fix recipe:** for "Xref ignored," confirm the AP151 row uses an **account+BU that actually has a paid 1099 booking** (#202615/#231528) — Xref only fires for accounts the override query already returns. If totals are wrong after the Xref maps correctly, it is the §5 account/running-total defect. For missing MISC/NEC dropdown values, re-apply **Code Table 63011** metadata (#196711).

**Bug IDs:** #231528, #196711, #202615. SF/NetSuite: NetSuite 183521/183522/183523 (the 1099 NEC enhancement that introduced these).

---

## 7. Cluster D — `INT1099STG` consolidation / export format

The consolidation step that merges QCFS + QRA into `SSTAG_1099_MISC`, and the export definition.

| Bug | Symptom | Root cause | Fix / build |
|---|---|---|---|
| **#237658** (Closed, 20.21) | `INT1099STG` **fails to insert** into `SSTAG_1099_MISC` — bad SQL syntax | When **>1 QRA row per key** (TIN/PTIN/ACCT_NO/ST/FORM_TYPE) the consolidate path builds an INSERT with a **missing single quote around `ALT_ST`** (`… 'TX'` rendered as `TX'`). Introduced at the start of the 1099 NEC enhancement (commit `7afa3b2f`); the multi-row-per-key + override scenario was never tested | Fixed string build; pushed Develop 2020.03 (17.19.7) & 2020.09 (17.21.1) |
| **#237740** (Closed, 20.21) | Export `INT1099EXP` (ImpExp `1099MISCINT`) produced **CSV instead of tab-delimited** | Export definition flipped to CSV during the NEC work (requirement referenced CSV ambiguously) | Reset def to tab-delimited; Develop 2020.03 (17.19.7) & 2020.09 (17.21.2). Repo: Quorum.Upstream.Metadata |
| **#200952 / #198920** (Closed) | EXPORT process description duplicates/garbles the STAGING description; awkward wording | Metadata text only | Text fix (see §10) |

**Diagnostic for #237658:** run the dev's detection query — count QRA rows per key in the client's `RSTG_1099_MISC` joined to `RRPT_1099_MISC` for the tax year; `HAVING count(*) > 1` reproduces the path that builds the bad INSERT.

**Bug IDs:** #237658, #237740, #200952, #198920.

---

## 8. Cluster E — Automatic tax withholding → 1099 box 4 (AP043 / AP061)

Withholding tax for owners **without a Tax ID** must flow to the 1099 (box 4). Several defects here.

| Bug | Symptom | Root cause | Fix / build |
|---|---|---|---|
| **#1392112** (Closed, 21.22, ENC) | Automatic AP tax-withholding amount **not getting sent to the 1099** (box 4) | Withholding amount not mapped to a 1099 box for BAs without a Tax ID | Delivered via a **global-config stop-gap** (avoid core DB change): new global tax-withholding box on AP043, mapped in `Override1099QSTG.cs`. No DB change → candidate for the **2020.09 November hotfix**. Follow-up planned for a fuller AP151-based design (new `XREF_1099_MISC` field). |
| **#1651177** (**Rejected**, 24.06) | AP061 Tax Withholding Amount always displays **0** | **Invalid test case** — withholding should apply **only to vendors with NO Tax ID** (BA005 / `SCTRL_BA_TAX_ID`), and AP043 must have a withholding %; after posting, the amount correctly updates to 0 | No code fix — test case corrected. (Possible relation to non-op % issue #1649828.) |
| **#106595** (Closed, Maintenance) | **Cannot void** check runs created *before* the tax-withholding enhancement — "Specified cast is not valid" | New `TAXWITHHOLDINGAMT` column **null** on pre-enhancement `BATCHCHECKRUNDETAIL` rows; void code cast null | **DB backfill script** set old rows to 0: `MSSQL UPS_17.0.00.0013.0000_…_106595.sql` (verified 2019.03). Core DB SIR 180690 |

**Fix recipe:** "withholding not on 1099" → confirm the AP043 global withholding box is configured and the BA truly has **no Tax ID** (withholding only applies then). "Tax withholding shows 0 on AP061" is usually **expected** post-posting / mis-set test (#1651177). "Cannot void old check run" → run the `106595` DB backfill for null `TAXWITHHOLDINGAMT`.

**Bug IDs:** #1392112 (ENC), #1651177 (Rejected), #106595. Related: parent feature 1372150/1351966, #1649828.

---

## 9. Cluster F — BA 1099 flag & Tax-ID master (BA005 / eSuite BA / PII)

Master-data and security issues around the BA 1099 flag and Tax-ID.

| Bug | Symptom | Root cause | Fix / build |
|---|---|---|---|
| **#1319075** (Closed, 21.08) | **Cannot check & save the 1099 flag on BA005**; `PUBBA` batch errors | The flag-save path threw "Unable to cast object of type `System.Data.DataRow` to `Quorum.QFC.Core.QDataRow`" — a **VAR-typed read without an explicit cast to QDataRow** (collateral from #260973). The *Producer-Type-CP* part is **expected** (you don't issue corporations 1099s unless `ALLOW 1099 FOR CORPORATION=1`). | Fix in **Quorum.Upstream.Shared.Batch**; routed to 2020.09 hotfix. Depends on ESUITE `Integration.QLS` beta picking up #260973. Cross-logged on Financials as #1096069. |
| **#1096612** (**Rejected**) | BA005 1099 checkbox ≠ `BA_1099_IND` in `QCTRL_BA_ADDRESS_QRA` | Config: indicator is tracked at **address level**; after enabling the address-level config it matched | No code fix — config (blocked behind the #1096069 PUBBA error) |
| **#1552782** (Closed, 22.22) | eSuite **Web BA Tax-ID field read-only** for all Tax-ID types → cannot save any Tax-ID record | **Security**: the `UNMASKTAXID` object (`QARCH_SEC_OBJECT`, module ENGS) was not granted to the right groups | Core DB script granting `UNMASKTAXID` to groups **10 (All Access)** & **90671007 (ESUITE-BA DATA ENTRY – TAX ID – BANK INFO)**; consumed in Quorum.Upstream.Database. Core DB #1557216. Controller: `BusinessAssociateController.cs` |
| **#1706954** (Closed, 25.03) | **Tax-ID columns not sanitized** by the PII scrubbing | PII sanitization missed some `TAX_ID` columns / didn't uniquely handle them across tables (QCFS **and QRA**) | Fix to PII sanitization (Quorum.Upstream.QCFS.Web + Shared.Web + ESuite.Web); QA confirmed QRA `TAX_ID` cols also covered |

**Fix recipe:** "1099 flag won't save / PUBBA error" → confirm the QPEC is consuming the **Shared.Batch / ESUITE Integration.QLS build that contains #260973** (the QDataRow cast fix), then retest (#1319075). "Web Tax-ID read-only" → grant the **`UNMASKTAXID`** security object to the user's group (#1552782). "PII didn't scrub a Tax-ID" → confirm the #1706954 fix and re-run, checking QRA tables too.

**Bug IDs:** #1319075, #1096612 (Rejected), #1552782, #1706954. Related: #260973, #1096069, #1557216.

---

## 10. Cluster G — QP073 process-launcher: inactive process & cosmetic text

QA-found issues on the **QP073 Process Launcher** during the 1099 NEC release. Mostly metadata/cosmetic — useful to recognize so you don't escalate them.

| Bug | Symptom | Root cause / fix |
|---|---|---|
| **#198847 / #200909** | `QSTG1099OV` "unexpectedly stopped / stays Queued" | **Tester left Execution Server = "Current Machine"** → job sat in QUE for a machine with no QPEC; also a real deploy gap ("Error converting data type varchar to numeric" until the build was actually picked up by nukeeper). **Leave Execution Server blank.** |
| **#200838 / #226253** | `QSTG1099EX` ("QCFS 1099 Export (QSTG)") **should not be runnable** — "Process ID QSTG1099EX is inactive…" | Deprecated step (hidden via #183523) but the WinForms launcher ignored `HIDDEN_IND`. Fix = **remove it from `QARCH_CTRL_PROCESS_TYPE`** (`DELETE … WHERE PROCESS_ID='QSTG1099EX'`) via metadata. |
| **#200924 / #201866** | `INT1099STG` "stopped with errors" | Same NEC-cycle deploy/data issues as above; resolved when the corrected build deployed |
| **#198530 / #198920 / #200952** | Grammar / awkward / duplicated **Description** text on QP073 | Pure metadata text fixes (Quorum.Upstream.Metadata) |

**Takeaway:** for a QP073 1099 process that "won't run," first check (a) **Execution Server is blank** (#198847), and (b) the step isn't the **deprecated `QSTG1099EX`** (remove from `QARCH_CTRL_PROCESS_TYPE`, #200838). Description-text items are cosmetic.

**Bug IDs:** #198847, #200909, #200838, #226253, #200924, #201866, #198530, #198920, #200952.

---

## 11. Cluster H — QCA depreciation tax/book duplication (adjacent area)

Matched on "tax" but it is **QCA depreciation**, not QRA 1099 — included because it is a classic multi-schedule **cartesian** the same engineer (Ben Weis) root-caused, and it surfaces in tax filings.

- **#110529** (Closed, Maintenance — PAR/Parsley): asset additions **duplicated in FA070** (`QTRAN_DDA_SL`) when an asset class has **both BOOK and TAX schedules**, inflating depreciation. Root cause: the insert SELECT has **multiple LEFT JOINs to `QCTRL_DDA_CLASS_METHOD`** (PK `FA_CLASS_CD, EFF_DT_FROM, SCHED_CD`) that **don't account for multiple `SCHED_CD`** → cartesian. Collateral from #73491. Fix in **Quorum.Upstream.QCA.ClassicBatch**; went out with the 2020.10 release (commit-dated). Core DB SIR 190622.

**Note this for QCA cases**, not QRA 1099. Bug ID: #110529.

---

## 12. Fix-Version Matrix

| Bug | Symptom (short) | State / Reason | Fixed-in build / branch | Repo & PR | SF/external |
|---|---|---|---|---|---|
| **#1638333** | QSTG1099OV timeout — long-term re-write | Closed (Acceptance) | **develop, iter 25.02** (merged 2025-01-15); **DB change → NOT hotfixed** | QCFS.Web PR #104911 + Upstream.Database PR #104989 | SF 500UG000000q2CK (EQT) |
| **#241162** | QSTG1099OVR query 16min→2hr (MEW) | Closed | dev, iter 20.23 (+ core DB index #241918) | QCFS.Web/QCFS.Database PRs 38921/38923/63282/64772 | — |
| **#99687** | QSTG1099EX timing out | Closed (Verified) | Maintenance branch | QCFS.Database PR #7803 | NetSuite 310486; SIR 179261 |
| **#237859** | Voided check → cartesian, dup box amounts | Closed (Verified) | **Develop 2020.03 (17.19.7), 2020.09 (17.21.1)** | QCFS.Web PRs #37736/#37720 | — |
| **#246560** | Re-run overrides → BA names swap, dup-key | Closed | dev + 2020.03 + 2019.05; MEW changeset 219483 | QCFS.Web PR #40649 | — (orig #129586) |
| **#231528** | AP151 Xref ignored; offset account; totals | Closed | dev, iter 20.19 (core DB #232115) | QCFS.Web PRs #36204/#36296 | — |
| **#202615** | Xref "wrong box" — not bonafide | Closed | n/a (by design) | — | — |
| **#196711** | MISC/NEC missing from AP170 dropdown | Closed | metadata re-apply (Code Table 63011) | Quorum.Upstream.Metadata | NetSuite 183521 |
| **#237658** | INT1099STG bad INSERT (ALT_ST quote) | Closed (Verified) | **Develop 2020.03 (17.19.7), 2020.09 (17.21.1)** | QCFS.Web PRs #37724/#37635 | — (intro commit 7afa3b2f) |
| **#237740** | Export CSV instead of tab-delimited | Closed (Verified) | **Develop 2020.03 (17.19.7), 2020.09 (17.21.2)** | Quorum.Upstream.Metadata PRs #37713/#37716 | — |
| **#1392112** | Tax withholding not on 1099 box 4 (ENC) | Closed | dev, iter 21.22; global-config stop-gap; **2020.09 Nov hotfix** candidate (no DB change) | QCFS.Web PR #60921 + Metadata PR #60925 | parent feat 1372150 |
| **#1651177** | AP061 withholding shows 0 | **Rejected** | n/a (invalid test case) | — | — |
| **#106595** | Can't void pre-withholding check runs | Closed | **2019.03 (17.0.00.0013)** DB backfill script | Upstream.Database/QCFS.Database PR #9539 | SIR 180690 |
| **#1319075** | BA005 1099 flag won't save (PUBBA cast) | Closed | dev, iter 21.08; **2020.09 hotfix**; needs #260973 in Shared.Batch/ESUITE QLS | Quorum.Upstream.Shared.Batch PRs #50173/#50175/#50179/#63170 | Fin dup #1096069 |
| **#1096612** | BA005 flag ≠ BA_1099_IND | **Rejected** | n/a (address-level config) | — | — |
| **#1552782** | Web BA Tax-ID read-only (security) | Closed | dev, iter 22.22; core DB grant UNMASKTAXID | Quorum.Upstream.Database PR #76643 | core DB #1557216 |
| **#1706954** | Tax-ID not sanitized (PII) | Closed | dev, iter 25.03 | QCFS.Web PR #105141 + ESuite.Web #105142 + Shared.Web #105146 | — |
| **#76822** | 1099 wrong, multiple invoices/1 check | Closed | Maintenance patch (broad) | QCFS.Web PR #3405 | NetSuite 308043 |
| **#105822** | Same as #76822 at Northwoods | Closed | Maintenance; NWD client-branch package | — | NetSuite 358164 |
| **#110529** | QCA FA070 tax+book depreciation dup | Closed | ~2020.10 release | Quorum.Upstream.QCA.ClassicBatch PR #10765 | SIR 190622 (orig #73491) |
| #198530/#198920/#200952 | QP073 description text | Closed | metadata text | Quorum.Upstream.Metadata | — |
| #198847/#200909/#200838/#226253/#200924/#201866 | QP073 run/deploy/inactive-step | Closed | metadata + deploy fixes | Metadata / QCFS.Web | NetSuite 183523 |

> **Build caveat:** `Microsoft.VSTS.Build.IntegrationBuild` is **empty on every bug** in this set — "fixed-in" above comes from **dev comments** (Ben Weis routinely states "Develop 2020.03 (17.19.7) / 2020.09 (17.21.x)"), the **iteration path**, and PR target branches. The dozens of `vstfs:///Build/Build/*` artifact links on each WI are cherry-pick/branch builds, **not** release builds — do not cite them as the fix version. Always confirm the exact release in `Quorum.Upstream.ReleaseNotes` / the QCFS release notes before telling a client a build contains a fix.

---

## 13. Diagnostic Pointers

```sql
-- A. (#237658) Does the client have >1 QRA 1099 row per consolidation key for the tax year?
--    Reproduces the bad-INSERT path in INT1099STG.
SELECT R.TIN, R.PTIN, R.ACCT_NO, R.ST, R.FORM_TYPE, COUNT(*)
FROM   <CLIENT>_QRA.dbo.RSTG_1099_MISC R
JOIN   <CLIENT>_QRA.dbo.RRPT_1099_MISC RP
       ON R.PTIN=RP.PTIN AND R.TIN=RP.TIN AND R.ACCT_NO=RP.ACCT_NO
      AND R.ALT_ST=RP.ALT_ST AND R.INT_CTGY=RP.INT_CTGY
WHERE  RP.TAX_YEAR = '<YYYY>'
GROUP BY R.TIN, R.PTIN, R.ACCT_NO, R.ST, R.FORM_TYPE
HAVING COUNT(*) > 1;

-- B. (#198847 / queue) Why is a 1099 process stuck or who launched it on a machine?
SELECT USER_ID, ASSIGNED_MACHINE_ID, STATUS_CD, PROCESS_QUEUE_ID
FROM   QARCH_QUEU_PROCESS
WHERE  PROCESS_ID IN ('QSTG1099OV','INT1099STG','INT1099EXP','QSTG1099EX')
ORDER BY PROCESS_QUEUE_ID DESC;     -- STATUS_CD='QUE' + a specific machine = Execution Server was not blank

-- C. Read the actual error for a failed run (varchar->numeric, inactive process, syntax, etc.)
SELECT * FROM QARCH_PROCESS_MSG_LOG WHERE PROCESS_QUEUE_ID = <PQID>;

-- D. (#200838) Is the deprecated export step still launchable? Remove it.
SELECT * FROM QARCH_CTRL_PROCESS_TYPE WHERE PROCESS_ID = 'QSTG1099EX';
-- fix: DELETE FROM QARCH_CTRL_PROCESS_TYPE WHERE PROCESS_ID = 'QSTG1099EX';

-- E. (#106595) Old check runs that will fail to void (null withholding column)
SELECT TAXWITHHOLDINGAMT, * FROM BATCHCHECKRUNDETAIL WHERE TAXWITHHOLDINGAMT IS NULL;

-- F. (#1096612) BA005 1099 flag vs stored indicator
SELECT BA_1099_IND, * FROM QCTRL_BA_ADDRESS_QRA WHERE BA_NO LIKE '%<BA>%';

-- G. (#1552782) Who can edit the Tax ID in Web (UNMASKTAXID security object)?
SELECT * FROM QARCH_SEC_OBJECT WHERE MODULE_CD='ENGS' AND OBJECT_ID='UNMASKTAXID';
-- grant to groups 10 (All Access) and 90671007 (ESUITE-BA DATA ENTRY - TAX ID - BANK INFO)

-- H. (#246560 / overrides) Inspect staged override rows the override process produced
SELECT * FROM QSTG_1099_MISC_OVR WHERE YEAR = '<YYYY>';   -- look for swapped BA names / wrong addresses after a re-run
```
> **Caveat:** column/table names are taken from the bug repro text and dev comments; Upstream is multi-DB (separate `_QCFS` / `_QRA` SQL Server DBs per client). **Verify against the client schema** and always run a verify-SELECT before any DELETE/UPDATE.

---

## 14. Escalation Guidance

**Is it already fixed in the client's build?**
- **Timeout (`QSTG1099OV`):** the *real* long-term fix (#1638333) is **develop-only / iter 25.02 (≈2025.x)** and carries DB changes — clients below that release have **only** the index + `COMMAND_TIMEOUT_SECONDS` workaround. Don't promise a hotfix.
- **Wrong-amount defects (#237859, #237658, #237740):** landed in **Develop 2020.03 (17.19.7)** and **2020.09 (17.21.x)**. Any client on **2020.09 patch ≥ 17.21.1** (and 17.21.2 for the export-format fix) has them; older releases need a back-patch.
- **Tax-withholding-to-1099 (#1392112):** delivered as a no-DB-change global-config stop-gap, candidate for the **2020.09 November hotfix** — confirm the client took that hotfix.
- **Web Tax-ID security (#1552782):** **22.22 / 2022.10** + the core DB grant must be applied.
- **PII Tax-ID (#1706954):** iter **25.03** (≈2025.x).
- **Multiple-invoice 1099 (#76822/#105822):** broadly patched via maintenance, **but #105822 proves some clients (Northwoods) were missed** — always verify the specific client received the patch.

**Route to Engineering (Software Defect) when:** a 1099 box amount is provably wrong on correct inputs (cartesian/voided-check #237859; offset-account/running-total #231528; bad INSERT #237658), the override times out at volume despite the index/timeout workaround (#1638333 — needs the develop re-write / segregated-process conversion), or withholding doesn't reach the 1099 (#1392112). Provide **PQID + failing step (QSTG1099OV/INT1099STG/INT1099EXP) + the `QARCH_PROCESS_MSG_LOG` error**, client + tax year, and whether a voided check / re-run / multi-invoice-check / >1-row-per-key was involved.

**Handle as Configuration / data (no code) when:** AP151 Xref uses a non-paid account (#202615/#231528), MISC/NEC dropdown metadata lost on refresh (#196711, Code Table 63011), deprecated `QSTG1099EX` still listed (#200838 — delete from `QARCH_CTRL_PROCESS_TYPE`), Execution Server left as "Current Machine" (#198847 — blank it), null withholding column on old check runs (#106595 — DB backfill), BA 1099 indicator at address level (#1096612), or Web Tax-ID security grant (#1552782).

**Recognize as Expected / Rejected (no fix):** AP061 withholding shows 0 after posting / withholding only for **no-Tax-ID** vendors (#1651177); you **don't 1099 corporations** unless `ALLOW 1099 FOR CORPORATION=1` (#1319075); AP151 box "receives" the federal value rather than re-routing it (#202615).

---

## 15. Key Code, Processes & Repos

### Processes / steps
| Step | Purpose | Notes |
|---|---|---|
| **QSTG1099OV / QSTG1099OVR** | 1099 Payables Override — stage AP into `QSTG_1099_MISC_OVR` for AP170 | The hot spot: timeouts (§4) + wrong amounts (§5). `QPS1099Override_QSTG.cs` / `Override1099QSTG.cs` |
| **INT1099STG** | Consolidate QCFS + QRA → `SSTAG_1099_MISC` | Bad-INSERT defect when >1 row/key (§7) |
| **INT1099EXP** | Export staged 1099 → file (ImpExp `1099MISCINT`) | Must be **tab-delimited** (§7) |
| **QSTG1099EX** | Deprecated export step | Should be removed from `QARCH_CTRL_PROCESS_TYPE` (§10) |

### Code locations (confirmed via PR/commit links on the bugs)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `Override1099QSTG.cs` (`Quorum.QCFS.BS`) | **Quorum.Upstream.QCFS.Web** | §4/§5/§6/§7 — the central 1099 override SQL |
| `QPS1099Override_QSTG.cs` (`Quorum.QCFS.QCFSBatchCore`) | **Quorum.Upstream.QCFS.Web** | §4 — the batch step object; 32-bit memory limit |
| 1099 SQL / index / `SSTAG_1099_MISC` AK | **Quorum.Upstream.QCFS.Database** + **Quorum.Upstream.Database** | §4/§7 — DB changes block hotfixing |
| ImpExp def `1099MISCINT`; AP170 Code Table 63011; QP073 text | **Quorum.Upstream.Metadata** | §6/§7/§10 |
| BA005 1099-flag save / `PUBBA` (`QDataRow` cast) | **Quorum.Upstream.Shared.Batch** (via ESUITE `Integration.QLS`, #260973) | §9 |
| `BusinessAssociateController.cs`, `UNMASKTAXID` security | **Quorum.ESuite.Web** / core DB | §9 |
| PII / Tax-ID sanitization | **Quorum.Upstream.QCFS.Web** + **Quorum.Upstream.Shared.Web** + **Quorum.ESuite.Web** | §9 |
| AP043 label / Classic GUI | **Quorum.Upstream.QCFS.ClassicGUI** | §6 (#1098615) |
| FA070 depreciation insert (`QTRAN_DDA_SL`, `QCTRL_DDA_CLASS_METHOD`) | **Quorum.Upstream.QCA.ClassicBatch** | §11 (#110529) |

---

*Skill created 2026-06-14 from 31 Closed/Resolved ADO Financials bugs (title-matched on tax/1099 terms). Deep-read: #1638333, #241162, #99687, #237859, #246560, #231528, #202615, #196711, #237658, #237740, #1392112, #1651177, #106595, #1319075, #1096612, #1552782, #1706954, #76822, #105822, #110529. Skimmed: #198847, #200909, #200838, #226253, #200924, #201866, #198530, #198920, #200952.*
*Caveat: severance / "sev tax" / ONRR / production-tax / NAUPA / TONL_TAX / TRSEV returned **no** Financials bugs — this skill is 1099/withholding-tax/Tax-ID only. Several items overlap QCFS (AP/1099) vs pure QRA; #110529 is QCA (depreciation), kept as adjacent. `IntegrationBuild` empty on all — fix versions inferred from dev comments + iteration + PR branches; confirm in release notes.*
