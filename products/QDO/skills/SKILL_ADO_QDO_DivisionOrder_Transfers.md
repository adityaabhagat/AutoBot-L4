# SKILL: QDO Division Order / DOI / Transfers — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** Quorum Upstream **QDO** (Division Order) — with DOI logic that crosses into **QCA** (Cost Accounting / AFE / JIB) and **QCFS** (Financials AP/GL voucher validation)
**Source:** Azure DevOps Bugs (Closed/Resolved) under Area Path `QuorumSoftware\Engineering\Financials`, title-filtered for: *division order, DOI, decimal interest, conveyance, transfer, suspend, ownership, owner relation*. **34 bugs matched; 24 deep-read** (Description + ReproSteps + dev comments + linked PRs/commits + attachments).
**Use When:** an Upstream case touches **DOI Setup (DO006), DOI calculation/approval, DOI Maintenance / Interest transfers, DOI validation on AP vouchers (AP055/GL025) and AFEs (JB020/AFE import), JIB DOI keys, or converted-AFE DOI decimals.** For pure JIB billing math, AP/GL posting, or AFE workflow not involving the DOI key, use the QCA/QCFS skills.

> **Honesty note:** Many "Financials transfer" bugs the WIQL pulled in are NOT QDO (Material Transfer #68244, JE Transfer Selection #65870/#71989/#78671, SFTP/EnergyLink transfer #1592537). They're noted as overlap and excluded from the QDO clusters. Several DOI bugs closed **Rejected / By-Design / Not-reproducible / Duplicate** — those are called out explicitly so you don't chase a phantom fix. **No build number is invented**: where ADO carries no clean `IntegrationBuild`, the fix is cited by **iteration / changeset / PR** instead, and "verify in `Quorum.Upstream.QDO.ReleaseNotes`" applies.

---

## TABLE OF CONTENTS
1. [Quick Triage](#1-quick-triage)
2. [Concepts & the DOI Key](#2-concepts--the-doi-key)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — DOI validation on AP vouchers & GL batches (AP055 / GL025)](#4-cluster-a)
5. [Cluster B — DOI / JIB validation on AFEs (JB020, AFE import, AFE type)](#5-cluster-b)
6. [Cluster C — DOI Setup screen: calculate / approve / delete / documents (DO006)](#6-cluster-c)
7. [Cluster D — DOI Maintenance & Interest Transfers (DOINTXWRK preview)](#7-cluster-d)
8. [Cluster E — Converted-AFE DOI decimals & DOI-key data fixes](#8-cluster-e)
9. [Cluster F — DOI query performance & picklist duplicates](#9-cluster-f)
10. [Overlap / Not-QDO (matched on "transfer")](#10-overlap--not-qdo)
11. [Fix-Version Matrix](#11-fix-version-matrix)
12. [Diagnostic pointers](#12-diagnostic-pointers)
13. [Key code & repos](#13-key-code--repos)
14. [Escalation guidance](#14-escalation-guidance)

---

## 1. Quick Triage

| Symptom (user report) | Likely cluster | First check |
|---|---|---|
| AP voucher / GL batch errors "Invalid DOI Key Combination" / "Must approve DOI before booking…" on **reverse/reclass** of an old voucher | **A** (#1609157, By-Design) | Was the original posted with NULL tier / incomplete DOI key *before* code-block rules tightened? TIER is part of the DOI key. |
| "Activity date is not within the DOI's effective date range" missing or wrong on AP Voucher (AP055 / web) | **A** (#216752/#216904/#217341) | Validation does fire for owner+property; confirm message text. |
| Duplicate pop-up / process-monitor messages for an **unapproved DOI** property on GL025/AP055 post | **A** (#1590711 → dup of #1588161) | `CustomCodeBlockUpstreamValidator.cs` logging the message twice. |
| AFE XML import (**AFEEXTIMP**) fails "The property must have a DOI" though manual AFE allows no DOI | **B** (#1371768) | Legacy import validations hard-require JIB DOI; web validations diverged. |
| JB020 "**not an effective JIB DOI**" error saving a valid record | **B** (#1382019) | `QBusinessRulePropEffDOI.cs` parsed dates as strings — broke on non-US machine date format. |
| DO006: **"NRI decimal sum of 1.75"**, can't Calculate/approve DOI | **C** (#364709, setup) | Clear inquiry date; look for a stray future-dated owner line (typo year). |
| DO006: **Delete** button greyed out on a header-only DOI | **C** (#1713445 → dup of #1717454) | Add an owner & save, or use Pending DOIs widget. |
| DO006: **documents won't attach/save** | **C** (#1623182, deployment) | Doc-Mgmt service port misconfig (123 vs 9005), not QDO code. |
| **Preview DOI Interest transfer (DOINTXWRK)** batch fails after a maintenance-group transfer | **D** (#1732619) | Missing `IQMetadataService.DO` / process-launcher service-container registration. |
| Converted AFEs have **NULL `AFE_DOI_DEC`** / can be re-submitted | **E** (#74170/#74171) | Recompute decimal from cost-center DOI_DEC; fix WF status. |
| **DOI picklist shows duplicates** (AFE committed-costs, web) | **F** (#1687634) | Picklist needs BU **and** AFE; distinct fix applied. |
| `Sel_DoiDecimals` query slow, high disk I/O | **F** (#106834, tabled) | Bloated interface tables; run archive/purge. |

---

## 2. Concepts & the DOI Key

- **DOI** = Division Order of Interest — the ownership split for a property. Stored in `DONL_DO_HDR` (header) + `DONL_DO_DETAIL` (owner detail rows with `EFF_DT_FROM`/`EFF_DT_TO`, `NRI_DEC`). Maintained on **DO006: DOI Setup**.
- **The DOI Key** = `PROP_NO + DO_TYPE_CD + DO_MAJ_PROD_CD + TIER + OPER_BUS_SEG_CD`. **TIER is part of the key** — anything posting to JIB requires a complete, *approved* DOI key. This is the crux of the AP/GL reversal failures (Cluster A): a voucher posted before the key was enforced cannot be reversed once the rules require it.
- **DOI Types** include **JIB** (Joint Interest Billing). A "JIB DOI" must be effective for the activity/accounting date.
- **DOI calculation (DOGWICALC)** sums owner NRI per effective window; it **fails approval if the NRI decimal sum ≠ expected** (e.g. "sum of 1.75"). Usually a *setup* problem (overlapping/future-dated owner lines), not an engine bug — §6.
- **Code-block validations** = the upstream rules that check the DOI/cost-center coding on AP/GL batch lines at validate/post (`CustomCodeBlockUpstreamValidator.cs`, logged to `QARCH_PROCESS_MSG_LOG`). They drive most AP055/GL025 DOI messages.
- **AFE_DOI_DEC** = the AFE-header decimal-interest summary (`QCTRL_AFE_HDR.AFE_DOI_DEC`), derived from cost-center `QCTRL_AFE_COST_CNTR.DOI_DEC`. Conversions can leave it NULL — §8.
- **DOI Maintenance / Interest Transfer** = the web flow that builds a **Maintenance Group**, performs a transfer between owners, and **Previews** via the `DOINTXWRK` batch (workspace-group preview) — §7.
- **DOINTXWRK** = "Preview DOI Interest transfer for Workspace Group" batch process.

---

## 3. Decision Tree

```
QDO / DOI case
│
├─ Error on an AP voucher (AP055) or GL batch (GL025)?
│   ├─ "Invalid DOI Key Combination" / "Must approve DOI…" on REVERSE/reclass of an OLD voucher
│   │        → §4 By-Design (#1609157): original posted w/ incomplete DOI key before rules tightened. Script the old batch's DOI key OR reclass via GL025.
│   ├─ Effective-date message missing/odd on the voucher                → §4 (#216752/#216904/#217341) — validation fires for owner+property
│   └─ Duplicate pop-up messages for an unapproved-DOI property          → §4 (#1590711 → #1588161) — code-block validator double-logging
│
├─ Error on an AFE?
│   ├─ AFE XML import fails "property must have a DOI" (AFEEXTIMP)        → §5 (#1371768) — legacy import validations vs web; fixed SQL/joins
│   ├─ JB020 "not an effective JIB DOI" on a valid save                  → §5 (#1382019) — date-format string parse in QBusinessRulePropEffDOI.cs
│   └─ Error after changing AFE type to require DOI                      → §5 (#57229, Rejected — no root cause captured)
│
├─ DO006 DOI Setup screen?
│   ├─ Can't Calculate / "NRI decimal sum of X.XX" / can't approve       → §6 (#364709, SETUP) — stray future-dated owner line; clear inquiry date
│   ├─ Delete button greyed on header-only DOI                           → §6 (#1713445 → #1717454) — add owner & save / Pending DOIs widget
│   ├─ Documents won't save                                              → §6 (#1623182, DEPLOYMENT) — Doc-Mgmt service port (123 vs 9005)
│   └─ Spurious QXREP_DOI_DOC popup on approve/unapprove                  → §6 (#1462177, NOT REPRODUCIBLE / env)
│
├─ DOI Maintenance / Interest Transfer (web)?
│   ├─ Preview (DOINTXWRK) batch fails after transfer                    → §7 (#1732619) — missing service-container registration (FIXED, PR #112477/#112478)
│   └─ "Add to Maintenance Group" button moved                          → §7 (#1665590, By-Design req #1632701)
│
├─ Converted AFE / DOI-key data anomaly?                                 → §8 (#74170/#74171) — NULL AFE_DOI_DEC; data UPDATE scripts
│
├─ Slow DOI query / duplicate picklist?                                  → §9 (#106834 perf-tabled; #1687634 picklist distinct)
│
└─ "transfer" in title but Material/JE/SFTP transfer?                    → §10 NOT QDO
```

---

## 4. Cluster A — DOI validation on AP vouchers & GL batches (AP055 / GL025)

The largest QDO-adjacent signature: the **DOI key / approval state** is enforced when posting AP vouchers (AP055) and GL batches (GL025) via the upstream **code-block validations**.

### A1 — Reverse/reclass fails: "Invalid DOI Key Combination" / "Must approve DOI before booking to account which is not JIB billable"  — **By-Design, data workaround**
- **Bug:** #1609157 (EQC, **Closed/Rejected**, "Recommend Close"). Linked SF case **22-00854618**.
- **Symptom:** reversing (or copying) an old posted voucher throws the DOI-key errors, although the *original* posted fine.
- **Root cause (dev, Ben Weis):** the original vouchers were posted **with a NULL tier / incomplete DOI key** at a time when the account/code-block setup did not require it. Since then the client changed setup (account code-block, JIB group, or took a validation fix) so a **complete DOI key (TIER included) is now required** for anything moving to JIB. New *and* reversal vouchers now correctly fail. "As of now I don't see an issue with the code really here."
- **Workaround (per Zeb / Nitin Shingi):** (1) **script the old posted batches to complete the DOI key** so it's fully populated on reclasses; (2) use **GL025** to reclass; or (3) manually build a reclass — copy the original batch, double the lines reversing the sign on originals, fix Tier coding, reclass on the new lines. Alternatively temporarily revert the code-block rules to repost as-was, then restore.
- **Takeaway:** when a reversal fails on DOI key but the original posted, **don't escalate as a code bug** — it's setup drift; fix the DOI key on the historical data.

### A2 — Effective-date validation message missing/wrong on AP Voucher  — **Fixed (cosmetic)**
- **Bugs:** #216752 (Owner No. not specified), #216904 (Owner No. specified), #217341 (Classic AP055 batch monitor). All **Closed**, iteration 20.15, related to feature WI #210356.
- **Symptom:** when the voucher **Activity Date is outside the DOI's effective date range**, the validate/save message wasn't displaying (or had capitalization discrepancies).
- **Resolution:** validation **does** fire; final message is: *"The Activity Date [date] is not within the DOI's effective date range for owner [owner] and property [property]."* (note: owner is included). The walkthrough/AC text was updated; QA's only remaining finding was capitalization, accepted. To trigger, use an account that is **neither** a valid JE account (`QCODE_JE_ACCOUNT_XREF.BILLING_ACCT_NO`) **nor** a valid inventory account (`QCODE_INVEN_TYPE_ACCT.LOC_ACCT_NO`).

### A3 — Duplicate unapproved-DOI messages on GL025/AP055 post  — **Fixed (via #1588161)**
- **Bug:** #1590711 (**Closed as Duplicate** of **#1588161**), tag "2023.04 Regression".
- **Symptom:** posting a GL025 batch / AP055 voucher that uses an **unapproved (inactive) DOI property** shows the inactive-property notification **twice** in the pop-up (and process monitor).
- **Root cause (Ben Weis):** both messages come from the **code-block validations** in the batch — logged to `QARCH_PROCESS_MSG_LOG` and displayed after the process finishes. Fix tracked under **#1588161**; code: `CustomCodeBlockUpstreamValidator.cs`.

---

## 5. Cluster B — DOI / JIB validation on AFEs

### B1 — AFE XML import (AFEEXTIMP) fails "The property must have a DOI"  — **Fixed**
- **Bug:** #1371768 (ENC/Encino, **Closed**, iteration 21.18, tag "Maintenance: ENGG"). Linked WIs #1457564/#1457781/#1432046/#1451694.
- **Symptom:** the AFE XML import process **AFEEXTIMP** rejects AFEs without a JIB DOI ("The property must have a DOI"), even though you **can** create such an AFE manually / in Web. Encino imports all AFEs from a 3rd-party system (AFENav) and had to hand-create the no-DOI ones.
- **Root cause (Wes Geier / Ben Weis):** the import process is legacy (built in 5.0) — its hard-coded validations in **`QPSQcaAFEExternalImportValidate.cpp` (`ValidateImportData()`)** and the registered SQLs **were never updated when validations moved to Web**, so they still inner-join `DONL_DO_HDR` and demand a DOI.
- **Fix:** updated the validation SQLs (branch `feature/1371768_AFE_ImportValidations`, repo **`Quorum.Upstream.QCA.ClassicBatch`**):
  - `m_QcaAFE_UPD_ValidDOI` and `m_QcaAFE_UPD_AFEValidateCCOpNonOp` → join `QCODE_AFE_RULE` where `DOI_RULE_ID = 2` (only require DOI when the AFE rule says so).
  - `m_QcaAFE_DEL_ExistingAFECostCntr` → change to **LEFT JOIN** to `DONL_DO_HDR`, allow `TIER` = NULL.
  - `m_QcaAFE_INS_AFEHDR` / `m_QcaAFE_DEL_ExistingAFEHDR` → remove the unnecessary `DONL_DO_HDR` join.
  - **PRs:** #57928, #57954, #69430, #72351. SQL fix scripts attached (`1371768_m_QcaAFE_UPD_ValidDOI.sql`, `1371768_m_QcaAFE_INS_AFEHDR.sql`).
- **Gotcha (config, not the bug):** after import, the process also fires a **notification**; if the client has **no event detector** set up it errors saying it couldn't send the notification — but the import already happened. Clients using this import must set up the detector.

### B2 — JB020 "not an effective JIB DOI" on a valid save  — **Fixed (date-format)**
- **Bug:** #1382019 (**Closed**, iteration 21.18, tag "2021.10 QA").
- **Symptom:** JB020 (Drilling Overhead) throws "not an effective JIB DOI" validation error saving a valid record for a valid AFE/property.
- **Root cause (Ben Weis):** the business rule **`QBusinessRulePropEffDOI.cs` → `IsDOIEffective`** passes the DOI from/to dates as **strings** and converts via `QDateTime.Parse(sDT_FROM)` / `Parse(sDT_TO)`. That parse is **unreliable under a non-US Windows short-date format** — QA's machine date format differed, so the comparison failed. (Repo: `Quorum.Upstream.QCA.ClassicGUI\Quorum.QCA.Shared\BusinessRules`.)
- **Fix:** rule reworked to evaluate the effective DOI **independent of the machine's date format**. Validity is checked with this query against `DONL_DO_HDR`/`DONL_DO_DETAIL` (MIN `EFF_DT_FROM` / MAX `EFF_DT_TO`, `JIB_ACTIVE_CD`, `APRV_FL`). **PRs:** #57864, #57865. Deployed to CORE_DEV/CORE_TST.

### B3 — Error changing AFE type to require DOI then adding DOI  — **Rejected (no RCA)**
- **Bug:** #57229 (**Closed/Rejected**, "Maintenance"). Repro: create AFE under a type with no DOI rule → change the type to require DOI → open AFE and add property/DOI → error on save. **No dev comments / no root cause captured** — likely a sequencing/setup edge; not a confirmed product fix. Don't cite a build.

---

## 6. Cluster C — DOI Setup screen (DO006): calculate / approve / delete / documents

### C1 — "NRI decimal sum of 1.75", can't Calculate / approve DOI  — **Setup, not a bug**
- **Bug:** #364709 (**Closed**, iteration 21.04). The DOGWICALC process fails: *"12/31/9999 has an NRI decimal sum of 1.75"* though the on-screen NRI total is 1.00, blocking all DOI approval (must calculate before approving).
- **Root cause (Chris Rhodes / Tammy Khan):** **setup error** — a stray owner line was created with a **typo effective date (7/1/2027 instead of 7/1/2017)**, retrievable only with a far-future inquiry date, so the DOGWICALC sum over the effective window double-counted to 1.75.
- **Fix / workaround:** **clear the inquiry date on DO006** to reveal both interest lines (one starting '17, one '27), **delete the bad 7/1/2027 line**, recalculate. The summing SQL (`SELECT SUM(NRI_DEC) … DONL_DO_DETAIL … EFF_DT_TO BETWEEN EFF_DT_FROM AND EFF_DT_TO`) is in the batch process — use it to spot the overlap.

### C2 — Delete button greyed on a header-only DOI  — **Duplicate, workaround**
- **Bug:** #1713445 (CEN/Permian, **Closed/Rejected**, **duplicate of #1717454**). Linked SF case **24-00990638** (Permian upgrade).
- **Symptom:** DO006 "Delete" is disabled when a DOI Header is saved with **no owner/detail rows**, so it can't be deleted.
- **Workaround:** add an owner row and save (Delete becomes enabled), **or use the Pending DOIs widget** to delete header-only DOIs. Medium severity — **not backported to 2023.04**; real fix tracked on the MEW WI #1717454.

### C3 — Documents won't attach/save on DO006  — **Deployment/config, not QDO code**
- **Bug:** #1623182 (**Closed**, iteration 23.20). Documents added in the DO006 Documents section don't save (also seen on PD035).
- **Root cause (Ben Weis):** a **deployment issue** — the GUI exe config endpoint for the Doc Management service pointed at **port 123** while the doc-mgmt middle-tier actually listens on **9005** (`net.tcp://…:9005/DocMgmtService`). The port resolution in deployment script **`SystemManagerFramework.ps1`** (`Quorum.Deployment.Tools`, ~line 567) produced the wrong port. GUI log showed `TCP error code 10061 … :123`.
- **Fix:** correct the service port/config; re-open the Upstream GUI to pull the updated config. Cloud WI **#1623240** (myQuorum Cloud) logged for the deployment side. QA passed on DO006 and PD035 after the fix.

### C4 — Spurious QXREP_DOI_DOC popup on approve/unapprove  — **Not reproducible / env**
- **Bug:** #1462177 (**Closed**, iteration 22.14). Unexpected error popup mentioning `QXREP_DOI_DOC` when approving/unapproving on DO006 — but it **did not stop** the approve/unapprove from working. Dev could not reproduce in CORE_TST17; QA also could no longer reproduce → closed as an **environment transient** (possibly a maintenance window). No code fix.

---

## 7. Cluster D — DOI Maintenance & Interest Transfers (DOINTXWRK preview)

### D1 — "Preview DOI Interest transfer for Workspace Group — DOINTXWRK" batch fails after a transfer  — **Fixed**
- **Bug:** #1732619 (QDO, **Closed**, iteration 25.11, tag "not 2026.04 Ups"). Parent #1705971; related #1732632/#1733284/#1733969/#1732209.
- **Symptom:** after performing a transfer on the DOI Maintenance screen and clicking **Preview** on the Maintenance Group, the **DOINTXWRK** batch fails with a `ServiceContainerInitializationException` → *"No available/responsive endpoints found for service 'IQMetadataService.DO'"* (a metadata/dynamic-layout service-client endpoint-resolution failure).
- **Root cause / fix (Ben Weis):** a **missing service-container registration** for the batch/process host. The fix **added back the service container** `Quorum.QFC.ProcessService.Client.QProcessLauncherServiceClientContainer` (`Quorum.QFC.ProcessService.Client`) so the DO metadata service resolves during the preview. Additional changes folded in under #1732209.
- **Fix in:** **PR #112477** and **#112478** (commits `8be8e5a1…`, `0e312e3d…`). Verified OK on RELQA17 (MSSQL2022). No clean `IntegrationBuild` field — confirm the 2025.11-line build in `Quorum.Upstream.QDO.ReleaseNotes`; tag says **not yet in 2026.04 Upstream** at time of fix.

### D2 — "Add to Maintenance Group" button moved (top-left → bottom-right)  — **By-Design**
- **Bug:** #1665590 (**Closed/Rejected**, "not an issue"). The button relocation is **expected behavior** per requirement **#1632701** ("myQDO Web — Move 'add to maintenance group' on Transfer/Modify Setup"). Not a defect.

---

## 8. Cluster E — Converted-AFE DOI decimals & DOI-key data fixes

### E1 — Converted AFEs have NULL `AFE_DOI_DEC` (and can be re-submitted)  — **Data scripts**
- **Bugs:** #74170 (**Closed/Rejected**, handled as one-off DB script via SIR 174945) and #74171 (**Closed**, PR **#3043**, Sprint 41).
- **Symptom:** AFEs created by **conversion** have `QCTRL_AFE_HDR.AFE_DOI_DEC` = NULL; converted AFEs in **Open** status also have NULL workflow status, so the **Submit** button wrongly appears and they can be re-submitted into workflow.
- **Fix:** data UPDATE scripts (attached `74170_Walkthrough.docx`):
  - Recompute the header decimal as the **average of cost-center DOI**:
    `UPDATE QCTRL_AFE_HDR SET AFE_DOI_DEC = (AVG of QCTRL_AFE_COST_CNTR.DOI_DEC grouped by AFE_NO/BUS_UNIT_CD/OPER_BUS_SEG_CD) WHERE AFE_DOI_DEC IS NULL`.
  - Stamp converted Open AFEs as already-approved so the Submit button is removed:
    `UPDATE QCTRL_AFE_HDR SET WF_STATUS_CD='Approved', WF_INSTANCE_ID='CONVERSION' WHERE WF_STATUS_CD IS NULL AND WF_INSTANCE_ID IS NULL AND AFE_STAT_CD='O'`.
  - #74171 also includes a **code change (PR #3043)** to suppress the Submit button for these. #74170 was the pure data correction (tabled to a DB issue, no product change).

### E2 — Voucher DOI Key description fields remain after AFE is cleared  — **Fixed**
- **Bug:** #65264 (**Closed/Split**, Sprint 36, PR **#1456**). On the voucher screen, the **DOI Key description fields don't clear when the AFE is cleared**. Code fix delivered (walkthrough `305248_Walkthrough v17.docx`); minimal dev discussion.

---

## 9. Cluster F — DOI query performance & picklist duplicates

### F1 — DOI picklist shows duplicate property rows (AFE committed-costs, web)  — **Fixed**
- **Bug:** #1687634 (**Closed**, iteration 24.21, tag "Not 2025.04 Ups"). PRs **#101197/#101200/#101598/#101599**.
- **Symptom:** in **AFE transactional code committed costs**, the **DOI picklist** shows duplicate property detail rows.
- **Root cause / fix:** the picklist must be filtered by **both Business Unit and AFE No.** to return **distinct** property records; the fix returns distinct records under that filter. **By-design caveat:** filtering by **BU only** still returns multiple rows (expected — the picklist needs BU+AFE). Verified OK on RELQA once BU+AFE supplied.

### F2 — `Sel_DoiDecimals` query slow, high disk I/O  — **Tabled (perf)**
- **Bug:** #106834 (Camino, **Closed/Rejected**, tag "FinancialsPerformance"). The `Sel_DoiDecimals` query runs hundreds of times/day, ~85s avg; DBA Tuning Advisor proposed 3 indexes + stats (claimed 99% gain).
- **Root cause (Ben Weis):** the real culprit is **bloated interface tables**, not missing indexes: `QSTAG_CORE_INTFC_IMP_QCA` (~66.5M rows) and `SEXTN_CORE_INTFC_JIB` (~24.5M). The SQL originates in **`QPDllCostAcctgJIB\QSQL_JIBModuleIntfc.cpp`** (multiple registered SQLs named `Sel_DoiDecimals`).
- **Resolution:** **tabled** — recommend running the **archive/purge jobs** on the interface tables (est. ~33% reduction) before applying indexes. No product fix shipped.

---

## 10. Overlap / Not-QDO (matched only on "transfer")

These were pulled by the broad "transfer" term and are **not Division Order**; classify elsewhere:

| Bug | Title | Actually is | State / Fix |
|---|---|---|---|
| #68244 | Material Transfer Imports Duplicating when Account shared across Inventory Types | QCFS Inventory / Material Transfer | Closed/Split, PR #1811 |
| #65870 | New Accounting Date Validation for JE Billing/Transfer **Selection** screens | QCA Journal Entry transfer | Closed/Rejected; PRs #1728/#1729, changeset 212126 (v16) |
| #71989 | Misc. LH Issues For Transfers, Billings (JE auto-pick / check-all) | QCA JE Billing/Transfer/Cost screens | Closed, PRs #3047/#3049/#3565 (v16) |
| #78671 | RPT_JEA001 Batch Audit Report no data when transfer dest = allocation group | QCA JE-transfer reporting | Closed, PR #3966, deployed 2018.09 |
| #1592537 | EQC EnergyLink **SFTP** Transfer Failing (msg type 93) | Platform SFTP framework `QSFTPOperation.cs` (doesn't handle `SSH_MSG_CHANNEL_WINDOW_ADJUST`) | Closed/Rejected ("Recommend Close") |
| #57151 | (MERGE) Update GST Journal Entry Auto Creation to include DOI info | QCA GST/JE (DOI-adjacent) | Closed/Rejected (Merge) |
| #57269 | DOI in AP GL code block not pulling correct DOI | QCFS code-block (DOI-adjacent) | Closed/Rejected |
| #157216 | Web QCA JE Transfer Selection — busy GIF spins on To Allocation Group | QCA JE-transfer web perf | Closed/Rejected |
| #364712 | QFC Upstream — Division Order Analyst Menu not updated to application names | QDO menu/branding cosmetic | Closed |

---

## 11. Fix-Version Matrix

| Bug | Symptom (short) | State / Reason | Fix carrier (PR / changeset / iteration) | Linked SF case |
|---|---|---|---|---|
| **#1732619** | DOINTXWRK Preview transfer batch fails (missing service container) | Closed | **PR #112477/#112478**; iter 25.11 → verify 2025.11 build (tag *not 2026.04 Ups*) | — |
| **#1371768** | AFE XML import "must have a DOI" (legacy validations) | Closed | **PR #57928/#57954/#69430/#72351**; `Quorum.Upstream.QCA.ClassicBatch`; iter 21.18 | — (ENC/Encino, internal) |
| **#1382019** | JB020 "not an effective JIB DOI" (date-format parse) | Closed | **PR #57864/#57865**; `Quorum.Upstream.QCA.ClassicGUI`; iter 21.18 / 2021.10 | — |
| **#1687634** | DOI picklist duplicates (AFE committed costs) | Closed | **PR #101197/#101200/#101598/#101599**; iter 24.21 / 2024.10 | — |
| **#216752/#216904/#217341** | AP voucher DOI eff-date message missing | Closed | feature WI #210356; iter 20.15 | — |
| **#1590711** | Dup unapproved-DOI messages GL025/AP055 | Closed (Dup) | fix under **#1588161**; `CustomCodeBlockUpstreamValidator.cs` | — |
| **#1623182** | DO006 documents won't save | Closed | deployment fix (`SystemManagerFramework.ps1` port); cloud WI #1623240; iter 23.20 | — |
| **#74171** | Converted AFE NULL AFE_DOI_DEC + Submit | Closed | **PR #3043** + data scripts; Sprint 41 | — |
| **#74170** | Converted AFE NULL AFE_DOI_DEC | Rejected | data UPDATE script only (SIR 174945) | — |
| **#65264** | Voucher DOI Key desc fields not cleared | Closed (Split) | **PR #1456**; Sprint 36 | — |
| **#1609157** | Reverse voucher "Invalid DOI Key Combination" | **Rejected (By-Design)** | none — DOI-key data fix / GL025 reclass | **22-00854618** |
| **#1713445** | Can't delete header-only DOI (DO006) | Rejected (Dup) | fix on **#1717454**; not backported to 2023.04 | **24-00990638** |
| **#1665590** | "Add to Maintenance Group" button moved | Rejected (By-Design) | per req **#1632701** | — |
| **#364709** | DO006 "NRI decimal sum 1.75", can't calc | Closed | none (setup: delete future-dated owner line) | — |
| **#1462177** | QXREP_DOI_DOC popup on approve | Closed | none (not reproducible / env) | — |
| **#1724273** | JB390 CTF-Failure side / unapproved DOI | Closed/Verified | none (invalid test case — direct bill → JBTRN_CTF by design) | — |
| **#57229** | Error after AFE type → require DOI | Rejected | none captured | — |
| **#106834** | `Sel_DoiDecimals` slow | Rejected (tabled) | none — archive/purge interface tables | — (Camino) |

> No bug in this set carried a populated `Microsoft.VSTS.Build.IntegrationBuild`; "fixed-in-build" is inferred from iteration/tags and must be confirmed in **`Quorum.Upstream.QDO.ReleaseNotes`** (or QCA/QCFS ReleaseNotes for the AFE/voucher ones) and the linked PR's target branch.

---

## 12. Diagnostic pointers

```sql
-- 1) The DOI key & effectiveness (DO006). PROP_NO+DO_TYPE_CD+DO_MAJ_PROD_CD+TIER+OPER_BUS_SEG_CD is the key.
SELECT A.PROP_NO, A.DO_TYPE_CD, A.DO_MAJ_PROD_CD, A.TIER, A.OPER_BUS_SEG_CD,
       A.JIB_ACTIVE_CD, A.APRV_FL,
       MIN(B.EFF_DT_FROM) EFF_FROM, MAX(B.EFF_DT_TO) EFF_TO
FROM   DONL_DO_HDR A
JOIN   DONL_DO_DETAIL B
  ON   A.PROP_NO=B.PROP_NO AND A.DO_TYPE_CD=B.DO_TYPE_CD AND A.DO_MAJ_PROD_CD=B.DO_MAJ_PROD_CD
   AND A.TIER=B.TIER AND A.OPER_BUS_SEG_CD=B.OPER_BUS_SEG_CD
WHERE  A.PROP_NO='<PROP>'
GROUP BY A.PROP_NO,A.DO_TYPE_CD,A.DO_MAJ_PROD_CD,A.TIER,A.OPER_BUS_SEG_CD,A.JIB_ACTIVE_CD,A.APRV_FL;

-- 2) NRI decimal sum per effective window (the "sum = 1.75" approval block, #364709).
--    A stray future-dated owner line (typo year) inflates the sum.
SELECT EFF_DT_FROM, EFF_DT_TO, SUM(NRI_DEC) NRI_SUM
FROM   DONL_DO_DETAIL
WHERE  PROP_NO='<PROP>' AND DO_TYPE_CD='<TYPE>' AND TIER=<TIER>
GROUP  BY EFF_DT_FROM, EFF_DT_TO ORDER BY EFF_DT_FROM;

-- 3) Converted AFEs with NULL header decimal / NULL workflow (#74170/#74171).
SELECT AFE_NO, BUS_UNIT_CD, OPER_BUS_SEG_CD, AFE_DOI_DEC, AFE_STAT_CD, WF_STATUS_CD, WF_INSTANCE_ID
FROM   QCTRL_AFE_HDR
WHERE  AFE_DOI_DEC IS NULL OR (WF_STATUS_CD IS NULL AND WF_INSTANCE_ID IS NULL AND AFE_STAT_CD='O');

-- 4) AFE rule: does this AFE actually require a DOI? (#1371768 — DOI_RULE_ID=2 means required)
SELECT AFE_RULE_ID, DOI_RULE_ID, * FROM QCODE_AFE_RULE;

-- 5) Interface-table bloat behind slow Sel_DoiDecimals (#106834) — candidates for archive/purge.
SELECT COUNT(*) FROM QSTAG_CORE_INTFC_IMP_QCA;
SELECT COUNT(*) FROM SEXTN_CORE_INTFC_JIB;

-- 6) Trace the SQL a failing batch ran (Ben Weis's technique on #1371768):
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE
WHERE  PROCESS_QUEUE_ID=<PQID> AND REGISTERED_SQL_NAME IN ('m_QcaAFE_INS_AFEHDR','m_QcaAFE_UPD_ValidDOI')
ORDER BY SEQ_NO;
-- Code-block validation messages (dup-message diagnosis, #1590711): QARCH_PROCESS_MSG_LOG for the PQID.
```
*Tables/columns are from case repro text and dev comments — verify against the client schema (per-client `<CLIENT>.Upstream.QDO.Database` / `<CLIENT>.QDOD.Database`) before scripting; always verify-SELECT inside a transaction.*

---

## 13. Key code & repos

**Core QDO repos** (`Quorum.Upstream.QDO.*`): `ClassicGUI`, `ClassicBatch`, `Batch`, `Web`, `Application.Web/MiddleTier/APIHost`, `Database`, **`DivisionOrder`**, `Events`, `DocumentManagement.EventHandlers`, `ReleaseNotes`. Legacy family `Quorum.QDOD.*` (`ClassicGUI/ClassicBatch/Database/Metadata/Reports/Web/Batch/ReleaseNotes`). **Per-client overrides** are abundant — `<CLIENT>.Upstream.QDO.Database` (AEL, APA, BKV, CEN, CNX, CRC, ENC, EQC, MEW, MRO, PER, PRM…) and the older `<CLIENT>.QDOD.*` (DCP, EMP, ENT, ETP, HVK, IAC, MGP, MKW, ONM, QSM…). **Always check the client repo/schema first.**

**DOI logic also lives in QCA & QCFS** — DOI validation on AFEs/JIB and AP/GL vouchers is in the cost-accounting and financials repos:

| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `QPSQcaAFEExternalImportValidate.cpp` (`ValidateImportData()`) + SQLs `m_QcaAFE_UPD_ValidDOI`, `m_QcaAFE_UPD_AFEValidateCCOpNonOp`, `m_QcaAFE_INS_AFEHDR`, `m_QcaAFE_DEL_ExistingAFE*` | `Quorum.Upstream.QCA.ClassicBatch` (branch `feature/1371768_AFE_ImportValidations`) | B1 AFE import |
| `QBusinessRulePropEffDOI.cs` (`IsDOIEffective`) | `Quorum.Upstream.QCA.ClassicGUI\Quorum.QCA.Shared\BusinessRules` | B2 JB020 eff-DOI |
| `CustomCodeBlockUpstreamValidator.cs` | Upstream code-block validation (QCFS/QCA batch) | A3 dup messages |
| `DOGWICALC` (DOI calc batch) + NRI-sum SQL over `DONL_DO_HDR`/`DONL_DO_DETAIL` | QDO ClassicBatch | C1 calc/approve |
| `DOINTXWRK` preview + service container `Quorum.QFC.ProcessService.Client.QProcessLauncherServiceClientContainer` | QDO process host / `Quorum.QFC.ProcessService.Client` | D1 transfer preview |
| `QSQL_JIBModuleIntfc.cpp` (`Sel_DoiDecimals`) in `QPDllCostAcctgJIB` | QCA JIB module | F2 perf |
| Doc-Mgmt service port resolution `SystemManagerFramework.ps1` (~line 567) | `Quorum.Deployment.Tools` | C3 documents |
| Tables: `DONL_DO_HDR`, `DONL_DO_DETAIL`, `QCTRL_AFE_HDR`, `QCTRL_AFE_COST_CNTR`, `QCODE_AFE_RULE`, `QCODE_JE_ACCOUNT_XREF`, `QCODE_INVEN_TYPE_ACCT`, `JBONL_REBILL_REQUEST`, `QARCH_PROCESS_MSG_LOG`, `QARCH_QFCBATCH_SQL_TRACE`, `QSTAG_CORE_INTFC_IMP_QCA`, `SEXTN_CORE_INTFC_JIB`, `JBTRN_CTF` | — | all |

---

## 14. Escalation guidance

**Confirm it's actually a defect (not setup/data/by-design) first** — over a third of this set closed Rejected/By-Design/Duplicate:
- **Reverse/reclass DOI-key failures** (#1609157) = setup drift; fix the historical DOI key or reclass via GL025. **Not** an engineering bug.
- **DO006 calc "NRI sum ≠ expected"** (#364709) = a bad owner line (often a year typo); clear inquiry date and delete it.
- **Delete-greyed header-only DOI** (#1713445) = add an owner / use Pending DOIs widget.
- **JB390 CTF-Failure vs CTF for an unapproved DOI** (#1724273) = by design — direct bills with only cost-center/owner (no full DO key) write to `JBTRN_CTF`; DO approval is irrelevant without a full key.
- **Button moved / menu names** (#1665590, #364712) = cosmetic/by-design per requirement.
- **DO006 documents won't save** (#1623182) = a **deployment** problem (service port), route to Cloud Ops, not QDO engineering.

**Route to Engineering (real code/SQL defect)** with **PQID + screen/process + exact error + client + property/AFE + repro**:
- AFE-import DOI validation (#1371768, `Quorum.Upstream.QCA.ClassicBatch`), JB020 eff-DOI date-format (#1382019, `Quorum.Upstream.QCA.ClassicGUI`), DOI picklist duplicates (#1687634, web), DOINTXWRK preview service-container (#1732619, QDO), duplicate code-block messages (#1588161).
- Converted-AFE decimals (#74170/#74171) → **data scripts** in the client `Database` repo (recompute `AFE_DOI_DEC`, fix WF status); verify-SELECT in a transaction.
- **Always confirm fix availability in `Quorum.Upstream.QDO.ReleaseNotes`** (or QCA/QCFS ReleaseNotes) and the linked PR's target branch — and **check the per-client repo** (`<CLIENT>.Upstream.QDO.*` / `<CLIENT>.QDOD.*`), since the client build may lag core.

---

*Skill created 2026-06-14. Source: ADO Bugs under `QuorumSoftware\Engineering\Financials` (title-filtered for DOI / division order / transfer / ownership / suspend / conveyance) — 34 matched, 24 deep-read. Notable WIs: #1732619, #1371768, #1382019, #1687634, #1609157(22-00854618), #1713445(24-00990638), #1590711(→#1588161), #1623182, #74170/#74171, #65264, #364709. Companion: SKILL_ADO_* QCA/QCFS skills; REPO_REFERENCE / REPO_INVENTORY for the Upstream repo map.*
