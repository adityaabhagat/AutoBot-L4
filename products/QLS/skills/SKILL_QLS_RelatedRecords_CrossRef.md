# SKILL — QLS Related Records & Cross References

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Scope (Coverage Plan group #11, 369 cases / 98 actionable):** Cross Reference node (types, rules, save), AFIS GL Cross Reference bulk screen, Related Agreements, Related Wells (grid, bulk edit, picklists, well-master sync), Non-Interest Related Wells, Prospect / Related Asset node.
> **Sources:** all-history Salesforce mining 2026-09-03 (3 SOQL survey pages + ~28 cases detail-sampled, SF case IDs verbatim) + ADO org `QuorumSoftware` (projects `QuorumSoftware`, `Quorum`) work-item mining. PII redacted (individual names removed; 3-letter client codes retained as anchors).
> **Maintained by Auto-Bot — the L4 issue solver built by Aditya Bhagat.**

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cluster | First check | Likely class |
|---|---|---|---|
| A Cross Reference Type is missing for one agreement/subject type | 3.1 | Cross-reference rules config (type ↔ agreement/subject type) | G2 Config |
| Cross Reference save errors / edited row erased when adding a new one | 3.1 | Build vs ADO 208479 family; client-env-only repro | G3 / G4 |
| AFIS GL Cross Reference "Retrieve All" caps out (20k of 23k rows) | 3.2 | `QUCAFISGLCROSSREF_*` SCREEN DEFAULTS config keys; ADO 1765085 | G2 Config (hotfixed) |
| Cannot add rows to AFIS GL Cross Reference — PK error, can't set seq manually | 3.2 | `AFIS_GL_XREF_SEQ` sequence behind MAX(key) | G4 Bad Data |
| Cross references missing after conversion / for specific rights (WIO, ORRI) | 3.3 | Conversion mapping completeness; insert scripts | G4 / Services |
| Cross References blank on Agreement Data Sheet (ADS) | 3.3 | `QCNFG_SCREEN_CONTROL_DISP.DISP_IND` for `ADS_AGMT_HDR_DTL`/`XREF_VALUE` | G2 Config |
| Related Wells bulk edit: delete doesn't stick / copy-paste rows won't save / blank rows | 3.4 | ADO 1759806 / 1788163 / 1808520 — hotfix tags | G3 Version |
| Related Wells "+" add-row leaves grid stuck spinning | 3.4 | ADO 1808378 (RelatedWells.js) — hotfixed; mock-save workaround | G3 Version |
| First Sale/1st Production Date won't stay populated on Related Well | 3.4 | ADO 1767423 (`WELL_INFO_QRA.FIRST_SALE_DATE`) | G3 Version |
| Deleting a Related Well throws ORA-00060 deadlock (`LIS.DEP_REL_WELL`) | 3.4 | Client custom trigger + missing index (GEC) | G5/G2 client-custom |
| Related Well picklist empty / no wells found at all | 3.5 | Well-master sync: qcode sync, `INT_QLSWL` schedule; registered SQL data | G4 Bad Data |
| Wells from the wrong state offered/related | 3.5 | Well-master filter/data (client feed) | G4 / G2 |
| Can't search related wells by Well ID in Land Web Screens | 3.5 | `WELL_KEY` exposure (fixed by product) | G3 Version |
| Can't add 2+ related agreements that share agreement # (different sub #) — duplicate error | 3.6 | Old defect, "available in current release" | G3 Version |
| "Already related" error but relationship invisible; audit shows one-sided delete | 3.6 | Asymmetric relationship rows — data fix script | G4 Bad Data |
| "Next Pay Due Date" blank on Related Agreements (large sets) | 3.6 | ADO 1760457 — hotfixed 2023.04→2025.04 | G3 Version |
| Related Agreement search feature broken | 3.6 | QPCK Session package script (26-01097129) | G4 / G3 |
| Prospect/Related Asset save fails silently; RA_TYPE values won't save | 3.7 | Code table 47235 missing `NODE_TYPE` column | G4 Bad Data |
| Cannot access Prospect node at all | 3.7 | `QVIEWRELATEDASSET` privilege on the user's role | G2 Config (security) |
| Non-Interest Related Well forces numeric Township/Range/Section | 3.7 | Grid 49250 metadata (`QARCH_CNFG_GRIDCTRL_COL_NET`); `LinkWell` config | G3 (metadata fix) |

---

## 2. Decision Tree

```
Symptom on the Cross Reference node?
├─ A type is missing from the dropdown for some agreement/subject type? → 3.1
├─ Save error / row overwritten? → 3.1
└─ Data missing (conversion, rights-driven, ADS display)? → 3.3
Symptom on AFIS GL Cross Reference (bulk financial xref screen)? → 3.2
Symptom on Related Wells?
├─ Grid behavior (bulk edit / add row / field won't persist / delete error)? → 3.4
└─ Wells missing or wrong wells offered (picklist/search/population)? → 3.5
Symptom on Related Agreements (add/delete/search/columns)? → 3.6
Symptom on Prospect / Related Asset / Non-Interest Related Well? → 3.7
```
Gate order stays G1→G2→G3→G4→G5. Grid-behavior symptoms in this group are overwhelmingly **G3** (2023.04→2025.04 hotfix wave on QLS Web grids); type/visibility symptoms are **G2** (cross-reference rules, screen-control config); "missing data" symptoms are **G4** (conversion or sync).

---

## 3. Symptom Clusters

### 3.1 Cross Reference types & save behavior

**Signature.** A needed Cross Reference Type does not appear in the Type dropdown for a given agreement/subject type ("WELL is not available as a Cross Reference Type for Contract Unitization", "Unable to Choose Legacy Agmt Number/File Number Cross Reference type"), or the screen errors/misbehaves on save.

**Root cause & fix.** Cross-reference availability is **rules configuration** — each type is activated per agreement/subject type:
- SF **24-00950684** resolution verbatim: *"ADDED TO cross reference rules"*.
- SF **24-00936733** resolution verbatim: *"Activate cross reference for the differents agreements types"*.
- SF **24-00988539** (`Unable to Choose Legacy Agmt Number/File Number Cross Reference type`) — *"Ran script in PRD for config change"*.
- SF **24-00943117** (`Saving a Cross Reference Change`) resolution verbatim: *"Added logic to ESUITE_QPHL.QLA_QROW_XREF_UPDT"* — the QLA↔QLS xref-update package (Oracle pkg `ESUITE_QPHL.QLA_QROW_XREF_UPDT`) needed a logic change; cite this when a QLA-sourced xref change won't save.
- Save-error/row-overwrite history: ADO **208479** `OXY - Cross Reference Save Error` (client-env-only repro; also noted: adding a new xref while another row is selected for editing erased that row). ADO **1783003** (`jQuery remains active on Multiple screens after clicking Add Row` — Payment, Cross Reference, Depth, Related Agreement) is the modern automated-test cousin.
- Note also SF 25-01044153 (`AOR X-Ref - No approval warning`) — approval-warning wiring per xref type is config.

**Fix recipe.** For "type missing": add the type↔agreement-type activation in the cross-reference rules (config script; Services deploys to PRD). For "save fails": reproduce in Core first — 208479-family issues were client-metadata-specific; compare xref screen metadata/registered SQL between Core and the client layer before opening a bug.

**Anchors:** SF 24-00950684, 24-00936733, 24-00988539, 24-00943117, 25-01044153, 25-01056307 (Type Codes), 24-00971353, 24-00969928 (Legacy Agreement Number xref, upgrade wave); ADO 208479, 1783003.

---

### 3.2 AFIS GL Cross Reference bulk screen (row caps & sequence)

**Signature A — not all rows retrieved.** SF **25-01050561**: "AFIS GL Cross Ref screen only displaying 20k rows when we select retrieve all. We have around 23k." ADO **1765085** `MACL - Unable to obtain all GL Cross Reference records` (Bulk Data Maintenance screen for AFIS GL Cross Reference; DB had 21,180 rows: `select COUNT (*) from afis_gl_cross_ref;`).
**Fix (CONFIRMED, from the work item):** global config keys, key group **SCREEN DEFAULTS** (key name = screen security ID `QUCAFISGLCROSSREF` + suffix):
```
QUCAFISGLCROSSREF_INITIALROWS     1000
QUCAFISGLCROSSREF_MOREBUTTONROWS  1000
QUCAFISGLCROSSREF_ALLBUTTONROWS   2000000
```
Add on the Configuration Settings screen (MDC script exists on the WI). Also shipped as hotfix **2023.04→2025.04** (SF resolution: *"2024.10 November 2025 HF"*).

**Signature B — cannot add rows, PK error.** SF **26-01110990**: "unable to add rows to the AFIS GL Cross Reference screen due to a PK error. It's not allowing me to update the seq number manually either." Resolution verbatim: *"Script was deployed to reset the AFIS_GL_XREF_SEQ sequence."* Classic Oracle sequence-behind-data: after bulk loads/imports into `AFIS_GL_CROSS_REF`, the sequence lags MAX(key) → every insert collides. Fix: re-seat `AFIS_GL_XREF_SEQ` above the current max (§5.2).

**Anchors:** SF 25-01050561, 26-01110990; ADO 1765085.

---

### 3.3 Cross-reference data missing (conversion, rights-driven, ADS display)

**Signatures & fixes.**
- **Rights-driven xrefs absent:** SF **25-01003686** — if Rights = WIO (Wellbore Interest Only) or ORRI, a cross reference should exist per the master mapping document; resolution: *"Cross-references Inserts has been added with the given details"* (Services insert script). Related config-era case: 26-01091558 (`ORRI Acreage Fields`).
- **Conversion mapping incomplete:** SF **25-01052611** (`Not all Cross reference types mapped in conversion`), 25-01047312 (converting PXD agreements), 25-01047310 (incorrect info), 25-01036208 (info missing) — all Application Configuration/conversion-wave; deliverable is a mapping correction + backfill script.
- **ADS shows blank Cross References:** SF **24-00982892** — fix script verbatim (screen-control display config):
```sql
UPDATE LIS.QCNFG_SCREEN_CONTROL_DISP
   SET DISP_IND = 1, UPDT_OPER = 'UPGRADE', UPDT_DATE = SYSDATE
 WHERE SCREEN_NAME = 'ADS_AGMT_HDR_DTL' AND COL_TAG_NAME = 'XREF_VALUE';
```
- **Downstream feeds:** SF **25-01006743** (`Add tables to nightly ETL`, Cross Reference category) — xref tables missing from a client's ETL extract; config request, not app defect.

**Anchors:** SF 25-01003686, 25-01052611, 25-01047312, 25-01047310, 25-01036208, 24-00982892, 25-01006743, 26-01091558.

---

### 3.4 Related Wells grid behavior (bulk edit, add row, persistence, delete)

This is a hotfix-wave family on the QLS Web grid framework — check build FIRST (G3):

| Defect | ADO (verbatim title) | Fixed-in |
|---|---|---|
| Bulk Edit delete doesn't delete (no dirty-row indicator; rows return after save) | **1759806** `XOM - QLS - Related Wells - Bulk Edit Doesn't Delete Records` — fix covered Related Well + Legal Description sub-tabs; payment grids split to #1768763/#1768760 | 2023.04→2025.04 HFs Completed (CONFIRMED). SF companion **25-01047328** — resolution: "Engineering resolved this issue with ADO WI - 1759806" |
| Bulk Edit copy/paste rows fail to save | **1788163** `QLS - Related Well - Save Failed for Bulk Edit Record` | 2023.04→2025.04 HFs Completed (CONFIRMED) |
| Bulk Edit adds blank rows | **1808520** `DVN - QLS - Bulk Edit with Related Wells adds blank rows` | ref'd from 1808378 (state per ADO) |
| "+" Add Row leaves toolbar stuck spinning; picklist unusable; workaround = mock save to clear | **1808378** `DVN | NEE - QLS - Related Well Add Row Toolbar in Stuck Loading State` — root cause (from WI analysis): `Quorum.QLS.Web.Core/Scripts/RelatedWells/RelatedWells.js`, function `postRelatedWellGridUpdate` lines 84–89 — null-guard early-return path missing `qGridRead` calls; pure JS UI-state bug, no DB impact | 2024.04→2025.04 HFs Completed (CONFIRMED) |
| First Sale Date / 1st Production Date doesn't persist after save+retrieve | **1767423** `XOM - QLS - Related Well - First Sale Date Doesnt Stay Populated In QLS` — column `FIRST_SALE_DATE` in `WELL_INFO_QRA` not written | 2023.04→2025.04 HFs Completed (CONFIRMED) |
| Delete Related Well → `ORA-00060: deadlock detected ... at "LIS.DEP_REL_WELL" line 112/179 ... ORA-04088 error during execution of trigger 'LIS.DEP_REL_WELL'` | **1729654** `GEC - QLS - Error when deleting Related Well - Check-in Index` — occurs only at GEC because of their **custom trigger `DEP_REL_WELL`**; missing index checked into Core as #1729653 | 2023.04→2025.04 HFs Completed (CONFIRMED) |

**Fix recipe.** Quote the matching ADO + hotfix tags; confirm the client consumed the hotfix (DVN in 1808378 was suspected of not being on latest). For any ORA-04088 on related-well DML, get the trigger name from the error — client-custom triggers (`<CLIENT>` override repos) put the case on the client-custom route, with a Core index/hotfix as the systemic fix.

**Anchors:** SF 25-01047328, 25-01047326 (conv-created subdivisions), 26-01064266 (TVD column), 25-01056309/25-01056314 (proration remarks / areal→depth conversion asks); ADO 1759806, 1788163, 1808378, 1808520, 1767423, 1729654 (+1729653).

---

### 3.5 Related Wells population — well master missing or wrong

**Signature.** Related Well picklist/search returns nothing ("Retrieve all… no data found", even by well number), specific wells missing, or wells from the wrong state offered.

**Root causes (three confirmed mechanisms).**
1. **Code-table (qcode) sync broken:** SF **25-01005067** (`Related Well not populating with wells`) resolution verbatim: *"qcode table sync had issues. Resolved and running now"*. Sister case same client/date: 25-01005063 (BAs missing — same sync).
2. **Well interface not scheduled:** SF **25-01008644** (`Wells Set-up in QRA not in QLS`) resolution verbatim: *"Enabled schedule definition 13 to run the INT_QLSWL process nightly at 10 PM"* — `INT_QLSWL` is the QRA→QLS well-population process; when it stops, QLS well master goes stale (case showed last run months old).
3. **Registered-SQL / data correction on picklists:** ADO **1780572** `QLS - EQC Perf - Picklist not showing any data on Related Agreement, Related Wells and Cross Reference screen` — fixed by data correction in the client DB; the picklists' registered SQL is **`SELECT_PICK_REL_AGREEMENT`** (Agreement Number picklist) and **`SELECT_RELATED_WELL_ENHC`** (Related Well picklist). Verification note: the Cross Reference picklist opens only when Type = 'Storage' — **by design**.

**Other confirmed items.**
- **Wrong-state wells:** SF **26-01082888** (`Related wells - wells from multiple states being related to Wyoming leases`, Application Configuration) — well-master feed/filter issue; validate the well source data before suspecting the screen.
- **Well ID search in Land Web Screens:** SF **22-00602985** resolution verbatim: *"The Well ID search in LWS corresponds to the WELL_KEY field, which was not exposed in QLS. …we have exposed WELL_KEY with the title 'Well ID'"* (product fix).
- Display/design asks: SF 25-01050802 (*"updated related well screen to match design"*), 25-01044713 (subdivision display), 25-01033448 (PXD node data).

**Fix recipe.** (1) Is the well in QLS at all (well master table, `WELL_INFO_QRA` era)? If not → check `INT_QLSWL` schedule + last run, and the qcode sync. (2) Well present but picklist empty → run the registered SQL (`SELECT_RELATED_WELL_ENHC`) manually with the screen's binds; if it returns rows, it's the screen/grid (G3 family §3.4); if not, data correction (G4).

**Anchors:** SF 25-01005067, 25-01008644, 26-01082888, 22-00602985, 25-01050802, 25-01044713, 25-01033448; ADO 1780572.

---

### 3.6 Related Agreements — add/delete integrity, columns, search

**Signature 1 — duplicate error adding same agreement # with different sub #s.** SF **22-00521949** (continuation of 22-00274541): adding 2+ subs of the same related agreement (e.g. 1314232000 001 and 002) throws a duplication error; workaround from the subs' side eventually dead-ends. Resolution: *"Available in current release"* — **G3**: confirm build, quote fixed-in.

**Signature 2 — hidden one-way relationship ("already related" but invisible).** SF **22-00825018** (`Related Agmt "Delete" Malfunction`): audit history proved the relationship was deleted from the Contract side only — the Lease side kept the row, blocking re-relate with "already related" while showing nothing on the front end. Resolution: one-off data fix by update statement. **G4 signature:** asymmetric rows in the related-agreement link data; verify both directions before scripting (§5.4). Related: SF 22-00825629 (`No available audit in Related Agreements of JOAs` — audit gap noted, config).

**Signature 3 — "Next Pay Due Date" not populating for large related-agreement sets.** ADO **1760457** `XOM - QLS - Related AGM screen - "Next Pay Due Date" not populating for Large Number of Related Agreements` (tagged Regression) — **2023.04→2025.04 HFs Completed**. SF companion **25-01047331** (resolution: "Resolved by Engineering with ADO WI - 1760457").

**Signature 4 — Related Agreement search broken.** SF **26-01097129** (`QLS - Search issue with Related Agreements`) resolution verbatim: *"Script to make changes to QPCK Session package"* — Oracle session package (`QPCK` family) patch; if search misbehaves per-session/per-user, suspect the session package version before the screen. Also SF 24-00970985 (Related Agreement searchability, upgrade-wave config); 22-00653751 (launching agreements from Related Agreements in PRD, Software Defect, 2022).

**Signature 5 — column/data asks (config):** SF 26-01088340 (`No Legacy file number on related agreements`), 25-01061479 (client/matter number into Related Agreements), 26-01107036 (Copy Agmt function vs Related Agreements) — column exposure/copy-scope configuration.

**Anchors:** SF 22-00521949 (+22-00274541), 22-00825018, 22-00825629, 26-01097129, 24-00970985, 22-00653751, 26-01088340, 25-01061479, 25-01047329/25-01047330 (screen-wave siblings); ADO 1760457.

---

### 3.7 Prospect / Related Asset / Non-Interest Related Wells

**Signature 1 — saves failing on Prospect/Org RA_TYPE values.** SF **26-01065697** (`Unable to add Org RA_TYPE values to UAT nor to PRD / Save Failing`) resolution verbatim: *"CDTBL 47235 was missing the 'NODE_TYPE' column and prevented users from saving. This col was added and users can now save."* — the RA-type **code table (CDTBL 47235)** must carry `NODE_TYPE`; a missing column in the client's code-table data breaks every save. Sister config asks: SF 25-01021060 (`Adding RA Type to prospect screen`), 24-00951009 (rename Prospect node from "Related Assets").

**Signature 2 — Prospect node inaccessible.** SF **25-01052616** resolution verbatim: *"Missing QVIEWRELATEDASSET object on user privileges"* — the Prospect/Related Asset node is gated by the **`QVIEWRELATEDASSET`** security object; add it to the role. Pure G2 (security).

**Signature 3 — Prospect picklist/values missing.** SF **25-00999864** (missing West Virginia prospect numbers — script populated the screen), 23-00912411 (`Prospects Not Loading` — script fix), 25-01032518 (PXD Prospect Cross Reference — conversion), 23-00934347 (Prospect Note Categories — code/decode), 23-00914607 (`Adding a Prospect to a Lease is not Working`, Software Defect 2023).

**Signature 4 — Non-Interest Related Well metadata.** ADO **1755366** `ECA - QLS - Metadata Update - Non-Interest Related Well forcing numeric values for Township, Range, and Section` — fields must accept alphanumerics (direction chars) + leading zeros; fixed via grid metadata **grid_id 49250** (`select * from qarch_cnfg_gridctrl_col_net where grid_id = 49250;`), columns WellTwnshp/WellRnge/WellSect switched to Text Edit. Precondition for manual entry: **`LinkWell` configuration = 0** (otherwise the node links to existing wells instead of free-entry). **2023.04→2025.04 HFs Completed.** Search-popup filters history: ADO **1547312** `QLS - Non-Interest Related Well - Search Screen Filters Failed` (2023.04/2024.04 HFs; follow-up #1685916).

**Anchors:** SF 26-01065697, 25-01052616, 25-00999864, 23-00912411, 25-01032518, 23-00934347, 23-00914607, 25-01021060, 24-00951009, 24-00950638 (Unit Name/Description display); ADO 1755366, 1547312 (+1685916).

---

## 4. Known ADO Items

| ADO | What | State | Fixed-in |
|---|---|---|---|
| 1759806 | Related Wells Bulk Edit doesn't delete records (XOM); fix spans Related Well + Legal Description tabs | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1760457 | Related AGM "Next Pay Due Date" blank for large sets (XOM); Regression | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1788163 | Related Well bulk-edit copy/paste rows fail to save | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1808378 | Related Well Add Row stuck spinner (DVN/NEE) — RelatedWells.js `postRelatedWellGridUpdate` missing qGridRead | Closed | 2024.04→2025.04 HFs (CONFIRMED) |
| 1808520 | Bulk Edit with Related Wells adds blank rows (DVN) | ref'd | sibling of 1808378 |
| 1767423 | First Sale Date not persisted (`WELL_INFO_QRA.FIRST_SALE_DATE`) (XOM) | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1729654 / 1729653 | ORA-00060 deadlock deleting Related Well via GEC custom trigger `LIS.DEP_REL_WELL`; index checked into Core | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1780572 | Picklists empty on Related Agreement / Related Wells / Cross Reference (EQC Perf) — data correction; registered SQL `SELECT_PICK_REL_AGREEMENT`, `SELECT_RELATED_WELL_ENHC` | Closed | client-DB data fix, no train tag (CONFIRMED) |
| 1755366 | Non-Interest Related Well forces numeric Township/Range/Section (ECA) — grid 49250 metadata | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 1547312 | Non-Interest Related Well search filters failed | Closed | 2023.04/2024.04 HFs (CONFIRMED); follow-up 1685916 |
| 1765085 | AFIS GL Cross Reference row cap (MACL) — SCREEN DEFAULTS config keys + hotfix | Closed | 2023.04→2025.04 HFs (CONFIRMED) |
| 208479 | Cross Reference save error (OXY, 2020) — client-env repro; row-overwrite note | Closed | legacy (CONFIRMED closed) |
| 1783003 | jQuery stays active after Add Row on Payment/Cross Reference/Depth/Related Agreement | Closed | AT-found platform item (CONFIRMED closed) |

Area paths seen: `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Land` (bulk of the grid wave), project `Quorum` for 2026+ items. Hotfix tags `YYYY.MM Hotfix (+ Completed)` reliable for G3 fixed-in checks; SF resolutions add the deployment wording ("2024.10 November 2025 HF").

---

## 5. Diagnostic SQL (Oracle, `lis` schema — drawn from real cases/work items)

**5.1 AFIS GL Cross Reference row count vs screen cap (ADO 1765085, verbatim):**
```sql
select COUNT (*) from afis_gl_cross_ref;
-- then compare against SCREEN DEFAULTS keys QUCAFISGLCROSSREF_INITIALROWS / _MOREBUTTONROWS / _ALLBUTTONROWS
```

**5.2 AFIS GL XRef PK error — sequence behind data (SF 26-01110990):**
```sql
-- compare sequence next value vs max key, then re-seat the sequence (script-review before PRD)
SELECT lis.afis_gl_xref_seq.NEXTVAL FROM dual;          -- consumes one value: run on DEV mirror
SELECT MAX(<pk_key_col>) FROM lis.afis_gl_cross_ref;    -- confirm PK column on live schema
-- fix pattern used by the deployed script: drop/recreate or ALTER the sequence to start above MAX
```

**5.3 ADS blank Cross References (SF 24-00982892, verbatim fix):**
```sql
UPDATE LIS.QCNFG_SCREEN_CONTROL_DISP
   SET DISP_IND = 1, UPDT_OPER = 'UPGRADE', UPDT_DATE = SYSDATE
 WHERE SCREEN_NAME = 'ADS_AGMT_HDR_DTL' AND COL_TAG_NAME = 'XREF_VALUE';
```

**5.4 Asymmetric related-agreement rows (SF 22-00825018 recipe):** query the related-agreement link rows for BOTH `arrg_key` directions of the pair; a row existing in only one direction while the UI shows nothing is the hidden-relationship signature — script the missing/extra side per the case's update-statement approach. (Link-table name varies by build — resolve via metadata server / registered SQL `SELECT_PICK_REL_AGREEMENT` join targets; label NOT YET RUN if metadata server is offline.)

**5.5 Non-Interest Related Well grid metadata (ADO 1755366, verbatim):**
```sql
select * FROM qarch_cnfg_gridctrl_col_net where grid_id = 49250;
-- WellTwnshp / WellRnge / WellSect should be Text Edit (alphanumeric + leading zeros)
-- precondition for manual entry: LinkWell configuration = 0
```

**5.6 Cross-reference debugging entry point (ADO 208479, verbatim):**
```sql
select * from all_agreements a where a.arrg_key = :arrg_key;  -- then walk CROSS_REFERENCES for the agreement
```

> DEV-tier caveat: run these on the client's `<CLIENT>_LND_DEV17` / `<CLIENT3>U_HD_DEV17` mirror via the metadata server; PRD data-state conclusions stay INFERRED until confirmed by client DBA output.

---

## 6. Expected-Behavior FAQ

- **"The Cross Reference picklist only opens for Type = Storage."** By design — verified on ADO 1780572 and matching TST17 behavior; other types take typed values.
- **"Why isn't WELL offered as a Cross Reference Type on my agreement type?"** Types are activated per agreement/subject type in the cross-reference rules; it's a config add, not a defect (SF 24-00950684, 24-00936733).
- **"Bulk Edit on Related Wells looks different from Date & Doc."** It should behave the same; if delete doesn't stick you're pre-1759806-hotfix. Legal Description sub-tabs deliberately hide Bulk Edit on Polygon/Exception/Non-Rect/Subdivision types (1759806 verification list).
- **"Users can't type Township '02N' on Non-Interest Related Well."** Fixed metadata (1755366); also check `LinkWell` — with LinkWell=1 the node expects linked wells, not free-entry.
- **"Should wells created in QRA/Upstream show in QLS automatically?"** Yes — via the `INT_QLSWL` interface (nightly schedule) + qcode sync; if they don't, the job is down, not the screen (SF 25-01008644, 25-01005067).
- **"Can we relate the same agreement twice with different subdivision numbers?"** Yes on current builds; the duplicate error was a defect fixed after 22-00521949.
- **"Prospect node is missing for one user only."** Security: the `QVIEWRELATEDASSET` object on their role (SF 25-01052616).

---

## 7. Escalation

- **Fixed-in citations:** quote ADO id + hotfix tags from §4; client-build claims stay INFERRED until the exact `hotfix/17.2x.y` build is confirmed. The Related-Wells grid wave (1759806/1788163/1808378) is the most-cited family — always check consumed-hotfix status before reproducing.
- **Escalate to Engineering** (`Quorum\North America\Upstream\Land RnD` current) when: a §4 grid defect reproduces on a hotfixed build; an ORA-00060/ORA-04088 fires from a CORE (non-client) trigger; `AFIS_GL_XREF_SEQ` re-desyncs after a re-seat (something is inserting with explicit keys).
- **Route to Services:** cross-reference rules activation, conversion xref mapping/backfills, prospect picklist population scripts, code-table repairs (CDTBL 47235 `NODE_TYPE` class), ETL table additions — deployed via client script/metadata repos (`<CLIENT3>.QLS.Metadata`).
- **Client-custom route:** errors naming client triggers (e.g. `LIS.DEP_REL_WELL` at GEC) or client-only repro (208479 at OXY) — compare client metadata layer vs Core before any Core bug.
- **Batch flag:** `INT_QLSWL` is a scheduled interface — "wells missing" complaints start at the batch schedule (`batch-debugger` agent), not the Related Well screen.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
