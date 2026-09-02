# SKILL (ADO): TIPS Master Data / Contracts / CCT / Meter — Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps closed/resolved Bugs (QuorumSoftware org)
**Product:** My Quorum TIPS (midstream measurement / allocation / settlement / statements)
**Area paths mined:** `Engineering\Midstream\*` (product backlog + Guardians/Samurai/TIPS'n Tricks teams) and `Engineering\Maintenance\Midstream and Transportation\*` (Customer/Professional Service)
**Use When:** A TIPS case traces to a master-data / contract setup object — Common Contract Terms (CCT), Contract Meter List (CML / QCM), Meter Definition, Meter Split, Shared Meter, Company / Company Lock / Company Batch — **including its downstream symptoms**: paystation build failures, duplicate `QTRAN_PAYSTATION` / `QTRAN_ALLOC_VOL` rows, imbalance `QTRAN_IMBAL_ACCT_BAL` doubling, INACCTACCM timeouts, settle/allocate registered-SQL failures, gas-lift doubling. In TIPS these master-data defects almost always *surface* downstream — start here whenever the trail leads back to a contract/meter/company object.
**Companion (functional, SF-sourced):** `SKILL_TIPS_Master_Data_Contracts.md` (TIPS Assitant dir) — same clusters from the Salesforce side.

> Evidence base: WIQL matched **~250 bugs** (capped from 499 raw hits; ORDER BY ChangedDate DESC) across the two area branches; **66 bugs deep-read** (description + ReproSteps + relations/PRs + full comment thread). Every root-cause/fix claim below cites a real ADO Bug ID and, where present, the PR number, the dev-comment root cause, and the linked SF case (`25-01xxxxxx` / `24-00xxxxxx` / `26-01xxxxxx`).
>
> **`Microsoft.VSTS.Build.IntegrationBuild` was EMPTY on every bug.** Fixed-in-build below is **inferred** from (a) iteration path YY.NN, (b) the release branch named in the dev's PR comment (e.g. "PR raised for 2025.04 / 2024.10 / develop"), and (c) "merged to 2022.10 and up" type closure notes. Treat all build numbers as **"(inferred — confirm in release notes / patch)."** Maintenance bugs ship as client **hotfixes/patches**, so the *client's* delivered build can lag the core fix branch.

---

## 1. Quick Triage Table

| Symptom | Cluster | Root cause (1-liner) | First check / fix | Key Bug → SF |
|---|---|---|---|---|
| `m_INS_STMT` / `m_INS_METER_TRANS` / `M_INS_GATH_REC_PAYSTATION` inserting **duplicate `QTRAN_PAYSTATION`** rows (same TRNX_ID/MTR_SFX) → CTRMTR/Allocate fails | §3 | Registered-SQL join defect (reversal rows or improper self-/CML join) **or** stale duplicate meter/CML data | Run the dup-key SQL; if data → Cloud Ops delete script; if code → PR per §3 | #1783341→26-01083551, #1698080→24-00989255, #1695221→24-00986307 |
| `sel_paystation` Reg SQL fails (FIXEDFUELS / SETTLEMAIN step) — "NULL" tacked onto SQL | §3 | `@ORDER_BY_MTR_NO`/`@ORDER_BY_TRNX_ID` param not initialized in **client override** of QPSSettleMain/QPSFixedFuels | Port the order-by param into the client's ClassicBatch override | #1610587(MKW), #1641272(ALT), #1654719(NRM) |
| **`QTRAN_IMBAL_ACCT_BAL` duplicate PK** on PLANTIMBAL/INACCTACCM | §4 | `RUN_IMBALANCE_BY_FACILITY` config + accounting-period-mode interaction → dup balance rows | Confirm config in repo; QCODE_POST_TABLES posting fix (PR 124423/124426) + dedupe script | #1772117→25-01060242/25-01061774 |
| "number precision too large" on imbalance activity | §4 | Sequence `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` passed NUMBER(10) | Widen `ACCT_ACTIVITY_DTL_ID` 10→19 (DB + codegen DO) | #1723573→25-01014345 |
| Company Imbalance **INACCTACCM** runs for hours / times out (3600s) | §4 | Imbalance splitting logic adds overhead → bad plan on large reruns | Workaround: raise `SPLIT_COUNT_INACCTACCM` (= #QPECs−2) + restart QPECs; code rework | #1636859→23-00934008, #1593783/#1596532, #1599265→23-00901236 |
| Gas-lift volumes **doubled/tripled** after realloc-mode rerun | §5 | ASSCGLM step re-inserts `QTRAN_ALLOC_VOL` without purging when plant in reallocation mode | DELETE existing PROCESS_ID='ASSCGLM' rows before insert + filter process_ind=1 | #1731166→25-01023169; dups #1734347, #1761294→25-01041541 |
| One owner's allocated volume **= 0** when split has many decimals (0.9421875 / 0.0578125) | §6 | Missing CAST on subquery → progressive rounding pushes pcr just over 1.0, drops a row | Add CAST to NUMERIC; CAN only | #1712833→25-01002874 |
| Meter split **% contribution = 0** for a gathering meter | §6 | PDA still on **old contract company**; meter's company changed (070→057) | Fix company on PDA/SCTRL_MTR_HEADER, re-run | #1720430 |
| CML lets you **delete a meter that still has an effective meter split** (Web) / false "end-date meter split" error | §7 | `VALIDATE_END_DT_NO_ORPHAN_MTR_SPLIT_CHILD_RECORDS` config off **and** stale cache (no refresh trigger) | Enable the config on client layer + add ESuite/TIPS cache-refresh trigger | #1627134, #1623285, #1666247, #1707431→24-00957962 |
| QCM CML "meter not valid for effective date" though timesliced | §7 | Plant-meter cache `FirstDayToCache()` excludes valid older slices | Cache-window validation fix (PR 126302/126357) | #1788087→26-01084783 |
| CML **duplicate row added** / Rejection-Option & Plant default to N/A | §7 | Web auto-sets opposite plant to "N/A" + reject-opt default differs from core | Don't persist "N/A"; default reject-opt to N(None); add dup validation | #1620262→23-00913209 |
| CCT effective **end date saves as 1st of month** | §8 | No validation that End Date = last day of month | New CCT date validation (PR 120456/120459…); on by default | #1763742→25-01052033 |
| Can't update CCT in Web — Event 235 / >4000-char notification | §8 | Event-detector message > `varchar2(4000)`; classic silently truncates | Truncate message in Web (PR 90843) | #1608551→23-00908598 |
| Default CCT blank on CML | §8 | Field not pulled from `QCTRL_CTR_FACILITY_CCT.MTR_CCT_NO`; CAN/client NFLB gap | Display read-only Default CCT (PRs 92596…95399) | #1637466(ALT) |
| User-defined Boolean on Meter Definition saved **true/false not 1/0** | §9 | QFC web wrote string `true`/`false`; Fee Condition logic expects 1/0 | Platform QFC opt-in-per-screen fix | #1551024(DTM), #1638163→23-00902756 |
| Can't delete Meter Definition — "meter split exists" (it doesn't, other plant) | §9 | Delete validation matched on meter# only, **not plant** | Add PLANT_NO to validation join | #128343 |
| Web lets you delete **Shared Meter** with tied CML (Oracle blocks, MSSQL doesn't) | §9 | Trigger `TR_V_SCTRL_MTR_HEADER_D` differs MSSQL vs Oracle | Add validation; only block if it's the meter's only range | #1679180 |
| Company Lock screen errors on open / no data; status not refreshing on Company Batch | §10 | Auto-retrieve + hardcoded LOCK_IND query; no auto-requery | `IS_SHOW_LOCKED` config; copy FBJS refresh logic | #193690, #1438866, #1543774→22-00287124 |

---

## 2. Decision Tree

```
TIPS master-data / contract / meter / company case
│
├─ Batch FAILS with a DUPLICATE-KEY / "unable to insert paystation" error?
│   ├─ dup QTRAN_PAYSTATION (m_INS_STMT, m_INS_METER_TRANS, INS_GATH_REC_PAYSTATION) → §3
│   │     run dup-key SQL FIRST. data dups → Cloud Ops delete script; code dup → PR (reversal/CML join)
│   ├─ "NULL" appended to sel_paystation (FIXEDFUELS/SETTLEMAIN) → §3 client-override order-by param
│   └─ dup QTRAN_IMBAL_ACCT_BAL on PLANTIMBAL/INACCTACCM → §4
│
├─ Batch is SLOW / TIMES OUT (not a hard error)?
│   ├─ INACCTACCM company imbalance hours/timeout → §4 (SPLIT_COUNT_INACCTACCM workaround)
│   └─ CTRMTR/Allocate slow on MSSQL → §3 (force-order query fix, #1745358/#1746523)
│
├─ Volumes WRONG / ZERO (no error)?
│   ├─ one owner zero w/ many-decimal split → §6 CAST rounding (#1712833)
│   ├─ split %=0 for a meter → §6 PDA on wrong company (#1720430)
│   └─ gas-lift doubled after realloc rerun → §5 ASSCGLM (#1731166)
│
├─ A SCREEN behaves wrong (Web ≠ Classic, validation, save error)?
│   ├─ CCT (dates, fees, event 235, default CCT, picklists) → §8
│   ├─ Contract Meter List (delete/dup/eff-date/QCM cache/copy-paste) → §7
│   ├─ Meter Split (suffix, DOI derivation, conv-factor import, freeze) → §6
│   ├─ Meter Definition / Shared Meter (delete validation, udef bool, facility) → §9
│   └─ Company / Company Lock / Company Batch Submittal (status, query) → §10
│
└─ Web-only & "works in classic"? → ALWAYS get PRD build vs fix branch FIRST (§11 escalation).
```

---

## 3. Paystation Build / Registered-SQL Duplicate & Failure Cluster

**Symptom:** CTRMTR / ALLOCATE / SETTLE / FIXEDFUELS batch step fails: *"UNABLE TO INSERT PAYSTATION RECORDS"*, PK violation on `QTRAN_PAYSTATION` (PK = TRNX_ID + MTR_SFX), or a registered SQL dynamic-execute failure.

**Sub-patterns & root causes (from dev comments / PRs):**

| Bug | Client / SF | Root cause (verbatim from thread) | Fix | Fixed-in (inferred) |
|---|---|---|---|---|
| **#1783341** | PEP / 26-01083551 | `m_INS_STMT` (CTRMTR) created 116 dup inserts; GETOPENINV `SQLID_INS_PRODUCERS_WITH_NO_INTEREST` included **Reversal** records; aggravated by PEP's GETOPENINV pointing at `QPDLLTIPSMEASUREMENTCAN.DLL` instead of the PEP-specific allocate DLL. Underlying data: same meter/sfx tied to two contracts in meter list vs meter split. | Core PR **124280** (`Quorum.TIPS.ClassicBatch`) + client PR **124281** (`PEP.TIPS.ClassicBatch`) — filter out reversal records | 2023.04 HF (exemption requested; client was on 2023.04) |
| **#1698080** | MER / 24-00989255 | `m_INS_METER_TRANS` (`QSQL_TransMeters.cpp`) self-join `LEFT JOIN QTRAN_TRNX_ID TA … COALESCE(M.ANALYSIS_MTR_NO,U.UNIT_MTR_NO,M.MTR)=TA.MTR_NO` produced 2 dup TRNX_IDs for one meter | **Rejected as code fix** — resolved by data script (WI #1697957) deleting the dup meter records | data fix only |
| **#142562** | Core | `SQLID_INS_METER_TRANS_NON_GATH` PK error when a meter exists in >1 plant w/ parent meters; join to `QCTRL_METER_PARENT` omitted plant_no | Add `plant_no` to the join | Resolved ~2019 (Sprint, v17) |
| **#84246** | Core | `Sel_Paystation_AllCtr` joined on a NULL (GCR contract-level fee via global UDF) → contract-fee step errored | Code fix (PR 7195/7326) | ~2019 v17 |
| **#1610587** | MKW / — | New param `@0ORDER_BY_TRNX_ID` added to `QSQLID_BPDLL::m_Sel_Paystation` (from #1573301); without optional config `TRNX_ID_ORDER_BY_CLAUSE_IN_SEL_PAYSTATION` it appended literal "NULL" → SQL bombs. Decided to order by **MTR_NO** not TRNX_ID; configs renamed. | PRs **89505/89630/89631** + collateral PRs 89971/90306-90309 (`Quorum.TIPS.ClassicBatch` + Metadata) | Merged 2021.10, 2022.10, 2023.04, develop |
| **#1641272** | ALT / — | Same as #1610587 but ALT's custom ClassicBatch passed `@ORDER_BY_TRNX_ID` while base expects `@ORDER_BY_MTR_NO` → null → bomb | Port param into ALT override (PR **92780**) | client-specific 2021.10 |
| **#1654719** | NRM / — | Same root cause; NRM override of `QPSSettleMain.cpp` didn't initialize `ORDER_BY_MTR_NO` in SETTLEMAIN | Add param to NRM override Initialize (PR **95414**) | client-specific 2023.04 |
| **#1745358 / #1746523** | SCT (Scout) / — | CTRMTR step stuck/timeout: `SQLID_INS_GATH_DEL_PAYSTATION` then `SQLID_INS_GATH_REC_PAYSTATION` query plans bad on MSSQL | Apply MSSQL **force order** hint (PRs 115120/115121 then 115145/115216/115217/115218) | 2021.04, 2024.10, 2025.04, develop |
| **#1757855** | SRI / 25-01045925 | Build Contractual Paystation: Settle-Only (Acct Mtr Type='IV', "Invoice Only") meters purged by `QCODE_REC_PURGE` custom-where in SETTLE but **not re-created** | Rebuild contractual paystation for IV meters in SETTLE (PRs 120517/120813/120840) | 2024.10, 2025.10, develop |
| **#1776751** | SRI / 26-01066265 | Cross-facility CCT (one CCT linked to 2 facilities, POP+FEE tabs) fails SETTLEMAIN | **Rejected** — client workaround: name CCT/contracts slightly differently per facility | n/a (won't-fix) |

**Triage rule:** a paystation "duplicate" is **data** (stale CML/meter-split dup, or contract time-slice overlap) until the dup-key SQL proves the registered SQL itself is multiplying rows. The recurring data fix is a Cloud Ops `DELETE FROM QTRAN_PAYSTATION WHERE TRNX_ID=… AND MTR_SFX=…` (then re-run). A *recurring* dup with a new TRNX_ID each run (#1783341) = genuine code defect, escalate.

**Diagnostic SQL:**
```sql
SELECT TRNX_ID, MTR_SFX, COUNT(*) FROM QTRAN_PAYSTATION
WHERE ACCT_DT='<MTH>' GROUP BY TRNX_ID, MTR_SFX HAVING COUNT(*)>1;
-- batch step logs:
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID='<id>' AND SQL_SUCCESS_IND=0;
SELECT * FROM QARCH_PROCESS_MSG_LOG   WHERE PROCESS_QUEUE_ID='<id>';
```
**Code refs:** `Quorum.TIPS.ClassicBatch` (`QSQL_TransMeters.cpp`, `QPSSettleMainBase.cpp`/`QPSFixedFuelsBase.cpp`), client repos `PEP/ALT/NRM/MKW/SCT.TIPS.ClassicBatch`.

---

## 4. Imbalance Cluster — `QTRAN_IMBAL_ACCT_BAL` Dups, Sequence Overflow, INACCTACCM Timeout

**4-A Duplicate customer-account-balance rows — #1772117 (HEC / 25-01060242, 25-01061774)**
- **Symptom:** PLANTIMBAL/IMBALANCE fails: `Violation of PRIMARY KEY 'PK_QTRAN_IMBAL_ACCT_BAL'. duplicate key (OBA,10,RES,SALE,Nov 1 2025,Aug 1 2025)`. Recurring monthly at Hilcorp; doubled balances in Customer Account Maintenance.
- **Root cause (dev thread):** tied to the **ACCOUNTING PERIOD MODE** change made for Hilcorp's auto roll-forward, and the config **`RUN_IMBALANCE_BY_FACILITY`** being set to 1 but **not checked into the Quorum-managed client repo** (so a patch reverts it, flipping behavior). The posting view pulls from both QTRAN and QPOST imbal tables.
- **Fix:** PR **124423** (`QCODE_POST_TABLES` [2025.04]) + PR **124426** ([2025.10]) — posting uses ACCT_DATE; plus Oracle migration script. Short-term: Cloud Ops dedupe script (Review #1772100 / Deploy #1772095). **Long-term:** ensure `RUN_IMBALANCE_BY_FACILITY` is checked into the client repo so patches don't wipe it.
- **Fixed-in (inferred):** 2025.04 + 2025.10 streams; Hilcorp delivered via HF.

**4-B Sequence too large — #1723573 (ETP / 25-01014345)**
- **Symptom:** INACCTACCM fails `PL/SQL: numeric or value error: number precision too large`; sequence `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` reached 10,000,000,032 (11 digits) vs `ACCT_ACTIVITY_DTL_ID NUMBER(10)`.
- **Fix:** widen precision **10 → 19** (DB PRs 110407/110411/110413) + regen `ImbalAcctActivityDtlDO` codegen (PRs 110562/110568/110569). Customer interim workaround was NUMBER(11); product standard is **NUMBER(19)** — cover QTRAN + QPOST + the CAW-schema copy.
- **Fixed-in (inferred):** 2020.03, 2024.04 (2024.10), develop. Tag "queued for next TIPS 2020.03".

**4-C INACCTACCM performance / timeout — #1636859 (MOM/23-00934008), #1593783 & #1596532 (ET/EMP), #1599265 (ONM/23-00901236)**
- **Symptom:** Company Imbalance step **INACCTACCM** runs for hours (17–22 h observed) then times out at 3600s (`Query timeout expired`), or memory errors. Triggered by processing many production-month **reruns** at once.
- **Root cause (Jon Shuck, dev):** the imbalance **splitting logic** adds heavy overhead to the query even when no splitting is configured; on large data the DB picks a small-data plan → mismatch → runaway. (`SQLID_REVERSAL_VOL`, `SQLID_SSEL_QTRAN_FIXED_FUEL` were the long-runners.)
- **Fix / workaround:** raise config **`SPLIT_COUNT_INACCTACCM`** to (#QPECs − 2) to parallelize + **restart QPECs** (immediate relief); code rework to bypass split overhead when no split configured (PRs 92067/92068/93041). NOTE #1593783's original core change was **backed out** (broke ONM collateral) and reworked under #1596532 — be careful citing the first attempt.
- **Fixed-in (inferred):** #1636859 merged 2022.10 + 2023.04 and up. **Overlap caveat:** INACCTACCM/Company-Imbalance straddles QPTM↔TIPS (Customer Account Accumulation); #1729655 (Summit/25-01012810) removed the `INUPSTRMFL` upstream-fuel step from CUSTOMER ACCOUNT ACCUMULATION for a QPTM SAP export (`BLCCSFACT`) — QPTM-leaning, listed only for completeness.

**Code refs:** imbalance balance logic in `Quorum.TIPS.ClassicBatch` (Common-QI / QPSCustAcctBal) and `Quorum.TIPS.Web` DO/DAL `ImbalAcctBalDO/DAL`, `ImbalAcctActivityDtlDO`.

---

## 5. Gas-Lift Duplication — ASSCGLM (#1731166)

- **Symptom:** Gas-lift volumes doubled/tripled after a plant re-run in **reallocation mode**; domino effect through allocation groups (DWHNLTB→RESAFS). "Automated Gas Lift Records Not Purged."
- **Root cause (repro in bug):** the **ASSOCIATED GAS LIFT METER VOL (ASSCGLM)** process step inserts `QTRAN_ALLOC_VOL` rows for gas-lift meters but does **not purge** prior ASSCGLM rows when the plant runs dailies in reallocation mode (realloc-mode rerun only reprocesses changed meters via `process_ind=1`, re-stacking rows).
- **Fix:** engineering added a **DELETE of existing `QTRAN_ALLOC_VOL` rows with `PROCESS_ID='ASSCGLM'` before re-insert** + only consider meters where `process_ind=1`. PRs **114597, 114879, 114880, 114881** (`Quorum.TIPS.ClassicBatch`).
- **Fixed-in (inferred):** **2025.04**; ships in **2025.04.1.3** hotfix (John Weems: "AHS not on 2025.04.1.3 HF yet, which has this fix").
- **Bug IDs / SF:** **#1731166** (core, Closed) ← **#1734347** (ETP, 25-01016940/25-01023169, closed not-repro internally) and **#1761294** (AHS, 25-01041541, **Rejected → dup of #1731166**; get AHS to ≥2025.04.1.3).
- **Workaround until on the build:** take the plant **out of reallocation mode** before re-running, or Cloud Ops purge the dup ASSCGLM rows.
- **Diagnostic:** `SELECT * FROM QTRAN_ALLOC_VOL WHERE PROCESS_ID='ASSCGLM' AND PROD_DT='<dt>'` (note the bug repro typo'd `ASCGLM`); `SELECT * FROM QTRAN_PLANT_STATUS_REALLOC WHERE PROD_DT='<dt>'`.

---

## 6. Meter Split Defects

| Bug → SF | Symptom | Root cause | Fix | Fixed-in (inferred) |
|---|---|---|---|---|
| **#1712833** → 25-01002874 (PEM, CAN) | One owner allocated 0 when split = 0.9421875 / 0.0578125 | Subquery lacked CAST → progressive rounding turned 0.0578125 into 0.057813… pushing pcr_contr > 1.0, dropping a row | Add CAST on the subquery to match S_DECIMAL precision (PRs 109849/110017/111073) | 2024.10 stream, CAN only (ORA+MSSQL) |
| **#1720430** (AHS) | Gathering meter split %-contribution = 0 in `QTRAN_ALLOC_VOL` | Meter's **contract company changed (070→057)** but the PDA for the prod month still on old company | Fix company on PDA / `SCTRL_MTR_HEADER`, re-run (data) | data fix |
| **#1721618** (DCP, 2024.10) | Split Decimal blank for **DOI Derivation** split source in Web | Web returned NULL for DOI-derived splits; should be **read-only blank** (split lives in QDOD). Plus Override Exempt Dec formatting mismatch vs classic | Metadata formatting fix across CAN/FCST/QG/TIPS layers (PRs 110957…111474) | 2024.10, develop, release |
| **#1721986** (DCP, 2024.10) | Meter Split "Build Split" popup stuck after OK (DOI derivation) | JS did `NULL.checked` (firstCheckBox/secondCheckBox null) → OK inert | Null-check the checkbox vars (PRs 110965/111008/111087) | 2024.10, develop |
| **#1617223** → 23-00915506 (ONM) | Web meter-split won't save with blank Meter Sfx (required) | Classic auto-fills 2 spaces `"  "` for null MTR_SFX (non-nullable col); Web didn't | Coalesce MTR_SFX null→`"  "` in Web (PRs 91470/91543/91593) | 2022.10 and up |
| **#1662516** → 24-00954040 (ONM) | Collateral to #1617223: blank-suffix save fails + `MTR_SP_NEW` notification NRE | `MtrSplitNewEventHandler`/`MtrSplitEndDatedEventHandler` padded a null MtrSfx → NullReferenceException | In-line coalesce MtrSfx in event handlers (PRs 96976/97055-97057) | 2022.10 and up |
| **#1554087** → 22-00251974 (NRM, CAN) | Meter-split conversion factors (USR_DEF_7-10) wiped after `NLDSSNONOP` import | Non-Op split import (CAN-only) dropped conv-factor cols on new time slice | Client-specific fix (PR 76390) | client-specific (NRM 2021.10/develop) |
| **#1674125** → 24-00965214 (NRM, CAN) | Delivery Point Terms popup freezes when attaching to meter split | Client-specific picklist query (metadata) | Metadata query fix (PR 99618) | client-specific HF |
| **#149205** (Core) | Meter-split screen wrongly errors on split decimal between 0–1.0 | Web validation defect | fixed | Maintenance |

> Functional FYI (from companion SF skill, confirmed pattern): a **Split Decimal of 0** at Meter Split flows zeros into Paystation and zeroes settlement — always check the split before suspecting the settle engine.

---

## 7. Contract Meter List (CML) / QCM Defects

**7-A Orphan-meter-split delete validation + cache — the dominant CML cluster.**
- **Symptom:** Web lets you delete a meter from CML even though it has an **effective (open-ended) meter split** (Classic blocks it); OR the inverse — false *"meter split exists / not end-dated"* error after you DID end-date it (works only after a service restart → caching).
- **Root cause:** two things together — (1) config **`VALIDATE_END_DT_NO_ORPHAN_MTR_SPLIT_CHILD_RECORDS`** not enabled on the client layer (and the screen moved Classic→ESuite web so the metadata override didn't carry over), and (2) the validation reads a **cached** view (`VTIP_QCTRL_MTR_SPLIT_DTL_VW`, cache-days config) so a just-end-dated split still appears effective.
- **Fix:** enable the config on the Q-owned client layer (METER_LIST key group) **and** add a DB **cache-refresh trigger** so end-dating a meter split flips `QARCH_TRAN_CACHE_STATUS` for both TIPS and ESuite MTs; later replaced with a cache-day check that goes directly to the DB view.
- **Bug IDs:** **#1623285** (BUG 149, MKW — TIPS-side trigger), **#1627134** (BUG 150 / 23-00925437, MKW — ESuite trigger, F/V), **#1666247** (24-00957962, MKW), **#1707431** (HPE HF F/V of 24-00957962 — just needed the config key=1, PR 105090). Fixed-in (inferred): **2022.10 and up** (2022.10/2023.04/2024.04/develop).

**7-B Other CML defects:**

| Bug → SF | Symptom | Root cause | Fix | Fixed-in (inferred) |
|---|---|---|---|---|
| **#1620262** → 23-00913209 (ONM) | CML allows **duplicate row** (Web + Classic); Reject Option defaults to None, Delivery Plant auto "N/A" | Web persisted "N/A" into opposite plant; reject-opt default differed from core (client had NA override) | Don't save "N/A"; default reject-opt to N(None); add dup validation; data script to clear "N/A" plants (PRs 91226…99831) | 2022.10 and up |
| **#1695221** → 24-00986307 (MOM) | Rejection Option on CML creates **dup QTRAN_PAYSTATION**, TPSCHDPRD fails on PK | `M_INS_GATH_REC_PAYSTATION` joins `QCTRL_MTR_LIST_DTL` **twice**; first join lacks `REJ_OPT_CD` → duplication when a meter has multiple reject-option rows | Fix the join + client remove dup meter-list rows (PRs 102562/102568/102645/102646) | 2022.10+ (16 builds) |
| **#1788087** → 26-01084783 (UPC) | QCM CML "Meter Exxx is not valid for effective date 8/1/2023" though correctly timesliced | Plant-meter cache `ValidPlantMeterCache.FirstDayToCache()` (default 365 days) excluded older-but-valid slices | Cache-window validation fix; honor `EffDateTo >= FirstDayToCache()` (PRs 126302/126357/126642/127743/127744) | 2025.04, develop; queued ESuite 2026.04 |
| **#1748551** → 25-01033727 (MKW) | Some contracts return **no rows** in QCM CML ("Object reference not set") | **TIPS↔QCM sync gap**: `SEXTN_MTR_HEADER_QRMTIPS` rows missing in `SEXTN_MTR_HEADER_QCM` → null deref | Code change (PR 119445) + sync the meter-header tables (data) | cherry-pick back to 2022.10 (client out-of-support → exception/script) |
| **#1756941** (ETP) | CML doesn't query when **all meters closed/end-dated** | Query logic excluded fully-closed meters | Fix (PRs 118883…119730) | 2025.x; merged widely |
| **#1758565** (DCP) | Same "CML doesn't query when meters closed" | — | **Closed as Duplicate of #1756941** | — |
| **#1740256** (DCP, 2024.10) | CML new effective date errors **Web only** (contract SPR111400*) | Eff-date splitting in Web (also repro core) | Fix (PRs 116914/116972-116974) | 2025.04, develop, release |
| **#1743518** (UPC, 2025.04) | CML "Plant No is not the same for Meter and Contract" blocks updates | UPC dropped QGM in upgrade; `ValidateMLHSameCtrMeter` + missing Global Field Defaults for QCU METERLIST screen | Disable that validation on client layer + add Field Defaults; check into metadata | config fix (UPC HF) |
| **#1769433** (ETP, QCM 2024.04) | CML **copy/paste** doesn't auto-populate Receipt Plant # | ETP classic override; works in core/My-Q | **Rejected** (won't fix in classic; use My Q) | n/a |
| **#1623285/#1627134/#128578** | Can't delete genuine **duplicate** meters on CML | dup rows already in `QCTRL_MTR_LIST_DTL`/SCTRL | Cloud Ops delete script (match Rec/Del MtrNo, MtrSfx, RejOpt, EffDateFrom, Rec/Del PlantNo, COALESCE nulls) — see #128578 .sql attachment | data |
| **#1610868** (DTM) | Can't end-date contracts in CML (false validation) | Same fix as #1458388; meter not effective for part of range = legit, but DTM hit a real bug | HF into DTM 2021.10 (PR 88111) | 2021.10 (already in later) |

---

## 8. Common Contract Terms (CCT) Defects

| Bug → SF | Symptom | Root cause | Fix | Fixed-in (inferred) |
|---|---|---|---|---|
| **#1763742** → 25-01052033 (DCP, 2024.10) | CCT screen lets End Date save as **1st of month** | No validation that effective End Date = last day of month | New CCT date validation (PRs 120456/120459/120773-120776); **on by default**; same gap noted on Meter Definition (logged separately) | 2025.04 + 2025.10 |
| **#1608551** → 23-00908598 (MKW) | Can't update CCT in **Web** (Event Detector #235) | Notification message > `varchar2(4000)`; classic silently truncates, Web (QFC) errors. (MKW also had stray `CCF` `QCODE_SYS_FUNC_AREA_OBJECT` rows → separate #1631148) | Truncate message in Web (PR 90843) | 2022.10 and up |
| **#1637466** (ALT) | **Default CCT** blank on CML (Web + Classic, also Core CAN) | Field not pulled from `QCTRL_CTR_FACILITY_CCT.MTR_CCT_NO`; CAN config + ALT NFLB gap (#1451460) | Display Default CCT read-only; align CAN to Core (PRs 92596-95399) | 2022.10 and up |
| **#1561361** (DCP, 2022.10) | CCT Keep-Whole: any payment-calc checkbox → "Error communicating with server" | **Data**: `QCTRL_CCT_KW.UomAdjSeq` = '12' instead of '123' → ArgumentOutOfRange in CCTRootVM; plus a platform bug surfacing AJAX error instead of field error (#1564920) | Fix the data (UomAdjSeq) + platform error-message fix (PR 78266) | 2022.10 HF |
| **#190067** (PEM, CAN) | Equalization reports empty after `m_Upd_Payowner_Cct` | `QSQL_BuildAEqualPayOwner.cpp`: `YEAR(QTRAN_PAYOWNER.PROD_DT)=YEAR(S.PROD_YEAR)` wrong — should be `=S.PROD_YEAR` | Fix the SQL (PR 27505) + CAN/MSSQL collateral | 2020.03 (PEM HF) |
| **#264857** (Core) | Contract-Basis **Margin** CCT writes same Rate Res ID to all records + dups | Contract-level margin recalcs each paystation term then overwrites the rateres of the already-calculated term | PRs 46534/46833 | 2021.04 |
| **#280352** (Core) | Meter-Basis Margin CCT not updating Rate Res ID in `QTRAN Settle Summary` (Producer % via Rate Schedule) | Margin rateres null for schedule-based producer share | PRs 51957/51999 | 2021.04 |
| **#264928** (Core) | "Value" CCT calculating a **Fee** doesn't populate Quantity UOM | `QContractTermValueBSA::OutputToDatabaseFEE()` not setting quantity UOM | PRs 45565/46834 | 2021.04 |
| **#1577942** (Core) | Keep-Whole statement had to reuse Invoice format | Add new **KW** statement format/type (KW_STMT) | PRs 82757/82764/82798 | 2023.04 |
| **#1568507/#1566977** (Core) | CCT Fixed-Fuels Calc Sequence accepts negative / defaults to 0 | Web validation | PR 78363 / 81d152 | 2022.10/2022.22 |
| **#1431618** (PEM, CAN) | "ALL" missing from CCT Facility dropdown (global CCT) | `HIDDEN_IND` on code table 24013/24846; removing it reverts the physical-constants bug (#230720) | New PEM-specific code table 24846 (PRs 65528…67211) | 2021.10, release, develop |
| **#1665538** (ALT, classic) | Dup entries in CCT Product/Disposition dropdown (POP tab) | classic-only dropdown dup | **Rejected** (medium, focus on My Q) | n/a |

> **CCT overlap caveat:** `CCT` is a substring that also matches **MCT/RFS timezone** items (e.g. #1635464 "Timezone label shows CCT but should be MCT" is a **QPTM RFS** screen, dropped) and Land "Legal API" tasks (#1561331, dropped). Verified each CCT hit is a TIPS Common-Contract-Terms object before including.

---

## 9. Meter Definition / Shared Meter Defects

| Bug → SF | Symptom | Root cause | Fix | Fixed-in (inferred) |
|---|---|---|---|---|
| **#128343** (ONM) | Can't delete Meter Definition — "meter split setup" error (split is on a *different plant*) | Delete validation `QTIPSValidationMeterHeader0023_CheckCapacityAndSplit` matched **meter# only, not plant**; also a stray 2018 date in the SQL | Add `PLANT_NO` to the validation join (PRs 39587/44822) | 2020.03 (ONM HF lineage) |
| **#1679180** (Core) | Web deletes **Shared Meter** with tied CML (Oracle blocks, MSSQL doesn't) | Trigger `ESUITE.TR_V_SCTRL_MTR_HEADER_D` differs MSSQL vs Oracle; no FK SVALD_MTR_LIST↔SVALD_MTR_HEADER | Add validation; only block if deleting the meter's **only** range (PRs 102229/102762/103263/104068) | 24.22 → 2024.x |
| **#1638163** → 23-00902756 / **#1551024** (DTM) | User-Defined **Boolean** on Meter Definition saved as `true`/`false` not `1`/`0` → Fee Condition logic breaks | QFC web wrote string true/false; classic writes 1/0 | Platform QFC fix changed to **opt-in per screen** (re-QA'd Contract Header, Functional Unit, Plant Header, Statement Group, Meter Def; also QPTM Location Maint #1452102). #1551024 shipped as DTM client workaround (PRs 79281/79353) | #1638163 PR 92203 → 2021.10 + 18.x + release; #1551024 client-specific |
| **#153358** (MKW) | Meter Definition facility not flowing to **Shared Meter** (blank facility tab) → settlement thinks meter not tied to facility | Broke in v16 project (Bug 196 patch 6); time-slice split didn't copy facility | Copy facility to new time slice, don't copy on meter-copy (PRs 18974…25402) | ~2020 (MKW HF) |
| **#1731356** → 25-01020950 (HEP) | Company Address State/Province dropdown "NO DATA FOUND" in Web (works classic, also core) | Web picklist data binding | **Rejected** (no resolution recorded) | — |
| **#1650646** → 24-00946543 (GNP) | QPTM BA Contact "Company Additional BAs" save fails (Web, Oracle) | Trigger `TR_H_SCTRL_CON_ADDL_BA_BI` references seq `SCTRL_CONTACT_ADDL_BA_TSP_HSQ` but codegen uses `SCTRL_BA_CONTACT_ADDL_BA_HSQ` | Modify trigger to match codegen seq (PRs 94968/96439) | 2023.04, 2024.04, develop |

> #1650646 is tagged **QPTM Reviewed** (BA Contact is shared QPTM/TIPS company master data) — included because it's a company/BA master-data trigger defect and matched the "company" term; note the QPTM lean.

---

## 10. Company / Company Lock / Company Batch Submittal Defects

| Bug → SF | Symptom | Root cause | Fix | Fixed-in (inferred) |
|---|---|---|---|---|
| **#193690** (ONM) | Company/Facility Lock Web: Acct Dt cropped, confusing true/false, big X; **Company Lock returns no data** (classic does) | Web hardcoded `LOCK_IND=1` query (classic did it via metadata); grid date col too narrow | New config **`IS_SHOW_LOCKED`** (0=show all w/ company filter, 1=locked only) + grid width fix (PRs 64079/64080/64744/64961) | 22.02 → 2022.x |
| **#1438866** (Core, 2022.04) | Company Lock screen throws error **on open** | Collateral from #193690 — auto-retrieve fired before company filter w/ IS_SHOW_LOCKED=0 | Remove auto-retrieve (PRs 66663/66714) | 2022.05/release |
| **#1543774** → 22-00287124 (MER) | Company Batch Job Submittal shows **no status** after a job completes | Screen didn't auto-requery (FBJS does) | Copy FBJS refresh logic (PRs 74470…74647) | 2021.10, 2022.10, develop |
| **#279946** (Core, 2021.04) | Company Batch **POST results** fails "Error in registered SQL & too many values" | Collateral from #232073/#219694 — new column added to STRAN but not the **SPOST** copy | Add column to SPOST table (PR 45829) | 2021.04 |
| **#1636859** etc. | Company Imbalance INACCTACCM timeout | see §4-C | | |

---

## 11. Fix-Version Matrix (deep-read bugs)

| Bug | Cluster | State / Reason | Fixed-in build (INFERRED unless noted) | PR(s) | SF case |
|---|---|---|---|---|---|
| #1731166 | §5 ASSCGLM | Closed | **2025.04 / 2025.04.1.3 HF** | 114597,114879-81 | 25-01023169 |
| #1734347 | §5 | Closed (not-repro) | dup of #1731166 | — | 25-01016940/25-01023169 |
| #1761294 | §5 | Closed/**Rejected** (dup) | get AHS to 2025.04.1.3 | — | 25-01041541 |
| #1783341 | §3 paystation dup | Closed | 2023.04 HF (exemption) | 124280,124281 | 26-01083551 |
| #1698080 | §3 | Closed/**Rejected** | data script #1697957 (no code build) | — | 24-00989255 |
| #142562 | §3 | Resolved | ~2019 v17 | 16500 | — |
| #84246 | §3 | Closed | ~2019 v17 | 7195/7326 | — |
| #1610587 | §3 sel_paystation | Closed | 2021.10/2022.10/2023.04/develop | 89505,89630/31,89971,90306-09 | — |
| #1641272 | §3 | Closed | client ALT 2021.10 | 92780 | — |
| #1654719 | §3 | Closed/Verified | client NRM 2023.04 | 95414 | — |
| #1745358 | §3 perf | Closed | 2024.10/2025.04/develop (MSSQL force-order) | 115120/21,114974/78,115483 | — |
| #1746523 | §3 perf | Closed | 2021.04/2024.10/2025.04/develop | 115145,115216-18 | — |
| #1757855 | §3 contractual ps | Closed | 2024.10/2025.10/develop | 120517,120813,120840 | 25-01045925 |
| #1776751 | §3 cross-fac CCT | Closed/**Rejected** | won't-fix (workaround) | — | 26-01066265 |
| #1772117 | §4 imbal dup | Closed | 2025.04 + 2025.10 (QCODE_POST_TABLES) | 124423,124426 + scripts | 25-01060242/25-01061774 |
| #1723573 | §4 seq overflow | Closed | 2020.03/2024.04(.10)/develop NUMBER(19) | 110407-13,110562-69 | 25-01014345 |
| #1636859 | §4 INACCTACCM | Closed | 2022.10 + 2023.04 (+ SPLIT_COUNT cfg) | 92067,92068,93041 | 23-00934008 |
| #1593783 | §4 INACCTACCM | Closed | **core change backed out** → #1596532 | 84102/06,84830 | — (ET/EMP) |
| #1599265 | §4 INACCTACCM | Closed | change reverted from core | 84830 | 23-00901236 |
| #1729655 | §4 (QPTM lean) | Closed | client SUI 2022.04 (script) | 113631 | 25-01012810 |
| #1712833 | §6 split CAST | Closed | 2024.10 CAN | 109849,110017,111073 | 25-01002874 |
| #1720430 | §6 split %=0 | Closed | data (PDA company) | — | — |
| #1721618 | §6 DOI split blank | Closed | 2024.10/develop/release | 110957-111474 | — |
| #1721986 | §6 build-split popup | Closed | 2024.10/develop | 110965,111008,111087 | — |
| #1617223 | §6 blank suffix | Closed | 2022.10 and up | 91470,91543,91593 | 23-00915506 |
| #1662516 | §6 suffix+notif | Closed | 2022.10 and up | 96976,97055-57 | 24-00954040 |
| #1554087 | §6 conv factors | Closed | client NRM (CAN) | 76390 | 22-00251974 |
| #1674125 | §6 DPT freeze | Closed | client NRM HF | 99618 | 24-00965214 |
| #1623285 | §7 CML orphan split | Closed | 2022.10 and up (trigger) | 90625-27 | (BUG149) |
| #1627134 | §7 | Closed | 2022.10 and up (ESuite trigger) | 90733,91106,91109,91137 | 23-00925437 |
| #1666247 | §7 | Closed | 2022.10/2023.04/2024.04 (config+cache-day) | 99122,99162,99164,99739 | 24-00957962 |
| #1707431 | §7 (HPE F/V) | Closed | client HPE patch6 (config key=1) | 105090 | 24-00957962 |
| #1620262 | §7 CML dup row | Closed | 2022.10 and up | 91226-99831 | 23-00913209 |
| #1695221 | §7 reject-opt dup ps | Closed | 2022.10+ | 102562,102568,102645/46 | 24-00986307 |
| #1788087 | §7 QCM cache valid. | Closed | 2025.04/develop; ESuite 2026.04 | 126302,126357,126642,127743/44 | 26-01084783 |
| #1748551 | §7 QCM sync null | Closed | cherry-pick 2022.10 (out-of-support) | 119445 | 25-01033727 |
| #1756941 | §7 closed-meter query | Closed | 2025.x widely merged | 118883-119730 | — |
| #1758565 | §7 | Closed/**Duplicate** of #1756941 | — | — | — |
| #1740256 | §7 eff-date web | Closed | 2025.04/develop/release | 116914,116972-74 | — |
| #1743518 | §7 plant validation | Closed/Verified | config (UPC 2025.04 HF) | — | — |
| #1769433 | §7 copy/paste | Closed/**Rejected** | won't-fix (classic) | — | — |
| #1610868 | §7 end-date ctr | Closed/Verified | 2021.10 (DTM HF) | 88111 | — |
| #1763742 | §8 CCT end-date | Closed | 2025.04 + 2025.10 (on by default) | 120456/59,120773-76 | 25-01052033 |
| #1608551 | §8 CCT event235 | Closed | 2022.10 and up | 90843 | 23-00908598 |
| #1637466 | §8 default CCT | Closed | 2022.10 and up | 92596-95399 | — (ALT) |
| #1561361 | §8 CCT keepwhole | Closed | 2022.10 HF (data + platform) | 78266 | — (DCP) |
| #190067 | §8 equalization | Closed/Verified | 2020.03 (PEM HF) | 27505 | — |
| #264857 | §8 ctr margin | Closed | 2021.04 | 46534,46833 | — |
| #280352 | §8 mtr margin | Closed/Verified | 2021.04 | 51957,51999 | — |
| #264928 | §8 value-fee UOM | Closed | 2021.04 | 45565,46834 | — |
| #1577942 | §8 keepwhole stmt | Closed | 2023.04 | 82757,82764,82798 | — |
| #1431618 | §8 CCT ALL fac | Closed | 2021.10/release/develop (PEM) | 65528-67211 | — |
| #1665538 | §8 dup dropdown | Closed/**Rejected** | won't-fix | — | — |
| #128343 | §9 mtr-def delete | Closed/Verified | 2020.03 (ONM lineage) | 39587,44822 | 20-00061614 |
| #1679180 | §9 shared-meter del | Closed | 2024.x (24.22) | 102229,102762,103263,104068 | — |
| #1638163 | §9 udef bool | Closed | 2021.10 + 18.x + release | 92203 | 23-00902756 |
| #1551024 | §9 udef bool (DTM) | Closed/Verified | client DTM | 79281,79353 | — |
| #153358 | §9 shared-meter fac | Closed | ~2020 (MKW HF) | 18974-25402 | — |
| #1650646 | §9 BA contact trig | Closed | 2023.04/2024.04/develop | 94968,96439 | 24-00946543 |
| #1731356 | §9 state dropdown | Closed/**Rejected** | — | — | 25-01020950 |
| #193690 | §10 company lock | Closed | 2022.x (IS_SHOW_LOCKED) | 64079/80,64744,64961 | — |
| #1438866 | §10 company lock open | Closed | 2022.05/release | 66663,66714 | — |
| #1543774 | §10 batch status | Closed | 2021.10/2022.10/develop | 74470-74647 | 22-00287124 |
| #279946 | §10 POST results | Closed | 2021.04 (SPOST col) | 45829 | — |

---

## 12. Diagnostic Pointers

```sql
-- §3 duplicate paystation
SELECT TRNX_ID, MTR_SFX, COUNT(*) FROM QTRAN_PAYSTATION WHERE ACCT_DT='<MTH>'
GROUP BY TRNX_ID, MTR_SFX HAVING COUNT(*)>1;
-- orphan TRNX_ID across child tables (MOM #1695221 pattern):
SELECT COUNT(*) FROM QTRAN_PAYSTATION WHERE TRNX_ID NOT IN (SELECT TRNX_ID FROM QTRAN_TRNX_ID);

-- §4 duplicate imbal balances
SELECT BA_NO,CTR_NO,ACCT_DT,PROD_DT,COUNT(*) FROM QTRAN_IMBAL_ACCT_BAL
WHERE ACCT_DT='<MTH>' GROUP BY BA_NO,CTR_NO,ACCT_DT,PROD_DT HAVING COUNT(*)>1;
-- sequence vs column precision
SELECT TABLE_NAME,COLUMN_NAME,DATA_PRECISION FROM ALL_TAB_COLUMNS
WHERE COLUMN_NAME='ACCT_ACTIVITY_DTL_ID';   -- product std = NUMBER(19)
-- INACCTACCM splitting config
-- Global config SPLIT_COUNT_INACCTACCM ; RUN_IMBALANCE_BY_FACILITY (HEC)

-- §5 ASSCGLM dup gas lift
SELECT * FROM QTRAN_ALLOC_VOL WHERE PROCESS_ID='ASSCGLM' AND PROD_DT='<dt>';
SELECT * FROM QTRAN_PLANT_STATUS_REALLOC WHERE PROD_DT='<dt>';

-- §7 QCM/TIPS meter-header sync (CML "no rows" / null deref, #1748551)
SELECT * FROM SEXTN_MTR_HEADER_QRMTIPS a WHERE NOT EXISTS
 (SELECT * FROM SEXTN_MTR_HEADER_QCM b WHERE a.MTR_NO=b.MTR_NO AND a.EFF_DT_FROM=b.EFF_DT_FROM);

-- any batch failure
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID='<id>' AND SQL_SUCCESS_IND=0;
SELECT * FROM QARCH_PROCESS_MSG_LOG   WHERE PROCESS_QUEUE_ID='<id>';
```

**Config keys that recur:** `VALIDATE_END_DT_NO_ORPHAN_MTR_SPLIT_CHILD_RECORDS` (CML orphan split, §7), `IS_SHOW_LOCKED` (Company/Facility Lock query, §10), `SPLIT_COUNT_INACCTACCM` (imbalance perf, §4), `RUN_IMBALANCE_BY_FACILITY` (HEC dup balances, §4), `TRNX_ID_ORDER_BY_CLAUSE_IN_SEL_PAYSTATION` (sel_paystation order-by, §3), `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK` (split rounding, companion skill §4).

**Cache:** CML/meter-split validations read cached views (`VTIP_QCTRL_MTR_SPLIT_DTL_VW`, plant-meter `FirstDayToCache`); a "false validation" that clears after a **service restart** = caching, not bad data. Fix is a cache-refresh trigger / cache-day config, not a re-run.

---

## 13. Escalation Guidance — is the client build fixed?

**Step 0 — ALWAYS capture:** client + env (PRD/UAT/DEV), the **build/patch version** (e.g. 2025.04.1.3), plant/facility + accounting + production month, the Process Queue ID, and the exact constraint/column/SQL-ID in the error. The constraint/table name routes the cluster: `QTRAN_PAYSTATION`→§3, `QTRAN_IMBAL_ACCT_BAL`→§4, `QTRAN_ALLOC_VOL`+ASSCGLM→§5, CML/QCM screen→§7.

**Is the fix on the client's build?**
- Build numbers above are **inferred** (IntegrationBuild was empty). Map: iteration `21.xx`→2021.04, `22.xx`→2022.10, `23.xx`→2023.04, `24.xx`→2024.04/2024.10, `25.xx`→2025.04/2025.10. The dev's PR comment naming a release branch (`[2025.04]`, `[2024.10]`, `[develop]`) is the most reliable signal — but always **confirm in the client's release/patch notes**.
- **Maintenance bugs ship as client hotfixes.** A core fix in 2025.04 does **not** mean the client has it — e.g. AHS gas-lift (#1761294) needed 2025.04.1.3 specifically. Confirm the client consumed the patch that contains the PR.
- **Out-of-support versions:** clients on 2022.04/2022.10 (e.g. MKW #1748551, SUI #1729655) are outside the standard patch policy → either a delivery **exception** or a **manual script** — flag to the product owner.

**Route the work:**
- **Code defect → Engineering/ADO bug:** registered-SQL dup generators (§3 #1783341), ASSCGLM purge (§5 #1731166), imbalance dup/precision (§4), CML cache/validation (§7), QFC udef-bool (§9), trigger seq mismatch (§9 #1650646). Only after confirming the fix isn't already in a later patch than the client's PRD.
- **Config/data → Cloud Ops:** dup-row delete scripts (paystation/imbal/CML — always scoped to client/env/month with a verify-SELECT), enable a config key (`VALIDATE_END_DT_NO_ORPHAN_MTR_SPLIT_CHILD_RECORDS`, `IS_SHOW_LOCKED`, `SPLIT_COUNT_INACCTACCM`), fix QCM↔TIPS sync, fix PDA company, check a config into the client repo so patches don't wipe it (§4 HEC).
- **Won't-fix / customer:** classic-only cosmetic or copy/paste gaps where My Q works (#1769433, #1665538, #1776751) — products deprioritizes classic; redirect to My Quorum.

---

## 14. Classification & Overlap Caveats (read before trusting counts)

- **WIQL matched 499 raw hits, capped to ~250 most-recently-changed; 66 deep-read.** Title-term `CCT` and `company` are broad substrings and pulled noise.
- **Cross-product (Maintenance branch is mixed QPTM+TIPS):** dropped clearly-QPTM items, e.g. #1635464 (RFS timezone MCT), #245317 (APL QPTM INTRDTRANS), #1645775 (Chart of Accounts QPTM), #1695530/#1696361/#1704986 (QPTM INACCTACCM/INGASACCTG/TSP). Kept-but-flagged QPTM-leaning company/imbalance items where they're genuinely shared master data: **#1650646** (BA Contact, "QPTM Reviewed" tag), **#1729655** (Customer Account Accumulation upstream-fuel/SAP export), and the INACCTACCM perf items (§4-C) which straddle both products.
- **False matches dropped:** #1561331 ("Legal API POST Unit Test", Land area — matched on `CCT` substring), and other `company`-substring UI tickets with no master-data root cause.
- **No root cause / Rejected / data-only (stated, not invented):** #1731356 (state dropdown, no resolution), #1769433 / #1665538 / #1776751 (Rejected won't-fix), #1698080 (Rejected → data script), #1720430 / #1554087 / #1748551 (data/sync fixes). These are labeled as such rather than given a build number.
- **All fixed-in-build values are INFERRED** from iteration + PR-branch comments (IntegrationBuild empty everywhere) — confirm against the client's release notes / patch manifest before quoting to a customer.
- ADO was **read-only** for this mining; no work items, PRs, or wikis were modified.
```
