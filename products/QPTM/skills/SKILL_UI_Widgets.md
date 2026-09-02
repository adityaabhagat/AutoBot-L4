# SKILL: QPTM Web UI, Dashboard Widgets & Design Studio Troubleshooting

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** myQuorum **Web** UI rendering (page not loading / spinning / blank / slow, grid & column display, field/picklist behavior, browser-specific), **dashboard widgets** (not loading, not configurable, missing, wrong data), and **Design Studio** (persona/menu/site-map design tooling, widget recompile). Cross-cutting theme: **myQuorum Web vs legacy Classic (Citrix) divergence.**
**Companions:** Nom-page UI rendering → **SKILL_Nominations.md §13**. App access / "app not showing in Citrix" / OKTA / password is largely **security/user-admin** → **SKILL_Security_UserAdmin.md**. Reports-on-web → **SKILL_Reporting_Regulatory_Postings.md**.

> Evidence base: 416 closed `My Quorum Gas Pipeline` cases in `Case_Category__c IN ('User Interface','Widgets','Design Studio')` (UI 262, Widgets 129, Design Studio 25). Every root-cause claim cites a real SF case# and/or ADO item.

---

## TABLE OF CONTENTS
1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Architecture & Concepts (Web vs Classic, QFC, QPEC, widgets, Design Studio)](#2-architecture--concepts)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Cluster A — Page Not Loading / Down / Spinning (HIGHEST VOLUME)](#4-cluster-a--page-not-loading--down--spinning)
5. [Cluster B — Slow / Performance / Session Drops](#5-cluster-b--slow--performance--session-drops)
6. [Cluster C — Dashboard Widget Not Loading / Missing / Not Configurable](#6-cluster-c--dashboard-widget-not-loading--missing--not-configurable)
7. [Cluster D — Widget Showing Wrong / Cross-Tenant Data](#7-cluster-d--widget-showing-wrong--cross-tenant-data)
8. [Cluster E — Grid / Column / Field / Picklist Display](#8-cluster-e--grid--column--field--picklist-display)
9. [Cluster F — Design Studio (Persona / Menu / Site Map / Recompile)](#9-cluster-f--design-studio)
10. [Cluster G — Browser-Specific / Mobile](#10-cluster-g--browser-specific--mobile)
11. [The Web-vs-Classic Divergence Theme](#11-the-web-vs-classic-divergence-theme)
12. [Diagnostics (no SQL-first — version/build/browser/config/cache)](#12-diagnostics)
13. [Key Code Files & Repos](#13-key-code-files--repos)
14. [Known ADO Bugs](#14-known-ado-bugs)
15. [Escalation Decision Tree](#15-escalation-decision-tree)
16. [Expected Behavior / User Education](#16-expected-behavior--user-education)

---

## 1. Quick Triage Checklist

UI cases lean on **environment** facts, not SQL. Answer these first:

```
[ ] 1. EXACT symptom + message? ("spinning wheel", "Bad Request (400)", "Error Communicating with Server",
        "You are not authorized to view any dashboards", blank grid, missing widget)
[ ] 2. Web or Classic (Citrix/Storefront)? Is it BOTH or only one? (the single most diagnostic question)
[ ] 3. Which environment — PRD / UAT / UBT / DEV / 1.5 / A1 vs B1? (UAT/B-side issues are often config/deployment)
[ ] 4. Scope — ALL users, all TSPs (→ outage/perf/infra) vs ONE user / one persona / one widget (→ config/security)?
[ ] 5. Internal or External (shipper/operator) user? External-only = persona/security/widget-access config.
[ ] 6. QPTM build/version? (2020.03, 2022.04, 2022.10, 2023.04 + HF/Patch, 2025.10) — many fixes are version-gated.
[ ] 7. Browser + device? (Edge/Chrome supported; IE/Safari/iOS not — see §10)
[ ] 8. Recent change? (new build/hotfix, persona/Design Studio publish, DB refresh, maintenance window)
[ ] 9. Did a hard refresh / clear cache / log out-in / different browser change anything? (cheap first test — §12)
[ ] 10. Is it the WHOLE app or one screen/widget? Reproducible by Quorum, or only that client/data?
```

### Where does it live?
| Symptom | Cluster | First look |
|---|---|---|
| Whole app won't load / "down" / can't launch | §4 | Scope=all? → outage/infra (QPEC services, Cloudflare, middle tier) |
| Loads but slow / sessions drop / tabs freeze | §5 | QPEC instance count, middle-tier load, expensive widget query |
| One widget blank / missing / "can't add" | §6 | Persona + widget-access config, security setting |
| Widget shows another shipper's data | §7 | **CRITICAL** — security/context defect; log-out/in workaround then RCA |
| Grid won't scroll / column missing / sort wrong / picklist empty | §8 | Web grid component; compare to Classic |
| Persona menu / site map / Designer page broken | §9 | Design Studio app (separate from QPTM.Web), persona publish |
| Only on iPhone/iPad/old browser | §10 | Unsupported browser/device |

---

## 2. Architecture & Concepts

```
[Browser] ──HTTPS──> [Cloudflare/Gateway] ──> [Citrix StoreFront] (Classic apps)
                                          └──> [myQuorum WEB (QFC = Quorum Framework Core)]
                                                  ├── Persona-based dashboards + WIDGETS
                                                  ├── MVC UIControllers per persona (Scheduler/Operator/Shipper)
                                                  └── Middle tier: QPEC service instances ──> SQL Server
[Design Studio] (separate Web app) ── designs personas/menus/site-maps/widgets ──> published to Web
```

- **Web vs Classic.** Classic = the legacy Windows/Citrix desktop app delivered via Citrix StoreFront. Web (myQuorum / QQM / "QPTM Web") = the modern browser UI built on **QFC** (Quorum Framework Core, repos `Quorum.QFC.Web*`). Many setup/admin screens **were never ported to Web** and remain Classic-only (24-00987383 — Location ID picklist "not on web"). Behavior, validation and rendering can diverge between the two (§11).
- **QPEC** = the middle-tier service pool that Web and Classic both call. Under-provisioned or stopped QPEC instances are a recurring cause of slowness/outage (25-01012307 scaled 8→24 instances; 26-01088449 QCloud restarted QPEC services).
- **Persona** = a role-based UI profile (Scheduler, Operator, Shipper, external customer). It controls which **menu items, screens and widgets** a user sees. Built/published in **Design Studio**.
- **Widget** = a dashboard tile (Notices, Inventory, Title Transfer, Nominations, RFS, Cycle Changes, Planned Service Outage, Contact, Measurement, Process Alerts…). Access is gated by persona + QPTM security setting; many widgets have **client-override** implementations (e.g. `APL.QPTM.Web/.../Widgets/_InventoryWidgetAPL.cshtml`).
- **IPWS** = the public Informational Postings website (often surfaced via the **Notices widget**); IPWS issues frequently arrive tagged UI/Widgets (24-00950287, 23-00913727).

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|---|---|---|---|
| Whole app "down" / can't launch, ALL users, Web **and** Classic | Cloud/infra outage — QPEC services stopped, Cloudflare, gateway, maintenance-window misfire | Infra (QCloud restart) | 25-01021598/99/600/02/03, 25-01055447 (Cloudflare), 25-01021600 (RCA #1731449), 26-01088449 |
| "Error Communicating with Server" / "cannot connect to SQL… IQEndpointbrokerservice" | Middle-tier / QPEC / broker service down or stuck step-error process | Infra restart | 26-01066310, 26-01088449, 25-01051674 |
| Web slow (>15s), sessions disconnect, "tabs freezing" | Perf — under-scaled QPEC, DB/MT congestion, lock timeouts | Infra (scale/reboot) | 23-00903797, 25-01012307, 24-00992284, 25-01030064 |
| One widget slow/heavy, drags whole dashboard | Inefficient widget query (DataAccess call inside a loop) | Code (optimize) | 24-00957874 (RFS), 22-00819874 (Cycle Changes, #), 22-00683270 |
| Widget(s) load **no data** / spinner forever | Perf or widget data-fetch defect | Code/Infra | 25-01058? n/a; ADO #1758237, #1772188, #1788142 (QLS EQC) |
| Widget **missing** from dashboard / "can't select widget" | Persona / widget-access / security config | Config | 25-01015318, 23-00907223, 23-00906780, 23-00934126, 24-00957874 |
| "You are not authorized to view any dashboards" | Persona/dashboard security not assigned | Config | 22-00638257 |
| Widget shows **another shipper's** data | Security/context defect (CRITICAL) | Workaround (log out/in) + RCA | 23-00926187 |
| Widget data ≠ report (Inventory vs IN62, Measurement) | Rounding / scoping defect in widget query | Code | 22-00605047, 22-00591499, 22-00613247 |
| Notices/Title-Transfer/Nom widget broken or missing items | Widget defect or persona/data config | Code or Config | 23-00919360, 22-00615120, 22-00676019, 23-00930874, 25-01015318 |
| Grid won't scroll (mobile), column/field missing, sort wrong | Web grid component defect / not-ported field | Code | 24-00980920, 25-01003507, 25-01003508, 24-00981562(nom) |
| Picklist/dropdown empty or duplicated | Web picklist defect or not-on-web; dup loc values | Code/Config | 24-00987383, 24-00947782 |
| TSP "flips"/doesn't switch when clicking widget / Contacts page | Web TSP-context defect | Code | 22-00609334, 25-01030215, 22-00580619 |
| Design Studio: menu/site-map/personas not working; screens won't open | Design Studio app defect or persona-publish step not run | Code or Config | 23-00900969 (#1598641), 23-00917623, 22-00818454, #1602776 |
| Design Studio Persona Designer page errors on open | Design Studio access/config defect | Code/Config | 24-00944417, #1688359, #1714737/#1757068 |
| "Design Studio Feed API Version 2 no longer supported" after hotfix | Stale feed API version config | Data script/config | 23-00918122 |
| Only on iPhone/iPad/old browser | Unsupported browser/device | Education/Config | 22-00591405, 25-01018386 (VALIDATE_BROWSER=false) |

---

## 4. Cluster A — Page Not Loading / Down / Spinning (HIGHEST VOLUME)

By far the largest UI bucket: **Cloud Outage (43)** + **Performance (27)** root causes dominate, almost all **Critical**. These are *infrastructure*, not product-code, problems — recognize them fast and route to QCloud Ops.

### Tell-tales it is an infra outage (not a product bug)
- Scope is **all users / all TSPs**, hits **Web AND Classic** simultaneously (25-01021598/99/600/602/603 — a wave of dup "QPTM is down" cases on the same minute = one outage).
- Messages: *"Error Communicating with Server"*, *"CommunicationException for service endpoint IQEndpointbrokerservice"*, *"cannot connect to SQL Server"*, *"PRDA1 is down"*, blank/launch failure.

### Confirmed root causes & resolutions (verbatim from cases)
| Root cause | Resolution | Case / ADO |
|---|---|---|
| QPEC middle-tier services stopped/stuck | "QCloud Team restarting all WWM QPEC services" | 26-01088449 |
| Step-error processes started on Web tier | cleared on HPE PRDA1 Web | 26-01066310 |
| Services stopped before the maintenance window | RCA #1731449 | 25-01021600 |
| **Cloudflare** global outage | "global outage for Cloudflare… resolved" | 25-01055447 |
| Global QCloud outage | "Global outage solved by Qcloud" | 25-01051674 |
| Gateway / Secure Gateway Tunnel | infra resolved | 24-00966503 |

### Diagnostic / action
1. **Check scope immediately** — all users? Web+Classic both? other clients on the same pod? If yes → declare/attach to the active **Cloud Outage** incident, don't debug product code.
2. Have the customer try a **second browser / incognito / Classic** to confirm it's tier-wide vs their session.
3. Route to **QCloud Ops** to (a) check/restart **QPEC services**, (b) check middle-tier/Web-tier, (c) check Cloudflare/gateway status, (d) confirm no maintenance window mis-stop.
4. Many of these spawn a follow-up **RCA case** (e.g., 24-00960231 RCA for 24-00960212; 25-01046254; 24-00966740/24-00966859) — link them.

> Single-user "can't launch / app missing in Citrix" is **NOT** this cluster — that's persona/security/storefront entitlement (see §6 / SKILL_Security_UserAdmin.md): 25-01006006, 24-00970837, 24-00966518.

---

## 5. Cluster B — Slow / Performance / Session Drops

Distinct from a hard outage: the app loads but is unusably slow, sessions drop, tabs freeze.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Web >15s on all pages, lock timeouts | DB/middle-tier congestion | Reboot MT + Web tier | 23-00903797 |
| Citrix + Web slow, frequent disconnects | QPEC pool under-scaled | **Scaled QPEC 8 → 24 instances** | 25-01012307 |
| "Tabs are freezing" | downstream of a perf event | resolved once perf fixed | 24-00992284 |
| QQM timeout | idle connection timeout too low | gave client a way to raise **Idle Connection Timeout** | 25-01030064 |
| RFS widget dragging the dashboard | DataAccess call **inside a loop** retrieving RFSHeader | **Code**: add filters, hoist DataAccess out of the loop into a dictionary, use LINQ vars in-loop | 24-00957874 |
| Cycle Changes widget perf | heavy widget | fixed in **2022.10** | 22-00819874 |
| Widgets loading slowly / no data | widget query perf | ADO #1758237, #1772188, #1788142, #1791070 (QLS EQC) | — |

**Diagnostics:** confirm whether slowness is global (infra/QPEC/DB) or **one widget/screen** (code). If one widget, get the persona + which widget; the fix pattern (24-00957874) is to stop per-row DataAccess calls. For global, route to QCloud for QPEC scaling / tier reboot.

---

## 6. Cluster C — Dashboard Widget Not Loading / Missing / Not Configurable

The defining "Widgets" cluster (129 cases). Split into **(a) config/access** ("I can't see/add the widget") vs **(b) widget defects** ("the widget is broken/blank").

### (a) Config / persona / security — most "missing widget" cases
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Title Transfer widget missing from dashboard | persona/widget config (answered) | Config / education | 25-01015318 |
| Shippers/operators can't select certain widgets (RFS, Title Transfer) when customizing | widget-access config for persona | Config | 23-00907223 |
| Shipper can't customize dashboard at all (base security) | QPTM base security setting for shippers | Config | 23-00906780 |
| Nomination widget not available for external CAW shipper/operator | persona/widget availability config | Config | 23-00934126 |
| "You are not authorized to view any dashboards" | dashboard/persona security not granted | Config | 22-00638257 |
| External user can't add Notice widget (errors) | widget-access permission | Config (customer error) | 22-00536950 |
| Operator L2 action needs QPTM security permission | missing permission | Config | 22-00565480 |

> **Pattern:** "missing / can't add / can't customize widget" is almost always **persona + widget-access + QPTM security config**, frequently **external-user-only**. Check the persona assignment and the widget access settings before suspecting a defect.

### (b) Widget defects
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Notices widget broken | widget defect | Software updated | 23-00919360, 22-00615120 (Tres Palacios) |
| Notices widget "View More" links not working | IPWS link defect | — (IPWS) | 24-00950287 |
| Notice detail blank navigating IPWS→Notice widget | widget/IPWS nav defect | Software updated | 22-00676019 |
| Planned Service Outage widget issue | widget data defect | **Data script provided** | 22-00591484 |
| Dashboard widget timeout (UAT) | widget perf/defect | Software updated | 22-00683270 |
| Widgets not loading when a default **QLNG** TSP exists | TSP-default handling defect | **Code change by engineering** | 22-00580619 |
| External-user process alerts widget | widget defect | Workaround | 22-00688189 |
| Process Queued ID popup keeps reappearing | widget/poll defect | Workaround | 22-00586596 |
| Build 2020.09 — widgets need L2 grid recompile | widget build dependency | Software updated (recompile) | 22-00818454 |
| Nom widget not showing cuts per cycle deadlines | widget data/timing defect | Software update available | 22-00565413 |
| Nominations widget missing Title Transfers (APL HF3) | widget data scope | (config) | 23-00930874 |

**Diagnostics:** identify (1) persona, (2) exact widget, (3) internal vs external, (4) build. If only one persona/user → config (a). If the widget itself errors/blank for everyone on that build → defect (b); check for a client-override widget (`<CLIENT>.QPTM.Web/.../Widgets/_<Name>Widget<CLIENT>.cshtml`) before assuming base behavior.

---

## 7. Cluster D — Widget Showing Wrong / Cross-Tenant Data

Low volume but **high severity** — treat as security incidents.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Shipper can see another shipper's inventory** on Inventory widget | data-scoping/context defect (Critical) | Workaround: **log out & back in** resolves; engineering RCA | 23-00926187 |
| Inventory Position widget ≠ IN62 report (tolerance min/max rounding) | rounding defect in widget calc | Software updated | 22-00591499, 22-00605047 |
| Operator Measurement widget (ALRX04) showing **all** locations' data | scoping defect | Software update available | 22-00613247 |
| Title Transfer widget wrong balances | data/context | Customer error / data | 22-00536956 |

**Action:** for cross-tenant data exposure (23-00926187) escalate immediately; the field workaround is log-out/in, but always open an RCA/bug. For widget-vs-report mismatches, reconcile against the authoritative report (IN62/ALRX04) — the widget query is usually the side that's wrong.

---

## 8. Cluster E — Grid / Column / Field / Picklist Display

Web-grid and field-rendering defects, frequently **Web-only** and frequently "this exists in Classic but not Web."

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| myQuorum grids won't scroll on mobile | Web grid component | (config/code) | 24-00980920 |
| Contract Maintenance sort broken | Web grid sort defect | fix in **2025.10** | 25-01003507 |
| Location Maintenance sort broken | Web grid sort defect | Eng resolved (no hotfix) | 25-01003508 |
| Location ID **picklist** returns no records | screen not ported to Web | **Declined** — "setup screen, not moving to web; type IDs manually" | 24-00987383 |
| PDA Submission Loc dropdown **duplicated** values | dup loc config | Config | 24-00947782 |
| Invoice Maintenance tab **duplicates** when clicked | Web tab defect | Software updated | 24-00950611 |
| Contacts page doesn't change TSP correctly | Web TSP-context defect | Config | 25-01030215 |
| TSP "flips" when clicking a widget | TSP-context defect | Software update available | 22-00609334 |
| Contact widget behavior | widget/field defect | Software updated | 22-00565500 |
| Report Favorites/Recents params don't save | Web reports-grid defect | Software updated | 22-00601097, 22-00712620 |
| TSP Labels gone (Design Studio) | rendering defect | Release upgrade required | 23-00922427 |

**Diagnostics:** reproduce in **both Web and Classic** — if it works in Classic, it's a Web port/grid defect (cite the version where it's fixed, e.g., 2025.10 for 25-01003507). For "picklist empty/dropdown" check whether the screen is even supported on Web (24-00987383).

---

## 9. Cluster F — Design Studio

Design Studio is a **separate Web application** (repos `Quorum.DesignStudio.Main` / `Quorum.DesignStudio.Application.Web`) used to design **personas, menus, site maps, and widgets**, then publish them to the runtime Web. Small volume (25 cases) but distinct.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Screens not opening from Menu using **new personas** | Design Studio menu/persona defect | Delivered **Patch 2, ADO #1598641** | 23-00900969 |
| **Hamburger menu** not working for Design Studio personas | menu defect | Bug **#1602776** Closed | (TGL 2022.10) |
| Persona Designer **Menu & Site Map** design not working | config/persona | Config | 23-00917623 |
| Error opening **Persona Manager / Designer** pages (UAT) | Design Studio access/config | Config | 24-00944417, #1688359, #1714737/#1757068 |
| "Design Studio **Feed API Version 2** no longer supported, use v3" after HF4 | stale feed-API version | **Data script** / config | 23-00918122 |
| Design Studio **Access** (APL 2023.04) | access config | Config | 23-00933867 |
| **Recompile Design Studio widgets** with L2 grid for 2020.09 | build dependency | Software updated | 22-00818454 |
| Standard personas / some widgets **not showing for external users** | persona publish/visibility | Training/config (run publish) | 23-00926747, 23-00900433, 23-00900972 |
| "What's the process to see new personas on web?" | publish step | Training (run the persona publish) | 23-00900469, 22-00816000 |

> **Tell-tale:** "new persona/menu/widget doesn't appear on the web" is usually that the **publish step wasn't run** (Training/config), not a defect — see §16. True defects (menu/site-map not working) trace to the Design Studio app and have ADO bugs (#1598641, #1602776).

---

## 10. Cluster G — Browser-Specific / Mobile

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Dashboard/widget issues on **iPhone/iPad** | iOS/Safari not a supported platform | Software update available / education | 22-00591405 |
| Grids not scrollable on mobile | mobile rendering limitation | code/config | 24-00980920 |
| IPWS "supported browser" block | browser-allowlist config | set config **`VALIDATE_BROWSER = false`** (`ValidateBrowserAttribute.cs`, QFC) | 25-01018386 |
| Citrix "black box" / session issues | Citrix client/session | terminate session / Citrix config | 25-01023882 |

**Action:** confirm browser/device first. myQuorum Web targets current **Edge/Chrome**; IE/Safari/iOS are not fully supported. The browser allowlist is enforced by QFC's `ValidateBrowserAttribute`; it can be disabled per environment via `VALIDATE_BROWSER` (25-01018386).

---

## 11. The Web-vs-Classic Divergence Theme

This is the cross-cutting QPTM theme to capture. It shows up three ways:

1. **Feature parity gaps** — screens/fields that exist in Classic were never ported to Web, so the Web behavior is "missing," not broken: Location ID picklist not on web (24-00987383, *declined*), Path Rank field missing on Web Nom Submission (24-00981562 — see Nominations §6), grid sort/scroll defects unique to Web (25-01003507/08, 24-00980920).
2. **Behavioral / validation divergence** — the same action validates or renders differently in each: a nom invisible on the Web Submission screen but present in Confirmation Response, with Classic **not** throwing the overlap error that Web does (25-01016479 — Nominations §13). Always ask **"does it work in Classic?"**; if yes, it's a Web defect and Classic is the workaround.
3. **Outages hit both, but symptoms differ** — infra outages take down Web **and** Classic together (25-01021598-603, 25-01051674), which is itself the diagnostic that it's infra, not a screen bug (§4). Conversely "Classic apps missing from Storefront" with Web fine (24-00952598) is an entitlement/storefront issue, not an outage.

**Practical rule:** for any UI case, the **2nd triage question is always "Web or Classic, and does the other one work?"** — the answer routes you to outage (both down) vs Web port defect (Classic works) vs storefront/entitlement (only Classic missing).

---

## 12. Diagnostics

UI diagnostics are **environment-first**, not SQL-first.

### Cheap first tests (do these / ask the client before escalating)
```
[ ] Hard refresh (Ctrl+F5) and CLEAR CACHE — fixes many stale-asset/widget issues
[ ] Log OUT and back IN — known workaround for context bugs incl. cross-tenant data (23-00926187)
[ ] Try a different SUPPORTED browser (Edge/Chrome) / incognito
[ ] Try CLASSIC — if it works, it's a Web defect (Classic = workaround) (§11)
[ ] Confirm BUILD/VERSION (Help/About) — map to known fix versions
[ ] Confirm SCOPE — just me / my persona / my TSP, or everyone? (config vs outage)
```

### What to capture for the ADO bug / escalation
- Build/version + HF/Patch level; environment (PRD/UAT/1.5, A1 vs B1).
- Persona + exact widget/screen; internal vs external user.
- Browser + version + device; screenshot and **browser console / network** errors (400/500, failed XHR).
- Whether Classic reproduces it.

### When DB *is* relevant (rare for UI)
Widget **data** mismatches (Cluster D) are reconciled against the authoritative report, not the widget. Persona/widget **access** lives in QPTM security/persona config (Design-Studio-published), checked via the Persona/Security admin screens — not free-form SQL. Only drop to SQL when a widget's underlying data is wrong (then query the same tables the report uses, e.g., inventory/measurement — see SKILL_Customer_Accounts_Inventory.md).

---

## 13. Key Code Files & Repos

### myQuorum Web framework — QFC (Quorum Framework Core)
| Repo | File | Purpose |
|---|---|---|
| `Quorum.QFC.Web` | `Quorum.QFC.Web.Core/Controllers/DashboardController.cs` | Dashboard host (widgets render here) |
| `Quorum.QFC.Web` | `Quorum.QFC.Web.Core/Filters/ValidateBrowserAttribute.cs` | **Browser allowlist** (config `VALIDATE_BROWSER`, case 25-01018386) |

### QPTM Web (persona controllers / widgets)
**Repo `Quorum.QPTM.Web`** (id `41e317c0-844c-4728-98da-529092957738`)
| File | Purpose |
|---|---|
| `Quorum.QPTM.Web.Controllers/Personas/Scheduler/QUIControllerInventoryImbalances.cs` | Scheduler Inventory widget data |
| `Quorum.QPTM.Web.Controllers/Personas/Operator/QUIControllerOBAInventoryImbalances.cs` | Operator Inventory/Imbalance widget |
| `Quorum.QPTM.Web.Controllers/Personas/Scheduler/QUIControllerInventoryStorageBalances.cs` | Storage balances widget |
| `Quorum.QPTM.ServiceClient/QPTMServiceClient.cs` | Web → middle-tier (QPEC) calls |
| `Quorum.QPTM.Application.Web/` | QPTM Web app host |

### Client-override widgets (always check before assuming base behavior)
**Repo `APL.QPTM.Web`** (representative): `APL.QPTM.Web/Views/Shared/Widgets/_InventoryWidgetAPL.cshtml` (+ `.generated.cs`), `APL.QPTM.Web.Core/UIControllers/QUIControllerRFSBidApproval.cs`, `APL.QPTM.DAL/CodeGen/RFSHeaderDAL.cs` (RFS-widget perf case 24-00957874). Pattern: `<CLIENT>.QPTM.Web/Views/Shared/Widgets/_<Name>Widget<CLIENT>.cshtml`.

### Notices / IPWS widget
| Repo | File | Purpose |
|---|---|---|
| `Quorum.Upstream.QDO.Web` | `Quorum.QDO.Web/Views/Shared/QDOWidgets/NoticesWidget.cshtml` | Notices widget view |
| `Quorum.Upstream.QDO.Web` | `Quorum.QDO.Web/Controllers/QDOWidgetAccessController.cs` | **Widget access** gating |
| `Quorum.IPWS.Application.Web` | `.../ApplicationStart/RouteConfig.cs` | IPWS routing (Notice "View More" links, 24-00950287) |

### Design Studio (separate app)
**Repos `Quorum.DesignStudio.Main`, `Quorum.DesignStudio.Application.Web`**
| File | Purpose |
|---|---|
| `Quorum.DesignStudio.Web/Controllers/PersonaDesignerController.cs` | Persona Designer page (#1688359, #1714737/#1757068) |
| `Quorum.DesignStudio.Web/Scripts/PersonaDesigner/MenuEditor.js` | Menu / site-map editor (hamburger-menu bug #1602776) |

### Code search patterns
```bash
{"searchText":"<WidgetName>Widget"}                         # e.g. InventoryWidget, NoticesWidget
{"searchText":"<WidgetName> repo:<CLIENT>.QPTM.Web"}        # client override
{"searchText":"PersonaDesigner OR MenuEditor"}             # Design Studio
{"searchText":"VALIDATE_BROWSER"}                          # browser allowlist config
```

---

## 14. Known ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1598641** | Patch / **Completed** | TGL — Patch 2 on 2022.10 (Design Studio screens-not-opening-from-menu fix) | §9 | 23-00900969 |
| **#1602776** | Bug / **Closed** | TGL — 2022.10 Hamburger menu not working for Design Studio personas | §9 | — |
| **#1688359** | Bug / **Closed** | QLS — error on Design Studio Persona (Customer Upgrade Testing, EQC) | §9 | — |
| **#1714737 / #1757068** | Bug / **Closed** | TGL — Cannot access Persona Designer in Design Studio (UAT) | §9 | 25-01005178 |
| **#1758237** | Bug / **Closed** | QLS EQC Perf — Widgets not loading any data | §5/§6 | — |
| **#1772188** | Task / **Closed** | QLS EQC Perf — Dashboard Widgets loading slowly | §5 | — |
| **#1788142 / #1791070** | Task | Dev — QLS EQC Perf — Dashboard Widgets loading slowly | §5 | — |
| **#1784098** | Bug / **Proposed** | QDO — Pending Maintenance screen loads slowly, grid stuck in continuous loading | §5/§8 | — |
| **#1731449** | RCA | Services stopped before maintenance window → PRDA1 outage | §4 | 25-01021600 |

> **Takeaway:** the highest-volume UI buckets (outage/perf) are **infra incidents dispositioned by QCloud Ops** (QPEC restart/scale, Cloudflare, MT reboot) and frequently are **not** linked to a product bug — they generate RCA cases instead (#1731449). Genuine product bugs concentrate in **Design Studio** (persona/menu) and **specific widgets** (perf/data-scope). Many client widget issues are resolved by **config** (persona/widget-access/security), not code.

---

## 15. Escalation Decision Tree

```
UI / Widget / Design Studio case
│
├─ Whole app won't load / "down"?  (§4)
│   ├─ Scope = ALL users AND Web+Classic both?  → INFRA OUTAGE → QCloud Ops
│   │     (check QPEC services, middle/Web tier, Cloudflare/gateway, maintenance window) → attach RCA
│   └─ Just me / one app missing in Citrix?  → entitlement/security → SKILL_Security_UserAdmin.md
│
├─ Loads but slow / sessions drop / freeze?  (§5)
│   ├─ Global slowness?  → QPEC scaling / MT reboot / idle-timeout (QCloud)
│   └─ One widget/screen heavy?  → CODE (hoist DataAccess out of loops — 24-00957874)
│
├─ Widget missing / can't add / "not authorized"?  (§6a)
│   └─ persona + widget-access + QPTM security config (often external-user-only) → CONFIG
│
├─ Widget blank / broken / shows wrong data?  (§6b / §7)
│   ├─ Wrong/cross-tenant data?  → CRITICAL: workaround log-out/in, open RCA/bug (23-00926187)
│   ├─ Widget ≠ report?  → reconcile vs report; widget query defect → CODE
│   └─ Check for <CLIENT>.QPTM.Web override widget before assuming base
│
├─ Grid/column/field/picklist?  (§8)
│   ├─ Works in Classic, not Web?  → Web port/grid defect → CODE (cite fix version)
│   └─ Screen not on web?  → may be by-design (24-00987383 declined)
│
├─ Design Studio (persona/menu/site-map/widget design)?  (§9)
│   ├─ "New persona/widget not showing"  → did they run PUBLISH? → Training/config
│   └─ Menu/Designer page errors  → Design Studio app defect (#1598641, #1602776, #1714737)
│
└─ Only on iPhone/iPad/old browser?  (§10)
    └─ unsupported platform → education; or VALIDATE_BROWSER config (25-01018386)
```

---

## 16. Expected Behavior / User Education

Root Cause = **Training (31)** / **Customer Error (9)** — recognize these to avoid needless escalation.

| Reported as | Reality | Case |
|---|---|---|
| "New personas/widgets don't show on the web" | The **persona publish process** wasn't run — run it | 23-00900469, 23-00900433, 23-00926747, 22-00816000 |
| "Dashboard widgets have disappeared" | User-level dashboard reset / re-add widgets | 23-00922456 |
| "Widgets are not loading" (2020.03) | Setup/usage question, not a defect | 22-00666853 |
| "How do I configure / use this widget?" | Documentation/how-to | 22-00803956, 22-00521678, 22-00597438, 22-00686174, 22-00666847/48, 22-00662444 |
| "Bad Request (400) errors" | client-side / stale session (customer error) | 26-01097792 |
| "Can't open any TSP in UAT" | usage/setup, not a defect | 26-01086114 |
| IPWS notices "not posting" | posting workflow not completed (customer) | 23-00913727 |
| iPhone/iPad rendering | unsupported device | 22-00591405 |
| "Help updating a widget in the Web" | how-to walkthrough | 26-01071118 |

**Tell-tale it's Training/Expected:** a *new* Design-Studio persona/menu/widget "isn't showing" (publish not run), a *single user's* dashboard changed (they customized/reset it), or the question is "how do I…". User-saved settings can also be wiped by a new build/env and need a restore script (23-00922221, *Data Script Provided*).

---

*Skill created: 2026-06-01*
*Based on: 416 closed QPTM `User Interface`/`Widgets`/`Design Studio` SF cases + ADO #1598641, #1602776, #1688359, #1714737/#1757068, #1758237, #1772188, #1788142/#1791070, #1784098, RCA #1731449.*
*Companion: SKILL_Nominations.md §13 (nom-page UI), SKILL_Security_UserAdmin.md (app access/entitlement), SKILL_Reporting_Regulatory_Postings.md (reports-on-web). Applicable to all QPTM clients on myQuorum Web.*
