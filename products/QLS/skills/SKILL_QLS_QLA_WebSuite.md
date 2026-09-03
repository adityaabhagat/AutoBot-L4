# SKILL: QLS — QLA (Land Administration Web Suite)

**Version:** 1.0 | **Created:** 2026-09-03 | **Product:** My Quorum Land (QLS) — `Product_list__c = 'My Quorum Land'`
**Scope:** Coverage-plan group **#9 QLA web suite** (384 cases, 134 actionable): QLAE (external/broker portal), QLAI (internal review app), QLARIS (client-branded QLA instance, e.g. XTO), agreement/payment push QLA→QLS, QLA payments → SAP/AFIS, code-table sync, validation rules (BusinessRules.xml), documents (QLATODOCMG), projects/tasks/contacts/parcels, access & environment issues.
**Companion skills:** `SKILL_QLS_QGIS_Mapping.md` (QLA parcel polygen), Payments & Financial-Export group skills (AFIS/SAP downstream once the payment is *in* QLS).
**DB:** Oracle. QLA runs its own schemas **`QLAI`** / **`QLAE`** beside QLS **`LIS`**; interface PL/SQL packages `QLA_INFC_QLS` / `QLA_INFC_QLS_CORE` / `QLA_INFC_PMT_CORE` live in the QLAI schema.

> **Evidence base:** 75 distinct SF case headers scanned across 3 validated LIMIT-25 pages (category `QLA - *` actionable newest-first ×2 + `%QLA%`-subject sweep outside the category), Resolution/Description deep-dives on 31 cases, and 15 ADO work items. Every claim cites a verbatim SF case number and/or ADO ID. Fixed-in builds **INFERRED** from hotfix tags unless release-note-confirmed.
> **PII:** individual names/emails/phones redacted; 3-letter client prefixes retained.

---

## 1. Quick Triage Table

| Symptom | Likely cause | Go to |
|---|---|---|
| Submit QLA→QLS fails "All Lessors must have a Valid Usage Type" though BAs look valid | Duplicate-Tax-ID BA resolves to the wrong `PRTP_ADDR_ID` (usage type not in configured list, e.g. 'P' instead of 'BI'); valid list lives in **BusinessRules.xml** (repo `Quorum.QLA.Batch`) | §4 A |
| "Name and Tax ID Do Not Match QLS" on valid BAs | Same duplicate Tax-ID / BA-address family; hotfix Sept 2025 (SF 25-01000372) | §4 A |
| Null Tax ID error in QLA | Sept 2025 hotfix (SF 25-01023016) — tax-ID sanitization family | §4 A |
| BA Suffix flips to a different `PRTP_ADDR_ID` after Save | First address record with same Tax ID always used (ADO **1739926** CNX; fixed by **1699827** in 2022.04) | §4 A |
| Copy Agreement carries the old BA's eSuite ID → wrong participant lands in QLS | Copy Agreement defect (ADO **1406963**, `QLA_INFC_QLS.prv_Agmt_AddParticipation()` line 2852) | §4 A |
| "Lessor Detail: Tax ID field is required" but client doesn't collect Tax IDs | Config `QLA_AGMT` / `SKIP_TAX_ID_TYPE_CODE_CHECK = 1`; NTR = "No Tax Reporting Required" type must be synced to QLA (ADO **1374015**) | §4 A |
| New required-document validation blocking submits | Client `BusinessRules.xml` — e.g. exclude a document type from the rule (SF 26-01085822 COP) | §4 A |
| Push to QLS errored but QLS agreement number was already assigned; re-submit says "agreement number already exists" | Known half-push behavior — QLS number reserved before validation completes (SF 24-00940061) | §5 B |
| Submit throws ORA-06502 "character string buffer too small" at `QLAI.QLA_INFC_QLS_CORE` + `LIS.TAR_ALL_AGREEMENTS` trigger | Interface-package/trigger defect family (ADO **1418332** history) | §5 B |
| Fields user filled in QLA blank after push to QLS | Interface mapping gap (SF 22-00821099; Software Defect) | §5 B |
| Renewal agreements: payment never lands on existing QLS agreement | v17 refactor dropped renewal payment integration (`ImportPaymentToQLS` / DB fn `PR_PYMT_INFCTOQLS`) — restored per ADO **874259** (CRI) | §5 B |
| QLA payment stuck; no SAP DOC # ; `lis.sap_je_account_gl` GL = 000… and `SAP_AP_OPTIONAL` NULL | GL derivation on the QLA→QLS payment interface (SF 26-01082073); check `AFIS_GL_CROSS_REF` | §6 C |
| QLA payments errored in SAP for one company code | Business partner not extended to that company code — restage after BP extension (SF 26-01081107) | §6 C |
| Unit Type (`REF_KEY_2`) stopped flowing to SAP checks | Check-mapping/interface config regression (SF 24-00981380) | §6 C |
| Payments from QLAi erroring out in AFIS | Recent GL config change on QLA side — roll back (SF 24-00982758) | §6 C |
| 6 duplicate payment workflows per payment | Payments created without saving one at a time (Aug'24 HF era defect; SF 24-00983707) | §6 C |
| Check voided in myQuorum/QLS but QLA still shows "Paid" | Void status not synced back to QLA (SF 23-00904713, Software Defect) | §6 C |
| User who lacks payment rights submitted a QLA payment | Authorization gap defect (SF 24-00953401) | §6 C |
| Payment type missing from Manual Payment / Payment Option screens | Payment-type config scoping (`QCODE_PAYMENT_TYPE` sync + per-screen config; SF 25-01050535, 25-01056749, 26-01094902 "add Extension to all ROW types" script) | §6 C |
| Code table sync skips a table / ORA-01400 during sync | `QLA_CODE_TABLE_SYNC` procedure list gap (e.g. `SYNC_QCODE_PRIORITY` never called) or bad source rows (`QCODE_ARRG_TYPE.SUBJ_CD` NULL) (SF 24-00990276) | §7 D |
| Users can't create payments in QLAI (privilege looks right) | Privilege row associated to QLAE instead of QLAI (`user privileges ID 3`; SF 24-00990265) | §8 E |
| QLAi approval/notification emails not sent | DB→SMTP ACL: allow `LIS` and `ESUITE`/QHEC schemas to reach SMTP server (SF 24-00982803, myQuorum-Cloud WI 1692625; also SF 24-00989373) | §8 E |
| "Server Error" opening QLA | Storefront notification footer defect — removed Apr'25 maintenance (SF 25-01015252); also "File Not Found" env config (SF 25-01036850) | §8 E |
| Manage Agreements view returns no records: "Invalid filter for an IN type query" | Hotfix collateral in `Quorum.QLA.Shared.DAL` filter builder (ADO **1406821**) | §8 E |
| QLA extremely slow opening agreements/payments | Perf family ADO **1354759** / **1418332** (CRI); check QLA.App.Web assembly refs + DB timing | §8 E |
| Multiple QLA docs with same QLS doc type collapse into one Date & Doc record | QLATODOCMG interface defect (ADO **1374022**, 2020.09/2022.04/2023.04 HF) | §9 F |
| Rejected-then-resubmitted agreement's setup copy classed as "Trailing", never feeds QLS | Doc-class derived from agreement stage (ADO **1591856**, open P2) | §9 F |
| "Unable to create the folder for storing the Index files" on submit | LPR index-folder path config; agreement still pushes (ADO **1322148**) | §9 F |
| QLAI project invisible in QLAE | Tasks must be enabled + ≥1 task assigned to the QLAE brokerage firm (SF 25-01047059) | §10 G |
| Can't change brokerage firm / can't save after changing landman once a task exists | Task-linkage locking (SF 25-01051262, Application Configuration) | §10 G |

---

## 2. Concepts & Vocabulary

- **QLA** = Quorum Land Administration web suite, front-end for land agreement intake ahead of QLS:
  - **QLAE** — External app for brokers ("brokerage firms"): create agreements, attach documents, Validate, Submit → QLAI.
  - **QLAI** — Internal app: assign, review, approval workflow, then **Submit to QLS** ("push"/"interface").
  - **QLARIS** — client-branded QLA deployment name (XTO); **QLAi/QLAe** casing varies in case subjects; **QLAD** appears for manual-payment agreement allocations (SF 25-01049664).
- **Agreement flow:** QLAE → QLAI → QLS. Stages: New / In Progress / Submitted to QLS / Interfaced. Push is executed by PL/SQL packages **`QLAI.QLA_INFC_QLS`** and core **`QLA_INFC_QLS_CORE`** (payments: **`QLA_INFC_PMT_CORE`**); a QLS agreement number is assigned during interface. QLS-side trigger **`LIS.TAR_ALL_AGREEMENTS`** fires during insert.
- **Code-table sync:** QLA keeps local copies of QLS code tables (`QCODE_*` in QLAI schema). The sync job runs `ESUITE_QAPA.QLA_CODE_TABLE_SYNC[_QAPA]` procedures (`SYNC_QCODE_AGMT`, `SYNC_QCODE_PRTP_ADDR`, `SYNC_QCODE_PAYMENT_TYPE`, … full list in SF 24-00990276). BAs surface in QLA as participants from `QCODE_PRTP_ADDR` (+ `QCODE_PRTP_ADDR_USAGE_RLTN` usage types); chosen participants stored in `QCTRL_AGMT_PRTP` (`QLA_ID`, `PRTP_ADDR_ID`, `PRTP_KEY_EXT`).
- **Validation rules:** client-specific **`BusinessRules.xml`** (repo `Quorum.QLA.Batch`) — required docs, valid lessor usage types (e.g. only `BI`), tax-ID rules. Config keys like `QLA_AGMT.SKIP_TAX_ID_TYPE_CODE_CHECK` gate individual validations.
- **Payments:** QLA payments push to QLS financials and onward to SAP (`lis.sap_je_account_gl`, `SAP_AP_OPTIONAL`, `AFIS_GL_CROSS_REF`, `REF_KEY_2` check field) or AFIS/Upstream AP. Approval workflow with email notifications.
- **Documents:** files attached in QLAE/QLAI interface to QLS Date & Document records; the QLS batch process **`QLATODOCMG`** ("Upload QLA Docs to Documentum") moves/associates the physical files.
- **Repos:** `Quorum.QLA.Web` / `QLA.App.Web` (UI), `Quorum.QLA.Shared` (DAL), `Quorum.QLA.Batch` (BusinessRules.xml, jobs). Admin console: `/Modules/Admin/admin.aspx` on the QLAI site (ADO 1678544).

---

## 3. Decision Tree

```
Validation error on Validate/Submit?
├─ Usage Type / Tax ID / BA identity → §4 A (duplicate PRTP_ADDR_ID family — run the §11 join FIRST)
├─ Required document/type → §4 A BusinessRules.xml (config, not code)
└─ Field-required rules client wants off → §4 A (SKIP_* configs; else BusinessRules.xml edit)

Push QLA→QLS failed?
├─ ORA-xxxx from QLA_INFC_QLS_CORE / TAR_ALL_AGREEMENTS → §5 B (defect family; capture full ORA stack)
├─ Number assigned but agreement stuck "In Progress" → §5 B half-push (24-00940061)
├─ Data missing on the QLS side after push → §5 B mapping gap (verify field list, then ADO)
└─ Renewal/payment missing on existing QLS agmt → §5 B (ADO 874259)

Payment problem?
├─ Stuck before QLS/SAP (no DOC #) → §6 C GL derivation (sap_je_account_gl / AFIS_GL_CROSS_REF)
├─ Errored in SAP/AFIS → §6 C (BP extension, GL config rollback)
├─ Wrong/missing field on check (REF_KEY_2 etc.) → §6 C mapping
├─ Duplicate workflows / status not syncing (void) / unauthorized submit → §6 C defects
└─ Payment type absent from a screen → §6 C config scripts

Sync/code-table drift QLS→QLA? → §7 D
Access, emails, errors opening QLA, slowness? → §8 E
Documents wrong class/collapsed/missing? → §9 F
Projects/tasks/contacts/parcels? → §10 G
```

---

## 4. Cluster A — Validation & participant identity (the biggest family)

**A1 — "All Lessors must have a Valid Usage Type" (APA/APAL; SF 24-00986193).**
- **Root cause (CONFIRMED, ADO 1699827):** when one BA (same Tax ID) has **two `PRTP_ADDR_ID`s** (e.g. 244066 usage `P`, 135353 usage `BI`), the interface picks the first record regardless of which ID the user selected. If that record's usage type isn't in the configured valid list, the submit fails. Valid usage types are configured in **BusinessRules.xml** in `Quorum.QLA.Batch` (APA had only `BI`).
- **Fix:** code fix hotfixed 2022.04→2024.10 (tags, INFERRED); Round 2 (ADO **1732448**) confirmed remaining reports were envs missing the QLA patch or genuine data (address IDs truly lacking a valid usage type). SF resolution: "August '25 2023.04 HF".
- **Workarounds:** add the extra usage type to BusinessRules.xml, or pick a participant whose usage type matches; long-term: cleanup so each Tax ID maps to one BA address record.
- **Verify with the §11 participant join before touching anything.**

**A2 — Same underlying defect, other costumes:**
- **BA Suffix switching after Save** (SF 25-01017620 CNX, closed-deferred; ADO **1739926**): picklist selection 9000328900 saved but 9000300001 (first `prtp_addr_id`) displayed/used. Fixed by the 1699827 change in 2022.04 — confirm client consumed the QLA code, else data-cleanup workaround (one Tax ID ↔ one BA address).
- **Copy Agreement carries eSuite ID** (ADO **1406963**, AST): copying a submitted agreement kept the source BA number; broker's new Contact has no eSuite ID so the *old* BA went to QLS via `QLA_INFC_QLS.prv_Agmt_AddParticipation()` (line 2852 anchor). Fixed: copy blanks the eSuite ID.
- **"Name and Tax ID Do Not Match QLS"** on certain BAs (SF 25-01000372) — resolved via Sept 2025 hotfix (INFERRED same identity family).
- **Null Tax ID issue** (SF 25-01023016, Software Defect → Sept 2025 Hotfix).
- **"Lessor Name must have a unique Tax ID"** validation blocking legitimate shared Tax IDs (ADO **1678544**): remediation was sanitizing Tax IDs in the QLS master table and re-selecting lessors so QLA picks up the fresh code-table copy.

**A3 — Turning validations off (config, not code):**
- Tax-ID-required: set config **`QLA_AGMT` / `SKIP_TAX_ID_TYPE_CODE_CHECK = 1`**; the `NTR` ("No Tax Reporting Required") tax-ID type is a core code that must be synced into QLA to be selectable (ADO **1374015**, WMN).
- Required-document rules: edit client `BusinessRules.xml` — e.g. COP excluded the "Evidence of Bonus Consideration" document type from New-Lease requirements (SF 26-01085822 resolution).
- Tax ID Type not displaying / defaulting to SSN in Participant Selector (ADO **239302** HEC): only `TAX_ID` transfers via `QLA_INFC_QLS_CORE`/`QLA_INFC_PMT_CORE`; grid fills tax type from description match against `QCODE_TAX_ID_TYPE` — sync gaps show as wrong default.

---

## 5. Cluster B — Agreement push QLA→QLS

- **Half-push / orphaned QLS number (SF 24-00940061, Software Defect):** validation error during submit did **not** stop the push; QLS number was assigned, agreement never reached "Submitted to QLS", stayed "In Progress"; after fixing data, resubmit blocked by "agreement number already exists". Triage: locate the reserved number in `LIS.ALL_AGREEMENTS`, complete or clear the stub, then resubmit. (Customer ask on record: don't assign the number until validation passes.)
- **ORA stack on submit (ADO 1418332 history, CRI):** `ORA-06502: character string buffer too small` at `QLAI.QLA_INFC_QLS_CORE line 688` + `ORA-01403 no data found` at `LIS.TAR_ALL_AGREEMENTS line 1250` (`ORA-04088` trigger failure) — capture the full stack; interface package and QLS trigger versions must match build.
- **Fields not auto-populating in QLS after push** (SF 22-00821099, Software Defect, Additional Parties category) — field-mapping gap; enumerate exact fields, then search ADO for the mapping item before writing a bug.
- **Renewals (ADO 874259, CRI):** v7 logic (`AF_DataContext.OnAfterAgreementStateChange` → `AfterImportingToQLS` → `QLAEntityExtensions.ImportPaymentToQLS` → DB fn `PR_PYMT_INFCTOQLS` + cross-reference insert) was deliberately dropped in the v16+ refactor; renewal submits then skipped payment/document integration to the existing QLS agreement. Restored via maintenance — if a client's renewal payments vanish, check their build against this item.
- **Subdivision/prospect errors on QLAE (SF 25-01047072):** resolved as configuration — "updated configuration to show all previous prospects".
- **Agreement interface logic corrections during upgrades** (SF 24-00939215 "Updated QLA to QLS Agreement Interface Logic", 24-00942189 "Not Always Requiring User to Map to BA", 24-00942399 "Payment Transaction Details Cannot be Edited in Initial Stage") — upgrade-project config/metadata deltas: compare client BusinessRules.xml + interface package version to core before treating as defects.
- **Duplicate menu entry "NEW AGREEMENT" post-go-live** — regression from latest hotfix (SF 24-00962290); treat as G3.

---

## 6. Cluster C — QLA payments → QLS / SAP / AFIS

- **No SAP DOC # (SF 26-01082073, Software Defect):** manual payments pushed QLA→QLS for one corp; `lis.sap_je_account_gl` populated with **zeros** and `SAP_AP_OPTIONAL` NULL → SAP integration rejects. `AFIS_GL_CROSS_REF` was correct and the front-end derived the right GL on payment-type selection — fault is in the interface's GL derivation for that path. Compare against a working payment (case reference `FT_KEY 117298`).
- **SAP company-code errors (SF 26-01081107):** payments error because Business Partner not extended to company code (0745 in case); after BP extension, **restage/reprocess** the payments. Data/master-data issue, not code.
- **REF_KEY_2 / Unit Type stopped flowing to SAP** since a date (SF 24-00981380, AC): check-mapping requirement; compare interface config before/after the date it stopped.
- **AFIS errors from QLAi payments (SF 24-00982758):** caused by GL additions made on the QLA side in another ticket; rollback restored function. Lesson: recent QLA GL config changes are the first suspect.
- **Duplicate workflows ×6 per payment (SF 24-00983707, Software Defect, Aug'24 HF era):** creating multiple payments without saving each one individually spawned duplicate approval workflows. Field remediation used: duplicate each payment, SAVE each, delete the duplicated payment-workflows.
- **Void not syncing back:** check voided in myQuorum/QLS but QLA status stays "Paid" (SF 23-00904713, Software Defect).
- **Unauthorized user could submit a payment** (SF 24-00953401, Software Defect) — authorization enforcement gap; pair with §8 privileges when triaging.
- **Check-form rendering:** Depository Bank info incorrectly pulled into Check Form for payees with Direct Pay/Check setup — "Need to Update Check form to account for Payees with Bank info" (SF 25-01056550, Software Defect). Check Number field greyed in Manual Payment Setup — fixed by hotfix (SF 24-00953773).
- **Payment-type availability is config:** payment types are synced (`SYNC_QCODE_PAYMENT_TYPE`) then scoped per screen/agreement type. Recurrent asks: missing type on Manual Payment screen (SF 25-01050535 XTO), removing international types / reducing billing list (SF 25-01056749), "Wire" transaction type disappeared (SF 25-01054208), new Extension type only on existing agreements — fixed by script adding Extension to all ROW types (SF 26-01094902), Bill Intercompany option missing in TST (SF 25-01050597).
- **Approval routing:** "Payment Approval/Routing Issue" (SF 26-01101073) and "Modifying Approval Rules" (SF 25-01037260, Software Defect) — approval-rule maintenance is config; rule-edit failures were defect-fixed.
- **Downstream note:** duplicated 1099-S report lines when one QLA payment ties to multiple agreements (SF 26-01093285) and QLARIS invoice unable to post to SAP (SF 26-01082284) route to the Payments/Financial-Export skill once data is in QLS.

---

## 7. Cluster D — Code-table sync QLS→QLA

- **Anatomy (verbatim log in SF 24-00990276):** the sync runs `QLA_CODE_TABLE_SYNC.SYNC_QCODE_*` procedures in sequence (AGMT, SUBJ, ARRG_TYPE, BROKERAGE_FIRM, ORG, COMPANY, COST_CENTER, PRTP_ADDR, PAYMENT_TYPE, GL_CROSS_REF, MAP_STAT, …). Two failure modes:
  1. **Procedure missing from the call list:** client-schema proc `ESUITE_QAPA.QLA_CODE_TABLE_SYNC_QAPA.SYNC_QCODE_PRIORITY` was never called → `QCODE_PRIORITY` stale unless manually scripted (the case's ask: call it like the others).
  2. **Bad source rows abort one table:** `SYNC_QCODE_ARRG_TYPE` failed `ORA-01400: cannot insert NULL into ("QLAI"."QCODE_ARRG_TYPE"."SUBJ_CD")` at `ESUITE_QAPA.QLA_CODE_TABLE_SYNC_QAPA line 76` — fix source data in QLS, re-run.
- Sync timestamp shows in QLA Admin ("Last code table sync"); connection string points at the QLAI schema (`USER ID=QLAI`).
- Stale code tables are the hidden cause behind §4 tax-type defaults and §6 payment-type availability — always check sync recency before deeper triage.

---

## 8. Cluster E — Access, environment, errors & performance

- **Privileges bound to the wrong app:** "UNABLE TO CREATE PAYMENTS IN QLAI UAT" — user-privilege row (ID 3) was associated with **QLAE instead of QLAI** (SF 24-00990265). Login failures for some users (SF 24-00987144), generic "Unable to Access QLA" (SF 24-00988953), and "QLS - User setup" (SF 26-01066952) are the same admin family: verify the user exists in the right app (QLAE vs QLAI) with synced brokerage/role rows.
- **Notification/approval emails not sending:** DB-originated SMTP was blocked — Cloud Ops had to allow the `LIS` and `ESUITE`* schemas to access the SMTP server (SF 24-00982803; myQuorum-Cloud WI 1692625). Same symptom at 24-00989373 ("QLA Notification emails aren't working").
- **Errors opening QLA:**
  - "Server Error … Accessing QLA Application": Storefront Notification **footer** malfunction; footer removed in Apr'25 maintenance (SF 25-01015252).
  - `QLS_UATA1_QLAe application not working - File Not Found` (SF 25-01036850) — env/deploy config.
  - Hyperlinks lost on pre-upgrade docs in QLAi (SF 25-00999337, Hosting) and QLAi hyperlink issues (SF 26-01084928) — path/URL config after moves.
  - Session timeout complaints in QLARIS = config (`Inactivity in QLARIS Timeout`, SF 26-01065376).
- **Manage Agreements view empty (ADO 1406821, CRI, "Collateral Introduced By Hotfix"):** `{"Message":"Invalid filter for an IN type query"}` from `Quorum.QFC.Core.DAL.NetCoreDALExt.BuildWhereClauseFragment` → `Quorum.QLA.Shared.DAL.QLABaseDALExt.GetRowCountForFilters` → `Ajax_ManageAgreementsService.Get_MA_INTERNAL_ManageAgreementsView`. Needed a QLA code fix **plus** a QLS database change that had been missed — verify both halves deployed. Sibling: Docs-Validated flag displayed inverted (ADO 1396517, referenced in the 1406821 retrospective).
- **Performance (CRI era, ADO 1354759 + 1418332):** QLAE→QLAI→QLS workflow "extremely slow"; first agreement open ~1 min. Investigation spanned missing assembly reference in `QLA.App.Web` vs `QLA.Web` and DB timing. If a hosted client reports this, gather timings per screen + check build parity between the two web apps.
- **View/LPR functionality config:** "Manage Agreements View LPR Functionality" (SF 24-00951192) — LPR (Lease Purchase Report) generation/config; index-folder errors in §9.

---

## 9. Cluster F — Documents

- **QLATODOCMG collapse (ADO 1374022, ENC; 2020.09/2022.04/2023.04 HF):** interface creates Date & Document records, then batch `QLATODOCMG` ("Upload QLA Docs to Documentum") attaches files. Multiple QLA docs mapping to the **same QLS Document Type** all tied to one Date & Doc record. Fix added a field so files link 1:1; interface package + batch both changed ("Change QLA -> QLS package to populate new field").
- **Rejection flips doc class (ADO 1591856, CRI — open P2):** when QLAI rejects back to QLAE, a re-attached setup copy is classed **Trailing** instead of **Original** because class is derived from agreement stage; Trailing docs don't auto-feed QLS pre-submit. Workaround: manually attach the setup copy in myQuorum.
- **Index-folder error on submit (ADO 1322148):** "Unable to create the folder for storing the Index files." during QLAI→QLS submit; agreement pushes anyway, documents don't. There is a separate batch process that can push the QLA docs afterwards. Root: LPR/index folder path config (2021.04 regression, Config tag).
- **File name mangled on upload** (SF 25-01015732, Software Defect — closed "No action taken"): known cosmetic; imported parcel documents failure (SF 23-00916343) — parcel-doc import path, closed-no-response.

---

## 10. Cluster G — Projects, tasks, contacts, parcels

- **QLAI project not visible in QLAE (SF 25-01047059, Software Defect):** visibility requires **tasks enabled and at least one task created and assigned to the QLAE brokerage firm**. This is the confirmed field fix ("enabled tasks, at least 1 task will need to be created and assigned to the QLAE brokerage firm for it to be visable").
- **Task locks agreement attributes:** after creating a task, brokerage firm can't be changed and saves after changing landman fail (SF 25-01051262, Application Configuration) — reassign/complete the task first.
- **Contacts:** "Unable to create a Contact Remark" (SF 25-01050790, AC — remark-type config).
- **Parcels:** QLA parcel polygen/ORA-00904 signature and `QLA_PLY` copy-on-import behavior live in `SKILL_QLS_QGIS_Mapping.md` §4 C (SF 26-01109433; ADO 1659890 enhancement: parcel polygons auto-copied to `QLA_PLY`, orphan cleanup via QLA Sync Attributes).
- **Client metadata:** "QLA Client Specific Metadata" (SF 25-01048060) — client overrides live beside QLS metadata (`<CLIENT3>.QLS.Metadata` repos); always check client BusinessRules.xml/metadata before core.

---

## 11. Diagnostic SQL (Oracle — verbatim from cases/work items)

**Participant / usage-type triage (from ADO 1732448 — run FIRST for any §4 error):**
```sql
select pa.prtp_key_ext, ap.prtp_Addr_id, ap.tax_id, ur.usage_cd
FROM qlai.qctrl_agmt_prtp ap
left join qlai.QCODE_PRTP_ADDR pa on pa.prtp_addr_id = ap.prtp_addr_id
left join qlai.QCODE_PRTP_ADDR_usage_rltn ur on ur.prtp_addr_id = ap.prtp_addr_id
where ap.qla_id = '2591' and upper(ap.prtp_nm) like '%NAME%';
-- >1 PRTP_ADDR_ID for one Tax ID = the §4 A duplicate-identity family
```

**Tax-ID type checks (from ADO 239302):**
```sql
select * from qlai.qcode_prtp_addr where tax_id_type_cd = 'NTR';
select * from qlai.QCODE_TAX_ID_TYPE;
```

**Payment→SAP GL triage (from SF 26-01082073):**
```sql
select * from lis.sap_je_account_gl where ...;    -- zeros in GL columns = interface derivation fault (NOT YET RUN template)
select * from AFIS_GL_CROSS_REF where ...;        -- confirm mapping exists for corp/payment type
-- compare with a known-good payment, e.g. FT_KEY 117298 in the source case
```

**Code-table sync recency / failures (from SF 24-00990276):**
```sql
select * from qlai.QCODE_PRIORITY;                -- stale? SYNC_QCODE_PRIORITY may not be in the call list
-- source-data fix for ORA-01400 during SYNC_QCODE_ARRG_TYPE:
select * from lis.<arrg_type source> where SUBJ_CD is null;   -- NOT YET RUN; identify NULL SUBJ_CD rows in QLS
```

**Half-push stub check (from SF 24-00940061 pattern):**
```sql
select * from lis.all_agreements where agmt_num = '<reserved number>';  -- stub created by failed push?
```

---

## 12. Expected-Behavior FAQ

- **"Why does the agreement get a QLS number before it's accepted?"** — current interface design assigns the number during push even if validation later fails (SF 24-00940061). Known complaint; enhancement-class, not defect.
- **"A rejected agreement's re-attached document became Trailing"** — by design the class derives from agreement stage; product bug filed (ADO 1591856, open). Workaround: manual attach in myQuorum.
- **"Same Tax ID on multiple BA addresses is invalid?"** — it's a *valid* data scenario (engineering: "it is a valid scenario to have the same Tax ID across multiple addresses" — ADO 1739926); the app defect in older builds mishandled it. Cleanup is a workaround, not a requirement.
- **"Broker can't see the project we created in QLAI"** — expected until tasks are enabled and one task is assigned to that brokerage firm (SF 25-01047059).
- **"Payment type X doesn't appear for new agreements"** — payment types are scoped per agreement/ROW type; adding a type to all ROW types is a standard config script (SF 26-01094902).
- **"Can we turn off the Lessor Tax ID validation?"** — yes: `QLA_AGMT.SKIP_TAX_ID_TYPE_CODE_CHECK=1`, and/or use the NTR tax type once synced (ADO 1374015).

---

## 13. Escalation

1. **Config gate first:** BusinessRules.xml (client repo), `SKIP_*` keys, payment-type scoping, privileges QLAE-vs-QLAI, code-table sync recency — the QLA group skews Application Configuration (95 of 134 actionable).
2. **Version gate:** the participant-identity family (1699827/1732448/1739926) and Manage-Agreements collateral (1406821) recur at clients that missed the QLA half of a hotfix — QLA web code and QLS DB scripts ship separately; verify BOTH deployed.
3. **Data gate:** run §11 participant join and GL triage live; DEV-tier results stay INFERRED for PRD claims.
4. **Engineering escalation:** ADO areas `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` / `Quorum\North America\Upstream\Land RnD`; repos `Quorum.QLA.Web`, `QLA.App.Web`, `Quorum.QLA.Shared`, `Quorum.QLA.Batch`; PL/SQL packages `QLA_INFC_QLS(_CORE)`, `QLA_INFC_PMT_CORE`, `QLA_CODE_TABLE_SYNC` (+ client `ESUITE_Q***` variants).
5. **Cloud Ops items:** SMTP ACLs for DB schemas (email), Storefront footer/platform errors, environment removals (SF 26-01095084), hosted URL/hyperlink moves.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
