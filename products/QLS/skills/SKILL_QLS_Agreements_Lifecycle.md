# SKILL — QLS Agreement Header, Search & Lifecycle

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Scope (Coverage Plan group #2):** Agreement Search (screen, saved searches, results grid, import/export), Agreement/Subdivision Header, Copy Agreement/Subdivision, Delete Agreement, agreement numbering (number pool / Modify Number / Create Agmt Number), Property Status, Map Status, approval lifecycle.
> **Sources:** all-history Salesforce mining 2026-09-03 (8 SOQL pages, 29 cases detail-sampled, SF case IDs verbatim) + ADO org `QuorumSoftware` (projects `QuorumSoftware` and `Quorum`) work-item mining. PII redacted (individual names removed; 3-letter client codes retained as anchors).
> **Maintained by Auto-Bot — the L4 issue solver built by Aditya Bhagat.**

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cluster | First check | Likely class |
|---|---|---|---|
| Saved search won't open / screen unresponsive / grid shows "No Data" after saving | 3.1 | Apostrophe in search name? Duplicate search name? | G3 Version (fixed 2026.04 HF) / G1 workaround |
| Results-grid column filter does nothing (Legacy #, File Reference #, Property Status…) | 3.2 | `UseLegacyFileNum` config; client build vs 2022.04/2023.04 HF | G3 Version |
| Search criteria not honored (Cost Center returns wrong agreements) | 3.2 | ADO 1657931 — fixed-in check | G3 Version |
| Filter funnel dropdown shows ALL code-table values, not just result set | 3.2 | By design (QFC grid framework) | G1 Expected Behavior |
| Search/header buttons dead until tab refresh; "Quorum Error" opening screens | 3.3 | Build has bug 1630958 collateral? | G3 Version |
| Ctrl+Shift+S doesn't run search in Edge | 3.3 | Shortcut changed to Ctrl+Alt+S | G3 Version / G1 |
| Agreement Search Import shows "1 errors on 1 page", can't clear | 3.3 | ADO 1804558; fixed 2024.04→2026.04 HFs | G3 Version |
| Agreement Search suddenly slow (minutes) | 3.4 | Legacy File # + Country Security configs ON? `QCTRL_AGMT_LEGACY_NUMBER` view-on-view | G5/G2 |
| Copy Agreement copies to 1st subdivision only, 2nd+ areal empty | 3.5 | ADO 1775691; fixed 2023.04→2025.04 HFs (SF fix: March 2026 HF for 2025.04) | G3 Version |
| Copy fails/false alert: "copy notes failed: NullReferenceException", "failed to copy data" | 3.6 | Missing QCLNT metadata layer; attachment-less agreement false alert (1648272) | G2 Config / G3 |
| Copy Agreement wizard: Financial Organization node not offered | 3.6 | Node enablement — data/config script | G2 Config |
| New agreement save: "agreement number already exists" | 3.7 | Two-user number race OR stale `AGREEMENT_NUM_POOL` OR unseated `arrg_key` sequence | G4 Bad Data |
| Modify Number: "'X' is not a valid Base Agreement Number" | 3.7 | ADO 1774238 — fixed 2023.04→2025.04 HFs | G3 Version |
| Header frozen, no field will save on ONE agreement | 3.7 | Carriage return in `AGMT_NUM` (`ALL_AGREEMENTS`) | G4 Bad Data |
| Delete Agreement: "record has been changed by another user" (false) | 3.8 | Multi-agreement/multi-sub delete concurrency (1628253); July 2022.04 HF | G3 Version |
| Delete Agreement errors when agreement has legal description | 3.8 | `MapLegalDetail` config ON + pre-2023.04-HF build (1655451) | G3 Version |
| Property Status won't change / values missing / wrong after conversion | 3.9 | Code-table (decode) rows + status-attribute config; conversion mapping | G2 Config |
| New agreement stuck un-Approved with validation errors | 3.9 | Cost-center completeness validation (now warning) | G2 Config |
| Map Status empty/wrong; reset process not working | 3.9 | `PCK_UPDT_MAP_STATUS_CORE.VALIDATE_LEGAL` / `_LDSEG_CORE` packages | G4 Bad Data |
| Agreement # not populating for a Subject type | 3.9 | `WORKSPACE_SUBJECT` duplicate/misconfigured subject | G2 Config |

---

## 2. Decision Tree

```
Symptom mentions Agreement Search?
├─ Saved-search name involved (apostrophe / duplicate / renamed by script)? → 3.1
├─ Results grid filter or criteria wrong records? → 3.2
├─ Screen dead / errors on open / shortcut / import? → 3.3
└─ Slow? → 3.4
Symptom mentions Copy Agreement / Copy Subdivision?
├─ Data missing on 2nd+ subdivision (ARE) after copy? → 3.5
└─ Error, false alert, missing node in wizard, doc/DD side effects, security? → 3.6
Symptom mentions agreement NUMBER (create/duplicate/modify/renumber)? → 3.7
Symptom mentions Delete Agreement (single, mass, admin tools)? → 3.8
Header fields / Property Status / Map Status / Approval / Subject type? → 3.9
```
Gate order stays G1→G2→G3→G4→G5. Most search/copy/delete symptoms here resolve at **G3 (already fixed in a hotfix)** — check build vs the hotfix tags in section 4 before writing SQL.

---

## 3. Symptom Clusters

### 3.1 Saved searches — apostrophe, duplicate names, broken lookup

**Signature.** Opening/saving a saved Agreement Search misbehaves: screen becomes fully unresponsive (can't save, delete, or switch searches), or result grid shows "No Data" after saving, or typing in the Search Name lookup returns "No Data Found".

**Root causes (three distinct, all CONFIRMED from cases):**
1. **Apostrophe in saved-search name** hangs the whole Agreement Search screen (e.g. a search named with `'s`). — SF 22-00824222 (verbatim description of full lockup). Resolution recorded: *"Users shouldn't create a saved search with an apostrophe in the name."* (workaround-class outcome; treat recurrence as a defect candidate).
2. **Saving a new search under an already-existing Search Name** makes the result grid display no data. — ADO Bug **1836950** (project Quorum) `QLS- AT- Agreement Search- Existing Saved Search Name Causes Result Grid to Display No Data`, Closed, **2026.04 Hotfix Completed** via `Quorum.QLS.Web` PR #129879 → `hotfix/17.27.3` PR #130391.
3. **A DB script that mass-renamed saved searches** broke the Search Name typeahead ("No Data Found"). — SF 23-00922776 (Software Defect; broke after rename script on PREM).

**Fix recipe.**
- Confirm client build ≥ 2026.04 HF for the duplicate-name defect; else quote fixed-in and give interim rule: unique names, no apostrophes.
- For a stuck search record, delete/rename it in the DB (saved-search tables) via services script — do NOT hand-edit without checking dependent widgets/routes: deleting a saved search used by Route Mapping is blocked with an unfriendly error (ADO **1832185**, New — error message cleanup pending).
- Related regression to know: clearing the dashboard-context search id (bug 1630958 change) caused "Quorum Error" popups on screen open — see 3.3.

**Anchors:** SF 22-00824222, 23-00922776, 23-00924237 (stale results after returning to search — same screen-state family); ADO 1836950, 1832185.

---

### 3.2 Results grid filters / search criteria return wrong records

**Signature.** Filters applied on the Agreement Search results grid do nothing (funnel icon doesn't latch), or criteria are silently ignored so the result set contains agreements that don't match.

**Root causes.**
- **Legacy File # / File Reference Number column filter dead.** Code had to switch between `LEGACY_FILE_M` and `XREF_VALUE` depending on global config **`UseLegacyFileNum`**; `Criteria_Agreement.cs` / `ColumnHandler` did not, so both criteria search and grid filter missed. Fixed by making ColumnHandler pick the column from the config (dictionary holding XREF_VALUE property). — SF 23-00908651 (verbatim fix narrative in `Resolution__c`), predecessor 23-00891022; SF 22-00831311 resolved by ADO Bug **1610505** (`ERFL - Agreement Search Results Grid: File Reference Number (Legacy File #) Filtering not working as expected`, Closed/Fixed, tags **AUG 2022.04**, 2022.04 + 2023.04 Hotfix Completed).
- **Cost Center criteria not honored** — search returned agreements with other cost centers; critical because eCalendar routes are driven by saved searches. — ADO Bug **1657931** (APA), Closed, fixed 2022.04/2023.04/2024.04 HFs (tag JUNE 2023.04). Match SF symptom "agreements placed into wrong routes".
- **Generic grid-filter failures on date columns** after participation criteria etc. — SF 22-00644807 (Software Defect, "fixed in new build environment"), SF 23-00908651 issue #2.
- **Filter funnel shows all code-table values (not just those in the result set)** — *Expected Behavior*: QFC grid framework has no option to limit funnel dropdowns to the current result set; would require per-grid changes across 64 views. — ADO Bug **1792433** (DVN), Closed as reviewed/not-changed.

**Fix recipe.** Identify the exact column; if Legacy/File-Reference → confirm `UseLegacyFileNum` config value and build vs AUG 2022.04 HF; if Cost Center → build vs JUNE 2023.04 HF; if "dropdown shows too many options" → explain design, no defect.

**Anchors:** SF 22-00831311, 23-00908651, 22-00644807, 25-01034749; ADO 1610505, 1657931, 1792433.

---

### 3.3 Agreement Search screen dead / errors on open / shortcut / import

**Signature.** Buttons on Agreement Search (or header buttons) do nothing until the browser tab is refreshed; intermittent "Quorum Error" toast when opening Agreement Search / New Agreement / eCalendar; Ctrl+Shift+S opens a screen-capture tool instead of searching (Edge); Agreement Search Import tool shows "1 errors on 1 page" that cannot be cleared.

**Root causes.**
- **Buttons dead until refresh** — regression from the fix in bug 1630958 (allowing dashboard-context search id to be cleared). — ADO Bug **1655228**, Closed, 2023.04 Hotfix Completed; sibling ADO Bug **1645370** ("Quorum Error on TST17 frequently", same 1630958 collateral), Closed, 2022.04→2024.04 HFs.
- **Edge hijacks Ctrl+Shift+S** (built-in screenshot); Quorum changed the search shortcut to **Ctrl+Alt+S**. — ADO Bug **1713347** (APA), Closed, 2023.04→2024.10 HFs.
- **Search-criteria Import errors**: importing an exported template fails ("1 errors on 1 page"); agreement numbers land in the wrong criteria level; date-range columns and dropdown-backed columns weren't round-trip compatible — export now includes Effective/Expiration Date From/To columns matching grid names. — ADO Bug **1804558** (NEE), Closed, fixed across 2024.04, 2024.10, 2025.04, 2026.04 HFs; matching SF 26-01096246 (`Root_Cause__c` Software Defect, resolution "2025.04 May 2026 HF").
- **Uncheck All / Uncheck Visible not working** on results grid — SF 26-01064987 (Software Defect; confirmed working after fix, no HF label recorded → INFERRED build fix).

**Fix recipe.** These are all version-gate outcomes: map client build to the tags above; interim workarounds are tab refresh (buttons), Ctrl+Alt+S (shortcut), regenerate the import template from a fresh export of the same environment (import).

**Anchors:** SF 26-01096246, 26-01064987, 23-00903685; ADO 1655228, 1645370, 1713347, 1804558.

---

### 3.4 Agreement Search slow (minutes instead of seconds)

**Signature.** Search from screen or Quick Search widget takes 30s–2min+; DB stats regathers don't help.

**Root cause (XOM, CONFIRMED in ADO analysis).** With configurations that add **Legacy File Number** and **Country Security** to Agreement Search enabled, the generated query references **`QCTRL_AGMT_LEGACY_NUMBER`** twice — a view built on view `LEGACY_AGREEMENTS_CORE`, itself on `ALL_AGREEMENTS` + `CROSS_REFERENCES`. Fix shipped across 2023.04→2025.04 HFs. A compatibility follow-up: the tuned SQL used `TO_NUMBER(GPL.OBJECT_ID DEFAULT -1 ON CONVERSION ERROR)` which raises **ORA-43907** on older Oracle — verify client Oracle version when backporting. Front-end contribution was also examined ("Platform grid JavaScript"). — ADO Bug **1764536** (XOM), Closed.

**Fix recipe.** Confirm the two configs are actually needed; check build vs the 1764536 hotfix tags; if still slow post-fix, capture the search SQL and check `QCTRL_AGMT_LEGACY_NUMBER` usage count. Note also `Check_Write_Lock` timeout was ruled OUT in that investigation, and a config exists to limit lock-record pulls on the tab to 1,000 (max 10,000) rows (ADO 1645370 comment) — relevant to grid-open slowness.

**Anchors:** ADO 1764536; SF 23-00922388 (Copy Agreement with Subs is very slow — same performance family, cancelled).

---

### 3.5 Copy Agreement/Subdivision — data lands on 1st subdivision only

**Signature.** Using Copy Agreement/Subdivision with "Update Existing Agreement": header (AGM) data copies to the first areal (ARE) subdivision only; 2nd/3rd subdivisions stay empty. Client workaround discovered organically: copy from areal-1 as source to areal-2..n as targets works.

**Root cause.** Node-specific stored-procedure logic (the copy is executed **entirely by DB procedures** — ADO 238463 comment) blocks or redirects certain nodes:
- **Legal Description:** the procedure validates the agreement hierarchy and blocks the copy if a legal description record already exists at ANY subdivision; by design Legal Description remains at AGM level when copying within the same agreement.
- **Participation:** copying within the same tree (AGM → ARE) deletes the source participation record afterwards to enforce the single-level participation constraint — so the "copy" behaves like a move for sub 1 and nothing remains for sub 2.
- Acreage copies correctly only in the intended flow (acreage added at AGM before subs exist, then copied down).
— ADO Bug **1775691** (SRC) `Agreement Copy "Update Existing Agreement" function not copying data to all subdivisions`, Closed, fixed across **2023.04 / 2024.04 / 2024.10 / 2025.04 Hotfix Completed**; earlier ADO Bug **1695647** (SRC, Proposed) same symptom, initially not reproduced.

**SF trail (same client family):** 24-00982429 ("Data Did Not Copy to 2nd Subdivision", closed Training at first pass) → 26-01063757 ("Quorum confirmed this is a bug… fixed in 2025.04… our users tested 2025.04 and it is NOT fixed") resolved by **March 2026 Hotfix for QLS 2025.04**. Lesson: the first 2025.04 claim was premature — always verify the concrete HF build, not the release train.

**Fix recipe.**
1. Reproduce with the exact node list (Acreage / Legal / Depth / Cross Reference / Participation).
2. If build < the 1775691 hotfix for the client's train → G3: cite fixed-in + workaround: use areal-1 as source for areal-2..n targets, or consider the roll-up feature instead of Copy Agreement.
3. If node = Legal Description or Participation and behavior matches the design constraints above → G1 Expected Behavior, explain the single-level rules.

**Anchors:** SF 26-01063757, 24-00982429; ADO 1775691, 1695647, 238463.

---

### 3.6 Copy Agreement — errors, false alerts, missing wizard nodes, side effects

**Signature & root causes (one line each, all Closed unless noted):**

| Symptom | Root cause | Fixed in / fix | Anchor |
|---|---|---|---|
| "copy notes failed: system.nullreferenceexception" on full copy | Missing client metadata layer | **Added QCLNT layer** (metadata config) | SF 23-00907899 |
| Alert "failed to copy data" (date & doc) though data copied fine | Code looked for an attached document even when none exists → exception → false warning | ADO **1648272**, 2022.04 + 2023.04 HF | ADO 1648272 |
| Exception creating payment events on copied agreement: `Row(-15): Column 'ArrgDscr' does not allow` | ArrgDscr not set on the copied agreement for the payment | ADO **1656660**, 2022.04/2023.04 HF | ADO 1656660 |
| Export to Excel from copy results page: HTTP 404 `A public action method 'CopyResultsGridExcelExport' was not found on controller 'Quorum.QLS.Controllers.CopyAgreementWizardController'` | Missing grid-export action on the Kendo grid | ADO **1624784** (CRI), 2022.04/2023.04 HF | ADO 1624784 |
| Financial Organization is the only node NOT offered in the copy wizard | Node enablement data/config | Services SQL script (client-specific; see case for script reference) | SF 23-00917109 |
| Deleting a file from a COPIED agreement deletes the original file from the server and `SARCH_CTRL_DOC` (files auto-LINK on copy) | Linked-document delete didn't respect links | ADO **1594716** (CRW), 2022.04/2023.04 HF | ADO 1594716 |
| DynamicDocs folder not created when copying via header three-dot menu | Copy runs via DB procedures, bypassing DD code — run the **attribute sync process** to create/sync the folder | ADO **238463**, 2020.09 Hotfix 1 | ADO 238463 |
| Read-only user can create agreements through Copy Agreement | Security not enforced on wizard | ADO **1706242**, 2022.04→2024.10 HFs | ADO 1706242 |
| Copy screen spins forever after "View Results in Agreement Nav" (mass copy 14 leases) | Wizard result-navigation hang | SF closed "Other" — treat as repro-first if seen on modern build | SF 22-00824669 |
| Provisions "copied" reported successful but absent on specific target agreements (others fine) | Data-dependent; never root-caused in SF record | Compare source/target provision rows in DB before escalating | SF 24-00957930 |

**Anchors:** SF 23-00907899, 23-00917109, 22-00824669, 24-00957930; ADO 1648272, 1656660, 1624784, 1594716, 238463, 1706242.

---

### 3.7 Agreement numbering — duplicates, pool collisions, Modify Number failures, corrupt numbers

**Signature.** "System generated a new agreement number which already exists"; integrations/renumbering hit existing numbers; Modify Number / Create Agmt Number error "'X' is not a valid Base Agreement Number"; save creates no areal/depth nodes; one agreement's header is frozen and unsavable.

**Root causes (each verified in a real case):**
1. **Two-user race:** the pending agreement number shown at create time is **not reserved** in the DB; a second user starting a create before the first saves gets the same number, and the later save fails with "already exists". Core MyQuorum design gap — for Fee/Lease types the user can manually bump the number; contract-type numbers can't be edited, forcing a re-create. — SF 22-00832061 (system-owner narrative verbatim in Description).
2. **Stale/overlapping `AGREEMENT_NUM_POOL`:** acquisition data loads consuming a block of numbers without blocking them off in the pool → later integrations collide. Fix: script to DELETE the exhausted range from the agreement number pool (UAT + PRD) after querying the latest used number, then renumber affected agreements manually. — SF 24-00944356 (resolution steps verbatim).
3. **Un-seated `ARRG_KEY` sequence:** create fails AND areal/depth nodes are not generated → Oracle sequence behind MAX(key). Fix recorded: *"re-seating arrg_key sequence"*. — SF 24-00961597. Related platform-level variant after V17 upgrade fixed by *"Ran sysgen after hours"*. — SF 25-01023346.
4. **Modify Number defect:** base-number parsing method "consistently returns '000' for any base agreement number", so `Modify Number` rejects valid targets ("'RE901225002' is not a valid Base Agreement Number"). Expected rules per ADO: Modify Number → target base # in use by another agreement; Create Agmt Number → new base # that exists in the pool. — ADO Bug **1774238** (PHL), Closed, fixed 2023.04→2025.04 HFs, tag `L4-Investigated`; SF 25-01059289 resolution "April 2026 2023.04 HF".
5. **Corrupt `AGMT_NUM` (trailing CR/LF):** header freezes, nothing saves on that agreement. Legacy Desktop QLS allowed a carriage return in the number; web QLS chokes on it. Diagnose and clean with the SQL in section 5. — ADO Bug **1764220** (INV), Closed via Script Review Resolution (93 more agreements found).
6. **DB-side renumbering doesn't fire the DynamicDocs interface** (`QARCH_CTRL_DATASTORE` not updated when `AGMT_NUM` changed by a nightly DB procedure) → downstream DD stale. UI renumbering does fire it. — ADO Bug **1620252** (TEP), Closed as enhancement-routed.
7. Historic: pool populated with wrong-length (11-digit) numbers surfacing randomly at create — ADO Bug **113320** (MRC), Closed with correction script.

**Fix recipe.** Order of checks: (a) duplicate-number error at save → ask if a colleague was creating simultaneously (race, G1/known limitation) else check pool overlap (SQL 5.2); (b) "not a valid Base Agreement Number" → build vs 1774238 hotfixes; (c) create fails with missing nodes → verify `ARRG_KEY` sequence vs MAX (SQL 5.3), re-seat after hours; (d) single-agreement freeze → CR/LF scan (SQL 5.1).

**Anchors:** SF 22-00832061, 24-00944356, 24-00961597, 25-01023346, 25-01059289; ADO 1774238, 1764220, 1620252, 113320.

---

### 3.8 Delete Agreement — false concurrency errors, config-dependent failures

**Signature.** Mass delete (Admin Tools) or Delete Agreement screen fails with "the record has been changed by another user" when selecting multiple agreements/subdivisions; delete errors on agreements that have a legal description; error unclear when agreement can't be deleted.

**Root causes.**
- **Concurrency error on multi-select:** selecting multiple agreement numbers (each with multiple subdivisions) in one Delete pass throws an optimistic-concurrency error; one-at-a-time works. — ADO Bug **1628253**, Closed. Release note from the fix: *Delete Agreement (from Agreement Navigator or Function Navigator) can now automatically delete child subdivisions when deleting a parent record*; behavior gated by config `QLSValidationAgreementDetail0019_HasSubAgreements` (0 = off). Matches SF 23-00910526 (mass delete "record has been changed by other user", resolution **July 2022.04 Hotfix**).
- **`MapLegalDetail` config ON** breaks delete of agreements that have legal descriptions (incl. polygon calls / metes & bounds). — ADO Bug **1655451**, Closed, 2023.04 + 2024.04 HF.
- **Residual UI defect:** deleted Depth tab persists with unsaved-changes indicator when opened via Agreement→Areal→Depth path (tab-close logic only closes the "current tab"). — ADO Bug **1757303**, Proposed/open at mining time.
- Generic "Unable to Delete Agreements / Areals" errors — SF 22-00866822 (Software Defect, fix detail not recorded; treat as repro-first).

**Fix recipe.** Build check vs July 2022.04 HF (concurrency) and 2023.04 HF (`MapLegalDetail`); interim: delete one agreement number at a time; check whether the agreement has events (delete completes with warning "Agreement has events" post-fix — that warning is expected).

**Anchors:** SF 23-00910526, 22-00866822; ADO 1628253, 1655451, 1757303.

---

### 3.9 Agreement Header lifecycle — Property Status, Map Status, Approval, Subject types

**Signature.** Property Status values missing/wrong or need to be required; header approval throws validation errors and status won't move to Approved; Map Status blank on new agreements or needs mass reset; a Subject type won't generate an agreement number; state/county show NOT APPLICABLE after conversion.

**Root causes & recipes.**
- **Property Status is code/decode + attribute config.** New statuses, attribute changes (e.g. required flag), and dropdown corrections are Code Table Navigator / decode-table work, often conversion cleanup. — SF 26-01120371, 26-01105203 ("make it requirement"), 25-01038488, 25-01031952, 25-01047283 (all Application Configuration). New code-table values not appearing in UI after direct-DB insert → cache/config refresh path (SF 23-00898803 family).
- **Approval blocked:** new agreement wouldn't move to Approved with errors; resolution: cost-center completeness check demoted — *"all cost centers are taken into account and this is a warning now"* (config/behavior change). — SF 25-01044524. A companion Repsol case closed Training (errors were legitimate blocks) — SF 25-01048483: verify the specific validation text before assuming defect.
- **Property Status mass change does not trigger re-approval** — reported during upgrade testing; treat as known behavior/defect candidate (root cause null in SF). — SF 24-00948459.
- **Map Status blank on create with new legal description** → services script fix (attached in the case). — SF 24-00957750. **Map-status reset at subdivision/legal-segment level** uses Oracle packages **`PCK_UPDT_MAP_STATUS_CORE.VALIDATE_LEGAL`** and **`PCK_UPDT_MAP_STATUS_LDSEG_CORE.VALIDATE_LEGAL`**; user-run failures of that procedure were a Software Defect case. — SF 26-01097855. "Update Map Status" from search results setting a status that mismatches its description — fixed **June HF** — SF 23-00903986.
- **Subject type doesn't populate an Agreement #:** duplicated/overlapping subject in `WORKSPACE_SUBJECT` (e.g. Easement/Surface vs Surface). Fix (real script, NEE): `UPDATE WORKSPACE_SUBJECT SET SUBJ_DISPLAY='N', TEXTUAL_SUBJ='N' WHERE SUBJ_CODE='ROW';` — SF 26-01083166.
- **State/County = NOT APPLICABLE post-conversion** → *"update state and county mappings"* (conversion mapping tables). — SF 25-01050950. Landowner-type list trimming per agreement type = land-classification config, applied via `Quorum.QLS.Conversion` repo post-conversion script (project QuorumServices). — SF 25-01056245.
- **Header frozen on one agreement** → see 3.7 root cause 5 (CR/LF in AGMT_NUM).

**Anchors:** SF 26-01120371, 26-01105203, 25-01038488, 25-01031952, 25-01047283, 25-01044524, 25-01048483, 24-00948459, 24-00957750, 26-01097855, 23-00903986, 26-01083166, 25-01050950, 25-01056245.

---

## 4. Known ADO items (fixed-in labels: CONFIRMED = tag/comment on the work item; INFERRED = SF resolution text only)

| ADO | Title (short) | State | Fixed-in |
|---|---|---|---|
| 1610505 | Agreement Search grid: Legacy File # filtering broken | Closed/Fixed | AUG 2022.04; 2022.04 + 2023.04 HF Completed (CONFIRMED) |
| 1657931 | Cost Center criteria not honored in Agreement Search (APA) | Closed | 2022.04/2023.04/2024.04 HF, JUNE 2023.04 (CONFIRMED) |
| 1836950 | Duplicate saved-search name → empty result grid | Closed | 2026.04 HF (QLS.Web PR 129879 → hotfix/17.27.3 PR 130391) (CONFIRMED) |
| 1804558 | Agreement Search Import "1 errors on 1 page" (NEE) | Closed | 2024.04→2026.04 HFs (CONFIRMED) |
| 1713347 | Ctrl+Shift+S hijacked by Edge → now Ctrl+Alt+S (APA) | Closed | 2023.04→2024.10 HFs (CONFIRMED) |
| 1655228 / 1645370 | Buttons dead until refresh / Quorum Error on open (1630958 collateral) | Closed | 2023.04 HF / 2022.04→2024.04 HFs (CONFIRMED) |
| 1764536 | Slow Agreement Search w/ Legacy File # + Country Security (XOM) | Closed | 2023.04→2025.04 HFs; ORA-43907 caveat (CONFIRMED) |
| 1792433 | Grid filter funnels show all code-table values (DVN) | Closed | By design — no code change (CONFIRMED) |
| 1775691 / 1695647 | Copy "Update Existing Agreement" skips 2nd+ subdivision (SRC) | Closed / Proposed | 2023.04→2025.04 HFs; SF says March 2026 HF for 2025.04 (CONFIRMED / INFERRED) |
| 1648272 | False "failed to copy data" alert (date & doc, no attachment) | Closed | 2022.04 + 2023.04 HF (CONFIRMED) |
| 1656660 | Copy: missing ArrgDscr → exception creating payment events | Closed | 2022.04/2023.04 HF (CONFIRMED) |
| 1624784 | Copy results Export to Excel 404 CopyResultsGridExcelExport (CRI) | Closed | 2022.04/2023.04 HF (CONFIRMED) |
| 1594716 | Delete of copy-linked file removes original + SARCH_CTRL_DOC (CRW) | Closed | 2022.04/2023.04 HF (CONFIRMED) |
| 238463 | DD folder not created on copy via header menu | Closed | 2020.09 Hotfix 1; run attribute sync (CONFIRMED) |
| 1706242 | Read-only user can create via Copy Agreement | Closed | 2022.04→2024.10 HFs (CONFIRMED) |
| 1774238 | Modify Number: "not a valid Base Agreement Number" (PHL) | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1764220 | CR/LF in AGMT_NUM freezes Agreement Header (INV) | Closed | Data-cleanup script, no code fix (CONFIRMED) |
| 1620252 | DB-side agreement-number change skips DD interface (TEP) | Closed | Routed as enhancement (CONFIRMED) |
| 113320 | 11-digit numbers from corrupt AGREEMENT_NUM_POOL (MRC) | Closed | Correction script (CONFIRMED) |
| 1628253 | Delete Agreement concurrency error, multi-select | Closed | SF companion: July 2022.04 HF (INFERRED); auto child-sub delete added (CONFIRMED) |
| 1655451 | Delete fails with MapLegalDetail config ON | Closed | 2023.04 + 2024.04 HF (CONFIRMED) |
| 1757303 | Deleted Depth tab persists in TreeView | Proposed | open |
| 1832185 | Deleting saved search used by Route Mapping — raw error | New | open |
| 1678669 | Delete-agreement dialog V2UI styling | Closed | 2023.04/2024.04 HF (PR 99695) (CONFIRMED) |

Area paths seen: `QuorumSoftware\Engineering\Land\Committed Backlog`, `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land`, `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services` (1610505), project `Quorum` for 2026+ items (1836950, 1804558, 1832185). Repos touched: `Quorum.QLS.Web` (Criteria_Agreement.cs, CopyAgreementWizardController), `Quorum.QLS.Conversion` (project QuorumServices, client post-conversion scripts).

---

## 5. Diagnostic SQL (Oracle, `lis` schema — every query below appeared in a real case/work item)

**5.1 Corrupt agreement number (CR/LF) — detect and clean (ADO 1764220):**
```sql
-- detect
SELECT * FROM ALL_AGREEMENTS WHERE INSTR(agmt_num, CHR(13)||CHR(10)) > 0;
-- audit how it was created
SELECT * FROM ALL_AGREEMENTS_LOG WHERE arrg_key = :arrg_key AND db_column = 'AGMT_NUM' ORDER BY updt_date;
-- clean (script-review before running in client PRD)
UPDATE ALL_AGREEMENTS SET agmt_num = REPLACE(agmt_num, CHR(13)||CHR(10), '')
 WHERE INSTR(agmt_num, CHR(13)||CHR(10)) > 0;
-- confirm the pool is clean too
SELECT * FROM AGREEMENT_NUM_POOL WHERE INSTR(agmt_num, CHR(13)||CHR(10)) > 0;
```

**5.2 Number-pool collision check (SF 24-00944356 recipe):** query the latest agreement number actually used in `ALL_AGREEMENTS` for the affected prefix, compare against remaining `AGREEMENT_NUM_POOL` rows, then script a DELETE of the overlapping pool range in UAT + PRD before renumbering (~run under change control; exact ranges are client-specific).

**5.3 Create-agreement failure with missing areal/depth nodes (SF 24-00961597):** compare the `ARRG_KEY` sequence's next value against `MAX(arrg_key)` across the agreement tables; if behind, re-seat the sequence after hours. (Case resolution verbatim: "re-seating arrg_key sequence". V17-upgrade variant required a sysgen run — SF 25-01023346.)

**5.4 Subject type hidden/duplicated (SF 26-01083166, real fix script):**
```sql
UPDATE WORKSPACE_SUBJECT SET SUBJ_DISPLAY = 'N', TEXTUAL_SUBJ = 'N' WHERE SUBJ_CODE = 'ROW';
```

**5.5 Map-status reset packages (SF 26-01097855):** `PCK_UPDT_MAP_STATUS_CORE.VALIDATE_LEGAL` (subdivision header) and `PCK_UPDT_MAP_STATUS_LDSEG_CORE.VALIDATE_LEGAL` (legal segment). If the CORE variant errors on valid data, escalate as defect with the exact ORA error — that combination was Software-Defect-classed.

**5.6 Legacy File # search config:** global config **`UseLegacyFileNum`** decides whether search/filter hits `LEGACY_FILE_M` or `XREF_VALUE` (SF 23-00908651). Performance objects: `QCTRL_AGMT_LEGACY_NUMBER` → `LEGACY_AGREEMENTS_CORE` → `ALL_AGREEMENTS` + `CROSS_REFERENCES` (ADO 1764536).

> DEV-tier caveat: run these on the client's `<CLIENT>_LND_DEV17`/`<CLIENT3>U_HD_DEV17` mirror via the metadata server; PRD data-state conclusions stay INFERRED until confirmed by client DBA output.

---

## 6. Expected-Behavior FAQ

- **"The filter funnel dropdown shows values that aren't in my results."** By design: QFC grid framework populates code-table funnels with all values; limiting to the result set would require per-grid changes across 64 views (ADO 1792433).
- **"Two of us created agreements at the same time and one save failed with duplicate number."** Known design gap: the pending number is displayed but not reserved until save (SF 22-00832061). Save early; for editable types bump the number manually.
- **"Copy Agreement didn't copy Legal Description down to my subdivision."** Design: Legal Description stays at AGM level when copying within the same agreement; copy is blocked if a legal record exists at any sub (ADO 1775691 analysis).
- **"Participation vanished from the source after I copied it to an areal."** Design: single-level participation constraint — AGM→ARE copy within the same tree deletes the source row (ADO 1775691 analysis).
- **"Delete completed but warned 'Agreement has events'."** Expected post-fix behavior of Delete Agreement (ADO 1655451 verification note).
- **"Why does Copy Agreement not create the DynamicDocs folder?"** Copy runs in DB procedures; run the DD attribute sync process afterwards (ADO 238463).
- **"Ctrl+Shift+S stopped working in Edge."** Edge reserved it; use **Ctrl+Alt+S** (ADO 1713347).
- **"Can we rename/renumber agreements directly in the database?"** UI-only, unless services-scripted: DB-side `AGMT_NUM` changes bypass the DD/`QARCH_CTRL_DATASTORE` integration (ADO 1620252) and AGM-level number changes must sync to subdivision level.

---

## 7. Escalation

- **Ready-to-cite fixed-in:** quote the ADO id + hotfix tag from section 4; label the client-build claim INFERRED until the client confirms their exact `hotfix/17.2x.y` build.
- **Escalate to Engineering (area `Quorum\North America\Upstream\Land RnD` for current, `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` legacy) when:** a section-4 defect reproduces on a build that already contains its hotfix tag (cf. the 26-01063757 lesson — "fixed in 2025.04" was wrong until the March 2026 HF); a new ORA error from the map-status packages; number-pool corruption recurs after cleanup.
- **Route to Services (not Engineering):** conversion-mapping fixes (state/county, property-status decode sets, landowner classification), number-pool range deletes, `WORKSPACE_SUBJECT`/code-table scripts — these ship as client scripts in `Quorum.QLS.Conversion` / `<CLIENT3>.QLS.Metadata`.
- **Batch flag:** none of this group's symptoms are batch-driven; if the complaint arrives as "agreement search error during an import", check the import/batch job first (SF 26-01096246 was Case_Category `QLS - Batch Process`).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
