# SKILL — FLOWCAL Family: Desktop UI, Screens, Tools & Utilities

> **Product family:** FLOWCAL · TESTit · PROVEit (`Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`)
> **Coverage-plan group:** #14 — Desktop UI, screens, tools & utilities (grids, editors, FcLoader, Toolbox, Bulk Changes, lists, locations) — ~3,225 family cases, ~240 actionable.
> **Sources:** Salesforce closed-case mining (all history, 2020–2026, ~190 case rows scanned, 38 cases deep-sampled with resolutions/descriptions/comments) + ADO org `QuorumSoftware` work items (projects `Quorum`, `QuorumSoftware`, `myQuorum Cloud`). Mined 2026-09-02.
> **Auto-Bot skill — built by Aditya Bhagat.** Every root-cause claim below cites SF case numbers and/or ADO work-item IDs verbatim. Fixed-in builds are **INFERRED** unless marked release-notes-confirmed.

---

## 1. Quick Triage

| Symptom (verbatim signature) | Likely cause | § |
|---|---|---|
| Toolbox / Run Validations fails to launch; `EEFFACE` instantly on Tools > Toolbox; "Date is less than minimum of 1/1/2072" | Jan-2023 date-window defect, all 10.0–10.4 branches; fixed by emergency patches | §3.1 |
| Bulk Change crash: "External exception EEFACE - Access violation at address … in module 'FCTIMEFRAMEEDITS.DLL'" | Defect editing Characteristics time span (Time Leads → Time Trails); still open in ADO | §3.2 |
| Bulk Changes > Meter Characteristics won't load / errors after Apply (10.2.0.x) | Defect in 10.2.0.22-era builds | §3.2 |
| Bulk Changes menu missing options present in single-meter editors ("Vol, Set VCF = 1", Auto Estimate Energy) | Product parity gap — route as Enhancement | §3.2 |
| FcLoader: FPV_METHOD/Z-method value ignored, only NX-19 lands | Field buffer defect (12→30 chars) + strict Z-method naming | §3.3 |
| FcLoader: "Unknown Operation Type" importing Calc Meter Members template | Members-template Operation Type value mismatch | §3.3 |
| FcLoader: validations/flow-parameters records fail on one env but not another | Wrong-size / stale `FcLoader.exe` binary | §3.3 |
| List Editor freezes forever on Save of a large static list; DBA must kill inactive session | 10.5.0.x defect (not in ≤10.4); fixed 10.5.0.20 (INFERRED) | §3.4 |
| List Editor "Will Not Save - Unable to connect to FLOWCAL.Enterprise.Integration.Service" | Integration service down/hung — restart services | §3.4 |
| Dynamic list not syncing FLOWCAL → TESTit; "Insufficient resources to perform operation (FlowCal.FieldApplications.Integration.Service)" | Red herring — meter characteristics duration gap; run Duration Fix utility | §3.4 |
| List Editor tile greyed out despite permissions | License allocation (RW seat), not security | §3.4 |
| Query Editor print fails / "Invalid report locations" | Report-path configuration on workstation | §3.5 |
| Exception Resolver freezes screen (10.0.3, 10.5.0.2) | Known defects; fixed in later 10.5 / upgrade to ≥10.6.0.6 | §3.6 |
| Exception Resolver shows no exceptions after visiting Edit Reason setup; edit reasons missing from dropdown | Bug 1739171 (Remember UI Filter Values interplay) | §3.6 |
| Double-click exception does not open Volume Editor; legacy resolver throws AV | Bug 1837313 | §3.6 |
| TESTit desktop error "root element missing" at launch | Corrupt local profile XML — delete `%LOCALAPPDATA%\Flow-Cal, Inc\TESTit3` | §3.7 |
| "Exception Error occurred in CMiscUtils: Could not find file '…\TESTit3\Layouts\…\Default.xml'" | Missing/corrupt layout file — File > Preferences > Restore Layout | §3.7 |
| TESTit 3.17.1 "Index was outside the bounds of the array" when filtering | Corrupt Layouts folder | §3.7 |
| PROVEit/TESTit "Exception Error occurred in CAppDATUtils: An item with the same key has already been added" | Corrupt per-user `.DAT` settings file — delete it | §3.7 |
| TESTit login fails after service upgrade: "CAppDATUtils: The input is not a valid Base-64 string…" / "Unable to load settings from dat file" | `.dat` written by older version (v1.17.1.0) unreadable by newer parser (v1.19.1.0) | §3.7 |
| Balance Explorer missing meters / L&U % blank / duplicate daily values | Screen-level display defects (10.0.3-era) | §3.8 |
| Users get `EEFACE` external exception on screens listing locations | Bad data — location rows with null entries from custom meter import | §3.8 |
| Empty Location drop-down in Truck Ticket Entry | Location/security configuration | §3.8 |
| FcDataBoss import: "unique constraint (FCOWNER.FC_EDIT_REASON_U_EDIT_REASON_I) violated" | Old DataBoss build — upgrade 3.5.3 → 3.5.4 | §3.9 |
| DataBoss "unable to connect to database" (new workstation) | Endpoint-security app blocking the exe — whitelist | §3.9 |
| CALCit "not working" / won't calculate (hosted) | Broken install — reinstall; site-key issues → Licensing skill | §3.9 |

**Batch flag:** none of these clusters are batch processes; do not route to batch-debugger. List-sync symptoms overlap the Integrations skill (group #11) — investigate UI side first, hand off if the Integration service itself is crashing.

---

## 2. Decision Tree

```
Desktop UI / tool / utility symptom
├─ Crash or error DIALOG with module name?
│   ├─ FCTIMEFRAMEEDITS.DLL ................................ §3.2 (open defect 1789500)
│   ├─ EEFFACE on Tools>Toolbox or Run Validations ......... §3.1 (version gate: <fix build?)
│   ├─ CAppDATUtils / CMiscUtils / "root element missing" .. §3.7 (local profile repair)
│   └─ EEFACE generic, multiple users, one client .......... §3.8 (bad location data) else escalate
├─ Screen HANGS / freezes (no error)?
│   ├─ List Editor on save of large list ................... §3.4 (G3: fixed 10.5.0.20)
│   ├─ Exception Resolver .................................. §3.6 (G3: fixed later 10.5 / 10.6)
│   ├─ Login screen (Citrix/hosted) ........................ §3.8 → Citrix profile cleanup
│   └─ everywhere / all screens ............................ NOT this skill → DB/perf skill (group 6)
├─ Tool runs but WRONG/NO result?
│   ├─ FcLoader field not landing .......................... §3.3 (G3 buffer bug + naming rules)
│   ├─ Bulk Change cleared a field / option missing ........ §3.2 (defect vs Enhancement)
│   ├─ Query Editor count ≠ List Editor count .............. §3.5 (expected-behavior first)
│   └─ Viewer missing rows (Balance Explorer/L&U) .......... §3.8
├─ GREYED OUT / missing menu?
│   ├─ List Editor tile greyed ............................. §3.4 (license seat — G2)
│   ├─ Volume Editor Set-up menu greyed .................... §3.2 (defect 23-00931010)
│   ├─ Bulk Changes menu missing options ................... §3.2 (Enhancement)
│   └─ TESTit whole menu missing ........................... §3.7 (profile reset per KB)
└─ Sync to TESTit/PROVEit broken? .......................... §3.4 first (data gap → Duration Fix),
                                                             then Integrations skill (group #11)
```

Gate discipline: most §3.7 fixes are **G1/G4** (profile repair, no code change); §3.1/§3.3/§3.4-freeze are **G3** (already fixed — version check first); greyed-out items are usually **G2** (license/config).

---

## 3. Symptom Clusters

### §3.1 Toolbox / Run Validations fail to launch — the Jan-2023 date-window event

**Signature.** Starting the first business days of January 2023, on ALL 10.x branches, clients could not open Tools > Toolbox (and Review > Run Validations): instant `EEFFACE` exception (SF 23-00876762) or explicit message **"Date is less than minimum of 1/1/2072"** (SF 23-00877067). Affected every environment/database at once ("prod, test, dev from any application or Citrix server on any database" — ADO 1571093 description). High-priority for clients because Toolbox is needed for month close (SF 23-00877659, client on 10.3.0.3).

**Root cause.** Date-window defect in the Toolbox screen date control tripped by the 2023 year boundary (two-digit-year window arithmetic — the "minimum 1/1/2072" message is the 1972 floor rendered in the wrong century). CONFIRMED as a code defect by the ADO port fan-out created 2023-01-03/04: Bug **1571093** (R1001 PORT), **1571448** (R1002 PORT), **1570989** (R1030 PORT), **1571003** (R1040 PORT), **1571037** (R1020 PORT) — all "23-00876651--error invoking toolbox", all Closed.

**Fix recipe.**
1. Version gate: if client is on a build older than its branch's Jan-2023 patch, upgrade. Observed fix deliveries: **10.2.0.22** (SF 23-00877403 "Upgrade to 10.2.0.22 for Toolbox Fix"; SF 23-00877659 client upgraded to **10.4.0.4**; SF 23-00876762 resolved by **10.3.0.10** upload). All fixed-in labels INFERRED from case resolutions, not release notes.
2. Any 2023+ build already contains the fix — if a client reports this today they are running a pre-2023 patch level; treat as G3 (version issue) and stop investigating.

**Anchors:** SF 23-00876651 (origin, via ADO title), 23-00876762, 23-00877067, 23-00877659, 23-00877403, 23-00877439, 23-00877308, 23-00876897, 23-00876756 · ADO 1571093, 1571448, 1570989, 1571003, 1571037.

---

### §3.2 Bulk Changes tool — crashes, non-functional tabs, parity gaps

**Signatures & causes.**

| Symptom | Cause | Anchor |
|---|---|---|
| "FLOWCAL: Bulk Change - External exception EEFACE - Access violation at address 0E0DBD4C in module 'FCTIMEFRAMEEDITS.DLL'. Read of address 00000000" | Defect editing Characteristics **time span Time Leads → Time Trails** (Volume Editor > Characteristic tab > Operations tab, and via Bulk Change). Reproduced by DEV with client FcDataBoss data (Delta Utilities meter, Feb 2026). **Still open** (Investigation) as of mining date — no fixed-in build. | SF 26-01095856, 26-01088026 · ADO **1789500** (Quorum, New/Investigation), **1789501** (QuorumSoftware, Closed as mirror) |
| Bulk Change > Meter Characteristics not loading / doesn't function (10.2.0.22); Operations errors after hitting Apply | 10.2.0.x-era defects in the Characteristics bulk-change path | SF 23-00891731, 23-00881567, 23-00880920 |
| Required field on an Integrated meter cleared by Bulk Changes | Tool wrote blank into a required field (no validation parity with single-meter editor) — treat as defect, warn client to re-check integrated meters after bulk ops | SF 24-00972091 |
| Bulk Changes menu lacks "Vol, Set VCF = 1" recalc option and Auto Estimate **Energy** value (both exist in single-meter editors) | Parity gap by design — route as **Enhancement**, not defect | SF 26-01105010 (description enumerates both gaps), 24-00972582 |
| Bulk changes demand System Information privilege | Security-model quirk; challenged by client, logged for product review | SF 23-00892068 |
| Cannot bulk-change Auto Estimate settings on Liquid meters | Not exposed in UI for LQ meters — Quorum provided SQL scripts updating the Meter Editor > Services > Auto Estimate fields directly | SF 24-00995522 (resolution: "SQL scripts were provided to update some fields for LQ meters") |
| Bulk Change slow on large scopes | Known performance profile — scope the meter list down; no code fix shipped from the sampled case | SF 23-00902235 |
| TESTit: "One or more schedules are currently in progress. Bulk changes are not allowed." | Expected behavior — TESTit blocks schedule bulk changes while any selected schedule is in progress; finish/close the schedules first | SF 24-00946703, 23-00917365 |

**Fix recipe (FCTIMEFRAMEEDITS.DLL crash).** No patch yet: workaround is to make the time-span change per-record in the Volume Editor avoiding the crashing transition path, or have engineering apply the data change via SQL. Link new cases to ADO 1789500; do NOT promise a fixed-in build.

---

### §3.3 FcLoader (command-line master-data loader)

FcLoader loads meter master data (master characteristics, flow parameters, calc-meter definitions, user fields, quality/source assignments) from pipe/text templates. High case volume; most are Training/UAR (send format docs). Actionable defects:

**(a) FPV_METHOD / Z-method not applied — only NX-19 works.**
- Repro (ADO 1644036/1782383 repro steps): 4 meters, FcLoader master-characteristics file with a different `FPV_METHOD` per meter; after import, Setup > Meter > Master Characteristics > Calculation Type tab shows Z method only for NX-19 rows; others null.
- Root cause (ADO 1644036 history, verified by testing): **input buffer for `fpv_method` was 12 chars, too short for values like `AGA8-Detail (2017)` — fix widened it 12 → 30**. Secondary cause: Z-method strings must match the supported naming exactly: `NX-19`, `AGA8-Detail (1992)`, `AGA8-Detail (2017)`, `AGA-8 Gross 1 (1992)`, `AGA-8 Gross 1 (2017)`, `AGA-8 Gross 2 (1992)`, `AGA-8 Gross 2 (2017)`, `AGA-8 GERG (2017)`, `Fpv = 1.0` (for AGA8-Gross 2 the field pairs are format-sensitive; wrong names are silently skipped — DEV declined fuzzy matching, and an enhancement was suggested to hard-reject bad values with a console message).
- Fixed-in: shipped in patch scopes **FLOWCAL 10.5.0.26** (ADO Requirement 1810511 regression list, item 1644036 R1050* PORT) and **FLOWCAL 10.8.0.7** (ADO Requirement 1807639 list, item 1782384 R1080 PORT); DEV item 1782383. Labels INFERRED from patch regression scopes.
- Anchors: SF 24-00940869, 25-01053909 · ADO 1782383 (DEV), 1644036 (R1050* PORT), 1782384 (R1080 PORT), 1810511, 1807639.

**(b) "Unknown Operation Type" importing the Calc Meter **Members** template.** Header/General/Custom templates import fine; Members template rejects every row regardless of member direction (Inlet/Outlet/Positive/Negative tried). Manual front-end add works. Root cause not published in the case (no resolution recorded) — verify the Operation Type column value against the template version shipped with the client's FLOWCAL build before blaming data. Anchor: SF 24-00987708 (description).

**(c) Wrong/stale `FcLoader.exe` binary.** Flow-parameter validation loads failed in PROD but worked in TEST on the same 10.3.0.10; support noticed **the PROD `FcLoader.exe` had the wrong file size** and replaced it with the TEST copy — fixed. Always compare exe size/version between working and failing envs first. Anchor: SF 25-01019896 (resolution verbatim).

**(d) Frozen Values header is all-or-nothing.** Values under a Frozen Values header do not import unless every column is populated. Logged as a defect request and **Declined — Not in Product Plan**; treat as expected behavior and tell clients to fill all frozen-value columns. Anchors: SF 22-00600375 (resolution: "Root Cause: Not in Product Plan / Resolution: Declined").

**(e) Connection errors running FcLoader.** Same troubleshooting as DataBoss (§3.9): TNS/DB alias, and local security software blocking the exe. Anchor: SF 26-01085529 (closed no-action).

Routing note: requests for FcLoader templates/formats/documentation are Training/UAR — send the format pack, no investigation (e.g. SF 26-01104719, 25-01029966, 26-01066580).

---

### §3.4 List Editor — static & dynamic lists (freeze, save failure, sync)

**(a) Screen freeze saving a large list — 10.5.0.x regression, fixed 10.5.0.20.**
- Signature: List Editor > New > move a few thousand meters to Selected > Save → FLOWCAL loads then "the screen will freeze and become unresponsive forever", leaving an inactive DB session the DBA must kill (ADO 1660076 description + repro). "This is not an issue in 10.4 or below" (DEV comment in SF 24-00947811 resolution and ADO repro); present in ALL 10.5.0.0+ builds until fixed.
- Workaround (DEV-provided): **switch to another tab of the editor (e.g. the Access tab) and save from there** — the hang is a screen-refresh issue on the main tab (SF 24-00947811 resolution; ADO 1660076 repro notes).
- Fixed-in: **FLOWCAL patch 10.5.0.20** (SF 25-01020741 resolution verbatim; SF 26-01093358 advises "upgrade to FLOWCAL 10.5.0.20 or later"). ADO chain: **1660076** (R1050* PORT), **1719299** (DEV), **1719300** (R1060 PORT) — root cause traced to commits that were reverted (1719299 history), with post-fix perf timings recorded (40k meters ≈ 62 s save — expected, not a hang). Related cosmetic item: Bug **1119877** "List Editor grids have cosmetic issues (R1041*)".
- Interim workaround used on 26-01093358: add the meters by running FLOWCAL directly on the application server (bypasses the client-side hang).
- Distinct flavor: ADO **1731988** — list editor unresponsive when editing ONE SPECIFIC dynamic list regardless of meter count (list-definition data issue; tagged Duplicate). If only one list hangs, suspect the list definition, not the version.

**(b) List Editor will not save — integration service unreachable.** Error: "Unable to connect to FLOWCAL.Enterprise.Integration.Service". Fix: review service logs and **restart the FLOWCAL Enterprise Integration service(s)** (cloud troubleshooting session confirmed list add worked afterwards). Anchors: SF 25-01022064 (resolution), 25-01033628 (Meter Master List not saving, same dependency).

**(c) Dynamic list not syncing to TESTit — "Insufficient resources to perform operation (FlowCal.FieldApplications.Integration.Service)".** RCA (SF 26-01082661 resolution, engineering-assisted): NOT infrastructure. Disk/queue thresholds were fine; actual cause was a **gap in one meter's characteristics data** (meter BB22139101) that destabilized the integration workflow and forced the service down. Fix: run the **Duration Fix utility** in FLOWCAL to close the characteristics duration gap; service stabilized immediately. Related engineering item: "Call Duration Fix Utility When Encountering Null Char" (ADO 1796061, in the 10.8.0.7 patch scope per ADO 1807639). Also check the plain-config causes first: list not flagged "Enabled for TESTit" in List Editor (question raised in ADO 1660076 history; SF 25-01026878 resolved as Application Configuration; SF 26-01105446 same theme).

**(d) Greyed-out List Editor.** User had correct security but no license seat — resolved under Licenses root cause (RW seat allocation). Check license counts before security deep-dives. Anchor: SF 25-01054869.

**(e) User missing from Available Users when sharing a static list.** Application Configuration — user/security setup, not a defect. Anchor: SF 25-01005602.

---

### §3.5 Query Editor

Mostly Training volume (wildcard syntax, table/field selection — SF 22-00531841, 23-00935510, 23-00913902). Actionable items:

- **Print from Query Editor fails.** "Error when attempting to print - Invalid report locations" (SF 22-00632837) and "Can't Print Meter Query Report" resolved as Application Configuration (SF 24-00945924): verify the workstation's report-location paths configuration before logging a defect. A cosmetic print error message variant was closed Training (SF 24-00969689).
- **Query editor error resolved by configuration** (SF 24-00986432, Application Configuration, Lists category).
- **Count mismatch: DYNAMIC List Editor vs Query Editor** (SF 24-00977687, closed no-action). Expected-behavior first: the two evaluate criteria at different times and dynamic lists apply include/exclude overrides; reconcile the definitions before suspecting data.
- Old enhancement backlog for the screen exists (SF 22-00684772 "Query Editor Enhancements/Fixes", Not in Product Plan) — set expectations accordingly.

---

### §3.6 Exception Resolver — freezes and UI defects

(The exception CONTENT rules live in the Exceptions/Validations skill (group #12); this section is the resolver UI itself.)

- **Screen freezing, 10.0.3:** multiple-year-old resolver; fix = upgrade. Quorum guidance verbatim: "We have made several updates to the Exception Resolver since version 10.0.3 … recommend upgrading to Flowcal **10.6.0.6**" (SF 25-01023065 resolution).
- **Freezing up on users, 10.5.0.2:** "known issue in 10.5.0.2. It was fixed and released in the latest 10.5 and up" (SF 24-00977061 resolution; INFERRED build).
- **Performance with dynamic list on a close group:** closed as Performance after tuning (SF 25-01054845) — check list size + close-group scope before blaming the resolver.
- **Resolver shows NO exceptions (and edit reasons missing from dropdown) after editing Edit Reasons:** Bug **1739171** — repro couples Settings Manager > System Configuration ("Allow free-form edit reason entry", "Require Edit Reason for Exceptions") with User Preferences > "Remember UI Filter Values"; after touching Settings Manager > Application > Edit Reason, the resolver returns empty and only exceptions-only edit reasons appear. State New — no fixed-in.
- **Double-click exception does not open Volume Editor; legacy resolver throws AV needing Task Manager kill:** Bug **1837313** (SF 25-01048298, NiSource data), closed with Training tag — check the client's resolver flavor (legacy vs new) and version before promising a fix.
- **Setting a User-Preference default list breaks the List dropdown** (10.5.0.19 test env): Bug **1838687**, closed.
- **AV when saving an edit made from the resolver (Volume Editor round-trip):** Bug **1788769**, New/Investigation — link, don't promise.
- **Email of selected exceptions caps at ~65 records:** Bug **1134948** (long-standing; old resolver capped ~15). Workaround: email in batches.
- Resolver settings persist per-user in `%APPDATA%\Roaming\Flow-Cal, Inc\FLOWCAL` (dashboard layout, widget config, resolver settings — ADO User Story 1852696 description). Corrupt state there explains "only this user" resolver weirdness — clear it as a diagnostic step.

---

### §3.7 TESTit / PROVEit desktop profile & layout corruption (launch + login errors)

The field apps persist per-user UI state and settings under **`%LOCALAPPDATA%\Flow-Cal, Inc\TESTit3`** (Layouts XMLs) and encrypted **`.dat`** settings files parsed by `CAppDATUtils.cs` (`GetSettings`/`SaveSettings`, per ADO Requirement 1510540 description — e.g. `Fieldapplications.dat`). Corruption of these files produces a family of launch/level errors:

| Error | Fix (in escalation order) | Anchor |
|---|---|---|
| "root element missing" at TESTit launch | Delete `%LOCALAPPDATA%\Flow-Cal, Inc\TESTit3` (whole folder); app regenerates it | SF 25-01010771 (resolution verbatim), 24-00968599 |
| "Exception Error occurred in CMiscUtils: Could not find file '…\TESTit3\Layouts\FSchedules\findLayoutControl\Default.xml'" | File > Preferences > **Restore Layout** | SF 25-01013677 (resolution), 25-01012703 |
| TESTit 3.17.1 "Index was outside the bounds of the array" when filtering | 1) File > Preferences > Restore Layout - Reset all Settings, restart; 2) delete the `Layouts` folder under `…\TESTit3`; 3) reinstall | SF 25-01020267 (resolution lists all three) |
| PROVEit "Exception Error occurred in CAppDATUtils: An item with the same key has already been added" | Delete the affected user's `.DAT` file (single-user impact, no permission loss) | SF 26-01102884 (resolution) |
| TESTit 3.18 login fails; log shows "CAppDATUtils: The input is not a valid Base-64 string…" (ErrorCode 229) | `.dat` unreadable — regenerate (delete) or re-key; seen at TTM on Citrix-published TESTit | ADO Incidents 1790854, 1785796 |
| After FieldApplications services upgrade v1.17.1.0 → v1.19.1.0: "Unable to load settings from dat file" on FcSrvFaDataManagement / FcSrvFaExportService / FcSrvFaImportService | Version-incompatible `.dat` encoding — regenerate service `.dat` settings post-upgrade | ADO Incident 1861272 (GPL TESTit UAT; log-scan finding verbatim) |
| TESTit Desktop menu missing entirely | Known KB fix (profile/layout reset) — resolved by sharing the KB article | SF 25-01048995 |
| PROVEit launch "Exception Error occurred in CAppDATUtils" generic | Same `.dat`/profile repair path | SF 26-01102884 pattern; PROVEit variant of above |

**Rule of thumb:** any TESTit/PROVEit error naming `CAppDATUtils`, `CMiscUtils`, `Layouts`, `.dat`, or "root element" is a **per-user local-state repair (G1/G4), not a code investigation** — unless it starts fleet-wide right after an upgrade, which is the §-1861272 version-incompatibility case (G3, coordinate with cloud/upgrade team).

---

### §3.8 Locations, viewers & general screen behavior

- **Comparison Location Editor broken for one comparison location:** deleting the offending comparison location (id 4436 in the case) cleared it — corrupt comparison-location row, not code (SF 26-01085178 resolution).
- **`EEFACE` external exceptions for many users, one client:** caused by **location rows with null entries** created by the client's custom NCTS meter-import path; fixed by a cleanup script deleting the null-entry locations (SF 25-01061337 resolution). Signature to remember: EEFACE ≠ always code — check for malformed location/master rows first.
- **Balance Explorer display defects (10.0.x era):** does not display all meters in a location (SF 22-00571714, 22-00696083); L&U data missing for one location/month (SF 23-00885250); L&U Viewer % and imbalance blank under Standard Conditions (SF 24-00994833); duplicate/erroneous values with the daily-data option (SF 25-01004734); post-upgrade performance (SF 22-00678501). All Software Defect root cause — version-gate first on anything Balance-Explorer-shaped.
- **Empty Location drop-down in Truck Ticket Entry:** Application Configuration (SF 24-00994715) — check location setup/security filters before defect-hunting.
- **Volume Editor Set-up menu greyed out:** Software Defect (SF 23-00931010, no published fix build — verify on current version, link if reproducible).
- **Calc meter editor throws error on edit:** Software Defect (SF 25-01008218, no published resolution — reproduce on current build before re-logging).
- **Coriolis Periodic Editor copy/paste failure:** Software Defect (SF 23-00935523).
- **Window z-order quirks:** Location Editor opens behind Location Tree Editor (SF 22-00614820); Location Editor Info-screen keyboard shortcuts bug (SF 22-00634142) — cosmetic-defect family, batch them for product backlog rather than per-case escalation.
- **Login screen freeze (hosted/Citrix):** Citrix profile bloat — restart the Citrix servers and clean inactive profiles under `C:\Users` (SF 24-00979148 resolution). Not a FLOWCAL defect.

---

### §3.9 Desktop data utilities — FcDataBoss, CALCit, ShowCFX, Duration Fix

- **FcDataBoss import fails: "unique constraint (FCOWNER.FC_EDIT_REASON_U_EDIT_REASON_I) violated".** Fix: upgrade DataBoss **3.5.3 → 3.5.4** (SF 24-00960754 resolution verbatim). Version-check DataBoss before debugging the data.
- **DataBoss cannot connect to database (single workstation):** client IT's endpoint-security app was blocking it; fixed by whitelisting DataBoss (SF 26-01111197 resolution). Same check applies to FcLoader (§3.3e).
- **DataBoss buffering issue (hosted PRD):** worked as cloud-side ADO chain in project `myQuorum Cloud` — items 1841069, 1845654, 1845120, 1845752 (SF 26-01111477 resolution lists all four). Route hosted DataBoss I/O issues to cloud ops with those precedents.
- **FcDataBoss modules disabled / sign-in refused:** licensing (site key) or user admin — SF 26-01116223 (Licenses), 26-01111276 (UAR). Not a defect path.
- **CALCit "not working":** hosted instance fixed by **reinstall by QCloud team** (SF 26-01117994 resolution). Site-key/Continue-button-greyed cases (SF 26-01107668) and version 4.2.0.0 authorization errors (SF 26-01121867) are Licensing skill (group #5) — hand off.
- **ShowCFX:** distribution/utility requests only in sampled history (SF 26-01123847 App Config, 26-01111597 capability question) — send the utility + usage doc; no defect cluster.
- **Duration Fix utility:** FLOWCAL-shipped data-repair tool for meter-characteristics duration gaps/null chars — the standard remediation when characteristic gaps destabilize list sync or editors (SF 26-01082661; ADO 1796061). Know it exists; it turns several would-be escalations into a same-day fix.

---

## 4. Known ADO Items (quick reference)

| ADO ID | Title (verbatim) | State at mining | Cluster |
|---|---|---|---|
| 1571093 / 1571448 / 1570989 / 1571003 / 1571037 | 23-00876651--error invoking toolbox (R1001/R1002/R1030/R1040/R1020 PORT) | Closed | §3.1 |
| 1789500 / 1789501 | Access violation [in module FCTIMEFRAMEEDITS.dll] / 26-01088026--Access violation in module FCTIMEFRAMEEDITS.dll | New (Investigation) / Closed | §3.2 |
| 1782383 / 1644036 / 1782384 | 24-00940869--FcLoader - FPV_METHOD - not working for some values (DEV / R1050* PORT / R1080 PORT) | Closed | §3.3 |
| 1810511 / 1807639 | FLOWCAL 10.5.0.26 / 10.8.0.7 Targeted Regression Testing and AT's run (patch scopes) | Closed | §3.3 |
| 1660076 / 1719299 / 1719300 | FLOWCAL Performance (Screen Freezing) (R1050* PORT / DEV / R1060 PORT) | Closed | §3.4 |
| 1731988 | The list editor becomes unresponsive when editing a dynamic list… | Closed (Duplicate) | §3.4 |
| 1119877 | List Editor grids have cosmetic issues (R1041*) | (referenced) | §3.4 |
| 1796061 | Call Duration Fix Utility When Encountering Null Char (R1080*) | in 10.8.0.7 scope | §3.4/§3.9 |
| 1739171 | Exception resolver doesn't show exceptions or exception edit reasons | New | §3.6 |
| 1837313 | Exception Resolver not opening volume editor | Closed | §3.6 |
| 1838687 | Exception Resolver - Setting a User Preference List Causes the List Dropdown to not function | Closed | §3.6 |
| 1788769 | Error when Editing from exception resolver (user data edit) | New (Investigation) | §3.6 |
| 1134948 | New .NET Exception Resolver - Email Issues | New (Escalated) | §3.6 |
| 1852696 | Multitenant: C# Main Screen config files and UI state | New | §3.6/§3.7 |
| 1861272 / 1790854 / 1785796 | TESTit `.dat`/CAppDATUtils incidents (GPL upgrade; TTM logins) | Closed | §3.7 |
| 1510540 | Plain Text Credentials in Services (documents CAppDATUtils.cs/.dat mechanics) | Closed | §3.7 |
| 1841069 / 1845654 / 1845120 / 1845752 | myQuorum Cloud DataBoss buffering chain (per SF 26-01111477) | per cloud project | §3.9 |

Area paths: `Quorum\North America\Measurement` (+ `\Maintenance`, `\Field Apps and API`), `QuorumSoftware\Engineering\Measurement\Maintenance`, cloud incidents in `myQuorum Cloud`. Port convention: title suffix `(DEV)` / `(R1050* PORT)` / `(R1080 PORT)` etc. — one bug per release branch.

---

## 5. Diagnostic SQL (verification only — NOT YET RUN; assumes FLOWCAL Oracle schema `FCOWNER`; adjust for SQL Server)

```sql
-- §3.4c / §3.9: meter characteristics duration gaps (the Duration Fix target signature).
-- Gap = a characteristics row whose end does not meet the next row's start for the same meter.
SELECT mc.meter_id, mc.effective_date, mc.effective_end_date
FROM   fcowner.fc_meter_char mc          -- verify exact table name via metadata server before running
WHERE  mc.meter_id = :suspect_meter
ORDER  BY mc.effective_date;             -- inspect for holes/nulls in the date chain

-- §3.9: pre-check before a DataBoss edit-reason import (constraint FC_EDIT_REASON_U_EDIT_REASON_I)
SELECT edit_reason, COUNT(*) FROM fcowner.fc_edit_reason GROUP BY edit_reason HAVING COUNT(*) > 1;

-- §3.6/§3.7: per-user UI state on the DB side (C++ object selector recents)
SELECT * FROM fcowner.fc_recent_item WHERE user_id = :user; -- table name from ADO 1852696 description
```

Env caveat: table names other than `fc_edit_reason`'s constraint (verbatim in SF 24-00960754) and `fc_recent_item` (verbatim in ADO 1852696) are INFERRED — confirm against live schema via the Quorum Metadata MCP before sending any script to a client.

---

## 6. Expected-Behavior FAQ

- **"Bulk changes are not allowed" while TESTit schedules are in progress** — by design; complete/close the in-progress schedules first (SF 24-00946703).
- **FcLoader Frozen Values header requires ALL columns filled** — by design after defect request was declined (SF 22-00600375).
- **FcLoader Z-method values must use exact supported naming** (`NX-19`, `AGA8-Detail (2017)`, …) — no fuzzy matching, by DEV decision (ADO 1782383 history).
- **Query Editor wildcard**: recurring how-to (SF 22-00531841, 23-00935510) — training material, not investigation.
- **Dynamic-list count ≠ Query Editor count** — different evaluation semantics + include/exclude overrides (SF 24-00977687).
- **Bulk Changes menu offering fewer options than single-meter editors** — parity gaps are Enhancements (SF 26-01105010).
- **Large list saves take up to ~1 minute at 40k meters post-10.5.0.20** — measured expected performance (ADO 1719299 history timings), not a regression.

---

## 7. Escalation Guidance

1. **Version-gate first** on §3.1 (any pre-2023 patch), §3.4a (pre-10.5.0.20 on 10.5), §3.6 freezes (10.0.3/10.5.0.2), §3.3a (pre-10.5.0.26/10.8.0.7): these are solved defects — deliver the upgrade recommendation with the ADO id, and an interim workaround from the cluster.
2. **Local-state repair before any escalation** for §3.7 signatures — 5-minute fix, no engineering needed. Escalate only fleet-wide post-upgrade outbreaks (cite ADO 1861272).
3. **Open defects (link, don't fix):** FCTIMEFRAMEEDITS.dll AV → ADO 1789500; Exception Resolver empty-after-edit-reasons → 1739171; resolver edit AV → 1788769; resolver email cap → 1134948. Attach the client's repro + FcDataBoss export, reference the SF case number in the ADO description (`Case Owner - {name}` + case-number convention).
4. **New bug filing:** project `Quorum`, area `Quorum\North America\Measurement` (desktop FLOWCAL) or `…\Field Apps and API` (TESTit/PROVEit); expect Engineering mirrors in `QuorumSoftware\Engineering\Measurement\Maintenance` and per-branch `(R####' PORT)` clones.
5. **Hand-offs:** list/dynamic-list sync failures where the Integration service itself crashes → Integrations & WebSync skill (group #11); CALCit/DataBoss site keys → Licensing & CrypKey skill (group #5); rollup screens (Rollup Viewer) → Reports skill (group #2); whole-app slowness → Database & performance skill (group #6).

---

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
