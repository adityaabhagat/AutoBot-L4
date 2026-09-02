# SKILL: QPTM Security / Admin / Config / Integration — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management; midstream/interstate gas)
**Source:** Azure DevOps **Bugs** (Closed/Resolved) under `Engineering\Energy Transportation` + `Engineering\Maintenance\Midstream and Transportation`, mined for the **Security / Admin / Config / Integration** functional area. Companion to the Nomination, Allocation, Reporting, and Capacity-Release QPTM ADO skills.

**Use When:** a QPTM case is about *who can see/do what* (internal vs external user, security privileges, BA visibility, login), *configuration not taking effect* (global/TSP config keys, code tables, Code Decode Maintenance, rounding), *system administration* (Menu Editor, Sitemap, batch-process framework, Business Associate setup, batch messages), or *cross-system integration* (QPTM↔TIPS, EDI inbound/outbound, IPWS export, FlowCal / Integration Platform). For nomination validation, allocation math, settlement, or report *content* logic, use the matching companion skill instead.

> **Evidence base:** WIQL matched **1,746** Closed/Resolved bugs across both area branches on the functional title terms (Security, user, login, SSO, MFA, business associate, config, integration, batch process, location, meter, code table, QQM). Those terms are broad — most hits are Nomination/Allocation/Reporting bugs that belong to other QPTM skills. **~95** of the most-recent matches map to this area; **~56 were deep-read** (description + repro + full dev comment thread + linked PRs). Every root cause below is quoted from a real ADO bug's dev comments/PR; no build number is invented. **`Microsoft.VSTS.Build.IntegrationBuild` is empty on every bug** in this set — fixed-in-build values are **inferred from the iteration path (YY.NN) and "queued for next QPTM <ver>" / HOTFIX tags, and marked "(inferred — confirm in release notes)".**

> **Product-overlap caveat:** the `Maintenance\Midstream and Transportation` branch is **mixed QPTM + TIPS**. The functional terms pulled in TIPS items (Paystation/Settlement-Statement/User-Defined-Formula/NGL-Offload/Keep-Whole, and TIPS Allocation Group Maintenance). Those were **dropped** from the clusters below. A few bugs are **genuinely shared QPTM+TIPS+ESuite** (security-user setup, notice types, batch-process sequence, config-metadata security) because the screens live in the shared **ESuite / QFC** layer — these are flagged inline. When in doubt, the giveaway is the repo/layer: shared = `Quorum.QFC.*` / `Quorum.ESuite.*`; QPTM-only = `Quorum.QPTM.*`.

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cluster | First check |
|---|---|---|
| "Works in Classic, not in Web" for a **config key** (e.g. `ALLOW_BA_MISMATCH`, `VALIDATE_MDQ_REC_DEL`) | **C — Web ignores config; uses validation** | Web is **validation-driven via Object Usage**, not config-key-driven. §4 |
| Internal user gets **blank / empty report**; external user sees correct | **A — SEC_USER_ID / module-type handling** | Internal user's `SEC_USER_ID` = **empty string** (not NULL) or ESUITE module `USER_TYPE_CD` is NULL → code treats as external. §3 |
| External user **sees BAs / data not assigned to them** (report or picklist) | **B — external data exposure** | Report view / picklist missing the BP_NO security filter. §3 |
| "Update allowed **without security privileges**" in Web (PDA Submission, Config screens) | **D — Web screen skips privilege check** | Web screen not checking the security Object ID / code table 296. §5 |
| Can't **save in Code Decode Maintenance** in Web but **can in Classic** | **E — code-table metadata drift** | Column missing from code-table **definition metadata**; FK error. §6 |
| **Global/TSP config key missing**, log says "missing from `qarch_cnfg_ctrl`" | **C — missing config keys** | Add key to PLTM-layer metadata or script TSP config; default in code is usually 0. §4 |
| Rounding/precision **config not honored** (hard-coded decimals) | **C — hard-coded rounding** | A prior client code change hard-coded the decimals. §4 |
| **EDI** outbound sends Location ID vs Interconnect Location ID wrong | **G — EDI loc/interconnect** | `USE_INTERCONNECT_LOC_FOR_RQCF/SQOP/RRFC` per-transaction config. §8 |
| Meter/contract **timeslice in QPTM/QCM not syncing to TIPS** | **H — QPTM↔TIPS sync** | `SEXTN_*_QRMTIPS` not written; Integration Module Setup config or Web DAL gap. §9 |
| **IPWS** export wrong/empty (locations, agents, batch list, OACY) | **I — IPWS** | Staging-table column width, security object in core, batch list, suppress-OACY filter. §10 |
| **FlowCal → eSuite → QPTM** meter/data not transferring | **H — Integration Platform** | TIPS object validation blocking the event; override at client layer. §9 |
| **Login crash** in QCM/Classic, app-tier / on-prem | **F — login / startup** | Usually deployment/env (App Sense, bad patch package, framework installer), not a code bug. §7 |
| **Menu Editor / Sitemap** screen broken or item invisible | **J — admin screens** | Menu item missing Security ID/URL; obsolete controller cast. §11 |
| **Web vs Classic parity** on batch-process params / screens (multiple gas-day) | **J — admin screens** | QFC param `Multiple Input` not splitting Date type; refresh cache. §11 |
| **Console error / "jQuery remains active"** on a Web screen | **J — Web JS** | Usually a null-check; often AT-only, not user-facing. §11 |

---

## 2. Decision Tree

```
QPTM Security / Admin / Config / Integration case
│
├─ SECURITY / "who sees what"?
│   ├─ Internal user gets BLANK report, external is fine        → §3 Cluster A  (SEC_USER_ID empty-string / ESUITE module USER_TYPE_CD NULL → treated as external)
│   ├─ External user SEES data/BAs not theirs (report/picklist) → §3 Cluster B  (view/picklist missing BP_NO security filter; ALR37, SAVR)
│   ├─ External report HANGS / times out                        → §3 Cluster B  (external view joins QARCH_SEC_USER unfiltered → millions of rows; ALR24)
│   └─ Web allows UPDATE without privileges                     → §5 Cluster D  (Web screen not checking Object ID / code table 296)
│
├─ CONFIG not taking effect?
│   ├─ "Works in Classic, not Web" for a config KEY             → §4 Cluster C  (Web is validation-driven, not config-driven; toggle the Object-Usage validation)
│   ├─ Log: config key "missing from qarch_cnfg_ctrl"           → §4 Cluster C  (add key to PLTM metadata / TSP config; default in code ≈ 0)
│   ├─ Rounding/precision config ignored                        → §4 Cluster C  (hard-coded decimals from a prior client change)
│   └─ Can't save Code Decode Maintenance in Web (Classic ok)   → §6 Cluster E  (column missing from code-table definition metadata; FK on code table)
│
├─ INTEGRATION?
│   ├─ EDI outbound wrong loc (RQCF/SQOP/RRFC)                  → §8 Cluster G  (per-transaction USE_INTERCONNECT_LOC_FOR_* config)
│   ├─ Timeslice not syncing QPTM/QCM → TIPS (SEXTN_*_QRMTIPS)  → §9 Cluster H  (Integration Module Setup config; or Web must write the QRMTIPS extension via Esuite DAL)
│   ├─ QPTM → TIPS nomination import (CSV/XLSX)                 → §9 Cluster H  (header rows, UP/DOWN vs PATH; NOMIMPEXTS)
│   ├─ FlowCal/IP event not creating QPTM/eSuite data           → §9 Cluster H  (TIPS object validation blocking; override at client layer; or IP perf)
│   └─ IPWS export wrong/empty                                  → §10 Cluster I
│
├─ ADMIN?
│   ├─ Menu Editor / Sitemap broken or item invisible           → §11 Cluster J
│   ├─ Web vs Classic param/screen parity (multiple gas-day)    → §11 Cluster J
│   ├─ Batch-process framework (Read Queue, PROCESS_LOG_ID seq) → §11 Cluster J
│   ├─ Business Associate save / orphan / FK                    → §11 Cluster J  (Web writes SCTRL_BA_ADDRESS but not SVALD_BA_ADDRESS → FK)
│   └─ Console error / jQuery remains active                    → §11 Cluster J
│
└─ LOGIN crash / startup warnings (QCM/Classic, on-prem)        → §7 Cluster F  (deployment/env: App Sense, bad patch package, framework installer, bootstrap warnings)
```

---

## 3. Cluster A & B — Security: user-type handling, blank reports & data exposure

**The dominant QPTM security defect family.** Reports and picklists key off the logged-in user's **security-user record**, and there are two recurring root causes: (A) an **internal** user's identity is mis-detected so they get *no* rows, and (B) an **external** user's data filter is missing/wrong so they get *too many* rows (other shippers' data) — or the unfiltered external view is so large the report hangs.

### Cluster A — internal user gets blank / empty report (SEC_USER_ID / module-type)
- **#255923 (ENT, TIPS report run from QPTM stack):** "subreport record selection… does not correctly handle situations where the user is internal and the `SEC_USER_ID` value is an **empty string**." When SEC_USER_ID is `''` (Oracle internal user), the record-select returns no rows → blank subreport. The bug is "how we treat **empty strings vs actual nulls**." Collateral from #130952 merging an MSSQL-only client fix back to core. **Fix:** correct the record-selection formula for the empty-string internal case. Iter = Maintenance; tag *ENT 2020.03* → fixed-in-build ~**2020.03 / merged to 2020.11, 2021.04, develop** (inferred — confirm in release notes).
- **#1786782 (HPE):** internal user got **empty reports in Web** because the security setup had the **ESUITE/ENGS module `USER_TYPE_CD` = NULL**; "the code reads that as external." Root causes found by dev: extra rows in **`QARCH_META_MOD_DEFINE`** in the `QRMTIPS` DB tripped the code into looking at **ENGS instead of ESuite**, and the **`QARCH_CODE_RPT_TYPE`** report-type 609 existed at the client (QHPE) layer for ENGS/QPTM/QTIP making ENGS discover remote TIPS reports. Code in **`Quorum.QFC.ProcessService`** flips the module to EXT when the **Gathering module is enabled**. **Fix:** one-off script to remove the extra `QARCH_META_MOD_DEFINE` rows from the TIPS DB + null-out spurious `QARCH_SEC_USER_MOD.USER_TYPE_CD`; deployed to HPE UAT/PRD. **Workaround that *masks* it:** set the ESUITE module to INTERNAL for the user (but an old engineering ticket says you shouldn't — leaving it INT for external users is wrong).

> **Diagnostic for Cluster A:** check `QARCH_SEC_USER_MOD` for the user — modules the user can drive from Classic should have `USER_TYPE_CD` NULL, others should resolve to INT/EXT correctly. A blank internal report = the engine thinks the internal user is external (empty-string/NULL → treated as external). See §12-A SQL.

### Cluster B — external user sees / can pick data not assigned to them, or report hangs
- **#1764600 (ENT, ALR_37, SF 25-01035363):** the core **ALR_37 external** report exposed unrelated BA data to external users for report level 101. The external views check the user's BA against `SP_BP_NO`/`OPERATOR_BP_NO`/`CONF_PARTY_BP_NO`/`OPER_AGENT_BP_NO`. **Fix:** for any Account-Activity-Type (AAT) **≥ 5** (i.e. *not* nomination level), **exclude `OR BP.BP_NO = AA.CONF_PARTY_BP_NO`** from views `ALRPTS_37_AL_DWNLD_DLY/MTH_XVW` + `ALALL_RPTS_37_*`. DB view change, cherry-picked to 2024.04 / 2024.10 / 2025.04 / 2025.10 (needed for a 12/26 hotfix). Iter 26.01 (inferred — confirm in release notes).
- **#1734720 (ONM, SF 25-01022205, SAVR):** the Shipper Allocated Volume Report **BA picklist let external users see BAs not assigned to them.** **Fix:** picklist now applies external-user security so it only shows BAs on the user's integrated security-user BA tab (internal users still see all). PR 117617.
- **#1661117 / #1742657 (ONK, SF 24-00946909, ALRX24 / ALR24 Allocation Imbalance):** the **external** Daily-Imbalance-with-Reversals report **hangs for hours and returns blank** for external users. Root cause (long dev dive): the **external view `ALRPTS_24_DLY_IMB_REV_XVW` joins `QARCH_SEC_USER` and returns *all* rows for *all* users whose BP_NO matches** (~300k+ rows vs ~19k internal), and the report's `PROD_MTH` logic used a clumsy Month/Year `<=`/`>=` instead of `PROD MTH =`; plus ~13 years of `ALHIST_ALLOC` history (10M+ rows). **Fix:** rewrite the external view to filter by the logged-in `SEC_USER_ID`→BP_NO subquery (seconds instead of hours), align AL24 views (VW *and* XVW, MSSQL *and* Oracle) to the AL03 prod-month pattern, and remove a duplicate/incorrect column (`REC_LOC_NM` written twice where `REC_ZONE_NM` was intended). Also offered as a perf/data fix (purge `ALHIST_ALLOC`). Iter Engineering; DB ticket #1692315.

**Cluster B fix recipe:** when an external shipper "sees data that isn't theirs" or a shipper picklist is too broad → the report **view** or **picklist query** is missing the BP_NO/SEC_USER security predicate (or applies it at the wrong AAT). When an **external** report *hangs*, suspect the external `_XVW` joining `QARCH_SEC_USER` unfiltered. Fix is a **DB view change** (both VW & XVW, both MSSQL & Oracle) — log a DB ticket and cherry-pick across releases.

**Bug IDs:** A → 255923, 1786782 · B → 1764600, 1734720, 1661117, 1742657.
**Linked SF:** 25-01035363 (1764600), 25-01022205 (1734720), 24-00946909 (1661117).

---

## 4. Cluster C — Configuration: Web ignores config keys, missing keys, hard-coded values

**The single biggest "it's not a bug, it's how Web works" trap.** In Classic, behavior is driven by **global/TSP config keys**; in **Web**, the same behavior is frequently driven by **enabling/disabling a validation rule via the Object Usage screen** (still metadata, but a *different* lever). Toggling the config key in Web does nothing.

| Symptom | Root cause (from dev comments) | Fix / fixed-in-build (inferred) | Bug / SF |
|---|---|---|---|
| `ALLOW_BA_MISMATCH` global config not honored in My Q Customer Account Maintenance (can add cross-BA contract in Classic, not Web) | Web is **validation-driven, not config-driven**: it checks whether validation `QTIPSValidationCustomerAccountMaintenance0007_CtrBaMismatches` is enabled, **not** the config value | Disable that validation at the client layer to allow it. **Caveat dev flagged:** Web still doesn't *read* `ALLOW_BA_MISMATCH`, so disabling the config doesn't re-block — known parity gap | **#1778592** / 26-01066150 (HEP) |
| `VALIDATE_MDQ_REC_DEL` turned off but Web still throws `K_RFSME020` MDQ-mismatch error (Classic respects it) | Same pattern: in Web the **`ContractMaintenance0008` validation in Object Usage** must be disabled; the global config alone doesn't gate Web | Enable/disable the matching Object-Usage validation; hotfix 1/23 | **#1764767** / 25-01042893 (HEP/Midship) |
| Config keys "missing from `qarch_cnfg_ctrl`" in MT logs (`NUM_STREAMING_OBJECTS`, `SHOW_UP_DN_CONTRACT_PICKLIST_IN_GRID`, `DISABLE_NOMINATION_SUBMISSION_BY_CONTRACT`, `NAESB30`) | Keys absent from core metadata; **code default ≈ 0** when missing | Add missing keys to **QPTM metadata at the PLTM layer with default 0**; script TSP-config ones | **#1744270** / 25-01031118 (ETC) — HOTFIX |
| `GAS_VOL_PRECISION` (round to 1 decimal) **not honored** — values rounding to 2 | A prior **Pembina** change (commit fa61d6f / PR 22040, WI 173612 preferential-loading) **hard-coded rounding to 2 decimals**, overruling the config; Conifer (ACL) inherited it on upgrade | Restore config-driven precision for preferential loading | **#1723064** (ACL Conifer) |
| Invoice qty differs — rounding to 4 decimals in code vs 10 in DB | Hard-coded `QGMUtility::Round(...,1000)` in `QVpEstimatedActualMaint*.cpp` (lines ~1374/1378, 924/930, 1458/1462) should be `1000000000` | Extend the round factor; hotfix to client build | **#1316779** / 20-00093450 — *Patch Immediately* |
| Code table missing a column/decode value (e.g. `PRE_TAX_IND`, `SUMMARY_QTY_IND` on CT 2401 / 37014) | Column added to DB table but **never added to the code-table metadata** → not visible/editable | Add the columns/rows to code-table metadata (core change) | **#1557785** (ONG, CT 2401), **#155977** (GLE, CT 37014) |

**Cluster C fix recipe:** First decide which lever applies. **Classic** → set the config key (`qarch_cnfg_ctrl` global or TSP layer) and refresh MT + pipeline caches. **Web** → the gate is almost always an **Object Usage validation rule**, not the config key — find the matching `*Validation*` rule and enable/disable it at the client layer. For "missing config key" log noise → add to PLTM metadata (default usually 0; **confirm the intended default with products — #1744270 shows devs disagreed: `NAESB30` core default is 1, not 0**). For rounding/precision → look for a **hard-coded round factor** introduced by a prior client change.

---

## 5. Cluster D — Web screen skips a security-privilege check

A focused, recurring **defect** family (2024-2026): Web maintenance/config screens that **fail to enforce the security Object ID** a user would need, so under-privileged users can edit.

- **#1798371 (ENT 2024.04, PDA Submission):** the Web **PDA Submission** screen does **not** check Object ID **`QVPPREDETERMINEDALLOCATIONSUBMISSION`** — any user with global query privileges could update all fields. **Fix:** enforce the object's privileges; verified by creating a group with the privilege. PR 127491/127533/127535/127538. Pushed to **2024.04.1.49** (per dev comment) — and develop / 2024.04 / 2026.04 (inferred). Iter 26.10.
- **#1798373 (ENT 2026.04, Config Settings screens — QPTM/TIPS/ESUITE, *shared*):** Web config screens **don't check code table 296 (`QARCH_SEC_EDIT_METADATA`)**. Configs `ALLOW_EDIT_METADATA` (top layer editable) and `ALLOW_EDIT_LOWER_LEVEL_METADATA` (default FALSE) should gate metadata edits by layer; Web ignored them and saved at NON-TEST / lower layers regardless. **Fix:** Web honors code table 296 + the two configs per layer. **Needs PRs in develop, 2024.04 (QFC Metadata 17.21.X) and 2026.04 (QFC Metadata 17.25.X)** per Dianne Miller. Iter 26.09.

**Cluster D fix recipe:** if a user can do something in Web their security shouldn't allow → the Web screen is missing the `IQSecurityObjectAttribute` / Object-ID check (or the code-table-296 metadata-layer check). This is a real code defect, not config. Provide the Object ID and the layer; route to engineering. The fix lands in the **QFC/ESuite metadata + Web** layers and must be cherry-picked across the client's release line.

**Bug IDs:** 1798371, 1798373. **Linked SF:** internal (ENT project defects).

---

## 6. Cluster E — Code Decode Maintenance: saves in Classic, fails in Web

A narrow but repeatable pattern: a code table can be edited in **Classic** but **not in Web**.

- **#1797552 (CT 26136):** new row won't save in Web. Root cause: column **`SCREEN_READ_ONLY_IND`** existed in the DB but was **missing from the code-table *definition* metadata** that the Web grid reads → save fails. **Fix:** add the missing column to CT 26136's definition (parallels CT 26065 which already had it). Iter 26.10; *queued for next QPTM 2025.10 & 2026.04* (inferred).
- **#1625007 (IPWS, CT 52011 `QXREF_DEFAULT_TSP`):** add/update threw a **DB foreign-key error**. The client could never add their own rows before; fix enabled Add/Update. **Note from dev:** **Delete still doesn't work** — a known limitation of classic code tables with effective dates. Iter 23.20 (inferred → ~2023.20).

**Cluster E fix recipe:** "saves in Classic, not Web" on a code table → compare the code-table **definition metadata** to the DB columns; a column present in the DB but absent from the definition breaks the Web grid save. FK errors on code-table add/update are a metadata/relationship gap. Delete on effective-dated classic code tables is generally unsupported.

**Bug IDs:** 1797552, 1625007.

---

## 7. Cluster F — Login crash / startup warnings (deployment & environment)

**Usually NOT a product code bug** — these resolve as deployment/environment/packaging issues. Recognize them to avoid a code escalation.

| Symptom | Root cause | Resolution | Bug / SF |
|---|---|---|---|
| QCM crashes on Login, DB dropdown empty, all users (PRD + lower) | Client-side **`App Sense`** running on user machines (had happened exactly 4 yrs prior, SIRT 184068) | Turn off App Sense — **not a Quorum issue** | **#253775** (ETP) |
| `OutOfMemoryException` on QCM login after Patch 25 | **Bad GUI patch package** (Patch 25 ClassicGUI) built in TeamCity by a since-departed dev; MT/Batch/Reports fine | Back-install the prior working GUI package (Patch 23); long-term = rebuild the patch in TeamCity | **#1585134** / 23-00885986 (ALT) — *Rejected* (env) |
| "Bootstrap" warning messages on Classic login (on-prem, multiple clients NMGC/DCP/PGAS) | New bootstrap/configurable-services messages introduced in **QFC 2019.10**; timing issue, retries succeed, just noisy | Long-term = config **`DISPLAY_SYSTEM_MSGS`** to suppress system warnings in the WinForms dialog; QFC platform change, full regression (not hotfixed) | **#187862** (NMGC) |

**Cluster F fix recipe:** for a login crash, first check **client-side / on-prem** factors (security software like App Sense, the exact patch package deployed, the framework-installer version) and **where the GUI logs actually live** (down in the install dir next to the .exe — clients often look too high in the path, #1585134). If the GUI package is bad, back-install the last known-good package rather than chasing a code fix. Bootstrap-warning noise on login is the known QFC 2019.10 cosmetic issue — suppress via `DISPLAY_SYSTEM_MSGS`.

**Bug IDs:** 253775, 1585134, 187862.

---

## 8. Cluster G — EDI: Location ID vs Interconnect Location ID (outbound)

A self-inflicted-regression cluster around which location identifier outbound EDI sends.

- **#1678265 (ENT, SF 24-00960415):** outbound **RQCF, SQOP** should send **Location ID** and **RRFC** the **Interconnect Location ID** (NAESB 3.0+). The single legacy config **`USE_INTERCONNECT_LOC_FOR_RRFC`** controlled *all three together* — ON sent interconnect for all, OFF sent location for all. **Fix:** code change so RQCF/SQOP send Location ID and RRFC sends Interconnect ID (driven by per-transaction config). *ENT Hotfixed*; queued 2020.03 (inferred). Repo: EDI datasets (`G873*` outbound).
- **#1694083 (TEP/Tallgrass, follow-on):** the #1678265 ENT change **broke Tallgrass/Williams** who relied on the old behavior — after upgrading 2024.04, RQCF started sending Location ID and trading partners rejected files. Dev consensus: the ENT fix **should have been opt-in.** **Fix:** introduce **per-transaction configs `USE_INTERCONNECT_LOC_FOR_RQCF` / `_SQOP` / `_RRFC`** so each client/transaction is independently controlled. Cherry-picked across releases. (Treated as "technically an enhancement" but fixed urgently as a regression.)

**Cluster G fix recipe:** when an outbound EDI confirmation file has the wrong location identifier, the lever is the **`USE_INTERCONNECT_LOC_FOR_<TXN>`** config **per transaction** (RQCF/SQOP/RRFC). Also confirm the TPA's **grammar set is NAESB 3.0+** (the change only applies on 3.0+; TPA 20 = 2.0) and the **confirming party on the locations matches the BP on the TPA** (else the run finds nothing). Beware: changing this for one client historically affected all — verify the per-transaction config exists in the client's build.

**Bug IDs:** 1678265, 1694083. **Linked SF:** 24-00960415. **Clients:** ENT, TEP (Tallgrass), Williams.

---

## 9. Cluster H — QPTM ↔ TIPS & Integration Platform (FlowCal)

Cross-system sync between QPTM/QCM and TIPS (shared eSuite control tables) and inbound data via the Integration Platform.

### Timeslice sync: QPTM/QCM → TIPS (`SEXTN_*_QRMTIPS`)
- **#226309 (BLU, contract):** timeslicing a contract in QCM updates `SEXTN_CTR_HEADER_QCM` + `SCTRL_CTR_HEADER` but **not `SEXTN_CTR_HEADER_QRMTIPS`** → TIPS shows the timeslice (sourced from `SCTRL`) with no data, and an overlap error on update. Root cause: **missing/incorrect Integration Module Setup** record (`SARCH_CNFG_INT_MODULE`, shared between the apps). **Fix:** correct the Integration Module Setup (delete the spurious eSuite app-layer record) + restart QPECs. (Config, not code — resolution was in linked #173632.)
- **#1774497 / #1763785 (ENT, meter — "Defect 54"):** can't timeslice a meter from **Web** Location Maintenance when the meter exists in **both QPTM and TIPS** — "orphan TIPS meter" error. Classic works; Web doesn't. Root cause: Web validation **`QPTMLocationMaintenance034_ValidateChangeOfDate`** blocks the timeslice, and Web (unlike Classic) **does not insert the matching row into `SEXTN_MTR_HEADER_QRMTIPS`**. Tables involved: `SCTRL_MTR_HEADER`, `SCTRL_MTR_FACILITY` (QPTM) ↔ `SEXTN_MTR_HEADER_QRMTIPS` (TIPS). **Fix:** modify the rule to match Classic for QRMTIPS data, and add explicit Web code to insert/update/delete `SEXTN_MTR_HEADER_QRMTIPS` via the **eSuite DAL** (`SMeterHeaderQRMT...`). HOTFIX 11/28/2025; cherry-picked 2025.04 / 2025.10 / develop. **Interim workaround:** end-date in TIPS Meter Definition first, then create the new QPTM timeslice. (ENT-specific integration; not in CORE.)

### QPTM → TIPS nomination import
- **#1706821 (HEP):** moving noms QPTM→TIPS required a manual CSV→XLSX PowerShell step (TIPS import wanted XLSX + two header rows). **Fix:** TIPS **`NOMIMPEXTS`** import now accepts **CSV directly** with mixed-case headers. Two gotchas dev hit: TIPS only starts reading data at **row 3** (first gas day was being lost with no warning), and HEP's **PNT** noms differ receipt vs delivery so they had to send **UP/DOWN** records, not just the PATH record (PATH duplicates receipt=delivery). Maintenance: Escalated.

### Integration Platform / FlowCal
- **#1811840 (XCL, SF 26-01102718):** meter data in FlowCal + PGAS records in eSuite but **no records flow to QPTM**. Likely an **IP** issue — messages complained about a **TIPS object**; **workaround:** disable that object validation by **overriding at the `QXCL` client layer** (same pattern as a prior DSU issue) + republish the create event + restart services. Resolved under a related IP WI.
- **#1716345 (HEP):** enabling **`metersampledaily`** in the Integration Platform made QPTM **and** TIPS unusable (reports/screens/picklists spinning) within minutes — the **eSuite API became unreachable / IIS backed up** under the event volume (Polly timeout, socket aborts). **Fix:** performance improvements to the meter-add path (daily & monthly liquid analysis). Disabling the flow restores performance immediately.

**Cluster H fix recipe:** for **timeslice not syncing to TIPS**, check the **Integration Module Setup (`SARCH_CNFG_INT_MODULE`)** first (226309), and remember **Web is stricter than Classic** — it may block via a validation and skip writing the `SEXTN_*_QRMTIPS` extension row (1774497). Verify both core (`SCTRL_*`) and the `*_QRMTIPS` extension are in sync. For **FlowCal/IP** non-delivery, look for a blocking **TIPS object validation** in the IP logs and override it at the client layer; for IP-induced slowness, identify the enabled **flow** (e.g. `metersampledaily`) and disable it to confirm.

**Bug IDs:** 226309, 1774497, 1763785, 1706821, 1811840, 1716345. **Linked SF:** 26-01102718 (1811840). **Clients:** BLU, ENT, HEP, XCL.

---

## 10. Cluster I — IPWS (Informational Postings) export & setup

IPWS is the public posting site fed by QPTM batch exports; this cluster is mostly **staging-table / metadata / security-object** issues.

| Symptom | Root cause | Fix / build (inferred) | Bug / SF |
|---|---|---|---|
| IPWS Locations download shows **Effective-Date-From in the Inactive-Date column** for inactive locations | Export used `EFF_DT_FROM` for `INACT_DT`. **Dev/product later judged this *expected*** — clients should create a new **inactive timeslice** (whose eff-date-from = the inactivation date) rather than just flipping status | Code change made, then **REVERTED (#1801373)** as a business-process change on ONEOK's end. Also surfaced a side bug: staging `PASTAG_LOC_EXPORT.UPDN_LOC_ID` is `VARCHAR(20)` but source `PACTRL_LOC_ASSOC.ASSOC_LOC_ID` is `VARCHAR(30)` → a 21-char ID failed the batch (widen the staging column) | **#1771370 / #1801373** (ONI/OkTex); queued 2023.04 & 2024.04 then reverted |
| Agent record not displaying in IPWS after Index-of-Customers batch (IOC) | IOC staging proc **`QPSStagIndxOfCust`** affiliate/agent joins (`KCTRL_CTR_AGENT` → `KCTRL_BP_ENTITY_HDR`, marketing-affiliate logic); client data/setup | Verified via the corrected steps; resolved as setup/data | **#1639588** / 24-00936650 (WWM) |
| IPWS link / Informational Postings **security object missing in core** | `QARCH_SEC_OBJECT` had no `IPWS_SECURITYID` / `IPWSSITEMAP_SECURITYID` in core (added ad-hoc in 2018) — hard to configure security in v17 | Script the sec objects into core, remove the redundant QPTM→IPWS sitemap link/object, add `IPWS_SECURITYID` to external personas; links also gated by `INFORMATIONAL_POSTING_SITE_GLOBAL` / `_SITE_MAP` configs | **#418322**; Iter 23.02 (inferred ~2023.02) |
| IPWS Maintenance app **Batch Process Execution screen shows no processes** | Front-end batch list empty | (Rejected — env/setup) | **#1623454** (VGP) |
| `CWOPERCAP` (Operational Available Capacity) batch **fails** | 2024.04 regression | Duplicate of #1649417; fixed | **#1654650** |
| Customer Activities screen not redirecting to myQuorum login | Menu/redirect setup | Tracked under #245437 (Rejected dup) | **#248452** |

**Cluster I fix recipe:** IPWS export "wrong/empty" → check the **staging table** (`PASTAG_*` — column widths vs source, e.g. `PASTAG_LOC_EXPORT`), the **batch proc / view** feeding it (`QPSStagIndxOfCust` for IOC), and the **config gates** (`INFORMATIONAL_POSTING_SITE_GLOBAL`/`_SITE_MAP`) + **security objects** (`IPWS_SECURITYID`) + external personas. Note the INACT_DT case is **expected behavior** — clients should create an inactive timeslice (don't code around it; #1771370 was reverted).

**Bug IDs:** 1771370, 1801373, 1639588, 418322, 1623454, 1654650, 248452. **Linked SF:** 24-00936650 (1639588).

---

## 11. Cluster J — Admin screens & framework (Menu/Sitemap, batch params, BA, JS)

| Symptom | Root cause | Fix / build (inferred) | Bug / SF |
|---|---|---|---|
| Manually-added **Menu Editor** items don't appear in the hamburger menu, no explanation | Items with **no Security ID, no URL, and no child nodes** are invalid and hidden | Add a **warning** in Menu Editor for invalid items; pairs with existing "Url could not be resolved" | **#1668941** (Iter 26.14; *2024.10*) |
| **Sitemap** screen won't open (internal/external) — 2024.04 regression | `System.InvalidCastException: ... 'System.ObsoleteAttribute' to 'IQSecurityObjectAttribute'` — platform marked something obsolete; obsolete `GlobalReportExecutionController` | Replaced with **`CoordinatedReportExecutionController`** | **#1648717** (2024.04) |
| Web **batch process won't accept multiple gas days** (`;`-separated) though the Batch Process Definition allows Multiple Input | QFC code handles `Multiple Input` for string params but **not for the `Date` dataType** — it doesn't split the semicolon-separated dates | Code change to split multi-value Date params like Classic (applies where Param Input = Multiple Input); **refresh cache** after editing params. Also blank values now ignored (`12/12/2025;;;`). HOTFIX | **#1772841** (ENT; Panaya Defect 58); also #1771793 |
| My Q **Batch Messages** screen can't show/search by **User ID** | Grid column not in metadata — and must be added in the **ESuite** application layer, **not** the product (TIPS/QPTM) layer (QFC) | Add `UserID` to the grid via **ESuite** Grid Definition (`QARCH_CNFG_GRIDCTRL_COL_NET.json`); core + CAN | **#1605056** / 23-00900536 (MWK/MPLX) |
| Batch-process **`PROCESS_LOG_ID` sequence** overflow risk (> 3 billion) | Sequence/column size | Enlarge `SQ_PROC_MSG_LOG` (MSSQL) / `QARCH_TRAN_SEQ.BIG_LAST_NO` (Oracle, `PROC_MSG_LOG`); `QARCH_PROCESS_MSG_LOG` + `QTRAN_PROC_MSG_DTL` support bigint | **#1612080** (Iter 23.25; *shared QPTM+TIPS+QGM checked*) |
| Random batch runs fail: "THERE ARE MESSAGES STILL IN THE READ QUEUE… BEFORE SENDMESSAGEANDWAITFORRESPONSE" | Inter-process messaging read-queue not drained (intermittent) | Code change pushed to client to test; not reproducible internally | **#245444** (QTR) |
| **Business Associate** screen: `ORA-02291` integrity-constraint error selecting Primary Usage after a custom BA suffix | Web inserts into **`SCTRL_BA_ADDRESS`** (new BA_NO/BA_SUF) but **not into `SVALD_BA_ADDRESS`**; selecting Primary Usage inserts `SCTRL_BA_USAGE` which has FK `FK_SVALD_BA_ADDR3` (Oracle)/`_ADDR2` (MSSQL) requiring a matching `SVALD_BA_ADDRESS` row | Insert the matching `SVALD_BA_ADDRESS` row from Web; reproducible in CORE. Cherry-picked 2024.04 / 2025.04 / 2025.10 / 2026.04 | **#1776151** (ENT; Defect 79) |
| Web screen logs **console error / "jQuery remains active"** (BA Name-Change-History, RFS Location/Contacts tab, Bids/Offers OData) | Missing **null check** in screen JS / OData service variable/port config; often **AT-only**, not user-facing | Add null check; for OData (Bids/Offers) it was DevOps variables/ports | **#1782252** (BA), **#1718905** (RFS), **#1752579** (Bids — OData service) |
| Bids/Offers screen "Something went wrong" outage (TEP) | App-tier crash on Capacity-Release screens | Restart QPEC/web services (transient) | **#1672445** / 24-00965597 (TEP) |

**Cluster J fix recipe:** Menu/Sitemap → invalid menu items (no Security ID/URL) or an obsolete-controller cast (platform regression). Web-vs-Classic param parity → QFC `Multiple Input` handling + **cache refresh**. Grid/metadata changes for shared screens (Batch Messages) must go in the **ESuite/QFC** layer, not the product layer, or Web won't pick them up. BA save/FK → Web missing the companion `SVALD_BA_ADDRESS` insert. "jQuery remains active" → usually a JS null-check and frequently AT-only (quarantine if not reproducible manually).

**Bug IDs:** 1668941, 1648717, 1772841, 1605056, 1612080, 245444, 1776151, 1782252, 1718905, 1752579, 1672445. **Linked SF:** 23-00900536, 24-00965597.

---

## 12. Fix-Version Matrix

> All `IntegrationBuild` fields were **empty**; "Fixed in (inferred)" is derived from the iteration path and "queued for next QPTM <ver>" / HOTFIX tags. **Confirm the exact build in the QPTM/QFC release notes and the linked PR's target branch before quoting to a client.**

| Bug | Cluster | Symptom (short) | State | Fixed in (inferred) | SF case | Client |
|---|---|---|---|---|---|---|
| #255923 | A | Internal user blank subreport (empty-string SEC_USER_ID) | Closed | 2020.03 → 2020.11/2021.04/develop | — | ENT |
| #1786782 | A | Internal user empty Web reports (ESUITE module USER_TYPE_CD NULL → EXT) | Closed | one-off script; HPE UAT/PRD | — | HPE |
| #1764600 | B | ALR_37 exposes other BAs to external (AAT≥5) | Closed | 26.01; cherry-pick 2024.04→2025.10 | 25-01035363 | ENT |
| #1734720 | B | SAVR BA picklist shows unassigned BAs to external | Closed | PR 117617 | 25-01022205 | ONM |
| #1661117 / #1742657 | B | ALR24 external imbalance report hangs/blank | Closed/Verified | DB view rewrite #1692315 | 24-00946909 | ONK |
| #1798371 | D | PDA Submission no privilege check (`QVPPREDETERMINEDALLOCATIONSUBMISSION`) | Closed | 2024.04.1.49 (+develop/2026.04) | — | ENT |
| #1798373 | D | Config screens ignore code table 296 / metadata-layer privileges | Closed | develop + 2024.04 (QFC Meta 17.21.X) + 2026.04 (17.25.X) | — | ENT |
| #1778592 | C | `ALLOW_BA_MISMATCH` not honored in Web (validation-driven) | Closed | dev/test | 26-01066150 | HEP |
| #1764767 | C | `VALIDATE_MDQ_REC_DEL` off but Web errors (Object-Usage validation) | Closed | hotfix 1/23 | 25-01042893 | HEP |
| #1744270 | C | Missing global/TSP config keys (default 0) | Closed | PLTM metadata; HOTFIX | 25-01031118 | ETC |
| #1723064 | C | `GAS_VOL_PRECISION` ignored (hard-coded round to 2) | Closed | PR 111222/111476 | — | ACL (Conifer) |
| #1316779 | C | Rounding hard-coded (QVpEstimatedActualMaint.cpp) | Closed | client hotfix (QGM 17.1) | 20-00093450 | GLE |
| #1797552 | E | CT 26136 won't save in Web (column missing from def metadata) | Closed | 26.10; 2025.10 & 2026.04 | — | core |
| #1625007 | E | CT 52011 FK error on add/update (delete still broken) | Resolved | ~23.20 | — | IPWS |
| #1678265 | G | EDI RQCF/SQOP/RRFC wrong loc (one config for all) | Closed | ENT hotfix; ~2020.03 | 24-00960415 | ENT |
| #1694083 | G | EDI regression — per-transaction `USE_INTERCONNECT_LOC_FOR_*` | Closed | cherry-pick 2024.04+ | — | TEP |
| #1718572 | G/I | OACY file still shows SPO-suppressed locations | Closed | 2024.10 hotfix | 25-01005337 | TEP |
| #1774497 / #1763785 | H | QPTM↔TIPS meter timeslice in Web (SEXTN_MTR_HEADER_QRMTIPS) | Closed | HOTFIX 11/28/25; 2025.04/2025.10/develop | — | ENT |
| #226309 | H | QCM→TIPS contract timeslice sync (Integration Module Setup) | Closed | config (#173632) | 20-00088799 | BLU |
| #1706821 | H | QPTM→TIPS nom import accept CSV directly (NOMIMPEXTS) | Closed | hotfix | — | HEP |
| #1811840 | H | FlowCal→eSuite→QPTM blocked by TIPS object validation | Closed | client-layer override | 26-01102718 | XCL |
| #1716345 | H | IP `metersampledaily` crushed eSuite API perf | Closed | meter-add perf fix | — | HEP |
| #1771370 / #1801373 | I | IPWS INACT_DT shows EFF_DT_FROM (reverted — expected) | Closed | reverted | — | ONI |
| #418322 | I | IPWS security object missing in core | Closed | ~23.02 | — | (HPE-origin) |
| #1668941 | J | Menu Editor warning for invalid menu items | Closed | 26.14 | — | core |
| #1648717 | J | Sitemap broken (obsolete controller cast) | Closed | 2024.04 | — | core |
| #1772841 | J | Web batch process multiple gas-day input | Closed | HOTFIX | — | ENT |
| #1605056 | J | Add User ID to Batch Messages (ESuite layer) | Closed | 17.19.1/17.20.3 hotfix; develop | 23-00900536 | MWK |
| #1612080 | J | PROCESS_LOG_ID sequence > 3B | Closed | 23.25 | — | core (shared) |
| #1776151 | J | BA Primary Usage FK (SVALD_BA_ADDRESS missing) | Closed | 2024.04/2025.04/2025.10/2026.04 | — | ENT |
| #1782252 / #1718905 / #1752579 | J | Console error / jQuery active / OData | Closed | 26.07 / 25.12 / 25.19 | — | core |
| #187862 | F | Bootstrap warnings on login (QFC 2019.10) | Closed | DISPLAY_SYSTEM_MSGS config | — | NMGC |
| #1585134 | F | QCM login OOM (bad Patch 25 GUI package) | Rejected | back-install Patch 23 | 23-00885986 | ALT |
| #253775 | F | QCM login crash (client App Sense) | Closed | not a Quorum issue | — | ETP |

---

## 13. Diagnostic SQL & pointers

> QPTM lives in MSSQL or Oracle per client (`<CLIENT>_HD_*`). Tables/columns below are taken from bug repro/comments and code search; **verify against the client schema** and run a verify-SELECT before any DML, wrapped in a transaction. Many fixes are in the shared **QFC/ESuite** layer — check the client repo/schema first.

```sql
-- A. Security-user module type: is an internal user being read as external? (§3 Cluster A)
--    Modules the user drives from Classic should have NULL USER_TYPE_CD; a stray INT/EXT or
--    extra QARCH_META_MOD_DEFINE rows in the *_QRMTIPS DB can flip the module to ENGS/EXT (#1786782).
SELECT SEC_USER_ID, MODULE_CD, USER_TYPE_CD FROM QARCH_SEC_USER_MOD WHERE SEC_USER_ID = '<USER>';
SELECT * FROM QARCH_META_MOD_DEFINE WHERE MODULE_CD IN ('ENGS','QPTM','QTIP','ESuite');

-- B. External report exposing other BAs / hanging (§3 Cluster B)
--    Inspect the external view that joins QARCH_SEC_USER; for ALR37 confirm AAT>=5 excludes CONF_PARTY_BP_NO.
--    (Views: ALRPTS_37_AL_DWNLD_*_XVW, ALALL_RPTS_37_*; ALRPTS_24_DLY_IMB_REV_XVW for the hang.)

-- C. Config key present? Which layer? (§4 Cluster C) — global vs TSP
SELECT KEY_GROUP_NM, KEY_NM, KEY_VALUE, APP_LAYER FROM QARCH_CNFG_CTRL
WHERE  KEY_NM IN ('ALLOW_BA_MISMATCH','VALIDATE_MDQ_REC_DEL','GAS_VOL_PRECISION',
                  'USE_INTERCONNECT_LOC_FOR_RRFC','NUM_STREAMING_OBJECTS','NAESB30');
--   In WEB, the gate is usually an Object-Usage VALIDATION rule, not this key — check the screen's *Validation* rules.

-- D. Web privilege-check defects (§5) — the security object the screen must enforce
SELECT * FROM QARCH_SEC_OBJECT WHERE OBJECT_ID = 'QVPPREDETERMINEDALLOCATIONSUBMISSION';
--   Metadata-edit gate: code table 296 = QARCH_SEC_EDIT_METADATA (+ configs ALLOW_EDIT_METADATA / ALLOW_EDIT_LOWER_LEVEL_METADATA).

-- E. Code-table-definition vs DB columns (Classic saves, Web doesn't) (§6)
--    Compare the code-table definition metadata (what the Web grid renders) to the actual table columns.

-- H. QPTM↔TIPS timeslice sync (§9) — core vs the QRMTIPS extension must be in sync
SELECT * FROM SCTRL_MTR_HEADER            WHERE MTR_NO = '<MTR>';
SELECT * FROM SEXTN_MTR_HEADER_QRMTIPS    WHERE MTR_NO = '<MTR>';   -- missing rows = the #1774497/#226309 pattern
SELECT * FROM SARCH_CNFG_INT_MODULE;                                 -- Integration Module Setup (shared)

-- I. IPWS staging column-width / IOC agent (§10)
--    PASTAG_LOC_EXPORT.UPDN_LOC_ID VARCHAR(20) vs PACTRL_LOC_ASSOC.ASSOC_LOC_ID VARCHAR(30) (#1771370 side bug).
SELECT * FROM QARCH_SEC_OBJECT WHERE OBJECT_ID LIKE '%IPW%';         -- IPWS_SECURITYID / IPWSSITEMAP_SECURITYID

-- J. BA Primary Usage FK (§11) — Web wrote SCTRL_BA_ADDRESS but not SVALD_BA_ADDRESS
SELECT * FROM SCTRL_BA_ADDRESS WHERE BA_NO = '<BA>' AND BA_SUF = '<SUF>';
SELECT * FROM SVALD_BA_ADDRESS WHERE BA_NO = '<BA>' AND BA_SUF = '<SUF>';  -- missing = ORA-02291 on usage save

-- J. Batch sequence overflow (§11)
--    MSSQL: SQ_PROC_MSG_LOG ; Oracle: QARCH_TRAN_SEQ.BIG_LAST_NO for PROC_MSG_LOG ; tables QARCH_PROCESS_MSG_LOG / QTRAN_PROC_MSG_DTL.
```

**Code/repo pointers (from PRs & comments):**
- Shared security/config/metadata & screens: **`Quorum.QFC.Metadata`**, **`Quorum.ESuite.*`**, **`Quorum.QFC.ProcessService`** (module INT/EXT switch). Grid metadata changes for shared screens go in the **ESuite/QFC** layer, not `Quorum.QPTM.Metadata`/TIPS (#1605056, #164627).
- QPTM screens: **`Quorum.QPTM.Web` / `.Web.Controllers` / `.Metadata`** (PDA Submission, Location/Contract/RFS, BA, Config). Web validations named like **`QPTMLocationMaintenance034_ValidateChangeOfDate`**, **`ContractMaintenance0008`**, **`QTIPSValidationCustomerAccountMaintenance0007_CtrBaMismatches`** (toggled via Object Usage).
- EDI: outbound dataset builders **`G873*` / `QEdiOACYout20.cs`, `QEdiUPRDIn30`** (suppress-OACY filter via `LocationManagerCache.LocationAttributeList`).
- Reports/views: external `_XVW` views join `QARCH_SEC_USER`; report params on the **QFC metadata** layer (picklist mappings, e.g. param 365/26956).
- IOC/IPWS staging proc: **`QPSStagIndxOfCust`**; tables `PASTAG_*`, `PACTRL_*`.

---

## 14. Escalation Guidance

**It's almost certainly NOT a code defect (config / setup / env) when:**
- "Works in Classic, not Web" for a **config key** → it's the **Object-Usage validation** lever in Web, not the key (§4: 1778592, 1764767). Toggle the validation at the client layer.
- A **config key is "missing from `qarch_cnfg_ctrl`"** → add to PLTM metadata / TSP config (§4: 1744270); confirm the default with products.
- **Login crash / startup warnings** → client-side App Sense, a bad GUI patch package, framework-installer version, or the QFC-2019.10 bootstrap-warning noise (§7: 253775, 1585134, 187862).
- **Timeslice not syncing to TIPS** → Integration Module Setup config (§9: 226309).
- **IPWS INACT_DT "wrong"** → expected; client should create an inactive timeslice (§10: 1771370 reverted).
- **Internal user blank report after a module/security change** → fix the security-user module setup / extra `QARCH_META_MOD_DEFINE` rows (§3: 1786782).

**Route to Engineering (real defect) when, with PQID/repro + client + screen + Object ID:**
- A **Web screen lets an under-privileged user act** (missing Object-ID / code-table-296 check) — §5: 1798371, 1798373.
- A **report/view exposes another shipper's data** or an external report **hangs on an unfiltered `QARCH_SEC_USER` join** — §3: 1764600, 1734720, 1661117 (DB view change, both VW/XVW, both MSSQL/Oracle, cherry-pick all releases).
- **EDI sends the wrong location identifier** and a **per-transaction `USE_INTERCONNECT_LOC_FOR_*`** config is absent — §8: 1678265/1694083.
- **Web won't sync a QPTM/TIPS timeslice** (validation blocks + missing `SEXTN_*_QRMTIPS` write) — §9: 1774497/1763785.
- A **code-table column exists in DB but not in definition metadata** (Web save fails) — §6: 1797552.
- **BA Primary Usage FK** (Web missing `SVALD_BA_ADDRESS` insert) — §11: 1776151.
- **Batch framework** (`PROCESS_LOG_ID` sequence, multiple-gas-day param, read-queue) — §11: 1612080, 1772841, 245444.

**Is the client's build fixed?** Because `IntegrationBuild` is empty on these bugs, **do not state a build from this skill alone.** Use the inferred version in §12 as a starting point, then confirm in the **QPTM/QFC release notes** and the linked **PR's target branch(es)**. Many fixes are **client-specific or hotfixes** (ENT, HEP, ONK, TEP) cherry-picked across 2024.04 / 2024.10 / 2025.04 / 2025.10 / 2026.04 — verify the client's exact release line includes the cherry-pick before promising the fix.

---

*Skill created: 2026-06-14. Source: ADO QPTM Bugs (Closed/Resolved) under Energy Transportation + Maintenance\Midstream and Transportation; WIQL matched 1,746, ~95 in this functional area, ~56 deep-read with full comment threads.*
*Known ADO items referenced: #255923, #1786782, #1764600, #1734720, #1661117/#1742657, #1798371, #1798373, #1778592, #1764767, #1744270, #1723064, #1316779, #1797552, #1625007, #1678265, #1694083, #1718572, #1774497/#1763785, #226309, #1706821, #1811840, #1716345, #1771370/#1801373, #1639588, #418322, #1623454, #1654650, #248452, #1668941, #1648717, #1772841, #1605056, #1612080, #245444, #1776151, #1782252, #1718905, #1752579, #1672445, #187862, #1585134, #253775, #164627. IntegrationBuild empty across the set — fixed-in-build values inferred from iteration/tags (confirm in release notes).*
