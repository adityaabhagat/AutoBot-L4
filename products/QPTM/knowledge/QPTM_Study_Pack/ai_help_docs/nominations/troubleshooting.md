---
title: Nominations (NOM) - Troubleshooting Guide
category: troubleshooting
feature: Nominations (NOM)
related_repos: Web, Batch
keywords: nomination errors, validation failure, submission failed, cycle closed, MDQ exceeded, contract invalid, FK error, override, nomination troubleshooting
last_updated: 2026-03-03
---

# Nominations (NOM) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Nomination issues in QPTM Web. It covers common errors, diagnostic queries, root cause analysis patterns, and historical issue references.

For business concepts, see [Domain Documentation](./domain.md).
For technical implementation, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Common Validation Errors](#common-validation-errors)
3. [Submission Failures](#submission-failures)
4. [Cycle and Timing Issues](#cycle-and-timing-issues)
5. [Quantity and Calculation Issues](#quantity-and-calculation-issues)
6. [Error Override Issues](#error-override-issues)
7. [API Nomination Issues](#api-nomination-issues)
8. [Autogeneration Issues](#autogeneration-issues)
9. [Performance Issues](#performance-issues)
10. [Diagnostic SQL Queries](#diagnostic-sql-queries)
11. [Key Code Locations for Debugging](#key-code-locations-for-debugging)
12. [Historical Issues](#historical-issues)

---

## Quick Diagnostic Checklist

When investigating a nomination issue, check these in order:

1. **What TSP, gas day, cycle, and service requester?** - Get specific parameters
2. **Is the cycle open?** - Check cycle status for the gas day
3. **Is the contract valid?** - Verify contract exists and is active for the date range
4. **Are locations valid?** - Check receipt and delivery locations are active
5. **What validation errors?** - Query NNCTRL_NOM_DTL_ERR for specific error codes
6. **What's the nomination status?** - Check NomStatCode in NNCTRL_NOM_DTL
7. **Were there recent code/config changes?** - Check rule cache, global configs

---

## Common Validation Errors

### Issue 1: Foreign Key Validation - Contract Not Found

**Symptoms:**
- Error: "Foreign Validation: The Contract does not exist or is not valid for the current record"
- Validation stops at FK level (level 2)
- NomStatCode = "VALD"

**Root Cause:**
- Contract expired or not yet effective for the gas day
- Contract number mistyped or doesn't exist
- Contract not configured for the TSP

**Investigation Steps:**
1. Verify contract exists in KCTRL_CTR_* tables
2. Check contract effective/expiration dates vs. nomination gas day range
3. Check ContractCache for stale data

**Resolution:**
```sql
-- Check contract validity
SELECT CTR_NO, EFF_DATE, EXP_DATE, TOS_CD, STATUS_CD
FROM KCTRL_CTR_HDR
WHERE TSP_NO = @TspNo
  AND SR_CTR_NO = @SrCtrNo;
```

**Code Reference:** `RuleNNFK000010` in `Quorum.QPTM.Validations.Rules.Nomination/ForeignKey/`

---

### Issue 2: Foreign Key Validation - Location Invalid

**Symptoms:**
- Error referencing receipt or delivery location
- Validation stops at FK level

**Root Cause:**
- Location not active for the gas day
- Location not configured for the TSP
- Location ID changed or deactivated

**Investigation Steps:**
1. Query location table for effective dates
2. Verify location is nominatable (NOM attribute)
3. Check if location was recently deactivated

**Resolution:**
```sql
-- Check location validity
SELECT LOC_ID, LOC_NM, EFF_DATE, EXP_DATE, STATUS_CD
FROM PACTRL_LOC
WHERE TSP_NO = @TspNo
  AND LOC_ID IN (@IdRecLoc, @IdDelLoc);

-- Check location attributes
SELECT LOC_ID, ATTR_TYPE_CD, ATTR_VALUE
FROM PACTRL_LOC_ATTR
WHERE TSP_NO = @TspNo
  AND LOC_ID IN (@IdRecLoc, @IdDelLoc)
  AND ATTR_TYPE_CD = 'NOM';
```

**Code Reference:** `RuleNNFK000020`-`RuleNNFK000060` in `ForeignKey/`

---

### Issue 3: Line Validation - Contract Not Valid Across Gas Days

**Symptoms:**
- Error: Contract not valid for all days in nomination range
- Nomination spans multiple gas days but contract expires mid-range

**Root Cause:**
- Contract expiration date falls within the nomination's BegGasDay-EndGasDay range
- Contract amendment changes effective in the middle of the nomination range

**Investigation Steps:**
1. Check contract effective/expiration vs. nomination date range
2. Look for contract amendments that change dates
3. Verify if contract has been renewed

**Resolution:**
- Split the nomination at the contract expiration boundary
- Or extend/renew the contract

**Code Reference:** `RuleNN00003010` in `LineRules/`

---

### Issue 4: Business Validation - MDQ Exceeded

**Symptoms:**
- Error indicating total delivery nominations exceed contract Maximum Daily Quantity
- Business validation level (level 5) error
- NomStatCode = "INVL"

**Root Cause:**
- Sum of all delivery nominations for a contract on a gas day exceeds MDQ
- K-contract MDQ calculation returning unexpected values
- Multiple activities submitted for same contract/gas day

**Investigation Steps:**
1. Sum all nominations for the contract on the gas day
2. Compare against contract MDQ
3. Check if K-contract (energy-based) MDQ calculation is correct
4. Look for nominations in other activities for the same contract

**Resolution:**
```sql
-- Check total nominated vs. MDQ
SELECT n.SR_CTR_NO,
       SUM(n.DEL_QTY) AS TotalDelQty,
       c.MDQ_QTY
FROM NNCTRL_NOM_DTL n
JOIN KCTRL_CTR_HDR c ON n.TSP_NO = c.TSP_NO AND n.SR_CTR_NO = c.SR_CTR_NO
WHERE n.TSP_NO = @TspNo
  AND n.BEG_GAS_DAY = @GasDay
  AND n.SR_CTR_NO = @SrCtrNo
  AND n.NOM_STAT_CODE NOT IN ('DEL')
GROUP BY n.SR_CTR_NO, c.MDQ_QTY;
```

**Code Reference:** `RuleNN00003060` in `BusinessRules/`

---

### Issue 5: Security Validation - User Not Authorized

**Symptoms:**
- Validation fails at security level (level 1)
- User cannot submit nominations

**Root Cause:**
- User doesn't have the required security object
- User ID mismatch between session and nomination record

**Investigation Steps:**
1. Check user's security assignments
2. Verify the security object IDs (NominationMaintenance, QVpSOANominationSubmission, etc.)
3. Check if user's BP association is correct

**Code Reference:** `RuleNNSEC00010` in `SecurityRules/`

---

### Issue 6: Path Validation Errors

**Symptoms:**
- Errors about path mismatch or invalid path
- PNT model nomination with incorrect path setup

**Root Cause:**
- Nomination path doesn't match contract default path
- Missing upstream or downstream component in PNT model
- Path balance issue: Receipt Total ≠ Delivery Total + Fuel

**Investigation Steps:**
1. Check contract path configuration
2. Verify PNT model balance: RecTotal = DelTotal + Fuel
3. Check if all path segments are valid

**Code Reference:** `RuleNN00003100`-`RuleNN00003115` in `BusinessRules/`, `PathValidator` in `Helpers/`

---

## Submission Failures

### Issue 7: Submission Fails After Validation Passes

**Symptoms:**
- Nominations validate successfully but submission fails
- Error during database persistence

**Root Cause:**
- Concurrency conflict (another user modified same nominations)
- Database constraint violation
- Transaction timeout

**Investigation Steps:**
1. Check `LastQueryDate` - nominations may be stale
2. Look for database deadlocks in SQL Server logs
3. Check if another submission was made between validate and submit
4. Verify `concurrencyGasDay` parameter

**Resolution:**
- Re-retrieve nominations and re-validate before submitting
- Check for concurrent access patterns

**Code Reference:** `SubmitNominations()` in `QPTMNominationService.cs`

---

### Issue 8: Submit by Contract Mode Issues

**Symptoms:**
- Some contracts submit but others don't
- Partial submission with errors on some contracts

**Root Cause:**
- `DisableNomSubmissionByContract` config setting
- `FilterOutErrorNominationsByContract()` filtering logic
- Business errors on specific contracts preventing their submission

**Investigation Steps:**
1. Check `DisableNomSubmissionByContract` global config
2. Review which contracts have errors vs. which were submitted
3. Check `BLOCK_BI_NOM_SUBMISSION` setting

**Code Reference:** `SubmitNominations()` in `QPTMNominationService.cs`

---

### Issue 9: Set ID Assignment Issues

**Symptoms:**
- `idSetAdd` or `idSetModify` is null after submission
- Nominations submitted but set IDs not returned

**Root Cause:**
- No new nominations (all modifications) or no modifications (all new)
- Database sequence issue

**Investigation Steps:**
1. Check if nominations are Added vs. Modified status
2. Verify set ID generation logic

---

## Cycle and Timing Issues

### Issue 10: Cycle Closed - Cannot Submit

**Symptoms:**
- Error: Cycle is closed for the gas day
- Submission rejected due to deadline

**Root Cause:**
- Nomination submitted after cycle deadline
- Gas day calculation incorrect (TSP start time mismatch)
- ENS vs. NAESB cycle confusion

**Investigation Steps:**
1. Check cycle deadlines for the TSP and gas day
2. Verify current gas day calculation with TSP preferences
3. Check if ENS cycles are enabled and which cycle the user is targeting

**Resolution:**
```sql
-- Check cycle status
SELECT CYCLE_ID, CYCLE_NM, DEADLINE_DT, IS_OPEN
FROM PACTRL_CYCLE
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND DEADLINE_CATEGORY = 'NOM';
```

**Code Reference:** `GetCycleStatus()`, `GetFirstNomOpenCycle()` in `QPTMNominationService.cs`

---

### Issue 11: Wrong Gas Day Calculated

**Symptoms:**
- Nominations appearing on wrong gas day
- Current gas day doesn't match expected

**Root Cause:**
- TSP gas day start time configuration
- Timezone differences
- Gas day offset parameter incorrect

**Investigation Steps:**
1. Check TSP preferences for gas day start time
2. Verify `GetCurrentGasDay(tspNo, gasOffset)` logic
3. Check server timezone vs. TSP timezone

**Code Reference:** `GetCurrentGasDay()` in `QPTMNominationService.cs`

---

## Quantity and Calculation Issues

### Issue 12: KMDQ Calculation Incorrect

**Symptoms:**
- K-contract MDQ showing wrong values
- Energy-based quantities not matching expected

**Root Cause:**
- Contract UOM type (ENG vs. VOL) mismatch
- Heating factor calculation error
- MSQ/MDWQ/MDIQ values not populated

**Investigation Steps:**
1. Verify contract UOM type (`MdqUomCode`)
2. Check heating factors on receipt locations
3. Verify `CalculateKMDQ()` input data

**Code Reference:** `CalculateKMDQ()` in `QPTMNominationService.cs`

---

### Issue 13: Fuel Calculation Errors

**Symptoms:**
- Fuel quantity incorrect
- Fuel percentage not applied
- PNT balance fails due to fuel

**Root Cause:**
- Fuel preference code misconfigured
- Fuel override flag (IsFuelOvrd) not set correctly
- Location-level fuel percentage not configured
- Contract-level fuel TOC not set

**Investigation Steps:**
1. Check fuel preference configuration for the contract/location
2. Verify `FuelPrefCode` and `FuelTocCode` values
3. Check if user has `ALLOW_USER_OVRD_FUEL` permission
4. Verify `CalculateRecHeatingFactors()` output

---

### Issue 14: EPSQ Calculation Issues

**Symptoms:**
- Evening Peak Scheduled Quantity not calculated
- EPSQ values incorrect

**Root Cause:**
- `SHOW_K_QUANTITIES_IN_PATHGRID` config disabled
- Cycle parameter not passed correctly
- Location MDQ calculation dependency

**Code Reference:** `CalculateEPSQ()` in `QPTMNominationService.cs`

---

## Error Override Issues

### Issue 15: Error Override Not Working

**Symptoms:**
- Override flag set but error still blocks submission
- Override not persisting after save

**Root Cause:**
- User doesn't have error override security
- Override through-date is in the past
- Nomination split logic failed during override

**Investigation Steps:**
1. Check user security for NominationErrorOverrides screen
2. Verify override through-date is valid
3. Check `QPTMNominationService_ErrorOverrideHelper.CheckErrorOverrideChanges()`

---

### Issue 16: Nomination Split During Override

**Symptoms:**
- Nomination unexpectedly split into two records
- Date ranges changed after override

**Root Cause:**
- Override end date is before nomination EndGasDay
- System correctly splits the nomination at the override boundary

**Explanation:**
This is expected behavior. When an override is applied through a specific date but the nomination extends beyond that date:
- Original nomination: adjusted to end at override date
- New nomination: starts day after override date, without override

**Code Reference:** `QPTMNominationService_ErrorOverrideHelper.cs`

---

## API Nomination Issues

### Issue 17: API Submission Returns Errors

**Symptoms:**
- REST API nomination submission returns validation errors
- API messages in `APIMessages` list

**Root Cause:**
- Missing required fields (TSP, cycle, gas day, SR)
- Invalid DUNS numbers
- Nomination model mismatch (PNT vs. PT)

**Investigation Steps:**
1. Check `QPTMNomAPIValidationUtility` error messages:
   - `TSPError` = "TSP must be set"
   - `MissingOrInvalidNomModel` = "Invalid Nom Model Code"
   - `ServiceRequestorError` = "Invalid Service Requester"
   - `CycleError` = "Invalid Cycle ID"
   - `GasDayError1` = "Beginning Gas Day is greater than End Gas Day"
   - `GasDayError2` = "Beginning Gas Day and End Gas Day in different month"
2. Check API request format matches expected schema
3. Verify DUNS number validation

**Code Reference:** `QPTMAPINominationProcessor.cs`, `QPTMNomAPIValidationUtility.cs`

---

### Issue 18: API Discrepancy Results

**Symptoms:**
- Discrepancies endpoint returns unexpected data
- Nominations don't match between API and UI

**Investigation Steps:**
1. Check filter parameters (NominationDiscrepanciesFilterEnum)
2. Verify gas day and cycle alignment
3. Compare API response with direct database query

**Code Reference:** `NominationsController.cs` - Discrepancies endpoints

---

## Autogeneration Issues

### Issue 19: Autogen Not Creating Nominations

**Symptoms:**
- Autogeneration rule configured but nominations not created
- No error messages visible

**Root Cause:**
- Imbalance threshold not met
- Contract filters excluding all contracts
- Source nominations don't match autogen criteria
- Execution sequence conflicts

**Investigation Steps:**
1. Check autogen rule configuration in NNCTRL_AUTOGEN_HDR
2. Verify imbalance threshold settings
3. Check contract filter grid for the autogen rule
4. Verify source nominations exist for matching

**Code Reference:** `NominationAutogenController.cs`, `IQPTMNominationAutoGenService`

---

### Issue 20: Autogen Validation Subset Issues

**Symptoms:**
- Autogen nominations failing validation that manual nominations pass
- Or autogen nominations bypassing validation rules

**Root Cause:**
- `ValidationNominationSubsetAGN` vs. `ValidationNominationSubsetAll` mismatch
- `subsetValidation` flag not set correctly

**Code Reference:** `ValidationEngineNomination.cs` - subset logic

---

## Performance Issues

### Issue 21: Nomination Retrieval Slow

**Symptoms:**
- GetNominations() takes excessive time
- UI timeout on query

**Root Cause:**
- Large number of nominations for the date range
- NominationHeaderCache stale or oversized
- Missing database indexes

**Investigation Steps:**
1. Check nomination count for the parameters
2. Monitor `SingletonCache<NominationHeaderCache>` size
3. Check SQL Server query plans for NNCTRL_NOM_DTL
4. Verify `NnnomloadMaxRecsPerSave` batch size setting

---

### Issue 22: Validation Performance Degradation

**Symptoms:**
- ValidateNominations() takes too long
- Timeout during validation

**Root Cause:**
- Large nomination set (hundreds of records)
- Rule cache invalidation causing recompilation
- NomLatestCycleData cache miss
- TransTypeFireCache/ContractFireCache not populated

**Investigation Steps:**
1. Check nomination count being validated
2. Monitor rule cache events (`RuleCacheChanged`)
3. Profile validation engine execution time per level
4. Check if `bStopValidatingOnError` flag is properly set

---

## Diagnostic SQL Queries

### Query 1: Nomination Status Overview

```sql
SELECT
    n.TSP_NO,
    n.SR_CTR_NO,
    n.SR_BP_NO,
    n.BEG_GAS_DAY,
    n.END_GAS_DAY,
    n.ID_CYCLE,
    n.NOM_STAT_CODE,
    n.REC_QTY,
    n.DEL_QTY,
    n.FUEL_QTY,
    n.ACTN_CODE,
    n.UPDATE_DATE
FROM NNCTRL_NOM_DTL n
WHERE n.TSP_NO = @TspNo
  AND n.BEG_GAS_DAY = @GasDay
  AND n.SR_BP_NO = @SrBpNo
ORDER BY n.SR_CTR_NO, n.NOM_SEQ_NO;
```

### Query 2: Nomination Validation Errors

```sql
SELECT
    d.NOM_SEQ_NO,
    d.SR_CTR_NO,
    d.BEG_GAS_DAY,
    e.RULE_CODE,
    e.ERROR_MSG,
    e.VALIDATION_LEVEL,
    e.IS_OVRD
FROM NNCTRL_NOM_DTL d
JOIN NNCTRL_NOM_DTL_ERR e ON d.NOM_SEQ_NO = e.NOM_SEQ_NO AND d.TSP_NO = e.TSP_NO
WHERE d.TSP_NO = @TspNo
  AND d.BEG_GAS_DAY = @GasDay
  AND d.SR_BP_NO = @SrBpNo
ORDER BY d.SR_CTR_NO, e.VALIDATION_LEVEL, e.RULE_CODE;
```

### Query 3: Nomination Header Details

```sql
SELECT
    h.ID_NOM,
    h.TSP_NO,
    h.SR_BP_NO,
    h.SR_CTR_NO,
    h.ID_REC_LOC,
    h.ID_DEL_LOC,
    h.TRANS_TYPE_CODE,
    h.NOM_CAP_TYPE_CODE,
    h.IS_PATH_RECORD,
    h.IS_UP_RECORD,
    h.IS_DN_RECORD,
    h.NAESB_MODEL_CODE,
    h.ID_NOM_HASH
FROM NNCTRL_NOM_HDR h
WHERE h.TSP_NO = @TspNo
  AND h.SR_BP_NO = @SrBpNo
  AND h.SR_CTR_NO = @SrCtrNo;
```

### Query 4: Latest Cycle Nominations

```sql
SELECT
    lc.ID_NOM,
    lc.GAS_DAY,
    lc.ID_CYCLE,
    lc.REC_QTY,
    lc.DEL_QTY,
    lc.FUEL_QTY,
    lc.REC_CONF_QTY,
    lc.DEL_CONF_QTY,
    lc.REC_SCHD_QTY,
    lc.DEL_SCHD_QTY
FROM NNCTRL_NOM_LATEST_CYCLE lc
WHERE lc.TSP_NO = @TspNo
  AND lc.GAS_DAY = @GasDay
  AND lc.ID_CYCLE = @IdCycle;
```

### Query 5: Error Override Records

```sql
SELECT
    eo.SEQ_NO,
    eo.NOM_ID,
    eo.CYCLE_TYPE_CODE,
    eo.SR_BP_NO,
    eo.SR_CTR_NO,
    eo.REC_LOC_ID,
    eo.DEC_LOC_ID
FROM NNTRAN_ERROR_OVERRIDES eo
WHERE eo.TSP_NO = @TspNo
  AND eo.NOM_ID = @NomId;
```

### Query 6: Nomination Lifecycle History

```sql
SELECT
    lf.ID_NOM,
    lf.GAS_DAY,
    lf.ID_CYCLE,
    lf.UPDATE_DATE,
    lf.USER_ID
FROM NNCTRL_LIFECYCLE lf
WHERE lf.TSP_NO = @TspNo
  AND lf.ID_NOM = @IdNom
ORDER BY lf.UPDATE_DATE DESC;
```

### Query 7: Autogen Configuration

```sql
SELECT
    ah.AUTOGEN_ID,
    ah.NOM_AUTOGEN_CODE,
    ah.TARGET_TSP_NO,
    ah.TARGET_CYCLE_ID,
    ah.NEW_REC_LOC_ID,
    ah.NEW_DEL_LOC_ID,
    ah.IMB_THRESHOLD_PCT,
    ah.EXE_SEQ_NO
FROM NNCTRL_AUTOGEN_HDR ah
WHERE ah.TSP_NO = @TspNo;
```

### Query 8: Total Nominated vs. Contract MDQ

```sql
SELECT
    d.SR_CTR_NO,
    d.BEG_GAS_DAY,
    SUM(d.DEL_QTY) AS TotalDelNominated,
    c.MDQ_QTY AS ContractMDQ,
    SUM(d.DEL_QTY) - c.MDQ_QTY AS OverMDQ
FROM NNCTRL_NOM_DTL d
JOIN KCTRL_CTR_HDR c ON d.TSP_NO = c.TSP_NO AND d.SR_CTR_NO = c.SR_CTR_NO
WHERE d.TSP_NO = @TspNo
  AND d.BEG_GAS_DAY = @GasDay
  AND d.NOM_STAT_CODE NOT IN ('DEL')
GROUP BY d.SR_CTR_NO, d.BEG_GAS_DAY, c.MDQ_QTY
HAVING SUM(d.DEL_QTY) > c.MDQ_QTY;
```

---

## Key Code Locations for Debugging

| Area | File | Key Method/Section |
|------|------|--------------------|
| **Core Service** | `ServiceCore.Nomination/QPTMNominationService.cs` | All nomination operations |
| **Validation Engine** | `Validations/ValidationEngineNomination.cs` | `Validate()` - orchestrates all levels |
| **Rule Firing** | `Validations/ValidationRuleBaseNomination.cs` | `ShouldRuleFireForNom()` |
| **Error Attachment** | `Validations/ValidationRuleHelper.cs` | `AddErrorToNomination()` |
| **Error Override** | `ServiceCore.Nomination/QPTMNominationService_ErrorOverrideHelper.cs` | `CheckErrorOverrideChanges()` |
| **API Processing** | `ServiceCore.Nomination/QPTMAPINominationProcessor.cs` | Batch API processing |
| **API Validation** | `ServiceCore.Nomination/QPTMNomAPIValidationUtility.cs` | API-specific validation |
| **Maintenance UI** | `Web.Core/Controllers/NominationMaintenanceController.cs` | Grid-based screen |
| **Submission UI** | `Web.Core/Controllers/NominationSubmissionController.cs` | NAESB submission screen |
| **Data Access** | `DataAccess/QNominationDataAccess.cs` | Database operations |
| **Header Cache** | `DataCache/NominationHeaderCache.cs` | Nomination header caching |
| **Events** | `Events.Nomination/QPTMNomSubEventDetector.cs` | Submission events |

### Business Rules Quick Reference

| Rule Range | Area |
|------------|------|
| RuleNNSEC* | Security (user authorization) |
| RuleNNFK* | Foreign key (reference data) |
| RuleNNMAN* | Manual nomination FK |
| RuleNNAK* | Alternate key |
| RuleNN00001* | Package, price, contract period |
| RuleNN00002* | Transaction type, flow direction |
| RuleNN00003* | Contract, MDQ, path, location, imbalance |
| RuleNN00004* | Nomination attributes, contract attributes |
| RuleNN00005* | Location, brokerage |
| RuleNN00009* | Fuel, source, cycle, credit, lease |

---

## Historical Issues

### Template for Recording Issues

When resolving nomination issues, document them here with this format:

```markdown
### Issue [N]: [Brief Title]
**WI**: #[number]
**Date**: YYYY-MM-DD
**Customer**: [customer name]
**Environment**: [PRD/UAT/UPG]
**Symptoms**: [what was observed]
**Root Cause**: [why it happened]
**Resolution**: [what was done to fix it]
**Files Changed**: [list of modified files]
**Prevention**: [how to prevent recurrence]
```

*(Add historical issues as they are investigated and resolved)*

---

## Related Documentation

- [Domain Documentation](./domain.md) - Business concepts and workflows
- [Architecture Documentation](./architecture.md) - Technical implementation details
- [CAS Troubleshooting](../capacity-scheduling-allocations/troubleshooting.md) - Scheduling issues (downstream of nominations)
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Feature/keyword mapping
- [WORK_ITEM_INVESTIGATION.md](../WORK_ITEM_INVESTIGATION.md) - WI investigation workflow

---

*Last updated: 2026-03-03*
*Document version: 1.0*
