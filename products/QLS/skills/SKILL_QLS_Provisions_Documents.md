# SKILL — QLS Dates/Documents, Provisions & Notes

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Scope (Coverage Plan group #10):** Agreement Navigator Provisions screen + provision models, `STIPULATION_PROVISIONS` / `STIPULATION_TYPES` / `STIP_PROV_DATA_VALUES` data chain, Date and Document screen (doc types, recordation, attachments, document repository / OpenText / Documentum links), Notes/Remarks (agreement notes, remark categories).
> **Sources:** all-history Salesforce mining 2026-09-03 (5 SOQL pages, 27 cases resolution/description-sampled, case IDs verbatim) + ADO org `QuorumSoftware` (projects `QuorumSoftware`, `Quorum`) work-item mining. PII redacted (individual names removed; 3-letter client codes retained as anchors; account numbers removed).
> **Maintained by Auto-Bot — the L4 issue solver built by Aditya Bhagat.**

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cluster | First check | Likely class |
|---|---|---|---|
| "Not able to save a provision in QLS" (save silently fails / errors) | 3.1 | `STIP_SEQ` Oracle sequence vs max `STIP_KEY` | G4 Bad Data |
| Trailing space in provision response; SF/other integration mismatch ("value with trailing space") | 3.2 | Client build vs 2024.04→2026.04 HFs (ADO 1791243); `STIP_UNIT_CODE` null for the type | G3 Version + cleanup script |
| Provision value stored "120.00 Days" sometimes, "120 Days" other times | 3.2 | `PROV_RESPONSE` is a composed display string — entry-path dependent | G1/G2 (formatting, not corruption) |
| Provision Response dropdown is EMPTY on Mass Changes but works on Agreement Navigator | 3.3 | Registered SQL `SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG` bind name | G2 Config (registered SQL) |
| Response/Value dropdown values in wrong order | 3.3 | `SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG_WEB` missing ORDER BY | G2 Config |
| Provision model missing for a contract type / provisions missing from model | 3.4 | Provision-model config (`STIPULATION_TYPES`, model membership) | G2 Config |
| Provisions/models wrong after upgrade or acquisition conversion ("did not convert", "converted incorrectly") | 3.4 | Post-conversion scripts in `Quorum.QLS.Conversion` | G2 Config (conversion) |
| Numeric provision response not editable / unit disappears after agreement approved | 3.4 | Agreement `arrg_stage <> 'NEW'` + model-added provision (ADO 110953) | G3 Version |
| "Unable to attach files" for SPECIFIC document types only | 3.5 | Doc-type ↔ content-type config (`SARCH_DOC_CONTENT_TYPE`), DD staging config | G2 Config |
| Cannot attach .pdf / error opening attachment with odd extension | 3.5 | Allowed file-extension list config (case-sensitive: `.PDF` vs `.pdf`) | G2 Config |
| "Object with such name already exists in the specified folder" on attach | 3.5 | ADO 1701865 — auto-rename regression; fixed 2024.10/2025.04 HF | G3 Version |
| Attachment "Posted By" shows "(no create user)" | 3.5 | ADO 1747290 — fixed 2023.04→2025.04 HFs | G3 Version |
| Uploaded file name corrupted (special char replaces a letter, link then errors) — QLA | 3.5 | Non-ASCII/encoding in file name (SF 25-01015732) | G5 candidate / workaround: rename ASCII |
| Attachment icon bold but "This document cannot be found in the Repository" | 3.6 | Repository path config + QLS Web/MT service restart | G2 Config |
| Docs show "Scan Complete"/Linked but file missing from server AND `SARCH_CTRL_DOC` | 3.6 | `DELETE_DOCUMENTS_FROM_REPOSITORY` ON + one file linked to multiple agreements (ADO 1594716) | G3 Version / G4 |
| Date & Doc URL links to OpenText wrong/dead after conversion | 3.6 | `CONVERT_IND` on migrated doc-link rows; rerun conversion queries | G4 Bad Data (conversion) |
| "Can't add documents older than 1900" (doc date or recording date rejected) | 3.7 | `QARCH_CNFG_CTRL` key `QLandGlobal / MinDate` | G2 Config |
| Notes missing after conversion/upgrade (Agreement Header, payments, property) | 3.8 | Conversion data script needed; note-category config | G2 Config (conversion) |
| Duplicated Remark Categories in dropdowns | 3.8 | Duplicate code-table rows — dedupe script | G4 Bad Data |
| Document types missing in PRD/UAT but present elsewhere | 3.5 | Doc types disabled/not visible (code-table enable flags) | G2 Config |

---

## 2. Decision Tree

```
Symptom on the PROVISIONS screen?
├─ Save fails outright? → 3.1 (sequence)
├─ Stored value has trailing space / unexpected ".00" / integration mismatch? → 3.2
├─ Value/Response DROPDOWN empty or badly ordered? → 3.3
└─ Model membership, defaults, conversion, post-approval editability? → 3.4
Symptom on DATE AND DOCUMENT?
├─ Attach/upload blocked or errors? → 3.5
├─ Attachment exists but file missing / wrong link / repository error? → 3.6
└─ Date value rejected (older than 1900 etc.)? → 3.7
Symptom about NOTES / REMARKS (missing, duplicated, categories)? → 3.8
```
Gate order G1→G2→G3→G4→G5. In this module most attach/upload symptoms are **G2 config** (extension lists, doc-type/content-type mapping, repository path) and most provision-value symptoms are **G3 already-fixed** or **conversion follow-up scripts** — check hotfix tags in section 4 before writing SQL.

---

## 3. Symptom Clusters

### 3.1 Provisions not saving — STIP_SEQ sequence out of step

**Signature.** User cannot save any provision on the Provisions screen ("I am not able to save a provision in QLS"); other screens fine.

**Root cause.** Provision rows live in `LIS.STIPULATION_PROVISIONS` keyed by `STIP_KEY`; the Oracle sequence feeding it (`STIP_SEQ`) had drifted below existing max key → unique-key collision on insert. CONFIRMED by resolution text.

**Fix recipe.**
1. Compare `STIP_SEQ.NEXTVAL` against `MAX(STIP_KEY)` in `LIS.STIPULATION_PROVISIONS` (see Diagnostic SQL — verification query, run before touching anything).
2. Reset/advance the `STIP_SEQ` sequence past max used key (DBA script; standard Oracle `ALTER SEQUENCE ... INCREMENT BY <gap>` + dummy nextval + restore increment, or drop/recreate per client DBA standard).
3. Retest save. Prevention note: sequence drift usually follows a data load/conversion that inserted `STIP_KEY` values directly without consuming the sequence.

**Anchors:** SF 24-00993887 ("Provisions not saving", Software Defect, Resolution: *"Reset the STIP_SEQ sequence solved this issue"*).

---

### 3.2 PROV_RESPONSE stored-value defects — trailing space & decimal formatting

**Signature.** Downstream integrations (client Salesforce sync, etc.) report mismatches because `STIPULATION_PROVISIONS.PROV_RESPONSE` contains `"<value> "` (trailing space) or `"120.00 Days"` where the UI showed `"120 Days"`. EQC reported **80,000+ rows** affected for SHUT-IN PAYMENT FREQUENCY and SHUT-IN RESTRICTION provisions; sources included conversion users (`2025_OLYMPUS ACQUISITION`, `CONVERSION`, `EQC_CONVERSION`) *and* interactive entry.

**Root cause (trailing space) — CONFIRMED, code-level.** `Quorum.QLS.Web.Core\Controllers\ProvisionsController.cs`, method `ProvisionsFieldUpdate` (lines ~244–323 at time of fix): inadequate null check (`!= string.Empty` instead of null-safe) when appending the unit description to the response value. When the provision type has **no unit configured** (`STIP_UNIT_CODE` null → `StipUnitDesc`/`RespUnitDesc` null), the concatenation appends a separator space with nothing after it. Columns: `PROV_RESPONSE` VARCHAR2(380), `RESP_RESPONSE` VARCHAR2(400). — ADO Bug **1791243** "EQC - QLS - Trailing space in provision response", Closed, hotfix tags **2024.04 / 2024.10 / 2025.04 / 2026.04 Hotfix Completed**.

**Root cause (decimal zeros) — INFERRED from the same mechanism.** `PROV_RESPONSE` is not a raw value: it is a **composed display string** built at input time from `PROV_VALUE` + unit lookups (ADO 86435 states: *"STIPULATION_PROVISIONS.PROV_RESPONSE ... is a combination of the PROV_VALUE and STIP_UNIT_CODE, with the appropriate code table lookups, upon Provision Details screen input"*). Different entry paths (Detail screen, mass insert, conversion) format the numeric portion differently → `"120.00 Days"` vs `"120 Days"` (SF 26-01083600, CONTINUOUS OPS). Related display-consistency complaints: SF 24-00951004 ($ amount display in Value/Units not consistent), SF 24-00951010 (units only show after toggling Subject To yes/no).

**Fix recipe.**
1. G3 first: confirm client build vs the 1791243 hotfix train (fixed 2024.04+; SF resolution on 26-01087181: *"Fixed in 2024.10+. Clean up script provided"*).
2. Data cleanup: one-time TRIM script on the two affected columns for affected provision types (script accompanied the case — request via case attachment; do not improvise mass UPDATE without HIST/audit strategy).
3. For decimal-format mismatch: treat as formatting-at-entry, not corruption — align the integration comparison logic or normalize on export; flag to product only if client demands consistent storage.

**Anchors:** SF 26-01087181 (verbatim symptom + 80k count + example agreements 343843000, 297025000), SF 26-01083600, SF 24-00951004, SF 24-00951010; ADO 1791243, 86435.

---

### 3.3 Provision Value/Response dropdowns — empty on Mass Changes, or mis-ordered

**Signature.** (a) On Mass Changes → Mass Add Provision, picking Yes (Subject To) then opening the Response dropdown shows **nothing**, while the same provision's dropdown works on the Agreement Navigator Provisions screen. (b) Dropdown options appear in non-ascending order for some provision types (PUGH (DEPTH), PUGH (ACREAGE), CONFIDENTIALITY PROVISION).

**Root cause.** The dropdowns are fed by **registered SQL** in `QARCH_SQL`:
- Empty-on-mass: `SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG` (APP_LAYER_CD='QLS') used bind `@RESP_DATA_CATG` where the mass screen passes `@PROV_DATA_CATG`. — ADO Bug **192663** (EQC), fix verbatim:
  ```sql
  UPDATE QLS_QFCONL.QARCH_SQL
     SET SQL_STATEMENT = REPLACE(SQL_STATEMENT, '@RESP_DATA_CATG', '@PROV_DATA_CATG')
   WHERE REGISTERED_SQL_NM = 'SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG'
     AND APP_LAYER_CD = 'QLS';
  ```
- Ordering: `SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG_WEB` lacked `ORDER BY` — metadata fix checked in (ADO Bug **1731536**, hotfixed 2023.04→2025.04), statement updated to:
  ```sql
  SELECT A.PROV_DATA_VALUE, A.PROV_DATA_VALUE_DESC, length(A.PROV_DATA_VALUE_DESC) as DESC_LEN,
         A.PROV_DATA_CATG, C.STIP_TYPE_CODE
    FROM STIP_PROV_DATA_VALUES A
    JOIN STIPULATION_TYPES C
      ON A.PROV_DATA_CATG = C.RESP_DATA_CATG
     AND C.STIP_CATG_CODE = 'PRV'
   ORDER BY A.PROV_DATA_VALUE_DESC ASC
  ```

**Fix recipe.** Pull the client's row from `QARCH_SQL` for the registered SQL name in play; diff against Core metadata (`Quorum.QLS.Metadata`); apply the metadata update (client layer if client-specific override exists). Cache/metadata refresh after update.

**Anchors:** ADO 192663, 1731536; SF 26-01069593 (Pooling / Pooling Horizontal response dropdown — config), SF 22-00813694 (provision value not pulling to top grid — same composed-grid family, Software Defect).

---

### 3.4 Provision models — membership config, conversion gaps, post-approval editability

**Signature.** A provision model is missing for a contract type; individual provisions missing from a model; models/types wrong after an upgrade or acquisition conversion ("Provision Models Converted Incorrectly", "Z-Shut-In Provision did not convert"); OR a numeric-response provision added through a model can't be edited once the agreement is approved.

**Root causes.**
1. **Model membership/config** — provision models and which provisions/contract types they apply to are pure configuration (`STIPULATION_TYPES` + model tables + `STIP_PROV_DATA_VALUES` value lists). Adds like "Add 3 existing QLS provisions to the Marcellus default provision model" are config work, not defects. Defaults mapping (ADO 86435): `STIPULATION_TYPES.DFLT_PROV_VALUE → PROV_VALUE`, `DFLT_PROV_UNIT → STIP_UNIT_CODE`, `DFLT_RESP_VALUE → RESP_VALUE`, `DFLT_RESP_UNIT → RESP_UNIT_CD`.
2. **Conversion gaps** — post-conversion scripts fix these; e.g. XOM/PNR acquisition: Z-Shut-In non-conversion fixed by a post-conversion script committed to `Quorum.QLS.Conversion` (repo path `CLIENT/XOM/2025 - XTO and PNR Acqisition/.../02_Post_Conversion_Scripts/47.LIS - Post Conversion Scripts - November.sql`, commit 59ad5a3).
3. **Post-approval editability defect** — provision with Response data type NUMBER added via model is not editable when `arrg_stage <> 'NEW'`; unit disappears on edit. ADO Bug **110953** (APA post-go-live P1), Closed.

**Fix recipe.** For membership complaints: script the code-table/model rows (client metadata layer), no code. For conversion complaints: locate/extend the client's post-conversion script set in `Quorum.QLS.Conversion` rather than hand-patching rows. For editability: G3 version check vs 110953 fix.

**Anchors:** SF 26-01068779, 25-01055157, 25-01034951, 23-00904723, 26-01065911, 26-01064995, 25-01032356, 26-01117341, 26-01117352, 26-01115788, 25-01005060, 24-00970983, 24-00951479; ADO 86435, 110953.

---

### 3.5 Date & Document — attach/upload blocked, wrong metadata

**Signature.** Attach fails for specific document types while others work; PDFs rejected; "Object with such name already exists in the specified folder"; Posted By shows "(no create user)"; uploaded file name mangled (special character substitution) and link errors; multiple uploads misbehave; document types missing from dropdowns in one environment.

**Root causes (five distinct).**
1. **Doc-type–level config** — a document type must be wired to a content type / staging config before files can attach. SF 26-01103286 (Memorandum of Lease and Release/Surrender types couldn't attach; *"config delivered to customer"*), SF 25-01054535 (*"Applied standard config changes to set up DD config (script attached SRCL_DD_Staging_Config.sql)"*), SF 26-01123453 (added doc types to LSE and FEE = config). Doc-type visibility per environment is an enable flag: SF 25-01040727 (*"Customer has updated the Document types to enable them and make them visible"*).
2. **Allowed file-extension list** — case-sensitive list in QLS config; `.PDF` and `.pdf` are distinct entries. SF 25-01021204 (*"updated QLS configuration to include .PDF & .pdf. Updated Doc type name in DD to match what QLS was sending over"*), SF 26-01064866 (CAP extension error; *"sent config to add '.PDF' to allowed list of file extensions"*).
3. **Duplicate-name regression** — QLS used to auto-rename same-named files on the Date/Docs screen; regression threw "Object with such name already exists in the specified folder". ADO Bug **1701865** (EQC), Closed, **2024.10 + 2025.04 Hotfix Completed** (prior partial fix #1675992 had regressed in a 2021.04 OOC hotfix patch).
4. **Posted By nulled** — after Save+Retrieve, attachment shows "(no create user)". ADO Bug **1747290**, Closed, hotfixed **2023.04→2025.04**. Related configs on that screen: `AllowSelectFile`, `ShowScanMenus` (both =1 for upload UI). Document name source of truth: `SARCH_CTRL_DOC.DOC_NM`.
5. **File-name encoding (QLA upload)** — non-ASCII substitution corrupted the stored name so the hyperlink 404s. SF 25-01015732 (Software Defect, closed "No action taken" — workaround: re-upload with ASCII-only name).

**Fix recipe.** Identify which of the five: (type-specific → 1), (extension-specific → 2), (duplicate name → 3, version check), (metadata fields wrong → 4, version check), (name mangled → 5, rename + re-upload). For 1–2, deliver config script on the client metadata layer and match the DD/Document-Direct doc-type name exactly to what QLS sends.

**Anchors:** SF 26-01103286, 25-01054535, 26-01123453, 25-01040727, 25-01021204, 26-01064866, 25-01015732, 24-00961362 (multi-upload issues), 24-00950962 (multiple documents on one Date/Doc row — see also ADO 1374022 QLA interface: multiple QLA docs with same QLS doc type collapse onto one record, QLATODOCMG batch, hotfixed 2020.09→2023.04); ADO 1701865, 1675992, 1747290, 1374022.

---

### 3.6 Document repository — missing files, dead links, OpenText/Documentum paths

**Signature.** Attachment icon present but open/download fails: "This document cannot be found in the Repository"; documents show Scan Complete/Linked status but the physical file is gone from the server and metadata absent from `SARCH_CTRL_DOC`; Date & Doc URL links (OpenText) wrong or unopenable after conversion/upgrade.

**Root causes.**
1. **Repository path config + stale services** — repository root config must point exactly to the `...\Document` folder; after correcting it, QLS **Web and MT services must be restarted** before it takes effect. ADO Bug **1797618** (GEC; predecessor #1775346).
2. **Linked-file delete defect** — with config `DELETE_DOCUMENTS_FROM_REPOSITORY` ON and a single file Linked to multiple agreements, deleting from ONE agreement deleted the file (and `SARCH_CTRL_DOC` metadata) for ALL — 310 PRD documents stranded at "Scan Complete" with no file. ADO Bug **1594716** (CRW), Closed, **2022.04 Hotfix**; copy path uses `DATEDOC_COPY` stored procedure.
3. **Conversion doc-links** — migrated OpenText links dead until conversion flags flipped: *"Ran script to flip CONVERT_IND to 1 for OAP docs and rerun conversion queries"* — script `52.LIS - 25-01047309 Doc Links.sql` in `Quorum.QLS.Conversion` (XOM/PNR set). SF 23-00933606 (URL links can't be opened/modified — resolved within APA upgrade project) is the same family.

**Fix recipe.** For repository errors on ALL existing docs but new uploads fine → path config + service restart (1797618 pattern). For selectively missing files with Scan Complete status → check 1594716 exposure (config ON + linked docs; version check; files may be unrecoverable — restore from DMS/backup). For conversion link families → post-conversion script, not per-row hand edits.

**Anchors:** SF 25-01047309, 23-00933606, 23-00905006 / 22-00874584 (Date Doc conversion review); ADO 1797618, 1775346, 1594716.

---

### 3.7 "Can't add documents older than 1900" — application MinDate

**Signature.** Date and Document (and recording data) rejects any date before 1/1/1900.

**Root cause.** Global minimum-date config key `QLandGlobal / MinDate` in `LIS.QARCH_CNFG_CTRL` — default floor 1/1/1900; clients with older instruments need it lowered. CONFIRMED — resolution carried the full insert:

```sql
insert into LIS.QARCH_CNFG_CTRL
  (KEY_GRP_NM, KEY_NM, KEY_DESCR, KEY_VALUE, KEY_VALUE_ALLOW_NULL_IND, KEY_VALUE_TYPE_CD,
   KEY_VALUE_MIN, KEY_VALUE_MAX, KEY_VALUE_CODETABLE_ID, ALLOW_USER_OVERRIDE_IND,
   ENVIRONMENT_SPECIFIC_IND, USER_ID, UPDT_DT, APP_LAYER_CD, HIST_IDX)
values
  ('QLandGlobal', 'MinDate', 'Set Minimum Date for Application', '1/1/1800', 0, 8,
   null, null, null, 0, 0, 'LIS', to_date('22-07-2010 11:40:30','dd-mm-yyyy hh24:mi:ss'), 'QSPR', 4269);
```
(Adjust `KEY_VALUE` to the floor the client needs; check for an existing row first — UPDATE instead of INSERT if present.)

**Anchors:** SF 24-00983402 (verbatim symptom + resolution SQL above).

---

### 3.8 Notes & Remarks — missing after conversion, duplicated categories, category config

**Signature.** Notes absent after an upgrade/conversion (Agreement Header notes, converted-payment notes, property note categories); Remark Category dropdown shows duplicates; requests to add new remark categories; Qlaris "Notes" vs QLS "Remarks" mapping confusion.

**Root causes.**
1. **Conversion data gaps** — converted agreements/payments missing their notes; fixed by targeted data scripts (SF 25-01047279 *"Ran data script - same as #25-01047282"*; SF 26-01085763 CONV payments → manual payments missing notes; SF 23-00933562 note categories missing in Property post-upgrade).
2. **Duplicate remark-category rows** — duplicated code-table entries; *"script to delete duplicated remarks were developed"* (SF 23-00925987, DEO).
3. **Category adds are config** — new remark/note categories are code-table maintenance (SF 24-00982508, 23-00933496). Mass note updates delivered as scripts (SF 24-00947281 / 23-00934316, script C919544).
4. **Web/Qlaris naming** — Agreement Header "Notes" in Qlaris = "Remarks" in QLS classic; not a data loss (SF 25-01047278).

**Fix recipe.** Missing-notes claims: first prove rows absent in the note tables for the affected keys (vs UI filter/category visibility), then deliver a conversion-followup data script; for duplicates, dedupe script keyed on category code keeping lowest key. Recordation-detail mass corrections likewise ship as scripts (SF 25-01027121 "Add Script to mass correct Recordation Details").

**Anchors:** SF 25-01047279, 25-01047282, 25-01047278, 26-01085763, 23-00933562, 23-00925987, 24-00982508, 23-00933496, 24-00947281, 23-00934316, 25-01027121, 25-01051603 (Notes formatting — config), 24-00947475 (Date&Doc add-new + missing note categories).

---

## 4. Known ADO items (fixed-in reference)

| ADO | Title (short) | State | Fixed-in evidence |
|---|---|---|---|
| **1791243** | EQC - Trailing space in provision response (`ProvisionsController.cs` / `ProvisionsFieldUpdate`) | Closed | Tags: 2024.04 / 2024.10 / 2025.04 / 2026.04 Hotfix Completed (CONFIRMED via tags) |
| **1731536** | Provision Response dropdown ordering — metadata check-in (`SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG_WEB`) | Closed | 2023.04→2025.04 Hotfix Completed |
| **192663** | Mass Change Provision Response dropdown empty (`@RESP_DATA_CATG` bind) | Proposed (fix = metadata script) | Client-applied registered-SQL fix (EQC retested OK) |
| **110953** | Numeric provision response not editable when `arrg_stage<>NEW` (model-added) | Closed | APA post-go-live maintenance (INFERRED build) |
| **86435** | Provision defaults from `STIPULATION_TYPES` (`DFLT_PROV_VALUE` etc.) — defines `PROV_RESPONSE` composition | Closed | 2019.09 QA |
| **115665** | Lease Provisions displaying Doc Type data when no document (`PROV_LOCN_DOCTYPE`) | Closed | Includes verbatim diagnostic SQL (section 5) |
| **1701865** | "Object with such name already exists in the specified folder" on Date&Doc attach | Closed | 2024.10 + 2025.04 Hotfix Completed (regression of #1675992) |
| **1747290** | Date & Document "Posted By" nulled to "(no create user)" | Closed | 2023.04→2025.04 Hotfix Completed |
| **1594716** | Docs Scan Complete but file missing from server & `SARCH_CTRL_DOC` (`DELETE_DOCUMENTS_FROM_REPOSITORY` + linked docs) | Closed | 2022.04 Hotfix Completed |
| **1797618** | "This document cannot be found in the Repository" (GEC) — repo path config + service restart | Closed | Config resolution (no code) |
| **1374022** | Multiple QLA docs with same QLS Doc Type collapse to one Date&Doc record (`QLATODOCMG`) | Closed | 2020.09→2023.04 Hotfix Completed |
| **1747273** | Date & Document description shows "No description" in attachment pane | Closed | Bug Bounty fix (PR hid read-only editor) |

Label any fixed-in claim **INFERRED** unless release notes confirm; tags above are hotfix-train tags, reliable but re-verify against the client's exact build branch (`hotfix/17.2x.y`).

---

## 5. Diagnostic SQL (Oracle, `lis` schema — verbatim from cases/bugs unless marked)

**Provision rows for an agreement (from ADO 115665, verbatim):**
```sql
select s.prov_locn_doctype, s.*
  from stipulation_provisions s
 where s.arrg_key in (select arrg_key from all_agreements a where a.agmt_num = 'REPLACEAGMTNUM');
```

**Provisions screen grid query (registered-SQL shape, from ADO 115665, verbatim):**
```sql
SELECT DISTINCT A.DISPLAY_SEQ, B.STIP_TYPE_DESC, DECODE(A.EXST_FLAG,'Y','Yes','N','No','') as EXST_FLAG,
       A.PROV_RESPONSE, A.PROV_LOCN_DOCTYPE, A.PROV_LOCN_PAGENO, A.PARAG_NO, C.FORM_TYPE_DESC,
       A.RMK_CNT, A.UPDT_OPER, A.UPDT_DATE, A.STIP_KEY, A.FORM_TYPE_CODE, A.STIP_TYPE_CODE,
       A.STIP_DATE_KEY, A.STIP_GRP_SEQ, GRP.STIP_GRP_DESCR, A.RESP_RESPONSE
  FROM STIPULATION_PROVISIONS A
  JOIN STIPULATION_TYPES B ON B.STIP_TYPE_CODE = A.STIP_TYPE_CODE AND B.STIP_CATG_CODE = 'PRV'
  LEFT JOIN FORM_TYPES C ON C.FORM_TYPE_CODE = A.FORM_TYPE_CODE
  LEFT JOIN STIP_GROUPS GRP ON GRP.STIP_GRP_CD = A.STIP_GRP_CD
 WHERE A.ARRG_KEY = :arrg_key
 ORDER BY A.DISPLAY_SEQ ASC;
```

**Orphan doc-type-without-document check (ADO 115665, verbatim):**
```sql
select * from stipulation_provisions s
 where (s.exst_flag = 'N' or s.exst_flag is null)
   and s.prov_locn_doctype is not null;
```

**Registered-SQL fix for empty Mass-Change Response dropdown (ADO 192663, verbatim):**
```sql
UPDATE QLS_QFCONL.QARCH_SQL
   SET SQL_STATEMENT = REPLACE(SQL_STATEMENT, '@RESP_DATA_CATG', '@PROV_DATA_CATG')
 WHERE REGISTERED_SQL_NM = 'SELECT_PROV_RESPONSE_VALUE_LIST_BY_CATG' AND APP_LAYER_CD = 'QLS';
```

**MinDate config (SF 24-00983402, verbatim):** see section 3.7.

**STIP_SEQ drift check (derived from SF 24-00993887 — verification SQL, `NOT YET RUN` unless metadata server connected):**
```sql
SELECT (SELECT MAX(STIP_KEY) FROM LIS.STIPULATION_PROVISIONS) AS MAX_KEY,
       LIS.STIP_SEQ.NEXTVAL AS SEQ_NEXT
  FROM DUAL;  -- INFERRED name from resolution text; confirm sequence owner/name in USER_SEQUENCES first
```

---

## 6. Expected-Behavior FAQ

- **"Why does the top Provisions grid show a combined value like '5000 Dollars'?"** `PROV_RESPONSE` is intentionally a composed display string (PROV_VALUE + unit description resolved at entry) — ADO 86435. Editing must go through the Detail pane; the grid value regenerates.
- **"Provision responses come from a dropdown — how can bad values exist?"** Conversion loads write `PROV_RESPONSE` directly and bypass the dropdown; interactive rows could also acquire trailing spaces via the 1791243 defect until the 2024.04+ hotfix. Both look like "impossible" values but are explainable.
- **"We asked for new provisions/models — is that a bug fix?"** No — provision types, models, value lists (`STIP_PROV_DATA_VALUES`) and defaults (`STIPULATION_TYPES.DFLT_*`) are configuration; route as Application Configuration with a metadata script.
- **"Document types differ between PRD and UAT — data loss?"** Usually the enable/visible flag on doc types per environment (SF 25-01040727). Compare code tables before assuming loss.
- **"Qlaris shows Notes but QLS shows Remarks — where did my data go?"** Same underlying records; naming differs between web (Qlaris) and classic (SF 25-01047278).
- **"Read-only users need add rights ONLY on Date and Doc"** — security-object design question (SF 24-00968485): grant query/add/delete/execute on the Date & Doc screen objects in a dedicated group; route to Security & Access skill for object names.

## 7. Escalation

- **Code change (G5):** anything reproducing 1791243-style composition bugs on a build ≥ 2026.04, or new attach/delete data-loss behavior → L4 Triaged doc + ADO bug in `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` (or `Quorum\North America\Upstream\Land RnD` for current PI). Repos: `Quorum.QLS.Web` (ProvisionsController, Date&Doc), `Quorum.QLS.Metadata` (registered SQL, config), `Quorum.QLS.Conversion` (post-conversion scripts).
- **Data-loss (missing repository files):** engage Cloud Ops for file-system/DMS restore BEFORE any rerun of delete-capable processes; 1594716 shows files can be unrecoverable.
- **Conversion families (XOM/PNR, APA, DEO, EQC/Olympus):** extend the client's existing post-conversion script set in `Quorum.QLS.Conversion` — never hand-patch individual rows.
- DEV-tier metadata caveat: schema/config findings on `<CLIENT>_LND_DEV17` are CONFIRMED anchors; client-PRD data-state claims stay INFERRED until PRD SQL is run.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
