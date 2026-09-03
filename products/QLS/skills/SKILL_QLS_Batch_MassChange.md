# SKILL — QLS Batch Processes & Mass Changes

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema (+ QPEC/QFC schemas `QLS_QFCONL`, `ESUITE_QFC`)
> **Scope (Coverage Plan group #13):** Batch Processes screen (visibility, security, parameters), QPEC scheduled jobs (`QARCH_CTRL_SCHED` family), REPOSCRUB, PUBBA/DATAPUBLSH publisher, financial/1099/Positive-Pay/SAP batch, import processes (CHKHISTIMP, Mass Legal Upload, Agreement Import), and the entire Mass Changes wizard family (notes, participation, date & document, status/inactivation, delete, approval).
> **Sources:** all-history Salesforce mining 2026-09-03 (5 SOQL pages, 30 cases resolution/description-sampled, case IDs verbatim) + ADO org `QuorumSoftware` (projects `QuorumSoftware`, `Quorum`) work-item mining. PII redacted (individual names and bank account numbers removed; 3-letter client codes retained).
> **Maintained by Auto-Bot — the L4 issue solver built by Aditya Bhagat.**

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cluster | First check | Likely class |
|---|---|---|---|
| A batch process "no longer appears under Batch Processes" | 3.1 | `QARCH_CTRL_PROCESS_TYPE` row for the process | G2 Config / G4 |
| Process dropdown on Process Execution is EMPTY / process "NOT Available" | 3.1 | `QARCH_CTRL_PROCESS` + `_TYPE` metadata; BTCH/BTYP security objects | G2 Config |
| Role can't run one specific process (e.g. AFISCRTAE) | 3.1 | Batch security for that role | G2 Config |
| Nightly scheduled job fails but MANUAL run works (SAPFINHIST…) | 3.2 | `QARCH_CTRL_PROC_SCHED_PARAM.PARAM_ID` vs process params | G4 Bad Data (sched metadata) |
| Scheduled job never fires (Pull Events, Roll Date, roll-forward) | 3.2 | Row in `QARCH_CTRL_SCHED` + `ENABLE_SCHEDULE_TASK_IND`; QPEC up? | G2 Config |
| Jobs stopped on a DATE and never resumed (STAGE_JE, SAPINTJE) | 3.2 | QPEC service/scheduler health at that date | G2/Env |
| "unable to establish a connection with any endpoint" intermittently on eCal Inbox | 3.3 | `ESUITE_QFC.QARCH_CTRL_OBJECT_REPOSITORY` growth (REPOSCRUB only scrubbing `QLS_QFCONL`) | G2 Config |
| REPOSCRUB "closing open sessions/screens nightly" | 3.3 | Expected behavior — that IS its job; tune days-to-scrub param | G1 Expected |
| Weekly PUBBA/DATAPUBLSH "Could not initialize: Error found in QMsgLog" | 3.4 | `QARCH_PROCESS_MSG_LOG` + stuck `QARCH_QUEU_PROCESS` CE rows | G2/G4 |
| 1099DBSP "stops processing on error", "Failed to execute stored procedure" | 3.5 | Bad data row feeding the DB proc — fix script | G4 Bad Data |
| Positive Pay file has wrong bank account (ADAMPPFDEO) | 3.5 | Client custom stored procedure content / change control | G4 / custom code |
| Mass Change note NOT saved on some/all records | 3.6 | Build vs note-omission hotfixes (multiple ADO items) | G3 Version |
| Duplicate notes with DESG_KEY=0 / HIST_SEQ_NO=0 after mass participation | 3.6 | ADO 1458731 / 1691135; cleanup script | G3 + cleanup |
| Mass Change Participation: BA search spins forever / no results | 3.7 | "core object was messed up" family; build check | G4 / G3 |
| Payee-Status / Prospect mass-change grid empty until filtered | 3.7 | ADO 1716514 fixed-in | G3 Version |
| Mass Date&Doc: "Date must be earlier than January 1, 2999" | 3.8 | ADO 1580959 — 2022.04 HF (March 2023 hotfix per case) | G3 Version |
| Mass Add Document only attaches to FIRST agreement | 3.8 | ADO 1616549 (`SARCH_DOC_CONTENT_TYPE` REL_URI `{STIP_KEY}`) — 2022.04 HF | G3 Version |
| Acreage zeroed by mass inactivation | 3.9 | Config `RecalculateAcreageIfSubdivisionActivatedOrInactiva…` | G2 Config |
| Mass Update Agreement Status "not working" for some agreements | 3.9 | Existing effective-dates beyond the new range (12/31/9000 rows) | G1/G4 |
| Mass delete errors; deleted child data but left the agreement | 3.9 | Validation `QLSValidationAgreementDetail0023_ScannedDocumentsAttached` blocking mid-delete | G2 Config (+ cleanup) |
| Mass approval times out with errors | 3.9 | 10-minute app timeout; `session_unload_timeout` config; smaller batches | G2 Config |
| Import stuck: "can't clear error on Agreement Search during an import" | 3.10 | ADO fixed-in ("2025.04 May 2026 HF") | G3 Version |
| CHKHISTIMP: "The field ID was a sequence that could not be initiated" | 3.10 | Import/FTP metadata setup for both steps | G2 Config |
| Mass Legal Upload: non-Jeff townships/sections not loading | 3.10 | Fixed "2023.04 OCT '25 HF" | G3 Version |

---

## 2. Decision Tree

```
Is it a BATCH PROCESS (screen/QPEC) issue?
├─ Process missing/not launchable/role-blocked? → 3.1
├─ Schedule exists but job fails or never fires? → 3.2
│    └─ Fails ONLY when scheduled (manual OK)? → 3.2 (sched-param metadata)
├─ Session/endpoint errors, repository bloat, REPOSCRUB questions? → 3.3
├─ PUBBA / DATAPUBLSH publisher errors? → 3.4
├─ Financial batch (1099DBSP, Positive Pay, SAP*, AFIS*)? → 3.5
└─ Import processes (CHKHISTIMP, Mass Legal Upload, Agreement Import)? → 3.10
Is it a MASS CHANGE (wizard) issue?
├─ Notes missing/duplicated/only-on-one-record? → 3.6
├─ Wizard grid/picklist won't load? → 3.7
├─ Date & Document mass change? → 3.8
└─ Status / inactivation / delete / approval? → 3.9
```
Gate order G1→G2→G3→G4→G5. Mass-change wizard defects are overwhelmingly **G3 already-hotfixed** (2022.04→2025.04 trains); batch-process visibility/scheduling issues are overwhelmingly **G2 metadata** in the `QARCH_CTRL_*` tables.

---

## 3. Symptom Clusters

### 3.1 Batch process missing / not available / role-blocked

**Signature.** A process disappears from the Batch Processes screen ("AFIS Batch Process no longer appears under Batch Processes"), the Process dropdown is empty for a Process Type, "QLS Bank Submission Process is NOT Available", or one role can't execute a process others can.

**Root cause.** Batch-process visibility is pure metadata + security:
- `LIS.QARCH_CTRL_PROCESS` — process definition (`PROCESS_ID`, `PROCESS_NM`, `ACTIVE_IND`, `HIDDEN_IND`, `APP_LAYER_CD='QLS'`).
- `LIS.QARCH_CTRL_PROCESS_TYPE` — maps process to a Process Type node (e.g. `'INTERFACES'`); **a missing row here removes the process from the screen** (SF 26-01116116: *"script has been provided to insert the missing record in QARCH_CTRL_PROCESS_TYPE table"*).
- `LIS.QARCH_CTRL_PROCESS_PARAM` — parameters.
- Security objects **BTCH** and **BTYP** gate the screen and process types; per-process batch security is granted per role (SF 26-01116490 AFISCRTAE for Financial Processor role → "updated security").
- Bank Submission missing = *"Update code tables to include missing processes"* (SF 25-01049301). Upgrades can drop scheduled processes wholesale (SF 22-00803045 — packaging issue).

**Fix recipe.** Query the three `QARCH_CTRL_PROCESS*` tables for the PROCESS_ID (section 5 has the verbatim verification set from ADO 1576289 — written for PUBBA, works for any process). Insert the missing rows on the client layer; then check batch security for the calling role; cache refresh.

**Anchors:** SF 26-01116116, 25-01049301, 26-01116490, 22-00803045, 24-00951222 (duplicate BP rows in UAT — same tables, dedupe); ADO 1576289 (PUBBA metadata recipe + KB "How to Schedule PUBBA Full Synch in QLS eSuite").

---

### 3.2 Scheduled jobs — never fire, or fail only when scheduled

**Signature.** (a) A process runs fine manually but the nightly QPEC-scheduled run fails every night. (b) A recurring process simply never runs (Pull Events, Roll Date, Recurring Event Roll Forward). (c) All/several jobs stopped on a specific date and never resumed (STAGE_JE & SAPINTJE stopped 27-Feb→25-Mar).

**Root causes.**
1. **Sched-param metadata mismatch (manual-OK/scheduled-fails).** The schedule's parameter rows in `QARCH_CTRL_PROC_SCHED_PARAM` point at a wrong/stale `PARAM_ID` after upgrade. ADO Bug **1460676** (SME, SAPFINHIST) fix verbatim:
   ```sql
   update qarch_ctrl_proc_sched_param p
      set p.param_id = 47005
    where p.param_id = 534
      and exists (select 1 from qarch_ctrl_sched s
                   where s.process_id = 'SAPFINHIST' and s.schedule_id = p.schedule_id);
   ```
   (The QDF upgrade updated the process but not `QARCH_CTRL_PROC_SCHED_PARAM` — check this table after every upgrade when nightly jobs break.)
2. **No schedule row / disabled row.** Schedules live in `QARCH_CTRL_SCHED` (`PROCESS_ID`, `SCHEDULE_ID`, `ENABLE_SCHEDULE_TASK_IND`). Pull Events fixed by *"Guided the client to successfully schedule ECALWF using the QFC Maint App"* (SF 25-01033689); Roll Date enabled per SF 26-01105936; Recurring Event Roll Forward was never scheduled at go-live (SF 26-01102441, Project Debt).
3. **QPEC/scheduler outage.** A date-bounded stop of multiple jobs = QPEC service or environment change, not per-job metadata (SF 26-01090133). Related history: ECALLOCK/ECALWF job questions (SF 23-00905109), nightly UPSLSINTFC failure (SF 22-00825868, Software Defect).

**Fix recipe.** Manual-vs-scheduled discrimination FIRST — it splits root cause cleanly. Then: run history in `QARCH_QUEU_PROCESS` (was it even queued?), schedule row in `QARCH_CTRL_SCHED` (enabled?), params in `QARCH_CTRL_PROC_SCHED_PARAM` (IDs valid?), errors in `QARCH_PROCESS_MSG_LOG`. Schedule new jobs via the QFC Maint App or scripted inserts into `QARCH_CTRL_SCHED` + `QARCH_CTRL_PROC_SCHED_PARAM` (pattern blessed in ADO 1576289).

**Anchors:** SF 25-01033689, 26-01105936, 26-01102441, 26-01090133, 24-00984825, 23-00905109, 22-00825868, 23-00924672 (eCal batch job re-schedule to hourly = config change); ADO 1460676, 1576289.

---

### 3.3 REPOSCRUB & QARCH_CTRL_OBJECT_REPOSITORY hygiene

**Signature.** Intermittent "unable to establish a connection with any endpoint" on the eCal Inbox (or general screen/session flakiness); or performance degradation with `QARCH_CTRL_OBJECT_REPOSITORY` at 50k–100k rows; or customer alarmed that "REPOSCRUB is closing open screens nightly".

**Root cause / model.** `QARCH_CTRL_OBJECT_REPOSITORY` houses unclosed sessions/screen repos; the QPEC job **REPOSCRUB** cleans it (that's its whole job — nightly screen closure is EXPECTED behavior, SF 25-01060786 / 22-00875107 / 24-00957853). The table exists in **BOTH** `QLS_QFCONL` and `ESUITE_QFC` schemas, and REPOSCRUB must be scheduled against **each**: clearing only `QLS_QFCONL` while `ESUITE_QFC` grows causes the eCal Inbox endpoint errors (SF 25-01026830, verbatim: *"clearing the QLS_QFCONL.QARCH_CTRL_OBJECT_REPOSITORY table but not the ESUITE_QFC.QARCH_CTRL_OBJECT_REPOSITORY table causes intermittent 'unable to establish a connection with any endpoint' errors on the ecal inbox screen"*). Schedule/params live in `QARCH_CTRL_SCHED` + `QARCH_CTRL_PROC_SCHED_PARAM` (one param = number of days to scrub). XOM PRD baseline: both repository tables cleared nightly; healthy counts were ~149 (ESUITE_QFC) and ~671 (QLS_QFCONL) (ADO 1831115).

**Fix recipe.**
- Verify run history and schedule per schema (section 5, ADO 1688097 verbatim queries).
- If QPEC scheduling is problematic, run the scrub as a DB job and disable the QPEC schedule (ADO 1729240, verbatim): `update QLS_QFCONL.qarch_Ctrl_sched set ENABLE_SCHEDULE_TASK_IND = 0 where process_id = 'REPOSCRUB';`
- If the table already ballooned (PHL: ~52k rows/7 days), a manual delete script was script-reviewed before running (ADO 1729240) — don't truncate blindly during business hours.

**Anchors:** SF 25-01026830, 25-01060786, 24-00976428, 24-00957853, 22-00875107; ADO 1688097, 1729240, 1831115.

---

### 3.4 PUBBA / DATAPUBLSH publisher errors

**Signature.** Recurring rows in `ESUITE_QFC.QARCH_PROCESS_MSG_LOG` for process `PUBBA` / `DATAPUBLSH`:
```
"Could not initialize: Error found in QMsgLog.
   at Quorum.QFC.ServiceFramework.PublisherService.QPublisherBase.Publish(String clientUID, QServiceRequest request, Int64& runID)
   at Quorum.ESuite.QLS.Integration.QESuiteQLSDataProviderBase.FullSynch(Int64 queueID, QSynchMsg[]& msgs, ...)"
```
queued by `QPEC_SCHEDULER`, with matching stuck `CE`-status rows in `ESUITE.QARCH_QUEU_PROCESS` (INTEG_ADAPTOR_TYPE(30020)=24 etc.).

**Root cause.** PUBBA full-sync publisher (BA publish from eSuite → LIS participant tables) failing at initialization — typically stale/erroneous queue entries or adaptor config, not the BA data itself. SF 24-00937509 closed once client confirmed BA updates flowed to Participation again (Application Configuration). PUBBA availability/launch issues are cluster 3.1 (metadata; ADO 1576289 adds PUBBA to the web Batch Processes screen — note *"For PUBBA specifically, this batch process is called when Saving on the Business Associate screen"*).

**Fix recipe.** Read the exact message in `QARCH_PROCESS_MSG_LOG`; inspect `QARCH_QUEU_PROCESS` for stuck `CE` rows for PROCESS_ID `PUBBA`/`DATAPUBLSH`; clear/requeue; verify adaptor params (INTEG_ADAPTOR_TYPE/ACTION/PARAM1-4). Full BA-sync failure families (address/country code data) route to the Participation/BA skill — this cluster covers the publisher machinery only.

**Anchors:** SF 24-00937509 (verbatim log rows), 26-01117564 (PUBBA full sync errors — owner not showing); ADO 1576289.

---

### 3.5 Financial batch — 1099DBSP, Positive Pay (ADAMPPFDEO), SAP, AFIS

**Signature & recipes (one line each — these share the "DB-procedure batch" shape):**
- **1099DBSP** ("1099 Submission - DB Procedure Version") halts entirely on first error: *"Failed to execute stored procedure."* → find the offending data row, fix via script (SF 26-01064559, resolution: *"provided script for SRC to run to fix issue"*). Class G4.
- **ADAMPPFDEO** (client custom interface creating the daily Positive Pay file to SFTP) produced the file with the **wrong bank account number** after an unrelated change touched the client stored procedure → correct the client-custom stored proc, audit change control, and check whether the value was changed anywhere else in QLS (SF 26-01106924, Software Defect; account numbers redacted). Custom-interface regressions are a change-control conversation, not core product.
- **SAPPMTCOVL** (SAP Payment Cost Object Validation) issues → fixed in later version; option = OOC hotfix (SF 26-01082309, resolution: *"Resolution will be included once APA upgrade to latest Version. Alternate option ... OOC HF"*). Class G3.
- **SAPFINHIST** nightly failure → sched-param metadata (cluster 3.2, ADO 1460676). Its date filter historically didn't filter (same bug — validation SQL: `SELECT * FROM sap_integration_log a ORDER BY a.log_date DESC;`).
- **AFIS** family: process visibility (cluster 3.1); GL mapping corrections shipped as scripts against `AFIS_TEMPLATE`/`AFIS_GL_CROSS_REF` (SF 26-01100472 "Script to Update AFIS_GL_CROSS_REF"; SF 25-01043176 / 25-01037417 AFIS Create Accounting Entries = config).
- **Create Accounting** batch is a known afternoon-performance contributor (open connections + slow stored-proc query) — XOM PRD analysis, ADO 1831115 (also fingered **ADSYNC** AD-sync batch for a recurring 2 PM degradation).

**Anchors:** SF 26-01064559, 26-01106924, 26-01082309, 26-01100472, 25-01043176, 25-01037417, 26-01087237 (FINTRANEXP-QLS error), 26-01103510 (Bank Recon = config); ADO 1460676, 1831115.

---

### 3.6 Mass Changes — notes omitted, duplicated, or half-written

**Signature.** The note entered in a Mass Change wizard is missing on some/all target records; duplicate note rows appear; note lands on only 1 of N records; Chain of Title doesn't show the participation note; Financial Detail Bulk Change Status drops its note on Save.

**Root causes (all code defects, all fixed — this is a VERSION cluster).**
1. **Several mass-change functions omitted the note** — fix detail verbatim (SF 23-00904000, Software Defect): *"For Mass Related Agreement, commented a code that was removing the related agreements from the active agreement... For Cross reference, updated the logic for checking mass actions. The condition that previously checked for only 'Add' action, now checks for 'Change' action."* Siblings: SF 23-00922556 (Mass XREF note not added), 23-00922614 (Mass Related Agreement note only on 1 agreement), 23-00920345 (Mass Insert Provisions not adding notes — hotfix patch to PRD).
2. **Duplicate notes with key 0** — Mass Participation Change with "Allocation of Original Interest" < 1 generated duplicate notes in the QXREF note tables with `DESG_KEY = 0`; fix moved note creation to the `DoSave` method on the 5 wizard screens (ADO Bug **1458731**, ENCL; related #230277, #1379440). Consequence: 0-key notes surface on unrelated new records. SF 23-00904005 (Mass Agreement Note duplicates) resolved via hotfix.
3. **Participation note not on Chain of Title** — both AN-Participation and Mass Change paths; bad entries with `HIST_SEQ_NO = 0`; hotfixed **2022.04→2025.04**, cleanup-script discussion in the item (ADO Bug **1691135**, APA).
4. **Bulk Change Status (Financial Detail) drops notes on Save** — backend controller fix, note now commits on OK; hotfixed **2023.04→2025.04** (ADO Bug **1764032**, CNX).

**Fix recipe.** Confirm client build against the hotfix trains above (G3). For residue: hunt 0-key rows (`DESG_KEY = 0` / `HIST_SEQ_NO = 0`) in the note/xref tables and clean by script — these rows keep resurfacing on unrelated records until removed.

**Anchors:** SF 23-00904000, 23-00904005, 23-00920345, 23-00922556, 23-00922614, 23-00922379 (Bulk View/Edit freezes after Mass Agreement Note Add — open defect); ADO 1458731, 1691135, 1764032, 230277, 1379440, 1639065 (summary-page Hide/Show columns dead — grid_Id 49196 protected-index fix, 2022.04→2024.04 HFs).

---

### 3.7 Mass Changes — grids/picklists won't load

**Signature.** Wizard cannot get off the ground: Participation Change BA search returns "no results" or spins forever; Transferor picklist empty; Payee-Status grid shows no rows until a column filter is applied; Prospect Change/Delete grid entirely absent.

**Root causes.** Mixed:
- SF 24-00981666 "Mass Change Participants Not Loading" — resolution verbatim *"core object was messed up"* (corrupt platform/core object → G4-style repair). SF 24-00945886 (BAs will not load) same family; SF 23-00922551 (Transferor picklist).
- ADO Bug **1716514** — Payee Status grid loads nothing until filtered; Prospect Change/Delete landing grid missing (partially by design: Next leads to prospect selection); code fix to the Mass Changes query; not reproducible in SUP17 (24.04)/DEV17 (24.10) → fixed in current trains.
- Mass "add area details to prospect" error — ADO Bug **1714367**, hotfixed 2022.04→2024.10.
- PII/obfuscation environments: Mass Change Exhibit Generation errors when data-redaction is ON (ADO Bug **1667579**) — check whether the env has obfuscated NOTE columns before chasing product defects.

**Fix recipe.** G3 build check first (1716514/1714367 trains). If on a fixed build: check whether a saved search feeds the wizard (too-large result sets time out the grid), then platform core-object integrity (re-deploy metadata/core objects), then PII/obfuscation status of the environment.

**Anchors:** SF 24-00981666, 24-00945886, 23-00922551, 24-00967058 (UAT mass-change defect batch); ADO 1716514, 1714367, 1667579.

---

### 3.8 Mass Change — Date & Document

**Signature.** Mass Date&Doc wizard rejects valid dates; document attaches to only the first agreement; attach-step UI distorted; screen filters missing.

**Root causes.**
1. **"Date must be earlier than January 1, 2999"** on dates that are fine — ADO Bug **1580959** (DVN), Sev 2-High, Closed, **2022.04 Hotfix** tags; SF 23-00904006 resolution cites the bug and *"March 2023 hotfix"*.
2. **Add Document only attaching to first agreement** — the platform re-uploaded the same doc per agreement and errored; key detail: client did **not** use `{STIP_KEY}` as the `REL_URI` in `SARCH_DOC_CONTENT_TYPE` (differentiator vs #1603203); reproducible in CORE_DEV; fix also covered Bug 1608446 (error linking agreement within Date&Doc screen). ADO Bug **1616549** (DVN), Closed, **2022.04 Hotfix**.
3. **UI distortion on attach step** (columns shrink, description disabled) — ADO Bug **1650398**, hotfixed 2023.04 + 2024.04 (PR 95971 "Style updates to MassDateDoc notes/attachments grid").
4. **Screen filters** on Mass Date&Doc grid — SF 22-00828348 Closed-Deferred (enhancement-class); general Mass Date&Doc misc fixed in 2024.04 GA (SF 23-00908228).

**Fix recipe.** Almost purely G3: map symptom → bug → hotfix train, compare client build, quote fixed-in + interim workaround (per-agreement attach via Date&Doc screen). For linked-doc content-type behavior verify the client's `SARCH_DOC_CONTENT_TYPE.REL_URI` pattern before assuming core defect.

**Anchors:** SF 23-00904006, 23-00908228, 22-00828348; ADO 1580959, 1616549, 1603203, 1608446, 1650398.

---

### 3.9 Mass status change, inactivation, delete, approval

**Signature.** Mass inactivation zeroes acreage; mass status update "doesn't work" on some agreements; mass delete errors and leaves half-deleted agreements; mass approval throws errors/timeouts.

**Root causes.**
1. **Acreage zeroing on mass inactivation** — controlled behavior: *"Acreage recalculation on mass agreement status change will be done only when `RecalculateAcreageIfSubdivisionActivatedOrInactiva` configuration is on"* (SF 23-00902642 resolution, config key name verbatim-truncated as stored). Turn it off if the client doesn't want recalc.
2. **Mass Update Agreement Status skips rows** — the wizard sets effective-date-to = 12/31/9000, but agreements already carrying status rows dated beyond the new range don't take the update (SF 25-01004160). Not a defect — date-range collision; fix the outlier rows first.
3. **Mass delete partial failure** — errors mid-run; one run deleted all child data but left the agreement shell (SF 25-01021123, resubmission of 24-00985239). Resolution verbatim: *"Duplicate the row 'QLSValidationAgreementDetail0023_ScannedDocumentsAttached' from QARCH_CTRL_OBJECT_USE_RELATION for the QDMB layer and set ENABLED_IND to 0"* — i.e. the scanned-documents-attached validation fires mid-delete; disable it on the QDMB layer for the delete path. Then clean the orphaned shells.
4. **Mass approval errors** — approval batch exceeds the application's 10-minute timeout; mitigations: smaller filtered batches + raise `session_unload_timeout` configuration (SF 26-01109081). Scheduled-inactivation errors during upgrades: SF 23-00933557 (resolved in APA upgrade project), 23-00931827 (Training).

**Fix recipe.** These are config/data gates — read the config keys above before touching code. For half-deleted agreements, inventory orphaned children by `arrg_key` before re-running delete.

**Anchors:** SF 23-00902642, 25-01004160, 25-01021123 (+24-00985239), 26-01109081, 23-00933557, 23-00933413 (mass processes not allowed for multiple subject types — config), 23-00930422 (Mass Participation Delete — config).

---

### 3.10 Import batch processes — CHKHISTIMP, Mass Legal Upload, Agreement Import

**Signature.** Import errors that won't clear on Agreement Search; CHKHISTIMP fails with "The field ID was a sequence that could not be initiated"; Mass Legal Upload silently skips non-Jeffersonian townships/sections.

**Root causes.**
1. **Un-clearable import error on Agreement Search** — SF 26-01096246, Software Defect, resolution "2025.04 May 2026 HF" (G3).
2. **CHKHISTIMP sequence error** — Check History Import is a two-step import needing FTP + Import/Export Definition metadata for BOTH steps; file flows FTP → `AppFiles\QLS\Imports` → `ACCEPTED`, staging into `QSTAG_CHECKHISTORY_INFO` (verify: `select * FROM QSTAG_CHECKHISTORY_INFO ORDER BY UPDT_DT DESC;`). "Field ID was a sequence that could not be initiated" = missing/wrong import-def metadata, not the data file. ADO Bug **1760947** (CHN), Closed, **2025.04 Hotfix Completed**.
3. **Mass Legal Upload non-Jeff not loading** — SF 24-00961228, Software Defect, fixed "2023.04 OCT '25 HF" (INFERRED build label).

**Anchors:** SF 26-01096246, 24-00961228; ADO 1760947.

---

## 4. Known ADO items (fixed-in reference)

| ADO | Title (short) | State | Fixed-in evidence |
|---|---|---|---|
| **1580959** | DVN - Date & Document Mass Change - "Date must be earlier than January 1, 2999" | Closed | Tags: 2022.04 Hotfix Completed (SF cites March 2023 hotfix) |
| **1616549** | DVN - Mass Change Add Document only attaching to first agreement (`SARCH_DOC_CONTENT_TYPE` REL_URI) | Closed | 2022.04 Hotfix Completed (also fixed 1608446) |
| **1650398** | Mass change Date&Doc — UI distorted on attach | Closed | 2023.04 + 2024.04 Hotfix Completed |
| **1458731** | ENCL - Mass Participation Change — duplicate notes `DESG_KEY=0` in QXREF note tables | Closed | Fix: note creation moved to `DoSave` on 5 wizard screens |
| **1691135** | APA - Participant change notes missing on Chain of Title (`HIST_SEQ_NO=0`) | Closed | 2022.04→2025.04 Hotfix Completed |
| **1764032** | CNX - Bulk Change Status not saving notes (Financial Detail) | Closed | 2023.04→2025.04 Hotfix Completed |
| **1639065** | Mass Changes Agreement Note summary — Hide/Show Columns dead (grid_Id 49196) | Closed | 2022.04→2024.04 Hotfix Completed |
| **1716514** | Mass changes — Payee Status grid empty / Prospect change-delete grid missing | Closed | Not repro in SUP17 (24.04)/DEV17 (24.10) — fixed in current trains (INFERRED) |
| **1714367** | Mass Changes — error adding area details to prospect | Closed | 2022.04→2024.10 Hotfix Completed |
| **1667579** | Mass change Exhibit Generation errors when PII/obfuscation ON | Closed | Env-conditional (obfuscated NOTE columns) |
| **1460676** | SAPFINHIST nightly fails, manual OK (`QARCH_CTRL_PROC_SCHED_PARAM` param_id) | Closed | Metadata fix (SQL in 3.2); date filter defect same item |
| **1576289** | Add PUBBA to web Batch Processes screen (full `QARCH_CTRL_PROCESS*` recipe) | Proposed | Metadata scripts (section 5); BTCH/BTYP security noted |
| **1688097** | WMN - network error on eCalendar approval — REPOSCRUB diagnostics | Closed | Diagnostic SQL (section 5) |
| **1729240** | PHL - Manual REPOSCRUB run + unschedule from QPEC | Closed | Script-reviewed delete + `ENABLE_SCHEDULE_TASK_IND=0` |
| **1831115** | XOM - PRD Land performance (ADSYNC 2 PM, Create Accounting afternoon, repo-table counts) | Analyze (open) | Diagnostic SQL (section 5) |
| **1760947** | CHN - CHKHISTIMP "field ID was a sequence that could not be initiated" | Closed | 2025.04 Hotfix Completed |
| **173425** | DOM - CWACHEMAIL blank reports (`qarch_ctrl_process_param` default 'FALSE') | Closed | Param-default metadata fix |

Fixed-in labels from hotfix tags are **INFERRED** unless release-notes-confirmed; re-verify against the client's `hotfix/17.2x.y` branch.

---

## 5. Diagnostic SQL (Oracle — verbatim from cases/bugs unless marked)

**REPOSCRUB health (ADO 1688097, verbatim):**
```sql
select * FROM qls_qfconl.QARCH_QUEU_PROCESS WHERE PROCESS_ID = 'REPOSCRUB' order by updt_dt desc;  -- runs that actually happened
select * FROM qls_qfconl.QARCH_CTRL_SCHED  WHERE PROCESS_ID = 'REPOSCRUB';                          -- schedule rows
select COUNT(*) FROM qls_qfconl.qarch_ctrl_object_repository;                                       -- unclosed sessions REPOSCRUB cleans
-- repeat the last two against ESUITE_QFC.* — BOTH schemas must be scrubbed (SF 25-01026830)
```

**Unschedule REPOSCRUB from QPEC to run as DB job (ADO 1729240, verbatim):**
```sql
update QLS_QFCONL.qarch_Ctrl_sched
   set ENABLE_SCHEDULE_TASK_IND = 0
 where process_id = 'REPOSCRUB';
```

**30-day batch/process forensic sweep (ADO 1831115, verbatim):**
```sql
SELECT * FROM lis.QARCH_QUEU_PROCESS       WHERE queue_dt >= (SYSDATE - 30) ORDER BY queue_dt DESC;
SELECT * FROM QLS_QFCONL.QARCH_PROCESS_MSG_LOG WHERE LOG_DATE >= (SYSDATE - 30) ORDER BY LOG_DATE DESC;
SELECT * FROM QLS_QFCONL.QARCH_QPEC_MSG_LOG    WHERE LOG_DATE >= (SYSDATE - 30) ORDER BY LOG_DATE DESC;
```

**Scheduled-run fails / manual OK — sched-param repair pattern (ADO 1460676, verbatim; adapt IDs):**
```sql
update qarch_ctrl_proc_sched_param p
   set p.param_id = 47005
 where p.param_id = 534
   and exists (select 1 from qarch_ctrl_sched s
                where s.process_id = 'SAPFINHIST' and s.schedule_id = p.schedule_id);
```

**Batch-process visibility verification (ADO 1576289, verbatim — swap PROCESS_ID):**
```sql
SELECT PROCESS_ID, PROCESS_NM, PROCESS_DESCR, APP_LAYER_CD, ACTIVE_IND, HIDDEN_IND
  FROM LIS.QARCH_CTRL_PROCESS
 WHERE PROCESS_ID = 'PUBBA' AND APP_LAYER_CD = 'QLS';

SELECT PROCESS_TYPE_CD, PROCESS_ID, APP_LAYER_CD
  FROM LIS.QARCH_CTRL_PROCESS_TYPE
 WHERE PROCESS_ID = 'PUBBA' AND APP_LAYER_CD = 'QLS';

SELECT p.PROCESS_ID, p.PROCESS_NM, p.PROCESS_DESCR, pt.PROCESS_TYPE_CD
  FROM LIS.QARCH_CTRL_PROCESS p
 INNER JOIN LIS.QARCH_CTRL_PROCESS_TYPE pt
    ON p.PROCESS_ID = pt.PROCESS_ID AND p.APP_LAYER_CD = pt.APP_LAYER_CD
 WHERE pt.PROCESS_TYPE_CD = 'INTERFACES' AND p.APP_LAYER_CD = 'QLS' AND p.PROCESS_ID = 'PUBBA';
```

**Missing-record fix for a process dropped from the screen (SF 26-01116116 pattern, INFERRED insert — model on the 1576289 recipe):**
```sql
INSERT INTO LIS.QARCH_CTRL_PROCESS_TYPE (PROCESS_TYPE_CD, PROCESS_ID, USER_ID, UPDT_DT, APP_LAYER_CD)
VALUES ('<TYPE_CD>', '<PROCESS_ID>', USER, SYSTIMESTAMP, 'QLS'); COMMIT;
```

**SAP financial-history verification (ADO 1460676, verbatim):**
```sql
SELECT * FROM sap_integration_log a ORDER BY a.log_date DESC;

SELECT * FROM financial_trans_histories a
  JOIN SAP_JE_DOCUMENT_HEADER b ON a.ft_key = b.ft_key
 WHERE b.status = 'COM' AND FT_TYPE = 'PAY' AND VOIDED_IND IS NULL
   AND a.ft_status = 'CR' AND DATE_CLEARED IS NULL
 ORDER BY b.date_posted DESC;
```

**Check History Import staging check (ADO 1760947, verbatim):**
```sql
select * FROM QSTAG_CHECKHISTORY_INFO ORDER BY UPDT_DT DESC;
```

---

## 6. Expected-Behavior FAQ

- **"REPOSCRUB closed my users' open screens overnight"** — by design; it scrubs unclosed sessions from `QARCH_CTRL_OBJECT_REPOSITORY`. Tune the days-to-scrub parameter in `QARCH_CTRL_PROC_SCHED_PARAM` rather than disabling it (disabling causes the endpoint-error class in 3.3).
- **"Mass Update Agreement Status skipped some agreements"** — agreements whose existing status effective-dates extend past the wizard's 12/31/9000 default are not updated; correct the outlier date rows, re-run (SF 25-01004160).
- **"Mass approval fails on big batches"** — the app has a 10-minute processing window; run filtered sub-batches and/or raise `session_unload_timeout` (SF 26-01109081).
- **"Acreage changed when we mass-inactivated"** — recalc is governed by the `RecalculateAcreageIfSubdivisionActivatedOrInactiva…` config; set per client intent (SF 23-00902642).
- **"Can we mass-change multiple subject types at once?"** — mass processes are restricted per subject type (SF 23-00933413) — split the run.
- **"A process ran fine last month and nothing changed"** — after ANY upgrade/QDF apply, `QARCH_CTRL_PROC_SCHED_PARAM` and `QARCH_CTRL_PROCESS_TYPE` can silently lose sync with the process definition (ADO 1460676, SF 26-01116116, SF 22-00803045). Diff the metadata first.

## 7. Escalation

- **Batch flag:** anything running under QPEC (`QPEC_SCHEDULER` in the log rows) is the *segregated* batch path — engage `batch-debugger` agent conventions; the QPEC ops runbook lives at `products/_shared/skills/SKILL_QPEC_Ops_Runbook.md`.
- **Code change (G5):** new mass-change wizard defects on builds ≥ 2025.04 → ADO bug in `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` or `Quorum\North America\Upstream\Land RnD`. Repos: `Quorum.QLS.Web` (wizard controllers), `Quorum.QLS.ServiceCore` (batch, e.g. `QQLSServiceCore_EcalBatch.cs`), `Quorum.QLS.Metadata` (QARCH metadata), `QLS.Batch`; client custom interfaces (ADAMPPFDEO-class) live in client repos/DB procs — treat as client-custom scope.
- **Half-deleted agreements after mass delete:** stop further runs, inventory orphans by `arrg_key`, script cleanup, THEN fix the blocking validation (3.9) — order matters.
- **Performance escalations** (Create Accounting / ADSYNC pattern): collect the 3-query forensic sweep (section 5) + QPEC server specs before engaging engineering (ADO 1831115 shows the expected packet).
- DEV-tier metadata caveat: schema/config findings on `<CLIENT>_LND_DEV17` are CONFIRMED anchors; client-PRD data-state claims stay INFERRED until PRD SQL is run.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
