# SKILL: QRA — eSuite / Owner Web Portal (BA web screens, eSuite API, web availability)

**Version:** 1.0 | **Created:** 2026-09-02 | **Curated by:** Auto-Bot — the L4 issue solver built by Aditya Bhagat
**Source:** Salesforce ALL-history mining, `Product_list__c = 'My Quorum Revenue Accounting'`, `Case_Category__c = 'eSuite'` (255 cases; 60 actionable = 12 Software Defect + 48 Application Configuration, complete actionable set enumerated 2026-09-02) + cross-category subject search (`%esuite%`, `%owner portal%`, `%owner relations%`) + ADO verification (org `QuorumSoftware`).
**Scope:** The QRA "eSuite" layer = the myQuorum **web** tier for owner/BA data — the **Business Associate web screens** (BA005 web equivalent: Addresses/Revenue/Contacts/Documents tabs), the **eSuite/QRA REST API** (`.../EQCU17QRAAPI`, `BusinessAssociateV1`, token endpoints), **web-site availability** (V17 upgrade, post-refresh scripts, Citrix/QCloud sessions), zip/postal **masking config**, and owner-facing **check-detail content**. Client DB schemas are named `<CLIENT>_PRD16UPS_ESUITE_<MODULE>` (e.g. `QRAPF16UPS_ESUITE_QFC`, `PNR_DEV16UPS_ESUITE_QPNR` — SF 22-00661267, 22-00702562).

> **Use when:** the case says eSuite, owner portal, BA web screen, Contacts tab, "web down", V17 upgrade web issues, ESUITE/QRA API errors, zip-code masking, check-detail owner-relations info.
> **Do NOT use for:** platform workflow engine / V2UI / Kendo / POSTWKFL — see `SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md`. Desktop BA005 master-data logic — see `SKILL_QRA_Ownership_MasterData.md`. Check runs/escheat — see `SKILL_QRA_Check_Processing.md`.
> **Routing trap (verified):** the eSuite SF category also collects mis-filed batch cases — LD18 PPN storms, MG flag flips, PUBORGCC — route those OUT (see §Cluster G).

---

## 1. Quick Triage

| Symptom reported | Cluster | First check |
|---|---|---|
| "Factory QCFSDataHelper does not exist" on Save in any BA web screen action (Royalty Payment Type, bank/direct-deposit removal, cost-center delete) | A | Does the client license QCFS? Error only fires for **non-QCFS** clients (CNX, TEP pattern) |
| Zip/postal code rejected in BA web — letters not allowed (UK/foreign), wrong mask applied after switching country | B | `ZIPCODE_MASK_WEB` / `ZIPCODE_MASK_WEB_CAN` global configs — must be NULL, masks live per-country in `SCODE_COUNTRY.ZIP_CD_MASK_WEB` |
| BA web screen loads no data at all on open | B | Client-layer override of `ZIPCODE_MASK_WEB` with literal "NULL" string (ADO 1622309) |
| BA update throws "Tax Type/Tax ID must have an Effective Date To value" after upgrade | C | NULL Effective-To rows in `SCTRL_BA_TAX_ID` from desktop-era entry |
| BA Number not auto-populating on create | C | BA # sequence out of range (set high at QCloud cutover) — reset sequence |
| Cannot save new BA Contact on Contacts tab / no edit rights on Contacts tab | C | Sequence out of sync: `EXEC UTIL_RESYNC_SEQ @tabname = 'SCTRL_CONTACT'` (SF 26-01116091) — not a security setting |
| Cannot rename BA when another BA has the same name (web only) | C | Known defect, fixed in later release, NOT hotfixable to 2022.04 (SF 24-00979262) |
| Web down / can't log in after environment refresh (V17) | D | Post-refresh scripts not (successfully) executed — re-run them (SF 25-01029044) |
| QRA API 500 error `/EQCU17QRAAPI`, eSuite site itself OK | D | API app pool/services didn't come back after weekend maintenance — restart services (SF 24-00945493) |
| ESUITE API endpoints erroring after a package deployment | D | Invalid ESUITE API Web components in the NI package — redeliver package (SF 26-01109316) |
| User sessions closing randomly / new users missing apps | D | Citrix: reset Citrix Workspace per user (25-01004359); publish apps for new users (25-01002539) |
| BA document attach spins forever; docs won't open | E | Document Management naming/size limits; desktop-vs-web warning parity gap (24-00938812); post-cutover = client BA security (25-01022928) |
| PRD comments/attachments missing in cloud test env | E | Conversion scripts (classic→notes, classic→web attachments) not run on that copy (24-00973126) |
| Owner-relations phone/email on check detail stub is stale | F | Dynamic Export definition for the bank check export (e.g. Export ID `WELLSFARGO`) — update definition, delivered via hotfix (25-01024806) |
| LD18 PPNs flooding, MG flags flipped C→P, PUBORGCC failing — filed under eSuite | G | MIS-FILED. Route to PPA / Ownership skills (§7) |

---

## 2. Decision Tree

```
eSuite / owner-web case
│
├─ Error text contains "QCFSDataHelper"?
│   └─ YES → Cluster A. Confirm client has NO QCFS module → known defect family,
│            fixed by isIntegratedQCFS guard (ADO 1718362 / 1644031 / 1783732). Version check.
│
├─ Zip / postal code / address save problem in BA web?
│   ├─ Mask rejects valid foreign zips, or mask "sticks" across country switch → Cluster B (ADO 1702463)
│   ├─ Screen loads empty → client-layer ZIPCODE_MASK_WEB override (ADO 1622309)
│   └─ State/country missing from picklist → GPOL_AREA_STATES / SCODE_COUNTRY row gap (SF 25-01003674, 23-00931451)
│
├─ BA identity data (Tax ID, BA #, Name, Contacts)?
│   └─ Cluster C — mostly data-state (NULL effective-to, dashes in TID, sequence out of sync)
│       fixed by data script or UTIL_RESYNC_SEQ; one true code defect (duplicate-name save).
│
├─ Whole web site / API / session availability?
│   └─ Cluster D — ladder: post-refresh scripts → services/app-pool restart →
│       NI package integrity → SAML/SSO cert → Citrix workspace/user publishing → QCloud outage banner.
│
├─ Documents / attachments / comments in web?
│   └─ Cluster E — naming-convention & warning-parity (attach), client BA security (view),
│       conversion scripts (env copies).
│
├─ Owner-facing check-detail content?
│   └─ Cluster F — Dynamic Export definition change; route calc issues to Check Processing skill.
│
└─ Batch/PPN/MG vocabulary (LD18, PPN, PUBORGCC, market group)?
    └─ Cluster G — mis-filed; route out (PPA / Ownership skills).
```

---

## 3. Cluster A — "Factory QCFSDataHelper does not exist" (BA web save family)

**Signature:** Any save/delete action on the BA web screens (or cost-center delete in eSuite web) throws `Error: Factory QCFSDataHelper does not exist`; the change is not persisted (re-query shows old value). Same action works in desktop BA005. Only occurs for clients **without** the QCFS product/module (CNX, TEP confirmed; CORE_SUP could not reproduce because it has QCFS).

**Root cause (CONFIRMED):** eSuite web validation/lookup code calls the QCFS data helper without an `isIntegratedQCFS` guard. Dev comment on ADO 1708874: "Very likely related to this recent QCFS change, where this new functionality was not properly added behind an isIntegratedQCFS check" — `Quorum.ESuite.Web` PR 103539. A sibling warning variant exists when updating code tables whose registered SQL points at an app layer not configured in the environment: "Could not find the data helper 'QCFSDataHelper' for Code Table ID '21011' and App Layer Code 'ENGSUPS'" (ADO 1694230 — eSuite metadata is shared between upstream and midstream).

**Fix recipe:**
1. Confirm the client does NOT have QCFS. If they DO, this is a different problem — stop.
2. Match the surface: Royalty Payment Type save → ADO 1718362 (SF 25-01002942 resolution: "Updated the validation rule to check if QCFS integrated before executing any open item lookups with the QCFSDataHelper"); bank-account/direct-deposit removal → ADO 1644031 (SF 24-00979256); BA save generally → ADO 1708874; cost-center delete → ADO 1783732 (secondary error `Invalid object Name "UVW_UPS_JETRANSACTIONINQUIRY"`).
3. All four ADO bugs are **Closed** — this is usually a **Version issue (G3)**: check the client's build against the fix delivery; hotfix availability to 2022.04 was constrained (SF 24-00979262: "Resolved in latest release but not able to hotfix back to 2022.04").
4. Interim workaround: make the change in desktop BA005 (works — SF 25-01002942 description).

**Anchors:** SF 25-00999441 (resolution: "Software update to add a check for if QCFS is integrated before making a call to the QCFS data helper"), SF 25-01002942, SF 24-00979256; ADO Bugs 1718362, 1644031, 1708874, 1783732, 1694230; repo `Quorum.ESuite.Web` (PR 103539).

---

## 4. Cluster B — Zip/postal masking & address reference data (BA web)

**Signature:** BA web screen refuses letters/numbers in Zip Code for foreign addresses (England/UK typical); or the mask from the previously selected country keeps applying after switching countries until browser refresh; or the BA web screen loads with **no data**.

**Root cause (CONFIRMED):**
- Design: masking moved from two global configs to per-country. `ZIPCODE_MASK_WEB` and `ZIPCODE_MASK_WEB_CAN` (table `QARCH_CNFG_CTRL`, Key Group `BA ENTITY`) must be **NULL/blank**, with per-country masks in `SCODE_COUNTRY` column `ZIP_CD_MASK_WEB` (Code Table ID 29037). SF 23-00926666 resolution verbatim: "A bug was fixed for the ZIPCODE_MASK_WEB and ZIPCODE_MASK_WEB_CAN global configurations. Both should be set to NULL (left blank) and the masking for each applicable country should be set in SCODE_COUNTRY." Code fix delivered in the **January 2024 hotfix** (SF 23-00926753).
- Sticky-mask variant: validator params don't reset on country switch without page reload — ADO 1702463 (SF ref 24-00987114, MEW 2024.04).
- Empty-screen variant: a client-layer override storing the string "NULL" for `BA ENTITY | ZIPCODE_MASK_WEB` broke BA screen data retrieval — ADO 1622309 (MRO; fix tags `NOV 2023.04`).
- Front-end maintainability gap: `ZIP_CD_MASK_WEB` column not visible in Code Table Value Editor for SCODE_COUNTRY, forcing SQL — ADO 1703813 (walkthrough doc attached to the WI).

**Related reference-data gaps (same triage lane):** BA with US Virgin Islands address not syncing to QLS → "Added US Virgin Islands to GPOL_AREA_STATES" (SF 25-01003674). Missing country code request (SF 23-00931451). German state (Hessen) address handling (SF 25-01003671, Complete-Pending-Delivery).

**Fix recipe:**
1. Read `QARCH_CNFG_CTRL` for Key Group `BA ENTITY`, keys `ZIPCODE_MASK_WEB` / `ZIPCODE_MASK_WEB_CAN` across metadata layers (client layer overrides are the usual culprit — QREP example in ADO Requirement 1832518 documents the metadata check-in shape: Metadata Layer QREP, Value NULL, Value Type String).
2. Set both to NULL/blank at the effective layer; populate `SCODE_COUNTRY.ZIP_CD_MASK_WEB` per country.
3. If client build predates Jan-2024 hotfix (2022.04/2023.04 era), the code fix may be missing — version-check before config-only remediation.
4. Sticky-mask on country switch: confirm build contains fix for ADO 1702463; workaround = refresh browser after changing country.

**Anchors:** SF 23-00926753, 23-00926666, 24-00967184, 24-00970053 ("Zip Code Error"), 24-00973127 ("Zip/Postal Code Error"), 25-01003674, 23-00931451; ADO 1622309, 1702463, 1703813, 1832518.

---

## 5. Cluster C — BA identity data: Tax ID, BA number, name, Contacts

**C1 — Tax ID NULL Effective-To blocks BA update (upgrade migrations).**
Signature: "The Tax Type (SSN) and Tax ID must have an Effective Date To value" on any BA update after moving desktop→web (MEW 2024.04). Root cause: legacy rows in `SCTRL_BA_TAX_ID` with NULL Effective-To; web validation enforces what desktop never did. Short-term per the case itself: script `12/31/9999` into the NULL Effective-To rows; long-term flagged to Engineering for CORE (SF 24-00984139, Root_Cause = Release Collateral Damage). Sibling data fixes: foreign TIDs saved with dashes → "Data script run to remove dashes from tax-ID field" (SF 25-01012358); TIN/SSN display formatting for imported BAs handled by script request (SF 25-01029277).

**C2 — BA number not auto-generating.**
Signature: BA Number field stays blank on create (QCloud). Root cause/fix verbatim (SF 25-01002292): "Reset the BA # sequence to 481486 so the next number is generated accordingly. The sequence was set to a large number during the QCloud go-live cutover." Classify Bad Data (G4), not code.

**C3 — Contacts tab: cannot save / apparent missing edit rights.**
Signature: user reports needing "edit rights" for the BA Contacts tab in eSuite; or new BA Contact won't save. Two verified causes: (a) transaction sequence out of sync — fix verbatim (SF 26-01116091): "Running EXEC UTIL_RESYNC_SEQ @tabname = 'SCTRL_CONTACT'; in PRD fixed the issue by getting the sequences in place on QARCH_TRAN_SEQ" — note the symptom masqueraded as a security question; (b) an over-eager validation, resolved by disabling it (SF 23-00926758, 2023 smoke testing).

**C4 — Duplicate-name save defect (web only).**
Signature: cannot update a BA so two BAs share the exact same name; desktop allows it. Known defect since 22-00831240; "Resolved in latest release but not able to hotfix back to 2022.04" (SF 24-00979262) — fixed-in build **INFERRED** (post-2022.04 release), confirm in release notes before quoting. Related save-blocker: error popping on every SAVE in BA screen → Cluster A's QCFS guard (SF 25-00999441).

**Anchors:** SF 24-00984139, 25-01012358, 25-01029277, 25-01002292, 26-01116091, 23-00926758, 24-00979262, 24-00965407 (BA module access = Training), 25-01006753 (BA005 update message = Customer Error).

---

## 6. Cluster D — Web/API availability: V17, refresh, services, Citrix, SSO

Ordered ladder (cheapest first) — each rung is an anchored past resolution:

1. **Post-refresh scripts.** Web down + can't log in right after an environment refresh: "the post refresh scripts were not executed or were not successfully executed... Re-executed the post refresh scripts and the environment now shows as available" (SF 25-01029044, V17 UBT). Same family: new UBT env missing QLS connections → processes fail (SF 24-00949165); stale connection rows in `QARCH_CTRL_CONNECT_INFO` after host rename (SF 22-00661267).
2. **Service/app-pool restart.** `500 Server Error in '/EQCU17QRAAPI' Application` while eSuite site is fine → "Services were restarted" (SF 24-00945493; repeat of 24-00944578 — a weekend-maintenance recurrence pattern).
3. **Deployment package integrity.** ESUITE API endpoint errors post-delivery → "Previously delivered NI package contained invalid ESUITE API Web components... Updated NI Package with re-packaged ESUITE API Web component resolved" (SF 26-01109316).
4. **Auth chain.** Token retrieval fails with `"error": "invalid_client"` (SF 24-00992555 — closed as Client Managed Infrastructure); SAML cert rotation requests (SF 25-01008143 `Update_TG_SAML_Certificate`); SSO failures for the eSuite web site (SF 22-00868523, no resolution recorded — treat as env/infra).
5. **Citrix/session layer.** Random session closes → "Reset Citrix workspace by user. RCA: NA" (SF 25-01004359); new users missing Citrix apps (SF 25-01002539); Citrix Adobe issue on QCloud (SF 24-00972246); desktop close error `IQConfigSettingValueProvider2` after long-open sessions → fixed in product ("The desktop application now closes successfully after it has been opened for an extended period" — SF 24-00941655 resolution, release-note wording; build INFERRED).
6. **Cloud outage.** Multiple same-day cases (25-01029479 / 25-01029478 / 25-01029506 on 2025-07-09) = QCloud outage — check status before touching config. Env-launch failure tied to Cohesity backup infra: SF 24-00963922.

**Anchors:** as cited inline. Cross-ref: `SKILL_QRA_Platform_Integration_Security.md` for Secure Gateway IP allowlists (SF 25-00999094, 24-00965407) and QPEC/batch infra.

---

## 7. Cluster E — Documents, attachments, comments in the BA web screens

- **Attach spins, never saves (web), desktop shows a warning instead:** BA005 desktop raises a Warning for the same document that the web app silently fails to attach — parity gap; interrogate document **naming convention / special characters / length / size** limits with Document Management in play (SF 24-00938812 — client on Q Document Management; resolution buried in case notes 2024-02-15, treat exact fix as INFERRED).
- **Users can't open BA documents after cutover import:** not a product bug — "Client updated security around BAs and now those users are able to view BA documents" (SF 25-01022928, V17 cutover). Sibling: SF 25-01006866 (Platform).
- **PRD comments/attachments absent in cloud test copy:** "Conversion scripts are required to convert the comments from classic to notes and converts attachments from the classic app to the web app in the upstream app" (SF 24-00973126) — an env-provisioning step, not data loss.

---

## 8. Cluster F — Owner-facing check detail content

**Signature:** Owner-relations phone/email or other header comments printed on the check-detail attachment are stale/wrong; client asks whether IT can change it.
**Fix recipe:** it lives in the **Dynamic Export definition** for the bank's check export — "The Dynamic Export definition for Permian's Wells Fargo check export was updated with the current email address and phone number. This will be included in the June HF" (SF 25-01024806; Export ID `WELLSFARGO` also appears in SF 25-01051609 template-logic change). Config change + hotfix packaging; classify Config (G2).
**Route out:** anything about check *amounts*, voids, escheat, ACH/NACHA → `SKILL_QRA_Check_Processing.md`.

---

## 9. Cluster G — Mis-filed under eSuite: route OUT

Verified examples of `Case_Category__c='eSuite'` cases whose substance belongs elsewhere — check vocabulary before trusting the category:

| Case | Actual topic | Route to |
|---|---|---|
| SF 25-01014296 "LD18 are being created too often" — LD18 PPNs fired on every WI Owner Change instead of only Direct Bearer group changes; fixed on ADO 1723481 (Closed, `...Maintenance\Upstream\Customer Service\Revenue`; tag "not 2026.04 Ups" — fixed-in INFERRED) | PPN trigger logic | `SKILL_QRA_Prior_Period_Adjustments.md` |
| SF 24-00994427 hotfix follow-up to 24-00993889 — MG flags flipped C→P; query pointed at `PONL_DVD_MKT_GRP_DETAIL` instead of `PONL_MKT_GRP_DETAIL`; code fix ADO 1703177 (SGY, tag SDP2504, delivered patch 14 DEC hotfix), WA script (dummy rows in `PONL_DVD_MKT_GRP_DETAIL`/`PONL_DVD_MKT_GRP_HDR`) reviewed on ADO 1703208 | Market-group data chain | `SKILL_QRA_Ownership_MasterData.md` |
| SF 23-00916623 PUBORGCC failing during acquisition CC load — Services script fixed ORG data + UAT refresh | Org/cost-center load | `SKILL_QRA_AcqDisp_Payouts.md` |
| SF 24-00973230 / 24-00973522 eSuite Bank Recon stuck — "User requested to cancel the stuck process from QP045" | Batch process ops | `SKILL_QRA_Check_Processing.md` |

---

## 10. Known ADO items

| ADO | Type/State | Title (verbatim, trimmed) | Note |
|---|---|---|---|
| 1718362 | Bug, Closed | 25-01002942 / 24-00979256 - CNX 2022.04 - Royalty Payment Type Error "Factory QCFSDataHelper does not exist" - BA Web Screens | isIntegratedQCFS guard |
| 1644031 | Bug, Closed | CNXU - 2022.04 - Cannot Remove Bank Account information in Business Associate Web screen | same family |
| 1708874 | Bug, Closed | eSuite (TIPS): Unable to save BA on Business Associate Screen | cause: `Quorum.ESuite.Web` PR 103539 lacked QCFS check |
| 1783732 | Bug, Closed | 26-01081113 - TEP - QCFS Related Error Message Encountered when Deleting a Cost Center in eSuite web | + `UVW_UPS_JETRANSACTIONINQUIRY` invalid object |
| 1694230 | Bug, Closed | When updating a code table, the process is trying to access metadata from app layers not configured... | shared eSuite metadata, warning-only |
| 1622309 | Bug, Closed | MRO - BA Screen not populating w/ data on opening | client-layer ZIPCODE_MASK_WEB override; refs #205040 / PR 58508 |
| 1702463 | Bug, Closed | 24-00987114 - MEW 2024.04 - Zip code and country code issue when trying to save BA in the web with Masking configuration on | sticky mask across country switch |
| 1703813 | Bug, Closed | 24-00987114 - MEW 2024.04 - ZIP_CD_MASK_WEB Column Visibility on SCODE_COUNTRY Web Request | Code Table 29037 column hidden |
| 1832518 | Requirement, Ready for QA | REP - Metadata Check In - BA Zip Code | documents QARCH_CNFG_CTRL / BA ENTITY / ZIPCODE_MASK_WEB / layer QREP |
| 1723481 | Bug, Closed | GEC-25-01014296- LD18 are being created too often | route-out anchor (PPA) |
| 1703177 | Bug, Closed | SGY-24-00993889--Market Groups flipped from complete to pending. | route-out anchor (Ownership); tag SDP2504 |
| 1703208 | Bug, Closed | {SGY} - {QRA} - {To_flip_flags_and_create_dummy_MGs} - Script Review | WA script for 1703177 |

Search ADO by the SF case number first — QRA bug titles routinely embed it (`25-01002942 / ...`, `GEC-25-01014296-...`). Area paths: `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Revenue` and `...\Professional Services` (see QRA_Coverage_Plan §4). All fixed-in builds above are **INFERRED** from tags/patch references unless a release note is quoted.

---

## 11. Diagnostic SQL

Verified-fix commands (ran in a real case):

```sql
-- Contacts tab cannot save / sequence out of sync (SF 26-01116091, verbatim fix)
EXEC UTIL_RESYNC_SEQ @tabname = 'SCTRL_CONTACT';
-- effect: re-seats sequences on QARCH_TRAN_SEQ
```

Verification queries — column names to be confirmed against the client schema via the metadata server before running (**NOT YET RUN**; tables are anchored, exact column names are not):

```sql
-- B: masking config at every layer (table/key group/keys anchored: ADO 1832518, SF 23-00926666)
SELECT * FROM QARCH_CNFG_CTRL
 WHERE KEY_GRP = 'BA ENTITY' AND CNFG_KEY IN ('ZIPCODE_MASK_WEB','ZIPCODE_MASK_WEB_CAN');
-- expected healthy state: NULL/blank at the effective layer

-- B: per-country masks (column anchored: ADO 1703813 — ZIP_CD_MASK_WEB on SCODE_COUNTRY, Code Table 29037)
SELECT COUNTRY_CD, ZIP_CD_MASK_WEB FROM SCODE_COUNTRY WHERE ZIP_CD_MASK_WEB IS NOT NULL;

-- B: state/area sync gap (table anchored: SF 25-01003674)
SELECT * FROM GPOL_AREA_STATES WHERE STATE_CD = '<missing state>';

-- C1: legacy tax rows blocking BA web updates (table anchored: SF 24-00984139)
SELECT COUNT(*) FROM SCTRL_BA_TAX_ID WHERE <effective_to_date_column> IS NULL;
-- remediation pattern from the case: script '12/31/9999' into NULL effective-to rows
```

---

## 12. Expected-Behavior FAQ

- **"Both eSuite zip-mask global configs are blank — is that broken?"** No — NULL/blank is the *correct* post-fix state; per-country masks belong in `SCODE_COUNTRY.ZIP_CD_MASK_WEB` (SF 23-00926666).
- **"Are BA Contacts available through the eSuite/QRA API?"** Asked and answered as a capability/training question on `BusinessAssociateV1` (SF 24-00960970) — check current API docs, not a defect.
- **"Can we get email notifications when a BA changes?"** Enhancement territory — prior request closed Customer Cancelled (SF 24-00947522). Flag `Enhancement`.
- **"Web won't let me do X but desktop BA005 does"** — genuine parity gaps exist (duplicate name §C4, attach warnings §7, QCFS guard §3). Reproduce in both tiers and say which tier misbehaves before classifying.
- **"Environment slow / sessions dropping — is eSuite down?"** Check QCloud status first (three-cases-in-one-hour pattern, 2025-07-09), then Citrix workspace per user, then Quorum-side services.

---

## 13. Escalation

1. Exhaust the ladder in §6 before escalating availability issues; capture the exact URL + app name (`/EQCU17QRAAPI` vs eSuite site) — they fail independently (SF 24-00945493).
2. For BA web defects: reproduce in desktop BA005 too, note client's QCFS licensing, and search ADO by SF case number, then by error string in quotes.
3. Engineering handoff targets: repo `Quorum.ESuite.Web`; area path `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Revenue`; tag pattern `Maintenance: Escalated`.
4. Data-fix scripts (tax-ID dashes, effective-to backfill, sequence resets) go through Script Review WIs (pattern: ADO 1703208).

---

*Evidence: complete actionable eSuite set (60/60 cases enumerated), 25 non-actionable eSuite cases, 25 cross-category eSuite-vocabulary cases, resolutions read for 27 cases, EmailMessage drilled where CaseComments were empty (this org's CaseComment usage is sparse — fix detail lives in Resolution__c + Description + EmailMessage). PII redacted: individual requester/user names omitted throughout; client codes retained for pattern value.*

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
