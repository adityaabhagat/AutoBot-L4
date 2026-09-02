# SKILL: QPTM Confirmations / Scheduling / CAS — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management)
**Source:** Azure DevOps **Bugs** (Closed/Resolved) under area paths `QuorumSoftware\Engineering\Energy Transportation` **and** `QuorumSoftware\Engineering\Maintenance\Midstream and Transportation`, filtered to the Confirmations / Scheduling / CAS functional area (CAS, prelim cut, CFAUTOCONF, PBBALCHAIN, path balancing, RQCF, EPSQ, ratcheting, Confirmation Response, CANOMCLTG, scheduling capacity override).
**Use When:** an L4 engineer needs the ROOT CAUSE + fix-build + workaround for a QPTM scheduling/confirmation defect, or needs to tell whether a "cut is wrong / autoconf overcut / balancing didn't run / conf screen slow / EPSQ not enforced / RQCF file failed" ticket is a known bug, a config issue, or expected behavior.

> **Evidence base.** WIQL matched **536** bug ids on the title terms. After dropping cross-product noise (TIPS settlement/billing ≈23, **QLNG Cargo "Scheduling Detail"** ≈43, and substring false-positives where "CAS"→case/cash, "cut"→cut**off**/cut**over**/exe**cut**e, plus generic RCA/report/billing items ≈228), **≈242** are genuine QPTM Confirmations/Scheduling/CAS bugs. This skill **deep-read 47** representative bugs (Description + ReproSteps + linked PRs + the full dev **comment threads**, which carry the root cause and fix decision). Every root-cause claim below cites the ADO bug id and (where present) the linked Salesforce case (`YY-xxxxxxxx`). **IntegrationBuild is empty on every one of these bugs**; fix-builds below are **inferred** from iteration path (YY.NN → release) and tags ("Merged to 2022.10", "TEP Deployed", "2021.04 QA") and are marked **(inferred — confirm in QPTM release notes / the PR target branch)**.

> **Overlap caveat.** The `Maintenance\Midstream and Transportation` branch is **mixed QPTM + TIPS**. The functional terms here are mostly QPTM, but "CAS" and "cut" are noisy. When triaging an unfamiliar id, confirm it is QPTM (TSP / nomination / confirmation / CAS / contract path vocabulary) and not TIPS (settle / journal / plant / fixed fuel) or QLNG (cargo / tanker / discharge terminal). Allocation / cashout / imbalance / billing bugs that merely *contain* "cut" belong to the **QPTM Allocations/Imbalance** skill, not here.

---

## 1. Quick Triage Table

| Symptom (what the customer reports) | Likely cluster | First check |
|---|---|---|
| `CFAUTOCONF` / AutoConfirmation **cuts an interconnect nom to 0** or **overcuts** a meter on a *different* TSP | **§4** AutoConf interconnect | `GetInterconnectLocations`/`MatchRelatedConfirmations` matches ALL IC-attribute locations sharing a DRN across **all** TSPs; check DRN match + IC attribute + `ONLY_AUTO_CONFIRM_LEASE` / `LEASE_NOM_CONFIRM_ACROSS_TSPS` configs |
| **Prelim Cut on CAS Maintenance reduces wrong rows / not balancing / extra cuts after PBBALCHAIN** | **§5** CAS balancing | The core balancing engine `NomDetailBalancingHelper_Impl_Core.cs` (#1317128 rewrite). Verify the client build has the #1317128 family fix; reproduce with a small cut first |
| **"Ratcheting error" when submitting a prelim cut** (esp. TEP/Whitewater, intraday) | **§6** Ratcheting | Collateral from #1317128 ratchet-qty accumulation lines (#1601901). Workaround: apply EPSQ overrides; confirm the #1601901 revert PRs are in the build |
| **PBBALCHAIN does not run after a Conf Response cut**, or runs but result differs from CAS | **§7** PBBALCHAIN | TSP config `CONF_UPD_CALL_BALANCING_AFTER`; param 26902 "Run PBBALCHAIN?". CAS balancing and PBBALCHAIN use *different* path-matching logic by design |
| **Confirmation Response screen slow (45s–3min) after Submit**, large gas day (1500+ recs) | **§8** Conf Response perf | `CONF_UPD_CALL_BALANCING_AFTER=1` makes the screen wait for `CFPSTRESP`; new config `CONF_WAIT_FOR_POST_RESPONSE`; `SendConfSubmitNotifications` cost; the `IX8_CFCTRL_CONF` index |
| **Confirmation Response grid empty / "Object reference" on submit / "unknown confirmation level"** | **§9** Conf Response correctness | `TranslateBoolToYesNoCode`/`IsConfSubCycleRecDelYorN` (#1675663); web vs classic security id `QVPSOACONFIRMATIONRESPONSE`; Object Usage validations |
| **EPSQ not enforced on prelim cut** / EPSQ not populating / decimals | **§10** EPSQ | EPSQ is checked in `SetReduceRecEngQty`/`SetReduceDelEngQty`; ratcheted vs unratcheted view; `EPSQCALC` ran? `PASTAG_EPSQ_CALC_INPUT` stale data; `EPSQ_STG_PURGE_IND` |
| **RQCF outbound file fails / no RRFC received / sends Location ID instead of Interconnect ID** | **§11** RQCF/EDI conf | `USE_INTERCONNECT_LOC_FOR_RQCF`/`_RRFC`/`_SQOP` config (regression #1678265→#1694083); EDIServ set up; EDIDev installed on server |
| **Inbound EDI (RQCF) cuts a confirmation to 0 / "ECRQR539 no corresponding nomination"** | **§11** RQCF/EDI conf | NAESB version mismatch (3.1 vs 3.2), SR/contract mismatch in file, PT-nom outbound grouping (`CFSegmentWriter.cs`) |
| **CANOMCLTG (nom classification) fails or runs long when retrieving CAS Maintenance** | **§12** CANOMCLTG | Duplicate `KCTRL_CTR_LOC` rows / invalid Cap Type for TSP (setup); MT cache-miss re-index perf; DB-vs-MT version drift |
| **CAS Maintenance screen: error retrieving / duplicate dictionary key / UI broken / slow** | **§13** CAS screen | Usually route-path / segment setup; cache; web graph control regressions |
| Cut order by trans-group / "new flowing not cut to zero first" / "pathing by rank" | **§14** Expected behavior | All-in-to-all-out / beneficial-gas (Tallgrass SIR 117839); these are usually **working as designed** |

---

## 2. Concepts & Pipeline (Quorum/QPTM vocabulary)

```
[Nominations: NNCTRL_NOM_HDR/_DTL]
   │  (CANOMCLTG = Nom Classification & Trans Grouping — indexes noms into scheduling objects/segments)
   ▼
[CAS Maintenance]  — scheduler enters a Cap Qty + "Prelim Cut" on a Segment/Location
   │  Prelim Cut → CAS balancing (NomDetailBalancingHelper_Impl_Core.cs) writes CACTRL_NOM_DTL / CFCTRL_CONF
   ▼
[Confirmation Response]  — manual confirm/cut a meter; Submit kicks off CFPSTRESP
   │  CFPSTRESP → (if CONF_UPD_CALL_BALANCING_AFTER) → PBBALCHAIN (path balancing across the path chain)
   ▼
[CFAUTOCONF]  — auto-confirms intercompany/interconnect noms across TSPs (DRN-matched IC locations)
   │
   ▼
[EDI outbound: RQCF / RRFC / SQOP]  via EDIServ to trading partners
```

- **CAS** = Capacity Allocation Scheduling. The **CAS Maintenance** screen (Screens → Scheduling → CAS Maintenance) is where schedulers do **Prelim Cuts** by Segment or Location. Retrieving it offers to run **CANOMCLTG** ("hit Yes").
- **Prelim Cut** = a preliminary capacity reduction; the engine then **balances** the cut across the path (rec ↔ pool ↔ del) and assigns reduction reasons.
- **CAS balancing vs PBBALCHAIN** — two *separate* implementations. CAS Maintenance has its own lightweight balancing in `NomDetailBalancingHelper_Impl_Core.cs`; the **PBBALCHAIN** batch process ("Balance Chain") balances the full path chain. **By design they don't follow identical rules** (#1594942): CAS balancing does "look for the UP, else the PATH"; PBBALCHAIN can rank an entire combined up/path list. When CAS leaves paths out of balance, PBBALCHAIN cleans up afterward — if PBBALCHAIN is making lots of extra cuts, CAS balancing produced wrong numbers (the #1317128 problem).
- **CFAUTOCONF** = Automatic Confirmation of Intercompany Nominations. Confirms locations flagged with the **Interconnect** attribute that share a **DRN** (interconnect DRN) across TSPs. Driven by configs `ONLY_AUTO_CONFIRM_LEASE`, `LEASE_NOM_CONFIRM_ACROSS_TSPS`. Also run inside `CFENDOFNN3` (end-of-nom-cycle).
- **PBBALCHAIN** = Path Balancing chain process; balances cuts across paths and stamps reduction reasons (CBL=Contract Balancing, PBL=Pipeline Balancing, CPR=Confirming Party Reduction, PBR/PBD=Path Balancing Rec/Del). Configs: `PB_STAMP_SPECIFIC_REDUCTION_REASON` / `PB_SCRN_SPECIFIC_REDUCTION_REASON` (cut-code directionality, ONEOK-origin), Path Tolerance param, Gas Day Offset param.
- **EPSQ** = Elapsed Pro-rata Scheduled Quantity (NAESB). `EngQty × (remaining hours/24) + EPSQ` etc. Computed by the **EPSQCALC** job into `PASTAG_EPSQ_CALC_INPUT`/the EPSQ tables; **EPSQ Maintenance** screen shows/overrides it. CAS prelim cuts should not cut a nom **below EPSQ** (in the unratcheted view).
- **Ratcheted vs Unratcheted** — intraday capacity views. Ratcheted Qty = `(24×(EngQty−EPSQ))/remaining hours`; Unratcheted Qty = `(EngQty×(remaining hours/24)) + EPSQ`. The CAS Summary "Capacity Qty" is a **ratcheted** value, so below-EPSQ values are normal in the ratcheted intraday view but should not appear in the unratcheted view.
- **CANOMCLTG** = batch nom classification + trans-grouping; indexes noms into scheduling objects and trans groups using `KCTRL_CTR_LOC`, Nom Classification Maintenance & Classification Rule Set setup.
- **RQCF / RRFC / SQOP** = NAESB EDI: RQCF (request for confirmation outbound), RRFC (received reply), SQOP (scheduled quantity outbound). `EDRQCFOUT`/`EDI G873RQCF Outbound` is the outbound batch; `EDINCOMING` ingests inbound; **EDIServ** is the service that physically sends/receives files (needs **EDIDev** installed on the server).
- **Key tables:** `CFCTRL_CONF` (confirmations), `CACTRL_NOM_DTL` (CAS nom detail), `NNCTRL_NOM_HDR`/`_DTL`, `NNCTRL_NOM_LATEST_CYLE` (AVG_FLOW_REC/DEL used for ratcheting), `PATRAN_PATH_UNSOLD_CAP`, `PACTRL_LOC_PATH`, `KCTRL_CTR_LOC`.
- **Key code:** `Quorum.QPTM.Batch` (CFAUTOCONF in `QAutoConfSeg.cs`; PBBALCHAIN), `Quorum.QPTM.Web` + `Quorum.QPTM.Web.Controllers` (CAS Maintenance, Confirmation Response, EPSQ Maintenance), `NomDetailBalancingHelper_Impl_Core.cs` (CAS balancing — core), `Quorum.QPTM.Scheduling` (`BatchNomClassificationHelper` for CANOMCLTG), `QPSAllPathUnsoldCapDetermination.cpp` (classic, unsold cap). Many fixes have **client overrides** (`DTE.QPTM.Web`, `TEP.QPTM.*`, etc.).

---

## 3. Decision Tree

```
QPTM Confirmations / Scheduling / CAS case
│
├─ AUTO-confirm process (CFAUTOCONF / CFENDOFNN3) cut something wrong?
│   ├─ Cut a meter on a TSP you didn't run, or interconnect → 0           → §4  (DRN-matched IC across ALL TSPs; #1377828/#1396176/#1568149)
│   └─ Process FAILS ("record modified", duplicate)                        → §4/§12 (concurrency / duplicate index data)
│
├─ A PRELIM CUT on CAS Maintenance is wrong?
│   ├─ Cuts wrong rows / extra cuts appear after PBBALCHAIN / fuel wrong   → §5  (CAS balancing engine #1317128)
│   ├─ "Ratcheting error" pop-up blocks the cut                             → §6  (collateral #1601901; workaround = EPSQ overrides)
│   ├─ Cuts below EPSQ / doesn't stop at EPSQ                               → §10 (ratcheted vs unratcheted view; usually expected)
│   ├─ Two-party / pool path one side not cut                              → §5  (#1547198 PT-through-pool)
│   └─ Cut order by trans-group / new-flowing-first / by rank "wrong"      → §14 (beneficial-gas / all-in-to-all-out = EXPECTED)
│
├─ PBBALCHAIN process?
│   ├─ Didn't run after a Conf Response cut                                → §7  (CONF_UPD_CALL_BALANCING_AFTER / param 26902 asInt vs asBool)
│   ├─ "Recut to EPSQ unexpectedly" on pool / contract balancing          → §7  (usually EXPECTED — pool/contract key balancing; #1629945)
│   ├─ Slow / memory-limit exit (~750MB)                                   → §7  (QPEC memory; reduce scope; not always reproducible)
│   ├─ Path-Tolerance decimals truncated in Web                           → §7  (#1580134 QFC numerictextbox format)
│   └─ Warning "PB_SCRN_SPECIFIC_REDUCTION_REASON not found, default 0"   → §7  (missing config key; add & set 0; #1816122)
│
├─ Confirmation Response screen?
│   ├─ Slow on Submit (large gas day)                                      → §8
│   ├─ Grid empty / object-reference / unknown level / sort/columns       → §9
│   └─ Sub-Cycle Y flips to N after balancing / confirm above nom         → §9/§14 (often expected or Object-Usage config)
│
├─ EPSQ (maintenance / override / calc / columns)?                         → §10
│
├─ EDI confirmation (RQCF / RRFC / SQOP / EDINCOMING)?                      → §11
│
├─ CANOMCLTG (nom classification) fails/long when retrieving CAS?          → §12 (duplicate KCTRL_CTR_LOC / invalid Cap Type / cache / version drift)
│
└─ CAS Maintenance screen UI (retrieve error, dup-dictionary-key, graph)   → §13
```

---

## 4. Cluster A — CFAUTOCONF / AutoConfirmation cuts across TSPs (HIGH IMPACT)

**Symptom.** AutoConfirmation (CFAUTOCONF, also run inside `CFENDOFNN3`) **cuts an interconnect nomination to 0**, or **overcuts** a shipper, or cuts a meter on a TSP the process wasn't run for. Recurrent after-hours criticals for ENT, WWM, QTR.

**Root cause (from the #1377828 thread — the canonical RCA).** The method that gathers interconnect locations (`GetInterconnectLocations`, used by `MatchRelatedConfirmations()`) **does not filter on the TSP the process was run for, nor on TSP effective date**. It grabs *all* locations with the **Interconnect attribute = true (across every TSP)** and then any of those that **share a DRN** (e.g. A809/TSP630 shares DRN DC809 with C809/TSP688), so running CFAUTOCONF for TSP 30051 still cuts A809 on TSP 630 (#1377828, SF 21-00106474, EPCO/ENT). The match also requires Up/Dn BP and Up/Dn contract to align like pool balancing (`MatchRelatedConfirmations`). When the data elements don't truly match, the IC nom is cut to 0 (#1396176 WWM; #1783681 QTR 26-01080193). Product repeatedly concluded the *behavior* is "working as coded" and any TSP-scoping is a **new requirement / enhancement** (#1377828, #1429349, #1716241) — i.e. these are frequently **not** core bugs but design gaps + setup.

**Fixes / dispositions.**
- **#1568149 (WWM, SF 22-00874403)** — *real overcut bug*. AutoConf overcut when cutting **above** a lower-ranked nom (the `ProRateReduction` over-reduced by the buy/sell delta). **Fixed** via PRs **78586, 79320, 79321, 79322** + unit test, cherry-picked to **2022.04, 2022.10, develop** *(inferred fix-build 2022.04/2022.10 — confirm in release notes)*.
- **#1377828 (ENT, SF 21-00106474)** — closed as **enhancement/feature** (TSP-scoped autoconf), not patched as a bug. Workaround offered = **end-date** the offending IC location's DRN so it stops matching.
- **#1396176 (WWM)** — resolved by **re-entering the Confirmation Plan / Level records** (config/data), and ensuring the receipt location isn't also flagged Interconnect. No code change.
- **#1429349 (WWM UBT)** — "record was modified by …" failure → traced to `GetResponseConfirmations` returning the **same nom id twice** (both `bProcessUpRecord` and `bProcessDnRecord` true) for a meter-bounce-at-interconnect setup the system isn't designed for. Closed as **invalid business case / enhancement**.
- **#1716241 (QTR MWP)** — CFAUTOCONF "not updating quantities after a cut" → **config**: QTR's `ONLY_AUTO_CONFIRM_LEASE`/interconnect-DRN settings caused non-lease noms to be ignored; DRNs didn't match. Closed Rejected (config/enhancement).
- **#1783681 (QTR, SF 26-01080193)** & **#1789219 (WWM, SF 26-01087210)** — production criticals where aligning deadlines caused **balancing + AutoConf overlap → crash + duplicate noms**. Resolution was **operational** (disable autoconf, remove true duplicates from `NNCTRL_NOM_DTL`, restore deadline offsets); **no reliable script** to isolate "bad" vs legitimately-similar noms. Engineering explicitly declined to delete records grouped only by similar business attributes.

**Workaround / triage recipe.** Get the **gas day, cycle, and TSP the process was run for**, plus the cut meter. Query `CFCTRL_CONF WHERE REC_CONF_METH_CD='AUT' OR DEL_CONF_METH_CD='AUT'`. Check: (1) the cut location's **Interconnect attribute** and its **DRN** — does another TSP share that DRN? (2) `ONLY_AUTO_CONFIRM_LEASE` & `LEASE_NOM_CONFIRM_ACROSS_TSPS` (both usually 0). (3) Do the matched noms' Up/Dn BP & contract actually align? If the cut is "correct given DRN match," it's the design gap (enhancement). For overcut-above-lower-rank, confirm the #1568149 fix is in the build.

**Bug IDs:** 1568149, 1377828, 1396176, 1429349, 1716241, 1783681, 1789219. **SF:** 22-00874403, 21-00106474, 26-01080193, 26-01087210. **Clients:** WWM, ENT/EPCO, QTR.

---

## 5. Cluster B — CAS prelim-cut balancing engine (CAS cuts not balancing) (FOUNDATIONAL)

**Symptom.** A prelim cut on CAS Maintenance produces wrong results: cuts rows that shouldn't be cut, leaves paths out of balance so **PBBALCHAIN afterward makes a lot of extra cuts**, fuel applied to paths that shouldn't have fuel (sometimes huge), or the cut absorbs on the wrong (rec vs path) location. "CAS not cutting correctly / cutting below capacity / overcutting."

**Root cause.** The CAS Maintenance balancing logic lives in **`NomDetailBalancingHelper_Impl_Core.cs`** (with historical Core↔client *dual maintenance*, e.g. a DTE override). It is described by its own author as **"brittle."** The landmark fix **#1317128 (DTE, SF 21-00106465 — "CAS Cuts Not Path Balancing")** was an **entire rewrite** of that helper: it (a) made CAS balancing produce correct numbers so **no further PBBALCHAIN cuts are needed**, (b) fixed the Prelim-Cut error dialog (reduction qty exceeding buys total when a path cut to 0), (c) corrected handling of cuts **below EPSQ**, and (d) **removed the Core/DTE code duplication** (added targeted core hooks). Verified with new unit tests and regression against **ONK, ENT, APL**.

**Fix / fix-build.** #1317128 merged via PRs **52378/52379 (Core + DTE 1/2 & 2/2), 52584, 52594, 52608, 52632, 52816, 52838**. Tags: "Merge Completed". It was hotfixed to DTE's **2019.09 (17.x)** line and merged forward to **2020.09, 2021.04, develop** *(inferred — confirm in release notes / PR target branches; HF tracked under #1352575)*. **This is the baseline every later CAS-balancing fix builds on** — if a client predates it, expect CAS-balancing symptoms.

**Related defects in the same engine:**
- **#1547198 (WWM) — PT-through-pool not balancing.** A two-party PT (title transfer) transaction `REC → POOL → DEL`: the delivery is cut but the **receipt upstream of the pool is not**. Root cause: in `BalanceAllPath`/`ApplyReducedQty`, for PT noms `TotalReducedRatchQty` is already non-zero so the code thinks the noms are already reduced and never links the two sides (PNT worked, PT/PT and PT/PNT didn't — there was even an `[Ignore]`'d 2021 unit test admitting "Reductions on PT noms balancing across title transfers does not appear to be supported"). **Fixed** PRs **76922, 77945, 78000, 78001**; **merged to 2022.10** (tag "Merged to 2022.10") *(inferred fix-build 2022.10)*. Requires the **Pooling** + **Allow Title Transfer** location attributes to reproduce.
- **#1594942 (TEP, SF 23-00883026) — "CAS Balancing does not follow same rules as PBBALCHAIN."** Confirmed: CAS balancing explicitly does `if (up exists) ReduceBuyOrSellUsingPath(up) else if (PoolBalanceAllInToAllOut) … path`, whereas PBBALCHAIN can rank a combined up/path list — **so a CAS prelim cut absorbs on a rec loc (45222) instead of the intended path loc**. Isolated to the **Prelim Cut** step. **Fixed** PRs **97002/97003/97004** *(inferred ≈2024.x — confirm)*. Blocked for a long time behind the ratcheting issues #1640320/#1645462/#1627184 (you often must clear ratcheting first).
- **#1567788 (QTR, SF 22-00873647) — "CAS cutting below capacity"** at Clay Basin (sched qty cut lower than the entered cap). **Not reproduced** in DEV; self-corrected when inventory was re-run; closed for lack of a repeatable example. (Treat as monitor-and-capture-another-example.)
- **#1575085 (BWP, SF 23-00881417) / #1559325 / #1559335 (BWP) — "CAS Not Cutting Correctly / Hall Summit / Perryville."** Mostly insufficient-info / data-dependent; closed Rejected or rolled into the engine work. Verify against the #1317128 baseline first.

**Workaround / recipe.** Reproduce with a **small cut** first — small cuts often balance fine while large cuts expose the engine. Confirm the client's build includes the #1317128 family and (for pool/PT) #1547198. Check `ENABLE_CAS_PATH_BALANCING` and `AUTO_BALANCE_IND` (web passes Auto Balance Ind; classic doesn't — classic was historically a workaround, but web/classic share the same balancing MT call so it usually won't help, per #1317128). After any prelim cut, run **CANOMCLTG → CFPSTRESP → PBBALCHAIN** and check `RPT_NN01` for left-over imbalance.

**Bug IDs:** 1317128, 1547198, 1594942, 1567788, 1575085, 1559325, 1559335, 1618202, 1325693. **SF:** 21-00106465, 23-00883026, 22-00873647, 23-00881417/419. **Clients:** DTE, WWM, TEP, QTR, BWP (+ regression on ONK/ENT/APL).

---

## 6. Cluster C — Ratcheting errors on prelim cut (collateral of the §5 rewrite)

**Symptom.** Submitting a prelim cut through CAS throws a **ratcheting error** that blocks the cut (esp. TEP intraday, Whitewater). Or (#1552981) the **ratcheted tabular view classifies all volume as New Flowing** for ID cycles (should be only the increase). Or (#1716916 HPE) CAS attempts to **reduce by a ratcheting quantity during the Timely cycle** (it shouldn't).

**Root cause.** Two distinct causes:
1. **#1601901 (TEP, SF 23-00901305) — ratcheting error on submit.** This is **collateral from the #1317128 rewrite**. The dev isolated it to **two lines** of ratchet-qty accumulation in `NomDetailBalancingHelper_Impl_Core.cs`:
   - new (broken): `dPathReduceByRatchQty += dReduceByRatchQty - dReducedRatchQty + oAssocNomDtlGrp.TotalReducedRatchQty;` (and the UnRatch equivalent)
   - old (correct): `dReduceByRatchQty -= dReducedRatchQty;` (and UnRatch)
   **Fix = revert those two lines.** PRs **89139/89140/89141**, plus **90167**; merged **2022.10 and up** *(inferred fix-build 2022.10 — confirm)*. Flagged "risky" because it reverts a piece of #1317128, so QA must re-run the full #1317128 regression (#1621185 logged for that). This bug **blocks** #1594942 — clear ratcheting first.
2. **#1552981 (WWM, SF 22-00291615) — all volume classified as New Flowing on ID ratcheted view.** Root cause: the CAS screen uses the **previous-cycle qty** (`AVG_FLOW_REC/DEL` from `NNCTRL_NOM_LATEST_CYLE`) to split new vs flowing; that value was **0 because `EPSQCALC` had not been run since 4/28/2022** (it's supposed to run inside `NNPSTCREAT`). So it's an **EPSQ-staleness / process-sequencing** problem, not a pure code bug. Fix = run EPSQCALC; the screen then classifies correctly.

**#1716916 (HPE, SF 25-01007363)** — "CAS reducing by ratcheting qty in Timely." Resolved via **location path maintenance / config change** (no core code); the unratcheted qty was abnormally high due to setup. Closed by client confirmation.

**Workaround.** When a ratcheting error blocks a prelim cut, **apply EPSQ overrides** on the affected location to get past it (Zach Koontz's documented workaround in #1594942). Verify `EPSQCALC` has run for the gas day (drives the new/flowing split). Confirm the #1601901 revert is in the build.

**Bug IDs:** 1601901 (+ duplicates 1627184, 1633392, 1640320, 1645462 = "CAS 1–5"), 1552981, 1716916, 1713154. **SF:** 23-00901305, 22-00291615, 25-01007363. **Clients:** TEP, WWM, HPE.

---

## 7. Cluster D — PBBALCHAIN (path balancing process)

**Symptom & root cause by signature:**

| Signature | Root cause | Disposition / fix |
|---|---|---|
| **PBBALCHAIN doesn't run** after a Conf Response cut (cut not balanced) | `CFPSTRESP` step `PBBALMON1` reads the "Run PBBALCHAIN?" param **26902** as `-1`; collateral from #164234 which changed numeric params to boolean but left `asInt()` calls that should be `asBool()` | **#222984** (2020.09) — fixed: changed `asInt()`→`asBool()` for the affected params; PR #34739 *(inferred 2020.09)*. Driven by TSP config `CONF_UPD_CALL_BALANCING_AFTER` |
| **PBBALCHAIN "recuts" a nom to EPSQ / cuts pool to 0** when you reset a Conf Response record | **Working as designed** — contract/pool balancing uses contract-based keys; for a pool location with no flip-side ("FROM ATP" but no "TO ATP") it balances to the 0-qty side | **#1629945 (APL)** — closed **not a bug**; doc "PBBALCHAIN Pool Cut" attached explaining pool setup needed for correct cuts |
| **PBBALCHAIN excessive runtime / cancels after >1hr** | QPEC **memory limit** exit ("QPEC is using 759MB, limit is 750MB … possible memory leak [PBBALCHAIN]") | **#1613950 (TEP, SF 23-00907675)** — **not reproducible**; stopped occurring; closed. Monitor QPEC memory; reduce scope (gas day / all-paths indicator) |
| **Path Tolerance param truncates to 2 decimals in Web** (classic keeps all) | QFC web **NumericTextBox** format set to `"n"` (culture default 2dp) instead of `n3`/`n8` — affects *any* floating-point process param in web, not just PBBALCHAIN | **#1580134 (CMX)** — short-term QFC fix hard-coding 8 decimal places + a `Default-Decimal-Format` global config (QFC.Web); merged **2022.10** only as short-term, long-term tracked under #1618850/#1621870 *(inferred 2022.10)*. PRs in QFC.Web |
| **PBBALCHAIN Gas Day Offset defaults to 0** (should be blank; 0 + Gas Day = invalid param set on "Previous Run Parameters") | Metadata default value on the param | **#1406318 (TEP)** — TEP-layer metadata fix (removed default in QTEP layer); **core left unchanged** (many clients rely on default 0). Root issue also tracked under HPE #1392865 *(inferred 2021.12 / 21.24)* |
| **PBBALCHAIN warning: "Both TSP and Global configuration not found … Key Name = PB_SCRN_SPECIFIC_REDUCTION_REASON … Value = 0"** | The config key (newer, TEP cut-code-directionality feature #1684803) simply **isn't set** in the client env; harmless warning, default applies | **#1816122 (WWM, SF 26-01104783)** — **config fix**: add key `PB_SCRN_SPECIFIC_REDUCTION_REASON` (Group BALANCING, Boolean, 0). No data impact. Reproducible in Core 2026.04 because the key isn't seeded anywhere |
| **Cut-code directionality (PBR/PBD/PRR/PRD) not stamped** with `PB_STAMP_SPECIFIC_REDUCTION_REASON` on | The feature was a **ONEOK-specific** enhancement (SIR 187104) for title transfers at a pool; code stamps PBR/PBD for path balancing but **has no logic for PRR/PRD** (confirming-party reductions at R/D) | **#1630441 (TEP, SF 23-00921222)** — closed as **enhancement, not a bug**; doesn't work for all-in-to-all-out pools. Not patched |

**Note:** CAS balancing and PBBALCHAIN are intentionally different (see §2 and #1594942). PBBALCHAIN cleaning up after CAS is expected; PBBALCHAIN making *many* cuts after CAS means CAS produced wrong numbers (→ §5).

**Bug IDs:** 222984, 1629945, 1613950, 1580134, 1406318, 1816122, 1630441, 1684803. **SF:** 23-00907675, 26-01104783, 23-00921222.

---

## 8. Cluster E — Confirmation Response screen performance on Submit

**Symptom.** After making a cut on Confirmation Response and clicking **Submit**, the screen hangs **45 seconds to 3 minutes** on large gas days (1,500–4,000+ records). Worse on 2024.10/2025.04 vs older releases. ETC (HPL/TSP 191) is the recurring reporter.

**Root cause (well-characterized in #1691300/#1728225/#1742229).** Two compounding factors:
1. **The screen waits for `CFPSTRESP` to finish before re-loading** when TSP config **`CONF_UPD_CALL_BALANCING_AFTER = 1`** (ETC runs balancing after submit). This wait was introduced by a **2023 change** so users see the latest balanced data.
2. **`SendConfSubmitNotifications`** (called from `DoSave` in `QUIControllerConfirmationResponse.cs` / `QPTMNominationService.cs`) is expensive — ~35–40s of the total; and `GetResponseConfirmations`/`GetSummaryConfirmationsHelper` loop over all confirmation DOs (4,055 recs for one gas day while the grid only shows 1,017). A stale `daysToCache` (30 vs default 1825) also inflated local times.
3. The **`IX8_CFCTRL_CONF`** index was identified by ETC as causing retrieve-side slowness (removing it helped) — handled separately.

**Fix.** New config **`CONF_WAIT_FOR_POST_RESPONSE`** so the screen **does not wait** for `CFPSTRESP` (with a popup so the user knows the process is still running), plus refactor of `submitList`/notifications (~15–25s saved). #1728225 → continued in **#1742229** (also stop the redundant re-retrieve after submit when the config is false). PRs **111401/111402/111472/111473/111862/111864/124373/127349** (#1728225) and **115072/115082/115253** (#1742229, tagged **HOTFIX, Core Code Change**); earlier perf work #1691300 PRs **102255/102256/102257/102670/102824/124373/127349**. Iteration → **2025.04** *(inferred — #1742229 is a 2025.04 hotfix; confirm exact 2025.04.x in release notes)*.

**Workaround.** Set `CONF_WAIT_FOR_POST_RESPONSE` = false (once on the build), or set `CONF_UPD_CALL_BALANCING_AFTER` = 0 if the client doesn't need post-submit balancing (cut local time ~50%). Tell users to **retrieve a specific location** rather than a whole 1,500+ gas day (Engineering considers the all-records case partly a usage pattern). Check the `IX8_CFCTRL_CONF` index and `daysToCache`.

**Bug IDs:** 1691300, 1728225, 1742229 (+ related 1709598, 1762977). **SF:** 24-00982682, 25-01014361. **Client:** ETC. Also general perf: 1640922, 218151, 106210, 184282, 193431, 238819 (DTE PRD), 1395381, 84≈k CAS-retrieve perf.

---

## 9. Cluster F — Confirmation Response screen correctness (grid/data/validation)

| Signature | Root cause | Fix |
|---|---|---|
| **Grid empty + "Query Successful" toast** (also Confirmation Summary blank) | `TranslateBoolToYesNoCode` for `IsConfSubCycleRecDelYorN` mishandles the Conf Sub Cycle Y/N translation (web; depends on `K_FLO_CD` R/D + `REC/DEL_CONF_SUB_CYCLE_IND`) | **#1675663** (2024.10 regression) — fixed PRs **100649/100662** *(inferred 2024.10 / 24.18)*. Was blocking 53 automated tests |
| **"Object reference not set…" on Submit** when Conf? and Confirm Sub Cycle both checked | Same Conf-Sub-Cycle family | **#1700772** — fixed PRs **103420/103433/103733/103942/103946/104185** (+124373/127349) *(inferred 2024.10 / 24.24)* |
| **Conf Response shows MORE than offsystem** transactions in web (classic correct) | Web used a **new Security ID** (`QVPSOACONFIRMATIONRESPONSE`) that **missed the confirmation exclusions**; scripting the exclusion records + cache refresh aligned web to classic | **#1535796 (TEP, SF/PRD 22 era)** — data/security-metadata fix (no engine change) |
| **Can't bump a cut back up** when the cut originated from the Cycle batch process (Max Qty left on path record; CONF_QTY won't move; Max Qty → -1) | The Cycle process stamps `MAX_QTY` on the path/up/dn records; on closed-cycle edit, `CFPSTRESP`/PBBALCHAIN re-syncs delivery back down to the receipt; `MAX_CONF_QTY=0` on the path record blocks the bump. Treated as a **closed loophole** (V16 allowed it) | **#1407729 (EPCO, SF 21-00211730)** — closed **not a code change**; use Nom Maintenance for post-close true-ups |
| **Confirm Sub Cycle "Y" flips to "N" after balancing** into a new (non-NAESB IDL) cycle | PBBALCHAIN recalculates Confirm Sub Cycle when delivery qty lines up with the conf Max Qty; **no config** controls it | **#1761680 (EQC)** — **not reproducible / by design**; would need an **enhancement** (a toggle config) to preserve the flag. Not a bug |
| **Conf Response allows confirming qty ABOVE nomination** (no validation error) | A web validation toggled via the **Object Usage** screen in classic — likely **disabled by the client** | **#1695520 (SF 24-00985949)** — closed Rejected; check Object Usage config (not a code defect) |
| **"unknown confirmation level: contract" / PostOnLoad object-reference on open** | Confirmation level / plan setup | **#1703290 (SF 24-00993946)** — Rejected; setup |
| Sort / Up-Dn rank columns / decimals / column visibility in web | Various web-grid metadata gaps | #1710177 (sort), #1547655 (Up/Dn rank cols), #1531877/#1531878 (decimals), #1650597 (missing columns), #1760068 (Path Loc Prop/Name cols vs classic) — web-parity fixes |

**Tell-tale.** Web-only Conf Response symptoms that work fine in classic are usually **web security-id / Object-Usage / grid-metadata** issues (#1535796, #1695520), not engine bugs. Grid-empty + "object reference" on 2024.10 = the Conf-Sub-Cycle translation family (#1675663/#1700772) — confirm those PRs are in the build.

**Bug IDs:** 1675663, 1700772, 1535796, 1407729, 1761680, 1695520, 1703290, 1710177, 1547655, 1531877, 1531878, 1650597, 1760068, 1634390. **SF:** 24-00985949, 24-00993946, 21-00211730.

---

## 10. Cluster G — EPSQ (enforcement / maintenance / calc / columns)

| Signature | Root cause | Disposition |
|---|---|---|
| **CAS prelim cut not enforcing EPSQ** (reduces a trans group to 0 instead of stopping at EPSQ) | EPSQ is checked in `SetReduceRecEngQty` / `SetReduceDelEngQty` (web). The confusion is **ratcheted vs unratcheted**: the CAS Summary "Capacity Qty" is a **ratcheted** value, so intraday cuts **can legitimately go below EPSQ** in the ratcheted view; only the **unratcheted** view should never go below EPSQ. GBG only uses unratcheted (ratcheted is read-only). | **#1644345 (SF 24-00940697)** — concluded **CAS is respecting EPSQ for prelim cuts** (mostly working as designed). See the [EPSQ calculator wiki](https://quorumsoftware.visualstudio.com/QuorumSoftware/_wiki/wikis/QuorumSoftware.wiki/6777/EPSQ-(elapsed-pro-rata-scheduled-quantity)-calculator). |
| **EPSQ Maintenance not updated correctly the first few times for a NEW TSP** (works after 4–5 nom edits) | **Stale `PASTAG_EPSQ_CALC_INPUT`** left behind by the automated-test TSP cleanup; the calc picks up >intraday rows. Purging that staging table before noms fixed it first-try. | **#1327448** (2021.04) — fixed (PR **93814**); also global config **`CONFIRMATIONS::EPSQ_STG_PURGE_IND`** purges `PASTAG` when on. AT TSP cleanup must clear the table too *(inferred 2021.04)* |
| **EPSQ Override Rec/Del clear/update fails on Save (web)** with "Upstream and Downstream totals must be equal" | **Expected** — must edit **both sides of the path** (double-click the downstream record to open the other side); variance must be zero | **#1095969** (2021.04) — closed **expected behavior**; test case updated |
| **EPSQ calc enforces TSP UOM scale → decimals (e.g. 31.2) so you "exceed EPSQ" cutting to 31** | EPSQ pulled the calculated qty with TSP UOM decimal scale; noms/confs don't support decimals | **#148781 (TECO/Cenegas)** — fixed: restrict EPSQCALC stored qty to whole numbers; in `develop` + `release/17.23.0` *(inferred 17.23)*. Only seen for clients carrying energy to decimals |
| **EPSQ override permission** error (external creates, internal overrides, external resubmits) | Override-permission path | **#280389 (APL, SF 21-00103017)** — fixed PRs **48919/48921/51524/51526/51527/51530/51534/51656** *(inferred 2021.x)* |
| **Override EPSQ columns visible in Classic, not Web** (security groups 107/109/110/209/210) | Web set column `Visible` from `IsAllowUpdate` → `HasEPSQMaintenanceUpdatePermission`; the EPSQ Maintenance security object mapping didn't grant view to those groups | **#1754815 (EQC)** (dup **#1768502**) — Core code change, PRs **117379/117850/117885/118499/119071** *(inferred 2025.x)* |
| Calc EPSQ button missing on Nom Submission (web) | Not implemented in web | **#1699312 (MGD, SF 24-00960341)** — **Rejected**, → UserVoice (enhancement) |
| EPSQ values not in decimals on Conf Response; cycle picklist pre-4/1/2016 | Web display | #1531877 (fixed PR 72117), #1648271 |

**Recipe.** For "EPSQ wrong on a cut," first determine **ratcheted vs unratcheted view** (most "not enforcing EPSQ" reports are the ratcheted Summary view — expected). For "EPSQ not populating," confirm **EPSQCALC** ran and **`PASTAG_EPSQ_CALC_INPUT`** isn't stale (new-TSP/AT clone drift) and check `EPSQ_STG_PURGE_IND`. For Save-fails on overrides, both path sides must net to zero variance.

**Bug IDs:** 1644345, 1327448, 1095969, 148781, 280389, 1754815, 1768502, 1699312, 1531877, 1648271, 127657, 630457. **SF:** 24-00940697, 21-00103017, 24-00960341. **Clients:** GBG, APL, EQC, TECO, MGD.

---

## 11. Cluster H — RQCF / EDI confirmation (outbound & inbound)

**H1 — RQCF outbound sends Location ID instead of Interconnect Location ID (REGRESSION).**
- **Symptom.** After upgrading 2024.04, RQCF outbound files use the **Location ID** rather than the **Interconnect Loc ID**, breaking trading-partner receipt (TEP, WWM).
- **Root cause.** Bug **#1678265** (an ENT change) switched RQCF to Location ID and **forced everyone** instead of making it opt-in — a behavior change for TEP/Williams/others.
- **Fix.** **#1694083 (TEP, SF 24-00995059-adjacent)** added configs **`USE_INTERCONNECT_LOC_FOR_RQCF`**, **`USE_INTERCONNECT_LOC_FOR_RRFC`**, **`USE_INTERCONNECT_LOC_FOR_SQOP`** to control Location vs Interconnect Loc ID for each outbound type. PRs **103172–103177**; verified R2 SUP *(inferred 2024.04/2024.10 — confirm)*. Needs grammar **3.0+** on the TPA. **Lesson:** opt-in for behavior changes.

**H2 — RQCF outbound fails / no RRFC received.**
- **#1719524 (TEP, SF 24-00995059)** — RQCF sent but no RRFC. Root cause = **EDIServ / TPA dataset setup**, not a code bug; resolved by correcting REX TPA dataset to match Cheyenne. **Important triage fact:** in QDEV there are **no EDIServ partners**, so steps 3–4 (receive RRFC) are not reproducible internally — get **EDIServ logs + exact timestamps** from QCloud and confirm `EDINCOMING` actually fired.
- **#1388635 (TEP) — `EDRQCFOUT` outbound failing** — root cause = **EDIDev not installed on the server** (+ EDI global config wiped by a refresh). No code change; QCloud install ticket #1397813.
- **#482132 (QTR, SF 21-00104017) — inbound RQCF "RECORD … WAS MODIFIED BY: EDIBROWSER … RE-QUERY"** — the inbound file had **two records for the same key**, one with contract one without (`confirmListFromClient` duplicate). **Not a Quorum bug** — the trading partner sent ambiguous data; closed Rejected. Also surfaced a refresh-wiped `PROCESS_OUT_MONITOR_PATH` config.

**H3 — Inbound EDI cuts a confirmation to 0 / "ECRQR539 no corresponding nomination."**
- **#1639014 (CHN, SF 23-00932772)** — EDI cuts a conf to 0 + ECRQR539 even though the conf exists. Root causes were a tangle: **SR mismatch** (contract 06032 SR = 401850 but EDI file referenced 401851), and CHN on **NAESB 3.1** while nom-agent logic + the `99999` config weren't aligned; FK errors because `VERSION_CD 3.2` wasn't in `QCODE_ED_VERSION`. **Fixed** across **Quorum.QPTM.Batch + Quorum.QPTM.Database** (3.1/3.2 version inheritance) — PRs **94363/94518/94762/94862/95020/95021/95036/95042–95045/99910**; **requires DB changes** and CHN is **pre-Fluent-Migrator** *(inferred — hotfix back to 2020.09 + develop; confirm)*.

**H4 — EDI not reducing confirmations / PT-nom outbound grouping.**
- **#1325708 (BWP)** — a RQCF inbound didn't reduce 3 confirmations (PT-derived). Root cause in the **outbound** path: `CFSegmentWriter.cs` `OutboundSwitchTSPtoOperator` (line ~143, "SIR 53745") switches SR→RecBPNo and `Utilities.cs` `SumGroup` (Group Key ~line 1225) **summarizes two PT conf rows into one** when NomModelCode/NomIdLoc/NomKFloCode/roles/SRBPNo match → wrong outbound qty. Mitigated by removing the **UP/DOWN Entity** grouping on the **TPA Maintenance** Outbound Conf Level (use the all-detail level). Largely **config/data**; closed without a forced core change.
- **#1646141 (QTR, SF 24-00939490)** — couldn't do EDI confirmations because a bidirectional location (40605) wasn't in `PATRAN_PATH_UNSOLD_CAP`. Root cause: location `POV_CD='D'` (delivery only); `RetrieveAndPublishPathData()` (in `QPSAllPathUnsoldCapDetermination.cpp`) only adds locs with POV_CD 'R'/'B'. **Fix = config**: set the location **BIDIRECTIONAL** + enable **AGGREGATE or VIRTUAL** attribute, then run **CAALLUNCAP** (not CANOMCLTG) to populate unsold cap.

**Bug IDs:** 1694083, 1678265, 1719524, 1388635, 482132, 1639014, 1325708, 1646141, 1713859 (RQCF/RRFC code compare), 241051/241453 (QTR RQCF reconcile). **SF:** 24-00995059, 21-00104017, 23-00932772, 24-00939490. **Clients:** TEP, QTR, CHN, BWP, WWM. **EDI repos/symbols:** `Quorum.QPTM.Batch`/EDI DataSets (`G873RQCF`), `CFSegmentWriter.cs`, `Utilities.cs SumGroup`, `QPSAllPathUnsoldCapDetermination.cpp`, EDIServ + EDIDev framework.

---

## 12. Cluster I — CANOMCLTG (Nom Classification & Trans Grouping)

Retrieving CAS Maintenance offers to run **CANOMCLTG**; failures/slowness here block CAS entirely.

| Signature | Root cause | Fix |
|---|---|---|
| **CANOMCLTG fails: "Unable to index … multiple instances of one ctr loc path"** | **Duplicate rows in `KCTRL_CTR_LOC`** for a contract + loc id | **#1763840 (WWM, SF 25-01052129)** — **data cleanup**: delete the duplicate `KCTRL_CTR_LOC` row(s). (Also found dups on TETCO.) |
| **CANOMCLTG fails: "Looking for Cap Type (P2P/IP2S) not valid for the given TSP"** + MT "User SYSTEM not a WebAccessCaller" | (a) Cap Type setup on **Nom Classification Maintenance / Classification Rule Set Trans Groups**, and (b) **DB-vs-MT version drift** — MT on 17.29.6 but DB on 17.29.0; missing columns (`REC_ZNE_MATCHES_CTR_CD`/`DEL_ZNE_MATCHES_CTR_CD` from #1683376) broke the cache | **#1777688 (NJR)** — run the #1683376 column script to fix the cache; align DB to the release's required DB build (per release notes, e.g. 2025.04.1.6 → DB 17.29.4). Mostly setup/version, not a code bug |
| **CANOMCLTG takes too long** (sporadic 9 min → 47 min during Day-in-the-Life) | MT **cache-miss re-indexing**: after a cache refresh the `KnownFiltersList` (filter→result map in `CacheHelper`) is cleared, so the first CANOMCLTG per TSP re-indexes every filter combination (`ClassifyNominationsStreamed`/`GetScheduleCacheStreamed`/`PathTempCache`); ~44 of 47 min were MT calls | **#1535792 (TEP)** — perf fix PRs **72416/72542** delivered to PRD; reverted the #1461446 timeout bump *(inferred 2022.10)*. Trigger = updating `QCTRL_DATA_CACHE_TABLES` for `PACTRL_LOC_PATH` |

**Recipe.** On a CANOMCLTG failure, read the **MT log** (not just the QPEC batch message). "Multiple instances of one ctr loc path" → dedupe `KCTRL_CTR_LOC`. "Cap Type not valid for TSP" → check Nom Classification Maintenance + Classification Rule Set, and **verify MT build == required DB build** (release notes). Sporadic slowness after a refresh → cache re-index (expect the first run per TSP to be slow).

**Bug IDs:** 1763840, 1777688, 1535792, 1683376, 1646141 (path/unsold-cap adjacent), 1404914 (CANOMCLTG repeating in CAS submission). **SF:** 25-01052129. **Clients:** WWM, NJR, TEP. **Code:** `Quorum.QPTM.Scheduling` `BatchNomClassificationHelper.ClassifyNominations`, `NomClassificationAndTransGroupingHelper`.

---

## 13. Cluster J — CAS Maintenance screen UI / retrieve

Mostly setup or web-grid regressions, not engine bugs.

| Signature | Root cause | Disposition |
|---|---|---|
| "Error Retrieving" on CAS Maintenance | **Route-path / segment setup** (missing a segment on route paths) | **#1388368 (TEP)** — Rejected; "these errors are almost always set up" (Lindsey Saunders) |
| **"Duplicate Dictionary Key" error** retrieving CAS Maintenance | Per-TSP data/setup (same fix needed per TSP) | **#1386128 / #1392564 (TEP, TPC/TIGT)** — fixed PR **60320**; must deploy per TSP *(inferred 2021.x)* |
| Graph not fully displayed / graphical interaction breaks after changes (2025.04) | Web graph control regressions | #1745775, #1745813, #1778027 ("ResizeObserver"), #1774794 (Heating Factor totals) — web UI fixes |
| Slow retrieve / "must retrieve multiple times" / timing out | Cache / volume | #1395381, #84651, #113953, #1357188 (XCL timeout), #238819 (DTE PRD perf) |
| TSP configs caching per screen instance / defaulting to Timely for past gas days / out-of-sync prompt on historical | Screen-state defects | #228106, #213669, #262617/#874141 (out-of-sync should not run on historical) |
| Prelim Cut updates other rows' capacity / color not applied / radio buttons | Web grid behavior | #1316033, #1439907, #241959 |

These are generally **config/data or web-UI** and are not the high-value engine defects; route them to the project/support team unless a clear web regression PR is needed.

---

## 14. Expected-Behavior / "Not a Bug" FAQ (avoid needless escalation)

| Reported as | Reality | Bug |
|---|---|---|
| "Prelim cut cuts the **higher trans group before IT/Overrun**" / "not cutting lowest rank first" | **Expected** for clients using **all-in-to-all-out / beneficial gas** (Tallgrass SIR 117839, since 2013): back-haul/beneficial gas is allocated to the same service requester's noms first, which changes cut order | #1391002, #1391156 (closed not-a-bug) |
| "**New Flowing not reduced to zero before cutting into Flowing**" | Same beneficial-gas logic; verified correct | #1394702 |
| "CAS balancing doesn't match PBBALCHAIN" | **By design** — different path-matching logic (§2); PBBALCHAIN cleans up after CAS | (context for #1594942) |
| "PBBALCHAIN **recut my pool nom to EPSQ / to 0** when I reset a record" | **Expected** for pool/contract balancing when there's no flip-side nom; needs proper pool setup | #1629945 |
| "EPSQ not enforced — cut went below EPSQ on intraday" | **Expected in the ratcheted Summary view**; only the **unratcheted** view should never go below EPSQ | #1644345 |
| "Confirm Sub Cycle Y flips to N after balancing" | PBBALCHAIN recalculates it when del qty = conf Max Qty; no config; would be an enhancement | #1761680 |
| "Can confirm above nomination — no error" | A web validation toggled in the **Object Usage** screen; likely disabled by the client | #1695520 |
| "Can't bump a Cycle-process cut back up in a closed cycle" | A V16 **loophole that was correctly closed**; use Nom Maintenance for post-close true-ups | #1407729 |
| "Cut-code directionality PRR/PRD not stamping" | **ONEOK-only enhancement** (SIR 187104); not built for all-in-to-all-out pools | #1630441 |
| "Calc EPSQ button missing in web Nom Submission" | Not implemented in web → UserVoice/enhancement | #1699312 |

**Tell-tale it's expected/setup:** cut order driven by beneficial-gas/all-in-to-all-out; "below EPSQ" in the ratcheted view; pool recut with no flip-side; a web-only validation that classic enforces (Object Usage); CFAUTOCONF cutting a DRN-matched interconnect across TSPs (design gap, not a bug). **Verify CAS/PBBALCHAIN config + nom-classification setup before treating as a defect.**

---

## 15. Fix-Version Matrix

> IntegrationBuild was empty on **all** these bugs. "Fixed-in-build" is **inferred** from iteration path (YY.NN → release: 21.08→2021.04, 21.21/21.23/21.24→2021.10/12, 22.14→2022.10, 24.18/24.24→2024.10) and tags ("Merged to 2022.10", "TEP Deployed", "HOTFIX"). **Confirm against QPTM release notes or the PR target branch before quoting to a customer.**

| Bug | Symptom (cluster) | State/Reason | Fixed-in-build (inferred) | PRs | SF case | Client |
|---|---|---|---|---|---|---|
| #1568149 | CFAUTOCONF overcut above lower rank (§4) | Closed/Acceptance | 2022.04 + 2022.10 + develop | 78586,79320-22 | 22-00874403 | WWM |
| #1377828 | CFAUTOCONF cuts DRN-matched IC across TSPs (§4) | Closed/Rejected | **enhancement — not patched** | — | 21-00106474 | ENT/EPCO |
| #1396176 | AUTOCONF IC to 0 (§4) | Closed/Rejected | config (re-enter Conf Plan/Level) | — | — | WWM |
| #1783681 | AUTOCONF bad data / crash (§4) | Closed | operational cleanup, no script | — | 26-01080193 | QTR |
| **#1317128** | CAS cuts not balancing — engine rewrite (§5) | Closed/Ready-for-QA | 2019.09 HF → 2020.09/2021.04/develop | 52378/79,52584,52594,52608,52632,52816,52838 | 21-00106465 | DTE |
| #1547198 | PT-through-pool not balancing (§5) | Closed/Acceptance | 2022.10 | 76922,77945,78000,78001 | — | WWM |
| #1594942 | CAS balancing ≠ PBBALCHAIN, prelim absorbs on rec (§5) | Closed/Verified | ~2024.x | 97002,97003,97004 | 23-00883026 | TEP |
| #1601901 | Ratcheting error on prelim cut (§6) | Closed/Acceptance | 2022.10 + up | 89139-41,90167 | 23-00901305 | TEP |
| #1552981 | Ratcheted = all New Flowing (§6) | Closed/Rejected | run EPSQCALC (data/seq) | — | 22-00291615 | WWM |
| #1716916 | CAS ratchets in Timely (§6) | Closed/Verified | config (loc path maint) | — | 25-01007363 | HPE |
| #222984 | CFPSTRESP not launching PBBALCHAIN (§7) | Closed/Ready-for-QA | 2020.09 | 34739 | — | core |
| #1580134 | Path Tolerance decimals truncated web (§7) | Closed/Acceptance | 2022.10 (short-term, QFC) | 89136 (+QFC.Web) | — | CMX |
| #1406318 | PBBALCHAIN Gas Day Offset default (§7) | Closed/Ready-for-QA | 2021.12 (TEP layer) | 62361,62362 | — | TEP |
| #1816122 | PB_SCRN_SPECIFIC_REDUCTION_REASON warning (§7) | Closed/Acceptance | config (add key=0) | — | 26-01104783 | WWM |
| #1630441 | Cut-code directionality PRR/PRD (§7) | Closed/Rejected | **enhancement — not patched** | — | 23-00921222 | TEP |
| #1691300 | Conf Response submit perf (§8) | Closed/Acceptance | 2024.10/2025.04 | 102255-257,102670,102824,124373,127349 | 24-00982682 | ETC |
| #1728225 | Conf Response perf — wait-for-CFPSTRESP (§8) | Closed/Acceptance | 2025.04 (new config CONF_WAIT_FOR_POST_RESPONSE) | 111401/02/72/73,111862/64,124373,127349 | — | ETC |
| #1742229 | Conf Response perf pt3 (§8) | Closed/Acceptance HOTFIX | 2025.04.x | 115072,115082,115253 | 25-01014361 | ETC |
| #1675663 | Conf Response grid empty (§9) | Closed/Ready-for-QA | 2024.10 | 100649,100662 | — | core (2024.10 regr) |
| #1700772 | Conf Response object-ref on submit (§9) | Closed/Acceptance | 2024.10 | 103420/33,103733,103942/46,104185 | — | core |
| #1535796 | Conf Response shows non-offsystem (§9) | Closed/Verified | data (security id QVPSOACONFIRMATIONRESPONSE) | — | — | TEP |
| #1407729 | Can't bump Cycle-process cut (§9) | Closed/Verified | **not a bug** (loophole closed) | — | 21-00211730 | EPCO |
| #1644345 | CAS not enforcing EPSQ (§10) | Closed/Verified | **mostly expected** (ratcheted view) | — | 24-00940697 | TEP/GBG |
| #1327448 | EPSQ Maint not updating new TSP (§10) | Closed/Verified | 2021.04 | 93814 | — | core |
| #148781 | EPSQ enforces UOM decimals (§10) | Closed/Verified | 17.23 (develop+release) | 41051,42291 | — | TECO |
| #280389 | EPSQ override permission (§10) | Closed/Acceptance | 2021.x | 48919/21,51524-656 | 21-00103017 | APL |
| #1754815 | Override EPSQ cols web vs classic (§10) | Closed/Acceptance | 2025.x (core code change) | 117379,117850,117885,118499,119071 | — | EQC |
| #1694083 | RQCF sends Loc ID not Interconnect (§11) | Closed/Acceptance | 2024.04/.10 (new USE_INTERCONNECT_LOC_FOR_* configs) | 103172-177 | (24-00995059) | TEP |
| #1639014 | Inbound EDI cuts conf to 0 / ECRQR539 (§11) | Closed/Acceptance | back to 2020.09 (DB + Batch) | 94363/518/762/862,95020-45,99910 | 23-00932772 | CHN |
| #482132 | Inbound RQCF "record modified" (§11) | Closed/Rejected | **not a bug** (TP file dup) | — | 21-00104017 | QTR |
| #1719524 | RQCF no RRFC received (§11) | Closed/Acceptance | config (EDIServ/TPA dataset) | — | 24-00995059 | TEP |
| #1535792 | CANOMCLTG slow (cache re-index) (§12) | Closed/Ready-for-QA | 2022.10 | 72416,72542 | — | TEP |
| #1763840 | CANOMCLTG dup KCTRL_CTR_LOC (§12) | Closed/Acceptance | data cleanup | — | 25-01052129 | WWM |
| #1777688 | CANOMCLTG Cap Type / version drift (§12) | Closed/Acceptance | DB-build alignment (#1683376 script) | — | — | NJR |
| #1392564 | CAS Maint dup dictionary key (§13) | Closed/Ready-for-QA | 2021.x (per TSP) | 60320 | — | TEP |

---

## 16. Diagnostic SQL & log pointers

> QPTM is the `QPTM`/`QPTM_<CLIENT>` schema. **Verify table/column names against the client schema; run a verify-SELECT before any DELETE/UPDATE in a transaction.** Names below are from repro text and dev comments.

```sql
-- A. CFAUTOCONF cuts on a TSP/cycle/gas day (§4) — who got method 'AUT'?
SELECT DISTINCT tsp_no, gas_day, conf_cycle_id, loc_id, sr_bp_no, sr_ctr_no,
       CF.REC_NOM_QTY, CF.REC_CONF_QTY, CF.REC_SCHD_QTY,
       CF.DEL_NOM_QTY, CF.DEL_CONF_QTY, CF.DEL_SCHD_QTY
FROM   CFCTRL_CONF CF
WHERE  GAS_DAY = '<DD-MON-YYYY>' AND TSP_NO = <TSP> AND CONF_CYCLE_ID = <CYC>
AND   (CF.REC_CONF_METH_CD = 'AUT' OR CF.DEL_CONF_METH_CD = 'AUT')
ORDER BY conf_cycle_id, loc_id, sr_bp_no;
-- Then: does the cut location share a DRN (interconnect DRN) with a location on ANOTHER TSP?

-- B. Duplicate KCTRL_CTR_LOC rows blocking CANOMCLTG (§12, #1763840)
SELECT CTR_NO, LOC_ID, COUNT(*) FROM KCTRL_CTR_LOC
GROUP BY CTR_NO, LOC_ID HAVING COUNT(*) > 1;

-- C. Ratcheting "all New Flowing" — is AVG_FLOW_REC/DEL populated? (§6, #1552981)
--    Driven by EPSQCALC inside NNPSTCREAT; 0 => screen mis-classifies.
SELECT TSP_NO, NOM_ID, CONF_CYCLE_ID, AVG_FLOW_REC_QTY, AVG_FLOW_DEL_QTY
FROM   NNCTRL_NOM_LATEST_CYLE WHERE NOM_ID = <NOM> ;

-- D. Conf Sub Cycle Y/N source for grid-empty / object-ref (§9, #1675663)
SELECT A.NOM_ID, K_FLO_CD, CONF_CYCLE_ID, REC_CONF_SUB_CYCLE_IND, DEL_CONF_SUB_CYCLE_IND, C.GAS_DAY
FROM   NNCTRL_NOM_HDR A
JOIN   NNCTRL_NOM_DTL B ON A.NOM_ID=B.NOM_ID AND A.TSP_NO=B.TSP_NO
JOIN   CFCTRL_CONF   C ON A.NOM_ID=C.NOM_ID AND A.TSP_NO=C.TSP_NO
WHERE  REC_CONF_SUB_CYCLE_IND = 1 AND K_FLO_CD = 'R';

-- E. Bidirectional loc missing from unsold cap (§11, #1646141)
SELECT LOC_ID, POV_CD FROM <loc maintenance/PACTRL loc table> WHERE LOC_ID = '<LOC>';
SELECT * FROM PATRAN_PATH_UNSOLD_CAP WHERE REC_LOC = '<LOC>';
-- POV_CD must be 'R' or 'B' to be added as a receipt; fix = BIDIRECTIONAL + AGGREGATE/VIRTUAL, run CAALLUNCAP.
```

**Config keys to check (TSP / Global):** `CONF_UPD_CALL_BALANCING_AFTER`, `CONF_WAIT_FOR_POST_RESPONSE` (perf, §8), `ENABLE_CAS_PATH_BALANCING`, `AUTO_BALANCE_IND`, `ONLY_AUTO_CONFIRM_LEASE`, `LEASE_NOM_CONFIRM_ACROSS_TSPS` (CFAUTOCONF, §4), `CONFIRMATIONS::EPSQ_STG_PURGE_IND` (§10), `PB_STAMP_SPECIFIC_REDUCTION_REASON` / `PB_SCRN_SPECIFIC_REDUCTION_REASON` (§7), `USE_INTERCONNECT_LOC_FOR_RQCF`/`_RRFC`/`_SQOP` (§11), param **26902** "Run PBBALCHAIN?".

**Logs:** CAS/CANOMCLTG perf and "User SYSTEM not WebAccessCaller" live in the **MT logs** (read those, not just the QPEC batch message). PBBALCHAIN memory exits are in `QPECRealTimeMsgLog_*.log` ("Exiting QPEC gracefully … too much memory"). EDIServ send/receive needs **EDIServ logs + timestamps from QCloud** (no EDIServ partners in QDEV, so RRFC isn't reproducible internally).

---

## 17. Escalation Guidance

**Route to Engineering (real code defect) when:**
- A **prelim cut produces wrong balancing numbers / extra PBBALCHAIN cuts / fuel on wrong paths** and the client build is **at/after #1317128** — provide gas day + cycle + TSP + a small repro and the `RPT_NN01` before/after. (`NomDetailBalancingHelper_Impl_Core.cs`.)
- A **ratcheting error blocks a prelim cut** and #1601901 is not in the build (the 2-line revert).
- **PT-through-pool** one-side-not-cut and #1547198 not in the build.
- **Conf Response submit perf** without `CONF_WAIT_FOR_POST_RESPONSE` (#1728225/#1742229).
- **Conf Response grid empty / object-ref on 2024.10+** (#1675663/#1700772 — Conf-Sub-Cycle translation).
- **CFAUTOCONF overcuts above a lower-ranked nom** (#1568149 — distinct from the DRN design gap).
- Provide: client + TSP + gas day + cycle, the contract/path, the failing process + PQID + **MT log**, and confirm fix availability via the PR target branch / QPTM release notes (IntegrationBuild is blank on these WIs).

**Handle as Configuration / Cloud Ops (no code):**
- CFAUTOCONF cutting a **DRN-matched interconnect across TSPs** (design gap → end-date DRN or enhancement; #1377828) and lease/IC configs (#1716241).
- **Conf Response showing non-offsystem / above-nom-allowed** (web security id / Object Usage; #1535796/#1695520).
- **EPSQ Maintenance new-TSP staleness** (purge `PASTAG_EPSQ_CALC_INPUT`, `EPSQ_STG_PURGE_IND`; #1327448) and override Save (edit both path sides; #1095969).
- **RQCF Loc-vs-Interconnect** (`USE_INTERCONNECT_LOC_FOR_*`; #1694083), **RRFC not received** (EDIServ/TPA dataset; #1719524), **EDRQCFOUT failing** (EDIDev not installed; #1388635), **unsold cap** (BIDIRECTIONAL + AGGREGATE/VIRTUAL + CAALLUNCAP; #1646141).
- **PB_SCRN_SPECIFIC_REDUCTION_REASON warning** (add config key = 0; #1816122) and Path-Tolerance decimals (#1580134, QFC).
- **CANOMCLTG**: dedupe `KCTRL_CTR_LOC` (#1763840), align **MT build == required DB build** + run #1683376 column script (#1777688), Cap Type setup on Nom Classification Maintenance.

**Handle as Training / Expected (no fix):** §14 — beneficial-gas/all-in-to-all-out cut order, below-EPSQ in the ratcheted view, pool recut with no flip-side, Sub-Cycle-Y flip after balancing, Cycle-cut bump in closed cycle, cut-code directionality for non-ONEOK pools, ambiguous trading-partner EDI files.

**Service / data-monitor first:** "CAS cutting below capacity" that self-corrects on inventory re-run (#1567788) — capture another concrete example with data before escalating; PBBALCHAIN memory exits — reduce scope and capture the QPEC memory log.

---

*Skill created 2026-06-14. Source: ADO QPTM bugs (Closed/Resolved) under Energy Transportation + Maintenance\Midstream and Transportation. WIQL matched 536; ~242 in-scope after dropping TIPS (~23), QLNG cargo (~43), and execute/cutoff/RCA noise (~228). Deep-read 47: #1317128, #1547198, #1594942, #1567788, #1575085, #1601901, #1552981, #1716916, #1568149, #1377828, #1396176, #1429349, #1783681, #1789219, #222984, #1629945, #1613950, #1580134, #1406318, #1816122, #1630441, #1691300, #1728225, #1742229, #1675663, #1700772, #1703290, #1407729, #1695520, #1761680, #1535796, #1535792, #1388368, #1392564, #1777688, #1763840, #1644345, #1095969, #1327448, #280389, #148781, #1754815, #1699312, #1531877, #1639014, #1325708, #1646141, #482132, #1388635, #1719524, #1694083. IntegrationBuild empty on all; fix-builds inferred from iteration/tags/PR branches — confirm in QPTM release notes.*
