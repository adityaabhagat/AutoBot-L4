# SKILL — QLS Payments & Financial Processing

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Coverage-plan group:** #1 Payments & Financial Processing (1,773 cases all-history, 308 actionable)
> **Sources:** Salesforce all-history mining 2026-09-03 (8 result pages, ~165 distinct cases validated against `Product_list__c='My Quorum Land'`; 30 cases deep-sampled via Description/Resolution) + Azure DevOps org QuorumSoftware (18 work items cited, hotfix tags/branches verified)
> **Auto-Bot skill — built by Aditya Bhagat.** Every claim is anchored to an SF case number or ADO work item. DEV-tier caveat: client-PRD data-state claims stay INFERRED until verified live.

**Screens in scope:** Payment node (Agreement), Payment Balancing, Create Payment Detail (CPD), Manual Payment Setup, Create Manual Payment Detail, Pay/Drop Authorization, Payee Selection, Financial Detail(s), Lease Cost / Lease Cost Allocation, Function Navigator → Land Financial.
**Core tables (Oracle `lis` schema, confirmed in ADO bug bodies):** `DESG_PAYMENTS` (payees; `LAST_PROCESSED`, `PIP_TYPE_CATG` BIL/PAY), `STIPULATION_OBLIGATIONS` (payment header; `LAST_PAID`, `DUE_DATE`, `END_DATE`, `HOLD_PAY_CODE`, `STIP_KEY`), `FINANCIAL_TRANS_HISTORIES` (`FT_KEY`, `FT_STATUS` COM/CR), `EVENTS` / `ALL_EVENTS` (`EVNT_PROCESSED`/`EVENT_PROCESSED`, `ARRG_KEY`), `EVENTS_LOG`, `PARTICIPANT_ADDR_RLTN` (address usage types), `PAYMENT_TYPES` code table.
**Status vocabulary:** `HOLD_PAY_CODE` = PAY (ready/approved to pay), HLD (hold), LPP (Last Period Paid), PR (processing/generated), plus screen statuses Pending Title → Ready to Pay. Payee-level pay statuses include Pay, Suspense, Escheat.

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cluster | First check |
|---|---|---|
| "Next Payment / Last Paid date did not roll after check run" | A | Any payee on the payment in **Suspense** status? (ADO 1761017) |
| "Aborted Check Run Detected" prompt; payments vanished or dates rolled backwards | B | Did the user answer Yes/No at the CPD confirm step? `RESET_ABORTED_CHECK_RUN` registered SQL version |
| Payment stuck in **Pay** (or flipped to **Ready to Pay** bypassing eCal) after processing | C | Mixture of one-time-only / last-iteration + recurring payments in same CPD run (ADO 1749732, 1720955) |
| "Invalid participant address usage type for payee…" on Payment Balancing | D | Payee address rows in `PARTICIPANT_ADDR_RLTN`; config `PaymentBalance/ValidPayeeAddressUsages` |
| "Cost Center Allocation does not add up to 100%" on balancing | D | Cost-center allocation rows on the payment |
| New BA not searchable in Payee Selection; payor lost Intercompany/We Pay flag | E | BA address usage types + participant setup |
| Manual payment: field greyed out / codes not in picklist / wrong check number in reports | F | Manual Payment Setup config + conversion data |
| Financial Detail screen missing columns (SAP Check #), empty Status dropdown, missing history | G | Grid config script + hotfix level |
| Payment made in QLS but never hit SAP / Upstream / QCFS | H | Interface batch (AFIS/`Create_AE`) logs, GL cross reference, scheduled services |
| Lease Cost tables not populating / Lease Cost Allocation timeout | I | `QReaderWriterLockTimeoutException` on `QViewLeaseCostAllocation`; lease-cost population job |
| Duplicate payments or duplicate eCal events after saving payments | J | Were 2+ payments saved simultaneously? Fixed by hotfix (ADO 1691907) |

**Gate bias for this family:** Check-run/date-roll and status-flip symptoms are overwhelmingly **G3 (version — already fixed)**: the core defects were hotfixed across the 2022.04→2025.04 trains in 2025–2026. Balancing/payee errors are usually **G2 (config)** or **G4 (bad data)** on the BA's address usage rows. Rollback/reload requests are **G4** scripting work.

## 2. Decision Tree

```
Payment date/status wrong after a check run?
├─ Dates (Next Payment / Last Paid) did not roll forward
│  ├─ Payee in Suspense/Escheat on the payment → Cluster A (bug 1761017 — fixed, hotfixed 2022.04–2025.04)
│  ├─ User answered "No" (abort) at check confirm → Cluster B (bug 1736794 / 1358794)
│  └─ ALL_EVENTS rows missing next rolling due date → Cluster A data variant (1358794 comment)
├─ Dates rolled BACKWARDS (e.g. next pay date a year prior) → Cluster B (RESET_ABORTED_CHECK_RUN registered SQL; SF 25-01045824)
├─ Status wrong (stuck Pay / flipped Ready-to-Pay / Hold) → Cluster C
└─ Whole run vanished / must un-do a run → Cluster B rollback-script recipe

Error while BALANCING a payment?
├─ "Invalid participant address usage type…" → Cluster D1
├─ "Cost Center Allocation does not add up to 100%" → Cluster D2
└─ Balances anyway despite error → known gap (bug 1095708; older fix 2020.03 for QLS — SF 22-00564755)

Payment/payee cannot be SET UP? → Cluster E (payee selection, intercompany, payment types)
Manual payment oddity? → Cluster F
Financial Detail screen wrong/missing data? → Cluster G
Payment never reached SAP/Upstream/QCFS? → Cluster H
Lease Cost issue? → Cluster I
Duplicates? → Cluster J
```

---

## 3. Cluster A — Dates did not roll after check run (payee in Suspense)

**Signature.** After Create Payment Detail completes, Last Paid and Next Payment dates do not update on some payments; `EVENTS.EVNT_PROCESSED` not updated; payments re-appear in the next run (double-pay risk). Trigger: the payment has **at least one payee in Suspense (or Escheat) status**. (ADO 1761017 description: "Payments that have a Payee in Suspense will not update/process correctly after Create Payment Detail… Last Paid and Next Payment dates do not get updated, and the EVENTS.EVNT_PROCESSED date does not get updated.")

**Root cause (CONFIRMED).** Regression from an earlier fix that changed payments from "Hold" to "Pay" when the payee was in Suspense (noted in 1761017). CPD's date-roll step skips payments whose payee set includes a Suspense payee — even after the Suspense portion is processed via "Create Payment for Suspense".

**Fix recipe.**
1. **Version gate (G3):** Bug **1761017** is Closed with tags `2022.04/2023.04/2024.04/2024.10/2025.04 Hotfix Completed` — CONFIRMED fixed in all supported hotfix trains (deployed to CNX via "Patch 9 on 2022.04 Land", ref 1747379; hotfix requirement 1716064 "Land 2022.04 Hotfix – May 2025"). If the client is below the relevant hotfix, quote fixed-in and request the patch.
2. **Data repair (G4):** script Next Payment/Last Paid forward for the affected stips (that was the L4 resolution on SF 25-01048531: "Update Next Date and Last Paid Date accordingly"; long-term fix delivered as "2022.04 November 2025 OOC release" per SF 25-01051506).
3. Related single-client variant: SF 25-01050143 "Next Payment Date not rolling" — fixed by "2024.10 November 2025 HF".

**Anchors.** SF 25-01048531, 25-01051506, 25-01050143, 23-00925055 (2022.04-era variant: payments stuck in "Hold" after payment + SAP interface stuck PND; resolved by hotfix + scripting missing transactions), 26-01070909. ADO 1761017, 1761771 (MACL A1 2024.10 duplicate), 1634618 (CNXL 2022.04, SF 23-00925055), 1725644 (referenced predecessor bug).

**Caveat (INFERRED).** 1358794 history: dates may also fail to roll when the recurring payment's `ALL_EVENTS` rows are not set up correctly (next rolling due date missing) — check events before blaming the suspense bug.

## 4. Cluster B — Check-run abort / rollback (`RESET_ABORTED_CHECK_RUN`)

**Signature family.**
- CPD confirm step asks "are you happy with the checks?" — answering **"No"** (abort) rolls Next Payment date **backwards** to the previous due date, or clears Last Paid (ADO 1358794 EQT: "the due date of the payment will roll back in time to the previous due date… led [client] to process the same payment multiple times"; ADO 1736794).
- Re-opening CPD after a crash/tab-close shows **"Aborted Check Run Detected"**; answering **Yes** can wipe a *completed* prior run (SF 26-01070773: all payments from the second 2/2/26 run disappeared from Financial Details and the Payment tab).
- Abort clears `LAST_PAID` on payments from *previous successful* instances, not just the aborted run (ADO 1759038, Proposed as of mining date).

**Root cause (CONFIRMED, code-anchored).** The rollback logic lives in the **`RESET_ABORTED_CHECK_RUN` registered SQL** (Quorum.QLS.Metadata) invoked by `ResetAbortedCheckRun()` — `Quorum.QLS.ServiceCore\QQLSServiceCore_Financial.cs:5125-5167`, called from `HandleAbortedCheckRun()` in `Quorum.QLS.Web.Controllers\QQLSPaymentDetailWizardInterfaceControllerBase.cs:526-538` (per 1759038 analysis). The legacy SQL `update @@s_table s set last_paid = null … where hold_pay_code = 'PR'` is too broad — it matches previous AND current instances. `DESG_PAYMENTS.LAST_PROCESSED` is nulled by design on abort (1726981 comment: retaining it "would be too complicated… it just gets nulled out").

**Fix recipe.**
1. **Version gate:** 1736794 ("Next Payment date rolling backwards if user select 'No'") Closed, hotfixed 2023.04→2025.04 — fix removed the unnecessary Next-Payment-Date rollback from `RESET_ABORTED_CHECK_RUN`. 1358794 fixed via a client `RESET_ABORTED_CHECK_RUN` registered-SQL script + PRs to Quorum.QLS.Metadata.
2. **Config gate:** verify the client metadata layer actually HAS `RESET_ABORTED_CHECK_RUN` — ADO 206694: the APA layer was missing it, so cancelling CPD didn't roll back all payment records. Workaround from that bug: **null out `LAST_PROCESSED` on `DESG_PAYMENTS`** for the affected payees, then rerun CPD (records reappear).
3. **Rollback/reload scripting (standing L4 recipe):** full-run rollback and financial-detail reload are routine script requests — SF 26-01113049 ("Request to rollback checks has been completed"; filterable by company + transaction generated date), 26-01084653 ("script has been developed", references 26-01070909), 26-01070773 ("Deployed Script to manually reload missing financial details records and rolling the dates forward"). The rolled-back data survives in underlying tables (client's Check Address for Labels report still showed the checks — SF 26-01070773).
4. SF 25-01045824 ("Check run undo put next pay date 1 year prior") resolved by **"updated registered SQL"** — for one-off date corruption, fix the client's `RESET_ABORTED_CHECK_RUN` before scripting data.

**User guidance (customer-facing).** Never answer the "Aborted Check Run Detected" prompt without verifying the prior run: if the prior run truly completed (checks + check numbers exist in Financial Details), the safe answer depends on build level — on unpatched builds BOTH answers have burned clients (duplicates on "No"-path rerun 26-01070773 history; wiped run on "Yes"). Escalate for a DB check first on any build below the 2025.04 hotfix line.

**Anchors.** SF 26-01070773, 26-01113049, 26-01070909, 26-01084653, 25-01045824. ADO 1358794, 1736794, 206694, 1759038, 1726981.

## 5. Cluster C — Payment status wrong after processing (PAY/HLD/LPP, eCal bypass)

**C1 — Status stays in "Pay" after CPD (should flip to Hold/LPP).** ADO **1749732** (WMN): reproducible only when the CPD run mixes payments to be flipped to 'Hold' and 'Last Period Paid' — i.e. recurring payments with future End Date processed together with One-Time-Only or last-iteration recurring payments (`DUE_DATE = END_DATE`). Result: `HOLD_PAY_CODE` stays 'PAY' with no eCal recommendation on the next event. Closed, hotfixed 2022.04→2025.04. **Workaround (from bug history):** process One-Time-Only + last-iteration payments in a **separate CPD run** from ongoing recurring payments.

**C2 — Future payments flip to "Ready to Pay" bypassing eCalendar.** ADO **1720955** (EQC) = SF 25-01007015: after the check run, the next instance of recurring payments (delay rental, surface rental, shut-in, free gas, storage, minimum royalty, one-time) goes Pending Title → Ready to Pay without an eCal recommendation. Tagged `L4-Investigated; Regression`; Closed, hotfixed 2022.04→2025.04 (SF resolution: permanent fix "available… once they upgrade").

**C3 — EFT vs Check processing order changes final status.** ADO **1678487** (WMN): a payment with both EFT and Check payees should stay in PAY until all methods are processed, then flip (Hold/LPP); processing in a different sequence left it in PAY or cleared the check payee's Last Paid. Also flagged `PayeeCheckCriteria` configuration not working as expected. Closed, hotfixed (2022.04, 2024.10 incl. `#2024.10 Hotfix 1`).

**C4 — Two-payee payments processed one payee at a time.** ADO **1726981** (OXY) = SF 25-01006981: payee 1 Check processed, payee 2 corrected EFT→Check, reprocessing only payee 2 leaves the payment stuck on the same date. Closed, hotfixed 2023.04→2025.04.

**C5 — Aborted CPD marks the FUTURE event processed.** ADO **1772699** (APA) = SF 25-01060905: abort before a successful run populates `EVENT_PROCESSED` on the *next* unprocessed event too, so it never gets an eCal workflow. Closed; hotfix PRs (Quorum.QLS.Web #123256) to `hotfix/17.23.35` (2023.04), `hotfix/17.24.13` (2024.04), `hotfix/17.25.9` (2024.10), `hotfix/17.26.8` (2025.04) — CONFIRMED branch mapping.

**C6 — Open ($0 payee).** ADO **1868725** "COP - QLS - $0 Payee causes incorrect payment status after generating check" — state New at mining time; cite as known-unfixed when symptoms match.

**Triage rule.** For any status-flip symptom: (1) get exact build + hotfix level; (2) map to C1–C5; (3) if at/above the fixed hotfix, treat as new defect and reproduce per the bug's steps (all five have full repro steps in ADO).

## 6. Cluster D — Payment Balancing errors

**D1 — "Invalid participant address usage type for payee X. Verify the payee or update the address usage types for the payee."**
- **Root cause:** the payee BA's active address has no valid *payee* usage type. Valid usages are configured in global config **`PaymentBalance / ValidPayeeAddressUsages`** (billing party analog: **`ValidBillingAddressUsages`**) — confirmed in ADO 280186 repro steps.
- **Fix (G4/G2):** add the payee usage row to the participant's address — SF 22-00548575 resolution verbatim: **"Added PRTP to Participant_ADDR_RLTN"**. Or correct the config lists if the client's usage taxonomy changed.
- **Display bug variant:** error prints `System.Collections.Generic.List`1[System.String]` instead of the payee id — ADO 212277 (code typo in Payee Validation), Closed. Seen at SF 23-00892660.
- **"Balances successfully WITH the error":** QLS variant fixed in build 2020.03 (SF 22-00564755 resolution); myQuorum "Invoice without Payment" variant still Proposed (ADO 1095708 — validation is warn-only). State this as expected-but-ugly on unfixed builds.
- **First-click failure with Auto Calculate:** ADO 280186 — the payment-balance DB package (e.g. `QPCK_PMT_LOC_RATE_CAN`, which inserts `DESG_PAYMENTS` rows with `PIP_TYPE_CATG='BIL'`) ran *after* validations, so the first Balance click errored and the second succeeded. Fixed 2020.09 Hotfix 6.

**D2 — "Cost Center Allocation does not add up to 100% / Payment cannot balance because Cost Center…"** — SF 22-00580212, 22-00646979. Bad-data gate: fix the payment's cost-center allocation rows to sum 100%. (Cost-center add errors in the Organization node: SF 25-01022371, defect, closed-no-response.)

**D3 — Balancing blocked on eCal-approved payments after editing amount** — SF 26-01063914, 24-00969076 (both closed No Action Taken/Deferred): editing payment amount on an already-approved eCal payment triggers balancing errors. Treat as expected-workflow friction; re-run recommendation/approval rather than fighting the balance step.

**D4 — Environment/packaging variants (for completeness):** balancing failures after upgrades were repeatedly root-caused to missing DB packaging — SF 22-00548575/22-00580212 root cause picklist "Packaging Issue - Database Scripts"; timeouts (SF 22-00621779) and cost-center validation failure (SF 22-00646979) were HW/env changes. Check invalid DB objects after any upgrade before deep-diving.

## 7. Cluster E — Payee / BA / payment setup (config-heavy)

- **New BA not found in Payee Selection** (searching All Participants / All Business Associates) though visible under Administrative → Business Associates — SF 25-01012068 (BA imported via API from Oracle ERP). Cause pattern: BA lacks the payee address usage/participant linkage that Payee Selection filters on (same mechanics as D1). Companion cases: 24-00939472 "Rental Payee Address has been Removed from many Business Partners" (Software Defect), 24-00948801 "BPs Missing Rental Payee Usage", 26-01079460 (BA unable to populate in Payee Selection — integration).
- **Intercompany payor lost "We Pay"** — SF 26-01064649: BA stopped being treated as Intercompany; We Pay checkbox unflagged, Billing tab flips to Pay Partner; short-term fix was a deployed data script. Check the BA's intercompany designation before scripting.
- **Payee Destination missing → payment processing error** — SF 25-01023281: processing fails when payee `Destination` is blank; fixed by data script adding the missing destination on LPP payments. Related defect: 24-00965240 "Payment Payee Destination field Needs to be Required". Code-table note: 22-00519598 — Payee Destination values appear for all subject/agreement types even when restricted (defect, Code Table Navigator).
- **Payment type not available** — SF 25-01050535 (payment type missing from Manual Payment screen for one company), 26-01094902 (new Extension payment type only applies to existing agreements), 26-01100265 (enable Rental Payments for LTS Subject type). All config: `PAYMENT_TYPES` code table + company/subject-type restrictions.
- **Payment frequency** — new frequencies (e.g. "Every 6 Years") are code/decode config — SF 26-01102565.
- **Configs that gate method behavior:** `PayeeCheckCriteria` (which pay-method codes count as checks — 1678487, and 1772699 repro uses it), `PayeeEFTCriteria` (coverage-plan vocab). After changing them, clear cache (1772699 repro step).

## 8. Cluster F — Manual payments & conversion

- **Check Number field greyed out** on Manual Payment Setup — SF 24-00953773 (Software Defect, closed 2024-11).
- **Cannot allocate agreement via Notes section** on Manual Payment Setup (UNCON) — SF 25-01030512 (Software Defect).
- **Payee picklist not joining on Country** — SF 22-00574382 (defect, 2021): manual-payment payee dropdown mixed countries.
- **Converted manual payments referencing nonexistent codes** — SF 25-01063130 (config; conversion data used codes missing from code tables) and 26-01085763 (converted CONV payments missing notes). Conversion QA: validate manual-payment codes against code tables post-load.
- **Check Report showing larger amount than payment** — SF 26-01092352 (config, Create Manual Payment Detail).
- **QLAD manual-payment allocations duplicating check number in XTA** — SF 25-01049664 (config, QLA Payments).
- **Net acreage not displayed in Additional Info tab** of Manual Payment Setup — SF 25-01030343 (config). **Reports not downloadable from Create Manual Payment Detail** — SF 25-01030524 (config).
- **"Object Reference Not Set to an Instance of an Object" balancing manual payments** during upgrade testing — SF 24-00955204 (closed-deferred; upgrade-era, retest on current build).

## 9. Cluster G — Financial Detail screen & grids

- **SAP Check # / financial history missing from Financial Detail and Payment node** — SF 25-01031282 (Software Defect). Resolution verbatim: "Hotfix fixed the SAP fields showing on the screen, but we also needed to run the attached script to enable the SAP columns in the Payment and Financial Detail grids." → Two-part fix: hotfix + grid-config script. Same-era: 23-00929221 "PAYMENT FINANCIAL DETAIL SS MISSING FIELD" (config).
- **Status dropdown empty** on Financial Details — SF 26-01109443 (Software Defect, closed 2026-08).
- **Filter criteria wrong** — SF 24-00963163 (DEO hotfix for 24-00950465, Financial Details Filter Criteria; config).
- **SAP check # editable when it should be locked** — SF 23-00923352 (config).
- **Date Cleared pushed incorrectly from QCFS** — SF 26-01092883 (Software Defect; QCFS→QLS financial detail sync).
- **Status update ability on Financial Details screen** — SF 23-00933542 (config; upgrade project).
- **PII masking on Financial Details** for BAs — SF 22-00651607 (defect, 2022).
- **Payments disappear if Currency nulled** on the Payment screen — SF 23-00929889 (defect; payment invisible in UI, data still in DB — restore currency value via script, don't recreate).

## 10. Cluster H — Downstream export: SAP / Upstream (AFIS) / QCFS

- **Check run not exporting / stuck** — SF 25-01044731 resolution verbatim: **"Missing GL cross reference caused Create_AE to fail. Process error message log does not provide helpful details from the afis log."** → When export fails silently, go to the AFIS log, not the process error log; verify GL cross-reference completeness for every account in the run.
- **QLS payments not batching to Upstream** — SF 26-01100202 (upgrade; scheduled services were enabled but export still config-gated — Application Configuration). Batch names from coverage plan: `AFISCRTAE` (QLS→Upstream AP financial export), `UPSFINEXP`, `SAPINTJE` (JE export), `DATAPUBLISH`, Positive Pay, Bank Submission.
- **Payment did not hit SAP** — SF 26-01087287 (config); 2022.04-era mass variant SF 23-00925055 (SAP interface stuck PND with errors). Also SF 22-00830687-era Random balancing + SAP issues.
- **Accounting date wrong on integrated payments** — SF 25-01014046: Land payments reached Upstream with random accounting dates; fix: "updated interface to sent over the first of the month always for the accounting month".
- **QCFS import of land payments erroring** — SF 26-01093976 (resolution: "account setup" — G/L account config in QCFS side).
- **Rolled-back check run's JE still crossed to Upstream** — SF 25-01007403 (companion to rollback 25-01005948): after any QLS check-run rollback, verify/reverse the exported JE downstream.
- **EFT payments: blank Check Form Report + no internal Quorum check number** — SF 24-00948083 (config). Resolution verbatim: "The adjustment can be enabled from the front end, in configuration setting by changing the Value to 1. Once this is modified the check report will print the EFT information." (EFT-on-check-report config key; value 0/1.) Related: 25-01011952 Check Numbering for QLS payments (config), 25-01044537 Check Number Field sequence (config).
- **Positive Pay / Bank Submission file errors** — SF 26-01103517 (config), 25-01006358 (QCloud env, Positive Pay file needed correction; Project Debt).

## 11. Cluster I — Lease Cost

- **Lease cost tables not populating for all QLS payments** — SF 25-01005853 (Software Defect; customer cancelled before final fix — treat as known symptom, reproduce before citing fixed).
- **Lease Cost Allocation screen lock timeout** — SF 26-01095155, error verbatim: `Quorum.QFC.Core.Interface.QReaderWriterLockTimeoutException: Unable to obtain ReadLock(ReadLock): QUIController.uic.<id>.QViewLeaseCostAllocation in the alloted time 30000ms` (stack through `QMvcBaseScreenController.SetupViewModel`). Older sibling: SF 23-00890349 "Lease Cost timeout" (defect). Pattern: a stuck UI-controller lock on the allocation view — app-pool recycle clears it; recurring cases → performance defect on the allocation query.
- **Lease Cost Template Import fails after upgrade** — SF 26-01063316 (config).
- **Lease Costs duplicating** — SF 24-00983372 (config).
- **Lease Cost reporting** — SF 25-01038485 (config).

## 12. Cluster J — Duplicate payments / duplicate eCal events (payments side)

- **Saving 2+ payments at once duplicates them (and their eCal workflows)** — ADO **1691907** (SGY, GEC, DMB): "Payment with One Time Only got Duplicated where Monthly one did not." Closed, `2022.04/2023.04/2024.04 Hotfix Completed`. SF twin: 25-01004742 "Duplicate payments" — resolution "deploying the Feb 2025 hotfix."
- **Duplicate eCal EVENTS with wrong dates created at payment creation** — ADO **1686931** (GEC & DMB), Closed + hotfixed. Diagnostic SQL in the bug (see §14). `ALL_EVENT_ROLL` should sync event dates when QLS payment dates change (bug history note).
- **Duplicate workflows on payment change** — SF 24-00983707 "Payments Duplicating workflows created", 25-00997334 "Duplicate Events when Multiple Payment Dates are Changed" (both Software Defect, Closed). Same family; route deeper eCal-workflow behavior to the eCalendar & Obligations skill.

---

## 13. Known ADO items (Payments & Financial)

| ADO | Title (short) | State | Fixed-in evidence |
|---|---|---|---|
| 1761017 | Dates did not roll after check run (payee in Suspense) | Closed | Tags: 2022.04→2025.04 Hotfix Completed (CONFIRMED) |
| 1761771 | MACL A1 2024.10 — payments with Suspense don't process | Closed | dup of 1761017 family |
| 1634618 | CNXL 2022.04 — payment dates not rolling (SF 23-00925055) | Closed | hotfix (per SF resolution) |
| 1736794 | Next Payment date rolls backwards on 'No' at check submission | Closed | 2023.04→2025.04 Hotfix Completed; fix removed rollback logic in RESET_ABORTED_CHECK_RUN |
| 1358794 | EQT — CPD rolling due dates backwards | Closed | client RESET_ABORTED_CHECK_RUN registered-SQL script + Quorum.QLS.Metadata PRs |
| 206694 | CPD not rolling back all records on cancel (APA missing RESET_ABORTED_CHECK_RUN) | Closed | metadata layer fix; workaround: null DESG_PAYMENTS.LAST_PROCESSED |
| 1759038 | Abort clears LAST_PAID of previous instances | Proposed | code anchors QQLSServiceCore_Financial.cs:5125-5167; QQLSPaymentDetailWizardInterfaceControllerBase.cs:526-538 |
| 1726981 | OXY — two payees, one processed at a time (SF 25-01006981) | Closed | 2023.04→2025.04 Hotfix Completed |
| 1749732 | WMN — status remains Pay when approved in eCal | Closed | 2022.04→2025.04 Hotfix Completed |
| 1720955 | EQC — recurring flips Ready-to-Pay bypassing eCal (SF 25-01007015) | Closed | 2022.04→2025.04 Hotfix Completed; tagged Regression |
| 1772699 | APA — future event marked Processed after CPD abort (SF 25-01060905) | Closed | PRs #123531-123534 → hotfix/17.23.35, 17.24.13, 17.25.9, 17.26.8 (CONFIRMED) |
| 1678487 | WMN — EFT+Check status depends on processing sequence | Closed | 2022.04 + 2024.10 Hotfix Completed |
| 1868725 | COP — $0 payee → incorrect status after generating check | New | not fixed at mining date |
| 212277 | Payee Validation error message typo (List\`1[System.String]) | Closed | fixed |
| 280186 | Payment Balance DB package must run before validations | Closed | 2020.09 Hotfix 6 |
| 1095708 | Invoice balances successfully with validation error | Proposed | warn-only validation, unfixed |
| 1691907 | eCal payments duplicated saving multiple at once (SF 25-01004742) | Closed | 2022.04→2024.04 Hotfix Completed |
| 1686931 | Duplicate eCal events with wrong dates | Closed | 2022.04→2024.04 Hotfix Completed |

Area paths seen: `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land`, `…\Professional Services\Land`, `…\Customer Service`. Repos: Quorum.QLS.Web, Quorum.QLS.ServiceCore, Quorum.QLS.Metadata, Quorum.QLS.ClassicGUI (`Quorum.QLS.Function/PaymentDetail/QViewCreatePaymentDetail.cs`), Quorum.QLS.Tests.

## 14. Diagnostic SQL (Oracle, `lis` schema — real queries from cases/bugs)

From ADO 1686931 (duplicate events investigation — verbatim):
```sql
select * from lis.all_agreements where agmt_num = 'L036201000';
select * from lis.events where arrg_key in (select arrg_key from lis.all_agreements where agmt_num = 'L036201000');
select * from lis.events_log order by updt_date desc;
```

Legacy rollback SQL at the heart of Cluster B (verbatim from `RESET_ABORTED_CHECK_RUN`, quoted in ADO 1759038 — reference only, do NOT run):
```sql
update @@s_table s
   set last_paid = null,
       hold_pay_code = (select DISTINCT orig_pmt_holdpaycode
                          from last_payment_ft_keys l
                         where l.stip_key = s.stip_key)
 where hold_pay_code = 'PR';
```

Verification queries for date-roll/abort triage (built strictly from tables/columns confirmed in 1761017/1759038/206694 — label `NOT YET RUN` until executed on the client env):
```sql
-- Payments whose payee set includes a Suspense payee (Cluster A candidates)
select s.stip_key, s.due_date, s.end_date, s.last_paid, s.hold_pay_code
  from lis.stipulation_obligations s
 where s.stip_key in (select d.stip_key from lis.desg_payments d
                       where d.pay_status_code = 'SUSPENSE');  -- exact code value: verify in client code tables

-- Financial transactions for a stip (was the run generated/completed?)
select ft_key, ft_status, gen_date
  from lis.financial_trans_histories
 where stip_key = :stip_key
 order by gen_date desc;

-- Cluster C5 signature: next event already flagged processed
select evnt_key, evnt_processed
  from lis.events
  where arrg_key = :arrg_key
 order by evnt_key;

-- Cluster B workaround precheck (206694): payees CPD refuses to re-pull
select stip_key, last_processed from lis.desg_payments where stip_key = :stip_key;
```
(Log tables referenced in 1761017 audit: stipulation-obligations log, desg-payments log, `lis.events_log` — use them to prove which patch/date the roll behavior changed.)

## 15. Expected-Behavior FAQ

- **"Last Paid goes blank when we abort a check run — bug?"** Partially expected: on abort, `DESG_PAYMENTS.LAST_PROCESSED` is intentionally nulled (1726981 dev comment). But clearing `LAST_PAID` on *previously completed* instances is defect 1759038 (open at mining date).
- **"Payment balanced even though it showed the address-usage error."** Known warn-only behavior on unfixed builds (1095708 Proposed; QLS-side fixed 2020.03 per SF 22-00564755).
- **"We Pay with Billing Party = $0 gave no warning."** Closed as Customer Error (SF 22-00633731) — no built-in warning; note $0-payee defect 1868725 is a separate, real status bug.
- **"Can EFT payments print on the Check Form Report?"** Yes — config toggle (value 0→1), SF 24-00948083.
- **"Agreement Stage column in Payment Balancing screen?"** Configurable grid column — SF 23-00906375 (Application Configuration).
- **"Why is a processed invoice not flipping to the next date on Payment screen/eCal?"** Defect family — SF 25-01014511 (granted surface invoices), 24-00937785 (Invoice Without Payment); same date-roll machinery as Cluster A/C.
- **"Payment Balancing button under Function Navigator does nothing."** SF 26-01084202 (closed No Action Taken) — check user's Land Financial menu security before escalating.

## 16. Escalation

1. **Before escalating any date-roll/status case:** capture build + hotfix level, one example `AGMT_NUM`/`STIP_KEY`, and whether a payee is in Suspense — this alone resolves the majority against the §13 table (G3).
2. **Rollback/reload scripts** (Cluster B) are standard L4 deliverables: get the company number + transaction generated date (the filter used in SF 26-01113049), and always check downstream JEs (SF 25-01007403) before running.
3. **New defect path:** file to `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` (or project `Quorum` path `Quorum\North America\Upstream\Land RnD` for current PI work), link the SF case, include repro from a `<CLIENT3>L_HD_DEV17_QLS` env, and check hotfix tag conventions (`YYYY.MM Hotfix`, branches `hotfix/17.2x.y`).
4. **Batch/export failures** (Cluster H): pull the AFIS log (not just the process error log — SF 25-01044731), then route to the Integration & Financial Export skill if the failure is downstream of QLS.
5. PII: customer names/contacts redacted in this skill; never copy contact info from case bodies into reports.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
