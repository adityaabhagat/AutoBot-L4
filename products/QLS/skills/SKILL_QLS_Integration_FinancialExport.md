# SKILL — QLS Integration & Financial Export (SAP / AFIS / PUBBA)

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Coverage-plan group:** #6 Integration & Financial Export (1,005 cases all-history, 172 actionable)
> **Sources:** Salesforce all-history mining 2026-09-03 (7 result pages ~150 rows, every page validated against `Product_list__c='My Quorum Land'` + keyword; 26 cases deep-sampled via `Resolution__c`/`Description`) + Azure DevOps orgs QuorumSoftware/Quorum/QuorumServices (27 work items cited; hotfix tags verified on the items).
> **Auto-Bot skill — built by Aditya Bhagat.** Every claim anchored to an SF case number or ADO work item. Fixed-in versions from hotfix tags are labeled INFERRED unless release-notes-confirmed. DEV-tier caveat: client-PRD data-state claims stay INFERRED until verified live.

**Pipelines in scope** (all confirmed in ADO 1762325 / 1728655, the U&L integration-setup features):

| Flow | Batch process(es) | Data path |
|---|---|---|
| QLS → Upstream (My Q Accounting) financial export | `AFISCRTAE` (aka `CREATE_AE`) → step `UPSFINEXP` → Upstream `FINEXPVALD` → `QCFSIMPCYC` | `FINANCIAL_TRANS_HISTORIES` + `AFIS_GL_CROSS_REF` → eSuite `QSTAG_CORE_INTFC_IMP` / `STRAN_CORE_INTFC` → GL025/AP055/AP157 |
| QLS → SAP journal entries | `AFISCRTAE`/`CREATE_AE` then `SAPINTJE` | AFIS tables → `SAP_JE_DOCUMENT_HEADER` (+ `SAP_JE_AP_OPTIONAL`, `SAP_JE_ACCOUNT_GL`) → SAP interface; errors in `SAP_INTEGRATION_LOG` / `SAP_JE_LOG` |
| Upstream eSuite → QLS Business Associates | `PUBBA` (adaptor type 24 "QLS Business Entity") | `SCTRL_BA_ENTITY`/`SCTRL_BA_ADDRESS`/`SCTRL_CONTACT` → `lis.participants` |
| Bank / check-status | `BNKSUBNEXP` + `BNKSUBN` (Bank Submission / Create PPF), `POSPAYEXP` (Positive Pay), `BNKREC` (reconciliation), `CHKSTSUPDT` (QCFS→QLS check status) | writes/reads `FINANCIAL_TRANS_HISTORIES` (`BANK_SUBMISSION`, `DATE_CLEARED`, `CHECK_NUM`, `FT_STATUS`) |
| Master data | `PUBORGCC` (cost centers/org hierarchy: `GEOG_AREAS`, `COST_CENTER_MASTER`), `PUBAGMT` (agreements QLS→QDO), SAP CC INTERFACE / Cost Object / JOA jobs | Upstream eSuite ↔ QLS `lis` |

**Key control tables (Oracle unless noted):** `QLS_QFCONL.QARCH_CTRL_PROCESS_TYPE` (which batch processes appear in the web Batch Processes screen), `QARCH_CTRL_CONNECT_INFO` (named DB connections: `QLS`, `ESB`, `QCADataHelper`, `UPSDataHelper`), `QARCH_QUEU_PROCESS` + `QARCH_PROCESS_MSG_LOG` (process queue/logs), `QARCH_CTRL_IMPEXP` (import/export defs, PPF), `AFIS_GL_CROSS_REF` (payment-type → GL mapping; exposed as code table **48980**), `AFIS_LOG` / `AFIS_ERROR_LOG` (interface logging — which one is used varies by client setup, ADO 1791870), SAP-side config table `/QBSOL/QLS_SYS_IN` (tcode `/QBSOL/QLS_SYS_INT` or SPRO → QLS Integration).

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Cluster | First check |
|---|---|---|
| "AFISCRTAE missing / no longer appears under Batch Processes" | A1 | `SELECT * FROM QLS_QFCONL.QARCH_CTRL_PROCESS_TYPE WHERE PROCESS_ID='AFISCRTAE'` — 0 rows on clean 2025.04+/2026.04 DBs (ADO 1814705) |
| "UPSFINEXP failed — `QUPSFinancialExportValdSeg : Object reference not set to an instance of an object`" | A2 | `QCADataHelper`/`UPSDataHelper` rows present in `QARCH_CTRL_CONNECT_INFO`? (ADO 1778213/1761422) |
| AFISCRTAE runs, staging has data, but nothing arrives in Upstream (no UPS logs) | A2 | Broken QLS→UPS connection after patch/refresh; check UPS-side FINEXPVALD logs (ADO 1777904) |
| Payments stuck **PND** instead of **COM** after AFISCRTAE + SAPINTJE | B1 | Which statuses AFISCRTAE picks up (only COM \| Generated, VD, VDN — ADO 1761422); JE status on Financial Detail |
| "SAPINTJE — Process not found" / STAGE_JE & SAPINTJE silently stopped | B2 | Process metadata + QPEC scheduler running? (SF 24-00991941, 26-01090133, 23-00925552) |
| SAP JE failed with truncation/character-limit errors on specific payments | B3 | `ALLOC_NMBR` >18 chars (`SAP_JE_AP_OPTIONAL`) or `REF_KEY_2` >12 chars (`SAP_JE_ACCOUNT_GL`) (SF 24-00940584) |
| "Cost center does not exist" from AFIS/SAP jobs though CC exists in SAP | G1 | CC missing in QLS-side cost-center rows — sync gap; script to add CC then re-run SAPINTJE (SF 26-01081458) |
| PUBBA full sync fails immediately / BA visible in eSuite but not in QLS | D | `QLS` connection row in `ESUITE_QFC` `QARCH_CTRL_CONNECT_INFO` (post-refresh miss, ADO 1768477); then error text |
| PUBBA error "Tax Type (XXX) for participant N cannot be translated" | D1 | Missing entry in QLS `TAX_TYPES` code table (ADO 1635807) |
| PUBBA processes stuck in QUE status | D2 | Per-BA API storm or services hung — QUE→UX script + full sync (ADO 1777960), or service restart (ADO 1834529) |
| Bank Submission "runs successfully but does not export checks" / "no records in the table to export" | E1 | `FINANCIAL_TRANS_HISTORIES.BANK_SUBMISSION` already populated for target checks? PPF only picks NULL (ADO 1675660) |
| Bank Submission / AFIS process not in process list at all | A1/E | Missing `QARCH_CTRL_PROCESS_TYPE` code-table rows (SF 25-01049301, 26-01116116) |
| Date Cleared on Financial Detail shows year 1926 (or century off) | E2 | QCFS→QLS check-clear push 2-digit-year handling (SF 26-01092883, Software Defect) |
| QLS payments error on QCFS import / QCFSIMPCYC = CE | F | QCFS-side account setup; staging `VALID_IND`; account-number format (SF 26-01093976, 25-00998038) |
| 1099 / AP 1099 checkbox not set on Upstream voucher (AP055/AP157) | A3 | Known defect: NULL 1099 flag on every AFISCRTAE-exported voucher regardless of `BA_1099_IND` (ADO 1814672) |
| SAP cost centers / vendors not syncing; duplicates in eSuite | G | CC INTERFACE connectivity (SAP RISE/S4 moves), `SCTRL_BA_ADDRESS` duplicate check (SF 26-01099787, 25-01055324) |

## 2. Decision Tree

```
Integration/financial-export symptom
├─ Process missing from Batch Processes screen?
│    └─ YES → Cluster A1: QARCH_CTRL_PROCESS_TYPE metadata (G2 config). Insert row + restart services.
├─ Process visible but FAILS?
│    ├─ Error "QUPSFinancialExportValdSeg : Object reference…" → A2: missing/broken QARCH_CTRL_CONNECT_INFO
│    │   dataHelper connections (G2 config; regression re-appears after patches — check ADO 1761422 lineage).
│    ├─ Error names a cost center / GL account / tax type / account # → G/D1/F: master-data or mapping gap
│    │   (AFIS_GL_CROSS_REF, TAX_TYPES, QCFS account setup) → G4 bad data or G2 config, script-fix recipes below.
│    ├─ Truncation on specific payments → B3: SAP staging column limits (expected behavior; fix the data).
│    └─ Silent stop (was nightly, no runs logged) → B2: QPEC scheduler / services down → batch-debugger.
├─ Process SUCCEEDS but data wrong/missing downstream?
│    ├─ Nothing in Upstream/SAP → check staging tables first (QSTAG_CORE_INTFC_EXP has rows? SAP_JE_DOCUMENT_HEADER
│    │   status PND vs ER?) → re-run next stage (QCFSIMPCYC / SAPINTJE) before suspecting code.
│    ├─ Wrong values downstream (1099 NULL, REF_KEY_2 missing, $0 escrow, 1926 dates) → known defects table.
│    └─ Checks not in PPF / same voids repeating → E1: BANK_SUBMISSION column state (G4 bad data).
└─ BA sync (PUBBA)?
     ├─ Fails immediately → connection row (ESUITE_QFC) or adaptor config (SCODE_EDP_ADAPTOR_TYPE 24).
     ├─ Errors on specific BA → translation gaps (TAX_TYPES, country/state ISO codes) or multi-address/routing-number
     │   defects (ADO 1777518, 23-00902968).
     └─ Runs but changes not picked up → full-sync only diffs SCTRL_BA_ENTITY (fixed 2024.04 HF1, ADO 1655373).
```

Gate discipline: most volume here resolves at **G2 (config)** — process-type metadata, connection info, code-table entries. Take **G5 (code)** only for the known-defect signatures with ADO anchors below.

---

## 3. Cluster A — AFISCRTAE / CREATE_AE (QLS → Upstream financial export)

### A1. Process missing from the Batch Processes screen

- **Signature:** AFISCRTAE (or Bank Submission) not listed under Function Navigator → Batch Processes → Interface Processes; worked before upgrade. SF 26-01116116, 25-01049304 ("AFIS Create Accounting Entries is missing", Release Collateral Damage), 25-01049301 (Bank Submission variant), 26-01116490 (visible but role can't run it — batch security, not metadata).
- **Root cause (CONFIRMED):** core builds 2025.04/2026.04 ship **no `QARCH_CTRL_PROCESS_TYPE` row for AFISCRTAE** unless a client QCLNT layer adds it — ADO Bug **1814705** (COP), Bug **1761422** (APH/SEP/SRC).
- **Fix recipe (from ADO 1814705/1761422, verbatim):**
  ```sql
  INSERT INTO QLS_QFCONL.QARCH_CTRL_PROCESS_TYPE
    (PROCESS_TYPE_CD, PROCESS_ID, USER_ID, UPDT_DT, APP_LAYER_CD)
  VALUES ('INTERFACES', 'AFISCRTAE', '<USER_ID>', SYSDATE, 'QLS');
  ```
  Then **restart services in System Manager** for the environment. SF 26-01116116 resolution: "script has been provided to insert the missing record in QARCH_CTRL_PROCESS_TYPE table".
- **If process is visible but greyed/denied for a role:** batch security update, not metadata (SF 26-01116490, resolution "updated security").

### A2. UPSFINEXP step fails — `QUPSFinancialExportValdSeg : Object reference not set to an instance of an object`

- **Signature:** AFISCRTAE completes/fails on step UPSFINEXP with that exact error; QLS staging `AFIS.QSTAG_CORE_INTFC_EXP` has recent data but the Upstream side has no logs after some date (often aligns with the last QLS patch deployment). SF 26-01097139 (UPSFINEXP failing in PRD, PQID logged), 26-01089422 (hung in UAT); ADO Bug **1778213** (MACL, tagged 2024.10 Hotfix), Bug **1761422** (APH/SEP/SRC, tagged 2024.10 + 2025.04 Hotfix Completed), Script Review **1777904** (MAC).
- **Root cause (CONFIRMED):** missing/broken **`QARCH_CTRL_CONNECT_INFO` dataHelper connections** between QLS and Upstream eSuite — "UPSFINEXP will fail without setting up a UPSdatahelper" (ADO 1778213 repro). Fix in the field was copying the `QCADataHelper` & `UPSDataHelper` rows from a working env's `QARCH_CTRL_CONNECT_INFO` into the broken one (ADO 1777904). A Configuration Settings screen for this was added in Upstream (ADO 1778213).
- **Config gotcha (CONFIRMED):** values are whitespace-sensitive — SF 26-01097139 resolution: "Additional issues occurred because setup had typos. **Extra space in front of the config value**."
- **Bank-Submission variant:** checks not exported because the **`ESB`** connection in `QLS_QFCONL.QARCH_CTRL_CONNECT_INFO` pointed at the QLS ESUITE schema instead of the Upstream eSuite DB — SF 25-01056317 resolution (verbatim): "Update the 'ESB' db connection in QLS_QFCONL.QARCH_CTRL_CONNECT_INFO to point to the Upstream Esuite database rather than QLS ESUITE schema."
- **Fixed-in:** error-surfacing improvements (UPS FINEXPVALD + AFIS_LOG/AFIS_ERROR_LOG errors shown in the QLS front end) shipped via Requirement **1763736** (2024.10/2025.04 HF) and User Stories **1791870/1791871** (2026.04 HF) — INFERRED from hotfix tags. Root-cause note on 1763736: `TransferAFISLogsToQPECLog` in `QQLSServiceCore_Accounting.cs` (Quorum.QLS.Web, lines 366–387) discarded the cloned base message, producing empty `ProcessMessageDO` objects.

### A3. Data-quality defects on the export

- **1099 flag NULL on every exported voucher** — BA has `BA_1099_IND='Y'` in QLS but the "AP 1099" checkbox is unchecked on the Upstream voucher (AP055/AP157). ADO Bug **1814672** (SOC; likely affects **all** AFISCRTAE-exported vouchers) — Closed, tagged 2024.04/2024.10/2025.04/2026.04 Hotfix Completed (fixed-in INFERRED). SF 25-01059624.
- **Only these FT statuses are picked up:** "COM | Generated", "VD | Voided", "VDN | Void Non-reported Transaction" (ADO 1761422 repro). Payments in other statuses will never export — that is expected behavior, not a defect.
- **Ran the wrong process ID:** clients configured for AFISCRTAE who run `CREATE_AE` (or vice versa) get failures + stuck records; recovery script sets `FT_STATUS` back to COM so AFISCRTAE can rerun (ADO Script Review **1741420** APH, **1808595** SOC rollback).
- **Precondition (expected behavior):** `FT_GEN_DATE` must fall inside the Accounting Month input parameter; after Upstream `FINEXPVALD` runs, **`QCFSIMPCYC` must run before batches appear in GL025/AP screens**; companies and cost centers must already be synced between QLS and UPS (ADO 1728655).

---

## 4. Cluster B — SAPINTJE / SAP JE export

### B1. Payments stuck PND instead of COM

- **Signature:** user runs AFISCRTAE then SAPINTJE; payments sit in PND, no visible DB errors. SF 23-00920414 (root cause Customer Error), ADO QuorumServices Req **1621531**.
- **Triage order:** (1) Check **JE status on the Financial Detail screen** — if SAP staging rows are in **Error** status, remediate the SAP-interface error then set the JE status back to **Pending** and re-run SAPINTJE; if Pending, SAPINTJE just needs to run (ADO Feature **1641796**/**1791821**, canonical troubleshooting flow). (2) Errors live in `SAP_INTEGRATION_LOG` / `SAP_JE_LOG` — not in QARCH logs until Requirement **1763772** (move SAPINTJE logging to `QARCH_PROCESS_MSG_LOG`) lands.
- **Staging check (from ADO 1776560 repro):** `SELECT * FROM SAP_JE_DOCUMENT_HEADER WHERE FT_KEY IN (...)` — STATUS column PND = staged awaiting interface.

### B2. Scheduled SAPINTJE/STAGE_JE silently stop

- **Signature:** nightly AFISCRTAE + SAPINTJE stop running for days/weeks; no errors, gap in run history. SF 26-01090133, 23-00925552 ("QPEC Schedulers Not Starting"), ADO QuorumServices Req **1627726** (NWE).
- **Root cause:** QPEC scheduler/services not running — an environment/ops issue, not integration config. Route to **batch-debugger** (segregated QPEC process family). Cloud variant: SF 26-01067067 "NO GL Data Exported to QCFS since 12/11" (Deployment Issue).

### B3. Hard-coded SAP staging column limits (expected behavior)

- **Signature:** JE interface errors on specific payments only. SF 24-00940584 (Software Defect classification, but resolution = fix the data): "**hard-coded limitations on ALLOC_NMBR in the SAP_JE_AP_OPTIONAL table, and REF_KEY_2 in the SAP_JE_ACCOUNT_GL table (limited to 18 and 12 characters respectively)**". Business fix: shorten the source values (Entry/Instrument # moved to a Note; rods value rounded).
- **Related:** REF_KEY_2 unit type no longer sent to SAP after config change — SF 24-00981380 (QLA Check Forms, Application Configuration).

### B4. Missing SAP document numbers / config wiped

- SAP document number not generated/populated back in QLS: SF 24-00952201, 24-00943123 (both Software Defect, closed). Check `SAP_JE_DOCUMENT_HEADER` for the FT_KEY before assuming SAP-side loss.
- JE-interface system configuration "wiped out" after deployment: SF 24-00941587 (Deployment Issue) — re-point config; also SF 23-00921023 resolution: "Configuration for JE interface was updated for URL and Credentials" (G2).
- SAPINTJE "Process not found": SF 24-00991941 — same `QARCH_CTRL_PROCESS_TYPE` family as A1.
- Upgrade collateral: **V7 financial org hierarchy still present in V17 caused JE interface errors** — SF 25-01058787 (Software Defect; fix = script to remove old data, G4).
- SAP payment cost-object validation process `SAPPMTCOVL` defect — SF 26-01082309 (Software Defect, Closed-Deferred; fix arrives with version upgrade or out-of-cycle HF).

---

## 5. Cluster C — AFIS_GL_CROSS_REF mapping (code table 48980)

- **What it is:** payment-type → GL account cross-reference driving accounting entries; maintained as code table **48980 AFIS_GL_CROSS_REF** (SF 26-01108256 — users often can't find it; that case was Training).
- **New payment types need new rows** — recurring script-request pattern: SF 26-01100472, 25-01014601 ("Script to Update AFIS_GL_CROSS_REF (2401-1001 to 2401-1021)"), 26-01092812, 26-01092814, 26-01082052 (all Business Change/App Config). Treat as G2 config with a data script; not a defect.
- **UBT/security variants:** "Unable to Add Records to AFIS GL Cross Reference" — SF 26-01110990 (Application Configuration).
- **Screen defect (CONFIRMED fixed):** AFIS GL Cross Reference screen not showing all rows — SF 25-01050561, Software Defect, resolution "2024.10 November 2025 HF" (fixed-in INFERRED from resolution text).
- **AFIS_ERROR_LOG hygiene:** runaway growth from a client-custom "RC IMPORT" job — SF 22-00831031 (Software Defect); periodic cleanup requests SF 26-01084414 (Performance).

---

## 6. Cluster D — PUBBA (Upstream eSuite → QLS Business Associates)

### D0. Where PUBBA lives / how to run

PUBBA is launched from the **Upstream eSuite web process launcher** (not QLS) for integration/adaptor type **24 — "QLS Business Entity"**; exposure steps: ENGS Process Type screen → QFCMAINT → add PUBBA → refresh cache → Batch Process screen (ADO Bug **279484** repro). Adaptor registration lives in `SCODE_EDP_ADAPTOR_TYPE` (`ADAPTOR_TYPE_CD=24`, ASSEMBLY `Quorum.ESuite.Integration.QLS`, OBJECT `Quorum.ESuite.QLS.Integration.QQLSBusinessAssociateIntegration`) (ADO 1777518 repro). The eSuite→QLS DB link is a `QLS` row in the **ESUITE_QFC** `QARCH_CTRL_CONNECT_INFO` (provider ORAOLEDB.ORACLE, schema LIS) (ADO 1635807 repro).

### D1. PUBBA fails on specific BAs — translation/code-table gaps

- **"Tax Type (IIT) for participant NNN cannot be translated"** — missing `IIT` (Backup WH) entry in QLS `TAX_TYPES` code table; fix = add the code-table row (no `QDataTranslations.xml` change needed). ADO Bug **1635807** (GEC), tagged fixed through 2023.04→2025.04 hotfixes (INFERRED); error raised from `QQLSBusinessAssociateDataSubscriber.cs` (~line 877–881, repo Quorum.ESuite.Integration.QLS). Same family as SF 24-00986001 (WMN): SAP upgrade reset **PARTICIPANT TAX TYPE / PARTICIPANT NULL TAX TYPE** in SAP table **`/QBSOL/QLS_SYS_IN`** (tcode `/QBSOL/QLS_SYS_INT` or SPRO → QLS Integration → Config for QLS Integration System) to values incompatible with QLS; restoring the "NA" backup-withholding type fixed the run.
- **Country/State ISO gaps:** "Country and State Abbr exist in QLS for participant address…" SF 24-00965527; ISO code PH-ZZ not in sync blocked a payment — SF 22-00638059.
- **Multi-address BA fails full sync** — SF 23-00902968 (ONSHORE, closed Customer Error). **Multiple new converted BAs sharing a routing number fail the mass sync** — ADO Bug **1777518** (ESUITE, Closed; workaround was one BA at a time).

### D2. PUBBA not running / stuck

- **Stuck in QUE:** SAP mass-loading BAs calls the API per-BA, each spawning a PUBBA run; queue jams. Field fix: script flips QUE records to UX, then rerun **full sync** (ADO Script Review **1777960**, HEC). Cloud variant: PUBBA QUE + web slowness resolved by service restart (ADO **1834529**, EQT PRD).
- **Fails immediately after a refresh:** post-refresh scripts missed the `QLS` connection in ESUITE_QFC — ADO Script Review **1768477** (MAC, SF 25-01056247 referenced); same signature as SF 26-01117564 (owner in eSuite, not in QLS; full sync fails immediately).
- **Process not available in the launcher:** exposure metadata (D0 steps) — SF 24-00941635, 24-00946589, 24-00950777.

### D3. PUBBA runs but changes don't arrive

- **Full Sync only diffed `SCTRL_BA_ENTITY`** — address/tax-ID/usage-only changes were skipped. ADO Bug **1655373**, Closed, tagged **2024.04 Hotfix 1** (fixed-in INFERRED). Pre-req notes on the bug: `PUBBA_LK` disabled in `_ESUITE_QFC`, config `USE_BU_CODE_FOR_ORG_UNIT_KEY` off.
- **Contact info not pulled for new BAs** — PUBBA only sent contact info tied to `SCTRL_BA_CONTACT_ADDRESS`; fixed (ADO Bug **216514**).
- **`'decode' is not a recognized built-in function`** — Oracle `decode()` leaked into a `QDatabaseVendor.All` SQL statement, breaking SQL-Server-hosted eSuite (ADO Bug **279484**, "Collateral Introduced By Hotfix").
- **Internal Company flag not set by PUBBA** — SF 23-00908641 (Application Configuration).

---

## 7. Cluster E — Bank Submission / Positive Pay / check status

### E1. "Runs successfully but exports nothing" / "no records are there in the table to export"

- SF 25-01056317, 24-00949344, 23-00921166, 23-00891136, 22-00574394 (warning-on-success, Software Defect).
- **Mechanics (CONFIRMED, ADO 1675660):** Create-PPF cursor selects `FINANCIAL_TRANS_HISTORIES` rows where `CHECK_NUM IS NOT NULL AND BANK_SUBMISSION IS NULL AND FT_STATUS NOT IN ('SUS','ESC','ER','ETS','HLD','NEW','BR5','PND','SR')`. If `BANK_SUBMISSION` is already populated the check is invisible to the PPF. Regenerate: `UPDATE financial_trans_histories SET bank_submission=NULL WHERE ft_key='<FT_KEY>';`
- **Inverse defect:** checks falsely marked as submitted never reach the bank — SF 22-00674544 (Software Defect) resolution: "script to update bank_submission column in financial trans histories table for 11 checks that were not submitted but falsely marked as such". Voids repeatedly regenerating in the PPF is the same column-state family — SF 22-00814749.
- **Process absent from the list:** "Update code tables to include missing processes" — SF 25-01049301 (same `QARCH_CTRL_PROCESS_TYPE` fix as A1; process IDs `BNKSUBN`/`BNKSUBNEXP`, legacy name `BNKSUBN-QLS` in SF 22-00559103).
- **Wrong ESB target = no export:** see A2 (SF 25-01056317).

### E2. Check-clear / date defects

- **Date Cleared = 1926 instead of 2026** on Financial Details pushed from QCFS — SF 26-01092883 (Software Defect, closed 2026-07): two-digit-year century bug in the QCFS→QLS clear-date push (`CHKSTSUPDT`/Bank Submission family updates `DATE_CLEARED` in `FINANCIAL_TRANS_HISTORIES` from UPS tables, ADO 1762325). Diagnostic: find `DATE_CLEARED < DATE '1990-01-01'`.
- DEO/EGO check clear date issue — SF 24-00984277 (Software Defect).

### E3. Client-custom PPF procedures

PPF file formats are frequently **client-owned stored procedures** (e.g. `ESUITE_QCNX.CREATE_PPF` for CNX/PNC-bank format — ADO 1670885/1675660; custom `ADAMPPFDEO` interface writing the positive-pay file to SFTP — SF 26-01106924, Software Defect: wrong bank account number hard-coded into the proc after an unrelated change). Before triaging as core, check the client override repo (`<CLIENT3>.QLS.Metadata` / `ESUITE_<CLIENT>` schema procs). PPF definitions ride on `QARCH_CTRL_IMPEXP` (ADO 1670885).

---

## 8. Cluster F — QCFS land-payment import (QLS → QCFS)

- **Pipeline:** AFISCRTAE/CREATE_AE → eSuite staging (`STRAN_CORE_INTFC` / `QSTAG_CORE_INTFC_IMP`) → **`QCFSIMPCYC`** → QCFS screens (AR076 shows imports; GL025/AP screens). If records sit in staging, running QCFSIMPCYC is the fix, not a code change (ADO 1641796).
- **Validation failures leave orphans:** payments error in QCFS but QLS still shows them sent. SF 25-00998038 resolution (verbatim): "Script deployment to set the **VALID_IND = 0** in the staging tables for the referenced payment(s). Script deployment to add **000000 to account number** to QCFS so the import is successful." Follow-ups SF 25-00999314 (bug for missing validation), 25-01049595 (update payment status/dates when QCFS validation fails).
- **QCFSIMPCYC shows CE (completed w/ errors):** usually QCFS-side account setup — SF 26-01093976 (resolution: "account setup"), 25-01002939, 25-01011936 (Customer Error).
- **Known defects:** QLS invoice voids did not post in QCFS — SF 24-00939144 (Software Defect); QCFS interop entries showing $0 for escrow entries from QLS — SF 22-00830839 (Software Defect); invoice grouping (1 vs 3 invoices) is config — SF 24-00953683.
- **Nothing exported since a date** → deployment/scheduler issue first (SF 26-01067067, Deployment Issue), then staging-table check.

---

## 9. Cluster G — SAP master-data sync (cost centers, vendors, WBS)

### G1. Cost Center interface (CC INTERFACE / PUBORGCC)

- **Errors after SAP-side moves (RISE/S4):** SF 26-01099787 (Apache SAP RISE; resolution "Connectivity configuration updated in SAP"); re-pointing test SAP to QCloud UAT SF 26-01089942; S4 transports SF 25-01010209, 26-01109973 (`/QBSOL/` namespace remediation). SAP-side config = `/QBSOL/QLS_SYS_IN` (see D1).
- **Silent failure:** SAP CC hierarchy sync silently failing for months — SF 26-01116794 (closed no-response; treat as monitoring gap). New cost centers not appearing in QLS — SF 26-01088655 (Customer Error — SAP side didn't send).
- **"Cost center does not exist" blocking payments:** QLS-side CC rows missing → script to add missing CC info, re-run SAPINTJE — SF 26-01081458 (Application Configuration). QLS↔UPS CC/org-hierarchy sync uses `PUBORGCC` over `GEOG_AREAS`/`COST_CENTER_MASTER` (ADO 1762325).
- **"SAP MT Error - No metadata server was found"** — SF 24-00938910 (Application Configuration; environment metadata-server config).

### G2. Vendor/customer (BA) master data from SAP

- **Duplicate customers/vendors created during S4 testing** — SF 25-01055324; real diagnostic SQL from the case (eSuite schema):
  ```sql
  SELECT * FROM esuite.SCTRL_BA_ADDRESS baa
   WHERE baa.EXTERNAL_NO IN (SELECT EXTERNAL_NO FROM esuite.SCTRL_BA_ADDRESS
                              GROUP BY EXTERNAL_NO HAVING COUNT(1) > 1)
   ORDER BY baa.EXTERNAL_NO, baa.UPDT_DT DESC;
  -- BAs missing contacts (each BA should have an SCTRL_CONTACT):
  SELECT COUNT(1) FROM esuite.SCTRL_BA_ENTITY
   WHERE BA_NO NOT IN (SELECT DISTINCT PRIMARY_BP_NO FROM esuite.SCTRL_CONTACT);
  ```
- **Vendors not arriving from S4** — SF 23-00882788 (Software Defect). **Vendor data populating wrong GL account (60901000) in SAP** — SF 26-01065312 (Release Collateral Damage; patch to client proc `ESUITE_QPHL.AFIS_GET_FUNCTION_PHL`, deployed via SF 26-01082423; SAPINTJE config follow-up SF 26-01107847 resolved by "Patch 9" in UAT).

---

## 10. Known ADO items (cite these; don't re-derive)

| ADO | Type/Project | Title (short) | State / fixed-in |
|---|---|---|---|
| 1814705 | Bug / Quorum | AFISCRTAE batch process not set up by default (2025.04/2026.04) | New — metadata workaround in item |
| 1761422 | Bug / QuorumSoftware | AFISCRTAE failing — broken QLS→Upstream integration (APH/SEP/SRC) | Closed; 2024.10 + 2025.04 HF (INFERRED) |
| 1778213 | Bug / QuorumSoftware | AFISCRTAE.UPSFINEXP failing (MACL, DataHelper connections) | Closed; 2024.10 HF (INFERRED) |
| 1777904 | Script Review | MAC — add QLS connections (QCADataHelper/UPSDataHelper) | Closed |
| 1763736 / 1791870 / 1791871 | Req + US | Publish FINEXPVALD + AFIS_LOG/AFIS_ERROR_LOG errors in AFISCRTAE logs | Closed; 2024.10/2025.04/2026.04 HF (INFERRED) |
| 1814672 | Bug / Quorum | 1099 flag NULL in AP157/AP055 for all AFISCRTAE vouchers (SOC) | Closed; 2024.04→2026.04 HF tags (INFERRED) |
| 1741420 / 1808595 | Script Review | Reset FT_STATUS→COM after wrong-process/failed AFISCRTAE runs | Closed |
| 1627726 / 1621531 | Req / QuorumServices | NWE nightly AFISCRTAE+SAPINTJE failures (QPEC schedulers; PND→COM) | Closed/RfQA |
| 1763772 | Req | Move SAPINTJE logging SAP_JE_LOG/SAP_INTEGRATION_LOG → QARCH_PROCESS_MSG_LOG | Proposed |
| 1641796 / 1791821 | Feature | JE Interface logging enhancements — FINEXPVALD (canonical troubleshooting flow) | PM Acceptance / Closed |
| 1776560 | Bug | COP payment file pulls from v17 notes (SAP_JE_DOCUMENT_HEADER repro SQL) | Closed |
| 1655373 | Bug | PUBBA full sync only diffs SCTRL_BA_ENTITY | Closed; 2024.04 HF1 (INFERRED) |
| 1635807 | Bug | PUBBA — missing IIT in TAX_TYPES ("cannot be translated") | Closed; 2023.04→2025.04 HF (INFERRED) |
| 1777518 | Bug | PUBBA mass sync fails: multiple new BAs, same routing number | Closed |
| 216514 | Bug | PUBBA doesn't pull contact info (SCTRL_BA_CONTACT_ADDRESS) | Closed |
| 279484 | Bug | PUBBA 'decode' not recognized (SQL Server) — hotfix collateral | Closed |
| 1777960 / 1768477 | Script Review | PUBBA QUE→UX cancel script (HEC); post-refresh missing QLS connection (MAC) | Closed |
| 1834529 | Problem / myQuorum Cloud | PUBBA stuck in QUE + web slowness (EQT PRD) — service restart | Closed |
| 1762325 / 1728655 | Feature | U&L integration setup (process/table map for every flow above) | In Dev / Closed |
| 1675660 / 1670885 | Req/Feature | CNX positive-pay format (CREATE_PPF cursor + BANK_SUBMISSION mechanics) | Resolved / Discarded |

---

## 11. Diagnostic SQL (Oracle, `lis` / eSuite schemas — all from cases/work items)

```sql
-- Process queue + logs for the export processes (ADO 1777904)
SELECT * FROM LIS.QARCH_QUEU_PROCESS
 WHERE PROCESS_ID IN ('CREATE_AE','AFISCRTAE') ORDER BY QUEUE_DT DESC;
SELECT * FROM LIS.QARCH_PROCESS_MSG_LOG
 WHERE PROCESS_ID IN ('CREATE_AE','AFISCRTAE') ORDER BY LOG_DATE DESC;

-- Is the process registered for the web Batch Processes screen? (ADO 1814705)
SELECT * FROM QLS_QFCONL.QARCH_CTRL_PROCESS_TYPE WHERE PROCESS_ID = 'AFISCRTAE';

-- Named connections used by UPSFINEXP / Bank Submission (ADO 1778213; SF 25-01056317)
SELECT CONNECTION_ID, DB_SERVER, DB_SCHEMA, DB_PROVIDER
  FROM QARCH_CTRL_CONNECT_INFO
 WHERE CONNECTION_ID IN ('QLS','ESB','QCADataHelper','UPSDataHelper');

-- SAP staging status for specific payments (ADO 1776560)
SELECT * FROM SAP_JE_DOCUMENT_HEADER WHERE FT_KEY IN ('<FT_KEY>');

-- What Create-PPF will pick up (ADO 1675660 — PPF eligibility cursor)
SELECT COUNT(*) FROM FINANCIAL_TRANS_HISTORIES F
 WHERE F.CHECK_NUM IS NOT NULL
   AND F.BANK_SUBMISSION IS NULL
   AND F.FT_STATUS NOT IN ('SUS','ESC','ER','ETS','HLD','NEW','BR5','PND','SR');
-- Re-stage a check for the PPF (ADO 1675660):
-- UPDATE financial_trans_histories SET bank_submission = NULL WHERE ft_key = '<FT_KEY>';

-- Century-bug scan for QCFS-pushed clear dates (SF 26-01092883)
SELECT FT_KEY, CHECK_NUM, DATE_CLEARED FROM FINANCIAL_TRANS_HISTORIES
 WHERE DATE_CLEARED < DATE '1990-01-01';

-- eSuite BA duplicates / missing contacts (SF 25-01055324)
SELECT * FROM esuite.SCTRL_BA_ADDRESS baa
 WHERE baa.EXTERNAL_NO IN (SELECT EXTERNAL_NO FROM esuite.SCTRL_BA_ADDRESS
                            GROUP BY EXTERNAL_NO HAVING COUNT(1) > 1)
 ORDER BY baa.EXTERNAL_NO, baa.UPDT_DT DESC;
SELECT COUNT(1) FROM esuite.SCTRL_BA_ENTITY
 WHERE BA_NO NOT IN (SELECT DISTINCT PRIMARY_BP_NO FROM esuite.SCTRL_CONTACT);

-- PUBBA adaptor registration (ADO 1777518)
SELECT * FROM SCODE_EDP_ADAPTOR_TYPE WHERE ADAPTOR_TYPE_CD = 24;
```
All queries above are **verification SQL**; when the metadata server is not bound to the client env, emit them labeled `NOT YET RUN`.

---

## 12. Expected-Behavior FAQ

- **"AFISCRTAE ran but my payment isn't in Upstream."** Only FT statuses `COM | Generated`, `VD`, `VDN` export (ADO 1761422); `FT_GEN_DATE` must be inside the Accounting Month parameter; and `QCFSIMPCYC` must run on the Upstream side before anything shows in GL025/AP (ADO 1728655). None of that is a defect.
- **"Bank Submission says success but the file is empty."** Checks whose `BANK_SUBMISSION` is already populated are excluded by design — the PPF exports each check once (ADO 1675660). Reset the column only with a reviewed script.
- **"SAPINTJE finished but SAP rejected entries."** SAPINTJE stages and hands off; SAP-side rejects land in `SAP_INTEGRATION_LOG` with the JE status on Financial Detail flipping to Error. Remediate in SAP, set status to Pending, re-run (ADO 1641796). Not a QLS defect.
- **"Payment fields truncate going to SAP."** `ALLOC_NMBR` caps at 18 chars, `REF_KEY_2` at 12 (SF 24-00940584). Shorten the source data.
- **"PUBBA doesn't push QLS edits up to eSuite."** PUBBA is one-way (eSuite → QLS participants). Upstream is the BA master.
- **New payment type errors in accounting** → it needs `AFIS_GL_CROSS_REF` rows first (Cluster C). Business-change script, not a bug.

## 13. Escalation

- **Engineering (G5)** only with a signature matching §10 known defects or a new anchored repro: exact process ID, step ID (`QARCH_CTRL_PROC_PROCSTEP.PROCESS_STEP_ID`), error text, staging-table state. Area paths: `Quorum\North America\Upstream\Land RnD` (current), `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` (maintenance). Repos: `Quorum.QLS.Web` (`QQLSServiceCore_Accounting.cs`), `Quorum.ESuite.Integration.QLS` (`QQLSBusinessAssociateDataSubscriber.cs`), `Quorum.Upstream.Application.QPEC`, client `ESUITE_<CLIENT>` DB procs / `<CLIENT3>.QLS.Metadata`.
- **Cloud Ops** for QPEC scheduler/service outages (silent stops, QUE jams — ADO 1834529 pattern) and SAP endpoint re-points (QCloud UAT/PRD).
- **Client/SAP team** for `/QBSOL/QLS_SYS_IN` config, SAP RISE/S4 connectivity, and bank-format changes (client-owned CREATE_PPF procs).
- Redaction note: client contact names/emails and bank account numbers from source cases are intentionally omitted.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
