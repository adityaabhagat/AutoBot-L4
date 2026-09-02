# SKILL: FLOWCAL — Meter Data Editing, Flow Data, Closing & PPA Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-09-02 | **Products:** `FLOWCAL` (this group is FLOWCAL-only; TESTit enters only as an upstream PPA trigger via meter inspections)
**Scope:** The **Volume Editor / Meter Editor** edit path (copy/paste, span edits, greyed-out menus, EEFFACE and access-violation crashes), **flow data & periodic records** (revisions, edit reasons, auto estimates, auto edits, split/off-hour records), **month-end closing** (Meter Close / Location Close, locked meters, close dates, close performance), and the **PPA lifecycle** (create → approve → apply → purge; PPA Approvals screen; Delta PPA math; Data Span pitfalls).
**Use when:** case mentions `Volume Editor`, `Meter Editor`, `EEFFACE` (edit/close screens), `copy/paste`, `edit reason`, `revision`, `periodic record`, `auto estimate`, `PPA`, `prior period`, `PPA Approvals`, `unclose`/`open data`, `close dates`, `locked meter`, `Meters Not Closed`, `batch split`, `contract hour`.
**Companion skills:** import drivers & CFX parsing → Imports skill (group #1); FcSrv service health, rollups & Transaction Queue → Services skill (group #3); gas-quality/GPA-2172/AGA calc correctness → Calculations skill (group #7); Exception Resolver & validation set points → `SKILL_FLOWCAL_Exceptions_Validations.md` (group #12).

> **Evidence base (mined 2026-09-02, Auto-Bot by Aditya Bhagat):** ~100 closed FLOWCAL cases surveyed across 5 SOQL clusters (editor errors, PPA/unclose, closing, flow-data/estimates, edit-reason/locked-meter — all `Root_Cause__c IN ('Software Defect','Application Configuration')`, all history, newest-first), with full Description/Resolution pulled on **28 richest cases**; **26 ADO work items** verified live in org `QuorumSoftware` (project `Quorum`, area `Quorum\North America\Measurement`). Every root-cause claim cites an SF case number and/or ADO id verbatim. Fixed-in versions are **INFERRED** from SF resolution text / ADO titles unless marked release-notes-confirmed.

---

## 1. Quick Triage Table

| Symptom | Likely cause | § | First action |
|---|---|---|---|
| **Copy/Paste in Volume Editor does nothing** (but every record gets a new revision) on 10.8.x | Defect in 10.8.0.7+ (works in 10.6, regression vs 10.5.0.14) | §3.1 | ADO 1836449 (DEV, Closed) / 1820072 (R1080* PORT, Closed) / 1836450 (R1090 PORT, Closed); SF 26-01101654. Upgrade to a patch containing the fix |
| Copy/Paste **crashes FLOWCAL** or adds a revision to every record in the month | Copy/paste defect family (ET data cases) | §3.1 | ADO 1780816 (26-01068138); crash variant works in 10.8.0.4 — version-match first |
| Copy/Paste shows **wrong NSV / SW Volume before save** (liquids) | Display-only defect: NSV/SW not recalculated until save | §3.1 | ADO 1777867 (26-01067712). Save, then verify values |
| Ctrl+C on liquids Periodic grid **copies whole row into Excel** | Legacy Citrix workaround in grid selection | §3.1 | ADO 1715416 (historic refs #1125664, #1124354) — cosmetic |
| **"External exception EEFFACE"** on Close Schedule > **Meters Not Closed** > Refresh (All Meters) | Defect, fixed in DEV + R1080 + R1090 ports (all Closed) | §3.2 | ADO 1853455 (DEV) / 1852237 (R1080*) / 1853457 (R1090) |
| EEFFACE on Validation **Set Points** run | See Exceptions skill §4 | — | Fixed 10.5.0.22 (INFERRED); SF 26-01066345, 25-01049379 |
| Volume Editor **Set-Up functions / Close Dates option greyed out** | Two causes: (a) defect in 10.5.0.2–10.5.0.8 fixed **10.5.0.20** (ported 10.6/10.7); (b) 10.6.0.6 defect when meter **lacks a quality source assignment**, fixed **10.6.0.7** | §3.3 | (a) 24-00968415, 24-00990297, 23-00931010, 24-00964956; (b) 25-01044340. Workaround: Setup > Meters > Close Dates |
| **Access Violation** right-clicking in Flow Data Periodic grid after drag-selecting past the last record | UI defect, workaround only | §3.4 | 25-01054813 — don't drag beyond last record; OK to dismiss |
| "**Destination buffer too small! Will truncate. dest size = 21**" opening a meter; app shuts down | Oversized `USER_FIELD_S*` values on `fc_meter_characteristic` | §3.5 | Clear user fields via SQL (recipe in §8.1); 26-01105704 |
| **"Batch 101" error** opening a meter in Volume Editor | Contract hour changed (e.g. 9→7) **without a batch split** → overlapping contract-month time slice in `fc_batch_total`/`fc_batch_report` | §3.6 | Restore contract hour + delete/fix batch rows (recipe §8.2), purge + reload periodic; 26-01084476 |
| Activated meter still shows **Disconnected/inactive in Meter Editor** | Cosmetic interface bug in 10.5.x, resolved 10.6+ (INFERRED) | §3.7 | 26-01093930, 25-01060837 — meter is actually active (check VE characteristics) |
| Volume Editor won't open: "**not a valid date and time**" | Windows regional date format on the client machine | §3.7 | Set format English (United States), reboot; 25-01014476 |
| **Excess revisions / duplicate edit reasons** ballooning on meters; imports slow | Engine defect writing repeated GPA-2172/characteristic edit reasons — fixed **10.6.0.18 / 10.8.0.8 / 10.9.0.0+** (INFERRED); until upgraded, monthly cleanup script | §4.1 | 25-01012338 (fix versions); 26-01122309, 26-01110804, 25-01032531 et al. (monthly QCloud cleanup runs) |
| **FCSRV making unsolicited daily meter data edits** (~every 24h, even inactive meters) | Defect introduced 10.5.0.17, fixed **10.5.0.20** (released 2025-06-25) (INFERRED) | §4.1 | 25-01027967 |
| Manual edits **overwritten by next CFX import** (off-hour / split periodic records) | Import settings + off-hour records create revisions over edits; "obscured original data" guard needs a code change | §4.2 | 26-01123268 — review Create Revisions & "Reject if start time not start of hour"; limit re-sent days in CFX |
| **No original (rev 0) flow data created** under estimates on import | `Create Revisions = Yes` in Meter Editor Imports tab interacts with estimates | §4.3 | 24-00948914 (dev advice: turn Create Revisions off on CFX-imported meters); ADO 1683994 / SF 24-00976894; 0-volume-over-0-estimate variant ADO 1767510 |
| **Auto Estimate removes pulses** on current data (rev over original) | Defect with Auto Estimate setting, fixed **10.6.0.7** (INFERRED) | §4.4 | 25-01024811 |
| Auto-estimate produces values with **wrong units initially**, self-corrects next day | Open defect (Investigation) | §4.4 | ADO 1660917 |
| **Math auto-edit not applied** when `Create Revisions = Yes`; deleting a rule row in Auto Edits editor throws External Exception | Defect vs 10.6-and-below behavior | §4.4 | ADO 1844518 (DEV, Acceptance) / 1838021 (R1090* PORT); SF 26-01088336 |
| **Meter locked** — can't close / can't import CFX / "abnormal program termination" | Stale service lock; crash variant fixed **10.6.0.14 & 10.8** (INFERRED); 10.6.0.15 adds an ignorable inter-service lock warning | §5.1 | Restart FLOWCAL services to clear the lock: 26-01065880, 25-01016994; warning-only: 26-01112718 |
| **Closing tickets extremely slow** after upgrade to 10.5.0.9 | Perf defect, fixed **10.5.0.13** (INFERRED) | §5.2 | 24-00967376 |
| "Open Data" **disabled for a closed month with PPAs** | Expected behavior — months with PPAs can't re-open until PPAs purged | §7 | 26-01104039 |
| **Volume Editor vs Rollup Viewer monthly volumes mismatch** after Time Leads ↔ Time Trails change | Rollup report IDs not updated on Data Span change | §5.3 | Recipe: purge PPAs → open month → restart FC → Toolbox **Recalc Rollup IDs** → close month → span edit to re-trigger source apply; 24-00989831 |
| Data Span change lets user **edit a closed month without a PPA** (record migrated across month boundary) | Defect, fixed **10.6.0.11** (Oct 2025) | §5.3 | 25-01025270 / **ADO-1708088**; also span-edit-characteristics-no-PPA 25-01003285 |
| **Purged PPA still shows in PPA Approvals** | Defect, fixed **10.6.0.14**, ported **10.8.0.4** (INFERRED) | §6.1 | 26-01063618 (re-file of 24-00977476) |
| PPA Approvals **volume/energy ≠ Volume Editor / Gas Volume Statement** | Delta PPA editor defect(s): prior PPA double-counted in display; preview of closed data misleading | §6.2 | ADO 1647551 (24-00943670), 1693974 (DEV) / 1684185 (R1060* PORT), 1704102; grid source = `FC_METER_EDIT` (query by `meter_number_index`) |
| Approval allowed **over the user's MMBTU limit** (MCF limit honored) | Defect in 10.6, not reproducible 10.8/10.9 (fixed indirectly, INFERRED) | §6.3 | 26-01080919 |
| TESTit meter inspections generate **duplicate PPAs** in FLOWCAL | Defect, fixed **10.6.0.11** (INFERRED) | §6.4 | 24-00974340 (TESTit 3.16 + FC 10.2.0.22) |
| **PPA Std Volume goes to 0 / wrong on second PPA**; std energy ignores gas condition | Calc defects on stacked PPAs | §6.5 | ADO 1702381 (24-00993074); std-energy-gas-condition fixed **10.6.0.5** (24-00985260); PPA batch split fixed **10.5.0.14** (24-00956874); PPA edited energy not used ADO 1866818 (26-01120789) |
| **PPA for missing data doesn't process fully** / can't process PPA on some meters | Defect fixed **10.7.0** (25-01011754); another variant resolved in **10.8+** (26-01079315 — client created PPAs outside the system until upgrade) | §6.6 | Version check first |
| **No PPA created** when closed-month volume recalcs via analysis update | Legacy defect (`fc_ppa_accounting_info` gets EOT effective date + garbage edit reason) | §6.6 | ADO 1811567 (Migrated-from-QS); Auto PPA no rev 0: ADO 1811561; daily PPA saved with 59-minute span: ADO 1811559 |
| **ORA-00936 approving a PPA** | Not a defect — user's group missing from the FLOWCAL system (permissions) | §6.7 | 26-01068838 |
| Deleted/broken **ticket PPA** needs undoing | Restore ticket data to REV 0 via dev-provided SQL (QCloud runs it) | §6.7 | 26-01099579 |

---

## 2. Decision Tree

```
Case mentions editing/closing/PPA?
│
├─ Error popup opening/using an editor screen?
│   ├─ "EEFFACE" ............................ §3.2 (close-schedule refresh; set points → Exceptions skill)
│   ├─ "Destination buffer too small" ....... §3.5 (user_field_s* overflow → SQL clean)
│   ├─ "Batch 101" .......................... §3.6 (contract-hour change w/o batch split → SQL fix)
│   ├─ "Access Violation" (right-click grid)  §3.4 (drag-select past last record; benign)
│   ├─ "not a valid date and time" .......... §3.7 (Windows regional settings)
│   └─ "locked by another user" ............. §5.1 (restart services; version check 10.6.0.14+)
│
├─ Edit made but data wrong / lost / duplicated?
│   ├─ Copy/paste no-op, crash, extra revisions §3.1 (10.8 regression family — VERSION FIRST)
│   ├─ Edits overwritten by next import ..... §4.2 (Create Revisions / off-hour records)
│   ├─ Revisions & edit reasons exploding ... §4.1 (fixed 10.6.0.18/10.8.0.8/10.9; else monthly cleanup)
│   ├─ Estimates wrong / pulses vanish ...... §4.4 (Auto Estimate defects)
│   └─ Auto-edit rule not applied ........... §4.4 (Create Revisions=Yes defect, ADO 1844518)
│
├─ Closing blocked or wrong?
│   ├─ Close Dates / Set-Up greyed out ...... §3.3 (10.5.0.20 fix, or missing quality source in 10.6.0.6)
│   ├─ "Unable to close data" exceptions .... §3.3 / §5.2
│   ├─ Meter locked, close/import blocked ... §5.1
│   ├─ Close performance .................... §5.2
│   └─ Rollup vs VE mismatch after DataSpan . §5.3 (Recalc Rollup IDs recipe)
│
└─ PPA lifecycle?
    ├─ Wrong numbers on Approvals screen .... §6.2 (display defects — verify in FC_METER_EDIT before trusting UI)
    ├─ Purged PPA still visible ............. §6.1 (10.6.0.14/10.8.0.4)
    ├─ Duplicate PPAs (TESTit source) ....... §6.4 (10.6.0.11)
    ├─ PPA math wrong (std vol/energy) ...... §6.5
    ├─ PPA missing / won't process .......... §6.6
    ├─ Closed-month edit WITHOUT a PPA ...... §5.3 (Data Span bypass — data-integrity severity)
    └─ Can't approve (ORA/permissions) ...... §6.7
```

**Gate guidance:** version-fix table hits (G3) resolve most defect rows above — check client version against the fixed-in versions FIRST. Data-correction SQL (§8) is G4. Config causes (import settings, quality source assignment, PPA options, permissions) are G2. `Open Data` disabled with PPAs and the 10.6.0.15 lock warning are G1 (expected behavior).

---

## 3. Cluster: Volume/Meter Editor errors & UI failures

### 3.1 Copy/Paste defect family (the #1 recent editor complaint)
**Signature:** right-click Copy/Paste in Volume Editor Flow Data Periodic either (a) silently does nothing while stamping a new revision on every record, (b) crashes FLOWCAL with a popup, or (c) shows stale NSV/SW volumes until save.
**Root cause & state (all anchors verbatim):**
- **ADO 1836449** "Copy/Paste function in Volume Editor not working (DEV)" — Closed; **ADO 1820072** (R1080* PORT, Closed, Escalated); **ADO 1836450** (R1090 PORT, Closed). From SF **26-01101654** (MarkWest): worked in 10.5.0.14, broken in **10.8.0.7 and all 10.8**, works in 10.6. Repro: "Copy from selected date time" → CTRL+click target rows → "Paste to selected date/time" → paste does not occur but every record gets a new revision.
- **ADO 1780816** "Copy and Paste Bugs" (SF **26-01068138**, Energy Transfer Non-Regulated): issue 1 — paste triggers popup + crash (works in 10.8.0.4); issue 2 — paste gives every record in the month an extra revision (base pressure 14.73 setup in repro).
- **ADO 1777867** "Copy Paste Incorrect Before Save" (SF **26-01067712**, Salt Creek): liquids meter — NSV/Adj Total NSV/SW Volume columns show wrong values until Data > Save recalculates.
- **ADO 1715416** "Issue copying and pasting selected Liquids Periodic Data into Excel": Ctrl+C copies the entire row; historic root — full-row highlighting was disabled for a Citrix issue (#1125664) when copy/paste was enhanced (#1124354).
**Fix recipe:** identify exact client build; map to the variant above. The (DEV/R1080/R1090) trio is Closed — fixed-in build **INFERRED** as a 10.8.x/10.9.x patch after 2026-08; confirm via release notes before promising. Interim: single-row paste, or span edit instead of paste; warn that failed pastes still create revisions (feeds §4.1 cleanup).
- **25-01004049** (copy/paste between two meters, App Config) — cross-meter copy/paste questions are usually usage guidance, not defects.

### 3.2 EEFFACE in close/edit screens
**Signature:** "External exception EEFFACE" — a Borland/C++Builder hardware-exception code surfacing across FLOWCAL screens.
- Close Schedule > **Meters Not Closed** UI, Refresh with All Meters after Show Open: **ADO 1853455 (DEV) / 1852237 (R1080* PORT) / 1853457 (R1090 PORT)** — all Closed (fixed, build INFERRED 10.8/10.9 patch line, 2026-08).
- Reports screen EEFFACE: SF **26-01105022**; **ADO 1725906** — session-poisoning behavior: once EEFFACE fires in the Location editor, anything using locations/reports fails in the same FLOWCAL session (restart the client app). **ADO 1718593** ties Location-editor EEFFACE to row counts/latency in the location tables.
- Validation Set Points EEFFACE (26-01066345, 25-01049379, fixed 10.5.0.22 INFERRED) → covered in the Exceptions & Validations skill §4.
**Triage rule:** capture the exact screen; EEFFACE is not one bug. Restart the client session before deeper diagnosis (poisoned-session effect, ADO 1725906).

### 3.3 Set-Up functions / Close Dates greyed out in Volume Editor
**Signature:** Volume Editor Set-Up menu (incl. Close Dates) disabled; monthly manual close of "Unable to close data" stragglers blocked.
**Two distinct root causes:**
1. 10.5.0.2–10.5.0.8 defect — fixed **10.5.0.20**, ported 10.6.0/10.7.0 (INFERRED): **24-00968415**, **24-00990297**, **23-00931010**, **24-00964956** ("fixed in FLOWCAL 10.5.0.20").
2. 10.6.0.6 defect — greyed out **because the meter lacks a quality source assignment**; fixed **10.6.0.7** (INFERRED): **25-01044340** (Ascent).
**Workaround (both):** close from **Setup > Meters > Close Dates** instead of inside the Volume Editor (25-01044340 resolution).

### 3.4 Access Violation on right-click in Periodic grid
**Signature:** drag-select rows past the bottom edge of the last record into empty space, then right-click (quick sum / accept estimates / purge from VE) → Access Violation; workflow continues after OK.
**Root cause:** UI defect, no fix shipped at case close. Anchor: **25-01054813**. Recipe: benign — dismiss and continue; avoid dragging beyond the last record.

### 3.5 "Destination buffer too small! Will truncate. dest size = 21"
**Signature:** opening a specific meter in Volume Editor shuts FLOWCAL down; purge attempts fail for that meter.
**Root cause:** oversized strings in `fc_meter_characteristic.USER_FIELD_S01..S30` for that meter (data, not code). Anchor: **26-01105704** (Coastal Flow, meter CNR6015) — support resolution was the clean-up SQL in §8.1. Classification: Bad Data (G4).

### 3.6 "Batch 101" error opening a meter
**Signature:** Volume Editor throws Batch 101 message opening a meter; overlapping contract-month time slice suspected.
**Root cause:** client changed **contract hour** (9 → 7) on the meter **without doing a batch split**, corrupting `fc_batch_total` / `fc_batch_report` effective-date slices. Anchor: **26-01084476** (App Config + bad data). Recipe (§8.2): restore contract hour on `fc_meter_characteristic`, delete affected `fc_batch_total`/`fc_batch_report` rows for the months, patch `EFFECTIVE_END_DATE` on the spanning batch, then purge & reload periodic data for the affected months. Prevention: contract-hour changes require a batch split.

### 3.7 Cosmetic / environment editor issues
- Activated meter displays **Disconnected/inactive in Meter Editor** after saving Basic screen: interface bug in client's 10.5.x version, resolved 10.6+ (INFERRED); the meter IS active — verify in Volume Editor characteristics. Anchors: **26-01093930** (ExxonMobil), **25-01060837**.
- Volume Editor rejects entry with "**not a valid date and time**": Windows regional date format; set "English (United States)", reboot, relaunch. Anchor: **25-01014476**.
- Meter Editor field permissions (e.g. TESTit checkbox): security group config, not defect — **25-01008191**, **24-00994090**.

---

## 4. Cluster: Flow data, periodic records, revisions & estimates

### 4.1 Excess revisions & duplicate edit reasons (recurring monthly cleanup)
**Signature:** meters accumulate thousands of duplicate edit reasons/revisions (frequently on GPA 2172 characteristic slices); Volume Editor and the import service slow to a crawl; several QCloud clients (FC_HEPP, Howard, SEMP) have a **standing monthly cleanup case**.
**Root cause:** engine defect writing repeated edit reasons — per **25-01012338**: "Fixed in **10.6.0.18, 10.8.0.8 and 10.9.0.0** and later" (INFERRED). A related generator: **FCSRV making unsolicited daily meter data edits** ~every 24h (even on inactive zero-import meters) — introduced in **10.5.0.17**, fixed **10.5.0.20** released 2025-06-25 (INFERRED): **25-01027967**.
**Fix recipe:** (1) version-check against the fix list — upgrade is the durable fix; (2) below fixed versions, the DEV-provided cleanup script is run by QCloud on request — do NOT hand-roll it; open/refer a QCloud ticket as in the monthly series: **26-01122309** (FC_HEPP Aug 2026, "cleaned up with a script just like every month"), **26-01117476**, **26-01110804**, **26-01103119**, **26-01083130**, **26-01068554**, **25-01063108**, **25-01032531**, **25-01027356**, **25-01016238**, **25-01005833**, **25-00999825**, **24-00991228**, **24-00986730**. (3) Check what's generating the churn: repeated characteristic slicing by imports (ADO **1833050** discussion), copy/paste failures (§3.1), or FCSRV defect above.

### 4.2 Imports overwriting manual edits (split / off-hour periodic records)
**Signature:** analyst edits missing-data exceptions; next CFX import reverts the edits (Merit/Scout meters, off-hour records splitting periodics).
**Root cause/state:** per Senior Product Owner in SF **26-01123268** (Eiger; closed App Config): suppressing the override ("Imported original data obscured by existing edited data" behavior) **requires a code change**; contributing config — import options **Create Revisions** and **Reject if start time not start of hour** inconsistently set across meters; CFX files re-sending too many prior days re-trigger the overwrite; guidance was also to take factor updates out of **Auto Edit**.
**Fix recipe:** align import-driver settings across meters; shrink the CFX lookback window; keep edits after the file cutoff; if client demands hard protection of edits, raise an enhancement (code change) to the product team.

### 4.3 Missing rev 0 / original flow data under estimates
**Signature:** no original (rev 0) flow-data volumes created on import; estimates sit on top with no original underneath; downstream "C' not recalculating" complaints.
**Root cause:** interaction of **Create Revisions = Yes** (Meter Editor > Imports tab) with existing estimated data. Anchors: **24-00948914** — dev recommendation: *turn Create Revisions off at least on all meters with a CFX file for import* (spreadsheet of affected meters delivered; references earlier case 22-00864853); **ADO 1683994** / SF **24-00976894** (rev 0 not created underneath the estimate during import); **ADO 1767510** "Importing 0 volume over estimated volume of 0 results in energy not being calculated" (New).
**Fix recipe:** audit Create Revisions on CFX-imported meters; for wrong-energy records, re-import or edit to force recalculation; cite the ADO ids on the handoff if the client needs the defect fixed rather than configured around.

### 4.4 Auto Estimate & Auto Edit defects
- **Pulses removed on current data** when Auto Estimate enabled (revise-and-remove on import): defect fixed **10.6.0.7** (INFERRED) — **25-01024811** (FCA Measurement).
- **Auto-estimate initially uses wrong units**, self-corrects on later runs: **ADO 1660917** (New, Escalated/Investigation) — no fix; workaround is re-estimate/next-day correction.
- **Math auto-edit (e.g. volume*1.05) not applied on import when Create Revisions = Yes** (works with No); also deleting a rule row in Setup > Meter > Auto Edits editor throws External Exception (correct in 10.6 and below): **ADO 1844518** (DEV, Acceptance) / **ADO 1838021** (R1090* PORT, Acceptance); SF **26-01088336** (Boardwalk). Note from the thread: volume-based auto-edit rules belong on the **VCF tab**, not the Volume tab, for VCF-driven recalc.
- Auto Estimate service setup/scheduling issues are config (G2), not defects: **26-01089191**, **25-01011146**, **23-00934306**, **24-00981270**.
- FC 10.9 API drops `auto_estimated` / `has_exception` flags from list data: **ADO 1867887** (DEV) / **1864820** (R1090* PORT, Ready for Code Review).

### 4.5 Transaction Queue not updating periodic data
**Signature:** edits/imports accepted but periodic values never refresh; TQ backlog. Anchor: **26-01064118** (closed App Config, no resolution text — service-side). Route to the **Services/Transaction Queue skill (group #3)**; from this skill's side, confirm it is not meter locks (§5.1) first.

---

## 5. Cluster: Closing, close dates & locked meters

### 5.1 Locked meters (close and import blockers)
**Signature:** "meter locked by another user" on close; meter stuck in rollup queue; CFX imports fail, sometimes with "abnormal program termination".
**Root cause:** stale/competing locks held by FLOWCAL services. The crash-on-locked-import defect is fixed in **10.6.0.14 and 10.8** (INFERRED): **25-01016994** (QCloud PRD, 8 locked meters). Since **10.6.0.15**, import services emit an explicit warning when another service already holds the meter lock — *"a message customer can ignore unless it causes any issues"*: **26-01112718**.
**Fix recipe:** stop and restart the FLOWCAL services (Settings Manager > Services) — clears the lock: **26-01065880** ("Stop all the FLOWCAL services and restart them"), **25-01016994** (Cloud restarted FC services), **22-00526791** (locked meter holding up closing, defect era). Then re-run the close/rollup. If recurring, version-check against 10.6.0.14+.

### 5.2 Close performance & close-run failures
- **Closing tickets extremely slow** after 10.5.0.9 upgrade: fixed **10.5.0.13** (INFERRED) — **24-00967376**. Meter-close performance defects also historic: **22-00614865**.
- Monthly "Unable to close data" exceptions on a subset of meters usually trace to §3.3 (greyed close dates / missing quality source) or §5.1 locks — check those before treating close service (FcSrvCloseData/FcSrvLcnCloseData → Services skill).
- No notification on location close: config/enhancement — **25-01015203**.

### 5.3 Data Span (Time Leads / Time Trails) pitfalls — data-integrity class
**Signature A (mismatch):** monthly volumes in **Volume Editor vs Rollup Viewer disagree** after a meter changed Time Leads ↔ Time Trails: rollup report IDs were not updated. Recipe (verbatim from **24-00989831**): (1) purge the month's PPAs; (2) Setup > Meter > Close Dates — open the month; (3) close & reopen FLOWCAL; (4) Tools > Toolbox > **Recalc Rollup IDs** for the month; (5) close the month again; (6) span edit the meter for that month to re-trigger source apply.
**Signature B (close bypass):** changing Data Span moved a boundary record (e.g. June 1 10:00) into the previously-closed month, after which **all records of the closed month became editable without a PPA**: **25-01025270** — fixed **10.6.0.11** (Oct 2025), **ADO-1708088** (id cited verbatim in the SF resolution). Sibling: span-editing plate size/characteristics in a closed month from the Daily tab creates **no PPA**: **25-01003285** (Software Defect).
**Triage rule:** any "edited closed data without PPA" report is a data-integrity finding — flag affected months for re-audit, not just the fix version.

---

## 6. Cluster: PPA lifecycle (create → approve → apply → purge)

### 6.1 Purged PPA still visible on PPA Approvals
**Signature:** PPA purged (Gas Volume Statement, Volume Editor, PPA Editor all clean) but still listed on the Approvals screen; purge of an approved PPA can leave it visible in Volume Editor too.
**Root cause:** defect; fixed **10.6.0.14** patch, ported **10.8.0.4** (INFERRED). Anchors: **26-01063618** (Williams; re-file of **24-00977476**).

### 6.2 PPA Approvals screen shows wrong volume/energy (display defects)
**Signature:** Approvals grid / preview disagrees with Volume Editor and Gas Volume Statement.
**Root causes (multiple, all ADO-verbatim):**
- **ADO 1647551** "24-00943670 - Issue with Delta PPA editor" (New) — from ONEOK; preview data stops at Oct 31 08:00 instead of running to month end (contract-hour boundary). Support workaround from the SF resolution: *query `fc_meter_edit` by `meter_number_index`* to see the true grid data.
- **ADO 1693974** "(DEV)" / **ADO 1684185** "(R1060* PORT)" — "Displayed PPA approval volume is incorrect when prior PPA occurred": approving a second PPA displays the prior PPA's volume change a second time; closed volume/energy columns also drift in VE.
- **ADO 1704102** "Preview of Closed Data in the Volume Editor on Manual Import and PPA Approval" (New): preview shows closed = adjusted after manual CFX import to a closed meter; Preview button should only be enabled for Pending Approval PPAs; `FC_METER_EDIT` row exists with **no `FC_METER_EDIT_DETAIL`** rows in one variant.
- **ADO 1617360** "discrepency value shown after PPA" (10.5.0.1): PPA Edit Vol appears only after save, not in the accept window — display-only.
**Triage rule:** these are DISPLAY defects; before escalating "PPA numbers wrong", verify persisted values in `FC_METER_EDIT`/`FC_METER_EDIT_DETAIL` (§8.3) — if the DB is right, it's this family.

### 6.3 Approval limits not enforced (MMBTU)
**Signature:** user approves a PPA under their MCF limit but **over their MMBTU limit**; a second meter correctly blocks.
**State:** reproduced in 10.6, NOT reproducible in 10.8/10.9 — "resolved indirectly by another fix in these patches" (INFERRED): **26-01080919**. Limit configuration itself (who can approve, amounts) is security/config: **25-01059859**, **24-00991152**.

### 6.4 Duplicate PPAs from TESTit meter inspections
**Signature:** importing TESTit calibrations/inspections into FLOWCAL generates multiple identical PPAs.
**Root cause:** defect (TESTit 3.16 + FC 10.2.0.22); fixed **FLOWCAL 10.6.0.11** (INFERRED): **24-00974340** (Williams). PPA-flag sibling on same stack fixed **10.2.0.30** (INFERRED): **25-01004163**.

### 6.5 PPA calculation defects (std volume / energy)
- **PPA Std Volume goes to 0 on a second PPA** (analysis-update revision path; Heating Value Condition Dry, Apply Immediate + Allow Auto PPAs): **ADO 1702381** "Standard volume incorrect on PPA" (New; SF 24-00993074, EnLink).
- **Standard energy ignores gas condition** when performing a PPA: fixed **10.6.0.5** (INFERRED): **24-00985260**.
- **PPA batch split bug**: fixed **10.5.0.14** (INFERRED): **24-00956874**.
- **FLOWCAL not using PPA edited energy** (PPAs that should zero energy don't; FC 10.5.0.21): **ADO 1866818** (New, Escalated; SF 26-01120789, XCEL).
- PPA error doubled in new version: **24-00974134** (defect, no resolution text — treat via 1693974/1684185 double-count family).
- Apply-PPA errors on 10.3: fix delivered to 10.5/10.6/10.8 only — 10.3 unsupported; upgrade required: **25-00996477** (Tallgrass).

### 6.6 PPA not created / won't process
- **PPA for missing original data does not process fully**: fixed **10.7.0** (INFERRED): **25-01011754**.
- **Unable to process PPA** on specific meters (Howard, Dec 2025): resolved in **10.8+** (INFERRED); interim: client creates PPAs outside the system: **26-01079315**.
- **No PPA on closed-month recalc via analysis update**; `fc_ppa_accounting_info` written with EOT `EFFECTIVE_DATE` and garbage `EDIT_REASON`: **ADO 1811567** (Migrated-from-QS, reported v10.0.3).
- **Gas Auto PPA doesn't create Rev 0** (Approval Required vs Apply Immediate import results differ): **ADO 1811561**.
- **Daily PPA saved spanning 59 minutes** instead of a contract day (contract hour 9; Enable Daily PPA Accounting): **ADO 1811559**.

### 6.7 PPA operational/config items
- **ORA-00936 on approve** = user group not in the right FLOWCAL system — permissions, not DB corruption: **26-01068838**.
- **Undo a ticket PPA / restore ticket data**: dev-provided SQL restores the ticket to **REV 0**; QCloud executes: **26-01099579**. Generating a PPA at all (setup): **26-01108057** (App Config/Integration).
- Meter month with PPAs cannot be re-opened; purge PPAs first (see §7): **26-01104039**.

---

## 7. Expected-Behavior FAQ (close as G1 with explanation)

| Question | Answer | Anchor |
|---|---|---|
| Why is "Open Data" disabled for a closed month? | A meter month **with PPAs cannot be re-opened**. Purge the PPAs first, then open. | 26-01104039 |
| We see "meter was locked already for processing" warnings since upgrading | Added intentionally in **10.6.0.15** so import services communicate lock contention; ignorable unless something actually fails. | 26-01112718 |
| Meter shows Disconnected in Meter Editor after activation | Display-only bug in 10.5.x; the meter is active (verify in Volume Editor > Characteristics). Fixed 10.6+ (INFERRED). | 26-01093930 |
| GQ edit in Periodic zeroes/blanks Mass in one environment but not another | Check **Energy Calc method** parity between environments — that was the whole story. | 25-01029313 |
| Where do PPA Approvals numbers come from? | `FC_METER_EDIT` (+ `FC_METER_EDIT_DETAIL`), keyed by `meter_number_index` — query it when the screen looks wrong. | 24-00943670 / ADO 1647551, 1704102 |
| Monthly edit-reason cleanup — is that normal? | It is a **known recurring script** QCloud runs for affected clients until they reach 10.6.0.18/10.8.0.8/10.9. | 26-01122309, 25-01012338 |
| Base density on original flow data in VE — how calculated? | Training/how-to, not defect — route to product documentation. | 24-00987230 |
| Who can change the TESTit box / meter fields in Meter Editor? | Security-group field permissions. | 25-01008191, 24-00994090 |

---

## 8. Diagnostic & correction SQL (Oracle FLOWCAL schema; verified from case resolutions — re-validate on the client's version before running; QCloud executes on hosted PRD)

### 8.1 "Destination buffer too small (dest size = 21)" — clear oversized user fields (from 26-01105704, VERBATIM support fix)
```sql
UPDATE fc_meter_characteristic
   SET user_field_s01='', user_field_s02='', user_field_s03='', user_field_s04='', user_field_s05='',
       user_field_s06='', user_field_s07='', user_field_s08='', user_field_s09='', user_field_s10='',
       user_field_s11='', user_field_s12='', user_field_s13='', user_field_s14='', user_field_s15='',
       user_field_s16='', user_field_s17='', user_field_s18='', user_field_s19='', user_field_s20='',
       user_field_s21='', user_field_s22='', user_field_s23='', user_field_s24='', user_field_s25='',
       user_field_s26='', user_field_s27='', user_field_s28='', user_field_s29='', user_field_s30=''
 WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number = '<METER>');
COMMIT;
```
(Blanks ALL 30 user fields — export them first if the client uses them.)

### 8.2 "Batch 101" after a contract-hour change without batch split (from 26-01084476, adapted — replace meter/months/batch)
```sql
ALTER SESSION SET nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
-- 1. restore the correct contract hour
UPDATE fc_meter_characteristic SET contract_hour = '<CORRECT_HOUR>'
 WHERE contract_hour = '<WRONG_HOUR>' AND meter_number_index = '<MTR_IDX>';
-- 2. remove batch rows for the affected months
DELETE FROM fc_batch_total  WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number='<METER>') AND measurement_month >= <YYYYMM>;
DELETE FROM fc_batch_report WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number='<METER>') AND measurement_month >= <YYYYMM>;
-- 3. re-terminate the spanning batch at the correct contract-hour boundary
UPDATE fc_batch_total  SET effective_end_date = '<MM/01/YYYY HH:00:00>' WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number='<METER>') AND batch_index='<BATCH_IDX>';
UPDATE fc_batch_report SET effective_end_date = '<MM/01/YYYY HH:00:00>' WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number='<METER>') AND batch_index='<BATCH_IDX>';
COMMIT;
```
Then have the client **purge and reload periodic data** for the affected months (26-01084476 resolution).

### 8.3 Inspect PPA truth vs. Approvals screen (from ADO 1647551 workaround + 1704102)
```sql
-- PPA edits as persisted (what the Approvals grid SHOULD show)
SELECT * FROM fc_meter_edit
 WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number='<METER>');
-- detail rows; a header with NO detail rows = the 1704102 signature
SELECT * FROM fc_meter_edit_detail WHERE meter_edit_index IN (
  SELECT meter_edit_index FROM fc_meter_edit
   WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number='<METER>'));
```
(`fc_meter_edit_detail` join column INFERRED from table naming — confirm on live schema via metadata server before citing.)

### 8.4 Revision ladder on periodic values (from ADO 1811561 repro SQL, VERBATIM pattern)
```sql
ALTER SESSION SET nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
SELECT mtr.meter_number, effective_date, sequence_number
  FROM fc_meter_periodic_values mpv, fc_meter mtr
 WHERE mtr.meter_number_index = mpv.meter_number_index
   AND mtr.meter_number = '<METER>'
   AND effective_date BETWEEN '<START>' AND '<END>'
 ORDER BY mtr.meter_number, effective_date, sequence_number DESC;
```
Use to check: missing rev 0 under estimates (§4.3), excess revisions (§4.1), post-paste phantom revisions (§3.1). `sequence_number` is the revision counter.

### 8.5 PPA accounting garbage signature (from ADO 1811567)
```sql
SELECT * FROM fc_ppa_accounting_info
 WHERE effective_date > SYSDATE + 3650 OR edit_reason IS NULL;  -- EOT dates / unknown chars in EDIT_REASON
```
(Heuristic; the bug writes end-of-time EFFECTIVE_DATE and corrupted EDIT_REASON.)

---

## 9. Known ADO items (org QuorumSoftware, project Quorum, area Quorum\North America\Measurement unless noted)

| ADO | Title (verbatim) | State (2026-09-02) | Linked SF |
|---|---|---|---|
| 1836449 | Copy/Paste function in Volume Editor not working (DEV) | Closed | 26-01101654 |
| 1820072 | Copy/Paste function in Volume Editor not working (R1080* PORT) | Closed | 26-01101654 |
| 1836450 | Copy/Paste function in Volume Editor not working (R1090 PORT) | Closed | 26-01101654 |
| 1780816 | Copy and Paste Bugs | New | 26-01068138 |
| 1777867 | Copy Paste Incorrect Before Save | New | 26-01067712 |
| 1715416 | Issue copying and pasting selected Liquids Periodic Data into Excel | New | — |
| 1853455 / 1852237 / 1853457 | External exception clicking on Refresh in Meters Not Closed UI if All Meters selected (DEV / R1080* / R1090 PORT) | Closed (all) | — |
| 1725906 | Unable to run Reports due to 'EEFFACE' error | New | — |
| 1718593 | Cannot create a Location | New | — |
| 1708088 | (Data Span change allows closed-month edit w/o PPA — id cited in SF resolution) | fix shipped 10.6.0.11 (INFERRED) | 25-01025270 |
| 1647551 | 24-00943670 - Issue with Delta PPA editor | New | 24-00943670 |
| 1693974 | Displayed PPA approval volume is incorrect when prior PPA occurred (DEV) | Backlog | — |
| 1684185 | Displayed PPA approval volume is incorrect when prior PPA occurred (R1060* PORT) | New | — |
| 1704102 | Preview of Closed Data in the Volume Editor on Manual Import and PPA Approval | New | — |
| 1617360 | discrepency value shown after PPA | New | — |
| 1702381 | Standard volume incorrect on PPA | New | 24-00993074 |
| 1866818 | FLOWCAL not using PPA edited energy | New | 26-01120789 |
| 1811567 | PPA not created on closed month volume when volume is recalculated via analysis update on closed data | New (Migrated-from-QS) | — |
| 1811561 | Gas Auto PPA doesn't Create Rev 0 | New (Migrated-from-QS) | — |
| 1811559 | Daily PPAs Application to date incorrect | New (Migrated-from-QS) | — |
| 1660917 | Auto-estimate initially has the wrong units | New (Escalated) | — |
| 1844518 | Math Auto Edit Not Working with create revisions; Auto editor issue (DEV) | Acceptance | 26-01088336 |
| 1838021 | Math Auto Edit Not Working with create revisions; Auto editor issue (R1090* PORT) | Acceptance | 26-01088336 |
| 1767510 | Importing 0 volume over estimated volume of 0 results in energy not being calculated | New | ← refs ADO 1683994 / SF 24-00976894 |
| 1867887 / 1864820 | FC 10.9 API Exception and Auto-Estimate flags should be included in data (DEV / R1090* PORT) | New / Ready for Code Review | — |

Port convention observed: `(DEV)` = mainline, `(R1080* PORT)` / `(R1090 PORT)` = 10.80/10.90 release branches; SF case number and "Case Owner - {name}" appear in bug descriptions (join key for future mining).

---

## 10. Escalation guidance

- **Data-integrity first:** anything matching §5.3 (closed-month edits without PPA) or §6.5 (PPA math) gets Severity ≥ High and a note to re-audit affected closed months — these change custody-transfer numbers.
- **Version-match before escalating:** most rows here died in a known patch (10.5.0.13/14/20/22, 10.6.0.5/7/11/14/18, 10.7.0, 10.8.0.4/8, 10.9.0.0). All fixed-in labels are INFERRED from SF resolutions — re-confirm against release notes before telling a client "fixed in X".
- **Locked meters / cleanup scripts / ticket-REV-0 restores** on hosted clients are executed by the **QCloud team** — support raises the internal ticket; never run correction SQL directly on PRD.
- **Repro assets convention:** dev repro data lives at `\\qddfcfs01.qdev.net\DATA\CustomerData\<Client>\<CaseNumber>` as FcDataBoss files — reference this path when filing new bugs in this area.
- **Filing a new editor/PPA bug:** include exact build (Help > About), FcDataBoss export of the meter, repro clicks Volume-Editor-style (the ADO items above are the template), and the `fc_meter_edit`/`fc_meter_periodic_values` evidence from §8.
- Escalation area path: `Quorum\North America\Measurement` (support triage) → `\Maintenance`; engineering copies at `QuorumSoftware\Engineering\Measurement\Maintenance`.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
