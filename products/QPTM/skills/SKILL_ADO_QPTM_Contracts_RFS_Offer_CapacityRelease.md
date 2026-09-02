# SKILL: QPTM Contracts / RFS / Offer / Capacity Release — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management) | **Source:** Azure DevOps bugs (NOT Salesforce)
**Scope:** The contracts & capacity-release front-to-back path — **Contract Maintenance** (time-slicing, MDQ/MSQ fields, Related-K Shared MDQ, PPA/Reallocation pop-up, save/validation), **Request for Service (RFS)** (wizard, unsold-capacity calc, approvals/award), **Offers / Bids / Awards** (Offer & Bid screens, CRBIDEVAL bid-eval, CRK_GEN/CRK_ALL award gen, replacement-contract generation, seasonal dates), **Capacity Release** (CR offers, Recall/Reput, IPWS transactional posting), **MDQ** (segment-subscribed MDQ, MDQ Comparison Report, MDQ-ROLLUP/NETMDQRES, MDQ nomination validations), **Ratchet** (Ratchet Maintenance, CAS ratcheting, storage MDWQ).

> **Evidence base:** WIQL over the two QPTM bug area branches (`Engineering\Energy Transportation` + `Engineering\Maintenance\Midstream and Transportation`), `WorkItemType=Bug`, `State IN (Closed,Resolved)`, titles containing the functional terms (Contract Maintenance, RFS, Offer, bid, award, capacity release, segmentation, MDQ, ratchet, amendment, prearranged, recall, reput) → **1008 matched** (ordered ChangedDate DESC; analysis focused on the most-recent ~250). **~62 deep-read** (Description + ReproSteps + relations/PRs + full comment thread). Every root cause below cites a real ADO bug ID and, where present, the linked SF case number. **Overlap caveat:** the Maintenance branch is mixed QPTM+TIPS — TIPS Settlement/Paystation/Facility-Batch items were dropped; a handful of dual-product items (storage ratchet → invoice/BLR_00, Contract Maintenance → billing/BLINVGEN) are noted where they touch QPTM contracts.

> **Build caveat (READ THIS):** `Microsoft.VSTS.Build.IntegrationBuild` is **empty on essentially every QPTM bug here**. Fix-version is therefore **inferred** from (a) the iteration path `YY.NN` (21.xx→2021, 22.xx→2022, 23.xx→2023, 25.21/25.22→2025.10, 26.06–26.09→2026.04), (b) `Planning:NN`/release tags, and (c) the dev/QA comment thread ("merged to 2022.10 and up", "cherry-picked to 2025.10", linked hotfix WIs). **Always confirm the exact build/patch in `Quorum.QPTM.ReleaseNotes` and the client's hotfix branch before telling a customer a fix is available.** Many maintenance fixes are **client-specific** (TEP, HPE/HEP, XCL, ENT, GBG, EQC, APL, BLH, QTR/Williams, ONK/ONEGas) and ship in that client's repo/patch, not core.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts & Pipeline](#2-concepts--pipeline)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — CRBIDEVAL / CRK_GEN bid-eval & award-gen batch failures](#4-cluster-a)
5. [Cluster B — Capacity Release seasonal dates & replacement-contract generation](#5-cluster-b)
6. [Cluster C — Offers / Bids / Awards screen & calculation defects](#6-cluster-c)
7. [Cluster D — RFS wizard, unsold capacity & RFS Approvals](#7-cluster-d)
8. [Cluster E — IPWS Capacity Release transactional posting (CWCAPRTRAN)](#8-cluster-e)
9. [Cluster F — Recall / Reput](#9-cluster-f)
10. [Cluster G — Contract Maintenance time-slicing, save & PPA/Reallocation pop-up](#10-cluster-g)
11. [Cluster H — MDQ: comparison report, roll-up, segment-subscribed & nom validations](#11-cluster-h)
12. [Cluster I — Ratchet Maintenance & CAS / storage ratcheting](#12-cluster-i)
13. [Fix-Version Matrix](#13-fix-version-matrix)
14. [Diagnostic pointers (SQL / logs / config)](#14-diagnostic-pointers)
15. [Key code, processes & repos](#15-key-code-processes--repos)
16. [Escalation guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (customer report) | Likely cause | First check / cluster |
|---|---|---|
| **CRBIDEVAL** "STOPPED PROCESSING ON ERROR" / fails only on scheduler, OK when run with an Offer No | Bad offer data: `REL_ACCPT_BID_BASIS_CD='IP'` with null `IBR_FORMULA_CD`; or no bid actually *submitted* | §4 — get PQID; check IBR ind vs basis cd |
| **CRK_GEN / CRK_ALL** award batch "completed with errors" | `PROP_CTR_NO_IND` config / Prop Ctr No read-only-ness (classic vs web); client-specific cartesian SQL | §4 |
| Awarded **replacement contract has wrong dates** (seasonal vs release) | Copied offer kept old `CRCTRL_OFFER_DTL` seasonal dates; `USE_SEASNL_DATES` not respected | §5 |
| Replacement K **S2S path created as P2P** | `CAP_TYPE_CD` hard-coded Primary→Primary in CR contract-gen | §5 (#1607331) |
| **Competing bid awarded over match-period bid** | Offer missing Cycle ID → timeline (`CROFFRTIML`) records not created | §6 (#1458730) |
| Offer **Capacity Available** wrong on Detail tab | `m_Sel_CrctrlOfferDtlWithSubmittedBids` missing `TSP_NO` join (pending MDQ across all TSPs) | §6 (#1696946 / #1735225) |
| RFS **Calculate Unsold Capacity** errors / number doesn't show / "invalid state" | Web-only: storage-facility unsold-cap grid missing; must save RFS before calculating | §7 |
| RFS **Approvals**: "Validation rule K01010 … Object reference not set" | Null-ref in `IsContractAttributeTrue` (`QContractDataAccess`) | §7 (#1783675) |
| RFS Approval **action reverts Pending → Pending** when changing rows | Grid action-status not persisting in web | §7 (#1772388/#1797407) |
| Capacity Release **duplicating** in IPWS every nightly run | IPWS appends a row when Post Date / Gas Day changes | §8 (#1739076/#1775918) |
| Capacity Release **missing** from IPWS after a "dup fix" | Collateral: GAS_DAY null → `SqlDateTime overflow` in `CapRelNaesb30DatabaseWriterHandler` | §8 (#1774746/#1806705) |
| **Recall** errors in web but OK in classic / no Timely-Notif error | Web vs classic `RuleCRRR000270` logic (per-day vs whole-period) | §9 (#1579815) |
| Recall/Reput "**An item with the same key has already been added**" | Duplicate rows in `QCODE_RECALL_NOTIF_PERIOD` | §9 (#1724570) |
| Contract Maintenance **time-slice save**: "SplitAction is not set" / "Value cannot be null" | ENT-only `CHECK_PRIMARY_TERM_EXPIRE_DT` auto-split path; web doesn't fire classic's split pop-up | §10 (#1789425/#1765986/#1731761) |
| Changing dates/Related-K **doesn't trigger PPA/Reallocation pop-up** in web | Event handler missing the changed table; or `BLXREF_REALLOC_PPA` object-id mapping | §10 (#1773033/#1784462) |
| **MDQ Comparison (External) Report** omits/duplicates locations or fails | XCL-specific view `KRPTS_MDQ_MEAS_EXTERNAL_VW` not date-filtering child/pool locs; report `KRX_MDQ` | §11 |
| **MDQ-ROLLUP** wrong sum / **NETMDQRES** applies first row's MDQ to all locations | `SP_QPTM_MDQ_ROLL_UP` uses GETDATE not As-Of; NETMDQRES timing on new time-slice | §11 |
| **Segment Subscribed MDQ** tab shows wrong amendment's segments | Client-specific view/data; `KCTRL_ROUTE_PATH_SEG_MDQ_VW` is correct | §11 (#1379364) |
| MDQ **nom validation** firing/not-firing wrong (NN0000307x / NN00009965) | Often working-as-designed (segment overrun) OR wrong source field (`OvrdCtrMdq` vs `CtrMdqDisplayOnly`), pool-to-pool not excluded | §11 |
| **Ratchet Maintenance** web shows -1 ID / can't query old ratchets / dup rows | Oracle missing X-DB view; duplicate-key dictionary in ServiceCore; classic dup rows | §12 |
| **CAS ratcheting** error on prelim cut / storage MDWQ off by rounding | Rounding mismatch in NomDetailBalancingHelper / `QResolverMDWQ.cpp` | §12 |

---

## 2. Concepts & Pipeline

```
[Contract Maintenance: header, amendments/time-slices, Locations, Related-K (Shared MDQ), Ratchet, MDQ/MSQ]
      │
      ├──► RFS (Request for Service): new request / amend / term extension / unsold-capacity calc → RFS Approvals → Award
      │
      ├──► CAPACITY RELEASE: Offer → Bid (prearranged/competing/match) → CRBIDEVAL (bid eval) → Award → CRK_GEN/CRK_ALL (replacement-contract gen)
      │                                                                                          └──► IPWS transactional posting (CWCAPRTRAN)
      │                                                              └──► Recall / Reput (post-award)
      └──► MDQ processes: MDQ-ROLLUP, NETMDQRES (net MDQ resolution), MDQ nom validations, MDQ Comparison Report
```

### Key terms / objects (QPTM vocabulary)
- **RFS** = Request for Service wizard (new / amend / term extension / storage). Has an **Unsold Capacity** tab (Locations / Zone / Storage-Facility grids) computed by a batch; results in `KTRAN_RFS_LOC_GRP_UNSOLD_CAP`. **RFS Approvals** is a separate screen that approves & awards.
- **Offer / Bid / Award** = the capacity-release lifecycle. Tables: `CRCTRL_OFFER_HDR`/`COH`, `CRCTRL_OFFER_DTL` (seasonal dates live here), `CRCTRL_*`. **CRBIDEVAL** ("CR – Bid Evaluation Process") evaluates submitted bids → **CRK_GEN/CRK_ALL** generates the **replacement contract**.
- **Match period** = NAESB-mandated wait after biddable period; depends on a **Cycle ID** on the offer and timeline records from **CROFFRTIML**.
- **Prearranged / biddable / competing / match bid** = NAESB bid types. `REL_ACCPT_BID_BASIS_CD` (`P`=Non-IBR-%, `IP`=IBR Form-%) + `IBR_FORMULA_CD` + IBR Ind must be consistent or CRBIDEVAL fails.
- **Seasonal dates** vs **Release dates**: `USE_SEASNL_DATES` (TSP config) hides seasonal-date columns when 0; when off, seasonal dates **must equal** release dates. `USE_AUTO_POPULATE_SEASNL_DATES` auto-fills them. Stale seasonal dates → wrong replacement-K dates → billing (BLINVGEN) errors.
- **Recall / Reput** = releasing shipper reclaims released capacity. `RuleCRRR000270` = Timely Notification Period validation. NAESB **Recall Notification Period Indicator** (Intraday-3 / `N9*48`) in **CROF/CRAN** EDI.
- **IPWS** = Informational Posting Website. **CWCAPRTRAN / CWCAPTRAN** posts capacity-release transactional data; **CWNIGHTLY** is the nightly umbrella. XML written to `…\AppFiles\QPTM\Exports\IPWS\CAPREL`, imported into IPWS by `CapRelNaesb30DatabaseWriterHandler`. **TOC-Object Association** maps a Type-of-Charge to the export object (`CWCAPTRAN`).
- **MDQ** = Maximum Daily Quantity (contract / location). **MSQ** = Max Storage Quantity. **MDWQ** = Max Daily Withdrawal Qty (storage). **MDQ-ROLLUP** (`SP_QPTM_MDQ_ROLL_UP`) rolls child-contract MDQ up to a parent; **NETMDQRES** = Net MDQ Resolution (recomputes Fixed MDQ from fuel rate, creates a new time-slice). **Override Contract MDQ** = `OvrdCtrMdq`; displayed contract MDQ = `CtrMdqDisplayOnly`.
- **Ratchet** = storage ratchet schedule (`QCTRL_RATCHET_SCHD_HDR`). **CAS** = Capacity Allocation/Scheduling (prelim cuts).
- **Time-slice** = an amendment-effective-date split of a contract record. ENT uses `CHECK_PRIMARY_TERM_EXPIRE_DT` to fire a split pop-up.
- **PPA / Reallocation pop-up** = appears on Contract Maintenance save when a change impacts a **closed accounting month**; driven by code table **`BLXREF_REALLOC_PPA`** (table 27310) mapping screen Object IDs → tables that should trigger.

---

## 3. Decision Tree

```
QPTM contracts / capacity-release case
│
├─ A BATCH process failed/erred? (get PQID + process name + exact error)
│   ├─ CRBIDEVAL "STOPPED PROCESSING ON ERROR"        → §4 (IBR/basis-cd bad data, or no bid submitted; client-specific cartesian SQL)
│   ├─ CRK_GEN / CRK_ALL "completed with errors"       → §4 (PROP_CTR_NO_IND; replacement-gen)
│   ├─ MDQ-ROLLUP wrong / NETMDQRES wrong              → §11
│   ├─ CWCAPRTRAN ran but IPWS wrong (dup or missing)  → §8
│   └─ EDINCOMING fails generating CROF                → §9 (NAESB ID3 / grammar config)
│
├─ Output WRONG but no crash?
│   ├─ Replacement K dates/cap-type wrong              → §5 (seasonal dates; S2S→P2P)
│   ├─ Competing bid won over match bid                → §6 (Cycle ID / timeline)
│   ├─ Offer Capacity Available wrong                  → §6 (TSP_NO join)
│   ├─ MDQ comparison report omits/dups locations      → §11 (XCL view)
│   └─ Nom validation fires/doesn't (NN0000307x/9965)  → §11 (often expected; or wrong MDQ source field)
│
├─ WEB screen broken (works in classic)?
│   ├─ Contract Maintenance time-slice save error      → §10 (SplitAction / Value-cannot-be-null; ENT)
│   ├─ PPA/Reallocation pop-up not firing              → §10
│   ├─ Ratchet Maintenance can't query / dup rows      → §12
│   ├─ RFS Approvals K01010 / action not persisting    → §7
│   └─ Recall "item with same key" / no timely error   → §9
│
└─ Vague "screen slow / error / restart" or "how does it work"  → perf/service-restart, or expected-behavior (verify config & classic first)
```

---

## 4. Cluster A — CRBIDEVAL / CRK_GEN bid-eval & award-gen batch failures

**The single largest capacity-release batch signature.** `CRBIDEVAL` (CR – Bid Evaluation) evaluates submitted bids; on award, `CRK_GEN`/`CRK_ALL` generates the replacement contract. Both fail on **bad/incomplete offer-bid data** more often than on a true code bug.

**Symptom:** `CRBIDEVAL` shows **"STOPPED PROCESSING ON ERROR"** — frequently fails when run by the **scheduler** (no Offer No parameter) but **succeeds when run manually for a specific Offer No**.

**Root causes & fixes seen:**
- **IBR/basis-cd bad data (#1639052, TEP TSP 325 Ruby — F/V, SF 23-00935940).** Offers had `REL_ACCPT_BID_BASIS_CD='IP'` (IBR Form-%) while **IBR Ind = No**, leaving `IBR_FORMULA_CD` NULL → "Bid rate could not be determined / Error initializing rsetEval". Debugged in `QPDBidEval_TEP.cpp` (`cpvFormulaCd`/`sNaesbBidBasicCd` set null for that TSP). **Fix:** code change so the **Rel Acpt Bid Basis droplist values are driven by the IBR indicator** (prevents the bad combo) + clean the existing bad offers (withdraw bids → withdraw offers, last-resort script). Merged to **2022.10 and up** (inferred). Recurs whenever a bid was **not actually submitted** before the eval runs — that alone yields the SQL error.
- **CRK_GEN award batch "completed with errors" (#1379334, 2021.10).** Root cause was `PROP_CTR_NO_IND` TSP config: in **classic** the *Prop Ctr No* field was **not** read-only when `PROP_CTR_NO_IND=0` (web already correct). Resolved via #1317175; fixed in **2021.10** line (iter 21.19).
- **HPE award process fails silently after a prior fix (#1411874, SF-linked).** Deploying the #1368605 fix to HPE 2021.04 broke CR award (OutOfMemoryException, native vcxproj not loading C++ DLLs in HPE's own QPEC). Fixed and **merged to 2021.04/2021.10 + develop**.
- **TEP CRBIDEVAL performance/locking (#1461450, iter 22.11).** `CRK_ALL` locked the contract table → web Contract Maintenance updates time out (30 s). Tallgrass-specific batch SQL `m_ContractGen_Sel_Max_Tariff_Rates` / `m_ContractGen_Sel_Max_Tariff_Rate_Sums` had **cartesian joins**; rewritten to complete <1 s.
- **Invalid column after a related fix (#1735225, EQC).** Collateral from #1696946: registered SQL `m_Sel_CrctrlOfferDtlWithSubmittedBids` referenced `TSP` instead of `TSP_NO` → offer submittal failed. **Fix:** correct the column name (PRs 112932-112937).
- **`BLCTRL_INVOICE_GRP_DOC` insert fail (#1813346, TEP 2026.04 — REJECTED).** "Insert on BLCTRL_INVOICE_GRP_DOC failed {QPTM-BLKINVGRP-73015108}" then CRBIDEVAL STOP. **Not reproducible** when run normally (blank Offer No across all valid offers in CORE TST/UPG) → closed as not-a-bug / bad test setup.

**Fix recipe:** Get **PQID + the exact error**. (1) Confirm a **bid was actually submitted** (status, not just saved). (2) Check the offer's **IBR Ind vs `REL_ACCPT_BID_BASIS_CD` vs `IBR_FORMULA_CD`** consistency — the classic bad-data signature. (3) If only the scheduler fails, run manually with the Offer No to isolate the bad offer. (4) For award (`CRK_GEN`) errors check `PROP_CTR_NO_IND`. Escalate to Engineering only after data is ruled out; provide PQID, TSP, offer/bid IDs.

---

## 5. Cluster B — Capacity Release seasonal dates & replacement-contract generation

**A recurring, multi-year TEP/REX defect family** + replacement-contract attribute copying.

### B1 — Seasonal dates used instead of release dates on the replacement K (RECURRING)
**Symptom (#1604135 / #1702160 / #1773394, TEP REX "Columbia Choice"; SF 23-00894085, 24-00990888/991839, 25-01050402/01056526):** an awarded replacement contract gets **seasonal dates** (e.g. 11/30–12/30) instead of the **release/effective dates** (12/1–12/31) used on the offer/bid → downstream **BLINVGEN billing failures**.

**Root cause:** when an offer is **created by Copy**, the new release dates are updated on the header but the **seasonal dates in `CRCTRL_OFFER_DTL` are copied from the source offer and never updated** (the seasonal columns are hidden when `USE_SEASNL_DATES=0`, so users can't see/fix them). CRBIDEVAL then builds the replacement K from the stale seasonal dates.

**Fix:**
- **Config (the original "fix", Nov-2023, #1604135 / patch #1622066):** set TSP config **`USE_SEASNL_DATES=0`** so seasonal columns are hidden on **both** Offer and Bid screens (web was only hiding on the Offer screen — that was itself a bug, fixed here). Merged to 2022.10/2023.04 hotfixes.
- **Code failsafe (#1702160 RCA, recommended by Grayson Lee):** in `QUIControllerCROfferV2.cs` (~line 3724), when `!UseSeasonalDates` force `item.SeasnlStartDate = OfferHeader.RelStartDate; item.SeasnlEndDate = OfferHeader.RelEndDate;` — so seasonal=release regardless of how the bad data arises. (PRs 105488/106246/106247/124373/127349.) The issue **recurred in Oct/Nov 2025** (#1773394) — suspected a project/hotfix wiped the earlier change, hence the code-level failsafe.

**Workaround:** confirm `USE_SEASNL_DATES=0` (and `USE_AUTO_POPULATE_SEASNL_DATES`), then correct `CRCTRL_OFFER_DTL` seasonal dates via script for the affected offers before billing.

### B2 — Replacement contract attribute / date defects
- **S2S path created as P2P (#1607331, SF-linked, iter — Maintenance).** Releasing contract with a Secondary-to-Secondary path generated a Primary-to-Primary replacement K. Root cause: CR contract-gen **hard-coded `CAP_TYPE_CD` = Primary→Primary**. **Fix:** fetch `CAP_TYPE_CD` from the releasing contract (changes in `QPSContractGen.cpp`, `QSQL_ContractGen.cpp`, `QColumnRefContainerCR.h`). Repo **`Quorum.QPTM.ClassicBatch`**, PRs 88380/88973/88974 (2022.10 & 2023.04).
- **Replacement K wrong date range when copying an offer (#1492803, iter 22.15).** Stale seasonal dates in `CRCTRL_OFFER_DTL` (same family as B1) when the Details tab clears on copy; tied to `USE_SEASNL_DATES`/`USE_AUTO_POPULATE_SEASNL_DATES`.
- **Offer can be submitted with a past start date via Copy Offer (#1683078, SF 24-00972809).** Copy-offer path skipped the start-date validation.
- **Award failed `ERROR SETTING VALUE FOR COLUMN CAP_TYPE_CD` for a Storage Release (#1679806, QTR SF 24-00971144).** Same `CAP_TYPE_CD` family in the storage path.

---

## 6. Cluster C — Offers / Bids / Awards screen & calculation defects

| Issue | Root cause | Fix / version (inferred) | Bug / SF |
|---|---|---|---|
| **Competing bid awarded over match-period bid** (TSP 403 OK on 302) | Offer had **no Cycle ID** → `CROFFRTIML` timeline records not created → match-period logic in BidEval filtered out by CYCLE_ID join | Core change to allow global field-default metadata (Cycle ID) on the web Offer header; PRs 71280/71281; **2022.x** (iter 22.13) | #1458730 |
| Offer Detail **Capacity Available** wrong (counts pending MDQ across all TSPs) | `m_Sel_CrctrlOfferDtlWithSubmittedBids` in **CRMDQMSQVL** missing a **`TSP_NO` join** | Add TSP_NO join; target **2024.04** + back-patch; PRs 104201/104777/112932-937 | #1696946 (EQT); regression #1735225 (EQC) |
| User can submit offer with **% Max Tariff > 100%** | Missing validation | Defect fix | #1430585 (TEP) |
| Max tariff rate / reservation rate **not populating** on award | Rate setup / autogen rate | Mostly config; some defect | #1727466, #1733043, #1755823, #1649746 (HPE/APL/PNGTS) |
| Bid Detail ID inconsistent / duplicated on withdraw | Bid duplication on withdraw (see also §4 #1639052) | Logged separately | #1704459, #1685581 |
| Offer/Bid web screen: grid filters not working, columns not show/hide/readonly, picklists route to wrong screen, export-to-excel broken | Web grid/Kendo defects (Kendo upgrade regressions) | Web fixes; **2025.10/2026.04** | #1552995, #1755289, #1755604, #1753312, #1710935, #1711712, #1711957, #1744755, #1741209, #1756256 |
| Bids screen: **Offer No picklist empty** | Picklist data/binding | Web fix | #1788996 (blocked #1775918 QA) |
| Prearranged bid: "must enter at least one bid detail record with a releasing contract" | Bid detail / Rel-K binding | Web fix | #1753317 |
| Discount offer using **location groups** doesn't generate a rate | **`RTOFF2RATE`** step of **NNPSTCREAT**: `SQLID_Select_Disc_Offer_Info` in `QSQL_OfferToRate.cpp` inner-joined `PACTRL_LOC_ATTR_FLAT` assuming LOC_ID_1/2 present | Use loc group when LOC_IDs null; PR 83624; **2023.x** (iter 23.08) | #1392863 |

**Note:** the Offer/Bid/Award web screens generated a large volume of beta-testing regression bugs (especially around the **Kendo grid upgrade**, 2025.10–2026.04) — most are UI fixes in `Quorum.QPTM.Web` with no data impact. Treat customer-reported *calculation* issues (capacity available, match award, rate) as defects; treat *cosmetic/grid* issues as web fixes likely already in the latest build.

---

## 7. Cluster D — RFS wizard, unsold capacity & RFS Approvals

### D1 — Unsold Capacity calculation/display (RFS wizard)
- **Storage-Facility unsold-cap grid missing in web (#1644589, QTR SF 23-00919327; follow-on #1752977).** "Calculate Unsold Capacity" runs but the number doesn't display in web (works in classic). Root cause: the **Storage Facility unsold-capacity grid was never built for web** on the RFS wizard *and* RFS Approvals (Location & Zone grids exist; grid IDs differ web vs classic; data table `KTRAN_RFS_LOC_GRP_UNSOLD_CAP`). **Fix:** add the static Storage-Facility grid to both screens (PRs 96996/97901/99699/99701). #1752977 is the related **display-only** double-count for Evergreen storage term-extensions (backend correct, UI deducts capacity twice).
- **Zone forward/backhaul classification (#1621534 / #1625763, QTR SF 23-00918681/924067).** Unsold-capacity zone classification (forward vs backhaul) for short-term/term-extension/Evergreen RFS; a conditional added in #1456336 then needed reverting — two cases **contradicted** each other on the same zone (871→448 vs 68→448). Long-term fix kept open; client reverted.
- **"current state was not saved because user is on an invalid state" after Calculate Unsold Capacity (#1758382, 2025.10 regression).** Web must **save the RFS before** calculating unsold capacity; fix adds a message/guard; PRs 118547/118629 (2025.10).
- **RFS performance for external users (#1623105, QTR SF 23-00922439).** 30-35 s query for external users only; consumed a QFC fix; **2022.10 HF** (caused collateral, redone).

### D2 — RFS Approvals
- **"Validation rule K01010 failed to execute. Object reference not set to an instance of an object" (#1783675; dup #1770527).** Null-ref in **`Quorum.QPTM.QContractDataAccess.IsContractAttributeTrue(nTspNo, sCtrNo, sAttr, dtAsOfDate)`** when approving / awarding from My Approvals. Originally found/fixed under #1768578 for **2026.04**, **cherry-picked to 2025.10**; PR 124961. (Same null-ref family as a Nom-Maint bug #1783680.)
- **Approval action reverts Pending→Pending / doesn't persist when navigating rows (#1772388 TST/EAT; #1797407 R2 SUP).** RFS Approve grid action-status not persisting on tab/row change. PRs 122068, 126555; **2025.10/2026.04**.
- **Status filter not working on RFS screen (#1738193), duplicate RFS tab auto-opens (#1700490/#1718089), End-Date update misleading status (#1715865)** — web RFS screen defects.

**Fix recipe:** for unsold-capacity "number doesn't show," confirm it's **web vs classic** and whether the **grid exists** for that capacity type (storage was the gap); have the user **save the RFS first**. For K01010 null-ref, confirm the build includes #1768578/#1783675 (2025.10+).

---

## 8. Cluster E — IPWS Capacity Release transactional posting (CWCAPRTRAN)

**The most entangled cluster — a duplication↔missing oscillation between two opposing fixes.** Process: **CWCAPRTRAN / CWCAPTRAN** (nightly via **CWNIGHTLY**) writes XML to `…\Exports\IPWS\CAPREL`, imported into IPWS by **`CapRelNaesb30DatabaseWriterHandler`**.

### E1 — Capacity Release **duplicating** in IPWS every run (#1739076 HPE SF 25-01018583; re-open #1775918; earlier VGL #102441 / #217890)
**Root cause:** each nightly run the **Gas Day (and import date) changes**, so IPWS treats it as a new record and **appends** a row for the same Offer No → duplicates on the site/CSV. (Confirmed: same offer, same data, different Gas Day per day.)
**Fix:** change the **XML Import/Export Definitions to drop Gas Day and Cycle ID** from `CapRelOfferEntity` (PLTM layer) so there's **one record per OfferNo**. First done for Firm/Interruptible reporting (VGL #1366389); applied to Capacity Release here. Fixes **going forward only** — existing dup rows must be scripted out of IPWS tables. PRs 114762/114853/116819/120039; re-worked under #1775918 (iter **26.07**, "one object per unique OfferNo"), cherry-pick to **2025.10**.

### E2 — Capacity Release **missing** from IPWS (collateral of E1) (#1774746 HEP SF 26-01063350; #1806705; #1759366)
**Root cause:** the E1 change removed **GAS_DAY**, so IPWS got `GAS_DAY = null → default 1/1/0001` → **`SqlDateTime overflow. Must be between 1/1/1753 and 12/31/9999`** in `CapRelNaesb30DatabaseWriterHandler` → nothing posted (CWCAPRTRAN completes clean, file looks fine, site empty). **Fix:** **reverted** the GAS_DAY/CYCLE_ID removal for affected customers (revert PRs in 2024.04/2025.04/2025.10/develop); proper dedupe handled long-term on **#1775918**. #1759366: duplicate `CAPRELK` segments in the XML (one with `RATE_FORM_TYPE_CD=1`, one null) because **virtual locations** were on the replacement K but not the offer → null rate-form-type record; workaround = remove the extra segment / add virtual locations to the offer.

### E3 — IPWS config / data (not a code fix)
- **TOC-Object Association multiple TOCs (#1727472/#1727477, PNG go-live).** More than just `RES` TOC tied to the `CWCAPTRAN` object ID → bad XML; files land in the **Processed** folder but nothing shows on site. Rejected as code bug — config (limit TOC-object association); proposed a validation warning.
- **NAESB descriptions wrong / Prearr Deal blank (#1370331 VGL; #1446229).** Perm-Rel / Prearr-Deal / Prev-Rel / Recall-Reput show non-NAESB values or blank when the **`NAESB_ABBREV`** column is null. Data/config — populate NAESB abbreviations; some core display fixes (2021.10).
- **CSV header shift / commas split fields (#102441 VGL, #217890).** CR transactional CSV download headers misaligned; commas in field values split columns. v17 core fix; IPWS/services side for v16.

**Fix recipe:** First decide which way the bug points. **Duplicating** → confirm the build has the Gas-Day/Cycle-Id removal (#1775918) AND that GAS_DAY-null handling is fixed (else you create E2). **Missing** → check IPWS QPEC logs for **`SqlDateTime overflow`** (the GAS_DAY-null signature, E2) and for **duplicate CAPRELK / null RATE_FORM_TYPE_CD** (virtual-location, #1759366); verify **TOC-Object Association** has only the intended TOC and the CAPREL POSTING key points to the right QCloud folder; restart QPTM **and** IPWS services. Many of these resolved operationally (refresh, empty the folder, manual XML edit) — capture IPWS logs before restarting.

---

## 9. Cluster F — Recall / Reput

| Issue | Root cause | Fix / version | Bug / SF |
|---|---|---|---|
| **Recall** can be submitted in classic but **errors in web**; Timely-Notif (`RuleCRRR000270`) not firing as expected; web shows "submission successful" but doesn't save | **Web vs classic validation logic differs**: classic compares awarded vs recall/reput **per day** over the range; web computed it **once for the whole period**. Classic logic deemed correct → **changed web to match classic**. (Code unchanged since 2017; MT migration altered it.) | Web logic aligned to classic; merged **2022.10 and up**, cherry-picked hotfix/17.19.2 + develop | #1579815 (TEP SF 22-00876156; HPE same issue tracked here) |
| Recall/Reput in web: **"An item with the same key has already been added"** (OK in classic, not repro in core) | **Duplicate rows in `QCODE_RECALL_NOTIF_PERIOD`** (overlapping code/decode values) → C# dictionary can't take dup key | **Data fix** — delete the dup code rows to match core (`DELETE FROM QCODE_RECALL_NOTIF_PERIOD WHERE USER_ID <> '<keep>'`); EQC UPG17 | #1724570 (EQC, DFCT 1644) |
| **CROF** outbound EDI fails / missing NAESB **Intraday-3 Recall Notification Indicator (`N9*48`)** | (1) Missing **CRNS grammar** config in TPA Maintenance → CROF dataset reused for "Notes Special Instruction" out-file → process errors; (2) `QEdiCROFOut18.cs` didn't emit ID3 for NAESB 3.1+ | Add TPA-Maintenance grammar entry (config, no script); code: add ID3 in `QEdiCROFOut18.cs` **mirroring the CRAN fix #1756196** (`QEdiCRANOut`, iter 25.21≈2025.10); cherry-picked to 2025.10/current/develop | #1781005 (QTR SF 25-01060489); CRAN: #1756196 |
| **Recall/Reput functionality not working in web** (BLH) | Web Ratchet/Recall screen retrieval (see also §12) | — | #1667506 area |
| Recall/Reput Submit + simultaneous error popup (#1717775, 2025.04 beta) | Web message timing | Web fix | #1717775 |

**Fix recipe:** for recall web/classic mismatches, remember **classic is authoritative** for `RuleCRRR000270` (per-day comparison). For "item with same key," dedupe **`QCODE_RECALL_NOTIF_PERIOD`**. For CROF/CRAN EDI ID3, check **TPA Maintenance grammar** + NAESB version gating; the CRAN pattern (#1756196) is the template for CROF (#1781005).

---

## 10. Cluster G — Contract Maintenance time-slicing, save & PPA/Reallocation pop-up

### G1 — Time-slice / save errors (mostly ENT, web-only)
- **"Cannot use effective date auto split logic b/c the SplitAction is not set nor is a SplitActionDelegate set" (#1789425 ENT 2024.04 SF, iter 26.06; explored in #1765986).** Modifying the Amendment Effective-From within an existing time-slice fails in **web** (classic shows a "would you like to add/update" pop-up). Root cause: the **`CHECK_PRIMARY_TERM_EXPIRE_DT`** primary-term-expiration pop-up path is **ENT-only and was never thoroughly tested**; web didn't wire up the SplitAction delegate. **Fix:** wire the split action so the effective-date pop-up fires and auto-splits the time-slice; PRs 125325-125532; **2024.04 hotfix + 2026.04**. (Note #1765986 was **closed as expected behavior** — to insert a slice *between* existing slices the user must **end-date the first** then begin the new one; "insert between" is not supported, per old #241831/#261397.)
- **"Value cannot be null" exception on save (#1731761, iter 25.11).** ENT-only, when ENT-specific code isn't present and effective-date logic should run on a description change — save happens but the batch isn't launched. PRs 111946/111947/112087/112088.
- **CICO Settlement Method validation error blocks save (#1774039/#1783130 — REJECTED).** "If Settlement Method is CICO/WACO there must be CICO PPA/Settlement Lag Time…" fired on new-TOS FTS contracts in **Oracle TST only**; **not reproducible** in MSSQL / could create in ORA → closed not-a-bug.

### G2 — PPA / Reallocation pop-up not triggered (ENT)
- **Changing Shared MDQ Related-K doesn't trigger Reallocation/PPA (#1773033, ENT Panaya Defect 90, HOTFIX).** Editing the **Related-K (Shared MDQ)** effective date in web Contract Maintenance saved but **no PPA/Reallocation pop-up**. Root cause: the event handler **`HandleGenericScreenChangeEvent` did not include `SCTRL_RELATED_CTR`** in its table list → `HandleContractMaintenanceChange` never fired → `PPAReallocationDialogData.ReallocateSelect` empty → `CheckPPAReallocationDialogRequired()` had nothing to evaluate. **Fix:** add `SCTRL_RELATED_CTR` to the handler; PRs 122294/122297/122616/122617; cherry-picked **2025.04 / 2025.10 / develop**. **Important nuance:** the pop-up correctly does **not** fire if an **unprocessed PPA event already exists** for that contract+production month (avoids dup `BLTRAN_PPA_EVENT` rows), and only fires when a **closed** accounting month is impacted.
- **Pop-up not triggered for Contract Maintenance (Object ID `QVPCONTRACTHEADER`) (#1784462, ENT Defect 110 — Resolved/Fixed but largely a data mapping).** Root cause: code expects `BLXREF_REALLOC_PPA` (table **27310**) rows mapped as `OBJECT_ID='QVPCONTRACTMAINTENANCE', DBTBL_NM='CONTRACTHEADER'`, but the client had `QVPCONTRACTHEADER` / `SCTRL_CTR_HEADER`. **Fix (client data):** `UPDATE BLXREF_REALLOC_PPA SET OBJECT_ID='QVPCONTRACTMAINTENANCE', DBTBL_NM='CONTRACTHEADER' WHERE OBJECT_ID='QVPCONTRACTHEADER' AND DBTBL_NM='SCTRL_CTR_HEADER';`. Caveat: **changing contract *status* alone is NOT expected to trigger** a PPA — only **date** changes that impact a closed month do.

**Fix recipe:** web-only time-slice save errors on ENT → look for the `CHECK_PRIMARY_TERM_EXPIRE_DT` split-action path (#1789425). PPA pop-up not firing → (1) is the changed table in the event handler (#1773033 added `SCTRL_RELATED_CTR`), (2) is `BLXREF_REALLOC_PPA` mapped to the right Object ID (#1784462), (3) is a closed accounting month actually impacted and is there no pre-existing unprocessed PPA event. "Insert a slice between two slices" is **not supported** — end-date then add.

---

## 11. Cluster H — MDQ: comparison report, roll-up, segment-subscribed & nom validations

### H1 — Contract MDQ Comparison (External) Report — `KRX_MDQ` / `RPTKRX_MDQ` (XCL-specific)
Crystal report **`KRPTS_MDQ_EXTERNAL.rpt`** over view **`KRPTS_MDQ_MEAS_EXTERNAL_VW`**. Long-running XCL pain (all SF-linked):
- **Omits locations (#216109 SF 20-00085810; #242060 SF 20-00094653).** Locations with MDQ defined are excluded — the report filters out any location on a contract that has an **amendment** record. Root cause in the **view**: production-date filter applied to premise (child) Capacity eff dates but **not** to the pool's child-location eff dates. **Fix:** modify `KRPTS_MDQ_MEAS_EXTERNAL_VW` to include those locations (DB ticket #243609; PRs 33976/33977/39740).
- **Displays unexpected/duplicate data (#1530880 SF 22-00262756).** Opposite symptom — duplicate premises (one valid + one invalid date range) because the view doesn't take **contract effective dates** for the production month into account. Needed a **view re-work**; PRs 78398/78399. (Fixing omission then over-included → this is the natural seesaw; test both walkthroughs together.)
- **Report fails/times out for all users (#1794375 SF 26-01089462 — Acceptance).** "Failed to retrieve data… Database Vendor Code 1101" after hours; XCL on **out-of-support 2019**; treated as **perf/version** → validate in the upgrade, not a core fix.

### H2 — MDQ roll-up / net resolution batch
- **MDQ-ROLLUP wrong parent sum (#1631014 XCL SF 23-00926685).** `MDQ-ROLLUP` summed child-contract Fixed MDQ wrong for the parent. Root cause: **`SP_QPTM_MDQ_ROLL_UP` uses `GETDATE` (today)** rather than the report's **As-Of date**, so end-dated child contracts (e.g. ended 12/31) are dropped/added depending on run date. **Fix:** alter `SP_QPTM_MDQ_ROLL_UP` (DB ticket #1636875); XCL Patch 30.
- **NETMDQRES applies first row's MDQ to all locations (#1674928 GBG SF 24-00965618).** Net MDQ Resolution, when it **creates a new time-slice during the run** (new production month / fuel-rate change), copies the **first location's Fixed MDQ to every location**; a **second run** corrects it. Strongly **timing-related** (running immediately after a fuel-rate update / the web **PPA-Reallocation pop-up** "Update" path); workaround = close (don't click Update on) the realloc pop-up, select the Production Month, ensure the process completes its full 31 steps. Dianne identified the code fix; PRs 115278/115934/115935/115937; **2024.04** hotfix for GBG.

### H3 — Segment Subscribed MDQ tab
- **Wrong segments shown (#1379364 TEP, iter 21.19; related #1379529).** Segment Subscribed MDQ tab displays a **different amendment's** segments (e.g. A3 records when A1 selected). The view **`KCTRL_ROUTE_PATH_SEG_MDQ_VW` is correct**; the screen/data drift is client-specific. Fix via SQL/metadata (1379364 - MSSQL.sql / ORA.sql); TEP hotfix 2021.09 / 2021.10.

### H4 — MDQ nomination validations (often expected behavior)
- **NN00003072 Segmentation-on-the-Fly "over MDQ" (#1726480 HPE SF 25-01009023 — L4-Investigated, Acceptance).** The validation sums nominated qty **per pipeline segment** (via Location Path Maintenance) and errors if a single segment exceeds KMDQ. **Working as designed** — total nominations may exceed contract MDQ as long as no single segment does; the customer's confusion was PRD-vs-UAT data, not a bug. (Debugged by Grayson Lee + Aditya Bhagat; design in EQT Segmentation Phase-3.)
- **NN00003075 custom EUT validation not firing (#1404268 DTE SF 21-00207007).** DTE-custom MDQ validation didn't fire → root cause **TOS code not tied to the validation rule** + a slow SQL causing a **timeout** ("user requested cancel"). **Fix:** add the TOS record + speed up the validation SQL. Client-specific.
- **NN00009965 AOS shared-MDQ validation wrong (#1775092 WWM SF 25-01041489 — L4-Investigated, iter 26.09).** Validation triggered on the wrong nomination (sometimes a 0-qty row) and counted pool-to-pool noms. Root cause: **Shared MDQ read from `ctr.OvrdCtrMdq` (returned 0)** and **pool-to-pool noms wrongly included in `dTotalNomQty`**. **Fix (L4 PR):** pull Shared MDQ from **`ctr.CtrMdqDisplayOnly`**, **exclude pool-to-pool** (ATT on both rec+del) from the total, point the error at the offending nom. *Later reverted the MDQ source back to `OvrdCtrMdq`* (a customer had Override MDQ legitimately set to 250,000) **while keeping the pool-to-pool exclusion**. WWM-only rule; consumed for **2026.04 + 2025.10**; PRs 126984/127254/128433-128535.
- **K_RFSME020 / VALIDATE_MDQ_REC_DEL blocks Override MDQ update (#1764767 HEP SF 25-01042893).** Web Contract Maintenance refused to save Override Contract MDQ / Fixed MDQ ("Total receipt MDQ does not equal Total Delivery MDQ") even with `VALIDATE_MDQ_REC_DEL=0`; classic honored the config, web didn't. **Fix:** web respects the config (validation `ContractMaintenance0008`); PRs 119945/119978/122604; HEP 1/23 hotfix.

**Fix recipe:** For the XCL MDQ comparison report, the bug is almost always the **view** (`KRPTS_MDQ_MEAS_EXTERNAL_VW`) not honoring contract/child eff dates for the production month — and fixing omission can re-introduce duplication (test both). For MDQ-ROLLUP/NETMDQRES, suspect **As-Of vs GETDATE** and **new-time-slice timing**; a second run "fixing it" is the NETMDQRES tell. For nom-validation cases, **verify the segment/path setup and classic behavior first** — several are working-as-designed; the real defects are wrong **MDQ source field** (#1775092) or web not honoring **config** (#1764767).

---

## 12. Cluster I — Ratchet Maintenance & CAS / storage ratcheting

| Issue | Root cause | Fix / version | Bug / SF |
|---|---|---|---|
| Ratchet Maintenance **New button shows `-1`** instead of next ID (Oracle only) | Code checks for ID collisions but the **QFC schema lacked a cross-DB view** to `QCTRL_RATCHET_SCHD_HDR` → can't read existing IDs | Add `XMod_view` for QCM_QFC over `QCTRL_RATCHET_SCHD_HDR`; PRs 87340/87883/87885/88339; ONG 2021.04 + 2022.10/2023.04 | #1607618 (ONG SF 23-00906803) |
| Ratchet Maintenance **web can't query old ratchets / shows dup rows** (BLH) | **Duplicate rows in classic** (updating Eff Date Range created dups; 128 vs 64) → ServiceCore **`Dictionary` "item with same key"** exception; classic SQL uses a different FROM (`QARCH_FORMULA` eff dates) than web | Changed the dictionary in **`Quorum.QPTM.ServiceCore`** to take distinct keys (web shows 64); **DECLINED** for classic — recommendation: **use web Ratchet Maintenance only** going forward (classic dups can't be deleted due to overlap) | #1667506 (BLH SF 24-00960195) |
| **CAS ratcheting** error on prelim cut (CAS 1 / CAS 3) | Rounding mismatch: values rounded in `SetReduceRecEngQty`/`SetReduceDelEngQty` but not in `IsQuantityLeftToReduce`; collateral from the v17 refactor #1317128 of `NomDetailBalancingHelper_Impl_Core.cs` (2 lines changed throw off totals) | Round consistently in `IsQuantityLeftToReduce`; revert the 2 refactor lines; PRs 89139-89141/90167 (CAS1), 91495/91711/91734/91735 (CAS3); **2022.10 and up**; long-term re-test req #1621185 | #1601901, #1633392 (TEP SF 23-00901305) |
| **Storage ratchet / MDWQ** on invoice ≠ nomination & Storage Info Report (IN14) | **Rounding applied before** the storage-% tier comparison in **`QResolverMDWQ.cpp`** (used across many reports) → IN14/nom-validation pick a higher Withdrawal % tier than the invoice (BLR_00, which rounds *after* determining the tier — and is correct). Also IN14 "Max AD W/D Qty" pulls **previous day's** value | Approved for dev: round **after** tier determination / err toward lower rounding for MDWQ; `GetMinMDWQ`/`GetMdwq`. (Touches dual product — QPTM nom validation `NN00003110` + TIPS invoice BLR_00.) L4-Investigated | #1734715 / #1783407 (TGL SF 25-01010705) |

**Fix recipe:** Oracle `-1` ratchet ID → missing X-DB view for `QCTRL_RATCHET_SCHD_HDR` (#1607618). BLH-style "web won't query old ratchets" → classic **duplicate rows** + ServiceCore dictionary; steer the client to **web-only** ratchet maintenance. CAS prelim-cut errors → rounding in `NomDetailBalancingHelper`/`IsQuantityLeftToReduce` (#1601901/#1633392); no guarantee one fix clears *all* ratcheting errors. Storage MDWQ off → rounding order in `QResolverMDWQ.cpp` (#1734715).

---

## 13. Fix-Version Matrix

> IntegrationBuild empty on all rows → **fixed-in-build INFERRED** from iteration `YY.NN` + tags + comment thread. **Confirm in `Quorum.QPTM.ReleaseNotes` / client hotfix branch.** State = ADO state/reason at time of mining.

| Bug | Symptom | Cluster | State / Reason | Fixed-in (inferred) | SF case | Client |
|---|---|---|---|---|---|---|
| #1639052 | CRBIDEVAL fails TSP 325 (IBR/basis-cd) | A | Closed/Verified | 2022.10 + up | 23-00935940 | TEP |
| #1379334 | CRK_GEN award batch errors | A | Closed/RFQA | 2021.10 (21.19) | — | core/ETS |
| #1411874 | HPE CR award fails after fix | A | Closed/Verified | 2021.04 & 2021.10 + develop | (SF) | HPE |
| #1461450 | CRBIDEVAL perf / table lock | A | Closed/RFQA | 2022.x (22.11) | — | TEP/TIGT |
| #1735225 | `TSP` vs `TSP_NO` invalid column | A/C | Closed/Acceptance | (Maintenance HF) | — | EQC |
| #1604135 | Seasonal dates hidden web Offer+Bid | B | Closed/Acceptance | 2022.10/2023.04 HF (patch 1622066) | 23-00894085 | TEP |
| #1702160 | Seasonal-dates RCA + code failsafe | B | Closed/Acceptance | 2024.04+ (failsafe) | 24-00990888/991839 | TEP |
| #1773394 | Seasonal dates recurred (perm fix) | B | Closed/Rejected | (pending — see #1700620) | 25-01061889 | TEP |
| #1607331 | S2S path → P2P replacement K | B | Closed/Acceptance | 2022.10 & 2023.04 | (SF) | CMX/core |
| #1492803 | Replacement K wrong dates on copy | B | Closed/RFQA | 2022.x (22.15) | — | TEP |
| #1458730 | Competing bid beats match bid | C | Closed/RFQA | 2022.x (22.13) | — | TEP |
| #1696946 | Capacity Available wrong (TSP join) | C | Closed/Acceptance | 2024.04 + back-patch | (SF) | EQT |
| #1392863 | NNPSTCREAT no rate for disc-offer loc groups | C | Closed/RFQA | 2023.x (23.08) | — | core |
| #1644589 | RFS storage unsold-cap grid missing (web) | D | Closed/Acceptance | 2024.x HF | 23-00919327 | QTR |
| #1752977 | Evergreen storage unsold-cap display | D | Closed/Acceptance | (Maintenance) | (RFS) | QTR |
| #1783675 | RFS Approvals K01010 null-ref | D | Closed/Verified | 2026.04 → cherry-pick 2025.10 | — | core/AT |
| #1772388 / #1797407 | RFS Approve action not persisting | D | Closed/RFQA | 2025.10 / 2026.04 (26.08) | — | core/AT |
| #1623105 | RFS perf external users | D | Closed/Acceptance | 2022.10 HF | 23-00922439 | QTR |
| #1739076 | IPWS CR duplicating (Gas Day) | E | Closed/Acceptance | 2025.x HF (superseded) | 25-01018583 | HPE |
| #1775918 | IPWS CR dup — proper fix | E | Closed/Acceptance | 2026.04 (26.07) → cherry-pick 2025.10 | 25-01018583 | HPE |
| #1774746 | IPWS CR missing (GAS_DAY null overflow) | E | Closed/Verified | revert in 2024.04/2025.04/2025.10/develop | 26-01063350 | HEP |
| #102441 | IPWS CR CSV header/commas | E | Closed/RFQA | 2020.24/.25 (v17) | — | VGL |
| #1370331 | IPWS NAESB descriptions | E | Closed/RFQA | 2021.10 (21.24) | — | VGL |
| #1579815 | Recall web≠classic (CRRR000270) | F | Closed/Acceptance | 2022.10 + up (HF 17.19.2) | 22-00876156 | TEP/HPE |
| #1724570 | Recall "item with same key" | F | Closed/Acceptance | data fix (QCODE dups) | DFCT 1644 | EQC |
| #1781005 | CROF EDI ID3 (N9*48) missing | F | Closed/Acceptance | 2025.10 + current/develop | 25-01060489 | QTR |
| #1756196 | CRAN EDI ID3 (template for CROF) | F | Closed/Acceptance | 2025.10 (25.21) | — | core |
| #1789425 | Contract Maint time-slice SplitAction error | G | Closed/Acceptance | 2024.04 HF + 2026.04 (26.06) | (ENT) | ENT |
| #1731761 | Contract Maint "Value cannot be null" save | G | Closed/Verified | 2025.x (25.11) | — | ENT |
| #1773033 | PPA pop-up not firing (Related-K Shared MDQ) | G | Closed/Acceptance | 2025.04/2025.10/develop | (Panaya 90) | ENT |
| #1784462 | PPA pop-up not firing (QVPCONTRACTHEADER) | G | Resolved/Fixed | client data (BLXREF_REALLOC_PPA) | (Defect 110) | ENT |
| #216109 / #242060 | MDQ Comparison Report omits locations | H | Closed/Verified | (XCL patch) | 20-00085810 / 20-00094653 | XCL |
| #1530880 | MDQ Comparison Report duplicates | H | Closed/Verified | (XCL patch) | 22-00262756 | XCL |
| #1631014 | MDQ-ROLLUP wrong (GETDATE vs As-Of) | H | Closed/Acceptance | XCL Patch 30 | 23-00926685 | XCL |
| #1674928 | NETMDQRES first-row MDQ to all locs | H | Closed/Acceptance | 2024.04 HF | 24-00965618 | GBG |
| #1379364 | Segment Subscribed MDQ wrong amendment | H | Closed/RFQA | 2021.09/2021.10 HF | — | TEP |
| #1726480 | NN00003072 seg-on-the-fly (expected) | H | Closed/Acceptance | n/a (working as designed) | 25-01009023 | HPE |
| #1775092 | NN00009965 AOS wrong MDQ source/pool | H | Closed/Acceptance | 2026.04 + 2025.10 (26.09) | 25-01041489 | WWM |
| #1764767 | VALIDATE_MDQ_REC_DEL not honored (web) | H | Closed/Acceptance | HEP 1/23 HF | 25-01042893 | HEP |
| #1607618 | Ratchet New = -1 (Oracle X-DB view) | I | Closed/Acceptance | ONG 2021.04 + 2022.10/2023.04 | 23-00906803 | ONG |
| #1667506 | Ratchet web can't query old / dup rows | I | Closed/Acceptance | web fix (DECLINED classic) | 24-00960195 | BLH |
| #1601901 / #1633392 | CAS ratcheting prelim-cut rounding | I | Closed/Acceptance/Verified | 2022.10 + up | 23-00901305 | TEP |
| #1734715 / #1783407 | Storage MDWQ rounding (IN14 vs invoice) | I | Closed/Verified | (dev approved) | 25-01010705 | TGL |

---

## 14. Diagnostic pointers (SQL / logs / config)

> **Caveat:** QPTM runs MSSQL & Oracle per client; table/column names below are from repro text + comments. **Verify against the client schema; run a verify-SELECT before any UPDATE/DELETE in a transaction.** Many fixes here are *client-specific repos* — check the `<CLIENT>.QPTM.*` repo first.

**Batch failures:** always get **PQID + process name + exact ORA/COM error** (double-click the Batch Messages error row / read the QPEC trace).

```sql
-- A. CRBIDEVAL bad offer data (the §4 IBR/basis-cd signature): IP basis with null formula
SELECT OFFER_NO, IBR_IND, REL_ACCPT_BID_BASIS_CD, IBR_FORMULA_CD
FROM   CRCTRL_OFFER_HDR
WHERE  TSP_NO = <tsp> AND (REL_ACCPT_BID_BASIS_CD='IP' AND IBR_FORMULA_CD IS NULL);

-- B. Stale seasonal vs release dates on a copied offer (§5 B1) — seasonal hidden when USE_SEASNL_DATES=0
SELECT OFFER_NO, OFFER_DTL_ID, REL_START_DT, REL_END_DT, SEASNL_START_DT, SEASNL_END_DT
FROM   CRCTRL_OFFER_DTL WHERE OFFER_NO = <offer>;
--   config: TSP/USE_SEASNL_DATES, CAPACITY_RELEASE/USE_AUTO_POPULATE_SEASNL_DATES

-- C. IPWS CR duplicates vs missing (§8): look at gas day / import date per OfferNo in the IPWS CR table;
--    in IPWS QPEC log a "SqlDateTime overflow … 1/1/1753 … 12/31/9999" = GAS_DAY null (E2, the over-corrected dup fix).
--    Duplicate CAPRELK with null RATE_FORM_TYPE_CD = virtual locations on replacement K but not offer (#1759366).

-- D. PPA/Reallocation pop-up not firing (§10 G2): the code-table mapping
SELECT OBJECT_ID, DBTBL_NM, * FROM BLXREF_REALLOC_PPA   -- code table 27310
WHERE  OBJECT_ID LIKE 'QVPCONTRACT%';
--   expected OBJECT_ID='QVPCONTRACTMAINTENANCE', DBTBL_NM='CONTRACTHEADER' (#1784462)
--   and there must be NO unprocessed row in BLTRAN_PPA_EVENT for that ctr+prod month, AND a CLOSED acctg month impacted.

-- E. Recall "item with same key" (§9) — duplicate code/decode rows
SELECT USER_ID, COUNT(*) FROM QCODE_RECALL_NOTIF_PERIOD GROUP BY USER_ID HAVING COUNT(*)>1;

-- F. MDQ Comparison Report (§11 H1) — XCL: inspect the view & report
--   view KRPTS_MDQ_MEAS_EXTERNAL_VW, Crystal KRPTS_MDQ_EXTERNAL.rpt (report id KRX_MDQ / RPTKRX_MDQ)
--   bug = prod-date filter not applied to child/pool location eff dates; or contract eff dates ignored.

-- G. MDQ-ROLLUP (§11 H2): SP_QPTM_MDQ_ROLL_UP uses GETDATE, not the report As-Of date.
-- H. Segment Subscribed MDQ (§11 H3): KCTRL_ROUTE_PATH_SEG_MDQ_VW is correct; screen shows wrong amendment.
-- I. NN00003072 seg-on-the-fly (§11 H4): map segments via Location Path Maintenance
SELECT NOM.SEGMENT_ON_THE_FLY_IND, NOM.* FROM NNCTRL_NOM_DTL NOM
WHERE  BEG_GAS_DAY = '<gas day>' AND SR_BP_NO = <sr> AND TSP_NO = <tsp>;
```

**Logs:** QPTM MiddleTier / QPEC trace (`qtrace.QPTM.MT.*`, `qtrace.QIPWS.MT.*`). For RFS Approvals K01010 grep the MT trace for `IsContractAttributeTrue` / `NullReferenceException`. For IPWS, grep IPWS QPEC for `CapRelNaesb30DatabaseWriterHandler` + `SqlDateTime overflow`.

---

## 15. Key code, processes & repos

### Processes / batch steps
| Process | Purpose | Notes |
|---|---|---|
| **CRBIDEVAL** | CR – Bid Evaluation (evaluate submitted bids) | §4; fails on IBR/basis-cd bad data or no submitted bid |
| **CRK_GEN / CRK_ALL** | Generate replacement contract on award | §4/§5; `CAP_TYPE_CD`, `PROP_CTR_NO_IND` |
| **CROFFRTIML** | Build offer timeline records (match period) | §6; needs Cycle ID |
| **CRMDQMSQVL** | Capacity-available / MDQ-MSQ validation for offers | §6; `m_Sel_CrctrlOfferDtlWithSubmittedBids` (TSP_NO join) |
| **NNPSTCREAT** (step **RTOFF2RATE**) | Create rate from discount offer on nom submit | §6; `QSQL_OfferToRate.cpp` loc-group bug |
| **CWCAPRTRAN / CWCAPTRAN / CWNIGHTLY** | IPWS capacity-release transactional posting | §8; XML → `…\Exports\IPWS\CAPREL` |
| **MDQ-ROLLUP** (`SP_QPTM_MDQ_ROLL_UP`) | Roll child MDQ to parent | §11; GETDATE vs As-Of |
| **NETMDQRES** | Net MDQ Resolution (recompute Fixed MDQ from fuel rate) | §11; new-time-slice timing |
| **EDINCOMING** | Generate CROF/CRAN outbound EDI | §9; NAESB ID3 `N9*48` |

### Code locations (from PRs / dev comments)
| Symbol / file | Repo / area | Cluster |
|---|---|---|
| `QPDBidEval_*.cpp` (e.g. `QPDBidEval_TEP.cpp`) | `Quorum.QPTM.ClassicBatch` (+ client) | §4 bid eval |
| `m_ContractGen_Sel_Max_Tariff_Rate(s)/_Sums` | client ClassicBatch (TIGT) | §4 perf |
| `QPSContractGen.cpp`, `QSQL_ContractGen.cpp`, `QColumnRefContainerCR.h` | `Quorum.QPTM.ClassicBatch` | §5 replacement-K cap type |
| `QUIControllerCROfferV2.cs` (~L3724) | `Quorum.QPTM.Web` | §5 seasonal-date failsafe |
| `m_Sel_CrctrlOfferDtlWithSubmittedBids` (registered SQL) | core/client Metadata | §6 capacity available |
| `QSQL_OfferToRate.cpp` (`SQLID_Select_Disc_Offer_Info`) | `Quorum.QPTM.ClassicBatch` | §6 disc-offer rate |
| `QContractDataAccess.IsContractAttributeTrue` | `Quorum.QPTM` service core | §7 RFS Approvals K01010 |
| `CapRelOfferEntity` (XML import/export defn) / `CapRelNaesb30DatabaseWriterHandler` | IPWS (QIPWS) | §8 |
| `QEdiCROFOut18.cs` / `QEdiCRANOut` | QPTM EDI datasets | §9 CROF/CRAN ID3 |
| `HandleGenericScreenChangeEvent` / `HandleContractMaintenanceChange` / `CheckPPAReallocationDialogRequired` | `Quorum.QPTM.Web` / ServiceCore | §10 PPA pop-up |
| `RatchetScheduleController.cs`, `QUIControllerRatchetSchedule.cs`; dictionary in `Quorum.QPTM.ServiceCore` | `Quorum.QPTM.Web` / ServiceCore | §12 ratchet |
| `NomDetailBalancingHelper_Impl_Core.cs` (`SetReduceRecEngQty`/`IsQuantityLeftToReduce`) | nom-balancing core | §12 CAS ratcheting |
| `QResolverMDWQ.cpp` (`GetMinMDWQ`/`GetMdwq`) | `Quorum.QPTM.ClassicBatch` (shared w/ reports) | §12 storage MDWQ |
| `KRPTS_MDQ_MEAS_EXTERNAL_VW`, `KRPTS_MDQ_EXTERNAL.rpt`, `SP_QPTM_MDQ_ROLL_UP` | XCL DB / report repos | §11 XCL reports |

### Repos
- **`Quorum.QPTM.Web` / `.Web.Controllers`** — RFS wizard/Approvals, Offer/Bid/Award screens, Contract Maintenance, Ratchet Maintenance (Kendo).
- **`Quorum.QPTM.ClassicBatch`** — CRBIDEVAL, CRK_GEN, contract-gen, offer-to-rate, MDWQ, EDI out.
- **`Quorum.QPTM.ServiceCore`** / **`Quorum.QPTM`** — service layer, `QContractDataAccess`, ratchet dictionary, PPA event handlers.
- **`Quorum.QPTM.Metadata`** — grids, registered SQL, validations (`RuleCROFxxxxxx`, `RuleCRRRxxxxxx`, `RuleNNxxxxxxxx`, `K01010`, `K_RFSME020`).
- **IPWS (`QIPWS`)** — capacity-release export/import, `CapRelNaesb30*`.
- **`<CLIENT>.QPTM.Web / .ClassicBatch / .Metadata / .Database`** and client **`<CLIENT>.ESUITE.Database`** — overrides for TEP, HPE/HEP/PNGTS, XCL, ENT, GBG, EQC/EQT, APL, BLH, QTR (Williams), ONK/ONG (ONEGas), CMX, TGL, VGL, WWM. **Check the client repo/schema first** — many fixes are client-specific (XCL MDQ view, ENT split-action/PPA, TEP seasonal/CAS, HPE/HEP IPWS, BLH ratchet).

---

## 16. Escalation guidance

**Route to Engineering (Software Defect) when:**
- A **batch crashes from code/SQL** after data is ruled out: CRBIDEVAL/CRK_GEN (PQID + IBR data checked), `TSP` vs `TSP_NO` (#1735225), discount-offer loc-group rate (#1392863), seasonal-date failsafe (#1702160), S2S→P2P cap-type (#1607331).
- A **calculation is provably wrong** on correct inputs: capacity-available TSP join (#1696946), match vs competing award (#1458730), CAS/storage MDWQ rounding (#1601901/#1633392/#1734715), AOS shared-MDQ source field (#1775092), NETMDQRES first-row MDQ (#1674928), MDQ-ROLLUP As-Of (#1631014).
- A **web screen behaves differently from classic** and classic is correct: Recall `RuleCRRR000270` (#1579815), time-slice SplitAction (#1789425), PPA pop-up event handler (#1773033), VALIDATE_MDQ_REC_DEL (#1764767), RFS Approvals K01010 (#1783675).
- Provide: **PQID + process + exact error**, client + TSP + contract/offer/bid IDs, prod/acctg month, a repro, and whether it reproduces in **CORE/SUP**. Confirm fix availability in `Quorum.QPTM.ReleaseNotes` + the client hotfix branch (IntegrationBuild is empty — don't quote a build you haven't confirmed).

**Handle as Configuration / data (no core code) when:**
- **Seasonal dates** → set `USE_SEASNL_DATES=0` + correct `CRCTRL_OFFER_DTL` (§5).
- **IPWS** → TOC-Object Association single TOC, CAPREL POSTING key folder, `NAESB_ABBREV` populated, restart QPTM+IPWS services, empty/refresh the export folder (§8).
- **PPA pop-up** → `BLXREF_REALLOC_PPA` Object-ID mapping (#1784462); remember status-only changes don't trigger it.
- **Recall dup key** → dedupe `QCODE_RECALL_NOTIF_PERIOD` (#1724570).
- **NN00003075/EUT** → tie TOS to the validation rule (#1404268); CROF EDI → TPA-Maintenance CRNS grammar (#1781005).
- **XCL MDQ comparison report / roll-up** → view/SP change ships in the **XCL** repo as a client patch (not core).

**Treat as Expected behavior / user education (verify config + classic first):**
- **NN00003072 segmentation-on-the-fly** over-MDQ when a single segment exceeds KMDQ (#1726480) — working as designed; review Location Path Maintenance.
- **Insert a time-slice *between* two existing slices** — not supported; end-date the first, then begin the new (#1765986).
- **Contract status change alone** not triggering PPA — only date changes impacting a closed month do (#1784462).
- **MDQ "missing"/"duplicate" on the XCL report for old 2019 versions / long runtimes** — validate in the upgrade (#1794375).

**Service-restart / refresh first (no code):** IPWS "posted file but nothing on site" (restart QPTM+IPWS QPEC, check folder/TOC), long-running custom reports on out-of-support versions. Capture **MT/QPEC logs before** restarting.

---

*Skill created: 2026-06-14. Source: ADO QPTM bugs — WIQL matched 1008 (areas Energy Transportation + Maintenance\Midstream and Transportation; State Closed/Resolved; functional title terms), ~62 deep-read across 9 clusters. Build numbers INFERRED from iteration path + tags + dev/QA comments (IntegrationBuild empty on all) — confirm in Quorum.QPTM.ReleaseNotes / client hotfix branch. Overlap: Maintenance branch is mixed QPTM+TIPS; TIPS-only items dropped; dual-product items (storage ratchet→invoice/BLR_00 #1734715, Contract Maintenance→BLINVGEN seasonal-date billing) noted.*
*Key ADO bugs: A #1639052/#1379334/#1411874/#1461450/#1735225; B #1604135/#1702160/#1773394/#1607331/#1492803/#1683078/#1679806; C #1458730/#1696946/#1392863/#1430585; D #1644589/#1752977/#1783675/#1772388/#1797407/#1623105; E #1739076/#1775918/#1774746/#102441/#1370331/#1727472/#1759366; F #1579815/#1724570/#1781005/#1756196; G #1789425/#1731761/#1765986/#1773033/#1784462; H #216109/#242060/#1530880/#1631014/#1674928/#1379364/#1726480/#1775092/#1764767/#1404268; I #1607618/#1667506/#1601901/#1633392/#1734715/#1783407.*
