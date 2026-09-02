# QPTM_SCREEN_INFO — Screen & Navigation Reference

Complete, source-verified inventory of every screen in the QPTM application (both UIs), the screen architecture, and the menu navigation paths. Built 2026-07-04/05 from live ADO source: Quorum.QPTM.Web (develop), Quorum.QPTM.ClassicGUI, APL.QPTM.* layers, and Quorum.QPTM.Metadata `/STANDARD 16.0/`.

## Files

| File | Contents | Use it for |
|---|---|---|
| **QPTM_SCREEN_REFERENCE.md** | Master document (Parts 1–3 combined) | Reading end-to-end / KB search hits |
| **01_WEB_SCREENS_AND_ARCHITECTURE.md** | ~110 Web screens + 25+ widgets by module; UIController/MVC/RootVM architecture; QARCH metadata; screen registration; L4 triage table | Anything myQuorum Web |
| **02_CLASSIC_SCREENS_AND_ARCHITECTURE.md** | ~151 ClassicGUI QVp screens by module with ✔/✖ Web-equivalence; plugin-DLL architecture; legacy-MFC vs SOA screens; CAW build; client overrides | Anything Classic/Citrix |
| **03_NAVIGATION_MAP.md** | Classic menu trees (Screens / System / Maintenance / CAW) + 3 Web persona menus + click-path examples | "How do I open screen X" |
| **QPTM_NAVIGATION_DATA.json** | 350 click-paths as structured data: `menuPath[]` + `screenSecurityId` + hidden/inactive flags, per build (internal/CAW) and per Web persona; per-screen Links menus | Walkthrough generation — template `menuPath` into steps |
| **SCREEN_INDEX.json** | One record per screen (168 web + 151 classic): name, module, kind, source path, notes/tabs, security id, and its menu paths joined in | Lookups / joining screen info to nav paths |

## Quick recipes

- **Walkthrough for a screen:** find it in `SCREEN_INDEX.json` → take `classicMenuPaths` / `webMenuPaths` → render "Click *A*, then *B*, then *C* — the *Screen* opens." Skip entries with `hidden`/`inactive` = true.
- **Which persona sees a Web screen:** `webMenuPaths[].persona` (PIPELINE INTERNAL / SCHEDULER / OPERATOR).
- **Screen exists on Web?** `02_...md` catalog has ✔/✖ per Classic screen; config screens (Cycles, Validation Rule Maintenance/XRef, TSP Maintenance, EDI defs…) are Classic-only.
- **Client-specific menus:** everything here is the STANDARD tree; clients override via `<CLIENT>.QPTM.Metadata` (`QARCH_CNFG_MENU` / `QARCH_CNFG_DYNUC`). Re-run the extraction against the client repo for client walkthroughs.

## Caveats

- `hidden`/`inactive` flags come from standard metadata; actual visibility is also security-trimmed per user (QVP*/QUC* security objects).
- Classic screen security id = the C++ class name (e.g. `QVpCycles` → menu rows use `QVPCYCLES`).
- 19 classic screens have no menu path in standard metadata — they are popups/dialogs launched from parent screens, unregistered/dormant screens, or client-menu-only items.
- QFC framework maintenance screens (Object Usage, security admin, code tables) ship in the QFCMaintScreens NuGet — they appear under Classic's Maintenance menu on internal builds but have no source in the QPTM repos.
