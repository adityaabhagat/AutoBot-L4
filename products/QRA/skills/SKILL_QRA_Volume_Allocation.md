# SKILL: QRA Volume / Production / Contractual Allocation Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — upstream oil & gas revenue accounting, myQuorum / On Demand suite)
**Scope:** The **volume-allocation front end** of QRA — everything that turns produced/measured volumes into allocated, contract-ready volumes that revenue distribution then prices and pays. Covers **Volume Allocation (VLA / Direct Revenue Input)** (VL031/VL040/VL100, VLCALCSPLT/VALCLCSPLT), **Production Allocation & the volume interface** (VA005/VA015/VA030/VA035, Staging Volume Upload, INT_ALLOC, the FI/IAN → QRA integration), **Contractual Allocation (CA)** (CA005/CA020, CACTRALLOC, market groups / MEG, masterlinks ML002), **Production Master Data** (PR005 properties, SP025 sales points, well completions, flow-grid connections PD051), **Volumetric / regulatory reporting** (OGP, RPT_JER036, ONRR/MMS royalty reporting), and **Gas Balancing** (GB010/GB015 imbalance).
**Companion / boundary:** This skill ends where the *allocated volume* is correct. Pricing, owner decimals (DOI/NRI), suspense, check write, ACH, 1099, journal and PPA-of-revenue belong to the Revenue-Distribution / Check-Write / Journal skills. **Allocation is upstream of revenue — when a check or distribution number is wrong, first decide whether the *allocated volume* is wrong (this skill) or the *pricing/decimal* is wrong (revenue skill).** Allocation is usually the messenger when volumes don't tie.

> **Evidence base:** Closed QRA cases in the volume-allocation category set (Production Allocation 128, Contractual Allocation 94, Volumetric Reporting 53, Gas Balancing 25, Volume Allocation 17, Production Master Data 14, Royalties 10, Wind Royalty 71, plus regulatory). Root-cause split across this set: **(blank) 95, Customer Cancelled 41, Customer Error 35, Software Defect 24, Training 23, Hardware/Software Change 16, Application Configuration 14**, Platform 11, Business Change 11, others. This skill mines the **~44 actionable** cases (Software Defect 24 + Application Configuration 14 + the handful of allocation-relevant Royalty/Wind defects) for fix recipes, plus ~40 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case and/or ADO work item observed during mining; where a mined case had no clear resolution it is marked *resolution pattern unclear*.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Contractual Allocation (CA020) failing on a flow grid / market group](#4-cluster-a--contractual-allocation-ca020-failing)
5. [Cluster B — Value Allocation (VL040 / VLCALCSPLT) fails — "theoretical of 0" / child records](#5-cluster-b--value-allocation-vl040--vlcalcsplt-fails)
6. [Cluster C — Volumes won't interface FI/IAN → QRA (VA035) / INT_ALLOC](#6-cluster-c--volumes-wont-interface-fiian--qra-va035--int_alloc)
7. [Cluster D — Market-group / bearer-percent (VL100 "sum ≠ 1", status flips to Pending)](#7-cluster-d--market-group--bearer-percent-vl100)
8. [Cluster E — Time slice / effective-date / masterlink (Big Pool, ML002, SP025/DO005/RC010)](#8-cluster-e--time-slice--effective-date--masterlink)
9. [Cluster F — Volumetric & regulatory reporting (OGP, RPT_JER036, ONRR)](#9-cluster-f--volumetric--regulatory-reporting)
10. [Cluster G — MMS / ONRR royalty reporting process failures (TRRYLMMS, TR010/TR011)](#10-cluster-g--mms--onrr-royalty-reporting-process-failures)
11. [Cluster H — Gas Balancing imbalance (GB015 / owners not in DOI)](#11-cluster-h--gas-balancing-imbalance)
12. [Cluster I — Import/interface definitions & batch step performance (FLOWCAL_VOLS, WLTSTARTSA)](#12-cluster-i--importinterface-definitions--batch-step-performance)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Screens, Processes & Repos](#16-key-screens-processes--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| **CA020** errors: "CA did not successfully allocate CA Equity Volumes" / "Found pipeline statement volumes, but no CA results were calculated" | New well added to a sales MP but the **pipeline (PL) override / pipeline statement was not increased** to cover the added volume; or CA Rules / masterlink gap | §4 — verify PL override vs grid volume; check CA005 rules; ML002 masterlinks (23-00897620 / ADO #1594775) |
| **CA020**: "CA Rules have not been entered for a measurement point/contract in the grid" | CA Rules missing in **CA005** for an MP/contract | §4 — RC010 eff-date must match the flow-grid connection's earliest eff date; a DB trigger then writes CA005 (25-01036725) |
| **CA020**: "Failed to find market group information… make sure all market groups for the grid are closed" / "Failed to populate the GMI staging table" | A **market group (MG) for the grid is still open / not Completed** | §4/§7 — close all MGs; if status flips back to Pending after VL100, see §7 (23-00921207) |
| **CA020 / process throws COM errors, can't input MMBTU into CA Results** | Invalid/unchecked masterlinks for the gas/oil flowgrid | §4 — ADO #1612983 (MAC, Closed) |
| **VL040 / VLCALCSPLT / VALCLCSPLT** "Failed to create child Value Allocation records… all well/completions have a theoretical of 0" / "no valid volume to allocate" | Value Allocation has **no volumes to use as theoreticals** for the child wells, or gross value/volume is 0 with plant-inlet volumes present | §5 — ADO #630582, #1448519; verify VL031 theoretical/gross inputs |
| **VA035** not populating / volumes from FI/IAN won't flow to QRA | FI/IAN → QRA **interface handshake**: VA must be opened/closed by a user with access before re-interfacing; or duplicate/overlapping MP disposition | §6 — open VA first, then re-send from FI/IAN (25-01003784); IAN-integration patch fixed duplicate-MP doubling (25-00999692) |
| **INT_ALLOC** fails / "unknown error condition" / adjustment volumes not reprocessing | Stale `PSTG_ALLOC_VOL` rows; or INT_ALLOC picked the *first* matching staging row, not the latest | §6 — clear `PSTG_ALLOC_VOL` for the period & rerun (22-00560531); restage for reprocess (24-00949190) |
| **VL100**: "DO Bearer group bearer percent sum is not equal to 1"; MEG groups flip Completed→Pending after VL100 | **Bearer-group decimal (BG_SUM)** not summing to 1 at 10-digit precision | §7 — ADO #1768726 (SGY, Closed) long-term fix; script #1770198 unblocks (25-01057020) |
| **Network processed in VA030 + CA020 but missing in VL100** | **RD flag in PD051** unchecked for that network | §7/§15 — check the RD (Revenue Distribution) flag on PD051 (23-00934333) |
| **Big Pool / CNX time slice**: new monthly slice won't create, or end-date won't come over | FI/IAN→QRA timeout / handshake: old slice end-dated in QRA but **new slice never sent** | §8 — disable IAN-QRA interface, create slice, re-send connections (ADO #210751) |
| **Well completion** "duplicate primary key" when end-dating an operator; **2nd completion** can't pass CA / ML002 | Overlapping completion timeslice / SP025 vs DO005 vs RC010 eff-date misalignment | §8 — align eff dates across SP025/DO005/RC010, rebuild ML002 (22-00825282, 23-00931823, 25-01007370) |
| **OGP / RPT_JER036 / volumetric report** stopped working / Crystal formula error | Report formula/field defect or report-config | §9 — RPT_JER036 Crystal "field name not known" (22-00830292); OGP report (22-00612459) |
| **MMS / ONRR royalty** process (TRRYLMMSRP/RF) fails / processes a fraction | Accounting month not rolled / preliminary-vs-final ordering / missing end-dated TR010 product rows | §10 — roll the acctg month first; add end-dated TR010 rows (26-01093185, 25-01045852) |
| **Gas balancing**: can't load an imbalance for an owner **no longer in the DOI** | Module forces owner to match the MGA/DOI exactly | §11 — script the GB015 rows in (22-00523696, 23-00908242) |
| Volume import file that worked last month now fails for all volumes | Import-definition column drift (e.g. extra/obsolete column) | §12 — compare the import def (FLOWCAL_VOLS / Merrick) to the file; remove the stale column (26-01084811, 22-00632237) |

---

## 2. Pipeline & Concepts

```
[Field measurement / FlowCal / Merrick files]            [FI / IAN allocation networks]
        │  Staging Volume Upload / import defs                    │  FI/IAN → QRA interface (connections, time slices)
        ▼                                                         ▼
[PSTG_ALLOC_VOL] ──INT_ALLOC──►  PRODUCTION ALLOCATION  ── VA005/VA015 (load) → VA030 (process) → VA035 (VA Results)
                                          │
                                          ▼  CONTRACTUAL ALLOCATION   CA020 → CACALCSPLT (splitter) → CACTRALLOC (calc) → PTRN_CA_VOL / PTRN_CA_VOL_ACT
                                          │     (uses CA005 rules, masterlinks ML002, market groups MG / MEG, pipeline-statement PL override)
                                          ▼  VALUE ALLOCATION (VLA)   VL031 (Direct Revenue Input) → VL040 (submit, VLCALCSPLT/VALCLCSPLT) → VL100
                                          │
                                          ▼
                                  ► REVENUE DISTRIBUTION / CHECK WRITE / JOURNAL  (other skills)
                                  ► VOLUMETRIC & REGULATORY REPORTING (OGP, RPT_JER036, ONRR/MMS royalty: TR010/TR011/TRRYLMMS)
                                  ► GAS BALANCING (GB010/GB015 imbalance)
```

### Key terms (QRA / upstream-accounting vocabulary)
- **Flow Grid** — the allocation unit: a network of measurement points (MPs), wells/completions and sales/disposition points for a product (100=Oil, 200=Gas, 400=Plant Products/NGL). Configured on **PD051** (Connections / Effective Date / Valid Products tabs).
- **MP (Measurement Point)** / **Measuring Point** — a metered point; mapped into flow grids via the Connections tab. Duplicate/overlapping MP "Valid Product" dispositions create double volumes (25-00999692).
- **VA (Volume / Production Allocation)** — VA005/VA015 load production & ticket volumes; **VA030** processes; **VA035 (VA Results)** is the allocated-volume output that CA and VLA consume. If VA035 is empty, nothing downstream works.
- **CA (Contractual Allocation)** — allocates VA volumes to **contracts** per **CA Rules (CA005)** and **market groups**. Run via **CA020**; the batch steps are `CACALCSPLT` (Contractual Allocation Splitter, writes/clears `PTRN_CA_VOL_ACT`) then `CACTRALLOC` (CA Calculation, `QFlowGrid.cpp` / `QContractUnit.cpp`, writes `PTRN_CA_VOL`). A grid finishing with **STATUS_CD = F** = failed.
- **Market Group (MG) / MEG** — grouping of owners/properties for CA & make-up (GMI) calculations; screens MG004/MG006. **All MGs for a grid must be Completed/closed** before CA can finish. **Bearer group / BG_SUM** = bearer-percent decimals that must sum to **1** (at full 10-digit precision) — a rounding drift causes the VL100 "sum ≠ 1" error.
- **VLA (Value Allocation) / DRI (Direct Revenue Input)** — VL031 holds DRI records (a **Value Allocation Parent Flag** marks a parent whose volume is split to child wells using **theoreticals**); **VL040** submits them (`VLCALCSPLT`/`VALCLCSPLT` = Value Allocation Splitter); **VL100** is the downstream volumetric/MEG step. "Theoretical of 0" = the engine has no volume to distribute to the child wells.
- **Masterlinks (ML002)** — the Measurement/Contract ↔ Well-Completion cross-reference build. CA can't run until masterlinks build; failures are almost always **eff-date misalignment** between **SP025** (sales-point), **DO005** (division-order), and **RC010** (rule/connection) for the well/completion.
- **FI / IAN** — Field Insights / the allocation app ("IAN") that feeds production networks into QRA. The **FI/IAN → QRA interface** sends connections and **time slices**; many "volumes won't come into VA035" and "can't create a new time slice" cases are interface-handshake issues, not QRA engine bugs (root cause often "prodops").
- **INT_ALLOC** — the batch that pulls staged volumes (`PSTG_ALLOC_VOL`) into allocation. **RD flag (PD051)** — Revenue Distribution flag; if unchecked, a network processes through VA030/CA020 but **drops out of VL100**.
- **PL override / pipeline statement** — the pipeline-volume figure CA reconciles equity volumes against; if a well is added but the PL override isn't raised, CA finds pipeline volumes it can't allocate and fails.
- **PTRN_CA_VOL / PTRN_CA_VOL_ACT** — CA results tables. "Failed to insert new records into PTRN_CA_VOL" surfaces during PPA / reverse-rebook of prior months.

---

## 3. Decision Tree

```
QRA volume-allocation case
│
├─ A batch/screen process failed? GET the SCREEN + PROCESS-STEP + PROCESS QUEUE ID (PQID) + exact error
│   ├─ CA020 → CACTRALLOC "no CA results / CA Equity Volumes" / "pipeline statement volumes but no CA"  → §4 (raise PL override; CA005 rules; ML002)
│   ├─ CA020 "CA Rules have not been entered…"                                                          → §4 (CA005 / RC010 eff-date trigger)
│   ├─ CA020 "Failed to find market group information / GMI staging"                                     → §4/§7 (close all MGs)
│   ├─ VL040 → VLCALCSPLT/VALCLCSPLT "child Value Allocation records / theoretical of 0 / no valid volume"→ §5 (theoreticals/VL031 inputs; ADO #630582/#1448519)
│   ├─ VL100 "bearer percent sum ≠ 1" / MEG flips Completed→Pending                                      → §7 (BG_SUM decimal; ADO #1768726 + script #1770198)
│   ├─ INT_ALLOC fails / adjustments not reprocessing                                                    → §6 (clear PSTG_ALLOC_VOL / restage)
│   ├─ MMS/ONRR royalty TRRYLMMSRP/RF fails                                                              → §10 (roll acctg month; TR010 end-dated rows)
│   └─ OGP / RPT_JER036 / volumetric report errors                                                       → §9
│
├─ Volumes won't appear where expected (no process crash)?
│   ├─ VA035 empty / FI-IAN volumes not flowing in                                                       → §6 (interface handshake; open VA before re-interface)
│   ├─ Network processed VA030+CA020 but missing in VL100                                                → §7 (RD flag in PD051)
│   └─ Double / duplicate volumes in VA035                                                               → §6 (overlapping MP disposition; IAN patch)
│
├─ Can't save / end-date / build master data?
│   ├─ New monthly time slice won't create (Big Pool / CNX)                                              → §8 (disable IAN-QRA interface; new slice never sent — ADO #210751)
│   ├─ Well-completion "duplicate primary key" / 2nd completion can't pass CA / ML002 won't build         → §8 (align SP025/DO005/RC010 eff dates; rebuild ML002)
│   └─ Import file that worked last month fails for all volumes                                          → §12 (import-def column drift)
│
├─ Gas balancing: imbalance owner no longer in DOI?                                                       → §11 (script GB015 rows; can't match MGA)
│
└─ "How do I…" / volumes look wrong but follow inputs / JIB-run load error / audit                        → §15 Expected-Behavior FAQ
```

---

## 4. Cluster A — Contractual Allocation (CA020) failing

**The single largest actionable allocation signature.** A flow grid runs VA030/VA035 fine, then **CA020 fails** (grid completes with STATUS_CD = F). The batch log shows the `CACALCSPLT` splitter step succeed, then `CACTRALLOC` (CA Calculation) error. Heavy clients: **Mach (MAC), BP GOM, Surge, Encino, Sentinel Peak**.

**Representative error chain (23-00897620, Mach FG 1160G — `QFlowGrid.cpp`):**
```
INFO  CONTRACTUAL ALLOCATION COMPLETED … WITH A STATUS OF F   (QPSContractualAllocation.cpp)
ERROR CA did not successfully allocate CA Equity Volumes.      (QFlowGrid.cpp:1551)
ERROR Found pipeline statement volumes, but no CA results were calculated.  (QFlowGrid.cpp:11612)
```

**Root causes & fixes seen:**
- **New well added to a sales MP, but the pipeline (PL) override / pipeline statement was not raised** to cover the added volume → CA finds pipeline volume it can't allocate and fails. This was the actual root cause of the Mach FG 1160G case — **ADO #1594775** ("MAC – 23-00897620 – FG 1160G Failing CA", Closed): *"while the client added a new well to sales MP 10175G for this grid/prdn dt, they did not increase the PL override to account for the increased volume from the new well."* **Fix: raise the PL override / correct the pipeline statement, re-run CA020.**
- **CA Rules missing in CA005 / RC010 eff-date mismatch (25-01036725, CNX 102-GAS WCAA APEX):** "CA Rules have not been entered for a measurement point/contract." Fix: set the **RC010 Effective-From date to match the Flow Grid Connection's earliest effective date** for the erroring MPs; **delete and re-insert** the RC010 rows (don't just edit the date) — a DB trigger then inserts the CA Rules into **CA005**. (Long-term RCA tracked under 25-01032589; root cause was FI/IAN→QRA interfacing.)
- **Market groups not closed (23-00921207, MID grids):** "Failed to find market group information… make sure all market groups for the grid are closed" + "Failed to populate the GMI staging table." Fix: **close/complete every MG for the grid** before CA. (If they flip back to Pending after VL100, see §7.)
- **Invalid / unchecked masterlinks (ADO #1612983, MAC, Closed):** "Contractual Allocation Processing Throwing COM Errors and Unable to Input MMBTU into CA Results" on CA020 flow grid 1482G — CA processed correctly once invalid/unchecked masterlinks for the gas/oil flowgrids were addressed. See §8 for the ML002 build.
- **DOI Change Warning flags blocking the grid (24-00949469, Sentinel Peak FG 19):** the grid errored with a "DO change warning"; **DOI Change Warning Flags were checked** — unchecking them let the grid process. (Application Configuration.)
- **PPA / reverse-rebook insert failures (22-00661351 / 22-00661358, BP GOM):** "Failed to insert new records into PTRN_CA_VOL" for a range of prior periods during a major reverse/rebook; client had hit the same in UAT and it was cleared with a script to **remove the parent records** before re-inserting. *Resolution pattern: data script to clear the colliding PTRN_CA_VOL parents, then reprocess the prior months.*

**Fix recipe:**
1. Get the **flow grid + production date + PQID** and read the CA020 batch messages; note whether the failure is at `CACALCSPLT` (splitter/setup) or `CACTRALLOC` (calculation).
2. "CA Equity Volumes / pipeline statement volumes but no CA results" → **a well/volume changed but the PL override didn't** (ADO #1594775). Raise the override, re-run.
3. "CA Rules have not been entered" → fix **RC010 eff-dates to match the flow-grid connection**, delete+re-insert the rows so the trigger writes **CA005** (25-01036725).
4. "Market group information / GMI staging" → **close all MGs** for the grid (23-00921207).
5. COM errors / can't write MMBTU → **rebuild masterlinks (ML002)**, fix eff-date alignment (§8), ADO #1612983.
6. PTRN_CA_VOL insert failure on PPA/reverse-rebook → escalate for the parent-clear script (BP pattern).

---

## 5. Cluster B — Value Allocation (VL040 / VLCALCSPLT) fails

A distinct **Software Defect / setup** cluster on the **Value Allocation (VLA)** path. The user submits DRI records in **VL040** and the **Value Allocation Splitter** (`VLCALCSPLT` / `VALCLCSPLT`) fails.

**Symptoms (verbatim):**
- "ERROR – Failed to create child Value Allocation records. Check setup for any issues. WARNING – All well/completions in this grid have a theoretical of 0." (26-01064031, 250-grid UAT batch)
- "There is no valid volume to allocate volume for this grid." → VA035 shows no sales line (25-01003784)
- Oil-grid variant: `RONL_MI_LINK` insert fails — *"Cannot insert the value NULL into column 'MANL_INPUT_ID'"*, "MI Link Eff Dt records NOT written to the database", `VALCLCSPLT` stops the process (26-01064031).

**Root causes & fixes seen:**
- **The engine has no volumes to use as theoreticals for the child wells** — confirmed root cause in **ADO #1448519** (Closed, "DRI Value Allocated – VALCLCSPLT fails"): *"the issue is that you don't have all the necessary volumes to act as theoreticals for the wells."* This is the literal meaning of "theoretical of 0."
- **Gross value/volume = 0 while plant-inlet volumes are non-zero** — **ADO #630582** (Closed, "BEP – VL040 VLCALCSPLT Fails When Processing Gas & NGLs Together"): when a DRI has plant-inlet volumes but 0 gross value/volume, the splitter can't use the gross ratio. **Fix: Value Allocation was enhanced to allocate these volumes through the flow-grid theoretical engine** instead of the gross value/volume ratio, so child VLA-DRI wells distribute even when gross value & volume are both 0. Confirm the build includes #630582.
- **Flow-grid / MP setup gaps (26-01064031, Riley UAT):** of 250 grids, 226 failed simply because **no valid Gross Volume/Value was input via VL031**; the remaining 24 failed on setup ("theoretical of 0" gas/NGL, null `MANL_INPUT_ID` oil). Resolution: **flow-grid / MP configurations updated** per engineering recommendation. → mostly a **VL031 input / flow-grid setup** problem, not an engine bug.

**Fix recipe:**
1. Get the **DRI ID / flow grid + production date + PQID**. Open **VL031** and confirm there is a **valid Gross Volume/Value** and that the **Value Allocation Parent Flag** + child DRI records are present and CS-Successful.
2. "Theoretical of 0" / "no valid volume" → the parent has **no volume to distribute as theoreticals** (ADO #1448519). Confirm the theoretical volumes feeding the wells exist for that grid/date.
3. Plant-inlet volumes with 0 gross → confirm the **#630582** enhancement (theoretical-engine allocation) is in the build.
4. Oil-grid null `MANL_INPUT_ID` / MI-Link not written → **MP/flow-grid mapping config** fix (26-01064031); check the Connections tab (§ Cluster — missing production meters, 26-01079482).

---

## 6. Cluster C — Volumes won't interface FI/IAN → QRA (VA035) / INT_ALLOC

"My volumes are in FI/IAN (or in staging) but they're not in **VA035**" — almost always the **interface handshake**, an **overlapping/duplicate MP**, or **stale staging rows**, not a core allocation bug.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| FI/IAN gas sales present but **VA035 not populating** sales line; resending from FI/IAN doesn't help | The **VA must be opened (by a user with the right access) before re-interfacing** from FI/IAN | RCA: a Quorum engineer **opened the VA with his access, then re-interfaced from FI/IAN** and the volumes flowed (25-01003784) | 25-01003784 |
| **Duplicate / double volumes in VA035** since go-live for a set of MPs (FG 20-OIL, 10 MPs) — duplicate "Valid Product" disposition = 91 | Overlapping MP record / duplicate disposition created double production rows every month | **The patch that fixes the IAN integration addressed this**; for historical months either reprocess VA per month or script-delete the duplicate VA035 sequence rows | 25-00999692 (rel. 25-00998984) |
| FI/IAN volumes (FG 229/40-OIL) **do not interface to QRA VA035** | FI/IAN → QRA interface (prodops side) | *resolution pattern unclear from mined case*; tracked as a prodops integration issue | 25-01004226 |
| `INT_ALLOC` fails with "unknown error condition" | Stale rows in `PSTG_ALLOC_VOL` | Workaround: `DELETE FROM PSTG_ALLOC_VOL WHERE VOLUME_PERIOD_CD = 'MONTH'`, then re-run **Staging Volume Upload + INT_ALLOC** | 22-00560531 |
| Adjustment volumes in staging but **INT_ALLOC didn't repopulate wells** (already marked processed) | The scheduled INT_ALLOC picks the **first** staging row matching the criteria, not the latest — there is **no timestamp compare** (rare to have two deliveries in a period) | Manually **re-stage the records for reprocessing**; behavior is by design for cost (24-00949190) | 24-00949190 |
| Allocation "Error to Accounting" on submit; manually-added MP disappears after save | Permission / interface glitch | *resolution pattern unclear*; verify user permissions and the interface state | 22-00640496 |
| FV / Field Insights allocations not interfacing to QRA (older) | Integration defect | Patch | 22-00628747, 22-00612474 |

**Fix recipe:** before assuming an allocation engine bug, (1) **open the VA for that grid/date with proper access, then re-send from FI/IAN** (25-01003784); (2) for doubles, look for **overlapping MP / duplicate "Valid Product" disposition** in PD055 and confirm the **IAN-integration patch** is applied (25-00999692); (3) for INT_ALLOC, **clear `PSTG_ALLOC_VOL` and re-stage** (22-00560531, 24-00949190). Many of these are dispositioned by ProdOps, not product engineering.

---

## 7. Cluster D — Market-group / bearer-percent (VL100)

**Symptom (25-01057020, Surge):** `VL100 error – market groups DO Bearer group bearer percent sum is not equal to 1 for the specified production date`. MEG groups show **Pending**; Division Order updates them to **Completed**, but running VL100 flips them **back to Pending**.

**Root cause & fix:**
- The **bearer-group decimals (BG_SUM)** for the DO bearer group **do not add up to 1 at 10-digit precision** — **ADO #1768726** (Bug, Closed, *"{SGY} – {QRA} – {Bearer group BG_SUM 10-digit decimal not adding up to 1}"*) is the **long-term fix**. The immediate unblock was a **Script Deployment, ADO #1770198** ("SGY Bearer group decimal change", Closed) — a one-time decimal correction so the group sums to 1. Same family resolved earlier under closed case 25-01013101 ("resolved via script").
- **Network processed VA030 + CA020 but missing in VL100 (23-00934333):** root cause was the **RD (Revenue Distribution) flag unchecked in PD051** for that network. **Fix: check the RD flag in PD051** for the missing network. (This is the go-to check whenever a network "disappears" only at the VL100 step.)
- **Marketing group flips Completed→Pending (25-01014835, Surge):** Software Defect in the status handling — same bearer/MEG family; tracked for product fix. *If a script is needed, it is the BG_SUM decimal correction above.*

**Fix recipe:** "bearer percent sum ≠ 1" / MEG won't stay Completed → it is the **BG_SUM 10-digit decimal** (ADO #1768726); request the **decimal-correction script** (per #1770198) to unblock the close, and confirm the long-term fix build. "Network missing only in VL100" → **RD flag in PD051** (23-00934333).

---

## 8. Cluster E — Time slice / effective-date / masterlink

A steady stream of "can't create a time slice / can't end-date / 2nd completion won't allocate" issues that resolve as **eff-date alignment** or **interface-handshake** fixes. Heavy client: **CNX (Big Pool network)**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **CNX Big Pool** new monthly time slice won't create / December end-date won't come over (PD051 Connections tab differs from Effective-Date & Valid-Products tabs) | FI/IAN → QRA interface timeout / handshake: the old slice gets **end-dated in QRA but the new slice is never sent** | **Disable the IAN-QRA interface**, create the new "current-month – open-ended" slice, re-enable and **re-send the prior-month connections** to complete the end-date | 22-00824974, 26-01085745, 26-01090354, 26-01091902; **ADO #210751** ("CNX Timeout Error When Date Splitting Big Pool Network", Closed) |
| **Well completion "duplicate primary key"** when end-dating the operator on the 2nd row | Overlapping completion timeslice the UI doesn't surface | *resolution pattern unclear from mined case*; treat as overlapping-timeslice data fix | 22-00825282 |
| **2nd completion on existing MP** — ML002 masterlink won't build: "There is no matching Prop/DOI for the WC and MPC in the Prop WC xref" | **SP025 / RC010 / DO005 eff-dates out of sync** for the new completion | Align SP025 (sales point) + RC010 (MP-contract xref) + DO005 (division order) eff-from/to dates for the completion, then rebuild **ML002** | 23-00931823 |
| ML002 "No Masterlinks built for Well/Compl…" | Out-of-sync Eff From/To dates between **SP025 and DO (DO005)** | Correct the eff-date alignment, rebuild ML002 | 25-01007370 |
| New time-slice creation in IAN requires interface disabled each month (Big Pool) | Process/handshake | ProdOps disables interface on request; resolved | 22-00824974 |

**Fix recipe:** for **Big Pool / CNX** time-slice issues, the proven sequence is **disable the IAN-QRA interface → create the new open-ended slice → re-enable → re-send the prior connections** (ADO #210751; the failure mode is "old slice end-dated, new slice never sent"). For **masterlink / 2nd-completion** failures, the fix is almost always **SP025 ↔ RC010 ↔ DO005 effective-date alignment** for the well/completion, then rebuild **ML002** (23-00931823, 25-01007370). Always verify-SELECT before any timeslice DELETE/UPDATE.

---

## 9. Cluster F — Volumetric & regulatory reporting

Reports that consume allocated volumes (state OGP, GL owner volumes/values, ONRR settings).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **RPT_JER036** (GL Owners Values and Volumes) fails: Crystal "Error in formula … 'numbervar ownrval' / 'ownernetamt' … This field name is not known" | Report (.rpt) formula / field-binding defect | Report fix to the JER036 Crystal report | 22-00830292 |
| **LA OGP – Preliminary** report stopped functioning (worked last month) | Report-config / formula | *resolution pattern unclear from mined case*; treat as report defect | 22-00612459 |
| **ONRR royalty payment amount** wrong | **JE Group Code** config | Changed JE Group Code to **CD1 with all fields open** | 25-01009451 |
| **Incorrect flow grid settings for ONRR** | Flow-grid config | Corrected the flow-grid settings (config) | 25-01009459 |
| **Volumetric Reporting File** won't run for a user | Missing security group + config | Added the security group to the user, edited configs to allow the file to run | 24-00945921 |
| Volume-upload process **requiring well tests** (Sable) | Volume-upload config requiring well-test records | Config change to the volume-upload requirement | 25-01008150 |
| WI owner allowed a **TEG / tax-exempt flag** that should be blocked (Gulfport, VL100) | Validation gap allowing an invalid flag combination on a WI owner | Software Defect — validation should block it | 22-00855056 |
| Missing **lease fuel** on wells after ND Oil reverse/rebook | Reverse/rebook volumetric defect | Software Defect | 22-00647308 |

**Fix recipe:** distinguish **report defects** (RPT_JER036 Crystal formula, OGP — fix/ship the report) from **config** (ONRR JE Group Code = CD1, flow-grid settings, security group for the volumetric file). For "report worked last month, now fails," check for a recent metadata/report change before escalating.

---

## 10. Cluster G — MMS / ONRR royalty reporting process failures

Federal royalty (MMS/ONRR) reporting runs as **preliminary** (`TRRYLMMSRP`) then **final** (`TRRYLMMSRF`); they read the **TR010/TR011** royalty setup.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **TR011** error on MMS royalty reporting | Missing end-dated product rows on **TR010** | **Add end-dated records for all products on TR010** — cleared the TR011 error (client to validate if behavior is expected) | 26-01093185 |
| MMS reporting process (TRRYLMMSRP preliminary / TRRYLMMSRF final) **fails or processes only a fraction** after a provided script | The **accounting month had not been rolled out** | **Post the entry to roll out the accounting month**, then re-run; preliminary must complete before final | 25-01045852, 25-01047455 (rel. 25-01033813) |

**Fix recipe:** for MMS/ONRR royalty process failures, first confirm the **accounting month is rolled** (25-01045852), and that **TR010 has end-dated rows for all products** the report expects (26-01093185). Run **preliminary (TRRYLMMSRP) to completion before final (TRRYLMMSRF)**. These recur per close cycle — treat as a checklist, not a defect, unless the data is correct and it still fails.

---

## 11. Cluster H — Gas Balancing imbalance

**Symptom (22-00523696 / 23-00908242, Mach/Cimarex):** owners have a **gas imbalance but are no longer in the DOI** (e.g. elected out of a workover, will return after payout). The Gas Balancing module **forces the load to match the MGA/DOI exactly**, so the imbalance can't be loaded.

**Root cause & fix:** the module's validation requires the owner to exist in the current DOI/MGA. Adding each missing owner at 0% interest is undesirable after processing. **Resolution: a script imports the imbalance rows directly into GB015** (the same approach used across both cases). The underlying gap (no transaction type for "owner elected out of workover / not in DOI") is a known limitation. **GB010** holds the Gas Balancing transaction types.

**Fix recipe:** for "can't load an imbalance for an owner not in the DOI," **script the rows into GB015** (22-00523696, 23-00908242) rather than back-loading 0% DOI lines. Confirm the imbalance belongs to the owner and verify-SELECT before the insert.

---

## 12. Cluster I — Import/interface definitions & batch step performance

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Volume import file that **worked last month now fails for all volumes** (new Merrick files, even a 1-line old file fails) | Import-definition / file-format drift | **Patch** to the import handling | 22-00632237 |
| **FLOWCAL_VOLS** import bringing in an obsolete column (`OBS_PRES`) | Import def had a column not needed/valid for the client | **Remove `OBS_PRES` from the FLOWCAL_VOLS Import Definition** and check the change into the client ADO repo (PR) — `SELECT * FROM QARCH_CTRL_IMPEXP_FILE_DEF WHERE IMPEXP_ID = 'FLOWCAL_VOLS'` | 26-01084811 |
| **FLOWCAL_VOL** import-def update check-in | Same family — import-def column change | PR to remove the column | 26-01084811 |
| **WLTSTARTSA** (Well Test Interface) "Completed with System Errors", hung 14 hrs, query timeouts on `Upd_DelWellTestRecs` / `DEL_OldStagingRecs` / `DEL_PurgeFlag` | Performance — purge/delete SQL timing out | **Performance code fix by Maintenance Engineering**, consumed via the February hotfix to 2020.09 | 22-00548400 |
| Oil flow grids **missing production meters** (VLA DRI issues) | MPs not mapped on the flow-grid Connections tab; some duplicate mappings | **Map the missing production meters in the flow-grid Connections tab**; clean up duplicate mappings | 26-01079482 |
| Flow grid **company change** | Company set wrong on the grid | Updated tables to reflect the correct company | 23-00911744 |

**Fix recipe:** for import failures, **diff the import definition against the incoming file** (`QARCH_CTRL_IMPEXP_FILE_DEF`) — the common cause is a column the def expects but the file lacks (or vice-versa); remove/realign the column and **check the change into the client ADO repo** (26-01084811). Batch-step timeouts on purge/delete SQL are performance code fixes (WLTSTARTSA, 22-00548400).

---

## 13. Known ADO Items

| ADO # | Project | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|---|
| **#1768726** | QuorumSoftware | Bug / **Closed** | SGY – QRA – Bearer group BG_SUM 10-digit decimal not adding up to 1 | §7 | 25-01057020 |
| **#1770198** | myQuorum Cloud | Script Deployment / **Closed** | SGY Bearer group decimal change (the unblocking script) | §7 | 25-01057020 |
| **#1594775** | QuorumSoftware | Bug / **Closed** | MAC – 23-00897620 – FG 1160G Failing CA (PL override not raised for added well) | §4 | 23-00897620 |
| **#1612983** | QuorumSoftware | Bug / **Closed** | MAC – Contractual Allocation throwing COM errors / can't input MMBTU into CA Results (CA020 FG 1482G) | §4 | (Mach CA family) |
| **#630582** | QuorumSoftware | Bug / **Closed** | BEP – VL040 VLCALCSPLT fails processing Gas & NGLs together (0 gross + plant-inlet → theoretical engine) | §5 | — |
| **#1448519** | QuorumSoftware | Bug / **Closed** | DRI Value Allocated – VALCLCSPLT fails (no volumes to act as theoreticals) | §5 | — |
| **#210751** | QuorumSoftware | Bug / **Closed** | CNX "Timeout" Error When Date Splitting Big Pool Network (slice end-dated but new slice never sent) | §8 | 22-00824974 + Big Pool family |

> Several actionable cases were dispositioned **operationally / by ProdOps** (FI/IAN interface, scripts) with no single product WI surfaced in code search: the **IAN-integration patch** for duplicate-MP doubling (25-00999692), VA-reopen-then-reinterface (25-01003784), `PSTG_ALLOC_VOL` clear + INT_ALLOC rerun (22-00560531), the **RC010 eff-date / CA005 trigger** fix (25-01036725, long-term RCA 25-01032589), and the BP **PTRN_CA_VOL** parent-clear script for reverse/rebook (22-00661351/358). The **WLTSTARTSA** performance fix shipped via the Feb hotfix to 2020.09 (22-00548400). Confirm exact build/patch in the QRA release notes before stating fix availability. The FI/IAN feeder issues are frequently rooted in **prodops**, not the QRA engine.

---

## 14. Diagnostic SQL

> **Caveat:** QRA runs on SQL Server (per-client DBs, e.g. `REP_PRDA1UPS_QRA`). Table/column names below are taken from case repro text and ADO; **verify against the client DB before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Stale staging rows blocking INT_ALLOC (§6, 22-00560531)
SELECT VOLUME_PERIOD_CD, COUNT(*) FROM PSTG_ALLOC_VOL GROUP BY VOLUME_PERIOD_CD;
-- Workaround (Production Allocation integration): DELETE FROM PSTG_ALLOC_VOL WHERE VOLUME_PERIOD_CD = 'MONTH';  then rerun Staging Volume Upload + INT_ALLOC.

-- B. Duplicate MP "Valid Product" disposition creating double VA035 volumes (§6, 25-00999692)
--    Look on PD055 for an MP with two rows of the same disposition (e.g. 91) in one time slice.
SELECT MP_NO, DISP_CD, COUNT(*) dup_ct
FROM   <VA035 results / MP valid-product table>
WHERE  GRID_NO = '<GRID>' AND PRDN_DT = '<PRDN_DT>'
GROUP BY MP_NO, DISP_CD HAVING COUNT(*) > 1;

-- C. CA results / status for a grid (did CA finish F = failed?) (§4)
SELECT GRID_NO, PRDN_DT, MAJ_PROD_CD, STATUS_CD, OPER_BUS_SEG_CD
FROM   PTRN_CA_VOL          -- and PTRN_CA_VOL_ACT for the splitter side
WHERE  GRID_NO = '<GRID>' AND PRDN_DT = '<PRDN_DT>';

-- D. CA Rules present for the grid's MPs/contracts? (§4, "CA Rules have not been entered")
SELECT * FROM CA005_<rules table> WHERE GRID_NO = '<GRID>';   -- compare RC010 eff-from to the flow-grid connection eff-from

-- E. Effective-date alignment for a 2nd completion / masterlink build (§8, 23-00931823, 25-01007370)
--    SP025 (sales point), RC010 (MP-contract xref), DO005 (division order) must agree on EFF_FROM/EFF_TO.
SELECT 'SP025' src, EFF_FROM_DT, EFF_TO_DT FROM <SP025 table> WHERE WELL_NO='<W>' AND COMPL_NO='<C>'
UNION ALL SELECT 'RC010', EFF_FROM_DT, EFF_TO_DT FROM <RC010 table> WHERE MP_NO='<MP>'
UNION ALL SELECT 'DO005', EFF_FROM_DT, EFF_TO_DT FROM <DO005 table> WHERE WELL_NO='<W>';

-- F. Bearer-group decimals not summing to 1 (§7, 25-01057020 / ADO #1768726)
SELECT MEG_GRP, SUM(BEARER_PCT) bg_sum
FROM   <DO bearer group table>
WHERE  PRDN_DT = '<PRDN_DT>'
GROUP BY MEG_GRP HAVING ABS(SUM(BEARER_PCT) - 1) > 0.0000000001;   -- 10-digit precision

-- G. Network present after CA but missing at VL100 → RD flag (§7, 23-00934333)
SELECT GRID_NO, RD_FL FROM <PD051 flow-grid connections table> WHERE GRID_NO = '<GRID>';  -- RD_FL must be checked

-- H. Import-definition column drift (§12, 26-01084811)
SELECT * FROM QARCH_CTRL_IMPEXP_FILE_DEF WHERE IMPEXP_ID = 'FLOWCAL_VOLS';

-- I. Find the failing allocation step + error by Process Queue ID
--    Get PQID from the user (e.g. CA020 PQID 9220194, VL040 PQID 7260765), then read the batch messages for that PQID + step.
```

---

## 15. Expected-Behavior / User-Education FAQ

~23 Training + ~35 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Volume load errors – **VA005 / VA015 / JIB run**" | Customer Error — wrong load parameters / file for the JIB or volume run; re-load with correct inputs | 26-01098442, 26-01098434, 26-01093221 |
| "Network processed VA030 **and** CA020 successfully but is **missing in VL100**" | **RD flag in PD051 unchecked** for that network — check it (not a bug) | 23-00934333 |
| "**2nd completion** on an existing MP — can't pass CA / ML002 won't build" | Customer setup — **SP025/RC010/DO005 eff-dates out of sync** for the new completion; align them and rebuild masterlinks | 23-00931823, 25-01007370 |
| "**CA020 errors** for our volume allocations" / "problems with FG 20-GAS / 229-Gas not populating sales-03" | Usually master-data: missing CA rules, MGs not closed, or the **VA must be opened before re-interfacing from FI/IAN** | 23-00921887, 25-01007370, 25-01003784 |
| "QRA MID error: **Failed to find market group information** for properties in the grid" | All **market groups for the grid must be closed/Completed** before CA — close them | 23-00921207 |
| "**IntAlloc failure to populate**" / "adjustment volumes didn't reprocess" | INT_ALLOC takes the **first** matching staging row (no timestamp compare); **re-stage** the records to reprocess | 24-00949190, 24-00943999 |
| "**QP043 not going to VL031**" / "Oil grid not showing for flow-grid upload" | Setup/process — verify the grid/DRI setup and upload selection (user/config) | 26-01071213, 25-01008151 |
| "Can I **delete a well-completion record** / add attachments to a DOI after approval / handle Pending DOIs?" | Training — documented procedures; deletion and post-approval edits have rules | 25-01034727, 25-01041220, 25-01032150 |
| "**GB010 Gas Balancing transaction type**" question | Training — explain the transaction-type options on GB010 | 25-01041596 |
| "**TR015 – No Data Found**" / "MMS reporting processed in error" | Training — TR015 returns nothing when the royalty setup/period has no data; roll the month / fix setup | 25-01032601, 25-01045159 |
| "**Water Volumes** upload into QRA & QCA" / "QRA Volume Allocation upload issue" | Training — water/volume upload procedure & file format | 24-00987103, 24-00980209, 24-00949486 |
| "**Pressure base** error — template columns not populating" | Customer Error — pressure-base / template config; populate the right template columns | 25-01009457 |
| "QQM Volume Allocation report (PRD) not working" / "QRM widget disappears each morning" | Often a QQM/Web-preferences setting — set Web Intelligence to **HTML** in preferences (26-01093638); widget/UX, not allocation | 24-00984473, 24-00977019, 26-01093638 |

**Tell-tale it's user/expected:** a network that "vanishes" only at **VL100** (RD flag in PD051); a **2nd-completion / masterlink** failure (eff-date alignment); **VA005/VA015/JIB** load errors (wrong inputs); "market group information" errors (MGs not closed); **IntAlloc** not reprocessing (re-stage); and FI/IAN "volumes won't come in" that clear once the **VA is opened and re-interfaced**. Verify the **flow-grid / MP / SP025-DO005-RC010 setup and the FI/IAN handshake** before treating it as a defect.

---

## 16. Key Screens, Processes & Repos

### Screens (QRA)
| Screen | Purpose |
|---|---|
| **VA005 / VA015** | Load production volumes / ticket volumes (JIB & volume runs) |
| **VA030 / VA035** | Process production allocation / **VA Results** (allocated volumes consumed by CA & VLA) |
| **CA005** | CA Rules (MP/contract); written by a DB trigger from RC010 eff-dates |
| **CA020** | Run Contractual Allocation (steps CACALCSPLT → CACTRALLOC) |
| **MG004 / MG006** | Market group setup; must be Completed before CA finishes |
| **VL031** | VL Direct Revenue Input (DRI); Value Allocation Parent Flag |
| **VL040** | VLA Flow Grid Selection / Submittal (steps VLCALCSPLT / VALCLCSPLT) |
| **VL100** | Downstream volumetric / MEG / bearer-group step (bearer percent must sum to 1) |
| **PD051 / PD055** | Flow Grid Connections / Effective-Date / Valid-Products tabs; MP valid-product dispositions; **RD flag** |
| **SP025 / DO005 / RC010** | Sales point / Division order / MP-contract xref — eff-date alignment for masterlinks |
| **ML002** | Masterlink (Measurement/Contract ↔ Well-Completion) build |
| **GB010 / GB015** | Gas Balancing transaction types / imbalance load |
| **TR010 / TR011 / TR015** | Royalty (MMS/ONRR) reporting setup & output |

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **Staging Volume Upload + INT_ALLOC** | Bring staged volumes into allocation | Clear `PSTG_ALLOC_VOL` if it fails (§6); picks first matching staging row |
| **CA020** → `CACALCSPLT` / `CACTRALLOC` | Contractual Allocation | `QFlowGrid.cpp`, `QContractUnit.cpp`, `QPSContractualAllocation*.cpp`; STATUS_CD = F = failed |
| **VL040** → `VLCALCSPLT` / `VALCLCSPLT` | Value Allocation Splitter | "theoretical of 0" / 0-gross + plant-inlet (§5) |
| **TRRYLMMSRP / TRRYLMMSRF** | MMS/ONRR royalty preliminary / final | Roll the acctg month first; TR010 end-dated rows (§10) |
| **WLTSTARTSA** | Well Test Interface | Purge/delete-SQL timeout, perf fix (§12) |
| **FI/IAN → QRA interface** | Send networks/connections/time slices | Disable to create a new slice (Big Pool); open VA before re-interfacing (§6/§8) |

### Code locations (confirmed via ADO)
| Symbol | Cluster |
|---|---|
| `QFlowGrid.cpp` ("CA did not successfully allocate CA Equity Volumes", "Found pipeline statement volumes but no CA results") | §4 |
| `QPSContractualAllocationSplitter.cpp` / `QPSContractualAllocation.cpp` / `QContractUnit.cpp` (CACALCSPLT/CACTRALLOC) | §4 |
| `RONL_MI_LINK` / `RONL_MI_LINK_EFF_DT` (MANL_INPUT_ID null on VALCLCSPLT) | §5 |
| `PTRN_CA_VOL` / `PTRN_CA_VOL_ACT` (CA results) | §4 |
| `QARCH_CTRL_IMPEXP_FILE_DEF` (import definitions) | §12 |

### Repos
- **QRA / On Demand upstream** product code is split across the **QuorumSoftware** project (core CA/VLA engine — the `Q*Allocation*` C++ and the QRA Web/metadata screens) and the **myQuorum Cloud** project (FI/IAN integration, ProdOps scripts/script-deployments). **Client-specific metadata/import-def/export-def changes are checked into the client's own ADO repo** (e.g. the FLOWCAL_VOLS / WELLSFARGO export-def PRs) — always confirm the client repo for config check-ins. The FI/IAN feeder side is frequently owned by **ProdOps**, not the QRA engine team.

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A batch **step** crashes from a code bug on correct setup: VLA splitter can't allocate 0-gross+plant-inlet via the gross ratio (#630582); CA throwing COM errors with valid masterlinks (#1612983); WLTSTARTSA purge-SQL timeout (22-00548400, perf fix); reverse/rebook `PTRN_CA_VOL` insert collision (BP family).
- A **calculation/validation** is provably wrong: bearer-group BG_SUM not summing to 1 at 10-digit precision (#1768726); WI owner allowed an invalid TEG/tax-exempt flag (22-00855056); missing lease fuel after ND reverse/rebook (22-00647308).
- Provide: **screen + process step + PQID + exact error**, client + grid + production/accounting month, the MP/contract/completion, and a repro. Confirm fix availability in the QRA release notes and the linked WI's build.

**Handle as Configuration / ProdOps when:**
- **CA**: PL override not raised for an added well (#1594775), CA Rules missing → RC010 eff-date / CA005 trigger (25-01036725), market groups not closed (23-00921207), DOI Change Warning flags checked (24-00949469).
- **VLA**: missing VL031 gross input / flow-grid + MP config (26-01064031), missing production meters on the Connections tab (26-01079482).
- **Interface/master-data**: FI/IAN handshake — disable interface to create a time slice / open VA before re-interfacing (ADO #210751, 25-01003784); SP025↔DO005↔RC010 eff-date alignment + ML002 rebuild (23-00931823, 25-01007370); import-def column drift checked into the client repo (26-01084811).
- **Reporting**: ONRR JE Group Code = CD1 (25-01009451), flow-grid ONRR settings (25-01009459), security group for the volumetric file (24-00945921); RPT_JER036 / OGP are **report** fixes.

**Handle as Training / Expected behavior (no fix):** see §15 — RD flag in PD051, 2nd-completion eff-date alignment, VA005/VA015/JIB load errors, "market group information" (MGs not closed), IntAlloc re-stage, MMS roll-the-month / TR015 no-data, and "volumes won't come into VA035" that clear once the VA is opened and re-interfaced.

**Data fixes (always verify-SELECT in a transaction):** clear `PSTG_ALLOC_VOL` for the period (22-00560531); script GB015 imbalance rows for owners not in the DOI (22-00523696, 23-00908242); bearer-group decimal correction (per #1770198); clear `PTRN_CA_VOL` parents before reverse/rebook reprocess (BP family).

---

*Skill created: 2026-06-14.*
*Based on closed QRA "My Quorum Revenue Accounting" volume-allocation cases (Production Allocation, Contractual Allocation, Volume Allocation, Volumetric Reporting, Production Master Data, Gas Balancing, Royalties, Wind Royalty). ~44 actionable mined for fix recipes (Software Defect 24 + Application Configuration 14 + allocation-relevant Royalty/Wind), plus ~40 Training/Customer-Error cases for the FAQ. ADO work items #1768726, #1770198, #1594775, #1612983, #630582, #1448519, #210751. Where a mined case had no clear resolution it is marked "resolution pattern unclear from mined cases."*
*Companion skills (mirror QPTM/TIPS pattern): Revenue Distribution, Check Write / ACH, Journal, PPA, DOI/Ownership — out of scope here; this skill stops where the allocated volume is correct.*
