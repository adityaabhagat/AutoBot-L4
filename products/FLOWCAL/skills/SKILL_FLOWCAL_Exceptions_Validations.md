# SKILL: FLOWCAL — Exceptions, Validations & Messages Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-09-02 | **Products:** `FLOWCAL` (primary; Exceptions/Messages is a FLOWCAL-only category — TESTit had 18 cases, PROVEit 0)
**Scope:** The **validation engine** (meter/analysis/quality validations, Validation Set Points, the recurring **EEFFACE** set-points corruption), the **Exception Resolver** (new .NET ER + Legacy ER: blank screens, freezes, access violations, settings resets, list visibility, tiles), **exception generation & auto-resolution defects** (missing-data / missing-analysis / no-flow exceptions not created or not cleared), **FLOWCAL Message NNN notifications** (Message 123/128/203/321 — routing, distribution lists, and the import failures behind them), and **Message Queue (MSMQ) / TI subscription** plumbing that the Message Queue viewer exposes.
**Use when:** case mentions `EEFFACE`, `Exception Resolver`, "exceptions not showing/created/resolved", `validation`, `set points`, `Message 123|128|203|321`, `Message Viewer`, `Message Queue`, "flagged", "limits", `Error -32000`, exception code `2158` (Drive Gain).
**Companion skills:** import failures themselves (CFX/ticket/GQ) → Imports skill (group #1); TI (TESTit↔FLOWCAL) integration service health → Integrations/WebSync skill (group #11); Windows services & Transaction Queue → Services skill (group #3); gas-quality/calc correctness → Calculations skill (group #7).

> **Evidence base (mined 2026-09-02):** ~95 closed FLOWCAL cases sampled across 4 SOQL clusters (`Case_Category__c='Exceptions / Messages'` actionable, Exception Resolver subjects all-history, validation subjects actionable, Message NNN / Message Queue subjects all-history) + 16 ADO work items verified live. Coverage plan sizes this group at ~1,425 cases, ~130 actionable. Every root-cause claim cites an SF case and/or ADO id. Fixed-in versions are **INFERRED** from SF resolution text unless marked otherwise.

---

## 1. Quick Triage Table

| Symptom | Likely cause | § | First action |
|---|---|---|---|
| "External exception **EEFFACE**" opening Setup > Meter > **Set Points** (may freeze app) | Corrupt/drifted `FC_METER_VALIDATION_HIST` table (unused/removed columns) | §4 | Bulk Change Editor: clear validation min/max on the failing meter → screen opens. Durable fix: rebuild the hist table (SQL w/ services stopped) |
| Same EEFFACE, client on ≤10.5.0.21 | Known defect, resolved **10.5.0.22** (INFERRED) | §4 | Upgrade path + workaround above (26-01066345) |
| Exception Resolver opens but shows **no exceptions at all** | ER display defect (unreproducible for dev) or edit-reason filter bug | §5 | Switch to **Legacy ER** (`<add key="legacy:ExceptionResolver" value="Y"/>`); ADO 1739171 |
| ER **settings/layout keep resetting** to default | Corrupt **Citrix user profile** | §5 | Cloud resets the Citrix profile (26-01104193, 26-01085068) |
| ER: **Access Violation** after editing data in Volume Editor | Known bug editing from ER; Citrix Workspace version aggravates | §5 | Update Citrix Workspace + use Legacy ER (25-01062048); ADO 1788769 (OPEN) |
| ER: "Error Loading Meter Periodic Values **Error: -32000**", app not responding | Defect in 10.5.x | §5 | Fixed 10.5.0.20 / 10.6.0.7 (INFERRED) (25-01022729) |
| ER: user's **list missing from dropdown** | List not granted to user's security group | §5 | List Editor → Group and User Access tab → add group (25-01048705) |
| ER: list selection returns nothing but meters have exceptions (Oracle) | Oracle shared-pool heap params | §5 | DBA sets `_kgl_large_heap_warning_threshold` / `_kgl_large_heap_assert_threshold` (25-01052324) |
| ER **Critical Error: Unhandled exception from AppDomain.CurrentDomain.UnhandledException** | Garbage data in meter **User-Defined Fields** | §9 | NULL the UDF gibberish (26-01104714, 26-01113739) |
| **Missing-data / missing-analysis exception not auto-resolved** after the gap is filled | Long-running engine defect family | §6 | ADO 1566894 (still in Code Review), 1690399/1675377 (Closed, 10.5 port) — check client version first |
| **No Flow exceptions missing** in 10.6.0.6 | Defect, fixed **10.6.0.7** (INFERRED) | §6 | 25-01029310 |
| **Run Validations on quality data creates no exceptions** (10.5.0.17) | Defect, fixed **10.5.0.19** (INFERRED) | §6 | 25-01012873 |
| Exceptions **not recreated** after purge/reimport (10.5.0.9) | Defect, fixed 10.5.0.20/10.6.0.7/10.7.0.1/10.8.0 (INFERRED) | §6 | 24-00965165 |
| Drive Gain exception (**2158**) shows wrong **Field Value** in ER | Known bug, fix targeted **10.9** (INFERRED) | §6 | 26-01068318, 25-01043587 |
| Email "**FLOWCAL Message 321: Ticket import failure**" going to the wrong people | Message Description notify list | §7 | Settings Manager → Message Description → filter to 321 → edit Contact Name/D-List (26-01087471) |
| "**FLOWCAL Message 123: Meter import failed**" repeating | Bad record wedged in the transaction queue | §7 | Delete `UNAVAILABLE = 0` rows from `FC_TRANSACTION_QUEUE` + `FC_TRANSACTION_SNAPSHOT` (23-00882995) |
| "**FLOWCAL Message 128: Meter data purge failed**" (FcDataBoss) | Services holding locks on the meters | §7 | Stop services, purge, restart (22-00660880) |
| **Message Queue viewer shows outgoing messages to the OLD server** after a migration | Stale TI **subscription table** | §8 | Truncate subscription table + restart TI services (26-01088473) |
| MSMQ queues piling up / service stuck "Starting" | Storage limit set, or MSMQ checkpoint replay after long uptime | §8 | Uncheck Message Queue Storage Limit (26-01064484); wait out checkpoint start (22-00633108); cleanup recipe (22-00604400) |
| Meter shows correct Z-Method in GQ Source Editor but **source apply conversion fails** in ER | Z-Method NULL at DB level (legacy data) | §9 | SQL update, or toggle Z-Method in editor save+revert (26-01122401) |

---

## 2. How the pieces fit

```
   IMPORTS (CFX/GQ/tickets/SCADA)          EDITS (Volume/Meter Editor)
         │                                        │
         ▼                                        ▼
 [ VALIDATION ENGINE ] ── set points & limits per meter/analysis/quality
   • Config lives in Setup > Meter > Set Points (a.k.a. Validation Set Points)
     and Review > Set Points > List/Location (bulk).
   • History tables: FC_METER_VALIDATION_HIST, FC_METER_VALIDATION_MKF_HIST;
     config tables: fc_meter_validation, _es, _fv, _mkf, _mrv, fc_ffmtr_validation
     (table list verbatim from ADO 1416377).
         │ violations
         ▼
 [ EXCEPTIONS ] → reviewed in EXCEPTION RESOLVER
   • Two implementations ship side-by-side: the new .NET ER and the LEGACY ER.
     Fallback switch in the app .cfg: <add key="legacy:ExceptionResolver" value="Y"/>
     (25-01022034). Many display bugs are new-ER-only.
   • ER dashboard tiles look back 60 days by design (ADO 1723389).
   • Exception types seen in cases: Missing Data, Missing Analysis, No Flow,
     FPC - Low Differential Pressure, FVC - frozen Temperature/Static Pressure
     (ADO 1134948), Drive Gain (code 2158), CV/T/P exceptions on compensated
     meters (25-01015006).
         │
 [ MESSAGES ] — system notifications "FLOWCAL Message NNN: <event>"
   • Defined in Settings Manager → Application → Message Description; each has a
     type (System/Location/Meter/Source) and a Contact Name/D-List (Notify) that
     emails on trigger (26-01087471).
   • Known codes: 123 Meter import failed · 128 Meter data purge failed ·
     203 Meter Opened · 321 Ticket import failure.
   • Viewed in MESSAGE VIEWER (grid bugs: 25-01061708, 22-00554899).
 [ MESSAGE QUEUE viewer ] — window onto Windows MSMQ used by TESTit↔FLOWCAL (TI)
   integration; NOT a FLOWCAL service (22-00633108). Subscription table routes
   outgoing messages (26-01088473).
```

---

## 3. Decision Tree

```
Exceptions/validations/messages complaint
│
├─ Error text is "External exception EEFFACE" on a Set Points screen?
│    → §4 (table corruption; version check; do NOT chase the meter's data)
│
├─ Exception Resolver misbehaving?
│    ├─ Shows nothing / partial → new-ER display defect: try Legacy ER (§5);
│    │    if list-scoped on Oracle, check _kgl heap params (25-01052324)
│    ├─ Crashes/AV/unhandled exception → data edit AV bug (1788769) OR
│    │    UDF garbage (§9) — ask: "does it crash on ONE meter or any?"
│    ├─ Settings reset daily → Citrix profile (§5)
│    ├─ Freezes (old versions 10.0.x-10.5.0.2) → upgrade (§5)
│    └─ List dropdown empty → list group access (§5)
│
├─ Exceptions WRONG (missing, stale, wrong values)?
│    → §6 defect table by version; verify the client build FIRST — most of
│      these have a fixed-in; otherwise file with R#### PORT convention
│
├─ "FLOWCAL Message NNN" email complaint?
│    ├─ Wrong recipients → Message Description notify list (§7)
│    └─ The failure itself (123/321) → unwedge FC_TRANSACTION_QUEUE (§7),
│         then route the underlying import defect to the Imports skill
│
└─ Message Queue / sync to old server / MSMQ bloat → §8
```

---

## 4. EEFFACE at Validation Set Points (chronic, cross-version)

**Signature:** user opens Setup > Meter > **Set Points** (or the Set Point Calculator) and selects a meter → "External exception EEFFACE"; frequently the app then locks and must be killed. Sometimes only specific meters trigger it. Seen in 10.1.0 → 10.5.x (cases span 2021-2026: 21-00216019, 21-00104676→ADO 1134716, 24-00940910, 24-00943441, 24-00946405, 24-00960801→ADO 1675708, 23-00925917, 23-00919320, 23-00882863, 25-01049379, 26-01066345).

**Root cause (CONFIRMED via ADO threads):** corruption/column-drift in the validation *history* table — `FC_METER_VALIDATION_HIST` (and `FC_METER_VALIDATION_MKF_HIST`). ADO 1675708: customer found 84 `MRV_METER` columns removed from `FC_METER_VALIDATION_HIST`; ADO 1649003/1416377 remediation used a "set columns unused.sql" then a rebuild. A separate trigger path: analysis validations on **Mole %** with **Run on Edit = YES** immediately EEFFACEs the Set Points editor (ADO 1134221, repro by dev). Product-side fix landed in **10.5.0.22** (INFERRED from 26-01066345).

**Fix recipe (ordered, cheapest first):**
1. **Workaround** — clear the validation min/max values for the failing meter(s) with the **Bulk Change Editor**, then reopen Setup > Meter > Set Points; re-enter set points afterwards (25-01049379 has the full walk-through incl. Review > Set Points > List/Location for bulk re-setup; same workaround in 23-00919320, 24-00940910/ADO 1648664).
2. **Durable fix** — rebuild the hist table: run the `fc_meter_validation_hist` recreate SQL (referenced as `fc_meter_validation_hist.SQL` in 23-00925917; `Recreate fc_meter_validation_hist.sql` in ADO 1651621) **with all services stopped and all users out**.
3. **Version fix** — upgrade to ≥10.5.0.22 (INFERRED, 26-01066345). Liquids-specific set-points bug fixed **10.8.0.4** (INFERRED, 25-01006168).
4. Diagnostics dev asks for (ADO 1651621/1649003): `select * from FC_METER_VALIDATION_HIST;` `select * from fc_meter_validation_mkf_hist;` and `desc` of `fc_meter_validation`, `_es`, `_fv`, `_mkf`, `_mrv`, `fc_ffmtr_validation` (ADO 1416377).

Related validation-engine defects: validation changes made through the **Volume Editor don't auto-apply** (24-00949750, defect, no published fix — verify current behavior); **FcLoader** validation loads failing — one case was literally a wrong-sized `FcLoader.exe` binary, replaced from TEST env (25-01019896); older FCLoader validations bug "fixed in a later version" (22-00561330); Toolbox + **Run Validations screens fail to launch** — 3rd-party UI component had incorrect min/max date logic, patched in **10.2.0.22** (23-00878503 — this case includes a rare formal RCA), also 23-00877659 (fixed by 10.4.0.4 upgrade), 23-00876792 (8.10.50.15 patch), 23-00877311.

---

## 5. Exception Resolver display/UX failures

The new .NET ER carries a family of display bugs; the **Legacy ER is the universal workaround** (`<add key="legacy:ExceptionResolver" value="Y"/>` in the app cfg — 25-01022034; per-user availability in some builds).

| Signature | Root cause / status | Fix | Anchors |
|---|---|---|---|
| ER shows **no exceptions at all** (10.4.0.15) | Dev could not reproduce; still open | Legacy ER | 25-01054794; ADO **1739171** (New — repro found: after editing Edit Reasons w/ "Remember UI Filter Values" on, ER returns blank; also edit-reason dropdown omits multi-type reasons) |
| ER **viewer not working for Source Lists** (10.5.0.2) | Defect | Fixed **10.8.0.2** (INFERRED) | 25-00995790 |
| Same **GQ source in multiple lists** breaks ER display | Defect | Fixed **10.6.0.12 / 10.8.0.2** (INFERRED) | 25-01060221 |
| **Access Violation** editing data from ER (edit → apply → save → close Volume Editor → AV) | OPEN bug; "not able to estimate when this issue will be resolved" | Update Citrix Workspace + Legacy ER as mitigation | 25-01062048; ADO **1788769** (New) |
| Double-clicking exception **doesn't open Volume Editor** (legacy ER AVs) | Closed as Training-tagged | — | ADO **1837313**; source case 25-01048298 |
| **User-Preference default list breaks the List dropdown** (10.5.0.19) | Closed | — | ADO **1838687** |
| ER **freezing** (10.0.3, 10.5.0.2) | Old-version defects | Upgrade ≥10.6.0.6 / latest 10.5 (INFERRED) | 25-01023065, 25-01025070, 24-00977061 |
| "Error Loading Meter Periodic Values **Error: -32000**" + not responding | Defect | Fixed **10.5.0.20 / 10.6.0.7** (INFERRED); sibling tickets 25-01020741, 24-00964956 same fix | 25-01022729 |
| ER **settings keep resetting** / Group Selector settings lost | Corrupt Citrix user profile | Cloud resets Citrix profile | 26-01104193, 26-01085068 (TGNR) |
| **List dropdown empty** for a user | List not granted to the user's group | List Editor → select list → **Group and User Access** tab → add group | 25-01048705 |
| List selected, no exceptions returned; huge lists on Oracle | Oracle shared-pool large-heap thresholds | DBA sets `_kgl_large_heap_warning_threshold` / `_kgl_large_heap_assert_threshold` | 25-01052324 |
| ER **tiles count ≠ ER grid count** | Expected behavior — tile widget looks back **60 days** | Set Date Selector = Effective Date, From = 60 days ago for apples-to-apples | 25-01011341; ADO **1723389** (Closed) |
| ER email: can only email ~65 exceptions at once | Long-standing limit bug in new ER | — | ADO **1134948** (New, escalated) |
| ER slow on **dynamic list for a close group** | Performance; no fix in case | Static list workaround; escalate w/ timings | 25-01054845 |

Message Viewer (sibling grid): column headers misaligned — accepted to backlog then deprioritized/closed (25-01061708); older Message Viewer error fixed in **10.2.0.8** (INFERRED, 22-00554899).

---

## 6. Exceptions wrong: not generated, not auto-resolved, wrong values

Version-check FIRST — this cluster is dominated by known defects with fixed-ins.

| Defect | Versions seen | Fixed in (INFERRED unless noted) | Anchors |
|---|---|---|---|
| **Missing Data exception not resolved on import** (gap filled, exception stays) | long-running | ADO **1566894** still in **Code Review** (DEV*) — NOT fully shipped; MERGEit STRs failed at one point | source case 22-00868682 (Plains Midstream Canada) |
| **Missing Analysis exception doesn't clear on Analysis Apply** | 10.5 era | Closed via ADO **1690399** (R1050 PORT) resolving **1675377**, ported to 10.5 for Boardwalk | 24-00968882 |
| **No Flow exceptions missing** | 10.6.0.6 | 10.6.0.7 | 25-01029310 |
| 'No Flow' exception error (Tory-Tech/TGI) | pre-update | cleared after client's FLOWCAL update | 24-00954411 |
| **Exceptions not recreated** after purge/reimport | 10.5.0.9 | 10.5.0.20 / 10.6.0.7 / 10.7.0.1 / 10.8.0 | 24-00965165 |
| **Run Validations on quality data creates no exceptions** | 10.5.0.17 | 10.5.0.19 | 25-01012873 |
| **Exception recognition issues** (TGI, severity High) | 10.4.0.14 | 10.8.0.4 | 25-01004221 |
| **Exception Queue/Validations bug** | 10.x | 10.3.0.23 | 24-00988967 |
| Auto Edits **set VCF = 1 and auto-resolve exceptions** they shouldn't | 10.6 era | 10.6.0.13 patch | 24-00992610 |
| **Drive Gain (code 2158)** exception pulls wrong **Field Value** into ER | 10.x | targeted 10.9 (June 2026) | 26-01068318, 25-01043587 |
| **CV exceptions for T and P on compensated meters** | — | defect accepted; no fix noted in case | 25-01015006 |
| **Exceptions Graph** misrepresents missing data; yellow exception line solid for whole month | 10.8.0.3 (also 10.6.0.24, 10.5.0.14 listed in repro) | ADO **1866898** (New) — OPEN | — |
| Coriolis raw-volume **exception reset** behavior | 10.x | defect per case; details thin | 25-01021218 |
| Incorrect exceptions for Coriolis / different Events & Alarms 10.1 vs 10.6 | 10.1 | 10.6 behaves correctly (10.1 bugs fixed) — Expected Behavior on 10.6 | 25-01029309, 25-01029317 |
| Analysis validation not firing | 10.2.0.x | 10.2.0.14 | 22-00648618 |
| CFX import fails on **bad GQ validations** | 10.2.x | 10.2.0.19 | 22-00645413, sibling 22-00571108 |
| GQ import validation exception issue | 10.0.3.x | 10.0.3.15 | 22-00603897 |
| Min/max validations on **alkenes (C3H6/C2H4)** in liquids never create exceptions | all | **Product limitation** — alkene mole % not editable/validated; confirmed with Product Management | 22-00550969 |

**Filing new ones:** Measurement bugs carry the SF case in the title (`2x-00xxxxxx--<subject>`) and land in `Quorum\North America\Measurement`(+`\Maintenance`) or `QuorumSoftware\Engineering\Measurement\Maintenance`; ports use the `(DEV*)` / `(R#### PORT)` suffix (observed on 1566894 DEV* / 1690399 R1050 PORT / 1854045 R1090 PORT).

---

## 7. "FLOWCAL Message NNN" notifications & the failures behind them

**Editing who gets notified (config recipe, verbatim from 26-01087471):** Settings → Settings Manager → **Message Description** (under the Application group) → filter the grid by type (System / Location / Meter / Source) → locate the message number (e.g. 321) → Edit → change **Contact Name/D-List (Notify)** → Save. Same path used to remove a departed employee from Message 321 in UAT (26-01120450 — note UAT and PRD have separate lists).

| Message | Meaning | What actually fixes the underlying failure | Anchors |
|---|---|---|---|
| **123** — Meter import failed | A record wedged in the transaction path blocks subsequent imports | Script: `DELETE` rows with `UNAVAILABLE = 0` from `FC_TRANSACTION_QUEUE` and `FC_TRANSACTION_SNAPSHOT`, then imports proceed past the bad record | 23-00882995 (script confirmed), 22-00827444, 22-00804957 (restart file imports; check which env has email enabled) |
| **128** — Meter data purge failed (FcDataBoss) | Running services hold the meters being purged | Stop all services → purge/import → restart | 22-00660880 |
| **203** — Meter Opened | Informational; clients keep asking to enhance/suppress | Enhancement territory (Not in Product Plan twice) → User Voice | 22-00708986, 22-00627945 |
| **321** — Ticket import failure | Liquids ticket import failed; notification list frequently stale | §7 recipe above for routing; the import failure itself → Imports skill | 26-01087471, 26-01120450 |

---

## 8. Message Queue viewer / MSMQ / TI subscription plumbing

MSMQ is **Windows** infrastructure used by TESTit↔FLOWCAL (TI) integration — not a Quorum service (22-00633108). The FLOWCAL "Message Queue" screen is a viewer over it.

| Signature | Root cause | Fix | Anchors |
|---|---|---|---|
| Outgoing messages routed to the **old server** after a server migration | Stale rows in the TI **subscription table** | **Truncate the subscription table**, restart TI services; queues then point at the new servers and TESTit↔FLOWCAL sync resumes | 26-01088473 |
| Queues not processing on Field Applications server | **Message Queue Storage Limit** checkbox set on the server | Uncheck it, restart the FieldApplications Integration service | 26-01064484 |
| MSMQ storage folder eating the disk (50-80+ GB) | No cleanup being run | Cleanup recipe (22-00604400, verbatim): stop Integration Services (set Manual) → delete messages in Private Queues + journals + dead-letter → stop MSMQ service → start it (slow — triggers cleanup) → verify storage back to ~2 GB; if not, PowerShell: `$msmqApp = New-Object -ComObject MSMQ.MSMQApplication; $msmqApp.Tidy()` | 22-00604400, 24-00942226, 25-01020975 (KB doc), 22-00604440 |
| MSMQ service stuck "**Starting**" after long uptime/Windows update | Checkpoint replay — takes hours, not broken | Wait it out; reboot cadence helps | 22-00633108, 22-00604475 (Windows Update fixed) |
| Blue line in Message Queueing | The **audit queue** — logging of successfully processed messages; ignorable | Expected behavior | 24-00956972 |
| General TI queue monitoring | — | KB **000003949** "TESTit (TI 3): Integration troubleshooting tips" | 25-00996950 |

Escalation note: MSMQ bad data after Vault/TI misconfig also appears in the Security skill (26-01098171 — purge audit/error queues after VaultApi fix).

---

## 9. Bad-data-shaped exception failures (data-investigator handoffs)

- **ER crashes with "Unhandled exception from AppDomain.CurrentDomain.UnhandledException"** on specific meters → gibberish written into meter **User-Defined Fields** (by an import). Clean/NULL the UDFs and ER works (26-01104714 MPLX). The same UDF garbage broke list rollups/reports in 26-01113739 (fix: NULL the fields, requeue Postponed records). **Rule: single-meter ER crash → inspect UDFs before filing a bug.**
- **Source apply conversion not possible (ER)** while GQ Source Editor shows a Z-Method → **Z-Method NULL at the database level**, inherited from older versions. Fix by SQL update or by toggling the Z-Method in the Gas Quality Source Editor (change → save → revert → save) which rewrites the row (26-01122401).
- **Plate change "Unable to Save" (Program Termination Window)** — device characteristics arriving from the field didn't match FLOWCAL standards (AGA-8 Detail 1992 + Time Trails), plus a blank record stamped 09:59:59 let the device characteristic in; after correcting those records the meter saved (25-01053071). Leads-vs-trails conversion clients are prone to this.
- Business Status ≠ validation problem: meters with Business Status other than "On" are treated **out of service — no imports, excluded from reports**; set via Meter Editor or TESTit imports; NOT date-effective (25-01017303 — full option list On/Off/Pending disconnect/Pending New/Pending reconnect).

---

## 10. Known ADO items (verified live 2026-09-02)

| ADO | Project / Area | Type / State | Title (verbatim) | Relevance |
|---|---|---|---|---|
| 1739171 | Quorum | Bug / **New** | Exception resolver doesn't show exceptions or exception edit reasons | Blank-ER repro incl. Remember UI Filter Values |
| 1788769 | Quorum | Bug / **New** | Error when Editing from exception resolver (user data edit) | Access violation on edit-from-ER |
| 1566894 | QuorumSoftware\Engineering\Measurement\Maintenance | Bug / **Code Review** | Missing Data Exception Not Resolved on Import (DEV*) | Auto-resolution engine defect, unshipped |
| 1690399 | QuorumSoftware\Engineering\Measurement\Maintenance | Bug / Closed | 21-00211212--Missing Analysis Exception Doesn't Clear on Analysis Apply (R1050 PORT) | Port that resolved 1675377 |
| 1675377 | QuorumSoftware\Engineering\Measurement\Maintenance | Bug / Closed | 24-00968882--Missing Analysis Exceptions Not Resolved on Data Import | |
| 1866898 | Quorum | Bug / **New** | Exceptions Graph in 10.8.0.3 Incorrectly Identifying missing data and date exception | Graph shows 0 for missing data; solid yellow line |
| 1723389 | QuorumSoftware\Engineering\Measurement | Bug / Closed | Exception Resolver Tiles count not matching with Exception Resolver. | 60-day tile lookback = by design |
| 1837313 | Quorum | Bug / Closed (Training tag) | Exception Resolver not opening volume editor | NiSource 25-01048298 |
| 1838687 | Quorum | Bug / Closed | Exception Resolver - Setting a User Preference List Causes the List Dropdown to not function UAT - PENDING SUPPORT (7/17/2026) | 10.5.0.19 |
| 1134948 | Quorum | Bug / **New** (Escalated) | New .NET Exception Resolver - Email Issues | ~65-exception email cap |
| 1651621 | QuorumSoftware | Bug / Closed | 24-00946405--Validation Set Points -- EEFFACE Error | Recreate fc_meter_validation_hist.sql |
| 1675708 | QuorumSoftware | Bug / Closed | EEFFACE Error- Set Point Calculator | 84 MRV_METER columns missing from FC_METER_VALIDATION_HIST |
| 1649003 | QuorumSoftware | Bug / Closed | 24-00943441--EEFFACE Error when trying to open meter Setpoints | "set columns unused.sql" + GMS_DATE diagnostics |
| 1648664 | QuorumSoftware | Bug / Closed | 24-00940910--FlowCal 10.3.0.10 issue with Set Point screen | Bulk-editor workaround documented |
| 1553289 | QuorumSoftware | Bug / Closed | [AHT] Meter Set Points EEFFACE Error (Dev) | Problematic SQL in set-points form found by dev |
| 1416377 | QuorumSoftware | Bug / Closed | 21-00216019--Flowcal Validation Set Point Error-"External exception EEFFACE" | Canonical validation table list |
| 1134716 | QuorumSoftware | Bug / Closed | [EXT] Validation Set Point Error | 10.2.0.2 freeze variant |
| 1134221 | QuorumSoftware | Bug / **Proposed** | Validation Set Point Editor Freezes When Null Values Are Saved (10.1.0) | Mole% + Run-on-Edit trigger for EEFFACE |

---

## 11. Diagnostic SQL (FLOWCAL Oracle; set date format first — support-standard per 25-01004570)

```sql
ALTER SESSION SET nls_date_format = 'mm/dd/yyyy hh24:mi:ss';

-- EEFFACE triage: state of the validation history tables (ADO 1651621/1649003)
SELECT METER_NUMBER_INDEX, GMS_DATE FROM fc_meter_validation_hist;
SELECT * FROM fc_meter_validation_mkf_hist;
-- structure drift check (ADO 1416377):
-- desc fc_meter_validation; desc fc_meter_validation_es; desc fc_meter_validation_fv;
-- desc fc_meter_validation_mkf; desc fc_meter_validation_mrv; desc fc_ffmtr_validation;

-- Message 123 unwedge (23-00882995) — BACK UP FIRST; services stopped:
DELETE FROM FC_TRANSACTION_QUEUE    WHERE UNAVAILABLE = 0;
DELETE FROM FC_TRANSACTION_SNAPSHOT WHERE UNAVAILABLE = 0;
COMMIT;
```
Env assumption: client PRD/UAT Oracle as fcowner. Column lists for the UDF-garbage sweep (§9) are **NOT YET RUN** against a live schema — enumerate the Volume Editor UDF columns via the metadata server on first connected case.

---

## 12. Expected-Behavior FAQ

- **"ER dashboard tile count doesn't match the ER grid."** Tile widget is a 60-day snapshot by design; set Date Selector = Effective Date, From = exactly 60 days back to compare (25-01011341, ADO 1723389).
- **"10.6 gives different Events/Alarms/exceptions than 10.1 for the same meter."** 10.6 is correct; 10.1 had bugs since fixed — not a regression (25-01029309, 25-01029317).
- **"Validations on alkene components don't create exceptions."** Mole % for alkenes isn't editable/validated — product limitation confirmed by Product Management (22-00550969).
- **"Blue line in Message Queueing?"** The audit queue — a log of successfully processed messages; ignore (24-00956972).
- **"Meter stopped importing and dropped off reports after a TESTit import."** Check Business Status — anything other than "On" = out of service, immediately, not date-effective (25-01017303).
- **"Resolution dates from SQL don't match FLOWCAL screens."** Set `nls_date_format = 'mm/dd/yyyy hh24:mi:ss'` in the session (25-01004570).
- **"Bulk-inhibit LQ sources from ER?"** Not in product plan — enhancement (23-00932755).

---

## 13. Escalation guidance

- **Before filing any exception-generation bug**: capture exact FLOWCAL version and test against §6's fixed-in table — half of these cases close as "already fixed in 10.x.y.z". Deliverable is then a Version-issue note + upgrade/patch path.
- **EEFFACE**: L4 can execute the workaround (§4 step 1) immediately; the table rebuild needs a change window (services down, users out). Attach `FC_METER_VALIDATION_HIST` diagnostics when escalating; ADO lineage 1416377→1649003→1651621→1675708.
- **ER display bugs**: reproduce with the Legacy ER toggled — if Legacy works, cite the matching open bug (1739171 blank ER, 1788769 edit AV, 1866898 graph, 1134948 email cap) instead of filing a duplicate; note dev historically **cannot reproduce** the blank-ER family, so ship repro artifacts (FcDataBoss export, User Preference settings, "Remember UI Filter Values" state).
- **Single-meter crashes** → data-investigator first (UDF garbage §9), engineering second.
- File new Measurement bugs with the SF case number prefix in the title and expect `(DEV*)`/`(R#### PORT)` twins; support-visible triage lands in `Quorum\North America\Measurement`, engineering copies in `QuorumSoftware\Engineering\Measurement\Maintenance`.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
