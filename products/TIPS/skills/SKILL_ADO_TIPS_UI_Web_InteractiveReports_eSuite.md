# SKILL: ADO Defect/Fix Reference — TIPS UI / Web / Interactive Reports / eSuite

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps TIPS bugs (QuorumSoftware org)
**Product:** My Quorum TIPS (midstream — measurement, allocation, settlement, statements) — Web/eSuite UI surface
**Scope:** TIPS Web ("My Quorum TIPS" / eSuite) UI defects mined from ADO Closed/Resolved Bugs: the **Interactive Reports → "Query Screens" replacement** epic, **Excel/CSV export** failures, **dashboard widgets** (FlowCal/Map Link/New Business/Monthly Close), **V2UI** grid/context regressions, **picklists** not filtering/empty, **grid** behavior (page size, bulk-edit, import/export buttons, column customization), **Web-vs-Classic** field/column gaps, and **Design Studio** widget/agent errors.
**Use When:** Triaging a TIPS Web/eSuite UI ticket and you want the matching ADO bug, its dev-confirmed root cause, the PR/fix, the release it shipped in, and whether the client's build already carries it.

> **Evidence base:** WIQL over both TIPS area branches (`...\Engineering\Midstream` and `...\Engineering\Maintenance\Midstream and Transportation`), WorkItemType=Bug, State IN (Closed,Resolved), title filtered on web/query screen/interactive report/grid/picklist/widget/eSuite/Excel export/dashboard/no records/works in classic. Raw WIQL matched **1754** rows; that count is inflated by broad terms (`web`,`grid`,`dashboard`) and a **mixed QPTM+TIPS Maintenance branch**. The actionable TIPS UI set after title triage is ~**70-90** bugs. **~48 deep-read** (description + ReproSteps + full comment thread + linked PRs). See the OVERLAP & CAVEATS section for what was dropped as QPTM.

> **IntegrationBuild is empty on every bug mined.** Fixed-in-build is therefore inferred from (a) iteration path `YY.NN` (Quorum sprint = calendar `20YY` sprint `NN`), (b) release tags (`2022.10`, `2023.04`, `2024.10`, `2025.04`, `2025.10`), and (c) explicit dev comments naming a release/hotfix branch. Inferred values are marked **(inferred — confirm in release notes)**. Where a dev comment names the build verbatim it is **(confirmed in thread)**.

---

## 1. QUICK TRIAGE TABLE

| Symptom | Cluster | Most likely root cause | First check | Bug IDs |
|---|---|---|---|---|
| TIPS "Query Screen" (Allocated Volumes, Settle Fees, Revenue, Invoice Detail, Imbalance, Journal Entry, Paystation…) shows a blank column, wrong column name, or wrong required-param set | §3 Query Screens | New feature (Interactive Reports replacement) delivery defects — DB view column not surfaced / metadata column-name mismatch / param config | Is it a 2025 release? Most fixed across 2025.04–2025.10 | #1706234, #1706486, #1708134, #1708342, #1708385, #1708551, #1708707, #1710186, #1710399, #1710402, #1710497 |
| Excel/CSV **export** of a report/query fails ("Error saving report", "No Data Qualified", or fails on huge result) | §4 Export | Old Exago Interactive Reports flakiness (mostly not reproducible) **or** the >1,048,576-row Excel limit | Row count? Old IR (Exago) vs new Query Screen? | #1685751, #1687017, #1706930 |
| **Export-to-Excel / Import / Bulk-Edit buttons missing** from a grid | §4 Export | `grid.AllowExcelExport/AllowExcelImport` not set in the screen's `.cshtml` grid def (V2UI regression) | Grep the view's grid def for the Allow* flags | #1544446, #1583754, #1556458 |
| Dashboard **widget loses Company/Facility context** (Monthly Close shows None Found, values go to 0) after timeout/reload | §5 Widget context | V2UI single-page-app (QSPA) cached the dashboard; widgets re-rendered without context | Was it a V2UI env? Beta version ≥ 18.0.0-beta.178? | #1546013, #1547197, #1442145, #1522839, #1535034, #1541961 |
| **FlowCal Integration widget** error alert / "No Meter configured for Source Module FLOWCAL" / pagination dead / OAuth token error | §6 FlowCal | Hardcoded API URL, error thrown on non-FlowCal facilities, QSPA pagination, or platform OAuth | Does the facility even use FlowCal? QCloud vs on-prem? | #1542384, #1540479, #1568402, #1709057, #1773737 |
| **Map Link / Design Studio widget** 401 / not visible for **external** users | §6 FlowCal/DS | Widget security gated on the internal-only `100 fnc_All_ReadOnly` group; external personas lack it | External user's security groups + code-table link | #1766312 (QTR) |
| **Picklist empty / not filtered / spinning** on a TIPS Web screen | §7 Picklists | Picklist SQL filters on context data (CO_CD/MTR_NO) that isn't populated → SQL fails; or missing pick-input filter; or wrong Parameter ID | Picklist SQL + pick-input definition in `*.TIPS.Metadata` | #1551017, #1547144, #1559675, #1760179, #1543615 |
| **Grid shows 10 rows instead of configured 100** (default page size) | §8 Grid | Screen-specific page-size config missing AND code didn't fall back to `DEFAULT_GRID_PAGE_SIZE` | `QARCH_CNFG_CTRL` for that screen's `*_PAGE_SIZE` | #1710832 (QPTM screens — shared QFC behavior) |
| **Web screen missing fields/columns / editable when it shouldn't be**, but Classic is correct | §9 Web-vs-Classic | Web grid/metadata driven by different config than Classic; read-only gating not ported; collateral from a hotfix | Reproduce in BOTH; check `<CLIENT>.TIPS.Web/.Metadata` override | #1640778, #1622265, #1685232, #1605097, #1729684 |
| **Design Studio agent won't start / can't connect to Service Bus** after MFA | §6 DS | DS doesn't support MFA; assembly binding-redirect / TLS 1.2 missing in client App.Web | web.config binding redirect + TLS 1.2 on DS Agent MT | #1581955 (ONK) |

---

## 2. DECISION TREE

```
TIPS Web / eSuite UI bug
│
├─ Is the screen a NEW "Query Screen" / "Query Suite" (Allocated Volumes, Settle Fees, Revenue,
│   Invoice Detail, Imbalance, Journal Entry, Paystation, Company Status, Analysis Components)?
│   └─ §3 Interactive-Reports-Replacement epic (#1644407). Almost all column/param defects are
│      Closed and shipped across 2025.04–2025.10. Match symptom → bug; confirm client build ≥ that release.
│
├─ Is the complaint about EXPORT (Excel/CSV)?
│   ├─ Buttons MISSING from grid → §4: grid.AllowExcelExport/Import not set in .cshtml (V2UI). #1544446
│   ├─ Export ERRORS on old Interactive Reports (Exago) → §4: mostly NOT reproducible / Exago being retired. #1685751,#1687017
│   └─ Export fails only on HUGE results → §4: >1,048,576 Excel row cap. #1706930
│
├─ Is it a DASHBOARD WIDGET?
│   ├─ Loses company/facility context / values blank after timeout → §5 QSPA context loss. #1546013,#1547197
│   ├─ L2 drill-in throws error when no context set → §5 graceful-handling defect. #1442145
│   ├─ FlowCal widget error / pagination / OAuth / non-FlowCal facility → §6. #1542384,#1540479,#1568402,#1709057
│   ├─ Map Link / Design Studio widget 401 / hidden for external users → §6 widget security. #1766312
│   └─ Can't EDIT/SAVE dashboard ("not allowed") → §6 ALLOWSAVEDASHBOARD security object. #1674248
│
├─ PICKLIST empty / not filtered / spinning forever?
│   └─ §7: picklist SQL using unpopulated context data, missing pick-input filter, or wrong Parameter ID. #1551017,#1547144,#1559675,#1760179
│
├─ GRID page size / bulk-edit / column order/visibility wrong?
│   ├─ Page size 10 not 100 → §8 fallback to DEFAULT_GRID_PAGE_SIZE. #1710832
│   └─ Column hide/order/header not honored in Web (SOA grid def) → §9: web uses different config than Classic. #1777976 (QPTM)
│
├─ Web behaves differently than Classic (fields missing / editable / rounding)?
│   └─ §9: reproduce in BOTH; web is config/metadata-driven separately; check client override. #1640778,#1605097,#1729684
│
└─ Design Studio AGENT won't start (Service Bus / MFA)?
    └─ §6 DS: binding redirect + TLS 1.2; DS doesn't support MFA natively. #1581955
```

---

## 3. CLUSTER: Interactive Reports Replacement → "Query Screens" (the dominant TIPS UI epic)

**Anchor:** Feature **#1644407** "Interactive Reports Replacement: My Quorum TIPS 'Query Screens'" (Closed, Guardians of TIPS). Parents 100+ child WIs and ~30 QA bugs.

**Why it exists (from #1644407 description):** The legacy TIPS **Interactive Reports** feature (since 2021) was built on the 3rd-party **Exago** tool, which lost support after acquisition and was painful to deploy/maintain multi-tenant in QCloud + on-prem across versions. The replacement moves the "Classic Query Screens" natively into My Quorum TIPS Web so a plant accountant can query live measurement/allocation/settlement/revenue/journal/invoice data without Exago.

**Symptom (the whole cluster):** On a TIPS Web Query Screen, a column is **blank / missing**, a **column name** differs from the requirement/Interactive Report/Classic, the **required-parameter set** is wrong, data **alignment** is inconsistent, or a query is shown in a CAN env where it doesn't apply.

**Root cause (per-bug, from dev/QA comments):**
| Bug | Symptom | Root cause / fix (from thread + PRs) | Iter |
|---|---|---|---|
| **#1706234** | Allocated Volumes — BA Name column blank | Column not joined/surfaced from view `QTRAN_ALLOC_VOL_VW`; fix maps Ctr Party BA Name. PRs 104812/104815/104816 | 25.01 |
| **#1706486** | Settle Fees — BA Name column absent + Core/CAN column-name divergence | Column added; names normalized per "Column Name Modifications" requirement. PRs 104813/104756/104818 | 25.03 |
| **#1708134** | Invoice Detail — "Facility # OR Company" required params | Product decision: show Facility, Company, Acct Dt; only Acct Dt required; validation fires if neither Facility nor Company supplied (no real OR between params — AND-only). PR 105814 | 25.03 |
| **#1708342** | Revenue — "Atl Vol Type" typo vs IR "Alt Vol Type" | Column header corrected to "Alt Vol Type". PR 105396 | 25.03 |
| **#1708385** | Paystation — "Marketing Int Decimal" vs IR "Marketing Decimal" | Header corrected to "Marketing Decimal". PR 105396 | 25.03 |
| **#1708551** | Company Status — "Update Dt" vs "Updt Dt" elsewhere | Header normalized to "Updt Dt". PR 105396 | 25.03 |
| **#1708707** | Analysis Components — Iso-Pen/Nor-Pen Gpm columns missing | Missing columns added; decision made NOT to compare query screen vs Classic (only vs requirement). PR 105396 | 25.03 |
| **#1710186** | Settle Contract Fees — column data alignment inconsistent | Alignment normalized. PR 105958 | 25.03 |
| **#1710399** | Journal Entry — JE Type not marked required | JE Type set as required param. PR 105874 | 25.03 |
| **#1710402** | Invoice Detail visible in CAN where N/A | Hide non-applicable queries in CAN env. PR 105909 | 25.03 |
| **#1710497** | Imbalance — wrong required params (had Facility#; need Posted Ind) | Required params corrected to Posted Ind, Acct Dt, Company. PR 105874 | 25.03 |

**Where the code/data lives:** Query Screen output binds to DB views `Quorum.TIPS.Database/Common/{MSSQL,Oracle}/Views/QTRAN_*_VW.sql` (e.g. `QTRAN_ALLOC_VOL_VW`) via DataObjects in `Quorum.TIPS.Web/Quorum.TIPS.DataObject/CodeGen/DataObject/*DO.cs`; column names/params are metadata-driven (`*.TIPS.Metadata`). PR 105396 carried several header-rename fixes together.

**Fix + fixed-in-build:** All Closed. Iterations 25.01–25.08 ⇒ **shipped across 2025.04 and 2025.10** (inferred — confirm in release notes). This was net-new functionality, so a client only sees these screens (and their fixes) once on **2025.04+** with the Query Screens feature enabled.

**Workaround:** If a client is pre-2025.04, the old Exago Interactive Reports is still the mechanism (with its known export flakiness, §4). For a single wrong header/param on a current build, it's a metadata change — escalate as a small config/metadata fix, not a core code bug.

**Linked SF cases:** none on the epic bugs (internal beta/QA finds). Related field-reported items: see §9.

---

## 4. CLUSTER: Excel / CSV Export

**4a. Old Interactive Reports (Exago) export errors — mostly NOT reproducible**
- **#1685751** ("Export as Excel/CSV Failing in Settle Summary Report", + missing Contract Party BA #/Suffix columns) — **Rejected**. Filter fields the tester used were transiently pre-populated and then gone; could not be reproduced. 2024.10 regression.
- **#1687017** ("'No Data Qualified' popup on exporting almost all reports") — **Rejected**. Dev (John Weems) could not replicate; attached "Cannot Replicate" video.
- **Takeaway:** these were Exago-era flakiness, a major reason for the §3 replacement. Don't chase a code fix; if a client is still on Exago IR and hits export errors, the strategic answer is migration to Query Screens (§3).

**4b. Excel row-limit**
- **#1706930** "Excel Export fails when number of records exceeds 1048576" — Closed, Guardians of TIPS, iter 25.08. The hard Excel sheet limit (1,048,576 rows). Fix in PRs 104917/104925/104935/104936/104997/105305/105310/105311 (the cluster of Query-Screen export PRs). QA couldn't hit the count in CORE; verified on PRF. **Fixed-in-build: 2025.10** (inferred). **Workaround:** narrow filters / export CSV / split the query so the result is < ~1.04M rows.

**4c. Grid export/import/bulk-edit BUTTONS missing (V2UI regression)**
- **#1544446** "Rate Schedules — Daily Rates grid missing Export/Import/Bulk-Edit" — **Root cause (dev Joe Kraft, verbatim):** the toolbar buttons require `grid.AllowExcelImport = true; grid.AllowExcelExport = true;` set in the grid def (`_RateSchedules_DailyRatesTab.cshtml` → grid `RateSchedulesDailyRates`), which were not set; BulkEdit had been intentionally removed in PR 72973. Fix re-adds the Allow* flags. PRs 83897/84018. Iter 23.09 ⇒ **2022.10/2023.04** (the bug is tagged `2022.10`).
- **#1583754** "Contract Rates — Hide/Show + Export not working on FEE EX grid" — same family; fix PRs 84271/84299. Iter 23.09 ⇒ 2023.04.
- **Diagnostic:** grep the screen's `.cshtml` for `AllowExcelExport` / `AllowExcelImport` / bulk-edit; 99 hits exist across `Quorum.TIPS.Web/Views/**`. Missing flag = missing button.

---

## 5. CLUSTER: Dashboard Widget Context Loss (V2UI / QSPA)

**Symptom:** Dashboard widgets (esp. **Monthly Close** "Current Open Billing Production Month" shows *None Found*, **FlowCal** shows 0) **lose the Company/Facility context** seemingly at random — typically after a screen timeout / Resume Work / reload. Navigating from the dashboard to a TIPS screen then throws **"Could not deserialize the response body stream"** (or "Stream was not readable"). Restored by re-selecting context (Context bar → Update) or logout/login.

**Root cause (from #1546013 thread):** Specific to **V2UI**; did not occur in V1UI. The dashboards were being handled by the **QSPA** (Quorum single-page-app) layer, which cached/re-rendered them and dropped the context payload. **Fix (dev Brynley Evans, verbatim):** "the dashboards have been excluded from QSPA to fix this issue" — required TIPS to consume **18.0.0-beta.178** (TIPS was lagging on beta.173). Platform/QSPA-driven, so build is platform-version-dependent.

**Related:**
- **#1547197** "Could not deserialize the response body stream" opening a screen right after the dashboard — the visible error of the same context loss (V2UI Oracle TST). PRs 71583/74463/74790/74791/74930/74944.
- **#1442145** Widget **L2 drill-in throws Quorum error screen** when context (Company/Plant) is blank — *"required parameters are not specified"* exception. Root cause (John Weems): L2s don't gracefully handle missing context data (happens after refresh / env restart / prod cut-over). Partial fix in `Quorum.TIPS.Web` (commit 59d24fc…) handling most widgets; New Business + OperatorInformationVariance L2s still re-query. Error originates in shared `Quorum.QFC.Web/.../QInterfaceControllerBase.cs`. Iter 23.11.
- **#1522839 / #1535034** FlowCal widget specifically losing context on reload (Volumes Available, then CMA). PR 71453. Iter 22.13/22.16.
- **#1541961** Context Overrides in widget settings can't be cleared and don't actually change widget values. PRs 83425/83707. Iter 23.08. (FlowCal override split off to #1594272.)

**Fixed-in-build:** 22.13–23.11 work ⇒ **2022.10 → 2023.04** (inferred); the QSPA exclusion is gated on the platform/QFC beta the client's release consumes — **confirm the QFC/platform version**, not just the TIPS release.

**Workaround:** re-select Company/Facility in the Context bar and click Update (or logout/login). For systemic recurrence after upgrade, confirm the client's QFC/platform build carries the QSPA-dashboard-exclusion.

---

## 6. CLUSTER: FlowCal & Design-Studio Widgets

| Bug | Symptom | Root cause / fix (thread) | Build (inferred) |
|---|---|---|---|
| **#1542384** | "No Meter is configured for Source Module FLOWCAL" error spams every TIPS Web screen on facilities that don't use FlowCal ("Configured" also misspelled) | Widget unconditionally probed for FLOWCAL-source meters; most clients don't use the FlowCal→eSuite→TIPS interface. Fix suppresses the error when no FlowCal meters exist. PRs 73687/74075/74076. Iter 22.18 | 2022.10 |
| **#1540479** | All FlowCal widget **L2 pagination + item counter dead** | Pagination/grid-height regression after QFC upgrade (sibling #1540148 "Design Studio L2 grids missing pagination after QFC upgrade"). PRs 73894/74130. Iter 22.18 | 2022.10 |
| **#1568402** | FlowCal widget assumes the TIPS API == `PRODUCTURL_API` — wrong in **QCloud** | Hardcoded API name; fix reads it from config instead. **Hotfixed back to 2022.10** (dev Cristina Keeton, confirmed). PRs 78494/79289/82411/82713/84421. Iter 23.06 | 2022.10 (hotfix, confirmed) |
| **#1709057** | "Error in FLOWCAL Integration Widget … Unable to create access token … OAuthToken" alert on L2 screens | Platform-side API access-token (OAuth) failure from dashboard widgets (env-specific, ORA DEV). Resolved via the platform "Product API Access from Dashboard Widgets" remediation (wiki 7939); related platform #1708315. PR 106338. Iter 25.03 | 2025.04 + platform fix |
| **#1773737** | FlowCal/Design-Studio widgets **log the full OAuth token** + show technical API logs to users (security) | Logging converted Debug→Info (PR 115959) exposed token strings on screen + in TIPS Web logs. Fix redacts token, logs only success/expiry, hides technical messages from users. PRs 122769/123155. Iter 26.03 | 2026.Spring (inferred) |
| **#1766312** | **Map Link widget 401 / not visible for EXTERNAL users** (QTR, SF 25-01052648) | Design-Studio widget visibility was effectively gated on the internal-only `100 fnc_All_ReadOnly` group, which can't be granted to external users; also a required **code-table link** had to be added for the widget. Affects ALL DS widgets (Map Link, Expiring Contracts, PPA Summary) for limited-group external users, not just Map Link. **Cherry-picked to 2025.04 + 2025.10** (dev, confirmed); moved to Maintenance (not platform). PRs 121001/121554/122006-122009. Iter 26.01 | 2025.04 & 2025.10 (confirmed cherry-pick) |
| **#1581955** | **Design Studio Agent stops / can't reach Service Bus** after MFA (ONK, SF 23-00886211) | DS web app **does not support MFA**; error was an assembly/protocol mismatch — needed `System.Net.Http.Extensions` binding redirect (oldVersion 0.0.0.0-2.2.28.0 → 2.2.28.0) in client App.Web **and** TLS 1.2 on the DS Agent middle tier. Redirects added to TIPS/ESUITE/QPTM/QLNG web repos in develop + 2023.04. PRs 85240-85244/86819/86827/86833/86973. | 2023.04 + client web.config |

**Code:** FlowCal OAuth in `Quorum.TIPS.DesignStudio.PackageSource/Quorum.TIPS.FlowCalculation/WebApiHelper.cs` (the `Quorum.TIPS.FlowCalculation.WebApiHelper+OAuthToken` type in the #1709057 error). Crude variant: `Quorum.TIPS.Crude.DesignStudio.PackageSource/Quorum.TIPS.Crude.Cargo/WebApiHelper.cs`.

**Dashboard-edit security (companion to widgets):**
- **#1674248** "Add ENGS Module Security Object **ALLOWSAVEDASHBOARD**" — a user with the config to edit dashboards still got "not allowed to edit" because the security object existed only under the QTIP module, not the **ENGS** module shared by TIPS/QPTM/QLNG. Fix inserts `ALLOWSAVEDASHBOARD` (OBJECT_TYPE 'OTH', MODULE_CD 'ENGS') into `QARCH_SEC_OBJECT` and grants it. PRs 100765-101373. Iter 24.20 ⇒ **2024.10**. (This is the ADO-side companion to the SF "can't modify global dashboard" pattern; on 2024.10+ grant the **ENGS** `ALLOWSAVEDASHBOARD` object to the group.)

---

## 7. CLUSTER: Picklists (empty / not filtered / spinning)

| Bug | Symptom | Root cause / fix (thread) | Build |
|---|---|---|---|
| **#1551017** | Allocated Quantity Query — ATT picklist returns **no items** in Web (Classic OK) | **Picklist SQL filtered on context data (CO_CD, MTR_NO); when those weren't populated the SQL failed.** Fix (dev Travis Heckel, verbatim): "Removed the context data filter criteria for CO_CD and MTR_NO so they are no longer populated by context data." PRs in `Quorum.TIPS.Metadata` (76294) + 76347. Iter 22.21 | 2022.10 (inferred) |
| **#1547144** | Weighted Avg Sales Price — Production Date picklist returns **ALL** plants, not the selected facility | Missing facility pick-input filter; fix adds it. SQL scripts attached (`ProdDatePicklistAddPickInput{MSSQL,ORA}.sql`). PRs 75425/75426. Iter 22.20 | 2022.10 (inferred) |
| **#1543615** | Location Fees — Fee Conditions field has **no picklist** | Picklist definition missing on the V2UI grid field; added. PRs 104013/112666. Iter 24.25 | 2024.10 (inferred) |
| **#1559675** | KW_STMT report — Ctr Party BA parameter has **no picklist** | Report parameter configured with wrong Parameter ID; fix sets **Parameter ID 24608** so the picklist appears. PR 76836 | 2022.10 (inferred) |
| **#1760179** | Fuel Pct Estimates — meter picklist doesn't add rows; Serv Req K / RIC-Up picklists **spin forever** | Grid set values were being populated with gas-day instead of contract values; CRUD/picklist binding fix on the Fuel Pct screen. PRs 118381-118919. Iter 25.22. Code: `Quorum.TIPS.Web.Core/Controllers/FuelPctController.cs`, `Quorum.TIPS.Web.Controllers/UIControllers/QUIControllerFuelPct.cs` | 2025.10 (inferred) |

**General picklist diagnostic:** an empty/failing TIPS Web picklist is most often the **pick-input SQL** in `*.TIPS.Metadata` — either it filters on context data that isn't set (remove that criterion, per #1551017) or it's missing the facility/plant filter (add the pick-input, per #1547144). For report-parameter picklists, it's the wrong **Parameter ID** (#1559675).

---

## 8. CLUSTER: Grid Page Size (shared QFC behavior — QPTM-reported)

- **#1710832** (ONK, SF 25-00999455) — "Query screen defaults to **10 instead of 100**" on RFS, Offers, Bids screens. **Root cause (dev Krutika Wagh/Grayson Lee):** these screens look up a **screen-specific page-size config** (e.g. `QVPCAPRELBIDWIZARDV2_PAGE_SIZE`); when missing, the code did **not** fall back to the QFC default. **Fix:** fall back to `DEFAULT_GRID_PAGE_SIZE` when the screen-specific config is absent. PRs 107208-107706 / 124373 / 127349. Code: shared `Quorum.QFC.Web/Quorum.QFC.Web.Core/Controls/QGridUIDef.cs`; config in `QARCH_CNFG_CTRL` (in `*.Metadata`). Default value in `Quorum.QPTM.Web/Quorum.QPTM.Common/ConfigSettings/QPTMGlobalConfigs.cs`.
- **NOTE — product:** the *screens* in #1710832 (RFS/Offers/Bids) are **QPTM**, but the **mechanism is shared QFC grid behavior** that any My Quorum grid (incl. TIPS Query Screens) uses. Listed here because the page-size fallback is the canonical answer to "grid shows fewer rows than configured" on any midstream Web grid. If a TIPS grid shows the wrong page size, check the same `QARCH_CNFG_CTRL` screen-config / default fallback.

---

## 9. CLUSTER: Web-vs-Classic field/column/edit gaps (field-reported, mostly QPTM-adjacent)

These are real TIPS-area Maintenance bugs but several are QPTM screens; included for the **pattern**: in My Quorum Web, grid columns/visibility/editability are driven by **separate config/metadata** from Classic, so "works in Classic, broken in Web" is usually a metadata/config gap or client override — not a core code bug.

| Bug | Symptom | Disposition | Build |
|---|---|---|---|
| **#1640778** (MKW, TIPS) | Contract Header QCM fields (Sub Ctr Type, Facility, Company ID, Org ID) **editable in TIPS Web** but read-only in Classic — collateral from a hotfix | Fix re-applies read-only gating in Web. PRs 92994-93028. Iter 24.05 | 2024.10 (inferred) |
| **#1605097** (TIPS) | eSuite **Report Viewer** appears in menu/search and confuses users (meant only as a run-dialog viewer, not a Generated Report Finder replacement) | Removed from menu; still searchable but clearly labeled TIPS/eSuite. PRs 94033-94108. Iter 24.05 | 2024.10 (inferred); may hotfix to 2022.10 |
| **#1729684** (TIPS) | Batch Process screen — **Run ID shows commas** (thousand-separators) out of focus | Number formatting fix. Pushed from 2025.10 to **2026.Spring** (dev John Weems, confirmed — too risky near QFC masters). PRs 117468/117838. Iter 26.02 | 2026.Spring (confirmed pushback) |
| **#1622265** (MKW, TIPS) | Contract Meter List **Object Reference error / spin** on large meter lists (timeout) | Performance fix: stop unnecessary reload of ValidPlantMeter cache. **Patched to 2022.10** as ESuite 2022.10.1.10 / TIPS 2022.10.1.12 (dev Jessica Bradham, confirmed), also 2023.04 + develop. PRs 89702/89722/90445 | 2022.10.1.12 (confirmed) |
| **#1685232** (TIPS) | Interactive Reports screen **not visible in TIPS CAN** RELQA | Security/permission + platform-dependent; intermittent (cache). PR 101252. Iter 24.20 | 2024.10 (inferred) |
| **#1777976** (ENT, **QPTM**) | SOA Web **grid def customization** (hide/order/header) not reflected in Web | Web grids driven by different config than Classic; many asks are intentional/hard-coded (e.g. svc requestor). Selective fixes (e.g. Hourly Profile made hideable). PRs 123253-124570. Iter 26.04 | 2024.04 hotfix + 2024.10+ |

**Rule of thumb:** reproduce in BOTH UIs; clear MT/eSuite/Pipeline caches and restart QPECs; then check the Web grid/metadata config and any `<CLIENT>.TIPS.Web` / `<CLIENT>.TIPS.Metadata` override before classifying as a core defect.

---

## 10. FIX-VERSION MATRIX

| Bug | Symptom (short) | State | Fixed-in-build | Source of build | SF case |
|---|---|---|---|---|---|
| #1644407 | Query Screens epic (feature) | Closed | 2025.04→2025.10 | iteration 25.x | — |
| #1706234 | Query: Allocated Vols BA Name blank | Closed | 2025.04 (inf) | iter 25.01 | — |
| #1706486 | Query: Settle Fees BA Name | Closed | 2025.10 (inf) | iter 25.03 | — |
| #1708134 | Query: Invoice Detail params | Closed | 2025.10 (inf) | iter 25.03 | — |
| #1708342/85/551/707 | Query: column-name mismatches | Closed | 2025.10 (inf) | iter 25.03, PR 105396 | — |
| #1710186/399/402/497 | Query: align/params/CAN-hide | Closed | 2025.10 (inf) | iter 25.03 | — |
| #1706930 | Export: >1,048,576 rows | Closed | 2025.10 (inf) | iter 25.08 | — |
| #1685751 | IR export Settle Summary fails | Closed(Rejected) | n/a — not reproduced | — | — |
| #1687017 | IR export "No Data Qualified" | Closed(Rejected) | n/a — not reproduced | — | — |
| #1544446 | Grid Export/Import/Bulk-Edit buttons missing | Closed | 2022.10/2023.04 (inf) | iter 23.09, tag 2022.10 | — |
| #1583754 | FEE EX grid hide/export | Closed | 2023.04 (inf) | iter 23.09 | — |
| #1546013 | Widgets lose context (QSPA) | Closed | 2022.10/2023.04 + QFC beta.178 | thread (Brynley) | — |
| #1547197 | "Could not deserialize body stream" | Closed | 2022.10 (inf) | iter 22.18 | — |
| #1442145 | Widget L2 error when no context | Closed | 2023.04 (inf) | iter 23.11 | — |
| #1522839/#1535034 | FlowCal widget context on reload | Closed | 2022.10 (inf) | iter 22.13/22.16 | — |
| #1541961 | Widget context overrides broken | Closed | 2023.04 (inf) | iter 23.08 | — |
| #1542384 | FlowCal error on non-FlowCal facility | Closed | 2022.10 (inf) | iter 22.18 | — |
| #1540479 | FlowCal L2 pagination dead | Closed | 2022.10 (inf) | iter 22.18 | — |
| #1568402 | FlowCal hardcoded API URL (QCloud) | Closed | 2022.10 (hotfix) | thread (confirmed) | — |
| #1709057 | FlowCal OAuth token error | Closed | 2025.04 + platform | iter 25.03 | — |
| #1773737 | FlowCal/DS logs leak token | Closed | 2026.Spring (inf) | iter 26.03 | — |
| #1766312 | Map Link widget 401 external users | Closed | 2025.04 & 2025.10 (cherry-pick) | thread (confirmed) | 25-01052648 |
| #1581955 | DS Agent / Service Bus / MFA | Closed(Verified) | 2023.04 + client web.config | thread (confirmed) | 23-00886211 |
| #1674248 | ALLOWSAVEDASHBOARD (ENGS) object | Closed | 2024.10 (inf) | iter 24.20 | — |
| #1551017 | ATT picklist empty (context-data SQL) | Closed | 2022.10 (inf) | iter 22.21 | — |
| #1547144 | WAVG picklist not filtered by plant | Closed | 2022.10 (inf) | iter 22.20 | — |
| #1543615 | Location Fees Fee-Condition no picklist | Closed | 2024.10 (inf) | iter 24.25 | — |
| #1559675 | KW_STMT param missing picklist (PID 24608) | Closed | 2022.10 (inf) | iter ~22.x | — |
| #1760179 | Fuel Pct meter picklist spins | Closed | 2025.10 (inf) | iter 25.22 | — |
| #1710832 | Grid page size 10 not 100 (QPTM) | Closed | per release (fallback) | iter — | 25-00999455 |
| #1640778 | Contract Header fields editable in Web | Closed | 2024.10 (inf) | iter 24.05 | — |
| #1605097 | eSuite Report Viewer in menu | Closed | 2024.10 (inf) | iter 24.05 | — |
| #1729684 | Run ID shows commas | Closed | 2026.Spring (confirmed) | thread | — |
| #1622265 | Ctr Meter List object-ref on large lists | Closed | 2022.10.1.12 (confirmed) | thread | — |
| #1685232 | IR screen not visible in CAN | Closed | 2024.10 (inf) | iter 24.20 | — |
| #1777976 | SOA Web grid customization (QPTM) | Closed | 2024.04 HF + 2024.10+ | thread | — |

> Iteration→release mapping used (inferred from dev comments naming release branches): **22.x ⇒ 2022.10**, **23.x ⇒ 2023.04**, **24.x ⇒ 2024.10**, **25.01-25.08 ⇒ 2025.04**, **25.09-25.22 ⇒ 2025.10**, **26.x ⇒ 2026 (Spring)**. Always confirm against actual release notes before quoting a build to a customer.

---

## 11. DIAGNOSTIC POINTERS (code & data)

| Artifact | Repo / path | Role |
|---|---|---|
| Query Screen data views | `Quorum.TIPS.Database/Common/{MSSQL,Oracle}/Views/QTRAN_*_VW.sql` (e.g. `QTRAN_ALLOC_VOL_VW`) | Source of Query Screen columns (§3) |
| Query Screen DataObjects | `Quorum.TIPS.Web/Quorum.TIPS.DataObject/CodeGen/DataObject/*DO.cs` | Maps view columns to grid (§3) |
| Grid Excel buttons | `Quorum.TIPS.Web/Views/**/*.cshtml` → `grid.AllowExcelExport`/`AllowExcelImport` | Export/Import button visibility (§4c) |
| Shared grid + page size | `Quorum.QFC.Web/Quorum.QFC.Web.Core/Controls/QGridUIDef.cs`; default in `Quorum.QPTM.Web/Quorum.QPTM.Common/ConfigSettings/QPTMGlobalConfigs.cs`; config rows in `QARCH_CNFG_CTRL` (`*.Metadata`) | Grid page size / fallback (§8) |
| Widget L2 error origin | `Quorum.QFC.Web/.../QInterfaceControllerBase.cs` | "required parameters not specified" on no-context drill-in (§5) |
| FlowCal widget OAuth | `Quorum.TIPS.DesignStudio.PackageSource/Quorum.TIPS.FlowCalculation/WebApiHelper.cs` (Crude: `Quorum.TIPS.Crude.DesignStudio.PackageSource/Quorum.TIPS.Crude.Cargo/WebApiHelper.cs`) | FlowCal token/API (§6) |
| Fuel Pct screen | `Quorum.TIPS.Web.Core/Controllers/FuelPctController.cs`, `Quorum.TIPS.Web.Controllers/UIControllers/QUIControllerFuelPct.cs` | Fuel Pct picklist/CRUD (§7) |
| Picklist pick-input SQL | `Quorum.TIPS.Metadata` (+ `<CLIENT>.TIPS.Metadata`) | Picklist filters & report params (§7) |
| Dashboard-edit security | `QARCH_SEC_OBJECT` (`ALLOWSAVEDASHBOARD`, MODULE_CD `ENGS`) + grants in `QARCH_SEC_GRP_PRIVILEGE` | Save/edit dashboard (§6) |
| Client overrides | `<CLIENT>.TIPS.Web` / `<CLIENT>.TIPS.Metadata` | Per-client grid/widget/metadata (§9) |

**Useful searches:** code-search `repo:Quorum.TIPS.Web`, `QTRAN_*_VW`, `AllowExcelExport`, `DEFAULT_GRID_PAGE_SIZE`, `OAuthToken`. WIQL: scope to both area branches and use team-name as the strongest product signal (see below).

---

## 12. ESCALATION GUIDANCE — is the client build fixed?

1. **Identify the cluster** (§1 table) and the matching bug ID.
2. **Read the Fix-Version Matrix (§10).** Compare the client's TIPS/eSuite build (and, for §5/§6 platform items, the **QFC/platform** version) against the fixed-in-build.
   - **(confirmed)** rows: quote the build (e.g. #1622265 → ESuite 2022.10.1.10 / TIPS 2022.10.1.12; #1568402 → 2022.10 hotfix; #1766312 → 2025.04 & 2025.10; #1729684 → 2026.Spring).
   - **(inferred)** rows: state the likely release from the iteration mapping but **verify in release notes** before promising a customer.
3. **If the client's build is at/after the fix:** likely a config/metadata/cache issue, not the code bug — clear MT/eSuite/Pipeline cache, restart QPECs, re-check context (§5) or security groups (§6). Reproduce in Classic too (§9).
4. **If the client's build is before the fix:**
   - Query Screens (§3) are net-new in **2025.04+** — pre-2025 clients won't have them; they're on Exago IR (export flakiness expected, §4a/b → migration is the strategic fix).
   - For a single shipped fix, route to Maintenance for a hotfix/cherry-pick to the client's release branch (several here were cherry-picked: #1766312, #1568402, #1622265).
5. **Platform/Design-Studio items (§6: #1709057, #1766312, #1581955, #5 QSPA):** these depend on the **platform/QFC** version and sometimes a **client web.config / code-table** change — not just the TIPS release. Confirm the platform build and the client-side config before declaring fixed.
6. **Picklist/grid config (§7/§8):** usually fixable in `*.TIPS.Metadata` (pick-input SQL, Parameter ID, `QARCH_CNFG_CTRL` page-size) without a core code change — these can often be scripted into the client env directly.

---

## 13. OVERLAP & CAVEATS (classification honesty)

- **Mixed Maintenance branch:** `...\Maintenance\Midstream and Transportation` carries **both QPTM and TIPS**. **Team/area sub-path is the strongest product signal:** `Guardians of TIPS`, `TIPS Samurai`, `TIPS'n Tricks` = **TIPS**; `Pirates of Pipeline`, `Pipeline Galaxy`, `Pipeline Titans` = **QPTM (pipeline)**. Titles mentioning Nomination/PDA/PAL/Offer/RFS/Bid/Confirmation/NN-reports = QPTM; Allocation/Measured Vols/Analysis/Cuts/Settle/Paystation/FlowCal/Plant/Query Screen = TIPS.
- **QPTM items intentionally INCLUDED here for the shared mechanism** (and flagged as such): **#1710832** (grid page-size fallback — RFS/Offers/Bids are QPTM screens but the `DEFAULT_GRID_PAGE_SIZE` fallback applies to all My Quorum grids) and **#1777976** (SOA Web grid-def customization — QPTM Confirmation/PDA/Nomination, but the "Web uses different config than Classic" lesson is universal). Treat their *screens* as QPTM; reuse their *root cause* for TIPS.
- **QPTM items DROPPED** from clusters (matched the title filter but are pure QPTM, no TIPS lesson): e.g. #1737771/#1739985 (PAL/Copy-Forward), #1754815/#1755819/#1760068/#1760071/#1763773/#1764714/#1765092/#1779785/#1796601/#1798371/#1666979 (ENT/EQC/TEP Nomination/Confirmation/PDA/SOA-picklist Web), #1631925 (UOM format). These belong in the QPTM UI/Web ADO skill.
- **IntegrationBuild empty everywhere** — all fixed-in-build values are inferred from iteration/tags/comments. The iteration→release mapping (§10 footnote) is itself inferred from dev comments; **do not quote a build to a customer without checking release notes.**
- **Two export bugs were Rejected/not-reproducible** (#1685751, #1687017) — they reflect Exago Interactive Reports flakiness, which is precisely why the Query Screens replacement (§3) exists. Don't open a code defect for old-IR export errors; the answer is migration.
- **WIQL count (1754) is NOT the TIPS UI defect count** — it's the raw title-filter match across both branches and both products. Actionable TIPS UI set ≈ 70-90; ~48 deep-read.
- **Companion SF skill:** the customer-facing TIPS UI guide is `TIPS Assitant/SKILL_TIPS_UI_Widgets.md` (SF-case-based). This file is the **ADO/engineering** complement — root causes, PRs, and fix versions. Use them together: SF skill for "what to tell the customer / config recipe", this skill for "which bug, which PR, which build."

---

*Skill created 2026-06-14 from ADO TIPS bugs (Closed/Resolved) across `QuorumSoftware\Engineering\Midstream` and `...\Maintenance\Midstream and Transportation`. ADO is READ-ONLY; no work items were modified. Fixed-in-build values are inferred from iteration paths, release tags, and dev comments unless marked (confirmed in thread).*
