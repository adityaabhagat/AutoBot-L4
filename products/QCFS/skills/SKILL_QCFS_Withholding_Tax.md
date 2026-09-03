# SKILL: QCFS Withholding Tax — State/Federal Calculation & Remittance

**Version:** 1.0 | **Created:** 2026-09-02 | **Product:** My Quorum Financial Accounting (QCFS / Upstream Accounting) — `Product_list__c = 'My Quorum Financial Accounting'`
**Mined by Auto-Bot — the L4 issue solver built by Aditya Bhagat.** Evidence: all-history SF subject sweep (~131 closed-case rows across withholding/tax/1099/remit pages) + 12 case bodies + 7 ADO work items pulled in full (anchor: Bug 1831243).

> **SCOPE NOTE (read first):** This skill owns the withholding **CALCULATION and remittance** recipes only — the state tax WH engine (AP200 / PA withholding, 2026.04), federal/backup withholding at check write (AP043), and the export of withheld amounts to 1099s (INT1099EXP). **Vendor setup, Tax ID maintenance, and 1099 export basics stay in `SKILL_QCFS_Accounts_Payable.md` clusters G–H** (1099 doubled amounts, AP151/XREF_1099 box overrides, QSTG1099 timeouts, BA/vendor master). **Revenue-side owner state/backup withholding** (batch type 18 on revenue distribution, CW010/CW011 screens) is **QRA**, not QCFS — route there (SF 25-01006246 is `Product_list__c='My Quorum Revenue Accounting'`; ADO Bug 1716410).

---

## 1. Quick Triage Table

| Symptom (verbatim-style) | Likely cluster | First check |
|---|---|---|
| Imported voucher's **state tax WH lines disappear when Validate/Approve clicked in AP055** | §A1 — Bug 1831243 (`ICOFFSET_IND=1` set by import) | Client on 2026.04 pre-hotfix? Check `BATCHVOUCHERGLDISTRIBUTION.ICOFFSET_IND` on WH lines |
| **No WH line auto-generated** when "Post to BU" ≠ header BU / intercompany coding; "property is not on business unit" errors on AP imports & GL MJEs | §A2 — Bug 1832480 (SF 26-01110470) | Fixed July 2026 — 2026.04 Hotfix; confirm build |
| **No WH line when Property is blank** on the GL distribution (allocation / G&A / cost-center-only coding) | §A3 — Bug 1832726 | Post-fix, state derived from Cost Center's property; confirm build |
| **AP055 voucher won't save at all** — business-rule exception naming `AUTO_CREATE_STATE_TAX_WH` | §A4 — Bug 1795333 | Fixed 2026.04: calc skipped gracefully when WH code block unavailable |
| **AP200 screen missing / not visible** after taking the PA withholding enhancement | §B — SF 26-01107186 | Tree metadata updates required with new AP200 screen (2026.04) |
| AP200 state-WH config rows **not replicating from global BU to child BUs** | §B — Bug 1852050 (+DB 1860092/1863368) | `QCTRL_AP_ST_TAX_WITHHOLDING.IDGLOBAL/GLOBAL_IND`; queued for next UPS 2026.04 |
| **Check run did not calculate/deduct federal withholding** for WH-subject vendors | §C — SF 26-01093081 → Bug 1801422 (Single Pay ind ignored on ADPUPLOAD) | Was the invoice imported? Check `SINGLE_PAYMENT_IND` on the batch vs the import file |
| WH calculates & journalizes, but **check form / ACH file / positive pay show gross payment amount** instead of net check amount; 1099 WH box empty | §C — SF 22-00684349 / 22-00690458 | Report/file pulls payment amount, not check amount — form/adapter change |
| **INT1099EXP errors** at first step (params 264/265 not settable on front end) | §D — SF 23-00935283 | IMP/EXP filepath definition missing for `1099MISCINT` |
| Old **"QCFS 1099 Export (QSTG)" fails** with endpoint/connection errors | §D — SF 22-00559099 | Process retired at 2020.09 — use the INT1099* export; metadata cleanup script |
| 1099 amounts doubled / wrong box / QSTG1099 timeouts | **Not this skill** → `SKILL_QCFS_Accounts_Payable.md` §10 | AP151/XREF_1099 |
| Owner state/backup WH on **revenue checks** (NM 4.9%, batch type 18, CW010/CW011) | **Not this skill** → QRA | SF 25-01006246, ADO Bug 1716410 |

---

## 2. The Two Withholding Engines (concepts)

1. **State tax withholding at voucher entry** — the **PA withholding enhancement, new in 2026.04** (pilot client: Range Resources / RRC). Configured on the **AP200** config screen + **Code Tables 63019 / 63020 / 63021**; control table **`QCTRL_AP_ST_TAX_WITHHOLDING`**. When a vendor + property + activity-date combination is WH-eligible, AP055 auto-generates a **state tax withholding line** in the GL Distribution Coding grid (interactive path: `CalculateStTaxWithholding()`). For **imported** vouchers (ADPUPLOAD / QSTAGXLSIM / OpenInvoice), the **MT100** interface flag **"Auto Create State Tax WH Entries"** makes the import create the WH line (import path: `APImportDataHandler.cs` in `Quorum.Upstream.QCFS.Web`, repo folder `Quorum.QCFS.QCFSExternalImport`). Anchors: Bug 1831243 (description + repro + RCA fields), Bugs 1832480/1832726/1795333.
2. **Federal / backup withholding at payment time** — legacy AP061 check-write behavior. Setup per SF 22-00684349 (Encino): add the **withholding account and withholding tax percent in AP043**; BAs **without a Tax ID record in BA005** are subject to backup withholding. The system **calculates and journalizes the WH amount during AP061**; the check pays net. Known reporting gap: check form, ACH file, and positive pay export pull the **payment amount** rather than the net check amount, and the 1099 WH amount may not populate (22-00684349; Parsley declined a custom positive-pay change — 22-00690458, Business Change).

Remittance of withheld amounts = the WH lines credit the AP043/AP200-configured withholding liability account; the accumulated liability is remitted to the taxing authority as a normal AP payment, and withheld amounts surface on 1099s (federal WH box) via the INT1099* export (§D). No mined case documents a defect in the remit-voucher step itself.

---

## 3. Decision Tree

```
Withholding case (QCFS)
│
├─ Is it revenue/owner withholding (batch type 18, CW010/CW011, revenue distribution)?
│      → QRA product — route out (25-01006246 / Bug 1716410)
│
├─ STATE tax WH (AP200 / PA withholding, 2026.04+)?
│   ├─ Client build < 2026.04?            → Expected: feature doesn't exist yet (§F)
│   ├─ WH lines vanish on Validate/Approve (imported vouchers) → §A1 (Bug 1831243)
│   ├─ WH line never generated:
│   │    ├─ Post-to-BU ≠ header BU / intercompany   → §A2 (Bug 1832480, SF 26-01110470)
│   │    ├─ Property blank on distribution          → §A3 (Bug 1832726)
│   │    └─ Config: AP200 rows / code tables 63019-21 / MT100 flag unset → §B (config, not defect)
│   ├─ Voucher won't save, AUTO_CREATE_STATE_TAX_WH error → §A4 (Bug 1795333)
│   └─ AP200 screen missing / rows not on child BUs → §B (tree metadata / Bug 1852050)
│
├─ FEDERAL/backup WH at check write (AP043)?
│   ├─ Not deducted at all on imported invoices → §C (Single Pay ind — Bug 1801422)
│   ├─ Deducted+journalized but forms/files show gross → §C (form/adapter change)
│   └─ "Can Quorum withhold federal tax in AP?"  → §F (yes — AP043 setup)
│
└─ 1099/export of withheld amounts?
    ├─ INT1099EXP first-step error → §D (filepath definition)
    ├─ Legacy QSTG export failing  → §D (retired 2020.09)
    └─ Anything else 1099          → SKILL_QCFS_Accounts_Payable.md §10
```

---

## §A — State tax WH calculation defects (2026.04 family, RRC pilot)

### A1. Imported WH lines deleted on Validate/Approve — **Bug 1831243** (the anchor)
- **Signature:** ADPUPLOAD/QSTAGXLSIM import with MT100 "Auto Create State Tax WH Entries" creates the voucher **with** the state-tax-WH line; clicking **Validate or Approve in AP055 removes it** from the GL distribution.
- **Root cause (verbatim RCA, Bug 1831243):** `APImportDataHandler.cs` line 719 called `BatchBuilder.AddLine()` with `icOffsetInd = true` for StateTaxWithholding lines → **`ICOFFSET_IND = 1`** on the WH row in `BATCHVOUCHERGLDISTRIBUTION` → Validate/Approve runs `ICOffsetFill()` → **`AutoDeleteOffset()` deletes all rows where `ICOFFSET_IND = 1`**, including the WH line. Interactive AP055 vouchers unaffected (`CalculateStTaxWithholding()` sets `ICOFFSET_IND = 0`).
- **Fix:** removed the hardcoded `true` (param defaults to `false`). Single change in `Quorum.Upstream.QCFS.Web` — `Quorum.QCFS.QCFSExternalImport/APImportDataHandler.cs:719`. PRs 129518 / 129519. Target Release **2026.04**; found in RRCU_HD_DEVA1; RCA category "Implementation Miss".
- **Post-fix data caveat (from the WI's implementation details):** Draft imported batches created **before** the fix still carry `ICOFFSET_IND = 1` on their WH lines and **will still lose them** on first Validate/Approve — review/correct those rows first (SQL in §E).

### A2. No WH on intercompany / Post-to-BU coding — **Bug 1832480** + SF **26-01110470**
- **Signature:** "Post to BU" in the GL distribution differs from the header BU → **state-tax-WH lines never auto-generate**, even when the vendor/property/activity-date is eligible per AP200 + code tables 63019/63020/63021. Client-side symptom (SF 26-01110470, RRC): during AP voucher imports and GL MJEs with intercompany allocation/well/property, "system errors and says property is not on business unit" (all RRC properties on BU 2).
- **Fix:** Bug 1832480 (project Quorum) Closed; SF resolution: "FIxed in July 2026 - 2026.04 Hotfix." Verified in both ClassicGUI and Web/Excel-import paths per WI test notes.

### A3. No WH when Property blank — **Bug 1832726**
- **Signature:** WH lines only generated when a **Property** is on the transaction; allocation-group / G&A lines coded by **Cost Center only** got no WH.
- **Fix:** logic updated — when Property is blank, look up the property **state from the Cost Center coding** to determine WH eligibility. PR 129569, repo `Quorum.Upstream.QCFS.ClassicGUI`. Closed (project Quorum).

### A4. Voucher save blocked by `AUTO_CREATE_STATE_TAX_WH` — **Bug 1795333** / Task 1796002
- **Signature:** saving a new AP055 voucher throws a business-rule exception naming `AUTO_CREATE_STATE_TAX_WH` when the state-withholding **code block is not available** — voucher can't be created at all.
- **Fix (release note):** state-WH calculation is now **skipped gracefully** when the code block is unavailable. 2026.04. AreaPath `QuorumSoftware\Engineering\Software Services\Professional Services`.

---

## §B — State-WH config surface & deployment

| Item | Detail | Anchor |
|---|---|---|
| **AP200** | New state-tax-WH config screen shipped with the PA withholding enhancement (2026.04); 3 code-table screens + 1 config screen. If AP200 **doesn't display** after upgrade: **tree metadata updates are required** with the new screen. | SF 26-01107186 (Release Collateral Damage, RRC) |
| **Code Tables 63019 / 63020 / 63021** | State-WH eligibility config referenced by every repro (vendor + property + activity date eligibility "based on configurations defined within AP200 and Code Tables 63019/63020/63021"). | Bug 1831243 / 1832480 repro steps |
| **MT100 — "Auto Create State Tax WH Entries"** | Per-import-interface checkbox; enables WH auto-creation on imported vouchers (with Batch Import Setting = Draft in the 1831243 repro). | Bug 1831243 |
| **`QCTRL_AP_ST_TAX_WITHHOLDING`** | The AP state-WH control table. 2026.08 DB changes: **ADD `IDGLOBAL` int** (DB Change 1860092) and **ADD `GLOBAL_IND` bit NOT NULL default 0 + backfill** of IDGLOBAL/GLOBAL_IND (DB Change 1863368; backup table `QCTRL_AP_ST_TAX_WITHHOLDING_BKP_1852050_DF`). | WIs 1860092, 1863368 |
| **Global replication** | AP200 rows entered on the global company must replicate to child BUs — **Bug 1852050** "RRC - QCFS - AP200 State Tax Withholding Global Replication", state **Test**, tag "queued for next UPS 2026.04" (as of 2026-09-02). If child BUs are missing WH config rows, this is the open defect, not client error. | Bug 1852050 (+Task 1859427/1862939) |
| Import file drop | Repro uses the `ADP_UPLOAD_INVOICE_UNPROCESSED` global configuration for the ADPUPLOAD file location; run via QP073 → Process Type "Core Financials" → ADPUPLOAD. | Bug 1831243 repro |

**Config-vs-defect rule:** on a 2026.04+ build, if **no** WH generates anywhere, verify AP200 rows + code tables 63019-21 + MT100 flag **before** touching the §A defects; if WH generates for plain coding but not for intercompany/blank-property/imported-then-validated cases, it's §A2/§A3/§A1 respectively.

---

## §C — Federal / backup withholding at check write (AP043)

| Issue | Root cause | Fix recipe | Anchor |
|---|---|---|---|
| Check run **did not calculate/deduct withholding** for federal-WH-subject vendors (domestic or foreign) | Invoices imported via ADPUPLOAD: after the process was converted to a **segregated (seg) process**, a bad copy/paste pulled **`SINGLE_PAYMENT_IND` from `OVR_DATEDUE_IND`** — the file's Single Pay indicator was ignored (config `ADP_UPDATE_SINGLE_PAY` = use file's value) | **Bug 1801422** (Closed, AreaPath `...Maintenance\Upstream\Professional Services\Financials`); confirm the batch's Single Pay flag matches the import file post-fix | SF 26-01093081 (RRC; Resolution field cites Bug 1801422); sibling SF 26-01094846 "Single Pay not coming across from OI" → same WI |
| WH **calculates and journalizes correctly** in AP061, but **check form and ACH file display the gross payment amount**; positive pay also shows gross ("does not exclude WH"); 1099 WH amount not populated | Check form / ACH file / positive-pay export pull **payment amount instead of check amount** | Form + export/adapter change per client (no core config toggles found in mining); Parsley chose not to pursue custom positive-pay changes | SF 22-00684349 (Encino — includes the AP043 setup recipe); SF 22-00690458 (Parsley, Business Change) |
| "Can Quorum handle **Federal Tax Withholding** in the AP system?" (need to cut checks withholding federal tax for two owners) | Capability question | **Yes** — AP043: add withholding account + withholding tax percent; vendors with **no Tax ID record in BA005** become WH-subject (client practice: dummy SSN/Tax-ID rows exempt those who have one). Case closed - no response | SF 24-00979234; setup steps from SF 22-00684349 |

---

## §D — Withheld amounts on 1099s / export (WH angle only)

*Everything about box mapping, doubled amounts, AP151 overrides, QSTG timeouts → `SKILL_QCFS_Accounts_Payable.md` §10. Below is only what that skill does not carry.*

| Issue | Root cause / recipe | Anchor |
|---|---|---|
| **INT1099EXP** errors after the first step; log shows `IMPORT EXPORT ID(200) = 1099MISCINT; OVERRIDE IMP/EXP FILENAME(264) = NULL; OVERRIDE IMP/EXP PATH(265) = NULL` and those params aren't settable on the front end | **IMP/EXP filepath definition was missing** for the `1099MISCINT` import/export definition — add it (Application Configuration) | SF 23-00935283 (EAG) |
| Legacy process **"QCFS 1099 Export (QSTG)" completes with errors** ("Unable to establish a connection with any endpoint", `Quorum.QFC.Core.Interface.QException`); `QSTG_1099_MISC` still partially populates | **QSTG 1099 Export is retired as of 2020.09** — do not troubleshoot it; a metadata clean-up script removes it from the dropdown; use the current INT1099* export path | SF 22-00559099 (Seneca, Release Collateral) |
| **QSTG1099OV** warns "Process Step does not have enough Contiguous Memory to continue" (may claim success); nothing in `QARCH_QFCBATCH_SQL_TRACE` | Workaround on 2021.04: **QPEC restart, then rerun**; long-term fix in the 2023.04 upgrade | SF 24-00937123 (Mewbourne, Software Defect) |
| **QSTG1099OV runs 3+ hours** (normally 40–50 min); `QSTG_1099_MISC_OVR` not filling | The process SQL was **updated to run faster/predictably on large datasets** (Performance) — check PQID before killing | SF 25-00996019 (EQT, PQID 8757814) |

Missing export file path / SFTP definition for 1099 (SF 26-01065080) and 1099 export file-removal behavior (26-01084288) are Import/Export-skill territory.

---

## §E — Diagnostic SQL

> QCFS = SQL Server. Tables/columns below come verbatim from ADO WI RCA/DB-change text — still verify against the client DB; SELECT before any UPDATE; wrap fixes in a transaction. Client-PRD data-state claims from DEV-tier connections stay INFERRED.

```sql
-- E1. Bug 1831243 exposure: imported DRAFT batches whose state-tax-WH lines carry ICOFFSET_IND=1
--     (these lose the WH line on first Validate/Approve even AFTER the code fix is deployed)
SELECT d.IDBATVOUMASTER, g.IDBATVOUDETAIL, g.ICOFFSET_IND
FROM   BATCHVOUCHERGLDISTRIBUTION g
JOIN   BATCHVOUCHERDETAIL d ON d.ID = g.IDBATVOUDETAIL
WHERE  g.ICOFFSET_IND = 1;          -- review rows that are WH lines, not real I/C offsets (1831243)

-- E2. State-WH control/config rows (AP200) + 2026.08 global-replication columns
SELECT * FROM QCTRL_AP_ST_TAX_WITHHOLDING;              -- WI 1860092/1863368
--   IDGLOBAL int (added 1860092); GLOBAL_IND bit NOT NULL default 0 (added 1863368)
--   Replication defect backup table: QCTRL_AP_ST_TAX_WITHHOLDING_BKP_1852050_DF

-- E3. Code-table eligibility config (state WH): tables 63019 / 63020 / 63021
--     Confirm rows exist for the state + activity-date window before calling §A a defect.

-- E4. Federal-WH candidates: batch Single Pay flag vs import file (Bug 1801422 family)
--     Check SINGLE_PAYMENT_IND on the imported AP batch rows; pre-fix it mirrored OVR_DATEDUE_IND.

-- E5. 1099 WH staging (perf triage): QSTG1099OV populates QSTG_1099_MISC / QSTG_1099_MISC_OVR;
--     process trace in QARCH_QFCBATCH_SQL_TRACE (24-00937123, 25-00996019).
```

---

## §F — Expected-Behavior FAQ

| Asked as | Answer | Anchor |
|---|---|---|
| "Can Quorum withhold **federal taxes** on AP checks?" | Yes — AP043 withholding account + WH tax percent; BA005 Tax-ID presence drives backup-WH applicability; WH is calculated/journalized at AP061 | 24-00979234, 22-00684349 |
| "Where is **state withholding** configured?" (2026.04+) | AP200 config screen + Code Tables 63019/63020/63021; MT100 "Auto Create State Tax WH Entries" for imports | Bug 1831243/1832480 |
| "We upgraded but there's **no AP200 / no state WH** anywhere" | Build must be **2026.04+**, and the new-screen **tree metadata** must be applied | 26-01107186 |
| "Positive pay / ACH file shows the **gross** amount for WH checks" | Known behavior of the stock forms/exports — pulling payment amount; changing it is a client form/adapter customization, not a config key | 22-00684349, 22-00690458 |
| "Owner **state/backup withholding rate** wrong on revenue checks" | Not QCFS-AP — that's the QRA revenue-distribution WH (batch type 18; CW010 State WH Tax Maintenance / CW011 State Backup WH Tax Maintenance screens) | 25-01006246 (QRA), Bugs 1716410, 1812407, 1813155 |
| "1099 walkthrough / box mapping / doubled amounts" | AP skill §10 (AP151/XREF_1099, AP170) | SKILL_QCFS_Accounts_Payable.md |

---

## §G — Known ADO Items

| WI | Project | Type/State | Title (abbrev) | Cluster |
|---|---|---|---|---|
| **1831243** | Quorum | Bug / Closed | RRC - Imported State Tax WH Line Items Delete on Validate/Approve in AP055 (`APImportDataHandler.cs:719`; PRs 129518/129519; 2026.04) | §A1 |
| **1832480** | Quorum | Bug / Closed | RRC - AP State WH Calculations Not Effective on Intercompany Transactions | §A2 |
| **1832726** | Quorum | Bug / Closed | RRC - Update State Tax WH Logic to Look Up Property State off Cost Center Coding (PR 129569, ClassicGUI) | §A3 |
| **1795333 / 1796002** | QuorumSoftware | Bug+Task / Closed | 2026.04: AP055 voucher not created — `AUTO_CREATE_STATE_TAX_WH` error | §A4 |
| **1852050** (+1859427, 1862939) | Quorum | Bug / **Test** | RRC - AP200 State Tax WH Global Replication (queued for next UPS 2026.04) | §B |
| **1860092** | QuorumSoftware | DB Change / Closed | ALTER `QCTRL_AP_ST_TAX_WITHHOLDING` ADD `IDGLOBAL` int | §B |
| **1863368** | QuorumSoftware | DB Change / Closed | Add `GLOBAL_IND` + backfill IDGLOBAL/GLOBAL_IND in `QCTRL_AP_ST_TAX_WITHHOLDING` | §B |
| **1801422** | QuorumSoftware | Bug / Closed | RRC - ADPUPLOAD Single Pay Ind Ignored (`SINGLE_PAYMENT_IND` ← `OVR_DATEDUE_IND` copy/paste; `ADP_UPDATE_SINGLE_PAY`) | §C |
| 1716410 | QuorumSoftware | Bug / Closed | MEW - State Withholding Ignoring Reversals (**QRA**, batch type 18) | routing only |
| 60489 | QuorumSoftware | Req / Closed | CHV - eSuite BA State Withholding tax (2018, historical) | context |
| 1812407 / 1813155 / 1866236 | Quorum | Feature/Bug | CW010 / CW011 State (Backup) WH Tax Maintenance web migration (**Revenue Accounting**) | routing only |

---

## §H — Escalation Guidance

- **Version gate first:** every §A defect and the AP200 surface ship in **2026.04** (RRC pilot). On older builds, "no state WH" is expected behavior, not a defect. On 2026.04, confirm the July-2026 2026.04 **Hotfix** for §A2 and the GA fix for §A1/§A4.
- **Route to Engineering** when: WH lines deleted on Validate/Approve with `ICOFFSET_IND=1` evidence (1831243 pattern recurring post-fix); no WH on Post-to-BU/blank-property coding on a fixed build; AP200 global replication gaps while **1852050 is still open** — attach to that WI rather than opening a duplicate. Provide: build/hotfix level, MT100 flag state, AP200 + code-table 63019-21 rows, one repro voucher with its `BATCHVOUCHERGLDISTRIBUTION` rows, PQID for import runs.
- **Handle as Config:** missing AP200/code-table rows on a working build; MT100 flag unset; INT1099EXP filepath definition (23-00935283); tree metadata for AP200 visibility (26-01107186).
- **Handle as Data:** pre-fix Draft imported batches with `ICOFFSET_IND=1` WH lines (verify-SELECT §E1, correct before users Validate).
- **Route out:** revenue-side owner WH → QRA; vendor/Tax-ID master + 1099 box mechanics → `SKILL_QCFS_Accounts_Payable.md` §9–§11.

---

*Skill created 2026-09-02 from the QCFS Coverage Plan partial gap (group 3). Sources: SF cases 26-01110470, 26-01093081, 26-01107186, 26-01094846, 24-00979234, 22-00684349, 22-00690458, 23-00935283, 22-00559099, 24-00937123, 25-00996019, 25-01006246 (QRA routing); ADO WIs 1831243, 1832480, 1832726, 1795333/1796002, 1852050, 1860092, 1863368, 1801422, 1716410, 60489. PII redacted (customer contact names removed).*
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
