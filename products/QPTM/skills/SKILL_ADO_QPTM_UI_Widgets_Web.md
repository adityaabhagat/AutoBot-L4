# SKILL: QPTM UI / Widgets / Web Defect & Fix Reference (from ADO bugs)

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management) | **Source:** Azure DevOps Bugs (Closed/Resolved), org `QuorumSoftware`
**Scope (functional area):** The **QPTM / eSuite Web UI layer** — maintenance screens (Location / Contract / Rate / Contract Meter List / Index / Code Decode), **picklists & dropdowns**, **batch-process & report parameter screens**, **Nomination Submission / RFS / Bids-Offers (Capacity Release) screens**, **IPWS exports**, **Report Viewer**, and **AT-detected console/jQuery** errors. This is overwhelmingly a **Web-vs-Classic parity** story: ENT (Enterprise/EPCO) and Unit (UPC) are the first big clients moving from eSuite Classic to QPTM Web (2024.04+), and the bugs are the validations/handlers/sequences/metadata that behave differently (or are missing) in Web.

> **Use When:** a QPTM/eSuite **Web screen** errors on save/query/timeslice; a **picklist or dropdown** doesn't filter / is missing values; a **batch process or report parameter** screen behaves wrong in Web; **Nomination Submission / RFS / Bids / Offers** UI misbehaves; an **IPWS export** file is wrong/missing; **Report Viewer** fails to open; or AT reports a **"console error / jQuery remains active."** For settlement/journal/rate-calc engine defects use the TIPS skills instead — this skill is the **UI / web-app** layer.

> **Evidence base:** WIQL over `Bug` + `State IN (Closed,Resolved)` under **two area branches** — `QuorumSoftware\Engineering\Energy Transportation` (active dev: teams *Pipeline Galaxy / Pirates of Pipeline / Pipeline Titans*) **and** `QuorumSoftware\Engineering\Maintenance\Midstream and Transportation` (maintenance: *Professional Service / Customer Service*), filtered to UI terms (widget/dashboard/screen/grid/picklist/jQuery/console/Design Studio/eSuite/not loading/web). **2,198 bugs matched**; analyzed the **250 most-recently-changed**, deep-read **~46** (description + ReproSteps + relations/PRs + full comment thread). **IntegrationBuild is EMPTY on every one** of these — fixed-in-build is **inferred** from `System.IterationPath` (YY.NN sprints / 20YY.NN release tags), `HOTFIX`/`queued for next QPTM 20YY.NN`/`Beta` tags, and dev comments; **confirm in release notes before quoting a build to a client.**

> **Product overlap caveat:** the **Maintenance\Midstream and Transportation** branch is a **mixed QPTM+TIPS** backlog (teams like *TIPS'n Tricks*, *TIPS Samurai*, *Guardians of TIPS* sit here). The UI terms skew QPTM, but **9 of the 250 were clearly TIPS** (NGL Offload Statement, Keep-Whole/Combined Settlement Statement, IN02MTR, TIPS User Defined Formula / Paystation, TIPS Meter-Definition boolean) and were **dropped**. Many "ambiguous" titles (Meter Definition, IPWS, Reports, Contract Meter List, batch processes) **are QPTM** — Contract Meter List & Meter Definition are shared eSuite screens but the *web* defects here are filed/fixed in the QPTM/ESuite Web layer. When a row says "TIPS" in the title and has no QPTM nomination/RFS/offer/allocation context, treat it as the other product.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [How QPTM Web fits together (concepts)](#2-how-qptm-web-fits-together-concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Maintenance-screen Save / Timeslice / Eff-Date errors (Web vs Classic)](#4-cluster-a--maintenance-screen-save--timeslice--eff-date-errors)
5. [Cluster B — Contract Meter List (QCM) Web errors](#5-cluster-b--contract-meter-list-qcm-web-errors)
6. [Cluster C — Picklist / dropdown not filtering or missing values](#6-cluster-c--picklist--dropdown-not-filtering-or-missing-values)
7. [Cluster D — Batch-process & report PARAMETER screens (Web)](#7-cluster-d--batch-process--report-parameter-screens-web)
8. [Cluster E — Nomination Submission / RFS / Bids-Offers UI](#8-cluster-e--nomination-submission--rfs--bids-offers-ui)
9. [Cluster F — "console error / jQuery remains active" (AT) & generic Web crashes](#9-cluster-f--console-error--jquery-remains-active-at--generic-web-crashes)
10. [Cluster G — Reports & Report Viewer](#10-cluster-g--reports--report-viewer)
11. [Cluster H — IPWS exports / downloads](#11-cluster-h--ipws-exports--downloads)
12. [Cluster I — Code Decode / metadata-definition gaps](#12-cluster-i--code-decode--metadata-definition-gaps)
13. [Fix-Version Matrix](#13-fix-version-matrix)
14. [Diagnostic pointers](#14-diagnostic-pointers)
15. [Escalation guidance](#15-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user/QA reports) | Likely cluster / root cause | First check |
|---|---|---|
| Web Location/Rate/Contract Maintenance **save fails** on a new timeslice / eff-date copy ("ORA-02289 sequence does not exist", "Value cannot be null. Parameter name: source", "Unable to enforce constraints … CASScheduleObjectCustom") — **works in Classic** | §4 Web-vs-Classic parity defect; missing sysgen sequence, ENT event-handler passing Id=0, or core insert/dup logic | Is it reproducible in **Classic**? Which client (usually ENT/UPC)? Get exact error text + screen + TSP/Loc/Rate ID |
| Contract Meter List (QCM): blank Meter Header on Links, duplicate meter rows saved, "item with same key already added," "invalid effective date" for correctly-timesliced meters | §5 QCM Web defects (missing menu metadata, Web N/A default, event detector, FirstDayToCache validation) | Reproducible in Classic? Event-detector active? §5 |
| A **picklist doesn't filter** what you type / shows all rows; or a **dropdown is missing a TSP/value** that appears on another screen | §6 metadata: wrong `Filter Column Expression` + missing `@@FULL_WHERE_CLAUSE`; or `CURRENT_TIMESTAMP` vs `EFF_DT` 24h gap | §6 — inspect `QARCH_CTRL_PKLIST_NET` / pick definition metadata |
| **Batch process** (NNNOMLOAD, NNAUTOGEN, CRBIDEVAL) fails or behaves wrong from the Web parameter screen | §7 (service-impl gap, reverted unique-constraint WI, offer-filter metadata) | §7 — exact process code + error; does the job still complete despite the error? |
| Nomination Submission: missing **Del? checkbox** for external user; can't add Up/Dn; "Something went wrong" on **Bids/Offers** | §8 config-gated UI / null-ref in CR Offer controller | §8 — config flags; restart QPEC/web as immediate unblock |
| AT logs **"console error / jQuery remains active"** on a tab switch (BA, RFS, etc.) | §9 null-reference in a shared JS control; often **AT-only**, not manually reproducible | §9 — quarantine AT or add null check |
| **Report Viewer** won't open / "Something went wrong" after clicking View Report | §9/§10 — obsolete controller cast; or §10 PDF-format + CAW-security | §10 — try Word format; check security group |
| **IPWS** Location/Capacity export file not created or has wrong dates/truncated values | §11 — staging column too narrow, `CUSTOMER_WHERE_CLAUSE` blocking export, business-process (inactive timeslice) | §11 — check export def path + staging table widths |
| Can't save a **Code Decode** row in Web (works in Classic) | §12 — code-table definition missing a column present in the DB | §12 |

---

## 2. How QPTM Web fits together (concepts)

```
[QPTM/eSuite Web UI (Razor/jQuery grids, picklists)]
      │  Controllers: QUIController* (e.g. QUIControllerCROfferV2)
      ▼
[ServiceCore: QPTMServiceCore_LocationMaintenance.cs, ContractMaintenance, RateMaintenance ...]
      │  Validation rules (RuleNN*, QPTMLocationMaintenance0XX_*), Event Handlers (HandleContractMaintenanceChange,
      │  HandleGenericScreenChangeEvent, client-specific QKExbEventHandler in <CLIENT>.QPTM.Web)
      ▼
[QFC platform: picklist engine (QARCH_CTRL_PKLIST_NET / pick definitions), menu (QARCH_CNFG_MENU_DETAIL),
      caches (ValidPlantMeterCache), batch launcher (IQProcessLauncherService)]
      ▼
[DB: SCTRL_* core tables, CACTRL_SCHD_OBJ_CUSTOM, BLTRAN_PPA_EVENT, PASTAG_LOC_EXPORT (IPWS staging),
      SEXTN_MTR_HEADER_QRMTIPS (TIPS-integration), sequences e.g. SCTRL_MTR_FACILITY_HSQ]
```

**Key vocabulary**
- **Classic vs Web (eSuite/QPTM Web):** the legacy desktop/Citrix app vs the browser app. The dominant root-cause pattern in this skill is **"works in Classic, fails in Web"** — Web re-implements validations/handlers and often diverges. Always ask "does it reproduce in Classic?" first.
- **QCM** = the eSuite **Contract Meter List** screen (a.k.a. QCM Contract Meter List). Shared with TIPS Meter Definition but the *web* save/query/timeslice defects are QPTM/ESuite Web.
- **Picklist / pick definition:** filtered dropdowns driven by metadata in `QARCH_CTRL_PKLIST_NET` (the `CUSTOM_QRY_STMT`, `Filter Column Expression`, and `@@FULL_WHERE_CLAUSE` token). Pick IDs are numeric (e.g. 26010 RFS, 26015 Bid No, 26475 ALR-89).
- **Event Detector / Event Handler:** server-side handlers fired on screen change (`HandleContractMaintenanceChange`, `HandleGenericScreenChangeEvent`); ENT has client-specific ones in `ENT.QPTM.Web` (`QKExbEventHandler`). Several defects = a table not registered with the handler, or a clone Id passed as 0/null.
- **PPA / Reallocation event:** a save in Contract/Location Maintenance that touches a *closed* accounting month should pop the **Reallocation/PPA** dialog and write `BLTRAN_PPA_EVENT`. Open-month changes correctly do **not** pop it (expected behavior — see §4/§8 FAQ).
- **Beta Testing / AHT / Regression tags:** `20YY.NN QPTM Beta Testing` and `20YY.NN AHT` (All-Hands Testing) bugs are internal pre-release finds — useful because the iteration/tag tells you the target release.
- **AT** = Automated Test. Many `console error / jQuery remains active` bugs are AT-detected and **not manually reproducible**; the disposition is often "quarantine the AT" or a defensive null check.
- **IPWS** = Informational Postings Web Site (NAESB customer activity website). Exports run via batch (PALOCEXP Location Export) into staging tables (`PASTAG_LOC_EXPORT`) then post to IPWS.
- **QPEC / web services restart:** the standard immediate unblock for transient "Something went wrong" / screen-crash outages.

---

## 3. Decision Tree

```
QPTM Web UI bug
│
├─ Does it reproduce in CLASSIC too?
│   ├─ NO (Web only)  → it's a Web parity defect →
│   │     ├─ Maintenance screen save/timeslice/eff-date error        → §4
│   │     ├─ Contract Meter List specifically                        → §5
│   │     ├─ Picklist/dropdown not filtering or missing a value      → §6
│   │     ├─ Code Decode won't save                                  → §12
│   │     └─ Report Viewer won't open / report param picklist        → §10 / §6
│   └─ YES (both) → core/data/config, not Web-specific (e.g. duplicate save logic #1620262, event-detector dup #1676927) → still §4/§5 but fix is in core/metadata
│
├─ Batch process screen (NNNOMLOAD / NNAUTOGEN / CRBIDEVAL / PALOCEXP)?
│   ├─ Process fails but nom/data still saves                        → §7 (#1664436 reverted-WI regression)
│   ├─ "service provider does not contain implementation for IQProcessLauncherService" → §7 (#1733844)
│   └─ Offer/parameter picklist not filtering                        → §6 + §7
│
├─ Nomination Submission / RFS / Bids / Offers / Capacity Release UI?
│   ├─ Missing column/checkbox for external user (config-gated)      → §8 (#1651310)
│   ├─ "Something went wrong" on Bids/Offers, screen crash           → §8/§9 (restart QPEC first; null-ref in CR Offer controller)
│   └─ console error / jQuery remains active (AT)                    → §9
│
├─ IPWS export wrong/missing                                          → §11
│
└─ Vague "error on save," intermittent, can't reproduce in core      → likely client-data/config or env; capture exact error + screen + IDs; restart services; §14
```

---

## 4. Cluster A — Maintenance-screen Save / Timeslice / Eff-Date errors (Web vs Classic)

**The single largest cluster.** ENT (Enterprise/EPCO) and Unit (UPC) move to QPTM **Web** and hit save/timeslice/effective-date errors on **Location Maintenance, Rate Maintenance, Index Maintenance, Contract Maintenance** that do **not** occur in Classic. Multiple distinct root causes share the symptom "Save failed due to an error."

**Symptoms (verbatim):**
- `Save failed due to an error. Error: ORA-06550 … PL/SQL: ORA-02289: sequence does not exist` (Location Maintenance timeslice)
- `Save failed due to an error. Error: Value cannot be null. Parameter name: source` (Rate / Index Maintenance copy-forward)
- `Unable to enforce constraints due to the following errors: Table CASScheduleObjectCustom Errors` (System Location Groups tab, bidirectional locations)
- Orphan-TIPS-meter validation error when timeslicing a meter that exists in both QPTM and TIPS

**Root causes & fixes seen:**
- **Missing DB sequence (sysgen)** — Location Maintenance timeslice ORA-02289 traced to sequence **`SCTRL_MTR_FACILITY_HSQ`** not existing (sysgen gap). **#1763785** (ENT, 25-01050064; PRs 120300/119643; HOTFIX 11/28/2025).
- **Web validation rule not syncing the TIPS extension table** — rule **`QPTMLocationMaintenance034_ValidateChangeOfDate`** blocked timeslicing in Web (Classic has no such block) and Web never wrote to **`SEXTN_MTR_HEADER_QRMTIPS`** the way Classic does. Fix: modify the rule to match Classic + add explicit insert/update/delete into `SEXTN_MTR_HEADER_QRMTIPS` via eSuite DAL (`SMeterHeaderQRMT`). **#1774497** (ENT "Defect 54"; PRs 122577/122584/122614/122615; cherrypicked 2025.04/2025.10/develop).
- **ENT-specific event handler passing a 0/null clone Id** — Rate/Index Maintenance copy-forward threw "Value cannot be null. Parameter name: source" because `QKExbEventHandler.HandleRateLocationDetailsChange()` got `IdRateHdr = 0` from `completeClone` instead of the newly-created `RateComplete.IdRateHdr` (the clone-Id assignment pattern existed only for Contract Maintenance, missing for Rate & Index). **#1777371** (ENT "Defect 73"; PRs 123785/123827/124284/124285; in `ENT.QPTM.Web` event handlers).
- **Core dup-insert on `CACTRL_SCHD_OBJ_CUSTOM`** — System Location Groups tab, bidirectional Area Capacity/Rate records (config `VALD_BIDIRECTIONAL_POV=1`, ENT). In `QPTMServiceCore_LocationMaintenance.cs` (~line 1359) the existence-check `if` wasn't matching, so Web tried to overwrite the existing custom schedule-object row → constraint error. Same family as a 2019 fix **#134284**. **#1782369** (ENT "Defect 65") and follow-on header eff-date **#1788366** (HOTFIX, Maintenance: Escalated).
- **Failure to create a new eff-date slice on Location Maintenance** (core, AT-found) — tied to an Oracle DB sequence from a separate WI; fixed once the sequence was corrected. **#1777414** (QPTM core; PRs 122928/123188/123197; sprint 26.03).

**Related same-family items:** `#1774299` (Location Maintenance — unable to save new location due to an error), `#1773033` (Shared MDQ Related Contract change doesn't trigger Reallocation/PPA — event handler `HandleGenericScreenChangeEvent` didn't include table **`SCTRL_RELATED_CTR`**, so `HandleContractMaintenanceChange` never fired and `PPAReallocationDialogData.ReallocateSelect` was empty; PRs 122294/122297/122616/122617, ENT Panaya Defect 90, planned 1/16 HF), `#1776151` (integrity-constraint error selecting a primary usage on BA Address), `#1782369`→`#1788366` chain.

**Fix recipe:**
1. **Confirm it's Web-only** (reproduce in Classic). Capture the **exact error string**, the **screen + tab**, and the **client + TSP + Loc/Rate/Contract ID**.
2. "ORA-02289 sequence does not exist" → check the client DB for the missing **sequence** (e.g. `SCTRL_MTR_FACILITY_HSQ`); a **sysgen** re-run / sequence create is the fix (#1763785).
3. "Value cannot be null. Parameter name: source" on copy-forward → ENT-specific event handler; the newly-created Id isn't propagated to the clone (#1777371) — Engineering fix in `ENT.QPTM.Web`.
4. "CASScheduleObjectCustom … Unable to enforce constraints" on bidirectional/System Location Groups → core dup-insert into `CACTRL_SCHD_OBJ_CUSTOM` (#1782369), config-gated by `VALD_BIDIRECTIONAL_POV`.
5. Timeslicing a **QPTM+TIPS shared meter** → Web is stricter than Classic; interim workaround = **end-date in TIPS Meter Definition first, then create the new QPTM Location timeslice** (Web validates the TIPS meter is effective for the same range). Real fix syncs `SEXTN_MTR_HEADER_QRMTIPS` (#1774497).

**Bug IDs:** #1763785, #1774497, #1777371, #1782369, #1788366, #1777414, #1774299, #1776151, #1773033 · **Linked SF:** 25-01050064 (#1763785), 25-01060777 (#1786342, related CAS) · **Clients:** ENT/EPCO (dominant), UPC.

---

## 5. Cluster B — Contract Meter List (QCM) Web errors

QCM (Contract Meter List) is the highest-touch shared screen; several **distinct** Web defects:

| Symptom | Root cause | Fix / build | Bug | SF |
|---|---|---|---|---|
| Click meter → **Links > METER HEADER opens blank** (doesn't query the meter) | `METER_HEADER` was removed from **`QARCH_CNFG_MENU_DETAIL`** metadata at the core layer, breaking the Links launch; the launch also wasn't passing **`mtr_no`** context to the Meter Header screen | Restore the menu-detail metadata; PRs 115832/115833; **HOTFIX**, Core Code Change | #1744361 (UPC QCM 2025.04) | — |
| **Duplicate meter rows saved** in Web (and Classic) | Web auto-set the **opposite plant to "N/A"** (Delivery Plant for a Receipt meter) and defaulted Rejection Option to **None**, which differed from the existing **NA** rows → uniqueness check passed and a dup saved. Web "N/A" came from web code, not the DB, so the Classic metadata `Field Defaults` fix didn't fix Web | Web code fix (don't persist "N/A"; block dup) in **`Quorum.ESuite.Web`**; PRs incl. 99943/99944/99946; merged 2022.10 + 2024.04 develop/release. Classic side = metadata (`REJ_OPT_CD` default, code table 36157) | #1620262 (ONM, 23-00913209) | 23-00913209 |
| **"Save failed … An item with the same key has already been added"** updating CCTs on multiple meters when an **MTR_CCT Event Detector is active** | Active event detector + multi-meter CCT change collides on a dictionary key (Web and Classic) | Fix in `Quorum.ESuite.Web`; PRs 99943/99944/99946 | #1676927 (ONM, 24-00968427) | 24-00968427 |
| **"Invalid effective date" for meters that ARE correctly timesliced** after upgrade; needs QPEC restart workaround | The Web validation used **`ValidPlantMeterCache.FirstDayToCache()`** (defaults to current date − 365 days); meters effective **before** that cache window were wrongly flagged invalid | Fix the eff-date-vs-`FirstDayToCache()` comparison (handle `effDt < / > / == FirstDayToCache`); PR 126642; queued for next ESuite 2026.04 (cherrypick 2025.04) | #1788087 (UPC, 26-01084783) | 26-01084783 |
| CML **doesn't query when meters are closed** | Query filter excluding closed meters | Fix | #1756941 (ETP) | — |
| CML **blank screen for Links** (older) | Menu/link metadata | — | #1095582 (SEM) | — |
| Meter# **picklist error** "Unable to Retrieve the data for the pick definition on click" | Pick definition metadata (see §6) | — | #1651309 (QCM) | — |

**Fix recipe:** establish Classic-vs-Web behavior. For blank Meter Header → check **`QARCH_CNFG_MENU_DETAIL`** has the `METER_HEADER` link and the launch passes `mtr_no` (#1744361). For duplicate saves → the **opposite-plant "N/A" web default** is the culprit; it is a `Quorum.ESuite.Web` **code** fix, not metadata (#1620262). For "invalid effective date" on correctly-timesliced meters → it's the **`FirstDayToCache()` 365-day window** (#1788087); QPEC restart is the temporary unblock.

**Bug IDs:** #1744361, #1620262, #1676927, #1788087, #1756941, #1651309, #1095582, #1597823 · **Linked SF:** 23-00913209, 24-00968427, 26-01084783 · **Clients:** UPC, ONM, ETP, SEM.

---

## 6. Cluster C — Picklist / dropdown not filtering or missing values

A recurring **metadata** defect family in the picklist engine (`QARCH_CTRL_PKLIST_NET` / pick definitions). Two distinct sub-causes:

**6a — Picklist returns ALL rows / doesn't filter what you type.**
Root cause (confirmed by dev, #1757897): the pick definition's **`Filter Column Expression`** column holds the **wrong value** (a label like `Releaser` instead of the actual DB field `REL_BP_NO`), **and/or** the picklist SQL is **missing the `@@FULL_WHERE_CLAUSE` token**, so the typed filter is never applied. Fix = set `Filter Column Expression` to the real DB column name (match the `Col Name`) and add `@@FULL_WHERE_CLAUSE` to the query. Known-affected picks: **RFS (26010), Bid No (26015)**, CRBIDEVAL Offer parameter. **#1757897** (CRBIDEVAL offer picklist; PR 119667; 2025.10 AHT). Also the ALR-88/ALR-89 report parameter picklists (§10) are the same "SOA Picklist Definition" parameter-mapping problem (#1590890, #1605446, #1605446's sibling #1605448 BLINVGEN — *Rejected* as not-Maintenance).

**6b — Dropdown is missing a TSP/value that appears on another screen.**
Root cause (#1721106): the picklist `CUSTOM_QRY_STMT` compared **`CURRENT_TIMESTAMP`** against `EFF_DT_FROM`/`EFF_DT_TO` (which carry **no time component**), creating a ~24-hour gap so a TSP effective "today 00:00" was excluded on Batch-Process/Contract-Maintenance dropdowns while the Nom-Submission picklist (different query) still showed it. Fix = generate DB-specific date SQL (MSSQL `GETDATE`/Oracle) stripping the time, instead of relying on `SCREEN_AS_OF_DATE` (which only worked on the Offers screen) or `@6QFC_UTIL.FN_STRIPTIME` (Classic-only). Dup of **#1680082**. Search offenders: `QARCH_CTRL_PKLIST_NET.CUSTOM_QRY_STMT LIKE '%TSP%' AND LIKE '%GETDATE%'` and `QARCH_CDTBL_DEFINE.CUSTOM_WHERE_CLAUSE` similarly. **#1721106** (2025.04 Beta).

**6c — SOA picklist effective-date default filtering (enhancement-style).**
ENT wanted picklists to **default the effective-date filter** when opened. Working on Contract Maintenance via the **`ScreenAsOfDate`** property on `ContractMaintenanceRootVM` + Mappings Static Controls; the ask was to extend the same to Location/Rate Maintenance/Auth-to-Post-Imbal/Customer Account Summary RootVMs. **#1779785** (ENT SOA Picklist Filters; HOTFIX; Core + Client Metadata; sprint 26.05). Also `#1645519` (TEP — locations not available in all picklists), `#1760071` (EQC — location missing from ALRX04_EX report picklist for operator-agent BA).

**Fix recipe:** for "picklist not filtering," open the **pick definition** for that Pick ID and verify (1) `Filter Column Expression` = the real DB column (not a label), (2) the SQL contains **`@@FULL_WHERE_CLAUSE`** (#1757897). For "value missing on one screen but present on another," suspect the **`CURRENT_TIMESTAMP` vs `EFF_DT` time-gap** in that picklist's `CUSTOM_QRY_STMT` (#1721106/#1680082). For "default the eff-date filter on open," it's the **`ScreenAsOfDate`/RootVM** pattern (#1779785).

**Bug IDs:** #1757897, #1721106 (dup #1680082), #1779785, #1645519, #1760071, #1651309 (QCM meter# pick), #1590890, #1605446 · **Clients:** ENT, TEP, EQC, ONG.

---

## 7. Cluster D — Batch-process & report PARAMETER screens (Web)

Batch processes launched from the **Web** parameter screen (distinct from the engine itself):

| Symptom | Root cause | Fix / build | Bug | SF |
|---|---|---|---|---|
| **NNNOMLOAD** errors `"Since last Retrieve, another user submitted nominations…"` but the **nom still submits** | Regression from **backing out** the unique-constraint WI **#1544800**; the spurious concurrency error returned | Reworked patch (related #1669941); PRs 97268/97284/97285/97357/97358; May-2024 review, Maintenance: Escalated | #1664436 (ETC, 24-00957668) | 24-00957668 |
| **NNAUTOGEN** batch fails on new nom: `"The service provider does not contain a service implementation for 'IQProcessLauncherService'"` | DI/service-registration gap for the process launcher in Web | PRs 112626-112629; 2025.04 Regression (sprint 25.12) | #1733844 | — |
| **CRBIDEVAL** offer-parameter picklist doesn't filter the queried offer | Picklist metadata (see §6a); also note Web won't let you pick an offer until its bid window is past — **expected**; Classic lets you type it manually as a workaround | PR 119667; 2025.10 AHT | #1757897 | — |
| **TSP dropdown** missing on NNNOMLOAD/Contract-Maint batch screen but present on Nom Submission | §6b `CURRENT_TIMESTAMP` vs `EFF_DT` time-gap | PRs 125054/125055/125527/125528; 2025.04 | #1721106 | — |
| **NNNOMLOAD** errors loading files **>1800 rows** | Row/payload limit in the web upload path | Fix | #1720362 (ETC) | — |
| AutoGen creating noms with an **invalid/external User ID** that lacks BA access | NNAUTOGEN propagated the submitting external user's ID onto target noms it generated for a back-dated cycle | PRs 111032-111206; Core + Client Metadata | #1721896 (ONK, 25-01007550) | 25-01007550 |
| Batch process **"Warning" shown instead of "Error"** for an invalid footnote | Severity mapping in the web message | Fix | #1776478 | — |
| Web Batch Process **not allowing multiple Gas Day input** | Web parameter control | Fix | #1772841 (ENT) | — |

**Fix recipe:** get the **exact process code + error string** and whether the underlying job **still completed**. "Still submits but errors" (#1664436) is a known reverted-WI regression — Engineering rework, confirm the patch is deployed. "IQProcessLauncherService not found" (#1733844) is a DI registration gap. Offer/TSP picklist issues route to §6.

**Bug IDs:** #1664436, #1733844, #1757897, #1721106, #1720362, #1721896, #1776478, #1772841, #1445272 (2022.04 NNNOMLOAD beta), #1392863 (NNPSTCREAT discount-offer rates) · **Linked SF:** 24-00957668, 25-01007550.

---

## 8. Cluster E — Nomination Submission / RFS / Bids-Offers UI

| Symptom | Root cause | Fix / build | Bug | SF |
|---|---|---|---|---|
| **Del? (delete) checkbox column not visible for external user** on Nomination Submission, even with `ALLOW_EXTERNAL_USERS_DELETE_NOMS=1` + `ALLOW_NOM_DELETES=1` | Web column-visibility logic for external users; config-gated AT regression (persisted across 2024.04→2024.10) | PRs 101034/102242/103528/124373/127349; 2024.04 Regression / AT | #1651310 | — |
| **"Something went wrong"** on **Bids / Offers** screens; Capacity Release builds blocked; outage cleared by **QPEC/web restart** | `Index was outside the bounds of the array` in **`QUIControllerCROfferV2.Initialize`** (~line 446) — empty `cdtbl.Tables[]` / null collection; isolated occurrences (App Insights) | Defensive **null checks** added (bare-minimum subset hotfixed); Offer-Viewer perf in 2024.Fall (#1635566); PRs 98369/98685/98686 | #1672445 (TEP, RCA of 24-00965274) | 24-00965597 / 24-00965274 |
| **RFS console error / jQuery remains active** on the Location/Contacts tab | Null-ref in shared JS control (see §9) | PRs 111980/111981/112822 | #1718905 (2025.04 Beta) | — |
| Can't add **Up/Dn records** when manually entering locations on a nomination path | Web grid path-entry logic | Fix | #1725611 | — |
| RFS **screen configs filtering incorrect data**; Query Existing RFS slow/no results for internal users | RFS query/config | Fix | #1713824 (ONK), #1638796 (APL) | — |
| LC nom submission **lets users delete submitted noms** | Validation gap (2 scenarios) | PRs; Documented in TestRail | #1700159, #1721617 (TEP) | 24-00968076 |

**Fix recipe:** the **"Something went wrong" on Bids/Offers** outage pattern = **restart QPEC/web services** as the immediate unblock, then look for the `Index was outside the bounds of the array` exception in the CR Offer controller (#1672445); the durable fix is null checks. The **Del? checkbox** is config-gated and was an AT-visible regression — verify both config flags first (#1651310).

**Bug IDs:** #1651310, #1672445, #1718905, #1725611, #1713824, #1638796, #1700159, #1721617, #1731388, #1674120 · **Linked SF:** 24-00965597/274, 24-00968076.

---

## 9. Cluster F — "console error / jQuery remains active" (AT) & generic Web crashes

A specific **Automated-Test** signature: switching tabs throws a browser **console error** and **"jQuery remains active,"** failing AT scripts. Often **NOT manually reproducible** (or only on one DB engine), and frequently dispositioned as quarantine-the-AT / defensive null check rather than a user-facing defect.

| Symptom | Root cause / disposition | Bug |
|---|---|---|
| eSuite **Business Associate** → Name Change History tab: console error + jQuery remains active (**MSSQL only**) | AT-only; manual repro failed; pushed to quarantine/null-check; child WIs #1784659/#1789686; PRs 125124/125361/125809 | #1782252 (sprint 26.07) |
| **RFS** Location/Contacts tab: console error + jQuery remains active | Null-ref in a shared control; a `null check` fixes the immediate case but the same pattern exists on other screens (platform raised #1726036); reproduced manually after AT debug, existed in prior release | #1718905 (2025.04 Beta) |
| **Sitemap** screen won't open (internal/external) | `System.InvalidCastException: 'System.ObsoleteAttribute' → IQSecurityObjectAttribute`; obsolete **`GlobalReportExecutionController`** replaced with **`CoordinatedReportExecutionController`**; PRs 95624/95704/95706 | #1648717 (2024.04 Beta) |
| **Bids/Offers "Something went wrong"** crash | `Index was outside the bounds of the array` in CR Offer controller (see §8) | #1672445 |
| **User Contact Information**: "Save successful" toast **and** error message both shown | Not a bug — screen requires the user to have an associated **contact id**; data-setup | #1765890 (closed not-a-bug) |

**Fix recipe:** if it's **AT-only**, confirm a **manual repro** before treating it as a product defect; the standard disposition is a defensive **null check** in the shared JS/control or quarantining the failing AT. A genuine cast/obsolete-type error (#1648717) is a platform code fix. "Something went wrong" outages → §8 (restart + null checks).

**Bug IDs:** #1782252, #1718905, #1648717, #1672445, #1765890.

---

## 10. Cluster G — Reports & Report Viewer

| Symptom | Root cause | Fix / build | Bug | SF |
|---|---|---|---|---|
| **Report Viewer fails to open** (View Report) — only for users in **"CAW External Shipper (QPTM)"** security group; **PDF format only** (Word works) | Report-format/security handling for CAW external shippers (PDF path) | Delivered in **ONG 2025.10 HF**; PRs 127336/127337/127340; sprint 26.09 | #1790197 (ONG) | — |
| **ALR-88 / ALR-89 report parameters not working**; wrong picklist, "No Pick Definition found for pick id 26475," Start-Typing/filter dead | **SOA Picklist Definition** parameter-mapping problem (same engine as §6); these were dispositioned as **Rejected** / not-Maintenance (sent to core team) | PR 85918 (shared) | #1590890, #1605446 (both Rejected), #1605448 (BLINVGEN, Rejected) | 23-00888805, 23-00888941 |
| **RPT_CF03** Daily Nomination missing "By Location KGS" Group-By; **RPT_NN33** Daily Nomination params; **RPT_CF03** etc. | Report parameter/picklist metadata | PR 126790; sprint 26.09 | #1793248, #1793244, #1793258, #1793293-family (ONG) | 26-01090230 |
| Various report **parameter / picklist** issues (ALR88/89, CA15z wrong choice, CA24 netting, AL07M grouping) | Report-definition / parameter-mapping | mixed | #1448224, #146687, #1318551, #134049 | — |
| Aggregate Location Daily Export throwing technical warnings | Report config | — | #134049 | — |

**Fix recipe:** Report-Viewer-won't-open for a specific security group + **PDF** → try **Word/Excel format** as a workaround and check the security-group report path (#1790197). Report **parameter/picklist** failures are the **SOA Picklist Definition** family (§6) — many were **Rejected** out of Maintenance and routed to the core team; confirm whether it reproduces in core before escalating.

**Bug IDs:** #1790197, #1590890, #1605446, #1605448, #1793248, #1793244, #1793258, #1448224, #146687, #1318551, #134049, #164627 (Group ID param missing picklist) · **Linked SF:** 23-00888805, 23-00888941, 26-01090230.

---

## 11. Cluster H — IPWS exports / downloads

IPWS (NAESB customer postings) exports run via batch (PALOCEXP Location Export, CWOPERCAP, etc.) into staging tables, then post to the website. Symptoms are wrong/missing/truncated export data.

| Symptom | Root cause | Fix / disposition | Bug | SF |
|---|---|---|---|---|
| **Location Download export file not created** | Test-data preconditions (Post-to-EBB attribute, FERC CID, export-def path) — largely **config/data**, not a code defect; verified working once preconditions met | Closed after data setup | #1789906 (2026.04 IPWS Beta) | — |
| IPWS Locations download: **'Inactive Date' shows 'Effective Date From'** for inactive locations | **Business-process** matter — customers should create a **new inactive timeslice** (then INACT_DT = that slice's eff-date). Code change to use eff-date-**To** was made then **reverted** (per ONEOK). Separately, the export **batch failed** because staging **`PASTAG_LOC_EXPORT.UPDN_LOC_ID` (VARCHAR 20)** was narrower than source **`PACTRL_LOC_ASSOC.ASSOC_LOC_ID` (VARCHAR 30)** — a 21-char loc id broke it (widen the staging column). Export also blocked when **`QARCH_CTRL_IMPEXP.CUSTOMER_WHERE_CLAUSE`** was set (NULL it to allow export) | Code change reverted (#1801373 revert); staging-width + where-clause are the actionable fixes | #1771370 (ONI/OkTex), revert #1801373 | (SF on case) |
| IPWS **Index-of-Customers report shows 12/30/1899** instead of user dates in XML | Default/empty date serialized as the 1899 epoch | Fix | #1782581 | — |
| IPWS **Locations filter not working** / OAC; Location CSV not matching QPTM | Filter/query metadata | mixed | #278938, #246782 (VGL) | — |
| CWOPERCAP **Operational Available Capacity batch failing** | Batch | Fix | #1654650 (2024.04 IPWS Beta) | — |
| IPWS **Index-of-Customers & Location links switched** | Menu/link metadata | Fix | #1415883 (WWM) | — |
| IPWS **can't add/update** code table 52011 (`QXREF_DEFAULT_TSP`) | Code-table edit in Web | Fix | #1625007 | — |

**Fix recipe:** for "export file not created," verify the **batch preconditions + export-def File Path** first (#1789906 was config). For wrong/truncated values, check **staging-table column widths vs source** (`PASTAG_LOC_EXPORT` vs `PACTRL_LOC_ASSOC`) and a non-null **`CUSTOMER_WHERE_CLAUSE`** in `QARCH_CTRL_IMPEXP` (#1771370). For "inactive date" semantics, it's a **business-process** decision (timeslice the location) — the code change was reverted.

**Bug IDs:** #1771370 (revert #1801373), #1789906, #1782581, #1654650, #1415883, #1625007, #278938, #246782, #1623454, #1727477.

---

## 12. Cluster I — Code Decode / metadata-definition gaps

| Symptom | Root cause | Fix / build | Bug |
|---|---|---|---|
| **Can't save a Code Decode record in Web** (code table 26136 `QCODE_LOC_ATTR`) — works in Classic | The **code-table definition** was missing the **`SCREEN_READ_ONLY_IND`** column on the UI (the column existed in the DB and on a sibling table 26065 but not in 26136's definition), so the Web save failed | Added the missing column to the code-table definition; PRs 127471/127472/128022-128027; queued QPTM 2025.10 + 2026.04 | #1797552 |
| **Code Decode 26136** can't add records (IPWS EBB attribute) | Same as above (related #1812869/#1812888) | — | #1797552 family |
| Pre-Tax Indicator not shown on Code Table 2401 | Code-table definition | Fix | #1557785 (ONG) |
| Missing decode value in Code Table 37014 (QGM layer) | Code-table data | Fix | #155977 |
| Menu Editor: warning for manually-added items without Security ID/URL | Enhancement | — | #1668941 |

**Fix recipe:** "saves in Classic, fails in Web" for a Code Decode table almost always means the **code-table definition in Web is missing a column that exists in the DB** — compare the definition against the DB and against a working sibling code table (#1797552).

**Bug IDs:** #1797552, #1557785, #155977, #1668941.

---

## 13. Fix-Version Matrix

> **IntegrationBuild was EMPTY on all 250 sampled bugs.** "Fixed-in-build" below is **inferred** from iteration path (sprint YY.NN), `HOTFIX`/`queued for next QPTM 20YY.NN`/`Beta`/regression tags, and dev comments. **Confirm in QPTM release notes before quoting a build to a client.** Most fixes are cherry-picked across multiple maintained branches (commonly 2024.04 / 2025.04 / 2025.10 / develop).

| Bug | Cluster | Symptom (short) | State | Fixed-in-build (inferred) | SF case | Client |
|---|---|---|---|---|---|---|
| #1763785 | A | Loc Maint timeslice ORA-02289 (seq `SCTRL_MTR_FACILITY_HSQ`) | Closed | ENT 2024.04 HOTFIX 11/28/2025 (17.27.20) | 25-01050064 | ENT |
| #1774497 | A | Timeslice QPTM+TIPS shared meter (SEXTN sync) | Closed | cherrypick 2025.04 / 2025.10 / develop | — | ENT |
| #1777371 | A | Rate/Index copy-forward "source null" (QKExbEventHandler) | Closed | cherrypick 2024.04 / 2025.04 / 2025.10 | — | ENT |
| #1782369 | A | CASScheduleObjectCustom constraint (Sys Loc Groups) | Closed | cherrypick 2024.04→2026.04 | — | ENT |
| #1788366 | A | Loc Maint header Eff-Date-From error | Closed | HOTFIX (March HF) | — | ENT |
| #1773033 | A | Shared MDQ Related K no PPA popup (SCTRL_RELATED_CTR handler) | Closed | HOTFIX ~1/16; cherrypick 2025.04/2025.10 | — | ENT |
| #1777414 | A | Loc Maint new eff-date slice save fail (Oracle seq) | Closed | sprint 26.03 (≈2026.04) | — | core |
| #1744361 | B | QCM Links→Meter Header blank (QARCH_CNFG_MENU_DETAIL) | Closed | 2025.04 HOTFIX, Core Code Change | — | UPC |
| #1620262 | B | QCM duplicate meter rows (Web N/A default) | Closed | 2022.10 + 2024.04 develop/release | 23-00913209 | ONM |
| #1676927 | B | QCM "same key already added" (MTR_CCT event detector) | Closed | ESuite.Web 2024.04 develop/release | 24-00968427 | ONM |
| #1788087 | B | QCM "invalid eff date" (FirstDayToCache 365d) | Closed | queued ESuite 2026.04 (cherrypick 2025.04) | 26-01084783 | UPC |
| #1757897 | C/D | CRBIDEVAL offer picklist not filtering (Filter Col Expr) | Closed | 2025.10 (AHT) | — | core |
| #1721106 | C/D | TSP dropdown missing (CURRENT_TIMESTAMP vs EFF_DT) | Closed | 2025.04 | — | core |
| #1779785 | C | SOA picklist eff-date default (ScreenAsOfDate RootVM) | Closed | HOTFIX; sprint 26.05 (≈2026.04) | — | ENT |
| #1664436 | D | NNNOMLOAD false "another user submitted" (revert #1544800) | Closed | May-2024 patch (≈2024.04) | 24-00957668 | ETC |
| #1733844 | D | NNAUTOGEN "IQProcessLauncherService" missing | Closed | sprint 25.12 (2025.04) | — | core |
| #1721896 | D | AutoGen noms get invalid external user ID | Closed | Core + Client Metadata (2025.04) | 25-01007550 | ONK |
| #1651310 | E | Nom Submission Del? checkbox missing (external user) | Closed | 2024.10 GA / later (AT regression) | — | core |
| #1672445 | E/F | Bids/Offers "Something went wrong" (CR Offer null-ref) | Closed/Verified | TEP HF (null checks); perf 2024.Fall | 24-00965597 | TEP |
| #1718905 | E/F | RFS console error / jQuery remains active | Closed | 2025.04 | — | core |
| #1648717 | F | Sitemap won't open (ObsoleteAttribute cast) | Closed | 2024.04 | — | core |
| #1782252 | F | eSuite BA console error / jQuery (MSSQL, AT-only) | Closed | sprint 26.07 (≈2026.04) | — | core |
| #1790197 | G | Report Viewer fails for CAW security (PDF only) | Closed | ONG 2025.10 HF | — | ONG |
| #1793248 | G | RPT_CF03 missing "By Location KGS" Group-By | Closed | sprint 26.09 (≈2026.04) | 26-01090230 | ONG |
| #1590890 / #1605446 | C/G | ALR-88/89 report params / picklist | Closed (**Rejected**) | n/a (routed to core) | 23-00888805/941 | 1.5 Fed |
| #1771370 | H | IPWS INACT_DT wrong + staging width | Closed | code change **reverted** (#1801373) | (case) | ONI |
| #1797552 | I | Code Decode 26136 can't save (missing SCREEN_READ_ONLY_IND) | Closed | queued QPTM 2025.10 + 2026.04 | — | core |

---

## 14. Diagnostic pointers

- **Always start with: "Does it reproduce in eSuite Classic?"** If Web-only, it's a parity defect (§4/§5/§6/§12). If both, it's core/data/config.
- **Capture the exact error string + screen + tab + client + IDs** (TSP, Loc/Rate/Contract/Meter ID, Pick ID, process code, PQID). Screenshots/walkthrough docs are attached to nearly every bug.
- **App Insights** is the dev's go-to for outage RCA (Bids/Offers): query `exceptions`/`traces` by `user_AuthenticatedId` and time window; look for `Index was outside the bounds of the array` (#1672445).
- **Picklist not filtering** → inspect the pick definition: `QARCH_CTRL_PKLIST_NET.CUSTOM_QRY_STMT` for `@@FULL_WHERE_CLAUSE`, and the `Filter Column Expression` vs `Col Name` (§6a). For missing values, look for `CURRENT_TIMESTAMP` vs `EFF_DT_FROM/TO` (§6b).
- **QCM "invalid eff date"** on a correctly-timesliced meter → `ValidPlantMeterCache.FirstDayToCache()` (today − 365d) window (§5, #1788087).
- **IPWS export wrong/missing** → check the **export-def File Path**, **staging-table column widths** (`PASTAG_LOC_EXPORT` vs `PACTRL_LOC_ASSOC`), and a non-null **`QARCH_CTRL_IMPEXP.CUSTOMER_WHERE_CLAUSE`** (§11).
- **Code Decode won't save in Web** → diff the **code-table definition** vs the DB columns (missing `SCREEN_READ_ONLY_IND`-type column) (§12).
- **Code locations** (from comments/PR links): `Quorum.QPTM.Web` (incl. `Quorum.QPTM.ServiceCore/QPTMServiceCore_LocationMaintenance/QPTMServiceCore_LocationMaintenance.cs`), `Quorum.ESuite.Web` (Contract Meter List, Code Decode, picklist controls), `ENT.QPTM.Web` (client-specific event handlers `QKExbEventHandler`), the Esuite DAL repo (`SMeterHeaderQRMT`), QFC platform (picklist engine, `IQProcessLauncherService`, security attributes).

---

## 15. Escalation guidance

**Is the client's build fixed?** IntegrationBuild is blank on these bugs, so you **cannot read the fixed build off the work item** — use §13 (inferred) and then **confirm against QPTM release notes / the client's installed version**. Most fixes are cherry-picked to several maintained branches (2024.04 / 2025.04 / 2025.10 / develop) plus a client **HOTFIX**; a client on an **older** branch likely does **not** have it.

**Route to Engineering (Web/core code change) when:**
- A maintenance screen **save/timeslice/eff-date** fails in **Web but not Classic** (§4): missing sequence/sysgen, ENT event-handler Id=0, `CACTRL_SCHD_OBJ_CUSTOM` dup-insert, missing `SCTRL_RELATED_CTR` in the change handler.
- A **picklist** doesn't filter / misses values due to **metadata** (`Filter Column Expression`, `@@FULL_WHERE_CLAUSE`, `CURRENT_TIMESTAMP` gap) — note these are often **metadata fixes** deliverable without a binary (§6).
- A **batch web screen** has a DI/service gap (`IQProcessLauncherService`) or a reverted-WI regression (NNNOMLOAD #1544800) (§7).
- A **code/cast** error: obsolete controller (`GlobalReportExecutionController`→`Coordinated…`), `Index was outside the bounds of the array` in CR Offer controller (§8/§9).
- Provide: **exact error, screen/tab, client + TSP + IDs, Classic-vs-Web result, reproducible-in-core?**, and any walkthrough doc. Medium-priority items are routinely asked to **prove a core repro** before Maintenance picks them up (and may be **deprioritized to backlog** otherwise — several here were).

**Handle as Configuration / Data / Metadata (often no binary needed):**
- Picklist/pick-definition metadata (§6), code-table definition columns (§12), menu metadata `QARCH_CNFG_MENU_DETAIL` (§5), Classic Field-Defaults (§5), IPWS export-def path / `CUSTOMER_WHERE_CLAUSE` / staging widths (§11).

**Service-restart first (immediate unblock, no code):** "Something went wrong" on Bids/Offers/Capacity Release and similar transient web crashes — **restart QPEC/web services** (#1672445); also the QCM "invalid eff date" workaround needed a **QPEC restart** (#1788087). Capture logs/App-Insights before restarting.

**Treat as Expected behavior / not-a-bug (verify before escalating):**
- CRBIDEVAL: Web only lets you select an offer whose **bid window has passed**; you can type it manually in Classic (#1757897).
- Reallocation/PPA popup fires only when a change impacts a **closed** accounting month, not an open one (#1773033).
- User Contact Information requires an associated **contact id** (#1765890).
- IPWS inactive-date semantics: customers should **timeslice** a location inactive, not just flip status (#1771370 — code change reverted).

---

*Skill created 2026-06-14 from ADO QuorumSoftware Bugs (Energy Transportation + Maintenance\Midstream and Transportation branches), UI/Web functional area. 2,198 bugs matched the WIQL; 250 most-recent triaged; ~46 deep-read (description + repro + relations/PRs + full comment threads). 9 TIPS items dropped (mixed Maintenance backlog). IntegrationBuild empty on all sampled bugs → fixed-in-build inferred from iteration/tags/comments — CONFIRM IN RELEASE NOTES. Companion: SKILL_TIPS_* skills for settlement/journal engine defects; REPO_REFERENCE.md for repo→module mapping.*
