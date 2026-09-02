# SKILL: QCFS General Ledger (GL) Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QCFS (My Quorum Financial Accounting — upstream oil & gas core accounting / general ledger)
**Scope:** The QCFS core-financials back end as it surfaces under the **"General Ledger (GL)"** case category — which in this product is *broad financial accounting*, not just manual JEs. Covers: **Journal Entry / batch JE creation & posting** (GL025, BJE batches, POSTWKFL / Post Pending / Could-Not-Post), **AP voucher workflow** as it feeds the GL (voucher stuck/duplicate/rejected, AP055), **invoice import** (ADPUPLOAD/APDUPLOAD from OpenInvoice, QCFSIMPCYC, QRA→QCFS interface, MT100), **Chart of Accounts & account master** (GL013, JE Code Types), **JE inquiry/queries & DW** (GL095/GL096/GL097/GL098), **financial statements & canned reports** (GL014/GL016/GL232, SSRS), **vendor check / Positive Pay** (AP155/156/157, BK010), and **period close** (SM006).
**Companion skills:** AP-specific deep dives → SKILL_QCFS_Accounts_Payable.md (when written); AR → SKILL_QCFS_Accounts_Receivable.md; bank reconciliation → SKILL_QCFS_Bank_Recon.md; revenue/JIB upstream of the GL feed → QRA skills. This skill consumes data *interfaced into* the GL (from QRA revenue, AP invoices, JIB) and *produces* posted journal entries, financial statements, and the check/Positive-Pay output — when a GL number is wrong, check the **interface source and the account's JE Code Type / code-block config first**; the GL is usually the messenger.

> **Evidence base:** 847 closed QCFS "General Ledger (GL)" cases. Root-cause split: (blank) 174, **Training 125**, **Customer Error 82**, **Software Defect 60**, **Application Configuration 53**, Customer Cancelled 52, Other 42, Business Change 42, Performance 31, Hardware/Software Env Change 26, ChangeConfig 4, others. This skill mines the **117 actionable** cases (Software Defect 60 + Application Configuration 53 + ChangeConfig 4) for fix recipes, plus ~60 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. **Where a cluster has no clear documented fix, that is stated explicitly.**

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Posting stuck: Post Pending / Could-Not-Post / POSTWKFL (HIGH FREQUENCY)](#4-cluster-a--posting-stuck-post-pending--could-not-post--postwkfl)
5. [Cluster B — AP voucher workflow stuck / duplicate / rejected (feeds GL)](#5-cluster-b--ap-voucher-workflow-stuck--duplicate--rejected)
6. [Cluster C — JE Code Type / code-block missing on accounts → post & import errors](#6-cluster-c--je-code-type--code-block-missing-on-accounts)
7. [Cluster D — Invoice import defects: ADPUPLOAD / QCFSIMPCYC / QRA→QCFS / MT100](#7-cluster-d--invoice-import-defects-adpupload--qcfsimpcyc--qra-qcfs--mt100)
8. [Cluster E — GL025 batch JE creation: copy/paste, delete-row, multi-BU, attachments](#8-cluster-e--gl025-batch-je-creation)
9. [Cluster F — Chart of Accounts / GL013 maintenance (add / delete / synchronize)](#9-cluster-f--chart-of-accounts--gl013-maintenance)
10. [Cluster G — JE inquiry / queries / GL DW (GL095/096/097/098)](#10-cluster-g--je-inquiry--queries--gl-dw)
11. [Cluster H — Financial statements & canned/SSRS reports (GL014/016/232)](#11-cluster-h--financial-statements--canned-reports)
12. [Cluster I — Vendor check & Positive Pay (AP155/156/157, BK010)](#12-cluster-i--vendor-check--positive-pay)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Screens, Processes & Repos](#16-key-screens-processes--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| JE / AP / BJE batch **stuck in Post Pending**, never reaches Posted | POSTWKFL not running / job pointed at a dead server / stuck PQID lock / huge batch still validating | §4 — QP045: is POSTWKFL scheduled & actually processing? Cancel stuck PQID + release lock |
| POSTWKFL **"Initialize Function Failed. Duplicate process found"** | A prior POSTWKFL PQID is still running and holding the lock | §4 — QP045, filter Process ID=POSTWKFL, find the Processing PQID, cancel + release lock (26-01107081) |
| Batch goes to **"Could Not Post" (CNP)** | Account missing a JE Code Type / code-block; intercompany-reversal bug; eSuite-side change | §6 / §4 — check the account's JE Code Type in GL013 first |
| **AP voucher** stuck "Waiting for Approval", duplicated in inbox, or rejected-but-not-returned | Orphaned / duplicate Workflow ID (WFID); workflow lock | §5 — cleanup/reset script to set voucher back to Draft & clear WF artifacts |
| Import/post error **"Account does not have JE Code Type"** / "Foreign key constraint" / null on equity accounts | Account in GL013 has **no JE Code Type ID** (now required in newer builds) | §6 — assign a JE Code Type (all fields Optional) to the account(s) |
| **ADPUPLOAD / APDUPLOAD** import fails (syntax/Object-reference/timeout) or **doubles amounts** | Import-engine defect: concurrent child jobs, connection-pool timeout, AFE/JIB-deck resolution | §7 — confirm fixed build; short-term: split SRC_DOC, override max connection attempts |
| **QRA export shows in QRA but not in QCFS GL**, or out-of-balance after interface | COA missing JE Code Type, OR orphaned staging rows (MT100 config cleared) | §7 — JE Code Type (§6) + restage via QCFSIMPCYC |
| GL025 **copy/paste of cost centers / decks fails or screen clears** on bad account | Older-build GL025 grid defect (fixed) OR AFE tier precedence (expected) | §8 / §15 — confirm build; check AFE tier on the deck |
| GL025 **can't delete a batch / detail row** | Grid defect (fixed in upgrade) OR batch in non-Normal control type / sent through WF | §8 / §9 — check BATCH CONTROL TYPE; older bug needs upgrade |
| **Canned/financial-statement reports won't run** ("report failed") | Global config `REPORTS / SSRS_ENDPOINT_URL` wrong | §11 — set SSRS_ENDPOINT_URL to the correct `%SSRS%` value |
| **Reports won't email** out of Quorum | Event Detector 227 (BATCH REPORT EMAIL) / Event Type `BRPTEMAIL` not Active | §11 — activate the event |
| **Financial statement / Trial Balance wrong or not zeroing** | FS mapping (GL232/GL016) OR soft-close not run for the month | §11 / §15 — run soft close; review FS mappings |
| GL095/GL096/GL097 query **returns no data / errors / DW stale** | Query defect or DW (`*_DW`) not refreshing nightly | §10 — confirm patch; check DW refresh job |
| Vendor **checks returned by bank** / ZIP & State misaligned on AP155 | BA ZIP missing hyphen + `WEB_BA_MASK_ZIP_CD` mask config; AP155/156/157 column misalignment defect | §12 — data script to fix BA ZIP + mask config; hotfix for the screen |
| "Can't close / re-open the year", "TB won't zero", "where do I…" | Period close / FS mapping / how-to | §15 Expected-Behavior FAQ |

---

## 2. Pipeline & Concepts

```
[QRA Revenue / JIB]   [AP Invoices: OpenInvoice → ADPUPLOAD]   [Manual JE: GL025]
        │                          │                                  │
        ▼  INTERFACE / IMPORT      ▼                                  │
   QP043 (QRA→QCFS GL/LOS export) ; QCFSIMPCYC (QP073) import cycle ; MT100 (journal/trans definitions)
        │   staging: QSTAG_CORE_INTFC_EXTERNAL_IMP / SEXTN_CORE_INTFC_*
        ▼
   [BJE batches in GL025]  ──(account must have a JE Code Type in GL013)──►  WORKFLOW (approval)
        │
        ▼  POSTWKFL  (segregated post-workflow process; runs ~every 5 min; QP045 monitors it)
   [POSTED to the GL]  →  Post Pending → Posted  (or → Could-Not-Post / CNP on error)
        │
        ├──► JE INQUIRY / QUERIES (GL095 doc/JE, GL096 cost-center, GL097/GL098 DW)
        ├──► FINANCIAL STATEMENTS / REPORTS (GL014 balance sheet, GL016, GL232 FS config; SSRS canned reports)
        ├──► PERIOD CLOSE (SM006: soft close, fiscal close, year close/re-open, retained-earnings roll-forward)
        └──► AP DISBURSEMENT (vendor check AP155/156/157; Positive Pay file BK010 → bank)
```

### Key terms (Quorum/QCFS vocabulary)
- **QCFS** = Quorum core financial system (My Quorum Financial Accounting). Runs on SQL Server (DBs named `<CLIENT>_PRD##UPS_QCFS`). Has a **Web app** and a **Classic** app — many web-only screen bugs have a Classic-app workaround (25-01050909, 25-01043706).
- **GL025** = **Batch Journal Entry Creation** screen. **BJE** = Batch Journal Entry; batches carry a **BATCH CONTROL TYPE** (Normal / Conversion / etc.) and a **Tier** used for validation/coding.
- **POSTWKFL** (a.k.a. PSTWKFL) = the **segregated post-after-workflow** process that takes approved batches from **Post Pending → Posted**. Should run on a standard ~5-minute schedule. Monitored/cancelled in **QP045** (process queue). Code: `QSegregatedPostWkflBalanceUpdate.cs` (`Quorum.Upstream.QCFS.Batch`).
- **Post Pending / Could-Not-Post (CNP)** = batch states. Stuck Post Pending = process not running or huge batch; CNP = a validation/posting error (often a missing JE Code Type or an intercompany-reversal bug).
- **JE Code Type** = a required attribute on every GL account (set in **GL013**, the Chart-of-Accounts / account-maintenance screen). Newer builds **require** it; an account without one throws "Account does not have JE Code Type" or a null/FK error on post/import. Fix = assign a JE Code Type (often a new one with **all fields marked Optional**).
- **Code block / code-block definition** = the per-account set of required coding fields. Populating a code-block field on an account that has no code-block definition errors in newer builds (25-01042275).
- **ADPUPLOAD / APDUPLOAD** = the process that uploads/stages **OpenInvoice (OI)** AP invoices into QCFS. `ADPIMPALLV` is a step. Stages into `QSTAG_CORE_INTFC_EXTERNAL_IMP`; the `QCFSIMP` step builds the batch.
- **QCFSIMPCYC** (process **QP073**) = the import cycle that interfaces staged data (AR/AP/JIB/QRA) into QCFS batches; reads/writes `SEXTN_CORE_INTFC_*` staging and needs valid **Journal/Trans definitions** (MT100).
- **QP043** = "Export GL & LOS data to QCFS" (the **QRA → QCFS** interface). **MT100** = the screen holding journal/transaction definitions used by the interface; **must be Quorum-managed** (a V16/older bug lets it silently clear settings — 24-00950935).
- **GL095** = JE/document inquiry; **GL096** = cost-center query; **GL097/GL098** = GL **data-warehouse (DW)** inquiry screens backed by `*_DW` tables (e.g. `JOURNALENTRYINQUIRY_DW`) refreshed nightly.
- **GL013** chart of accounts; **GL014** balance sheet / balance refresh; **GL016** + **GL232** financial-statement configuration; **GL282** financial reporting.
- **SM006** = Global Company Maintenance / **period & fiscal close** (soft close, fiscal close, year close/re-open). The fiscal-close flag is **not** a permanent lock — Close is re-runnable.
- **AP155 / AP156 / AP157** = vendor check / check-inquiry screens. **BK010** = bank-account setup driving **Positive Pay** file export. `WEB_BA_MASK_ZIP_CD` = ENV-metadata config controlling ZIP-code masking/formatting for the BA (business associate / vendor).

---

## 3. Decision Tree

```
QCFS "General Ledger (GL)" case
│
├─ Something STUCK in posting (Post Pending / CNP / POSTWKFL)?
│   ├─ POSTWKFL not moving / "Duplicate process found"        → §4  (QP045: is it scheduled? cancel stuck PQID + release lock)
│   ├─ Job error "server does not exist" / not scheduled       → §4  (schedule fix / point at valid server)
│   ├─ Batch in Could-Not-Post (CNP)                           → §6 first (JE Code Type), then §4 (intercompany-reversal bug)
│   └─ Huge batch (tens of thousands of GL rows) "slow"        → §15 (expected — it's validating, not stuck)
│
├─ AP VOUCHER workflow problem (stuck/duplicate/rejected) feeding GL?  → §5 (orphaned/duplicate WFID → reset-to-Draft script)
│
├─ POST or IMPORT error mentions JE Code Type / code block / null on account / FK?  → §6 (assign JE Code Type in GL013)
│
├─ IMPORT problem (OI invoices / QRA→QCFS / JIB)?
│   ├─ ADPUPLOAD/ADPIMPALLV syntax/Object-ref/timeout, or doubled amounts  → §7 (import-engine defect — confirm fixed build)
│   ├─ QRA exported but not in QCFS GL / out of balance                     → §7 (+§6) (restage via QCFSIMPCYC; check MT100/JE Code Type)
│   └─ MT100 settings cleared / orphaned staging rows                       → §7 (reload MT100 from DEV; restage)
│
├─ GL025 screen behavior (copy/paste, delete row, multi-BU, attachment)?   → §8 (grid defects — many fixed by upgrade)
│
├─ Chart of accounts maintenance (add/delete/synchronize accounts)?        → §9 (GL013: delete-script / DATAPUBLISH connection config)
│
├─ JE inquiry/query returns no data / errors / DW stale?                    → §10 (GL095/096/097 defect or DW refresh)
│
├─ Reports / financial statements won't run, won't email, or are wrong?    → §11 (SSRS config / BRPTEMAIL event / GL232 mapping / soft close)
│
├─ Vendor checks returned / ZIP-State misaligned / Positive Pay file error? → §12 (BA ZIP + WEB_BA_MASK_ZIP_CD; AP155 hotfix; BK010 adapter)
│
└─ "How do I close the year / why won't TB zero / how does X work"          → §15 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — Posting stuck: Post Pending / Could-Not-Post / POSTWKFL

**The single largest GL signature.** Batches sit in **Post Pending** and never reach Posted, or land in **Could-Not-Post (CNP)**. The mechanism is almost always the **POSTWKFL** segregated process (the thing that drains Post Pending), not the batch itself.

**Root causes & fixes seen:**
- **POSTWKFL not scheduled / disabled** → nothing drains Post Pending. **Fix:** enable POSTWKFL on the standard ~5-minute schedule (25-01006218 "PSTWKFL - Not scheduled").
- **Job pointed at a server that doesn't exist** (post-upgrade) → JEs stuck. **Fix:** repoint the job to a valid server (24-00990635, Permian upgrade).
- **A prior POSTWKFL PQID is still running and holds the lock** → new runs fail with **"Initialize Function Failed. Duplicate process found."** **Fix (26-01107081):** in **QP045**, filter Process ID = `POSTWKFL`, Process Status = Processing; double-click the stuck PQID, **issue Cancel, then Release the Lock**. (Watch for genuinely-still-posting PQIDs first — see the "expected" note below.)
- **Stuck/transient at the process tier** → a **process-engine restart (QPEC)** clears it (22-00628247 "QPEC restart corrected the issue"; 22-00628370 "NWD_PRD restart"). Restart before assuming a code bug.
- **Intercompany AP voucher reversal created from Web** → voucher stuck CNP; **system bug fixed in 2022.04+**. Workaround: create the reversal voucher from the **Classic** app (25-01043706). A *reversal of a reclass* is **not supported**; newer builds validate against it (25-01052627 "Nullable object must have a value" → **ADO #1769179**, customer must upgrade).
- **Vendor-suffix validation missing** historically let bad-suffix batches stick in Post Pending (22-00520562/563, 22-00518351, 22-00672569 — Software Defect, validation added).

**Fix recipe:**
1. **QP045** — is POSTWKFL **scheduled** and is there a PQID actually **Processing**? If a stuck PQID holds the lock → Cancel + Release Lock (26-01107081). If not scheduled → enable it (25-01006218).
2. If POSTWKFL runs but a batch is **CNP** → open the batch error; jump to **§6** (JE Code Type / code block) which is the #1 CNP cause, then check for an **intercompany / reversal-of-reclass** pattern (25-01043706, 25-01052627 — needs ≥2022.04 / upgrade).
3. Transient / "no movement" with no clear data error → **restart the process engine (QPEC)** for that env (22-00628247, 22-00628370).
4. Confirm the batch isn't simply **huge** (tens of thousands of GL rows validate slowly but *are* progressing — 25-01035751, see §15).

---

## 5. Cluster B — AP voucher workflow stuck / duplicate / rejected

AP vouchers route through workflow before they post to the GL; a corrupted **Workflow ID (WFID)** strands them. These are **data fixes** (reset scripts) with a parallel **product hardening** to stop the double-submit.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Voucher submitted twice → **2 WFIDs**, one orphaned and frozen | Web allowed the same batch into workflow more than once | Script to clean the voucher WF; **separate case raised to patch** so only one active WF ID per voucher is allowed | 25-01049584 |
| **Duplicate workflow** on vouchers | Duplicate WF rows | Script to remove the duplicate Workflow for the vouchers | 26-01087415 |
| Voucher rejected but **did not return to submitter inbox**; stuck inconsistent WF state | Stuck workflow state tied to failed WF artifacts | Cleanup/reset script → return voucher to **Draft**, clear WF artifacts | 26-01084929 |
| "Workflow instance is no longer available…" / "Voucher was not submitted to workflow"; can't approve | WF locks | Script to **remove the workflow locks**; long-term hotfix to the client build | 25-01018721 |
| Posted vouchers **remain in AP inbox** | Version bug; aggravated by multiple instances open / resubmission | Resolved by **upgrade**; meantime keep one instance open, don't resubmit | 25-01019052 |
| Voucher stuck "Waiting for Approval" in inbox | Stuck inbox entry | Removed voucher from inbox (data) | 25-01041942 |

**Fix recipe:** confirm the voucher's WF state (look for **duplicate/orphaned WFIDs** or **WF locks**). The repeatable unblock is a **reset-to-Draft + clear-WF-artifacts script** (26-01084929, 25-01018721, 25-01049584). The recurring root defect is the **Web app letting a voucher into workflow more than once** — when you see duplicate WFIDs, note whether the client is on a build that has the single-active-WFID guard (raised off 25-01049584). Many of these auto-close on "no response after UAT validation" — verify the script actually cleared the state before closing.

---

## 6. Cluster C — JE Code Type / code-block missing on accounts

The **most common Application-Configuration root cause** for posting and import failures. Newer QCFS builds **require every GL account to carry a JE Code Type** (and a valid code-block definition). Older data converted before this rule trips errors on post/import.

| Symptom (verbatim) | Root cause | Fix | Case |
|---|---|---|---|
| GL025 posting error; intercompany JEs erroring with a **null** error on equity accounts | Equity accounts had **no JE Code Type ID** (now required in the new build) | Assign JE Code Type IDs to the accounts missing them → null error clears, entry posts | 23-00915415, 23-00903880 |
| **QRAREV import: "Account Does not have JE Code Type Error"** | Accounts in GL013 with no JE code type | **Set up a new JE Code Type with all fields marked Optional** and assign to those accounts | 24-00995039 |
| QCFS export succeeds in QRA but **doesn't show in QCFS GL** | COA missing the appropriate JE Code Type | Add the JE Code Type to the account | 23-00915272 |
| JE Code Type error in smoke test | Customer populated a **code-block field on an account with no code-block definition** | Latest release adds a validation; fix the account's code-block setup | 25-01042275 |
| Foreign-key constraint / null error entering a JE | Same family — account attribute (JE Code Type / code block) not set | Configure the account | 25-01039575 (Training) |

**Fix recipe:** when *any* post/import error mentions **JE Code Type**, **null on an account**, **foreign key**, or **"could not post"** with no obvious data problem → open **GL013** for the offending account(s) and confirm a **JE Code Type ID** is assigned. If a class of accounts (e.g. equity) lacks one, **create a JE Code Type with all fields Optional** and apply it (24-00995039). This is config, not a code fix. ADO history confirms a recurring theme: #216506 "COA — 121 accounts have missing JE code types"; #254192/#258079/#265135 (APH "Account JE Code Type Issues").

---

## 7. Cluster D — Invoice import defects: ADPUPLOAD / QCFSIMPCYC / QRA→QCFS / MT100

Importing AP invoices (OpenInvoice via **ADPUPLOAD**) and interfacing QRA/JIB data (**QCFSIMPCYC / QP043 / MT100**) is a distinct **Software Defect**–heavy area.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Imported invoice amount DOUBLED** | Two **child jobs of ADPUPLOAD ran concurrently**; both inserted into `QSTAG_CORE_INTFC_EXTERNAL_IMP`, the `QCFSIMP` step combined both jobs' data into one invoice | Latest build: ADPUPLOAD **no longer launches a child job and locks by PQID until complete** → no duplication | 25-01023102 |
| **ADPUPLOAD timeout** "all pooled connections in use / max pool size reached" (Data Access Helper `QCFSDataHelper`) | Connection-pool exhaustion per file | Short-term: **override max connection attempts per file** (let it process); long-term: code modification | 25-01011282 |
| **ADPIMPALLV** step: "Incorrect syntax near the keyword WHERE" | Staging code bug in the AFE→Tier / DOI→JIB-deck resolution path | Hotfix (bug) | 25-01007131 |
| ADPUPLOAD "Object reference" error **when coded to a control account** | Import-engine null handling | Bug | **ADO #1744756** (APH, Closed) |
| **QP043 / MT100**: failed JIB import; MT100 config cleared (V16 bug lets the screen silently change untouched settings) → orphaned staging rows with no journal/trans definition | (1) MT100 must be Q-managed; client edits cleared it. (2) Orphaned rows in SEXTN staging | (1) Script to **reload MT100 from DEV A1**; (2) script to **delete orphaned staging rows and rerun QCFSIMPCYC** to re-interface | 24-00950935 (= 24-00948961) |
| **QRA→QCFS export not making it to QCFS** | Batch didn't interface | Script to **reimport the QRA batch** | 22-00680638 |
| QRA→QCFS **out of balance** (BU 107/108) | QRA-side data | Script provided; opened a **QRA-team case** to root-cause | 22-00674469/480 |
| Rev batch stuck Post Pending when imported via QCFSIMPCYC and **BU is inactive** | Inactive BU not handled | Bug | **ADO #1752121** (APH, Closed) |
| QCFSIMPCYC very slow (open-item applied to AR batch; no BA_NO match) | Performance | Perf fixes | **ADO #1724602, #1782515** (Closed); #1565787/#1682284/#1683641 quick-wins |

**Fix recipe:**
1. **Doubled amounts** → almost certainly the **concurrent-child-job** ADPUPLOAD bug (25-01023102). Confirm the build has the PQID-lock/no-child-job change; if not, hotfix/upgrade. As a one-off, dedupe `QSTAG_CORE_INTFC_EXTERNAL_IMP` for that file.
2. **Timeout / pool exhaustion** → override max connection attempts per file as the unblock; long-term code fix (25-01011282).
3. **Syntax / Object-reference errors** in ADPIMPALLV / control-account coding → import-engine defect; escalate with the PQID and SRC_DOC split (25-01007131, #1744756).
4. **QRA exported but not in QCFS** → first check **JE Code Type (§6)**; then check **MT100** integrity and **restage via QCFSIMPCYC** (24-00950935, 22-00680638). MT100 should never be client-edited.

---

## 8. Cluster E — GL025 batch JE creation

GL025 grid behavior (copy/paste, delete-row, multi-BU, attachments). Mostly **Software Defects already fixed in newer builds** — confirm the client's version first.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Can't delete batch detail rows**; "Delete row information cannot be accessed through the row" | Grid delete defect | Fixed in upgrade (SRC) | 24-00943303 |
| **Copy/paste of cost centers fails / screen locks** when an invalid account is pasted (2020.03) | Old GL025 grid bug — once an invalid account is pasted, nothing on the screen can be saved | Fixed in newer versions (also perf changes to AFE/cost-center auto-populate) | 25-01001961 |
| **Grid copy/paste doesn't work for entries with multiple BUs** | Multi-BU copy/paste defect | Hotfix | 22-00631158; **ADO #1327661/#1328329/#1366499/#1372282/#1378765/#1539899** (EQT GL025 copy/paste program) |
| **Cost center not populating** in GL025 | Defect | Hotfix provided | 22-00645838; related #1534675 (cost center in GL025 missing in GL095 via copy/paste) |
| **GL025 not validating Tier when Drafter clicks Approve** | Validation defect | **Patch 7 on 2020.09 (ADO #1458999)** | 22-00663381 |
| Attachment not opening (GL025) / documents not displayed after import | Attachment-handling defect | Bug (2026.04) | **ADO #1788555, #1789707**; AP055/GL025 doc-copy inconsistency #1655846 |
| AP voucher creation screen **clears after any error/warning** (Web) | Web batch-screen defect | Workaround: use **Classic** app for AP batch create/modify/delete | 25-01050909 |
| I/C offset creates **multiple offset entries** | Intercompany-offset defect | Software Defect | 22-00674410 |
| FA010/GL025 serial-number length | Enhancement | Feature | #1743388 (EQC) |

**Fix recipe:** identify the GL025 behavior and the client's **build** — copy/paste-lock, delete-row, multi-BU copy/paste, and tier-on-approve are all **known fixed defects** (25-01001961, 24-00943303, 22-00631158, 22-00663381). If on an old build, the answer is upgrade/hotfix; the **Classic app** is the standard interim workaround for Web grid bugs (25-01050909). Distinguish from the *expected* "default decks not appearing" case (AFE Tier precedence — §15, 25-01045261).

---

## 9. Cluster F — Chart of Accounts / GL013 maintenance

Add / delete / synchronize accounts. Deletes that the UI blocks are done by **scoped scripts**; "synchronize" failures are **connection config**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Can't delete a GL account** created by mistake / never used (GL013) | UI won't delete used/locked accounts | **Script to delete the unused accounts** in GL013 | 23-00885678 |
| Can't delete a **test BJE batch** (GL conversion type, sent through WF) | BATCH CONTROL TYPE = Conversion blocks delete | Script to set batch to **Draft** and change **BATCH CONTROL TYPE → Normal** so the user can delete it | 25-01005486 |
| **Synchronize Accounts in GL013** errors: "Exception has been thrown by the target of an invocation" (DATAPUBLISH) | New company missing connection config | Add **Connection ID `QLS` and `QLandDataHelper`** in Connection Management of the **Maintenance app** (per KB article 000003851) | 24-00989365 |
| Chart-of-Account **attribute updates** | Config | resolution pattern unclear from mined case (Resolution__c blank) — treat as COA attribute change in GL013 | 23-00922838 |
| Deactivate / correct GL accounts | Account maintenance | Software Defect (corrections) | 22-00682730 |

**Fix recipe:** for "**can't delete**" an account or batch, the UI is correctly blocking a used/locked/non-Normal record — resolve by a **scoped script** (delete unused account 23-00885678; reset batch to Draft + Normal control type 25-01005486) after a verify-SELECT. For **Synchronize Accounts / DATAPUBLISH** errors on a *new company*, the cause is **missing Connection Management entries** (`QLS`, `QLandDataHelper`) in the Maintenance app, not a code bug (24-00989365, KB 000003851).

---

## 10. Cluster G — JE inquiry / queries / GL DW

GL095 (JE/document), GL096 (cost center), GL097/GL098 (data-warehouse) query screens.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **GL097 not refreshing nightly** — table `JOURNALENTRYINQUIRY_DW` stale | DW refresh job not populating | resolution pattern unclear from mined case (Resolution__c blank) — check the nightly **DW refresh** job that loads `JOURNALENTRYINQUIRY_DW`; reschedule/rerun | 22-00871717 |
| **GL095 returns no data when data is available** | Query defect | Delivered via patch (22-00256305) | 22-00687036 |
| **GL096 Cost Center query error** | Query defect (opened 2017) | Consumed in a later release | 22-00597800 |
| **Vendor number not populating in GL095** | Display/query defect | Tracked under 20-00094356 | 22-00512784 |
| Can't view document/image in GL095 (cross-company JE); poor doc-attachment performance | Attachment defects | Software Defect | 22-00823235, 22-00825631 |
| GL095 JEs **locked** (BJE…) | Lock state | Software Defect / script | 22-00690487 |
| GL DW tables usable in QCFS (GL097 & GL098) | Enhancement/clarification | Software Defect (delivered) | 24-00948000 |

**Fix recipe:** "query returns no data / errors" on GL095/096 are mostly **fixed query defects** — confirm the patch level. For **GL097/GL098 stale data**, the screens are backed by **`*_DW` tables** (`JOURNALENTRYINQUIRY_DW`) refreshed by a **nightly job** — verify that job ran; the screen itself isn't broken. Document-view/attachment issues in GL095 are a separate attachment-handling defect family (cross-ref §8 attachment bugs).

---

## 11. Cluster H — Financial statements & canned reports

Reports that won't run, won't email, or show wrong numbers.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Canned QCFS reports won't run** ("UAT reports will not run", "PRD A1 reports failing") | Global config `REPORTS / SSRS_ENDPOINT_URL` wrong/blank | Set Global config **Key Group `REPORTS`, Key `SSRS_ENDPOINT_URL`** to the correct `%SSRS%` value | 23-00904243, 23-00921346 |
| **Reports not emailing** from Quorum | Event not active | **Event Detector 227 (BATCH REPORT EMAIL)** / Event Type Code **`BRPTEMAIL`** was not Active → activate it | 23-00915691 |
| **Financial Statement changes** (mappings) | FS config | **Adjust FS configuration in GL232 and GL016** | 23-00913295 |
| **Trial Balance not zeroing out** (V17) | Soft close not run | **Run the soft-close process** for the month | 25-01026344 (Training) |
| Cost Center Trial Balance report | Report config | Application Configuration (report setup) | 23-00924809 |
| QEMAIL attachment not attaching | Email/report defect | Software Defect | 25-01013171 |

**Fix recipe:** "reports won't run" in a new/refreshed env is **99% the `SSRS_ENDPOINT_URL` global config** (23-00904243, 23-00921346) — check it first. "Won't email" → the **`BRPTEMAIL` / Event Detector 227** event is inactive (23-00915691). "Statement numbers wrong" → **FS mapping in GL232/GL016** (23-00913295) or a **soft close** that hasn't run for the period (25-01026344). These are configuration, not defects.

---

## 12. Cluster I — Vendor check & Positive Pay

AP disbursement output (checks + bank Positive Pay file). A recurring **ZIP/State formatting** defect plus per-client Positive Pay adapters.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Checks returned by bank** — ZIP printed **without the hyphen** | BA ZIP stored without hyphen + missing mask config | **Script to fix BA ZIP_CD** + set **`WEB_BA_MASK_ZIP_CD`** in the ENV metadata layer so ZIPs are entered/formatted correctly | 26-01083748 |
| **ZIP & State misaligned** on AP155 / vendor check-inquiry screen | Data misalignment on AP155/156/157 | **Script to align the data** (run in UAT then PRD); **long-term hotfix** to the screen | 26-01089614, 26-01091641, 26-01093457 (Upstream 2025.04 Hotfix Apr-2026) |
| **Positive Pay file** issue | Check form + export defect | **Check-form update + engineering code fix** for AP positive-pay export | 25-01039786 |
| Positive Pay adapter creation / bank change (MidFirst, Mizuho, Mitsui, Sandridge, Riley, PRM BK010) | New bank / adapter config | Per-client **Positive Pay adapter** build in **BK010** | #187887, #195913, #1569807, #1587309, #1633345(PRM BK010, 23-00928811), #1649090, #1657966, #1766026 |

**Fix recipe:** for **returned checks / misaligned ZIP-State**, the immediate unblock is a **data script** to correct the BA ZIP_CD (add the hyphen / align AP155 data), plus the **`WEB_BA_MASK_ZIP_CD`** mask config so future entries are correct (26-01083748); the screen-misalignment itself has a **long-term hotfix** (26-01089614 → 2025.04 hotfix). **Positive Pay** failures split into (a) the generic export defect/check-form (25-01039786) and (b) **per-client bank adapters** configured in **BK010** (the large #15xx/#16xx/#17xx feature series).

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1769179** | Bug / **Closed** | SGY — AP Reversal in Post Pending due to POSTWKFL in CE status ("Nullable object must have a value") | §4 | 25-01052627 |
| **#1766274** | Bug / **Closed** | CNR — POSTWKFL fails on setting ID value to -1 | §4 | — |
| **#1744756** | Bug / **Closed** | APH — ADPUPLOAD failing with Object-reference when coded to control account | §7 | — |
| **#1789707** | Bug / **Closed** | 2026.04 — ADPUPLOAD documents not displayed as attached after import | §7/§8 | — |
| **#1752121** | Bug / **Closed** | APH — Rev batch stuck Post Pending via QCFSIMPCYC when BU inactive | §4/§7 | — |
| **#1724602 / #1782515** | Bug / **Closed** | QCFSIMPCYC long runtimes (open-item on AR / no BA_NO match) | §7 (perf) | — |
| **#1565787 / #1682284 / #1683641 / #1715552** | Requirement / **Closed** | QCFSIMPCYC performance / step quick-wins | §7 | — |
| **#216506** | Requirement / Proposed | UPS CORE_REL — COA: 121 accounts missing JE code types | §6 | — |
| **#254192 / #258079 / #265135** | Bug / **Closed** | APH — Account JE Code Type Issues / validation | §6 | — |
| **#1458999** | Patch / **Completed** | JNE — Patch 7 on 2020.09 Upstream (GL025 tier-on-approve) | §4/§8 | 22-00663381 |
| **#1327661 / #1328329 / #1366499 / #1372282 / #1378765 / #1539899** | Feature / Requirement / **Closed** (one Pending Customer) | EQT — GL025 grid copy/paste (incl. span multiple BUs) | §8 | 22-00631158 |
| **#1534675** | Bug / **Closed** | EQT — Cost Center in GL025 missing in GL095 via copy/paste | §8/§10 | 22-00272577 |
| **#1655846** | Bug / **Closed** | AP055 & GL025 — inconsistent document behavior on copy | §8 | — |
| **#1788555** | Bug / **Closed** | 2026.04 — GL025 attachment not opening | §8 | — |
| **#91586** | Bug / **Closed** | TIPS data to AP import error running QCFSIMPCYC | §7 | 309515 |
| **#187887 / #195913 / #1569807 / #1587309 / #1633345 / #1649090 / #1657966 / #1766026** | Requirement / Feature | Per-client Positive Pay adapters (MAC/SND/JNE/PRM/MIT/REP) | §12 | 23-00928811 (PRM) |
| **#1743388** | Feature / Proposed | EQC — serial-number field length in FA010 & GL025 | §8 | — |

> Many actionable cases were dispositioned **operationally** (data/reset script or config) with no single product WI: voucher WF reset-to-Draft scripts (26-01084929, 25-01018721, 25-01049584), GL013 delete-account script (23-00885678), QRA/MT100 restage (24-00950935), BA ZIP fix + `WEB_BA_MASK_ZIP_CD` (26-01083748), SSRS/BRPTEMAIL config (23-00904243, 23-00915691). Confirm exact build/patch in **`Quorum.Upstream.QCFS.ReleaseNotes`** before stating fix availability.

---

## 14. Diagnostic SQL

> **Caveat:** QCFS runs on **SQL Server** (T-SQL); DBs are named `<CLIENT>_PRD##UPS_QCFS` (e.g. `SGY_PRD17UPS_QCFS`). Table/column names below are inferred from case repro text and code search — **verify against the client schema** (object names vary by version), and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Batches stuck in Post Pending / Could-Not-Post (§4). State column name varies; look for BATCH_STATUS / WKFL.
SELECT BATCH_ID, BATCH_CONTROL_TYPE, BATCH_STATUS, COMPANY_NO, ACCT_PERIOD, CREATE_DT
FROM   <BJE batch header table>     -- e.g. GL batch header
WHERE  BATCH_STATUS IN ('POST PENDING','COULD NOT POST','CNP')
ORDER BY CREATE_DT DESC;

-- B. Is POSTWKFL scheduled / currently processing / stuck? (§4)  -- backs the QP045 screen
SELECT PQID, PROCESS_ID, PROCESS_STATUS, START_DT, SERVER_NM
FROM   <process queue table>        -- the QP045 process queue
WHERE  PROCESS_ID = 'POSTWKFL'
ORDER BY START_DT DESC;
-- "Duplicate process found" => an older PQID is still PROCESSING and holding the lock (26-01107081):
--   cancel that PQID in QP045 and release the lock.

-- C. Accounts missing a JE Code Type (the #1 CNP / import error, §6)
SELECT ACCT_NO, ACCT_DESC, JE_CODE_TYPE_ID
FROM   <GL013 account master table>
WHERE  JE_CODE_TYPE_ID IS NULL
ORDER BY ACCT_NO;

-- D. Duplicate / orphaned AP voucher Workflow IDs (§5)
SELECT VOUCHER_NO, WFID, WF_STATUS, COUNT(*) OVER (PARTITION BY VOUCHER_NO) wf_ct
FROM   <voucher workflow table>
WHERE  VOUCHER_NO = '<VM...>' ;          -- >1 WFID for one voucher = the 25-01049584 pattern

-- E. Import staging rows for a file (doubled-amount / orphaned-staging, §7)
SELECT *
FROM   QSTAG_CORE_INTFC_EXTERNAL_IMP     -- ADPUPLOAD staging (AP/OI)
WHERE  SRC_DOC = '<file/src doc>';
-- and the QCFSIMPCYC interface staging:
SELECT * FROM <SEXTN_CORE_INTFC_*> WHERE <batch/file key> = '<...>';
-- Red flag: same SRC_DOC inserted by two ADPUPLOAD child jobs => duplicated amounts (25-01023102).

-- F. GL097/GL098 DW staleness (§10): when was JOURNALENTRYINQUIRY_DW last loaded?
SELECT MAX(<load/refresh dt column>) last_refresh, COUNT(*) rows
FROM   JOURNALENTRYINQUIRY_DW;

-- G. Trial Balance won't zero (§11/§15): confirm the soft close ran for the period.
SELECT COMPANY_NO, ACCT_YEAR, ACCT_PERIOD, SOFT_CLOSE_FLAG, FISCAL_CLOSE_FLAG
FROM   <SM006 period/close control table>
WHERE  ACCT_YEAR = <YYYY>;

-- H. Vendor/BA ZIP without a hyphen (returned-check pattern, §12)
SELECT BA_NO, BA_NAME, STATE_CD, ZIP_CD
FROM   <BA / vendor master table>
WHERE  ZIP_CD NOT LIKE '%-%' AND LEN(ZIP_CD) > 5;
```

---

## 15. Expected-Behavior / User-Education FAQ

~125 Training + ~82 Customer-Error GL cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "POSTWKFL stuck / no movement" on a **huge batch** | Not stuck — it's **validating tens of thousands of GL records** (one batch had 48,890; another 73,695). It completes the same day. Check record counts before escalating. | 25-01035751 |
| "POSTWKFL completing with errors / Duplicate process found" | A prior **POSTWKFL PQID is still Processing**. In **QP045** find it, Cancel, **Release the Lock** (don't kill a PQID that's genuinely still posting). | 26-01107081, 26-01093920 (user lacked permission), 25-01027244 |
| "JE / BJE stuck in Post Pending" (one-off) | Usually the user's batch needs the standard POSTWKFL cycle, or has a fixable validation issue — check **JE Code Type** and that POSTWKFL is running before assuming a bug. | 25-01054171, 26-01065520, 25-01017174, 25-01016851 |
| "Can't close / accidentally fiscally closed the year" (SM006) | The **fiscal-close flag is NOT a permanent lock**. SM006 → Links → **Close is re-runnable** for the correct year range; re-run it to reset the flags. | 26-01083974, 25-01000816, 25-01016067, 25-01058580 |
| "Trial Balance not zeroing / TB won't balance" | Run the **soft-close** for the month; review **FS mapping (GL232/GL016)**. Not a defect. | 25-01026344, 26-01080022, 26-01105296, 25-00995754, 26-01082738 |
| "Retained earnings roll-forward / year-end close steps" | Training — walk through SM006 close + RE roll-forward sequence. | 26-01083938, 25-01009982, 26-01070375 |
| "Can't delete a BJE batch / GL account" | The system is correctly blocking a **used / locked / non-Normal-control-type** record. Resolve by script (reset to Draft + Normal, or delete-if-unused) — not a bug. | 25-01005486, 25-01018984, 25-01019767, 25-01005486 |
| "Default decks not appearing in GL025 when entering cost center/property" | **Expected precedence**: GL takes the **AFE Deck tier first, then the JIB Flag**. If the AFE was set up with Tier 80, that tier wins. | 25-01045261 |
| "JE Code Type error / FK error entering a JE" | Account is missing a **JE Code Type or code-block definition** — configure it in GL013 (see §6). Newer builds validate this. | 25-01042275, 25-01039575, 25-01033391 |
| "GL014 / GL095 balances disagree" or "GL014 balance wrong" | Often a **Balance Refresh** is needed (GL014 → Balance Refresh), or gross-vs-cutback account mapping; reconcile before treating as a bug. | 22-00647320, 26-01105296, 25-00995754, 26-01080022 |
| "GL096 / GL097 query error after upgrade" | Permissions / query-screen setup post-upgrade; confirm access and DW refresh (§10) before assuming a defect. | 25-01007087 |
| "Auditor wants the GL095 window / TRN_GL definitions / how does IC offset work" | Documentation/education — explain the screen/table, not a defect. | 25-01034369, 24-00995463, 25-01008203, 25-00998343 |
| "Can we automate recurring JEs / prepaid amortization?" | Product/how-to — recurring batch (BJEA) functionality; training. | 26-01100683, 25-01033910 |

**Tell-tale it's user/expected:** a "stuck" POSTWKFL that is really a **huge batch validating** or a **duplicate-PQID lock** cleared in QP045; a year that was "accidentally closed" (SM006 close is re-runnable); a TB that won't zero until **soft close** runs; a delete the UI **correctly blocks** (used/locked/conversion batch); "default decks missing" that follow **AFE Tier precedence**; and JE-Code-Type/code-block errors that are **account config (§6)**. Verify POSTWKFL status, the account's JE Code Type, and the period-close state before treating a GL case as a defect.

---

## 16. Key Screens, Processes & Repos

### Screens
| Screen | Purpose |
|---|---|
| **GL013** | Chart of Accounts / account master (JE Code Type lives here) |
| **GL014 / GL016 / GL232 / GL282** | Balance sheet & balance refresh / FS line config / financial-statement config / financial reporting |
| **GL025** | Batch Journal Entry Creation (BJE) |
| **GL095 / GL096 / GL097 / GL098** | JE & document inquiry / cost-center query / GL data-warehouse inquiry (`*_DW`) |
| **AP055** | AP batch / voucher creation (sibling of GL025) |
| **AP155 / AP156 / AP157** | Vendor check / check-inquiry (ZIP/State) |
| **BK010** | Bank account setup → Positive Pay adapter |
| **SM006** | Global Company Maintenance / period & fiscal close |
| **QP043 / QP045 / QP073 / MT100** | QRA→QCFS export / process queue monitor / QCFSIMPCYC import cycle / journal-trans definitions |

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **POSTWKFL** (PSTWKFL) | Segregated post-after-workflow: Post Pending → Posted | Runs ~every 5 min; monitor/cancel in QP045; code `QSegregatedPostWkflBalanceUpdate.cs` |
| **ADPUPLOAD / APDUPLOAD** (incl. `ADPIMPALLV`) | Upload/stage OpenInvoice AP invoices | Stages `QSTAG_CORE_INTFC_EXTERNAL_IMP`; concurrent-child-job bug doubled amounts (25-01023102) |
| **QCFSIMPCYC** (QP073) | Import cycle interfacing AR/AP/JIB/QRA → QCFS batches | `SEXTN_CORE_INTFC_*` staging; needs valid MT100 journal/trans definitions; perf-heavy |
| **QP043** | Export GL & LOS data QRA → QCFS | MT100 must be Q-managed |
| **DATAPUBLISH** | Synchronize Accounts into GL013 | Needs Connection Mgmt entries `QLS`, `QLandDataHelper` (24-00989365) |

### Code locations (confirmed via ADO code/repo search)
| Symbol / area | Repo / path | Cluster |
|---|---|---|
| POSTWKFL workflow & posting | `Quorum.Upstream.QCFS.Web /Quorum.QCFS.ServiceCore/Workflow/QCFSWFServiceCore_InboxService.cs`, `/Quorum.QCFS.BS/Base/ThinBsWorkflow.cs`, `/ServerBusinessServiceRun.cs` | §4/§5 |
| POSTWKFL balance update (segregated) | `Quorum.Upstream.QCFS.Batch /Quorum.Upstream.QCFS.QCFSBatchCore/QSegregatedPostWkflBalanceUpdate.cs` | §4 |
| Process-step params (POSTWKFL config) | `<CLIENT>.Upstream.Metadata /STANDARD <ver>/QARCH_CTRL_PROCESS_STEP_PARAM.json`, `QARCH_CTRL_PROC_PROCSTEP.json` | §4 |
| GL025 grid / copy-paste / attachments | `Quorum.Upstream.QCFS.Web` + `Quorum.Upstream.QCFS.ClassicGUI` | §8 |
| Import staging / QCFSIMPCYC | `Quorum.Upstream.QCFS.Batch` + `Quorum.Upstream.QCFS.Database` (procs) | §7 |

### Repos (QuorumSoftware project; ~3,300 Upstream repos total)
- **`Quorum.Upstream.QCFS.*`** — core QCFS product: `.Web`, `.ClassicGUI`, `.Batch`, `.Application.MiddleTier`, `.API`, `.Database`, `.Events`, **`.ReleaseNotes`** (confirm fix builds here).
- **`Quorum.Upstream.QRA.*`** — revenue/JIB that feeds the GL via QP043/QCFSIMPCYC (out-of-balance and "not in QCFS" cases often root-cause here).
- **`Quorum.Upstream.Shared.*`** (`.Batch`, `.ClassicBatch`, `.Web`, `.ClassicGUI`) and `Quorum.Upstream.Application.QPEC` (the process-engine restarted in §4 fixes).
- **`<CLIENT>.Upstream.QCFS.Database` / `.Metadata` / `.Reports`** — per-client overrides (PRM, SGY, EQC, CNR, APH, MAC, GLE, NOG, …). **Always check the client repo/schema first** — JE-Code-Type setup, MT100, Positive-Pay adapters, and many "stuck batch" fixes are client-specific. (`GLE.Upstream.QCFS.*` and `MAC.Upstream.QCFS.Web` are notable clients with their own QCFS Web/Batch forks.)

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **posting/import defect** reproduces on correct data: intercompany AP-voucher reversal from Web (25-01043706, fixed 2022.04+), reversal-of-a-reclass null (25-01052627 / #1769179), POSTWKFL set-ID-to-`-1` (#1766274), ADPUPLOAD doubled amounts / Object-reference / timeout (25-01023102, #1744756, 25-01011282), ADPIMPALLV syntax (25-01007131), QCFSIMPCYC inactive-BU stuck (#1752121).
- A **GL025 grid** defect (delete-row, copy/paste-lock, multi-BU paste, attachment, tier-on-approve): 24-00943303, 25-01001961, 22-00631158, 22-00663381 (#1458999), #1788555/#1789707.
- A **query/report** defect: GL095 returns no data (22-00687036), GL096 query error (22-00597800), GL097 DW not refreshing (22-00871717), Positive Pay export (25-01039786), AP155 ZIP/State screen (26-01089614 → 2025.04 hotfix).
- Provide: the **PQID + process (POSTWKFL/QCFSIMPCYC/ADPUPLOAD) + exact error**, client + company/BU + accounting period, the BJE/voucher number, the account(s), and a repro. Confirm fix availability in **`Quorum.Upstream.QCFS.ReleaseNotes`** and the linked WI's target build.

**Handle as Configuration / Cloud Ops when:**
- **JE Code Type / code-block** missing on accounts (the dominant CNP/import config fix) — assign in GL013, often a new JE Code Type with all fields Optional (24-00995039, 23-00915415, 23-00903880, 23-00915272).
- **POSTWKFL not scheduled / on a dead server / stuck-lock** — enable schedule, repoint server, or cancel+release in QP045 (25-01006218, 24-00990635, 26-01107081); QPEC restart for transient hangs (22-00628247, 22-00628370).
- **Reports**: `SSRS_ENDPOINT_URL` global config (23-00904243, 23-00921346), `BRPTEMAIL`/Event Detector 227 (23-00915691), FS mapping GL232/GL016 (23-00913295).
- **GL013 Synchronize Accounts** connection config `QLS`/`QLandDataHelper` (24-00989365); **MT100** reload from DEV + restage (24-00950935).
- **Vendor ZIP / Positive Pay**: BA ZIP_CD fix + `WEB_BA_MASK_ZIP_CD` (26-01083748); per-client Positive Pay adapter in BK010.

**Handle as data fix (script) when:** orphaned/duplicate voucher WFIDs → reset-to-Draft (§5), unused-account or test-batch delete blocked by the UI (§9), QRA/staging orphans → restage (§7), AP155 ZIP/State misalignment (§12). Always verify-SELECT in a transaction; many of these auto-close on "no response after UAT" — confirm the state actually cleared.

**Handle as Training / Expected behavior (no fix):** see §15 — huge-batch POSTWKFL "slowness", duplicate-PQID locks, SM006 fiscal-close re-run, TB-won't-zero (soft close), UI-blocked deletes, AFE-Tier default-deck precedence, JE-Code-Type config errors, and audit/"how does it work" questions. Verify POSTWKFL status, the account's JE Code Type, and the period-close state before treating a GL case as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 847 closed QCFS "General Ledger (GL)" SF cases — 117 actionable (Software Defect 60 + Application Configuration 53 + ChangeConfig 4) mined for fix recipes, plus ~60 Training/Customer-Error cases for the FAQ. ADO work items #1769179, #1766274, #1744756, #1789707, #1752121, #1724602/#1782515, #1458999, #1327661/#1328329/#1366499/#1372282/#1378765/#1539899, #1534675, #1655846, #1788555, #216506, #254192/#258079/#265135, #91586, and the BK010 Positive-Pay adapter series.*
*Companion (when written): SKILL_QCFS_Accounts_Payable.md, SKILL_QCFS_Accounts_Receivable.md, SKILL_QCFS_Bank_Recon.md; upstream feed: QRA skills.*
