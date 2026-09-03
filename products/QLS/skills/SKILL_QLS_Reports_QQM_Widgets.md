# SKILL — QLS Reports, QQM & Widgets

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Scope (coverage-plan group #5):** core Reports screen (RPT_### Crystal/SSRS-launched reports), Agreement Data Sheet (ADS), QQM (SAP BusinessObjects / Web Intelligence query tool: universes, BIAR/LCMBIAR files, CMC), MyQuorum dashboard widgets (eCalendar Inbox/Coordinator, Obligations, Payments, Expiring Acreage, Agreement Search widgets).
> **Sources:** all-history Salesforce mining (8 SOQL pages, ~180 closed cases sampled, 2019–2026) + ADO work items (projects `QuorumSoftware` + `Quorum`), 2026-09-03.
> **Built by Auto-Bot — the L4 issue solver by Aditya Bhagat.**

---

## 1. Quick Triage

| Symptom you hear | Likely cluster | First check |
|---|---|---|
| "Report errors / won't run", picklist empty, "parameter error" | §3 Report launch & metadata | Report params in metadata; backing view columns (LURE_ACREAGES etc.) |
| "Payment Forecast (RPT_019) returns nothing / wrong totals / duplicates" | §4 RPT_019 family | ADO #1836615 (QCTRL_PMT_CC_ALLOC join); multi-cost-center duplication #1743269 |
| "SecurityException / security error generating a report" | §5 Report security | `QARCH_SEC_OBJECT.APP_LAYER_CD` for the RPT object; user's report security group (e.g. group 37005) |
| Crystal error "Error in formula … field name is not known" | §6 Crystal ↔ view mismatch | .rpt file vs backing view (EXHIBIT_A_VIEW etc.) — view is stale or client .rpt points at core view |
| "ADS fails / PDF not generated / sad-face error" | §7 ADS generation | OpenJDK on MT server; TOTAL_ADS_REC (>9 related wells); >30-char SEC_USER_NM; duplicate `all_agreements_log` rows |
| "ADS shows wrong acreage / blank section / wrong label" | §8 ADS content config | `OnlySumAreal`, Acreage Count flag, `QCNFG_SCREEN_CONTROL_DISP.DISP_IND`, code/decode values |
| "QQM object errors on Run Query / column missing in QQM" | §9 QQM universe & BIAR | Object→table mapping in universe (client-suffixed views!); fix = universe update + LCMBIAR deploy |
| "QQM down / can't log in / SSO loop" | §10 QQM login & infra runbook | Tomcat + SIA restart first; then krb5/Okta/CMC |
| "Widgets blank / error / won't load" | §11 Widget access & loading | Security objects `QLSWIDGETACCESS`, `QUCDASHBOARDEDITOR`; `OPENID-AUTHORITY` config; IIS app pool |
| "Widget counts wrong or don't match L2 screen / dashboard slow" | §12 Widget counts & perf | Hotfixed count bugs (#1712612 etc.); bad route-step sequence (#1657086); NULL obligation data |

**Gate mapping (Auto-Bot classes):** most report/ADS/widget issues here land in **G2 Config** (metadata, security objects, config keys) or **G3 Version** (long list of hotfixed defects below). QQM universe issues are G2 handled by the **BI team** (universe + LCMBIAR), not code. Bad-data (G4) shows up in ADS (`all_agreements_log`, `GEOG_AREAS`) and Obligations-widget (`STIPULATION_OBLIGATIONS`) clusters.

---

## 2. Decision Tree

```
Report/QQM/widget complaint
├─ Which surface?
│  ├─ Reports screen (Function Navigator → Reports, RPT_###) ──► launch error?
│  │     ├─ Missing picklist / param error ────────────────► §3 (report metadata / backing view)
│  │     ├─ "Error in formula …field name is not known" ───► §6 (Crystal .rpt vs view)
│  │     ├─ Security error / SecurityException ────────────► §5 (QARCH_SEC_OBJECT / report sec group)
│  │     └─ Runs but wrong data ───────────────────────────► §4 if RPT_019/020; else §6 view logic
│  ├─ ADS (Agreement Data Sheet)
│  │     ├─ Fails / no PDF / error ────────────────────────► §7 (env + data blockers, ranked)
│  │     └─ Generates but content wrong ───────────────────► §8 (config + code/decode)
│  ├─ QQM (BusinessObjects / WebI)
│  │     ├─ Object/report errors, missing columns ─────────► §9 (universe/BIAR — BI team)
│  │     └─ Login/outage/applet ───────────────────────────► §10 (runbook; mostly Cloud Ops)
│  └─ Dashboard widgets
│        ├─ Blank / error / cannot move-save ──────────────► §11 (security objects, config, app pool)
│        └─ Counts wrong / mismatch / slow ────────────────► §12 (defect history + data checks)
└─ Always: check §Known-ADO table first — many symptoms are already-fixed
   hotfix items (G3 exit: "fixed in <tag>, take hotfix").
```

---

## 3. Cluster: Report launch errors & missing report metadata (G2)

**Signature:** a core Land report (Acreage, Obligation/Expiration/Recommendation Calendar, Manual EFT Register…) errors on launch, a parameter picklist (State/County/Township) is empty, or the report is missing entirely from the Reports screen. Frequent right after an upgrade or environment refresh.

**Root causes seen (each anchored):**
- **Missing report/parameter metadata.** Recommendation/Payment Calendar reports errored because the *State input parameter* row was missing from report metadata — "Missing metadata was added to fix the Payment Calendar reports. State input param was missing" (SF 26-01102483, Closed 2026-05).
- **Backing view missing required columns.** Expiration Calendar report failed until "required parameters by expiration calendar report were added to the **LURE_ACREAGES** view" (SF 26-01099875).
- **Missing State/County/Township picklists** blocked Acreage + Obligation Calendar reports; fixed with a metadata script; the same script also restored the *missing* Payment Forecast Detail and Past Payments reports for that client (SF 25-01047986; SF 25-01052336 "fixed by script on 25-01047986").
- **Stale layer-parameter metadata after upgrade:** RPT_050/RPT_051 (Acreage Detail by State/County/Township/Range/Section) filters "not perpetuated" — fix was a script to **remove QLOD (client layer) parameter entries** and leave core QLS metadata (SF 23-00904584; SF 22-00517997).
- **Pick list definition broken:** Manual EFT Register report — "Unable to render control for Report Email Subject (PRLaunch_RPT_X097_Report Email Subject): **No valid pick returns defined for pick list 50012**" (SF 24-00985766). Client-custom reports are `RPT_X###`.
- **Hidden report definitions:** client custom Check/Invoice reports invisible until "Report definitions updated to become non-hidden" (SF 25-01049869).

**Fix recipe:**
1. Reproduce and capture the exact control/param name from the error (it names the report process, e.g. `PRLaunch_RPT_X097_…`).
2. Compare report metadata (report definition, input params, pick lists) against a working core environment; check the client layer (`QLOD`/`Q<CLIENT>` `APP_LAYER_CD`) for stale overrides — *remove* stale client-layer rows rather than editing them.
3. If the param sources from a view (LURE_ACREAGES etc.), verify the view has the columns the report requests.
4. Deliver as a metadata script; re-run report.

**Anchors:** SF 26-01102483, 26-01099875, 25-01047986, 25-01052336, 23-00904584, 22-00517997, 24-00985766, 25-01049869.

---

## 4. Cluster: Payment Forecast Detail (RPT_019) / Summary (RPT_020) family (G3 first, then G2)

**Signature:** RPT_019 "does not pull any data", pulls only some checks, duplicates payments, or totals look wrong. Recurring across clients and versions — check version fixes before investigating.

**Known defects (check these FIRST):**
- **ADO #1836615** (Proposed, 2026-07): Core RPT_019 SQL uses an **INNER JOIN to QCTRL_PMT_CC_ALLOC** where it needs a LEFT OUTER JOIN → only payments having Cost Center Allocation rows are returned; clients with no rows in QCTRL_PMT_CC_ALLOC get an **empty report**. Repro'd in CORE TST17 + JNE DEVA1. *Not yet released as of 2026-09 — INFERRED open.*
- **ADO #1743269** (Closed; tags 2023.04/2024.04/2024.10/2025.04 Hotfix Completed): payments with >1 cost center were **duplicated**; fix added a "Cost Center Amount" column (payment amount × CC allocation %) and made Grand Total sum that column. SF twin: 25-01024065 ("company share" showing total payment share — after the fix this is working as designed, see FAQ).
- **Regression pattern:** SF 26-01080097 — RPT_019 returned nothing on 2025.04; "this report was previously fixed for version 2022.04, **deploying the fix again for version 2025.04** solved the issue" (client-layer report fix lost in upgrade).
- **Post-patch QQM linkage:** SF 26-01120493 — payment forecast report broke right after a patch; resolved when "the BI team updated the **QQM Production connection**" (the report was QQM-side, not application-side).
- SF 26-01108865: new core RPT_019 returned "wrong information" for one client; resolution was a **client-specific report** cloned from their old one.

**Fix recipe:** (1) Confirm version + whether client layer has an RPT_019 override; (2) if empty output, test the QCTRL_PMT_CC_ALLOC join defect (#1836615) — run the report for a payment known to have no CC-alloc rows; (3) if duplicates/multi-CC totals, verify client has #1743269's hotfix; (4) after any patch, confirm which side (QLS report vs QQM connection) actually runs the report.

**Anchors:** ADO 1836615, 1743269, 243465 (RPT_019/020 launch-title fix); SF 26-01080097, 26-01108865, 26-01120493, 25-01024065.

---

## 5. Cluster: Report security errors (G2)

**Signature:** "Security Error when Generating Reports", `SecurityException`, or report works for admins but not end users.

**Root causes:**
- **RPT_1029 (View Invoice / View Check Receipt) SecurityException in PROD** — SF 26-01103127 (Devon): fixed by aligning **`QARCH_SEC_OBJECT.APP_LAYER_CD` from `QINT` to `QLS` for `OBJECT_ID=1029`**, and adding the matching client-layer (`QDVN`) rows in **`QARCH_CTRL_PROCESS_REPORTS`** / **`QARCH_RPTS_DEFINE`** so RPT_1029's data layout mirrors working RPT_999. No code fix required.
- **Report security group membership:** three 2026 cases at one client (Exhibit A security error 26-01084687; Audit History/Land report error 26-01085210; New Lease and Contract report timeout 26-01085212) all closed with "User was added to **group 37005**" — a client report-access security group. Pattern: per-report launch failures for specific users = check group membership before anything else.

**Fix recipe:** (1) Identify the report OBJECT_ID; (2) `SELECT * FROM lis.QARCH_SEC_OBJECT WHERE OBJECT_ID = <id>` — check APP_LAYER_CD matches the layer the app resolves (QLS, not QINT); (3) verify user's security groups include the group granting that report object; (4) if data-layout differs from a working sibling report, mirror its `QARCH_CTRL_PROCESS_REPORTS`/`QARCH_RPTS_DEFINE` rows in the client layer.

**Anchors:** SF 26-01103127, 26-01084687, 26-01085210, 26-01085212.

---

## 6. Cluster: Crystal report file ↔ database view mismatch (G2/G5)

**Signature:** `Error in formula : '{VIEW.COLUMN}' This field name is not known. Details: errorKind` / `Failed to export the report`, or a report runs but returns wrong/blank data. The RPT engine fills a Crystal `.rpt` template from a database view; either side can be stale.

**Cases:**
- **Exhibit A (RPT_009):** `Error in formula book/page/desc: '{EXHIBIT_A_VIEW.RCDN_DATA}' This field name is not known … Error in File EXHIBIT_A 11204_8088_{GUID}.rpt` — resolved with a "script to fix the **view** behind this report" (SF 25-01052334). Companion visual defect: rightmost borderline cut off, data NOT cut off — repro'd in core, logged low priority (SF 25-01000782).
- **Auditor Report (RPT_007) inaccurate users:** core view **`qctrl_auditor_core`** pulled bad data; updated to base "inactive" on the inactive flag in **`QARCH_SEC_USER`** (SF 22-00682757); other RPT_007 fixes: core-view modification (SF 22-00559604), "Fixed in 2021.04 GA release" (SF 22-00566291), hotfix (SF 24-00972976). If RPT_007 shows inactive users active *today*, first check for duplicate user accounts (SF 24-00988365 — customer error).
- **Client custom report wrong results:** RPT_X027 Trade Wells/Bonus — "report view needed to be updated to point to **WELL_INFO_QRA**" (SF 22-00659335).
- **Wrong .rpt targeted:** after upgrade a client needed to "re-point all of the crystal reports to the DVN specific versions" (SF 26-01065390); check signature/logo assets too — check-run signature updated directly on check files (SF 25-01060044).
- Other core-view updates: Obligation Calendar RPT_012 (SF 23-00900001), Payment Calendar RPT_018 crystal logic (SF 22-00704987), RPT_051 acreage views aligned to state reporting requirements (SF 23-00911227), Invoice report metadata + client report fix (SF 22-00684334, 22-00684212).

**Fix recipe:** (1) Pull the exact formula/field name from the error — it names the view; (2) `DESC lis.<VIEW>` and compare to the .rpt's expected fields; (3) determine which is stale (client .rpt vs upgraded view, or client view vs core .rpt); (4) script the view fix or re-point the report definition to the correct .rpt; (5) re-run and verify export (PDF) completes, not just preview.

**Anchors:** SF 25-01052334, 25-01000782, 22-00682757, 22-00559604, 22-00566291, 24-00972976, 24-00988365, 22-00659335, 26-01065390, 25-01060044, 23-00900001, 22-00704987, 23-00911227, 22-00684334, 22-00684212.

---

## 7. Cluster: ADS (Agreement Data Sheet) fails to generate (G2/G3/G4)

**Signature:** "Generate ADS" errors, spins, or produces no/garbage output. Rank checks by frequency:

1. **Missing/incompatible Java on the MT server (post-upgrade).** ADS PDF is produced by Apache **FOP** via `Quorum.QLS.ADSNetLib` and requires **OpenJDK 11** (Requirement 232285; ADO #1718170 tracks the FOP .jar files). Two 2026 cases fixed by "Deploying the **AdoptOpenJDK x64 and x86 on the MT server** … The PDF now generates" (SF 26-01092366, 26-01092395).
2. **`Cannot set column 'TOTAL_ADS_REC'` (ArgumentException)** when the agreement has **10+ Related Wells** — ADO #1407753 (Closed). Error surfaces as `Web Access Error [Action 'AgreementHeader.GetADSPDFForAgreement']`.
3. **Security user name > 30 chars** when ADS displays Last-Update fields: if `QCNFG_SCREEN_CONTROL_DISP.DISP_IND=1` for `COL_TAG_NAME IN ('LAST_UPDT_BY','LAST_UPDT_DT')` on ADS screens and the last updater's `QARCH_SEC_USER.SEC_USER_NM` exceeds 30 characters, ADS fails with "One or more rows contain values violating non-null, unique, or foreign-key constraints" in `GetADSFileContent`. View: `QLIS_AGM_LAST_UPDATED_QUERY` registered SQL. ADO #1694486 (SF 24-00937207), hotfix-completed 2022.04→2024.10.
4. **Bad data blockers** (SF 25-01042880, three root causes in one case):
   - duplicate `<Agreement Created>` rows in **`all_agreements_log`** (conversion-script artifact) break the Agreement Summary node query → PDF not generated; delete the duplicates;
   - **`GEOG_AREAS` rows where `GEOG_PRNT_KEY = GEOG_KEY`** break the Organization node; update the parent key;
   - **504 gateway errors** on large ADS = AWS load balancer idle timeout; raising it 1 min → 10 min fixed most.
5. **Bulk ADS ≠ single ADS.** Bulk runs as a *batch process* (output to `AgmtSrchBulkADSOutputPath`), single runs through the MT. APA saw Bulk ADS emit **FO and XML files instead of PDFs** while single ADS worked (ADO #1638136, hotfix-completed 2022.04/2023.04). Users can't see bulk output unless the share is published (SF 24-00984449 "BulkADSOutput" file share; SF 24-00977861 one-time bulk run delivered via FTP; SF 25-01023273 bulk error resolved by upgrade).

**Anchors:** SF 26-01092366, 26-01092395, 25-01042880, 24-00984449, 24-00977861, 25-01023273; ADO 1718170, 1407753, 1694486, 1638136, 1668034.

---

## 8. Cluster: ADS content wrong (blank sections, wrong acreage, wrong labels) (G2)

**Signature:** ADS generates but a section is blank, acreage totals are wrong, or labels are wrong/garbled. Almost always configuration:

| Symptom | Config / fix | Anchor |
|---|---|---|
| Lessor name wrong (pulls Participation name) | Turn on **`UseLessorNmInsteadOfPrtpName`** → pulls from Additional Party screen | SF 26-01084488 |
| Acreage not summed / zero in ADS + Agreement Summary | With Acreage Count flag config enabled, the **Acreage Count flag must be checked on the Areal(s)** (or on Header acreage when no Areals exist) | SF 26-01084488 |
| ADS not calculating acreage at all | Config **`OnlySumAreal`** turned on | SF 24-00980823 |
| Wrong acreage when areal is inactive + count flag on | Core bug, fixed ("Bug fix") | SF 22-00808639 |
| Count checkbox should read "Do Not Count" | Label override: `ACR_COUNT` config / INSERT into **`QARCH_CNFG_LABEL_OBJECT`** (`DBTBL_NM='ChkAcreageCount'`, `OBJECT_ID='QViewAcreage'`, client `APP_LAYER_CD`); display gate = `Acreage / DisplayCountFlag` config | ADO 1390010 |
| Cross References blank on ADS | `UPDATE LIS.QCNFG_SCREEN_CONTROL_DISP SET DISP_IND=1 WHERE SCREEN_NAME='ADS_AGMT_HDR_DTL' AND COL_TAG_NAME='XREF_VALUE'` | SF 24-00982892 |
| Provisions out of order / notes label unhelpful | Data cleanup to populate NULL **`DISPLAY_SEQ`** + config **`OrderByProvision` = DISPLAY_SEQ**; 2021.10 Hotfix 1 | ADO 1386173 |
| Provision Group name repeats per provision; Lease Form header missing | Known display defect (Group Form provisions) — ADO 1460610 (Proposed) | ADO 1460610 |
| Garbled characters in ADS labels (e.g. CO2 sequestration) | Fix the offending **code/decode** values (doc attached to case) | SF 24-00952351 |
| Migrated agreements can't run ADS | Data-fix script shared with client | SF 25-01043833 |

---

## 9. Cluster: QQM universe & BIAR/LCMBIAR object issues (G2 — route to BI team)

QQM = **SAP BusinessObjects Web Intelligence** over a per-client "QLS universe". Objects map universe names → `lis` tables/views. All fixes ship as **BIAR / LCMBIAR** files built by the BI team and deployed to the client's CMS; support's job is diagnosis + routing.

**Signatures & causes:**
- **Object errors on Run Query.** NEE's `Depth True Gross` and `Areal True Grs` objects were **linked to core tables instead of the client-suffixed views**: `lure_dep_acreages.dtr_acres` should have been `lure_dep_acreages_qnee.dtr_acres`, `lure_are_acreages.atg_acres` → `lure_are_acreages_qnee.atg_acres`. SQL from the objects returned nothing against core tables. Fix: universe remap + updated **lcmbiar** deployed (ADO #1801786; SF 26-01092072 "updated lcmbiar file provided"). Diagnostic move: *pull the SQL from the object and run it in the DB directly*.
- **Add / unhide objects.** "Add Formations to QQM" → universe updated to include the Formation tab (SF 24-00994882; ADO #1840769 — Formation folder under Depth folder, LCMBIAR attached). Hidden object exposed: `DESG_PAYMENTS.PIP_TYPE_CODE` under Billing/Payee Information, BIAR deployed to PRD (SF 24-00976933). Objects "turned on" via PRD deployment (SF 25-00999668). Missing eCalendar Reports folder → universe refreshed from **QLS Core Universe** (ADO #1834733; watch post-deploy CMC rights — "user isn't able to edit reports" follow-up #1840622).
- **Non-hosted clients:** adding objects (e.g. DOC ID column) is **billable professional services** (~1 OOS hour per object): BI builds the BIAR, client deploys to their universe; alternative offered was a direct DB query export (SF 25-01002524; repeat request 25-01051360).
- **Universe not retrieving data in UAT** after refresh — client-side config change resolved (SF 26-01081978). **Report corruption** after a deploy — reverted to pre-deploy backup (SF 24-00950539). Old custom reports needing updates after upgrade (SF 24-00968198). Object values blank though populated in QLS frontend (Width/Length — ADO #1852381, Proposed).
- **WebI quirks:** report block disappears after refresh → Report Property **layout changed horizontal → vertical** (SF 25-01053436); Java-applet install errors → set QQM WebI **View preference to HTML** instead of applet (SF 26-01116222).

**Fix recipe:** (1) Reproduce; pull generated SQL from the object; run in DB — if it errors/returns nothing, it's a universe mapping issue; (2) check whether the client has client-suffixed (`_q<client>`) acreage/depth views the object should target; (3) open a BI-team work item for universe update + LCMBIAR; (4) deploy to UAT first, verify object visible in QQM (not just in universe — old sessions/instances cache), then PRD; (5) keep a pre-deploy BIAR backup (24-00950539 precedent).

**Anchors:** ADO 1801786, 1840769, 1834733, 1852381, 1836970; SF 26-01092072, 24-00994882, 24-00976933, 25-00999668, 25-01002524, 25-01051360, 26-01081978, 24-00950539, 24-00968198, 25-01053436, 26-01116222.

---

## 10. Cluster: QQM login / availability runbook (mostly Cloud Ops, keep for triage speed)

Ranked by observed frequency in closed cases:

1. **Restart Tomcat + SIA** (Server Intelligence Agent) — resolves most "QQM down / login loop / SSO error" incidents (SF 26-01109173, 26-01109090, 25-01103495-style repeats, 26-01117146 "Restarting the SIA resolved the issue", 26-01123458 "QQM server needed a restart").
2. **Kerberos encryption types** (login fails after infra change): stop SIA + Tomcat, set in `krb5.ini`: `default_tgs_enctypes = aes256-cts-hmac-sha1-96 aes128-cts-hmac-sha1-96` and same for `default_tkt_enctypes`, start SIA then Tomcat (SF 26-01103402).
3. **SSO/identity config:** service account + service provider names updated to restore SSO (SF 25-01060789); Okta↔QLS user-ID mismatch (SF 25-01053546); Okta profile reset (SF 26-01112755); "password never expires" needed for federated service user (SF 25-01031384); backend **domain-mapping** mismatch between domain names and usernames (SF 25-01019064); stale certificate on federation server (SF 26-01114412).
4. **CMC permissions:** users needing CMC/report-edit rights added to the super-user group (SF 26-01081042).
5. **Citrix-delivered QQM:** .ica/profile issues → reprovision the Citrix user (SF 26-01122352, 25-01050623).
6. **Deleted QQM user = deleted Personal Folder + Inbox.** Reports in a deleted user's Personal Folder are unrecoverable unless previously saved elsewhere — warn before user deletions (SF 26-01110404, expected behavior).
7. Emailing WebI reports to Outlook / SMTP from the QQM app server is environment config; may be OOS work for non-hosted (SF 25-01035695, 25-01032012).

---

## 11. Cluster: Widgets blank, erroring, or not editable (G2)

**Signature:** dashboard loads but widgets show errors/blanks; user can't move/save widgets; new or upgraded users affected.

**Checklist (in order):**
1. **Widget security object missing from the user's group:** add **`QLSWIDGETACCESS`** to the security group and refresh cache (SF 24-00986832 — read-only users couldn't save searches on eCal widgets; SF 24-00953491 — script granted view-only account "the QLS widget security object"). Upgrade projects repeatedly hit this ("added sec grp" SF 25-01044422; "User Security changes" SF 24-00961289; missing privileges SF 25-01056306; custom security groups → widget errors in 2025.04 SF 26-01065384).
2. **Cannot move/rearrange widgets:** the group lacks **`QUCDASHBOARDEDITOR`** object (SF 24-00969250).
3. **All eCal widgets stopped after config change:** a **special character in the `OPENID-AUTHORITY`** config value broke widget auth calls — remove it (SF 24-00985729). Related platform failure mode: widget-count API bearer-token errors `Unable to create bearer token: invalid_client` after QFC platform consumption (ADO #1708087).
4. **Widgets don't load in PRD intermittently:** restart the **IIS application pool** (SF 26-01115740); services restart (SF 25-01022078).
5. **Post-refresh missing API configs** → errors on New Agreement Search from Dashboard; post-refresh scripts updated to set API config values (SF 23-00903685).
6. Legacy (v17 era) known issue: widgets missing at login, workaround = refresh, or edit URL replacing `ESUITE` segment with `QLS` (SF 22-00656712); resolved by GA release (SF 22-00577373).

**Not a defect:** "Export of widget views to Excel failing" — deprioritized by engineering; widgets are live-action screens, not reporting surfaces (SF 25-01046350, Closed-Deferred).

---

## 12. Cluster: Widget counts wrong, mismatched, or slow (G3/G4/G5)

**Signature:** eCalendar/Obligation widget numbers differ from the L2 screen or full Inbox, counts stuck at 0, or dashboard takes minutes / times out.

**Known fixed defects (G3 — verify client build first):**
- **Dashboard "Expiration Pending Count" ≠ Inbox Pending-Approval grid count** — ADO **#1712612**, Closed, hotfix-completed **2022.04 / 2023.04 / 2024.04 / 2024.10**. SF twins: 26-01065792, 23-00914720 (also flagged widget not respecting Land Division permissions), 23-00903267 (Inbox widget count ignores context filters — "Resolved in August hotfix").
- **eCal Inbox widget 500 error / counts 0 for Land-Admin user** — ADO **#1542261**, Closed, 2022.04 hotfix; MT null-ref, count APIs made async/optimized.
- **Upcoming / In Progress counts 0 with valid data** — ADO **#1657086**: count SQL assumed `ID_WF_ROUTE_SMPL_STEP` increments by 1 within a route (`QARCH_WF_ROUTE_SMPL_STEP`/`_DESK`); breaks with re-sequenced routes; validation should use `ROUTE_STEP_NO_SEQ`. If counts are 0 only for some routes, inspect the route's step-key sequencing.
- **Widget count APIs dead after platform (QFC) upgrade** — ADO #1708087 (`invalid_client` token errors in logs).

**Performance (large clients):**
- **Coordinator widget timeouts** (Overdue / Payment Exceeding / Unapproved Locked): counts built from three `SELECT DISTINCT` category subqueries joined across `EVENTS`, `QWF_TRAN_INBOX_EVENTS`, `QARCH_WF_TRAN_INBOX_BASE`, `STIPULATION_OBLIGATIONS`, `ALL_AGREEMENTS`, UNIONed then re-aggregated — degrades badly with large saved searches; DVN's DBA workaround simplified to distinct-record counts (ADO **#1854846**, New as of 2026-08 — open defect).
- **Runaway eCal widget-count SQL consuming DB CPU** (RESULT_CACHE-hinted count query) — ADO **#1721573** (Oxy), Closed, hotfix-completed 2022.04→2024.10.
- **2026.04 widget optimization + its regression:** #1755350 shipped search-SQL-as-subquery counts (QLS.Web PR 124978) + Oracle indexes (QLS.Database PR 125770) — 13–41× faster on 6M-agreement DBs, but *slower* on small/medium DBs; follow-up tuning under ADO **#1808308** (2026.04 Hotfix). If a client complains dashboards got slower after 2026.04, this is the thread.
- 2025.04 broad degradation with 10+ concurrent users incl. dashboard path — ADO #1724175 (Closed).

**Bad data making counts "wrong" (G4):** Obligations widget totals wrong because `STIPULATION_OBLIGATIONS.START_DATE` and `HOLD_PAY_CODE` were NULL for converted obligations — correction script in §Diagnostic SQL (SF 23-00927378).

**Config, not defect:** Agreement Search widget shows only 5 recent searches → config `AGREEMENT SEARCH WIDGET / NumberOfRecentSearches` in `QARCH_CNFG_CTRL` (SF 23-00927397, SQL below). Payments widget only shows **unbalanced payments with status ≠ Pay** (SF 24-00951693 — expected behavior).

---

## Known ADO items (quick reference)

| ADO | Title (abridged) | State / fixed-in | Confidence |
|---|---|---|---|
| 1836615 | RPT_019 missing LEFT JOIN `QCTRL_PMT_CC_ALLOC` (empty/partial output) | Proposed (open, 2026-07) | CONFIRMED open |
| 1743269 | RPT_019 duplicates payments with multiple cost centers | Closed; hotfix-completed 2023.04→2025.04 | CONFIRMED (tags) |
| 243465 | RPT_019/020 launch-message/title mixup | Closed | CONFIRMED |
| 1694486 | ADS fails with >30-char SEC_USER_NM + LAST_UPDT fields displayed | Closed; hotfix-completed 2022.04→2024.10 | CONFIRMED (tags) |
| 1407753 | ADS fails `Cannot set column 'TOTAL_ADS_REC'` with 10+ related wells | Closed | CONFIRMED |
| 1638136 | Bulk ADS emits FO/XML instead of PDFs (batch path) | Closed; hotfix-completed 2022.04/2023.04 | CONFIRMED (tags) |
| 1718170 | ADSNetLib FOP .jar security warnings (OpenJDK 11 dependency) | Proposed | CONFIRMED open |
| 1386173 | ADS provision order (NULL DISPLAY_SEQ) + notes label | Closed; 2021.10 Hotfix 1 | CONFIRMED |
| 1390010 | ADS acreage Count flag label ("Do Not Count") config | Closed | CONFIRMED |
| 1460610 | ADS provision-group name repeats; Lease Form header missing | Proposed | CONFIRMED open |
| 1801786 | QQM universe objects linked to core instead of `_q<client>` views | Closed (LCMBIAR deployed) | CONFIRMED |
| 1840769 | QQM add Formation folder (DMB) — LCMBIAR workflow | Closed | CONFIRMED |
| 1834733 | QQM missing eCalendar Reports folder objects (universe refresh) | Closed | CONFIRMED |
| 1852381 | QQM Width & Length objects return no values | Proposed | CONFIRMED open |
| 1712612 | eCal dashboard vs Inbox Expiration count mismatch | Closed; hotfix-completed 2022.04→2024.10 | CONFIRMED (tags) |
| 1542261 | eCal Inbox widget 500 / counts 0 (MT null ref) | Closed; 2022.04 hotfix | CONFIRMED (tags) |
| 1657086 | Upcoming/In-Progress counts 0 with re-sequenced routes | Closed | CONFIRMED |
| 1708087 | Widget count APIs broken after QFC consumption (invalid_client) | Closed | CONFIRMED |
| 1854846 | eCal Coordinator widget timeouts (UNION/DISTINCT count SQL) | New (open, 2026-08) | CONFIRMED open |
| 1721573 | eCal widget-count SQL consumes DB CPU (Oxy) | Closed; hotfix-completed 2022.04→2024.10 | CONFIRMED (tags) |
| 1755350 / 1808308 | 2026.04 dashboard-widget count optimization (PR 124978/125770) + small-DB regression fix | RfR / Closed 2026.04 Hotfix | CONFIRMED |

"Fixed-in" from hotfix tags = INFERRED build unless release notes confirm for the client's exact train.

---

## Diagnostic SQL (Oracle, `lis` schema — all taken verbatim from solved cases)

**1. What did the eCal workflow scrubber (ECALWFSCRU) touch in a time window?** (SF 25-01041448)
```sql
SELECT a.AGMT_NUM, e.* FROM LIS.EVENTS e
JOIN LIS.ALL_AGREEMENTS a ON e.ARRG_KEY = a.ARRG_KEY
WHERE e.EVNT_KEY IN (SELECT evnt_key FROM lis.events_log
   WHERE SCR_LABEL NOT IN ('Approval Status')
     AND UPDT_DATE >= TO_DATE('08/23/2025 08:21:11 AM','MM/DD/YYYY HH:MI:SS AM')
     AND UPDT_DATE <  TO_DATE('08/23/2025 08:22:00 AM','MM/DD/YYYY HH:MI:SS AM'))
ORDER BY e.EVNT_KEY;
-- window = QARCH_QUEU_PROCESS start/end for the ECALWFSCRU run
```

**2. Obligations-widget correction: NULL START_DATE / HOLD_PAY_CODE on converted obligations** (SF 23-00927378)
```sql
ALTER TABLE LIS.stipulation_obligations DISABLE ALL TRIGGERS;
UPDATE LIS.stipulation_obligations
SET START_DATE = (SELECT EFFTV_DATE FROM LIS.ALL_AGREEMENTS
                  WHERE LIS.stipulation_obligations.ARRG_KEY = LIS.ALL_AGREEMENTS.ARRG_KEY)
WHERE stip_catg_code = 'OBL' AND START_DATE IS NULL;
UPDATE LIS.stipulation_obligations SET HOLD_PAY_CODE = 'OPN'
WHERE stip_catg_code = 'OBL' AND END_DATE >= TO_DATE('27-11-2023','dd-mm-yyyy') AND HOLD_PAY_CODE IS NULL;
UPDATE LIS.stipulation_obligations SET HOLD_PAY_CODE = 'CLS'
WHERE stip_catg_code = 'OBL' AND END_DATE <  TO_DATE('27-11-2023','dd-mm-yyyy') AND HOLD_PAY_CODE IS NULL;
ALTER TABLE LIS.stipulation_obligations ENABLE ALL TRIGGERS;
-- adjust the cutover date to the client's go-live
```

**3. Unblank a hidden ADS column (example: Cross References)** (SF 24-00982892)
```sql
UPDATE LIS.QCNFG_SCREEN_CONTROL_DISP
SET DISP_IND = 1, UPDT_OPER = 'UPGRADE', UPDT_DATE = SYSDATE
WHERE SCREEN_NAME = 'ADS_AGMT_HDR_DTL' AND COL_TAG_NAME = 'XREF_VALUE';
```

**4. Widen the Agreement Search widget's recent-searches list** (SF 23-00927397; layer code per client)
```sql
INSERT INTO qarch_cnfg_ctrl (KEY_GRP_NM, KEY_NM, KEY_DESCR, KEY_VALUE,
  KEY_VALUE_ALLOW_NULL_IND, KEY_VALUE_TYPE_CD, KEY_VALUE_MIN, KEY_VALUE_MAX,
  KEY_VALUE_CODETABLE_ID, ALLOW_USER_OVERRIDE_IND, ENVIRONMENT_SPECIFIC_IND,
  USER_ID, UPDT_DT, APP_LAYER_CD, HIST_IDX)
VALUES ('AGREEMENT SEARCH WIDGET','NumberOfRecentSearches',
  'Number of recent searches to display in the Agreement Search L1 Widget',
  '10', 0, 1, 0, 20, NULL, 1, 0, '<USER>', SYSDATE, 'QINV', 11196);
```

**5. Repro/verify the ADS long-username defect (#1694486)** — enable the fields, then test with a >30-char name:
```sql
UPDATE QCNFG_SCREEN_CONTROL_DISP SET DISP_IND = '1'
WHERE SCREEN_NAME LIKE '%ADS%' AND COL_TAG_NAME = 'LAST_UPDT_BY';
UPDATE QCNFG_SCREEN_CONTROL_DISP SET DISP_IND = '1'
WHERE SCREEN_NAME LIKE '%ADS%' AND COL_TAG_NAME = 'LAST_UPDT_DT';
UPDATE qarch_sec_user SET sec_user_nm = '<ANY NAME LONGER THAN 30 CHARACTERS>'
WHERE sec_user_id = '<USER_ID>';
```

**6. RPT_1029 security-layer check** (pattern from SF 26-01103127)
```sql
SELECT OBJECT_ID, APP_LAYER_CD FROM lis.QARCH_SEC_OBJECT WHERE OBJECT_ID = 1029;
-- expect APP_LAYER_CD = 'QLS' (not 'QINT'); then compare client-layer rows in
-- QARCH_CTRL_PROCESS_REPORTS / QARCH_RPTS_DEFINE against a working report (e.g. RPT_999).
```

---

## Expected-Behavior FAQ (close at G1)

- **"Payments widget doesn't show my payment."** By design it pulls only **unbalanced** payments with any status **besides Pay** (SF 24-00951693).
- **"Exhibit A doesn't show book/page for some documents."** The report only pulls recordation info for documents of the **'Original' document type** (SF 23-00900000).
- **"Exhibit A right border is cut off."** Visual-only; data is complete. Known low-priority core defect (SF 25-01000782).
- **"RPT_019 company share isn't the full payment amount."** Post-#1743269, the Cost Center Amount column = payment amount × that cost center's allocation %, and Grand Total sums those (SF 25-01024065, ADO 1743269).
- **"We deleted a QQM user and their reports are gone."** Deleting the BusinessObjects user removes their Personal Folder and Inbox permanently; export/copy reports first (SF 26-01110404).
- **"Widget counts differ from a colleague's."** Widgets respect the user's context filter (gear icon / favorite saved search) and Land security; same-user mismatch vs the L2 screen is the defect family in §12 — check build.
- **"Can we get widget grids exported to Excel?"** Not supported; engineering deprioritized (SF 25-01046350).
- **"Add a new column to QQM for a non-hosted client?"** Billable OOS (~1 hr/object): BI builds a BIAR, client deploys (SF 25-01002524).

---

## Escalation

- **QQM universe/BIAR builds, CMC administration, WebI server restarts** → BI team (they own universes + LCMBIAR generation; hosted-client deploys via Cloud Ops). Provide: client, environment (UAT/PRD), object names, generated SQL, error screenshot.
- **QQM/Citrix/Okta outages, Tomcat/SIA, federation certs** → Cloud Ops (QCloud). These are not product defects; RCA cases exist (SF 26-01114888, 26-01114412).
- **Report/ADS/widget code defects** → ADO bug in `Quorum\North America\Upstream\Land RnD` (current) referencing the matching historical item from the Known-ADO table; legacy escalations live in `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land`. Repos: `Quorum.QLS.Web` (widget count APIs, controllers), `Quorum.QLS.ServiceCore` (MT/ADS `GetADSFileContent`), `Quorum.QLS.ADSNetLib` (FOP/PDF), `Quorum.QLS.Database` (views, indexes), `Quorum.QLS.Metadata` + `<CLIENT3>.QLS.Metadata` (report definitions, config layers).
- **Hotfix availability**: version fixes ride the `YYYY.MM Hotfix` tags / `hotfix/17.2x.y` branches — confirm the client's train before promising "already fixed" (label INFERRED otherwise).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
