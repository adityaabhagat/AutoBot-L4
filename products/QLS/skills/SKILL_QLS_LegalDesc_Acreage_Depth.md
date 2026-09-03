# SKILL — QLS Legal Description, Acreage & Depth

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Coverage-plan group #4:** Legal Description, Acreage & Depth — 1,471 cases all-time, 222 actionable (Software Defect + Application Configuration). Folds in: Legal Description, Legal Block Description, Acreage, Depth, Aliquot, Chain of Title, Undivided Interest, Tract Relations.
> **Sources:** all-history Salesforce mining (6 validated SOQL inventory pages ≈140 case rows, 31 cases sampled in depth via Description + `Resolution__c` + CaseFeed) + ADO work-item mining (org QuorumSoftware, project `QuorumSoftware`, area paths `Engineering\Land\Committed Backlog`, `Engineering\Maintenance\Upstream\Customer Service\Land`). Mined 2026-09-03.
> **Auto-Bot skill** — built by Aditya Bhagat. Every claim cited to SF case number or ADO work item ID. Customer employee names/emails redacted; 3-letter client codes retained where they identify a client-layer override.

---

## 1. Quick Triage

| Symptom (verbatim-style) | Cluster | Likely gate |
|---|---|---|
| "Cannot save/delete legal description" + *no data found* error | C1 | G3 version (MapLegalDetail trigger fix) |
| "Legal description shows in tree but node is empty / can't delete it" | C2 | G4 bad data (orphan segment rows) |
| "Acres field won't take more than 9,999 / 10,000 acre limit" | C3 | G2 config (validation rule) |
| "Net acreage didn't recalculate / wrong rollup / inactive acres included" | C4 | G4 bad data → G5 (ACRE_CALC package) |
| "Formations disappear after save / must add formations twice" | C5 | G3 version (Measured Depth Only defect) |
| "Error adding depth — FormationsFilter.FormKey invalid filter" | C5 | G2 config + G4 missing FORMATIONS_FILTER data |
| "Formation missing from All Depths list / dropdown for a state-county" | C5 | G2/G4 (FORMATIONS_FILTER reference data) |
| "Depth interval stuck — exists at agreement level AND depth level" | C6 | G4 bad data (cleanup script) |
| "Can't rename Areal that has depth subdivisions" | C6 | G4 (admin-type row removal) |
| "Save with Note on Participation change — note missing from Chain of Title" | C7 | G3 version (hotfixed on all trains) |
| "Mass legal upload notes duplicated / dropped; tree counts stale after import" | C8 | G3 version |
| "Lots don't auto-populate acreage / Tax Parcel-Jeffersonian tab missing / need new townships-sections" | C9 | G2 config + reference data |
| "Legal Description save is slow / spinner never ends / grids blank" | C10 | G3 version → G2 config |

Triage questions to ask first (from repeated case patterns):
1. **Is `MapLegalDetail` ON or OFF for this client?** The single most common legal-description save/delete failure family flips on this config (SF 24-00941202, 24-00970216; ADO 1655451). Ask before reading any code.
2. **Which legal type?** Jeffersonian (township/range/section) vs Non-Jeffersonian vs Metes & Bounds vs Tax Parcel vs Other Legal — screens, grids, validation objects, and landgrid tables differ per type (SF 25-01020784 tested Jeff and Non-Jeff separately; 24-00990093 is Tax-Parcel-only).
3. **Did the acreage number *save* wrong, or *display/rollup* wrong?** Wrong stored value → validation/entry issue (C3). Right stored value, wrong total → ACRE_CALC package / rollup (C4).
4. **Client build vs hotfix train.** The formations-on-save and Chain-of-Title-notes defects are hotfixed on every train 2022.04→2025.04 — check version (G3) before investigating code (ADO 1712613, 1691135).

---

## 2. Decision Tree

```
Legal Description screen error?
├─ "no data found" on save/delete of legal rows
│   └─ MapLegalDetail config OFF but trigger expects LGL_DTL_KEY_RLTN rows
│       → G3: TR_LD_METES_BOUNDS_LGL_DTL fixed to check MapLegalDetail [24-00941202, 24-00970216]
├─ Delete Agreement fails when agreement has a legal description
│   └─ MapLegalDetail config ON → known defect, hotfixed 2023.04/2024.04 [ADO 1655451]
├─ Tree shows an (agreement-level) legal that opens empty / cannot delete
│   → G4: orphan rows in LIS.LEGAL_DESCRIPTION_SEGMENTS + LIS.LD_ACREAGES [24-00981552]
├─ Grids not rendering at all on a new agreement → config-tagged defect [ADO 1656718]
└─ "Entered Country and State setup is invalid" on Legal/Tax Parcel tab
    → G2: state/county setup (APOL_AREA_STATES + landgrid) incomplete for that country [24-00990093]

Acreage wrong?
├─ Cannot ENTER >9,999 acres → G2: inactivate/adjust QLSValidationLegalDescription0015_CheckSegAcres
│   in QARCH_CTRL_OBJECT_USE at client layer [25-01030271, 26-01103576, ADO 1747387]
├─ Subdivision-level edits saved but header net acreage not recalculated
│   → run ACRE_CALC package via script (500+ records at one client) [25-01032413]
├─ INACTIVE areal net/company-net acres rolling into header totals
│   → acreage-calc package regression; client reverted package version [25-01003323, 26-01113965]
├─ Header acreage rounded to 3 decimals → ACRE_CALC rounding changed to 6 [25-01045304]
├─ New agreement type doesn't calculate acreage → data cleanup script [24-00976925]
└─ Areal/Depth acreage-participation rollup or Agreement Summary grid wrong
    → known treeview/rollup defects [ADO 1751387, 1752049]

Depth / Formations problem?
├─ Formations vanish after save ("must add twice")
│   ├─ Depth type = Measured Depth Only → G3: QQLSServiceCore_DepthIntervals.cs:327
│   │   RemoveFormationRelations() deletes DEPTH_FORMATION_RLTN after insert [ADO 1712613, SF 23-00890081]
│   └─ Formations grid still shows rows as "new" after save (display only) [ADO 1709002]
├─ Error on add depth "All Depths Apply": Filter Name 'FormationsFilter.FormKey': Invalid filter
│   → configs IncludeFormationofInterestFlag=1 + FilterFormationsByStCnty=1 but no
│     FORMATIONS_FILTER rows for that state/county [ADO 1723183]
├─ Formation missing from list (e.g. Marcellus under All Depths Apply)
│   → G2/G4: add rows to FORMATIONS_FILTER for the state/county [26-01102134, ADO 1723183]
├─ Depth interval exists on agreement level AND depth level — screen locked
│   → G4: cleanup script removes agreement-level interval [24-00969045]
└─ Areal rename blocked when it has depth subs → remove admin-type row in DB [24-00976415]

Chain of Title?
└─ Participation change "Save with Note" → note on Participation but NOT on CoT
    → G3: ADO 1691135, hotfixed 2022.04→2025.04 trains; verified by client in Oct 2025 HF [25-01015775]
```

---

## 3. C1 — Legal Description save/delete errors tied to `MapLegalDetail` (trigger `TR_LD_METES_BOUNDS_LGL_DTL`)

**Signature:** editing or deleting legal description rows throws an Oracle *no data found*-style error; edits do not save; users "stuck with the inaccurate legal segments". Also: Delete Agreement wizard fails at the legal-description step.

**Root cause (CONFIRMED, from resolutions):** the database trigger `TR_LD_METES_BOUNDS_LGL_DTL` selects into a variable from `LGL_DTL_KEY_RLTN`. That table is only populated when the **`MapLegalDetail`** configuration is ON. For clients with the config OFF (e.g. client CRC), a delete of a legal description performs a `SELECT INTO` on an empty `LGL_DTL_KEY_RLTN` → *no data found* → save/delete aborts. Fix: the trigger was updated to check the `MapLegalDetail` config before reading `LGL_DTL_KEY_RLTN`.
- SF **24-00941202** (Resolution verbatim: "Legal details trigger TR_LD_METES_BOUNDS_LGL_DTL is updated with MapLegalDetail check to handle error.")
- SF **24-00970216** — same client re-hit it after client installers alone; the full root-cause text above is from this case's Resolution. Confirms the fix is DB-side (trigger), not client-side.
- Mirror image with the config ON: **Delete agreement is not working if 'MapLegalDetail' config is ON** — ADO Bug **1655451** (Closed; tags `2023.04 Hotfix Completed`, `2024.04 Hotfix Completed`). Repro: Delete Agreement → retrieve → select agreement that has a legal description → Next → error.

**Fix recipe:**
1. Confirm the client's `MapLegalDetail` value (config table / metadata layer) and their DB build.
2. If build predates the trigger fix → G3 "fixed in version": deliver the updated `TR_LD_METES_BOUNDS_LGL_DTL` trigger (DB patch), not client installers (24-00970216 proved installers alone do not fix it).
3. If Delete Agreement fails with the config ON → cite ADO 1655451, hotfixed 2023.04/2024.04 trains.

**Related predecessor:** SF **24-00974601** / **23-00888482** — "error message when opening the legal description node" on Texas legals (same error family, earlier report; 24-00974601 explicitly says "exact same error message for Texas legal descriptions as case #23-00888482").

---

## 4. C2 — Phantom / orphaned legal description rows (bad data)

**Signature:** the agreement tree shows a legal description node (often at agreement level) but the screen opens empty; the record cannot be deleted, which blocks adding legals at the areal levels.

**Root cause (CONFIRMED):** orphan rows in `LIS.LEGAL_DESCRIPTION_SEGMENTS` and `LIS.LD_ACREAGES` left behind on the agreement.
- SF **24-00981552** (Resolution verbatim: "Orphan records in LIS.LEGAL_DESCRIPTION_SEGMENTS and LIS.LD_ACREAGES were causing the issue. Delete them from the agreements to solve this issue."). CaseFeed confirms an L4 script was written and deployed to UAT first for client approval.

**Fix recipe:**
1. Identify the agreement (file number → `arrg` key chain).
2. Verify orphan rows exist in `LIS.LEGAL_DESCRIPTION_SEGMENTS` / `LIS.LD_ACREAGES` for the agreement level that displays empty (see Diagnostic SQL — template, label results before claiming).
3. Data-correction script deleting the orphan rows, UAT first, client sign-off, then PRD. This is the established pattern (24-00981552).

**Adjacent view defect:** SF **23-00923612** — the delivered view `LIS.LGL_DTL_KEY_ACREAGE` was missing columns `LGL_DTL_SRC` and `LGL_DTL_DESC` that exist in production and are referenced by client schema `ESUITE_MRO_LAGN`; Quorum re-issued the view script. If a client reports missing columns on this view after an upgrade, it is a known packaging defect, not client error.

---

## 5. C3 — 10,000-acre entry limit on Legal Description (validation config)

**Signature:** "The legal description grid only allows <10,000 acres to be entered in total" / "10,000 acreage limit on a parcel record under Legal Description tab". Hits clients with large (international / New Mexico) parcels.

**Root cause (CONFIRMED):** delivered validation object **`QLSValidationLegalDescription0015_CheckSegAcres`** caps the Acres field at 9,999. It is controlled per metadata layer via **`QARCH_CTRL_OBJECT_USE`**.
- SF **25-01030271** (Resolution verbatim: "I inactivate this rule by updating the table QARCH_CTRL_OBJECT_USE WHERE OBJECT_DEF_NM = 'QLSValidationLegalDescription0015_CheckSegAcres' for the specific client layer QINV").
- SF **26-01103576** (Resolution: "The land configuration 'QLSValidationLegalDescription0015_CheckSegAcres' has been updated to allow values greater than 9999 in the Acres field."). CaseFeed links the config recipe to ADO **1747387** (Script Review, `INVL - QLS - Legal Description - Value is greater than 9999`, area `Engineering\Maintenance\Upstream\Customer Service\Land`).

**Fix recipe (G2 config, no code):**
1. Confirm the client wants the cap raised/removed (it is a data-quality guard).
2. Update/inactivate `QLSValidationLegalDescription0015_CheckSegAcres` in `QARCH_CTRL_OBJECT_USE` **at the client layer only** (pattern: layer `QINV` for client INV). Deliver as a reviewed script (ADO 1747387 is the precedent Script Review).
3. Cache/metadata refresh per standard config-change procedure.

---

## 6. C4 — Acreage calculation & rollup wrong (`ACRE_CALC` package)

**Signature family:** header/net acreage totals do not match subdivision inputs. Variants:

1. **Net acreage not recalculated after subdivision-level saves.** Edits to acreage counts at the Subdivision level saved, but the AGM-level net never recalculated because Save was never executed at the AGM level — ~500+ records at one client. Fix was a **script to run the acreage-calc package** across the affected agreements. (SF **25-01032413**, Resolution verbatim: "script to run acreagew calc package solved the issue".)
2. **Inactive areal net / company-net acres rolling into header totals.** Client CNX (QCloud): inactive areals' net acres included in header rollup, inconsistent with their prior v17 behavior. Resolution: **"reverted acreage calc package"** — i.e., a package-version regression, not data. (SF **25-01003323**; follow-on **26-01113965** "Inactive Net/Co Net acreage not converted" still In Review 2026.)
3. **Rounding.** Header acreage node rounded to 3 decimals; client needed 6. Resolution: "Changed rounding in ACRE_CALC package to fit 6 decimals instead of 3" (SF **25-01045304**). ACRE_CALC precision is client-adjustable.
4. **New agreement type not calculating acreage.** New type "Aggregate" didn't calc; fixed by data cleanup script (SF **24-00976925**) — check type/code-table wiring before code.
5. **Rollup/summary display defects (known, fixed):** newly added Areal/Depth subs not syncing to treeview, acreage + participation rollup to agreement level not working (ADO **1751387**, Closed); Agreement Summary grid shows wrong Agreement Type column and wrong per-depth Net Acres (ADO **1752049**, Closed — repro: areal gross acres + two depth participations with different interests → summary should show different net acres per depth).
6. **Acreage-change remark not copied to Notes:** changing areal gross acres pops the "Acreage change reason" dialog, but the remark did not populate the acreage-screen Notes — fixed, hotfix tags 2022.04/2023.04 (ADO **1651972**).

**Fix recipe:**
- Wrong totals with correct inputs → determine ACRE_CALC package version vs release; if a recent package deploy preceded the complaint, compare with prior version (25-01003323 precedent: revert).
- Stale totals after mass/subdivision edits → run the acreage-calc package by script over affected `arrg` keys (25-01032413 precedent). Do NOT hand-edit totals.
- Rounding/precision complaints → ACRE_CALC rounding parameter change (25-01045304 precedent).

---

## 7. C5 — Depth screen: formations not saving / formation list problems

**Signature A — "Formations disappear after save" / "must add formations twice":**
- ADO Bug **1712613** — `QLS - Depth Screen - Measured Depth Only functionality is not saving formations on screen`. Root cause (verbatim from ADO analysis): *"Line 327 in QQLSServiceCore_DepthIntervals.cs incorrectly deletes all formations for 'Measured Depth Only' depth type after they have been successfully saved"* — `Depth_BusinessRules.RemoveFormationRelations()` in `UpdateMultipleDepthIntervals()` (repo `Quorum.QLS.ServiceCore`) deletes the just-inserted `DEPTH_FORMATION_RLTN` rows. Hotfix tags: 2023.04 / 2024.04 / 2024.10 / 2025.04 Hotfix Completed. Tag `Preexisting Bug`, `Maintenance: Escalated`.
- Predecessor ADO **1709002** — Depth grid shows formations still "new"/dirty after save (display refresh); closed in favor of 1712613.
- SF **23-00890081** — "Formations must be added twice for several users" (Software Defect, Closed-No Response) — matches this defect family; if a client reports add-twice behavior, check build against the 1712613 hotfix trains before anything else (G3).

**Signature B — error adding depth with "All Depths Apply":** `Error: Filter Name 'FormationsFilter.FormKey': Invalid filter for an IN type query`.
- ADO Bug **1723183** (hotfix tags 2022.04 / 2024.04 / 2024.10): occurs when configs `IncludeFormationofInterestFlag=1` **and** `FilterFormationsByStCnty=1` are set but the agreement's state/county combination has **no rows in `FORMATIONS_FILTER`** — the auto-populate errors out unhandled. Verification SQL from the work item is in the Diagnostic SQL section (California/Fresno has rows and works; Gulf of Mexico/CGM had none and errored).

**Signature C — formation missing from the list:** e.g. "When 'All Depths Apply' is selected, Marcellus does not populate in the formations list" (SF **26-01102134**, Application Configuration). The pick list is fed by registered SQL **`SELECT_DEPTH_FORMATIONS_DEPTH_WEB`** (picklist ID 47071) joining `FORMATIONS_FILTER` to `FORMATIONS`, ordered by `STRAT_SEQ` (ADO **174346** history contains the full query — see Diagnostic SQL). Fix = add/extend `FORMATIONS_FILTER` rows for the state/county (reference-data change), not code.

**Related configs (all confirmed in ADO 1712613/1723183/174346/1787602):**
- `FilterFormationsByStCnty` (+ `FilterFormationsByStCntyCriteria` — header vs legal-description state/county source)
- `IncludeFormationofInterestFlag`
- `DisableMeasuredDepth` (=1 disables the "Measured Depth Only" radio)
- `DisableFormationOnly` (=0 has an OPEN defect: Depth From/To incorrectly editable for Formation Only rows — ADO **1787602**, state Proposed as of 2026-05)

**Fix recipe:**
1. Ask the depth **Type** in play (All Depths Apply / Measured Depth Only / Formation Only / Measured Depth and Formation) — each has its own failure mode.
2. Measured Depth Only + disappearing formations → G3: hotfixed on all trains (ADO 1712613).
3. FormKey filter error or missing formations → check `FORMATIONS_FILTER` coverage for the agreement's state/county (G4/G2), then the four configs above.
4. `DEPTH_FORMATION_RLTN` is the persistence table to verify whether formations actually saved.

---

## 8. C6 — Depth/Areal structure locked (bad data & admin rows)

1. **Depth intervals at both agreement level and depth level → screen locked.** Lease had intervals on level 000 *and* depth level 002; system then refused delete/modify/add on either. Root cause: system should have prevented the agreement-level interval. Fix: L4 **cleanup script** removing the agreement-level interval to unlock the depth level (SF **24-00969045**, Resolution: "Develop a script to clean up this agreement and remove the agreement level interval so the depth level is unlocked").
2. **Areal rename blocked when it is parent to depth subs.** User cannot change an areal's name without first deleting/moving its depth children. Resolved by a delivered SQL: `24-00976415_Areal Name Error - Remove Admin Type in DB.sql` (SF **24-00976415**, client CNX 2024 Stability Project) — an admin-type row in the DB enforced the lock.
3. **Areal count requirement.** "QLS is requiring more than one Areal for Lease and for Minerals type" — configuration of subject-type requirements, not defect (SF **24-00968286**, Application Configuration).
4. **Tree label truncation.** Header/Areal/Depth names cut off in the tree when long — Software Defect, "Available in the March 2026 - 2025.04 HF release" (SF **25-01061588**). G3.
5. **Treeview collapses to parent on subdivision screen navigation.** Root cause `Quorum.QLS.Web.Core\Controllers\AgreementsCommonBaseController.cs` (lines 765-773), `SetTreeNodes()` built the tree with the parent ArrgKey instead of the subdivision ArrgKey; one-line fix, commit `82d49b0`, PR 120460 (ADO **1767018**, Closed).

---

## 9. C7 — Chain of Title: participation-change note not written

**Signature:** Participation Change with **"Save with Note"** adds the note to both Participation records but NOT to the Chain of Title record.

**Root cause & fix (CONFIRMED):** ADO Bug **1691135** — `APA - QLS - Participant change notes are not reflecting on Chain of Title page` (area `Engineering\Land\Committed Backlog`, tag `Preexisting Bug`). Hotfixed on **every** train: tags 2022.04 / 2023.04 / 2024.04 / 2024.10 / 2025.04 Hotfix Completed.
- SF **25-01015775**: initially mis-titled "March 2025 Hotfix" regression — L4 explicitly determined it was NOT caused by the March 2025 hotfix (the DEV env without the hotfix also lacked the note); it is the preexisting defect above. `Resolution__c` = "August 2025 2023.04 HF"; client confirmed "This looks good in the October 2025 hotfix!".

**Fix recipe:** pure G3. Match the client's train to the 1691135 hotfix tags; deliver the appropriate hotfix. Interim workaround: manually add the note to the CoT record.

**Note on 2023-era CoT config cases:** SF **23-00894623 / 23-00894624** ("Chain of Title", Application Configuration) — screen/config setup requests, not defects.

---

## 10. C8 — Mass legal upload & import side effects

1. **Notes duplicated/dropped by mass legal upload templates.** "When using the mass legal upload templates, the Notes in the right-most column do not come through" (tested Jeff and Non-Jeff). Software Defect; `Resolution__c` = "2023.04 Oct '25 HF" (SF **25-01020784**). G3.
2. **Stale tree counts after external LD imports.** ADO Bug **1760443** — `Stale AgmtFolderDataCountInfo cache after external data imports (e.g. LD NON JEFF EXCEL TO LIVE)`: run the **LD NON JEFF EXCEL TO LIVE** import, reopen the agreement tree → folder counts unchanged even though the legal screen shows the new records. Closed. If a client says "the tree doesn't show my imported legals", have them check the legal screen first — data is there, the count cache is stale.
3. **Legal-description note defects (fixed):** notes not shown in Exhibit A until refresh (ADO **1638963**); note change not disabled on rolled-up legal rows at agreement level (ADO **1675425**); cannot add notes to legal description in customer upgrade testing (ADO **1690816**); Kendo-upgrade note-add error (ADO **1710444**, platform-tagged).

---

## 11. C9 — Jeffersonian landgrid, lots, tax parcels & reference data

1. **Lot acreages not auto-populating.** "When entering Lots on the Legal Description screen, acreages associated are not auto-populating." Fix (verbatim): "**ShowJeffLotDropDown** config needs to be set to 1 at the MST layer" (SF **24-00969566**). G2.
2. **Adding townships/sections to the Jeffersonian landgrid.** Client requests to extend the grid are inserts into **`GPOL_JEFF_SECTIONS`** (SF **26-01116137**, Resolution: "Insert the requested data into the GPOL_JEFF_SECTIONS table"; SF **25-01009608** "GPOL update for Jeffersonian" — loaded additional Jeffersonian township/sections for client FANG; the delivered non-Jeff script/process does not cover Jeff — Jeff updates are GPOL-table loads).
3. **Tax Parcel / Jeffersonian tab missing or erroring.** "Entered Country and State setup is invalid" on a UK agreement — country/state landgrid setup incomplete even though `apol_area_states` had the county; resolved via a documented setup script (SF **24-00990093**). Same family: state/county values not showing on the Tax Parcel tab (SF **24-00992271**); legal-description dropdown updates for a new state/county (SF **25-00999152**, **24-00966325** Map Status field missing on Jeff screen).
4. **Map Status flips en masse.** Adding one subdivision put ALL legal lines across all subdivisions into "Requested - Manual Map" status; only added/modified lines should transition (SF **22-00647281**, Software Defect). Related: Map Status set on non-GIS tax parcels (SF **24-00947009**).
5. **Entire Section / ALL flag.** "Entire Section flag on Legal Description Header records are not propagating down to the 'ALL_FLAG' in child table" (SF **22-00558633**, Software Defect). The follow-up fix missed QLA-sourced agreements — legal summary only generated on first QLS-side save, and audit history then wrote a spurious "deleted" entry; fixed by updating **`QLA_INFC_QLS_CRI`** (SF **22-00818478**). If a legal-description defect fix "doesn't work" for some agreements, ask whether those agreements originated in QLA.
6. **Other Legal conversions (design/config work, not defects):** moving Metes & Bounds or legacy PXD subdivision data into Other Legal and hiding the M&B tab is an established client conversion pattern (SF **25-01027378**, **25-01027379**, **25-01026989**).

---

## 12. C10 — Performance & rendering on Legal/Acreage screens

1. **Legal Description save hangs (spinner forever), data actually saved.** Root cause per L4 CaseFeed: "the Legal Description updates are getting locked up by a piece of the update package that is not optimized in your version. We have optimized this package in a later release" — delivered in next patch (SF **22-00804010**, Software Defect). Diagnostic used at the time: `select count(*) from sde.states` (large count = GIS-side drag).
2. **Legal Description saves take ~80 seconds each** during mass edits (P66/Landworks migration): short-term nightly service restart to clear cache latency; long-term patch (SF **24-00966377**). If save latency grows over a mass-edit campaign, suspect cache growth, not user network.
3. **Legal Description grids not rendering on new agreements** (client SRC) — Closed defect, tags `2022.04 Hotfix`, `2023.04 Hotfix Completed`, `Config` (ADO **1656718**). Check config + hotfix level.
4. **Non-Jeffersonian screen layout issue** — Closed, hotfixed 2023.04/2024.04 (ADO **1681543**).
5. Load-test context: Legal Description and Acreage screens are on the standard QLS performance script; 2025.04 showed degradation ≥10 concurrent users, closed after Round 2 tuning (ADO **1724175**) — cite when a client on 2025.04 reports broad slowness on these screens.

---

## 13. Known ADO items (quick reference)

| ADO ID | Type | Title (abbrev.) | State | Fixed-in evidence |
|---|---|---|---|---|
| 1655451 | Bug | Delete agreement fails when `MapLegalDetail` ON | Closed | tags 2023.04/2024.04 Hotfix Completed (CONFIRMED tags) |
| 1691135 | Bug | Participation-change notes not on Chain of Title | Closed | tags 2022.04→2025.04 Hotfix Completed (CONFIRMED tags) |
| 1712613 | Bug | Measured Depth Only not saving formations | Closed | tags 2023.04→2025.04 Hotfix Completed; root cause `QQLSServiceCore_DepthIntervals.cs:327` |
| 1709002 | Bug | Depth screen shows formations as new after save | Closed | superseded by 1712613 |
| 1723183 | Bug | Error adding depth — FormationsFilter.FormKey invalid IN filter | Closed | tags 2022.04/2024.04/2024.10 Hotfix |
| 1787602 | Bug | Depth From/To editable when `DisableFormationOnly=0` | **Proposed** (open) | none yet — do not promise a fix |
| 1747387 | Script Review | Legal Description acres > 9999 (config script) | Closed | config recipe, client INV |
| 1760443 | Bug | Stale AgmtFolderDataCountInfo cache after LD NON JEFF EXCEL TO LIVE | Closed | — |
| 1656718 | Bug | Legal Description grids not rendering (SRC) | Closed | tags 2022.04/2023.04 Hotfix; `Config` |
| 1681543 | Bug | Non-Jeff screen layout issue | Closed | tags 2023.04/2024.04 Hotfix |
| 1638963 | Bug | LD Notes not in Exhibit A until refresh | Closed | tags 2023.04→2024.04 Hotfix |
| 1675425 | Bug | Note change not disabled on rolled-up LD rows | Closed | tags 2023.04/2024.04 Hotfix |
| 1690816 | Bug | Cannot add notes to legal description (EQC upgrade) | Closed | BLD* |
| 1710444 | Bug | Kendo upgrade — error adding LD note | Closed | Product-2024.10 platform tags |
| 1651972 | Bug | Acreage-change remark not populating Notes | Closed | tags 2022.04/2023.04 Hotfix |
| 1751387 | Bug | New Areal/Depth subs not syncing treeview; acreage/participation rollup | Closed | — |
| 1752049 | Bug | Agreement Summary grid/acreage mismatch | Closed | — |
| 1767018 | Bug | Subdivision treeview collapses on navigation | Closed | commit 82d49b0, PR 120460, `AgreementsCommonBaseController.cs:765-773` |
| 174346 | Bug | QLA cannot select Formation Only (contains `SELECT_DEPTH_FORMATIONS_DEPTH_WEB` SQL) | Closed | Fall.2022 |

Fixed-in labels above are **INFERRED from hotfix tags** unless a release note confirms; re-verify against the client's exact build before telling a customer "already fixed".

---

## 14. Diagnostic SQL (Oracle, `lis` schema — real queries from cases/work items)

**Formations coverage for a state/county (ADO 1723183, verbatim from the work item, keys are examples from that bug):**
```sql
select * from formations_filter u
 where u.gpol_dtl_st_key = 326004      -- State = California
   and u.gpol_dtl_cnty_key = 326004019; -- County = Fresno  → rows exist, screen works
select * from formations_filter u
 where u.gpol_dtl_st_key = 326087      -- State = Gulf Of Mexico
   and u.gpol_dtl_cnty_key = 342015105; -- County = CGM     → no rows, add-depth errored
```

**Formation picklist source — registered SQL `SELECT_DEPTH_FORMATIONS_DEPTH_WEB`, picklist ID 47071 (ADO 174346, verbatim):**
```sql
SELECT FORM_CODE, FORM_KEY, STRAT_SEQ, FORM_DESC,
       GPOL_DTL_ST_KEY, GPOL_DTL_CNTY_KEY, FORMATION_OF_INTEREST
FROM (SELECT DISTINCT FF.FORM_CODE, FF.FORM_KEY, FF.STRAT_SEQ, F.FORM_DESC,
             FF.GPOL_DTL_ST_KEY, FF.GPOL_DTL_CNTY_KEY, FF.FORMATION_OF_INTEREST,
             ROW_NUMBER() OVER(PARTITION BY F.FORM_CODE
                               ORDER BY FF.STRAT_SEQ, F.FORM_DESC) AS RN
        FROM FORMATIONS_FILTER FF
        JOIN FORMATIONS F ON FF.FORM_CODE = F.FORM_CODE) TMP
WHERE 1 = 1
@@WHERE_CLAUSE
ORDER BY FORM_CODE;
-- WHERE RN = 1 moved to parameter value so additional picklist criteria can be included
```

**Acre-limit validation rule locator (from SF 25-01030271 resolution):**
```sql
SELECT * FROM QARCH_CTRL_OBJECT_USE
 WHERE OBJECT_DEF_NM = 'QLSValidationLegalDescription0015_CheckSegAcres';
-- inactivate/override at the CLIENT layer only (precedent layer: QINV)
```

**GIS-side latency smell during LD save hangs (SF 22-00804010 CaseFeed, verbatim):**
```sql
select count(*) from sde.states;  -- "If the number is large it indicates poor performance"
```

**Orphan legal-description check (VERIFICATION TEMPLATE — derived from SF 24-00981552; label results NOT YET RUN until executed):**
```sql
-- Rows on LIS.LEGAL_DESCRIPTION_SEGMENTS / LIS.LD_ACREAGES for the agreement level
-- that renders empty in the tree; join keys per live schema via metadata server.
SELECT * FROM lis.legal_description_segments WHERE <agreement-level key> = :arrg_key;
SELECT * FROM lis.ld_acreages              WHERE <agreement-level key> = :arrg_key;
```

Confirmed table/object names for search-anchoring (do not invent columns): `LGL_DTL_KEY_RLTN`, `LIS.LGL_DTL_KEY_ACREAGE` (view; cols incl. `LGL_DTL_SRC`, `LGL_DTL_DESC`), `LIS.LEGAL_DESCRIPTION_SEGMENTS`, `LIS.LD_ACREAGES`, `FORMATIONS`, `FORMATIONS_FILTER` (`GPOL_DTL_ST_KEY`, `GPOL_DTL_CNTY_KEY`, `STRAT_SEQ`, `FORM_CODE`, `FORM_KEY`, `FORMATION_OF_INTEREST`), `DEPTH_FORMATION_RLTN`, `GPOL_JEFF_SECTIONS`, `APOL_AREA_STATES`, `QARCH_CTRL_OBJECT_USE`; trigger `TR_LD_METES_BOUNDS_LGL_DTL`; package `ACRE_CALC`; interface criteria object `QLA_INFC_QLS_CRI`; registered SQL `SELECT_DEPTH_FORMATIONS_DEPTH_WEB`.

---

## 15. Expected-Behavior FAQ

- **"Why does the Acres field reject values over 9,999?"** Working as delivered — validation rule `QLSValidationLegalDescription0015_CheckSegAcres` guards data quality. It can be relaxed per client layer on request (25-01030271, 26-01103576).
- **"Header acreage doesn't match my subdivision edits."** Header nets recalc when Save is executed at the agreement level; subdivision-only saves can leave the header stale — a recalculation script exists for bulk cases (25-01032413). Not data loss: the subdivision values are stored correctly.
- **"Should inactive areal acres roll into header totals?"** Client-expectation-sensitive; v17 behavior excluded inactive net acres and a package change that included them was treated as a regression and reverted (25-01003323). Confirm the client's baseline before calling it a defect.
- **"The tree count didn't change after my Excel-to-Live legal import."** Records are saved; the folder-count cache was stale (ADO 1760443). Check the Legal Description screen for the data before re-importing.
- **"Formation fields are read-only for Measured Depth Only."** By design at the UI layer (DepthController per ADO 1712613 analysis); formations are auto-populated from `FORMATIONS_FILTER` based on footage and Strat Seq.
- **"Why can't I rename an areal that has depth subdivisions?"** Historically an admin-type DB row enforces the lock; removal via reviewed SQL is the precedent (24-00976415) — treat as config/data request, not defect.
- **"More than one Areal is required for Lease/Minerals types."** Subject-type requirement configuration, adjustable (24-00968286, 26-01096055 removed Legal Description and Depth requirements for ROW subject approval).
- **"Metes & Bounds vs Other Legal?"** Migrating M&B data into Other Legal and hiding the M&B tab is a supported conversion pattern several clients have executed (25-01027378/79).

---

## 16. Escalation

- **G3 first for:** formations-vanish-on-save (1712613), CoT note missing (1691135), delete-agreement-with-LD (1655451), mass-upload notes (25-01020784 → 2023.04 Oct '25 HF), tree-name truncation (25-01061588 → March 2026 2025.04 HF). Match the client train to hotfix tags; these are all already fixed.
- **G4 script precedents (get client sign-off, UAT first):** orphan LD segment/acreage rows (24-00981552), agreement-level depth interval removal (24-00969045), acreage-calc package re-run (25-01032413), areal admin-type row removal (24-00976415), GPOL_JEFF_SECTIONS inserts (26-01116137).
- **G5 / engineering handoff:** new failures in `TR_LD_METES_BOUNDS_LGL_DTL` beyond the MapLegalDetail check; ACRE_CALC rollup logic disputes (bring 25-01003323 revert history); `QQLSServiceCore_DepthIntervals.cs` regressions; open defect 1787602 (`DisableFormationOnly=0` editability) — reference, do not promise dates.
- **Route away:** Aliquot/quarter-call ArcPro tool crashes (23-00894043, 23-00897566, 25-01058317) and Polygen acreage-calc on `ALL_LGL_SEG_PLY` (24-00987484) belong to the **QGIS / Mapping & Polygen** group (coverage-plan group #7), even though subjects say "aliquot"/"acreage". QQM acreage-field universe errors (26-01093906) → Reports/QQM group.
- If the client is QLA-sourced (agreements created in QLA), test the QLA interface path (`QLA_INFC_QLS_CRI`) before declaring a QLS-side fix complete (22-00818478).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
