# SKILL: QDO JIB / Cost Center / AFE Crossover + Imports & Bulk Data Loads

**Version:** 1.0 | **Created:** 2026-09-03 | **Product:** My Quorum Division Order (QDO) — `Product_list__c = 'My Quorum Division Order'`
**Scope:** Two coverage-plan GAP groups in one skill.
**Section I — JIB / Cost Center / AFE crossover (G12, ~18 actionable):** JIB DOI decks (Base Flag, tiers, backdating, templates, offset flag), JIB interest transfers and their warning codes (RADOITRW58/59), Cost Center creation/numbering/security, AFE sync. The *ADO defect-reference* side of DOI-validation on AP/GL/AFE (AP055, GL025, JB020, AFEEXTIMP) lives in `SKILL_ADO_QDO_DivisionOrder_Transfers.md` — this skill covers the SF case families.
**Section II — Imports & bulk data loads (G13, ~16 actionable):** Import From Excel (DOI Setup / DO Maintenance / DOI Worksheet), Owner Lease Xref import, Bulk View/Edit, Datayank and third-party loads (Mineral Answers).
**Companion skills:** `SKILL_QDO_Division_Orders.md` (DOI setup/worksheet core), `SKILL_QDO_Transfers_SuspendRelease.md` (transfer pipeline), `SKILL_QDO_Upgrade_Patch_Regressions.md` (upgrade-wave regressions), `SKILL_QDO_Platform_Integration.md` (Owner Lease Xref via Design Studio, SAP JIB netting).

> **Evidence base:** all 17 closed actionable JIB/CC/AFE cases + all 16 closed actionable import/bulk cases (single LIMIT-25 pages each — complete populations, `Root_Cause__c IN ('Software Defect','Application Configuration','ChangeConfig')`), with Description/Resolution + case-feed deep-dives on 12 of the richest, and ADO verification of 7 work items. Every claim cites a verbatim SF case number and/or ADO ID. Fixed-in builds **INFERRED** unless a tag/release note confirms.
> **PII:** individual names redacted; 3-letter client prefixes retained (org identifiers).

---

## 1. Quick Triage Table

| Symptom | Likely cause | Go to |
|---|---|---|
| Can't save/set up a 2nd JIB tier: "must have JIB Base Flag checked" | Base-flag validation defect family (should require exactly ONE base tier per property, not one per deck) | §4 A |
| JIB tier number typed as 100 saves as Tier 1 | Configs `CAN_CHANGE_TIER_VALUE` / `CAN_CHANGE_TIER_JIB_VALUE` disabled | §4 B |
| JIB deck won't appear in the backdate screen (BD006) — only REV decks listed | Registered SQL `SELECT_DONL_DO_PROP_BACKDATE_PICK` filters JIB out; add JIB to the pick query | §4 B |
| JIB transfer preview/approve throws warnings `RADOITRW58` ("No default market rep found… may cause fatal error") / `RADOITRW59` (combine warning with 'WI' in every parameter) | Invalid warnings on JIB DOIs — market-rep validation belongs to REV only (code table 29100); messages corrected in later builds | §4 C |
| JIB deck template imports interest type MI but system shows DI | Template/config mapping (Application Configuration) | §4 D |
| Saving an owner flagged JIB Offset forces Pay Reason 5-Pay Regardless (ignores $100 minimum) | Working-as-configured product rule; recurring complaint | §8 FAQ |
| New cost center errors "number already in use" | Auto-number bug: creating multiple CCs at once bumps code-table "Last No" by 1 only (code table **29111** / `QARCH_TRAN_SEQ`); ADO **1837136** | §4 E |
| Cost center saves but property screen never opens → can't create property/DOI | User lacks execute on **ORGCOSTGEN** process — security scripts | §4 E |
| Cost center setup shows security error but still creates the CC | Missing `ORG/BTYP/QRA` security object on the user's groups | §4 E |
| Import From Excel loads some NRIs as **0.00000000** | Excel emits tiny decimals as scientific notation ("1E-08"); parser drops them (ADO **1322617**, **1813832**) | §5 G |
| Import From Excel: small decimals invisible in grid, total allocation < 1.0, validation blocks import | Same scientific-notation family, DO Maintenance path (26-01103568) | §5 G |
| DOI Worksheet import skips ~50 owners' NRI | Precision-mask defect — `NRIDecMasked` fix in worksheet import/export | §5 G |
| Owner Lease Xref import "Replace Content" reverts on Save | Xref replace defect — fixed in patch (22-00672538) | §6 H |
| Bulk View/Edit on Bearer Group adds/deletes rows instead of updating; FK error; pasted decimals rounded | Two logged defects (FK error → 2025.10 GA; rounding → 2024.04 hotfix) | §6 I |
| "Load BA data from Mineral Answers" | No standard product loader — route to Services (Datayank/scripts) | §7 J |

---

## 2. Concepts

- **JIB DOI decks:** a property can carry REV and **JIB** DOI decks (`DO_TYPE_CD='JIB'`), multi-tier (base + overhead tiers). Rule: **exactly one tier per property carries the JIB Base Flag** — enforcement of this rule was buggy in both directions (forced on every deck, then not enforced at all). JIB decks route suspense with reason `JB`; JIB DOIs are validated by Financials screens (AP055 vouchers, GL025 batches, JB020 — "not an effective JIB DOI", see S4 skill).
- **Cost Centers** are created from the eSuite/web Cost Center Maintenance screen; on save the system auto-assigns the next number from a code table (**29111**, ADO title says `QARCH_TRAN_SEQ`) and is supposed to chain into Property creation (**ORGCOSTGEN** process) → then DOI setup.
- **Imports:** grid-level "Import From Excel" exists on DOI Setup detail grids, DO Maintenance, DOI Worksheet, External Funds Transfer, Owner Lease Xref (Design Studio). The recurring killer is **Excel representing small decimals as scientific-notation strings**, which different import paths mishandle (silent 0s or blocked validation).

---

## 3. Decision Tree

```
JIB question?
├─ Setup/save of the deck (base flag, tier #, backdate) → §4 A/B (mostly config + known defects)
├─ Warnings during a JIB transfer → §4 C (invalid-warning family; usually ignorable, verify)
├─ Values wrong coming FROM a template/import → §4 D or §5 G
└─ Netting / SAP / AP-GL-AFE validation → S3 / S4 skills

Cost Center question?
├─ Numbering error on create → §4 E (code table 29111 Last No; ADO 1837136)
├─ Nothing happens after create (no property screen) → §4 E (ORGCOSTGEN security)
└─ Security error but record created anyway → §4 E (ORG/BTYP/QRA object)

Import/bulk question?
├─ Decimals become 0 / disappear / block validation → §5 G (scientific notation)
├─ Imported values don't SAVE (revert) → §6 H (Xref replace) / §6 I (bulk edit)
└─ "Load external data set" (Mineral Answers, PRD→UAT copy) → §7 J (Services/Datayank)
```

---

# SECTION I — JIB / COST CENTER / AFE CROSSOVER

## 4. Symptom clusters

### A — JIB Base Flag validation (multi-tier setup blocked or unguarded)

**Signature:** Web DOI Setup refuses a new JIB tier header with an error demanding JIB Base Flag, even though an approved base tier already exists — or (post-fix regressions) approves JIB decks with **no** base tier at all.

- **23-00916387** "UAT2 - Error when trying to set up multiple JIB tiers" (Software Defect). `Resolution__c` (verbatim): "Updated the filter for **tierJibFlagList** to check whether any DOI with JIB flag checked is present in the database while adding DOI."
- ADO Bug **1618171** "CNR, MEW - Cannot save JIB DOI without JIB Base Flag checked" (Closed, tags `SEPT 2022.04; OCT 2022.04`): "The JIB Base flag is required for one tier per property, but current validation is forcing checking this box on every JIB DOI upon saving the header." Workaround users found (checking the flag everywhere) is dangerous: "there should only be one JIB base defined per property… multiple… will cause functional issues in JIB processing."
- ADO Bug **1639565** "CNR - JIB Base Flag Fix Still Does Not Work" (Closed): original fix #1618171 incomplete — DOI Copy to a new tier gave an erroneous error yet approved on refresh; and a brand-new JIB DOI with **no** base flag and no other JIB deck approved without validation.
- **24-00940784** "Upgrade Project: QDO - JIB Base Flag required on file copy DO" (Application Configuration) — same family on the copy path.

**Recipe:** confirm exactly one `JIB_BASE_FL`-checked tier exists per property in `DONL_DO_HDR`-level data (verify column names via metadata server); if validation blocks a legitimate overhead tier, check build vintage against #1618171/#1639565 (2022.04-era fixes, INFERRED); if multiple base flags exist, treat as bad data — fix before JIB processing.

### B — JIB tier numbering & backdating

- **25-01043348** "JIB Tier number not saving correctly - it is auto changing to Tier 1" (Application Configuration). `Resolution__c` (verbatim): "Enabled the following configs `CAN_CHANGE_TIER_VALUE` `CAN_CHANGE_TIER_JIB_VALUE`" — with these off, the system auto-generates the next tier number and overrides manual entry.
- **26-01118522** "Unable to backdate a JIB Deck" (Application Configuration): BD006 backdate pick only returned REV decks. `Resolution__c` (verbatim): "We provided the client a configuration in the Reg SQL ID: **SELECT_DONL_DO_PROP_BACKDATE_PICK**, where JIB was added in order to allow the client to run the DO backdate process for JIB decks."
- **25-01021825** "Backdate a JIB Tier" (Application Configuration) — same question, earlier ("I can do it for REV but I don't know how for JIB"); precedes the reg-SQL recipe above.

**Recipe:** for tier numbering, flip the two configs; for backdating, edit registered SQL `SELECT_DONL_DO_PROP_BACKDATE_PICK` to include JIB DO types (metadata server → registered SQL), then rerun the backdate from BD006.

### C — JIB transfer warning codes RADOITRW58 / RADOITRW59

**Signature:** Previewing/approving a JIB maintenance-group transfer (typically many-to-one with Combine Flag) logs:
- `RADOITRW58`: "No default market rep found… This may cause fatal error" — some builds even label it "FATAL ERROR".
- `RADOITRW59`: combine warning whose parameters all print "WI" instead of actual values — while the interest **did** combine correctly into a single 1.00-NRI line.

**Root cause (CONFIRMED via ADO):** market-rep validation is only meaningful for REV DOIs (default market rep lives in **code table 29100** per business unit); the check misfired on JIB DOIs, and RADOITRW59's parameter substitution was wrong.
- **25-01027179** "Invalid Error Messages During JIB Transfer" (Software Defect) ↔ ADO Bug **1739512** "MEW - Invalid Warning Messages About Combining Interest (25-01027179)" (Closed). Case feed timeline: warning wording/validity fixed in the client's November hotfix + later patch (INFERRED); the remaining "No default market rep found" REV-only rework shipped with the client's **2025.04 upgrade**, not backported to 2024.04.
- **26-01064806** "JIB TRANSFER - WARNING MESSAGE 'FATAL ERROR'" (Software Defect, GLE). `Resolution__c` (verbatim): "Long term fix is in WI **1622910** - this warning has been updated in later versions… to no longer say 'Fatal Error' and also was changed to only hit on REV DOIs. Since they don't have this change and this is for JIB, GLE can ignore this warning."
- ADO Bug **1622910** "23-00918228--No default market rep found warning message on converted dummy DOIs for Revenue Suspense" (Closed, tag `Robot RN 2026.04`): validation changed to "ONLY validate for DOIs of type REV (DO Group Type R)"; a TRANS_SEQ_NO can only contain JIB or REV, never mixed.

**Recipe:** if the DOI in the warning is JIB → warning is noise; confirm the transfer result (combine line, sequencing) and tell the client to ignore / consume the fix build. If REV → check code table 29100 has a default market rep for the business unit; a missing rep there is a **valid** config gap.

### D — JIB deck values wrong from template / owner flags

- **25-01027690** "JIB Deck Incorrect Interest Type" (Application Configuration): template set interest type **MI** but deck came in as **DI** (example property on case). Closed as config — check template↔interest-type mapping before suspecting code.
- **26-01094960** "JIB OFF SET FLAG" (Application Configuration): saving an owner marked JIB Offset forces Pay Reason **5-Pay Regardless**, which bypasses the $100 minimum-suspense pay amount; client wanted 5-Pay Regardless to respect the minimum (repeat of their earlier 23-00878496). No product change on case — treat as product rule + enhancement candidate (§8 FAQ).
- **23-00920921** "MG Error - Remove JIB Netting from BA" (Software Defect) and **22-00676527** "JIB Netting Interface with SAP" (Software Defect, Integration) — JIB-netting flag/interface family; SAP netting detail in `SKILL_QDO_Platform_Integration.md`.

### E — Cost Center creation, numbering & security

**E1 — Auto-number collision (CONFIRMED defect + workaround).**
**26-01111459** "COST CENTER ISSUES-HIGH IMPORTANCE" (Software Defect, Closed-Deferred). Support analysis (case feed, verbatim core): "when a cost center is created, the system looks at the last used cost center number and automatically assigns the next available number. In PRD, the last used number is currently reflected as 500997; however, a cost center already exists with 500998… This is a bug where if multiple cost centers are created at once then it will increase the last number by 1 instead of how many cost centers you made."
**Workaround (from case feed):** Maintenance → **Code Table Value Editor** → code table ID **29111** → update column **Last No** to the true last-used number → Update.
**ADO:** Bug **1837136** "REP 2024.10 - Cost Center Last No does not correctly update in code table QARCH_TRAN_SEQ" (project Quorum, Closed, release-noted — fixed-in INFERRED from `SDP CRN` tag).

**E2 — Property screen doesn't open after CC creation (CONFIRMED security).**
**25-01042097** "UNABLE TO CREATE PROPERTY AFTER COST CENTER CREATED" (Application Configuration). `Resolution__c` (verbatim): "Ran security update scripts to give users access to the **ORGCOSTGEN** process."

**E3 — Security error on CC setup though record saves (CONFIRMED security).**
**25-01048054** (UAT cost center: security error, but "property was successfully created"; worked in PRD). `Resolution__c` (verbatim): "Added **ORG/BTYP/QRA** security object to groups 70000 and 90671012" (group numbers client-specific).

**E4 — Navigation defect:** **23-00902872** "View Details of Associated Cost Centers Returns you to the Dashboard" (Software Defect, Query Screens) — older web-screen defect, no recipe on case.

### F — AFE crossover

- **22-00645822** "Multiple AFE Sync Jobs Launched" (Software Defect): duplicate AFE sync job launches — batch-dedup family; if recurring, check process-queue for duplicate submissions before rerunning.
- DOI-validation failures raised by AFE/JIB Financials screens (JB020 "not an effective JIB DOI", AFEEXTIMP, AP055/GL025 voucher/GL validation, converted-AFE DOI decimals) are documented with ADO anchors in **`SKILL_ADO_QDO_DivisionOrder_Transfers.md`** — route there; the QDO-side check is always: does an *effective, approved* JIB DOI exist for the property/date the Financials transaction references?

---

# SECTION II — IMPORTS & BULK DATA LOADS

## 5. Cluster G — Import From Excel drops or zeroes small decimals

**Signature (three surfaces, one root cause):** owner NRI/allocation decimals that Excel stores in scientific notation (≤ ~1E-05) either import as `0.00000000`, or don't display in the import grid and make total allocation fail validation.

| Case | Surface | Fix |
|---|---|---|
| **22-00676543** "MRO - NRIs Loading as 0 With Import From Excel" (new DOI setup; random rows 0.00000000; see legacy 20-00080816) | DOI Setup detail grid | `Resolution__c`: "Included in upcoming release" ↔ ADO Bug **1322617** "APA - 2020.09 Build Upgrade - myQDO DOI Setup Screen Importing from Excel Sets Some Owner NRIs to 0" (Closed, tag **2021.04 hotfix 1** — CONFIRMED tag). WI history: "Excel stores small enough values as strings in scientific notation (i.e. 0.1e-5). this should be taken into account when parsing." |
| **26-01103568** "Import From Excel Not Recognizing Small Decimals For DO Maintenance" (Software Defect) | DO Maintenance import | ADO Bugs **1813831**/**1813832** (project Quorum, Closed). Root cause from WI history (verbatim): "Calling `.ToString()` on a `double` like `0.00000001` produces `\"1E-08\"`… import paths with raw decimal properties… go through `Convert.ChangeType(\"1E-08\", typeof(decimal))` which uses `NumberStyles.Number` — no `AllowExponent` — so it throws a `FormatException`, the value silently defaults to 0, and the allocation total fails validation." Fix scheduled in **Upstream 2025.04 Hotfix – June 2026** (case feed, INFERRED). Repro: DO Maintenance → Import From Excel → rows with 8-decimal/tiny values → preview totals < 1.000000 → blocked. Happens whether the Excel column is numeric or text. |
| **23-00924182** "PRD A1 TEST - DOI Worksheet not all decimals are importing" (Software Defect; ~50 owners' NRI blank) | DOI Worksheet import | `Resolution__c` (verbatim): "Added a property **'NRIDecMasked'** in `DSTGDoDetailDoEXT.cs` which controls the precision configuration for small number and set it on Import and export excel methods in DOIWorksheet Controller." |
| **22-00676548** "DOI Detail Grid and Bearer Group Detail Grid Allowing Import and Manual Input of Decimals Passed Precision Config" (Software Defect) | Opposite direction — import bypassed the decimal-precision config | fix in release (2021-era); when auditing, check for detail rows whose decimal scale exceeds the client's precision config |

**Recipe:** (1) identify affected rows (values ≤ 1E-05 or scale > precision config); (2) check the client's build against the surface-specific fix above; (3) workaround pre-fix: format the Excel column so values don't serialize in scientific notation (pad to fixed 8-decimal text) or key the handful of tiny rows manually; (4) validate post-import totals sum to 1.0 per DOI.

## 6. Clusters H & I — Bulk edits that don't stick

### H — Owner Lease Xref import (Design Studio)

- **22-00672538** "Importing Owner Lease Xref to Replace Existing Content Not Working" (Software Defect): export → change xref number → import with "Replace Content" → grid shows new value but **Save reverts to the old number**. Reproduced by support; "Engineering has a fix… included in your upcoming patch" (case feed, 2021 — INFERRED build). Retest recipe from the case: filter by both Property and Owner Number, export/import the agreement-number change, Save, requery.
- **22-00823022** "Owner Lease Xref - Bulk Edit load does not work" (Software Defect, Design Studio) — same screen family, bulk-edit path.
- S3 skill Cluster H covers the Owner-Lease-Xref import basics; this cluster adds the replace/save-revert defect lineage.

### I — Bulk View/Edit defects

- **24-00965362** "MEW 2024.04 upgrade - Bulk Edit Not Functioning For Bearer Group Maintenance when Bearer Group details have date breaks" (Software Defect): replacing Bearer Decimal en masse produced adds/deletes instead of updates. Case feed splits it into **two tracked defects**: (1) *FK error on Bearer Group bulk edit* — Medium, approved for the **2025.10 GA release**; (2) *Bearer Percent decimal rounding on copy/paste* — High, fixed in the next engineering sprint on **2024.04** (tested OK in UAT 2024-12; both builds INFERRED).
- **22-00676537** "MRO myQuorum DOI Setup - Unable to Type or Paste the Agreement Number Within Bulk View Edit Screen" (Software Defect) — input-lock defect on bulk view/edit.
- **23-00884583** / **22-00823946** "System Time Delays/Maintenance Bulk Edit/Import to Owners" (Software Defect) — bulk-edit + import performance/time-out family (pair with S2 performance cluster).
- **22-00641176** "DOI History Search - Filtering On Multiple Records Values Within A Single Column Breaks Excel Export" (Software Defect) — the export side of the same grid stack.
- **22-00672533** "Import Spreadsheet Requesting Addt'l Fields on External Funds Transfer Screen" (Software Defect) — EFT import template demanded fields it shouldn't.

**Recipe:** for any "bulk edit didn't save / mangled rows" report: capture the exact grid + operation (update vs add/delete), row-count and whether date breaks exist on the target records; search ADO for the grid name — this family is heavily pre-logged; check build vs the fixed-in trains above before filing new.

## 7. Cluster J — External data loads (Mineral Answers, Datayank, well import)

- **26-01112343** "Import Data from Mineral Answers" (Application Configuration): client asked for "a loader their other clients use… not the A&D module." Support outcome: no standard product loader confirmed; request routed toward the **Services team** (case feed). Answer template: BA data loads from third-party sources are a Services/Datayank engagement, not a product feature.
- **26-01068062** "Datayank new PRD Business Associates for insert into UAT" (Application Configuration): client created BAs in PRD, refused a PRD→UAT refresh (would wipe a patch under test). `Resolution__c`: "Created the necessary scripts to add required BA data. Ref ADO WI **1778563** for the scripts" (Bug, Resolved, `QuorumServices\Managed Services`). Pattern: targeted datayank + QCloud deployment script instead of full refresh.
- **24-00941844** "Well Import Load Issue" (Application Configuration) — well-master import config family.

---

## 8. Expected-Behavior / User-Education FAQ

- **"Why does a JIB Offset owner force Pay Reason 5-Pay Regardless?"** Product rule: JIB-offset owners are set to pay regardless so offsets always settle; side effect is bypassing the minimum-suspense ($100) check. Recurring client complaint (26-01094960, prior 23-00878496) — no config exposed to change it; log as Enhancement if the client insists.
- **"Can we backdate a JIB deck?"** Yes — but only after the backdate pick registered SQL (`SELECT_DONL_DO_PROP_BACKDATE_PICK`) includes JIB; out of the box BD006 may list only REV decks (26-01118522).
- **"Why did my tier number change to 1?"** Auto-numbering is the default; manual tier numbers need `CAN_CHANGE_TIER_VALUE` / `CAN_CHANGE_TIER_JIB_VALUE` enabled (25-01043348).
- **"The transfer warned about market rep / fatal error but everything looks fine."** On JIB DOIs those warnings (RADOITRW58/59) are invalid noise in pre-fix builds — verify the combine result, then ignore (26-01064806, ADO 1622910/1739512).
- **"Exactly one JIB Base tier per property"** — both the error demanding it everywhere and silent approval with none are known defect states, not the rule itself (ADO 1618171/1639565).

---

## 9. Known ADO Items

| WI | Type/State | Title (verbatim) | Fixed-in |
|---|---|---|---|
| **1618171** | Bug, Closed | CNR, MEW - Cannot save JIB DOI without JIB Base Flag checked | tags `SEPT 2022.04; OCT 2022.04` (CONFIRMED tags) |
| **1639565** | Bug, Closed | CNR - JIB Base Flag Fix Still Does Not Work | follow-up to 1618171 |
| **1739512** | Bug, Closed | MEW - Invalid Warning Messages About Combining Interest (25-01027179) | Nov-hotfix wording fix; market-rep REV-only in 2025.04 (INFERRED) |
| **1622910** | Bug, Closed | 23-00918228--No default market rep found warning message on converted dummy DOIs for Revenue Suspense | tag `Robot RN 2026.04` (INFERRED) |
| **1837136** | Bug, Closed (project Quorum) | REP 2024.10 - Cost Center Last No does not correctly update in code table QARCH_TRAN_SEQ | release-noted (INFERRED) |
| **1322617** | Bug, Closed | APA - 2020.09 Build Upgrade - myQDO DOI Setup Screen Importing from Excel Sets Some Owner NRIs to 0 | tag `2021.04 hotfix 1` (CONFIRMED tag) |
| **1813832 / 1813831** | Bugs, Closed (project Quorum) | MEW - QDO - Import From Excel Not Recognizing Small Decimals For DO Maintenance - 26-01103568 | Upstream 2025.04 Hotfix – June 2026 (INFERRED, case feed) |
| **1778563** | Bug, Resolved (QuorumServices\Managed Services) | 26-01068062--Datayank new PRD Business Associates for insert into UAT | scripts delivered |

---

## 10. Diagnostic SQL

Verify all table/column names via the metadata server before running; SELECT before UPDATE, in a transaction. Items marked NOT YET RUN are templates derived from case text.

```sql
-- A. Cost-center numbering drift (code table 29111; ADO names it QARCH_TRAN_SEQ)  [NOT YET RUN]
-- Compare the code table's "Last No" against the true max cost-center number.
-- UI path (CONFIRMED workaround, 26-01111459): Maintenance > Code Table Value Editor
--   > code table ID 29111 > set "Last No" = actual last used number > Update.

-- B. JIB base-flag audit: exactly one base tier per property  [NOT YET RUN]
-- SELECT PROP_NO, COUNT(*) FROM <DONL DO header table>
-- WHERE DO_TYPE_CD='JIB' AND <JIB base flag column>='Y'
-- GROUP BY PROP_NO HAVING COUNT(*) <> 1;

-- C. Backdate pick: inspect registered SQL SELECT_DONL_DO_PROP_BACKDATE_PICK
--    (metadata server > registered SQL) and confirm JIB DO types are included
--    (CONFIRMED fix vector, 26-01118522).

-- D. Import-decimal audit after an Excel load  [NOT YET RUN]
-- SELECT <owner cols>, NRI_DEC FROM <DONL_DO_DETAIL>
-- WHERE <deck keys> AND (NRI_DEC = 0 OR NRI_DEC < 0.0001)
-- ORDER BY NRI_DEC;  -- compare against the source spreadsheet rows
```

Config keys referenced (CONFIRMED in cases): `CAN_CHANGE_TIER_VALUE`, `CAN_CHANGE_TIER_JIB_VALUE` (25-01043348). Security objects/processes: `ORGCOSTGEN` (25-01042097), `ORG/BTYP/QRA` (25-01048054). Code tables: **29100** default market rep (ADO 1622910/1739512), **29111** cost-center sequence (26-01111459 / ADO 1837136).

---

## 11. Escalation

- **Config/security fixes** (tier configs, backdate reg SQL, ORGCOSTGEN, ORG/BTYP/QRA, code table 29111 Last No): applyable by support/Managed Services with client approval; document key, table, value, and whether QPEC/cache refresh is needed.
- **Code defects:** search ADO first — every import-decimal and JIB-base-flag symptom above already has a closed bug; answer with fixed-in build where possible. New defects: project `QuorumSoftware` (areas `Engineering\Revenue\Committed Backlog`, `Engineering\Maintenance\Upstream\…\Revenue`) or project `Quorum` (`North America\Upstream\myQ Accounting RnD` for newer CC/import bugs). Title convention: client prefix + SF case number.
- **External data loads** (Mineral Answers, PRD→UAT datayank): route to Services / Managed Services (`QuorumServices\Managed Services`), reference WI 1778563 as the delivery pattern.
- **AP055/GL025/JB020 DOI-validation escalations:** `QuorumSoftware\Engineering\Financials` per `SKILL_ADO_QDO_DivisionOrder_Transfers.md`.

---

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
