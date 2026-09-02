# SKILL: QCFS Accounts Payable (AP) Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Financial Accounting (QCFS — Upstream Accounting suite; "Upstream", myQuorum AP/Web + Classic GUI)
**Scope:** The Accounts Payable subledger end-to-end — **AP voucher entry & batches** (AP055 Batch Voucher Creation, AP061 check/payment run, AP056 Voucher Maintenance, AP150/151/155/156/157 vendor & 1099 screens), the **AP approval workflow** (AP Full Inbox / AP Web approve-reject-route, POSTWKFL post process), **invoice import** (ADPUPLOAD / ADP / OpenInvoice / JIBLINK / QLS), **payments** (check print, ACH/NACHA, positive pay, void/reissue), **1099 reporting** (QSTG1099OV/EX, AP170), and **vendor/Business Associate (BA) master setup**. QCFS is the AP/AR/GL core that posts journals to the general ledger.
**Companion skills (Upstream Assistant):** GL / journal entry / period-close issues → **SKILL_QCFS_General_Ledger.md** (if present); AR / cash receipts → **SKILL_QCFS_Accounts_Receivable.md**; bank reconciliation → **SKILL_QCFS_Bank_Reconciliation.md**; JIB/owner suspense & revenue distribution (OFRS, owner funds) → the Land/Revenue skills. This skill *consumes* invoices from imports + vendor master + approval routes and *produces* posted vouchers, payments, and 1099 data. When the AP number is wrong because of a coding/DOI/AFE problem, fix the **subledger coding** first — AP is usually the messenger.

> **Evidence base:** 2,517 closed QCFS "Accounts Payable (AP)" cases. Root-cause split: (blank) 480, **Training 250**, **Software Defect 248**, **Customer Error 213**, **Application Configuration 180**, Customer Cancelled 168, Business Change 163, Hardware/Software Change 119, Performance 92, … **ChangeConfig 18**. This skill mines the **446 actionable** cases (Software Defect 248 + Application Configuration 180 + ChangeConfig 18) for fix recipes, plus ~60 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [AP Pipeline & Concepts](#2-ap-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Ghost / stuck / phantom vouchers in the AP Inbox (HIGH FREQUENCY)](#4-cluster-a--ghost--stuck--phantom-vouchers)
5. [Cluster B — Could Not Post / Post Pending / POSTWKFL failures](#5-cluster-b--could-not-post--post-pending--postwkfl)
6. [Cluster C — Invoice import errors (ADPUPLOAD / OpenInvoice / JIBLINK / QLS)](#6-cluster-c--invoice-import-errors)
7. [Cluster D — AP055 Batch Voucher Creation screen defects](#7-cluster-d--ap055-batch-voucher-creation-defects)
8. [Cluster E — Payments: check print, ACH/NACHA, positive pay, void/reissue](#8-cluster-e--payments-check-ach-positive-pay-voidreissue)
9. [Cluster F — Vendor / Business Associate (BA) master setup & corruption](#9-cluster-f--vendor--ba-master-setup)
10. [Cluster G — 1099 reporting (QSTG1099OV/EX, AP151/156/170)](#10-cluster-g--1099-reporting)
11. [Cluster H — Vendor address / ZIP-state alignment on checks & AP155](#11-cluster-h--vendor-address--zip-state-alignment)
12. [Known ADO Items](#12-known-ado-items)
13. [Diagnostic SQL](#13-diagnostic-sql)
14. [Expected-Behavior / User-Education FAQ](#14-expected-behavior--user-education-faq)
15. [Key Screens, Processes & Repos](#15-key-screens-processes--repos)
16. [Escalation Guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| Posted/paid/permanently-rejected voucher **still showing "Awaiting Approval" in a user's AP Inbox** ("ghost"/"phantom" voucher) | Abandoned/orphaned workflow row whose state did not sync to the voucher | §4 — recurring; resolved by a **reusable PRD data script** that resets/deletes the abandoned WF row. Confirm in `APWORKFLOW`/inbox view |
| Voucher **stuck "In Progress" / "Waiting for Approval"** though history shows Approved; can't approve/reject/cancel | Workflow lock or stale WF instance ("Workflow instance is no longer available or does not exist") | §4 — script to remove the WF lock / reset status to Draft |
| Vouchers in **"Could Not Post"** after final approval | Validation that should be a *hard error* at final-approve fired only at post; or bad config/data (zero bank acct type, missing accounts/attributes sync) | §5 — read the post error; sync Accounts↔Attributes; AP043 zero-bank-acct config |
| **POSTWKFL** process erroring continuously / stuck | Config mismatch (e.g. zero bank account type ≠ BR036/AP048) or data | §5 — POSTWKFL error text; AP043/BR036/AP048 |
| **ADPUPLOAD / ADPIMPALLV / APDUPLOAD** import fails / "completed on error" | Image step on a no-image client; JIB-deck/DOI resolution; connection-pool timeout; cartesian validation query | §6 — exact failing **step** + PQID |
| OpenInvoice/JIBLINK invoices import with **bad coding / won't post / wrong amount** | Import mapping / staging defect; coding (AFE/DOI/cost-center) gap | §6 / §5 |
| **AP055** intercompany (I/C) lines **disappear from posted vouchers** | `AutoDeleteOffset` update had no `IDBATVOUMASTER` filter → deletes I/C lines on ALL posted batches | §7 — confirmed code defect, Hotfix 18 (24-00958104) |
| **AP055** code-block / owner / cost-center grid clears on tab; can't delete a draft; duplicate vouchers created | Web/Classic grid screen defects (validation deselects voucher) | §7 |
| Single invoice **paid on multiple checks**; payment type changes on void/reissue; positive-pay rounding | Payment/void code defects | §8 |
| **Check** ZIP code missing hyphen / phone cut off / signature/address line missing | Check form / BA address mask config | §8 / §11 |
| **AP155 / vendor screens**: state shows in the ZIP column, State column blank | Misaligned vendor address data | §11 — PRD data-align script + long-term Hotfix |
| Can't save a **BA "Use as Vendor" flag** / vendor table broken after creating a new BA | BA creation drops GLOBAL BUSINESS / vendor-table records when the BA Web screen isn't closed | §9 — backfill script + Patch 15 code fix |
| **1099** amounts doubled (AP170) / mapped to wrong box (Box 7 vs 17) / export ≠ paid | AP151 (XREF_1099) state-box override missing; 1099 calc/validation defect | §10 |
| "How do I…" NACHA / payment types / save queries / 1099 walkthrough; inactive-BA selection; fiscal close | Training / expected behavior | §14 |

---

## 2. AP Pipeline & Concepts

```
[Invoice source]                         [Manual entry]
 OpenInvoice / ADP / JIBLINK / QLS  ──►  AP055 Batch Voucher Creation (Classic) / AP Web manual voucher
        │  (ADPUPLOAD / ADPIMPALLV / APDIMGUPLD steps)        │
        ▼                                                     ▼
   [Draft voucher / batch]  ──►  APPROVAL WORKFLOW (AP Full Inbox / AP Web: route, approve, reject, R&R)
        │                              │  (validations: sum-of-lines=total, GL budgeted for AFE, DOI/property…)
        ▼                              ▼
   POSTWKFL (post process)  ──►  POSTED voucher  ──►  GL journals
        │                              │
        │                              ├──► PAYMENT: AP061 check run / ACH (NACHA) / positive pay / void-reissue
        │                              └──► 1099: QSTG1099OV (overlay) / QSTG1099EX (export) / AP170 / AP151 XREF_1099
        ▼
   "Could Not Post" (validation fired at post) | "Post Pending" (in flight) | ghost in inbox (WF row orphaned)
```

### Key terms (Quorum/QCFS vocabulary)
- **AP055** = Batch Voucher Creation screen (Classic GUI). Where invoices/vouchers are entered/coded into a **batch** (BV…/BCK… numbers). The single most-cited AP screen. Backed by `QFrmBatchVoucherMaster.cs` and the `BATCHVOUCHERMASTER / BATCHVOUCHERDETAIL / BATCHVOUCHERGLDISTRIBUTION` tables.
- **AP Full Inbox / AP Web** = the approval surface. Final-approve sends the voucher to **POSTWKFL**.
- **POSTWKFL** = the post-workflow batch process that turns an approved voucher into posted GL entries. "Post Pending" = queued/in-flight; "Could Not Post" = a post-time validation failed.
- **Ghost / phantom voucher** = a posted/paid/perm-rejected voucher that still appears as "Awaiting Approval" in a user's inbox because the **workflow row / inbox-view row was orphaned** (state didn't sync). Cosmetic but slows users; cleared by a data script (§4).
- **ADPUPLOAD** = the AP invoice import batch process (a.k.a. ADP import). Sub-steps include **ADPIMPALLV** (allocate/validate — resolves AFE tier / JIB deck / DOI) and **APDIMGUPLD / ADPIMGUPLD** (image attach). **OpenInvoice (OI)** and **JIBLINK** feed it; **QLS** (Quorum Land System) feeds AP land payments.
- **BA** = Business Associate = the vendor/owner master record. "Use as Vendor" flag makes a BA payable. BA setup lives on AP159/BA Maintenance (Web & Classic) and code tables.
- **AFE / DOI / cost center / property** = the coding dimensions on an AP line. An invoice can't post if the coding can't resolve (no JIB deck, invalid AFE-property combo, GL not budgeted for the AFE).
- **AP061** = check/payment run (print checks, generate ACH/NACHA, positive pay export). **AP056** = Voucher Maintenance (open items, approve-to-pay, payment type). **AP157** = payment/check inquiry. **AP043/BR036/AP048** = bank account / zero-bank-account-type config.
- **1099:** **QSTG1099OV** stages/overlays 1099 amounts, **QSTG1099EX** exports; **AP170** displays totals by box; **AP151 (XREF_1099)** holds the GL-account→form-type/state-box overrides. BU defaults a box; AP151 overrides per account.
- **Hotfix / Patch on 20xx.xx** = QCFS ships fixes as version hotfixes (e.g. 2020.09, 2021.10, 2022.04, 2023.04, 2024.04, 2024.10, 2025.04). Many AP cases close as "in the <month> Hotfix"; confirm the client's target build.

---

## 3. Decision Tree

```
QCFS Accounts Payable case
│
├─ Voucher visible in inbox but shouldn't be (posted/paid/perm-rejected still "Awaiting Approval")?
│      → §4  GHOST/PHANTOM — reusable PRD data script to reset/delete the orphaned WF row (recurring, low-risk)
│
├─ Voucher won't move forward?
│   ├─ "Could Not Post" after final approval                 → §5 (read post error; validation should be hard-error at approve; sync Accounts/Attributes)
│   ├─ "Post Pending" stuck / POSTWKFL erroring               → §5 (POSTWKFL error text; AP043 zero-bank-acct vs BR036/AP048; QPEC restart)
│   ├─ "Workflow instance no longer available" on approve     → §4/§5 (remove WF locks; hotfix)
│   └─ Stuck "In Progress"/"Waiting for Approval"             → §4 (WF lock / reset to Draft script)
│
├─ Invoice import problem (ADPUPLOAD / OI / JIBLINK / QLS)?
│   ├─ Fails at APDIMGUPLD/ADPIMGUPLD (image) on no-image client → §6 (remove image step on QClient layer — 24-00985437)
│   ├─ Fails at ADPIMPALLV ("near WHERE" / JIB-deck/DOI)         → §6 (deck/DOI resolution defect → hotfix; find offending property)
│   ├─ Connection-pool / "Timeout … max pool size"               → §6 (split SRC_DOC; override max connection attempts; long-term code fix)
│   └─ Bad coding / doubled amount / blank-$0 imported           → §6/§5 (mapping/staging; verify OI coding)
│
├─ AP055 screen behaving wrong?
│   ├─ I/C lines disappear from POSTED vouchers                 → §7 (AutoDeleteOffset missing IDBATVOUMASTER filter — Hotfix 18, 24-00958104)
│   ├─ Code-block/owner/cost-center grid clears; can't delete draft; dup vouchers created → §7 (grid/validation defect → hotfix)
│   └─ Timeout / reversal performance                           → §7 (perf; ADO #1625903/#1707005/#1720772)
│
├─ Payment problem?
│   ├─ One invoice paid on multiple checks                      → §8 (locking defect — void the extra check; long-term fix)
│   ├─ Payment type wrong after void/reissue                    → §8 (derive payment type from check-run journal — Apr-2025 Hotfix)
│   ├─ Positive-pay rounding / file path / void showing         → §8 (check-form + engr code fix; config file path)
│   └─ Check ZIP missing hyphen / phone cut off / signature/addr → §8/§11 (check form + BA address mask)
│
├─ Vendor / BA master?
│   ├─ Can't save "Use as Vendor"; vendor table broke after new BA → §9 (backfill GLOBAL BUSINESS/vendor rows; Patch 15 code fix)
│   ├─ Vendor defaults/term/payment-type wrong vs AP055           → §9 (BA vs AP055 payment-term/type mismatch — config)
│   └─ Security: can't access AP/AFE, print check, positive pay   → §9/§16 (run security-object grant scripts)
│
├─ 1099?  → §10 (doubled = AP151 validation; wrong box = AP151 XREF_1099 state-box override; export≠paid = calc patch; QSTG1099 timeouts = §14)
│
├─ Vendor address shows State in ZIP column (AP155 / checks)? → §11 (PRD data-align script + 2025.04 Hotfix)
│
└─ "How do I…", audit, inactive-BA, fiscal close, save query   → §14 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — Ghost / stuck / phantom vouchers

**The single largest actionable AP signature.** A voucher that is **posted, paid, or permanently rejected still shows as "Awaiting Approval"** in one or more users' AP Inbox (or a voucher is **stuck "In Progress"/"Waiting for Approval"** though its history shows Approved). The voucher itself is fine — the **workflow / inbox-view row is orphaned** and never synced to the final state. Cosmetic, but it slows approvers and blocks month-end views.

**Symptoms (verbatim):**
- "5 'ghost vouchers' in awaiting approval; however, the vouchers are already posted and paid … reoccurring issue … resolved by data scripts applied directly to PRD previously … Quorum has been able to leverage essentially the same script" (24-00944211).
- "Vouchers that have been either Posted or Permanently Rejected still showing up as Awaiting Approval … able to run a script to clear these" (25-01003393).
- "Voucher VNOJ002190 … posted but stuck in Workflow - In Progress … history shows Approved" (22-00582908).
- "workflow instance [xxxxxxx] is no longer available or does not exist … causes users not being able to approve" (25-01005671).

**Root cause:** an abandoned/orphaned workflow instance or inbox-view row; sometimes a stale **workflow lock**. Repeated across many clients (Alta, EQT, Permian, SandRidge…) and many years — this is a recurring data-hygiene issue, not a per-client bug.

**Fix recipe (the repeatable resolution):**
1. Identify the affected user + voucher numbers + BU (screenshot of "Awaiting Approval" inbox is usually attached). For "stuck in progress," capture the WF status vs the posted/paid status.
2. The fix is a **PRD data script** that resets the orphaned voucher's status to Draft (22-00582908) or **deletes the abandoned workflow** row / inbox-view row (23-00907599 "Script was deployed to delete abandoned WF"; 24-00944211 "created script"). For lock-type errors, **remove the workflow locks** (25-01005671).
3. This is a **reusable script** — prior cases' scripts (e.g. 22-00823538, 23-00907599, 23-00916288) are modified for the new voucher list. Treat as **low risk**; run in PRD (the issue is not reproduced in UAT). Always verify-SELECT the WF/voucher rows first, wrap in a transaction.
4. **Long-term:** several were flagged for a hotfix to the client's version (25-01005671 "long-term solution is to hotfix this issue"). When the volume is high, push the version fix rather than re-running scripts each month.

> **Tell-tale ghost vs real stuck:** if the voucher is already **posted/paid/perm-rejected** → ghost (cosmetic, data script). If it is genuinely **un-posted** and won't move → that's §5 (Could Not Post / POSTWKFL), a different fix.

---

## 5. Cluster B — Could Not Post / Post Pending / POSTWKFL

Distinct from §4: here the voucher is **genuinely not posted**. Two states: **"Post Pending"** (in flight / queued — often a process/QPEC issue) and **"Could Not Post"** (a validation fired at post time).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Approvers can **final-approve from AP Full Inbox despite validation issues**; vouchers then land in "Could Not Post" at post | Validations ("sum of lines ≠ total", "GL code not budgeted for AFE") were **only hard errors on AP Inbox / AP055**, but mere warnings at final-approve in AP Web | **Code change** to make those validations hard errors at the final-approve step in AP Web | 23-00877861 |
| Many AP workflow entries in "Could Not Post" | Accounts and Attributes reference tables out of sync | **Sync the Accounts and Attributes tables** | 23-00897008 |
| **POSTWKFL** erroring continuously: "The bank account type does not correspond to the zero bank account type" | Zero-bank-account-type config did not match the bank config | Updated **AP043** to align the **zero bank account type** with **BR036/AP048** configuration | 24-00937529 |
| Approve fails: "Workflow instance is no longer available or does not exist" / "Voucher was not submitted to workflow" | Stale WF locks | Script to **remove workflow locks**; long-term hotfix | 25-01005671 |
| AP reversal in Post Pending because **POSTWKFL in CE (completed-on-error) status** | Process-state defect | Defect (hotfix) | 25-01052627 |
| Same invoice# for same BA allowed to post to multiple BUs | Duplicate-validation gap across BUs | Defect | 24-00942635 |
| Vouchers stuck in **Post Pending** (assorted) | Frequently a **QPEC instance** died / process not running | Restart QPECs; clear/reschedule POSTWKFL | 22-00690577, 24-00955166, 25-01048250 |

**Fix recipe:**
1. Read the **exact post error** (open the "Could Not Post" voucher / the POSTWKFL process log + PQID). The error text routes the fix.
2. "Sum of lines ≠ total" or "GL not budgeted for AFE" on a final-approved voucher → the validation should have blocked at approve (23-00877861, code fixed) — fix the coding, and confirm the hard-error hotfix is deployed.
3. Bank-account-type errors in POSTWKFL → check **AP043 zero bank account type vs BR036/AP048** (24-00937529).
4. "Could Not Post" en masse with no obvious coding error → check **Accounts↔Attributes table sync** (23-00897008).
5. **Post Pending** that never completes → check whether a **QPEC** (Quorum process engine) instance is down; restart QPECs and confirm POSTWKFL is scheduled/running.

---

## 6. Cluster C — Invoice import errors (ADPUPLOAD / OpenInvoice / JIBLINK / QLS)

AP invoices arrive via **ADPUPLOAD** (with sub-steps **ADPIMPALLV** = allocate/validate, **APDIMGUPLD/ADPIMGUPLD** = image attach), fed by **OpenInvoice (OI)**, **JIBLINK**, or **QLS** land payments. Failures are step-specific.

| Failing step / signature | Root cause | Fix | Case |
|---|---|---|---|
| ADPUPLOAD fails at **APDIMGUPLD / ADPIMGUPLD** "no image file" on a client that does **not** import images | Image step shouldn't be a hard error for no-image clients | **Removed the ADPIMGUPLD step from ADPUPLOAD on the QClient layer** | 24-00985437 |
| **ADPIMPALLV** errors "Incorrect syntax near the keyword 'WHERE'" | Staging logic: looks for AFE→tier, else DOI→JIB deck; if no JIB deck and multiple REV decks it builds bad SQL | **Hotfix**; operationally, identify the property with no JIB deck but multiple REV decks | 25-01007131, 25-00999300 |
| ADPUPLOAD "Timeout expired … max pool size was reached" on a specific file | Per-file connection-attempt exhaustion (not the file's data/structure) | **Short-term:** override max connection attempts per file (split into SRC_DOC proved data was fine); **long-term:** code fix | 25-01011282, 25-01012535 |
| ADPUPLOAD **kills QPEC instances** each run (job still completes) | Process resource/handling defect | (resolution pattern unclear from mined case — restart QPEC; escalate) | 22-00818916 |
| ADPIMPORT batches in "Could Not Post" — cost center w/ no property/DOI got property+DOI auto-applied after a hotfix | Regression in ADP changes (2020.09.1.15) | **Script** to update the Could-Not-Post batches; fix the auto-apply | 22-00571406, 22-00571421 |
| OI invoices import with **bad coding** / cost center & AFE not in Quorum | OI mapping brings coding that doesn't exist in Quorum | Config / mapping correction; verify OI side | 25-01054722, 25-01026392 |
| JIBLINK voucher import — can't delete AP invoices / upload errors | Import metadata / mapping | Metadata check-in / config | 24-00994713, 24-00963392, 24-00976102 |
| ADPUPLOAD validation logs the **same message many times** (cartesian) | Validation query cartesian join | Fix (ADO #1721153/#1721469) | (perf) |
| Blank / $0.00 AP invoices from QLS imports | QLS→AP import defect | Defect | 24-00950299 |

**Fix recipe:**
1. Get the **PQID and the exact failing step** from the process log (ADPUPLOAD vs ADPIMPALLV vs APDIMGUPLD). The step names the fix.
2. **APDIMGUPLD** image failure on a no-image client → remove that step on the **QClient (client override) layer** (24-00985437).
3. **ADPIMPALLV** "near WHERE" → a **JIB-deck/DOI resolution defect** (25-01007131); operationally find the property that has REV decks but no JIB deck; the permanent fix is a hotfix.
4. **Connection-pool timeout** → confirm it's not the file (split the file by SRC_DOC and re-run; if pieces succeed, it's the pool). Short-term override the per-file max connection attempts; long-term code fix (25-01011282).
5. **Bad coding from OI/JIBLINK** → the import faithfully brought coding that doesn't resolve in Quorum; fix the OI/JIBLINK mapping or the missing AFE/DOI/cost-center, not the importer.

---

## 7. Cluster D — AP055 Batch Voucher Creation defects

The Classic AP055 screen (`QFrmBatchVoucherMaster.cs`, repo `Quorum.Upstream.QCFS.ClassicGUI`) is the most-cited AP screen. Several confirmed code defects.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Intercompany (I/C) lines deleted from POSTED vouchers** (business isn't deleting them; can't re-add; blocks void/reversal) | The `AutoDeleteOffset` code-block in **`QFrmBatchVoucherMaster.cs`** ran an UPDATE with **no `ID`/`IDBATVOUDETAIL`/`IDBATVOUMASTER` filter** — clicking the **I/C Offset** button on *any* voucher deleted I/C offset lines from **all** posted batches | Code fix: add an **`IDBATVOUMASTER` filter** so only the current batch's lines are deleted. Merged to 2022.04 + EQT version; **Hotfix 18 (10/31/2024)** | **24-00958104**; earlier 22-00687034 (patch, case 22-00256305) |
| Code-block **comment / owner / cost-center grid wipes prior entries** on tab/lookup | Grid tab+lookup interaction defect (worse when column order changed) | Hotfix (August Hotfix 2021.10) | 22-00687042 (orig 22-00261703) |
| `BatchVoucherCustomCodeBlockUpstream` fields **don't populate on a reclass** | Reclass didn't carry the custom code-block field | Code change to include the field on reclassification vouchers | 25-01025370 |
| AP Web manual voucher: **can't delete a draft**; editing required-blank fields **creates duplicate vouchers** (created 11 from 1) | A warning/error message **unselects the voucher**, so save creates a new one | **Workaround:** delete in **Classic** AP055; **long-term fix** 25-01050909 | 25-01050156, 25-01050909 |
| AP055 "Deleted row information cannot be accessed through the row" | Row-state defect | Defect | 23-00882512 |
| AP055 voucher not created — error related to `AUTO_CREATE_STATE_TAX_WH` | State-tax-withholding auto-create defect | Fix (ADO #1795333/#1796002, 2026.04) | (26-…) |
| AP055 **timeout** / reversal performance | Screen/query perf | Perf fixes (ADO #1625903, #1707005, #1720772) | 22-00867682 |

**Fix recipe:** for AP055 data-loss/odd-grid behavior, identify whether it's the **I/C offset delete** (the high-impact one — confirm Hotfix 18 / 2022.04+ is deployed; if I/C lines already deleted on posted vouchers, a data script is needed to restore them), a **grid tab/lookup wipe**, or the **Web "warning deselects voucher → duplicate"** pattern (workaround in Classic, long-term fix 25-01050909). Most AP055 defects are version hotfixes — confirm the client's build vs the fix's target version.

---

## 8. Cluster E — Payments: check, ACH, positive pay, void/reissue

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Single invoice paid on multiple checks** (lock that previously blocked an invoice already in an open check run didn't fire) | Check-run locking defect | Void the duplicate check; long-term fix tracked | 24-00953679, 24-00952419 |
| After **void on AP061**, payment type doesn't update on reissue (AP056 / AP157 mismatch) | Payment type was derived from the invoice payment type, not the check-run journal | **Code change** to derive Payment Type from the **check-run journal**; **April 2025 Hotfix** | 24-00986526 |
| **Positive Pay** export shows a **different decimal than the printed check** (rounding) | Positive-pay export rounding | **Check-form update + engineering code fix** for AP positive pay export | 25-01039786 |
| Positive Pay **file path** wrong / file not removed after processing / void showing in positive pay | Config (export path, post-process cleanup) | Correct file path / adapter config | 25-01031840, 25-01026110, 25-01035464, 26-01095699 |
| **Check MICR / written-amount blank line** on 2nd page | Check-form logic inserted a blank line when the written amount spilled to page 2 | Adjusted so no blank line is inserted | 22-00582863 |
| **ACH / NACHA**: paid wrong vendor (missing ACH validations on Voucher Maintenance); CCD vs PPD; savings-account NACHA; ACH email duplication | Mix of missing validations (defect) and bank-format config | Add ACH validations (defect); correct bank format/CCD-PPD config | 22-00553451, 22-00527107, 24-00988072, 23-00921303 |
| Check ZIP missing hyphen / phone cut off / address line 2 / signature missing | Check form + BA address config | §11 / check-form config | 25-01007996, 24-00939993, 25-01020780, 26-01079707 |
| AP void stuck in **Post Pending** | Void post issue | Often QPEC/POSTWKFL (§5) | 25-01016183, 25-01000541 |

**Fix recipe:** read whether it's a **defect** (multiple checks for one invoice 24-00953679; payment-type-on-void 24-00986526 → Apr-2025 Hotfix; positive-pay rounding 25-01039786) or **config** (positive-pay file path/adapter, bank format CCD/PPD, check-form ZIP/signature). For "paid wrong/duplicate," void the bad payment first, then pursue the long-term fix. Positive-pay adapter creation for new clients is a known onboarding task (ADO #1782337/#1782839 REP; #1820238 CTE).

---

## 9. Cluster F — Vendor / Business Associate (BA) master setup

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Can't save BA with **"Use as Vendor" flag**; vendor table broken | Creating a BA **lost the GLOBAL BUSINESS records** for the BA/USERKEY | **Script** to create/associate the missing vendor-table records | 25-01019914 |
| RCA of above: **creating a new BA corrupts the vendor table** when using "New" and **not closing the BA Web screen** after creation | BA Web screen didn't finalize before next action | **Code fix** — **Patch 15** | 25-01020116 |
| Vendor defaults not populating on AP055; BA has ACH term but AP055 shows Check; vendor term variances Web vs Classic | BA ↔ AP055 payment-term/type config mismatch | Align BA payment term/type config | 25-01048017, 24-00977168, 22-00874591 |
| Currency [USD] not defaulting on BA; BA multiple-contacts error; bank-number drop-down missing | BA screen/config | Config / defect | 22-00644794, 24-00989499, 26-01092936 |
| **Security** — user can't access AP/AFE, print check (AP061), create check run, positive pay, update BA Tax ID, run ORGCOSTGEN | Missing security objects in the user's groups | **Run security-object grant scripts** (e.g. "Added BA TAX ID security objects to BA Data Entry groups"; "ORG/BTYP/QRA to groups 70000/90671012"; ORGCOSTGEN access) | 25-01042111, 25-01048054, 25-01042097, 23-00906458, 23-00910878 |

**Fix recipe:** for "can't save BA / vendor table broke," **backfill the missing GLOBAL BUSINESS / vendor rows** with a script (25-01019914) and confirm the **Patch 15** code fix is in (25-01020116) so it stops recurring — and tell users to **close the BA Web screen after creating a new BA**. For BA-vs-AP055 payment mismatches, fix the BA payment-term/type config. AP **security** cases are routine: run the appropriate **security-object grant script** for the user's groups (these are config, not defects).

---

## 10. Cluster G — 1099 reporting

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **1099 amounts doubled** on AP170 (Box 3 / Box 1) | 1099 staging/overlay double-count | A **validation on AP151** checking state-box vs fed-box value; coded check on box values | 23-00908616, 23-00926296 |
| **1099 exported AP amounts ≠ actual paid** | 1099 calc bug (v16) | **Patch** for the 1099 bug | 22-00612483 |
| 2025 1099 **MISC mapped to Box 7 instead of Box 17** (didn't subtotal) | BU defaults to Box 7; affected GL accounts had **no State Box override in AP151 (XREF_1099)** → fell back to BU default | **Update AP151 account-level overrides**: set Form Type (MISC) + State Box (Box 17), then re-run staging/export | 26-01067238 |
| Can't change **1099 flag in AP156** ("voucher not most up to date, requery") on any posted voucher | Invalid stale-record error | **Patch** | 22-00544814, 22-00527045, 22-00647295 |
| **QSTG1099OV / QSTG1099EX / QP073** timing out | Performance on large 1099 runs | Perf/config (see §14) | 23-00882354, 23-00881122, 22-00853230, 24-00937123 |

**Fix recipe:** **doubled** amounts → 1099 staging double-count; the durable fix was an **AP151 validation** (23-00908616/926296). **Wrong box** (Box 7 vs 17) → almost always a **missing AP151 (XREF_1099) State Box override** on the GL accounts; set Form Type + State Box at the account level and re-run (26-01067238). **Export ≠ paid** → version patch (22-00612483). **AP156 flag-update errors** → patch. **QSTG1099 timeouts** → performance (often config/index/scope), see §14.

---

## 11. Cluster H — Vendor address / ZIP-state alignment

A recurring data + form-formatting cluster on vendor addresses surfacing on **checks** and the **AP155** vendor screen.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **AP155**: the **State value appears in the ZIP column** and the State column is blank (multiple BAs) | Misaligned vendor address data (state/zip columns shifted) | **PRD data-align script** (run in UAT then PRD); **long-term fix in Upstream 2025.04 Hotfix (April 2026)** | 26-01089614, 26-01091641, 26-01093457 |
| Check ZIP printed without hyphen (`586404101` vs `58640-4101`) | ZIP mask on the BA web screen | **Remove the ZIP mask** on the BA web screen so users can enter the hyphen | 25-01007996, 25-01089614, 25-01049189 |
| **Returned checks** for ZIP-code formatting | Same ZIP-format family | Check-form / BA address fix | 26-01083748 |
| Phone number / address line 2 cut off on check form | Check-form field width/layout | Check-form config | 24-00939993, 25-01020780 |
| Misplaced ZIP/State on **vendor check inquiry (AP157-family)** screen | Same data/format family | Script + form fix | 26-01093457 |

**Fix recipe:** for "state in the ZIP column" on AP155/vendor screens, run the **data-alignment script in UAT, validate, then PRD** (26-01089614/091641), and confirm the **2025.04 Hotfix** for the durable fix. For check ZIP-hyphen, **remove the ZIP mask** on the BA web screen (25-01007996). These are address-display issues, not payment-amount defects.

---

## 12. Known ADO Items

> All in project **QuorumSoftware** (repo `Quorum.Upstream.QCFS.*`). Titles abbreviated; confirm target build in the QCFS release notes / hotfix list.

| ADO # | Type / State | Title (abbrev.) | Cluster |
|---|---|---|---|
| **#1096545** | Bug / Closed | Classic QCFS — AP055 error updating a voucher with missing vendor data | §7 |
| **#1355138 / #1383633** | Bug / Req / Closed | SRC — AP055 Batch Voucher Creation: vendor picklist / lookup issue | §7 |
| **#1410429** | Task / Closed | Classic QCFS — AP055 "Object cannot be cast from DBNull" after attach | §7 |
| **#1416517** | Bug / Closed | ENR — Classic QCFS — AP055 extra Reject button for Post Pending vouchers | §5/§7 |
| **#1625903 / #1707005** | Bug / Closed | SRC — AP055 Batch Voucher Creation screen **timed out** | §7 (perf) |
| **#1685515** | Bug / Closed | 2024.10 — AP055 Validate button disabled for imported vouchers in Classic | §7 |
| **#1720772** | Bug / Closed | AP055 — **Reversal voucher performance** | §7 (perf) |
| **#1775588** | Task / Closed | QCFS — error thrown only at posting, skips validation at Validation/Approval | §5 |
| **#1795333 / #1796002** | Bug / Task / Closed | 2026.04 — AP055 voucher not created (`AUTO_CREATE_STATE_TAX_WH`) | §7 |
| **#1721153 / #1721469** | Req / Task / Closed | ADPUPLOAD — validation query **cartesian** logging duplicate messages | §6 |
| **#1730937** | Requirement / Closed | CEN — Metadata check-in for **ADPUPLOAD performance** | §6 |
| **#1744756** | Bug / Closed | APH — **ADPUPLOAD** failing with Object-reference error when coded to control account | §6 |
| **#1767791** | Script Deployment / Closed | CNR — Deploy **ADPUPLOAD script** in PRD | §6 |
| **#1789707** | Bug / Closed | 2026.04 — ADPUPLOAD documents not displayed as attached after import | §6 |
| **#1805503** | Requirement / Closed | EIG — Commit ADPUPLOAD metadata | §6 |
| **#1782337 / #1782839** | Requirement / Task / Closed | REP (Riley Exploration Permian) — **AP Positive Pay adapter** creation | §8 |
| **#1782495** | Task / Closed | Re-visit PII on **positive pay and ACH** functionality | §8 |
| **#1820238** | Feature / Proposed | CTE — CTOC Energy — AP and Revenue **Positive Pay adapter** | §8 |

> Many actionable AP cases close **operationally** (reusable PRD data script for ghost vouchers; security-object grant scripts; AP151 override; AP043 config) **without a product WI**, or as a **"<month> Hotfix on 20xx.xx"** with no public WI #. Notable code fixes named in resolutions: **AutoDeleteOffset IDBATVOUMASTER filter** (Hotfix 18, 24-00958104); **payment-type-from-check-run-journal** (April 2025 Hotfix, 24-00986526); **BA-creation vendor-table** fix (Patch 15, 25-01020116); **final-approve hard-error validations** (23-00877861). Confirm the exact build before stating fix availability.

---

## 13. Diagnostic SQL

> **Caveat:** QCFS is SQL Server. Table/column names below are taken from case repro text + the confirmed `QFrmBatchVoucherMaster.cs` code; **verify against the client DB before scripting**, and always run a verify-SELECT before any UPDATE/DELETE, wrapped in a transaction. Ghost-voucher and BA-backfill scripts are normally PRD-only and reuse a prior approved script — get it reviewed.

```sql
-- A. AP055 batch voucher + GL distribution (I/C lines, deleted flag) — the AutoDeleteOffset defect (§7)
SELECT * FROM BATCHVOUCHERMASTER       WHERE ID = '<idbatvoumaster>';
SELECT * FROM BATCHVOUCHERDETAIL       WHERE VOUNUM = '<VM…>';
SELECT * FROM BATCHVOUCHERGLDISTRIBUTION WHERE IDBATVOUDETAIL = '<idbatvoudetail>';
--   Red flag: I/C offset rows with DELETED='1' on a POSTED batch the user didn't touch → 24-00958104.

-- B. Ghost / orphaned workflow rows for a user's "Awaiting Approval" inbox (§4)
--    Find the WF instance whose state is open but whose voucher is posted/paid/perm-rejected.
--    (APWORKFLOW / WF instance + inbox-view tables — confirm names in the client DB.)
--    Get the voucher numbers + approver from the inbox screenshot, then locate the stale WF rows.

-- C. Vouchers in Could Not Post / Post Pending (§5) — review the post error + coding
--    Read the POSTWKFL process log by PQID first; then inspect the voucher coding (AFE/DOI/cost center).

-- D. 1099 box mapping override — the Box 7 vs Box 17 fallback (§10)
--    AP151 / XREF_1099 holds per-GL-account Form Type + State Box overrides; BU default applies when missing.
SELECT * FROM XREF_1099 WHERE /* account / BU */;   -- confirm missing State Box override (26-01067238)

-- E. BA "use as vendor" / vendor-table backfill (§9)
--    Confirm GLOBAL BUSINESS / vendor rows exist for the BA/USERKEY; backfill if dropped (25-01019914).

-- F. AP155 address column misalignment (§11) — state value landing in the ZIP column
--    Identify BAs where the ZIP column holds a 2-char state and State is blank; align with the approved script.
```

---

## 14. Expected-Behavior / User-Education FAQ

~250 Training + ~213 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Voucher/invoice stuck in Draft / WIP — delete it" | If never submitted, it's a **draft the user can delete** (or a quick PRD delete) — not the ghost-voucher defect | 26-01105099, 25-01035426 |
| "MyQuorum AP won't let me select an **inactive BA** in voucher search" | **Working as designed** — inactive BAs are filtered; reactivate the BA or use a different filter | 26-01103927 |
| "How do I produce a **NACHA** file / re-export a Sent ACH batch / create additional payment types / ACH effective-date logic?" | **Training** — walk through AP061 ACH/NACHA, payment-type code tables, effective-date config | 26-01082989, 26-01098231, 26-01094872, 26-01094867 |
| "How do I **save queries** / what's the **PO field character limit** / GL reporting?" | **Training** — screen/query usage | 26-01097087, 26-01096383, 26-01085078 |
| "Help with our **first-time 1099 processing** / 1099 walkthrough" | **Training** — schedule a QCFS SME walkthrough of QSTG1099OV/EX, AP151, AP170 | 25-01049089 |
| "Once we **close the fiscal year**, can we ever post back into it?" | **Expected** — closed periods are locked; reopening is a controlled period-close action | 25-01015041 |
| "**Invalid AFE/property combination** on AP voucher" / "Cost Center Tier error" | **Customer Error / coding** — the AFE-property-DOI combo or cost-center tier isn't valid; fix the coding, not the app | 25-01062554, 25-01039117 |
| "**QSTG1099 / QP073 timing out**" | Often **volume/performance** — narrow the run scope / off-peak; not always a defect | 22-00853230, 23-00882354 |
| "**Batch locking** behaving strangely / locked batch" | Usually a user has the batch open or a stale lock — verify before scripting | 25-01007016, 25-01041190, 22-00996916 |
| "**QPECs** need restarting / process didn't run for 2 days" | Operational — restart the QPEC process engine instances | 22-00513264, 24-00955166, 25-01048250 |
| "AP055 question / how to change AFE number / multiple external imports" | **Training** on AP055 usage | 25-01023268, 25-01053648, 26-01101359 |

**Tell-tale it's user/expected:** a "stuck" voucher that's still a **Draft** (deletable), an **inactive BA** correctly filtered out, a **how-do-I** (NACHA, payment types, save queries, 1099 first run), an **invalid AFE/DOI/cost-center coding** error (fix coding), a **closed-period** question, or a **QPEC restart**. Confirm the voucher's real status and the coding before treating it as a defect.

---

## 15. Key Screens, Processes & Repos

### Screens
| Screen | Purpose |
|---|---|
| **AP055** | Batch Voucher Creation (Classic) — enter/code vouchers into batches (BV…/BCK…). `QFrmBatchVoucherMaster.cs`. |
| **AP Full Inbox / AP Web** | Approval workflow — route, approve, reject, Route & Return; final-approve → POSTWKFL. |
| **AP056** | Voucher Maintenance — open items, approve-to-pay, payment type. |
| **AP061** | Check / payment run — print checks, ACH/NACHA, positive pay export, void/reissue. |
| **AP150 / AP155 / AP156 / AP157 / AP159** | Vendor/BA & payment screens — AP150 emails/remittance, AP155 vendor address, AP156 1099 flag, AP157 payment/check inquiry, AP159 BA number control. |
| **AP151 (XREF_1099) / AP170** | 1099 account-box overrides / 1099 totals by box. |
| **AP043 / BR036 / AP048** | Bank account / zero-bank-account-type config (POSTWKFL dependency). |

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **POSTWKFL** | Post approved vouchers → GL | "Post Pending" / "Could Not Post"; depends on AP043 bank config; needs QPEC running |
| **ADPUPLOAD** | AP invoice import | Sub-steps **ADPIMPALLV** (allocate/validate → AFE tier / JIB deck / DOI), **APDIMGUPLD/ADPIMGUPLD** (image attach) |
| **OpenInvoice / JIBLINK / QLS** | Invoice/land-payment sources feeding AP | Bad coding here surfaces as AP errors |
| **QSTG1099OV / QSTG1099EX** | 1099 stage/overlay & export | Perf-sensitive on large runs; AP170 displays |
| **QP073 / QP074 / QEMAIL** | AP report/import job launch & email | Timeouts/email failures common (config) |
| **QPEC** | Quorum process engine instances | Restart when Post Pending / imports stall |

### Repos (confirmed via ADO code search)
- **`Quorum.Upstream.QCFS.ClassicGUI`** — Classic AP screens; **`/Quorum.QCFS.AP/QFrmBatchVoucherMaster.cs`** is AP055 (the `AutoDeleteOffset` I/C bug, 24-00958104).
- **`Quorum.Upstream.QCFS.*`** — QCFS Web, metadata, batch/process, database (procs for ADPUPLOAD/1099/POSTWKFL). Client overrides live on a **QClient layer** (e.g. removing the ADPIMGUPLD step for a no-image client, 24-00985437) — **always check the client/QClient layer first**, since many AP fixes are client-specific (import steps, positive-pay adapters, check forms, security objects).

---

## 16. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A confirmed code path is wrong: **AutoDeleteOffset** deleting I/C lines across posted batches (24-00958104, Hotfix 18); **payment type not derived from check-run journal** on void/reissue (24-00986526, Apr-2025 Hotfix); **BA-creation corrupts vendor table** (25-01020116, Patch 15); **ADPIMPALLV "near WHERE"** JIB-deck/DOI defect (25-01007131); **positive-pay rounding** (25-01039786); **1099 doubled / export≠paid** (23-00908616, 22-00612483); **single invoice on multiple checks** (24-00953679); **final-approve validations not hard errors** (23-00877861).
- Provide: **screen + exact error text**, **PQID + failing step** (for ADPUPLOAD/POSTWKFL), voucher/batch numbers + BU, client + version/build, and a repro. Confirm fix availability and target build in the QCFS hotfix/release notes.

**Handle as Configuration / Cloud Ops when:**
- **POSTWKFL** bank-account-type errors → **AP043 vs BR036/AP048** (24-00937529); **Accounts↔Attributes** sync (23-00897008).
- **Positive-pay / ACH** file path, adapter, bank format CCD/PPD; **check-form** ZIP-mask/signature/address (25-01007996, 24-00939993).
- **AP151 (XREF_1099)** state-box overrides (26-01067238); **1099/QP073 timeouts** (scope/off-peak).
- **Security** — run the appropriate **security-object grant script** for the user's groups (AP/AFE access, check print, positive pay, BA Tax ID, ORGCOSTGEN) — these are routine config (25-01042111, 25-01048054, 23-00906458).
- **QPEC restart** when imports/posts stall.

**Handle with a reusable PRD data script (low-risk, recurring) when:**
- **Ghost / phantom / stuck** vouchers in the inbox (§4) — reset orphaned voucher to Draft / delete the abandoned WF row / remove WF locks (22-00582908, 23-00907599, 24-00944211, 25-01005671). Reuse the prior approved script; verify-SELECT in a transaction; push the version hotfix if it recurs.
- **BA vendor-table backfill** (25-01019914) and **AP155 address-column re-alignment** (26-01089614/091641) — run in UAT, validate, then PRD; confirm the long-term hotfix (Patch 15 / 2025.04).

**Handle as Training / Expected behavior (no fix):** see §14 — draft vouchers the user can delete, inactive-BA filtering, how-do-I (NACHA/payment types/save queries/1099 first run), invalid AFE/DOI/cost-center coding, closed-period questions, QPEC restarts, batch locks. Verify the voucher's real status and the coding before treating it as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 2,517 closed QCFS "Accounts Payable (AP)" SF cases — 446 actionable (Software Defect 248 + Application Configuration 180 + ChangeConfig 18) mined for fix recipes, plus ~60 Training/Customer-Error cases for the FAQ. Code location confirmed: `Quorum.Upstream.QCFS.ClassicGUI /Quorum.QCFS.AP/QFrmBatchVoucherMaster.cs` (AutoDeleteOffset). ADO work items #1096545, #1355138/#1383633, #1410429, #1416517, #1625903/#1707005, #1685515, #1720772, #1775588, #1795333/#1796002, #1721153/#1721469, #1730937, #1744756, #1767791, #1789707, #1805503, #1782337/#1782839, #1782495, #1820238.*
*Companion (if present): SKILL_QCFS_General_Ledger.md, SKILL_QCFS_Accounts_Receivable.md, SKILL_QCFS_Bank_Reconciliation.md, REPO_INVENTORY / CONFIG_REFERENCE.*
