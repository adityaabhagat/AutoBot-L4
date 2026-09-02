# SKILL — FLOWCAL Database & Performance (Oracle / SQL Server, partitioning, purge, sequences, DB errors)

> **Product:** FLOWCAL (Product_list__c `FLOWCAL`; SQL Server clusters also cover `TESTit` and `PROVEit` field apps)
> **Coverage plan group:** #6 — Database & performance (~4,130 family cases, ~260 actionable)
> **Sources:** Salesforce closed-case mining (all history, 2014–2026-09; ~150 cases surveyed, 44 detail-sampled) + ADO org `QuorumSoftware` (projects `Quorum`, `QuorumSoftware`, `myQuorum Cloud`; area paths `Quorum\North America\Measurement*`, `QuorumSoftware\Engineering\Measurement\Maintenance`). Mined 2026-09-02.
> **Auto-Bot** — the L4 issue solver built by **Aditya Bhagat**.
> Confidence labels: `CONFIRMED` = anchored to SF Resolution/ADO repro/verbatim SQL; `INFERRED` = fixed-in-build claim from case text or regression-test listing, not release-notes-verified.

FLOWCAL persists to Oracle (large enterprise installs, schema owner **FCOWNER**, app roles `fcuser` / `fcviewer` / `fcadministrator`, service accounts `FCSRV` / `svcfcinstant`) or SQL Server (small installs + the TESTit/PROVEit field apps). DB-level failures surface in the app as `(CDbio)Db Error ...` popups, `Error (201)(12): Unable to save data.` messages, and entries in the **FC_DB_ERROR.log** file on the app/service server. Most "database" cases resolve at G2 (config: space, profiles, parameters) or G4 (bad data: stray rows, exhausted sequences) — true code defects cluster around import/TQ constraint violations and close-path performance regressions.

---

## 1. Quick Triage

| Symptom | Likely cause | § |
|---|---|---|
| `ORA-01653: unable to extend table FCOWNER.<T> ... in tablespace <TS>` (imports/rollups stop) | Tablespace full — add datafile (G2 config, not a product bug) | §3 |
| `ORA-08004: sequence <S>.NEXTVAL exceeds MAXVALUE` (Volume Editor, rollups, edits fail) | Sequence exhausted (2^31-1) or MAXVALUE mangled by refresh/scripts — reset via negative range | §4 |
| Sequences broken right after a UAT←PRD refresh | Refresh copied data but sequences out of sync — sequence-fix SQL | §4.4 |
| `ORA-00001: unique constraint (FCOWNER.FC_AMETANL_PK) violated` — TQ + CFX imports ALL stop | Known defect: stray rows in FC_METER_ANALYSIS_ALT; delete them; fixed 10.6.0.13 (INFERRED) | §5.1 |
| `ORA-00001 (FCOWNER.FC_BATCHRPT_PK)` importing FC_BATCH_REPORT revision via TQ | Defect, fixed 10.9.0.1 (INFERRED) | §5.2 |
| `ORA-02291 (FCOWNER.FC_METANL_F_LAB_ANALYSIS_ID) parent key not found` on CFX import | Older-version source/lab-analysis defect — workaround + upgrade | §5.3 |
| `ORA-00001 (FCOWNER.FC_GQANLEXT_PK)` on GQ apply | Duplicate GQ extended-analysis rows — purge month, re-import, re-apply | §5.4 |
| `ORA-00001 (FCOWNER.LCNROLLQ_PK)` while purging | Location rollup queue collision — drain/reset queue + sequence | §4.2 |
| "Warning: Purge NOT allowed because there are PPAs" but "No PPA to purge" | End-of-time PPA rows in fc_ppa_accounting_info / fc_meter_edit — data-fix SQL | §6.1 |
| Purged PPA still shows on PPA Approvals screen | Defect: test-report apply wrote edit_type='E' not 'P'; fixed 10.6.0.14 / 10.8.0.4 (INFERRED) | §6.2 |
| Purge PPA fails on split batches (10.2.x) | PPA Batch Split defect — SQL + recalc/save batch workaround | §6.3 |
| `ORA-01502: index ... or partition of such index is in unusable state` | Partition maintenance left index unusable — rebuild; recurring on FC_MTRROLLQ_PK | §6.5 |
| Meter close suddenly slow since 10.6.0.7 (gas meters, fcm/fct_component_periodic_rev) | Component close-translation regression — `close_gas_components = N` debug option / 10.6.0.11 | §7.1 |
| Slow point-to-point / import on GPA 2172 meters | Duplicate Edit Reason rows (defect) — dedup SQL; fixed 10.6.0.18 / 10.8.0.9 / 10.9.0.1 (INFERRED) | §7.2 |
| Volume Editor freezes ~30 s opening months with many notes | Fixed 10.6.0.12 (INFERRED, RN-quoted in case) | §7.3 |
| Deleting meters takes 19–20 min (Non-Reg) | FC_REPORT_SCHEDULE(_PARAM) query bottleneck; resolved 10.6.0.11 (INFERRED) | §7.4 |
| `ORA-02395: exceeded call limit on IO usage` | Oracle profile LOGICAL_READS limits too low — ALTER PROFILE (G2) | §7.5 |
| `ORA-00020: maximum number of processes exceeded` (TESTit services) | Connection leak, expected fixed TESTit 3.17 (INFERRED); raise processes + reinstall services | §7.6 |
| Meters "locked", can't edit/import/close; "abnormal program termination" | Stale service lock (restart FC services) or liquid-import infinite-loop defect | §8.1 |
| Can't log in / services can't connect right after refresh or upgrade | DB account passwords/locks out of sync after RMAN clone — alter user ... account unlock | §8.2 |
| `ORA-12154` / `ORA-12170` / `ORA-12514` TNS errors | Connectivity/listener/tnsnames — environment, not product | §8.3 |
| `ORA-03113` / `ORA-03114` end-of-file / not connected (desktop) | Network path broken — antivirus (AVG/Avast) confirmed culprit once | §8.3 |
| FLOWCAL upgrade DB scripts fail on Oracle 19c (identifier too long / invalid table name) | `COMPATIBLE` init parameter still 11.x — set to 19.0.0 | §8.4 |
| SQL Server 2022 install fails on Windows 11 (PROVEit/TESTit) | NVMe 4K-sector issue — registry workaround | §8.5 |
| PROVEit/TESTit Password Utility: `Sqlcmd ... Login failed for user 'SA'` | Known DB-creation failure on SQL 2019/2022 — KB 000004569 + `__createMSDb.sql` | §8.5 |

## 2. Decision Tree

```
DB / performance issue reported
├─ Specific ORA-/SQL error code in log or popup?
│   ├─ ORA-01653 (unable to extend) → tablespace full → §3 add datafile; ask WHY it grew (§3.2)
│   ├─ ORA-08004 (sequence exceeds MAXVALUE) → §4 sequence reset (which sequence? §4.1–4.3)
│   ├─ ORA-00001 unique constraint → which PK?
│   │   ├─ FC_AMETANL_PK → §5.1 known defect (FC_METER_ANALYSIS_ALT cleanup)
│   │   ├─ FC_BATCHRPT_PK → §5.2 fixed 10.9.0.1
│   │   ├─ FC_GQANLEXT_PK → §5.4 purge/re-import/re-apply
│   │   ├─ LCNROLLQ_PK → §4.2 rollup queue + sequence reset
│   │   └─ FC_METPER_PK (import by IMPORTID) → duplicate periodic rows — treat as G4, compare import file vs fc_meter_periodic_values
│   ├─ ORA-02291 FC_METANL_F_LAB_ANALYSIS_ID → §5.3
│   ├─ ORA-02395 → §7.5 profile limits
│   ├─ ORA-00020 → §7.6 processes/connection leak
│   ├─ ORA-01502 unusable index/partition → §6.5 rebuild
│   ├─ ORA-12154/12170/12514 → §8.3 TNS/listener (environment)
│   └─ ORA-03113/03114 → §8.3 network path/antivirus
├─ No error code — "slow"?
│   ├─ Slow CLOSE (gas meters, since 10.6.0.7) → §7.1
│   ├─ Slow on GPA 2172 meters / slow import on one meter → §7.2 duplicate edit reasons
│   ├─ Volume Editor slow to open a month → §7.3 (notes) / check periodic row counts
│   ├─ Slow meter DELETE → §7.4
│   └─ Whole app slow after upgrade/refresh → stats stale? partitioning health check (§6.4); env/Citrix out of scope → Security/FLOWCloud skills
├─ Purge won't run / purged data still visible? → §6 (PPA blockers first — most purge failures are PPA rows)
├─ Meter locked / can't edit-import-close? → §8.1 restart services first, then match defect
├─ Right after a DB refresh? → §4.4 sequences + §8.2 passwords + rerun post-refresh checklist
└─ Install/DB-create failures (SQL Server, field apps)? → §8.5
```

Gate mapping: §3, §7.5, §8.2–§8.5 are usually **G2 Config**; §4, §5.4, §6.1, §6.5 are **G4 Bad Data** (with correction SQL); §5.1–5.3, §6.2–6.3, §7.1–7.4, §7.6, §8.1(defect) are **G3 Version / G5 Code**. Routine UAT←PRD refresh requests are ops tickets (`Database Refresh Request` root cause), not investigations.

---

## 3. Cluster A — Tablespace exhaustion (ORA-01653)

### 3.1 Signature and fix recipe
- **Signature:** `ORA-01653: unable to extend table FCOWNER.<TABLE> by 8192 in tablespace <TS>` in FC_DB_ERROR.log / service logs / "Unable to save data" popups. Imports, rollups, or saves stop. Recurring offenders across a decade of cases: `FC_FFMTR_HOURLY` in `FC_ROLLUPS_FFMTRHLY_TS` (SF 26-01079753, 23-00902929, 22-00625918, 22-00653527, 22-00534478), `FC_METER_PERIODIC_VALUES` in `FC_MAIN_MPER_TS` (SF 22-00528696 — system down), `FC_METER_ANALYSIS` in `FC_MAIN_TS` via FCSRVTRANS (SF 22-00633005), general `FC_MAIN_TS` (SF 24-00973539). Location rollups stopping is a classic presentation (SF 23-00889118).
- **Root cause:** Datafile(s) for the tablespace hit max size / disk full. G2 config (DBA action), not a product bug.
- **Fix recipe (`CONFIRMED` verbatim from SF 22-00528696):**
```sql
-- as SYSTEM: see existing datafiles for FC tablespaces
select tablespace_name, file_id, round(bytes/1024/1024/1024) file_gb,
       substr(file_name,1,90) file_name
from dba_data_files
where tablespace_name like 'FC%'
order by 1,2;

-- add a datafile (adjust path/TS name; can live on a different drive — SF 25-01023601)
alter tablespace FC_MAIN_MPER_TS
   add datafile '<path>\FC_MAIN_MPER_TS_29.FCF' size 100M reuse
   autoextend on next 100M
   MAXSIZE UNLIMITED;
```
- **Anchors:** SF 22-00528696 (verbatim SQL), 26-01079753 (App Config; KB article on tablespace sent), 25-01023601 (datafile on a different drive when DB drive full), 25-01023361, 24-00973539, 23-00889118, 22-00633005.

### 3.2 Ask WHY the tablespace filled
- `CONFIRMED` SF 24-00973539: FC_MAIN_TS filled "too quickly" because the customer queued **all meters for "All Data"** rollups; after adding space, the Meter Rollup service failed again — two meters (9025, 9018) had **future rollup dates 1/1/2037 to EOT** in the queue. Fix: put the future-dated queue records on **Hold**, restart Meter Rollup Service, clean up the rollup queue.
- Rapid FFMTR_HOURLY growth = final-form hourly rollups; check rollup scope and purge/partition strategy (§6.4) before just adding space.

---

## 4. Cluster B — Sequence exhaustion & corruption (ORA-08004)

FLOWCAL Oracle schemas allocate surrogate keys from FCOWNER sequences capped at 2,147,483,647 (signed 32-bit). High-churn sites exhaust them; the supported trick is to **swing into the negative range** (min -2,147,483,646). A "Packaging Issue - Database Scripts" root cause was coded on one case (SF 23-00885414) — upgrade scripts had left MAXVALUE wrong.

### 4.1 FC_UNIQUENUM_SEQUENCE (Volume Editor errors)
- **Signature:** `ORA-08004: sequence FC_UNIQUENUM_SEQUENCE.NEXTVAL exceeds MAXVALUE and cannot be instantiated` opening/saving in Volume Editor.
- **Fix:** reset the sequence; MAXVALUE **should be 2147483647** (was found mangled); when the positive range is truly exhausted, "our trick is to go and use the negative values" (`CONFIRMED` SF 23-00885478, 23-00885414 — root cause coded *Packaging Issue - Database Scripts*).

### 4.2 FC_LCNROLLQ_SEQ (location rollup queue; also LCNROLLQ_PK collisions on purge)
- **Signature:** `ORA-08004: sequence FC_LCNROLLQ_SEQ.NEXTVAL exceeds MAXVALUE` + `ORA-04088: error during execution of trigger 'FCOWNER.FC_LCNROLLQ_INDEX'`; or `(CDbio)Db Error ORA-00001: unique constraint (FCOWNER.LCNROLLQ_PK) violated` when purging data (SF 26-01084565).
- **Fix recipe (`CONFIRMED` verbatim from SF 24-00967605):**
```sql
-- 1. Stop all location and meter rollup services.
-- 2. Any unprocessed queue records?  N=not processed, Y=processed, M=merged
select rolled_up, count(*), min(ROW_INDEX), max(ROW_INDEX)
from fc_location_rollup_queue group by rolled_up;
-- If no 'N' rows:  truncate table fc_location_rollup_queue;
-- If 'N' rows exist, clear only processed ones (repeat until clean):
delete fc_location_rollup_queue where rolled_up = 'Y' and rownum < 100000; commit;
delete fc_location_rollup_queue where rolled_up = 'M' and rownum < 100000; commit;
-- 3. Swing the sequence negative:
alter sequence FC_LCNROLLQ_SEQ increment by -2147483600;
select FC_LCNROLLQ_SEQ.nextval from dual;
alter sequence FC_LCNROLLQ_SEQ increment by 1;
select FC_LCNROLLQ_SEQ.nextval from dual;
```
  Shortened variant (`CONFIRMED` SF 25-01021271): `alter sequence fc_lcnrollq_seq minvalue -2147483646; alter sequence fc_lcnrollq_seq restart start with -2147483600; alter sequence fc_lcnrollq_seq maxvalue 0; select fc_lcnrollq_seq.nextval from dual;` then verify with `select min_value, max_value, last_number from all_sequences where sequence_name = 'FC_LCNROLLQ_SEQ';`
- **Anchors:** SF 24-00967605, 25-01021271 (proactive "about to run out"), 26-01084565.

### 4.3 FC_MTREDIT_ROWIDX_SEQUENCE (meter edit tables) — heavy surgery
- **Signature:** `ORA-08004: sequence FC_MTREDIT_ROWIDX_SEQUENCE.NEXTVAL exceeds MAXVALUE` — meter edits fail everywhere.
- **Fix (`CONFIRMED` SF 25-01000305, explicitly *not* one-size-fits-all — solution depends on the client's data):** investigate min/max/count of `METER_EDIT_INDEX` by year in `FC_METER_EDIT`, `FC_METER_EDIT_DETAIL`, `FC_METER_EDIT_APPROVAL` (positive vs negative ranges); keep the currently-active range (that client: negative), rebuild via `create table ... parallel 8 as select ... where meter_edit_index < 0`, drop+rename, re-grant (`fcviewer` select; `fcuser`,`fcadministrator` select/insert/update/delete), recreate public synonyms, recreate trigger `fc_mtreditdet_rowidx` (`SELECT fc_mtredit_rowidx_sequence.NEXTVAL INTO :NEW.row_index FROM dual;`), recreate PK/FK/check constraints and indexes (`FC_MTREDIT_PK`, `FC_MTREDITDET_PK`, `FC_MTREDIT_F_METER_NUMBER_INDE`, `FC_MTREDITDET_F_METER_EDIT_IND`, `FC_MTREDITAPPRV_F_METER_EDIT_I` — enable novalidate), then reset the sequence (`maxvalue 2147483647`, verify nextval > 0, `minvalue 0`) **line by line, never as one script**. Full verbatim SQL is preserved in the case's Resolution.
- **Sanity checks first:** `select table_name, trigger_name from all_triggers where table_name like 'FC_METER_ED%';` and `select sequence_name, min_value, max_value, last_number from all_sequences where sequence_owner = 'FCOWNER' order by 1;`

### 4.4 Sequences out of sync after a database refresh
- **Signature:** PK violations / ORA-08004 shortly after a UAT←PRD (or PRD←UAT) refresh.
- `CONFIRMED` SF 26-01100082: "provided SQL to fix their sequences after a UAT refresh from PRD." SF 25-01002310 ("Fixing the sequences in the PROD database") was coded **Software Defect** with "fixed in 10.8" (INFERRED). Historical upgrade script `update_sequences7_4_6 to 7_4_15.sql` (SF 22-00529524) shows sequence-sync is a maintained script family.
- **Recipe:** for each FCOWNER sequence, compare `last_number` against `max(<pk column>)` of its table; restart the sequence above the max. Add this to every refresh checklist (§8.2).

---

## 5. Cluster C — Constraint violations blocking imports / TQ (ORA-00001, ORA-02291)

### 5.1 FC_AMETANL_PK — the big one: ALL TQ + CFX imports stop
- **Signature:** `Error: ORA-00001: unique constraint (FCOWNER.FC_AMETANL_PK) violated` repeatedly in FC_DB_ERROR.log; `Error (201)(12): Unable to save data.`; manual imports also fail; "Characteristic Error(201)(12)" variant on meter edit (SF 26-01112798). Everything importing to affected meters ceases.
- **Root cause (`CONFIRMED` ADO Bug 1770141 / 1717255):** stray "empty" rows accumulate in **FC_METER_ANALYSIS_ALT** (alternate analysis table) with `sequence_number = 0` — FLOWCAL touched the alt analysis/periodic tables even though "Import Alternate Periodics" was NOT enabled on the meter (Meter Editor > Imports tab, `meter_2.import_alternate_periodics` null = No). Next import collides with those rows.
- **Workaround (`CONFIRMED`, executed by Cloud DBA in ADO 1840164 — 94,806 rows for CFL/Coastal Flow, and ADO 1795593 — 5,463 rows for CHD/Chord Energy):** verify the rows are empty, then `DELETE FROM FC_METER_ANALYSIS_ALT;` + commit. Verification PL/SQL (loops all_tab_cols and counts non-null values per column of FC_METER_ANALYSIS_ALT) is preserved verbatim in ADO 1795593. A Quorum KB article exists: "Troubleshooting Error ORA-00001: unique constraint (FCOWNER.FC_AMETANL_PK) violated for FLOWCAL" (SF 26-01114165).
- **Fixed in:** FLOWCAL **10.6.0.13** (INFERRED from SF 26-01114165 + 26-01074177 resolutions; ADO 1774534 R1060 PORT is listed in the "FLOWCAL 10.6.0.13 Targeted Regression Testing" work item 1776672) and 10.8.0.3+ (SF 26-01074177); DEV item in 10.9 line (ADO 1770141, 1770143 R1080 PORT, 1717255 R1050* PORT).
- **Anchors:** SF 26-01114165 (Software Defect), 26-01074177, 26-01090557, 26-01112798, 26-01101356; ADO 1770141, 1717255, 1770143, 1774534, 1776672, 1840164, 1840056, 1795593; related ADO 1690118 (24-00979495, TQ meter analysis 10.5.0.13).

### 5.2 FC_BATCHRPT_PK — batch report revision via TQ
- **Signature:** `ORA-00001: unique constraint (FCOWNER.FC_BATCHRPT_PK) violated` when importing a **revision** for `FC_BATCH_REPORT` via the Transaction Queue.
- **Status:** "This bug is fixed in 10.9.0.1" (`CONFIRMED` case resolution, build INFERRED). Anchor: SF 26-01080237 (Software Defect).

### 5.3 FC_METANL_F_LAB_ANALYSIS_ID — parent key not found on CFX import
- **Signature:** `ORA-02291: Integrity Constraint (FCOWNER.FC_METANL_F_LAB_ANALYSIS_ID) violated - parent key not found`; files stop importing. Meter analysis rows reference a lab analysis that was never created.
- **Status:** "comes up for sources in previous versions of the software" — workaround in place, upgrade recommended (`CONFIRMED` SF 26-01098284, Software Defect; also 25-01060909 coded App Config). Treat as version issue (G3); if client can't upgrade, insert/repair the missing parent or clear the orphan reference (G4).

### 5.4 FC_GQANLEXT_PK — GQ extended analysis duplicates
- **Signature:** `ORA-00001: unique constraint (FCOWNER.FC_GQANLEXT_PK) violated` around source-quality apply.
- **Fix recipe (`CONFIRMED` SF 26-01086651, Software Defect):** 1) Purge the month's data for the meter. 2) Re-import the file. 3) Apply the source again.

### 5.5 Other recurring constraint signatures
- `ORA-00001 (FCOWNER.FC_METPER_PK)` inserting into `FC_METER_PERIODIC_VALUES (meter_number_index, time_stamp, sequence_number, ...)` — duplicate periodic row, typically TXT import by IMPORTID re-sending an existing interval (SF 25-01050945, 22-00686502). G4: diff the file against existing rows.
- `ORA-02290: check constraint (FCOWNER.FC_METPER_N_MEASUREMENT_MONTH)` on meter import (SF 26-01102120) — record dated outside its measurement month.
- `ORA-02291 (FCOWNER.FCL_COMO_F_LOCATION_INDEX_ROLL)` on import (SF 25-01040838) — liquids component rollup parent missing.
- `ORA-00936` blocking PPA approval (SF 26-01068838, App Config) — malformed registered SQL/config, not data.

---

## 6. Cluster D — Purge, archive, PPA blockers & partitioning

Purge order matters (`CONFIRMED` SF 25-01057090): **1)** open the meter list for the month → **2)** purge all PPAs → **3)** purge the data → **4)** location rollups auto-reschedule → **5)** FF LCN (final-form location) data recalcs or clears based on remaining meters. Purge = Tools > Purge > Meter Data.

### 6.1 "Purge NOT allowed because there are PPAs" … then "No PPA to purge"
- **Root cause (`CONFIRMED` ADO Bug 1592594 / SF 23-00894675, 24-00938300):** PPA rows whose `effective_end_date` ran to **end-of-time (01/18/2038 21:14:06)** in `fc_ppa_accounting_info` and `fc_meter_edit`. The purge PPA check sees them; the purge PPA action can't.
- **Fix (verbatim pattern from ADO 1592594):**
```sql
alter session set nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
update fc_ppa_accounting_info
set effective_end_date = '<true end>', end_time_stamp = <epoch>
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<mtr>')
  and effective_date = '<start>' and effective_end_date = '01/18/2038 21:14:06';
update fc_meter_edit set effective_end_date = '<true end>', end_time_stamp = <epoch>
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<mtr>')
  and effective_date = '<start>' and effective_end_date = '01/18/2038 21:14:06';
commit;
```
- SF 24-00938300 resolution: "provided SQL to fix the PPAs that went to the end of time."

### 6.2 Purged PPA still showing on PPA Approvals screen
- **Root cause (`CONFIRMED` ADO Bug 1772806 DEV / 1687000 R1060* PORT):** the TESTit test-report Apply process wrote `fc_meter_edit.EDIT_TYPE = 'E'` (user edit) instead of `'P'` (PPA), so Purge PPAs skips the approval record. Repro uses Settings Manager > System > System Configuration > Approvals tab = "Approval Required", purge PPAs for a month, then Review > Approvals still lists the month.
- **Fixed in:** 10.6.0.14 patch, ported to 10.8.0.4 (INFERRED, `CONFIRMED` as case-resolution text SF 26-01063618). Related: ADO 1725795 (Purge PPA does not purge PPAs created by calibration-adjustment apply — approval record left in FC_METER_EDIT), ADO 1684986 (TESTit 3.16 Meter Inspections causing duplicate PPAs in FLOWCAL 10.2.0.22), ADO 1780149 (Unable to Approve the PPA created by TESTit Calibration Adjustment, R1080* PORT), ADO 1691084 (PPA approval double-click → Access Violation 0C24929B in FCENTERPRISEFORMS.DLL).
- **Anchors:** SF 26-01063618 + 24-00977476 (same client, Williams; Software Defect), ADO 1772806, 1687000, 1725795, 1691084.
- **Interim data fix:** correct `EDIT_TYPE` to 'P' on the affected `fc_meter_edit` rows, or purge again after the fix version.

### 6.3 Purge PPA Batch Split error (10.2.x liquids)
- **Signature:** purging a PPA fails where a batch was split. `CONFIRMED` SF 24-00954505: "This is a PPA Batch Split issue... pending DEV... To purge the PPA, we would have needed to run SQL and recalc the batch ... and save it." Sister case SF 24-00952332 (both Software Defect). If client declines the DB workaround, the delta can be handled downstream.

### 6.4 Partitioning & archive/purge programs (mostly G1/G2, not defects)
- The **Archiving, Purging & Partitioning module** is licensed and implemented as a services engagement — cases are overwhelmingly documentation/white-paper/implementation requests (SF 26-01120809, 26-01086489, 25-01045342, 25-01022289 "Technical Health Check - Partitioning\Purge", 24-00983643, 23-00917028, 22-00700497 and ~10 older). Deliverables that exist and can be requested internally: Oracle partitioning white paper, partition-creation scripts, repartition scripts, Oracle STATS script for partitioned tables (SF 25-01044852).
- FcDataboss 3.5.4 had a purge bug (SF 24-00950336, Software Defect) — verify tool version before large databoss purges. Purged production tickets have been recovered via DataBoss extract restore (SF 25-01004080) and mistaken purges restored from backup (SF 25-01008705) — always snapshot before mass purge.

### 6.5 ORA-01502 unusable index/partition
- **Signature:** `ORA-01502: index 'FCOWNER.FC_MTRROLLQ_PK' or partition of such index is in unusable state` (SF 22-00648854; also 22-00631496, 22-00671360) — typically after partition maintenance/moves; rollup queue processing stops.
- **Fix:** `alter index <owner.index> rebuild;` (partitioned: `alter index ... rebuild partition <p>;`), then restart the affected service. Check for other unusable indexes: `select index_name, status from dba_indexes where owner='FCOWNER' and status not in ('VALID','N/A');`

---

## 7. Cluster E — Performance regressions & resource limits

### 7.1 Meter close slow since 10.6.0.7 (gas meters / component close translations)
- **Root cause (`CONFIRMED` SF 26-01085085 resolution):** 10.6.0.7 began creating close translation IDs for **components on gas meters** (visible churn on `fcm_component_periodic_rev` / `FCT_COMPONENT_PERIODIC_REV`), slowing gas closes.
- **Fix:** FLOWCAL **10.6.0.11** added an FcDebugOption to skip component close-translation creation for customers who don't report closed/PPA component liquid volume & mass on gas meters (liquid meters unaffected; 10.6-only — later versions get an application option):
```ini
[METER_CLOSE]
close_gas_components = N
```
- Group-close performance twin: SF 26-01105689 ("functionality introduced in 10.6.0.7 ... addressed in 10.6.0.11; upgrade to 10.6.0.18"). Both INFERRED builds from resolution text.

### 7.2 Duplicate/excessive Edit Reasons slow GPA 2172 meters and imports
- **Root cause (`CONFIRMED` ADO Bug 1721407, R1060*, SF 25-01012338/Clearfork):** CFX import creates a **new GPA 2172 edit reason spanning the whole month for every import**, even when nothing changed → `fc_edit_reason` bloat → point-to-point operations and imports crawl.
- **Diagnostic (verbatim from ADO 1721407):**
```sql
alter session set nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
select * from fc_edit_reason
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<mtr>')
  and gms_date > sysdate - 0.1;   -- look for one-per-import full-month GPA 2172 rows
```
- **Fix:** SQL script to delete duplicate Edit Reason rows (retaining the legitimate ones), then upgrade — fixed in **10.6.0.18 / 10.8.0.9 / 10.9.0.1** (INFERRED, `CONFIRMED` as resolution text SF 26-01118526, Software Defect). Liquids variant: ADO 1839778 (R1090 PORT) — excessive edit reasons block liquid CFX imports outright in 10.8.
- **Anchors:** SF 26-01118526, ADO 1721407, 1839778.

### 7.3 Volume Editor slow opening months with many notes
- Fixed in **10.6.0.12** (INFERRED; SF 26-01086803 resolution quotes the release note: "Performance Improvement: Volume Editor Load Times for Periodic Data With Notes (25-01011858)" — ~30 s freeze → ~4 s).

### 7.4 Meter delete extremely slow (Non-Regulated)
- **Signature (`CONFIRMED` SF 25-01013744, Software Defect):** deleting a new meter ~53 s; meters with history 19–20 min. SQL performance logging pinned the bottleneck on queries against `FC_REPORT_SCHEDULE` and `FC_REPORT_SCHEDULE_PARAM`; emptying the tables + fresh Oracle stats did NOT fix it (structural/row-by-row delete pattern). Resolved in **10.6.0.11** (INFERRED). Bonus: FLOWCAL's SQL performance logging tool itself had a bug compromising diagnostics, also fixed 10.6.0.11.

### 7.5 ORA-02395: exceeded call limit on IO usage
- **Root cause:** Oracle **profile** limits (LOGICAL_READS_PER_CALL/SESSION) too low for FLOWCAL workloads. G2 config.
- **Fix (`CONFIRMED` verbatim SF 26-01095486):**
```sql
SELECT profile FROM dba_users WHERE username = '<USER>';
ALTER PROFILE default LIMIT LOGICAL_READS_PER_CALL UNLIMITED;
ALTER PROFILE default LIMIT LOGICAL_READS_PER_SESSION UNLIMITED;
```

### 7.6 ORA-00020: maximum number of processes exceeded (TESTit 3.17 services)
- **Signature:** DB rejects new connections; TESTit sync/export services flapping. Known TESTit services connection leak "expected to be fixed in 3.17"; if seen ON 3.17, verify 3.17 services actually installed — uninstall/reinstall services (`CONFIRMED` SF 25-00996077 resolution text; fix version INFERRED). DBA can raise `processes` as a stopgap. Cross-ref: services skill §4.3.

### 7.7 General "FLOWCAL is slow" intake questions
Ask: since when (upgrade? refresh? month-close?), one meter or all, one screen or all, Citrix/local. Stats+index health and partitioning health-check (§6.4) for DB-wide slowness; single-meter slowness is almost always data bloat (edit reasons §7.2, notes §7.3, revisions). Cases: 24-00993655, 26-01064461, 26-01086752, 26-01109464 (client-managed infra), 26-01090080 (indexing Q&A).

---

## 8. Cluster F — Connectivity, sessions, refreshes & SQL Server field apps

### 8.1 "Meter locked" — can't edit / import / close
- **First move (`CONFIRMED` SF 26-01065880):** stale service-side lock — **stop ALL FLOWCAL services and restart them**; the lock clears. QCloud: request Cloud restart (SF 25-01016994 workaround).
- **Known defect behind repeat lockups (`CONFIRMED` ADO 1773369/1773370/1726956 "Liquid meters freeze on import", SF 25-01016994 Kinetik):** liquid CFX import enters an **infinite loop** (collection grows until "abnormal program termination"); the importing meters stay locked. Interim: Meter Editor > Imports tab → uncheck **Apply MF / Apply DMF to start of batch** for the affected meter. Fixed in **10.6.0.14 patch and 10.8** (INFERRED from SF resolution). Ops runbook (ADO Problem 1726755): kill/stop services → pull logs → clear locks → restart.
- Historic: meter held locked while `FCSRVTESTITCALADJAPPLY` runs (ADO 1135074). Cross-ref locked USER accounts → Security & Access skill.

### 8.2 Database refresh (UAT←PRD) — procedure + post-refresh gotchas
- Routine refreshes are ops tickets (`Database Refresh Request`; dozens/year — e.g. SF 26-01109551, 26-01102415, 26-01095808, 25-01043852). Investigate only when something breaks after:
  - **Logins/services broken after RMAN clone (`CONFIRMED` SF 26-01081662):** PRD passwords came along; UAT creds no longer match. Fix: `alter user FCSRV identified by <uat pwd> account unlock;` — same for `svcfcinstant`, `fcowner` (values from the environment's credential vault).
  - **TESTit login fails after refresh (`CONFIRMED` SF 25-01043966):** run the **Password Utility** to reset app passwords.
  - **Sequences behind data** → §4.4 (SF 26-01100082).
- Post-refresh checklist: app users unlocked, service accounts re-pointed, sequence sync, CrypKey/licensing revalidated, service configs point at the right DB.

### 8.3 Connection errors (TNS / ORA-03113/03114 / ORA-01034)
- `ORA-12154` (can't resolve connect identifier — tnsnames/alias, SF 26-01094099), `ORA-12170` (connect timeout — network/outage, SF 26-01103315/26-01103305 coded Cloud Outage), `ORA-12514` (listener doesn't know service — listener down/service not registered, SF 26-01081002), `ORA-01034/ORA-27101` (instance down, SF 26-01094071). All environment: route to DBA/Cloud, verify with `tnsping` + `lsnrctl status`.
- `ORA-03113/03114` on desktops: connection severed mid-session. `CONFIRMED` SF 26-01087778: **AVG/Avast antivirus updates blocked FLOWCAL↔Oracle traffic**; allow-listing both program trees fixed it. Check AV/firewall before blaming the DB.

### 8.4 Oracle 19c upgrade-script failures — COMPATIBLE parameter
- **Signature (`CONFIRMED` SF 26-01113819, Targa):** FLOWCAL upgrade DB scripts (`_updateDB_10.6.0.17_to_10.7.0.0.sql`, `_updateDB_10.7.0.0_to_10.8.0.0.sql`) fail with identifier-length / invalid-table-name errors; DBColCheck flags errors. Root cause: Oracle 19c had `COMPATIBLE=11.2.0.1.0`, still enforcing the 30-char identifier limit.
- **Fix:** `ALTER SYSTEM SET COMPATIBLE='19.0.0' SCOPE=SPFILE;` → restart DB → re-run scripts. Always check `select value from v$parameter where name='compatible';` before a 10.7+ upgrade.

### 8.5 SQL Server (TESTit/PROVEit field apps) install & DB-creation failures
- **SQL Server 2022 on Windows 11 won't install (NVMe 4K sector) — `CONFIRMED` SF 26-01100072:** uninstall SQL 2022 completely (delete `MSSQL16.MSSQLSERVER` leftovers), confirm `Get-PhysicalDisk` BusType=NVMe, then `REG ADD "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "ForcedPhysicalSectorSizeInBytes" /t REG_MULTI_SZ /d "* 4095" /f`, reboot, verify `fsutil fsinfo sectorinfo C:` shows PhysicalBytesPerSectorForAtomicity=4096, reinstall.
- **Password Utility DB creation fails on SQL 2019/2022 — `Sqlcmd: Error: Microsoft ODBC Driver 17 for SQL Server: Login failed for user 'SA'` (`CONFIRMED` SF 26-01087584 PROVEit 9.8.2; also 25-01054218 TESTit):** SQL 2014 engine is NOT an option on Win 11 (PowerShell V2 removed). Recipe: copy PasswordUtilityUI files (`fccel.dll`, `PasswordUtility.exe(.config)`, `PasswordUtilityUI.exe(.config)`) into the field app `bin` → run PasswordUtilityUI → on failure check `<install dir>\Resources\Database\sql_output.log` → apply **KB 000004569** → if still failing, run `<install dir>\Resources\Database\__createMSDb.sql` manually in SSMS (update default passwords to meet complexity on old versions) → rerun PasswordUtilityUI → launch app.
- **DB moved to another SQL Server (`CONFIRMED` SF 26-01113956 PROVEit 9.5.1):** post-move failures were folder **permissions** — grant full control on the FlowCal installation folder. Also verify connection config re-point.
- TESTit exports blocked by "DB locked" (SF 26-01064202, no resolution recorded) — check SQL blocking sessions/single-user flags before app debugging.

---

## Known ADO items (Database & performance)

| ADO | Title (verbatim, trimmed) | Cluster | Status seen |
|---|---|---|---|
| 1770141 | TQ Imports have stopped working - Error: ORA-00001: unique constraint (FCOWNER.FC_AMETANL_PK) violated. (DEV) | §5.1 | Closed |
| 1717255 | same (R1050* PORT) | §5.1 | Closed |
| 1770143 | same (R1080 PORT) | §5.1 | Closed |
| 1774534 | same (R1060 PORT) — in 10.6.0.13 regression list (1776672) | §5.1 | Closed |
| 1776672 | FLOWCAL 10.6.0.13 Targeted Regression Testing | §5.1 | Closed |
| 1840164 / 1840056 / 1795593 | Cloud ops: FC_METER_ANALYSIS_ALT cleanup scripts (CFL, CHD) | §5.1 | Closed |
| 1690118 | 24-00979495--TQ meter analysis 10.5.0.13 | §5.1 | Closed |
| 1772806 | Test reports applied with edit_type = E instead of PPA for PPAs (DEV) | §6.2 | Closed |
| 1687000 | same (R1060* PORT) | §6.2 | Closed |
| 1725795 | Purge PPA does not purge PPAs from calibration adjustment apply correctly | §6.2 | Closed |
| 1684986 | TESTit 3.16 Meter Inspections causing duplicate PPA's in FLOWCAL 10.2.0.22 | §6.2 | referenced |
| 1780149 | Unable to Approve the PPA created by TESTit Calibration Adjustment (R1080* PORT) | §6.2 | referenced |
| 1691084 | PPA Failure (Access Violation FCENTERPRISEFORMS.DLL on approval) | §6.2 | Closed |
| 1592594 | 23-00894675--Error Purging Meter and Loading Text File (EOT PPA SQL fix) | §6.1 | Closed |
| 1721407 | Excessive edit reasons on meter causing imports to process slowly (R1060*) | §7.2 | Closed |
| 1839778 | Liquids Meter CFX File Import Service Issue (R1090 PORT) | §7.2 | Acceptance |
| 1773369 / 1773370 / 1726956 | Liquid meters freeze on import (DEV / R1080 / R1060* PORT) | §8.1 | Closed |
| 1726755 | 25-01016994 ECM FC PROD 10.6.0.5 Multiple errors (ops runbook) | §8.1 | Closed |
| 1135074 | Meter Locked on FCSRVTESTITCALADJAPPLY | §8.1 | Closed |

Port-title convention: `(DEV)` = mainline, `(R1050/R1060/R1080/R1090 PORT)` = release-branch ports, `*` = active branch at filing.

## Diagnostic SQL quick pack (Oracle; run as FCOWNER unless noted — DEV-tier binding: label results INFERRED for client PRD)

```sql
-- Tablespace headroom (as SYSTEM)
select tablespace_name, file_id, round(bytes/1024/1024/1024) file_gb, autoextensible
from dba_data_files where tablespace_name like 'FC%' order by 1,2;

-- All FCOWNER sequences vs 2^31 ceiling
select sequence_name, min_value, max_value, last_number
from all_sequences where sequence_owner = 'FCOWNER' order by last_number desc;

-- Location rollup queue state (ORA-08004/LCNROLLQ triage)
select rolled_up, count(*), min(ROW_INDEX), max(ROW_INDEX)
from fc_location_rollup_queue group by rolled_up;

-- FC_METER_ANALYSIS_ALT stray rows (FC_AMETANL_PK triage)
select count(*) from FC_METER_ANALYSIS_ALT;

-- End-of-time PPA rows (purge blocker triage)
select meter_number_index, effective_date, effective_end_date
from fc_ppa_accounting_info
where effective_end_date > to_date('01/01/2037','mm/dd/yyyy');

-- Edit-reason bloat for one meter (GPA2172 slowness)
select count(*) from fc_edit_reason
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<mtr>');

-- Unusable indexes after partition maintenance
select index_name, status from dba_indexes
where owner = 'FCOWNER' and status not in ('VALID','N/A');

-- Oracle 19c compatibility gate before 10.7+ upgrade scripts
select value from v$parameter where name = 'compatible';
```
Env assumptions: Oracle installs; table/sequence names verified verbatim in cited SF/ADO items. SQL Server field-app installs use `sql_output.log` + `__createMSDb.sql` instead.

## Expected-Behavior FAQ

- **"Can we purge data outside the Volume Editor?"** Yes — Tools > Purge > Meter Data (SF 26-01088692, Training). Follow the §6 order; PPAs first.
- **"Purge says PPAs exist — is that a bug?"** Usually not: purge is designed to refuse while PPAs exist. It's only a bug/data issue when *Purge PPAs* then finds nothing (§6.1) or leaves ghosts (§6.2).
- **"Do we need Quorum to partition our database?"** Partitioning is a licensed module + services engagement with official white paper and scripts (§6.4) — route as Expected Behavior/engagement, not defect.
- **"Sequence numbers went negative — is the database corrupt?"** No — swinging into the negative range is the supported remediation for exhausted 32-bit sequences (§4).
- **"Archive/purge license?"** Archive/purge capability is licensed (SF 25-01033530) — check entitlement before advising a purge program.
- **"UAT is slow but PRD is fine."** UAT tiers are usually smaller (client-managed or Cloud sizing); confirm infra tier before treating as product regression (SF 26-01109464, 26-01112402).

## Escalation guidance

- **DBA/Cloud ops (no ADO):** tablespace adds (§3), profile limits (§7.5), TNS/listener (§8.3), refreshes (§8.2), index rebuilds (§6.5).
- **L4 data surgery (peer review + backup snapshot mandatory):** sequence resets (§4), FC_METER_ANALYSIS_ALT deletes (§5.1), EOT PPA fixes (§6.1), edit-reason dedup (§7.2), FC_METER_EDIT rebuild (§4.3 — never run as one script).
- **File/port an ADO bug (area `Quorum\North America\Measurement`; cite SF case in description):** new constraint-violation signatures not in §5, purge ghosts on fix versions ≥10.6.0.14/10.8.0.4, close-perf regressions on ≥10.6.0.11, locked-meter loops on ≥10.6.0.14/10.8. Check the port family (DEV + R#### PORT) before filing a duplicate.
- **Version pitch:** 10.6.0.13/10.6.0.14 and 10.6.0.18 close out most of this skill's defect load on the 10.6 line; 10.8.0.4/10.8.0.9 and 10.9.0.1 on later lines (all INFERRED unless release-notes-confirmed).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
