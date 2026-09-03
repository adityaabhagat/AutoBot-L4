# SKILL — QLS Participation, Organization & Business Associate Master Data

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Scope (Coverage Plan group #8, 646 cases / 149 actionable):** Participation node (screen, participation change, change of interest, import/bulk edit), Business Associate (BA) master data + address suffixes/usages, BA integration (SAP/Upstream/PUBBA/Boomi), intercompany flagging (`ORG_UNIT_KEY`), Additional Party tab, Names & Addresses, Organization node (org codes, cost centers, WBS, financial org hierarchy), Payee Selection as a BA-visibility symptom.
> **Sources:** all-history Salesforce mining 2026-09-03 (6 SOQL survey pages + ~30 cases detail-sampled, SF case IDs verbatim) + ADO org `QuorumSoftware` (projects `QuorumSoftware`, `Quorum`) work-item mining. PII redacted (individual names/emails removed; 3-letter client codes retained as anchors).
> **Maintained by Auto-Bot — the L4 issue solver built by Aditya Bhagat.**

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cluster | First check | Likely class |
|---|---|---|---|
| Participation screen won't open: "missing ) after argument list" / blank screen | 3.1 | Build vs ADO 1760536 hotfix tags; recent patch deploy | G3 Version |
| Participation screen error only after a patch/upgrade, AGM + ARE + DEP levels | 3.1 | Patch collateral (#1733207 family); JS bundle minify failure | G3 Version |
| "Type of Change" dropdown blank on Participation Change; or duplicated on Change of Interest | 3.2 | Stale QCEN config layer (V17 upgrades) vs ADO 1767904 flip-flop | G2 Config / G3 |
| Participation Excel import fails / imported checkboxes+addresses wrong / bulk edit misbehaves | 3.3 | Screen properties AllowExcelImport/AllowBulkEdit; ADO 1720163/1624237 | G3 / G2 |
| QLS allowed total WI > 100% on a depth | 3.3 | ADO 1783638 — save-time validation added, hotfixed | G3 Version |
| BA no longer flagged intercompany / payments to internal company fail | 3.4 | `USE_BU_CODE_FOR_ORG_UNIT_KEY` config; SAP/UPS interface overwrite | G2 Config |
| `ORG_UNIT_KEY` set to null/0 in `PARTICIPANT_ADDRESSES` by service account | 3.4 | Same config key (key group INTEGRATION); interface adaptor | G2 Config |
| New/updated BAs not appearing in QLS at all | 3.5 | PUBBA/interface running? code-table (qcode) sync? | G4 Bad Data / G2 |
| New BA exists in Admin → Business Associates but not in payment Payee Selection | 3.5 | BA address usages/suffixes; how BA was loaded (API vs interface) | G4 Bad Data |
| BA address suffix "0" rows, duplicate BA/BP numbers, crosslinked BAs | 3.5 | Known data signatures — correction scripts | G4 Bad Data |
| Rental Payee usage/address disappeared from many BPs | 3.5 | Interface update overwriting usage rows | G4 Bad Data |
| PUBBA error saving foreign BA address | 3.5 | Missing country/state combos in QLS code tables | G2 Config |
| Delete in Additional Party errors: "Column 'ArrgKey, SeqNum' is constrained to be unique" (AddnLessorsMView) | 3.6 | Duplicate additional-party rows pushed from QLA | G4 Bad Data |
| Agreement Search by Participation returns BAs no longer on participation | 3.6 | Orphan `MULTIPLE_ADDRESSES` rows after participation change | G4 Bad Data (defect-sourced) |
| Organization sync errors after an org node was deleted/recreated | 3.7 | Org Code reused under new Org Key — broken QLS↔UPS sync | G4 Bad Data |
| JE interface failures on old agreements (V7→V17 converts) | 3.7 | Leftover V7 "STD" financial-org hierarchy levels | G4 Bad Data |
| Organization tab empty/locked/wrong count; Get Cost Centers dead for a subject type | 3.7 | Config/security on org node; subject-type mapping | G2 Config |

---

## 2. Decision Tree

```
Symptom is on the Participation node?
├─ Screen won't open / JS error / readstream error? → 3.1
├─ Participation Change or Change of Interest dropdown wrong? → 3.2
└─ Import/bulk-edit/validation (WI>100%) issue? → 3.3
Symptom is about a BA (master data)?
├─ Intercompany / internal flag / ORG_UNIT_KEY? → 3.4
└─ BA missing, duplicated, wrong address/usage/suffix, sync? → 3.5
Symptom on Additional Party tab, or Participation search wrong results? → 3.6
Symptom on Organization node / cost center / WBS / financial org? → 3.7
```
Gate order stays G1→G2→G3→G4→G5. This group splits roughly: screen behavior → **G3** (hotfixed), intercompany/dropdowns → **G2** (config layers), master-data visibility → **G4** (interface/data correction scripts).

---

## 3. Symptom Clusters

### 3.1 Participation screen fails to open (JavaScript/bundle errors)

**Signature.** Opening the Participation node on any agreement throws "missing ) after argument list" (browser JS error) or the screen never renders. Visible at AGM, ARE and DEP levels. Server log variant: `System.NullReferenceException` inside `Microsoft.Ajax.Utilities.JSParser` → `Minifier.MinifyJavaScript` → `System.Web.Optimization` bundle pipeline (i.e., the Participation screen's JS bundle fails to minify/parse).

**Root cause.** Defective JavaScript delivered by a patch: ADO Bug **1760536** `SOC - QLS - Error when opening Participation screen` — introduced by patch work item #1733207, propagated to PRD by patch #1760979; the participation screen script was the problem (2023.04 and 2025.04 trains were verified NOT affected; 2024.04/2024.10 were). Fixed under **2024.04 Hotfix + 2024.10 Hotfix** (tags Completed). A related read-path failure: ADO **1800776** `QLS - Participation screen readstream not working` (project Quorum, Closed).

**Fix recipe.**
1. Confirm the client build/train. If 2024.04/2024.10 pre-hotfix → quote ADO 1760536 fixed-in (G3), have Cloud Ops deploy the hotfix/patch.
2. If error appeared right after a patch, diff the deployed Participation screen script vs the hotfix — this family is always patch collateral, not data.
3. SF companion: **25-01044130** ("Error when opening Participation screen", Software Defect) — resolution recorded verbatim: *"2024.10 December 2025 HF"*.

**Anchors:** SF 25-01044130; ADO 1760536, 1800776, 1733207/1760979 (causing patches), 1720163 (history contains the full JSParser stack trace).

---

### 3.2 Participation Change / Change of Interest — dropdown blank or duplicated

**Signature.** Actions → Participation Change: "Type of Change" dropdown is blank (no change can be made). Or Change of Interest shows the reason list duplicated several times. After a session timeout + re-login the two symptoms can flip-flop.

**Root causes (two distinct).**
1. **Stale/outdated config layer (G2):** SF **25-01024089** `V17 Upgrade - QLS - Unable to Choose Participation Change Type` — resolution verbatim: *"removed out dated QCEN configuration. No functionality lost."* On V17 upgrades, an old client (QCEN-era) configuration layer masks the code/decode set feeding the dropdown.
2. **Code defect (G3):** ADO Bug **1767904** `XOM - QLS - Participation Screen - Change Reason Codes` — blank Type of Change on Participation Change AND duplicated list on Change of Interest, flip-flopping with session state; reproduced in XOM_DEV17HD. **Hotfix Completed on 2023.04 / 2024.04 / 2024.10 / 2025.04.** SF companion: **25-01047304** `Participation Screen - Change Reason Codes` (Application Configuration). Follow-up regression: ADO **1791941** `QLS - Participation - Change Of Interest popup not visible` (Closed, project Quorum, post-25.04).

**Fix recipe.** Check build against 1767904 hotfix tags first (cheaper). If the build already has the fix, hunt the config: compare the participation-change code/decode values across metadata layers (core vs client vs environment); remove the stale layer entry rather than adding new values on top.

**Anchors:** SF 25-01024089, 25-01047304; ADO 1767904, 1791941.

---

### 3.3 Participation import / bulk edit / interest validation

**Signature.** Excel import to Participation errors or silently drops Operator/Partner checkboxes and Participant Addresses; bulk edit misbehaves; or QLS accepts participations whose total decimal interest for one interest type exceeds 100%.

**Root causes / known items.**
- ADO **1624237** `Cannot Import Spreadsheet on Participation Screen` — Engineering decision recorded: instead of fixing import on this screen, set screen properties **AllowBulkEdit=false, AllowExcelImport=false, AllowExcelExport=true** for Participation (export-only). If a client asks why import is gone: that is the product decision. Note from its history: what "worked" before was only updating editable fields (Type of Interest, Decimal Interest), not truly adding BAs (#1556796).
- ADO **1720163** `Import functionality Operator, Partner checkbox and Participant Addresses not visible as expected` — Closed, **2023.04/2024.04/2024.10 Hotfix Completed**, tagged `platform:dependent`.
- ADO **1711136** `Kendo Upgrade - Update Participation Interest popup position/stuck open` — Closed (Kendo-upgrade collateral family).
- ADO **1783638** `DMB - QLS allowing over 100% WI on depths` — validation added **on save** (existing bad data is NOT auto-corrected; user sees the error when next managing the record; approval blocked for agreements with invalid participation). **Hotfix Completed 2023.04→2025.04.** Per-interest-type totals validated independently; Mass Participation Change Wizard regression-tested.
- SF **25-01007798** `Performance Issue - Participation Screen` (Software Defect) — resolution verbatim: *"Land 2022.04 April 2025 Hotfix"*.
- SF **24-00969242** `Unable to Import Excel Spreadsheet in Participation` (Application Configuration) — same import family as 1624237.

**Fix recipe.** For import complaints, check the screen-property configuration first (G2), then 1720163 fixed-in (G3). For >100% WI, quote 1783638: fixed-in + the explicit caveat that historic over-100% rows remain until touched.

**Anchors:** SF 25-01007798, 24-00969242; ADO 1624237, 1720163, 1711136, 1783638, 1556796 (ref).

---

### 3.4 Intercompany BAs — internal flag / `ORG_UNIT_KEY` overwritten by integration

**Signature.** A BA that was intercompany stops being intercompany after a SAP/Upstream interface run; payments with the internal company as payor fail to save; `PARTICIPANT_ADDRESSES.ORG_UNIT_KEY` shows null or 0 where it should be 1 (or the business-unit code); scripts that set the flag get silently reverted.

**Mechanism (CONFIRMED across two eras).**
- Design history: ADO Requirement **150643** `UPS to QLS BA Interface - ORG_UNIT_KEY is populated as boolean rather than the business unit code` (2020.03 hotfix, clients CNX/EQC/KKR/MRO). The UPS→QLS BA interface (**PUBBA**, launched as an eSuite batch process; adaptor `Quorum.ESuite.QLS.Integration.QQLSBusinessAssociateIntegration`, assembly `Quorum.ESuite.Integration.QLS`, object type `QlsBusinessAssociate`) populates `ORG_UNIT_KEY`. A configuration decides whether it writes `1` (boolean "internal") or the true company code per `SCTRL_BUS_UNIT_BA` setup; internal-entity source is `SCTRL_BA_ENTITY.INTERNAL_ENTITY` (eSuite side; ref bug 150630).
- Modern config key: **`USE_BU_CODE_FOR_ORG_UNIT_KEY`** under key group **INTEGRATION**. SF **24-00970663** resolution verbatim: *"Changed USE_BU_CODE_FOR_ORG_UNIT_KEY = 0 in Western Client Managed layers in configuration to allow changes made to intercompany BA's to allow them to remain intercompany. Original list of BA's fixed with a data script to reassign them intercompany."*
- SF **25-01055070** `SVC_PRO17Q service account changing the ORG_UNIT_KEY to null and 0 in PARTICIPANT_ADDRESSES` — resolution: SAP-side updates + the same INTEGRATION / `USE_BU_CODE_FOR_ORG_UNIT_KEY` config change. (Internal-organization participants should carry `ORG_UNIT_KEY = 1` for correct internal-company recognition when the boolean mode is used.)
- Recurrence chain at one client (WML/Solaris entity): SF **25-01060211 → 26-01064649 → 26-01089230 → 26-01103725** — a SAP-interfaced change on the BA repeatedly overrode the manual internal-flag script; each time fixed by re-running the script (26-01103725 resolution: *"Redeployed script to set internal flag for the BA"*). Short-term payment workaround tracked in 26-01064649.
- Address-level variant: ADO Bug **199279** (CHV) — intercompany address flag reverts whenever the BA is edited on the Business Associate screen; correction script `CHEVRON_CORRECT_ADDRESS_FLAG_FOR_INTERCOMPANY` with the explicit warning that BA-screen edits revert it again.
- Missing intercompany BPs entirely: SF **25-01035744** `Missing Business Partner numbers from SAP - Participation Issue` — agreements holding those BPs in Participation error until the BPs interface over.

**Fix recipe.**
1. Verify the config: `USE_BU_CODE_FOR_ORG_UNIT_KEY` (key group INTEGRATION) in the client's managed config layer. Value must match how the client's financial integration expects `ORG_UNIT_KEY` (boolean 1 vs BU code). Wrong/default value ⇒ every interface run reverts manual fixes — fix the config, THEN re-run the data script once.
2. Data correction (after config): set the internal flag / `ORG_UNIT_KEY` for the affected BAs by script (see §5.1); document that the script is idempotent and keep it handy only until the config change lands.
3. Never classify these as one-off data fixes — if a script had to be redeployed (26-01103725 chain), the config/interface is still overriding: that is G2, not G4.

**Anchors:** SF 24-00970663, 25-01055070, 26-01103725 (+chain 25-01060211, 26-01064649, 26-01089230), 25-01035744, 24-00980207 (participant tax types extension); ADO 150643, 199279, 150630 (ref).

---

### 3.5 BA master-data visibility & integrity (sync, suffixes, duplicates, usages)

**Signature family** (all G4-leaning; each has a distinct data signature):

| Symptom | Case (verbatim resolution where recorded) | Signature / fix |
|---|---|---|
| New BAs created in Upstream never arrive in QLS | SF **24-00970908** — *"Updated config & did full resync follow data conversion due to bad data"* | Interface config wrong post-conversion → fix config, PUBBA full resync |
| Not all BAs appearing in QLS | SF **25-01005063** — *"code table sync fixed"* | qcode/code-table sync job stopped; restart/fix sync |
| BA queryable in Admin → Business Associates but absent from payment Payee Selection | SF **25-01012068** (BAs loaded from client ERP via API) | BA row exists but payment-payee picklists join on address/usage rows — check `PARTICIPANT_ADDRESSES` + address-usage rows for the BA (see §5.2); insert missing usage/suffix rows |
| Existing owner not findable in QLS | SF **25-00996536** — *"Script to insert the participant and participant address has been executed"* | Missing `PARTICIPANTS` / `PARTICIPANT_ADDRESSES` rows |
| BAs created with a "0" address suffix; deleting suffix in QRA does not remove it in QLS | SF **25-01034563** (prior: 22-00569472) | Known sync gap: the QRA→QLS sync does not delete removed suffixes; clean by script; QLS BA table is not analyst-editable |
| Duplicate BA numbers / duplicate BPs | SF **24-00941585**, 24-00961543 | Data cleanup script; check number-assignment source before cleanup |
| Crosslinked BAs | SF **24-00970384** — cleanup script requested | Correction script family |
| Rental Payee usage/address stripped from hundreds of BPs (PRD ~502 vs UAT 2000+) | SF **24-00939472**, 24-00948801 | Interface update removed usage rows en masse — restore by script, then find the interfacing run that dropped them |
| Supplier/BA address integration updates ALL suffix lines instead of line 1 | SF **25-01017936** — *"After removing hyphens on zip codes in Boomi this integration works as expected"* | Middleware (Boomi) payload normalization — zip+4 hyphens broke line matching |
| PUBBA error saving foreign BA address | SF **25-01013544** (Netherlands owner) | Missing country/state combinations in QLS code tables — add combos (G2) |
| Missing SVALD records for BA addresses | SF **24-00984757** — script executed in PRD | Validation-support rows; script family |
| Conversion missed `PARTICIPANT_ADDR_USAGE_RLTN` | SF **25-01045683** | Conversion completeness — backfill table |
| TaxID field not editable creating BA | SF **24-00953772** | Field-level security/config on BA screen |

**Investigation order.** (1) Is the BA row present at all (`PARTICIPANTS`)? (2) Are its addresses/suffixes present (`PARTICIPANT_ADDRESSES`)? (3) Are usage rows present (address-usage relation; Rental Payee usage etc.)? (4) Is the interface/sync (PUBBA / qcode sync / Boomi flow) currently healthy, and did it cause the gap? A BA visible on the BA screen but missing from a payee picklist is almost always missing rows at step 2/3 — not security.

**Anchors:** all SF ids in table above.

---

### 3.6 Additional Party & participation-search data integrity

**Signature 1 — Additional Party save/delete blows up.** Deleting (or saving) rows on the Additional Party tab fails with:
`PostActionException ... Unable to enforce constants due to the following errors: Table AddnLessorsMView Errors: Row(...): Column 'ArrgKey, SeqNum' is constrained to be unique. Value '...' is already present.` Stack goes through `QUIControllerAdditionalParty.DoSave` → `QQLSServiceClient.UpdateMultipleAddnLessorsMView`.
**Root cause:** duplicate additional-party rows injected in bulk — SF **24-00944637**: a QLA→QLS lease push inserted *every* BA suffix of one BA (2036612) as additional parties on the pushed leases; the duplicated (ArrgKey, SeqNum) pairs then break any UI save/delete. Fix: dedupe/delete the rows by script (UI cannot), then chase the QLA push defect. Related QLA-push gap: SF **22-00821099** (`Certain data not auto-populating when pushing from QLA to QLS`, Software Defect).

**Signature 2 — Search by Participation returns agreements whose BA is NOT on participation.** SF **22-00824627** (Software Defect) resolution verbatim: *"when you do a participation change it's not deleting from the MULTIPLE_ADDRESSES table"* — orphan rows in `MULTIPLE_ADDRESSES` keep the BA associated for search purposes after a participation change removed it. Fix: clean orphans (§5.3); treat recurrence on current builds as a defect candidate.

**Signature 3 — Additional Party type maintenance** (pure G2): adding/renaming Additional Party types per subject code is code/decode configuration — SF **26-01103095** (add `IP - Interest Party` for all subject codes), **26-01102136** (rename type). Route as config change with the exact decode values.

**Anchors:** SF 24-00944637, 22-00821099, 22-00824627, 26-01103095, 26-01102136, 24-00950668 (auto-fill Lessor from Agreement name — config).

---

### 3.7 Organization node — org keys, cost centers, WBS, financial org hierarchy

**Rule #1 (from a broken-sync postmortem):** *Once created, an Org Code/Key combination must not change.* SF **25-01042225** — an Organization node (Org Code F009766) was deleted and recreated; the Org Code was reused under a **new Org Key**, breaking QLS↔UPS organization sync ("Manual Changes Causing Organization Data Sync Errors"). Fix required data repair in UAT + engineering review. If a client asks to delete/recreate an org node: warn, and prefer end-dating/editing.

**Other confirmed signatures.**
- **V7→V17 conversion leftovers:** SF **25-01058787** — records still holding the V7 "Standard Hierarchy" (STD Org Level Types) in Financial Org cause **JE interface failures**; those level types no longer exist in V17 data, so the client cannot even find them from the UI. Fix: identify agreements carrying STD levels by script (active records with future payments first), remap to Cost Center/Profit Center flow.
- **WBS/cost-center hygiene:** SF **24-00980255** (delete bad WBS code that crashes FDW processes), 23-00912482 / 23-00912921-22 (WBS elements scripted/pushed into Quorum), **24-00982959** (mass inactivate TMC cost centers at AGM/ARE/DEP levels) — all script-serviced (Services route).
- **Get Cost Centers dead for one subject type:** SF **25-01036210** (`Get Cost Centers Not working for Land-Prospect`, Application Configuration) — subject-type→org mapping config.
- **Org node display/behavior:** SF 24-00952726 (tab shows "1 loaded" but empty when opened), 23-00901419 (Organization Tab Locked Up), 23-00904010 + 23-00901782 (`Organization Node Displaying Wrong Count`, Software Defect, deferred), 23-00877925 (`organizations not pulling up from sub (again)`, Software Defect — recurring sub-level retrieval bug in v17), 25-01029632 (Organization Node Issue (Uncon)).
- **Approval interplay:** SF 25-01031778 (`Agreement Approval Rules - Organization Requirement`, Security-categorized config), 25-01045391 (PXD Agreement Approval Error — org-node related config), 23-00903702 (approval errors from missing Prospect/Cost Center).
- **Copy Agreement wizard missing Financial Organization node:** SF 23-00917109 — node enablement config (also covered in the Agreements-Lifecycle skill §3.6).

**Anchors:** all SF ids above.

---

## 4. Known ADO Items

| ADO | What | State | Fixed-in |
|---|---|---|---|
| 1760536 | Participation screen won't open — "missing ) after argument list" (SOC); patch collateral of #1733207/#1760979 | Closed | 2024.04 + 2024.10 HFs (CONFIRMED); 2023.04/2025.04 unaffected |
| 1800776 | Participation screen readstream not working | Closed | project Quorum, 2026 (CONFIRMED closed; train unlabeled — INFERRED post-25.04) |
| 1767904 | Participation Change dropdown blank / COI reasons duplicated, session flip-flop (XOM) | Closed | 2023.04→2025.04 HFs Completed (CONFIRMED) |
| 1791941 | Change Of Interest popup not visible (post-25.04 regression of 1767904 family) | Closed | project Quorum (CONFIRMED closed) |
| 1720163 | Participation Excel import drops Operator/Partner checkboxes + Participant Addresses | Closed | 2023.04/2024.04/2024.10 HFs; platform:dependent (CONFIRMED) |
| 1624237 | Participation import broken → product decision: import & bulk-edit disabled, export kept | Closed | screen-property config, no code fix (CONFIRMED) |
| 1711136 | Kendo upgrade — Update Participation Interest popup stuck/mispositioned | Closed | Kendo-upgrade fix wave (CONFIRMED closed) |
| 1783638 | QLS allows >100% WI per interest type on depths (DMB) — save-time validation added | Closed | 2023.04→2025.04 HFs (CONFIRMED); existing bad rows not auto-fixed |
| 150643 | UPS→QLS BA interface: ORG_UNIT_KEY boolean vs business-unit code; config per SCTRL_BUS_UNIT_BA | Closed (Requirement) | 2020.03 hotfix (CONFIRMED) |
| 199279 | Intercompany address flag reverts on BA-screen edit (CHV); correction script | Closed | script `CHEVRON_CORRECT_ADDRESS_FLAG_FOR_INTERCOMPANY`, no code fix (CONFIRMED) |
| 1656716 | Agreement Search: Participation criteria tab goes invisible | Closed | 2023.04 HF (CONFIRMED) |

Area paths seen: `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Land` (1759806-family, 1760536, 1767904), `QuorumSoftware\Engineering\Land\Committed Backlog`, project `Quorum` for 2026+ items. Hotfix-tag convention `YYYY.MM Hotfix (+ Completed)` holds throughout — usable for G3 checks.

---

## 5. Diagnostic SQL (Oracle, `lis` schema — drawn from real cases; verify column lists against live schema before running)

**5.1 Intercompany / ORG_UNIT_KEY audit (SF 25-01055070, 24-00970663):**
```sql
-- internal-company participants whose org unit key was nulled/zeroed by the interface
SELECT p.prtp_key_ext, pa.addr_suffix, pa.org_unit_key
  FROM lis.participants p
  JOIN lis.participant_addresses pa ON pa.prtp_key = p.prtp_key
 WHERE pa.org_unit_key IS NULL OR pa.org_unit_key = 0;   -- expected 1 (boolean mode) or BU code
-- config that controls the interface behavior (table INFERRED from client metadata repos):
SELECT * FROM lis.qarch_cnfg_ctrl WHERE key_name = 'USE_BU_CODE_FOR_ORG_UNIT_KEY';
```
Correction (case-verbatim intent, 25-01055070): script the affected internal participants' `ORG_UNIT_KEY` back to `1` — but only after the INTEGRATION config is fixed, or the next PUBBA/SAP run reverts it (26-01103725 chain).

**5.2 BA visible in Admin but missing from Payee Selection (SF 25-01012068, 25-00996536):**
```sql
-- does the BA have address + usage rows the payee picklists join on?
SELECT * FROM lis.participant_addresses WHERE prtp_key = :ba_key;
SELECT * FROM lis.participant_addr_usage_rltn WHERE prtp_key = :ba_key;  -- table missed by one conversion (SF 25-01045683)
```
Empty result at either level with a present `PARTICIPANTS` row = the 25-00996536 signature (fix = insert participant address/usage rows by script).

**5.3 Orphan participation-search associations (SF 22-00824627):**
```sql
-- BAs still present in MULTIPLE_ADDRESSES for an agreement but no longer on participation
SELECT m.* FROM lis.multiple_addresses m
 WHERE m.arrg_key = :arrg_key
   AND NOT EXISTS (SELECT 1 FROM lis.participants p
                    WHERE p.arrg_key = m.arrg_key AND p.prtp_key = m.prtp_key);
```
(Join predicate INFERRED from the case's resolution statement; confirm key columns on the live schema.)

**5.4 Additional Party duplicate-row signature (SF 24-00944637):** the error text carries the dataset key pair — `AddnLessorsMView (ArrgKey, SeqNum)`. Find and dedupe the duplicated additional-party rows for the named `ArrgKey` (349494 in the case) in the additional-party base table, then re-open the tab. UI delete cannot fix it — the constraint fires before the delete lands.

**5.5 V7 financial-org leftovers (SF 25-01058787):** search Financial Org assignments for org level types that do not exist in the V17 hierarchy ("STD" Standard-Hierarchy levels), restricted to active records with future payments — deliverable is an inventory list + remap script (Services).

> DEV-tier caveat: run these on the client's `<CLIENT>_LND_DEV17` / `<CLIENT3>U_HD_DEV17` mirror via the metadata server; PRD data-state conclusions stay INFERRED until confirmed by client DBA output.

---

## 6. Expected-Behavior FAQ

- **"Why can't I import owners into Participation from Excel anymore?"** Product decision on ADO 1624237: Bulk View/Edit and Import from Excel were disabled for the Participation screen; Export to Excel remains. Participation adds go through the screen/picklist.
- **"QLS let us approve an agreement with 120% working interest — is that right?"** It was a gap; since ADO 1783638's hotfixes, save is blocked when one interest type totals >100%. Pre-existing invalid rows are only flagged when next edited; approval is blocked for agreements carrying them.
- **"Can the BA analyst edit the QLS BA table directly?"** No — BA master data is interface-owned (QRA/Upstream/SAP source of record); QLS-side edits get overwritten by the next sync (SF 25-01034563 answer, ADO 199279 warning).
- **"We deleted and recreated an Organization node with the same code — why did sync break?"** Org Code/Key combinations must never be recreated; the new Org Key orphans the old mappings (SF 25-01042225). End-date instead of delete.
- **"Should ORG_UNIT_KEY be 1 or our company code?"** Either, by design — `USE_BU_CODE_FOR_ORG_UNIT_KEY` (key group INTEGRATION) picks boolean vs SCTRL_BUS_UNIT_BA company code (ADO 150643). What matters is that QLS config and the financial-integration expectation agree.
- **"A BA's intercompany flag keeps reverting after we fix it."** The interface is authoritative — fix the config/source system, not just the row (§3.4). A redeployed script is a symptom, not a solution.

---

## 7. Escalation

- **Fixed-in citations:** quote ADO id + hotfix tags from §4; label client-build claims INFERRED until the exact `hotfix/17.2x.y` build is confirmed.
- **Escalate to Engineering** (`Quorum\North America\Upstream\Land RnD` current; `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` / `...\Professional Services\Land` legacy) when: a §4 defect reproduces on a build containing its hotfix tag; the AddnLessorsMView constraint error appears WITHOUT a duplicate-row cause; participation-change orphans (`MULTIPLE_ADDRESSES`) recur on current builds; org sync breaks without any manual org-node change.
- **Route to Services:** BA data-correction scripts (suffix-0 cleanup, crosslinked BAs, SVALD backfill, usage restores), V7 STD-hierarchy inventory/remap, conversion backfills (`PARTICIPANT_ADDR_USAGE_RLTN`), code/decode changes (Additional Party types, country/state combos). These ship via `<CLIENT3>.QLS.Metadata` / conversion script repos.
- **Route to Integration team (not Land Eng):** PUBBA adaptor behavior, SAP BP feeds, Boomi payload issues (zip-hyphen class), `SVC_*` service-account write patterns.
- **Batch flag:** PUBBA is an eSuite batch process — if the complaint is "BAs stopped syncing," check the batch schedule/health first (`batch-debugger` agent) before diagnosing data.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
