# SKILL: QCA Fixed Assets / Inventory / DD&A Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Cost Accounting (QCA) — upstream oil-and-gas accounting suite (myQuorum / On Demand)
**Scope:** The **Fixed Assets / Inventory / DD&A** corner of QCA — **Material Transfers (MT)** through the inventory subledger and out to the GL/JIB/AFE subledgers (FA110/FA120 → QCFS → JIB → GL; AFE_IMPORT to the AFE subledger), **DD&A** (depreciation schedules/methods — UOP, asset-class setup, FA005 post), **Fixed-asset master & inventory master data** (FA010 asset master, FA100/FA150 stock items, stock-item locations/quantities/average cost), and **Capital Tracking (CT)** (AFE/capital approval routes). These three SF case categories — **Inventory (FA)**, **DD&A (FA)**, **Capital Tracking (CT)** — are mined together because they share the MT → subledger → GL pipeline and the FA* screen family.
**Companion skills:** GL / JE code-block & account setup, JIB processing, AFE/billing-deck setup, Check Write / QCFSEXPORT (the revenue/check side of the GL export) live in their own QCA skills — when an MT export fails on a *GL/account* validation the fix is usually in **GL013/GL105** (this skill, §4) but the account design question belongs to the GL/JIB skill.

> **Evidence base:** 185 closed QCA Fixed-Assets/Inventory/DD&A cases (Case_Category__c IN `Inventory (FA)` 77, `DD&A (FA)` 100, `Capital Tracking (CT)` 8). Root-cause split: **(blank) 33, Training 33, Application Configuration 23, Customer Cancelled 21, Customer Error 14, No Action Taken 12, Software Defect 10**, Release Collateral 6, Business Change 5, Hardware/Software Change 5, others. This skill mines the **33 actionable** cases (Application Configuration 23 + Software Defect 10 — there are **no ChangeConfig** cases in this group) for fix recipes, plus ~33 Training and ~14 Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Where a cluster's resolution is thin, it says so explicitly.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — MT export to GL blocked by code-block / account validation (FAGLEXPORT) — HIGH FREQUENCY](#4-cluster-a--mt-export-to-gl-blocked-by-code-block--account-validation-faglexport)
5. [Cluster B — MT post / subledger failures (FAMTPOST / FAMTEDIT, "Post to Subledger failing")](#5-cluster-b--mt-post--subledger-failures-famtpost--famtedit)
6. [Cluster C — MT not importing to the AFE / inventory subledger (mapping & DOI)](#6-cluster-c--mt-not-importing-to-the-afe--inventory-subledger)
7. [Cluster D — DD&A schedule / method / asset-class configuration (UOP, templates, accounts)](#7-cluster-d--dda-schedule--method--asset-class-configuration)
8. [Cluster E — DD&A post / divest / closed-month posting](#8-cluster-e--dda-post--divest--closed-month-posting)
9. [Cluster F — Inventory quantity / average-cost discrepancies](#9-cluster-f--inventory-quantity--average-cost-discrepancies)
10. [Cluster G — FA screen / picklist / grid-layout / security config](#10-cluster-g--fa-screen--picklist--grid-layout--security-config)
11. [Cluster H — Fixed-asset & inventory master data (FA010 / FA110 / FA150, BU & vendor)](#11-cluster-h--fixed-asset--inventory-master-data)
12. [Known ADO Items](#12-known-ado-items)
13. [Diagnostic SQL](#13-diagnostic-sql)
14. [Expected-Behavior / User-Education FAQ](#14-expected-behavior--user-education-faq)
15. [Key Screens, Processes & Repos](#15-key-screens-processes--repos)
16. [Escalation Guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| **FAGLEXPORT errors** "fields not allowed for code block on account NNNN-NNNN" (Inventory ID, Material Transfer No, Serial No, UOM Code, Material Trns Type Code, Cond Code) when exporting MTs to GL / before JIB | The account's **JE Custom Code Type** has those code-block columns set to **NOT ALLOWED** in **GL105**; MT carries inventory code-block values the account rejects | §4 — look up account JE Code Type in **GL013**, then in **GL105** set the offending columns to **Optional** (or Required), re-run FAGLEXPORT |
| "MT (Post to) Subledger failing" / "could not post MT" | Inventory account ↔ company / BU routing, or required validation; sometimes a script to move inventory to the correct company | §5 — get PQID + exact error; check inventory-account-to-company mapping & JIB-month enforcement |
| **MT Imported JE in "Could Not Post" status**; GL025 Vendor No not editable | Code defect — FA110 didn't validate Vendor BA No, JE imported but cannot post | §5 — **Software Defect**, fixed in **2024 October Patch** (24-00957997); FA110 vendor-validation gap also 22-00659963 |
| MT posted to GL but **records didn't import to the AFE subledger** (AFE_IMPORT "no records selected") | **MT100 mapping** wrong / DOI (Prop, Tier) not on the batch | §6 — fix **MT100** mappings (24-00954717) |
| MT data **duplicated in the GL** (one set MT→QCFS→JIB→GL, another MT→JIB→GL) | Duplicate import path | §6 — remove the duplicate set; long-term path reviewed separately (25-01020792 / 25-01025562) |
| DD&A schedule using wrong method — undeveloped reserves included in UOP, or UOP vs UOPLWE | **DD&A schedule / template** assigned wrong method to asset classes | §7 — script to flip the asset-class schedule (UOP → UOPLWE, 26-01085282); re-load DD&A template (26-01083257) |
| DD&A post errors / "month already closed in DDA module" | Closed-month / validation-rule config, or a defect leaving entries unposted | §8 — disable BU/property validation rule congruent with JIB (24-00967388); script + reprocess for closed month (22-00713795) |
| FA Inventory **Property filter / Company droplist not working / not sorted** | Picklist definition (filter-column expression / sort) | §10 — Picklist Definition (e.g. Picklist ID 5042); registered SQL `SELECT_QCA_AUTO_RESOLVE_BU` for the FA010 company-sort (25-01049653) |
| **Can't save Inventory grid layout** | Grid-layout save defect | §10 — fixed in **UPS ≥ 2023.04** (23-00923613); older v17 instance 22-00553555 |
| Stock-item shows an unexpected condition/qty (e.g. "B-Used qty 6") or average-cost mismatch | Inventory quantity/cost reconciliation — usually data, occasionally a script | §9 — compare qty **and** average cost (24-00955854) |
| FA010 missing a Business Unit / new BU not in QCA; FA security | BU not added to FA master / DDA security groups missing | §10/§11 — add BU to FA master (23-00925729); add DDA security groups (23-00923574) |

---

## 2. Pipeline & Concepts

```
[Material Transfer entry: FA110 (MT header/detail) ]
      │  FAMTEDIT (validate/edit)   →   FAMTPOST (post to inventory subledger FA120)
      ▼
[Inventory Subledger  FA120]
      │  FAGLEXPORT  (build GL entry — validates each line against the account's JE code-block rules)
      ▼
[QCFS  → JE (GL025) → GL095 post → GL ]      ── and ──>  AFE_IMPORT  → [AFE Subledger]
      │
      └──►  JIB (joint-interest billing reads the posted GL/AFE)        DD&A:  FA005 load SL → FA05/FADDAPOST post depreciation → GL
```

### Key terms (Quorum/QCA vocabulary)
- **MT** = **Material Transfer** — moves inventory/material between yards/locations or to an AFE/asset. Entered/edited on **FA110**, posted to the inventory subledger **FA120**.
- **FAMTEDIT / FAMTPOST** = the batch processes that **edit/validate** and **post** MTs to the inventory subledger. Implemented in `Quorum.Upstream.QCA.ClassicBatch /QPDllCostAcctgFA/QPSQcaFAMTPost.cpp`. Running both **concurrently** caused a half-post/half-rollback corruption — a lock was added (§5, 23-00889383 / ADO #1585578).
- **FAGLEXPORT** = the process that exports posted MTs from QCA inventory **to the GL** (creating the QCFS/JE entry). It validates **every line's code-block fields against the destination account's JE Custom Code Type** — the single biggest actionable failure (§4).
- **Code block / JE Custom Code Type** = the GL's per-account rule set defining which sub-ledger columns (Inventory ID, Material Transfer No, Serial No, UOM Code, Material Trns Type Code, Cond Code, Quantity …) are **Required / Optional / Not Allowed** on a journal line. Maintained on **GL105 (Custom Code Type Maintenance)**; the account→code-type link is on **GL013**. An MT carries inventory code-block values; if the target account's code type says **Not Allowed**, FAGLEXPORT errors (§4).
- **GL013** = GL account maintenance — shows an account's **JE Code Type** (e.g. `EXP-MISC`, `OPEX-NET-AFE`) and its **IDCODETYPE** value; also where an account is made **visible to QRA / JIB / FA**.
- **GL105** = **Custom Code Type Maintenance** — order by **JE Custom Code ID**, find the code type, set the code-block columns Required/Optional/Not Allowed.
- **MT100** = the mapping config that controls how MT transactions flow into the **AFE subledger** (DOI: Prop, Tier, etc.). Wrong MT100 mapping → AFE_IMPORT selects no records (§6).
- **AFE_IMPORT** = process that pulls posted MT/GL data into the **AFE subledger**. "There were no records selected during AFE Import Validation" = mapping/DOI gap, not a crash (§6).
- **FA005** = load the DD&A / fixed-asset **subledger** for an accounting month (then post depreciation). "Already closed in the DDA module" is a closed-month guard (§8).
- **FA05 / FADDAPOST** = post DD&A (depreciation) entries for the month. Validation business rules (BU/property combination) can block it (§8, 24-00967388).
- **DD&A schedule / template & method** = how an asset class depreciates. **UOP** = Units of Production (uses reserves); **UOPLWE** = UOP **without** undeveloped reserves ("Less Undeveloped/With Expected"-type variant). Assigning the wrong method to asset classes (ARO, CAPINT, DIC/DTC, etc.) over/understates DD&A; the fix is a schedule/asset-class **config script** (§7, 26-01085282).
- **FA010** = fixed-asset **master** list (per Business Unit); FA100/FA150 = stock items / stock-item-to-account setup; FA110/FA120 = MT entry / inventory subledger; FA070/FA060 = depreciation detail/summary.
- **QCFS** = the financial-staging layer the GL export writes through (shared with revenue/check write). **JIB** = joint-interest billing downstream.

---

## 3. Decision Tree

```
QCA Fixed-Assets / Inventory / DD&A case
│
├─ A process FAILED with an error? (FAGLEXPORT / FAMTPOST / FAMTEDIT / AFE_IMPORT / FA005 / FA05)  → GET PQID + EXACT ERROR TEXT + the ACCOUNT NUMBER
│   ├─ FAGLEXPORT "fields not allowed for code block on account NNNN-NNNN"        → §4  (GL013 → GL105: set columns Optional/Required; config)
│   ├─ MT post/subledger fails / "could not post MT"                              → §5  (inventory-account↔company routing; JIB-month enforce; script)
│   ├─ MT Imported JE stuck "Could Not Post" / Vendor No not editable             → §5  (Software Defect — Oct-2024 Patch; FA110 vendor validation gap)
│   ├─ FAMTPOST/FAMTEDIT half-posted / ran concurrently / slow                    → §5  (concurrency lock #1585578; perf #1644523)
│   ├─ AFE_IMPORT "no records selected"                                           → §6  (MT100 mapping / DOI)
│   └─ FA005 "month already closed in DDA module" / FA05 DD&A post errors         → §8  (closed-month guard / validation rule)
│
├─ Output WRONG (not a crash)?
│   ├─ MT data DUPLICATED in GL                                                   → §6  (duplicate import path — remove dup set)
│   ├─ DD&A amount wrong / wrong method (UOP vs UOPLWE) / undeveloped reserves     → §7  (schedule/asset-class config script)
│   └─ Stock-item qty / average-cost mismatch                                     → §9  (reconcile qty AND avg cost; data)
│
├─ A SCREEN/UI problem? (filter, droplist sort, grid layout, missing BU/security) → §10  (picklist def / registered SQL / metadata / grid-layout fix ≥2023.04)
│
├─ MASTER DATA missing/invalid? (FA010 BU, FA110 vendor BA/sub, FA150 accounts)   → §11
│
└─ "How do I set up …" / UOP question / "where does X come from" / cancelled      → §14 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — MT export to GL blocked by code-block / account validation (FAGLEXPORT)

**The single largest actionable signature in this group.** Posted Material Transfers fail to export to the GL because the **destination GL account's JE Custom Code Type forbids the inventory code-block fields** the MT carries (Inventory ID, Material Transfer No, Serial No, UOM Code, Material Trns Type Code, Cond Code, Quantity). FAGLEXPORT validates every line, so one mis-configured account blocks the whole run — and because **JIB reads the posted GL**, it blocks JIB for the month too.

**Symptom (verbatim, 24-00977772):** "error in the FAGLEXPORT process, showing that some of the fields for Material Transfers MT20 and MT21 were not allowed for code block based on the account 7210-1690." (26-01082941: "got the errors when trying to export MTs to the GL. The MTs were final posted to the subledger so they cannot be deleted.")

**Root cause:** the account's JE Custom Code Type (looked up via **GL013 → IDCODETYPE / JE Code Type**, e.g. `EXP-MISC`, `OPEX-NET-AFE`) has the inventory columns set to **NOT ALLOWED** in **GL105**. The MT was correctly posted to the inventory subledger and **cannot be deleted**, so you can't fix it by re-entering — you must make the account accept the columns.

**Fix recipe (repeatable — 26-01082941, 24-00977772):**
1. From the FAGLEXPORT error, note the **account number** and the **code-block fields** it rejected.
2. In **GL013**, look up that account's **JE Code Type** (e.g. account `6200-8011` → `EXP-MISC`; account `7210-1690` → IDCODETYPE `3426` = `OPEX-NET-AFE`).
3. In **GL105 (Custom Code Type Maintenance)**, **order by JE Custom Code ID** and locate that code type.
4. Change the offending columns — **Inventory, Serial Number, Quantity, UOM Code, Mtrl Trns Type Code** (and Inven ID / Material Transfer No / Cond Code as listed) — from **Not Allowed** to **Optional** (or **Required** if the client wants them enforced). Hit **Update**.
5. **Re-run FAGLEXPORT.**

> **Note (24-00977772 nuance):** the trigger was a user coding an MT to the **Net** account instead of the **Gross** account; the *correct* long-term answer is "code MT20/MT21 to the proper gross account," but the *unblock* is the GL105 code-type change so the already-posted MT can export. Decide with the client whether to loosen the code type or reverse/re-key — but the MT can't be deleted once final-posted.

---

## 5. Cluster B — MT post / subledger failures (FAMTPOST / FAMTEDIT)

MTs that fail to post to the inventory subledger, or post into a bad state. Mix of **config/data** (account↔company routing, validation enforcement) and a couple of confirmed **defects**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| "MT Post to Subledger failing" | Inventory sitting on the wrong company | **Script to move inventory from company 506 to company 2** | 26-01084706 |
| "Inventory errors … need to disconnect the inventory subledger from inventory account" (validation after AP055, GL code set up, no red boxes) | Inventory-subledger ↔ inventory-account linkage / validation config | App-config fix (resolution thin in case text — confirm the subledger-to-account disconnect was applied) | 26-01096717 |
| "Unable to Proceed with Posting MT" | JIB-month not enforced on all accounts | **Modified registered SQL to enforce JIB month for all accounts** | 24-00947606 |
| **MT Imported JE in "Could Not Post" status**; FA110 let an MT save with no valid Vendor BA No.; GL025 "Vendor No" not editable, picklist does nothing | **Software Defect** — FA110 had **no validation** on Vendor BA No., so the JE imported but couldn't post | **Hotfix included in the 2024 October Patch** (deployed to PRD 11/22/2024) | **24-00957997** (Defect) |
| "FA110 does not validate vendor ba and sub" (MEW upgrade) | Same FA110 vendor-validation gap, surfaced on upgrade | Software Defect | 22-00659963 |
| **FAMTPOST and FAMTEDIT executed concurrently → both completed with system errors and did NOT roll back** (half posted / half rolled back; FA120 vs FA110 out of sync) | No lock prevented simultaneous execution; rollback not graceful | **A new lock was added to prevent simultaneous execution** of the two processes; hotfix delivered & validated | **23-00889383** / **ADO #1585578** (Bug, Closed) |
| MT post "System.AggregateException" errors | Process error | "Fix has been provided" (resolution thin — confirm build) | 22-00852476 |
| FAMTEDIT / FAMTPOST slow | Performance | Perf fix | **ADO #1644523** (Bug, Closed) |

**Fix recipe:** get the **PQID + exact error + the account/company involved**.
- "Could Not Post" JE with an **un-editable Vendor No** on GL025 → the **FA110 vendor-validation defect** (24-00957997 / 22-00659963); confirm the client is on the **2024 October Patch or later**. You generally cannot clear the bad vendor on the imported batch (GL025 Vendor No is read-only, picklist disabled) — the proper path is the patched validation plus re-keying.
- MT "can't post / subledger failing" that resolves with a script (move inventory to the right company, 26-01084706) is **data/routing**, not a defect — verify the inventory account's company assignment first.
- **Never run FAMTPOST and FAMTEDIT at the same time** on older builds without #1585578 — concurrency caused unrecoverable half-posts (23-00889383). If you see FA120 and FA110 disagreeing after a concurrent run, that's the signature.

---

## 6. Cluster C — MT not importing to the AFE / inventory subledger

MT posted fine to the GL, but the **AFE subledger** import found nothing — or data came in **twice**. These are **mapping / DOI config**, not engine bugs.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| MT posted to GL but **not imported to AFE SL**; AFE_IMPORT "There were no records selected during AFE Import Validation"; DOI (Prop, Tier) not on the batch | **MT100 mapping** wrong / incomplete | **Instructed customer to modify MT100 mappings** | 24-00954717 |
| MT data **duplicated in the GL** — one set came in normally (MT → QCFS → JIB → GL), the same set also came in **directly MT → JIB → GL** | Duplicate import path | Support walked the client (via meeting) through **removing the duplicated rows**; the *how-it-got-in-twice* long-term fix tracked in **25-01025562** | 25-01020792 |
| "Re-Loading DD&A Template" — changes to Fixed Assets implemented in **FA and AFE SL tables** | Master/template change | Implemented the requested FA/AFE SL table changes | 26-01083257 |

**Fix recipe:** when an MT posts to GL but the **AFE subledger is empty after AFE_IMPORT**, check **MT100 mappings** and confirm the **DOI details (Prop, Tier)** are populated on the MT batch (24-00954717). For **duplicated GL amounts**, look for the data arriving via **two paths** (the normal MT→QCFS→JIB→GL and a direct MT→JIB→GL) and remove the duplicate set; flag the root path for a long-term fix (25-01020792 → 25-01025562).

---

## 7. Cluster D — DD&A schedule / method / asset-class configuration

DD&A amounts that are wrong because the **depreciation schedule/method assigned to asset classes is wrong** — most often **UOP vs UOPLWE** (whether undeveloped reserves are included). These resolve as **config scripts / template reloads**, not code.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Asset classes (ARO, CAPINT, CIC/CTC, DIC/DTC, FIC/FTC, G&G, WIC/WTC) were including **undeveloped reserves** in the system UOP calc | Wrong DD&A method on those asset classes | **Script to update the schedule from UOP → UOPLWE** for the listed FA_CLASS_CDs so undeveloped reserves are excluded | 26-01085282 |
| "Re-Loading DD&A Template" | Template/account changes | Changes implemented in the **FA and AFE SL tables** | 26-01083257 |
| **DDA Conversion loaded with the wrong account number** (SQL update request) | Conversion/data loaded to wrong account | SQL update to correct the DD&A schedule account | 24-00950314 |
| "Can we separate DEPR amounts from ASSET END amounts under an ASSET ID in the DDA schedule report?" | Report/schedule layout question | Schedule/report config (representative of report-layout requests) | 24-00950314 (desc) |

**Fix recipe:** when DD&A is over/understated, first confirm the **method assigned to the asset class** (UOP includes reserves; UOPLWE excludes undeveloped reserves). Flipping the schedule is a scoped **config script keyed by FA_CLASS_CD** (26-01085282). For "wrong account" symptoms, check whether a **conversion loaded the schedule to the wrong GL account** (24-00950314). Template-driven changes go through the **DD&A template + FA/AFE SL tables** (26-01083257). **Verify-SELECT before any schedule/asset-class UPDATE.**

---

## 8. Cluster E — DD&A post / divest / closed-month posting

Posting depreciation, or removing/divesting assets, where a **validation rule** or **closed-month guard** blocks or mis-handles the post.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Posting DD&A in **FA05** threw many errors for a line | **Validation business rules** validating BU/property combination were active | **Disabled** that validation rule **congruent with JIB processing** | 24-00967388 |
| DD&A May entries showed posted in FA005 but **didn't actually post**; re-post blocked by "The accounting month you have selected has already been closed in the DDA module." | Earlier process failures left entries unposted; module then closed the month | **Script to update records and reprocess DD&A Post** for the month | 22-00713795 (Software Defect) |
| Need to **remove properties from DDA when divesting** | No clean product path to divest properties from DD&A | **Data-script workaround provided** while the long-term solution sits with Engineering | 22-00688736 (Software Defect) |
| "DDA Calc Warning on Schedule Map" | Schedule-map warning | Software Defect (resolution thin — confirm via linked WI/build) | 22-00644854 |
| User unable to **export data from QCA to QCFS** | Export defect | "Will run script if this happens in a future month" (operational; underlying defect) | 22-00678237 (Software Defect) |

**Fix recipe:** for **FA05 DD&A post errors**, check for an active **BU/property validation business rule** and confirm it should be **disabled congruent with JIB** (24-00967388). For "**month already closed in the DDA module**" after a partial/failed post, the fix is a **script to correct the unposted records + reprocess the DD&A post** for that month (22-00713795). **Divesting properties from DD&A** has no clean UI path — expect a **data-script workaround** (22-00688736); set client expectations accordingly.

---

## 9. Cluster F — Inventory quantity / average-cost discrepancies

Stock items showing an unexpected condition/quantity or an average-cost mismatch. These are **reconciliation / data** cases — the fix is a corrected comparison script, not a code change.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Stock item #1001206 showing **"B – Used, Qty 6"** that the client couldn't tie to any MT | Discrepancy surfaced only when comparing **quantity in addition to average cost** | Initial script compared only **average cost**; adding a **Quantity comparison** revealed the same discrepancy lines (1001180, 1001226) — reconcile on **both qty and cost** | 24-00955854 |

**Fix recipe:** when a stock-item quantity/condition "doesn't tie," **reconcile on both average cost and quantity** — a cost-only comparison misses qty-only drift (24-00955854). Trace the contributing **MT transactions** for that stock item / yard / condition. This is a small cluster; if a discrepancy can't be tied to MTs and isn't a scripting artifact, treat it as a data investigation rather than assuming a defect.

---

## 10. Cluster G — FA screen / picklist / grid-layout / security config

A steady stream of **screen/UI** issues — picklist filters not working, droplists not sorting, grid layouts not saving, security/metadata. Mostly **Application Configuration** with two confirmed grid-save **defects**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **FA Fixed-Assets Inventory Property filter not working** | Picklist filter-column expression incomplete | In **Pick List Definition → Picklist ID 5042 (Property Pick / Level 5 Organization) → Query Cols tab**, updated the **Filter Column Expression** to include **PROP_NO and PROP_NM** for rows 3 and 4 | 23-00909885 |
| **FA010 Company droplist not sorted** by BU# (regressed in 2025.05; was sorted in 2020.09) | Registered-SQL sort | **Script to update registered SQL `SELECT_QCA_AUTO_RESOLVE_BU`** to restore BU# sort | 25-01049653 |
| **Can't save changes to the Inventory grid layout** | Grid-layout save defect | **Fixed in UPS versions ≥ 2023.04** | 23-00923613 (Software Defect) |
| "Unable to save changes to grid layout" (older) | Same grid-save defect family | Also exists in **v17 upgrade**, tracked on **#21-00197079** | 22-00553555 (Software Defect) |
| **Material Transfer Doc Attachment config missing** | Document-management not enabled | **Global config Key Group `DOCMGMT`, Key `ENABLED` set to 1** on the QVTL layer + metadata check-in | 25-01035711 |
| Stock Item & Location **Report description** wrong | Metadata | **Changes made to metadata** | 23-00889311 |
| **Fixed Assets security** (Lauren Lister) | Missing security groups | **Added DDA groups** | 23-00923574 |
| **FA010 missing Business Units 510 & 515** from the fixed-asset master list (PRDA1) | BUs not in the FA master | Add the BUs to the FA master (App-config) | 23-00925729 |
| Adding accounts to **FA150** | Stock-item/account setup | App-config (resolution blank — confirm the FA150 account add) | 24-00965803 |
| QCA **Approval Route** (Capital Tracking) | Custom approval routing | **Set up a custom route to take the PRL approval route** | 23-00913818 (Capital Tracking) |
| Material Transfer **Post processing time / performance** | Perf | Linked to 23-00889383 (the concurrency/perf family) | 23-00910384 |

**Fix recipe:** screen issues are almost always **config**:
- **Filter not working** → Pick List Definition → the picklist's **Query Cols → Filter Column Expression** (23-00909885, Picklist ID 5042).
- **Droplist not sorted** → the **registered SQL** behind it (`SELECT_QCA_AUTO_RESOLVE_BU` for FA010 company sort, 25-01049653).
- **Grid layout won't save** → confirm build; this is a **fixed defect at ≥ 2023.04** (23-00923613), older v17 = #21-00197079.
- **Missing attachment / report / column** → **global config (DOCMGMT/ENABLED) or metadata** (25-01035711, 23-00889311).
- **Missing BU / missing access** → add the BU to the FA master (23-00925729) or add **DDA security groups** (23-00923574).

---

## 11. Cluster H — Fixed-asset & inventory master data

Master-data gaps that block MTs or FA processing — the line between this and §10 is thin; group here when the missing thing is a **record** (BU, vendor, account) rather than a screen behavior.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **FA110 does not validate vendor BA and sub** | No validation on Vendor BA No. → invalid vendor saved → JE can't post | **Software Defect** (same family as the "Could Not Post" JE, §5); FA110 validation fix | 22-00659963, 24-00957997 |
| **FA010 missing BUs 510 / 515** | BUs not added to FA master | Add BUs to FA master | 23-00925729 |
| Adding accounts to **FA150** | Stock-item account setup | App-config | 24-00965803 |
| Voucher reclass bug (capital) | Code defect on voucher reclass | **Long-term code fix in package 35** (legacy) | 22-00641109 (Bug 135279) |

**Fix recipe:** confirm the **master record exists and is valid for the effective dates / BU** before chasing a process error — a missing FA010 BU (23-00925729) or an invalid FA110 vendor (22-00659963/24-00957997) presents downstream as a post/export failure. The FA110 vendor gap is a **patched defect** (Oct-2024 Patch), so on current builds the screen should now block the bad vendor.

---

## 12. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1585578** | Bug / **Closed** | SRC — Material Transfer Post: FAMTPOST/FAMTEDIT executed simultaneously → improperly rolled back (lock added) | §5 | 23-00889383 |
| **#1644523** | Bug / **Closed** | SRC — Performance issue for Material Transfer FAMTEDIT and FAMTPOST process | §5 | (perf follow-on) |
| **#1735154 / #1741527** | Requirement / Task / **Closed** | QCA Performance Review — FAMTPOST (+ TEST) | §5 | — |
| **#1551158** | Requirement / **Closed** | GEC (VSTS 263573) — Update FAGLEXPORT to generate a generic source description for MATTRANS | §4 | — |
| **#251709** | Change / **Closed** | VOG — UAT script deploy: FA120 SL batch posted to CAPEX account after JIB close; errors in FAGLEXPORT | §4/§8 | — |
| **#1363917** | Requirement / Proposed | Upstream: QCA: DD&A | §7 | — |
| **#1365829 / #1411270 / #1599820 / #1599864** | Requirement / Proposed | QCA — DD&A Training / DD&A Configuration (CRC) | §7/§14 | — |
| **#21-00197079** | (legacy SF/WI ref) | v17 grid-layout save issue (carried from 22-00553555) | §10 | 22-00553555 |

> Several actionable cases were dispositioned **operationally** (config or data script) with **no single product WI**: FAGLEXPORT code-block fixes via GL105 (26-01082941, 24-00977772) are pure config; the FA110/"Could Not Post" vendor defect (24-00957997) shipped in the **2024 October Patch** (PRD 11/22/2024) — confirm via the QCA/Upstream release notes; grid-layout save is fixed at **UPS ≥ 2023.04** (23-00923613). When stating fix availability, verify the exact build/patch in the Upstream/QCA release notes.

---

## 13. Diagnostic SQL

> **Caveat:** QCA table/column names below are taken from case repro text, screen names, and code search; **verify against the client schema before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction. Screen lookups (GL013/GL105/FA110/FA010/Pick List Definition) are usually faster than raw SQL for the config clusters.

```sql
-- A. An account's JE Custom Code Type and its code-block column rules (the §4 FAGLEXPORT block)
--    Step 1: find the account's JE Code Type / IDCODETYPE (mirror of GL013).
SELECT ACCT_NO, ACCT_NM, JE_CODE_TYPE, IDCODETYPE
FROM   <GL account master>            -- GL013 backing table
WHERE  ACCT_NO = '7210-1690';
--    Step 2: see which code-block columns are Not Allowed / Optional / Required for that code type (mirror of GL105).
SELECT JE_CUSTOM_CODE_ID, COLUMN_NAME, ALLOW_FLAG   -- Not Allowed / Optional / Required
FROM   <custom code type maintenance table>          -- GL105 backing table
WHERE  JE_CUSTOM_CODE_ID = 'OPEX-NET-AFE'
ORDER BY COLUMN_NAME;
-- Red flag: INVENTORY / SERIAL_NO / QUANTITY / UOM_CODE / MTRL_TRNS_TYPE_CODE = 'NOT ALLOWED' on an account that receives MTs.

-- B. MT header/detail vs inventory subledger (FA110 vs FA120) — the §5 concurrency half-post signature
SELECT MT_NO, BATCH_NO, POST_STATUS, POST_DT
FROM   <FA110 MT table>
WHERE  BATCH_NO = '<BATCH>';
SELECT MT_NO, BATCH_NO, POST_STATUS
FROM   <FA120 inventory subledger table>
WHERE  BATCH_NO = '<BATCH>';
-- Red flag: FA110 shows posted but FA120 has no row (or vice-versa) after FAMTPOST/FAMTEDIT ran concurrently.

-- C. MT not importing to AFE SL — DOI present on the batch? (§6, MT100 mapping)
SELECT MT_NO, PROP_NO, TIER, AFE_NO, ACCT_MTH
FROM   <FA120 inventory subledger table>
WHERE  BATCH_NO = '<BATCH>';
-- Red flag: PROP_NO / TIER null when AFE_IMPORT returns "no records selected".

-- D. DD&A schedule/method per asset class (§7, UOP vs UOPLWE)
SELECT FA_CLASS_CD, FA_CLASS_DESCR, DDA_SCHEDULE_CD, DDA_METHOD
FROM   <FA asset-class / schedule map table>
WHERE  FA_CLASS_CD IN ('ARO','CAPINT','CIC','CTC','DIC','DTC','FIC','FTC','G&G','WIC','WTC');
-- Red flag: DDA_METHOD = 'UOP' where the client wants undeveloped reserves excluded (should be 'UOPLWE').

-- E. DD&A accounting-month status (the §8 "already closed in DDA module" guard)
SELECT ACCT_MTH, MODULE_CD, CLOSE_STATUS, CLOSE_DT
FROM   <DD&A accounting-month / module-close table>
WHERE  MODULE_CD = 'DDA' AND ACCT_MTH = '<ACCT_MTH>';

-- F. Stock-item reconciliation — compare BOTH quantity and average cost (§9)
SELECT STOCK_ITEM_NO, YARD_CD, COND_CD, ON_HAND_QTY, AVG_COST
FROM   <inventory on-hand table>
WHERE  STOCK_ITEM_NO = '1001206'
ORDER BY YARD_CD, COND_CD;
-- Reconcile against the sum of contributing MT transactions for that stock item / yard / condition.

-- G. FA010 missing BU (§10/§11)
SELECT BUS_UNIT_NO, BUS_UNIT_NM FROM <FA010 fixed-asset master table>
WHERE  BUS_UNIT_NO IN ('510','515');   -- expect rows; absence = the 23-00925729 pattern.
```

---

## 14. Expected-Behavior / User-Education FAQ

~33 Training + ~14 Customer-Error cases. Recognize these to avoid needless scripts/escalations. **DD&A / UOP setup questions dominate.**

| Reported as | Reality / answer | Case |
|---|---|---|
| "DD&A **Units of Production** — impact of first sales date on templates / WIP to NET for UOP / UOP pre-work" | **Training** — UOP method, first-sales-date, and WIP→NET behavior are configuration/education topics; walk through the DD&A schedule + template setup (see §7 for the *config* version) | 26-01085283, 26-01085279, 26-01082880, 26-01082741, 26-01081034 |
| "FA050 / FA070 / GL014 question," "Book depreciation questions," "FA070 vs FA060 depreciation difference" | **Training** — explain how the depreciation detail/summary screens tie out; FA070↔FA060 differences are usually method/timing, not a bug | 26-01085280, 26-01085274, 26-01085271, 25-01031978 |
| "Adding and deleting assets in DDA" / "write off / close out assets for DDA tax schedules" | **Training** — asset add/retire flow (note: *divesting* properties needs a script workaround — §8, 22-00688736) | 22-00713827, 22-00688795 |
| "Can't get depreciation to **stop** calculating on a zero-value asset" | **Training/Customer-Error** — the asset/schedule must be **retired/end-dated**; depreciation follows the schedule until then | 25-01020521 |
| "Error in **FA005** — can't load subledgers" / "DDA error loading SL in FA005" | Usually **Customer Error / setup** — subledger not ready, month/validation; check before assuming a defect | 25-01012821, 22-00644926 |
| "New **BU not showing up in QCA** / FA" | **Training/config** — the BU must be added to the FA master (the *config* fix is §10/§11, 23-00925729) | 22-00547140 |
| "**Inventory Clearing Account** / Fixed-Assets Inventory **set up** question" | **Training** — clearing-account and inventory setup walkthrough | 24-00983531, 22-00667786 |
| "**Property Addition** transaction issue," "FA120 screen tables & data ties," "FA005 question" | **Training** — how the FA screens/tables tie together | 22-00513225, 22-00646279, 24-00948564 |
| Screen COM error in FA110 ("Either BOF or EOF is True…") / "Unable to Obtain Lock" / "DDA Accounting Month Screen Error" | Often **transient / session / lock** — retry, clear the lock, re-enter; capture the exact COM error + PQID if it persists | 23-00924324, 22-00631165, 22-00559016 |
| "DDA **import** not working" (UAT) / "Fixed Asset Process Failure" / "PUBBA Full Synch times out" | Frequently **conversion/UAT data or environment**, not core code — verify the import file/mapping and environment first | 23-00905266, 23-00921321, 23-00904374 |

**Tell-tale it's user/expected:** a **UOP/DD&A "how does it work / how do I set up" question** (by far the most common — route to training, not Engineering); depreciation that "won't stop" on a zero-value asset that simply hasn't been **retired/end-dated**; a "new BU not in QCA" that just needs adding to the FA master; or an FA005/FA110 screen error that's a **transient lock/session** issue. Confirm the **DD&A schedule/method, asset-class setup, and the GL013/GL105 account config** before treating any of these as a defect.

---

## 15. Key Screens, Processes & Repos

### Screens
| Screen | Purpose |
|---|---|
| **FA010** | Fixed-asset master (per Business Unit); company droplist sort = registered SQL `SELECT_QCA_AUTO_RESOLVE_BU` |
| **FA100 / FA150** | Stock items / stock-item-to-account setup |
| **FA110 / FA120** | Material Transfer entry (header/detail) / inventory subledger |
| **FA005** | Load DD&A / fixed-asset subledger for an accounting month |
| **FA05** | Post DD&A (depreciation) entries |
| **FA050 / FA060 / FA070** | DD&A schedule / depreciation summary / depreciation detail |
| **GL013** | GL account maintenance — JE Code Type / IDCODETYPE; QRA/JIB/FA visibility |
| **GL105** | **Custom Code Type Maintenance** — set code-block columns Required/Optional/Not Allowed (the §4 fix) |
| **MT100** | MT → AFE subledger mapping (§6) |
| **Pick List Definition** | Picklist filter/sort config (e.g. Picklist ID 5042 Property Pick, §10) |

### Processes / batch steps
| Process | Purpose | Notes |
|---|---|---|
| **FAMTEDIT** | Validate/edit MTs | Do **not** run concurrently with FAMTPOST on builds < #1585578 |
| **FAMTPOST** | Post MTs to inventory subledger (FA120) | `QPSQcaFAMTPost.cpp`; concurrency lock #1585578; perf #1644523 |
| **FAGLEXPORT** | Export posted MTs to the GL (via QCFS/JE) | Validates each line vs the account's code-block rules → §4 |
| **AFE_IMPORT** | Import MT/GL data to the AFE subledger | "no records selected" = MT100/DOI gap (§6) |
| **FA05 / FADDAPOST** | Post DD&A | BU/property validation rule can block (§8) |

### Code locations (confirmed via ADO code search)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `QPSQcaFAMTPost.cpp` (FAMTPOST) | `Quorum.Upstream.QCA.ClassicBatch /QPDllCostAcctgFA/` | §5 |
| `QFrmInventorySubledger.cs` | `Quorum.Upstream.QCA.ClassicGUI /Quorum.QCA.FA/` | §5/§9 inventory subledger screen |
| QCA process/step/param config (FAMTPOST, FAGLEXPORT defined here) | `SUM.Upstream.Metadata /STANDARD <ver>/QARCH_CTRL_PROCESS*.json`, `QARCH_CTRL_PARAM*.json` | §4/§5 |

### Repos
- **`Quorum.Upstream.QCA.ClassicBatch`** — C++ FA/cost-accounting batch (`QPDllCostAcctgFA` → FAMTPOST/FAMTEDIT/FAGLEXPORT/DD&A post).
- **`Quorum.Upstream.QCA.ClassicGUI`** — FA/Inventory/DD&A screens (`Quorum.QCA.FA`).
- **`SUM.Upstream.Metadata`** (+ client `*.Upstream.Metadata`) — process/step/param + screen metadata, picklist definitions, code-block (GL105) config. **Check the client metadata/QVTL layer for config overrides** (e.g. DOCMGMT/ENABLED, 25-01035711).
- Many fixes here are **config in metadata or registered SQL**, or **data scripts** — not core C++ changes. Check the client layer first.

---

## 16. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A process **crashes/corrupts from a code bug, not data**: FAMTPOST/FAMTEDIT concurrency half-post (23-00889383 / #1585578 — lock added); FAMTPOST performance (#1644523).
- A **screen fails to validate / save** as designed: FA110 not validating Vendor BA No. → "Could Not Post" JE (24-00957997 — **2024 October Patch**; 22-00659963); Inventory **grid-layout won't save** (23-00923613 — **fixed ≥ 2023.04**; legacy v17 #21-00197079).
- DD&A leaves entries **unposted** / can't divest cleanly (22-00713795, 22-00688736 — long-term solution with Engineering; interim is a data script).
- Provide: **PQID + exact error text + the account/BU/MT batch + accounting month**, the client, and a repro. Confirm fix availability in the Upstream/QCA release notes and the linked WI's target build.

**Handle as Configuration (Cloud Ops / consultant) when:**
- **FAGLEXPORT code-block block** — set the account's code type columns to Optional/Required in **GL105** (look up the code type in **GL013**); re-run (26-01082941, 24-00977772). This is the most common actionable fix in the group.
- **MT → AFE not importing** — fix **MT100 mappings** / ensure DOI on the batch (24-00954717).
- **DD&A wrong method** — flip the asset-class schedule (UOP → UOPLWE) via a config script keyed by FA_CLASS_CD (26-01085282); correct conversion accounts (24-00950314).
- **Screen/picklist/sort/security** — Pick List Definition filter expression (23-00909885), registered SQL sort `SELECT_QCA_AUTO_RESOLVE_BU` (25-01049653), DDA security groups (23-00923574), global config `DOCMGMT/ENABLED` (25-01035711), metadata (23-00889311).
- **FA05 DD&A post blocked** by a BU/property validation rule — disable it congruent with JIB (24-00967388).

**Handle as Data fix when:** inventory on the wrong company (script to move company 506→2, 26-01084706); duplicated GL rows from a double import path (25-01020792); closed-month DD&A reprocess (22-00713795); stock-item qty/cost reconciliation (24-00955854); missing FA010 BU (23-00925729). **Always verify-SELECT in a transaction first.**

**Handle as Training / Expected behavior (no fix):** see §14 — **UOP/DD&A setup & "how does it work" questions** (the dominant Training theme), depreciation that "won't stop" on an un-retired asset, "new BU not in QCA," inventory/clearing-account setup, and transient FA005/FA110 screen/lock errors. Verify the **DD&A schedule/method, asset-class setup, and GL013/GL105 account config** before treating as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 185 closed QCA Fixed-Assets/Inventory/DD&A SF cases (Inventory (FA) 77, DD&A (FA) 100, Capital Tracking (CT) 8) — 33 actionable (Application Configuration 23 + Software Defect 10; no ChangeConfig cases in this group) mined for fix recipes, plus ~33 Training and ~14 Customer-Error cases for the FAQ. ADO work items #1585578, #1644523, #1735154/#1741527, #1551158, #251709, #1363917, #1365829/#1411270/#1599820/#1599864.*
*Companion: QCA GL/JE & JIB skill, QCA Check Write / QCFSEXPORT skill, QCA AFE / billing-deck skill, REPO_REFERENCE.*
