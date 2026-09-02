# SKILL: TIPS UI / Dashboard & Widgets Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Scope:** TIPS Web dashboard & widgets (Business Results, Cuts Dashboard, CAW/WEBCAW notices, Operator/Scheduler/Plant-Accountant persona widgets), Plant/Company context selector, widget security & personas, dashboard edit rights, Web-vs-Classic screen behavior, query screens returning no data, browser/server-metadata cache, OKTA login/access as it presents through the UI, file upload (Analysis/Import-Export), and UI symptoms that are really QPEC/Middle-Tier environment failures.
**Use When:** Any TIPS case categorized User Interface / Dashboard / Widgets / Design Studio — widgets missing or not editable, dashboard blank, context selector missing, "no company set," screen shows no records in Web but works in Classic, UI frozen/unresponsive, multi-user disconnects, or a widget renders the wrong/duplicated value.
**Companion:** Excel/Crystal export & report-rendering issues fall under **Reporting** (Case_Category = Reporting), not here — see the TIPS Reporting/Statements skill. For batch/accounting processes see the TIPS process skills. QPTM has its own dashboard-widget surface — do **not** confuse the products; both render "myQuorum dashboard" widgets but security objects and repos differ.

> **Evidence base:** 145 closed TIPS UI/Dashboard/Widgets/Design-Studio cases (re-mined 2026-06-13; matches the ~142 originally cited). Only **19 are actionable** — **Application Configuration 11 + Software Defect 8**. There is **no "ChangeConfig" root cause value** in this data. The category is heavily polluted: **User Administration Request 45** (mostly OKTA account ops), Training 10, Cloud Outage 9, Customer Cancelled 9, No Action Taken 7, null 7, Business Change 5, Customer Error 4, Platform 4, Performance 3. **True UI-defect rate in TIPS is low** — most "UI" tickets are user-admin, outage, or education. Every claim below cites a real SF case and/or ADO item observed during mining. Where the data showed no clear fix, this file says "resolution pattern unclear" rather than inventing one.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Decision Tree](#2-decision-tree)
3. [Widget Security, Personas & Dashboard Edit Rights (top actionable cluster)](#3-widget-security-personas--dashboard-edit-rights)
4. [Context Selector / "No Company Set"](#4-context-selector--no-company-set)
5. [Widget Data Display Defects (renders, but wrong)](#5-widget-data-display-defects)
6. [Web-vs-Classic Screen Behavior](#6-web-vs-classic-screen-behavior)
7. ["UI Problem" That Is Really the Environment (QPEC / Middle Tier)](#7-ui-problem-that-is-really-the-environment)
8. [OKTA / User Administration (45 cases — biggest bucket, zero defects)](#8-okta--user-administration)
9. [Expected Behavior / User Education FAQ](#9-expected-behavior--user-education-faq)
10. [Known ADO Items](#10-known-ado-items)
11. [Key Code Files & Repos](#11-key-code-files--repos)
12. [Diagnostic SQL / Checks](#12-diagnostic-sql--checks)
13. [Escalation Guidance](#13-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom | Most likely cause | First check | Evidence |
|---|---|---|---|
| Regular (non-power) user can't add/delete/move widgets — "not allowed to modify global dashboard" | Missing dashboard-edit / widget security objects on the group (GRP 5610 "TIPS Regular User" pattern); acknowledged gap, script exists | Compare group security objects vs Power User group; run the known seeding script | 24-00965645, 24-00967070, 23-00917209, ADO #1739530 (Proposed/open) |
| Whole group / scheduler dashboards have no widgets configured | Personas + widgets never seeded for that group's securities | Persona-widget seed rows for the group; script into DB | 23-00912075 |
| Plant (or Company) context selector missing from TIPS Web dashboard | One or more modules in Security User Setup not set to INTERNAL | Security User Setup → set ALL modules = INTERNAL for that user | 25-01034152 |
| "No company set" alert / blank dashboard for NEW users | User never picked Company/params in Dashboard settings — user education | Dashboard settings → select Company (+ related params) | 26-01091486 |
| Dashboard stale / can't start app / widgets odd after upgrade | Browser cache or server metadata cache stale | Clear browser cache; reload metadata cache; restart web servers post-release | 24-00982617, 22-00530860 |
| UI frozen, blank, "Query Returned No Results", random disconnects — multiple users | NOT a UI bug — QPEC/Middle-Tier service down, memory/RAM exhaustion, or storage latency | QPEC/QTIPS service state + memory on MT servers; restart; check host | 26-01069207, 26-01066701 |
| Widget shows wrong/duplicated/blank value (renders but incorrect) | Core widget/report display defect | Match to known ADO bug (§5); confirm client fix version | 24-00941216 (#1649311), 22-00556223 (#142551), 22-00530861 |
| Web screen blank / behaves differently while Classic works | Web-vs-Classic defect, persona shift, or client grid override hiding columns/fields | Reproduce in BOTH; check client `<CLIENT>.TIPS.Web`/Metadata override | 25-01025847, OXY 22-00521907/911/912/913 |
| Query screen returns no records | Wrong persona (no Query tab), wrong BA/time-slice, or different base view in Web | Persona → filter params → base-view mapping | 26-01106043, 26-01080882 |
| File upload (e.g. Analysis CSV) fails "file name/path doesn't exist" | Import/Export definition path missing | Add the Import/Export definition path for that interface | 26-01064032 |
| User can't log in / sees nothing at all | OKTA account/group membership / MFA — user-admin request, not a defect | OKTA groups (`<Client> External Users` + `... ESuite PRD A1` + `... TIPS PRD A1`); MFA dual-authenticator | 45 user-admin cases, e.g. 26-01100742, 25-01049102 |

---

## 2. Decision Tree

```
TIPS UI / dashboard / widget case reported
│
├─ Multiple users / whole environment affected (freeze, blank, disconnects, timeouts)?
│   └─ ENVIRONMENT, not UI → §7. Check QPEC/QTIPS/MT services & memory; restart; check VM host.
│      (26-01069207 storage latency on QPEC host; 26-01066701 hung QTIPS services)
│
├─ Single user, can't see ANYTHING (login fails / no apps / blank eSuite)?
│   └─ §8 User-admin: OKTA account exists? In the right groups (<Client> External Users,
│      ESuite PRD A1, TIPS PRD A1)? MFA/dual-authenticator? Activation email expired? Right User-ID prefix?
│
├─ Widgets missing or not editable?
│   ├─ "Not allowed to modify global dashboard" → §3 dashboard-edit security script/objects (24-00965645)
│   ├─ Whole group / scheduler has no widgets → §3 persona/widget seeding script (23-00912075)
│   └─ One widget can't be turned off → missing security object for that widget (23-00917209)
│
├─ Context selector missing / "no company set"?
│   ├─ Plant selector missing → Security User Setup modules = INTERNAL (25-01034152)
│   └─ New user "no company" → user picks Company in Dashboard settings (26-01091486)
│
├─ Widget renders but data is wrong/blank/duplicated?
│   └─ §5 known display defects: Cuts Sched-Qty-blank-when-0 (#1649311 Closed),
│      CAW Notices wrong time format (#142551 Closed), Operator Dashboard report period
│      (set core report param = Gas Day, 22-00530861)
│
├─ Web screen ≠ Classic?
│   └─ §6: reproduce in BOTH. Blank fields in Web only → config/cache/persona shift (25-01025847).
│      Columns missing → client web-grid override (`<CLIENT>.TIPS.Web`). Crash → core defect (22-00521907).
│
├─ Query/search screen returns nothing?
│   └─ Persona (Query tab present?) → filter (BA/time-slice) → base-screen mapping (§6b)
│
├─ File upload fails "path/name doesn't exist"?
│   └─ Add Import/Export definition path (26-01064032)
│
└─ "How do I…" / fee grouping / parameter defaults / Web run-time differences?
    └─ §9 Expected behavior / user education
```

---

## 3. Widget Security, Personas & Dashboard Edit Rights

**(Top actionable cluster — 4 of 19 actionable cases.)**

**Symptom:** A TIPS *Regular User* (the GRP ID 5610 pattern) cannot add, delete, or move widgets on their dashboard; the error says the user is **"not allowed to modify a global dashboard."** Granting individual security privileges does not help. Variants: an entire group / scheduler persona sees **no widgets at all** (23-00912075 — "Schedulers are seeing errors for widgets"); a single widget (e.g. FlowCal) **cannot be toggled off** (23-00917209).

**Root cause:** TIPS Web treats the shared dashboard as a *global* dashboard. Edit rights and widget visibility hang off security objects and persona/widget seed rows that are **not granted to non-power-user groups out of the box**. Quorum acknowledged this as a defect — ADO **#1739530** ("EQC - Can't add widgets - User not allowed to modify global dashboards") is **still Proposed** (no shipped product fix as of mining date). Until it ships, this is dispositioned operationally with a script/security-object grant.

**Resolution recipe (what actually closed the cases):**
1. **24-00965645 (MarkWest), Software Defect:** Resolution verbatim — *"A script was provided to the client that will allow TIPS regular user to modify dashboards."* Request that script from Cloud Ops / prior-case attachments rather than re-deriving it. The case originator had already documented the manual security steps tried (GRP 5610) and still hit the global-dashboard error.
2. **24-00967070 (MarkWest), Application Configuration:** the duplicate/companion BUG case — closed by answering which hotfix carries the fix (ties to #1739530). Use to set client expectation: product fix is pending, script is the interim.
3. **23-00912075 (Crestwood "TIPS Gathering"), Application Configuration:** schedulers logging in saw widget errors → *"system updated for the widgets"* — the persona-widget rows for the scheduler group were seeded/corrected. Pattern: seed the persona-widget config, don't grant Power User wholesale.
4. **23-00917209 (Pioneer), Application Configuration:** could not turn off the FlowCal widget → *"User needed to add additional security object. See Attached Document."* The case attachment names the exact object.
5. **Verify after change:** user logs out/in (or clears cache) and can edit a *personal* copy of the dashboard / toggle the widget.

**Where the code lives:** the **global-dashboard edit gate is in the shared QFC Web layer**, not TIPS-specific — `Quorum.QFC.Web/Quorum.QFC.Web.Workbench/UIControllers/QUIControllerDashboardEditorBase.cs` and `Quorum.QFC.Web.Core/Controllers/QMvcBaseScreenController.cs`. TIPS widget access is gated in `Quorum.TIPS.Web → Quorum.TIPS.Web.Core/Controllers/QTIPWidgetAccessController.cs`; widget definitions render from `Quorum.TIPS.Web/Views/Shared/Widgets/*.cshtml`; widget/dynamic-UC configuration is seeded via `QARCH_CNFG_DYNUC` (in metadata repos, e.g. `IPF.Esuite.Metadata`, `SRB.TIPS.Metadata`). Client overrides live in `<CLIENT>.TIPS.Web` / `<CLIENT>.TIPS.Metadata`.

**Representative cases:** 24-00965645, 24-00967070, 23-00912075, 23-00917209.

---

## 4. Context Selector / "No Company Set"

| Issue | Root cause | Resolution recipe | Case |
|---|---|---|---|
| **Plant context selector missing** from TIPS Web dashboard (Company selector present, Plant not) | One or more modules in **Security User Setup** not set to **INTERNAL** | **Set ALL modules in Security User Setup to INTERNAL** for users who need the Web dashboard Plant Context Selector (resolution verbatim) | 25-01034152 (IACX), Config |
| **"No company set"** alert / blank dashboard for **new** users | First-run setup never done — user education | Walk the user through **Dashboard settings → select the desired Company (and related parameters)**; alert clears and dashboard populates | 26-01091486 (Customer Error) |

> These two are the most common "my dashboard is empty" causes after widget-security. Check them before suspecting a defect — neither is a code bug.
> Historical context: the multi-context selector + CSS for long module names was delivered under ADO #64307 / #236704/#236705 (§10).

---

## 5. Widget Data Display Defects

**(Data renders, but the value is wrong/blank/duplicated. 3 of 19 actionable are here.)**

| Widget / screen | Issue | Disposition | Evidence |
|---|---|---|---|
| **Cuts Dashboard** | Scheduled Qty shows **blank when the value is 0**, confusing users | Bug **#1649311 Closed** (analysis #1688531, dev #1689372). SF resolution: engineering moved it to the **core TIPS Backlog as medium priority, tentatively 2024.10 (~Apr 2025)** — **verify the client's build carries it** before re-raising | 24-00941216 (Harvest), Software Defect |
| **CAW Notices widget** | Notice times display in the **wrong time format** | Bug **#142551 Closed** — *"Code change required"*, shipped | 22-00556223 (Enable), Software Defect |
| **Operator Dashboard Widget report** | Report pulled the **wrong period** | **Change the core report parameter to Gas Day** (resolution verbatim) — config, not code | 22-00530861 (ETC), Software Defect→config fix |
| **Business Results Widget (V2UI)** | Graphs **not auto-advancing** (#1544990 **Proposed/OPEN**); Purchases/Fees **font style** off (#1544993 Closed) | V2UI polish; auto-advance still open | — |

> **Caveat — fees doubling:** the original v1.0 mining flagged a "Business Results Widget fees doubled after PPA" pattern (NorthRiver 22-00824922). That case did **not** appear in the 2026-06-13 actionable set (it closed under a non-actionable root cause / different category), and no matching ADO fix was found. **Resolution pattern unclear from mined cases** — treat any recurrence as a fresh defect with full repro data; do not assume a fix exists.

Implementation reference: `Quorum.TIPS.Web/Views/Shared/Widgets/BusinessResultsWidget.cshtml` (+ client copies, e.g. `EMP.TIPS.Web`, `Quorum.TIPS.Crude.Application.Web`).

---

## 6. Web-vs-Classic Screen Behavior

### 6a. Screen blank / different / crashes in Web while Classic works

| Issue | Root cause | Resolution | Case |
|---|---|---|---|
| **Contract Header in Web populates no fields** (specific PUR/PRO contracts); Classic shows all fields; was working earlier same day then went blank (2024.10) | Closed as **Application Configuration**; exact config not recorded in the resolution | **Resolution pattern unclear from mined cases.** Reproduce in both UIs, clear/reload cache, reverify after config — escalate with the specific contract IDs if it persists | 25-01025847 (DCP), Config |
| **Contract header screen crashes** deleting a ctr header record that has **no TIPS extension record** | Core Web defect | Fixed in a later build — confirm client version | 22-00521907 (OXY), Software Defect |
| Legacy OXY Web-parity defects (2022): **Customer Acct Maintenance** won't add contracts when BA differs from primary; **Report Launcher** report-table-map dropdown lists each option twice; **Rate Schedule** eff-date should default to each schedule's eff prod month | Old (B2018-era) Web parity gaps | **Resolutions not recorded (Resolution__c null)** — pattern unclear from mined cases; check current build behavior before escalating | 22-00521913, 22-00521912, 22-00521911 (all OXY), Software Defect |

### 6b. Query / search screens return no records

| Issue | Root cause | Resolution | Case |
|---|---|---|---|
| Query not populating in dashboard | User on a **persona without the Query tab** in the Side Menu for TIPS Web | Switch to / grant the correct persona | 26-01106043 (Customer Error) |
| Web Customer Account Maintenance returns no records | **Wrong BA selected for the time slice** | User education — pick the correct BA / time slice | 26-01080882 |

> **Rule of thumb (same as QPTM):** when "Web behaves differently than Classic," reproduce in BOTH before classifying. In TIPS the Web-only causes seen are, in order of frequency: **persona shift, client grid/metadata override, stale cache, then a genuine core Web defect.** A blank Web screen with a populated Classic screen is far more often config/persona/cache than a code bug.

---

## 7. "UI Problem" That Is Really the Environment

A large share of TIPS UI complaints (freezes, blank dashboards, disconnects, "Query Returned No Results", screens timing out) are **environment failures** — root-caused as Cloud Outage / Performance / Platform, **not UI code**. Recognize and route fast.

| Reported as | Actual root cause | Resolution | Case |
|---|---|---|---|
| Recurring DB connection errors, app freezes, users dropped during longer jobs (e.g. **Facility processing**) — environment-wide, not user-specific | **Intermittent storage latency on the VMware host running QPEC** → dropped SQL connections | Infra team **migrated the VM to a new physical host**; no QPEC/app/connection-string change | 26-01069207 (EQT), Config/Platform |
| **Emails not being received from TIPS** (RCA) | **QTIPS services hung** | **Graceful restart of QTIPS services** | 26-01066701 (EQT), Config |
| Can't start app / dashboard stale after upgrade | Stale **browser cache** | Clear browser cache (resolution verbatim: *"Clearing the browser cache fixed this issue"*) | 24-00982617 (Pivotal), Config |
| WEBCAW widgets / dashboard slow to load after a v17 install | **App initialization settings not set per the install guide** (install-guide screenshots omitted some settings) | Correct the missed app-init settings per the v17 installation guide | 22-00530860 (ETC) |

**Triage questions:** one user or all? Web and Classic both? Did it start after a release or at a specific time (correlate with QPEC/MT logs)? If environment-wide → **Cloud Ops immediately** with server names + UTC timestamps + ProcessQueueIDs; do **not** burn time on widget config.

**Cache recipe (single-user / post-release weirdness):** clear browser cache → reload server metadata cache if "Metadata cache is out of date" → restart web services if a deploy just happened.

---

## 8. OKTA / User Administration

**(45 of 145 cases — the single biggest bucket, ZERO defects.)** These are routine requests miscategorized under UI because the user "can't see the dashboard." Sampling confirms they are: *Create New OKTA User*, *New Salesforce ID*, *Reset/Unlock password*, *Account Reset*, and *Access Issue* tickets (e.g. 26-01105796, 26-01100742, 26-01098928, 26-01092646, 26-01083011).

| Request | Recipe | Example |
|---|---|---|
| Create new external user | Create OKTA account, add to **`<Client> External Users`**, **`<Client> External Users ESuite PRD A1`**, **`<Client> External Users TIPS PRD A1`** (group names analogous per client) | 26-01100742, 26-01098865, 26-01087192 |
| Okta sign-in failure / MFA loop | **Untick the dual-authenticator option** (resolution verbatim, IT-side); or reactivate inactive account + reset link | 25-01049102 (IPL) |
| Can't log in / blank eSuite in PRD but UAT works | User not added to the app / missing a group (sometimes removed accidentally) — add the missing group | (user-admin queue) |
| Password / activation problems | Reset password / resend activation; if no email, client IT checks spam/quarantine | 26-01092646, 26-01090193 |
| SSO/access differs from a working colleague | Compare OKTA group memberships **side-by-side**; add the missing SSO/app group | 26-01098928 |

**Routing:** these go to **Cloud Ops / user-admin queue**, not Engineering. L4 triage tip: always diff the broken user's OKTA groups against a known-working user at the same client first.

---

## 9. Expected Behavior / User Education FAQ

| Asked as | Answer | Case |
|---|---|---|
| "Why can't Settlement Calculation **group these fee types**?" | By design — each fee type shows individually with its own rate/basis and appears separately on the gas statement. Combining them would misstate the volume/rate per fee | 25-01008044 (HEP), Config→answer |
| "New user sees **'no company set'**" | One-time setup: pick Company (+ related params) in **Dashboard settings** | 26-01091486 |
| "**Query** not populating in my dashboard" | You're on a **persona without the Query tab** — switch persona | 26-01106043 |
| "**Copy/paste from grid** locks up Classic (UATA1/PRDA1)" | Working as designed — the business should use **Web** for grid copy/paste | 23-00926840 |
| "**Process Explorer** doesn't show recent warnings when opened" | Defaults to a window — **update defaults to the 24-hr report** (ref 21-00197822) | 22-00691481 |
| "**Company batch jobs** won't run" | The **Company must be in billing status** before company jobs run | 25-01058281 |
| "**Calendar** shows the wrong users" | Maintained via **code table 296** — update it to show the user | 22-00686353 |
| "**Menu / report menu missing** in Web for operator role" | Guided the user through the necessary Web menu/report setup (not a defect) | 22-00876091 |

---

## 10. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1739530** | Bug / **Proposed (OPEN)** | EQC — Can't add widgets — user not allowed to modify global dashboards | §3 | 24-00965645 / 24-00967070 pattern |
| **#1649311** | Bug / **Closed** | HVM 24-00941216 — Cuts Dashboard Scheduled Qty blank when 0 | §5 | 24-00941216 |
| **#1688531** | Task / **Closed** | Analysis for #1649311 (Cuts Scheduled Qty) | §5 | 24-00941216 |
| **#1689372** | Task / **Closed** | Dev for #1649311 (Cuts Scheduled Qty) | §5 | 24-00941216 |
| **#142551** | Bug / **Closed** | EMP — CAW Notices widget displays wrong time format | §5 | 22-00556223 |
| **#1544990** | Bug / **Proposed (OPEN)** | V2UI TIPS — Business Results Widget graphs not auto-advancing | §5 | — |
| **#1544993** | Bug / **Closed** | V2UI TIPS CAN — Business Results Widget font style (Purchases/Fees) | §5 | — |
| **#64307** | Requirement / Closed | FED Review: Dashboard Multiple Context Selector | §4 | — |
| **#236704 / #236705** | Req / Task | Context Selector bar CSS for longer module names | §4 | — |

> **Takeaway:** the only **open** product bugs are the **global-dashboard widget-edit gate (#1739530)** and the **Business Results auto-advance polish (#1544990)**. The high-frequency display defects (Cuts blank-when-0 #1649311, CAW time format #142551) are **already Closed/shipped** — for those, confirm the client's build version before re-raising rather than opening a duplicate.

---

## 11. Key Code Files & Repos

| Artifact | Repo / path | Role |
|---|---|---|
| `QUIControllerDashboardEditorBase.cs`, `QMvcBaseScreenController.cs` | `Quorum.QFC.Web` (`...Workbench/UIControllers`, `...Web.Core/Controllers`) | **Shared QFC layer** that enforces the "modify global dashboard" gate (root of §3 / #1739530) |
| `QTIPWidgetAccessController.cs` | `Quorum.TIPS.Web/Quorum.TIPS.Web.Core/Controllers` | TIPS widget access control |
| `Views/Shared/Widgets/*.cshtml` (incl. `BusinessResultsWidget.cshtml`) | `Quorum.TIPS.Web` (+ client copies in `EMP.TIPS.Web`, `Quorum.TIPS.Crude.Application.Web`) | Widget rendering (§5) |
| `Quorum.TIPS.Constants/Constants.cs` | `Quorum.TIPS.Web` | Widget IDs / constants |
| `QARCH_CNFG_DYNUC.json` | metadata repos: `IPF.Esuite.Metadata` (e.g. `/STANDARD 16.0/`), `SRB.TIPS.Metadata` | Dynamic-UC / widget configuration seed (§3) |
| Client overrides | `<CLIENT>.TIPS.Web` / `<CLIENT>.TIPS.Metadata` | Per-client grid/widget overrides — **always check before assuming base behavior** (Web-vs-Classic column differences) |

> Search repos for code: `IPF.TIPS.*`, `Quorum.TIPS.*`, `Quorum.TIPS.Crude.*`, `ACL.TIPS.*`, `<CLIENT>.TIPS.Web/.Metadata`.

---

## 12. Diagnostic SQL / Checks

> Column names are conservative. `QARCH_CNFG_DYNUC` and **code table 296** are confirmed from mined evidence; verify other exact shapes against the client schema before scripting.

```sql
-- A. Widget / dynamic-UC configuration seeded for the environment
--    (the table the metadata repos seed via QARCH_CNFG_DYNUC.json)
SELECT * FROM QARCH_CNFG_DYNUC;          -- confirm the widget IDs the group should see

-- B. Compare security group objects: broken group vs Power User
--    (the §3 gap — dashboard-edit / widget objects missing from GRP 5610-style "Regular User" groups)
--    Use Security User/Group Setup screens, OR dump the group-object grant tables for
--    GRP <broken> vs GRP <power user> and DIFF. Missing dashboard-edit object = the
--    "not allowed to modify global dashboard" error.

-- C. Calendar user display (22-00686353)
SELECT * FROM <code table 296>;          -- maintained via code-table maintenance, table 296

-- D. Environment health BEFORE debugging "UI" (§7 pattern — multi-user freeze/blank/timeouts):
--    1) QPEC / QTIPS service state + memory on each Middle-Tier server
--    2) Storage/VM-host latency on the QPEC host (26-01069207 root cause)
--    3) Process queue: any stuck long-running run (Facility processing, CAWDATA) — note ProcessQueueID
--    4) Web logs for QFC.Web.Core PostActionException / NullReferenceException bursts
```

**Non-SQL checks that resolve most cases (in order):**
1. Persona in use (Query tab / widget visibility).
2. Security User Setup modules = **INTERNAL** (Plant context selector — 25-01034152).
3. Browser cache; then server metadata cache; then restart web services if a deploy just happened.
4. OKTA group membership diff vs a working user (login/access).
5. Import/Export definition **path** present (file-upload failures — 26-01064032).
6. Dashboard settings → Company selected (new-user "no company" — 26-01091486).

---

## 13. Escalation Guidance

| Situation | Route |
|---|---|
| Environment-wide freeze / blank / timeouts / disconnects; QPEC/QTIPS memory, storage, or service failure | **Cloud Ops immediately** (server names + UTC timestamps + ProcessQueueIDs). RCA pattern: restart, then memory/storage/VM-host remediation (26-01069207, 26-01066701) |
| OKTA user creation, groups, password, activation, MFA | **Cloud Ops / user-admin queue** — standard recipes §8, no engineering |
| Widget security gap ("global dashboard" error, group missing widgets, can't toggle a widget) | **Cloud Ops to run the known seeding/permission script or grant the security object** (24-00965645, 23-00912075, 23-00917209). Reference **open bug #1739530**; if the client wants a product fix, attach the case to it |
| Plant context selector missing / "no company set" | **Config / user-education** — Security User Setup modules = INTERNAL (25-01034152); Dashboard settings Company (26-01091486). Not engineering |
| Reproducible wrong data in a widget (blank-when-0, wrong time format, wrong report period) | **Engineering (defect)** with Web+Classic repro, screenshots, build version. **Check §10 first** — Cuts (#1649311) and CAW (#142551) are already fixed; verify the client build before raising. Operator report period is a **config** change (param = Gas Day) |
| Web ≠ Classic where client metadata/grid override is involved (missing columns/fields) | **Client-override change** (`<CLIENT>.TIPS.Web` / `.Metadata`), not core engineering |
| File upload fails on path | **Config** — add the Import/Export definition path (26-01064032) |
| Config / "how do I" questions (fee grouping, base-screen mapping, defaults, Web run-time vs Classic) | Answer from §9; enhancements → **UserVoice** |

---

*Skill created: 2026-06-11; re-mined & validated 2026-06-13 from 145 closed TIPS UI/Dashboard/Widgets/Design-Studio SF cases.*
*Actionable: 19 (Application Configuration 11 + Software Defect 8). No "ChangeConfig" value exists in this data. Non-actionable bulk: User Administration Request 45, Training 10, Cloud Outage 9, Customer Cancelled 9, No Action Taken 7, null 7.*
*ADO confirmed (states verified live): #1739530 (Proposed/open), #1649311 + #1688531/#1689372 (Closed), #142551 (Closed), #1544990 (Proposed/open), #1544993 (Closed), #64307, #236704/#236705. Code confirmed: shared dashboard-edit gate in `Quorum.QFC.Web` (`QUIControllerDashboardEditorBase.cs`, `QMvcBaseScreenController.cs`); TIPS widget code in `Quorum.TIPS.Web` (`QTIPWidgetAccessController.cs`, `BusinessResultsWidget.cshtml`, `QARCH_CNFG_DYNUC`).*
*Data-quality caveats: (1) the UI category is heavily polluted with user-admin/outage tickets — true TIPS UI-defect rate is low. (2) Several Web-parity cases closed with null Resolution__c (OXY 22-00521911/912/913, DCP 25-01025847) — flagged "resolution pattern unclear." (3) A "Business Results fees doubled after PPA" pattern from earlier mining (22-00824922) did not surface in the actionable set and has no matching ADO fix — treat any recurrence as a fresh defect. (4) Excel/Crystal export issues that sometimes land under UI are categorized Reporting and belong in the TIPS Reporting skill.*
