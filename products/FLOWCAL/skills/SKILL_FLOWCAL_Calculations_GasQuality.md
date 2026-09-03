# SKILL — FLOWCAL Calculations, Gas Quality & Measurement Standards

> **Product family:** FLOWCAL (primary), TESTit / PROVEit (calc-adjacent)
> **Coverage plan group:** #7 — Calculations, gas quality & measurement standards (~4,900 family cases, ~365 actionable)
> **Sources:** Salesforce all-history mining (Product_list__c IN ('FLOWCAL','TESTit','PROVEit'), Case_Category__c IN ('Calculations','Source Quality','Gas Calculations','Meter Calculations') + keyword mining), ADO org `QuorumSoftware` (projects `Quorum`, `QuorumSoftware`; area paths `Quorum\North America\Measurement*`, `QuorumSoftware\Engineering\Measurement\Maintenance`). Mined 2026-09-02.
> **Auto-Bot** — the L4 issue solver built by **Aditya Bhagat**.
> Fixed-in versions are **INFERRED** from case resolutions unless marked release-notes-confirmed. PII redacted; client codes retained.

---

## 1. Quick Triage

| Symptom | Likely cause | § |
|---|---|---|
| AGA3-1992 volume/VCF differs ~10% from AGA3-2013 at identical conditions | Flow-time edit mishandled when meter configured for Calc from Extension (defect) | §3.1 |
| Volume calculates as zero/incorrect with bad temperature, AGA3-2013 + GPA 2172 + calc-from-extension, no exception raised | Missing out-of-AGA-limits exception handling (open defect) | §3.1 |
| VCF not calculated for no-flow records (AGA3-13) | Old defect, fixed 8.11.37.28 / 10.1.0.8 / 10.2.0 GA (I-09927) | §3.1 |
| Exception 1032 "AGA-8 Gross2 FPV calculation (N2 too low)" while FPV method is AGA-8 Detail (1992) | Wrong FPV routine invoked (defect, fixed 10.6.0.0) | §3.2 |
| GPA 2172 correction has no effect on AGA3-2013 meters (works on AGA3-1992) | Known incompatibility — GPA 2172 not applied to AGA3-2013 (open Feature 1788560) | §3.3 |
| GPA 2172 water correction skipped for some hours on a wet meter | Data-state issue; purge + re-import resolved | §3.3 |
| Severe slowness on GPA2172-enabled meters / point-to-point ops | Duplicate `fc_edit_reason` rows; SQL cleanup + fix in 10.6.0.18 / 10.8.0.9 / 10.9.0.1 | §3.3 |
| Meter recalculates ENERGY when GQ assignment is set to "recalc VCF" only | Defect family, fixed in 10.2.0.23 / 10.3 line | §3.4 |
| Repeating (stuck) heating value on meters using Send To feeding GQ source | 10.2.0.28 patch regression, fixed 10.2.0.29 | §3.4 |
| GQ heating values wrong right after upgrade | Version regression (e.g. 10.5.0.13 → fixed 10.5.0.16) | §3.4 |
| FVC "Frozen Heating Value" (exc 2060) regenerates immediately after acknowledge; generation time `00:00:01` | Defect, fixed 10.8.0.4 (ADO 1770409/1715831) | §3.4 |
| Source analysis shows 0.00 Dry/Wet/As-Deliv HV after TQ feed | `btu_base` (saturated condition) missing on inserted TQ records | §3.4 |
| "Number of Analysis Revisions has Exceeded Limit" / analyses applying multiple times per day | Defect, fixed 10.6.0.12+ | §3.5 |
| GQ source analyses overlapping / wrong `effective_end_date` (analysis import gaps, wrong apply) | Bad data in `fc_gq_source_analysis` — Dev correction SQL | §3.5 |
| New GQ Source Effective/Characterization Date defaults to 2017-02-01 | UI limitation; Ctrl+S workaround in Characteristic tab | §3.5 |
| VCF / standard volumes will not calculate on one meter | Meter characteristic revision anomaly (Rev 1 should be Rev 0) or version defect (10.6.0.18 fix) | §3.6 |
| VCF not calculated when accepting an AutoEdit | Defect — blocks analysis apply until forced recalc | §3.6 |
| Coriolis meter not recalculating on GQ assignment | Missing density-of-air in analysis (config/data, Coriolis-only) | §3.6 |
| MCF/MMBTU gas-equivalents from NSV bbl wrong (incl. ethylene) | Defect family, fixed 10.7 / 10.8 | §3.6 |
| Floating Roof Adjustment calculation wrong | Defect, fixed 10.6 | §3.6 |
| CALCit won't launch / "not authorized" | Almost always CrypKey/site-key licensing — route to Licensing skill (group #5) | §6 |

## 2. Decision Tree

```
Calculation/GQ complaint
├─ Is the complaint a STANDARDS discrepancy (AGA/API/GPA number mismatch vs independent calc)?
│   ├─ AGA3 1992-vs-2013 delta, calc-from-extension meter → §3.1 (ADO 1785281 family)
│   ├─ FPV/Z-method exception or FPV factor wrong → §3.2
│   └─ GPA 2172 applied/not applied or water correction → §3.3
├─ Is it a HEATING VALUE / ENERGY symptom?
│   ├─ Energy recalculated when only VCF recalc requested → §3.4 (fixed ≥10.2.0.23)
│   ├─ HV stuck/repeating, wrong after upgrade, zeros after TQ feed → §3.4
│   └─ FVC frozen-HV exception loop → §3.4 (fixed 10.8.0.4)
├─ Is it GQ SOURCE data (assignments, analyses, revisions)?
│   └─ §3.5 — check fc_gq_source_analysis integrity FIRST (overlaps/end-dates), then version
├─ Is it LIQUIDS / VCF / density / equivalents?
│   └─ §3.6 — check meter characteristic revisions (Rev 0/Rev 1) and analysis completeness
│      (air density for Coriolis, relative density per hour) before suspecting code
└─ Version gate reminder (G3): most confirmed defects here are already fixed —
   compare client build against the fixed-in versions before escalating to code (G5).
```

Gate mapping: standards discrepancies land G5 (code) or G3 (already fixed); GQ-source data issues are usually G4 (bad data) with a correction script; date-default and BLM-uncertainty items are G1 (expected behavior/doc gap).

---

## 3. Symptom Clusters

### §3.1 AGA-3 volume calculation discrepancies (1992 vs 2013, Calc from Extension)

**Signature.** Client compares FLOWCAL against an independent orifice calculator: AGA3-2013 matches nearly exactly, but AGA3-1992 differs ~10% at the same flowing conditions where API 14.3.4 Table 7 says the delta should be <0.01. All rows using AGA-8 Detail (2017) Z-method. (SF 25-01047622 description, verbatim symptom.)

**Root cause (CONFIRMED).** ADO Bug **1785281** "AGA 3 1992 Calculations Incorrect (DEV)" (QuorumSoftware\Engineering\Measurement\Maintenance, Closed 2026-06): engineering TLDR — *"The only issue with AGA-3 1992 was the edit of flow time when configured for Calc from Extension."* Editing flow time on a Calc-from-Extension meter corrupted the 1992-method recalc. A dev note (MMB 2/25/2026) also flags negative-value handling in extension recalculation for review.

**Fix recipe.**
1. Confirm meter Calc Method = AGA3-1992 and the characteristic uses "Calc from Extension"; ask whether flow time was edited on the affected records.
2. Repro (from ADO 1811577, FLOWCAL 10.5.0.5): create orifice meter, Z Method = AGA 8 Detail (2017), set Calc Method AGA3-13 on one span and AGA3-92 on another, import identical flow data, compare hour-pair VCFs — deltas > 0.01 confirm.
3. DEV-branch fix closed (1785281); R1060 port **1811576** still New/Escalated at mining time — check its state for the client's release line before promising a build. Fixed-in build: **INFERRED ≥ 10.9-era maintenance** — verify against release notes.
4. Workaround used by clients: run the affected meters on AGA-8 Detail 2017 / AGA3-2013 until patched.

**Related open defect — bad temperature, no exception.** ADO **1785773** / migrated copy **1811580** "Incorrect Volume Calc with Bad Temp FLOWCAL using AGA3-2013 with GPA 2172 and calc from extension enabled": with an out-of-limits temperature, AGA3-2013 records recalc to zero/incorrect volume and *no exception is generated*; expected behavior is an out-of-AGA-limits exception. AGA3-1992 on the same data recalculates non-zero. Track 1785773 (State New at mining).

**No-flow records (legacy).** VCF not calculated for no-flow records on AGA3-13: SF **22-00636066** — fixed with **I-09927** in 8.11.37.28, ported to 10.1.0.8 and 10.2.0 GA (resolution verbatim). Companion SF **22-00588593** (AGA2013 no-flow) resolved in 8.11.37.29.

**Not fixed / deferred.** SF **24-00962394** "Master Characteristic Calc Method AGA3-2013 (factor options)" — closed-deferred by product ("no time frame for delivering a fix… will consider it for future cycles").

**Anchors:** SF 25-01047622, 25-01054979 (Howard Midstream, dup), 22-00636066, 22-00588593, 24-00962394 · ADO 1785281, 1811579, 1811576, 1811577, 1785773, 1811580.

### §3.2 AGA-8 / FPV (Z-method) issues

**Signature.** Exception **1032** "AGA-8 Gross2 FPV calculation (N2 too low)" raised on meters whose FPV method is **AGA-8 Detail (1992)** — i.e., a Gross-2 range check firing under the Detail method.

**Root cause (CONFIRMED).** SF **23-00893138** resolution: defect logged as **ADO 1590047** ("23-00893138--Exception 1032 questions (Dev*)", Bug, Closed, area `QuorumSoftware\Engineering\Measurement\Maintenance`); resolved for the **FLOWCAL 10.6.0.0 GA** release (INFERRED from case resolution).

**Fix recipe.**
1. Verify FPV method on the meter characteristic vs the exception text — mismatch (Detail configured, Gross-2 exception) confirms this defect.
2. Interim workaround (from the case): switch FPV calculation method to AGA-8 Gross 2 — exception clears.
3. Permanent: upgrade to ≥ 10.6.0.0.

**Related.** SF **22-00804875** "FPV Factor / Volumes being recalculated incorrectly" (Software Defect, 2022 — 10.2 era). FPV method enum vocabulary (useful when reading evs-measurement migration data, ADO Task **1805151**): `Nx19=1, Aga8_Gross1_1992=2, Aga8_Gross2_1992=3, Aga8_Detail_1992=4, FpvOne=5, Aga8_Gross1_2017=6, Aga8_Gross2_2017=7, Aga8_Detail_2017=8, Aga8_Gerg_2017=9`; CalcMethod enum: `Liquid=1, Aga3_1985=2, Aga3_1992=3, Aga7=4, Vcone=5, Coriolis=6, Iso5167_2003=7, Aga3_2013=8`.

**Anchors:** SF 23-00893138, 22-00804875 · ADO 1590047, 1805151.

### §3.3 GPA 2172 application (water correction, energy) & GPA-meter performance

**Signature A — GPA 2172 ignored on AGA3-2013.** Two meters identical except "Apply GPA 2172-09 = Yes": on AGA3-**1992** the corrected meter shows lower volume/energy (correction applied); on AGA3-**2013** both meters show identical values — GPA 2172 has no effect.

**Root cause (CONFIRMED).** ADO **1788560** "Remediate Compatibility Between AGA-3 (2013) and GPA-2172 (2025)" (Feature, state Develop at mining; converted from Bug): *"the GPA 2172 calculation is not applying to AGA3-2013 calculation."* Reporting customers: ETE Non-Regulated, Cimarex, Chevron; source cases include SF 24-00950445 and SF **23-00932955** ("ETE Non Regulated - GPA 2172 Issue"). No fixed-in version at mining time — treat as open; check 1788560 state per case.

**Signature B — water correction skipped hours (wet meter).** SF **22-00551850**: GPA 2172 water correction not applied for all hours. Not reproducible in-house; resolved by **purge + re-import** of the affected data — treat as G4 bad data first.

**Signature C — GPA2172-enabled meters slow.** SF **26-01118526** "Slow Performance on GPA2172 enabled meters": investigation confirmed *excessive duplicate Edit Reason records* inflating point-to-point processing time. Fix: SQL cleanup of duplicate `fc_edit_reason` rows (retain the valid entries) + upgrade to **10.6.0.18 / 10.8.0.9 / 10.9.0.1**, which contain the duplicate-Edit-Reason fix (resolution verbatim). Related generator defect: ADO **1839778** "Liquids Meter CFX File Import Service Issue (R1090 PORT)" — CFX import creating an edit reason for every record in the month even when data unchanged (case 26-01082401, EQT); also a PK violation on meter periodic values in 10.8.

**GPA 2172 tab vocabulary** (Volume Editor › Span Edit › Analyses GPA 2172; from ADO 1116244 repro): `Flowing Gas Condition` (e.g. Partially Saturated @ Flowing Conditions, Sat @ Base), `Apply GPA 2172-09` (Yes/No), `Reporting Condition`, `EFM Rel. Density Condition`. System-wide defaults live in System Factors (Base pressure, Heating value condition).

**Anchors:** SF 23-00932955, 24-00950445, 22-00551850, 26-01118526, 26-01082401 · ADO 1788560, 1839778, 1116244.

### §3.4 Heating value & energy recalculation (GQ apply chain)

**Signature A — energy recalculated when only VCF requested.** GQ assignment set to "recalc VCF", but meters recalculate ENERGY too (TQ-processed records included). Cases: SF **22-00549996** (client ref FC-1935965), **22-00586264** (ONEOK, 10.0.1.0), **22-00558532** / **22-00824309** (10.2.0.17, TQ records), **22-00558530** (Coriolis meters). Fixes (INFERRED from resolutions): 22-00586264 "Fixed in 10.2.0"; 22-00824309 "resolved as of 10.2.0.23"; 22-00549996 confirmed clean in 10.3. Rule of thumb: **any 10.2.0.17-era client reporting energy churn on VCF-only recalc → version issue, fixed ≥ 10.2.0.23.**

**Signature B — repeating heating value with Send To.** After upgrading 10.2.0.24 → 10.2.0.28, meters using the **Send To** function (meter analysis feeding a GQ source) copy over one repeating HV even though TQ shows the HV changing hourly. SF **24-00954826** (Energy Transfer; meter + GQ source pair in case). **Fixed in 10.2.0.29** (resolution verbatim). Historic sibling: ADO **1448541** "Analysis Chromatograph - Meter is applying incorrect quality after purge/reimport (R1020* PORT)" — `heat_value_wet` drift after work item 1375046; behavior depends on System Config › **"Do Not Extend Source Analysis on Import"** because Send To performs an implicit source import.

**Signature C — GQ HVs wrong after upgrade.** SF **24-00987592**: GQ heating values wrong after upgrading to 10.5.0.13; resolved by shipping **10.5.0.16**. Generic play: when HVs shift right after a patch, diff patch notes before touching data.

**Signature D — FVC "Frozen Heating Value" exception loop.** Acknowledge the pending FVC exception, run validation/save in Volume Editor → a NEW unresolved FVC exception appears at the same timestamp; affected exceptions share generation time **"00:00:01"**. SF **26-01088112** — **fixed 10.8.0.4**. ADO **1770409** (DEV, Closed) + **1715831** (R1080* PORT, Closed) "Exception gets regenerated after acknowledged"; repro data from case 25-01004221 (TORY Tech, meter ARGOS). Exception catalog: **2060 = FVC - Frozen heating value** (`fc_exception_description`). Older sibling: SF 22-00589966.

**Signature E — zeros fed to source from TQ.** Source Analysis › Gas Quality shows 0.00 Dry/Wet/As-Deliv HV after transaction-queue feed. ADO **1113038** (R8.11): TQ-inserted records lacked **`btu_base`** (saturated condition), so **`avg_btu`** (measured HV) was never assigned to Dry/Wet/As-Delivered; resolution logic: if btu_base missing, infer from H2O value / set As Delivered when water present. Workaround used: Toolbox › apply meter analysis to the source. If a modern case shows the same zeros, check the import feed populates btu_base.

**Signature F — rollup/final-form gaps.** Dry & Wet HV not rolling up: SF **22-00598311**, fixed 10.2.0.14. Heating Value Dry not populated in final-form tables: SF **22-00814897**, fixed 8.11.37.28.

**Also in this family:** monthly mole % > 100 (SF **22-00824689**, fixed 10.5.0.4); flow-weighted average wrong with null values (SF **23-00923945**, fixed 10.2.0.25); C5+ totaling incorrect (SF **22-00830937**, no recorded resolution); HV computed from mole % wrong on screen — HC Properties table display bug, Dev supplied an update SQL (SF **22-00672286**); calculated-meter HV wrong (SF 22-00621485 defect-era; SF 26-01100266 and 26-01088704 resolved as configuration — check the calc-meter formula/GQ source before filing a bug).

**Anchors:** SF 22-00549996, 22-00586264, 22-00558530, 22-00558532, 22-00824309, 24-00954826, 24-00987592, 26-01088112, 25-01004221, 22-00589966, 22-00598311, 22-00814897, 22-00824689, 23-00923945, 22-00830937, 22-00672286, 22-00621485, 26-01100266, 26-01088704 · ADO 1448541, 1113038, 1770409, 1715831, 1375046 (ref).

### §3.5 GQ source data integrity (assignments, analyses, revisions)

**Signature A — corrupted analysis end-dates.** GQ source analyses with wrong/overlapping `effective_end_date`/`duration` (symptoms: analysis gaps, wrong analysis applied, import anomalies). SF **24-00937105** (NNG, FlowCal 10.0.3.1, Oracle) — Dev-team correction SQL (see §5 verbatim). Two GQ sources at the client had the corruption; script fixed both.

**Signature B — revision-limit exceptions.** "Number of Analysis Revisions has Exceeded Limit" when a crude/gas analysis applies multiple times per day instead of once. SF **25-01023659** — **fixed 10.6.0.12 and higher** (resolution verbatim). Related churn: SF 22-00820032 "High Revision Count Issue"; the "excessive revision issue" is also name-checked in SF 24-00954826. Batch side-effect sibling: ADO **1317758** "Batches are not created after importing analysis - round 2 (R1020)".

**Signature C — new-source date defaults.** New GQ Source Effective Date & Characterization Date default to 2017-02-01 (FC 10.5.0.14). SF **24-00990548** — expected behavior + workaround: create source, Edit › Characteristic tab › white-page icon on From date › select From field › **Ctrl+S** (begin-of-time) or type the date. Characterization Date is auto-calculated (analysis "age" used for interval-approaching warnings) and cannot be edited — per Dev, an FYI value, not BLM-required.

**Signature D — historical assignments missing.** Historical GQ source assignments absent for some facilities (validation vs legacy system). SF **25-01034526**, **25-01034631** — both closed as Application Configuration (migration/config, not code). Check assignment effective ranges before suspecting a defect.

**Exception catalog for this cluster** (`fc_exception_description`, ADO 1208907 8.11.36 upgrade script): 55 "GQ Source Assignment Missing", 56 "Default GQ Source Assigned", 61 "GQ Source Record Marked As Inhibited", 15201/15202/15203 "GQ Apply conversion not possible" (HV condition / pressure base / heating value), 15209 unit-set discrepancy, 100000 "GQ Source Assignment error: stack overflow in assignment/recalc process".

**Also:** GQ Editor errors creating new sources (SF 24-00960411, DB error); 10.6.0.0 source-quality regression fixed 10.6.0.3 (SF 24-00966320); un/inhibit error resolved as config (SF 23-00934189); GQ Editor "Accumulated" behavior — engineering declined change (SF 24-00948197, expected behavior).

**Anchors:** SF 24-00937105, 25-01023659, 22-00820032, 24-00990548, 25-01034526, 25-01034631, 24-00960411, 24-00966320, 23-00934189, 24-00948197 · ADO 1317758, 1208907.

### §3.6 Liquids & meter-level calc failures (VCF/CTL, S&W, density, gas equivalents)

**Signature A — VCF/standard volumes won't calculate on one meter.** First check `fc_meter_characteristics` revisions: SF **25-01059943** — most recent characteristic record was **Rev 1 where Rev 0 was expected**, starting at the no-flow timestamp and running to end-of-time; fix = purge the data covering that range (resolution verbatim; entry cause not reproduced). If many meters affected on 10.6.x: SF **25-01004345** — defect **fixed 10.6.0.18**. Calculated meters not calculating at all: SF **24-00995430** — **fixed 10.6.0.5**.

**Signature B — VCF not calculated on accepting AutoEdit.** SF **24-00976883**: accepted autoedit leaves VCF null, which then blocks analysis apply and further edits until a forced recalc. Software Defect (no fixed-in recorded — check current release notes). Related config-flavored: autoestimated data + VCF (SF 25-01006126, App Config); "Can't recalculate VCF" resolved via workaround (SF 23-00884608).

**Signature C — Coriolis specifics.** IV calculation error on Coriolis meter: SF **23-00906252** — **fixed 10.5.0.3**. Coriolis GQ assignment not recalculating: SF **24-00982676** — missing **density of air** in the analysis was the blocker; air density affects **only Coriolis meters** (resolution verbatim). Raw-volume exception reset: SF 25-01021218 (resolved in later version, INFERRED).

**Signature D — S&W and tickets.** Sediment & water volume not calculating: SF **22-00831458**; S&W wrong on 10.2.0.10 persisting into 10.3.0.5: SF **22-00600284**; truck tickets/S&W issues: SF **23-00898785**. No definitive fixed-in captured — treat as G5 candidates with ticket-level repro.

**Signature E — gas equivalents (MCF/MMBTU from NSV bbl).** Meter configured to derive MCF/MMBTU equivalents from entered barrels computes them wrong: SF **23-00925076** — **resolved in 10.8**; ethylene gas-equivalent error SF **25-01008366** is the same family ("related to 23-00925076"), fix shipped in **10.7** (resolutions verbatim; the two versions reflect different sub-fixes — verify per release notes).

**Signature F — tank calcs.** Floating Roof Adjustment calculation wrong: SF **24-00975619** + **22-00558091** — **fixed in 10.6** ("Chevron will need to upgrade to 10.6"). GEV doesn't roll up for tanks: SF 22-00635505.

**Also:** density issues (SF 24-00936682); Mass % not always calculated — relative density missing on scattered hours, two meters on the same GC diverging (SF **25-01047045**, no recorded resolution; check GC feed completeness per hour); calc meter negative-volume handling (SF 22-00662173, 22-00635519).

**Anchors:** SF 25-01059943, 25-01004345, 24-00995430, 24-00976883, 25-01006126, 23-00884608, 23-00906252, 24-00982676, 25-01021218, 22-00831458, 22-00600284, 23-00898785, 23-00925076, 25-01008366, 24-00975619, 22-00558091, 22-00635505, 24-00936682, 25-01047045, 22-00662173, 22-00635519.

---

## 4. Known ADO Items (verbatim IDs)

| ADO | Type/State (at mining) | Title / relevance |
|---|---|---|
| 1785281 | Bug, Closed | AGA 3 1992 Calculations Incorrect (DEV) — root cause: flow-time edit + Calc from Extension |
| 1811576 | Bug, New (Escalated) | AGA 3 1992 Calculations Incorrect (R1060* PORT) |
| 1811577 | Bug, New (Duplicate) | AGA3-1992 Calculation Error (Howard Midstream 25-01054979; full repro steps) |
| 1811579 | Bug, New | AGA 3 1992 Calculations Incorrect (DEV) — Migrated-from-QS copy |
| 1785773 | Bug, New | Incorrect Volume Calc with Bad Temp, AGA3-2013 + GPA 2172 + calc-from-extension |
| 1811580 | Bug, Closed | Same as 1785773 (Migrated-from-QS copy) |
| 1788560 | Feature, Develop | Remediate Compatibility Between AGA-3 (2013) and GPA-2172 (2025) |
| 1590047 | Bug, Closed | Exception 1032 (AGA-8 Gross2 FPV N2-too-low under Detail 1992) — fixed 10.6.0.0 |
| 1770409 | Bug, Closed | Exception gets regenerated after acknowledged (DEV) — FVC frozen HV loop |
| 1715831 | Bug, Closed | Exception gets regenerated after acknowledged (R1080* PORT) |
| 1317758 | Bug, Closed | Batches not created after importing analysis - round 2 (R1020) — exc 2060 context |
| 1113038 | Bug, Closed | Meter Analysis not applying to source (R8.11) — missing btu_base → zero HVs |
| 1448541 | Bug, Closed (Duplicate) | Analysis Chromatograph — wrong quality after purge/reimport; heat_value_wet drift post-1375046 |
| 1116244 | Bug, Closed | Volume Editor load performance (GPA 2172 span-edit repro; fc_log_sql_performance) |
| 1839778 | Bug, Acceptance | Liquids Meter CFX Import — excessive edit reasons / PK violation (R1090 PORT) |
| 1805151 | Task, New | Legacy CalcMethod/FpvMethod enum preservation (evs migration vocab) |
| 1208907 | Task, Closed | fc_exception_description text catalog (8.11.36 upgrade script) |

Port convention observed: same defect exists as `(DEV)` + `(R10x0* PORT)` twins, and 2026+ items carry `Migrated-from-QS` copies in project `Quorum` — always check all twins' states before declaring "fixed".

## 5. Diagnostic SQL

Environment note: scripts below came from Oracle-based client DBs (`alter session set nls_date_format`); adapt date handling for SQL Server sites. Label results INFERRED for client-PRD unless run live.

**5.1 GQ source analysis end-date/duration repair (Dev-authored, SF 24-00937105 — replace source number and cutoff date per case; take backups first):**
```sql
alter session set nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
update fc_gq_source_analysis outer
set effective_end_date = (select min(effective_date) from fc_gq_source_analysis
                          where gqsource_index = outer.gqsource_index
                            and effective_date > outer.effective_date and sequence_number = 0)
where gqsource_index = (select gqsource_index from fc_gq_source where gqsource_number = '<GQ_SOURCE_NO>')
  and effective_date >= '<CUTOFF mm/dd/yyyy hh24:mi:ss>' and sequence_number = 0
  and effective_date <> (select max(effective_date) from fc_gq_source_analysis
                         where gqsource_index = outer.gqsource_index);

update fc_gq_source_analysis outer
set duration = fc_timestamp(effective_end_date) - fc_timestamp(effective_date)
where gqsource_index = (select gqsource_index from fc_gq_source where gqsource_number = '<GQ_SOURCE_NO>')
  and effective_date >= '<CUTOFF>' and sequence_number = 0
  and effective_date <> (select max(effective_date) from fc_gq_source_analysis
                         where gqsource_index = outer.gqsource_index);
commit;
```

**5.2 Duplicate edit-reason detection (from ADO 1839778 repro; supports §3.3-C slowness):**
```sql
alter session set nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
select * from fc_edit_reason
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<METER_NO>')
  and gms_date > sysdate - 0.1;
-- Symptom: a fresh edit reason for EVERY record in the month when only a subset of hours changed.
```

**5.3 SQL performance tracing (client-side, from ADO 1116244):** add to `FcDebugOptions.cfg` under the user's section: `fc_log_sql_performance=Y`, then rerun the slow operation and review the log (hot tables seen: FC_GQ_HC_PROPERTY, FC_UNIT_CONVERSION, FC_COMBO_BOX_ITEM, FC_DAYLIGHT_SAVINGS_TIME).

## 6. Expected-Behavior FAQ

- **BLM Heating Value Uncertainty values don't match the Help-doc example** (BLM Property = Yes, FMP Tier = Very High Volume, ±1% limit; exception "Heating value uncertainty exceeds designated limit"): SF 24-00962837 closed without a defect — the Help example is dated relative to the current uncertainty computation. Ask product for the current formula rather than filing a calc bug.
- **Characterization Date can't be edited**: auto-calculated "analysis age" used to warn when the re-characterization interval approaches; FYI value, not BLM-required (SF 24-00990548, Dev statement).
- **GQ Editor "Accumulated" behavior**: change request declined by engineering (SF 24-00948197) — expected behavior.
- **Density of air matters only for Coriolis meters** (SF 24-00982676) — reassure clients other meter types are unaffected.
- **New GQ Source dates defaulting to 2017-02-01**: by design at creation; use the Edit › Characteristic › From-date + Ctrl+S workaround (SF 24-00990548).
- **CALCit "not working"/"not authorized"**: overwhelmingly CrypKey site-key/licensing (SF 26-01113746, 22-00554416 et al.), not a calculation defect — route to the Licensing & CrypKey skill.

## 7. Escalation Guidance

1. **Version gate first (G3):** this family is dense with already-fixed defects — key fixed-in ladder (all INFERRED from case resolutions unless noted): 8.11.37.28/.29 (no-flow VCF, HV-dry final form) → 10.2.0.14 (HV rollup) → 10.2.0.23 (energy-on-VCF-recalc) → 10.2.0.25 (FWA nulls) → 10.2.0.29 (Send-To HV) → 10.5.0.3 (Coriolis IV) → 10.5.0.4 (mole%>100) → 10.5.0.16 (GQ HV post-10.5.0.13) → 10.6.0.0 (Exception 1032) → 10.6.0.3 (GQ 10.6.0.0 regression) → 10.6.0.5 (calc meters) → 10.6.0.12 (revision limit) → 10.6.0.18/10.8.0.9/10.9.0.1 (duplicate edit reasons; also 10.6.0.18 VCF/std-vol) → 10.7/10.8 (gas equivalents) → 10.8.0.4 (FVC exception loop).
2. **Escalate to Measurement engineering** (area `Quorum\North America\Measurement\Maintenance`, or `...\Field Apps and API` for TESTit/PROVEit calc issues) when a standards-number discrepancy survives: (a) independent-calculator comparison attached, (b) meter characteristic + analysis snapshot, (c) FcDataBoss export of the meter — every closed calc bug above shipped with exactly that package.
3. **Open items to watch before filing new bugs:** 1788560 (GPA2172-on-AGA3-2013), 1785773 (bad-temp no-exception), 1811576 (AGA3-1992 R1060 port), 1839778 (edit-reason generator). File ports against the client's release line; note the `(DEV)`/`(R#### PORT)` twin convention.
4. **PROVEit/TESTit calc questions** (CTL/CPL on proving reports — e.g. SF 25-01004767; prover expansion coefficients Ga/Gl/Gc, API 12.2) route to the Field Operations skill (group #13) unless the number itself is produced by FLOWCAL.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
