# SKILL — FLOWCAL Family: Field Operations (Tasks, Schedules, Devices & Proving Runs)

> **Products:** TESTit (`Product_list__c = 'TESTit'`) + PROVEit (`'PROVEit'`), with FLOWCAL touchpoints.
> **Coverage plan group:** #13 (Field operations) — ~1,720 family cases, ~95 actionable floor.
> **Sources:** Salesforce all-history mining (closed cases, 2018–2026-09) + ADO org `QuorumSoftware`
> (area paths `Quorum\North America\Measurement`, `\Maintenance`, `\Field Apps and API`, `\Field Apps Saas`,
> `QuorumSoftware\Engineering\Measurement\*`). Mined 2026-09-02.
> **Auto-Bot skill — built by Aditya Bhagat.** Every root-cause claim below cites SF case and/or ADO ids verbatim.

---

## 1. Quick Triage

| Symptom / error text | Likely cause | § |
|---|---|---|
| PROVEit/TESTit crashes at launch; "Exception Error occurred in CAppDATUtils: An item with the same key has already been added" | Corrupt local `.DAT` state file (per-user or ProgramData) | §3.1 |
| "Exception Error occurred in CMiscUtils: Could not find file '...\TESTit3\Layouts\FSchedules\findLayoutControl\Default.xml'" | Missing/corrupt user layout XML | §3.1 |
| "CAppDATUtils: '.', hexadecimal value 0x00, is an invalid character" | Corrupt DAT/XML (null bytes) after crash/disk event | §3.1 |
| "CAppDATUtils: Attempted to perform an unauthorized operation" | AppData/ProgramData permissions | §3.1 |
| OMNI retrieve fails: "Value was either too large or too small for a Decimal" (stack: `CCommOmni.RetrieveMassRuns`) | Garbage register value from OMNI (e.g. viscosity) blows Decimal ctor | §3.2 |
| OMNI retrieve then save fails: "CDbio: Arithmetic overflow error converting numeric to data type numeric", viscosity absurd | Same family — fixed in PROVEit 9.18.0 (INFERRED) | §3.2 |
| PROVEit hangs retrieving OMNI prove via EFM / "unable to retrieve OMNI" | Legacy rigid OMNI driver (fixed registers); or comms/block mapping | §3.2 |
| OMNI retrieval returns only the LAST prove regardless of selected meter | OMNI stores last prove per run area — expected device behavior | §7 |
| Auto Run button greyed out / does nothing | Required prove-section data missing (often Analog config incomplete) | §3.3 |
| Auto Run disabled after discarding/removing runs (post-9.12) | Discard≠delete design change at 9.12 | §3.3 |
| "An application error occurred." on run ~20 of a proving task, app closes; uncertainty won't calculate | PROVEit 9.16.1 defect (run-count crash) | §3.3 |
| Run data values wrong during prove | Defect fixed in PROVEit 9.17.0 (INFERRED) | §3.3 |
| Prover Expansion Coefficient differs between PROVEit prover setup and tasks | Display-only bug, versions x.15+, tied to Proving Calc. Method (API 12.2 2021 vs 12.2.3 1998) | §3.4 |
| Schedule recurrence/due date changed "by itself" after FLOWAVERAGES import | Import never changes recurrence — a user edited the Schedule Definition | §3.5 |
| Schedules on tech laptops ≠ server even after sync | Sync/schedule-entry divergence — PS/FA engagement (24-00945917); see also WebSync skill | §3.5 |
| Cannot link historical tasks to schedules after 3.18 upgrade | ADO 1837892 (open defect) | §3.5 |
| "Error importing FA_ATTACHMENT_TASK_REL" during TIDX import | Null/orphan attachment on a task in the export file | §3.6 |
| Cannot save fields on a task (e.g. 'SA Gas Sample') | User missing technician role; recurrence → reinstall/upgrade | §3.6 |
| Can't print / print-preview tasks; Log File Viewer empty | Environment/report config (Citrix printer/perm) — App Config | §3.6 |

## 2. Decision Tree

```
Field app problem (TESTit/PROVEit)
├─ App won't launch or crashes on open?
│   └─ Error names CAppDATUtils / CMiscUtils / a .dat or Layouts\*.xml file → §3.1 (local state reset; G2/G1 — NOT a code defect except "same key" variant)
├─ Device communication (OMNI/SVP/flow computer)?
│   ├─ Decimal/numeric overflow in error → §3.2 (bad register data; version gate G3: 9.18.0+)
│   ├─ Hang / no data / partial data → §3.2 (driver era, block mapping, COM settings)
│   └─ Values differ PROVEit vs OMNI → §7 (calc host mode / method — usually expected)
├─ During a proving task?
│   ├─ Auto Run greyed → §3.3 (missing prove data — config, G2)
│   ├─ Crash at high run count → §3.3 (9.16.1 defect, G5/G3)
│   └─ Coefficient display mismatch → §3.4 (display bug, ADO 1807377 — G3/G1 hybrid)
├─ Schedules / flow-average recurrence wrong? → §3.5 (G1 expected behavior vs Schedule Definition edits; 3.18 tooling)
└─ Task-level (save, import, print, delete)? → §3.6
Sync/integration to FLOWCAL failing? → route to SKILL_FLOWCAL_Integrations_WebSync.md
```

---

## 3. Symptom Clusters

### 3.1 Launch crashes & corrupt local state (CAppDATUtils / CMiscUtils / .DAT / layout XML)

**Signature.** App fails during load or when opening a screen. Variants seen in history:
- `Exception Error occurred in CAppDATUtils: An item with the same key has already been added.` — PROVEit crash at launch (SF 26-01102884, Software Defect).
- `Exception Error occurred in CMiscUtils: Could not find file 'C:\Users\<user>\AppData\Local\Flow-Cal, Inc\TESTit3\Layouts\FSchedules\findLayoutControl\Default.xml'` — hit BOTH products; three cases in one quarter (SF 25-01012703 PROVEit, 25-01013677 TESTit, 25-01005681 TESTit — all Software Defect). Note: PROVEit shares the `TESTit3` layouts directory.
- `CAppDATUtils: '.', hexadecimal value 0x00, is an invalid character.` — null-byte corrupted DAT/XML (SF 22-00633117, 22-00619839).
- `CAppDATUtils: Attempted to perform an unauthorized operation.` — filesystem permission on the state files (SF 22-00549633).
- Generic "Error Message when launching PROVEit Application" (SF 26-01122957, App Config).

**Root cause.** `CAppDATUtils` reads serialized local state (`.DAT`) files; `CMiscUtils` reads per-user layout XML. A duplicate key, truncated write (0x00), missing file, or ACL problem in these files kills startup/screen load. CONFIRMED via resolutions on 26-01102884 and 26-01122957.

**Fix recipe (cheapest first):**
1. Machine-wide DAT: delete `C:\ProgramData\Flow-Cal, Inc\Field Apps\fieldapplications.dat`, relaunch (verbatim resolution, SF 26-01122957).
2. Per-user DAT: remove the user's `.DAT` file — "we removed the .DAT file, this was only for one user so no permissions were affected" (SF 26-01102884).
3. Layout XML: in-app `File > Preferences > Restore Layout / Reset All Settings` (verbatim resolution, SF 25-01012703). If app won't open, rename `%LOCALAPPDATA%\Flow-Cal, Inc\TESTit3\Layouts`.
4. "Unauthorized operation": grant the user modify rights on `%LOCALAPPDATA%\Flow-Cal, Inc\` and `C:\ProgramData\Flow-Cal, Inc\` (SF 22-00549633 pattern).

**Anchors:** SF 26-01102884, 26-01122957, 25-01012703, 25-01013677, 25-01005681, 22-00633117, 22-00619839, 22-00549633. Related ADO 1855449 "TESTit 3.17.1 Error for many users" (Closed).

---

### 3.2 OMNI / flow-computer retrieval failures (devices)

**Signature.** Retrieving prove/run data from an OMNI 6000/7000 (serial or EFM) fails, hangs, or returns garbage. Distinct sub-signatures:

| Sub-signature | Case/ADO | Status |
|---|---|---|
| `Value was either too large or too small for a Decimal.` — stack `System.Decimal..ctor(Double)` at `FlowCal.FieldApplications.Classes.Communication.Omni.CCommOmni.RetrieveMassRuns() → RetrieveRuns() → ExecuteSequence → GetRunsThread()`, PROVEit 9.17.1.0 | ADO 1855354 (Bug, `Quorum\North America\Measurement`, **New/open**) | Open |
| `CDbio: Arithmetic overflow error converting numeric to data type numeric` on save after OMNI retrieve; viscosity value "extremely off" | SF 25-01026896 — resolution: "This issue has been fixed in PI 9.18.0" | Fixed in PROVEit 9.18.0 (INFERRED — support statement, not release-notes-confirmed) |
| ProveIt hanging when retrieving OMNI prove via EFM | SF 24-00957670 | No recorded resolution |
| Prove run data not pulled in at all (old TESTit) | SF 25-01021215 | By design of legacy driver — see below |
| Omni connection crashing | SF 23-00892071 (ChangeConfig) | Config |

**Root cause.** Two real mechanisms:
1. **Bad register data → numeric conversion blowup.** A nonsense float in an OMNI register (viscosity is the repeat offender) overflows .NET `Decimal` or the DB numeric column. CONFIRMED via ADO 1855354 stack + SF 25-01026896.
2. **Legacy driver rigidity.** Verbatim from SF 25-01021215: "The OMNI communication in the older versions of the application is somewhat rigid in that it has hard requirements on what data is required and where it comes from (registers). ... later versions that have the Flow Computer/Modbus comms are a lot more flexible and can be configured to poll data from any register."

**Fix recipe:**
1. Read the field-app log (`_fc`-style Serilog `.jsonl`, e.g. `%ProgramData%\Flow-Cal, Inc\...\PROVEit` logs) for the exact stack. If `RetrieveMassRuns` + Decimal → inspect/correct the OMNI's mass-run registers (esp. viscosity) at the device; upgrade to PROVEit ≥ 9.18.0 for the CDbio overflow variant (INFERRED fix, SF 25-01026896).
2. Hang or partial retrieval on old versions → recommend upgrade to the Flow Computer/Modbus comms driver generation and re-map registers (SF 25-01021215).
3. Verify block mapping for OMNI 4000/7000 (modbus config guides exist — SF 24-00955340, 23-00914195, 23-00897042).
4. "Only last prove retrieved regardless of meter" → expected: the OMNI exposes its stored prove reports sequentially; select correct run/report on the device (SF 25-01029545, closed Training).

**Anchors:** ADO 1855354; SF 25-01026896, 24-00957670, 24-00958279, 25-01021215, 25-01029545, 24-00955340, 23-00892071, 22-00874899 (`FA_TASK_METER.omni_meter` column reference).

---

### 3.3 Proving-run execution: Auto Run greyed, discard vs delete, run-count crash

**Signature A — Auto Run greyed out / unresponsive.**
Root cause (CONFIRMED, verbatim from SF 24-00982690): "If the auto run is greyed out something in the prove section is missing data. ... turns out to be it was the Analog config was open and that needs the setup with some section needed to be filled in. After this, the auto run worked."
Fix recipe: walk meter characteristics → prover → product data → analog/temperature/pressure input config; the first incomplete section is the blocker. Anchors: SF 24-00982690 (9.17.1), 25-01004543.

**Signature B — Auto Run disabled after removing "invalid" runs.**
Root cause (CONFIRMED, SF 26-01101757 resolution): "9.12 techs could delete runs, after 9.12 version techs will only see a line over the runs as discarded not deleted." Post-9.12 the runs remain (struck through); techs who try to "clean up" mid-task can end up with the task in a state where Auto Run stays disabled. Companion case SF 26-01101772 (Training): discard greys the button by design until the task state is valid.
Fix recipe: educate on discard semantics; complete/close the task rather than deleting runs; if truly stuck, reopen task from schedule.

**Signature C — crash at high run count.**
"An application error occurred." on run 20 (5 passes/run) of a Meter Proving Task, application exits; uncertainty won't calculate. PROVEit 9.16.1. Root cause: product defect — "This is a bug. The customer has a workaround for now." (SF 25-01049568, Software Defect). Workaround in practice: keep runs-per-task below the crash threshold / split the prove; escalate for fix version.

**Signature D — run data incorrect during prove.**
Root cause: defect; resolution verbatim "This issue has been fixed in PROVEit 9.17.0." (SF 24-00955724) — label INFERRED fixed-in 9.17.0.

**Anchors:** SF 24-00982690, 25-01004543, 26-01101757, 26-01101772, 25-01049568, 24-00955724, 24-00943809 (zeros in run data — laptop-specific/security), 25-01021215.

---

### 3.4 Prover Expansion Coefficient display mismatch (Ga / Gl / Gc)

**Signature.** Prover Exp. Coeff. shown in a proving task ≠ value on the prover record; customers fear miscalculation (SF 26-01073315, 25-01030324).

**Root cause (CONFIRMED — verbatim from SF 26-01073315 resolution):** "This is a display bug for all versions x.15 and later. It is tied to the selection of the 'Proving Calc. Method'. When 'API 12.2.3 (1998)' is selected, then the Prover Exp. Coeff. value displays as the Gc value for provers with internal switches (e.g. sphere type provers) and displays as the Ga value for provers with external switches (e.g. piston type provers). However, when 'API 12.2 (2021)' is selected, then the Prover Exp. Coeff. displays as the Gl value always for all types of provers. The correct value is being applied in the calculations, but the display value changes."

ADO: **1807377** "Prover Coefficient Expansion not displayed correctly" (Bug, `Quorum\North America\Measurement\Field Apps and API`, Closed).

**Fix recipe:** reassure — calculations are correct, display-only. Workaround to make displayed value match legacy expectation: set Proving Calc Method to `API 12.2.3 (1998)` (SF 26-01073315). Terminology change stems from API MPMS Ch. 12.2 (2021).

**Anchors:** SF 26-01073315, 25-01030324; ADO 1807377.

---

### 3.5 Schedules, recurrence & flow averages (TESTit)

**Signature.** Schedule due dates or recurrence "changed by themselves"; flow-average-driven (tiered) schedules out of bounds; laptop schedules diverge from server; can't link historical tasks after upgrade.

**Root causes (each anchored):**
1. **FLOWAVERAGES import does NOT touch recurrence.** Verbatim (SF 26-01114269, Software Defect→analysis): "importing FLOWAVERAGES records from FLOWCAL or via CSV does not update the Due Date or Recurrence settings in TESTit. The recurrence change observed by the customer was traced to a Schedule Definition modification performed by a user." Recurrence can be recalculated by toggling the Schedule Definition recurrence type, saving, then restoring the original tiers — but Due Date must still be updated manually. TESTit **3.18** added out-of-bounds schedule identification + recurrence recalculation from tier settings (release-notes-referenced in case; treat build as CONFIRMED-by-notes).
2. **Flow-average sync itself has had real defects** — ADO 1736018 / 1812254 "Syncing FlowAverages happens with open data even though Closed option specified" (1812254 Closed; port pair), ADO 1789020 "FlowCal.FieldApplications.Integration.Service crashing due to Flow Averages (R1060 Logging)" (Closed), ADO 1687515 "Flow Averages to TESTit (R1080* PORT)" + 1775815 "(DEV)" (both Closed → INFERRED fixed in FLOWCAL R10.80 line). If averages aren't ARRIVING, route to the Integrations/WebSync skill §4.
3. **Historical task linking broken after 3.18 upgrade** — ADO 1837892 "Unable to Link Historical Tasks to Schedules Since Upgrading to TESTit 3.18 (From 3.16)" (New/open).
4. **Laptop vs server schedule divergence after sync** — SF 24-00945917 (Software Defect; resolved via Professional Services + Field Apps engagement, no packaged fix — treat as escalation path). Related: SF 25-01008392 "Schedules not being shown under calendar grid", 24-00978881 errors in Calendar/Schedules/Task Explorer, 24-00940843 status icon missing.
5. **Schedule export filters** — SF 24-00995663 "TESTit 3.13 Exporting Schedule using 'Use Task Filter' option" (Software Defect); SF 25-01015500 "not exporting scheduled jobs" (Software Defect).

**Fix recipe:** first ask "who edited the Schedule Definition?" (audit), then check tier config, then only then suspect the import/sync. For tier/out-of-bounds pain, upgrade to ≥3.18 for the recalculation tooling (SF 26-01114269).

**Anchors:** SF 26-01114269, 26-01090630, 25-01031250, 26-01096679, 24-00945917, 25-01008392, 24-00978881, 24-00940843, 24-00995663, 25-01015500, 25-01050517; ADO 1837892, 1736018, 1812254, 1789020, 1687515, 1775815.

---

### 3.6 Task-level operations: save failures, TIDX task import, printing, deletion

**Sub-clusters (anchored):**
1. **Task fields won't save** — SF 24-00993150 ('SA Gas Sample'): "The user ... was not set to a role. We added him to the technician role. This seems to have fixed the issues." Recurred → reinstall + upgrade to 3.17.1. Always check role assignment FIRST.
2. **TIDX import fails on task attachments** — `Error importing FA_ATTACHMENT_TASK_REL` (SF 26-01097299 + 26-01088241, both Software Defect). Root cause: a task in the export carries a null/broken attachment record. Resolution verbatim: "The only way to correct this is to re-create the export file. Customer will need to remove the null file from the troubling task and re-create the export." Check the FieldApplication log for the failing task id.
3. **Print / print-preview failures** — SF 26-01095488 (PROVEit can't print proving task), 25-01033924 (TESTit Server can't print-preview any task + empty Log File Viewer), 25-01023027 — all Application Configuration (server printer/permissions/report runtime), not defects.
4. **Deleting proving-task steps / tasks** — permission-gated: SF 26-01118225 (App Config); bulk deletion is a support-assisted operation (SF 24-00984645). Post-9.12 run deletion is impossible by design (§3.3B).
5. **Tasks show Failed inside TESTit itself** — usually a characteristic/UOM data issue, see Integrations skill §3 (SF 26-01109077: "Pressure base units was missing.").

**Anchors:** SF 24-00993150, 26-01097299, 26-01088241, 26-01095488, 25-01033924, 25-01023027, 26-01118225, 24-00984645, 26-01109077.

---

## 4. Known ADO items (Field Ops)

| ADO id | Title (verbatim) | State | Area path |
|---|---|---|---|
| 1807377 | Prover Coefficient Expansion not displayed correctly | Closed | Quorum\North America\Measurement\Field Apps and API |
| 1855354 | error when retrieving prove from OMNI 6000 | New | Quorum\North America\Measurement |
| 1837892 | Unable to Link Historical Tasks to Schedules Since Upgrading to TESTit 3.18 (From 3.16) | New | Quorum\North America\Measurement\Maintenance |
| 1736018 / 1812254 | Syncing FlowAverages happens with open data even though Closed option specified | New / Closed | Maintenance / Measurement |
| 1687515 / 1775815 | Flow Averages to TESTit (R1080* PORT) / (DEV) | Closed | Maintenance |
| 1849247 / 1854030 | TESTit: Reports Causing Duplicate PPA's / (R1060 Logging) | New / Closed | Maintenance |
| 1855449 | TESTit 3.17.1 Error for many users | Closed | Measurement |
| 1862622 | 26-01112292--TESTit Server upgraded to 3.19.0.0- Imports not working | New | Maintenance |
| 1853073 | Prover Restore Button Does not Fully Revert Deleted State in UI | New | Field Apps Saas |
| 1861317 | Restore Prompt never appears when creating a device with a deleted Prover's ID | New | Field Apps Saas |
| 1859220 | Provers have no server-side permission enforcement | New | Field Apps Saas |
| 1805160 | Legacy sync status values not preserved; three states missing from Blazor enum | Closed | Field Apps Saas |

Port convention: paired DEV/PORT bugs, suffixes like `(DEV)`, `(R1080* PORT)`, `(R1060 Logging)`. All fixed-in builds INFERRED unless release notes say otherwise.

## 5. Diagnostic SQL (templates — label every run; DEV-tier envs only, FLOWCAL/TESTit DB objects; NOT YET RUN)

```sql
-- Task↔meter linkage incl. OMNI flag (column confirmed via SF 22-00874899)
SELECT * FROM FA_TASK_METER WHERE meter_id = :meter_id;           -- check omni_meter flag

-- TIDX attachment import failures: find task attachment relations for the failing task
SELECT * FROM FA_ATTACHMENT_TASK_REL WHERE task_id = :task_id;    -- look for null file refs (SF 26-01097299)
```
Env assumption: TESTit/PROVEit SQL Server or Oracle field-apps schema (`FA_*` tables). Client-PRD data-state claims stay INFERRED until run.

## 6. Expected-Behavior FAQ

- **"OMNI gives me the last prove, not my meter's prove."** The device serves its stored prove reports; select the correct report/run area on the OMNI (SF 25-01029545).
- **"Meter Factor differs between PROVEit and OMNI."** Check the Calc Host mode (PROVEit vs OMNI as calculation host) and the proving calc method before suspecting a bug (SF 22-00541091, 22-00603912, 24-00994623).
- **"Techs can't delete bad runs anymore."** By design since 9.12 — runs are discarded (struck through), never deleted (SF 26-01101757).
- **"Prover coefficient looks wrong on the task."** Display-only, API 12.2 (2021) terminology (Gl vs Ga/Gc); calculations unaffected (SF 26-01073315, ADO 1807377).
- **"FLOWAVERAGES import changed my recurrence."** It can't; audit Schedule Definition edits (SF 26-01114269).

## 7. Escalation guidance

- Reproducible crash with a stack trace naming `FlowCal.FieldApplications.*` → ADO Bug in `Quorum\North America\Measurement` (triage) / `\Field Apps and API`; include the Serilog `.jsonl` snippet, app version (e.g. 9.17.1.0), and SF case number in the description (`Case Owner - {name}` + case-number convention).
- OMNI Decimal-overflow retrievals: attach the register dump; reference ADO 1855354 before filing a duplicate.
- Schedule/laptop divergence with no clean signature → engage Field Apps + Professional Services (pattern of SF 24-00945917).
- Anything where the task syncs but FLOWCAL doesn't reflect it → wrong skill: use SKILL_FLOWCAL_Integrations_WebSync.md.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
