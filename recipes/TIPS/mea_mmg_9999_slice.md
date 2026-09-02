# Fix: MMG rerun leaves derived analysis open-ended 12/31/9999 (current month won't generate)

## Steps
1. Recognize the tell: TIPS end-of-time is **12/31/9000** — any derived weighted-average analysis time-slice ending **12/31/9999** is the bug state (a rerun of a prior production month created it, overlapping later analysis records and failing the current billing month). ADO #1435165 (rerun date-range), #1328845 (`DateTime.MaxValue.Date` 9999 slice), #1685847 (analysis meter generates nothing).
2. **Field-proven cleanup:** delete the bad `12/31/9999` timeslice on the derived (Master Meter Group) analysis, then **rerun MEASUREMENT** for the affected plant/month. Existing bad slices must be deleted/cleaned — the code fix only prevents new ones.
3. Ensure the Master Meter Group setup is valid and non-overlapping (Meter Group# / Analysis Meter# / Effective Start Date) — the #1685847 fix added a Web validation to block bad setups.
4. **Durable fix:** confirm the client build carries the fixes — #1435165 merged from 2020.03 forward across 2021.04/2021.10/2022.04/2022.10 (`MasterMeterGrpWghtAvgGasAnalyzer`), #1685847 in 2022.10/2024.04 (all inferred — confirm in release notes).

## Verification
- No analysis/timeslice row for the MMG derived meter ends 12/31/9999 (all open-ended slices end 12/31/9000).
- After rerunning MEASUREMENT, the current billing month generates a new weighted-average analysis for the Master Meter Group.

## Workaround
Delete the 9999 slice + rerun is both the workaround and the cleanup; until the client is on a fixed build, every prior-month MMG rerun can recreate the bad slice — re-check after each rerun.

## Source
SKILL_ADO_TIPS_Measurement_VolumeImport_FlowCal.md Cluster D (ADO #1435165 / SF 22-00220682, #1685847 / SF 24-00963716, #1328845); SKILL_TIPS_Measurement_Ticketing.md §6 (22-00869412, 22-00868194 — 12/31/9999 vs 12/31/9000 tell).
