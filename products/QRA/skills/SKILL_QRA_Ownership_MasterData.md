# SKILL: QRA Ownership & Master Data Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — upstream oil-&-gas revenue/owner accounting; myQuorum / On Demand suite)
**Scope:** The owner & master-data foundation that everything else in QRA reads — **Ownership** (DOI Setup, DOI/Interest Transfers via Maintenance Groups (MG), Workspace Groups, Market Groups (MEG), Bearer Groups (BG), the DOINTXFER/DVD pipeline, NRI/decimal-interest balancing) and **Master Data / Revenue Master Data** (Business Associates incl. tax-ID/1099/state-zip, Properties, Cost Centers, Well Completions, Masterlink/ML links, code tables, security/access, hotfix-patch packaging, integration to SAP/Enverus).
**Companion skills (sibling QRA back-end pipeline — fix the master-data/ownership *first* when those downstream numbers are wrong):** Revenue Distribution / Check Write → revenue & disbursement; Prior-Period Adjustment (PPA) reprocess; Journal / JE; Tax & Regulatory (severance, 1099 output). This skill *produces* the DOI / owner / market-group / BA / property records those processes *consume* — a wrong NRI, a pending Market Group, or a missing security group here surfaces downstream as a blocked Revenue Distribution, a CA020 failure, or a mispaid owner. Verify ownership/master-data integrity before treating a downstream number as a defect.

> **Evidence base:** 760 closed QRA cases in categories **Master Data (401) + Ownership (292) + Revenue Master Data (67)**. Root-cause split: (blank) 114, **Software Defect 94**, **Application Configuration 91**, Customer Error 81, Training 62, Customer Cancelled 61, No Action 34, Project Debt 30, Platform 29, Performance 22, others. This skill mines the **187 actionable** cases (Software Defect 94 + Application Configuration 91 + ChangeConfig 2) for fix recipes, plus ~35 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining; where a resolution was not recorded, it is marked *"resolution pattern unclear from mined cases."*

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts & Data Flow](#2-concepts--data-flow)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — DOI / Interest Transfer failures (Maintenance Group / DOINTXFER / DVD)](#4-cluster-a)
5. [Cluster B — NRI / decimal-interest & Bearer-Group balancing](#5-cluster-b)
6. [Cluster C — Market Group (MEG) status flip, won't-save, wiped data](#6-cluster-c)
7. [Cluster D — Workspace Group integrity (empty/trapped, duplicate inserts)](#7-cluster-d)
8. [Cluster E — Maintenance Group stuck / "completed with errors" / didn't move funds](#8-cluster-e)
9. [Cluster F — Business Associate master data (state/zip/tax-ID/1099/dup-name)](#9-cluster-f)
10. [Cluster G — Property / Well Completion / Cost Center master data](#10-cluster-g)
11. [Cluster H — Masterlink (ML) & integration (SAP / Enverus) errors](#11-cluster-h)
12. [Cluster I — Security / access (SC010) & service (QPEC) restarts](#12-cluster-i)
13. [Cluster J — Upgrade fallout & hotfix/patch packaging (V17/Permian, 2024.x)](#13-cluster-j)
14. [Cluster K — Tax / exemption / LOS / GROSS master data feeding revenue](#14-cluster-k)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Key Code, Screens & Repos](#18-key-code-screens--repos)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| DOI/Interest transfer **fails on approve** with `Violation of UNIQUE KEY 'AK_DONL_DO_OWNR_LSE'` (or `AK_DONL_DVD_DO_OWNR_LSE`) — "duplicate key" | Duplicate lease-xref / system firing duplicate inserts into `DONL[_DVD]_DO_OWNR_LSE` | §4 — get PQID + dup-key tuple; workaround: remove lease xref on DO136; MEG 2→1 duplicate-insert is the defect (24-00980704) |
| Transfer errors **"NRI decimal sum > 1.0" / "NRI_DEC sum is not equal to 1"** / "GWI Calculation Failed" | Preview/PPN-reversal date defect, or a genuinely out-of-balance market/bearer group | §5 — fix query `m_GetDOsForReversalDVDNew` (PPN reversal date) defect; or rebalance NRI per prod date |
| Transfer errors **"Bearer group bearer percent sum is not equal to 1"** (esp. recoupment / WI→OR conversion) | BG decimal changed during transfer | §5 — **Refresh the MG** then re-preview (BG burden decimal returns to 1); defect #1655401 |
| **Market Group flips Completed→Pending** during a transfer; then CA020/Revenue blocked ("status P, only closed grids processed in CA") | MG didn't update during transfer; needs recalc & re-close | §6 — manually correct owners/dates, **Calculate for each effective-date break**, re-close nontier MGs |
| **Market Group won't save (Save greyed out) / recalculation failed** — blocks Revenue cycle | MG out of sync after a transfer; CIA/contract MG with stale owners | §6 — correct owners/date ranges, recalc each eff-date break (25-01025633, 25-01016888) |
| **Market Groups / DOIs wiped out** after a maintenance-group refresh | "Copy To Live after Failed Group Refresh" deletes MG/DOI data | §6 / §7 — restore from UAT via script; long-term **ADO #1690965** |
| MG/Bearer Group **stuck "Processing"/"Previewing"** after QPEC error, no funds moved | Process interrupted mid-flight | §8 — use **"Revert Maintenance Group"** action → resubmit (25-01013609, 25-01011373, 25-01036705) |
| MG **"completed with errors" / "Plugged Transaction exceeds tolerance" / didn't move all funds** | User missing a **security group** | §8 — add the missing SC010 security group (e.g. 30021), re-run MG (24-00990886, 25-01004838) |
| **Empty/trapped wells in Workspace** that no longer exists / can't update | Workspace Creation never ran; header saved but no DOI detail; or orphaned WS group | §7 — script to reinsert/unstick; empty-WS-approval defect (23-00897809) |
| **BA State / Country dropdown blank or missing a state** (V17/upgrade) | State hidden in code table, OR null `ZIP_CODE_MASK_WEB` config breaking dropdown load | §9 — unhide state (set hidden=0); null-mask code fix in Patch 7 |
| **Duplicate BA Name validation** firing wrongly / re-enabled after a patch | Validation applied to wrong metadata layer; overwritten by patch | §9 — override on client (QCEN) layer; backport (25-01013566, 25-01033456) |
| **Tax ID / SSN masking** inconsistent / can't save BA in cloud | Masking config / type (SSN/FED) handling | §9 — add Tax-ID masking for SSN/FED (23-00917192) |
| **Property web save / copy fails** (FK constraint, unique-key on copy) | Web property-edit code gap; eff-date unique key | §10 — backported web edit (25-01008169); copy workaround = toggle eff-date & re-save |
| **Well Completion #2 won't create** — "cost center already used" | Cost-center validation too strict | §10 — disable `QRAValidationWellCompletion004_ValidateCostCenter` (25-01006980) |
| **Masterlink (ML002/ML005) build errors** / "duplicate path" | Overlapping/multiple open FG time slices (often from Prod Ops integration) | §11 — delete erroneous time slices by script (25-01042994); SOD masterlink fixed in 2022.04 |
| **Web Access Error / can't open Web / can't create FlowGrid** (V17) | SC010 security profile: Default group blank / ENGS module missing | §12 — set Default group, add ENGS module (25-01028254, 26-01080959) |
| Jobs "running for hours, no progress" / slow web | Needs service restart | §12 — **QPEC/QPECS restart** |
| **GROSS / LOS** value wrong or $0 in QCFS/QCA; exemption ignored during RD | Summarization / exempt-logic defect feeding revenue | §14 — GROSS-LOS summarization (22-00584889); exempt logic uses `adjCtgyCode` not `adjTypeCode` (22-00566269) |

---

## 2. Concepts & Data Flow

```
[Business Associates (BA)]  [Properties / Cost Centers / Well Completions]  [Code tables / Security (SC010)]
        │  (owners, tax-ID, 1099)        │  (the asset hierarchy)                  │
        └──────────────┬─────────────────┴───────────────┬─────────────────────────┘
                       ▼                                  ▼
            [DOI Setup]  ──►  Bearer Groups (BG)  ──►  Market Groups (MEG, a.k.a. Marketing/Market Group)
                       │           burdens                 valuation/contract owners per prod date
                       ▼
      OWNERSHIP CHANGES via WORKSPACE / MAINTENANCE GROUP (MG):
        create MG → add transfer transactions → PREVIEW (PPN/reversals) → APPROVE → DOINTXFER / DVD pipeline
        writes DONL_DO_OWNR_LSE / DONL_DVD_* ; generates PPNs; syncs to SAP
                       │
                       ▼
            [Masterlink (ML) builds links FG↔owners]  ──►  CA (Contractual Allocation, CA020)  ──►
            REVENUE DISTRIBUTION / CHECK WRITE / JOURNAL / 1099   (downstream — separate skills)
```

### Key terms (Quorum / QRA vocabulary)
- **DOI** = Division of Interest — the owner-share record per property/tier/product. **NRI** = Net Revenue Interest; the **NRI decimals across a market/bearer group for a production date must sum to exactly 1.0** (1.0000000001 fails — §5).
- **MG (Maintenance Group)** = the work unit for ownership changes/transfers; lifecycle **Work in Progress → Submitted for Approval → Previewing → Completed** (can "complete with errors"). The **"Revert Maintenance Group"** action resets a stuck MG back to Submitted-for-Approval.
- **MEG / Market Group** = market/marketing group; valuation owners per production date & contract. Has **tier** and **nontier** records; CA only processes **closed** market groups (a Pending MG blocks CA020). **CIA market group** = contract-/index-based MG.
- **BG (Bearer Group)** = burden grouping; **bearer percent must sum to 1**; "User Maintained Bearer Group" flag lets you edit detail manually.
- **Workspace Group** = the staging area (`DONL_DVD_GRP`, `DONL_DVD_DO_LIST`) for an ownership change; on approve, "check-in" logic deletes the live DOI detail and re-inserts from workspace. An **empty** workspace group (header saved, detail never loaded) wipes DOIs on approve (§7).
- **DOINTXFER / DVD** = the interest-transfer/divide pipeline (DO126 approve, `QDVDGroup`/`QDVDGroupSAP` batch). **PPN** = the reversal/adjustment posting notice created on backdated transfers.
- **PPN reversal** = preview generates reversal entries for prior periods; the date came from query `m_GetDOsForReversalDVDNew` (the source of several NRI/preview defects).
- **Masterlink (ML)** = ML002 "Build Links" / ML005 SOD links the flow grid (FG) to owners; **SOD** = Statement of Distribution masterlink.
- **DO136 / DO126 / SP025 / SC010 / CC010 / PD025/PD035 / BA005 / ML002 / CA020** = classic screen IDs (web has parallel screens). Document data for web master files now lives in `SARCH_CTRL_DOC_PROPERTIES` (was GUI `QXREF_DOI_XFER_DOC`).
- **QPEC / QPECS** = the QRA processing-engine services; "restart QPECs" clears hung/slow batch jobs.
- **ENGS / QCEN / QMEW / QMRO / QGC layers** = metadata override layers; **core = ENGS**, client layers sit on top. Putting a fix on the wrong layer is a recurring root cause (§9, §13).

---

## 3. Decision Tree

```
QRA Ownership / Master-Data case
│
├─ An ownership change/transfer FAILED or produced wrong result?
│   ├─ "duplicate key AK_DONL_DO_OWNR_LSE / AK_DONL_DVD_DO_OWNR_LSE"      → §4  (lease-xref dup; MEG 2→1 duplicate-insert defect)
│   ├─ "NRI decimal sum > 1.0" / "NRI_DEC not equal to 1" / GWI failed    → §5  (PPN-reversal date defect m_GetDOsForReversalDVDNew; or rebalance)
│   ├─ "Bearer group percent sum not equal to 1" (recoupment/WI→OR)       → §5  (REFRESH MG → re-preview; defect #1655401)
│   ├─ MG flipped Completed→Pending / MG won't save / recalc failed        → §6  (recalc each eff-date break; re-close nontier MGs)
│   ├─ Market Groups / DOIs WIPED OUT after refresh                        → §6/§7 (restore from UAT; ADO #1690965)
│   ├─ Empty / trapped Workspace group                                     → §7  (script reinsert/unstick; empty-WS defect)
│   ├─ MG stuck "Processing/Previewing" after QPEC error, no funds moved   → §8  (Revert Maintenance Group → resubmit)
│   └─ MG "completed with errors / exceeds tolerance / didn't move funds"  → §8  (missing SECURITY GROUP in SC010)
│
├─ Master data won't save / wrong dropdown / wrong format?
│   ├─ BA state/country dropdown / dup-name / tax-ID-SSN masking           → §9
│   ├─ Property / Well Completion / Cost Center save/copy/create error      → §10
│   └─ Masterlink ML002/ML005 build error / "duplicate path"               → §11
│
├─ Can't log in / open web / create FlowGrid / jobs hung?                   → §12 (SC010 security profile; QPEC restart)
│
├─ Right after an upgrade/hotfix (V17, Permian, 2024.x) something broke?    → §13 (config blown away / wrong layer / backport)
│
├─ Tax/exemption/LOS/GROSS/1099 master data wrong feeding revenue?          → §14
│
└─ "How do I…", audit, "can't change a property #", expected behavior?      → §17 Expected-Behavior FAQ
```

---

## 4. Cluster A — DOI / Interest Transfer failures (Maintenance Group / DOINTXFER / DVD)

**The single largest actionable ownership signature.** DOI/interest transfers approved through a Maintenance Group (DO126/DO136 → DOINTXFER → DVD pipeline) fail on **unique-key violations** when the transfer attempts a duplicate insert into the owner-lease tables.

**Symptom (verbatim, 25-01008778):**
```
[ADO Error] Violation of UNIQUE KEY constraint 'AK_DONL_DO_OWNR_LSE'.
Cannot insert duplicate key in object 'dbo.DONL_DO_OWNR_LSE'.
The duplicate key value is (70080, Jan 1 2005, REV, ALL, 2, CEN, 9087, 1, RI, 8, 171695).
[COM Error] File: QADORecordset.cpp ... NativeError: 2627
```
Approving Transfer Group 7574 on DO126 (PDID 9782113) failed; user could not locate the duplicate.

| Issue | Root cause | Fix / workaround | Case / ADO |
|---|---|---|---|
| Transfer approve fails on `AK_DONL_DO_OWNR_LSE` dup key | A duplicate lease-xref row in the transfer set | **Workaround:** removed the lease-xref data from **DO136** to complete the transfer | 25-01008778 |
| Workspace Exemption / MEG **2→1 transfer** fails on `AK_DONL_DVD_DO_OWNR_LSE` dup `(-)` | System **fires multiple duplicate inserts** into `DONL_DVD_DO_OWNR_LSE` though only one unique `(ARRG_KEY, GRP_NO, DOI)` exists | Code defect (byproduct of 23-00904958) | 24-00980704 |
| DOI transfer **hangs at report-launch step**, no report generated | `QRPTLAUNCH` step performance | Resolved by **QRPTLAUNCH performance enhancements in upgraded releases**; interim = script to set process User-Cancelled | 25-01000188 |
| Recoupment transfer "errors" but queue shows only warnings | BG percent rebalanced during WI→OR conversion | See §5 (Refresh MG workaround) | 24-00951452 |
| Generic "DO Transfer Error" on completing a workspace transfer | resolution pattern unclear from mined cases (screenshot-only) | capture PQID + exact error | 25-01003788, 24-00957162 |
| DVD interest transfer **"stuck in status 3"** / "In Interest Transfer status preventing updates" | Transfer left in an in-progress status blocking new transactions | Script to clear the transfer status (recurring) | 22-00571543, 24-00940459, 22-00571438 |

**Fix recipe:**
1. Get **PQID/PDID + the exact unique-key constraint name + the duplicate key tuple** (DO126 "Approve" error, or Batch Messages — double-click the error row).
2. `AK_DONL_DO_OWNR_LSE` → find the duplicate lease-xref row for that DOI/owner/date; the proven unblock is to **remove the offending lease xref on DO136** and re-approve. Verify-SELECT the tuple first.
3. `AK_DONL_DVD_DO_OWNR_LSE` on a **MEG 2→1** transfer → this is the duplicate-insert defect (24-00980704); escalate to Engineering with the property/owner combo and PQID.
4. "In Interest Transfer"/"status 3" blocking updates → scoped script to clear the transfer status (verify which transfer + property first).
5. Always scope re-runs to the specific **property + tier + production/eff date**; wrap any cleanup in a transaction with a verify-SELECT.

---

## 5. Cluster B — NRI / decimal-interest & Bearer-Group balancing

A tightly related family: transfers fail because **NRI decimals don't sum to 1.0** for a production date, or **bearer-group percents don't sum to 1**.

**Symptoms (verbatim):**
- 25-00997124: `"12/31/9999 has an NRI decimal sum of 1.0000000001."` + `"GWI Calculation Failed for production date 09/01/2024"` + `"DO NRI_DEC sum is not equal to 1 ... MKT_GRP_SEQ_NO = 15851"`.
- 24-00951452: `"DO Bearer group bearer percent sum is not equal to 1 for the specified production date"` (all BGs were 100% one owner → only out of balance if the transfer wrongly changed the BG).

| Issue | Root cause | Fix / workaround | Case / ADO |
|---|---|---|---|
| WI→WI transfer "NRI decimals totaled more than 1.0" + "Reversal Creation Failed" even when no PPN requested | **Preview PPN-reversal used the wrong date** | Fixed: *"The date used for Preview PPN reversals now is correct from the query `m_GetDOsForReversalDVDNew`."* | 25-01004078, 25-01004082, 25-01004079 |
| DOINTXFER fails "NRI decimal sum 1.0000000001" across multiple tiers | NRI genuinely out of balance for the prod date (rounding/8th-decimal carve) | Rebalance NRI per production date so each market group sums to exactly 1; verify the 8th-decimal carve | 25-00997124 |
| Recoupment / WI→OR conversion: "bearer percent sum ≠ 1"; BG 1 shows burden > 1 | System changes the bearer group during a transfer that should not touch it | **Workaround:** "**Refresh**" the Maintenance Group to restore Work-in-Progress; re-create the transaction, re-preview (BG burden decimal returns to 1), approve. Underlying = DOI-transfer-changes-BG-decimal defect | 24-00951452 / **#1655401** |
| 8th-decimal NRI not shown on MG/DOI Preview when < full NRI carved | Display precision on the preview/modify grid | Add NRI decimal to the DOI Maintenance Modify grid | 22-00828790 / **#1666087** |
| DOINTXFER NRI-decimal >1.0000000001 (Sandridge) | Same balancing family | (config/data) — verify per-prod-date sums | 25-00997124 |

**Fix recipe:** When a transfer throws an NRI/BG-sum error, first decide **defect vs genuine imbalance**:
- If the user **did not request PPNs / backdated reversals** yet sees "Reversal Creation Failed" + NRI>1 → it's the **PPN-reversal date defect** (`m_GetDOsForReversalDVDNew`); confirm the fix build (25-01004078 family).
- If it's a **bearer-percent ≠ 1** on a recoupment/WI→OR where BGs were already 100% one owner → use the **Refresh-MG** workaround and flag defect #1655401.
- Otherwise the NRI genuinely doesn't sum to 1 for that prod date — rebalance the carve (watch the 8th decimal) per market group / production date, then re-preview.

---

## 6. Cluster C — Market Group (MEG) status flip, won't-save, wiped data

The highest-impact master-data cluster because a bad Market Group **blocks the whole revenue cycle** (CA020 / Revenue Distribution).

**Symptom (verbatim, 25-01016888):** ML002 build on FG 46-OIL succeeds, then CA020 throws `"A market group was found to have a status of P on this property. Only grids with closed market groups will be processed in CA."` — the process flips those MEGs back to **Pending** and CA fails. In 25-01025633 the **Save button is greyed out** so the manual correction can't be saved and **recalculation fails**, blocking Revenue Distribution.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| MEG flips **Completed→Pending** during a transfer; CA020/Revenue then blocked | MG didn't update during the transfer (certain WI-xfer scenarios) | Manually correct owners; set MEG back to Completed; investigate the xfer scenario | 24-00957731, 25-01016888 |
| MEG **won't save (Save greyed out) / recalc failed** after a transfer; blocks Revenue | Nontier vs tier MGs out of sync; or stale **CIA/contract MG** with wrong owners | **Manually correct owners & date ranges, then Calculate for EACH effective-date break**; re-close the **nontier** MGs (Surge fixed nontier MGs to current ownership, recalced, closed) | 25-01016888, 25-01025633, 25-01025023 |
| Market Groups / DOIs **wiped out**, then QRA Export fails (`unique key constraint` PQIDs) | **"Market Groups Deleted by Copy To Live after Failed Group Refresh"** in a maintenance group | Short-term: **copy the data from UAT and script it back to PRD**; long-term **ADO #1690965** | 24-00985156, 24-00982421 |
| Backdated **MEG/SOD change didn't create PPN** | PPN-creation gap for backdated MEG/SOD changes | **Hotfix addresses PPN creation for backdated MEG/SOD changes** | 25-01000261 |
| Child records **missing from Market Groups tab** | Web grid child-record load | Code fix | — / **#1748670** |
| CIA market group "no longer used" but **can't be end-dated** | No end-date on the MG record itself | Workaround: correct owners/date ranges and **calculate for each eff-date break** (end-date the individual owners) | 25-01025023 |

**Fix recipe:**
1. Identify whether the symptom is **status (Pending) / save (greyed out) / wiped data** — these have different fixes.
2. **Pending / won't-save:** open the Market Group; for the affected property/tier (and especially the **nontier** record), correct owners & date ranges to current ownership and **run Calculate for each distinct effective-date break**, then re-close. This is the repeatable manual fix (25-01016888, 25-01025633). For a stale **CIA/contract** MG, fix or end-date the individual owners.
3. **Wiped MEGs/DOIs:** this is the Copy-To-Live-after-failed-refresh defect — restore the MEG/DOI/BG data from UAT via script and confirm **#1690965** is in the target build (24-00985156).
4. **Backdated MEG/SOD didn't make a PPN:** confirm the hotfix (25-01000261) is applied.
5. A "long-term solution" follow-up case (25-01026869) tracks the won't-save/recalc problem — link new occurrences to it.

---

## 7. Cluster D — Workspace Group integrity (empty / trapped, duplicate inserts)

Workspace Groups stage ownership changes in `DONL_DVD_GRP` / `DONL_DVD_DO_LIST`; on approve, check-in logic **deletes the live DOI detail and re-inserts from the workspace**. When the workspace is empty or orphaned, data is lost or the well is trapped.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Empty Workspace Groups can be approved & wipe out DOIs** (then QRA Export fails — wells have no DOIs) | Workspace **Creation process never ran**: header + DOI list saved (`DONL_DVD_GRP`, `DONL_DVD_DO_LIST`) but DOI detail never loaded; approve then **deletes live DOI detail with nothing to re-insert** | Short-term: **script to re-insert the DOI, Bearer Group, and Market Group info**. Long-term: **code change to prevent empty workspace groups from being approved** | 23-00897809 |
| Wells **"trapped" in Workspace** that no longer exists; can't be updated again | Workspace approved but well still flagged in a now-deleted workspace | Script to clear the workspace flag / unstick the well | 22-00622155 |
| Workspace group **blocking property/JIB-DOI updates** | Orphaned/locked workspace group | Short-term script to release; long-term WI logged separately | 22-00566303, 22-00566223 |
| MEG 2→1 transfer **duplicate inserts** into `DONL_DVD_DO_OWNR_LSE` | See §4 (same defect family) | Code | 24-00980704 |

**Fix recipe:** For "DOIs wiped / wells trapped / can't update in workspace," confirm whether a workspace group was **approved while empty** or **left orphaned**. Recovery is a **scoped data script** that re-inserts DOI + Bearer Group + Market Group detail (restore from UAT or from history) and/or clears the trapped-well flag. Always verify-SELECT the affected decks first. The structural fix (block empty-workspace approval) is the long-term ask in 23-00897809.

---

## 8. Cluster E — Maintenance Group stuck / "completed with errors" / didn't move funds

Distinct from §4–§7 (where the transfer logic itself is wrong) — here the MG is interrupted or the user lacks rights.

| Signature | Root cause | Fix | Case |
|---|---|---|---|
| MG **stuck "Processing"/"Previewing"** after a QPEC error; no funds moved | Process interrupted mid-flight (QPEC error / server restart) | **"Revert Maintenance Group"** action → status back to Submitted-for-Approval → resubmit | 25-01013609, 25-01011373, 25-01036705 |
| MG **"completed with errors" / "Plugged Transaction amount exceeds tolerance" / did NOT move all funds** (e.g. $395.19 stranded) | User was **missing a security group** required for the transfer | **Add the missing SC010 security group** (e.g. **30021**); have the user set up & approve a new MG | 24-00990886, 24-00990637, 25-01004838 |
| MG **approved then re-approved, now in Error** | MG left in a bad status | **Script to set the MG to Completed** | 25-01007817 |
| MG shows **Pending after "Sync to SAP Status"**; SAP shows the move but Quorum doesn't | Sync-status drift | Exact root cause never found; **script to resync the DOI** (did not recur) | 22-00830862 |
| "Unable to delete Maintenance Group" | Missing security group | Add the security group (e.g. 30021), logout/login, retest | 25-01004838, 24-00990638 |

**Fix recipe:**
1. **Stuck Processing/Previewing** → first try **Revert Maintenance Group** (built-in action) and resubmit — no script needed in most cases.
2. **Completed-with-errors / tolerance / funds-not-moved / can't-delete-MG** → check the **user's SC010 security groups**; the recurring miss is security group **30021** (Permian). Add it, have the user redo a fresh MG. Only escalate as a defect if security is confirmed complete.
3. **Stuck/bad status that won't revert** → scoped script to set the MG status (Completed/Submitted) after verifying SAP vs Quorum state.

---

## 9. Cluster F — Business Associate (BA) master data

BA dropdowns, name validation, and tax-ID/1099 masking — a large config + defect cluster, heavily surfaced during V17/upgrade.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **BA State dropdown not populating** on BA create (V17) | Code failed to load the state-code dropdown when global configs **`BA ENTITY \| ZIP_CODE_MASK_WEB`** and **`ZIP_CODE_MASK_WEB_CAN`** were **NULL** | Code updated to handle a null masking value (**Patch 7**); **move these config overrides to the core ENGS layer** (NULL mask = 9-char zips show without a hyphen) | 25-01024760 |
| **State missing from dropdown** (e.g. Iowa) | The state was **flagged hidden** in the code table (V16 & V17) | Set the hidden flag to **0** for that state | 25-01026573 |
| **Duplicate BA Name validation** firing wrongly / re-enabled after a patch | `QESUITEValidationBAEntity0024_DuplicateBAName` applied to the **wrong metadata layer** (overwritten by the patch) | Put the override on the **client QCEN layer**; reproducible in 2023.04, fixed in newer releases → **backport to 2023.04 HF** | 25-01013566, 25-01033456 |
| **Tax ID / SSN masking inconsistent** (last-4 vs first-4); can't save BA in cloud | Masking config / Tax-ID-type handling differs Citrix vs QCloud | **Added masking for Tax ID when Tax ID type is SSN or FED**; format-consistency item moved to backlog (low priority) | 23-00917192, 25-01007287 |
| **1099 indicator / 1099 Address Override** not behaving on BA / output | 1099 flag/override handling | resolution pattern unclear from mined cases (1099 indicator 26-01070765 had no recorded resolution; Address Override 22-00584935 open question) | 26-01070765, 22-00584935 |
| BA **Document Types / ZIP code / Contact screen / Primary Usage Code** errors (V17) | Code-table configs / multiple primary-usage codes / web screen | Config corrections; Primary-Usage multiple-code save error (Defect #41) | 25-01024369, 25-01012267, 25-01013179, 25-01010365 |
| **BA Suffix 0 / "BA Number giving yellow error" / Country UK zip** | Code-table & validation gaps | Defect fixes | 23-00934115, 23-00894720, 24-00940270 |

**Fix recipe:** For a BA **dropdown** problem after an upgrade, check **(a)** is the value **hidden** in the code table (unhide → set 0, 25-01026573), and **(b)** are the **`ZIP_CODE_MASK_WEB`/`_CAN`** global configs NULL (the state-dropdown-load defect, 25-01024760 — Patch 7, and move the override to ENGS). For **Duplicate BA Name** false-positives, the fix is **metadata-layer placement** (client QCEN), not disabling the rule (25-01033456). For Tax-ID/SSN issues, verify the **masking config per Tax-ID type** (23-00917192).

---

## 10. Cluster G — Property / Well Completion / Cost Center master data

Saving, copying, and creating the asset hierarchy — web-vs-classic edit gaps and over-strict validations dominate.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Property web save fails** adding legal descriptions — `FK_RONL_ST_TAX_RATE_OVRD__PONL_WELL_COMPL` reference constraint | Web property-edit path couldn't delete/update the child correctly | **Backported the 2024.04 functionality** that allows code changes / property edits in **web** | 25-01008169 |
| **Copy Property fails** — unique-key on `PonlWellComplOperEffDt` (`WellNo, OperBusSegCode, ComplNo, EffDateFrom`) | Side-effect of the January hotfix on copy | **Workaround:** change the effective date, save, change it back, save again | 25-01004764 |
| **Well Completion #2 won't create** — "this cost center is already being used by another well completion" | `QRAValidationWellCompletion004_ValidateCostCenter` too strict | **Disable the validation** `QRAValidationWellCompletion004_ValidateCostCenter` | 25-01006980 |
| **Cost Center type wrong** (Property vs Well Completion) | Data value in CC010 | **Data update script** to set cost-center type to Well Completion | 23-00927327 |
| **Auto-creation creates Operated wells for Non-Op properties** | Auto-create (from CC010) ownership-type bug | Code (Engineering) | 22-00650871 / **#199979** |
| **DO Copy sets Revenue Active = Yes on JIB DOIs** | Copy process checks revenue-active flag on JIB DOIs | Code (Engineering) | 22-00650873 / **#203714** |
| **API Well-number format validation** behavior differs web vs desktop / config disabling it blown away by hotfix | Validation config (QMEW layer) not persisted | **Check the metadata into the repo** so the disable persists across patches | 25-01018894, 24-00983716 |
| **BTU factor blank vs 0.00** on oil records (Enverus export) | Incorrect logic in the **Enverus export** | Short-term update script; **code fix to the Enverus export logic** | 24-00954034 |
| Property **legal description / number filtering / Prospect pick-list** issues | Web grid / pick-list bugs | Defect fixes | 23-00936009, 22-00821096, 23-00910235 |

**Fix recipe:** Property/Well-Completion **save/copy errors after a hotfix** are usually a **web-edit code gap or a unique-key on eff-date** — the proven unblock for copy is the **toggle-eff-date-and-resave** workaround (25-01004764), and the structural fix is the **backported web-property-edit** (25-01008169). For "well completion can't use this cost center," **disable `QRAValidationWellCompletion004_ValidateCostCenter`** (25-01006980). For any **config disabling a validation that disappears after a patch** (API well format, prospect validation), the durable fix is to **check the metadata into the repo / put it on the right layer** (25-01018894).

---

## 11. Cluster H — Masterlink (ML) & integration (SAP / Enverus) errors

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **ML002 "Build Links" errors** for a flow grid; **"duplicate path"** | **Multiple open time slices** for the FG (often from a **Prod Ops integration**) | **Delete the erroneous time slices by script**; Prod Ops to fix the source | 25-01042994, 22-00869445 |
| **SOD masterlink (ML005)** "system error" when eff-from date differs within masterlink dates | Masterlink eff-date handling bug | **Resolved via the 2022.04 upgrade** (walkthrough doc provided to confirm) | 22-00832337 |
| **BG change integrates to SAP but doesn't complete in Quorum** | Sync/integration completion gap | Defect | 23-00932061 |
| **Email/Phone (and Combine flag) not integrating to SAP** | Integration field-mapping defect / config | Defect / config | 23-00930040, 23-00930326 |
| **QRA → QCFS/QCA / Subledger / QLS→QRA Lease interface** export errors | Interface/summarization defects | Defect fixes | 23-00930775, 22-00680610, 22-00674437 |
| **Enverus EnergyLink** revenue XML / wrong process ID or file path | Integration config | Provide correct **process ID** + valid file path in **QP043** | 25-01024575 |

**Fix recipe:** **ML002/ML005 build errors** are almost always **time-slice/eff-date overlaps** on the flow grid or masterlink — find the **multiple open time slices** (frequently created by a Prod Ops integration) and **script-delete the erroneous ones** (25-01042994), then have Prod Ops fix the source. SOD-masterlink eff-date crashes were fixed in **2022.04** (22-00832337). For SAP/Enverus integration gaps, verify field mapping/config (process ID + file path in QP043) before assuming a code defect.

---

## 12. Cluster I — Security / access (SC010) & service (QPEC) restarts

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Web Access Error** / works only after a property search; shows "Division Order Analyst" not "Default" | **SC010 security profile**: Default Group Settings blank; **ENGS** module not added | In **SC010**: set Default Group Settings to "Default" and **add the ENGS module** to the user | 25-01028254 |
| **Can't create first FlowGrid in PRD** | SC010 profile missing **Default Settings** | Select Default Settings in SC010 | 26-01080959 |
| **Users can't open Upstream Web / can't view/search Property** (V17) | Security/profile gaps (inconsistent across users) | Security profile fixes in SC010 (per-user) | 24-00970056, 24-00969850, 23-00913729 |
| MG "completed with errors / can't delete MG / funds not moved" | Missing security group (e.g. **30021**) | Add the security group (cross-ref §8) | 24-00990886, 25-01004838 |
| **Jobs running for hours / slow web / hung MGs** | Services need recycling | **Restart QPEC/QPECS** (Tribune MLN_PROD, UAT, etc.) — very common, no code change | 25-01012681, 24-00972504, 25-01021513, 25-01006602 |
| **Desk ID / Code-Decode / screen access** missing | Security object / desk-ID maintenance config | Grant the security object / desk-ID access | 23-00918835, 22-00828184, 23-00913438 |

**Fix recipe:** For **"can't open web / web access error / can't create FlowGrid,"** the answer is nearly always the **SC010 security profile** — set **Default Group Settings = "Default"** and ensure the **ENGS module** is on the user (25-01028254, 26-01080959). For **MG approval errors / can't delete MG**, add the missing **security group (30021)** (§8). For **hung/slow jobs**, request a **QPEC/QPECS restart** first — it clears most "stuck" complaints without any data fix.

---

## 13. Cluster J — Upgrade fallout & hotfix/patch packaging (V17/Permian, 2024.x)

A large share of recent actionable cases are **upgrade fallout** — config or validations behaving differently after V17/Permian or a 2024.x hotfix, usually because a fix landed on the **wrong metadata layer** or a client override got **blown away** by the patch.

| Pattern | Root cause | Fix | Case |
|---|---|---|---|
| A client config/validation override **disappears after a hotfix** (API well format, prospect validation, dup-BA-name) | Override was on a layer the patch overwrites, or never checked into the repo | **Put the override on the durable layer (ENGS/QCEN) and check the metadata into the repo** | 25-01018894, 25-01018863, 25-01033456 |
| **Web vs desktop behavior differs** (property edit, API well number, attachments/comments storage, masked Tax-ID) | Web parity gaps vs classic | Backport the web functionality, or advise using the classic screen (e.g. SP025) where parity isn't there yet | 25-01008169, 24-00983716, 25-01014214, 25-01014212 |
| **Dropdowns missing / blank after upgrade** (state, document types) | Hidden code-table values / null mask config | Unhide values; null-mask code fix (§9) | 25-01026573, 25-01024760, 25-01024369 |
| **"Patch N / Hotfix request" tracking cases** | Packaging/coordination | Deliver the patch; confirm contents in release notes | 26-01070888, 25-01059633, 25-01053206, 25-01050185, 25-01041010 |
| **Smoke/UAT-testing defects (2023 cycle)** — NMA add/modify, PK error combining interest, code/decode access, nullable-object error | Pre-release defects caught in smoke testing | Fixed in the release/hotfix | 23-00926987, 23-00926744, 22-00828184, 23-00930513 |

**Fix recipe:** When something "worked before the upgrade," first determine whether a **client override was overwritten** or a fix **landed on the wrong layer**. The durable resolution is to place the config/validation override on the correct layer (**ENGS** core for shared, **QCEN/QMEW/QMRO** for client) **and check the metadata into the repo** so the next patch doesn't blow it away (25-01018894, 25-01033456). For web-vs-classic parity gaps, either confirm the backport build or advise the classic screen as an interim.

---

## 14. Cluster K — Tax / exemption / LOS / GROSS master data feeding revenue

Master-data settings here surface downstream as wrong revenue/tax — verify the master data before treating it as a Revenue Distribution defect.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **GROSS LOS** values **overstated or $0** when data migrates QRA→QCFS/QCA (vs JE111) | Summarization defect for GROSS LOS | Defect (reviewed with old 20-00087921) | 22-00584889, 22-00572128 |
| **Exemption 11 ignored during Revenue Distribution (RD)** | Exempt logic checked the wrong field | **Software fix: exempt logic now looks at `adjCtgyCode` instead of `adjTypeCode`**; MJEs used for cleanup | 22-00566269 |
| **Tax Exemption configuration / Tax Exemption Group (TEG)** setup | Config / test-script clarity | Config script (26-01084895); TEG steps clarified (25-01021041) | 26-01084895, 25-01021041 |
| **Backup Withholding required vs not** / **VL006 DOI Accounting Rule autofill** | BA/DOI tax-flag config | Configuration guidance | 23-00922154, 23-00906569 |
| **CW200 / PPA Perm Flag** — growing number of owners paid incorrectly | Perm-flag handling defect | Software Defect (engineering) | 23-00900300 |
| **1099 patch / December patch including 1099** | Packaging | Patch delivered | 22-00527060, 22-00584935 |

**Fix recipe:** For **GROSS/LOS** discrepancies, compare the QCFS/QCA summarized value against **JE111** for the same accounting month + major product (22-00584889) — a mismatch points at the summarization defect, not the source data. For **exemptions ignored during RD**, confirm the build has the **`adjCtgyCode`** exempt-logic fix (22-00566269). Tax-exemption/backup-withholding "issues" are usually **BA/DOI tax-flag config** — verify the flag before escalating.

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1655401** | Bug / **Closed** | GEC — DOI transfer causes change to bearer group decimal (defect 266) | §5 | 24-00951452 |
| **#1666087** | Requirement / **Closed** | GEC — Add NRI Decimal in DOI Maintenance Modify grid (defect 329) | §5 | 22-00828790 |
| **#1690965** | Bug / **Closed** | GEC — Market Groups Deleted by Copy To Live after Failed group refresh | §6 | 24-00982421, 24-00985156 |
| **#1748670** | Bug / **Closed** | Child records missing from Market Groups tab | §6 | — |
| **#199979** | Bug / **Closed** | KKR — Auto-created wells don't have same Ownership Type as Property | §10 | 22-00650871 |
| **#203714** | Bug / **Closed** | KKR — JIB DOI copies with Revenue Active Flag | §10 | 22-00650873 |
| **#1394235** | (BA-name validation) | Duplicate BA Name | §9 | 25-01013566, 25-01033456 |
| **#1637960** | (PPN reversal) | PPN reversal | §5 | 25-01004078 family |

> **Operationally dispositioned (no single product WI):** the **PPN-reversal date** fix (`m_GetDOsForReversalDVDNew`, 25-01004078/079/082 — see `Quorum.Upstream.Tools/work_item_analysis/1729989_Move_Preview_PPN_To_DVD_Verify.md`); **null ZIP-mask state-dropdown** fix → **Patch 7** (25-01024760); **Duplicate-BA-Name** backport to 2023.04 HF (25-01033456); **PPN-creation for backdated MEG/SOD** hotfix (25-01000261); **Enverus BTU-export** logic fix (24-00954034); **exemption `adjCtgyCode`** fix (22-00566269); SOD-masterlink fix in **2022.04** (22-00832337); web-property-edit backport from 2024.04 (25-01008169). Confirm exact build/patch in the Upstream/QRA release notes when stating fix availability. *(Many cases referenced `Engineering #`/`SIR`/`Defect #` tracker numbers — e.g. 266, 329, 41, 199979, 203714, 161952 — rather than modern ADO IDs; treat those as legacy tracker references.)*

---

## 16. Diagnostic SQL

> **Caveat:** QRA runs on **SQL Server**, per-client DBs named like `CEN_PRDA1UPS_QRA` / `MAC_PRDA1UPS_QRA` (client prefix + env + `UPS_QRA`). Table names below are from case repro text and code search; **verify against the client DB before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Duplicate owner-lease rows behind AK_DONL_DO_OWNR_LSE / AK_DONL_DVD_DO_OWNR_LSE (§4)
SELECT PROP_NO, EFF_DT, DO_TYPE_CD, MAJ_PROD_CD, TIER, OPER_BUS_SEG_CD,
       BA_NO, COMPL_NO, INT_TYPE_CD, COUNT(*) dup_ct
FROM   dbo.DONL_DO_OWNR_LSE          -- or DONL_DVD_DO_OWNR_LSE for the DVD/preview pipeline
WHERE  PROP_NO = '<PROP_NO>'
GROUP BY PROP_NO, EFF_DT, DO_TYPE_CD, MAJ_PROD_CD, TIER, OPER_BUS_SEG_CD,
         BA_NO, COMPL_NO, INT_TYPE_CD
HAVING COUNT(*) > 1;

-- B. NRI decimal sum per market group / production date — must equal exactly 1.0 (§5)
SELECT OPER_BUS_SEG_CD, PROP_NO, DO_TYPE_CD, TIER, MAJ_PROD_CD,
       MKT_GRP_TYPE_CD, MKT_GRP_SEQ_NO, PROD_DT, SUM(NRI_DEC) nri_sum
FROM   <DOI owner detail / market-group owner table>
WHERE  PROP_NO = '<PROP_NO>' AND PROD_DT = '<PROD_DT>'
GROUP BY OPER_BUS_SEG_CD, PROP_NO, DO_TYPE_CD, TIER, MAJ_PROD_CD,
         MKT_GRP_TYPE_CD, MKT_GRP_SEQ_NO, PROD_DT
HAVING ABS(SUM(NRI_DEC) - 1.0) > 0.0000000005;   -- catches 1.0000000001

-- C. Bearer-group percent sum — must equal 1 (§5)
SELECT PROP_NO, TIER, BEARER_GRP_NO, PROD_DT, SUM(BEARER_PCT) bg_sum
FROM   <bearer group detail table>
WHERE  PROP_NO = '<PROP_NO>'
GROUP BY PROP_NO, TIER, BEARER_GRP_NO, PROD_DT
HAVING ABS(SUM(BEARER_PCT) - 1.0) > 0.0000000005;

-- D. Market Groups stuck in Pending (status 'P') blocking CA020 (§6)
SELECT OPER_BUS_SEG_CD, PROP_NO, TIER, MKT_GRP_SEQ_NO, MKT_GRP_STATUS_CD, LAST_CALC_DT
FROM   <market group header table>
WHERE  PROP_NO = '<PROP_NO>' AND MKT_GRP_STATUS_CD = 'P';   -- expect 'C' (closed) for CA to process

-- E. Empty / orphaned workspace group: header + list saved but no DOI detail (§7)
SELECT g.DVD_GRP_NO, g.GRP_STATUS_CD,
       (SELECT COUNT(*) FROM dbo.DONL_DVD_DO_LIST l WHERE l.DVD_GRP_NO = g.DVD_GRP_NO) list_ct,
       (SELECT COUNT(*) FROM dbo.DONL_DVD_DO_OWNR_LSE o WHERE o.DVD_GRP_NO = g.DVD_GRP_NO) detail_ct
FROM   dbo.DONL_DVD_GRP g
WHERE  g.DVD_GRP_NO = '<GRP_NO>';   -- list_ct > 0 but detail_ct = 0  ==>  the empty-WS wipe risk (23-00897809)

-- F. Maintenance Group status (stuck Processing / completed-with-errors) (§8)
SELECT MAINT_GRP_NO, MAINT_GRP_STATUS_CD, DOI_SYNC_STATUS_CD, LAST_PQID, UPDT_DTTM
FROM   <maintenance group header table>
WHERE  MAINT_GRP_NO = '<MG_NO>';   -- Revert action resets to 'Submitted for Approval'

-- G. Multiple open time slices on a flow grid → ML002 "duplicate path" (§11)
SELECT FLOW_GRID_NO, EFF_DT_FROM, EFF_DT_TO, COUNT(*) ct
FROM   <flow grid / masterlink time-slice table>
WHERE  FLOW_GRID_NO = '<FG>' AND EFF_DT_TO IS NULL   -- multiple open (null end) slices = the dup-path risk
GROUP BY FLOW_GRID_NO, EFF_DT_FROM, EFF_DT_TO
HAVING COUNT(*) > 1;

-- H. State code-table value hidden, blocking the BA dropdown (§9)
SELECT STATE_CD, STATE_NM, HIDDEN_FLAG FROM <state code table> WHERE HIDDEN_FLAG <> 0;  -- set to 0 to expose

-- I. Are the ZIP-mask configs NULL (the V17 state-dropdown-load defect, §9)?
SELECT CONFIG_NM, CONFIG_VALUE, LAYER FROM <global config table>
WHERE  CONFIG_NM IN ('ZIP_CODE_MASK_WEB','ZIP_CODE_MASK_WEB_CAN');  -- NULL = pre-Patch-7 break
```

---

## 17. Expected-Behavior / User-Education FAQ

~62 Training + ~81 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Maintenance Group / Bearer Group **stuck Processing/Previewing** after a QPEC error" | Use the **"Revert Maintenance Group"** action to reset to Submitted-for-Approval, then resubmit — not a defect | 25-01013609, 25-01011373, 25-01036705 |
| "MG **won't approve / can't delete MG / didn't move funds**" | Almost always a **missing SC010 security group** (e.g. 30021) — add it, logout/login, retry | 25-01004838, 24-00990886 |
| "**Web Access Error** / can't open Web / can't create FlowGrid" | **SC010 security profile**: set Default Group Settings = "Default", add the **ENGS** module | 25-01028254, 26-01080959 |
| "**My DOIs don't show in the MG Creation screen**" | By design — a DOI is eligible only if **Approved + Property Active + type JIB or REV** (RRV/RRC/INF are excluded) | 25-01035983 |
| "**Can't change a Property number / BA number**" | Not supported. Mark the property+cost-center (or BA) **Inactive** if unused and **create a new one** with the desired number | 26-01092830, 26-01080625 |
| "Bearer Group **'doesn't exist'** / pay-code issue" | Usually a **trailing space in the property number** or an approved BG — unapprove BG, remove the space, re-save | 25-01025942, 25-01040473 |
| "**Can't roll the QRA accounting period**" | Stuck OFR processes block the roll — script them to **Prevent Posting = Y** after confirming the client's workaround is correct | 25-01053279 |
| "New **desk ID / metadata** not showing in a pick list" | **Clear system & browser cache** after adding desk IDs/metadata | 25-01034290 |
| "Where is the **web document table** (vs GUI `QXREF_DOI_XFER_DOC`)?" | All master-file doc data (BA, DOI Setup, DO Xfer…) now lives in **`SARCH_CTRL_DOC_PROPERTIES`** | 25-01036150 |
| "Jobs slow / running for hours" | Request a **QPEC/QPECS restart** | 25-01021513, 25-01006602, 25-01004722 |
| "Can I **schedule MG005 calculations** (GMICALCRUN)?" | Technically possible for upcoming runs, but **no customer does this** — advise against | 26-01100246 |
| "County codes / zero-padding / Product-Code account cross-ref" | Data-format housekeeping — **update script** (e.g. zero-pad county codes) | 26-01100561 |
| "Bearer Group **Approval** stuck after V17" | Documented multi-step workaround: export owners, check "User Maintained Bearer Group," delete detail, save, unapprove BG, delete the bad line, re-import owners | 25-01040473 |

**Tell-tale it's user/expected:** an MG that just needs **Revert + resubmit**; an "approval/can't-delete" error that's really a **missing SC010 security group**; a web-access failure fixed by the **Default group + ENGS module**; a DOI "missing" from MG Creation that simply isn't Approved/JIB-REV/Active; a request to change an immutable **property/BA number**; or a stale pick list cleared by **cache refresh**. Verify the **security profile, MG status, and master-data eligibility** before treating it as a defect.

---

## 18. Key Code, Screens & Repos

### Screens / processes (classic IDs; web has parallels)
| Screen / process | Purpose | Notes |
|---|---|---|
| **DOI Setup / DO126 / DO136** | Maintain DOIs; approve transfer groups; lease xref | DO136 lease-xref removal is the §4 unblock |
| **Maintenance Group (MG)** | Work unit for ownership transfers | **"Revert Maintenance Group"** action unsticks Processing/Previewing |
| **Market Group / MEG** | Valuation owners per prod date/contract | Must be **closed** for CA020; recalc per eff-date break (§6) |
| **Bearer Group (BG)** | Burden grouping | Percent must sum to 1; "User Maintained BG" flag |
| **Workspace Group** | Staging for ownership change | `DONL_DVD_GRP` / `DONL_DVD_DO_LIST`; empty-approval wipe risk (§7) |
| **DOINTXFER / DVD pipeline** | Interest transfer/divide; PPN generation; SAP sync | `QDVDGroup` / `QDVDGroupSAP` batch; `QRPTLAUNCH` report step |
| **BA005 / BA Entity (web)** | Business Associates | dup-name, tax-ID masking, 1099, state/zip dropdowns (§9) |
| **CC010 / PD025 / PD035 / SP025** | Cost Center / Property / Well-Completion / DOI-XREF | type values, copy/create validations (§10) |
| **ML002 / ML005 (SOD)** | Masterlink Build Links / SOD links | time-slice/eff-date overlaps → "duplicate path" (§11) |
| **SC010** | Security profile / groups / modules | Default group + ENGS module; security group 30021 (§8/§12) |
| **CA020** | Contractual Allocation | rejects properties with a Pending ('P') market group (§6) |
| **QP043 / Enverus EnergyLink** | Revenue XML export | process ID + valid file path (§11) |

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `QRAValidationWellCompletion004_ValidateCostCenter.cs` | `Quorum.Upstream.QRA.Web /Quorum.QRA.Validations/WellCompletion/Validation Rules/` | §10 (disable to allow Well Completion #2) |
| `QESUITEValidationBAEntity0024_DuplicateBAName.cs` | `Quorum.ESuite.Web /Quorum.ESuite.Validation/BAEntity/Validation Rules/` | §9 (dup-BA-name; layer placement matters) |
| `DonlDvdDoOwnrLseDO.cs` / `DonlDvdDoOwnrLseDAL.cs` | `Quorum.Upstream.Shared.Web /Quorum.QDO.DataObject(/DAL)/CodeGen/` | §4/§7 (DVD owner-lease) |
| `QDVDGroupSAP.cpp` / `QDVDGroup.cpp` | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgDO/` | §4/§8 (DVD/transfer batch, SAP sync) |
| `m_GetDOsForReversalDVDNew` (+ `PPN_Technical_Deep_Dive.md`, `1729989_Move_Preview_PPN_To_DVD_Verify.md`) | `Quorum.Upstream.Tools /documentation, /work_item_analysis/` | §5 (PPN reversal date defect) |
| State-code dropdown / `ZIP_CODE_MASK_WEB` handling | `Quorum.ESuite.Web` (BA Entity) + metadata layers | §9 (V17 dropdown-load fix, Patch 7) |

### Repos
- **`Quorum.Upstream.QRA.Web`** — QRA web screens & validations (Well Completion, Property, Cost Center).
- **`Quorum.ESuite.Web`** — shared eSuite web incl. **BA Entity** screens/validations (dup-name, tax-ID, dropdowns).
- **`Quorum.Upstream.Shared.Web`** — QDO data objects / DAL (DOI, DVD, owner-lease).
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ revenue-accounting batch incl. **`QPDllRevenueAcctgDO`** (DVD group, SAP sync, DOINTXFER).
- **`Quorum.Upstream.Tools`** — work-item analysis & technical deep-dives (PPN, pay-code, preview).
- **Metadata repos / layers** — `SUM.Upstream.Metadata` (STANDARD/core = **ENGS**), client layers **`CEN.Upstream.ESuite.Metadata`**, `QMEW`, `QMRO`, `QCEN`, `QGC.QLS.ESuite.Metadata`. **Always confirm the override layer** — wrong-layer placement and patch-overwrite are recurring root causes (§9, §13).

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A transfer **fires duplicate inserts** into `DONL_DVD_DO_OWNR_LSE` on a MEG 2→1 (24-00980704); **empty workspace groups can be approved & wipe DOIs** (23-00897809); **Copy-To-Live-after-failed-refresh deletes Market Groups** (#1690965).
- **PPN reversal uses the wrong date** producing spurious NRI>1 / "Reversal Creation Failed" with no PPN requested (25-01004078 family; `m_GetDOsForReversalDVDNew`); **DOI transfer changes the bearer-group decimal** (#1655401).
- A provable master-data defect on correct input: GROSS-LOS summarization (22-00584889), exemption logic using the wrong field (22-00566269), auto-create wells wrong ownership type (#199979), JIB-DOI copy sets Revenue Active (#203714), Enverus BTU export logic (24-00954034).
- Provide: **PQID/PDID + the exact constraint/error + the duplicate key tuple or NRI/BG sum**, client + property + tier + prod/eff date, the MG/MEG/workspace number, and a repro. Confirm fix availability in the Upstream/QRA release notes + the linked WI's target build.

**Handle as Configuration / Cloud Ops when:**
- **Security**: SC010 Default-group/ENGS-module for web access (25-01028254); missing **security group 30021** for MG approval/delete (24-00990886, 25-01004838); desk-ID/code-decode access.
- **Metadata layer / packaging**: a fix or validation override on the **wrong layer** or **blown away by a patch** — place it on **ENGS/QCEN** and **check the metadata into the repo** (25-01018894, 25-01033456); unhide code-table values (state, 25-01026573).
- **Time-slice / data fixes**: ML002 "duplicate path" → delete erroneous open FG time slices (25-01042994); cost-center type via update script (23-00927327); county-code zero-padding; clear stuck OFRs to roll the period (25-01053279). Always verify-SELECT in a transaction.
- **CCT-style master-data**: BA tax-ID masking per type (23-00917192); backup-withholding / DOI accounting-rule flags (23-00922154, 23-00906569).

**Handle as Training / Expected behavior (no fix):** see §17 — **Revert Maintenance Group** for stuck MGs, **missing security group** for approval errors, **Default group + ENGS module** for web access, DOI eligibility (Approved/JIB-REV/Active) for MG Creation, immutable property/BA numbers (Inactive + recreate), trailing-space/BG-approval workarounds, and cache refresh for new pick-list values.

**Service-restart first (no code):** "jobs running for hours / slow web / hung MG" → **QPEC/QPECS restart** clears most of these (25-01012681, 24-00972504, 25-01021513).

---

*Skill created: 2026-06-14.*
*Based on: 760 closed QRA Ownership + Master Data + Revenue Master Data SF cases — 187 actionable (Software Defect 94 + Application Configuration 91 + ChangeConfig 2) mined for fix recipes, plus ~35 Training/Customer-Error cases for the FAQ. ADO work items #1655401, #1666087, #1690965, #1748670, #199979, #203714, #1394235, #1637960. Code: QRAValidationWellCompletion004_ValidateCostCenter, QESUITEValidationBAEntity0024_DuplicateBAName, DonlDvdDoOwnrLse*, QDVDGroup(SAP).cpp, m_GetDOsForReversalDVDNew.*
*Companion: QRA Revenue Distribution / Check Write, PPA, Journal/JE, Tax & Regulatory skills; REPO_REFERENCE.*
