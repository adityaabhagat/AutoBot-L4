# SKILL: QCFS Accounts Receivable & Bank Reconciliation Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Financial Accounting (QCFS — upstream oil & gas accounting; the GL/AP/AR/Bank-Recon module of the myQuorum / On Demand Upstream suite)
**Scope:** The **Accounts Receivable** pipeline (AR076 Batch Invoice Creation, AR086/AR090 invoice adjustment, AR173 Customer Item Inquiry, AR308 Deposit Creation/Deposit-with-Match, cash application, prepayments/cash calls, the QRA→QCFS netting interface, POSTWKFL batch posting) and **Bank Reconciliation** (BR005 reconciliation screen, BR036 bank-account/deposit-journal setup, CW005 check register, voids/reversals, period close).
**Companion skills:** Severance-tax / 1099 / ONRR (TS010, TR010, TRSEVTX*, QRA 1099, NAUPA/escheat) are a *separate* category group — not covered here even though several share the AR/BR queue. JIB cost generation (JB010/JB310/JB340 mechanics, overhead rates) and the GL posting engine itself live in their own modules; this skill consumes JIB output and produces AR/bank-recon results — **fix the upstream JIB/GL or the QRA export first when the AR number itself is wrong** (AR is usually the messenger).

> **Evidence base:** 446 closed QCFS AR/Bank-Recon cases (AR 333, BR 113). Root-cause split — AR: Training 52, (blank) 60, **Application Configuration 28**, Customer Error 26, **Software Defect 22**, Customer Cancelled 18, Other 18, Business Change 16, No-Action 16, … **ChangeConfig 1**; BR: Training 20, (blank) 20, **Software Defect 14**, Customer Error 13, **Application Configuration 7**, Customer Cancelled 7, … This skill mines the **72 actionable** cases (Software Defect 36 + Application Configuration 35 + ChangeConfig 1) for fix recipes, plus ~35 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — POSTWKFL "Could Not Post" / "approach zero" / $0 QRA netting (HIGH FREQUENCY)](#4-cluster-a--postwkfl-could-not-post--approach-zero--0-qra-netting)
5. [Cluster B — POSTWKFL / QCFSIMPCYC stuck "Post Pending", locks, timeouts](#5-cluster-b--postwkfl--qcfsimpcyc-stuck-post-pending-locks-timeouts)
6. [Cluster C — AR308 deposit setup: "Deposit Journal Definition not set" (BR036)](#6-cluster-c--ar308-deposit-setup-deposit-journal-definition-not-set-br036)
7. [Cluster D — AR308 attachments / Document Management errors](#7-cluster-d--ar308-attachments--document-management-errors)
8. [Cluster E — AR308 deposit delete / business-rule exceptions](#8-cluster-e--ar308-deposit-delete--business-rule-exceptions)
9. [Cluster F — BR005 reconciliation defects (balance, dates, reversals, picklist)](#9-cluster-f--br005-reconciliation-defects-balance-dates-reversals-picklist)
10. [Cluster G — BR005 batch-creation timeout / constraint exception](#10-cluster-g--br005-batch-creation-timeout--constraint-exception)
11. [Cluster H — Voiding "reconciled" ACH / bank-account number sync (CW005)](#11-cluster-h--voiding-reconciled-ach--bank-account-number-sync-cw005)
12. [Cluster I — Import-driven bad data (BOABANKSTMT dates, QGM/QRA interface, eONE)](#12-cluster-i--import-driven-bad-data-boabankstmt-dates-qgmqra-interface-eone)
13. [Cluster J — AR076 prepayment GL distribution & grid/picklist defects](#13-cluster-j--ar076-prepayment-gl-distribution--gridpicklist-defects)
14. [Cluster K — AR173 / metadata-grid customization fragility (grid 36062)](#14-cluster-k--ar173--metadata-grid-customization-fragility-grid-36062)
15. [Cluster L — AR/BR reports (Deposit Batch Review, ARR003, ARR014, cash-call print)](#15-cluster-l--arbr-reports-deposit-batch-review-arr003-arr014-cash-call-print)
16. [Known ADO Items](#16-known-ado-items)
17. [Diagnostic SQL](#17-diagnostic-sql)
18. [Expected-Behavior / User-Education FAQ](#18-expected-behavior--user-education-faq)
19. [Key Code, Screens & Repos](#19-key-code-screens--repos)
20. [Escalation Guidance](#20-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| AR076/QRANET batch **"Could Not Post"**; error **"The applied amount + current amount must approach zero"** on `BatchPaymentApplicationOpenItem.APPLIEDAMT` | A **$0 netting line** from QRA hitting the non-zero payment-application validation; or an over-applied open item | §4 — workaround: AR044 **Allow Non-Zero Payment Application**; defect fix blocks $0 AR trans-type export (#66157 family) |
| Batch (BI…/BD…) **stuck "Post Pending"** for hours/days; PQID shows running but no movement; locks not released | POSTWKFL/QCFSIMPCYC died, **stale lock**; or `DATETOPOST` is a future date; or closed period | §5 — release lock in **QP110**; check `DATETOPOST`; check SM006 |
| AR308 **"Could not create autoNumber for Deposit b/c BankAccount … does not have a Deposit Journal Definition set"** | New bank account missing `IDJOURNALDEFDEPOSIT` | §6 — set **Deposit Journal Def = DEP** in **BR036** |
| AR308 / AR076 **attach or post fails with DocumentManagement error**; attachments won't open in Draft | Document-management + ClassicGUI pipeline needs redeploy (or Patch 4) | §7 |
| AR308 **"Unable to delete" deposit/receipt**; `FIRE_ENTITY_EVENTS` / `GET_ENTITY_ACTION_TYPE` business-rule error | Delete-on-receipts defect (deleted-row-state handling) | §8 (#1566024) |
| BR005 **GL balance wrong / spans two months / reversal shows nothing / void date blank / forced GL-account picklist** | BR005 reconciliation defects (Defect 301 family) | §9 |
| BR005 **batch creation times out** ("Not responding") or **"failed to enable constraints … non-null/unique/FK"** | Timeout (config `BANK_RECON_SCREEN_TIMEOUT`) / batch-then-check sequence | §10 |
| **Can't void a "reconciled" ACH** ("already reconciled with the bank") | Client-specific validation auto-marks `BANKRECONCILED` | §11 (#1524343) — NULL the flag short-term |
| Cleared dates show **1926 instead of 2026** in BR005/AP157/CW005; QGM→AR interface failed | **Import** definition (YY vs YYYY date; wrong env path) | §12 |
| AR076 **prepayment line requires owner** / prepayment not in JB340 | GL105 JE-code-type `OWNER` required; or **JBPREPAY** not run | §13 |
| AR076 **Open Apply ID picklist pulls wrong customer's records**; Customer BA missing on GL095/096 | Picklist/grid-definition defect (grid 36064) | §13 |
| AR173 **accounting-date filter stops working** every few months | Grid 36062 **Filter Expression Col** cleared; metadata layer not checked in | §14 |
| Report (Deposit Batch Review, ARR003, cash-call print) wrong/blank/error | Report SQL/SSRS-path/release fix | §15 |
| "How do I…", "why is AR173 vs JB340…", post-pending-just-wait, period-close questions | Training / expected behavior | §18 |

---

## 2. Pipeline & Concepts

```
[JIB close / QRA revenue netting] ──► QRA EXPORT (EXPOI Export Open Items) ──► QCFSIMPCYC (import cycle, stages AR batches)
      │                                                                              │
      ▼                                                                              ▼
[AR076 Batch Invoice Creation]  [AR308 Deposit Creation / Deposit-with-Match]  [cash application]
      │  (draft → validate → approve → POSTWKFL post)                                │
      ▼                                                                              ▼
[GL: GL095/GL096 detail, ACCOUNTBALANCE]  ◄──► [AR173 Customer Item Inquiry / open items]
      │
      ▼  CHECK WRITE (QRA) → CW005 register
[BR005 Bank Reconciliation]  (uses BR036 bank-account setup; BANKRECONCILED flag; period close SM006)
```

### Key terms / screens (QCFS vocabulary)
- **AR076** = Batch Invoice Creation (creates BI…batches: JIB invoices, prepayments, cash-call invoices; draft→validate→approve→post).
- **AR086 / AR090** = AR invoice acceptance / **invoice adjustment** (needs an Invoice Adjustment amount in **SM003** per user, else error).
- **AR173** = Customer Item Inquiry (the AR sub-ledger of open items; double-click a line drills to **GL095**).
- **AR308** = Deposit Creation / **Deposit Creation with Match** (records cash receipts; produces BD…/DEP… deposits, applies them to open items).
- **AR044** = Accounts Receivable Configuration (per-BU; holds the **Allow Non-Zero Payment Application** flag and the Global IND).
- **BR005** = Bank Reconciliation screen (drafts a reconciliation batch; tabs: items to clear, **Bank Adjustments & Missing Deposits**, **Add Bank Charges/Interest**).
- **BR036** = Bank Account setup — the **Deposit Journal Def** field here writes `BANKACCOUNT.IDJOURNALDEFDEPOSIT`; also controls which bank accounts appear in AR308.
- **CW005** = Check Register / check status (Processed vs not) — depends on bank-account-number formats matching across tables.
- **POSTWKFL** = the Post Workflow batch process that posts approved AR/deposit/JE batches; **QP110** is where you release a stale POSTWKFL lock.
- **QCFSIMPCYC** = QCFS Import Cycle — imports/stages the QRA-netted AR batches into AR076; timeouts here leave batches un-created or post-pending.
- **EXPOI** = QRA "Export Open Items"; **QRANET / QRAREV** = the netting / revenue batches QRA sends into QCFS; tracked in `SEXTN_CORE_INTFC_QRA`.
- **JBPREPAY / PREPAY** = the QCA process that moves a posted AR076 prepayment into the owner's prepayment balance, visible in **JB340** (Cash Call verification screen).
- **BANKRECONCILED** = column on the payment/check record; once set, the void is blocked ("already reconciled with the bank").
- **SM006** = period / accounting-month open-close (per BU, per module); **hard close** is re-runnable. **SM002/SM021** = BU + bank/journal config. **SM003** = per-user invoice-adjustment limit.
- **Grid Definition / Metadata Layer (Environment Specific, QSGY)** = how QCFS screens (AR173 grid 36062, GL095 grid 36064, AR076) are customized; custom changes must be **checked into the metadata catalog** or a release overwrites them.
- **"approach zero"** = the payment-application invariant `applied + current ≈ 0`; a $0 line or an over-application breaks it.

---

## 3. Decision Tree

```
QCFS AR / Bank-Recon case
│
├─ A batch won't POST / POSTWKFL errored?  → GET batch ID (BI…/BD…) + PQID + exact error
│   ├─ "must approach zero" / $0 QRA netting line                       → §4  (AR044 Allow Non-Zero; defect #66157 family)
│   ├─ over-applied open item (double EXPOI / re-export)                → §4  (MJE correction; long-term release fix)
│   ├─ stuck "Post Pending", lock held, no movement                     → §5  (release lock in QP110; check DATETOPOST; SM006)
│   ├─ "Could not post" but no detail → period closed                   → §5/§18 (reopen SM006, reject→approve→post)
│   └─ "Could not post" → a BA on the batch not approved                → §18 (approve the BA, then reject→approve→post)
│
├─ AR308 deposit problem?
│   ├─ "does not have a Deposit Journal Definition set"                 → §6  (BR036 Deposit Journal Def = DEP)
│   ├─ attach / open attachment / post → DocumentManagement error       → §7  (redeploy doc-mgmt + ClassicGUI pipeline / Patch 4)
│   ├─ "Unable to delete" / FIRE_ENTITY_EVENTS / GET_ENTITY_ACTION_TYPE → §8  (delete-on-receipts defect #1566024)
│   └─ which bank accounts show / Customer BA not on GL                 → §6/§13 (BR036 / grid 36064 CUST_NO)
│
├─ BR005 reconciliation output wrong (not crashing)?
│   ├─ GL balance wrong / spans 2 months / mid-month cutoff             → §9  (Defect 301, 24-00977408; period close §18)
│   ├─ reversal shows no record / totals wrong on reversal              → §9  (#1722419)
│   ├─ void date blank / item missing because of ACH date              → §9  (22-00825516, 23-00931115)
│   └─ forced GL-account picklist on bank charges                       → §9  (23-00906555, HF11)
│
├─ BR005 won't open/create a batch?
│   ├─ timeout / "Not responding"                                       → §10 (config BANK_RECON_SCREEN_TIMEOUT; HF #1435865)
│   └─ "failed to enable constraints" / Out-of-Range exception          → §10 (Add batch first, THEN check items)
│
├─ Can't void a "reconciled" ACH / CW005 won't mark Processed?         → §11 (NULL BANKRECONCILED / sync bank-acct number format)
│
├─ Bad data after an import (dates, failed interface, cost centers)?   → §12 (BOABANKSTMT YY/YYYY; QGM/QRA path; eONE)
│
├─ AR076 detail won't save / picklist wrong / prepayment missing?      → §13 (GL105 OWNER optional; grid 36064; run JBPREPAY)
│
├─ AR173 accounting-date filter stopped working?                       → §14 (grid 36062 Filter Expression Col; QSGY check-in)
│
├─ A report is wrong/blank/errors?                                     → §15
│
└─ "How do I…", AR173-vs-JB340, just-wait post-pending, audit Q       → §18 Expected-Behavior FAQ
```

---

## 4. Cluster A — POSTWKFL "Could Not Post" / "approach zero" / $0 QRA netting

**The single largest actionable AR-posting signature.** A QRA netting/revenue batch (QRANET / QRAREV) comes into QCFS, POSTWKFL tries to post it, and it fails "Could Not Post" with:

```
The applied amount + current amount must approach zero.
context={table="BatchPaymentApplicationOpenItem", column="APPLIEDAMT", select="ID=…"}
```

**Root causes & fixes seen:**
- **$0 netting line from QRA (25-01006202, 25-01006390, 25-01012055).** QRA issues $0 invoices to be netted; they flow into QCFS and hit the validation that blocks applying $0 to an AR open item.
  - **Immediate workaround:** in **AR044** for the BU, uncheck **Global IND**, check **Allow Non-Zero Payment Application**, Update; reject the AR076 batch, approve, **manually run POSTWKFL**; then **reverse the AR044 change**. (Disable the scheduled POSTWKFL first so nothing else picks up the relaxed config — 25-01012055.)
  - **Long-term fix (Software Defect, 25-01006390):** code change prevents **AR Trans Type records from exporting to QCFS when both `TRANS_AMT` and `TRANS_QTY` are 0** while the respective `DOWNLOAD_VOL_FL`/`DOWNLOAD_VAL_FL` are enabled. Delivered in a hotfix — confirm the client's build before promising it.
- **Over-applied open item from a double EXPOI / re-export (23-00932894, Pre-Check Write Netting Doubled).** Open items re-exported by a second EXPOI run got processed twice, netting twice the AR. Records weren't flagged in `SEXTN_CORE_INTFC_QRA`. Correction required an **MJE** (credit owner payable, debit AR, book netting-clearing accounts) and manual `SYS_SRC_CD` reclass (PAR/PCW) in `JTRN_JE_INPUT_ACCT` / `JSTG_JE_INPUT` before posting. The requested guard (don't release locks on an OI batch until processed) is a **future-release** change.
- **A single line applying no amount ("does not approach zero", 22-00518323).** Found the offending line, turned off a configuration on it, batch posted.
- **Missing JIB netting configuration (22-00560577).** QRANET batch had invoice detail/lines but **no payment-application data** → "must approach zero". Workaround to post; long-term tracked as a QRA ticket.

**Fix recipe:**
1. Get the **batch ID (BI…/BD…) + PQID + exact error** from the POSTWKFL message log (AR076 → batch → message log).
2. "approach zero" + a $0 line → AR044 **Allow Non-Zero Payment Application** workaround (disable scheduled POSTWKFL first, revert after). Confirm/await the $0-export defect fix for the client's build.
3. "over applied" → look for a **re-exported open item** (double EXPOI) in `SEXTN_CORE_INTFC_QRA`; correction is an MJE + `SYS_SRC_CD` reclass (escalate; this is delicate).
4. Always scope to the specific **BU + batch ID**; verify-SELECT before any data change.

---

## 5. Cluster B — POSTWKFL / QCFSIMPCYC stuck "Post Pending", locks, timeouts

Distinct from §4 (validation failure): here the process **dies or hangs** and leaves batches in Post Pending with locks held. This is the most common *Training/operational* AR signature and also the QCFSIMPCYC performance area.

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Batch stuck "Post Pending"; PQID shows running, no movement, **locks released but no progress**; only some of N batches created | **QCFSIMPCYC timed out** → AR batches from JIB never staged/created | **Re-stage script** to recreate the missing records; they then appear in AR076 | 25-01058210 (POSTWKFL "released locks", 10/30 batches) ; 26-01070724 (QCFSIMPCYC interrupted during JIB) |
| JE / Payment Application "Post Pending" > 1 hr; can't print checks | **POSTWKFL failed, lock not released** | **Release the lock manually in QP110**, POSTWKFL resumes | 22-00713776 ; 25-01051167 (stale lock on PQID 4465946) |
| AR batch in Post Pending, won't move | `DATETOPOST` set to a **future date** → POSTWKFL will pick it up that day | No fix needed — it posts on the scheduled date | 25-01022292 |
| BR005 batch creation **timeout / "Not responding"** | Screen timeout on large bank-recon set | Hotfix; raise global config `BANK_RECON_SCREEN_TIMEOUT` (see §10) | 22-00651669 (HF #1435865) ; 22-00821009 |
| QCFSIMPCYC very long runtime when an open item is applied to an AR batch / BU inactive | Import-cycle performance / inactive-BU handling | Perf improvements & bug fixes | #1724602, #1752121, #1565787, #1683641, #1689851 |

**Fix recipe:** for any "Post Pending" complaint, first determine whether POSTWKFL/QCFSIMPCYC actually **completed**. If a lock is stale → **QP110 release**. If QCFSIMPCYC **timed out and never created the batches** → re-stage script (engineering). If `DATETOPOST` is future → it's expected. Always grab the **PQID** and the process-run history.

---

## 6. Cluster C — AR308 deposit setup: "Deposit Journal Definition not set" (BR036)

A frequent, fully-deterministic **Application Configuration** case when a new bank account is added.

**Symptom (verbatim, 23-00935999 / 24-00963987):**
```
Could not create autoNumber for Deposit b/c BankAccount '<name>' does not have a Deposit Journal Definition set
```
…so AR308 can't assign a deposit number and won't save.

**Root cause:** the new bank account has no `IDJOURNALDEFDEPOSIT` (the `BANKACCOUNT.IDJOURNALDEFDEPOSIT_USERKEY` / `_NAME` columns are null). SM002/SM021 looking "set up the same" is a red herring — the Deposit Journal Def is a separate field.

**Fix:** open **BR036**, type **`DEP`** into the **Deposit Journal Def** field for that bank account, hit **Update**. (This writes `IDJOURNALDEFDEPOSIT`.) The same BR036 field controls **which bank accounts appear in AR308** — remove an account from AR308 by clearing it there (25-01041812 "Bank Account Clean Up"). Default QCFS Import config (ARD/DEP) for AR308 import is set on **MT100** (#1799888).

---

## 7. Cluster D — AR308 attachments / Document Management errors

A recurring **Document Management** signature on AR308 (and AR076 posting).

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Attach in AR308 throws **Quit/Continue** error; can't attach backup support | Document-management + ClassicGUI pipelines out of sync | **Redeploy document-management pipeline then ClassicGUI pipeline** | 23-00924029, 25-01012104 |
| Documents attached to a **Draft** AR308 batch won't open | Cluster-wide document defect | **Patch 4** (high-engagement doc fix across Upstream & QLS) | 25-01060641 |
| **DocumentManagement.Services error when posting in AR076** | DD relationship for QP045 / AP055 / GL025 document attachments | Service/config fix on the document relationship | 25-01007748 |
| Classic AR308 doc-management exception via WF005 double-click | Classic doc-management exception | Bug | #226951 |

**Fix recipe:** AR308 attach/open failures are almost always **pipeline / document-service** issues, not data. First action is **redeploy the document-management pipeline and then the ClassicGUI pipeline**; if the whole environment's attachments are broken, it's the Patch-4 family. Capture the exact exception + whether the batch is Draft.

---

## 8. Cluster E — AR308 deposit delete / business-rule exceptions

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Delete on a deposit that has receipts doesn't work**; `FIRE_ENTITY_EVENTS` / `GET_ENTITY_ACTION_TYPE` business-rule errors | Delete used the wrong row state for deleted records → "deleted row information" exception | **`GET_ENTITY_ACTION_TYPE` updated to use the original state** for deleted records | 22-00827489, 22-00868012 / **#1566024** (SRC, Bug, Closed) |
| Deposit batch deleted while a **check # was left blank** → line items remain **locked** in AR173 | Orphaned lock from a half-deleted deposit | **Script to unlock** the AR173 items | 22-00654673 |
| Activity-date on deposits | ChangeConfig | Config | 22-00827490 |

**Fix recipe:** AR308 delete exceptions (`FIRE_ENTITY_EVENTS`/`GET_ENTITY_ACTION_TYPE`) are the confirmed delete-on-receipts defect (#1566024) — confirm the client's build. If a deposit was force-deleted and **left items locked in AR173**, the unblock is a scoped **unlock script** (22-00654673).

---

## 9. Cluster F — BR005 reconciliation defects (balance, dates, reversals, picklist)

A distinct **Software Defect** cluster where the reconciliation *output* is wrong (the screen runs fine).

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Calculated Total GL account balance wrong** on a mid-month batch — uses end-of-month balance while the accounting date is the daily cutoff | Inconsistency between account balance and GLT data | **"Defect 301": BR005 now derives Calculated Total GL balance from the input accounting date** | 24-00977408 |
| GL balance on recon **spans two months** (Dec + Jan combined) | Period boundary / open-period handling | Limit to the bank balance for that BU batch; **hard-close the prior year in SM006** | 26-01070043 |
| **Reversal of a posted bank rec shows no record**; can't edit adjustment / can't zero the variance | Reversal display defect | **Software update so adjustment & other totals display correctly on BR005** | 23-00935181 / **#1722419** (2025.04, Bug, Closed) |
| **Void date blank** — voids coming into BR005 no longer pull the check void date | Logic not carried from old build to new (workaround: GL096 shows the txn date) | **Code fix** (packaged in a later hotfix) | 22-00825516 |
| **Items in GL not showing on the recon** — an ACH's email was changed and the ACH date excluded it | Items excluded based on ACH date | **Code changed to prevent ACH being excluded based on ACH date** | 23-00931115 |
| **Forced GL-Account picklist** on the "Add Bank Charges/Interest" grid (auto-opens, duplicates the account 50–100×, blocks typing) | UX defect on the picklist trigger | **Resolved in Upstream Hotfix 11** | 23-00906555 |
| BR005 unhandled "Object reference not set…" / exception opening links (customer/vendor item inquiry) | Screen exception defects | Bugs | #1443233, #1651187 |
| Earlier **BR005 reversals / "Check Out of Balance"** | Reversal defect | **GLE Patch 5 on 2021.04** | 22-00547077 / **#1413340** (GLE, Bug, Closed) |

**Fix recipe:** for a "BR005 number is wrong" case, identify which sub-symptom — **balance vs accounting-date** (Defect 301, 24-00977408), **reversal totals** (#1722419), **void/ACH date exclusion** (22-00825516 / 23-00931115). These are confirmed defects with known fixes; confirm the client's build. If the GL balance spans months, it's a **period-close** matter (SM006 hard close, §18) not a code bug.

---

## 10. Cluster G — BR005 batch-creation timeout / constraint exception

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| BR005 **"Not responding" → timeout** creating a batch | Screen timeout on a large recon set | **Hotfix**; the global config **`BANK_RECON_SCREEN_TIMEOUT`** (seconds) raises the limit — but note the screen may time out earlier (~1.5 min) than the configured value on a fresh upgrade | 22-00651669 (**HF #1435865**, EQC) ; 22-00821009 (MEW upgrade) |
| **"Failed to enable constraints. One or more rows contain values violating non-null, unique, or foreign-key constraints"** then `ArgumentOutOfRangeException` + red X | Checking items before the batch row exists creates a statement conflict | **Workaround:** **create the batch first (Add), then start checking the boxes** | 26-01106297 |

**Fix recipe:** timeout on BR005 batch creation → confirm `BANK_RECON_SCREEN_TIMEOUT`, but be aware it didn't fully take on an upgrade (22-00821009) — the durable fix is the hotfix (#1435865). The constraint/red-X exception (26-01106297) is an **order-of-operations** workaround: **Add the batch first**, then tick the items.

---

## 11. Cluster H — Voiding "reconciled" ACH / bank-account number sync (CW005)

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **"Payment ACHxxx cannot be voided because it has already been reconciled with the bank on x/x"** even though it isn't truly reconciled | A **client-specific validation auto-marks `BANKRECONCILED`** on ACH payments coming in; with no BR reference, the void is blocked | Short-term: **set `BANKRECONCILED` to NULL** for those items to clear the validation; long-term **code fix** logged | 24-00964709 / **#1524343** (MEW, Bug, Closed) |
| QRA check-write checks **won't mark "Processed" in CW005** | **Bank-account number formats not synced** across the tables CW005/check-write read | **Config updates + data-cleanup scripts to sync bank-account number formatting** so Check Register Update accounts for QRA bank-recon status | 22-00875748 |
| Range — Unreconciled ACH Payment QP063 & BR005 | ACH reconciled-state handling | Bug / task | #1781008, #1790246 |

**Fix recipe:** "can't void a reconciled ACH" is the `BANKRECONCILED` auto-flag (#1524343) — short-term **NULL the flag** for the specific items, then void. For CW005 "not Processed," the cause is **bank-account-number format mismatch** across tables — sync the formats (config + cleanup script), focusing only on the QRA check-write accounts.

---

## 12. Cluster I — Import-driven bad data (BOABANKSTMT dates, QGM/QRA interface, eONE)

A steady stream where the AR/BR symptom is really a **bad import definition or path**, not an app bug.

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Payment **cleared dates show 1926 instead of 2026** in BR005, AP157, CW005 | Client's customized **BOABANKSTMT** import interprets the date as **YY/MM/DD**; CORE expects **YYYY/MM/DD** | **Script to correct the dates** (1926→2026); long-term, have the bank issue **4-digit-year** statements so the env-specific metadata import can be used | 26-01102535 / **#1813192, #1821482** (EQC, Cloud Ops, Closed) |
| **QGM → AR interface FAILED** | **Wrong path** in the environment-specific import path in the imp/exp definition | **Correct the path** | 25-01045557 |
| **Cost centers not pulling from eONE into Upstream** | eONE invoice-module entries vs import template | Use the **invoice import template** (not the eONE 'Invoice' module) | 24-00979253 |
| AR308 **"Index was outside the bounds of the array"** on lockbox import | **Invalid data in the bank's Lockbox Import (CSV) file**; QARCH queue message was generic | Engineering debugged the PQID to find the offending CSV line; client fixed the line and re-imported | 24-00972630 |

**Fix recipe:** when dates/values look wrong **only after an import**, inspect the **client's customized import definition** (date mask, env-specific path) before suspecting the app. The BOABANKSTMT YY/YYYY mismatch is the textbook case (26-01102535): fix forward with a date-correction script and push the bank to 4-digit years. For lockbox "index out of bounds," the bad row is in the **bank's CSV** — debug the PQID to find it.

---

## 13. Cluster J — AR076 prepayment GL distribution & grid/picklist defects

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| AR076 prepayment **detail line requires owner #/suffix** even though the client doesn't use suffixes | The prepayment account's **JE Code Type** (e.g. `PREBILLJIB` on acct 3400.1000) has **`OWNER` required** in **GL105** | In **GL105**, set the **Owner** column to **OPTIONAL** for that code type, save → AR076 saves the line with no owner/suffix | 25-01031193 |
| Posted AR076 **prepayment doesn't reach JB340** | **JBPREPAY** process not running | **Manually kick off JBPREPAY** (or schedule it) | 25-01028952, 25-01036401 |
| AR076 **Open Apply ID picklist pulls only the first customer's open items** for every row | WinForms "Input Value is Outside Grid" on the picklist returns **row 0** regardless of selected row | Screen sets the selected customer in **context data** and maps the picklist to context data | 25-01040984 |
| **Customer ID (BA) not flowing to GL095/GL096** for AR308 batch deposits | **Grid 36064** (Journal Entry Inquiry) has `CUST_NO` **Hidden** in the core definition; GL096 has no Customer-No column at all | Add an **Environment Specific** metadata layer on grid 36064, **uncheck Hidden on `CUST_NO` (row 67)**, Update; in GL095 → Advanced → Show all columns (involve Services to make it permanent) | 25-01040928 |
| AR076 **error posting** / DocumentManagement | See §7 (QP045/AP055/GL025 doc relationship) | — | 25-01007748 |
| Adding two overhead rates in **JB010** per JOA | Config | App config | 26-01096308 |

**Fix recipe:** AR076 "requires owner on a prepayment" → **GL105 JE-code-type Owner = OPTIONAL**. Prepayment "not in JB340" → **run JBPREPAY**. Picklist/column oddities are **grid-definition** issues (grid 36064 for GL095/JE inquiry, grid 36062 for AR173) — fix in the **Environment Specific / QSGY metadata layer** and have Services check it in.

---

## 14. Cluster K — AR173 / metadata-grid customization fragility (grid 36062)

A repeatable **Application Configuration** issue: custom screen changes silently revert.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **AR173 search by Accounting Date stops working every few months** | The custom **"Filter Expression Col" values on grid #36062** (Customer Item Inquiry) get **cleared**, and the change wasn't checked into the **QSGY metadata layer** so a release/override wipes it | Re-add the Filter Expression Col on grid 36062; **include the custom grid filtering logic in the metadata catalog (QSGY)** so it survives | 24-00973662 ; 24-00963418 (added Accounting Date to grid 36062, Reg SQL `SELECT_FD_CUSTOMEROPENITEM`) |
| AR173 **displays incorrect AR Invoice documents** | Screen defect | Bug (in a pending patch) | 23-00893491 |
| AR308 **Control Total slightly cut off** | Display defect | Bug | #1379562 |

**Fix recipe:** any "this screen customization keeps disappearing" is a **metadata-layer check-in** problem — the custom grid/filter change must live in the **QSGY (Environment Specific) metadata catalog**, not just be applied ad-hoc, or the next release overwrites it. Grid IDs of note: **36062** = AR173 Customer Item Inquiry; **36064** = GL095/JE Inquiry.

---

## 15. Cluster L — AR/BR reports (Deposit Batch Review, ARR003, ARR014, cash-call print)

| Report / symptom | Root cause | Fix | Case |
|---|---|---|---|
| **Deposit Batch Review Report** shows **deleted** deposits (BD…) on the unposted report | Report didn't filter deleted rows | **Added `DELETED = 0` check on the MASTER table** | 23-00913062 |
| **Deposit Batch Review Report** errors in the **web app** (picklist error) | Report defect | Fix in **UPS 2025.04.1.11** (delivered via upstream patch) | 26-01094576 |
| **ARR003** "Netted" column blank for some owners | Null `BA_SUF` handling | **SQL fix** to select the max BAS address from the QRA address table when `BA_SUF` is null | 23-00907751 |
| **ARR014 Payment Application Journal Report** (QP074) | Report defect | Report fix | 22-00646950 |
| **Cash-call invoice won't print** (AR076 batch) — error | **SSRS server paths pointed at a Quorum internal server** | Correct the SSRS path for the client environment | 25-01053811 |
| Cash-call script "not working at end" (Script 38) | Config / script | App config | 24-00989983, 24-00984736 |

**Fix recipe:** AR/BR report bugs are usually **report-SQL** (null handling, deleted-row filter) or **SSRS path / release** issues. "Shows deleted records" → `DELETED = 0` filter (23-00913062). "Won't print" → check the **SSRS path** points at the client's report server, not a Quorum-internal one (25-01053811).

---

## 16. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#66157** | Bug / Closed | AR payment application can only **approach zero**, preventing reconciliation | §4 | (defect family) |
| **#75995** | Requirement / Closed | AR308 — AR payment application can only approach zero | §4 | — |
| **#1566024** | Bug / Closed | SRC — **Unable to Delete Receipts from AR308: Deposit Creation with Match** | §8 | 22-00868012 |
| **#1722419** | Bug / Closed | 2025.04: **BR005 batch bank reversal does not show any record for reversal** | §9 | 23-00935181 |
| **#1413340** | Bug / Closed | GLE — 21-00213049 — **BR005 Bank Recon Check Out of Balance** | §9 | 22-00547077 |
| **#1435865** | Requirement / Closed | OOC — Upstream 2020.07 Hotfix Feb-2022 — **EQC** (BR005 batch-creation timeout) | §10 | 22-00651669 |
| **#1524343** | Bug / Closed | MEW — **users able to Void a check marked reconciled/cleared** | §11 | 24-00964709 |
| **#1781008 / #1790246** | Bug / Task — Acceptance/Closed | Range — **Unreconciled ACH Payment QP063 and BR005** | §11 | — |
| **#1813192 / #1821482** | Request Global Cloud Ops / Closed | EQC — 26-01102535 — **Invalid clear dates in BR005 and AP157** (UBT/PRD) | §12 | 26-01102535 |
| **#1799888** | Database Change / Closed | Update default QCFS Import config **ARD/DEP on MT100 for AR308 Import** | §6 | — |
| **#1443233** | Bug / Closed | QCFS Classic — **BR005 — "Object reference not set" unhandled exception** | §9 | — |
| **#1651187** | Bug / Closed | **BR005 — exception opening links** (customer/vendor item inquiry) | §9 | — |
| **#1379562** | Bug / Closed | QCFS Classic — **AR308 — Control Total slightly cut off** | §14 | — |
| **#226951** | Bug / Closed | AHT — Classic QCFS — WF005 → AR308 — **DocManagement Exception** | §7 | — |
| **#1618436 / #1623794** | Bug / Closed | **Fast-track POSTWKFL** picked up & erroring / "Post In Progress" status | §5 | — |
| **#1565787 / #1683641 / #1689851 / #1724602 / #1752121** | Requirement / Bug — Closed | **QCFSIMPCYC / POSTWKFL performance** (batch-creation/post time; open-item applied; inactive BU) | §5 | — |

> Several actionable cases were dispositioned **operationally** with no single product WI: AR044 Allow-Non-Zero workaround + $0-export defect (25-01006390), QCFSIMPCYC re-stage scripts (25-01058210, 26-01070724), BOABANKSTMT date-correction script (26-01102535), Document Management **Patch 4** (25-01060641), BR005 forced-picklist **Hotfix 11** (23-00906555), GLE **Patch 5 / 2021.04** (22-00547077), Deposit-Batch-Review report fix **UPS 2025.04.1.11** (26-01094576). Confirm exact build/patch in the Upstream release notes before stating fix availability.

---

## 17. Diagnostic SQL

> **Caveat:** QCFS lives in Oracle (per-client schema, e.g. `QCFS` / client DB like `PRMU_PRD`). Table/column names below come from case repro text and code search — **verify against the client schema first**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction. Many "fixes" here are **config in a screen** (BR036, GL105, AR044, SM006) — prefer the screen over raw DML.

```sql
-- A. Bank account missing a Deposit Journal Def (the AR308 autoNumber error, §6)
--    Fix in BR036 (sets these columns); do not hand-edit unless directed.
SELECT BANKACCOUNT_NO, BANKACCOUNT_NM, IDJOURNALDEFDEPOSIT_USERKEY, IDJOURNALDEFDEPOSIT_NAME
FROM   BANKACCOUNT
WHERE  IDJOURNALDEFDEPOSIT_NAME IS NULL;

-- B. AR open items / payment application for a batch that won't post ("approach zero", §4)
SELECT ID, OPENITEM_ID, APPLIEDAMT, CURRENTAMT
FROM   BATCHPAYMENTAPPLICATIONOPENITEM
WHERE  ID = '<ID from the error context>';
-- Red flag: a $0 line (APPLIEDAMT/CURRENTAMT ~0) from a QRANET batch → AR044 Allow-Non-Zero workaround.

-- C. QRA interface staging — was an open item re-exported (double EXPOI / over-apply, §4)?
SELECT * FROM SEXTN_CORE_INTFC_QRA
WHERE  OPEN_ITEM_ID = '<oi>' ORDER BY EXPORT_DT;
-- Two unprocessed rows for the same open item = the 23-00932894 double-export pattern.

-- D. Batches stuck Post Pending — is DATETOPOST a future date, or is a lock held? (§5)
SELECT BATCH_ID, WF_STATUS, DATETOPOST FROM <AR batch header>
WHERE  WF_STATUS = 'Post Pending';
--    Stale POSTWKFL lock → release in QP110 (find the PQID first).

-- E. Period open/closed for the BU + module (the "Could not post / balance spans months", §5/§9/§18)
--    Use SM006 in-app; the hard close is re-runnable.

-- F. Bad imported dates (BOABANKSTMT YY vs YYYY → 1926, §12)
SELECT REFNO, CLEAR_DT FROM <bank-statement / payment table>
WHERE  CLEAR_DT < DATE '1950-01-01';   -- 19xx rows are the corrupted ones

-- G. ACH auto-marked reconciled, blocking a void (§11)
SELECT PAYMENT_NO, BANKRECONCILED, BANKRECON_DT FROM <payment/check table>
WHERE  PAYMENT_NO = '<ACHxxx>';
-- Short-term: set BANKRECONCILED = NULL for the specific item(s), then void (per #1524343 guidance).

-- H. AR173 grid customization that keeps reverting (§14) — verify the grid/metadata, not data:
--    Grid #36062 = AR173 Customer Item Inquiry (Reg SQL SELECT_FD_CUSTOMEROPENITEM);
--    Grid #36064 = GL095 / Journal Entry Inquiry (CUST_NO hidden by core). Fix in QSGY metadata layer.

-- I. GL vs AR/sub-ledger imbalance (GL014) — a Balance Refresh, not a defect (§18)
--    SM006 → select BU/period → Links → Balance Refresh (re-runnable, refreshes ACCOUNTBALANCE).
```

---

## 18. Expected-Behavior / User-Education FAQ

~52 AR + ~20 BR Training cases and ~26 AR + ~13 BR Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "AR076/JIB batch **Could Not Post**" (generic, no detail) | Almost always **period closed** or a **BA not approved**: reopen **SM006** for the AR module (clear the closed-month dates) then **reject → approve → post**; or approve the BA on the Business Associate screen first | 25-01042452, 26-01065273, 26-01079757, 25-01009380 |
| "Batches **stuck in Post Pending**" | Wait for POSTWKFL to finish, or **release a stale lock in QP110**; if `DATETOPOST` is future it posts that day | 25-01006596, 25-01051167, 25-01022292 |
| "Can't **reject/delete** a batch — 'Cannot move to the status specified'" | Unlock → Reject (BUSSVCRUN runs, completes with that error) → re-run, and the **delete option enables**; or fix DOI errors then reopen the month | 25-01021205, 25-01009380 |
| "**Prepayment not in JB340**" / "AR173 credit only on one property vs JB340 on all" | Run **JBPREPAY** after the AR076 prepayment posts; **AR173 is the customer open-item view, JB340 verifies cash-call/prepayment balances** — trace the line via double-click → GL095 → BI# → AR076 | 25-01036401, 25-01047821 |
| "**AR090 / invoice adjustment** error" or "can't set adjustment" | The user has **no Invoice Adjustment amount in SM003** — set a non-zero amount for that username (new usernames need it re-set) | 25-01030610, 25-01021283 |
| "POSTWKFL **permissions** error — no permission to post" | Add group **QCFS-PAY APP POST (5427)** to the user via **SC010** | 25-01013808 |
| "**Bank Rec auto-selects another item** when I check one" | BR005 groups by **REFNO + REFNOSOURCE** and selects everything with the same check #; reverse & recreate with a distinct Check No. to separate them | 25-01026831 |
| "Lost a December bank rec before **hard close**, now can't post January" | **Hard close is re-runnable** — reopen, post the bank rec, re-run hard close | 25-01007315 |
| "**GL014 imbalance** but GL095/096 and AR173 tie out" | Run a **Balance Refresh** (SM006 → BU/period → Links → Balance Refresh) — re-runnable, refreshes `ACCOUNTBALANCE`, changes no GL data | 25-00997954 |
| "Reversal **not showing in AR173**" | Expected — a posted reversal removes the Closed flag and restores the current amount; verify the apply/reverse cycle | 25-01010061 |
| "Can post to a **cost-center-required account on AR308**" / "want CC validation on AR308" | AR308 isn't set up to use code-block CC validation today — that's an **enhancement** | 25-01010036 |
| "Duplicate invoices imported from **QLS**" / "$0 invoices to clear" | MT100 config imports them "posted" so they hit the GL → **offset via an MJE**; close $0 invoices in **AR086** (Accepted both lines, post) | 25-01003156, 24-00987084 |
| Electronic lockbox / sFTP setup, report-population "how does ARR002 work", invoice-adj-type meaning | Configuration/education — provide credentials/format/explanation (lockbox is config; Invoice Adj Type is informational only) | 24-00980923, 25-00999272, 24-00987928, 25-00995771 |

**Tell-tale it's user/expected:** a generic "Could Not Post" that's really a **closed SM006 period** or an **unapproved BA**; a Post-Pending that just needs **time or a QP110 lock release**; a prepayment "missing" because **JBPREPAY** hasn't run; an AR090 block because **SM003** isn't set; a GL014 imbalance fixed by a **Balance Refresh**; a bank-rec auto-select driven by **REFNO grouping**. Verify the **period status, BA approval, and the relevant config screen** before treating it as a defect.

---

## 19. Key Code, Screens & Repos

### Screens / processes
| Screen / process | Purpose | Notes |
|---|---|---|
| **AR076** | Batch Invoice Creation (JIB, prepayment, cash-call) | Prepayment owner-required → GL105; picklist → grid 36064 |
| **AR086 / AR090** | Invoice acceptance / **adjustment** | Adjustment needs SM003 per-user amount |
| **AR173** | Customer Item Inquiry (AR sub-ledger) | Grid **36062**; double-click → GL095 |
| **AR308** | Deposit Creation / **with Match** | Needs **BR036** Deposit Journal Def; doc-mgmt for attachments |
| **AR044** | AR Configuration (per BU) | **Allow Non-Zero Payment Application** flag (§4) |
| **BR005** | Bank Reconciliation | Balance/date/reversal defects (§9); timeout config (§10) |
| **BR036** | Bank Account / Deposit Journal Def setup | Writes `BANKACCOUNT.IDJOURNALDEFDEPOSIT`; gates AR308 accounts |
| **CW005** | Check register / status | Needs synced bank-acct number formats (§11) |
| **POSTWKFL / QP110** | Post Workflow / **release stale lock** | §5 |
| **QCFSIMPCYC / EXPOI** | QCFS import cycle / QRA Export Open Items | Timeout → re-stage; double EXPOI → over-apply (§4/§5) |
| **JBPREPAY → JB340** | Prepayment balance build / verify | §13 |
| **SM006 / SM002 / SM021 / SM003** | Period close / BU & bank config / per-user adj | §18 |
| **GL105 / GL013 / GL095 / GL096 / GL014** | JE code types / accounts / JE detail / balance | §13/§18 |
| **MT100** | Import metadata (AR308 ARD/DEP default) | #1799888 |

### Code locations (confirmed via ADO code search)
| Symbol / area | Repo / path | Cluster |
|---|---|---|
| `PaymentApplicationWorkflow.cs`, `DepositWithMatchWorkflow.cs`, `PaymentApplicationTransactionBase.cs`, `InvoiceAdjustmentWorkflow.cs` ("must approach zero") | `Quorum.Upstream.QCFS.Web / Quorum.QCFS.BS/Base/` | §4 / §8 |
| `BankAccountDO.cs`, `BankaccountVM.cs`, `ARConfigurationDO.cs` (`IDJOURNALDEFDEPOSIT`) | `Quorum.Upstream.Shared.Web / Quorum.QCFS.DataObject/`, `Quorum.Upstream.QCFS.Web / Quorum.QCFS.DATA/` | §6 |
| `BANKRECONCILED`, Deposit/Check-run journal datasets | `Quorum.Upstream.QCFS.Web / Quorum.QCFS.DATA/CodeGen/` (`DepositJournalDataSet.cs`, `CheckRunJournalDataSet.cs`) | §9 / §11 |
| Classic AR308 / BR005 screens | `Quorum.QCFS.ClassicGUI` / `Quorum.*.ClassicGUI` (doc-mgmt exceptions, control-total) | §7 / §9 / §14 |

### Repos
- **`Quorum.Upstream.QCFS.Web`** — the web QCFS app: business-services (`Quorum.QCFS.BS` — payment-application & deposit workflows, the "approach zero" validation), data layer (`Quorum.QCFS.DATA`), data objects (`Quorum.QCFS.DataObject`).
- **`Quorum.Upstream.Shared.Web`** — shared QCFS data objects / view models (BankAccount, AR config).
- **`*.ClassicGUI`** (`Quorum.QCFS.ClassicGUI`, plus QLS/QPTM) — the classic Win-forms screens (AR308 doc-management exceptions, BR005 picklist/control-total, the WinForms "Input Value Outside Grid" picklist bug).
- **Grid / metadata** — screen grids (36062 AR173, 36064 GL095) live in the **Grid Definition / Environment-Specific (QSGY) metadata layer**; custom changes must be checked into the metadata catalog (§14).

---

## 20. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- The "**must approach zero**" failure is from a **$0 AR trans-type export** (workaround via AR044 first; the real fix blocks $0 `TRANS_AMT`/`TRANS_QTY` export — 25-01006390, #66157 family).
- **AR308 delete** throws `FIRE_ENTITY_EVENTS` / `GET_ENTITY_ACTION_TYPE` (#1566024); **BR005** balance-vs-accounting-date (Defect 301, 24-00977408), **reversal shows nothing** (#1722419), **void/ACH date exclusion** (22-00825516, 23-00931115); **can't void a reconciled ACH** (#1524343).
- Provide: **batch ID (BI…/BD…) + PQID + exact error/context table+ID**, BU/company, the bank account or open item, and a repro. Confirm fix availability + target build in the Upstream release notes.

**Handle as Configuration / Cloud Ops when:**
- **AR308 "Deposit Journal Definition not set"** → **BR036** Deposit Journal Def = DEP (23-00935999, 24-00963987); which accounts show in AR308 (25-01041812).
- **AR076 prepayment requires owner** → **GL105** JE-code-type Owner = OPTIONAL (25-01031193); prepayment not in JB340 → **run JBPREPAY** (25-01028952).
- **Grid/metadata** customization that reverts → check into **QSGY** (AR173 grid 36062 — 24-00973662; GL095 grid 36064 CUST_NO — 25-01040928).
- **Import** definition/path (BOABANKSTMT YY/YYYY date — 26-01102535; QGM→AR path — 25-01045557; lockbox CSV — 24-00972630).
- **AR044 Allow-Non-Zero** workaround for $0 netting (disable scheduled POSTWKFL first, revert after — 25-01012055).
- **Document-management** attach/post failures → **redeploy doc-mgmt + ClassicGUI pipelines** / Patch 4 (25-01012104, 25-01060641).

**Operational / data fix (verify-SELECT in a transaction):**
- **QCFSIMPCYC re-stage** scripts for batches that never created (25-01058210, 26-01070724); **unlock** scripts for items locked by a half-deleted deposit (22-00654673); **date-correction** script for 19xx import dates (26-01102535); **NULL `BANKRECONCILED`** for ACH that must be voided (24-00964709).

**Handle as Training / Expected behavior (no fix):** see §18 — "Could Not Post" = closed **SM006** period or unapproved BA; Post-Pending = wait / **QP110 lock release** / future `DATETOPOST`; prepayment "missing" = run **JBPREPAY**; AR090 block = **SM003**; GL014 imbalance = **Balance Refresh**; bank-rec auto-select = **REFNO grouping**; AR308 cost-center validation = **enhancement**. Verify period status, BA approval, and the relevant config screen before treating as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 446 closed QCFS AR/Bank-Recon SF cases (AR 333, BR 113) — 72 actionable (Software Defect 36 + Application Configuration 35 + ChangeConfig 1) mined for fix recipes, plus ~35 Training/Customer-Error cases for the FAQ. ADO work items #66157, #75995, #1566024, #1722419, #1413340, #1435865, #1524343, #1781008/#1790246, #1813192/#1821482, #1799888, #1443233, #1651187, #1379562, #226951, #1618436/#1623794, #1565787/#1683641/#1689851/#1724602/#1752121.*
*Companion category groups (separate skills): Severance-tax/1099/ONRR (QCFS), JIB cost generation (JB-series), GL posting engine.*
