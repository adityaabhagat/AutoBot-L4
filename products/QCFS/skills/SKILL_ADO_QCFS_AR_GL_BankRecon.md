# SKILL: QCFS Accounts Receivable / General Ledger / Bank Reconciliation — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QCFS (Quorum Upstream Financial Accounting — AP/AR/GL/Bank-Recon, the "eSuite" financial back end)
**Source:** Azure DevOps bugs (NOT Salesforce). Area Path `QuorumSoftware\Engineering\Financials`, `WorkItemType = Bug`, `State IN (Closed, Resolved)`, title matching receivable / AR0 / AR3 / general ledger / GL0 / journal / bank recon / BR0 / period close / WF005.
**Scope:** The QCFS posting/accounting pipeline — **POSTWKFL / PSTWKSPLT** (the post-workflow batch engine that posts AP vouchers, GL journal entries, AR invoices, check runs, deposits/payment applications, and bank-recon batches to the General Ledger and updates account balances), **period close / balance refresh** (SoftClose/Close/BalanceRefresh business-service runs), **AR** screens (AR076 batch invoice, AR086/AR308/AR090, payment application/netting), **GL** screens (GL025 batch journal entry, GL014 balances, JB500), and **Bank Recon / BK** screens (BK040, BR005). Sibling areas overlap heavily (AP voucher screens AP055/AP061/AP171, AFE=QCA) — those bugs are noted but de-scoped here.

> **Evidence base:** 184 Closed/Resolved Financials bugs matched the WIQL title filter; ~45 deep-read (description + repro + dev comments + linked PRs/commits). Most of the 184 are eSuite UI / V2UI cosmetic or AP-voucher (QCFS adjacent) and metadata items; the **actionable QCFS AR/GL/Bank-Recon core** is ~35 bugs concentrated in two defect families: **(1) POSTWKFL/PSTWKSPLT concurrency — fast-track double-post and account-balance/GL-transaction deadlocks**, and **(2) POSTWKFL "Could Not Post" data/validation failures** (netting $0 lines, BA params, duplicate AR lines, missing sysgen metadata). Every root-cause claim below cites a real ADO Bug ID and, where a fix shipped, the PR/commit + iteration→release. The dev voice throughout is **Ben Weis / Jimmy Bidwell (engineering)** and **Harshal Katkar (QA)**.

> **Fix-version note:** ADO `Microsoft.VSTS.Build.IntegrationBuild` is **empty on every one of these bugs** — do NOT cite an IntegrationBuild number. Derive fix availability from the **iteration path** (e.g. `Product Development\25.16`–`25.19` → **2025.04** per Ben Weis's "Merged to 2025.04" comments; `Sprint NN` = old v16/v17 maintenance), the **tags** (`2022.04 QA`, `2023.04 Regression`, `Robot RN 2026.04`), and the **PR/commit** links. Confirm exact build in `Quorum.Upstream.QCFS.Web` release notes before telling a client.

---

## TABLE OF CONTENTS

1. [Quick Triage](#1-quick-triage)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — POSTWKFL/PSTWKSPLT account-balance & GL deadlocks (HIGH VALUE, 2025.04)](#4-cluster-a)
5. [Cluster B — Fast-track double-post / "Post In Progress" status](#5-cluster-b)
6. [Cluster C — POSTWKFL "Could Not Post" data & validation failures](#6-cluster-c)
7. [Cluster D — $0 netting lines (cross-area: QRA → QCFS)](#7-cluster-d)
8. [Cluster E — POSTWKFL/PSTWKSPLT "errors" that are NOT code defects](#8-cluster-e)
9. [Cluster F — GL025 / AR076 attachments & batch-screen UI](#9-cluster-f)
10. [Cluster G — Performance (POSTWKFL / JBPREPROOF / 1099 / Close All)](#10-cluster-g)
11. [Fix-Version Matrix](#11-fix-version-matrix)
12. [Diagnostic Pointers (SQL & tables)](#12-diagnostic-pointers)
13. [Key Code, Processes & Repos](#13-key-code-processes--repos)
14. [Escalation Guidance](#14-escalation-guidance)

---

## 1. Quick Triage

| Symptom (what the user/QA reports) | Likely cause | First check |
|---|---|---|
| `Transaction (Process ID NNN) was deadlocked … chosen as the deadlock victim` during POSTWKFL/PSTWKSPLT; account balances not updated | POST balance-refresh overlapping a close/refresh job, or bulk-insert lock-hint contention on `GENERALLEDGERTRANSACTION` | §4 — confirm build ≥ 2025.04 (deadlock-prevention split: #1739552, #1741103) |
| Batch posts twice / picked up by both POSTWKFL and the fast-track post | Fast-track batch left in `POSTPEN` and grabbed by a long-running POSTWKFL | §5 — "Post In Progress" status fix #1618436/#1623794 (2023.04) |
| Batch stuck in **Post In Progress** | Fast-track/splitter job died mid-post | §5 — `PSTPRGFIX` cleanup process (#1749964, 2025.04) |
| POSTWKFL "Could Not Post" on an **AR076 invoice / netting batch**; `The applied amount + current amount must approach zero` | A **$0-amount detail line** applied to a non-zero open item (QRANET netting) | §7 — QRA-side; AR044 "allow non-zero" config = client workaround |
| POSTWKFL error: `Cannot find column [IDOPENITEM_APPLY]` / object reference, AR batch | Duplicate AR line item (applied > open-item amount); misleading error | §6 — delete the duplicate line + fix totals (#113083) |
| POSTWKFL `@ba_no` param error on a **voucher reversal** | `SHOW_APPROVAL_FIELDS` config on; vendor user key not checked for null | §6 — code fix 2022.04 (#1446832) |
| Check-run creation batch errors when vendor has **>1 BA contact** | Multi-contact handling in check-run post | §6 — fixed 2024.10 (#1679169) |
| POSTWKFL "stops processing on error" on the **scheduler** (endpoint/connection) | DEBUG mode on the scheduled definition makes the MT unresponsive | §8 — turn DEBUG off (#104443) |
| POSTWKFL fails with **"LOCK"/"invalid objects"/"could not acquire lock"** after upgrade or while ARCCOREINT runs | Missing **sysgen/metadata** post-upgrade, or **by-design lock** vs ARCCOREINT | §8 — usually NOT a product code bug |
| GL025 attachment won't open / AR076 delete-attachment error | Screen document-handling defect | §9 — fixed 2026.04 (#1788555), 2025.04 (#1786000) |
| POSTWKFL / JBPREPROOF / 1099 / Close-All slow or timing out | Missing DB index / unfiltered SQL / undersized tempdb | §10 |

---

## 2. Pipeline & Concepts

```
[AP055 vouchers] [GL025 journal entries] [AR076 invoices / AR086 payment apps / netting]
[AP061/AP171 check runs] [BR005 bank-recon batches]
      │  user clicks Approve → Approved Final → Post (Post Date set)
      ▼  batch status = POSTPEN ("Post Pending")
   POSTWKFL  (scheduled or QP073 manual; web = eSuite Batch Processes)
   PSTWKSPLT (Schedule Post Workflow Splitter — parallel child jobs for throughput)
      │  posts batch → GENERALLEDGERTRANSACTION (insert-only) ; then balance refresh
      ▼
[General Ledger / Account Balances (GL014)]  →  period SoftClose / Close (SM006)
```

### Key terms (Quorum/QCFS vocabulary)
- **POSTWKFL** = "Schedule Post Workflow" — the batch process (Process ID `POSTWKFL`) that picks up every batch in `POSTPEN` status and posts it to the GL. Runs scheduled or manually from **QP073** (classic) / eSuite Batch Processes (web). The single busiest QCFS process and the source of most defects here.
- **PSTWKSPLT** = "Schedule Post Workflow Splitter" — splits the POSTWKFL workload into parallel child jobs for large clients.
- **BUSSVCRUN** = Business Service Run — the engine that executes a single posting/close action. `RunWorkflowAction("VoucherWorkflow", id, WorkflowAction.Post, 0)` posts a batch; `SoftClose(...)` / `Close(...)` close a period.
- **Fast track / direct post** = when a user clicks Post on a batch while a *long-running* POSTWKFL is already running (config `LONG_RUNNING_POSTWKFL_MINUTES`), the screen launches BUSSVCRUN directly instead of waiting. This created the double-post race fixed in §5.
- **Post status flow:** `Approved Final` → `Post Pending (POSTPEN, status 90)` → `Post In Progress` (intermediate, fast-track only) → `Posted` *or* `Could Not Post`.
- **Account balance / close processes (added 2025.04 for the deadlock fix):** `BSVCLOSE` (SoftClose/Close), `BSVCRFRSH` (BalanceRefresh), `PSTWKBAL` (balance refresh launched *during* POSTWKFL), `BSVPOST` (fast-track / null-post-date post), `BSVBCHRFSH` (BatchRefresh), `PSTPRGFIX` (cleanup of stuck Post-In-Progress).
- **ARCCOREINT** = the AR/Core-interface archive/purge process; moves `STRAN`→archive. Shares a lock with POSTWKFL/PSTWKSPLT so they cannot run concurrently (#1667696).
- **Netting / QRANET** = revenue (QRA) nets a receivable against a payable and sends the open items back to QCFS for an AR076 batch; $0 net lines break the post (§7).
- **QXREF_AFE_VALID_POST_STATUS, QARCH_CTRL_PROCESS, QARCH_SEC_OBJECT/SEC_GRP_PRIVILEGE, QARCH_LOCK_MASTER(_PROCESS), QARCH_CNFG_CTRL** = the metadata/config/lock tables that POSTWKFL reads; **missing rows here cause most "POSTWKFL errors" after an upgrade** (§8), not a code bug.
- **Process Queue ID (PQID)** = key to the run log (`QARCH_PROCESS_MSG_LOG`). Always get the PQID + the exact error text.

---

## 3. Decision Tree

```
QCFS POSTWKFL / AR / GL / Bank-Recon case
│
├─ "Deadlock victim" / balances wrong after POSTWKFL or close?
│     → §4  Account-balance/GL deadlock. Fixed 2025.04 (#1739552 + #1741103). Confirm client build.
│
├─ Batch posted twice, or stuck in "Post In Progress"?
│     → §5  Fast-track double-post. "Post In Progress" status (2023.04 #1618436/#1623794) + PSTPRGFIX cleanup (2025.04 #1749964).
│
├─ POSTWKFL ran but batch = "Could Not Post"? (process itself completes)
│   ├─ AR076 / netting "applied amount must approach zero"     → §7  $0 netting line (QRA-side, #184253/#1379243)
│   ├─ "Cannot find column [IDOPENITEM_APPLY]" / dup AR line    → §6  delete duplicate line (#113083)
│   ├─ "@ba_no" param error on voucher reversal                 → §6  SHOW_APPROVAL_FIELDS null vendor (#1446832, 2022.04)
│   ├─ Check-run batch + vendor has >1 BA contact               → §6  (#1679169, 2024.10)
│   └─ Missing prop/tier validation only at post (AP171→AP055)  → §6  validation-timing gap (#1550783, by-design-ish)
│
├─ POSTWKFL "error" but the batch actually POSTED, or after upgrade, or vs ARCCOREINT?
│     → §8  NOT a code defect: missing sysgen/metadata (QARCH_CTRL_PROCESS / QXREF_AFE_VALID_POST_STATUS),
│           DEBUG-mode scheduler hang, or by-design lock. Check metadata/config first.
│
├─ GL025 attachment won't open / AR076 delete-attachment error / copy-doc inconsistency?
│     → §9  Document-handling screen defects (2026.04 #1788555, 2025.04 #1786000; copy diff = by-design #1655846)
│
└─ Slow / timeout (POSTWKFL, JBPREPROOF, 1099 override, Close All Companies)?
      → §10  Index/SQL/tempdb. Several FinancialsPerformance fixes; some "fixed" by infra (memory/tempdb).
```

---

## 4. Cluster A — POSTWKFL/PSTWKSPLT account-balance & GL deadlocks (HIGH VALUE, fixed 2025.04)

**The marquee QCFS posting defect family.** Under concurrency, the posting process and the period-close/balance-refresh process both try to update the same account-balance rows (or bulk-insert into `GENERALLEDGERTRANSACTION`), producing SQL deadlocks that abort the post and leave **account balances not updated**.

**Symptom (verbatim, #1739552 / #1741103):**
```
Transaction (Process ID 413) was deadlocked on lock | communication buffer | generic waitable object
resources with another process and has been chosen as the deadlock victim. Rerun the transaction.
```
- **#1739552 — POSTWKFL Account Balance deadlock** [Closed, iter 25.19]. Root cause (Ben Weis): overlap of `POSTWKFL` balance refresh with `BUSSVCRUN → SoftClose/Close` and `BalanceRefresh` actions all hitting the same account-balance info under the **same PROCESS_ID**. Fix: gave the close/soft-close/post/refresh actions **their own PROCESS_IDs and locks**, and moved the post-time account-balance refresh into a **separate sequential child job (`PSTWKBAL`)** so refreshes run one-at-a-time and never inside the POSTWKFL transaction (a plain lock couldn't be used because it would break fast-track post). New processes: `BSVCLOSE / BSVCRFRSH / PSTWKBAL / BSVPOST / BSVBCHRFSH / PSTPRGFIX`. PRs 113962/113965/113966/114361/114412/117015-117020. **Merged to 2025.04.**
- **#1741103 — PSTWKSPLT deadlock on `GENERALLEDGERTRANSACTION`** [Closed, iter 25.19, RN 2026.04]. Root cause: the bulk-insert lock **hint** applied to update-heavy tables was being applied to `GENERALLEDGERTRANSACTION`, which is **insert-only (never updated)** — the hint caused contention. Fix: control whether the hint is used based on the table (don't lock-hint the insert-only GL table). Required a **QFC platform hotfix** (`Quorum.QFC.Core → 17.25.7`, then 17.28.2 for the QCFS consumption). PRs 114357/114620/117011. **Merged to 2025.04** (release-noted 2026.04 for the splitter).
- **#1743547 — Reproduce the POST-vs-close deadlock** [Closed/Rejected]: logged to reproduce; could not time a repro in develop. Dev note: **seen by CEN (2023.04) and MAC (2024.10)** in the field. Closed because #1739552 + #1745586 + #1749964 cover the actual fix.

**Supporting (same family, 2025.04):**
- **#1745586** — add **cancel-prevention metadata** for the new BSVCLOSE/BSVCRFRSH/PSTWKBAL/BSVPOST/BSVBCHRFSH processes (so a user can't cancel a half-done close/balance run). [iter 25.16]
- **#1749964** — add **security objects** for the new processes (incl. `PSTPRGFIX`) matching `BUSSVCRUN` in `QARCH_SEC_OBJECT` / `QARCH_SEC_GRP_PRIVILEGE`. [iter 25.17]
- **#1667696** (Requirement) — created the **shared lock** so `ARCCOREINT`, `POSTWKFL`, `PSTWKSPLT` cannot run concurrently (`LOCK_TYPE_CD = 'ARCNT_WKFL'` in `QARCH_LOCK_MASTER`). Configurable via `QARCH_CNFG_CTRL` keys `DEFAULTMAXLOCKATTEMPTS` / `DEFAULTTIMEBETWEENLOCKATTEMPTS`. [2024.15] — see §8 for the by-design follow-on.

**Triage:** "deadlock victim during POSTWKFL/close" + "balances didn't update" → confirm the client is on **2025.04 or later**. If older (esp. **CEN 2023.04, MAC 2024.10**), this is the known issue — the fix is a 2025.04 upgrade (plus the QFC 17.25.7/17.28.2 platform piece for the splitter). No data workaround beyond serializing the jobs (don't run close/refresh while POSTWKFL is running).

**Bug IDs:** 1739552, 1741103, 1743547, 1745586, 1749964, 1667696. **Linked SF cases:** none in titles (internal/E2E-found; field clients CEN, MAC).

---

## 5. Cluster B — Fast-track double-post / "Post In Progress" status (fixed 2023.04, hardened 2025.04)

**Symptom:** a batch gets **posted twice**, or a fast-tracked batch errors out one of two concurrent posting paths.

- **#1618436 — Fast-track batches picked up by POSTWKFL and erroring** [Closed, iter 23.21]. Root cause: when a user posts a batch directly (fast track) it sits in `POSTPEN` until done; a concurrently running `POSTWKFL`/`BUSSVCRUN` could **also** grab the same `POSTPEN` batch → double post / error. Fix: added an intermediate **"Post In Progress"** workflow status that the direct post stamps so POSTWKFL **filters it out**. Triggered only when a **long-running** POSTWKFL exists (config `LONG_RUNNING_POSTWKFL_MINUTES`). Covers GL025, AP055, AP061, AR076, AR308, AR086, BR005. PRs 88951/88952/89114.
- **#1623794 — myQ AP: apply "Post In Progress" to the web** [Closed, iter 23.21]: same fix ported to myQuorum AP web. Status goes `Post In Progress` → `Posted` when BUSSVCRUN completes.
- **#1669576 — "Post In Progress" stuck possibility** [Closed/Duplicate, iter 25.17]: if the fast-track/splitter job dies, a batch could be stranded in `Post In Progress`. Resolved by the **`PSTPRGFIX`** cleanup process (delivered under #1749964, 2025.04). Moving a batch back to `Approved Final` from `Post In Progress` must first verify (via the QUE table) that no BUSSVCRUN / POSTWKFL child job is still running for it, or you re-introduce the double-post race.

**Bug IDs:** 1618436, 1623794, 1669576 (+ PSTPRGFIX via 1749964). **SF cases:** none in titles.

---

## 6. Cluster C — POSTWKFL "Could Not Post" data & validation failures

The process **completes**, but a batch lands in **"Could Not Post"** (status reflects a final validation that fires only at post time). These are genuine code/data defects with shipped fixes.

| Bug | Symptom | Root cause | Fix / build |
|---|---|---|---|
| **#1446832** | Voucher **reversal** → POSTWKFL `@ba_no` param error (PQID e.g. 6834157) | Config `SHOW_APPROVAL_FIELDS` on → code validates vendor approval but **doesn't check the vendor user key is non-null** on the row (tied to #1407749) | Code fix, **2022.04** (PRs 67766/67769/67787/70570/70675) |
| **#1445857** | QP073 POSTWKFL completes with errors re `QXREF_AFE_VALID_POST_STATUS` | Missing **sysgen metadata** on the wrong layer (ENGS instead of an UPS-owned layer) — Book-to-Pending-AFE cross-ref | Moved sysgens to UPS layer + DB-snapshot fix, **2022.04** (PRs 67465/67466/68046/68047) |
| **#1679169** | Check-run creation batch (AP061/AP171) errors when **vendor has >1 BA contact** | Multi-contact handling on check-run post | Code fix, **2024.10** (PRs 99398/101366) |
| **#113083** | POSTWKFL `Cannot find column [IDOPENITEM_APPLY]` / object ref on AR batch (CNR) | A **duplicate AR line** from QRA made applied-amt > open-item amt; error text is misleading | Data fix: delete the dup `BATCHINVOICELINEITEM` and re-total master/detail; error message flagged as needing improvement |
| **#1584004** | AR076 "Could Not Post" + **duplicate Reject/Post buttons** after re-query | Final post-time validation failed (expected when validations fail) + UI re-render dup | Confirmed working 2023.04; the dup-button is a separate minor UI issue (Ben Weis: "could-not-post is the final safety check") |
| **#1550783** | Voucher created via **AP171 manual check** validates/approves clean but POSTWKFL fails on missing **prop/tier** | Validation runs at post, not at validate/approve, for the AP171→AP055 path | Logged to core backlog; treat as validation-timing gap |
| **#57354** | Unable to post **JIB to Inbox** status on AP vouchers not matching batch workflow status | Status-mismatch on JIB post | Old maintenance fix (Sprint 34, v16-era) — Validation Test Passed |

**Triage:** get **PQID + the exact error**. "approach zero" → §7. "Cannot find column IDOPENITEM_APPLY" → look for a **duplicate AR line** (#113083). "@ba_no" on a reversal → confirm 2022.04+. Check-run + multi-BA-contact → confirm 2024.10+.

**Bug IDs:** 1446832, 1445857, 1679169, 113083, 1584004, 1550783, 57354. **SF/legacy case refs:** #1446832 ties to legacy 304011/305857-era maintenance.

---

## 7. Cluster D — $0 netting lines breaking AR076/POSTWKFL (cross-area: QRA → QCFS)

A long-running, **cross-area** defect: **QRA revenue netting (QRANET / QCFSEXPORT)** sends a **$0-amount open item** back to QCFS; the AR076 payment-application validation then throws and POSTWKFL can't post the netting batch (and it blocks other Post-Pending batches behind it).

**Symptom (verbatim, #184253 / #1379243):**
```
The applied amount + current amount must approach zero.
context={table="BatchPaymentApplicationOpenItem", column="APPLIEDAMT", select="ID=..."}
```
(also `BATCHINVOICELINEITEM.TOTALPRICE = 0` against a non-zero `CUSTOMEROPENITEM.CURAMT`.)

- **#184253 — GLE $0 netting lines causing POSTWKFL errors** [Closed/Duplicate]. Spent years in long-term-blocked for lack of an internal repro (needs QRA↔QCFS data interplay). Dev consensus (Jin Kim / Ray Wang / Ross Holden): **filter $0 `TRANS_AMT` AR/GL rows out of `SSTAG_CORE_INTFC`** during the export/PCW path so they never reach QCFS. **Resolved via #1411454** (per Lindsey Farrar) for GLE; recurred at GLE on the 2021.04 upgrade (#1408282/#1411454).
- **#1379243 — MAC: $0 netting line caused POSTWKFL error in AR076** [Closed/Duplicate of #184253]. Root cause confirmed: a `BI...` batch (BI00000409) with a $0 detail applied to a $0.19 open item; `PaymentApplicationWorkflow` detail validation fires. Traced to a $0 record in `JSTG_JE_INPUT` created by `CWPRECW`/`CWPREPOST` from `RSTG_CORE_FNCL_JIB_UPLOAD`.

**Workaround (client-side, NOT a fix):** the client toggles **AR044 "allow non-zero" config** on, posts the netting batch, then toggles it off. Engineering explicitly flagged this as unacceptable long-term (the config affects more than netting) — the real fix is preventing $0 netted lines from being generated/exported by revenue.

**Classification caveat:** this is **owned by QRA / Revenue**, surfacing as a QCFS POSTWKFL/AR076 symptom. If you see "approach zero" on a netting batch, route the root cause to Revenue (QRANET/QCFSEXPORT $0 lines) and offer the AR044 toggle as the stopgap.

**Bug IDs:** 184253, 1379243 (fix #1411454). **SF cases:** field clients GLE (Greylock), MAC.

---

## 8. Cluster E — POSTWKFL/PSTWKSPLT "errors" that are NOT code defects

A large share of "POSTWKFL is erroring" reports are **environment / metadata / by-design**, not product bugs. Recognize these to avoid a needless escalation.

| Bug | Reported as | Reality | Resolution |
|---|---|---|---|
| **#1656826** | myQ web POSTWKFL "invalid objects" errors after client upgrade | Shared validations run via the **ESUITE data helper**; the env was **missing a sysgen** | Upgrade-team metadata fix, not product |
| **#1687638** | 2024.10 myQ web "errors on running POSTWKFL" (but voucher posts) | Could not reproduce; likely bad data | Closed/Rejected, kept under observation |
| **#1692736** | 2024.10 client-upgrade PSTWKSPLT not executing | Code running on a stray QPEC server vs the upgraded box | Env config, not product (Closed/Rejected) |
| **#1675655** | POSTWKFL/PSTWKSPLT fails when ARCCOREINT is running | **By design** — #1667696 added the lock so they can't run together; expected to go to **SXL "could not acquire lock"** (the bug was it failed instead of waiting; tune `DEFAULTMAXLOCKATTEMPTS`/`DEFAULTTIMEBETWEENLOCKATTEMPTS`) | Closed/Rejected — behavior is intended |
| **#1720373** | 2025.04 QP073 POSTWKFL fails with "LOCK batches" errors | Reversal vouchers create a reversal **check run** that locks the open items; errors are valid (open items locked to an unposted/un-reversed check run). Some error wording unhelpful. Note: **only the POSTWKFL run reported failure; batches actually posted.** | Partial fix (PRs 108954/108957) + "valid errors" disposition |
| **#1698180** | APH POSTWKFL **STUCK** / `Execution Timeout Expired` (SF 24-00989239) | Could not reproduce in lower env; CPU/memory fine; service restart didn't help | Closed/Rejected — infra/data-volume, see §10 |
| **#104443** | POSTWKFL **scheduled** process "stops processing on error — unable to establish a connection with any endpoint" | **DEBUG mode** on the scheduled POSTWKFL definition makes the UPS MT unresponsive over time | Turn DEBUG **off** on the scheduled def (use `QOperationContext` fix #106923 in broker service) |
| **#105931** | Impersonation error during POSTWKFL on the scheduler | Scheduler impersonation context | Maintenance-era fix |
| **#74064/#74065** | POSTWKFL using **Fiscal Period 0 instead of 1** | Off-by-one fiscal period | Code fix, v16/v17 maintenance (PR 2697) |
| **#1712859** | BK040 (bank) "Send email" throws error (tagged PII) | Missing process metadata (`EML_REMIT` in `QARCH_CTRL_PROCESS`) / profile-module launch, **not PII** | Resolved by #1710494 (metadata) |

**Tell-tale it's metadata/env:** error mentions "invalid objects", "could not find process/sysgen", appears **only after an upgrade**, or the **batch actually posts** while the run reports an error. Check `QARCH_CTRL_PROCESS`, `QXREF_AFE_VALID_POST_STATUS`, and the security/sysgen layer before assuming code.

**Bug IDs:** 1656826, 1687638, 1692736, 1675655, 1720373, 1698180, 104443, 105931, 74064/74065, 1712859.

---

## 9. Cluster F — GL025 / AR076 attachments & batch-screen UI

Document-handling defects on the financial batch screens (these are real but low-severity).

| Bug | Symptom | Root cause / fix | Build |
|---|---|---|---|
| **#1788555** | **GL025** added attachment won't open (AR076/AP055 fine) | Screen attachment-open defect; fixed | **2026.04** |
| **#1786000** | **AR076** `SAVE_DOCUMENTS … Object reference not set` on **delete attachment** in Draft; screen doesn't refresh the grid until re-query | Delete-handler didn't update screen state to remove the doc from the grid (add path worked) | **2025.04** (PRs 124545/124546/124641/124672-675); multi-invoice case needed a follow-up |
| **#1655846** | AP055 carries attachments on **copy**, GL025/AR076 do **not** | **By design** — voucher copy handles related docs differently | Closed/Rejected (not a bug) |
| **#187265** | JB500 Journal Entry Coding Master "Account Default" History window issue | Classic eSuite window defect | v16-era (2020.03) |

**Bug IDs:** 1788555, 1786000, 1655846, 187265. **SF case:** #1786000 = Seneca (SRC), found-in 2025.04.

---

## 10. Cluster G — Performance (POSTWKFL / JBPREPROOF / 1099 / Close All)

`FinancialsPerformance`-tagged items; fixes are usually **DB indexes / SQL rewrites**, sometimes **infra (memory/tempdb)**.

| Bug | Symptom | Fix |
|---|---|---|
| **#72944** | 304058 — POSTWKFL timeout | Resolved by a **DB index** (v16/v17 maintenance, Sprint 40; core DB #132534) |
| **#1550460** | MEW POSTWKFL runtime jumped to ~20 min post-hotfix | New index `BATCHJOURNALENTRYLINE (IDBATJE, IDACCOUNT)` (SQL from `UpstreamJournalEntryWorkflow.cs`); a similar index added under #1643630 during splitter testing. Closed/Rejected as "review for core inclusion" |
| **#111029** | CNR **JBPREPROOF** slow on v17 | SQL rewrite (`Sel_DoiDecimals`) + new indexes on `QSTAG_CORE_INTFC_IMP` (core DB #181826) |
| **#241162** | MEW **QSTG1099OVR** query went 16 min → 2 hrs (`Override1099QSTG.cs`) | Query/index fix (core DB indexes #241918) |
| **#1582359** | DAY **Close All Companies** fails for FY2021 (16 BUs) | Short-term: **increase server memory / undersized tempdb**, run close per-company; long-term tied to APH perf #1588863. Closed (verified after upgrade) |
| **#1698180** | APH POSTWKFL stuck / timeout | Infra/data-volume, no code fix (see §8) |
| **#107643/#108425/#109427** | QCA/AP processing perf (CNR, Jonah) | LOS/AFE indexing + hotfix — adjacent (QCA), noted for overlap |

**Triage:** POSTWKFL/JBPREPROOF/1099 slowness is almost always an **index or unfiltered SQL** problem on a large client (MEW, CNR, MAC, APH, DAY). Pull the slow SQL from the process, run an execution plan, check for the indexes above. Close-All-Companies failures often resolve with **tempdb/memory**, not code.

**Bug IDs:** 72944, 1550460, 111029, 241162, 1582359, 1698180.

---

## 11. Fix-Version Matrix

> IntegrationBuild is empty on all of these — "Fixed in" is derived from iteration path / "Merged to" dev comments / tags. **Verify in `Quorum.Upstream.QCFS.Web` release notes before quoting to a client.**

| Bug | Symptom (short) | State / Reason | Iteration → Release | SF / field client |
|---|---|---|---|---|
| #1739552 | POSTWKFL/close account-balance **deadlock** | Closed / Acceptance | 25.19 → **2025.04** | CEN, MAC (field) |
| #1741103 | PSTWKSPLT **deadlock** on GENERALLEDGERTRANSACTION | Closed / Acceptance | 25.19 → **2025.04** (QFC 17.25.7/17.28.2); RN 2026.04 | — |
| #1743547 | POST-vs-close deadlock repro | Closed / Rejected (covered by 1739552) | 25.15 | CEN 2023.04, MAC 2024.10 |
| #1745586 | Cancel-prevention for new close/post processes | Closed | 25.16 → **2025.04** | — |
| #1749964 | Security objects + **PSTPRGFIX** cleanup | Closed | 25.17 → **2025.04** | — |
| #1667696 | Shared **lock** ARCCOREINT/POSTWKFL/PSTWKSPLT | Closed | 24.15 → **2024.10** | — |
| #1618436 | Fast-track **double-post** ("Post In Progress") | Closed | 23.21 → **2023.04** | — |
| #1623794 | Same fix for **myQ AP web** | Closed | 23.21 → **2023.04** | — |
| #1669576 | "Post In Progress" **stuck** cleanup | Closed / Duplicate (→ PSTPRGFIX) | 25.17 → **2025.04** | — |
| #1446832 | Voucher-reversal **@ba_no** param error | Closed | 22.06 → **2022.04** | — |
| #1445857 | QP073 **QXREF_AFE_VALID_POST_STATUS** sysgen | Closed | 22.06 → **2022.04** | — |
| #1679169 | Check-run + **>1 BA contact** | Closed | 24.21 → **2024.10** | ARS (field) |
| #113083 | AR batch **Cannot find column IDOPENITEM_APPLY** (dup line) | Closed / Verified | v17 Maint (Sprint 60) | CNR |
| #1379243 | MAC **$0 netting** line POSTWKFL error | Closed / Duplicate → #1411454 | Maintenance | MAC; GLE (#184253) |
| #184253 | GLE **$0 netting** lines | Closed / Duplicate → #1411454 | Engineering | GLE (Greylock) |
| #1720373 | 2025.04 QP073 **LOCK batches** (reversal check-run) | Closed | 25.07 → **2025.04** | — |
| #1786000 | AR076 **delete-attachment** SAVE_DOCUMENTS error | Closed / Acceptance | 26.05 → **2025.04+** | SRC (Seneca) |
| #1788555 | **GL025** attachment won't open | Closed | → **2026.04** | — |
| #74065 | POSTWKFL **Fiscal Period 0 vs 1** | Closed | Sprint 40 (v16/v17) | — |
| #72944 | POSTWKFL **timeout** (DB index) | Closed / Test Passed | Sprint 40 (v16/v17) | — |
| #104443 | POSTWKFL scheduler **endpoint** error (DEBUG mode) | Closed / Verified | Sprint 57 (v16/v17) | — |
| #111029 | CNR **JBPREPROOF** perf | Closed / Verified | Sprint 60 (v16/v17) | CNR |
| #241162 | MEW **QSTG1099OVR** 2-hr query | Closed | 20.23 → **2020.x** | MEW |
| #1582359 | DAY **Close All Companies** perf | Closed / Rejected (infra) | — | DAY |
| #1712859 | BK040 send-email (missing metadata, not PII) | Closed | 25.04 → **2025.04** | — |

---

## 12. Diagnostic Pointers

> QCFS is **SQL Server** (T-SQL), schema `dbo`, per-client environments (`<CLIENT>_HD_DEV17`, `CORE_TST`, `RELQA`, `DOCU_TST`). Table/column names below come from bug repro/comment text — verify against the client DB and always run a SELECT before any DELETE/UPDATE, in a transaction.

```sql
-- A. Batches stuck in Post Pending (status 90) — the POSTWKFL backlog (#1720373)
SELECT * FROM UVW_WORKFLOWINBOX WHERE STATUSWORKFLOW = 90;   -- 90 = POSTPEN

-- B. The $0 netting line that breaks AR076/POSTWKFL (§7, #1379243)
SELECT L.IDOPENITEM_APPLY, CU.USERKEY, L.TOTALPRICE, C.CURAMT, (L.TOTALPRICE+C.CURAMT) AS TOTALAPPLYAMT
FROM   BATCHINVOICEMASTER M
JOIN   BATCHINVOICELINEITEM L ON M.ID = L.IDBATINVMASTER
JOIN   CUSTOMEROPENITEM     C ON L.IDOPENITEM_APPLY = C.ID
JOIN   CUSTOMER            CU ON C.IDCUSTOMER = CU.ID
WHERE  M.STATUSWORKFLOW = '140'           -- use the batch's actual status
  AND  (L.TOTALPRICE + C.CURAMT) <> 0 AND L.TOTALPRICE = 0
ORDER BY (L.TOTALPRICE + C.CURAMT);
-- Stopgap: AR044 "allow non-zero" config ON → post → OFF.  Real fix: filter $0 TRANS_AMT AR/GL rows from SSTAG_CORE_INTFC (QRA side).

-- C. Duplicate AR line causing "Cannot find column [IDOPENITEM_APPLY]" (#113083)
--    Find the dup line where applied > open-item amount, delete it, then re-total master/detail. (verify first!)

-- D. Missing process metadata behind a "POSTWKFL error after upgrade" (§8)
SELECT * FROM QARCH_CTRL_PROCESS WHERE PROCESS_ID IN
  ('POSTWKFL','PSTWKSPLT','BUSSVCRUN','BSVPOST','BSVCLOSE','BSVCRFRSH','PSTWKBAL','BSVBCHRFSH','PSTPRGFIX','ARCCOREINT','EML_REMIT');

-- E. Security objects for the new 2025.04 close/post processes match BUSSVCRUN (#1749964)
SELECT * FROM QARCH_SEC_OBJECT
 WHERE OBJECT_ID IN ('BSVCLOSE','BSVCRFRSH','PSTWKBAL','BSVPOST','BSVBCHRFSH','PSTPRGFIX') AND MODULE_CD='QCFS';
SELECT OBJECT_ID, COUNT(*) GRP_COUNT FROM QARCH_SEC_GRP_PRIVILEGE
 WHERE OBJECT_ID IN ('BUSSVCRUN','BSVCLOSE','BSVCRFRSH','PSTWKBAL','BSVPOST','BSVBCHRFSH','PSTPRGFIX') GROUP BY OBJECT_ID;

-- F. ARCCOREINT vs POSTWKFL/PSTWKSPLT lock + retry tuning (§4/§8, #1667696)
SELECT * FROM QARCH_LOCK_MASTER          WHERE LOCK_TYPE_CD = 'ARCNT_WKFL';
SELECT * FROM QARCH_LOCK_MASTER_PROCESS  WHERE LOCK_TYPE_CD = 'ARCNT_WKFL';
SELECT * FROM QARCH_CNFG_CTRL WHERE KEY_GRP_NM='LOCK'
  AND KEY_NM IN ('DEFAULTMAXLOCKATTEMPTS','DEFAULTTIMEBETWEENLOCKATTEMPTS');

-- G. Voucher-reversal @ba_no error config (#1446832)
SELECT * FROM QARCH_CNFG_CTRL WHERE KEY_NM = 'SHOW_APPROVAL_FIELDS';

-- H. Read a failed run's log by Process Queue ID
SELECT * FROM QARCH_PROCESS_MSG_LOG WHERE PROCESS_QUEUE_ID = <PQID>;

-- I. Deadlock graph (the exact query devs used, #1739552/#1741103/#1743547)
SELECT XEvent.query('(event/data/value/deadlock)[1]') AS DeadlockGraph
FROM ( SELECT XEvent.query('.') AS XEvent FROM (
  SELECT CAST(target_data AS XML) AS TargetData
  FROM sys.dm_xe_session_targets st
  JOIN sys.dm_xe_sessions s ON s.address = st.event_session_address
  WHERE s.NAME='system_health' AND st.target_name='ring_buffer') AS Data
  CROSS APPLY TargetData.nodes('RingBufferTarget/event[@name="xml_deadlock_report"]') AS X(XEvent)) AS source;

-- J. Reversal-voucher / check-run lock diagnosis (#1720373)
SELECT A.USERKEY, B.VOUNUM, A.IDBATCHMASTER, A.STATUSWORKFLOW, A.NAME, B.POSTED, C.POSTED,
       B.REVERSALVOUNUM, A.LOCKEDUSERNAME, B.LOCKEDUSERNAME
FROM BATCHVOUCHERMASTER A
JOIN BATCHVOUCHERDETAIL B ON A.ID = B.IDBATVOUMASTER
JOIN BATCHVOUCHERGLDISTRIBUTION C ON B.ID = C.IDBATVOUDETAIL
WHERE A.IDBATCHMASTER = <id>;
```

---

## 13. Key Code, Processes & Repos

### Processes (Process IDs)
| Process | Purpose | Notes |
|---|---|---|
| `POSTWKFL` | Schedule Post Workflow — posts all Post-Pending batches to GL + balance refresh | QP073 (classic) / eSuite Batch (web). Most defects here. |
| `PSTWKSPLT` | Post Workflow **Splitter** — parallel child jobs | Bulk-insert lock-hint deadlock on insert-only `GENERALLEDGERTRANSACTION` (#1741103) |
| `BUSSVCRUN` | Business Service Run — single post/close/refresh action | Fast-track post launches this directly |
| `BSVPOST / BSVCLOSE / BSVCRFRSH / PSTWKBAL / BSVBCHRFSH / PSTPRGFIX` | 2025.04 split-out processes for post / close / balance refresh / cleanup | New PROCESS_IDs + locks added by #1739552/#1745586/#1749964 |
| `ARCCOREINT` | AR/Core-interface archive/purge | Shares lock `ARCNT_WKFL` with POSTWKFL/PSTWKSPLT (#1667696) |
| `JBPREPROOF` | JIB pre-proof | Perf (#111029) |
| `QSTG1099OVR` / `Override1099QSTG.cs` | 1099 override staging | Perf (#241162) |
| `QCFSEXPORT` / `CWPRECW`/`CWPREPOST` / PCW | Revenue→QCFS export & pre-check-write | $0 netting source (§7) |

### Code locations (from bug links/comments)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `UpstreamJournalEntryWorkflow.cs` (post-workflow SQL) | `Quorum.Upstream.QCFS.Web` → `Quorum.QCFS.Upstream/BS/` | §4/§10 (BATCHJOURNALENTRYLINE index #1550460) |
| `CustomCodeBlockData.cs` → `CopyValuesTo` (note: in matched-set #1708039, AP-area) | `Quorum.QCFS.BL` | check-run ID/identity handling |
| `PaymentApplicationWorkflow` (AR detail validation) | `Quorum.QCFS.*` | §7 "approach zero" |
| `ClientBusinessServiceRun` / `ClientBusinessServiceRunBase` | `Quorum.QCFS.BS` / `Quorum.QCFS.BSGUI` | §4 BUSSVCRUN post/balance |
| `Override1099QSTG.cs` | `Quorum.QCFS.*` | §10 1099 perf |
| `QInterProcessMessaging` / broker `QOperationContext` | platform (`Quorum.QFC.Core`) | §8 scheduler/DEBUG; §4 QFC 17.25.7/17.28.2 |

### Repos
- **`Quorum.Upstream.QCFS.Web`** — the primary QCFS repo (post-workflow BS, journal/AR/GL screens, web). Branches `develop` / `release`; releases tagged 2022.04 … 2026.04.
- **`Quorum.QFC.Core`** (platform/QFC) — the splitter bulk-insert/lock-hint piece lives here (hotfix 17.25.7 → 17.28.2 consumed by QCFS for #1741103).
- Client environments are **DB-level** (no per-client code repo like TIPS) — most "missing sysgen/metadata" issues (§8) are fixed by the **upgrade team** in the client DB / metadata layer, not in product code.

---

## 14. Escalation Guidance

**Route to QCFS Engineering (true code defect) when:**
- A **deadlock** occurs during POSTWKFL/close and the client is **pre-2025.04** → the fix is the 2025.04 split (#1739552 + #1741103, + QFC 17.25.7/17.28.2 for the splitter). Provide the **deadlock graph** (query I in §12) + PQID. Field clients already hit: **CEN (2023.04), MAC (2024.10)**.
- A batch **double-posts** or sticks in **Post In Progress** and the client is pre-2023.04 / pre-2025.04 (PSTPRGFIX) → §5.
- A real **"Could Not Post"** code/data defect: voucher-reversal `@ba_no` (pre-2022.04, #1446832), check-run + >1 BA contact (pre-2024.10, #1679169), `IDOPENITEM_APPLY` dup line (#113083). Provide PQID + exact error + the batch.

**Route to Revenue / QRA when:**
- **$0 netting "approach zero"** on an AR076/QRANET batch — the root cause is QRA exporting $0 open items (§7, #184253/#1379243/#1411454). Give the client the **AR044 toggle** stopgap.

**Handle as configuration / upgrade-team / infra (NOT product code) when:**
- POSTWKFL "invalid objects / could not find process / missing sysgen" **after an upgrade**, or the **batch posts but the run reports an error** → missing rows in `QARCH_CTRL_PROCESS` / `QXREF_AFE_VALID_POST_STATUS` / security layer (§8, #1656826/#1687638/#1692736/#1712859).
- POSTWKFL/PSTWKSPLT "could not acquire lock" while **ARCCOREINT** runs → **by design** (#1675655); tune `DEFAULTMAXLOCKATTEMPTS`/`DEFAULTTIMEBETWEENLOCKATTEMPTS`.
- POSTWKFL scheduler "stops on error / endpoint" → turn **DEBUG mode off** on the scheduled definition (#104443).
- POSTWKFL/JBPREPROOF/1099/Close-All **slow** → DB index / SQL / **tempdb-memory** (§10); often resolved by infra, not a code change.

**Dead ends / caveats:**
- IntegrationBuild is empty on every bug — never quote it; use iteration→release + release notes.
- Several "bugs" are **By Design / Rejected** (copy-doc difference #1655846, ARCCOREINT lock #1675655, dup-button minor #1584004) — don't escalate as defects.
- The $0-netting family was **long-term-blocked for years** for lack of an internal repro; if a client hits it, the reproducible data path is **QCFSEXPORT/OI export → PCW** with a $0 net against a non-zero open item.

---

*Skill created 2026-06-14. Source: 184 Closed/Resolved ADO Financials bugs (WIQL title filter on receivable/AR/GL/journal/bank-recon/period-close); ~45 deep-read for root cause + PR/commit. Marquee items: #1739552 / #1741103 (POSTWKFL/PSTWKSPLT deadlock, 2025.04), #1618436 / #1623794 (fast-track double-post, 2023.04), #1667696 (ARCCOREINT lock, 2024.10), #184253 / #1379243 ($0 netting, QRA-side), #1446832 / #1679169 / #113083 (Could-Not-Post defects). Companion: REPO_INVENTORY / CONFIG_REFERENCE in the Upstream ADO Assistant dir; QCA/QRA/QDO sibling skills.*
