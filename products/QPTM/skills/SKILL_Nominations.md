# SKILL: QPTM Nominations Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Nomination submission & validation, duplicate/overlapping noms, contract/location/path errors, imbalance/MDQ, nom upload (NNNOMLOAD)/import/copy-paste, AutoGen, nom deletion ops, nom reports, web/UI on nom pages.
**Companion:** For EDI-driven noms (NMST/NMQR, ENMQR error codes, cycle deadlines / late-nom RuleNN00009011) see **SKILL_EDI_Troubleshooting.md** — do not duplicate that content; cross-references are noted below.

> Evidence base: ~430 QPTM Nominations cases (Root Cause = Software Defect / Application Configuration / Customer Error / Training). Every root-cause claim below cites a real SF case number and/or ADO work item.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Nomination Concepts & Status Codes](#2-nomination-concepts--status-codes)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Duplicate / Overlapping Nom Error (HIGH FREQUENCY)](#4-duplicate--overlapping-nom-error-high-frequency)
5. [Nom Submission / Validation Errors](#5-nom-submission--validation-errors)
6. [Contract / Location / Path Errors](#6-contract--location--path-errors)
7. [Imbalance / Quantity / MDQ / Fuel](#7-imbalance--quantity--mdq--fuel)
8. [Nom Upload (NNNOMLOAD) / Import / Copy-Paste](#8-nom-upload-nnnomload--import--copy-paste)
9. [AutoGen Noms](#9-autogen-noms)
10. [Nom Deletion Runbook (Ops)](#10-nom-deletion-runbook-ops)
11. [Late / Retro / Cycle Deadline (cross-link)](#11-late--retro--cycle-deadline-cross-link)
12. [Nom-Related Reports](#12-nom-related-reports)
13. [Web / UI Rendering Issues on Nom Pages](#13-web--ui-rendering-issues-on-nom-pages)
14. [Expected Behavior / User Education](#14-expected-behavior--user-education)
15. [Key Code Files & Repos](#15-key-code-files--repos)
16. [Database Tables Reference](#16-database-tables-reference)
17. [Diagnostic SQL Queries](#17-diagnostic-sql-queries)
18. [Known Historical ADO Bugs](#18-known-historical-ado-bugs)
19. [Escalation Decision Tree](#19-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. What is the EXACT error/message text? (e.g., "dates that overlap another nomination", MDQ exceeded, "duplicate key")
[ ] 2. Which TSP_NO and Service Requester / shipper (BP_NO / GID)?
[ ] 3. Which gas day(s) and cycle (Timely / Evening / ID1-3)?
[ ] 4. The NOM_ID(s) involved? (clients almost always supply this for dup/delete cases)
[ ] 5. Where did it fail — Nom Submission screen, Location Centric, Nom Maintenance, NNNOMLOAD import, API, or AutoGen batch?
[ ] 6. Web or Classic (Citrix/Desktop)? Several bugs are Web-only or Classic-only.
[ ] 7. Internal or External (shipper/TPA) user? Validation/override behavior differs.
[ ] 8. Is there a hard deadline on the case? (dup-nom cases are usually CRITICAL w/ a cycle deadline)
[ ] 9. One-off or recurring for this shipper/TSP? (recurring dup-nom = underlying defect cluster)
[ ] 10. QPTM version (e.g., 2023.04, 2024.04, 1.5) — many fixes are version-gated.
```

### Where does the issue live?
| Entry point | Likely cluster | First place to look |
|-------------|----------------|---------------------|
| Submit on Nom Submission screen → "overlap"/"duplicate" | §4 Duplicate/Overlap | NNCTRL_NOM_DTL + NNCTRL_ACTV_DTL for the NOM_ID |
| Validation error blocking submit (BI/LI) | §5 Validation | QARCH_VALD_RULE + Validation Rule X-Ref screen |
| Contract/location not found, path disappears | §6 Contract/Loc | NNCTRL_CTR / NNCTRL_LOC / contract path |
| MDQ/fuel/imbalance wrong | §7 Qty | NNCTRL_CTR MDQ, fuel rate tables |
| Excel import/copy-paste fails | §8 Upload | NNNOMLOAD logs, import template version |
| Noms appear/disappear after batch | §9 AutoGen | NNAUTOGEN config, source/target TSP |
| "Please delete this nom" | §10 Deletion | Ops runbook — confirm before scripting |

---

## 2. Nomination Concepts & Status Codes

### Nom record model
A nomination is stored across **header + detail + activity** rows:
- `NNCTRL_NOM_DTL` — the nomination detail (one row per NOM_ID + CYCLE_ID + gas-day range). Key fields: `NOM_ID`, `BEG_GAS_DAY`/`END_GAS_DAY`, `CYCLE_ID`, `NOM_STAT_CD`, `REC_QTY`/`DEL_QTY`, `REC_LOC_ID`/`DEL_LOC_ID`, `SR_CTR_NO`, `SR_BP_NO`, `ACTV_NO`, `ACTV_DTL_NO`, `ACTN_CD`, `DELETE_IND`, `ORIG_END_GAS_DAY`, `NOM_HASH_ID`.
- `NNCTRL_NOM_HDR` — nomination header.
- `NNCTRL_ACTV_DTL` — the **activity detail** that the Nom Submission grid binds to. The screen maps grid rows to activity rows via `NOM_ID`. Activity/NOM_ID mismatches here are the root of "ghost noms" (see §4).

### Status codes (NOM_STAT_CD)
| Code | Meaning | Notes |
|------|---------|-------|
| BV / VI | Valid / submitted successfully | Clean state |
| **BI** | Business Invalid | Business-rule failure (e.g., over MDQ). Configurable whether external users can submit over BI. |
| **LI** | Line Invalid | Security/foreign-key failure. **Blocks the whole submission batch** (see EDI skill §12). |
| AV / activity code | Activity created, not a final nom | AutoGen/upload that errored often leaves an **activity code** instead of a nom — a key diagnostic signal (cases 24-00984178, 23-00903185). |

### Grids on the Nom Submission screen
PT (Path / threaded), PNT (non-threaded, with Up/Dn grids), Location-Centric, and the 30-day pop-up. Bugs are frequently grid-specific (e.g., spinning wheel only on PT add-row — case 25-01036695).

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| "The nominations has dates that overlap another nomination… edit the original nomination" | Orphaned/overlapping NOM_DTL or ACTV_DTL rows ("ghost nom") that don't render on screen | **Data script (delete bad nom)** | 25-01060535, 24-00995062, 25-01044354, 25-00996203 |
| "Duplicate key" / "duplicate nom id" on save | Identity/Nom-ID generation defect inserting colliding NOM_IDs (Web) | Data script now; code fix #1761678 | 26-01099624, ADO #1761678 |
| Dup error recurs nightly for REX/TIGT/TPC shippers | Recurring overlap-nom defect cluster under RCA | Data script per occurrence | 25-01029022, 26-01099232, RCA #1699360 |
| BI error "exceeds MDQ" when contract is NOT at MDQ | MDQ validation config / shared-MDQ not summed | Config change | 24-00994503, 25-01041489 |
| Over-MDQ nom submits with NO validation | Validation not enabled / wrong severity | Config (enable rule) | 24-00985947, 25-00999987 |
| Import/upload submits a nom that the Submission screen would have rejected | Import path skips a validation (model type, TT-for-TOS, Up/Dn ID) | Code fix (add validation to import) | 25-01015207, 23-00909876, 23-00928342 |
| NNNOMLOAD "unique constraint" error when existing noms span the dates | Upload merge/insert defect on overlapping date ranges | Code fix | 24-00957669, 22-00830582 |
| AutoGen creates noms in Late status / for wrong days / for parties w/o contract | AutoGen source/target metadata profile or range-nom defect | Code fix / config | 24-00977086, 25-01007550, 25-01022652 |
| Cannot delete / zero out a nom path | Overlap/ghost data prevents update | Data script | 26-01063743, 26-01090812 |
| Path/Up-Dn volumes don't match on screen | Bidirectional / TT point display defect | Code/config | 22-00818831 |
| Nom paths vanish after fixing LI+BI errors | LI/BI combo drops unchanged paths from grid | Code fix (planned) | 24-00952492 |
| Spinning wheel prevents add-row (PT/PNT) | Web grid rendering defect | Code fix | 25-01036695 |
| Late/BI noms missing from NN12 Nom Error Report | Report filter excludes the status | Code/config | 25-01001265 |

---

## 4. Duplicate / Overlapping Nom Error (HIGH FREQUENCY)

This is the **single highest-volume Nominations cluster** (41+ "Duplicate Nom" subjects plus many "Not able to delete" / "ghost nom" variants). It is also the most operationally urgent — these cases almost always arrive flagged **CRITICAL with a cycle deadline** ("Deadline 4PM MST") because the shipper cannot submit until the bad record is removed.

### The canonical symptom
On Submit (or even on attempting to **zero out / delete** a path), the system throws:

> *"The nominations has dates that overlap another nomination. Rec Loc ID: `<x>`, Del Loc Id : `<y>`, Service Req K: `<k>`. Rather than adding a new nomination, you should edit the original nomination."*

…or a raw **"duplicate key"** error. The user often **cannot see** the conflicting record on the Nom Submission screen — hence "ghost nom" (cases 26-01085239, 26-01099339). The phrase is generated in `QPTMNominationService.cs` (see §15).

### Root cause(s)
1. **Orphaned / overlapping detail rows** in `NNCTRL_NOM_DTL` whose date range overlaps a new submission but which don't render on the grid (the grid binds to `NNCTRL_ACTV_DTL`). The overlap check fires on the hidden rows. (24-00995062 / 25-00996203, 25-01044354, 26-01090812.)
2. **Nom-ID generation defect (Web)** — `IdNomForAdded` defaulted incorrectly so the Submission controller inserted NOM_IDs starting at `10000000` even though the last identity value was far lower, creating colliding/duplicate IDs in `NNCTRL_ACTV_DTL` (the activity then doesn't show on screen). Root-caused in **ADO #1761678** (APL, case 25-01049356); reproduced by debugging that `IdNomForAdded` was wrong. `UTIL_RESEED_IDENTITIES_SYN` did **not** fix it — it is a code defect in `QUIControllerNominationSubmissionBase.cs`.
3. **User-induced** — editing an editable field on a submitted nom (e.g., REC Rank) or copying a bad path forward creates a second overlapping record (26-01098678, 25-01023727, "Customer Error" root cause). A shipper deleting their own nom mid-cycle can also leave an overlap (26-01097498).
4. **RCA umbrella:** the recurring nature is tracked under **ADO #1699360** (RCA: Duplicate Nom Error Cima on Ruby) and **#1739654** (MOM remove-duplicate-noms script). RCA conclusion in case 25-01024051: *"Nominations are not allowed to be submitted that would cause overlapping dates… an error is thrown to inform the user that the record they are trying to submit would overlap with an existing record and to re-query the screen."*

### Diagnostic SQL — find the bad/overlapping nom
```sql
-- 1. Pull ALL detail rows for the supplied NOM_ID (incl. hidden/overlapping ones)
SELECT NOM_ID, TSP_NO, CYCLE_ID, BEG_GAS_DAY, END_GAS_DAY, ORIG_END_GAS_DAY,
       NOM_STAT_CD, ACTN_CD, REC_LOC_ID, DEL_LOC_ID, REC_QTY, DEL_QTY,
       SR_BP_NO, SR_CTR_NO, ACTV_NO, ACTV_DTL_NO, DELETE_IND, SUBMIT_DT, USER_ID
FROM NNCTRL_NOM_DTL
WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
ORDER BY CYCLE_ID, BEG_GAS_DAY;

-- 2. Find overlapping ranges for the same shipper/path/cycle (the actual conflict)
SELECT NOM_ID, CYCLE_ID, BEG_GAS_DAY, END_GAS_DAY, REC_LOC_ID, DEL_LOC_ID, NOM_STAT_CD
FROM NNCTRL_NOM_DTL
WHERE TSP_NO = <TSP_NO> AND SR_BP_NO = <BP_NO>
  AND SR_CTR_NO = '<CTR>' AND CYCLE_ID = <CYCLE>
  AND BEG_GAS_DAY <= '<NEW_END>' AND END_GAS_DAY >= '<NEW_BEG>'
ORDER BY BEG_GAS_DAY;

-- 3. Check for activity/NOM_ID mismatch (the "ghost" — #1761678 pattern)
SELECT NOM_ID, * FROM NNCTRL_ACTV_DTL WHERE ACTV_NO = <ACTV_NO> ORDER BY NOM_ID;
-- Red flag: NOM_IDs jumping to 10000000+ while the table's real max NOM_ID is much lower.
```

### The fix recipe (what L4 actually does)
For the overwhelming majority (Resolution Type = **Data Script Provided**), the fix is a **targeted delete of the bad NOM_ID for the affected gas day(s) forward**, deployed by Cloud Ops:
1. Confirm the exact `NOM_ID`, `TSP_NO`, shipper, gas-day range, and cycle from the client.
2. Run diagnostic SQL #1–#3 above to confirm the overlap/ghost and that you are deleting the *bad* record, not the live one.
3. Provide the **nom-delete / "ghost nomination" script** (a.k.a. "duplicate-nom delete script") to Cloud Ops for PRD deployment. This is a standardized, repeatedly-reused script — cases reference it as "the normal script/delete process" (26-01097145), "Ghost nomination script" (25-01060757), "Script for Duplicate noms" (25-01059423).
4. Have the client re-query the screen and resubmit before the cycle deadline.

> **Ops note:** raise a "Request Global Cloud Ops" work item for the deployment (e.g., ADO #1806364 = case 26-01099232). These are time-boxed to the cycle deadline.

> **Don't over-fix:** if only one cycle is blocked and the client can keep nominating under a later cycle (ID2), some clients prefer to leave it rather than run a "noisy" script mid-day (26-01096143). Confirm scope with the client.

### Standardized nom-delete scripts — VERBATIM templates (redacted)

These are the **actual** scripts Cloud Ops deploys, reconstructed from real attachments. Concrete TSP/NOM/BP/date/hash/server values are replaced with `<PLACEHOLDER>` tokens; **real table names, columns, join logic, and delete ordering are kept intact.** Always run the verify-SELECT and confirm the row count BEFORE deleting. **The delete order matters** — child/dependent tables (confirmation, cycle, activity, error) must be cleared before the parent `NNCTRL_NOM_DTL` row, or FK/constraint errors block the delete.

#### Template A — QPTM cascade hard-delete (NNCTRL_/CFCTRL_, keyed by NOM_ID + NOM_SEQ_NO)
> Source (verbatim): ADO **#1806364** `NomDeletionScriptTEP_MAY2026.sql` (TEP/REX, case 26-01099232) and ADO **#1747369** `1_DELETE_NOM5064766_8.6.25QPTM.sql` (HEP, EDI-failing ghost). This is the dominant QPTM pattern. One block PER blocked gas-day range; repeat for each `NOM_SEQ_NO`/range. Wrap in a transaction.

```sql
-- Standardized nom-delete script template (redacted) — QPTM NNCTRL cascade
-- Params: <TSP_NO>, <NOM_ID>, <NOM_SEQ_NO>, <BEG_DAY>, <END_DAY> (e.g. 'May  8 2026 12:00AM')
BEGIN TRAN;  -- (or BEGIN/COMMIT per DB engine; verify counts before COMMIT)

-- 0. VERIFY FIRST — confirm you are targeting the bad row(s), note the count
SELECT NOM_SEQ_NO, NOM_ID, BEG_GAS_DAY, END_GAS_DAY, CYCLE_ID, NOM_STAT_CD, ACTV_NO
FROM   NNCTRL_NOM_DTL
WHERE  TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
  AND  BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';

-- 1. Confirmation (hourly then base)
DELETE FROM CFCTRL_CONF_HR WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';
DELETE FROM CFCTRL_CONF    WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';

-- 2. Cycle roll-up tables
DELETE FROM NNCTRL_ALLOC_MAX_CYCLE     WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';
DELETE FROM NNCTRL_NOM_LATEST_CYCLE    WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';
DELETE FROM NNCTRL_NOM_OVERALL_CYCLE   WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';

-- 3. Activity (hourly, error, base) — resolve ACTV_NO via subquery on the activity table
DELETE FROM NNCTRL_ACTV_DTL_HRLY WHERE TSP_NO = <TSP_NO> AND ACTV_NO IN (
  SELECT DISTINCT ACTV_NO FROM NNCTRL_ACTV_DTL
  WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
    AND (BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>' OR END_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>'));
DELETE FROM NNCTRL_ACTV_DTL_ERR  WHERE TSP_NO = <TSP_NO> AND ACTV_NO IN (
  SELECT DISTINCT ACTV_NO FROM NNCTRL_ACTV_DTL
  WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
    AND (BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>' OR END_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>'));
DELETE FROM NNCTRL_ACTV_DTL      WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
    AND (BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>' OR END_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>');

-- 4. Nom detail (hourly, error, base) — keyed by NOM_SEQ_NO (NOT NOM_ID); delete the parent LAST
DELETE FROM NNCTRL_NOM_DTL_HRLY WHERE TSP_NO = <TSP_NO> AND NOM_SEQ_NO = <NOM_SEQ_NO>;
DELETE FROM NNCTRL_NOM_DTL_ERR  WHERE TSP_NO = <TSP_NO> AND NOM_SEQ_NO = <NOM_SEQ_NO>;
DELETE FROM NNCTRL_NOM_DTL      WHERE TSP_NO = <TSP_NO> AND NOM_SEQ_NO = <NOM_SEQ_NO>;

-- COMMIT;  -- only after row counts above match expectations; else ROLLBACK;
```

#### Template B — TIPS/QLNG soft-style delete (QCTRL_, keyed by NOM_HASH_ID)
> Source (verbatim): ADO **#1739654** `MOM_NOM_FIX.sql` (MOM "Remove Duplicate Noms", case 25-01027984, deployed to the **QRMTIPS** schema). TIPS uses `QCTRL_NOM_DTL` (+ `_INVALD` / `_INVALD_ERR`) and identifies the bad rows by **`NOM_HASH_ID`** rather than NOM_SEQ_NO. Note the script's own header: *"Please follow this sequence."*

```sql
-- Standardized nom-delete script template (redacted) — TIPS/QCTRL by NOM_HASH_ID
-- Params: <SR_BA_NO>, <SR_CTR_NO>, <BEG_DAY> (e.g. '1-JUL-2025'), <HASH_1>,<HASH_2>,...
-- Deploy to the QRMTIPS schema.

-- 0. VERIFY FIRST — list the rows you intend to remove, capture NOM_HASH_IDs
SELECT * FROM QCTRL_NOM_DTL
WHERE  SR_BA_NO = '<SR_BA_NO>' AND SR_CTR_NO = '<SR_CTR_NO>' AND BEG_GAS_DAY >= '<BEG_DAY>';

-- 1. Detail rows by hash + gas day
DELETE FROM QCTRL_NOM_DTL
WHERE NOM_HASH_ID IN ('<HASH_1>','<HASH_2>', ...) AND BEG_GAS_DAY >= '<BEG_DAY>';

-- 2. Invalid-error and invalid tables for the SAME hashes (clears the BI/LI residue)
DELETE FROM QCTRL_NOM_DTL_INVALD_ERR
WHERE NOM_HASH_ID IN ('<HASH_1>','<HASH_2>', ...) AND BEG_GAS_DAY >= '<BEG_DAY>';

DELETE FROM QCTRL_NOM_DTL_INVALD
WHERE SR_BA_NO = '<SR_BA_NO>' AND NOM_HASH_ID IN ('<HASH_1>','<HASH_2>', ...) AND BEG_GAS_DAY >= '<BEG_DAY>';
```

> **Which template?** QPTM (`My Quorum Gas Pipeline`) noms → **Template A** (`NNCTRL_*`/`CFCTRL_*`). TIPS/QLNG → **Template B** (`QCTRL_*`, QRMTIPS schema). The SF-side "GhostNominationDelete.sql" / "ghost nomination script" attachments (cases 25-01060757, 25-01027751, 25-01059423) are variants of Template A scoped to a single ghost `NOM_SEQ_NO`.

> **Transaction safety (from the real scripts):** (1) every script begins with a **verify-SELECT** of the target rows — run it and eyeball the count before deleting; (2) delete strictly **child → parent** (confirmation → cycle → activity → nom-detail) or constraints block you; (3) the parent `NNCTRL_NOM_DTL` row is keyed by `NOM_SEQ_NO`, while child rows key on `NOM_ID` + gas-day range — don't mix them up; (4) wrap in `BEGIN TRAN ... COMMIT` so you can `ROLLBACK` if a count is off; (5) one block per gas-day range — repeat, don't widen the range.

> **Evidence / provenance:** verbatim script text obtained from ADO attachments **#1806364**, **#1747369**, **#1739654**. Additional script attachments confirmed (titles only, binary in SF) on cases 25-01027751 (`GhostNominationDelete.sql`, `45_BI_NOM_*_DeleteScript.sql`), 24-00958275 (`Delete Permian nom...`), 25-00996203 (`HPE_PRD_*_NomDelete.sql`). On-prem/older clients receive this as a **PDM** instead of a self-service script (22-00803981).

---

## 5. Nom Submission / Validation Errors

The core cluster. A submission is blocked when a validation rule fires **BI** (business) or **LI** (line). Rules are defined in `QARCH_VALD_RULE` (code pattern `NN########`) and toggled/cross-referenced via the **Validation Rule Cross Reference** screen and **Nomination Configuration System Preferences**.

### Common patterns & fixes
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| TT (Trans Type) dropdown blank / required but unpopulated | Pooling TOS x-ref missing; `QCODE_ACTN` and `KCTRL_TOS` name+descr mismatch | Config: fix Nom Config System Pref + align QCODE_ACTN/KCTRL_TOS | 26-01095071 |
| Validation doesn't fire past contract effective end date | Rule only re-evaluates after the date passes | Code fix (on CAB) | 25-01034998 |
| PAL/Park-Loan validations not firing | Missing transaction types in Validation Rule X-Ref; PAL/ISS contract tab not synced | Config + re-run KPALISS batch | 25-01007318, 25-00999987 |
| External user submits past BI error (over MDQ) | No rule preventing external submit over BI | Config: enable/raise severity | 25-00999055 |
| Need to block TT06+TT07 (inj+withdrawal) same day | New validation needed | Config in Nom Config System Pref (block TT07 on Sched-Qty-Override-Source rec loc) | 24-00985223 |
| Zero-qty noms skip Up/Dn name validation (NN4170/NN4180) | Rules only evaluate qty>0 | Config/code | 25-01058114 |
| Nom API: fuel qty / saveOnValidationFailure / returnOnlyErrorActivities not working | API parameter handling defects | Code fix | 25-01018907, 25-01014097, 25-01020820 |
| Nom Maintenance error when changing TSP | Code defect | Software updated | 25-01041634 |

### Diagnostic
```sql
-- Active NN validation rules + severity (which would fire BI vs LI)
SELECT FUNC_AREA_CD, VALD_RULE_CD, VALD_RULE_DESCR, NAESB_CD,
       VALD_RULE_TYPE_CD, SEVERITY_CD, IS_ALLOW_OVRD, IS_ACTIVE
FROM QARCH_VALD_RULE
WHERE VALD_RULE_CD LIKE 'NN%' AND IS_ACTIVE = 1
ORDER BY VALD_RULE_CD;
```
Always check whether the client has a **`<CLIENT>.QPTM.Web` override** of a standard rule before assuming the base behavior (see EDI skill §17).

---

## 6. Contract / Location / Path Errors

Config-driven. The nom references a contract, a receipt/delivery location, and a path; if any is inactive, expired, or not on the contract path, submission fails. (For EDI-side ENMQR301/525-538 see EDI skill §8.)

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| CAS/processing "complete with errors" — volumes not pushing through | Location **end-dated** before the nom's gas day (nom on 5/5, loc end-dated 4/30) | Re-activate / re-date location | 26-01098270 |
| Path Rank field missing from Web Nom Submission | Field not rendered | Code fix | 24-00981562 |
| Nom paths disappear with LI+BI error combo | Unchanged paths dropped from grid | Code fix (Fall 2025) | 24-00952492 |
| Receipt/Delivery path volumes ≠ Up/Dn at bidirectional/TT points | Display/calc defect | Code/config | 22-00818831 |
| Location Centric not matching Nom Maintenance | Sync/display | Config | 23-00905397 |
| Cannot modify/insert valid noms during reallocation period | Reallocation window config | Config | 24-00951650 |
| Path Form on PT noms doesn't keep package IDs | Code defect | Software updated | 25-01020766 |

### Diagnostic (see EDI skill §17 for full NNCTRL_LOC / contract-path queries)
```sql
-- Is the location active for the gas day?
SELECT ID_LOC, LOC_NM, IS_ACTIVE, EFF_DT_FROM, EFF_DT_TO
FROM NNCTRL_LOC
WHERE TSP_NO = <TSP_NO> AND ID_LOC = '<LOC>';
-- Watch for EFF_DT_TO earlier than the nom gas day (26-01098270 pattern).
```

---

## 7. Imbalance / Quantity / MDQ / Fuel

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| "Exceeds MDQ" fires when contract is NOT at MDQ | MDQ config / shared-MDQ not aggregated across paths | Config | 24-00994503, 25-01041489 |
| Over-MDQ nom accepted with no validation | Rule not enabled on contract/TOS | Config (enable) | 24-00985947 |
| FSS storage MDIQ/MDWQ not shown on Nom screen | PT tab only displays MDQ (by design) | Education | 26-01102716 |
| Fuel rate not appearing / fuel not calculated on screen | Missing fuel-rate reference data | Data script to populate `PATRAN_LOC_GRP_*`, `PACTRL_LOC_GRP_OTHER`, `PAHIST_SYS_LOC_GRP_LOC` | 26-01083221 |
| Fuel rounding inconsistent across TSP401→TSP801 AutoGen | TSP fuel-rounding config | Config (TSP 801) | 25-01044076 |
| NNCALCFUEL erroneously resubmitting noms / Oracle constraint, 274 overlapping records | Fuel-recalc batch defect → creates overlapping noms (feeds the §4 cluster) | Code fix | 22-00828752, 24-00976912 |
| Invalid Fuel Qty on API POST | API fuel-qty handling | Code fix | 25-01018907 |

> **Link to §4:** `NNCALCFUEL` defects are a *source* of duplicate/overlapping noms (24-00976912 created 274+ overlapping rows). If duplicate-nom cases spike for a TSP, check whether fuel recalc ran.

---

## 8. Nom Upload (NNNOMLOAD) / Import / Copy-Paste

Batch/bulk entry path. Two recurring failure modes: (a) **validation gaps** — the import path lets through noms the Submission screen would reject; (b) **insert/merge defects** on overlapping date ranges.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Import submits nom that Submission screen would reject (model-type mismatch) | Import skipped Contract-Nom-Model vs Nom-Model check | Code: added model-type validation | 25-01015207 |
| Import accepts invalid TT-for-TOS | Import skips TT/TOS validation | Config | 23-00909876 |
| Import validates Up/Dn ID that manual entry doesn't | Inconsistent validation between paths | Code fix | 23-00928342 |
| NNNOMLOAD "unique constraint" when existing noms span the dates | Insert/merge defect on overlapping ranges (esp. monthly nom spanning multiple days) | Code fix | 24-00957669, 22-00830582 |
| NNNOMLOAD "another user submitted… Please requery" but nom still submits | Concurrency/retrieve-timestamp defect | Code fix | 24-00957668 |
| NNNOMLOAD creating false BI noms for large shippers | Import merge produces spurious BI rows | Code fix | 24-00961235 |
| NNNOMLOAD insert into nom-header table extremely slow / times out (10 min/query) | Header-insert query performance | Code fix (perf) | 24-00953202 |
| Process pop-up doesn't show until screen refresh (looks hung) | Web async/poll defect | Code fix | 22-00825302 |
| Import template missing Path Rank column | Template generation config | Config (re-add field) | 24-00987765, 22-00830410 |
| 30-day copy/paste adds instead of overwriting existing noms | Copy-paste merge config | Config/code | 24-00983163 |
| Copy noms to new month errors (Desktop/Classic only) | Classic copy defect | Code fix | 24-00954247, 24-00961083, 24-00958055 |
| Import invalid locations → PANIGHTLY errors | Validation rule config on import | Config | 25-01002472 |
| NNRPTS_12_NOM_ERROR not populating after NNNOMLOAD | Event-detector auto-param defect; must clear Report ID/Type params | Config workaround + backlog | 22-00825908 |

### Diagnostic
- Pull the NNNOMLOAD process-queue log (look for the slow header-insert and the row that errored).
- Compare the **import template version** the client used vs the current download (Path Rank field is the usual missing column).
- Reproduce by importing the client's exact `.xlsx`; many of these bugs are data-shape-specific (monthly nom spanning a date range over an existing timely nom).

---

## 9. AutoGen Noms

The NNAUTOGEN engine auto-creates target noms (e.g., imbalance/load-following from a Source TSP to a Target TSP, 401→801). Recurring themes: noms generated for the **wrong days / wrong status / parties without a contract**, or AutoGen producing an **activity code instead of a nomination**.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Storage AutoGen 401→801 not generating | Wrong `DefaultMetadataProfile` / `SupportedMetadataProfiles` | Config change | 24-00977086 |
| AutoGen creates **activity codes** instead of target noms; "BUSINESS OR LINE LEVEL ERRORS… ACTIVITY ID" warning | Underlying EPSQ nom-submission error blocks generation; needs graceful handling | Code fix (release upgrade) | 24-00984178 |
| AutoGen runs for ID1 but updates noms 5 days back into **Late status** | AutoGen day-targeting defect (critical — impacts inventory) | Investigate AutoGen day selection | 25-01022652 |
| AutoGen external-user submit doesn't autogen (internal does), no fail/activity | Core hotfix needed | Software updated (2024.04 hotfix) | 25-01011822 |
| AutoGen creates target noms for external customer w/o TSP/contract access | Target-resolution defect | Software updated | 25-01007550 |
| AutoGen single-day trigger generates a **full month of range noms** + unexplained activity codes; NN3176 fires | Range-nom generation defect (or expected if multi-day submitted) | Education / investigate | 23-00903185, 23-00898288 |
| AutoGen populating incorrect DownK name | Down-name population defect | Software updated | 25-01000534 |
| AutoGen "dummy" Mustang paths created for Green Country setup | Shared-contract setup defect | — | 25-01002594 |

> **Enhancement (not a defect):** cross-TSP target contracts (Up/Dn population across TSPs) and configurable imbalance thresholds are **enhancement requests**, not bugs — 26-01091462, 24-00984415, 26-01065484. Classify accordingly.

### Diagnostic
- Confirm Source/Target TSP and the AutoGen rule type (DIS/DIL imbalance, load-following).
- Check the AutoGen batch log for "NOM AUTOGEN WARNING… ACTIVITY ID: `<n>`" — that means a downstream validation (often EPSQ) failed and an activity code was left instead of a nom.
- Verify the metadata profile config on the target TSP (24-00977086).

---

## 10. Nom Deletion Runbook (Ops)

Routine but high-frequency. Clients open "Nom Deletion Request" cases supplying TSP, Svc Req, gas-day range, and NOM_ID(s). Many also stem from a nom that **won't delete via the UI** because of the §4 overlap/ghost condition.

### Safe deletion procedure
1. **Get the exact identifiers:** `TSP_NO`, `Svc Req (BP_NO)`, `Gas Day` (Beg + Def End), `NOM_ID(s)`, cycle, and the **deadline**.
2. **Verify before deleting** with diagnostic SQL #1–#3 (§4). Confirm the record(s) are bad/orphaned and not active production noms you'd be destroying. Common legitimate reasons: missing DUNS# causing EDI errors (26-01091559), nom missing `DEL_LOC_ID` breaking NNAUTOGEN/EDI/OpCap jobs (22-00803981).
3. **Provide the delete script to Cloud Ops** for PRD deployment — use the **verbatim, parameterized templates in §4** ("Standardized nom-delete scripts"): **Template A** (QPTM `NNCTRL_*`/`CFCTRL_*` cascade by `NOM_ID`+`NOM_SEQ_NO`) or **Template B** (TIPS/QLNG `QCTRL_*` by `NOM_HASH_ID`, QRMTIPS schema). For older/on-prem this may be a **PDM** (Production Data Modification) rather than a self-service script (22-00803981 PDM for NOM_ID 5423184).
4. **Confirm scope:** delete "for GD `<n>` forward" as the client specifies, not the whole month, unless asked.
5. Have the client re-query and resubmit.

Representative deletion cases: 26-01091559, 26-01090812, 25-01030613, 25-01010084, 25-01005020, 26-01063743, 25-01044354.

> Some "can't delete" cases resolve with **no script** — the client fixes the ghost themselves on a call (26-01099339) or the blocking cycle simply closes (26-01097498). Try the cheap path first.

---

## 11. Late / Retro / Cycle Deadline (cross-link)

**Do not duplicate the EDI skill.** For ENMQR315 (late/retro nom), `RuleNN00009011`, cycle deadline config, and `PACTRL_CYCLE_DEADLINE`, see **SKILL_EDI_Troubleshooting.md §4, §6, §11**.

QPTM-screen-specific notes found in cases:
- **Cycle deadline mis-config breaks all submission** for a TSP set up via scripts — verify `PACTRL_CYCLE_DEADLINE` rows exist and are correct (25-01044634, TPCO2).
- **External users can bypass late-nom override** by editing fields that don't re-trigger the rule (Up Rank/Dn Rank/Nom User Data 1/2) once a late nom was already overridden — fixed in 2024.04 (23-00902666).
- **"Nomination Deadlines by Type of Service" not working as designed** (25-01010386).
- **Late/BI noms not appearing on NN12 Nom Error Report** — see §12 (25-01001265).
- Retro-nom how-to is a Training case — provide steps, not a fix (25-01061715).

---

## 12. Nom-Related Reports

Lower volume; usually report-config or registered-SQL issues.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Late/BI noms missing from **NN12** Nom Error Report | Report status filter excludes BI/LI | Code/config | 25-01001265 |
| Pool Balance External Report "Error in registered SQL: m_Ins_SQLID_NN03_POOL" | Registered SQL defect | Code fix | 24-00945479, 23-00904173 |
| **ALR93** report 2 date-range fields break re-run | Report parameter design | Config | 23-00890970 |
| REPORT EXPORT MODE parameter breaks scheduled jobs | Param config | Config | 23-00926219 |
| Erroneous reports being sent | Scheduling config | Config | 23-00922319 |
| Transactional Reporting duplicating FT/IT lines on re-run; IT noms missing dates | Report dedup + date defect | Code | 25-01025914, 25-01025910 |

---

## 13. Web / UI Rendering Issues on Nom Pages

Web-specific (vs Classic/Citrix). Many of these are the *visible* symptom of a deeper data/grid issue.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Spinning wheel prevents Add Row (PT path / PNT Up-Dn) | Web grid add-row defect | Code fix | 25-01036695 |
| Nom paths disappear (LI+BI combo) | Grid drops unchanged rows | Code fix | 24-00952492 |
| Nom Maintenance line with no matching Nom Submission line (ghost) | §4 activity/NOM_ID mismatch surfacing in UI | Data script | 26-01085239 |
| Fuel rate not reflected on nom path | Missing fuel ref data | Data script | 26-01083221 |
| Nom not visible in Submission screen but visible in Confirmation Response; classic doesn't throw overlap error | Web/Classic validation+render inconsistency | Code fix | 25-01016479 |
| Nom Maintenance Screen Date wrong | Config | Config | 25-01020185 |
| 30-day pop-up populates random data on forward days after edit/submit | Copy/30-day grid defect | Config/code | 25-01054466 |
| API GET requires security user in deployed envs | Deployment/auth | Code fix | 25-01018906 |

> When a client says "I can't see the nom but the system says it exists," treat it as a **§4 ghost-nom** case, not a pure UI bug — run the §4 diagnostics.

---

## 14. Expected Behavior / User Education

Not every Nominations case is a defect. Root Cause = **Customer Error / Training** (~150+ cases). Recognize these to avoid unnecessary scripts/escalations.

| Reported as | Reality | Case |
|-------------|---------|------|
| "Gas day defaults to 10am-9am, should be 9am-9am CST" | Time matches the cycle on the Nom Submission screen — correct as designed | 26-01097569 |
| "Duplicate key error, can't save" | Customer-induced overlap (edited a submitted nom / copied bad path) | 26-01099624, 26-01084541, 26-01098678 |
| "Can't see / submit, overlap error" | Their own shipper deleted a nom mid-cycle, or ID1 already closed → submit under ID2 | 26-01097498 |
| "AutoGen generated a month of noms" | Customer submitted a multi-day (range) trigger nom — working as designed | 23-00903185 |
| "Nom volumes reverting after month-end" | Process the client was running, not reproducible | 25-01031073 |
| "Load Following extra upstream record" | Data-related setup, not a bug | 26-01065484 |
| "Need help adding a retro nom" | Provide documentation/steps | 25-01061715 |
| FSS storage MDIQ/MDWQ not on Nom screen | PT tab only shows MDQ by design | 26-01102716 |
| "CAS complete with errors" | Location end-dated before the nom gas day — fix the location, not the nom | 26-01098270 |

**Tell-tale that it's user/expected:** the client created the overlap by editing an editable field (REC Rank) on an already-submitted nom, or by copying a bad path forward; or the "error" is a correctly-firing validation.

---

## 15. Key Code Files & Repos

### Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
| File | Purpose |
|------|---------|
| `Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService.cs` | **Submit/validate noms; source of the "dates that overlap another nomination" message** (overlap check) |
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerNominationSubmissionBase.cs` | **Nom Submission Web controller; `IdNomForAdded` / NOM_ID assignment — root of the duplicate-NOM_ID defect (ADO #1761678)** |
| `Quorum.QPTM.ClassicGUI/Managed/Quorum.QPTM.UserControls/PathBindingSource.cs` | Classic PT path grid binding |
| `Quorum.QPTM.ClassicGUI/Managed/Quorum.QPTM.UserControls/LCPathBindingSource.cs` | Classic Location-Centric path binding |
| `Quorum.QPTM.Validations/...` | Validation rules (`RuleNN########`) |

### Quorum.QPTM.Batch (e024d80b-5c45-411c-93e1-78e2798ed885)
| File / process | Purpose |
|----------------|---------|
| `NNNOMLOAD` (Nom Upload/Import) | Bulk nom import; unique-constraint & validation-gap defects (§8) |
| `NNAUTOGEN` | AutoGen target-nom generation (§9) |
| `NNCALCFUEL` | Fuel recalc batch — can create overlapping noms (§7) |
| `KPALISS` | PAL/ISS contract-value sync (must run after contract changes) |

### Override repos
`<CLIENT>.QPTM.Web` (e.g., APL, OKTEX, ONK/ONEOK, TEP) override base validation rules and submission behavior. **Always check for a client override before assuming base behavior.** Code search: `{"searchText":"<RuleID> repo:<CLIENT>.QPTM"}`.

> Cross-product note: TIPS (`Quorum.TIPS.Web/QTIPSServiceCore_Nomination.cs`) and QLNG share the same "overlap" message logic — relevant if mining the TIPS assistant.

---

## 16. Database Tables Reference

| Table | Purpose |
|-------|---------|
| `NNCTRL_NOM_DTL` | **Nomination detail (NOM_ID, gas-day range, cycle, status, qty, loc, ctr). Primary table for overlap/dup diagnosis.** |
| `NNCTRL_NOM_HDR` | Nomination header |
| `NNCTRL_ACTV_DTL` | **Activity detail the Submission grid binds to; ghost noms = NOM_ID mismatch here (#1761678)** |
| `NNCTRL_NOM_ERROR` | Nomination validation errors |
| `NNCTRL_CTR` / `NNCTRL_CTR_ATTR` / `NNCTRL_CTR_PATH` | Contracts, attributes, paths |
| `NNCTRL_LOC` / `NNCTRL_LOC_ATTR` | Locations (check EFF_DT_TO vs gas day) |
| `PACTRL_CYCLE` / `PACTRL_CYCLE_DEADLINE` | Cycle defs & deadlines (see EDI skill) |
| `QARCH_VALD_RULE` | Validation rule definitions (NN########) |
| `QCODE_ACTN` / `KCTRL_TOS` | Action codes / Type-of-Service (name+descr must align — 26-01095071) |
| `PATRAN_LOC_GRP_*`, `PACTRL_LOC_GRP_OTHER`, `PAHIST_SYS_LOC_GRP_LOC` | Fuel-rate / loc-group ref data (26-01083221) |
| `NNRPTS_12_NOM_ERROR` | Nom Error Report (NN12) backing table |
| `EDTRAN` / `EDTRAN_QR_ERROR` | EDI transaction + QR errors (see EDI skill) |

---

## 17. Diagnostic SQL Queries

(See §4 for the duplicate/overlap queries — the most-used set.)

### A. Full nom detail for a NOM_ID (the client-supplied ID)
```sql
SELECT NOM_SEQ_NO, TSP_NO, NOM_ID, BEG_GAS_DAY, END_GAS_DAY, ORIG_END_GAS_DAY,
       CYCLE_ID, NOM_STAT_CD, ACTN_CD, REC_QTY, REC_RANK, DEL_QTY, DEL_RANK,
       FUEL_QTY, FUEL_PCT, REC_LOC_ID, DEL_LOC_ID, SR_BP_NO, SR_CTR_NO,
       ACTV_NO, ACTV_DTL_NO, DELETE_IND, NOM_HASH_ID, SYS_SRC_CD, SUBMIT_DT, USER_ID
FROM NNCTRL_NOM_DTL
WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
ORDER BY CYCLE_ID, BEG_GAS_DAY;
```

### B. Noms for a shipper/gas-day (find the conflict set)
```sql
SELECT NOM_ID, CYCLE_ID, BEG_GAS_DAY, END_GAS_DAY, NOM_STAT_CD,
       REC_LOC_ID, DEL_LOC_ID, REC_QTY, DEL_QTY, SR_CTR_NO
FROM NNCTRL_NOM_DTL
WHERE TSP_NO = <TSP_NO> AND SR_BP_NO = <BP_NO>
  AND '<GAS_DAY>' BETWEEN BEG_GAS_DAY AND END_GAS_DAY
ORDER BY CYCLE_ID, NOM_ID;
```

### C. Activity / NOM_ID mismatch (ghost-nom check — #1761678)
```sql
SELECT NOM_ID, ACTV_NO, ACTV_DTL_NO, BEG_GAS_DAY, END_GAS_DAY, NOM_STAT_CD
FROM NNCTRL_ACTV_DTL WHERE ACTV_NO = <ACTV_NO> ORDER BY NOM_ID;
-- Compare max(NOM_ID) here vs max in NNCTRL_NOM_DTL; a 10000000+ jump = the defect.
```

### D. Active validation rules
```sql
SELECT VALD_RULE_CD, VALD_RULE_DESCR, VALD_RULE_TYPE_CD, SEVERITY_CD,
       IS_ALLOW_OVRD, IS_ACTIVE
FROM QARCH_VALD_RULE WHERE VALD_RULE_CD LIKE 'NN%' AND IS_ACTIVE = 1
ORDER BY VALD_RULE_CD;
```

### E. Location active for gas day
```sql
SELECT ID_LOC, LOC_NM, IS_ACTIVE, EFF_DT_FROM, EFF_DT_TO
FROM NNCTRL_LOC WHERE TSP_NO = <TSP_NO> AND ID_LOC = '<LOC>';
```

### F. Contract MDQ
```sql
SELECT CTR_NO, CTR_MDQ, OVRD_CTR_MDQ, EFF_DT_FROM, EFF_DT_TO, IS_ACTIVE
FROM NNCTRL_CTR WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<CTR>';
```

---

## 18. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1761678** | Bug / **Closed** | APL — Nom Submission generating duplicate NOM_IDs in NNCTRL_ACTV_DTL (`IdNomForAdded` wrong; IDs start at 10000000; reseed didn't help) | §4 Duplicate/Ghost | 25-01049356 |
| **#1699360** | Bug / **Closed** | RCA: Duplicate Nom Error Cima on Ruby (recurring, solved by delete script) | §4 Duplicate | 24-00990345 |
| #1739654 | Script Deployment / Closed | MOM — Remove Duplicate Noms | §4 Duplicate | 25-01027984 |
| #1747369 | Script Review / Closed | HEP — review scripts to delete a duplicate nom causing EDI errors | §4 / §10 | — |
| #1620547 | Task / Closed | ENT — Duplicate nomination error thrown while submitting (DEV) | §4 | — |
| #1655926 | Bug / **Proposed** | ONK — PDA Submission screen attempts to create a duplicate Nomination Header | §4 | 24-00949186 |
| #1806364 | Request Global Cloud Ops / Closed | TEP — Duplicate Nom on REX, nom deletion deployment | §4 / §10 | 26-01099232 |
| #162571 | Bug / Closed | CRW17 — AutoGen Nominations disappearing | §9 AutoGen | — |

> The big takeaway: duplicate/overlapping-nom cases are dispositioned operationally (delete script) rather than via a single product fix. The closest thing to a code root cause is **#1761678** (Web NOM_ID generation). Many "Duplicate Nom" SF cases are NOT linked to an ADO bug — they're recurring Cloud Ops script deployments.

---

## 19. Escalation Decision Tree

```
Nomination case reported
│
├─ "dates that overlap" / "duplicate key" / can't delete/zero a nom?  (§4, §10)
│   ├─ Get NOM_ID + TSP + shipper + gas day + cycle + deadline
│   ├─ Run §4 SQL #1–#3 → confirm overlap/ghost (and #1761678 ID-jump pattern)
│   ├─ Customer created it (edited submitted nom / copied bad path)? → may be Customer Error; try UI fix first
│   ├─ Confirmed orphaned/ghost? → provide standardized nom-DELETE script to Cloud Ops (deadline-boxed)
│   └─ Recurring for this TSP/shipper? → link to RCA #1699360; check if NNCALCFUEL ran (§7)
│
├─ Validation blocking submit (BI/LI)?  (§5)
│   ├─ Is the rule firing CORRECTLY (over MDQ, bad TT/TOS)? → Config / educate
│   ├─ Rule NOT firing when it should? → enable in Validation Rule X-Ref / Nom Config System Pref
│   └─ Client has <CLIENT>.QPTM.Web override? → check the override rule
│
├─ Contract / location / path?  (§6)
│   └─ Check NNCTRL_LOC EFF_DT_TO vs gas day, contract effective dates, path membership
│
├─ MDQ / fuel / imbalance?  (§7)
│   └─ MDQ config / shared-MDQ aggregation / fuel ref data / NNCALCFUEL
│
├─ Excel import / NNNOMLOAD / copy-paste / 30-day pop-up?  (§8)
│   ├─ Validation gap (import lets bad nom through)? → code fix
│   ├─ Unique-constraint / merge error on overlapping dates? → code fix
│   └─ Template missing field / perf / pop-up? → config or code per table
│
├─ AutoGen wrong/excess/late noms or activity-codes-not-noms?  (§9)
│   ├─ Metadata profile / target-TSP resolution? → config (24-00977086)
│   ├─ Activity code + AUTOGEN WARNING? → downstream validation (EPSQ) failed; investigate
│   └─ Cross-TSP target / threshold request? → ENHANCEMENT, not a bug
│
├─ Report (NN12 / ALR93 / Pool Balance / transactional)?  (§12)
│   └─ Report filter / registered SQL / parameter config
│
├─ Web/UI: spinning wheel, vanishing paths, ghost rows?  (§13)
│   └─ If "exists but I can't see it" → treat as §4 ghost-nom
│
└─ Late / retro / cycle deadline?  →  SEE SKILL_EDI_Troubleshooting.md §4/§6/§11
```

---

*Skill created: 2026-06-01*
*Based on: ~430 QPTM Nominations SF cases + ADO work items #1761678, #1699360, #1739654, #1747369, #1620547, #1655926, #1806364, #162571*
*Companion: SKILL_EDI_Troubleshooting.md (EDI/cycle-deadline/late-nom). Applicable to all QPTM TSPs/clients.*
