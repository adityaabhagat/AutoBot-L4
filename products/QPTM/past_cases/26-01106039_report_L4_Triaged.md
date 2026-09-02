# L4 Triaged — Case 26-01106039

| | |
|---|---|
| **Salesforce Case** | 26-01106039 (`500UH00000qEDViYAO`) |
| **Client / TSP** | EQT Corporation (EQC/Equitrans) / TSP 24 & 241 (no LPS activity on TSP 8925) |
| **Contact** | *(customer contact not on brief — pull from SF before sending; L2/L3: LeWebster Lacy)* |
| **Product / Module** | QPTM / Billing — Invoice Generation (`Case_Category__c`: Invoice Generation; `Azure_DevOps_Module__c` blank on case) |
| **Environment** | EQC DEV / UAT / PRD, found-in **2024.04**, MSSQL. DEV (`EQC_DEV17MID`) fixed 2026-07-06 (WI 1836679); **UAT & PRD still missing the object → production billing still failing** [CONFIRMED, Bug 1836277 re-verified 2026-08-14] |
| **Priority** | Medium (SF) — note: PRD revenue impact + manual workaround since Dec 2025 |
| **Classification** | **Software Defect — confirmed at code level** (not configuration — both PAL gates active and L2-validated; not customer error — full PPA lifecycle completes correctly; not working-as-designed — same path bills correctly at DTE where the object exists, Bug 1638997; not bad data — DEV fixed by object insert alone, zero data correction) |
| **L4 / Date** | Auto-Bot (Aditya Bhagat) / 2026-08-14 |

## 1. Issue Summary
LPS (Park-and-Loan, TOS **LPS-F**) PPAs complete the full lifecycle — retro nom error → reallocation → PPA event → PAN "processed" → Customer Account Main shows the revised balance — but **no billing adjustment is generated**. Example: TSP 24, contract **LPS 1269.2278**, gas day **5/31/2026**, **114 dth** — balance adjusted, invoice **260675** shows **Adj = 0** (screenshot on case). Batch error (verbatim, ADO Bug 1836277): `Invalid object name 'BLSTAG_PAL_EXT'` — SQL 208 / SQLState 42S02 / ADO Error -2147217865 in registered SQL **`QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY`** → "PAL statement records were not successfully inserted." / "CreateNewData function failed." (QADOCommand.cpp:1287). Business impact: **every LPS-F daily parking/loan charge on TSP 24/241 is unbilled in PRD**; customer manually computes charges and enters LGAs (revenue-accuracy/audit risk). Carried over from case 25-01058356; defect open since Dec 2025.

## 2. Reproduction
Steps 1–6 and 8 EXPLICIT (case description, screenshot, Bug 1836277); step 7 ordering DERIVED from code walkthrough:
1. Precondition: EQC instance with `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` active + `PALDailyOrMonthly=DAY` (TSP key `INV_DOC_PAL_STMT`); LPS-F contract 1269.2278 (TSP 24); **`BLSTAG_PAL_EXT` absent from schema** (the defect condition).
2. Enter retro nom change for gas day 5/31/2026 (114 dth) → retro nom error triggers.
3. Reallocation records generate (Reallocation Maintenance).
4. PPA event records trigger (`BLTRAN_PPA_EVENT`).
5. Run PANIGHTLY/PAN → PPA status = "processed".
6. Customer Account Main shows revised balance (114 dth) — lifecycle complete, Adj still 0 (invoice 260675).
7. Run `CalcPALExtension`, then BLINVGEN **"Run All PPAs"** for prod month May 2026. *(DERIVED ordering)*
8. Batch crashes in `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY` — SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` → no PEX billing line written to `BLTRAN_INVOICE_GEN_QTY` → no adjustment.

**Reproducibility: REPRODUCIBLE in EQC UAT/PRD** (object still missing, Bug 1836277 re-verified 2026-08-14; L2/L3 reproduced in DEV 2026-07-01 and captured the batch error on the bug). **DEV no longer repros** since 2026-07-06 — object inserted via WI 1836679, error cleared. Verdict rests on the captured batch error + WI trail — WALKTHROUGH (not executed) this session; no fresh run needed. Condition is structural (missing object), no timing dependency. PQID not recorded on case — triage substitute is the verbatim error on Bug 1836277 (PQID+step+exact-error unit per SKILL_ADO_QPTM_Billing_Invoice_Rates §4 Cluster A).

## 3. Root Cause (code level)
**CORE `QPSGenerateDocuments.cpp` string-injects a literal `LEFT OUTER JOIN BLSTAG_PAL_EXT` into the PAL daily invoice-doc insert whenever config `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` is true (and it defaults to TRUE when the key is missing), while QPTM build 3.1.00.0069 dropped `BLSTAG_PAL_EXT` from the CORE schema — so on any instance without the object the insert fails to bind (SQL 208), the Generate Documents step aborts, and no PEX billing line is written.** [CONFIRMED — live `repo_file` reads 2026-08-14, independently re-verified same day]

Trace (`Quorum.QPTM.ClassicBatch /QPDllPipelineMgrBL/`, default branch, all line numbers verified live 2026-08-14):
- `QPSGenerateDocuments.cpp` **L200–201**: `GetConfigKeyBoolValWithDefault("BILLING", "USE_DTE_BLRPTS_10_INVOICE_DOC_PAL", &bMissing, true)` — ⚠️ **default = TRUE**: the DTE branch runs even where the key is absent, exposing every non-DTE client on 0069+.
- **L214/221**: `m_sPALDailyOrMonthly` read from TSP key `INV_DOC_PAL_STMT` (default "MTH") — the real key behind "PALDailyOrMonthly=DAY".
- **L616**: `if (bSuccessful && m_bBLRPTS_10_INVOICE_DOC_PAL_SQL2)` — the failing branch. **L618–624**: builds `LEFT OUTER JOIN BLSTAG_PAL_EXT D ON …` into `sDateDiffJoin`. **L626–627**: injected as `SEL_DATE_DIFF`/`JOIN_DATE_DIFF` — **the ONLY place `BLSTAG_PAL_EXT` enters the SQL**. **L629–636**: executes `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY`; failure emits the exact cascade text on Bug 1836277 (L635).
- **L639–656** (else branch): same registered SQL with `SEL_DATE_DIFF="NULL"`, `JOIN_DATE_DIFF=""` — no `BLSTAG_PAL_EXT` at all → crash comes solely from the injected fragment.
- `QSQL_GenerateDocuments.cpp` **L2328–2408**: registered SQL text (`INSERT INTO BLRPTS_10_INVOICE_DOC_PAL … @0JOIN_DATE_DIFF …`, DTE Issue 197521 day-counter, merged from DTE 1.11 in QPTM 2.2); registered at L2408–2409; MTH variant L1610.
- Why the object is gone: dropped by QPTM **3.1.00.0069** cleanup (`Quorum.QDBManager …/QPTM/3.1.00/_AllDBChanges/MSSQL/QPTM_3.1.00.0069.0000_00_CORE_QPTMSCR_04_62349.sql` DROP TABLE; `…_CORE_QPTM_15_62349.sql` DROP VIEW + metadata deletes; ST# 50950/50552, issue 62349) — while the CORE reader stayed. **No CREATE DDL survives in any indexed repo** (incl. `EQC.QPTM.Database`) [CONFIRMED]. WI 1451380 lists it as a CORE DTM base TABLE + `PK_BLSTAG_PAL_EXT`.
- Writer/reader split: the **writer** (`QPSCalcPALExtension.cpp`/`QSQL_CalcPALExtension.cpp`) exists only in `DTE.QPTM.ClassicBatch` and `Quorum.QLNG.ClassicBatch` — never in CORE. The **reader** stayed in CORE with a default-TRUE gate. Consequence: **an empty `BLSTAG_PAL_EXT` is a complete fix for EQC** — LEFT OUTER join, only `EXT_DAY_COUNT` read, no writer → `DATE_DIFF` NULL, byte-identical to else-branch output. This is exactly why WI 1836679's object insert alone flipped DEV to non-repro.
- Differential proof: DEV repro → non-repro on 2026-07-06 with **zero code change, zero data correction** (WI 1836679); DTE runs the same path successfully with the object present (Bug 1638997, Closed/Client-Specific).
- Client-override check: org-wide search for `BLSTAG_PAL_EXT` = 12 hits, **zero in EQT/EQC repos** → EQC runs base CORE ClassicBatch. `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY` exists in exactly one file org-wide.

**NOT at fault — ⚠️ do NOT change:** the registered SQL `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY` itself (no `BLSTAG_PAL_EXT` in it; runs clean when the fragment is blanked); the DAY/MTH selection (L641–643) and MTH query (L1610); EQC config values (both gates correct, L2-validated — flipping them is a behavior change, not a repair); upstream CalcPALExtension/PAN/PPA data and `BLTRAN_PPA_EVENT` rows (clean per batch-debugger). Latent side note for the CORE fixer (moot for EQC): TRUE branch hardcodes the DAY query at L629 — `INV_DOC_PAL_STMT=MTH` honored only in the else branch.

## 4. Suggested Code Fix (ranked)
### Primary (Recommended) — ops deploy, no code build
Re-create **`BLSTAG_PAL_EXT`** in EQC **PRD and UAT** exactly per the WI 1836679 DEV precedent: **script the object from EQC DEV `EQC_DEV17MID` (post-2026-07-06) or from a DTE instance — ⚠️ do NOT hand-build the DDL** from column lists. Then rerun BLINVGEN "Run All PPAs" for prod months **May 2026 → current** on TSP 24 and 241, and **reverse the manual LGAs** entered as workaround. Missing-configs list: attachment `EQC DEV DB Configs_1836679.docx` on WI 1836679.
- Regression risk: **minimal** — additive DDL; object only ever LEFT-OUTER-JOIN-read at EQC; no writer to populate it; DEV has run with it since 2026-07-06 without incident.
- ⚠️ Drift risk: the 0069 drop script is **guarded/idempotent** (`IF OBJECTPROPERTY(… 'IsTable') IS NOT NULL`) — any future QDBManager 3.1.00 baseline re-run **silently re-drops** the restored table. The CORE follow-through below is therefore **required, not optional**.

**CORE follow-through (Bug 1836277 — answer to the CORE-vs-client question: CORE defect):** restore the CREATE DDL to the QPTM DB baseline (revert the object-drop half of 3.1.00.0069, ST# 50950) **or**, if DDL restore is refused, guard the reader — minimal diff (re-baseline L200–201 against the client's build branch before committing):
```cpp
// QPSGenerateDocuments.cpp L200-201 — BEFORE
m_bBLRPTS_10_INVOICE_DOC_PAL_SQL2 = pConfigControlMgr->GetConfigKeyBoolValWithDefault("BILLING", "USE_DTE_BLRPTS_10_INVOICE_DOC_PAL", &bMissing, true);
```
```cpp
// QPSGenerateDocuments.cpp L200-201 — AFTER (missing-key default flipped to opt-in)
m_bBLRPTS_10_INVOICE_DOC_PAL_SQL2 = pConfigControlMgr->GetConfigKeyBoolValWithDefault("BILLING", "USE_DTE_BLRPTS_10_INVOICE_DOC_PAL", &bMissing, false);
```
⚠️ The code guard does **NOT** fix EQC (key is explicitly true there) — EQC still needs the DDL deploy; the guard only stops silent exposure of other clients. Fix build must target the 2024.04 line.

### Alternative (Rejected) — set `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL=false` at EQC
Functionally equivalent output today (writer absent → `EXT_DAY_COUNT` NULL either way), zero DDL — **rejected** because: (1) contradicts the L2-validated config baseline and the DEV state already walked through/accepted with the object present (UAT/PRD would diverge from the DEV proof); (2) silently changes which code path bills EQC, invalidating the "After" walkthrough evidence; (3) leaves the CORE reader/schema mismatch latent (default TRUE) for every other client and any future EQC config refresh.

### Alternative (Rejected) — delete the L618–627 join injection from CORE
Breaks DTE/QLNG PAL statements (loses the day-count column, re-opening DTE Issue 197521 / Bug 1638997 territory), requires a ClassicBatch build EQC would wait months for, and is unnecessary — the object is the missing half, not the code.

**Recommendation:** deploy the object to EQC PRD+UAT now (WI 1836679 recipe), rerun/reverse, and drive Bug 1836277 to a CORE DDL-baseline restore so upgrades stop regressing.

## 5. Expected Result After Fix
- BLINVGEN "Run All PPAs" completes without SQL 208; `BLTRAN_INVOICE_GEN_QTY` gains **`CHARGE_BASIS_CD='PEX'`** rows for TSP 24 / contract 1269.2278 / PROD_MTH 2026-05-01; the successor to invoice 260675 shows **Adj = 114 dth × daily rate** instead of 0. Same for all pending LPS-F PPAs on TSP 24/241, May 2026 → current. LeWebster's "After" walkthrough doc is the acceptance artifact.
- Manual LGA workaround retired (existing manual LGAs reversed to avoid double-billing).
- **Never affected:** the PPA lifecycle itself (retro nom, reallocation, PPA events, PAN processing, Customer Account balances) — always worked correctly; the MTH PAL path; all non-PAL invoice generation; DTE and other clients where the object exists.

## 6. Diagnostic SQL
⚠️ NOT YET RUN (DB metadata server not connected this session) — run before and after the PRD/UAT deploy:
```sql
-- Proves the defect condition: NULL = object missing (expect NULL in EQC PRD/UAT pre-fix;
-- non-NULL in DEV since 2026-07-06 and in PRD/UAT post-fix).
SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT');

-- Proves billing impact: 0 rows = no PEX (PAL Extension) billing lines written for the prod month
-- (expect 0 in PRD pre-fix; rows appear after the object deploy + "Run All PPAs" rerun).
SELECT * FROM BLTRAN_INVOICE_GEN_QTY
WHERE CHARGE_BASIS_CD='PEX' AND TSP_NO=24 AND PROD_MTH='2026-05-01';

-- Proves the PPA exists and is unbilled (lifecycle completed; billing half missing).
SELECT * FROM BLTRAN_PPA_EVENT
WHERE TSP_NO=24 /* contract 1269.2278, prod month May 2026 */;

-- Optional PQID pull if a queue record is wanted for the case file:
-- process queue rows for BLINVGEN, TSP 24, prod month 2026-05, status = error, order by run date desc.
```

## 7. Related Items
- **Bug 1836277** (QuorumSoftware) — "EQC - 'BLSTAG_PAL_EXT' is invalid object name in DEV and PRD for EQC" — **Proposed / Triage Pending / PM "Prioritization Pending"**, unchanged since 2026-07-02, re-verified live 2026-08-14. **No fixed-in version exists [CONFIRMED]** → G3 upgrade path unavailable; this bug is the CORE vehicle. ⚠️ **Stalled ~6 weeks** on the CORE-vs-client decision (Jimmy Nguyen → LeWebster Lacy) — answer above: **CORE defect** (CORE code references it; WI 1451380 = CORE base table).
- **WI 1836679** — Closed/Successful 2026-07-06: DEV object insert from another instance. The deploy precedent + missing-configs attachment.
- **WI 1836447** — DEV refresh from `EQC_PRD1715MID` still threw the error → **proves PRD source is missing the object** [CONFIRMED].
- **Bug 1638997** — Closed/Client-Specific: DTE runs the same PAL-extension path successfully with the object present → feature works when object exists.
- **WI 1451380** — DTM schema inventory: `BLSTAG_PAL_EXT` = base TABLE + PK → supports CORE-table answer.
- WI 1819195 (cloud-ops, Closed 2026-07-27), WI 1833658 (access side-issue, Closed).
- Sibling SF cases: **25-01058356** (direct predecessor, transferred into this case), 22-00530416 / 22-00530439 (2017/18 symptom family, detail unrecoverable), 24-00977605 (unrelated).
- Existing-fix cross-check (WIQL 2026-08-14): `Title CONTAINS 'BLSTAG_PAL_EXT'` → exactly 1836277 + 1836679. **No newer code/branch fix anywhere.**
- Latent risks to ride along on Bug 1836277: (1) idempotent drop script re-drop on baseline re-run; (2) **all non-DTE clients on 0069+ with PAL statements configured are exposed via the default-TRUE gate**; (3) TRUE branch ignores `INV_DOC_PAL_STMT=MTH` (L629 hardcodes DAY); (4) `QARCH_CTRL_ARCHIVE_DEFINE`/`UTIL_VIEW_SOURCE_LIST` metadata rows deleted by 0069 are NOT restored by the table-only fix (irrelevant to billing, relevant to archive tooling).
- ⚠️ Prior automated Case Analysis HTML on the case (2026-06-08) is **wrong** (guessed `BLSTAG_INVOICE_PPA_CTR` / missing DPC path; real charge basis is **PEX**) — disregard it.

## 8. ADO Bug — ready to paste
*(Bug **1836277 already exists** — do NOT file a duplicate. Use this block to complete/update 1836277 and move it out of Proposed.)*

| Field | Value |
|---|---|
| Work Item Type | Bug (existing: 1836277) |
| Title | EQC - 'BLSTAG_PAL_EXT' is invalid object name in DEV and PRD for EQC (CORE schema drop 3.1.00.0069 vs CORE reader in QPSGenerateDocuments.cpp) |
| Area Path | QPTM ClassicBatch / Billing — Invoice Generation *(confirm on 1836277; `Azure_DevOps_Module__c` blank on case)* |
| Severity | High recommended — PRD billing loss, manual workaround since Dec 2025 (SF priority Medium) |
| Found in Version | 2024.04 (MSSQL) |
| Customer / Case | EQT Corporation (EQC) / 26-01106039 |
| Root Cause category | Software Defect — CORE DB-baseline/code mismatch (schema object dropped, reader retained) |

**Repro Steps:** On an EQC-config instance (`BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` true, `INV_DOC_PAL_STMT=DAY`) where `BLSTAG_PAL_EXT` is absent: complete an LPS-F PPA lifecycle (retro nom 114 dth, gas day 5/31/2026, contract 1269.2278, TSP 24; reallocation → PPA event → PAN processed), then run BLINVGEN "Run All PPAs" for prod month May 2026.
**Expected / Actual:** Expected — PEX billing line written to `BLTRAN_INVOICE_GEN_QTY`, invoice adjustment = 114 dth × daily rate. Actual — SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` in `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY`, "PAL statement records were not successfully inserted.", no billing line, Adj = 0 (invoice 260675).
**Root Cause:** QPTM 3.1.00.0069 (ST# 50950, issue 62349) dropped CORE table `BLSTAG_PAL_EXT` while CORE `QPSGenerateDocuments.cpp` L616–636 still injects `LEFT OUTER JOIN BLSTAG_PAL_EXT` into the PAL daily insert whenever `USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` is true (missing-key default TRUE). No CREATE DDL survives in any repo. Writer lives only in DTE/QLNG repos; reader is CORE → every non-DTE 0069+ instance with PAL statements is exposed. [CONFIRMED — live source reads + DEV differential proof WI 1836679]
**Proposed Fix:** (a) Immediate: deploy `BLSTAG_PAL_EXT` to EQC PRD+UAT per WI 1836679 recipe (script from `EQC_DEV17MID` or DTE), rerun "Run All PPAs" May 2026→current TSP 24/241, reverse manual LGAs. (b) CORE: restore CREATE DDL to the QPTM DB baseline (revert object-drop half of 3.1.00.0069) or flip the missing-key default to false at `QPSGenerateDocuments.cpp` L200–201 (does not fix EQC by itself). Target 2024.04 line.
**Regression Risk:** Minimal for (a) — additive DDL, LEFT-OUTER-read-only at EQC, DEV stable since 2026-07-06. ⚠️ Guarded drop script will re-drop on baseline re-run until (b) ships.
**Test / Verification:** Prove bug — `SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT')` NULL in PRD/UAT; rerun reproduces SQL 208. Prove fix — OBJECT_ID non-NULL; rerun clean; PEX rows in `BLTRAN_INVOICE_GEN_QTY` (TSP 24, PROD_MTH 2026-05-01); Adj 0 → 114 dth × rate on invoice 260675 successor; "After" walkthrough accepted.
**Release Note (draft, customer-plain):** Corrected an issue where daily park-and-loan (LPS) adjustments completed the account-balance update but did not generate the matching billing adjustment, so the charge did not appear on the invoice. Billing adjustments for these contracts are now generated automatically, and the interim manual entries are no longer needed. Account balances, adjustment processing, and all other billing charge types were never affected — only the billing line for daily park-and-loan extension charges was missing.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
