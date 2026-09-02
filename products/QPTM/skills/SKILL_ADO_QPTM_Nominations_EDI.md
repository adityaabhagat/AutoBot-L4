# SKILL: QPTM Nominations & EDI — ADO Defect/Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management)
**Source:** Azure DevOps closed/resolved Bugs (org `QuorumSoftware`), area paths `Engineering\Energy Transportation` and `Engineering\Maintenance\Midstream and Transportation`.
**Scope:** Nomination submission/upload/copy, nomination validation rules (NN000*), autogen (NNAUTOGEN/NNATGLF), fuel recalc (NNCALCFUEL), confirmations & balancing (CFAUTOCONF/PBBALCHAIN) as they relate to noms, and the full **EDI** pipeline — inbound (EDINCOMING / EDINSEG / EDSPLITIN) and outbound datasets (NMST/SQTS, NMQR/RQCF, RRFC, SQOP, CRAN/CROF, MSIN/OACY), EDIServ (the WCF EDI receiver/sender), and GnuPG encrypt/decrypt. NAESB grammar versions (1.8/3.0/3.1/3.2/4.0) and the per-TPA datasets.

> **Use When:** an ADO bug or SF case is about a nomination not validating/submitting/copying correctly, a nom-upload/import failing, an autogen rule misbehaving, an EDI file failing to generate/send/parse, a confirmation cut being wrong, or a NAESB-compliance gap in an outbound EDI file. This is an **ADO-mined** companion to the L4 QPTM skills (`SKILL_EDI_Troubleshooting.md`, `SKILL_QPTM_Nomination_Validation.md`, `SKILL_Cycle_Deadline_Reference.md`).

> **Evidence base:** WIQL matched **916** closed/resolved Bugs across the two area branches (functional title filter: Nomination, NMST, NMQR, RRFC, EDI, EDIServ, cycle, late nom, ENMQR, ECRQR, cycle indicator). Capped to the **250** most-recently-changed for field triage; **57 deep-read** (Description + ReproSteps + relations/PRs + the full dev comment thread). Every root-cause/fix claim below cites a real ADO Bug ID and (where present) the SF case in the title (`YY-0xxxxxxx`). **Overlap caveat:** the Maintenance branch is mixed QPTM+TIPS; the title filter pulled ~17 TIPS-genuine items (Gas Statement, Billing Invoice, ND REG EDI tax, Settlement) which were **dropped**. A few "TIPS" titles are actually QPTM (e.g. #1672104, #1706821 — QPTM→TIPS nom integration) and are kept. Also dropped: a large false-positive class where the title substring "edit"/"Bulk Edit" matched the "EDI" filter (Measurement/Credit/Rate-Maintenance Bulk-Edit bugs — out of scope).

> **Fixed-in-build caveat:** `Microsoft.VSTS.Build.IntegrationBuild` is **empty on every bug** in this set, and `IterationPath` carries only a dev *sprint* number (`YY.NN`, e.g. 25.07 = 2025 sprint 7), **not** a release. Release/patch targets below (2024.04, 2024.10, 2025.04, 2025.10, 2026.04, client hotfixes) are taken from the **dev comment thread / PR cherry-pick notes** where stated, else marked **(inferred — confirm in release notes / the linked patch WI)**. Always confirm the client's actual build before promising a fix is present.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — EDINCOMING / EDIServ runtime failures (object-reference, TPA-not-found, decrypt, timeout)](#4-cluster-a)
5. [Cluster B — Outbound EDI Location-ID vs Interconnect-ID & NAESB nom model code](#5-cluster-b)
6. [Cluster C — NAESB version gaps in outbound files (ID3 recall indicator, FNAK version, MSIN qty, OACY suppress)](#6-cluster-c)
7. [Cluster D — Inbound confirmation cuts & RRFC/SLN mismatch (cut-to-zero, PT vs PNT)](#7-cluster-d)
8. [Cluster E — Non-standard cycle IDs & cycle/confirmation carry-forward](#8-cluster-e)
9. [Cluster F — Nomination validation rules firing / not firing](#9-cluster-f)
10. [Cluster G — Nomination upload / import (NNNOMLOAD / NOMIMPEXTS) failures](#10-cluster-g)
11. [Cluster H — Autogen (NNAUTOGEN / NNATGLF) & NNCALCFUEL](#11-cluster-h)
12. [Cluster I — Nomination Submission screen behavior (copy, BA-name/nom-hash, picklists, LI-deletes-paths, error wrap)](#12-cluster-i)
13. [Fix-Version Matrix](#13-fix-version-matrix)
14. [Diagnostic Pointers](#14-diagnostic-pointers)
15. [Key Code, Processes & Repos](#15-key-code-processes--repos)
16. [Escalation Guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user/ADO bug reports) | Likely cause | Cluster |
|---|---|---|
| EDINCOMING / NMQR "Object reference not set to an instance of an object"; no response file sent to TP | Null `TrackId` on NMST error records flows into NMQR `Sort`; or **TPA not found** (bad/duplicate DUNS) → null-ref | §4 |
| EDI process fails to **decrypt** incoming file (GPG "Invalid argument" / "GPG command exceeded timeout") | File-share path/permissions (Cohesity) + GPG `PROCESS_TIME_OUT` too low (5 s default) | §4 |
| EDIServ picks the **wrong trading partner** / cache built off wrong DUNS | EDIServ TPA cache keyed on `PACTRL_TSP.DUNS_NO` instead of the TSP BA DUNS; or duplicate TPAs silently resolved to "first" | §4 |
| Outbound RQCF/SQOP carries **Interconnect Loc ID** when it should carry **Location ID** (or vice-versa); RRFC the opposite | `USE_INTERCONNECT_LOC_FOR_RRFC` config controlled all three; ENT fix changed shared functionality | §5 |
| SQTS/NMST shows nom model **'U' (unthreaded)** when it should be **'T' (threaded)** | LC Nomination Submission stamps wrong `NAESB_MODEL_CD` on `NNCTRL_NOM_HDR` | §5 |
| Outbound file missing **NAESB-required segment** (ID3 recall `N9*48`, FNAK version 7030, MSIN QTY when zero, OACY rows) | Dataset class never updated for NAESB 3.1+ / version-gating gap | §6 |
| EDI **cuts a confirmation to 0** though the matching confirmation exists; `ECRQR539 no corresponding nomination` | SR# / nom-flow-code / nom-agent (BP) mismatch between EDI file and contract; or PT-vs-PNT LOC_ID handling | §7 |
| Manual RRFC produces **different SLN** than automated RRFC (TP can't match → cuts to 0) | `CONF_TRK_ID` null for Path noms; manual RRFC reads DB, auto RRFC uses cached file data | §7 |
| EDINSEG / EDINCOMING fails "**No cycles open**" / "cycle already closed" for a client using non-standard cycle IDs | Code compares `IdConfCycle < nOpenCycle` against standard IDs only | §8 |
| Nomination validation **not firing** when it should (MDQ, eff-end-date, inventory account, segmentation) | Rule scope/logic gap (begin-day-only check, null OIA, unchecked rule assignment) — sometimes config | §9 |
| Nomination validation **firing wrongly** / on the wrong row / in all envs | Rule reads wrong field, pool-to-pool not excluded, picks first nom row; or a WWM-only rule leaked to core | §9 |
| Nom **upload/import** (NNNOMLOAD/NOMIMPEXTS) fails: unique constraint, "please requery", arithmetic overflow, integrity constraint, multi-SR | Staging/merge defects; `.xls` vs `.xlsx`; single-SR/company restriction; staging-table schema drift | §10 |
| Autogen creates wrong downstream BP / Activity IDs instead of noms / only Timely cycle picked up | Target-TSP resolution bug; bad cycle data; `ActiveCyclesByDay` null in Load-Following path | §11 |
| NNCALCFUEL not updating fuel % after rate change | Rate **cache** not refreshed; or nom in line error | §11 |
| Nom Submission: copy picks up **old BA name** / picklists become editable on submitted nom / **LI nom deletes all paths** / long error not wrapped | Nom-hash/`NNCTRL_NOM_HDR` BA-name, DataObjectState='Added', validation-engine date-split, V2UI grid CSS | §12 |

---

## 2. Pipeline & Concepts

```
[Nomination Submission / LC Nom / Nom Upload (NNNOMLOAD) / Nom Import (NOMIMPEXTS)]
     │  (validation rules NN000* fire: LI = Line Invalid, BI = Business Invalid)
     ▼
[NNCTRL_NOM_HDR + NNCTRL_NOM_DTL]  ──► AUTOGEN (NNAUTOGEN / NNATGLF) ──► target-TSP noms
     │                              ──► NNCALCFUEL (re-applies changed fuel %)
     ▼
[Confirmations]  ◄──►  EDI INBOUND (EDINCOMING / EDINSEG / EDSPLITIN)
     │  CFAUTOCONF / PBBALCHAIN apply cuts                  RQCF/RRFC/CRAN/CROF/NMST inbound
     ▼
EDI OUTBOUND datasets (per TPA, per NAESB grammar):
   G873 NMST/SQTS (nom)  · G874 NMQR/RQCF (quick response/confirm) · RRFC (request reduction confirm)
   SQOP (offer) · CRAN/CROF (capacity release) · MSIN (measurement) · OACY (operationally avail cap)
     │  → GnuPG encrypt → EDIServ sends to Trading Partner (TP)
```

### Key terms (Quorum/QPTM vocabulary)
- **EDINCOMING / EDINSEG / EDSPLITIN** = inbound EDI batch processes (run through **QPEC**, the QPTM segregated-process executor). Read the encrypted file from the **PROCESS_IN_ENCRYPTED_PATH**, GPG-decrypt, parse against the **TPA dataset**, write confirmations/noms, then generate the response (e.g. NMST in → NMQR out).
- **EDIServ** = the standalone WCF service that physically **receives/sends** EDI to trading partners and maintains a **trading-partner (TPA) cache**. Distinct from QPEC; an EDIServ issue is not a QPEC issue (#1737489).
- **TPA** = Trading Partner Agreement / record (BA + DUNS + NAESB grammar version + dataset config). Keyed by DUNS. Duplicate or wrong-DUNS TPAs cause null-ref or wrong-partner resolution (§4).
- **NAESB grammar version** = WGQ EDI standard version on the TPA: `1.8`, `3.0`, `04010`/`3.1` (maps to X12 `007030`), `3.2`, `4.0`. Dataset classes are versioned: `QEdiNMSTOut18`, `QEdiCRANOut31`, `QEdiCROFOut18`, etc. 3.2 inherits 3.1; 4.0 inherits 3.2 — so a fix on the 3.1 base often flows up.
- **NMT segment / `NAESB_MODEL_CD`** = nomination model: **'T'** threaded (path) vs **'U'** unthreaded. Stamped on `NNCTRL_NOM_HDR`; wrong value → wrong NMT in NMST/SQTS (§5).
- **Location ID vs Interconnect Location ID** = which location identifier goes in an outbound dataset. NAESB 3.0+: RQCF & SQOP carry **Location ID**, RRFC carries **Interconnect Loc ID**. Controlled by `USE_INTERCONNECT_LOC_FOR_RRFC` (and intended siblings) global configs (§5).
- **ECRQR539 / "no corresponding nomination"** = inbound confirmation can't match a nomination (SR#, nom-flow-code, BP/DUNS, or pkg mismatch) → cut to 0 (§7).
- **SLN / `CONF_TRK_ID`** = confirmation tracking id grouping a confirmation's lines; a manual RRFC that mints a different SLN than the automated one breaks TP matching (§7).
- **Cycle IDs** = `1 Timely, 10 Evening, 132/148/166 Intraday 1/2/3` are *non-standard* client IDs (Cheniere); core compares against standard IDs and rejects (§8). IDL = a newer non-NAESB intraday-late cycle (EQC, §8).
- **LI / BI** = Line Invalid / Business Invalid nomination validation states. Rules named `NN00009xxx` / `NN00003xxx` / `NNFK0000xx` (FK checks) / `NNG001`/`NNG031` (TIPS-side nom transaction).
- **NNAUTOGEN / NNATGLF** = autogen batch (NNATGLF = the Load-Following flow). Reads a source nom, generates a target-TSP nom per autogen rules (storage, imbalance DST/DSL threshold, etc.).
- **NNCALCFUEL / NNBULKCOPY** = ONK-specific fuel-recalc (core analogue = NNBULKCOPY). Re-applies a changed fuel rate to existing future noms.
- **QPEC** = QPTM segregated process executor (runs EDI/nom batch steps); **QFC** = the Quorum file/config layer; **QFC architecture** auto-stamps audit columns (USER_ID/UPDT_DT) on saves.

---

## 3. Decision Tree

```
QPTM Nomination / EDI bug
│
├─ EDI process CRASHED or sent nothing?
│   ├─ "Object reference not set..." in EDINCOMING/NMQR, no response file        → §4  (null TrackId / TPA-not-found; #1737489, #1606709/#1736915, #1719226)
│   ├─ GPG decrypt "Invalid argument" / "GPG exceeded timeout"                   → §4  (file share + PROCESS_TIME_OUT; #1672049)
│   ├─ EDIServ picks wrong/duplicate TP, or cache off wrong DUNS                  → §4  (#1735182, #1725907)
│   └─ "No cycles open" / cycle-closed for non-standard cycle IDs                → §8  (#1611244)
│
├─ EDI file GENERATED but WRONG content?
│   ├─ Loc ID vs Interconnect Loc ID swapped (RQCF/SQOP/RRFC)                     → §5  (#1678265, #1694083, #1708573)
│   ├─ NMST/SQTS model U vs T wrong                                               → §5  (#1595439)
│   ├─ Missing NAESB segment (ID3 N9*48 / FNAK 7030 / MSIN QTY / OACY rows)       → §6  (#1756196, #1781005, #1799746, #1764346, #1759474/#1718572)
│   └─ Inbound cut to 0 / ECRQR539 / manual-vs-auto RRFC SLN mismatch            → §7  (#1639014, #1770476, #1708573)
│
├─ Nomination VALIDATION wrong?
│   ├─ Not firing (eff-end-date, MDQ, inventory acct, segmentation, late-nom)     → §9  (#1730358/#1755248, #1404268, #1712405, #1726480, #1609881)
│   ├─ Firing wrongly / wrong row / all envs (AOS pool-to-pool, WWM rule in core) → §9  (#1775092, #1712648)
│   └─ Import/screen validation inconsistent (DUNS, invalid TT-for-TOS)           → §9/§10 (#1630769, #1610219)
│
├─ Nom UPLOAD/IMPORT failing (NNNOMLOAD / NOMIMPEXTS)?                            → §10 (#1664076, #1664436, #1455439, #1532428, #1692624)
│
├─ AUTOGEN or NNCALCFUEL misbehaving?                                            → §11 (#1710461, #1692472, #1747677, #1442540, #1460001, #166087)
│
└─ Nom Submission SCREEN behavior (copy/BA-name/picklist/LI-deletes/wrap)?       → §12 (#1454476, #1666979, #1452323, #1607098)
```

---

## 4. Cluster A — EDINCOMING / EDIServ runtime failures
<a name="4-cluster-a"></a>

The single largest EDI-runtime signature: the inbound process throws **`Object reference not set to an instance of an object`** and **no response file** reaches the trading partner, or it fails to decrypt, or EDIServ resolves the wrong partner.

### A1 — Null-ref in NMQR `Sort` from null `TrackId` (APL/EDF — #1737489)
**Symptom:** EDINCOMING errors; NMQR file never sent to TP (EDF Trading). EDI server log shows no attempt to send the response. Intermittent, TP-specific.
**Root cause (dev, Grayson Lee):** for noms **already submitted** for the date range covered by an incoming NMST, the NMST path *did not* set/guard `TrackId`, so **error records with null TrackId** were generated; those then cause an **object-reference exception inside `QEdiQRBase.Sort`** when building the NMQR. (Repo path the dev cited: `Quorum.QPTM.Batch /Quorum.QPTM.EDI.DataSets/G874NMQR/QEdiQRBase.cs` ~line 153.)
**Fix:** added the missing **null checks where `TrackId` is set** in the NMST processing; feature branch fixed it locally in APL_HD_DEVA1. Note dev's initial position: very infrequent → start with proactive null-checks/logging. **Fixed-in-build:** client hotfix for APL planned 2025 (inferred — confirm the linked patch WI); develop.
**Key lesson:** **this is a QPEC issue, not an EDIServ issue.** Gather **QPEC GatherLogs** (the `qtrace.QPTM.QPEC.*.segregated.log` in the Managed Steps folder), not just EDIServ logs.

### A2 — Null-ref when TPA not found, inbound & outbound (#1606709 inbound, #1736915 outbound; sourced from #1455963)
**Symptom:** EDINCOMING (or outbound EDI) → "Processing failed. Additional information: Object reference not set to an instance of an object" when the **TPA/DUNS isn't found**.
**Fix:** add a null guard so an invalid DUNS that doesn't exist in the DB returns a clean error instead of a null-ref. **Fixed-in-build:** sprint 25.13 → **2025.10** (inferred from iteration).

### A3 — EDIServ TPA cache keyed on wrong DUNS / duplicate TPAs (#1735182, #1725907)
- **#1735182:** EDIServ trading-partner **cache loads off `PACTRL_TSP.DUNS_NO` instead of the true TSP BA's DUNS**. Fix: make EDIServ cache logic **mimic the batch** `QEdiDataCacheQPTM.cs`. Sprint 25.12 → **2025.10** (inferred).
- **#1725907:** when looking up a TP, EDIServ silently picked the first of multiple matches. Fix: **throw an error whenever multiple TPs match** (regardless of `UseTpaDunsPriority`) — force the client to fix duplicate TPA setup rather than guess. Sprint 25.09 → **2025.10** (inferred).
- Related EDIServ hygiene: **#1710259** (incoming EDIServ sometimes saved the entire multipart form-data instead of just the EDI file — 25.03); **#1772081** (`UTIL_RESYNC_SEQ` SP fails on a table literally named `NA - EDISERV` → "Incorrect syntax near '-'"; fix = rename to `EDISERV`; also reproduces in core — 25.26); **#1794863** EDIServ release pipelines failing (build infra, 26.09). **#1719226** EDINCOMING null-ref during 2025.04 beta regression (closed as not-repro in MSSQL ETS RELQA — sometimes data, not code).

### A4 — GPG decrypt failures: "Invalid argument" / "GPG command exceeded timeout" (HPE/Skippingstone — #1672049)
**Symptom:** intermittent EDI responses; EDINCOMING completes with errors. Log: `gpg: error creating '...dec': Invalid argument` → `Failed to decrypt encrypted file`; later `Could not start GPG ... GPG command has exceeded timeout`.
**Root cause:** (1) the EDI decrypted-file path lived on a **Cohesity share** (`\\HDC2-COH-QCSFS01\QFC17$`) that GPG couldn't write to reliably; (2) the GPG **`PROCESS_TIME_OUT` defaults to 5000 ms (5 s)** in code, too low under load.
**Fix/Workaround:** moved off the Cohesity share **and** added a QPTM global config override `EDI / PROCESS_TIME_OUT = 15000` (metadata, requires DB upgrade or a manual `QARCH_CNFG_CTRL` insert + **QPEC restart**). Mostly resolved; remaining `CE` errors were legit. Delivered via `QHPE.QPTM.Metadata` hotfix (inferred). **This is a Cloud-Ops + metadata fix, not a core code change.**

---

## 5. Cluster B — Outbound EDI Location-ID vs Interconnect-ID & NAESB nom model code
<a name="5-cluster-b"></a>

A recurring, **NAESB-compliance** family: which location identifier (sender Location ID vs Interconnect Location ID) goes into each outbound dataset, and the threaded/unthreaded nom model.

### B1 — One config controlled all three datasets; the ENT fix broke shared functionality (#1678265 → collateral #1694083)
**Symptom (ENT, 24-00960415):** outbound **RQCF, RRFC, SQOP** all sent the same loc id. Expected (NAESB 3.0+): **RQCF & SQOP = sender Location ID; RRFC = Interconnect Loc ID**. The `USE_INTERCONNECT_LOC_FOR_RRFC` config, when ON, made *all three* send Interconnect; when OFF, all three sent Location ID.
**Root cause:** the single config gated all three datasets instead of just RRFC.
**Fix (ENT, #1678265):** code change so RQCF/SQOP send Location ID and RRFC sends Interconnect, per NAESB. **ENT hotfixed (Aug 2024); queued for QPTM 2020.03** per tags.
**Collateral (#1694083, TEP/Tallgrass, 2024.04):** the ENT change **forced the new behavior on everyone** (Tallgrass, Williams) who were relying on the old behavior. Products' decision: should have been **opt-in**. Fix = a config to control Location vs Interconnect for RQCF/SQOP (and RRFC); **note also TPA must be NAESB 3.0+** (TPA 20 on 2.0 grammar won't get the change). Closed ~2024.12/2025.04 release (inferred). **Lesson:** treat any "loc id wrong in outbound EDI" as config + NAESB-version-on-TPA first; the underlying behavior is shared across RQCF/RRFC/SQOP.

### B2 — RRFC sends wrong interconnect for displacement / PT noms (#1708573, QTR/MWOP, 25-00996583)
**Symptom:** inbound RQCF for loc 10030 → generated RRFC contains displacement data for **10027** instead, cutting Ruby's interconnect at 10030 to 0. Running RRFC from the batch screen produced the *correct* file.
**Root cause (dev, Santaji/Zach):** a 2011-era **override of `LoadDataFromDB()` for RRFC** (handles outbound differently when triggered by an inbound file) was **moved into the base class's `LoadDataFromDB()`**, breaking the RRFC inbound-triggered path. Deeper: **PT noms have only one confirmation record** stamped with LOC_ID + REC_LOC_ID + DEL_LOC_ID, and RRFC **always pulls LOC_ID** — fine for PNT (two conf records) but wrong for PT depending on rec/del perspective.
**Fix:** ensure the RRFC override logic runs inside the RRFC override of `LoadDataFromDB()` (not the commented base code). Multiple PRs; **2025.04** + hotfix to client's 2022.04 (inferred). Related: #1713859 (compare RQCF vs RRFC inbound/outbound datasets).

### B3 — Wrong NAESB nom model code (U vs T) from LC Nom Submission (#1595439, TEP, 23-00891839)
**Symptom:** SQTS EDI shows nom model **'U' (unthreaded)** where rec & del have a **threaded path** → should be **'T'**.
**Root cause (dev, ZGK):** **not** an SQTS-outbound bug — the **LC (Location-Centric) Nomination Submission screen stamps the wrong `NAESB_MODEL_CD`** onto `NNCTRL_NOM_HDR`. EDI just reflects the bad header. Most of the client's historical data was wrong since ~Aug 2022.
**Fix:** correct the LC Nom screen so brand-new `NNCTRL_NOM_HDR` records stamp the right model code (both web and classic — classic needed a separate fix; existing single HDR records that only add DTL rows won't flip U→T without a data script). **Go-forward only** (Products confirmed no past-data fix). TEP **Patch 13** (2024.03, complete) + develop. **Lesson:** "EDI shows wrong model/threading" → check the **source `NNCTRL_NOM_HDR.NAESB_MODEL_CD`** (EDI is the messenger; the code is NAESB-regulated and rarely the bug).

---

## 6. Cluster C — NAESB version gaps in outbound files
<a name="6-cluster-c"></a>

Dataset classes that were **never updated for a newer NAESB version**, so a required segment is missing → TP rejects the file. Same fix pattern repeats per dataset.

| Bug / SF | Dataset | Missing element | Root cause & fix | Build |
|---|---|---|---|---|
| **#1756196** | CRAN out (capacity release notification) | **ID3 Recall Notification Period Indicator** `N9*48` | `QEdiCRANOut31` (NAESB 3.1) never added ID3 (only through ID2 / `N9*45`). Fix: copy the ID2 segment builder (`CreateHeaderN9_Intraday2RecallNotificationIndicatorSegment`) for ID3, **version-gated to NAESB 3.1+** (3.2/4.0 inherit). | sprint 25.21 → **2025.10** (inferred) |
| **#1781005** (QTR, 25-01060489) | CROF out (capacity release offer) | same **ID3 `N9*48`** + CROF process failed/incomplete | Same pattern as CRAN. Two parts: (1) batch error was a **missing CRNS grammar config in TPA Maintenance** (CROF dataset was being reused for the Notes/Special-Instruction out file) — config fix; (2) added ID3 in `QEdiCROFOut18`, version-gated. **Cherry-picked to 2025.10, current release, develop.** Client must add the TPA-maintenance grammar entry. | **2025.10** (+ TPA config) |
| **#1799746** (APL) | FNAK (functional acknowledgement / 997) | sending **NAESB 04010** when TP (Eleox) expects **7030** | We *should* support 7030 as of NAESB 3.1 datasets; APL_UAT was on 3.2. **Rejected as a bug → routed to Feature #1800045** (treated as enhancement/new work). No code fix shipped under this bug. | — (Feature) |
| **#1764346** (TEP/Trellis) | MSIN out (measurement) | **QTY segment missing when no measurement data exists** | When qty=0 / no `ALCTRL_MEAS_VOL` rows, file is header-only; TP calls it incomplete. **Closed without code change** — could send a "0" entry but it's one TP's requirement, **not a confirmed NAESB violation**, and not reproducible in CORE. Left on hold/closed. | — (no fix; NAESB concern unconfirmed) |
| **#1759474** (GBG, 25-01041261) + **#1718572** (TEP, 25-01005337) | OACY out (operationally available capacity) | OACY **missing data for all locations** (GBG) / OACY **showing locations flagged "Suppress from OACY"** (TEP) | TEP fix #1718572 filtered out SPO-flagged locations → broke GBG, which uses **location-group roll-up** and needs SPO locations to still contribute to the group total. Fix: new global config **`INCLUDE_SPO_LOC_IN_GROUP_ROLLUP`** (PLTM layer, Key Group `EDI`, default 0) — SPO locations don't display individually but still roll up under a location group. **Cherry-picked to 2024.10, 2025.04, 2025.10**; also 2024.04 branch. | **2024.10 / 2025.04 / 2025.10** (+ 2024.04 HF) |

**Fix recipe:** for "outbound EDI file missing a NAESB-required field," first confirm the **TPA NAESB grammar version** and that the field is required at that version; then the fix is almost always **add the segment to the versioned dataset class, gated to the right NAESB version** (e.g. ID3 in `QEdiCRANOut31`/`QEdiCROFOut18`). Confirm there isn't also a **missing TPA-maintenance grammar config** (the CROF batch-error half of #1781005).

---

## 7. Cluster D — Inbound confirmation cuts & RRFC/SLN mismatch
<a name="7-cluster-d"></a>

Inbound EDI applies the wrong cut, or a manual vs automated outbound RRFC disagree, so the TP cuts to 0.

### D1 — EDI cuts confirmation to 0 / `ECRQR539 no corresponding nomination` (#1639014, CHN, 23-00932772)
**Symptom:** inbound EDI cuts a confirmation to zero though the exact confirmation exists for that gas day; `ECRQR539 no corresponding nomination` in the quick-response.
**Root cause (dev, Dianne Miller):** the **Service Requestor in the EDI file (401851) didn't match the contract's SR (401850)**, *and* the confirmation match also depends on **`NomKFloCode`** (was 'T' not 'D' in the table). The "no matching confirmations" filter keys on GasDay/cycle/DelLoc/Contract-BpNo/SR-CtrNo/DUNS/Pkg — any mismatch cuts to 0. Also involved: CHN uses **NAESB 3.1 datasets and a nom-agent BP** that the 3.1 dataset path didn't fully support; FK errors from `VERSION_CD 3.2` not in `QCODE_ED_VERSION`.
**Fix:** EDI/dataset code changes across `Quorum.QPTM.Batch` + `Quorum.QPTM.Database`; backported **3.1** to 2020.09 and added **3.2** versions in develop (inherit pattern). CHN is **pre-Fluent-Migrator** so the patch required explicit DB scripts. Client hotfix on 2020.09 (inferred). **Lesson:** "EDI cuts to 0 / ECRQR539" → diff the **EDI file's SR# / BP-DUNS / nom-flow-code / pkg** against the contract & confirmation table before assuming a code bug.

### D2 — Manual RRFC mints a different SLN than automated RRFC (#1770476, QTR/Ruby↔MWOP, 25-01047182)
**Symptom:** manually-generated RRFC produces **different SLN numbers for PT vs PNT** noms of the same shipper pair; automated RRFC groups both under one SLN. Ruby treats the mismatched SLNs as conflicting → cuts to 0/EPSQ.
**Root cause (dev, Santaji):** **EDI RRFC outbound builds from confirmations saved in the DB**, but for **Path noms (`K_FLOW_CD = 'T'`) `CONF_TRK_ID` is null**, so it falls back to `100000`. The **inbound-handler response uses cached process data** (correct) — hence manual ≠ automated. Compounded by an **older shared code path** that intentionally **did not persist** a confirmation when the EDI qty matched the DB qty (so `CONF_TRK_ID` was never set), and `CFNOMSYNCH` clearing `CONF_TRK_ID`.
**Fix:** populate `CONF_TRK_ID` (and only modify `CONF_TRK_ID`/`ConfMethCode` when qty unchanged; full behavior when qty changes); broaden to cover the "qty matches DB" path without breaking it. **Cherry-picked to 2025.04, 2025.10, develop** (closed 2025-12-30). Manual RRFC path dates to 2012 — long-standing, only surfaced under PT+PNT.

---

## 8. Cluster E — Non-standard cycle IDs & cycle/confirmation carry-forward
<a name="8-cluster-e"></a>

### E1 — EDI fails "No cycles open" for non-standard cycle IDs (#1611244, CHN)
**Symptom:** `EDINSEG` fails saying an open cycle with the standard cycle IDs is already closed, then lists the same cycle by the client's **non-standard IDs** (CHN: `1 Timely, 10 Evening, 132 ID1, 148 ID2, 166 ID3`). Only Timely (=standard 1) processes.
**Root cause (dev, Zach):** code throws when **`row.IdConfCycle < nOpenCycle`** — the file's `IdConfCycle` (non-standard) is compared against standard open-cycle numbering. BWP hit the same in 2019 (fixed in 4.0.2 changesets 217258/217259).
**Fix:** manual merge of the historical BWP changesets into EDI code (low risk, EDI-only; also affects the SQTS dataset). Patched to CHN's release (inferred ~2023.04 era). **Lesson:** non-standard cycle IDs → known, fixable; reference #105085 / BWP fix.

### E2 — Confirmation Sub-Cycle Y flips to N after balancing into a new cycle (#1761680, EQC, IDL cycle)
**Symptom:** confirmations entered in ID3 don't carry into the **newer non-NAESB IDL cycle** after `PBBALCHAIN`; "Confirm Sub Cycle" checkbox flips Y→N for some records. Intermittent, not reproducible internally.
**Root cause (dev, Christine Lee):** **`PBBALCHAIN` recalculates confirmation state**; when **delivery qty == max qty on the confirmation** (or the record is rebalanced), the process **resets the sub-cycle checkbox to N**. No config gates this; IDL is new and not fully accounted for in carry-forward logic.
**Disposition:** **Rejected as a bug → enhancement** (would need a new toggle config to preserve sub-cycle Y). No code fix shipped. Closed; reopen as enhancement if EQC pursues.
- **Cosmetic cousin:** #1522549 duplicate values in the Confirmation Response **Cycle filter** (V2UI) — code fix to dedupe (metadata approach didn't work); 23.09 → 2023.04 (inferred).
- **PBBALCHAIN not applying EDI cuts to paths (#1757082, HEP, 25-01037438):** EDI cuts didn't apply PBL to paths like manual cuts did; root cause was largely **client config/data** (missing TSP 610 config, BA 10354 not in QPECUSER, weird cycle IDs). Resolved as a **client-specific metadata change** (HEP layer); planned 1/23/2026 hotfix. Treat "PBBALCHAIN behaves differently per TSP" as a **TSP-config diff** first.

---

## 9. Cluster F — Nomination validation rules firing / not firing
<a name="9-cluster-f"></a>

Largest non-EDI cluster. Split into **not-firing** (rule scope/logic gap) and **firing-wrongly** (rule reads wrong field / wrong row / leaked to core).

### F1 — Not firing for noms spanning past contract Effective End Date (#1730358 ETC 24-00990212 → re-occurrence #1755248 ETC 25-01034998)
**Symptom:** contract amendment ends 11/1; a nom 11/1–11/30 validates & submits; the validation **only fires once the nom is later edited**.
**Root cause (dev, Grayson):** **`NN00003010` checked only the *begin* gas day**, not the full nom date range.
**Fix:** change NN00003010 to **pull the full range of nom gas days and loop each day**, checking the contract is effective for every day. Feature branch off develop; **must go in 2025.04 for ETC** (not 2024.04). The recurrence #1755248 also surfaced a **config angle**: NN00003010 zero-nom validation was *unchecked* for PNT & PT in Validation Rule Assignment (so partly a config fix), and interacts with `USE_SR_K_99999_ON_PNT_BUYS_SELLS`. **Core code change**, cherry-picked. **Lesson:** "validation only fires on edit, not on initial submit" → begin-day-only logic.

### F2 — MDQ validation not resolving inventory account (#1712405, HPE, 25-00999987 — NN00009602)
**Root cause (dev, Matthew Lee):** rule is correct *when* it can resolve the Inventory Account, but it **can't handle a NULL Operational Impact Area (OIA)** — it pulls OIA from the receipt location, but OIA isn't required on locations.
**Fix:** default `sOperImpAreaCd` to **"SYS"** when null/empty in `InventoryManager.FindInvAcctIdTiedToContractByAndOIA()` and `InventoryCache.GetInventoryAccountHeaderByPrimaryCtrNoAndOIA()`. Workaround (Matthew) delivered via script first; code fix in a **March 2025 hotfix** (inferred). Software defect (Maintenance).

### F3 — Segmentation-on-the-fly MDQ (NN00003072) — usually NOT a bug (#1726480, HPE, 25-01009023)
**Root cause (dev, Grayson):** NN00003072 sums nominated qty **per pipe segment** (from **Location Path Maintenance**) and errors when a single segment exceeds KMDQ. In the reported case **almost all noms passed through one segment**, so the sum (3,342) > KMDQ (2,563) → correct error. PRD-vs-UAT difference was **Location Path setup**, not code.
**Disposition:** **working as designed**; closed (no customer response). Educate on Location Path Maintenance segment setup.

### F4 — AOS shared-MDQ validation reads wrong field / fires on wrong (0-qty) row (#1775092, WWM, 25-01041489 — NN00009965)
**Symptom:** MDQ validation triggers when total del qty exceeds shared MDQ even though the excess is **Authorized Overrun / Pool-to-Pool (ATT on both rec & del)**; and the error attaches to a **0-qty nomination**, looking wrong.
**Root cause (L4 + dev, Aditya Bhagat / Kunal Ugale):** Shared MDQ was read from **`ctr.OvrdCtrMdq` (returning 0)** and **pool-to-pool noms were included in `dTotalNomQty`**; the engine also defaulted the error to the **first nom row** rather than the offending del nom.
**Fix:** read Shared MDQ from **`ctr.CtrMdqDisplayOnly`**, **exclude pool-to-pool** from the total, and attach the error to the right row. Then a **follow-up correction**: when Override Contract MDQ is null it was treated as 0 (validation fired on everything) → **reverted MDQ source back to `OvrdCtrMdq`** while keeping the pool-to-pool exclusion. **Consumed in 2026.04 and 2025.10**; final revert early June 2026. WWM-specific rule.

### F5 — WWM-only rule NN00009965 leaked into all core environments (#1712648)
**Root cause:** NN00009965 ("Total Del exceed shared CTR MDQ excl Pool to Pool and Auth Ovrn") is **meant to be active only for WWM** but appeared in **Validation Rule Assignment by default** in core, firing on every nom in TST/RELQA.
**Fix:** **remove the two `NNXREF_VALD_RULE_GRP_EFF_RULE` records from core** (`Quorum.QPTM.Database`), keep the rule available in Validation Rule **Maintenance**, and add the WWM-specific records on the WWM layer. Cherry-picked back to **17.27 hotfix**; 2025.04 regression item.

### F6 — Other validation defects (config vs code)
| Bug / SF | Symptom | Disposition |
|---|---|---|
| #1404268 (DTE 21-00207007) | Custom EUT MDQ rule NN00003075 not firing | A **TOS code tied to the validation rule was missing** (data); plus a SQL timeout (sped up the query). Mixed config + perf. |
| #1609881 (ETP/ETC 23-00902666) | Late-nom rule **NN00009015** not re-firing when external user edits Up Rank/Dn Rank/Nom User Data 1/2 | Override-clear logic cleared the flag for Qty/Rank but **missed those 4 fields**. Fix: add them to the uncheck list (`ActivityDetailDOExt.cs`). 2024.04 RELQA; not hotfixed. |
| #1630769 (GBG 23-00928342) | Nom **import** validates Up/Dn DUNS but the **screen doesn't** (inconsistent) | **Not a bug → feature**: there's no FK on the DUNS field; making them consistent is new work (2024.10 consideration). Backed out the changes. |
| #1610219 (CMX) | Nom **import** accepts an **invalid Transaction Type (TT) for a Type of Service (TOS)** | Missing validation on import. Fix: **add TransTypeCode-vs-ActnCode validation** on import (web & classic share it). 2022.10 + 2023.04 hotfix + develop. |
| #1568149 (WWM 22-00874403) | **CFAUTOCONF** over-cuts confirmations when balancing interconnect | Pro-rate reduction defect on the has-key buys/sells. Code fix + unit test; cherry-picked 2022.04, 2022.10, develop. |
| #1371507 (TECO) | "Meter is not nominatable" misfires for most noms | **`maxRecordsToSelect` app.config reverted to 1,000,000 during upgrade** (should be 3,000,000) → not all location data cached → validation thinks meter absent. Fix the app.config (`TEC.QPTM.Application.MiddleTier`). Client-specific. |

---

## 10. Cluster G — Nomination upload / import (NNNOMLOAD / NOMIMPEXTS) failures
<a name="10-cluster-g"></a>

The ETC "Nomination Upload enhancement" (staging tables `NNSTAG_NOM_LOAD_ERROR` / `NNSTAG_ACTV_DTL`) spawned a tightly-linked defect family; plus the QPTM→TIPS `NOMIMPEXTS` import.

| Bug / SF | Symptom | Root cause & fix | Build |
|---|---|---|---|
| **#1664076** (ETC 24-00957669) | NNNOMLOAD errors on **unique constraint** when noms already exist (esp. a timely-only month with a multi-day range) | On submit-validate, the loader also validates day-1 noms with a subset effective day-10, and `CreateCycleOveridesForAnyNominationWithError()` re-adds a nom with the **same key (IdNom, GasDay, Cycle, TSP)** already in the DB → unique violation. Fix tied to #1664436. | client HF + develop (2024) |
| **#1664436** (ETC 24-00957668) | NNNOMLOAD throws **"Since last Retrieve, another user submitted noms… Please requery"** but **the nom still submits** | Re-work after reverting #1544800; loop over `cycleList` passed an unused cycleId; staging path. Fix the requery/merge logic. Reproduce by running the nom-delete script then NNNOMLOAD. | client HF + develop (2024) |
| **#1455439** (ETC) | Nom Upload enhancement **fails to populate `NNSTAG_NOM_LOAD_ERROR`** (integrity constraint); LI/BI errors stop the process | **Oracle vs MSSQL staging-table column-name drift** (`DN_RECORD_IND` Oracle vs `DN_RECORD_IN` MSSQL+code) so Oracle save failed; LI/BI errors threw integrity constraints. Fix the column name + make the DB script **rerunnable** (#1575393). Merged develop, 2022.10, 2022.04, 2021.10. | 2021.10 / 2022.04 / 2022.10 |
| **#1532428** (ETC 22-00268065) | Nom Upload **Process Queue ID not passed to NN12 Nom Error Report** | Enhancement: add optional PQID param to NN12; write `NNSTAG_ACTV_DTL`; filter NN12 by PQID instead of hard-coded `PROCESS_ID='NNNOMLOAD'` and `MAX(PROCESS_QUEUE_ID)` (unreliable with parallel TSP jobs). | Merged to 2022.10 |
| **#1692624** (HEP) | TIPS **NOMIMPEXTS** import fails: `System.OverflowException` (Syncfusion `PropVariant`), then **multi-SR/company restriction** | The overflow was the `.xls` format → **save as `.xlsx`** clears it. The remaining error ("Service Requester does not match the queried SR") is **by design**: the batch import **restricts to a single company AND service requestor** per file. | working-as-designed + xlsx |
| **#1706821** (HEP) | QPTM→TIPS nom integration: QPTM exports **CSV**, TIPS needs **xlsx with 2 header rows, mixed-case headers**, data starts row 3 | Fix: make **NOMIMPEXTS accept CSV directly** (no PowerShell xlsx conversion) and handle header-case/2-row template; also use UP/DOWN records (not just PATH) because HEP PNT rec≠del. **2024.04 hotfix** + develop. | **2024.04** |

**Fix recipe:** for NNNOMLOAD failures get the **exact error** — *unique constraint* (#1664076, key collision on re-add), *"please requery"* (#1664436, merge/requery), *integrity constraint / staging not populating* (#1455439, Oracle/MSSQL column drift, verify the staging table schema matches code in **both** vendors). For NOMIMPEXTS: **xlsx not xls**, and **one company+SR per file**.

---

## 11. Cluster H — Autogen (NNAUTOGEN / NNATGLF) & NNCALCFUEL
<a name="11-cluster-h"></a>

| Bug / SF | Symptom | Root cause & fix | Build |
|---|---|---|---|
| **#1710461** (ONK 25-01000534) | Autogen creates target-TSP storage nom with **wrong downstream BP** (contract holder Atmos instead of nom-agent Sequent) | `AutoGenRelatedNomFromExistingNom.cs` used **TSP 40 (source) instead of TSP 16 (target)** to resolve the agent; fix uses the existing `cacheTargetTsp` → assign to `delCtrAgentDO`. Inconsistent results during testing (services stepping on DEVB1). | ONK Apr-2025 HF (inferred) |
| **#1692472** (WWM 24-00984178) | Autogen generates **Activity IDs instead of target-TSP noms**; NN00003185/3180 throw on the target | **Bad cycle data: TSP 801 had overlapping dates for cycles 4 & 6** → "item with same key already exists" exception during validation (repro even with manual entry). Fix: (1) **data fix** (end-date/delete the duplicate 2016 rows) + (2) **code handles the duplicate-cycle case gracefully**. | WWM 11/1 HF (inferred) |
| **#1747677** (ONK) | New **DST/DSL imbalance-threshold autogen rules only process Timely cycle** | In the **Load-Following flow (NNATGLF)**, `RetrieveActiveCyclesByDay()` is never called, leaving `this.ActiveCyclesByDay` null → exception, only Timely worked. Fix: move `RetrieveActiveCyclesByDay()` into the second `DoExecute()` of `QNomAutoGenSeg.cs` so it runs for both NNAUTOGEN and NNATGLF. Also `AUTOGEN_TARGET_TSPS` TSP config triggers the null path. **Core code change; HOTFIX** tag. | ONK Aug/Oct-2025 HF; RELQA/TST verified |
| **#1442540** (ONG) | Autogen Setup screen flags **Contract Filters fields as required** when they shouldn't be | Validation requiring source TOS / Contract Attribute filters. Fix = hotfix **PR 57389 "Remove AutoGen validations requiring source TOS and Contract Attribute filters"** (client-specific metadata). | client HF (2022) |
| **#1460001** (ONK 20-00098967) | **NNCALCFUEL** resubmits noms / leaves downstream variance with no fuel-rate change | Long saga; ultimately the **rate cache wasn't refreshed** after a Rate-Maintenance change, so the batch saw stale fuel. Adding `RefreshEntireCache` worked but was a perf risk → fix put in **`QPTMRateService` (ServiceCore)** instead. Several sub-issues (NN12 collateral #1387566, NNBULKCOPY error #1657201). Note: NNCALCFUEL is **ONK-specific** (core analogue NNBULKCOPY). Ultimately **Rejected** — "refresh the cache and it works." | — (cache/ServiceCore) |
| **#166087** (ONG v17) | **NNCALCFUEL completes successfully despite nomination line errors**, new fuel rate not loaded | Process continued through LI errors (e.g. contract terminated). Client-specific fix isolated to `ONG.QPTM.Batch`. | ONG patch (2020) |

**Lesson:** autogen "wrong target" bugs are usually **source-vs-target TSP resolution** (#1710461) or **bad cycle/overlap data** (#1692472) or a **null `ActiveCyclesByDay` in the Load-Following path** (#1747677). NNCALCFUEL "not updating fuel" → **refresh the rate cache** before blaming code.

---

## 12. Cluster I — Nomination Submission screen behavior
<a name="12-cluster-i"></a>

| Bug / SF | Symptom | Root cause & fix | Build |
|---|---|---|---|
| **#1454476** (DTE 22-00257059) | Changing a **BA name** doesn't update on the nom screen; "fixing" it corrupted other noms (TEP collateral #1556881) | **BA name is part of `NNCTRL_NOM_HDR` and the `NOM_HASH_ID`**; just re-displaying the new name desyncs the hash. Products' decision: **only update the BA name on Copy** (DataObjectState='Added'), never on existing/Modified/Unmodified rows. Watch unit-test mocking on `QServiceContainer.GlobalInstance`. | develop / release / 2022.10 |
| **#1666979** (GNP 24-00956891) | On a submitted nom, after a failed 2nd change, **picklists become editable** on already-submitted rows | Editing Rec/Del Qty on a **Timely record creates a new overridden ID1/ID2/ID3 record with `DataObjectState='Added'`**, and the screen shows picklists for "Added" rows. Repro needs: a TIM record + retrieve on a non-TIM cycle + an error + Validate. Fix at QFC grid level (Bid Trans Rate was a dynamic `GridColumnActions` not a `GridColumnCommandBtn`). Note: changes never actually saved (validation blocks) — the **editable picklist itself** was the issue. | GNP 6/28/2024 HF (inferred) |
| **#1452323** (ONG 24-00952492) | Making an existing nom **Line Invalid then adjusting it deletes ALL other nom paths** | Validation-engine: the offending nom is **date-split into 2 ranges and only one range comes back** → others dropped. Deep in `PrivateValidateNominations`/`ValidateNominations`; required full Nom regression. **Fix only in GA 2025.10** (ONG upgrading to it) — **not hotfixed to older versions.** | **2025.10** only |
| **#1672104** (MOM 24-00962813) | Copy creates a nom with **BEG_GAS_DATE > END_GAS_DATE** (bad data); intermittent, not reliably reproducible | QPTM/TIPS Nomination Transaction copy. Added validation **NNG001/NNG031** ("Ending Gas Day must be ≥ Beginning Gas Day") to block bad inserts. **Recurrence #1769494 (ONM 25-01051919):** validation still not triggering on Copy because **`ShouldValidate` only checked `DataObjectState='Added'`** — Copy leaves state Unchanged → fix to validate on any non-Deleted state. 2024.04 + DEV. | 2024.04 (#1672104) / 2024.04 (#1769494) |
| **#1607098** (ONK 23-00907095) | Long nom **error message not wrapping** in V2UI grid (must widen column) | V2UI grid CSS. Fix: `td.data-field-textarea { white-space: normal!important; }` (always-expanded). 2022.10 through develop. | 2022.10 |
| **#1735885** (NMG 25-01024027) | Web dashboard 500: **"Unknown Widget Type: Quorum-QPTM-CycleChangesMvc.CycleChangesWidget"** | **On-prem `Web.Config` misconfig** — `SERVICE_BUS_CLIENT_CODE` / `SERVICE_BUS_ENVIRONMENT_NAME` wrong on the client's web server. Resolved by updating the config; **Rejected** (not a code bug). Deployment-config item. | — (config) |

---

## 13. Fix-Version Matrix
<a name="13-fix-version-matrix"></a>

> Build column: explicit release/patch where the dev thread stated it; **(inf)** = inferred from sprint iteration / cherry-pick notes — **confirm in release notes or the linked patch WI before promising a client**.

| Bug | Symptom (short) | State | Fixed-in-build | SF case | Client |
|---|---|---|---|---|---|
| #1737489 | NMQR null-ref (null TrackId), no response file | Closed | APL HF 2025 (inf) + develop | 25-01023837 | APL |
| #1606709 | EDINCOMING null-ref when TPA not found | Closed | 2025.10 (inf, 25.13) | — | core |
| #1736915 | EDI **outbound** null-ref when TPA not found | Closed | 2025.10 (inf, 25.13) | — | core |
| #1719226 | EDINCOMING null-ref (2025.04 regression) | Closed | not-repro / closed | — | core |
| #1735182 | EDIServ cache off wrong DUNS | Closed | 2025.10 (inf, 25.12) | — | core |
| #1725907 | EDIServ duplicate-TP → error not guess | Closed | 2025.10 (inf, 25.09) | — | core |
| #1710259 | EDIServ saves whole multipart form-data | Closed | 2025.04 (inf, 25.03) | — | core |
| #1772081 | `UTIL_RESYNC_SEQ` fails on "NA - EDISERV" | Closed | 2025.04+ (inf, 25.26) | — | NJR/core |
| #1672049 | GPG decrypt/timeout intermittent | Closed | QHPE metadata HF (config) | 24-00964519 | HPE |
| #1678265 | Outbound loc id: config gated all 3 datasets | Closed | ENT HF Aug-2024; QPTM 2020.03 | 24-00960415 | ENT |
| #1694083 | RQCF loc id collateral of #1678265 | Closed | ~2024.12/2025.04 (inf) | — | TEP |
| #1708573 | RRFC wrong interconnect for PT/displacement | Closed | 2025.04 + client 2022.04 HF (inf) | 25-00996583 | QTR |
| #1595439 | SQTS/NMST model U vs T (LC Nom screen) | Closed | TEP Patch 13 (2024.03) + develop | 23-00891839 | TEP |
| #1756196 | CRAN out missing ID3 N9*48 | Closed | 2025.10 (inf, 25.21) | — | multi |
| #1781005 | CROF out missing ID3 + batch error | Closed | **2025.10** + current + develop | 25-01060489 | QTR |
| #1799746 | FNAK sending NAESB 04010 not 7030 | Closed-Rejected | → Feature #1800045 | — | APL |
| #1764346 | MSIN missing QTY when no meas data | Closed | no fix (NAESB unconfirmed) | — | TEP |
| #1759474 | OACY missing all-location data | Closed | **2024.10/2025.04/2025.10** + 2024.04 HF | 25-01041261 | GBG |
| #1639014 | EDI cuts conf to 0 / ECRQR539 | Closed | CHN HF on 2020.09 (inf, DB scripts) | 23-00932772 | CHN |
| #1770476 | Manual RRFC SLN ≠ auto (CONF_TRK_ID null) | Closed | **2025.04 / 2025.10 / develop** | 25-01047182 | QTR |
| #1611244 | EDINSEG "no cycles open" non-std cycle IDs | Closed | CHN patch ~2023.04 (inf) | — | CHN |
| #1761680 | Sub-cycle Y→N after balancing into IDL | Closed-Rejected | enhancement (no fix) | — | EQC |
| #1522549 | Confirmation Cycle filter duplicates | Closed | 2023.04 (inf, 23.09) | — | core |
| #1757082 | PBBALCHAIN not applying EDI cuts to paths | Closed | HEP metadata HF 1/23/2026 (config) | 25-01037438 | HEP |
| #1730358 | NN00003010 not firing (eff-end-date) | Closed | **2025.04** (ETC) + develop | 24-00990212 | ETC |
| #1755248 | NN00003010 recurrence (+config) | Closed | core code change, cherry-picked | 25-01034998 | ETC |
| #1712405 | NN00009602 null OIA → no inv acct | Closed | Mar-2025 HF (inf) | 25-00999987 | HPE |
| #1726480 | NN00003072 segmentation MDQ | Closed | working-as-designed | 25-01009023 | HPE |
| #1775092 | NN00009965 AOS pool-to-pool / wrong row | Closed | **2026.04 / 2025.10** | 25-01041489 | WWM |
| #1712648 | NN00009965 leaked into core (all envs) | Closed | core remove; 17.27 HF (inf) | — | core/WWM |
| #1404268 | NN00003075 EUT MDQ not firing (TOS code) | Closed | client data + perf | 21-00207007 | DTE |
| #1609881 | NN00009015 late-nom miss 4 fields | Closed | 2024.04 RELQA (not hotfixed) | 23-00902666 | ETP/ETC |
| #1630769 | Import vs screen DUNS validation | Closed | feature (backed out) | 23-00928342 | GBG |
| #1610219 | Import accepts invalid TT for TOS | Closed | 2022.10 + 2023.04 HF + develop | — | CMX |
| #1568149 | CFAUTOCONF over-cuts | Closed | 2022.04/2022.10/develop | 22-00874403 | WWM |
| #1371507 | "meter not nominatable" misfire | Closed | app.config `maxRecordsToSelect` | — | TECO |
| #1664076 | NNNOMLOAD unique constraint | Closed | client HF + develop (2024) | 24-00957669 | ETC |
| #1664436 | NNNOMLOAD "please requery" | Closed | client HF + develop (2024) | 24-00957668 | ETC |
| #1455439 | Nom upload staging not populated | Closed | 2021.10/2022.04/2022.10 | — | ETC |
| #1532428 | NN12 missing PQID | Closed | 2022.10 | 22-00268065 | ETC |
| #1692624 | NOMIMPEXTS overflow / multi-SR | Closed | xlsx + by-design | — | HEP |
| #1706821 | QPTM→TIPS CSV nom import | Closed | **2024.04** + develop | — | HEP |
| #1710461 | Autogen wrong downstream BP | Closed | ONK Apr-2025 HF (inf) | 25-01000534 | ONK |
| #1692472 | Autogen makes Activity IDs (dup cycle data) | Closed | WWM 11/1 HF (inf) + data fix | 24-00984178 | WWM |
| #1747677 | DST/DSL autogen only Timely (NNATGLF null) | Closed | ONK Aug/Oct-2025 HF | — | ONK |
| #1442540 | Autogen Setup fields wrongly required | Closed | client HF (PR 57389) | — | ONG |
| #1460001 | NNCALCFUEL stale fuel (cache) | Closed-Rejected | ServiceCore cache | 20-00098967 | ONK |
| #166087 | NNCALCFUEL continues through LI errors | Closed | ONG patch (2020) | — | ONG |
| #1454476 | BA-name change / nom-hash desync | Closed | develop/release/2022.10 | 22-00257059 | DTE |
| #1666979 | Submitted-nom picklists editable | Closed | GNP 6/28/2024 HF (inf) | 24-00956891 | GNP |
| #1452323 | LI nom adjust deletes all paths | Closed | **2025.10** only | 24-00952492 | ONG |
| #1672104 | Copy → BEG>END bad dates (NNG001/031) | Closed | 2024.04 | 24-00962813 | MOM |
| #1769494 | #1672104 recurrence (ShouldValidate state) | Closed | 2024.04 + DEV | 25-01051919 | ONM |
| #1607098 | Long nom error not wrapping (V2UI) | Closed | 2022.10 | 23-00907095 | ONK |
| #1735885 | Unknown widget type (web.config) | Closed-Rejected | on-prem config | 25-01024027 | NMG |

---

## 14. Diagnostic Pointers
<a name="14-diagnostic-pointers"></a>

- **Always get from the user:** the **batch process name + Process Queue ID (PQID)**, the **exact error string** (COM/ORA/.NET), the **TPA ID + NAESB grammar version**, the **client + TSP + gas day + cycle**, and (for EDI) the **actual .edm/.dec file**. EDI bugs cannot be worked without the file (Zach's standing rule on #1611244).
- **Which log?** EDI runtime errors are usually **QPEC** errors → pull **GatherLogs** (`qtrace.QPTM.QPEC.*.segregated.log` in the Managed Steps folder), not just the EDIServ log (#1737489). Decrypt issues show in the QPEC log as GPG arg lines (#1672049).
- **Read the EDI file with the in-app Dataset Viewer / EDI Transaction Viewer**, not Notepad — easier to find the CS/NMT/N9 loops (Dianne's note on #1595439). Change the segment delimiter to line-feed to read it.
- **NAESB compliance gaps** (§6): confirm the **TPA grammar version** first; the missing element is required only at certain versions. The fix is in the versioned dataset class (`QEdi*Out18/30/31`), version-gated.
- **EDI cut-to-0 / ECRQR539** (§7): diff the **EDI file's SR# / BP-DUNS / nom-flow-code (`NomKFloCode`) / pkg** against the contract and the confirmation table. The "no matching confirmations" log line prints the exact filter.
- **Validation "not firing/firing wrong"** (§9): check **Validation Rule Assignment** (is the rule even assigned/overridable for PNT & PT?) before assuming a code bug — several "defects" were unchecked rules or WWM-only rules in core. For the rule's data dependency, check for a missing **TOS code tied to the rule** (#1404268) or null **OIA** (#1712405).
- **Nom upload** (§10): `.xls` Syncfusion overflow → save **.xlsx**; NOMIMPEXTS is **one company + one SR per file**; staging-table failures → verify the **Oracle vs MSSQL column names match the code** (#1455439).
- **Autogen** (§11): wrong target = **source-vs-target TSP** resolution; "Activity IDs not noms" / "item with same key" = **duplicate/overlapping cycle data** on the TSP; "only Timely" = `ActiveCyclesByDay` null in **NNATGLF** (Load-Following).
- **Nom screen oddities** (§12): "old BA name on copy" / "picklists editable" / "paths deleted" all trace to **`NNCTRL_NOM_HDR` + nom-hash** and **`DataObjectState='Added'`** on overridden/copied records.
- **Reproducibility warning:** a large share of these (especially intermittent EDI, copy-creates-bad-dates, sub-cycle flip) **could not be reproduced in CORE/DEV** — many were closed as not-repro, working-as-designed, or fixed proactively with null-checks. Don't assume "can't repro" = "no defect"; capture data cuts and logs while it's failing.

---

## 15. Key Code, Processes & Repos
<a name="15-key-code-processes--repos"></a>

### Processes / batch steps
| Process | Purpose | Notes |
|---|---|---|
| **EDINCOMING / EDINSEG / EDSPLITIN** | Inbound EDI file handler (decrypt → parse → confirm/nom → response) | Runs in QPEC; needs the encrypted file + TPA. §4/§7/§8 |
| **EDI G873/G874 … Outbound** (RQCF, RRFC, SQOP, NMST/SQTS, CRAN, CROF, MSIN, OACY) | Generate per-TPA outbound datasets | Versioned dataset classes; §5/§6 |
| **EDIServ** | WCF receiver/sender + TPA cache | Distinct from QPEC; §4 |
| **NNNOMLOAD** | Core nom upload (staging `NNSTAG_*`) | §10 |
| **NOMIMPEXTS** | Import noms from external source (QPTM→TIPS) | xlsx, 1 company+SR/file; §10 |
| **NNAUTOGEN / NNATGLF** | Autogen target-TSP noms (NNATGLF = Load-Following) | §11 |
| **NNCALCFUEL / NNBULKCOPY** | Re-apply changed fuel % (ONK / core) | §11 |
| **CFAUTOCONF / PBBALCHAIN / CFNOMSYNCH** | Confirmation auto-confirm / path balancing / nom-conf sync | §7/§8 |
| **RPT_NN12** | Nom Error Report (LI/BI) | PQID param; report-def vs process-def metadata must match per layer (#1712646, #1532428) |

### Code locations (cited in dev comments / PRs)
| Symbol / path | Repo | Cluster |
|---|---|---|
| `Quorum.QPTM.EDI.DataSets/G874NMQR/QEdiQRBase.cs` (`Sort`) | `Quorum.QPTM.Batch` | §4 null-ref |
| `Quorum.QPTM.EDI.DataSets/G873NMST/QEdiNMSTOut18.cs` (NMT U/T) | `Quorum.QPTM.Batch` | §5 |
| `QEdiCRANOut31` / `QEdiCROFOut18` (ID3 `N9*48`); `CreateHeaderN9_Intraday2RecallNotificationIndicatorSegment` | `Quorum.QPTM.Batch` | §6 |
| RRFC `LoadDataFromDB()` override | `Quorum.QPTM.Batch` | §7 |
| `QEdiDataCacheQPTM.cs` (EDIServ should mimic) | `Quorum.QPTM.Batch` / EDIServ | §4 |
| `QNomAutoGenSeg.cs` (`RetrieveActiveCyclesByDay`/`DoExecute`), `AutoGenRelatedNomFromExistingNom.cs`, `AutogenNNK.cs` | `Quorum.QPTM.Batch` | §11 |
| `QPSNomLoadSeg.cs` (Nom Load), `QNomLoadSeg` | `Quorum.QPTM.Batch` | §10 |
| `ActivityDetailDOExt.cs` (override-clear fields), `NominationSubmissionControllerBase.cs`, `NominationSubmission.js` (`addAddRecordIconToGrids`), `NominationDetailDOExt.cs` (RecBPNm/DelBPNm/nom-hash) | `Quorum.QPTM.Web` | §9/§12 |
| `RuleNN00003010` / `NN00009965` / `NN00009602` / `NN00003072` validation rules | `Quorum.QPTM.Web` `*ValidationRules*` | §9 |
| `InventoryManager.FindInvAcctIdTiedToContractByAndOIA()`, `InventoryCache.GetInventoryAccountHeaderByPrimaryCtrNoAndOIA()` | ServiceCore | §9 |
| `QPTMRateService` (ServiceCore) — fuel-rate cache | ServiceCore | §11 |
| `NNXREF_VALD_RULE_GRP_EFF_RULE` (rule assignment), staging `NNSTAG_NOM_LOAD_ERROR`/`NNSTAG_ACTV_DTL` | `Quorum.QPTM.Database` | §9/§10 |
| `QARCH_CNFG_CTRL` (EDI `PROCESS_TIME_OUT`), `QCODE_ED_VERSION` (NAESB versions), `PACTRL_TSP.DUNS_NO` | DB | §4/§7 |

### Repos & client overrides
- **`Quorum.QPTM.Batch`** — EDI datasets (`Quorum.QPTM.EDI.DataSets/`), nom load/autogen/fuel batch (`QPDllNominations`).
- **`Quorum.QPTM.Web`** — Nomination Submission/LC Nom screens, validation rules, V2UI grid.
- **`Quorum.QPTM.Database`** — core SQL/metadata, rule assignment, staging tables (watch **Oracle vs MSSQL** column drift).
- **`<CLIENT>.QPTM.*`** — client overrides: `ENT`, `TEP`, `CHN`, `ONK`, `ONG`, `WWM`, `QTR`, `HEP`, `GBG`, `DTE`, `TECO`, `CMX`, `NMG`, `EQC`, `APL`. Examples: `TEC.QPTM.Application.MiddleTier/app.config` (#1371507), `QHPE.QPTM.Metadata` (#1672049), `ONG.QPTM.Batch` (#166087), `*.QPTM.Metadata` (TPA grammar / config). **Check the client repo/layer first** — many of these are client-specific or pre-Fluent-Migrator (CHN needs explicit DB scripts).

---

## 16. Escalation Guidance
<a name="16-escalation-guidance"></a>

**Route to Engineering (Software Defect) when:**
- A null-ref/exception in EDI processing from a code gap: null `TrackId`→NMQR `Sort` (#1737489), TPA-not-found null-ref (#1606709/#1736915), RRFC `LoadDataFromDB` override (#1708573), autogen `ActiveCyclesByDay` null in NNATGLF (#1747677), autogen source/target TSP (#1710461), validation-engine date-split dropping paths (#1452323).
- A **NAESB-required outbound segment is missing** and the field *is* required at the TPA's grammar version (ID3 `N9*48` #1756196/#1781005; OACY group roll-up #1759474). Provide the **TPA NAESB version, the dataset, and the expected vs actual file**.
- A validation provably reads the wrong field / wrong row on correct config (#1775092 AOS, #1712405 null-OIA, #1730358 begin-day-only, #1609881 missing override fields).
- Provide: **batch process + PQID + exact error**, client + TSP + gas day + cycle, the contract/SR, the **EDI file**, and a repro. Confirm fix availability against the **linked patch WI / release notes** (IntegrationBuild is empty here).

**Handle as Configuration / Cloud-Ops (no core code) when:**
- **GPG decrypt/timeout** → file-share + `EDI/PROCESS_TIME_OUT` global config + QPEC restart (#1672049).
- **EDIServ wrong/duplicate TP** → fix the **TPA setup/DUNS** (the code now errors on duplicates, #1725907).
- **Outbound loc id wrong** → confirm `USE_INTERCONNECT_LOC_FOR_*` config **and TPA NAESB version ≥ 3.0** before code (#1678265/#1694083).
- **EDI cut-to-0 / ECRQR539** → fix the **SR# / BP-DUNS / nom-flow-code / pkg mismatch** in the file or contract (#1639014).
- **CROF batch error** → add the missing **CRNS grammar config in TPA Maintenance** (#1781005).
- **PBBALCHAIN behaves per-TSP** → diff **TSP configs** / missing BA in QPECUSER (#1757082).
- **Unknown widget type / on-prem 500** → fix `Web.Config` `SERVICE_BUS_*` (#1735885).
- **"meter not nominatable" misfire** → `maxRecordsToSelect` in client MT `app.config` (#1371507).
- **Autogen Setup required-field / NNCALCFUEL stale fuel** → metadata / refresh the rate cache (#1442540, #1460001).

**Handle as Data fix when:**
- **Autogen duplicate/overlapping cycle data** on a TSP (#1692472), **NNNOMLOAD unique-constraint** key collisions (#1664076), **NMST model U→T** on existing `NNCTRL_NOM_HDR` (#1595439 — go-forward code + script for old data), **Oracle/MSSQL staging column drift** (#1455439). Always verify-SELECT in a transaction.

**Expect "not a defect / can't reproduce" when:**
- Segmentation MDQ (#1726480 — Location Path setup), import-vs-screen DUNS (#1630769 — feature), MSIN-no-data (#1764346 — NAESB unconfirmed), sub-cycle Y→N (#1761680 — enhancement), FNAK version (#1799746 — feature), NNCALCFUEL (#1460001 — cache refresh). Verify config and reproduce in CORE before escalating; capture data cuts + logs while it's failing.

---

*Skill created: 2026-06-14 from ADO QPTM Nominations/EDI bugs.*
*Evidence: WIQL matched 916 closed/resolved Bugs (area paths Energy Transportation + Maintenance\Midstream and Transportation; functional title filter); 250 field-triaged; 57 deep-read with full comment threads. Cited ADO bugs: #1737489, #1606709, #1736915, #1719226, #1735182, #1725907, #1710259, #1772081, #1672049, #1678265, #1694083, #1708573, #1595439, #1756196, #1781005, #1799746, #1764346, #1759474, #1718572, #1639014, #1770476, #1611244, #1761680, #1522549, #1757082, #1730358, #1755248, #1712405, #1726480, #1775092, #1712648, #1404268, #1609881, #1630769, #1610219, #1568149, #1371507, #1664076, #1664436, #1455439, #1532428, #1692624, #1706821, #1710461, #1692472, #1747677, #1442540, #1460001, #166087, #1454476, #1666979, #1452323, #1672104, #1769494, #1607098, #1735885.*
*Caveats: IntegrationBuild empty on all bugs → fixed-in-build values inferred from comment threads / cherry-pick notes / sprint iteration, marked (inf) where uncertain — confirm in Quorum.QPTM release notes / linked patch WIs. Maintenance area branch is mixed QPTM+TIPS; ~17 TIPS-genuine items dropped; "Bulk Edit" false-positives (matched 'edi' substring) excluded. Companion: SKILL_EDI_Troubleshooting.md, SKILL_QPTM_Nomination_Validation.md, SKILL_Cycle_Deadline_Reference.md, REPO_REFERENCE.md.*
