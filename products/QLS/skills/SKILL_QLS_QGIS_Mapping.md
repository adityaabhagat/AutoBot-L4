# SKILL: QLS — QGIS / Mapping & Polygen

**Version:** 1.0 | **Created:** 2026-09-03 | **Product:** My Quorum Land (QLS) — `Product_list__c = 'My Quorum Land'`
**Scope:** Coverage-plan group **#7 QGIS / Mapping & Polygen** (503 cases, 163 actionable): the QGIS ArcGIS Pro Add-In (Quorum GIS tab), Polygen (polygon generation), Agreement Linker / Mass Link / Working List, QGIS nightly SDE batch jobs (Sync Attributes, Transaction Models, GDB/FTP exports), Web Map, Esri licensing/portal, map-status synchronization between QGIS feature classes and QLS tables.
**Companion skill:** `SKILL_QLS_QLA_WebSuite.md` (QLA parcel polygen shares the Polygen service — see §4 C for the QLA-parcel ORA-00904 signature).
**DB:** Oracle. QLS core = `LIS` schema; GIS side = `QGIS` schema (feature classes) + `QGIS_ARCH` / `QLS_QFCONL` (config); SDE geodatabase managed by Esri.

> **Evidence base:** 76 distinct SF case headers scanned across 4 validated LIMIT-25 pages (category `QGIS - *` actionable, newest-first, + `%Polygen%` subject sweep), Resolution/Description deep-dives on 30 cases, and 18 ADO work items (search + hotfix-tag verification). Every claim cites a verbatim SF case number and/or ADO ID. Fixed-in builds **INFERRED** from hotfix tags unless release-note-confirmed.
> **PII:** individual customer names/emails redacted; 3-letter client prefixes retained (org identifiers).

---

## 1. Quick Triage Table

| Symptom | Likely cause | Go to |
|---|---|---|
| Polygen "Object cannot be cast from DBNull to other types" on Generate | `LEGAL_DESCRIPTION_SEGMENTS.SEG_ACRE` is NULL on the segment; defect also flips `MAP_STAT` to GEN despite failure (ADO **1779514**; SF 26-01064358) | §4 A |
| Polygen not running — `ORA-00904: "q"."QCODE_SURVEY_TYPESURVEY_TYPE_CD": invalid identifier` against `QCTRL_PRCL_LDS` | EF-Core shadow-column vs QLA-parcel table schema mismatch (build/DB out of step) — QLA Parcel polygen path (SF 26-01109433) | §4 C |
| Polygen fails: "Objects in this object class cannot be updated outside of an edit session" at `QPolyGeneratorBase.DeleteExistingDetail` | ArcGIS Pro edit-session defect in current build, TX LGL SEG job (SF 24-00980347) | §4 A |
| Nightly Polygen: "Missing QPOLYGENCONSOLE.EXE" after applying a QGIS hotfix | Hotfix NI package shipped without the EXE (SF 25-01035515, Sept-2024 HF package) | §4 B |
| Polygen runs but legal stays in tree / QLS map status stays `REQ` | Map-status writeback defect in QGIS Pro Add-In (ADO **1779491**); or "Standard View" vs `LAND_DIVISIONGEOG_KEY` config difference | §5 |
| Polygen shows green/success but Log Explorer shows FAIL | Result-pane defect: `QGIS.QGIS_LOG_ACTION.RESULT_CD='FAIL'` not surfaced (ADO **1595611**) | §4 A |
| Polygen regenerates legals from a previous session / performance degrades in one session | Session-ID caching defect, QGIS Pro 3.1 (ADO **1639573**) | §4 A |
| Nothing polygened since a date / nightly job "not completing" | Nightly chain broken: check scheduler, env var for Polygen console (2024.04 upgrade KB), FTP/SFTP hosts, ArcPro upgrade collateral (SF 25-01042726, 26-01064769, ADO **1729754**) | §4 B |
| Nightly "Sync Attributes for QLS Agreements" fails `ORA-30926: unable to get a stable set of rows` | Duplicate polygon rows in `QGIS.ALL_LGL_SEG_PLY` for same agreement+segment (double auto-map) feeding the confidence MERGE (SF 26-01109725; same family ADO **134423**) | §4 B |
| Rolled-up subdivision polygon missing `SOB_SYS_FK` after nightly TM | Append column-mapping defect in Sync Attributes TM rollup (ADO **1687847**, regression, 2022.04–2024.04 HFs) | §4 B |
| Polygon records mass-deleted by nightly job | `removeDeletedAgreements` sub-procedure ran even with global config disabled (ADO **1687847**; fix distributed as updated Sync Attributes python file — SF 24-00987484) | §4 B |
| GDB export fails to upload / FTP layers stale | Job-order or host config: SFTP job running before `export_all`; FTP host details stale after infra move (SF 26-01098944, 26-01070042, 26-01064769) | §4 B |
| Agreement Linker sets Capture Method to BROKER instead of configured default | Defect ignoring `DefaultCaptureMethod`/`UseDefaultValues_AgmtLink` configs (ADO **1777299**, fixed 2023.04–2025.04 HFs via `Quorum.QGIS.ArcGISPro.AddIn` PR 123541) | §6 |
| Mass Linker crashes ArcPro / shows stale results from last session | ADO **1593313** (no reset between sessions); Working List "Group By" crash (SF 24-00971828) | §6 |
| Agreement link fails when selecting shape on an SDE feature class (e.g. `QGIS.QGIS_SURVEY_PLSS_SECTIONS`) | ArcGIS Pro 3.1 compatibility defect (ADO **1646327**, merged to core via **1656008**) | §6 |
| Error linking certain polygons; table has shape columns mid-table | `ALL_AGREEMENTS_PLY` column order — shape/BLOB columns must be last; rebuild table (ADO **110788**, CHN/CHV migration script) | §6 |
| Custom agreement attributes not populated on linked polygons | Linker doesn't use client `GET_AGREEMENT_ATTRIBUTES` registered SQL in `QARCH_SQL` (ADO **1632290**, fixed for Generate/Mass Link/Working-List link) | §6 |
| Map status differs between QGIS feature class and QLS `ALL_AGREEMENTS` / `LEGAL_DESCRIPTION_SEGMENTS` | Writeback path defect or legal-vs-subdivision mapping mix (ADO **1653142**; SF 24-00979582, 24-00949667 MapLegalSegment) | §5 |
| Agreements re-flip to "Requested" overnight | Sync Attributes can't find the legal shape (legal-segment mapping enabled but client maps at subdivision) — `MapLegalSegment` config (SF 24-00949667) | §5 |
| New Polygen configuration won't save — `ORA-00001` on `PK_QARCH_GIS_POLYGEN` | `METADATA_PROFILE` not set (fixed by setting profile, e.g. `QINT`) (ADO **1650812**) | §7 |
| Polygen tool tree empty / config invisible in Pro app | Security-object casing: Polygen & Grid Source security objects must be camel-case, not ALL-CAPS (SF 26-01107511) | §7 |
| Web Map: `QGIS_PRDA1_DOJO Request Script Error` / portal URL error on launch | Client Esri portal / Secure-Gateway connectivity, not QLS code (ADO **1772706**; SF 25-01055483) | §8 |
| QGIS launch redirects users to Esri login | ArcGIS Pro licensing lost concurrent-use config — repoint to License Manager (SF 26-01103536) | §8 |
| GIS Calculated Area blank in QLS since some date | Warehouse sync job disabled — `WH_PopulateQlsWarehouseTables` config (SF 26-01099246); Calc Area missing from Legal Detail Poly layer was a defect (SF 23-00935976, March-2024 HF) | §9 |
| QLS Legal Description save takes minutes | SDE compress not running (`SDE.COMPRESS_LOG` stale) and/or synchronous map-status call on save (ADO **1681430**, **1732560**; KB "QGIS Desktop: Slow Performance in the App and SDE Compress") | §9 |

---

## 2. Concepts & Vocabulary

- **QGIS** = Quorum GIS: an **ArcGIS Pro Add-In** (`Quorum.QGIS.ArcGISPro.AddIn`, service layer `Quorum.QGIS.ArcGISPro.ServiceInterface`, shared polygen engine `Quorum.QGIS.ArcGISPro.Shared`). Legacy era = ArcMap ("QGIS Desktop"). Hosted clients get a shared "QGIS Desktop machine" (Citrix-style; restarts are Cloud-Ops requests, SF 26-01118107).
- **Feature classes (QGIS schema, in SDE):** `QGIS.ALL_LGL_SEG_PLY` (legal-segment polygons; key `AGMT_KEY`, `MAP_STAT_DESCR`, `CAPTURE_MTHD_CD`), `QGIS.ALL_AGREEMENTS_PLY` (agreement/subdivision rollup; key `SOB_SYS_FK`), `QGIS.AGMT_OUTLINES`, `QLA_PLY` (QLA subdivision/parcel polygons). QLS-side status lives in `LIS.ALL_AGREEMENTS.MAP_STATUS` and `LIS.LEGAL_DESCRIPTION_SEGMENTS.MAP_STAT`.
- **Polygen** = polygon generation from legal descriptions (PLSS aliquots, TX surveys, league & labors…). Configured per survey type in **`QGIS_ARCH.QARCH_GIS_POLYGEN`** (tree SQL in column `GUI_TREE_SQL`; PK includes `SURVEY_TYPE_CD` + `METADATA_PROFILE`). Runs interactively from the Pro Add-In or headless via **`QPOLYGENCONSOLE.EXE`** in the nightly batch.
- **Map status lifecycle:** `REQ` (Requested/Requested-Automap) → polygen/link → `GEN`/`COM`/Mapped (+ "Mapped - Verified", "Needs Review", "Mapped Partial"). Statuses come from `MAP_STATUSES` / `QCODE_MAP_STAT`; capture methods from `QCODE_CAPTURE_METHOD`.
- **Nightly SDE batch:** `_SDE_Batch_Nightly.bat` + `Run_TM_Python.bat` run Transaction Models: **Sync Attributes** (QLS→QGIS attribute/status sync + confidence MERGE), Sync QLA Parcel Attributes, rollups (legal→subdivision dissolve/append), grid loads, `export_all` GDB export then SFTP upload. Work queue: `QGIS.QGIS_BATCH_REQUEST_QUEUE` (STATUS `WAIT`). Logs: `QGIS.QGIS_LOG_ACTION` (`RESULT_CD`), Log Explorer in the Add-In. Correct order matters: Sync Attributes before/after Polygen questions are common (SF 25-01009237); export before SFTP (SF 26-01098944).
- **GIS global configs** live in **`QLS_QFCONL.QARCH_CNFG_CTRL`** with `KEY_GRP_NM='GIS'` (e.g. `MapLegalSegment`, `LaunchMapStatusPrompt_Agreement`, `LaunchMapStatusPrompt_LD`) and per-env agreement-linker keys with `APP_LAYER_CD='ENV'` (`UseDefaultValues_AgmtLink`, `ShowRemarksPrompt`, `DefaultCaptureMethod`, `DEFAULT_MAP_STATUS`).
- **Hotfix trains:** QGIS Add-In fixes ride the same QLS trains — tags `2022.04/2023.04/2024.04/2024.10/2025.04 Hotfix (Completed)`, branches `hotfix/17.1.26` (2023.04), `17.2.10` (2024.04), `17.3.6` (2024.10), `17.4.5` (2025.04) (from ADO 1777299 automation comment). "Fixed-in" claims below are **INFERRED** from these tags.

---

## 3. Decision Tree

```
Polygen problem?
├─ Single legal fails to generate (error text present)
│   ├─ "DBNull" → §4 A (SEG_ACRE null; ADO 1779514)
│   ├─ "outside of an edit session" → §4 A (ADO/SF 24-00980347)
│   ├─ ORA-00904 QCODE_SURVEY_TYPE… on QCTRL_PRCL_LDS → §4 C (QLA parcel path)
│   ├─ "invalid legal description" but data looks valid → §4 A / §5 (24-00979582)
│   └─ padded-vs-unpadded legal key mismatch → §4 A (25-01053481)
├─ Nothing generates / nightly silent → §4 B (console EXE, env var, scheduler, ArcPro upgrade)
├─ Generates but status wrong / stays in tree → §5 (map-status writeback)
└─ Config screen/save problem → §7 (QARCH_GIS_POLYGEN, security casing, METADATA_PROFILE)

Nightly batch failed?
├─ ORA-30926 on Sync Attributes → §4 B duplicates in ALL_LGL_SEG_PLY
├─ Rollup missing SOB_SYS_FK → §4 B (ADO 1687847)
├─ Mass deletions of polygons → §4 B (removeDeletedAgreements)
├─ GDB/FTP upload failed → §4 B (job order, host config)
└─ Python/TM errors after ArcPro upgrade → §4 B (24-00972906, 25-01033805)

Linking problem? → §6
Map status mismatch QGIS vs QLS? → §5
Web map / Esri login / portal? → §8
Calculated area / acreage / performance? → §9
```

---

## 4. Cluster A/B/C — Polygen failures & the nightly batch

### A. Interactive Polygen failures (generate errors)

**A1 — DBNull cast, the #1 recurring signature.**
- **Signature:** Generate fails "Object cannot be cast from DBNull to other types."; worse, `LEGAL_DESCRIPTION_SEGMENTS.MAP_STAT` flips to `GEN` anyway so the segment disappears from the Polygen tree.
- **Root cause (CONFIRMED, ADO 1779514, client CNX):** segment has `SEG_ACRE = NULL`. Setting any value ≥ 0 makes generation succeed.
- **Fix recipe:** short-term — update null `SEG_ACRE` to 0 (SF 26-01064358 resolution: "Bug fixed in latest GA release. Short-term script used to populate the null lg_seg_acre value to 0."). Long-term — code fix hotfixed across 2023.04/2024.04/2024.10/2025.04 trains (tags on ADO 1779514, INFERRED).
- **Anchors:** SF 26-01064358 (POLYGEN not Running, Software Defect), ADO 1779514 (contains verbatim diagnostic SQL — see §11).

**A2 — Edit-session error (TX LGL SEG).**
- **Signature:** nightly/interactive polygen errors `Error generating Segment. Objects in this object class cannot be updated outside of an edit session.` at `ArcGIS.Core.Data.Row.Delete()` → `Quorum.QGIS.ArcGISPro.Shared\Polygen\Generator\QPolyGeneratorBase.cs:930 (DeleteExistingDetail)` / `:456 (ProcessSegmentKey)`.
- **Root cause:** build-specific defect ("Nothing changed in our configurations. It started in this current build" — SF 24-00980347). Regeneration path deletes existing detail rows outside an Esri edit session.
- **Anchors:** SF 24-00980347 (verbatim stack). Status closed-no-response; treat as version issue (G3) — check client build against hotfix tags before debugging data.

**A3 — False success / stale sessions.**
- Log Explorer shows FAIL (`QGIS.QGIS_LOG_ACTION.RESULT_CD='FAIL'`) but Polygen Results pane shows green — ADO **1595611** (2022.04+2023.04 HF, INFERRED).
- Polygen re-processes legals from the previous Session ID and slows down; Refresh doesn't clear cached legals — ADO **1639573** (QGIS Pro 3.1, COP).
- Legal-call SQL compares padded vs not-padded keys → specific polygons fail: fixed by "modif[ying] the legal call sql to compare not-padded records 1 to 1" (SF 25-01053481, Application Configuration).
- "Polygen Failing" after consuming a 2023.04 hotfix — regression, re-fixed on all trains (ADO **1672961**, clients MIT/DMB).
- Polygen Spreadsheet Importer says success but tool not populated (import tree driven by `QARCH_GIS_POLYGEN.GUI_TREE_SQL`) — SF 23-00932193 / ADO **1636631** (client MRO; 2022.04+2023.04 HF).

### B. Nightly SDE batch & exports

**B1 — Sync Attributes ORA-30926 (duplicate polygons).**
- **Signature:** nightly step "Sync Attributes for QLS Agreements" fails `ORA-30926: unable to get a stable set of rows in the source tables`; QGIS↔QLS statuses drift afterwards.
- **Root cause (CONFIRMED, SF 26-01109725 resolution):** duplicate rows in `QGIS.ALL_LGL_SEG_PLY` for the same agreement+segment (example: AGMT 339528002 / AGMT_KEY 281398, seg 2, OBJECTIDs 841098+841099, from a double auto-map generation) — the confidence-update MERGE receives two source rows for one target. 18 more latent duplicate pairs found in the same investigation. Same signature at SHL years earlier (ADO **134423**: "remove duplicate data").
- **Fix recipe:** find + delete the duplicate polygon rows (keep one), re-run the step; then hunt the double-generation source.
- **Anchors:** SF 26-01109725 (Software Defect), ADO 134423.

**B2 — Rollup/append loses SOB_SYS_FK; unintended mass deletes.**
- ADO **1687847** (regression, 2024.10 AHT): TM Sync Attributes rollup dissolves legal segments into `ALL_AGREEMENTS_PLY` but the Append column mapping fails, so `ALL_LGL_SEG_PLY.AGMT_KEY → ALL_AGREEMENTS_PLY.SOB_SYS_FK` never transfers → orphan shapes with no tie-back. Also: batch execution unintentionally ran the `removeDeletedAgreements` sub-procedure even when its global config was disabled. Hotfixed 2022.04/2023.04/2024.04 (tags, INFERRED).
- Field fix seen in support: engineering sent an **updated Sync Attributes python file** that included the fix for "polygon records getting mass deleted incorrectly" (SF 24-00987484 resolution — also the case where acreage calc on `ALL_LGL_SEG_PLY` wasn't populating).

**B3 — Nightly Polygen silently not running.**
- After ArcPro/Add-In upgrades polygen may vanish from the nightly: ADO **1729754** (ArcPro 3.4) — per the **2024.04 Upgrade KB an environment variable must point at the appropriate folder** for Polygen to work with nightly batch jobs; SDE nightly job command then runs it.
- Hotfix package missing `QPOLYGENCONSOLE.EXE` (SF 25-01035515 — "Previous NI package was missing the QPOLYGENCONSOLE.EXE file").
- "polygen not running since 03/26" = Deployment Issue (SF 25-01023945); "nothing polygened since early August" (SF 25-01042726). Always check: scheduler ran? console EXE present? env var set? errors in `QGIS_LOG_ACTION`?
- Nightly job can also be deliberately disabled per client request (SF 26-01112527 — "Request to turn off polygen in nightly batch job has been completed").
- ArcPro 3.1-upgrade collateral: TM python errors (SF 24-00972906), polygen batch failures in DEV (SF 25-01033805), generic "QGIS Error after the upgrade of QGIS add on and Arcgis to 3.1" (SF 25-01051358).

**B4 — GDB export / FTP layer refresh.**
- SFTP upload job scheduled **before** the `export_all` batch job → truncated/failed GDB uploads. Fix: reorder so export completes first (SF 26-01098944; repeat at 26-01070042).
- Client-side local layers stale because FTP host details changed: "script to update ftp host details has been developed" (SF 26-01064769, Software Defect).
- Grid feature classes invisible to loads until **synonyms** created in Quorum Database Manager (SF 26-01084935 "GIS Loading Issue").
- Grid/intersection engine layer changes (e.g. adding `TRACTS_PLY` CCS logic) are config/services work, not defects (SF 26-01067791).

### C. QLA-parcel Polygen path (shared service)

- **Signature:** Polygen dead for parcels; log shows EF-Core SQL `SELECT "q"."SEG_ID", … "q"."QCODE_SURVEY_TYPESURVEY_TYPE_CD" … FROM "QCTRL_PRCL_LDS" "q"` failing `ORA-00904: "q"."QCODE_SURVEY_TYPESURVEY_TYPE_CD": invalid identifier`.
- **Read:** `QCODE_SURVEY_TYPESURVEY_TYPE_CD` is an EF shadow/navigation column name — the app build expects a column the DB doesn't have (or FK mapping broken): **schema vs build mismatch on the QLA parcel legal-segments table `QCTRL_PRCL_LDS`** (QLAI schema). Align DB migration/patch level with app build.
- ADO 1779514 also notes a *separate* config-side failure for "QLA Parcel LglSeg - Tax Parcel" polygen configuration — check `LD_TAX_PARCEL_HEADER.GIS_TAX_PARCEL_ID` chain (§11 SQL) before blaming code.
- **Anchors:** SF 26-01109433 (verbatim log), ADO 1779514 (comment), ADO 1585122 ("Sync QLA Parcel Attributes" TM logging gaps).

---

## 5. Cluster — Map-status sync & legal-vs-subdivision mapping

**Symptom family:** statuses disagree between QGIS feature classes and QLS screens/tables; agreements re-flip to "Requested"; users can't set a status back; polygen finishes but status not flipped from `REQ`.

- **Writeback defects (version issues first):**
  - ADO **1779491** (SJP/CORE): running Polygen didn't update QLS map status, legal stayed in the tree; note that "Standard View" vs `LAND_DIVISIONGEOG_KEY` search-results setup changed behavior. Hotfixed 2023.04→2025.04 (tags, INFERRED).
  - ADO **1653142** (COP, Pro 3.1): `MAP_STAT_DESCR` in `QGIS.ALL_LGL_SEG_PLY`/`ALL_AGREEMENTS_PLY` not updated though `LIS.ALL_AGREEMENTS.MAP_STATUS` / `LEGAL_DESCRIPTION_SEGMENTS.MAP_STAT` did update (verbatim verification SQL in §11).
  - ADO **1588028** (WMN): polygen wrote agreement-level rows to `AGMT_OUTLINES` / map status at wrong level; behavior depends on `MapLegalSegment` (0 ⇒ new agreements don't appear in the generate screen at legal level).
- **Configuration root cause — the WMN/Anadarko pattern (SF 24-00949667, rich writeup):** client maps at **Subdivision** level but `MapLegalSegment=1` (legacy inheritance) left legal-segment mapping on → nightly Sync Attributes can't find legal shapes → resets agreements to "Requested"; users can't flip status back in QLS or QGIS. Remediation plan from the case: set `QLS_QFCONL.QARCH_CNFG_CTRL` `KEY_GRP_NM='GIS', KEY_NM='MapLegalSegment'` to 0; disable legal-segment Polygen configs / enable Subdivision configs in `QGIS_ARCH.QARCH_GIS_POLYGEN`; update nightly scripts to subdivision-level configs; optionally enable `LaunchMapStatusPrompt_Agreement` / `LaunchMapStatusPrompt_LD` (popup on legal change — SF 24-00937969 is the "popup not received" config case); verify synonyms not pointing at `_STUB` views (`ALL_AGMTS_PLY_ALL_VW`, `ALL_AGMTS_PLY_EVW`, `LNK_GIS_LGL_SEG_PLY_EXISTS_VW`, `PRCL_PLY_EVW`); one-time status/polygon cleanup.
- **"Map status discrepancy QGIS vs QLS Legal" (SF 24-00979582, CNX cloud testing):** resolution combined (1) fixing an "invalid legal description" false failure, (2) changing which status polygen sets per error/result, (3) repointing polygen at a client-schema copy of the tax-parcel grid (`ESUITE_QCNX.CNX_TAX_PARCEL`).
- **Stuck "Polygon Requested"** with no error → check `QGIS_BATCH_REQUEST_QUEUE` for `WAIT` rows and whether nightly ran (SF 25-01034169; customer-cancelled, pattern only).
- **Legal-level polygons show "Unmapped" in working list** — depth information rows in the working list broke globe icon/search; depth removed from working list in 3.X GIS build (SF 24-00973070 resolution; related globe-icon defect SF 23-00933819, March HF).

---

## 6. Cluster — Agreement Linker / Mass Link / Working List

- **Default values ignored (ADO 1777299, XOM):** with `UseDefaultValues_AgmtLink=1`, `ShowRemarksPrompt=0`, `DefaultCaptureMethod='AMAP'`, `DEFAULT_MAP_STATUS='COM'` (all in `QARCH_CNFG_CTRL`, `APP_LAYER_CD='ENV'`), Link Legal Segment still wrote `CAPTURE_MTHD_CD='BROKER'` to `ALL_LGL_SEG_PLY`. Fixed in `Quorum.QGIS.ArcGISPro.AddIn` (source PR 123541 → hotfix PRs 123762–123765 on `hotfix/17.1.26|17.2.10|17.3.6|17.4.5` = 2023.04/2024.04/2024.10/2025.04; INFERRED from automation comment).
- **Mass Linker:** doesn't reset between sessions — previous agreement numbers/errors shown again (ADO **1593313**, 2022.04 HF); "MASS LINKER FUNCTIONALITY CRASHES" during cloud testing (SF 24-00979588).
- **Working List:** Actions → Refresh → Group By click crashes ArcPro every time (SF 24-00971828, Software Defect); Data Confidence dropdown missing (SF 24-00979584); Confidence Auto-Calculation option missing (SF 24-00971365, Transaction Models).
- **Link against SDE feature classes fails** (select shape on `QGIS.QGIS_SURVEY_PLSS_SECTIONS`, link from working list) — ArcGIS Pro 3.1 compatibility round (ADO **1646327**), plus **missing warning prompt** when linking to an agreement that already has a shape (ADO **1646835**); both merged core via ADO **1656008**. Note: link-to-already-linked shape does NOT override — user must run Unlink first (ADO **1669436**, open/New; expected behavior until prioritized).
- **Custom attributes:** linker/polygen must call client's `GET_AGREEMENT_ATTRIBUTES` registered SQL from `QARCH_SQL` — HES found custom fields ignored; fix routed all three paths (Generate Polygen, Mass Link, Working-List Link) through the registered SQL (ADO **1632290**, 2022.04–2024.04 HFs).
- **Column-order corruption:** errors linking specific polygons when `ALL_AGREEMENTS_PLY` shape columns aren't the last columns — rebuild the table (ADO **110788**; migration script `01_CHV_QGIS_ALL_AGREEMENTS_PLY Reorder`). Modern echo: "Null row appearing when linking directly to ALL_AGREEMENTS_PLY" (SF 26-01065599, In Development Queue — open defect, cite don't promise).
- **Search side:** QGIS Search results view error (SF 24-00978603), missing analyst searches after migration (SF 23-00915998), "Land Search - Operation not implemented" (SF 23-00916169, fixed pending HF), Search Criteria dropdowns defect (SF 25-01049622).

---

## 7. Cluster — Polygen/Grid configuration & security

- **Can't create a new Polygen configuration:** save throws `ORA-00001: unique constraint (PK_QARCH_GIS_POLYGEN)` on `SURVEY_TYPE_CD` — root cause was `METADATA_PROFILE` not set; once set (e.g. `QINT`) config saves (ADO **1650812**, 2023.04 HF tag).
- **Configs exist but Pro app can't see/authorize them:** Polygen and Grid Source **security objects are case-sensitive** — script to camel-case them (they were ALL-UPPER) + follow core walkthrough to configure League/Labor polygen (SF 26-01107511, HIL/Hilcorp; Application Configuration).
- **Grid source / nightly grid loads:** "Nightly Grid Load Job - Errors" resolved as B1 duplicates above (SF 26-01109725); grid-source management & Esri Framework categories fold here.
- **Sync-order question:** "Correct Order of Sync Attributes and Polygen" (SF 25-01009237, closed-no-response) — treat as expected-behavior/config question; core guidance is polygen requests drain first, sync attributes reconciles after (verify per client's `_SDE_Batch_Nightly.bat`).

---

## 8. Cluster — Web Map, Esri portal & licensing

- **DOJO Request Script Error / QGIS down (web map):** `Errorloading https://<client-gis-portal>/portal/sharing/rest/portals/self?f=json&callback=dojo_request_script_callbacks.dojo_request_script0` after launching QGIS from QLS — client connects via Secure Gateway directly (not Esri Portal); root cause was on the client/portal connectivity side (ADO **1772706** RCA, HEC; SF 25-01055483 closed-no-response).
- **Esri login redirect:** all users bounced to Esri sign-in when launching ArcGIS Pro integration — ArcGIS Pro had lost its **concurrent-use license** config; fix = repoint Pro to the License Manager host (SF 26-01103536; resolution names the license server host — treat host names as env-specific).
- **Web-map hotfix wave (2026):** repeated "QGIS Webmap Hotfix" delivery cases (SF 26-01081648, 26-01081639, 26-01081636, 26-01081642 "April 2026 HF (and QGIS Webmap Feb 2026 HF)") — when a client reports a webmap defect already fixed, route as **G3 version issue** and attach the current webmap HF.
- **SSO collateral:** "QGIS Web App Error After Enabling SSO" (SF 25-01035186, closed-deferred) — flag to Cloud Ops/platform, not product code.
- **Broken layer in web map:** parcel layer dead → "Fixed broken layer in web map" (SF 25-01060774); tmp search layer not working (SF 25-01060771). These are web-map config artifacts (layer/source definitions), not code.
- **Hosted QGIS Desktop:** user can't connect after outage → restart the QGIS Desktop machine (Cloud Ops; SF 26-01118107).

---

## 9. Cluster — Calculated area, acreage & GIS performance

- **GIS Calculated Area blank in QLS** since a date ⇒ the warehouse sync stopped: enable nightly sync via **`WH_PopulateQlsWarehouseTables`** configuration (SF 26-01099246, Application Configuration).
- **Calc Area missing from Legal Detail Poly layer** — product defect, fixed March 2024 HF (SF 23-00935976, INFERRED build).
- **Acreage calc on `ALL_LGL_SEG_PLY` not populating** — bundled with the Sync Attributes python fix (SF 24-00987484; see §4 B2).
- **Legal Description saves take minutes (QLS side, GIS root cause):**
  - SDE **compress** hasn't run — check `SDE.COMPRESS_LOG`; nightly batch should compress every night (ADO **1681430**, PHL/P66; Salesforce KB: "QGIS Desktop: Slow Performance in the App and SDE Compress"). If compress has failed for months, request nightly batch logs.
  - Synchronous **map-status update call on LD save**: a config makes saving Legal Description kick a QGIS map-status update; per engineering it's unnecessary because Sync Attributes covers it nightly — the on-save call was removed/disabled (ADO 1681430 history, ADO **1732560** AST; hotfixed 2022.04–2024.04, INFERRED).
- **Bulk polygen etiquette (context):** very large polygen runs (~14k tracts) can saturate shared mapping services — product added rate-limiting/isolation (ADO 1837928 story; different Land platform, cite only as context, NOT a QLS fix).

---

## 10. Known ADO items (QGIS group)

| ADO | Title (short) | State / fixed-in (tags, INFERRED) |
|---|---|---|
| 1779514 | CNX — "Object cannot be cast from DBNull" generating polygen (SEG_ACRE null) | Closed; 2023.04/2024.04/2024.10/2025.04 HF |
| 1779491 | SJP, CORE — Polygen not updating Map Status | Closed; 2023.04→2025.04 HF |
| 1672961 | MIT, DMB — Polygen failing (2023.04 HF regression) | Closed; 2022.04/2023.04/2024.04 HF |
| 1636631 | 23-00932193 Polygen Spreadsheet Importer (MRO) | Closed; 2022.04/2023.04 HF |
| 1650812 | Unable to create new Polygen configuration (ORA-00001 / METADATA_PROFILE) | Closed; 2023.04 HF |
| 1639573 | QGIS Pro 3.1 COP — Polygen Session-ID refresh/caching | Closed |
| 1595611 | ArcPro — Polygen green icon though Log Explorer FAIL | Closed; 2022.04/2023.04 HF |
| 1729754 | ArcPro 3.4 — Polygen does not work during Nightly Batch Jobs (env var) | Closed |
| 1687847 | TM Sync Attributes rollup — SOB_SYS_FK append mapping + removeDeletedAgreements | Closed; 2022.04/2023.04/2024.04 HF |
| 1585122 | TM module messages missing from LOG tables (incl. Sync QLA Parcel Attributes) | Closed; 2022.04 HF |
| 134423 | SHL — SDE batch investigation; Sync Attributes ORA-30926 duplicates | Closed |
| 108116 | P66 — nightly Sync Attributes failure (custom fields) | Closed |
| 1777299 | XOM — Agreement Linker ignores DefaultCaptureMethod (BROKER) | Closed; 2023.04→2025.04 HF (PR 123541) |
| 1593313 | Mass Agreement Linker not resetting between sessions | Closed; 2022.04 HF |
| 1646327 / 1646835 / 1656008 | Pro 3.1 COP — link vs SDE FC fails / missing warning prompt / core merge | Closed |
| 1669436 | DMB — Agreement Link Override (no override on linked shape) | **New/open** — workaround: Unlink first |
| 1632290 | HES — custom GET_AGREEMENT_ATTRIBUTES registered SQL ignored | Closed; 2022.04–2024.04 HF |
| 110788 | CHN — agreement linking fails; rebuild ALL_AGREEMENTS_PLY column order | Closed |
| 1653142 | Pro 3.1 COP — QGIS MAP_STAT_DESCR not updating | Closed |
| 1588028 | WMN — Polygen map status at agreement level / AGMT_OUTLINES | Closed; 2022.04 HF |
| 1681430 / 1732560 | PHL / AST — Legal Description save slow (SDE compress + on-save status call) | Closed; 2022.04–2024.04 HF |
| 1772706 | HEC — QGIS down, DOJO request script error (RCA) | Closed (client portal side) |

---

## 11. Diagnostic SQL (Oracle — verbatim from cases/work items)

**Polygen DBNull triage (from ADO 1779514):**
```sql
select * from lis.all_agreements where agmt_num = '306071000';
select * from lis.legal_description_segments where arrg_key = 611903;   -- check SEG_ACRE, MAP_STAT
SELECT * FROM LD_TAX_PARCEL_HEADER where LEGAL_DESC_KEY = 611903;       -- GIS_TAX_PARCEL_ID
SELECT * FROM gpol_area_counties where cnty_code in ('129') and st_code in ('37');
```

**Map-status compare QLS vs QGIS (from ADO 1653142):**
```sql
SELECT * FROM LEGAL_DESCRIPTION_SEGMENTS WHERE ARRG_KEY = '36405191';
SELECT MAP_STATUS FROM ALL_AGREEMENTS WHERE ARRG_KEY = '36405191';
SELECT * FROM QGIS.ALL_LGL_SEG_PLY WHERE AGMT_KEY = '36405191';
SELECT MAP_STAT_DESCR FROM QGIS.ALL_AGREEMENTS_PLY WHERE SOB_SYS_FK = '36405191';
```

**GIS configuration keys (from SF 24-00949667 / ADO 1777299):**
```sql
SELECT * FROM QLS_QFCONL.QARCH_CNFG_CTRL
 WHERE KEY_GRP_NM = 'GIS' AND KEY_NM IN ('MapLegalSegment','LaunchMapStatusPrompt_Agreement','LaunchMapStatusPrompt_LD');
select * from QARCH_CNFG_CTRL
 where KEY_NM IN ('UseDefaultValues_AgmtLink','ShowRemarksPrompt','DefaultCaptureMethod','DEFAULT_MAP_STATUS')
   and app_layer_cd = 'ENV';
SELECT * FROM QGIS_ARCH.QARCH_GIS_POLYGEN;           -- polygen configs (GUI_TREE_SQL, METADATA_PROFILE)
select * from QCODE_CAPTURE_METHOD;
select * from MAP_STATUSES;
```

**Nightly batch / duplicates / queue (from ADO 1687847, SF 26-01109725):**
```sql
SELECT * FROM QGIS.QGIS_BATCH_REQUEST_QUEUE WHERE PARAM_1 = '5071';     -- WAIT rows = pending work
-- duplicate polygons feeding ORA-30926 (pattern from 26-01109725):
SELECT AGMT_KEY, SEG_ID, COUNT(*) FROM QGIS.ALL_LGL_SEG_PLY
 GROUP BY AGMT_KEY, SEG_ID HAVING COUNT(*) > 1;                          -- NOT YET RUN template
```

**Stub-synonym check (from SF 24-00949667):**
```sql
SELECT * FROM ALL_SYNONYMS WHERE TABLE_NAME LIKE '%_STUB'
  AND SYNONYM_NAME IN ('ALL_AGMTS_PLY_ALL_VW','ALL_AGMTS_PLY_EVW','LNK_GIS_LGL_SEG_PLY_EXISTS_VW','PRCL_PLY_EVW');
```

**SDE performance (from ADO 1681430):**
```sql
SELECT * FROM SDE.COMPRESS_LOG ORDER BY COMPRESS_START DESC;             -- has compress run nightly?
```

---

## 12. Expected-Behavior FAQ

- **"Polygen left pane shows [0] next to legal descriptions even though records exist"** — the number is the count of records *selected by the user* for the Generate run, not total available (ADO 1672961 QA thread). Not a defect.
- **"Linking an agreement to an already-linked shape warns instead of overriding"** — current design; use the dedicated Unlink tool first (ADO 1669436 open enhancement).
- **"We changed a legal description but no re-map popup appeared"** — the popup is config-gated (`LaunchMapStatusPrompt_LD` / `_Agreement`); off by default at many clients (SF 24-00937969, 24-00949667).
- **"Can we polygen records already linked to a polygon?"** — no; Polygen skips records that already have a linked polygon (ADO 1636631 discussion). Reset map status to a Requested state first.
- **"Nightly reset our manual map statuses"** — Sync Attributes reconciles statuses from shapes; if you map at subdivision level, disable legal-segment mapping (`MapLegalSegment=0`) or statuses will keep flipping (SF 24-00949667).
- **"Who restarts the hosted QGIS Desktop machine?"** — Cloud Ops via case; standard after QLS outages (SF 26-01118107).

---

## 13. Escalation

1. **Version gate first:** the QGIS Add-In has a dense hotfix history (see §10). Match the client's Add-In/ArcGIS Pro version + hotfix tags before any data/code work — most "new" polygen/linker reports are already-fixed regressions (G3).
2. **Data gate:** SEG_ACRE nulls, duplicate `ALL_LGL_SEG_PLY` rows, `_STUB` synonyms, missing grid synonyms — run §11 SQL (label results CONFIRMED only on live env; otherwise NOT YET RUN).
3. **Engineering escalation path:** ADO area `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` (maintenance) / `Quorum\North America\Upstream\Land RnD` (current); repos `Quorum.QGIS.ArcGISPro.AddIn`, `Quorum.QGIS.ArcGISPro.ServiceInterface`, `Quorum.QGIS.ArcGISPro.Shared` (polygen engine), DB scripts in `Quorum.QLS.Database`.
4. **Esri/portal/licensing issues** (License Manager, portal URLs, Secure Gateway, SSO) → Cloud Ops + client GIS admins; not product defects.
5. **Never** hand-edit feature classes outside an Esri edit session; corrections to `ALL_LGL_SEG_PLY`/`ALL_AGREEMENTS_PLY` should go through the Add-In tools or reviewed scripts (edit-session errors are exactly what §4 A2 shows).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
