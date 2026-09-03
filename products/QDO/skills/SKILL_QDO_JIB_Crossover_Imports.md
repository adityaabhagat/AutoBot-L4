# SKILL: QDO JIB / Cost Center / AFE Crossover + Imports & Bulk Data Loads

**Version:** 1.0 | **Created:** 2026-09-02 | **Product:** My Quorum Division Order (QDO)
**Built by Auto-Bot — the L4 issue solver by Aditya Bhagat.**
**Scope — two families:**
**Section I (JIB crossover):** JIB-type DOIs (`DO_TYPE_CD='JIB'`), JIB decks/tiers, JIB Base Flag, JIB netting/offset (owner pay-reason interplay + `DSTG_SAP_JIB_OFFSET`), Cost Center creation from the eSuite web (ORGCOSTGEN), and the AFE↔DOI sync (`AFE_SYNCDO`). The *ADO defect-reference* side of DOI validation on AP/GL/AFE (AP055, GL025, JB020, AFEEXTIMP) is owned by S4 `SKILL_ADO_QDO_DivisionOrder_Transfers.md` — this skill owns the SF case families.
**Section II (Imports & bulk loads):** DOI Worksheet / DOI Setup "Import From Excel", Bulk Edit/View grids, Bulk Modify Loader, external loaders (Mineral Answers, Datayank), Owner Lease Xref (deep dive in S3 Cluster H), and well imports.

> **Evidence base:** all-history mining 2026-09-02, coverage-plan groups G12 (~18 actionable) + G13 (~16 actionable). SOQL sample: 50 closed JIB/cost-center/AFE/voucher cases + 47 closed import/excel/datayank/bulk cases, newest-first; 25 deep-read (Description + Resolution__c + comment/email probes); ADO confirmations via `search_workitem`/`wit_work_item`. Every claim cites a verbatim SF case number or ADO WI. Fixed-in builds **INFERRED** unless the WI states the merge.

---

# SECTION I — JIB / Cost Center / AFE crossover

## 1. Quick Triage (JIB)

| Symptom | Likely cause | Go to |
|---|---|---|
| JIB transfer Preview/Approve shows warnings `RADOITRW58` / `RADOITRW59`, or *"No default market rep found… This may cause fatal error"* | **Warning noise** — invalid on JIB DOIs (they don't use market groups); combine warning fires even when combine worked | §3-A (26-01064806, 25-01027179; ADO #1622910, #1739512) |
| Can't backdate a **JIB deck** — BD006 only lists Revenue decks | Registered SQL `SELECT_DONL_DO_PROP_BACKDATE_PICK` excludes JIB | §4-B1 (26-01118522) |
| **JIB Tier # reverts to Tier 1** on save | Configs `CAN_CHANGE_TIER_VALUE` / `CAN_CHANGE_TIER_JIB_VALUE` disabled | §4-B2 (25-01043348) |
| Error setting up **multiple JIB tiers** on one property | Code defect in `tierJibFlagList` filter (fixed) | §4-B3 (23-00916387) |
| "JIB Base Flag required" blocks a **file-copy DO** | Validation `QDODonlDoHdr_000022_ValidateJIBbaseFlag` | §4-B4 (24-00940784) |
| **Cost Center creation fails** with a security error (sometimes property still created) | Missing grants: `ORGCOSTGEN` process / ORG-BTYP-QRA security objects | §5-C (25-01042097, 25-01048054) |
| Saving an owner flagged **JIB Offset** demands Pay Reason **5-Pay Regardless**; tiny checks then get paid | JIB-netting pay-reason requirement vs $100 minimum-suspense conflict (by design; long-running gripe) | §6-D (23-00878496, 26-01094960) |
| MG **removing JIB netting** from a BA errors on Preview | Netting-removal defect | §6-D (23-00920921) |
| BA JIB-netting changes push **wrong values into `DSTG_SAP_JIB_OFFSET`** | Web BA screen → SAP staging mapping defect | §6-D (22-00830502; 22-00676527 fixed Spring 2021 GA) |
| **AFE not updated** after a JIB DOI transfer | `AFE_SYNCDO` failed to auto-launch; run it manually | §7-E (ADO #1397799) |
| JIB DOI MG **approve completes but errors** `Unable to establish a connection with any endpoint` | Middle-tier endpoint config (`EndpointInfoResolver… endpointInfos was non-null, but is empty`) | §7-E (ADO #1723387, related #1732619) |
| AP055/GL025/JB020 "not an effective JIB DOI" validation on vouchers/GL/AFE | Financials-side DOI validation defects | **S4** (ADO reference skill) |

## 2. Concepts

- **JIB DOI** = Joint Interest Billing deck: working-interest cost-share ownership (vs REV = revenue). Same DOI machinery (DO006 setup, MG/workspace transfers, tiers) with `DO_TYPE_CD='JIB'`; consumed by JIB billing (JB020) and AP/GL DOI validation (S4).
- **JIB tier** = a JIB deck's tier number; tier edits are config-gated (§4-B2). **JIB Base Flag** (`JIB_BASE_FL` on `DONL_DO_HDR`; users asked to expose it on DO005 — 26-01069400, closed No Action) marks the base JIB deck; duplicated base flags have needed cleanup scripts (22-00825881).
- **JIB netting / JIB Offset** = a working-interest owner's revenue is offset against their JIB (billing) balance. Flagged on the BA/owner; integrates to SAP via **`DSTG_SAP_JIB_OFFSET`**. Netting requires the owner to pay regardless of minimum-suspense thresholds — hence the forced **Pay Reason 5-Pay Regardless** (§6-D).
- **Cost Center** = the accounting entity behind a property; created from the eSuite web via the **`ORGCOSTGEN`** batch process (security-gated). Property and cost-center creation are separate steps that can half-succeed (§5-C).
- **AFE_SYNCDO** = batch process that pushes DOI ownership changes to AFE cost-center information after a JIB DOI transfer (§7-E).
- **Warning codes:** `RADOITRW58`/`RADOITRW59` are transfer-preview warnings; message id `{DO-DOINTXFRWB-7316856}` appears in the "No default market rep found… may cause fatal error" text. Market reps come from **Code Table 29100** (per ADO #1622910 repro).

## 3. Cluster A — JIB transfer warning noise ("Fatal Error" that isn't)

**Signature:** MG Preview/Approve on a **JIB** DOI logs warnings — `RADOITRW58` (*"No default market rep found. This may cause fatal error {DO-DOINTXFRWB-7316856}"*) and/or `RADOITRW59` (combine-interest warning) — process itself completes green.
**Root cause:** two related message defects. (1) JIB DOIs don't use market groups, so the market-rep warning is invalid on JIB (valid but overworded on REV; rep configured on Code Table 29100) — ADO **#1622910** "23-00918228--No default market rep found warning message on converted dummy DOIs for Revenue Suspense" (Closed 2025-10-22). (2) Combine warnings fire on many-to-one JIB transfers with Combine Flag even though the interest *did* combine and the transfer-to owner was not sequenced — ADO **#1739512** "MEW - Invalid Warning Messages About Combining Interest (25-01027179)" (Closed; reproduced in MEWU_HD_DEVA1 and CORE_SUP).
**Fix recipe:** on current builds the message was reworded (no more "Fatal Error") and restricted to REV DOIs. On older builds, per SF `26-01064806` resolution (verbatim): *"this warning has been updated in later versions… to no longer say 'Fatal Error' and also was changed to only hit on REV DOIs. Since they don't have this change and this is for JIB, [client] can ignore this warning."* → classify **Version issue (G3)**; customer explanation: warning is cosmetic on JIB, transfer results are correct (verify the Message Log shows the process green and decimals foot).
**Anchors:** SF 26-01064806 (Software Defect, Closed 2026-01-09), SF 25-01027179 (Software Defect, Closed 2026-04-14), ADO #1622910, #1739512.

## 4. Cluster B — JIB deck / tier setup & backdating (config-heavy)

**B1 — Backdating a JIB deck.** `26-01118522` (App Config, Closed 2026-08-03): BD006 backdate picklist only offered Revenue decks. Resolution (verbatim): *"We provided the client a configuration in the Reg SQL ID: `SELECT_DONL_DO_PROP_BACKDATE_PICK`, where JIB was added in order to allow the client to run the DO backdate process for JIB decks."*
**Recipe:** edit that registered SQL to include `DO_TYPE_CD='JIB'` in the pick; retest BD006. Related how-to: `25-01021825` "Backdate a JIB Tier" (App Config — same lever; REV worked, JIB needed the config).

**B2 — JIB tier # auto-reverts to Tier 1.** `25-01043348` (App Config, Closed 2025-09-22). Resolution (verbatim): *"Enabled the following configs CAN_CHANGE_TIER_VALUE, CAN_CHANGE_TIER_JIB_VALUE."*
**Recipe:** both configs must be on for users to key a non-default tier on JIB DOIs; check them before suspecting a save defect.

**B3 — Multiple JIB tiers error.** `23-00916387` "UAT2 - Error when trying to set up multiple JIB tiers" (Software Defect, Closed). Resolution (verbatim): *"Updated the filter for tierJibFlagList to check whether any DOI with JIB flag checked is present in the database while adding DOI."* → G3 on old builds; cite the case when a client on a pre-fix build can't add a second JIB tier.

**B4 — JIB Base Flag validation blocks file-copy DO.** `24-00940784` (App Config). Resolution (verbatim): *"Disabled QDODonlDoHdr_000022_ValidateJIBbaseFlag validation."*
**Recipe:** the validation requiring a JIB base flag can be disabled per client when their file-copy workflow legitimately creates DOs without it. Cleanup precedent for *duplicate* base flags: 22-00825881 (script).

## 5. Cluster C — Cost Center creation & security (eSuite web)

**Signature:** user creates a Cost Center / property from the web; gets a security error; sometimes the property is still created (half-committed workflow).
- `25-01042097` "UNABLE TO CREATE PROPERTY AFTER COST CENTER CREATED" (App Config). Resolution (verbatim): *"Ran security update scripts to give users access to the ORGCOSTGEN process."*
- `25-01048054` "UAT tried setting up a cost center. security error, but it also says that the property was successfully created." (App Config). Resolution (verbatim): *"Added ORG/BTYP/QRA security object to groups 70000 and 90671012."*
- `26-01111459` "COST CENTER ISSUES-HIGH IMPORTANCE" (Software Defect, **Closed - Deferred**): sudden failures creating cost centers regardless of name; deferred without published fix — if this signature reappears, treat as open defect and re-escalate citing 26-01111459.
**Recipe:** (1) capture the exact security-object name from the error; (2) grant `ORGCOSTGEN` process access + ORG/BTYP/QRA objects to the user's groups; (3) after a "half-created" run, verify whether the property exists before re-running, to avoid duplicates. Expected-behavior note: cost-center *code/renumbering* questions (26-01098849, 26-01092858, 23-00913910) are usually Training/Customer-Error — check numbering standards before investigating.

## 6. Cluster D — JIB netting / JIB Offset

**D1 — JIB Offset forces Pay Reason 5-Pay Regardless.** `23-00878496` + repeat `26-01094960` (App Config, Closed 2026-04-22). Description (verbatim, condensed): *"When trying to save an owner record and the owner is marked with JIB OFFSET the system requires us to change the pay reason to 5-PAY REGARDLESS… Pay Regardless will ignore the minimum suspense amount and pay checks under $100."* This is the JIB-netting design: netted owners must be payable regardless of minimum-release thresholds so revenue can offset billing; the side effect is small checks. No config to make 5-Pay-Regardless honor the minimum was delivered on these cases — treat as **Expected Behavior + enhancement flag**; workaround used historically (from 23-00878496): mass-set non-netted owners back to 1-Normal, keep 5 only on true netting owners.
**D2 — Removing JIB netting errors the MG.** `23-00920921` "MG Error - Remove JIB Netting from BA…" (Software Defect, Closed 2023-12-13; resolution not recorded in SF — comments empty). Reproduce on two MGs before escalating; cite this case as precedent.
**D3 — SAP staging values wrong.** `22-00830502` "Changes to JIB Netting Information within Business Associate Screen Populating Incorrect Values into `DSTG_SAP_JIB_OFFSET`" (Closed - No Response) and `22-00676527` "JIB Netting Interface with SAP" (Software Defect) — resolution (verbatim): *"Included in Spring 2021 GA Release."* → G3 for legacy builds; verify staging rows against the BA screen values (SQL §12).
**D4 — Misc anchors:** JIB decks not appearing in MG Creation (26-01087387, 26-01083172, 26-01069321 — all closed No Action Taken; check DOI-type filters/effectivity before escalating); JIB deck changes missing in SAP (23-00912174, Customer Cancelled); JIB DOI integrations failing on MG approval (22-00581746); suspense owners for JIB net (22-00809679, Training).

## 7. Cluster E — AFE crossover & JIB process launch failures

**E1 — AFE_SYNCDO not launching after JIB DOI transfer.** ADO **#1397799** "APHU - myQDO Web - AFE Sync DO Process Failure to Launch Upon JIB DOI XFER" (Closed, MergedToDevelop, 2022.04 retest tag). Per WI description: *"When initiating a JIB DOI transfer associated with an AFE, the AFE_SYNCDO updates the AFE Cost Center information"* — the process was expected to auto-run on every JIB DOI transfer but didn't; AFE stayed stale until `AFE_SYNCDO` was run manually.
**Recipe:** if AFE cost-center ownership doesn't reflect a completed JIB transfer, run `AFE_SYNCDO` manually and compare; on pre-fix builds classify G3, else re-escalate.
**E2 — JIB MG approve: endpoint error after green batch.** ADO **#1723387** "QDO - Getting error on JIB DOI Maintenance Group approve" (Closed, tag `not 2026.04 Ups`): approve batch completes but UI shows *"Unable to establish a connection with any endpoint."* MT log (verbatim): `EndpointInfoResolver.Construct.NoEndpointInfos… parameter endpointInfos was non-null, but is empty` from `Quorum.QFC.Metadata.ServiceCommon\EndpointManagement\EndpointInfoResolver.cs`, service `Quorum.Upstream.QDO.Application.MiddleTier`; blocked for a time by Bug **#1732619** "'Preview DOI Interest transfer for Workspace Group - DOINTXWRK' batch process gets failed."
**Recipe:** this is *environment/service endpoint config*, not data: verify the QDO MT service endpoints (metadata endpoint registration) before touching the MG. The MG data itself is usually fine (batch completed).
**E3 — Financials-side validations** (AP055 voucher "not an effective JIB DOI", GL025, JB020, AFEEXTIMP, converted-AFE DOI decimals) → **S4** owns the ADO defect map; `25-01029847` "'AFER ENDDATEOILOWNER DO…' error on PA059" (Project Debt) is a related SF-side anchor.

---

# SECTION II — Imports & bulk data loads

## 8. Quick Triage (Imports)

| Symptom | Likely cause | Go to |
|---|---|---|
| DOI Worksheet **Import From Excel drops small decimals** (NRI blank/0 for 50+ owners) | Web grid loader fails on small decimals (scientific-notation range) | §9-F1 (23-00924182, ADO #1625151) |
| Imported NRIs accept **more decimal places than PRECISION config** | Worksheet ignores global `PRECISION` (core default 8; DB supports 10) | §9-F2 (ADO #1727280; 22-00676548) |
| **NRIs load as 0** with Import From Excel | Same decimal-parse family, legacy builds | §9-F1 (22-00676543, 22-00559779) |
| Bulk Edit/View **missing a required column** (Owner Sub) → save fails validation | Release collateral damage in 2023.04 | §10-G1 (23-00924854) |
| **TEGs load to worksheet but never reach live** tables | Worksheet→live import gap | §10-G2 (22-00830146) |
| Import errors "**GWI Bearer Group 1 does not exist**" but re-keying the same value saves | Grid-import validation quirk — re-key the cell | §10-G3 (25-01055290) |
| Bearer-group Bulk Edit **PK violation with date breaks** | See Upgrade skill §7-D5 | (24-00965362, ADO #1687869) |
| Need **PRD BAs copied into UAT** (Datayank) | Managed-Services scripted data load | §11-H1 (26-01068062, ADO #1778563) |
| How to load **Mineral Answers** BA data | Standard BA loader path (not the A&D module) | §11-H2 (26-01112343) |
| Well import fails "**Legal Description is required if in-house operated**" | Registered SQL `SELECT_VALIDATE_WC_LEGAL_DESC` validation | §11-H3 (24-00941844) |
| Owner Lease Xref bulk load broken / replace-existing not working | Design Studio loader defects | S3 Cluster H (22-00823022, 22-00672538) |
| Bulk edit / import-to-owners **times out** on big MGs | Too many lines pulled into edit screen | §12-I (22-00823946, 23-00884583) |

## 9. Cluster F — DOI Worksheet / DOI Setup Excel-import decimal failures

**F1 — Small decimals dropped.** SF `23-00924182` "PRD A1 TEST - DOI Worksheet not all decimals are importing" (Software Defect, Closed 2026-06-30): importing the worksheet left 50+ owners' NRI blank. Resolution (verbatim): *"Added a property 'NRIDecMasked' in DSTGDoDetailDoEXT.cs which controls the precision configuration for small number and set it on Import and export excel methods in DOIWorksheet Controller."* ADO **#1625151** "CNR - Web Grid Excel Loader in DOI Worksheet Fails On Small Decimals (23-00924182)" (Closed, tag `NOV 2022.04`): *"The web grid excel loader fails on decimals that are too small"*; WI notes the DB table supports 10 decimal places and the same loader also serves DOI Setup → DOI Owners → Actions → Import From Excel. Follow-up `24-00951251` "PRD A1 Hotfix - DOI Worksheet small decimals not importing" resolved as *"resolved in Camino January 24 Hotfix"* (fixed-in **INFERRED**). Legacy twins: `22-00676543` / `22-00559779` "NRIs Loading as 0 With Import From Excel" (MRO).
**Recipe:** confirm the client build has the NRIDecMasked fix (G3 check first). Workaround pre-fix: format NRI cells as text/expanded decimals (no scientific notation) before import; spot-check the smallest decimals after load.

**F2 — Precision-config bypass.** ADO **#1727280** "25-01012855 - DOI Worksheet Ignores PRECISION set in global configurations" (Closed): worksheet accepted 10 decimal places while the global `PRECISION` config (core default 8) rounds DOI Setup to 8 — bulk-edit save now rounds per config. Legacy anchor `22-00676548` (MRO) — DOI Detail + Bearer Group grids allowed import/manual input past precision config.
**Recipe:** mismatched NRI totals between Worksheet and Setup after imports → check `PRECISION` global config and the build's #1727280 status; re-foot after rounding.

## 10. Cluster G — Bulk Edit/View grid defects

**G1 — Missing Owner Sub column.** `23-00924854` "Build 2023.04 - UAT - DOI Worksheet Bulk Edit/View missing owner sub" (**Release Collateral Damage**): upload leaves Owner Sub blank → validation fails on return to the normal screen. Classify G3/version; cite the case; interim: key Owner Sub on the normal screen after upload.
**G2 — Worksheet→live gaps.** `22-00830146` "TEGs not importing to live table from DO Worksheet" (closed No Action Taken): TEGs loaded to the worksheet but never imported to live. If seen again: verify the TEG rows in the workspace tables vs live `DONL_*`, then escalate with both row sets (this case died without a fix — don't assume resolved).
**G3 — "Bearer Group does not exist" import quirk.** `25-01055290` "DOI Import UBT" (Customer Cancelled) — description shows the loop: import errors that GWI Bearer Group 1 doesn't exist; deleting it errors that non-working interests need a bearer group; **re-keying the same value over the imported cell** then saves clean. Known workaround, not a data problem. Duplicate: 25-01055296.
**G4 — Misc anchors:** can't type/paste Agreement Number in DOI Setup Bulk View/Edit (22-00676537, Software Defect); "Value N exceeds maximum defined length" adding NRI via Bulk Edit (22-00698356, Customer Error — column-length data issue); External FT import spreadsheet requesting extra fields (22-00672533); External FT shouldn't require DO Type/Maj Prod on Bulk Edit (24-00937029, Closed-Deferred); DOI History Search multi-value filter breaks Excel export (22-00641176, Software Defect).

## 11. Cluster H — External loaders & data-copy requests

**H1 — Datayank (PRD→UAT data copies).** `26-01068062` "Datayank new PRD Business Associates for insert into UAT" (App Config, Closed 2026-03-20). Resolution (verbatim): *"Created the necessary scripts to add required BA data. Ref ADO WI 1778563 for the scripts."* ADO **#1778563** (project **QuorumServices\Managed Services**, Resolved) holds the reusable scripts.
**Recipe:** these are Managed-Services scripted loads, not defects — reuse the WI 1778563 script pattern; verify BA keys don't collide in the target env.
**H2 — Mineral Answers.** `26-01112343` "Import Data from Mineral Answers" (App Config, Closed 2026-08-14): client asked how to load Mineral Answers BA data; guidance was the standard BA loader used by other clients — explicitly *"not the A&D module"* (case description). No defect; route as a services/how-to with S3's BA-interface knowledge.
**H3 — Well import validation.** `24-00941844` "Well Import Load Issue" (App Config). Resolution (verbatim, condensed): templates loaded clean except one failing *"Legal Description is required if in-house operated"*; fix was *"to disable the registered SQL `SELECT_VALIDATE_WC_LEGAL_DESC` by adding 'AND 1=-1' to the end."*
**Recipe:** the disable-a-registered-SQL-with-`AND 1=-1`" pattern is the standard soft-off switch for optional validations — record which Reg SQL was touched in the case.
**H4 — Owner Lease Xref loader** (22-00823022 "Bulk Edit load does not work", Software Defect; 22-00672538 "Importing Owner Lease Xref to Replace Existing Content Not Working", Software Defect) → deep dive lives in **S3 Cluster H**; keep anchors here for routing.
**H5 — Loader security:** "Security Role Unable to Access Bulk Modify Loader" (22-00676439, Customer Error) and "Error on Bulk Modify Loader" (22-00676492, Customer Error) — check loader security objects/roles before debugging the loader.

## 12. Cluster I — Bulk-operation performance

`22-00823946` and re-open `23-00884583` "System Time Delays / Maintenance Bulk Edit / Import to Owners / time-outs selecting funds" (both Software Defect): an MG with too many lines (case text: *"it appears to be too many lines of data to pull into the edit screen before time out"*) can't get past the New Transaction screen. Workaround: split the maintenance into smaller MGs / fewer owners per transaction; escalate with the MG number and row counts if splitting is unacceptable. Related mass-transfer chunking fix: ADO #1651746 (see Upgrade skill §7-D3).

---

## 13. Known ADO Items (both sections)

| ADO WI | Title (condensed) | State | SF anchor | Notes |
|---|---|---|---|---|
| #1622910 | "No default market rep found" warning on converted dummy DOIs | Closed 2025-10-22 | 23-00918228, 26-01064806 | reworded, REV-only; Robot RN 2026.04 (INFERRED fixed-in) |
| #1739512 | Invalid combining-interest warnings (RADOITRW58/59) | Closed | 25-01027179 | part of #1622910 family |
| #1723387 | Error on JIB DOI MG approve (endpoint) | Closed | — | `EndpointInfoResolver` MT config; related #1732619 DOINTXWRK failure |
| #1397799 | AFE_SYNCDO fails to launch on JIB DOI XFER | Closed | — | MergedToDevelop; 2022.04 retest tag |
| #1625151 | Web grid Excel loader fails on small decimals | Closed | 23-00924182 | tag NOV 2022.04; also DOI Setup import path |
| #1727280 | DOI Worksheet ignores PRECISION global config | Closed | 25-01012855 | bulk-edit save rounds per config |
| #1687869 | Bearer bulk edit date breaks → PK violation | Closed | 24-00965362 | see Upgrade skill §7-D5 |
| #1778563 | Datayank PRD BAs → UAT (scripts) | Resolved | 26-01068062 | QuorumServices\Managed Services |
| S4 set | AP055/GL025/JB020/AFEEXTIMP DOI-validation bugs | — | — | see SKILL_ADO_QDO_DivisionOrder_Transfers.md |

## 14. Diagnostic SQL (label `NOT YET RUN` without a live metadata connection)

```sql
-- B1: does the backdate picklist include JIB? (registered SQL text)
SELECT * FROM <registered_sql_table> WHERE SQL_ID = 'SELECT_DONL_DO_PROP_BACKDATE_PICK';  -- verify reg-SQL store name on build

-- B2: tier-edit configs
SELECT * FROM <global_config_table> WHERE CONFIG_NM IN ('CAN_CHANGE_TIER_VALUE','CAN_CHANGE_TIER_JIB_VALUE','PRECISION');

-- D3: JIB offset staging vs BA screen
SELECT TOP 25 * FROM DSTG_SAP_JIB_OFFSET ORDER BY 1 DESC;   -- compare against BA JIB-netting values

-- F1: post-import decimal audit — smallest NRIs that should exist
SELECT TOP 25 PROP_NO, TIER, FROM_BA_NO, NRI_DEC
FROM DONL_DO_DETAIL WHERE NRI_DEC IS NULL OR NRI_DEC = 0;    -- candidates for dropped-decimal import rows

-- H3: the soft-off validation pattern (find validations disabled with AND 1=-1)
SELECT SQL_ID FROM <registered_sql_table> WHERE SQL_TEXT LIKE '%AND 1=-1%';
```
*(Table names from case/ADO text; verify against the client DB and run SELECTs in a transaction first.)*

## 15. Expected-Behavior / FAQ

- **"Why must a JIB Offset owner be 5-Pay Regardless?"** JIB netting needs the owner payable so revenue can offset billing; minimum-suspense thresholds would strand the offset. Small checks are the known trade-off (23-00878496, 26-01094960). Flag as Enhancement if the client wants threshold-aware netting.
- **"Can we backdate a JIB deck?"** Yes — it's a picklist configuration (§4-B1), not a product limitation.
- **"JIB decks don't show in Maintenance Group Creation."** Three closed no-action cases (26-01087387, 26-01083172, 26-01069321) — verify DOI type filters, approval status, and effectivity dates before logging a defect.
- **"Import from Excel says my Bearer Group doesn't exist."** Re-key the flagged cell(s) over the imported value and save (25-01055290) — known grid quirk.
- **"Fatal Error warning on JIB transfer"** — cosmetic on JIB DOIs; see §3-A before alarming the client.
- **Cost-center renumbering / code standards** questions are usually process questions (Training) — 26-01098849, 26-01092858, 23-00913910.

## 16. Escalation

- JIB warning/message defects and worksheet-import defects: `QuorumSoftware\Engineering\Revenue\Committed Backlog` or `...\Maintenance\Upstream\Professional Services\Revenue`; include the exact warning code (RADOITRW58/59), MG number, DOI type (JIB/REV), and build.
- Endpoint/launch failures (§7-E2): environment/MT config first — attach the `EndpointInfoResolver` log block from `Quorum.Upstream.QDO.Application.MiddleTier` before any code escalation.
- Data loads (Datayank/Mineral Answers): route to Managed Services (`QuorumServices\Managed Services`), citing WI #1778563 as the script precedent.
- Financials crossover validations (AP055/GL025/JB020): escalate per **S4** to `QuorumSoftware\Engineering\Financials`.

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
