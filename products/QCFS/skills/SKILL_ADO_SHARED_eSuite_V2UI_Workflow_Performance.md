# SKILL: Upstream SHARED — eSuite / V2UI / Workflow / Performance (ADO defect-fix reference)

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps `QuorumSoftware\Engineering\Financials` Bugs (Closed/Resolved)
**Scope (SHARED area):** The cross-product platform layer shared by QRA/QCA/QCFS/QDO — the **eSuite shell** (Classic + Web/myQuorum), the **V2UI** Kendo-based Web framework, the **approval Workflow engine** (POSTWKFL / PSTWKSPLT scheduled processes, desk routing, workflow events, AFE/voucher status transitions), and **Performance** (load-test regressions, validation/inbox/dashboard slowness, DB-index fixes). These touch QCA AFE, QCFS AP, and QDO screens but the *root cause* lives in shared infra (QFC platform, QPEC middle tier, ESuite Web tier, broker/process-launcher services, Kendo).

> **Use When:** a case spans more than one product, or names the platform: POSTWKFL/PSTWKSPLT failing or slow, "Workflow does not exist", workflow events not firing, AFE/voucher status stuck after approve, dashboard/inbox/validation slowness, "frowny face"/console error on a Web screen, Kendo-upgrade UI regressions, XSS error pop-ups, login/password-reset, ORGCOSTGEN launch failures, impersonation errors on the scheduler. For product-specific calc/data bugs, use the QRA/QCA/QCFS/QDO skills instead.

> **Evidence base:** 291 SHARED-keyword bugs matched by WIQL (title CONTAINS eSuite/V2UI/workflow/POSTWKFL/PSTWKSPLT/performance/deadlock/PII/login/attachment/plugin/metadata/FINANVALD, all Closed/Resolved under Financials); 285 fields-skimmed; **47 deep-read** for description + repro + relations (PRs/commits/builds) + dev root-cause comments. Every root-cause claim below cites a real ADO Bug #. Big caveats up front: (1) the matched set skews heavily to **QCA AFE Web UI cosmetic bugs** (Kendo/V2UI) — most are not "shared infra" defects; (2) the **`Microsoft.VSTS.Build.IntegrationBuild` field is empty on every bug in this area** — Quorum does not populate it, so "fixed-in-build" below is derived from **IterationPath** (e.g. `25.15` ≈ release 17.25.15) + tags (`2022.10 QA`, `Release Note Reviewed`) + PR target branch (`hotfix/17.25.15`). Treat versions as approximate; confirm in `Quorum.Upstream.*.ReleaseNotes` before quoting to a client.

---

## TABLE OF CONTENTS
1. [Quick Triage](#1-quick-triage)
2. [Decision Tree](#2-decision-tree)
3. [Cluster A — POSTWKFL / PSTWKSPLT scheduled-process failures](#3-cluster-a)
4. [Cluster B — Workflow engine: "does not exist", events, status stuck](#4-cluster-b)
5. [Cluster C — Performance: load-test regressions vs real defects](#5-cluster-c)
6. [Cluster D — V2UI / eSuite Web framework (frowny face, console, Kendo)](#6-cluster-d)
7. [Cluster E — XSS hardening & login/password-reset](#7-cluster-e)
8. [Cluster F — Attachment / document handling](#8-cluster-f)
9. [Cluster G — Process-launch / impersonation / metadata-sysgen plumbing](#9-cluster-g)
10. [Fix-Version Matrix](#10-fix-version-matrix)
11. [Diagnostic Pointers](#11-diagnostic-pointers)
12. [Key Code, Processes & Repos](#12-key-code-processes--repos)
13. [Escalation Guidance](#13-escalation-guidance)

---

## 1. Quick Triage

| Symptom (what the user/QA reports) | Likely cluster | First check |
|---|---|---|
| POSTWKFL "Stops Processing on Error" / "unable to establish a connection with any endpoint" on the **scheduler** (runs fine when launched manually) | A | DEBUG mode on the scheduled definition; impersonation perms (§3) |
| POSTWKFL "Execution Timeout Expired" / stuck for hours at one client | A | a **blocking DB session** (e.g. VENDOR-table trigger) — kill it; then index/cache (§3) |
| `PSTWKSPLT` process fails on upgrade | A | regression on the split process; usually env/config, several Rejected (§3) |
| "Workflow: Instance ID '<id>' is no longer available or does not exist" on Approve | B | desk **Notice Delivery type = Widget / Email & Widget** — only EMAIL is supported (§4, #1552303) |
| AFE/voucher stays PENDING / "Post Pending" after Approve; workflow status not "Approved" | B | regression in status write-back; check build (§4, #1583340, #1439453) |
| Workflow events (WF_*) not triggering; no event logged | B | event-detector setup / desk config (§4 — several Rejected as config) |
| Dashboard / View Full Inbox / GetCodeTable "X secs slower in 20YY.ZZ" load test | C | mostly **Rejected** perf-lab noise (WEB restarts, not reproduced) — NOT a client defect (§5) |
| Real slowness: AP055 **Validate** runs hours on a huge batch; AFE **Search by Cost Center** 40s+ | C | repeated un-cached SQL (XREF_COSTCNTR_ACCTATTRIB) — real fix exists (§5, #1721402, #1566911) |
| "Frowny face" page / console 500 instead of a screen or report | D | usually env/data/regression; reproduce in CORE_SUP before escalating (§6) |
| Kendo-upgrade UI regressions (alignment, scrollbars, filters, dirty-mode) after 2024.10 | D | cosmetic Web regressions, fixed in 25.xx batch (§6) |
| XSS script in notes/attachment shows an **error pop-up / console error** | E | input-sanitization hardening; some Rejected (env not on latest deploy) (§7) |
| Password reset "request received" even with **blank email** | E | validation gap on login; Rejected (low pri) (§7) |
| Can delete an AFE attachment after submit-to-workflow despite a warning | F | lock/validation gap; Rejected as same behavior in CORE_SUP (§8, #1439683) |
| QDO Cost Center save → "Upstream Process ORGCOSTGEN failed" pop-up | G | ESuite launched the process via MT `IQGlobalProcessLauncherService`; moved to Web tier (§9, #1704488) |

---

## 2. Decision Tree

```
SHARED / platform case
│
├─ A scheduled/batch WORKFLOW process? (POSTWKFL / PSTWKSPLT)
│   ├─ Fails ONLY on the scheduler, fine when run manually  → §3 DEBUG-mode / impersonation (#104443,#105931,#106219)
│   ├─ Timeout / stuck for hours at one client              → §3 find the BLOCKING session first (#1698180), then index/cache
│   ├─ "completes with errors" re: a QXREF_*/sysgen table   → §3 missing metadata sysgen on wrong layer (#1445857)
│   └─ PSTWKSPLT fails on upgrade                            → §3 (mostly Rejected/env)
│
├─ Workflow OUTPUT wrong (engine, not a batch crash)?
│   ├─ "Instance ID … does not exist" on Approve            → §4 desk Notice Delivery = Widget (#1552303) — only EMAIL supported
│   ├─ Status stuck PENDING / Post-Pending after Approve    → §4 status write-back regression (#1583340,#1439453,#162814)
│   ├─ No Approve option after Submit / blank inbox         → §4 env/security-user inactive (#1773689)
│   ├─ Duplicate / cleared History entries                  → §4 (#1786355 dup Reject rows; #1645172 cancel clears = by design)
│   └─ WF_* events not firing                               → §4 event-detector/desk config (mostly Rejected)
│
├─ PERFORMANCE?
│   ├─ "X secs slower in 20YY.ZZ" load/reliability test     → §5 LIKELY perf-lab noise → most are REJECTED, not client defects
│   └─ Reproducible client slowness on a real action        → §5 real fix (cost-center XREF cache #1721402, AFE search #1566911, POSTWKFL index #72944/#1550460)
│
├─ Web SCREEN broken (frowny face / console / Kendo / cosmetic)? → §6  (reproduce in CORE_SUP; check build)
├─ XSS pop-up / login / password reset?                          → §7
├─ Attachment / document?                                        → §8
└─ Process-launch / impersonation / metadata-sysgen plumbing?    → §9
```

---

## 3. Cluster A — POSTWKFL / PSTWKSPLT scheduled-process failures
*(8+ bugs; the core "shared workflow batch" signature)*

**POSTWKFL** = the Post-Workflow scheduled process (QP073 launcher) that picks up final-approved AFEs/vouchers and posts them; **PSTWKSPLT** = the "Post Workflow Splitter" variant. The recurring theme: the process **runs fine when a user launches it manually but fails when run by the scheduler**, or **hangs for hours at one client**.

### A1 — Scheduler-only failure: DEBUG mode + impersonation (the classic)
- **Symptom (#104443):** "Post Workflow scheduled process, POSTWKFL, stops processing on error — *unable to establish a connection with any endpoint*. Runs fine if a user manually runs it." Example PQID 6830304.
- **Root cause (dev comments):** **DEBUG mode turned ON for the POSTWKFL scheduled definition** makes the UPS middle tier (MT) unresponsive after a period — it stops communicating with any endpoint. Confirmed by Jimmy Bidwell: "Whenever the scheduled definition has Debug turned off, it appears to complete fine."
- **Fix / workaround:** **Turn DEBUG mode OFF** on the scheduled definition (immediate unblock — Brian Lee: "resolved after Debug Mode is turned off"). Broker-service handling of `QOperationContext` was addressed in related **#106923**. Note: even with debug off it could still regress in one PRD, so the broker-service work was the durable fix.
- **Related impersonation variant (#105931):** scheduler POSTWKFL throws *"Original Authenticated User 'QPECUSER_DEV01' does not contain the correct permissions to impersonate Security User 'QPEC_SCHEDULER' : impersonationMode 'CompleteImpersonation'"*. Fix delivered via **`Update SEC Group 9001.sql`** (grant the scheduler user impersonation perms). **#106219** (QCFS scheduled processes POSTWKFL/QCFSIMPCYC) is the same impersonation family (Rejected — handled under 105931/104443). Sister item #1773689: blank inbox / no Approve was a **deactivated QPEC security user** — `update QARCH_SEC_USER set INACTIVE_IND=0 where SEC_USER_ID='QPECUSER_DEV02'`.

### A2 — Client hang / timeout: a blocking DB session
- **Symptom (#1698180, SF 24-00989239, APH):** POSTWKFL failing since 11/13 with *"Execution Timeout Expired … statement has been terminated."* Could not reproduce in lower env.
- **Root cause (Ben Weis):** it **was not really POSTWKFL** — a **blocking DB session** (DBAs confirmed it was blocked by the **VENDOR table trigger**, likely a user left a BA005 screen open editing payment type). Once the blocking session was killed, normal processing resumed.
- **Fix:** kill the blocking session; the durable follow-up was **VENDOR caching / QDC trigger cleanup** handled under **#1698965**. *Closed as not-a-product-defect.*
- **Triage rule:** for a single-client POSTWKFL timeout that you cannot reproduce, **look for a blocking/idle session first** (BA/VENDOR edits) before chasing code.

### A3 — POSTWKFL performance / DB index
- **#72944 (SF 304058):** "POSTWKFL timeout resolved with DB index" — a missing index caused the timeout; adding the index fixed it (Closed/Validation Test Passed). Old (Sprint 40) but the pattern recurs.
- **#1550460 (MEW):** post-workflow runtime shot to 20 min after a hotfix; the hot SQL was in **`UpstreamJournalEntryWorkflow.cs`** (`Quorum.Upstream.QCFS.Web`). Proposed index `CREATE NONCLUSTERED INDEX BATCHJOURNALENTRYLINE_IDBATJE ON BATCHJOURNALENTRYLINE (IDBATJE, IDACCOUNT)` gave MEW a big speedup. **Closed/Rejected as a standalone WI** — a similar (not identical) index was already added under **#1643630** during post-workflow split testing; this came to core eng as a review/inclusion, not a new fix. **Do not invent a build** — confirm whether #1643630's index is in the client build.

### A4 — "completes with errors" tied to a metadata sysgen
- **#1445857 (QCFS Classic QP073):** POSTWKFL completes with errors re: **`QXREF_AFE_VALID_POST_STATUS`**. Root cause (Ben Weis): **missing sysgens were defined on the wrong (ENGS) metadata layer** instead of a UPS/QCFS-owned layer, so the QCFS connection couldn't see them. Fix: moved the 9 sysgen entries from the ENGS layer to the correct product layer and corrected the DB snapshot (see `1445857_UpdatedSysgenLayers.xlsx`). Fixed-in iteration **22.06** (tags `2022.04 QA`).

### A5 — POSTWKFL data-driven failures (route to product)
- **#70246** voucher with an Approval Reference fails to submit to **ATP** workflow on post (had to submit manually) — Closed/Duplicate of the ATP-launch family (#115381).
- **#1379243 (MAC):** a **$0 netting line** caused a POSTWKFL error in **AR076** ("applied amount + current amount must approach zero"). Root cause traced (Oleksii P.) to one BatchInvoice detail with a $0 amount against a $0.19 open item, firing the FINANVALD payment-application validation. **Closed/Duplicate of #184253** (a QRA/revenue issue — QCFSEXPORT sends $0-netted invoices back to QCFS). Workaround: temporarily enable the AR044 "allow non-zero" config (flip on → post → flip off) — explicitly called out as **not acceptable long-term**. This is a revenue defect, not a workflow defect.

**Fix recipe (Cluster A):** get **PQID + exact error**. (1) Scheduler-only + "no endpoint" → turn **DEBUG off** on the scheduled def, verify scheduler impersonation perms. (2) Single-client timeout you can't repro → hunt a **blocking session** (DBA). (3) Slow but completes → DB **index** (#72944/#1550460/#1643630). (4) "completes with errors re: QXREF_*" → **metadata sysgen on wrong layer** (#1445857). (5) $0/validation error in AR076 → revenue side (#184253).

---

## 4. Cluster B — Workflow engine: "does not exist", events, status stuck
*(Approval routing / desk / status write-back; QCA AFE + QCFS voucher)*

### B1 — "Workflow Instance does not exist" on Approve (the headline defect)
- **Symptom (#1552303, 2022.10):** approving an AFE / voucher throws *"Workflow: Instance ID '<ID>' is no longer available or does not exist"* — **only when the approval desk's Notice Delivery type = "Email & Widget" (or "Widget")**. AFE does not get approved.
- **Root cause (Ben Weis):** the **`QARCH_WF_CODE_DELIVERY_TYPE`** code table (managed in the **QFC** core-metadata repo) had the **Widget / Email & Widget** values present again, though **only EMAIL is supported**. A 2019 Core DB ticket had removed all but EMAIL (commit `413711ad…`); the values came back via the QFC snapshot.
- **Fix:** re-apply the Core DB / QFC script that updates the FK `QARCH_WF_DESK` rows and **deletes the invalid values from `QARCH_WF_CODE_DELIVERY_TYPE`** so only EMAIL remains. Fixed-in iteration **22.23** (tags `2022.10 GA QA`). Platform ticket **#1554243** tracks the QFC side.
- **Triage rule:** any "workflow instance does not exist" on approve → **check the desk's Notice Delivery type**; if it's Widget/Email&Widget, that's the cause — set it to EMAIL and clean the code table.

### B2 — AFE/voucher status stuck after approve
- **#1583340 (2023.04 regression):** after Approve, AFE status stays **PEN/PENDING** (not OPEN) and workflow status not "Approved." Tagged `Not in 2024.04 - Ups` (a 2023.04-only regression). Fixed-in iteration **23.05**.
- **#1439453 (SRCU, Maintenance):** same symptom (inbox preview shows approved, status stays Pending even after Retrieve/refresh). **Closed/Rejected** — could not be reproduced as a standalone defect / overlapped with the 23.05 fix.
- **#162814 (QCFS Web):** AP voucher stays in **"Post Pending"** — same status-write-back family on the AP side.
- **Pattern:** these are **status write-back regressions** in the Web approval path, clustered around the 2023.04 release; if a client reports it, confirm they are not on a 2023.04-era build and that #1583340's fix is included.

### B3 — Workflow events / desk plumbing
- **#70256:** WF_RTERTRN / WF_COMMENT / WF_FNLRJCT / WF_DLGT events not triggering in TST17 — **Rejected** (event-detector/desk config in that env, not a code bug).
- **#63692:** a single user assigned to **multiple desks** caused a **stack overflow getting edit authorities** → workflow instance aborted with no logged error. Old (2018.05) but a real engine fix (PR #1224) — note if a client reports workflow "aborting silently" with multi-desk users.
- **#1786355 (2026.04):** **duplicate entries in the History tab for Reject** — real fix (PRs #124588/#124612), iteration **26.06**. **#1645172** (history cleared after Cancel Workflow) was Closed/**Rejected** — same behavior in CORE_SUP/APH, i.e. **by design**.
- **#1758402 (26.02):** AFE Inbox query can build an **invalid filter with an empty `IN ()` clause** for additional properties → MT exception → no results. Real fix (PRs #121359 etc.), iteration **26.02**. Related #1710580 (no records in AFE Inbox widget).
- **#1773689 (MNT, 26.01):** after Submit, no Approve option + blank inbox — was a **deactivated QPEC security user** in that env (fix = reactivate, see A1), not an engine bug.

---

## 5. Cluster C — Performance: load-test regressions vs real defects
**The single most important caveat in this skill:** the bulk of "performance" bugs in this area are **internal load-test (perf-lab) regression reports**, and **most are Closed as Rejected** — the regression was not reproduced in the next test run, or it was traced to the WEB tier being **restarted mid-test**. Do **not** quote these to a client as known product defects.

### C1 — Perf-lab regressions (REJECTED — not client defects)
All run the same scripted load test against `qddperweb5x.qdev.net …PRF_GLE_PRU_R1_HD_PRF17_ESuite` (Login → AP/AFE dashboards → open/copy/save → full inboxes):
- **#1725894** Dashboard +127s in 2025.04, **#1757514** Dashboard +58s in 2025.10, **#1725889** "across the board 20+ users 2025.04", **#1645818** View AFE Full Inbox +10.5s in 2024.04, **#1588989** GetCodeTable up to 300s in 2023.04, **#1633143** GetRegisteredWidgets up to 213s, **#1734942** "sudden CPU/memory drop + response spike" — all **Closed/Rejected** ("don't see it in the latest run" / "WEB was restarted at least 2 times" / closed per latest results).
- For #1588989, Ben Weis traced the slow GetCodeTable calls to small code tables (UVW_GCDE_BU_SECURITY=12 rows, QCODE_AFE_STAT=13 rows) — "nothing special… most likely a resource or blocking issue," i.e. **lab contention, not a query defect**.

### C2 — Real, reproducible performance defects (FIXED)
- **#1721402 (MIT, Cost Center / Account Validation):** AP055 **Validate** of a 420k-line non-operated JIB voucher ran **4+ hours**. Root cause: `SELECT 1 FROM XREF_COSTCNTR_ACCTATTRIB …` fired **~70k times** (MIT had 389k XREF rows; every other client has ~0), plus repeated `QXREF_AFE_VALID_POST_STATUS` per AFE row. **Fix:** **cache** the account/cost-center XREF and the post-status XREF (query once per account/cost-center). 12k-record batch went **22 min → 2 min**. PRs #109328/#109334/#109404/#109438 in **`Quorum.Upstream.QCFS.Web`**; target `hotfix/17.25.15`; per Ben Weis **checked into 2023.04, 2024.10, Develop**. Caveat: caching is tailored to the **voucher** batch type; other batch types (GL/AR) may still issue per-line queries.
- **#1566911 (Seneca/SRCU, SF 22-00868517):** AFE Search widget by **Cost Center** takes 40s+ (and could throw a 240s `QReaderWriterLockTimeoutException`). **Fix:** "Updated AFE Search Cost Center Performance" PR #114500 in **`Quorum.Upstream.QCA.Web`** → `develop`, completed 2025-07-22, iteration **25.15** (tags `QA Approved TST`, `Robot RN 2026.04`). Long-lived (raised 2020.09, fixed 2025).
- **#72944 / #1550460:** POSTWKFL DB-index fixes — see §3-A3.

**Triage rule:** "performance" + a `qddperweb5x …PRF…` URL + a "20YY.ZZ slower than 20YY.XX" title = **internal perf regression**, usually Rejected → not a client deliverable. A **client** perf case naming a real action (Validate a big batch, AFE Search by CC) with a trace showing one SQL fired thousands of times = a real, cacheable defect (#1721402, #1566911).

---

## 6. Cluster D — V2UI / eSuite Web framework (frowny face, console, Kendo)
*(Largest matched cluster by count — mostly cosmetic QCA AFE Web UI; low L4 value but high volume)*

- **"Frowny face" page** loads instead of a screen/report (#177217 Cover Sheet, #185711, #234205 Security User Setup, #155166 Contract Meter List, #1395957 AFE Creation): the generic eSuite Web error page. Usually **env/data/regression-specific** (e.g. #177217 reproduced in TST17 but not SUP17 for one AFE number). **Reproduce in CORE_SUP before escalating**; many are Rejected or fixed in the noted release.
- **Kendo upgrade regressions (2024.10 → fixed 25.04/25.05):** a large batch of cosmetic Web bugs after the Kendo control upgrade — missing scrollbars (#1711725), label/checkbox misalignment (#1711752), filter-icon/column-cut, dirty-mode, dimmed fields (#1711728-#1711732). All tagged `Platform-2024.10`/`UX-2024.10`, fixed across iteration **25.04/25.05**. If a client on 2024.10 reports AFE-screen cosmetic glitches, point to the 2025.x Kendo-fix batch.
- **eSuite Classic framework:** #868480 STP020 "Object reference not set to an instance of an object" on Retrieve Instance OK; #1374686 QP070 multiple-messages window; #1455953 missing "Interactive Reports" tree menu (blocked Exago reports), fixed in Product Development. These are platform/metadata fixes, not product logic.
- **Bulk AFE Header (v2UI) screen (#1574xxx, 23.xx):** a whole feature's worth of V2UI-standards bugs (pagination, scrollbars, dirty-mode, filters, notes overlap, delete). Cosmetic/behavioral polish on the new grid; fixed across 23.xx.

**These rarely need L4 root-cause work** — they're QA-found UI regressions fixed in a known release. Use the matrix to tell a client "fixed in 25.04/25.05" and move on.

---

## 7. Cluster E — XSS hardening & login/password-reset

- **XSS (parent #1592176, 23.08):** entering `<img src=1 onerror=alert(1)>` into **notes / attachment / message** text areas produced an **error pop-up or console error** (not an actual script execution — the input was being rejected, but the rejection surfaced an error). Affected eSuite Business Associates, Contract Meter List, and QCA/QCFS AFE/AP notes+attachment dialogs (#1594282, #1594256, #1594032, #1594032/#1595171). **Mixed disposition:** #1594282 fixed (Ready for QA, `BLD*`) — but note #1594282 QA found it was a **stale deployment** (SUP17 hadn't been updated to the correct ESuite Web release). Several others (#1594256, #1594032) **Closed/Rejected** as env/deploy issues. The hardening lives in **`Quorum.Upstream.ESUITE.Application.Web`**.
- **Login / password reset (#1644255):** the "Forgot password" screen shows *"Your password reset request has been received"* even when the **mandatory email field is blank** (no validation). **Closed/Rejected** (low priority — the username alone is enough to process, no security exposure). Note as a known minor gap, not a fix to chase.

---

## 8. Cluster F — Attachment / document handling

- **#1373167 (21.21):** after discarding an edited document, the attachments pane title wrongly reads **"Grid Row Attachments"** instead of "Attachments." Real cosmetic fix (PR #59221).
- **#1358464 (Com16, 21.13):** saving a document in AFE Creation/Approval shows "Save successful" **but throws an error** behind it — tagged `Config`; fixed/Ready-for-QA.
- **#1624616 (AP156/A157):** attachments not displayed for a voucher — fixed (Ready for QA, `BLD`).
- **#1439683 (Core SUP):** user can **delete an AFE attachment after submit-to-workflow** despite a warning and despite the AFE being locked to someone else. **Closed/Rejected** — same behavior reproduced in CORE_SUP and APH 2022.04, i.e. **current expected behavior** (the warning is informational only). Note as a known limitation, not a defect with a fix.

---

## 9. Cluster G — Process-launch / impersonation / metadata-sysgen plumbing
*(The genuinely "shared infra" defects — highest L4 value when a process launched from a screen fails)*

- **#1704488 / #1705774 (QDO ORGCOSTGEN):** saving a Cost Center in QDO pops **"Upstream Process ORGCOSTGEN failed"** (the cost center IS created, but no process-progress dialog). **Root cause (Pratik Zanjurne):** ESuite Web launched ORGCOSTGEN for module QRA/QDO via **`IQGlobalProcessLauncherService`** running in the **MT**, where **`IQGlobalProcessLauncherService` is not available** (the endpoint can't be resolved). **Fix:** move the launch to the **Web tier** so `QUIControllerCostCenterMaintenance` calls the QDO MT directly via **`WebProcessLauncherServiceClientCoordinator`** (which resolves the endpoint through the **broker service**). Same fix applied to the Org Maintenance screen. PRs #104409/#104597, iteration **25.02**, Acceptance. **This is the canonical "process launched from a Web screen silently fails / can't find endpoint" root cause** — the MT process-launcher service isn't resolvable; use the Web-tier coordinator.
- **Impersonation on the scheduler (#105931)** and **broker-service `QOperationContext` (#106923)** — see §3-A1; the same broker/endpoint plumbing underlies both POSTWKFL-on-scheduler and ORGCOSTGEN-from-Web failures.
- **Metadata sysgen on wrong layer (#1445857)** — see §3-A4; "completes with errors re: a QXREF_* table" ⇒ sysgen defined on the ENGS layer instead of the product (QCFS/UPS) layer; move it and refresh the DB snapshot.
- **AFE External Import (#1655235, QP053):** import "failed" — QA root-caused it to **missing event-detector setup** (Event Type `AFE_EXTIMP`) so the post-import notification email failed, and **validation errors in the input XML** (must reference an existing OPEN AFE no). Not a core code defect; a config/data issue. The valid-element schema lives in the `QcaAfeXml*` import classes.

---

## 10. Fix-Version Matrix
*(IntegrationBuild is empty on all of these — "Fixed-in" is the IterationPath/tags/PR-target-branch proxy; verify in ReleaseNotes. State reasons: "RFQ"=Moved out of Ready-for-QA i.e. dev-complete & QA-passed.)*

| Bug # | Cluster | Symptom (short) | State / Reason | Fixed-in (approx) | SF case |
|---|---|---|---|---|---|
| #104443 | A1 | POSTWKFL scheduler "no endpoint" | Closed/Verified | Sprint 57 + broker fix #106923 | SIR 180805 (BLU) |
| #105931 | A1 | Scheduler impersonation (QPEC_SCHEDULER) | Closed/RFQ | Sprint 56 (+ SEC Group 9001 sql) | — |
| #106219 | A1 | QCFS scheduled POSTWKFL/QCFSIMPCYC | Closed/Rejected | Sprint 57 (dup of above) | — |
| #1698180 | A2 | POSTWKFL timeout/stuck (blocking session) | Closed/Rejected (not a defect) | n/a — kill session; cache via #1698965 | 24-00989239 (APH) |
| #72944 | A3 | POSTWKFL timeout fixed by DB index | Closed/Validated | Sprint 40 | 304058 |
| #1550460 | A3 | POSTWKFL 20min; BATCHJOURNALENTRYLINE index | Closed/Rejected | index added under #1643630 | — (MEW) |
| #1445857 | A4 | POSTWKFL errors re: QXREF_AFE_VALID_POST_STATUS (sysgen layer) | Closed/RFQ | 22.06 (2022.04) | — |
| #1379243 | A5 | $0 netting line → AR076 POSTWKFL error | Closed/Duplicate of #184253 | n/a (revenue side) | (MAC/GLE) |
| #1552303 | B1 | "Workflow Instance does not exist" (Widget delivery) | Closed/RFQ | 22.23 (2022.10) + QFC #1554243 | — |
| #1583340 | B2 | AFE status stuck PENDING after approve | Closed/RFQ | 23.05 (2023.04 regression) | — |
| #1439453 | B2 | SRCU AFE status not → OPEN | Closed/Rejected | overlaps 23.05 | — (SRCU) |
| #63692 | B3 | Multi-desk user → stack overflow, WF abort | Closed/RFQ | 2018.05 (PR #1224) | — |
| #1786355 | B3 | Duplicate History rows on Reject | Closed/RFQ | 26.06 (PR #124588/#124612) | — |
| #1758402 | B3 | AFE Inbox query empty IN() → MT exception | Closed/Acceptance | 26.02 (PR #121359…) | — |
| #1773689 | B3/A1 | MNT: blank inbox, no Approve (inactive QPEC user) | Closed/RFQ | 26.01 (reactivate user) | — |
| #1721402 | C2 | AP055 Validate 4h on 420k lines (XREF cache) | Closed/Acceptance | hotfix 17.25.15; also 2023.04/2024.10/Develop | — (MIT) |
| #1566911 | C2 | AFE Search by Cost Center 40s+ | Closed/Acceptance | 25.15 (PR #114500 → develop) | 22-00868517 (Seneca) |
| #1725894/#1757514/#1725889/#1645818/#1588989/#1633143/#1734942 | C1 | Perf-lab "slower in 20YY.ZZ" | Closed/**Rejected** | n/a (not reproduced) | — (internal) |
| #1711725/#1711752/#1711728-32 | D | Kendo-upgrade UI regressions | Closed/RFQ | 25.04 / 25.05 | — |
| #177217 | D | Frowny face instead of Cover Sheet | Closed/Rejected | 20.05 (env-specific) | — |
| #868480 | D | STP020 "Object reference" popup | Closed/RFQ | 2021.04 | — |
| #1455953 | D | Missing "Interactive Reports" tree menu | Closed/RFQ | Product Dev | — |
| #1594282 | E | XSS error pop-up (BA/Contract Meter) | Closed/RFQ | 23.08 (stale deploy on SUP) | — |
| #1594256/#1594032 | E | XSS console error (attachment) | Closed/Rejected | 23.08 (env/deploy) | — |
| #1644255 | E | Password reset accepts blank email | Closed/Rejected | n/a (low pri) | — |
| #1373167 | F | "Grid Row Attachments" wrong pane title | Closed/RFQ | 21.21 (PR #59221) | — |
| #1358464 | F | Error after "Save successful" on document | Closed/RFQ | 21.13 | (Com16) |
| #1439683 | F | Delete attachment after submit-to-WF | Closed/Rejected | n/a (by design) | — |
| #1704488 | G | QDO ORGCOSTGEN launch fails from Web | Closed/Acceptance | 25.02 (PR #104409/#104597) | — |
| #1655235 | G | QP053 AFE External Import "failed" | Closed/RFQ | 24.06 (config/data) | — |

---

## 11. Diagnostic Pointers
*(No client-schema confirmed; treat table names from repro/comments as starting points. Always verify-SELECT before any change.)*

- **Get the PQID + exact error first** for any POSTWKFL/PSTWKSPLT/ORGCOSTGEN failure. Read the batch message log for that PQID + step. "Unable to establish a connection with any endpoint" / "endpoint" ⇒ broker/MT/process-launcher plumbing (§3/§9), not business logic.
- **Scheduler vs manual:** if a process succeeds when a user launches it but fails on the scheduler ⇒ **DEBUG mode** on the scheduled definition and/or **scheduler impersonation perms** (`QPEC_SCHEDULER` in SEC group; `QARCH_SEC_USER.INACTIVE_IND`).
- **Single-client POSTWKFL timeout you can't reproduce:** ask the DBA to check for a **blocking session** (esp. around the **VENDOR** table trigger / BA005 edits) before assuming code (#1698180).
- **"Workflow does not exist" on approve:** check the desk's **Notice Delivery type**; if not `EMAIL`, that's it. Code table: `QARCH_WF_CODE_DELIVERY_TYPE` (QFC-managed) should contain **only EMAIL**.
- **Real perf defect vs lab noise:** a `qddperweb5x…PRF…` URL + "slower in 20YY.ZZ" title ⇒ internal regression (usually Rejected). For a client trace, grep the **qtrace** for one SQL repeated thousands of times (e.g. `XREF_COSTCNTR_ACCTATTRIB`, `QXREF_AFE_VALID_POST_STATUS`) ⇒ a cacheable defect (#1721402).
- **"completes with errors re: QXREF_*"** ⇒ missing/mislayered **metadata sysgen** (ENGS vs product layer) (#1445857).
- **Process launched from a Web screen silently fails / endpoint not found** ⇒ MT `IQGlobalProcessLauncherService` not resolvable; the Web tier must use `WebProcessLauncherServiceClientCoordinator` (#1704488).
- **Web screen broken (frowny face / console / cosmetic):** reproduce in **CORE_SUP** first — a large share are env/data/stale-deploy, not code.

---

## 12. Key Code, Processes & Repos

### Processes / batch
| Process | Purpose | Notes |
|---|---|---|
| **POSTWKFL** (QP073) | Post-workflow: post final-approved AFEs/vouchers | Scheduler-only failures = DEBUG/impersonation (§3); timeouts = blocking session / missing index |
| **PSTWKSPLT** | Post-Workflow Splitter | Upgrade-time failures, mostly env (Rejected) |
| **ORGCOSTGEN** (QDO) | Generate org/cost-center structures on save | Launched from Web; must use Web-tier launcher coordinator (§9) |
| **QCFSIMPCYC** | QCFS import cycle | Same scheduler-impersonation family as POSTWKFL |
| **QP053 / AFE_EXTIMP** | AFE External Import | Needs event-detector setup + valid OPEN-AFE XML (§9) |

### Code / infra symbols (from comments/PRs)
| Symbol / table | Where | Cluster |
|---|---|---|
| `UpstreamJournalEntryWorkflow.cs` | `Quorum.Upstream.QCFS.Web` (`/Quorum.QCFS.Upstream/BS/`) | §3 POSTWKFL hot SQL / index |
| `XREF_COSTCNTR_ACCTATTRIB`, `QXREF_AFE_VALID_POST_STATUS` | validation caching | §5 #1721402 |
| `QARCH_WF_CODE_DELIVERY_TYPE`, `QARCH_WF_DESK` | QFC core metadata (delivery type) | §4 #1552303 |
| `QARCH_SEC_USER` (`INACTIVE_IND`), SEC group `9001` | scheduler/impersonation security | §3 #105931/#1773689 |
| `IQGlobalProcessLauncherService` (MT) vs `WebProcessLauncherServiceClientCoordinator` (Web) + broker service | process launch from Web | §9 #1704488 |
| `QUIControllerCostCenterMaintenance`, `QUIControllerAFEFullInbox`, `AFESearchWidget.cshtml`, `HomeController.cs` | `Quorum.Upstream.QCA.Web` / `.QCFS.Web` ESuite Web tier | §4/§5/§6 |
| `QOperationContext`, `QReaderWriterLockTimeoutException` | QFC core interface | §3/§5 |

### Repos
- **`Quorum.Upstream.QCA.Web`** — AFE Web screens, AFE Search widget, full inbox (most V2UI/Kendo + AFE perf fixes).
- **`Quorum.Upstream.QCFS.Web`** — AP voucher Web, post-workflow journal SQL, cost-center validation caching.
- **`Quorum.Upstream.ESUITE.Application.Web`** — the eSuite Web shell (XSS hardening, tree menu, login).
- **QFC core / metadata repos** (`a7ab4c86-…`, `ecaedfc6-…` project) — `QARCH_WF_*` code tables, sysgen layers, broker/impersonation. Core DB tickets land here.
- Client overrides as `<CLIENT>.Upstream.*` (e.g. MIT, MEW, APH, SRCU) — confirm the **client build** carries the core fix.

---

## 13. Escalation Guidance

**Route to Engineering (Software Defect):**
- Process-launch endpoint plumbing: ORGCOSTGEN-from-Web (#1704488), POSTWKFL-on-scheduler broker `QOperationContext` (#104443/#106923), impersonation (#105931).
- Workflow-engine defects: "instance does not exist" via Widget delivery (#1552303 — also a QFC code-table DB fix), status stuck after approve (#1583340), multi-desk stack overflow (#63692), duplicate History rows (#1786355), empty-IN-clause inbox query (#1758402).
- Reproducible client performance: un-cached XREF validation (#1721402), AFE search by cost center (#1566911), POSTWKFL index (#72944). Provide **PQID + exact error + qtrace showing the repeated SQL + client/build**.

**Handle as Config / Ops (no code fix):**
- Turn **DEBUG off** on the POSTWKFL scheduled definition; grant **scheduler impersonation** / reactivate the QPEC user (#105931/#1773689).
- Kill a **blocking DB session** for a single-client POSTWKFL timeout (#1698180).
- Set desk **Notice Delivery = EMAIL**; clean `QARCH_WF_CODE_DELIVERY_TYPE` (#1552303).
- Move a **sysgen** to the correct metadata layer + refresh the DB snapshot (#1445857).
- Set up the **event detector** and fix the **import XML** for AFE External Import (#1655235).

**Do NOT chase (Rejected / by design / lab noise):**
- "Performance slower in 20YY.ZZ" perf-lab reports not reproduced in the next run (§5-C1).
- Delete-attachment-after-submit (#1439683) and Cancel-clears-History (#1645172) — current expected behavior.
- Password-reset blank-email (#1644255) — low-pri, no security exposure.
- XSS "error pop-up" cases that were **stale deployments** (#1594282/#1594256) — verify the env is on the latest ESuite Web release first.

**Always:** confirm the client's build carries the fix in `Quorum.Upstream.*.ReleaseNotes` (the IntegrationBuild field is unreliable/empty); for client-specific repos verify the core fix was merged down.

---

*Skill created: 2026-06-14.*
*Based on 291 ADO Bugs (Closed/Resolved) under `QuorumSoftware\Engineering\Financials` matching SHARED keywords; 47 deep-read for root cause. Notable ADO items: #104443, #105931, #1698180, #1445857, #1552303, #1583340, #63692, #1786355, #1758402, #1721402, #1566911, #72944, #1704488, #1655235, #1711725/#1711752, #1373167, #1594282. Companion product skills: SKILL_ADO_QRA_*, SKILL_ADO_QCA_*, SKILL_ADO_QCFS_*, SKILL_ADO_QDO_* (Upstream ADO Assistant dir); REPO_INVENTORY / CONFIG_REFERENCE.*
