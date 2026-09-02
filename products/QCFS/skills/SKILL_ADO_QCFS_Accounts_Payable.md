# SKILL: QCFS Accounts Payable — ADO Defect / Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** Upstream QCFS (Financial Accounting) — Accounts Payable
**Source:** Azure DevOps bugs under area path `QuorumSoftware\Engineering\Financials` (Bug, State Closed/Resolved). NOT a Salesforce mining; this is the engineering-side defect/fix view. Cross-reference with the SF-case skills for customer symptoms.
**Use When:** triaging an AP/voucher/check-run/POSTWKFL/1099/vendor (BA005) issue and you need to know (a) is this a known defect, (b) what was the root cause, (c) which build/release the fix landed in, and (d) is it config/data vs code. Pair with the linked SF case if the customer reported it.

> **Evidence base:** WIQL matched **548** Financials bugs on AP title terms (voucher, payable, AP0/AP1/AP, POSTWKFL, fast track, invoice, bulk submit, BA005, vendor). After dropping cross-area "invoice" noise (QRA/QDO/QLS billing), **395** are clearly QCFS-AP. **~50 deep-read** (description + repro + dev comments + linked PR/commit). Cluster sizes (of the 395): Voucher Create/Approval screen **156**, 1099/AP170/QP073 **50**, AP061 check-run/print **31**, Bulk Voucher Handling **31**, POSTWKFL/post-batch **26**, BA005/Vendor master **23**, Reclass/Reversal **20**, V2UI/Kendo cosmetic **20**, AP150/ACH/EFT export **18**, IC-offset/inter-company **6**, Fast Track **4**, other **10**.

> **Release-mapping caveat:** ADO `Microsoft.VSTS.Build.IntegrationBuild` is **empty** on every AP bug, so "fixed-in-build" is inferred from (a) the **release prefix in the title** (`2023.04`, `2024.10`, `2025.04`, `2026.04`) and (b) the **iteration path** (`24.xx`→2024 cycle, `25.xx`→2025.04, `26.0x`→2026.04; `Sprint NN` / `Product Development` / `QuorumSoftware` = pre-2020 legacy with no clean release tag). Where only an iteration is known, the release is stated as "≈". Confirm the exact build in `Quorum.Upstream.QCFS.ReleaseNotes` / the linked PR before quoting a build to a client.

---

## TABLE OF CONTENTS
1. [Quick Triage](#1-quick-triage)
2. [Decision Tree](#2-decision-tree)
3. [Cluster A — POSTWKFL / post-batch failures (deadlock, stuck, timeout)](#3-cluster-a--postwkfl--post-batch-failures)
4. [Cluster B — Voucher Create/Approval screen (web concurrency, status, coding)](#4-cluster-b--voucher-createapproval-screen)
5. [Cluster C — Bulk Voucher Handling](#5-cluster-c--bulk-voucher-handling)
6. [Cluster D — Reclass / Reversal](#6-cluster-d--reclass--reversal)
7. [Cluster E — AP061 check-run / check-print / AP155-158-159](#7-cluster-e--ap061-check-run--check-print)
8. [Cluster F — AP150 / ACH / EFT export](#8-cluster-f--ap150--ach--eft-export)
9. [Cluster G — BA005 / Vendor master](#9-cluster-g--ba005--vendor-master)
10. [Cluster H — 1099 / AP170 / AP151 / QP073](#10-cluster-h--1099--ap170--ap151--qp073)
11. [Cluster I — IC offset & inter-company posting](#11-cluster-i--ic-offset--inter-company-posting)
12. [Cluster J — Fast Track workflow](#12-cluster-j--fast-track-workflow)
13. [Fix-Version Matrix](#13-fix-version-matrix)
14. [Diagnostic pointers (SQL & code)](#14-diagnostic-pointers)
15. [Escalation guidance](#15-escalation-guidance)

---

## 1. Quick Triage

| Symptom (customer / QA report) | Likely cluster | First check |
|---|---|---|
| POSTWKFL/PSTWKSPLT fails with **"deadlock victim"** / "Execution Timeout Expired" / account balances not updated | A | Is a **fiscal close / balance-refresh** job running concurrently? §3 (#1739552 lock serialization fix, ≈2025.04) |
| Batch stuck in **"Post In Progress"** / "Post Pending" forever | A | POSTWKFL/PSTWKSPLT/Fast-Track died mid-run; §3 (#1669576, #1747642) — script the batch back, confirm 2025.04 self-heal |
| POSTWKFL fails when **another batch (ARCCOREINT, fiscal close)** is running | A | Working as designed — lock relationship added (#1667696); §3 |
| POSTWKFL fails posting a **check run** (bulk-insert / ID error) | A | §3 #1708039 (JECUSTOMCODEBLOCKUPSTREAM identity change, fixed ≈2025.04) |
| Reversal voucher **"Could not Post" — "no accounts payable configurations set up for this BU"** | A / I | **Zero check-run definition missing** in AP config for that BU (data, not code) — §3/§11 (#209184, #70249) |
| Web voucher **double-submitted / deletable while in workflow / status mismatch** in 2 tabs | B | Concurrency check; §4 (#1722429/#1741065 resubmit, #1705837 delete-in-WFIP) |
| AP voucher screen: **Validate/Delete/Reclass buttons wrongly enabled** for posted/paid status | B/D | Control-state bug; §4 (#1651807) §6 (#1623972) |
| Voucher screen **auto-populates wrong Property / wipes AFE coding** | B/D | BU-mismatch auto-lookup; §4 (#1666027) §6 (#1616173) |
| **Bulk Voucher Handling** screen: count mismatch, reverse-to-draft no-op, buttons missing | C | §5 |
| **Check prints blank PDF** / wrong amount / duplicate vendor combined | E | SSRS check-form setup or report SQL; §7 (#1449309, #264880, #107894) |
| AP155/AP158 wrong company or **state in zip column** | E | §7 (#1795190 CHECKRUNJOURNAL SQL, ≈2026.04; #1631300 ID vs USERKEY = not a bug) |
| AP150 **ACH/EFT export throws exception / "service unavailable"** | F | §8 — re-export validation (#1684117) or **SSRS down** (#1725807) |
| **BA005 vendor edits don't save / clear out / PUBBA fails** | G | §9 — PUBBA metadata priority, address-override save, config-level mismatch |
| **1099 box wrong / AP170 columns missing / QP073 1099 override errors** | H | §10 — most are env/QFC-upgrade or test-misunderstanding; real ones = 1099-on-single-check |
| **Inter-company voucher won't post** when Journal Def uses Account Xref | I | §11 (#101971, fixed 2019.02) |
| Fast Track **skips final approval / errors when not locked to self** | J | §12 (#1443159 `>` vs `>=`; #1450881/#1444650 lock+security) |

---

## 2. Decision Tree

```
QCFS AP issue
│
├─ A batch process failed / stuck?  (POSTWKFL, PSTWKSPLT, PUBBA, ACH_EMAIL, QP073)
│   ├─ "deadlock victim" / timeout / balances not updated      → §3 Cluster A (concurrency w/ close/refresh; #1739552)
│   ├─ stuck "Post In Progress" / "Post Pending"               → §3 (script back; #1669576/#1747642)
│   ├─ fails posting a CHECK RUN (bulk insert / ID)            → §3 (#1708039)
│   ├─ reversal "no AP configurations for this BU"             → DATA: zero check-run def missing (#209184/#70249)
│   └─ fails because another batch is running                  → BY DESIGN lock (#1667696/#1675655)
│
├─ Voucher screen behaving wrong (not a batch crash)?
│   ├─ concurrency: double submit / delete in workflow / 2-tab → §4 (#1722429, #1705837)
│   ├─ control-state: button enabled/disabled wrong by status  → §4 (#1651807)
│   ├─ coding auto-populate / AFE wipe / property from wrong BU → §4/§6 (#1666027, #1616173)
│   └─ Bulk Voucher Handling specifics                         → §5
│
├─ Reclass or Reversal specific?                               → §6 (#1623972, #1609157 DOI, #1616173)
│
├─ Check run / check print / outstanding checks (AP061/155/158/159/171)?
│   ├─ blank PDF / wrong amount / duplicate-vendor combine      → §7 (SSRS form + report SQL)
│   └─ wrong company / state-zip                                → §7 (#1795190 code; #1631300 not-a-bug)
│
├─ ACH/EFT export (AP150)?                                      → §8 (re-export validation; SSRS up?)
├─ Vendor master (BA005) save/clear/PUBBA?                      → §9
├─ 1099 (AP170/AP151/AP043/QP073)?                              → §10 (mostly env/QFC or expected)
├─ Inter-company posting?                                       → §11
└─ Fast Track workflow?                                         → §12
```

---

## 3. Cluster A — POSTWKFL / post-batch failures
*26 bugs. The highest-value operational cluster. POSTWKFL (QP073) posts approved AP vouchers/check-runs; PSTWKSPLT is the split variant; both update GL account balances.*

### A1 — POSTWKFL deadlock vs concurrent fiscal-close / balance-refresh (the marquee defect)
- **Symptom:** POSTWKFL errors and account balances are not updated. Trace shows `Transaction (Process ID NNN) was deadlocked on lock|communication buffer|generic waitable object resources … chosen as the deadlock victim. Rerun the transaction.`
- **Root cause:** the **POST job and a fiscal close / balance-refresh job run at the same time** on the same BU/year and deadlock on the balance tables. Seen by **CEN (2023.04)** and **MAC (2024.10)**.
- **Fix:** **#1739552** — put **locks around the close/refresh jobs and the post jobs**, and make the account-balance refreshes that happen during post **run sequentially in a child job**. Merged to **2025.04**. (Reproduction attempt #1743547 could not consistently repro, so the fix is preventative-locking, not a repro-driven patch; related #1745586, #1749964.) Linked PRs 113962/113966. Note: also exposed missing metadata `QARCH_CTRL_PROCESS.PROCESS_ID='BSVPOST'` for the new child job — verify that row exists.
- **Bug IDs:** #1739552 (fix, Closed), #1743547 (repro attempt, Rejected). **Fixed-in: ≈2025.04.**

### A2 — Batch stuck in "Post In Progress" / "Post Pending"
- **Symptom:** a batch sits in **Post In Progress** (Fast Track / POSTWKFL splitting) or **Post Pending** and never moves to Posted or Could-Not-Post.
- **Root cause:** the POSTWKFL/PSTWKSPLT job died mid-run leaving the interim status; normal operation should land on Posted or Could Not Post.
- **Fix / workaround:** **#1669576** self-heal/guard so a failed job doesn't strand the batch (Closed as Duplicate of #1660263, iteration 25.17 ≈2025.04). Operationally: **script the batch status back** to a re-runnable state, then re-run POSTWKFL. **TPW 25-01035193 / #1747642** = batch checks stuck in Post Pending in AP061 (same family).
- **Bug IDs:** #1669576, #1747642 (TPW), #1660263. **Fixed-in: ≈2025.04** (guard); stuck batches before that need a script.

### A3 — POSTWKFL fails posting a check-run (SQL bulk-insert / identity)
- **Symptom:** POSTWKFL fails to post a check-run batch after the SQL-bulk-insert refactor.
- **Root cause:** the change that removed the identity from `JECUSTOMCODEBLOCKUPSTREAM` and relied on our own sequence allocation broke `CustomCodeBlockData.cs CopyValuesTo` — it overrode the expected `-1/-2/-3` add-row handling for the `ID` field. Fix: ignore the `ID` field when `< 0`.
- **Code:** `\Quorum.QCFS.BL\CustomCodeBlockData.cs` → `CopyValuesTo`. PR 105031.
- **Bug ID:** #1708039 (Closed). **Fixed-in: ≈2025.04** (iter 25.02).

### A4 — POSTWKFL fails when another batch is running (BY DESIGN)
- **Symptom:** POSTWKFL/PSTWKSPLT **directly fails** (instead of waiting in SXL "could not acquire lock") while **ARCCOREINT** is running.
- **Resolution:** **By design** — #1667696 intentionally added the lock relationship so they cannot run concurrently. #1675655 was **Rejected** (the "direct fail vs go-to-SXL" nuance was not a defect).
- **Bug IDs:** #1675655 (Rejected), #1667696 (the lock requirement).

### A5 — Reversal voucher "Could Not Post" — "no accounts payable configurations set up for this BU" (DATA)
- **Symptom:** a reversal (negative) voucher final-approves, POSTWKFL runs, but the voucher is left **Could Not Post**; message "There are no accounts payable configurations set up for this BU."
- **Root cause:** **missing zero-run / zero-check-run definition** in the AP config for that BU — required to post a negative voucher. **Data/config, not code.**
- **Code ref for the error:** `VoucherWorkflow.cs` (~line 649). Improved error message shipped (`Quorum.Upstream.QCFS.Web` 17.20.0).
- **Bug IDs:** #209184 (Closed — added zero-run def + better message), #70249 (Rejected — "data related, no zero check run def"). Also #1446832 — POSTWKFL completed with `@ba_no` parameter error on AP voucher reversal.

### A6 — Legacy POSTWKFL items (pre-2020, no clean release tag)
- **#74065 / #74064:** POSTWKFL using **Fiscal Period 0 instead of 1** — code fix (PR 2697, v16 TFS 70606).
- **#72944:** POSTWKFL timeout **resolved with a DB index** (perf; PRs 2593/2596).
- **#106219:** QCFS scheduled processes (POSTWKFL, QCFSIMPCYC) stopped in UAT — **fixed by adding the UPS Impersonation group / group 9001 security** (env/config, Rejected as a product bug).
- **#111224 (CNR):** "Object reference not set" posting payment applications — code fix (PR 10778).
- **#1635436:** voucher status not updated after POSTWKFL in myQ web (≈2023.11 family).

---

## 4. Cluster B — Voucher Create/Approval screen
*156 bugs — the largest cluster. Two-thirds are UI/control-state and web-vs-classic parity; the actionable sub-families below recur.*

### B1 — Concurrency in multi-tab / stale state (HIGH VALUE)
- **Double submit / resubmit:** voucher submitted, queried back still in Draft (timing), user submits again → two submits logged. Resubmit possible in multiple tabs without a concurrency error. Fix = concurrency check on submit/resubmit. **#1722429** (Closed, ≈2025.04, PRs incl. 120363/120366/125234), **#1741065** (copy of #1722429, Verified). `APWFValidateVoucher000630` is the validation point.
- **Delete while in WFIP:** in a second tab (not requeried) the Delete action stays enabled and lets you delete a voucher that's in workflow → inbox count mismatch. Fix = concurrency check on delete. **SGY/NOG #1705837** (Closed, ≈2025.04).
- **Pattern:** any "I did X in one tab and Y was still allowed in another tab" → a missing concurrency/requery guard.

### B2 — Control-state wrong for status (buttons enabled/disabled incorrectly)
- **#1651807:** Validate button visible/active on **Posted (Paid)/Posted (Reversed)** vouchers; also the **Alt+V shortcut fired even when the button was hidden** (offloaded to #1654633). ≈2024.04 (iter 24.06).
- **#1623263:** posted-status vouchers have editable fields in web.
- **#1717806:** AP Voucher **Security** maintenance — duplicate new keys not validated on save (PRs 108161/108171, ≈2025.04).

### B3 — GL-distribution coding auto-populate / BU mismatch
- **#1666027:** loading an **AFE from a different BU** auto-populates a Property not belonging to the voucher BU, then fails validation on save. Fix in `VoucherController` coding logic (PR 121755, ≈2026.01). Related #1578508.
- See also §6 #1616173 (reclass wiping AFE) — same auto-lookup-clears-control family.

### B4 — Client/SF-case voucher bugs
- **SRC 22-00825502 / #1568564:** errors submitting an AP invoice when the **Desk name contains "&"** — the route-preview return put the invalid desk name back into the submitter desk. Resolution: **add a QFC validation to disallow special chars in Desk names** (Rejected as a code-handling fix; validation approved instead).
- **SRC 22-00866963 / #1571201:** History tab shows **duplicate Reject records** (AP & AFE). Still reproducible in 2025.04 at time of logging (Closed/Duplicate).
- **SGY 25-01050156 / #1762549:** **orphan notes** on a brand-new voucher — `QXREF_VOUCHER_NOTE.ID = 0` rows look like orphans on a new (unsaved) voucher. Cleanup: `delete from QXREF_VOUCHER_NOTE where ID = 0`; could not consistently reproduce the ID=0 creation (Rejected). `BATCHVOUCHERDETAIL.ID` should tie to `QXREF_VOUCHER_NOTE.ID`.
- **#1602672:** AP055 voucher not moving past Draft after approve though BUSSVCRUN completed — **env**: QPECs couldn't log messages (`DATABASE/SQLSERVER_ODBC_DRIVER` key), so processes appeared CS but should have errored. Not a code defect.

---

## 5. Cluster C — Bulk Voucher Handling
*31 bugs. The web Bulk Voucher Handling / Bulk Submit screen (mass reverse/submit/reverse-to-draft of unpaid vouchers). Heavy 2023.xx build-out, so most are net-new-screen QA finds, fixed in the same cycle.*

- **Recurring symptoms:** count mismatch between UI grid and DB query (#1650794); Reverse-To-Draft button no-op / not logging errors (#1548465, #1588170, #1554349); buttons missing / radio-label mismatches / menu-tree gaps (#1532701/#1532778/#1532727/#1532768); creating a reversal of an **invalid Unpaid** voucher (#1541825); STARTS-WITH grid filter unsupported (#1550014); include-attachments behavior (#1543551/#1542050/#1533528).
- **Root cause family:** new-screen completeness/validation gaps; **not** posting-engine defects. Fixes shipped across **2023.04 / 2024.10**.
- **Earlier (pre-rewrite) bulk-submit:** #1455078 / #1457105 "AP Bulk Submit Web Screen Bug Fixes" (≈2022 cycle).
- **Triage:** if the customer's number is wrong, confirm it's not an **upstream POSTWKFL/voucher-state** issue first (§3/§4); Bulk Voucher Handling bugs are about the bulk-action UI/validation, not the posted amounts.

---

## 6. Cluster D — Reclass / Reversal
*20 bugs. Reclass = re-allocate a posted voucher's GL line to a different account; Reversal = negate a posted voucher.*

- **#1623972 — Reclass action bar:** Bulk Edit / Import-from-Excel wrongly enabled during reclass; the negated original line should be **read-only**. Fix in `VoucherController.cs SetControlStates_ReverseReclass()` (set the reclassified-entry fields read-only). PRs 90293/92395, ≈2023 cycle (iter 23.26).
- **ERF #1616173 — AP055 reclass wipes AFE coding:** entering a new AFE during reclass deletes AFE no / cost center / DOI key. Root cause = a control gets cleared as the **auto-lookup fires** (works the 2nd time). Closed/Duplicate.
- **EQC 22-00854618 / #1609157 — DOI errors reversing a voucher:** "Invalid DOI Key Combination" / "Must approve DOI before booking to account which is not JIB billable." Root cause = **code-block / DOI rules changed since the original voucher posted** (original allowed a NULL tier / incomplete DOI; reversals now require complete DOI). Workaround (per Zeb): script old posted batches to complete the DOI key, then **reclass via GL025** (copy batch, double the lines, reverse the sign). Not a clean product fix — config/data + manual reclass.
- **#1538627:** bulk-reversal discrepancy from AP056 fixes; **#1687637:** classic AP055 vs web give different messages on reversal.
- **Triage:** reversal/reclass "can't post" is usually **DOI/code-block rule** or **missing zero check-run def** (§3 A5), not the reversal engine.

---

## 7. Cluster E — AP061 check-run / check-print
*31 bugs (incl. AP155/AP158/AP159/AP171 outstanding-check & manual-check screens).*

- **Blank check PDF (#1449309):** check for a given bank prints empty — **SSRS check-form not deployed** for the bank (`QCODE_CHECK_FORM` points e.g. to `/QCFS/Accounts Payable/CheckForm_CapOne`). Env/SSRS setup, not code.
- **AP061 unhandled exception cutting multiple GL rows (#1449120 / #1554412):** a **platform grid bug** — `QDbGridUserControl.cs` removes an "Added"-state row mid for-loop, so the loop index outruns the row count. Fixed in **QFC Winforms**; QCFS could only consume it once UI v2 started (so it lingered Active across cycles; #1554412 finally Closed ≈2022.23).
- **Manual check wrong amount, multiple suffixes (#264880):** AP171 manual check for a vendor with **multiple address-override suffixes** printed 4 checks at wrong amounts — a **cartesian** in the report join over `SCTRL_BA_ADDRESS_VENDOR`. Fix = corrected report SQL (PR 44974, ≈2021.03). Only triggers when payee override is defined on >1 suffix.
- **Cash Requirements report combines vendors (#107894):** two BUs with identical name but different BA numbers get combined onto one AP check / `RPT_CMR007` line. Report fix (legacy).
- **AP155 state-in-zip (26-01089614 / #1795190):** state code appears in the Zip column, State blank, in CHECKRUNJOURNAL. Root cause = `SELECT_CHECKRUNJOURNAL_INQUIRY` CASE statements for state/zip. Code fix going forward; **existing rows need a data script** to fix CHECKRUNJOURNAL. ≈2026.04 (iter 26.07), PRs 126018-126021.
- **AP158 wrong company (SGY #1631300):** outstanding checks entered for company 20 show as 201 — **`ID`/`IDBEOWNER` vs `USERKEY`** display, **not a defect** (Rejected).
- **AP159 accepts invalid BA (EQC #1717465):** records with non-existent BA numbers get saved to DB though they vanish from the grid on refresh — add BA validation (PR 117526, ≈2025 cycle).
- **AP061 "Save Changes?" popup with no changes (#1379476):** after Validate with no errors the `VALIDATESUCCESSDATE` is set in memory but not yet committed, so rows look modified on Approve. Also affects GL025. PRs 59177/59178 (≈2021.19).
- **AP061 "multiple messages / object reference" (#1317524):** transient — a **service was down** at the time (couldn't talk to any endpoint); not reproducible after. Restart-services class.

---

## 8. Cluster F — AP150 / ACH / EFT export
*18 bugs. AP150 = ACH/EFT payment export; ACH_EMAIL = vendor remittance email.*

- **Re-export exception (#1684117):** ticking **Re-Export** on the Export ACH dialog throws an exception. Added a guard to surface a proper validation instead of the raw exception (PRs 119124/119125/119579, ≈2024.10 regression). Underlying "missing bank export setup" is a client config item.
- **ACH_EMAIL "service unavailable" (#1725807):** Send-Email-for-selected-vendor fails with **HTTP 503** — **SSRS down/unreachable**, not AP code. `QPSACHEmailNotification.cs ExecuteReport` picks the report; if SSRS is down it 503s. Logged box review #1728503. ≈2025.04.
- **AP150 re-export / bank-format issues (#22-00827175 SRC family, #1578890 resubmit, #1632215 AP reports param):** several AP report/export param issues resolved by **report-def / registered-SQL config** (e.g. #1632215 RPT_APR009 — removed picklist ID from param 36540, converted code table 36217 to registered SQL).
- **Triage:** AP150/ACH "fails to run" is most often **SSRS availability** or **bank-export setup**, not a code defect — check SSRS first, capture the exact HTTP/COM error.

---

## 9. Cluster G — BA005 / Vendor master
*23 bugs. BA005 = Business Associate (vendor) maintenance, classic + web; PUBBA = publish-BA batch.*

- **PUBBA fails after Update (#1318316):** clicking Update fires PUBBA which fails — **metadata mod-define priority** picked the wrong (ENGS vs UPS) PUBBA. Workaround `UPDATE QARCH_META_MOD_DEFINE SET PRIORITY=8 WHERE METADATA_PROFILE='QUIN' AND MODULE_CD='ENGS' AND METADATA_LAYER_CD='UPS'`. **Recurs every cycle** after QFC upgrades reset the priority — check this first. Related #1445255 (PUBBA errors after BA005 update).
- **Vendor payee override clears out in classic (#1625265):** Address-Overrides → Vendor Payee Override details wiped on Update in classic (web is correct). Method changed incorrectly; PR 90161, ≈2023.21. Related long-running GEC #1608773, #1409007.
- **Override Reason dropdown empty (#1391730):** mandatory Override Reason dropdown has no data → can't create any address override. Root cause = **`SCODE_COUNTRY` had `US` marked `HIDDEN_IND=1`**; fix `UPDATE SCODE_COUNTRY SET HIDDEN_IND=0 WHERE COUNTRY_CD='US'`. Data/config. PRs 60004/64482.
- **Web-vs-classic parity (CNX 20-00098269 / #1555206):** duplicate Tax-ID save allowed in classic but blocked in web — long-standing parity backlog (Closed/Duplicate of #1371251; "six different BA bugs" reviewed together).
- **DISABLE_CLASSIC_SCREEN not honored (#1694778):** when `DISABLE_CLASSIC_SCREEN=1` the BA005 **Comment** button is still editable. Fix = remove note initialization / disable the toolbar button on disable (PR 119132, ≈2025.23). Doc: `documentation/Analysis/Quorum.QCA.ClassicGUI/BA005_Screen_Disable_Behavior.md`.
- **1099 checkbox vs DB mismatch (#1096612):** BA005 1099 checkbox vs `QCTRL_BA_ADDRESS_QRA.BA_1099_IND` mismatch — resolved by **enabling the config to address level** (config; Rejected). See also #1319075 (can't save 1099 for Corporation = **expected**: don't issue corporations 1099s, gated by `ALLOW 1099 FOR CORPORATION`).
- **#249402 (EQC):** vendor bank account not saved at a BA-Suffix level; **#1722541 (ARS 25-01013311):** Core Financials tab "Saved Successfully" but nothing persisted → vendor picklist "No Data Found" in AP055 (global BU-ID association).

---

## 10. Cluster H — 1099 / AP170 / AP151 / QP073
*50 bugs. AP170 = 1099 Payables Override screen; AP151 = Xref 1099 Misc; AP043 = 1099 form config; QP073 = QCFS process launcher (runs the 1099 Payables Override process QSTG1099OV).*

- **Real defect — 1099 wrong when multiple invoices paid by one check (#105822 / #76822, legacy issue 308043):** the marquee 1099 calc defect. Fixed via a **client patch** (e.g. NWD Package 10) — when the same check pays multiple invoices the 1099 total was wrong. If a client hits this near IRS deadline, confirm their build includes the 308043 fix. Also #105822 was patched to NWD individually.
- **QP073 1099 Payables Override "stopped with errors" (#200909, #198847):** root cause = **QFC DocumentManagement service container failed to load** after a QFC upgrade (`Unable to create service container … QClientDocumentManagementServiceContainer`) — **env/QFC**, resolved when QFC upgrade settled. Not a 1099-logic bug.
- **AP170 columns missing BOX15/BOX17 (#196983 etc.):** new columns added at the **end of the table** (we never drop/recreate to preserve client data); after metadata reapply they appear. Largely **metadata/QA-perception**, not posting logic.
- **AP170 BOX# not populated per AP151 xref (#202615):** **not a bonafide bug** — the tester misunderstood AP151 (the box you specify *is* the box populated; no remapping). Closed as expected behavior.
- **Pattern:** most AP170/AP151/QP073 bugs are **(a) QFC-upgrade env issues, (b) metadata column/label fixes, or (c) test misunderstanding of 1099 box mapping**. The one true calc defect is **multiple-invoices-one-check (308043)**. Validate config + service health before assuming a 1099 engine bug.

---

## 11. Cluster I — IC offset & inter-company posting
*6 bugs.*

- **Inter-company voucher won't post with Account Xref (#101971):** IC vouchers fail Post Validations (GL400/GL401) when the **Journal Definition is configured to Use Account Cross-Reference**. Code fix. **Fixed 2019.02** (GEC 217064 / CORE 217069). Verified.
- **I/C Offset not creating GL lines (#66539, #70248, #70250 family):** clicking I/C Offset on a line with a Post-to BU different from the header created no offset line. Several logged **"no longer reproducible" / Rejected** (#70248, #66539 split) — the function was repaired during the QCFS→VSTS port; if a client reports it, confirm the Post-to BU differs from the header and the offset config exists.
- **String/varchar BU posting (#185432):** couldn't post a voucher/JE to a BU set up as a string (varchar BU from QRA). Code fix (PR 24489, related #174585), ≈2020.07.

---

## 12. Cluster J — Fast Track workflow
*4 bugs. Fast Track = one-click approve-through-all-remaining-steps; shared QFC workflow used by AP & QCA AFE.*

- **#1443159 — final approval-limit step not marked mandatory when dollar = user limit:** when the voucher amount **exactly equals** the user's approval limit, the final approval-limit step isn't flagged mandatory, so Fast Track skips it. Root cause = **`>` vs `>=`** in `\Quorum.QFC.Workflow\Managed\Quorum.QFC.Workflow.ApprovalRoute\QWFBuilderForMetadata.cs`. PRs 66897/67325/67327, ≈2022.06.
- **#1450881 — Fast Track errors when in inbox but not locked to self:** with locking enabled (`AFE_ALLOW_LOCK`), Fast Track errored "must lock to yourself" unlike normal Approve. Fix aligns Fast Track with approve behavior. ≈2022.08.
- **#1444650 — Fast Track admin-action security:** added a new security object (`AFE_ROUTE_ADMIN_FAST_TRACK`, AP equivalent in `QCFSConstants`) checked before showing the admin Fast Track option; new rows in `QARCH_SEC_OBJECT`. Touches `VoucherController.cs`, `QUIControllerVoucher.cs`, `QCFSConstants.cs`.
- **#1618436 / #1623794:** Fast-track batches getting picked up by POSTWKFL and erroring / needing the "Post In Progress" status like classic (cross-ref §3 A2).

---

## 13. Fix-Version Matrix

| Bug | Cluster | Symptom (short) | State / Reason | Fixed-in (inferred) | Linked SF / client |
|---|---|---|---|---|---|
| #1739552 | A | POSTWKFL deadlock vs close/refresh | Closed | ≈2025.04 (merged) | CEN/MAC |
| #1743547 | A | deadlock repro attempt | Rejected (no repro) | n/a | CEN(2023.04), MAC(2024.10) |
| #1669576 | A | "Post In Progress" stuck guard | Closed/Dup (#1660263) | ≈2025.04 | — |
| #1747642 | A | batch checks stuck Post Pending AP061 | Closed | ≈2025.04 | TPW 25-01035193 |
| #1708039 | A | POSTWKFL check-run bulk-insert ID | Closed | ≈2025.04 | — |
| #1675655 | A | POSTWKFL vs ARCCOREINT | Rejected (by design) | n/a (#1667696) | — |
| #209184 | A/I | reversal "no AP config for BU" | Closed | ≈2020 (Web 17.20.0) | — |
| #70249 | A | reversal could-not-post | Rejected (data) | n/a | — |
| #74065/#74064 | A | fiscal period 0 vs 1 | Closed | legacy v16 (TFS 70606) | — |
| #72944 | A | POSTWKFL timeout / DB index | Closed | legacy Sprint 40 | issue 304058 |
| #111224 | A | CNR payment-app null-ref | Verified | legacy Sprint 60 | CNR |
| #1722429 / #1741065 | B | voucher double resubmit (concurrency) | Closed/Verified | ≈2025.04 | — |
| #1705837 | B | delete voucher while in WFIP | Closed | ≈2025.04 | SGY/NOG |
| #1651807 | B | Validate button on Posted(Paid) | Closed | ≈2024.04 | — |
| #1717806 | B | voucher-security dup-key validation | Closed | ≈2025.04 | — |
| #1666027 | B | AFE auto-populates wrong-BU Property | Closed | ≈2026.01 | — |
| #1762549 | B | orphan notes (ID=0) | Rejected (cleanup script) | n/a | SGY 25-01050156 |
| #1568564 | B | Desk name with "&" | Rejected→add validation | ≈2022 cycle | SRC 22-00825502 |
| #1571201 | B | dup Reject history records | Closed/Dup | still seen 2025.04 | SRC 22-00866963 |
| #1602672 | B | voucher stuck Draft after approve | Closed (env) | n/a | — |
| #1623972 | D | reclass action-bar control states | Closed | ≈2023 cycle | — |
| #1616173 | D | reclass wipes AFE coding | Closed/Dup | — | ERF (Enerplus) |
| #1609157 | D | DOI errors on reversal | Rejected→script+GL025 | n/a | EQC 22-00854618 |
| #1449309 | E | blank check PDF (SSRS form) | Closed (env) | n/a | — |
| #1449120 / #1554412 | E | AP061 cut-rows grid crash (QFC) | Closed | ≈2022 (QFC Winforms) | — |
| #264880 | E | manual check wrong amt (cartesian) | Closed | ≈2021.03 (PR 44974) | — |
| #107894 | E | cash-req combines vendors | Verified | legacy | — |
| #1795190 | E | AP155 state-in-zip | Acceptance/Closed | ≈2026.04 | 26-01089614 |
| #1631300 | E | AP158 wrong company | Rejected (not bug) | n/a | SGY |
| #1717465 | E | AP159 accepts invalid BA | Closed | ≈2025 cycle | EQC |
| #1379476 | E | AP061 false "Save Changes?" | Closed | ≈2021.19 | — |
| #1684117 | F | AP150 re-export exception | Closed | ≈2024.10 | — |
| #1725807 | F | ACH_EMAIL 503 (SSRS) | Closed (env) | n/a | — |
| #1632215 | F | AP reports param (RPT_APR009) | Closed | ≈2023.04 (config) | 23-00928008 (MEW) |
| #1318316 | G | PUBBA wrong meta-mod priority | Closed | recurs each QFC cycle | — |
| #1625265 | G | vendor payee override clears (classic) | Closed | ≈2023.21 | — |
| #1391730 | G | Override Reason dropdown empty | Closed (data: SCODE_COUNTRY) | ≈2021.20 | — |
| #1694778 | G | BA005 comment editable w/ DISABLE_CLASSIC_SCREEN | Closed | ≈2025.23 | ENGS |
| #1096612 | G | 1099 checkbox vs BA_1099_IND | Rejected (config) | n/a | — |
| #1319075 | G | can't save 1099 for Corporation | Closed (expected) | n/a | — |
| #1555206 | G | BA tax-ID save parity classic vs web | Closed/Dup (#1371251) | backlog | CNX 20-00098269 |
| #1722541 | G | vendor Core-Financials won't save | Verified | ≈2025.04 | ARS 25-01013311 |
| #105822 / #76822 | H | 1099 wrong, multi-invoice one check | Closed | client patch (308043) | NWD |
| #200909 / #198847 | H | QP073 1099 override service container | Closed (env/QFC) | n/a | — |
| #196983 | H | AP170 BOX15/17 columns | Closed (metadata) | ≈Product Dev | — |
| #202615 | H | AP170 box per AP151 xref | Closed (expected) | n/a | — |
| #101971 | I | IC voucher won't post (Account Xref) | Verified | 2019.02 | GEC |
| #185432 | I | post to string/varchar BU | Closed | ≈2020.07 | — |
| #1443159 | J | Fast Track skips final step (>= bug) | Closed | ≈2022.06 | — |
| #1450881 | J | Fast Track lock-to-self error | Closed | ≈2022.08 | — |
| #1444650 | J | Fast Track admin-action security | Closed | ≈2022.07 | — |

---

## 14. Diagnostic pointers

> Verify table/column names against the client schema; always verify-SELECT before any UPDATE/DELETE, in a transaction.

**Get the failing process + error (always do this first for batch issues):**
```sql
-- POSTWKFL / PSTWKSPLT / PUBBA / ACH_EMAIL / QP073 messages by process queue id
SELECT * FROM QARCH_PROCESS_MSG_LOG WHERE PROCESS_QUEUE_ID = <PQID> ORDER BY 1;
-- Confirm the new post child-job metadata exists (A1 fix prerequisite)
SELECT * FROM QARCH_CTRL_PROCESS WHERE PROCESS_ID = 'BSVPOST';
```

**Stuck batch status (A2):**
```sql
SELECT DELETED, * FROM BATCHVOUCHERDETAIL ORDER BY ID DESC;   -- find the stuck batch
-- Post In Progress / Post Pending rows are the stranded ones; script status back, then re-run POSTWKFL.
```

**Orphan voucher notes (B4 #1762549):**
```sql
SELECT * FROM QXREF_VOUCHER_NOTE ORDER BY ID DESC;   -- ID = 0 rows look like orphans on a new voucher
-- DELETE FROM QXREF_VOUCHER_NOTE WHERE ID = 0;       (after verify)
```

**PUBBA metadata priority (G #1318316) — recurs after QFC upgrades:**
```sql
SELECT * FROM QARCH_META_MOD_DEFINE WHERE MODULE_CD IN ('UPS','ENGS') AND METADATA_PROFILE='QUIN';
-- UPDATE QARCH_META_MOD_DEFINE SET PRIORITY=8 WHERE METADATA_PROFILE='QUIN' AND MODULE_CD='ENGS' AND METADATA_LAYER_CD='UPS';
```

**Override Reason dropdown empty (G #1391730):**
```sql
SELECT * FROM SCODE_COUNTRY WHERE COUNTRY_CD='US';   -- HIDDEN_IND must be 0
```

**Manual-check cartesian over suffixes (E #264880):**
```sql
SELECT * FROM SCTRL_BA_ADDRESS_VENDOR WHERE BA_NO = '<BA>';  -- >1 payee override row = the multi-suffix trigger
```

**Check-form / SSRS (E #1449309, F #1725807):**
```sql
SELECT * FROM QCODE_CHECK_FORM;   -- the form path must exist & SSRS must have it deployed; blank PDF / 503 = SSRS not deployed/down
```

**Key code locations:**
| Symbol / file | Repo / area | Cluster |
|---|---|---|
| `CustomCodeBlockData.cs` → `CopyValuesTo` | `Quorum.QCFS.BL` | A3 (ID<0 add-row handling) |
| `VoucherWorkflow.cs` (~L649) | `Quorum.Upstream.QCFS.Web` | A5 (no-AP-config error) |
| `APWFValidateVoucher000630` | QCFS workflow validation | B1 (submit concurrency) |
| `VoucherController.cs` `SetControlStates_ReverseReclass()` | QCFS web controllers | B2/D (reclass control states) |
| `QFrmBatchVoucherMaster.cs` | QCFS classic | (copy-voucher SQL quoting, #1720446) |
| `QDbGridUserControl.cs` | `Quorum.QFC.Winforms` | E (#1449120 cut-rows loop) |
| `QPSACHEmailNotification.cs` `ExecuteReport` | QCFS ACH | F (#1725807) |
| `QWFBuilderForMetadata.cs` | `Quorum.QFC.Workflow.ApprovalRoute` | J (#1443159 `>=`) |
| `QCFSConstants.cs`, `QUIControllerVoucher.cs` | QCFS | J security objects |
| `SELECT_CHECKRUNJOURNAL_INQUIRY` (registered SQL) | QCFS | E (#1795190 state/zip) |

---

## 15. Escalation guidance

**Is it fixed in the client build?** — Inferred fix-versions above use the title release prefix / iteration; **confirm against `Quorum.Upstream.QCFS.ReleaseNotes` and the linked PR before telling a client a build**. Quick rule of thumb: `2025.04`-tagged or `25.xx`-iteration fixes are in **2025.04+**; `2024.10`/`24.xx` in **2024.10+**; `2026.04`/`26.0x` in **2026.04+**; "Sprint NN"/"Product Development"/legacy = pre-2020, generally in any current build but may need a **client patch** for old branches (e.g. the 1099 308043 patch, NWD/ATR).

**Route to Engineering (real code defect) when:**
- POSTWKFL deadlock vs close/refresh (#1739552), check-run bulk-insert ID (#1708039), reversal AP055 perf loop (#1720772), copy-voucher SQL quoting (#1720446).
- Voucher concurrency (double submit / delete-in-WFIP) #1722429/#1705837; Fast Track `>=` #1443159; IC voucher Account-Xref #101971; multi-invoice-one-check 1099 (308043).
- Provide: **PQID + exact error**, client + BU + accounting period, voucher/batch IDs, repro, and the linked WI's iteration/PR.

**Handle as Configuration / Data (no code) when:**
- Reversal "no AP configurations for this BU" → add the **zero check-run definition** (#209184/#70249).
- PUBBA failing after BA005 update → **`QARCH_META_MOD_DEFINE` priority** (#1318316, recurs after QFC upgrades).
- BA005 Override-Reason empty → `SCODE_COUNTRY US HIDDEN_IND=0` (#1391730); 1099-checkbox/DB mismatch → enable address-level config (#1096612).
- AP report/export param issues → report-def / registered-SQL config (#1632215).
- DOI errors reversing a voucher → script DOI key complete + reclass via GL025 (#1609157).
- Existing bad data after a code fix (AP155 state/zip #1795190, AP158 #1631300) → data script on CHECKRUNJOURNAL.

**Restart-services / environment first (no code):**
- ACH_EMAIL 503 / AP061 "couldn't talk to any endpoint" / blank check PDF → **SSRS / service availability** (#1725807, #1317524, #1449309). Capture the exact HTTP/COM error while failing.
- QP073 1099 "service container" errors → **QFC upgrade** settling (#200909).

**Expected behavior / not-a-bug (educate, don't escalate):**
- Can't 1099 a Corporation when `ALLOW 1099 FOR CORPORATION=0` (#1319075).
- AP170 box populated = the AP151 box you specified (no remapping) (#202615).
- AP158 company "201" vs "20" = `USERKEY` vs `IDBEOWNER` display (#1631300).
- POSTWKFL failing while ARCCOREINT runs = intentional lock (#1675655/#1667696).

---

*Skill created 2026-06-14. Source: ADO Financials bugs (Closed/Resolved) — 548 WIQL matches, 395 QCFS-AP, ~50 deep-read. ADO is read-only; no work items were modified. Fix-versions are inferred from title release prefix + iteration path (IntegrationBuild is unpopulated) — verify in Quorum.Upstream.QCFS.ReleaseNotes / the linked PR before quoting to a client.*
