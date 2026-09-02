---
title: Contracts (CTR) - Troubleshooting Guide
category: troubleshooting
feature: Contracts (CTR)
related_repos: Web, Batch
keywords: contract errors, validation failure, save failed, amendment error, TOS code, MDQ mismatch, attribute flat table, FK error, agent save, location validation, contract troubleshooting, effective date, status code
last_updated: 2026-03-03
---

# Contracts (CTR) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Contract Maintenance issues in QPTM Web. It covers common errors, diagnostic queries, root cause analysis patterns, and historical issue references.

For business concepts, see [Domain Documentation](./domain.md).
For technical implementation, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Common Validation Errors](#common-validation-errors)
3. [Save Failures](#save-failures)
4. [Amendment Issues](#amendment-issues)
5. [Location Issues](#location-issues)
6. [Agent Issues](#agent-issues)
7. [Attribute and Flat Table Issues](#attribute-and-flat-table-issues)
8. [Rate and Billing Issues](#rate-and-billing-issues)
9. [Performance Issues](#performance-issues)
10. [API Issues](#api-issues)
11. [Diagnostic SQL Queries](#diagnostic-sql-queries)
12. [Key Code Locations for Debugging](#key-code-locations-for-debugging)
13. [Historical Issues](#historical-issues)

---

## Quick Diagnostic Checklist

When investigating a contract issue, check these in order:

1. **What TSP, CtrNo, and AmendNo?** - Get the specific contract identifiers
2. **What is the contract status?** - Check STATUS_CD in SCTRL_CTR_HEADER
3. **Is the TOS code valid and active?** - Verify SUB_TYPE_CODE exists in the TOS tables
4. **Are effective dates valid?** - Check for gaps, overlaps, or backwards date ranges
5. **What validation errors appear?** - Check the message log for specific error codes (K_CTRME*)
6. **Was the attribute flat table updated?** - Check KCTRL_CTR_ATTR_FLAT for the time slice
7. **Are there FK constraint issues?** - Check related tables (agents, locations, child objects)
8. **Were there recent code/config changes?** - Check global configs, screen defaults, TOS attribute configuration

---

## Common Validation Errors

### Issue 1: Amendment Status Ordering Error

**Symptoms:**
- Error on save: "Previous amendment must be Executed or Active before this amendment can be Executed"
- Message code: `K_CTRME067`, `K_CTRME068`, `K_CTRME070`
- New amendment cannot be set to Executed or Active status

**Root Cause:**
- For **Additive** amendment handling TOS: all previous amendments must be Executed or Active before a new amendment can be set to Executed or Active
- For **Replacement** amendment handling TOS: amendment 0 must be Executed or Active
- An amendment with the same effective date already exists

**Investigation Steps:**
1. Query all amendments for the contract to check their statuses
2. Verify the TOS code's `AmendHandlingCode` (Additive vs Replacement)
3. Check if amendment 0 exists and its status

**Resolution:**
- Set previous amendments to Executed or Active status first
- For Replacement TOS: ensure amendment 0 is Executed or Active
- If duplicate effective dates exist, modify the date range

**Code Reference:** `QPTMContractMaintenace008_HeaderValidateTosCode.cs` in `Quorum.QPTM.Validations/Screens/ContractMaintenance/Validation Rules/HeaderValidations/`

---

### Issue 2: Contract Number Generation Failure

**Symptoms:**
- Error on save: "Next Contract Number was not found"
- Message code: `K_CTRME006`
- New contract save fails immediately

**Root Cause:**
- The global sequence number generator returned -1 or an empty value
- The sequence table may be exhausted or locked
- The `UseTSPTOSContractPrefix` config may produce a CtrNo longer than 12 characters

**Investigation Steps:**
1. Check the global sequence table for the CTR_NO sequence
2. Verify the `UseTSPTOSContractPrefix` global config
3. Check if the TSP/TOS prefix combination produces overly long contract numbers

**Resolution:**
- Reset or increment the global sequence if exhausted
- If prefix mode is enabled, verify the prefix length does not exceed limits
- Check database locks on the sequence table

**Code Reference:** `GetNextCtrNo()` in `QPTMServiceCore_ContractMaintenance.cs` (around line 732)

---

### Issue 3: Executed Status Requires Executed Date

**Symptoms:**
- Error when setting status to Executed: "Executed Date is required when status is Executed"
- Contract cannot be saved with Executed status

**Root Cause:**
- The `ExecutedDate` field is null when the status is set to "EXE"
- The auto-set logic in the controller did not fire (e.g., status was set via data import)

**Investigation Steps:**
1. Check if `ExecutedDate` is populated in the contract header
2. Verify the status change was made through the normal UI flow

**Resolution:**
- Set the ExecutedDate to the appropriate date before saving
- If importing data, ensure ExecutedDate is included in the import

**Code Reference:** `QPTMContractMaintenance001_DatesValidateStatusCode.cs` in `Validation Rules/Dates/`

---

### Issue 4: Inactive Business Party Warning

**Symptoms:**
- Warning on save: "Business Party is inactive"
- Message code: related to `K_CTRME*` header validation

**Root Cause:**
- The business associate (BaNo) associated with the contract has an inactive status
- This is a warning, not an error -- save will still proceed

**Investigation Steps:**
1. Look up the BA_NO in the business associate table
2. Verify the active/inactive status

**Resolution:**
- If the BA should be active, update the business associate record
- If expected, the warning can be acknowledged and the save will succeed

**Code Reference:** `QPTMContractMaintenace006_HeaderValidateInactiveBusinessParty.cs`

---

### Issue 5: Location Required Attribute Validation

**Symptoms:**
- Error on save: "Required attribute not set for location {loc1} / {loc2} and TOS {tos}"
- Locations cannot be added to the contract

**Root Cause:**
- The TOS/Location attribute cross-reference (`KXREF_TOS_LOC_ATTR`) requires certain location attributes that are not satisfied
- Receipt or delivery location does not have the required attribute indicator set

**Investigation Steps:**
1. Check the TOS/Location attribute cross-reference for the TOS code
2. Verify the location's attribute flags match the required attributes
3. Check if the location was recently changed or deactivated

**Resolution:**
- Configure the required attributes on the location
- Or update the TOS/location attribute cross-reference if the requirement has changed

**Code Reference:** `QPTMContractMaintenance001_LocationsValidateRequireAttributes.cs` in `Validation Rules/Locations/`

---

### Issue 6: Primary Point Pair Violation

**Symptoms:**
- Error on save related to primary point pair configuration
- Locations fail validation when PPP attribute is enabled

**Root Cause:**
- The contract TOS has the PPP (Primary Point Pairs) attribute enabled
- The receipt and delivery location pair is not configured as a valid primary point pair

**Investigation Steps:**
1. Check if the contract TOS has PPP attribute set to true
2. Verify the receipt/delivery pair in the point pair configuration tables
3. Check if the contract is properly set up for PPP routing

**Resolution:**
- Add the receipt/delivery pair to the PPP configuration
- Or remove the PPP attribute if it should not apply to this TOS

**Code Reference:** `QPTMContractMaintenance010_LocationsValidatePrimaryPointPairs.cs`

---

### Issue 7: Effective Date Gap Between Amendments

**Symptoms:**
- Error on save: date gap detected between amendments
- Message indicates a gap between the end of one amendment and the start of the next

**Root Cause:**
- For Additive amendment handling, effective date ranges should be contiguous
- A gap exists between EffDateTo of one amendment and EffDateFrom of the next

**Investigation Steps:**
1. Query all amendments ordered by EffDateFrom
2. Check for gaps between consecutive amendment date ranges

**Resolution:**
- Adjust effective dates to close the gap
- Ensure EffDateFrom of the new amendment follows immediately after EffDateTo of the previous one

**Code Reference:** `QPTMContractMaintenance012_HeaderDateGapValidation.cs`

---

### Issue 8: Imbalance Configuration Error

**Symptoms:**
- Errors related to imbalance fields when saving
- Trade lag time, CICO, or settlement method validation failures

**Root Cause:**
- The IMB (Imbalance) attribute is enabled but required imbalance fields are not configured
- Settlement method is inconsistent with other imbalance settings
- Tied contract for imbalance is invalid or expired

**Investigation Steps:**
1. Check if IMB attribute is set on the contract
2. Verify all required imbalance fields are populated
3. Check tied contract validity

**Resolution:**
- Complete all required imbalance configuration fields
- Ensure tied contracts are valid and effective for the same date range

**Code Reference:** `QPTMContractMaintenance001_ImbalanceValidateTradeLagTime.cs` through `QPTMContractMaintenance010_*` in `Validation Rules/Imbalance/`

---

### Issue 9: PAL/ISS Trade Validation Failures

**Symptoms:**
- Errors on PAL/ISS Trade tab fields
- Flow date, deal quantity, or amendment type validation failures
- Rate resolution warnings (daily rate is zero or exceeds tariff)

**Root Cause:**
- PAL/ISS deal fields are inconsistent (e.g., flow dates out of range, deal qty does not match total vol)
- Rate resolution process returned zero rate or rate exceeds daily rate
- Amendment type does not match the expected action

**Investigation Steps:**
1. Check the PAL/ISS deal record in KCTRL_PAL_ISS_DEAL
2. Verify flow dates are within the contract effective date range
3. Check rate resolution results

**Resolution:**
- Correct flow dates and quantities to be consistent
- Verify rate schedule configuration for the TOS
- Check the BATCHID_DETDAILYRT process configuration

**Code Reference:** `QPTMContractMaintenance001_PALISSTradeFlowDateValidate.cs` through `QPTMContractMaintenance015_*` in `Validation Rules/PALISSTrade/`

---

### Issue 10: Delete Fails - Contract Has Active References

**Symptoms:**
- Delete operation fails with foreign key constraint errors
- Contract cannot be deleted even though all headers are marked for deletion

**Root Cause:**
- Child objects (agents, locations, inventory accounts, auth overrun, FSS) still reference the contract
- The pre-delete validation detected active nominations, allocations, or billing records

**Investigation Steps:**
1. Check KCTRL_CTR_LOC for remaining location records
2. Check SCTRL_CTR_AGENT for agent records
3. Check inventory account headers referencing the contract
4. Check nomination/allocation/billing tables for references

**Resolution:**
- Ensure all child objects are properly marked for deletion
- Remove references from downstream systems first (nominations, allocations, billing)
- The system automatically deletes child objects, user-defined records, auth overrun, FSS, and inventory account headers when all amendments are deleted

**Code Reference:** `QPTMContractMaintenace010_HeaderValidatePreDelete.cs` and `DeleteChildObjects()` in `QPTMServiceCore_ContractMaintenance.cs`

---

### Issue 11: Contract Agent Save FK Error

**Symptoms:**
- Save fails with a foreign key error related to contract agents
- Error occurs even though the contract header appears to save successfully

**Root Cause:**
- The contract agent table has a FK constraint on CTR_NO that requires the contract header to exist first
- If agents are saved as part of the same transaction before the header, the FK check fails

**Investigation Steps:**
1. Check if the contract is new (CtrNo was just generated)
2. Verify the agent records have the correct CtrNo
3. Check if the SextnCtrAgentQptm records have TspNo set

**Resolution:**
- This is handled by the two-phase agent save in the code (WI #206053)
- If the issue persists, check that agents are being cleared before header save and re-added after
- Verify TspNo is set on the SextnCtrAgentQptm binding list

**Code Reference:** `UpdateSingleContractMaintenanceComplete()` in `QPTMServiceCore_ContractMaintenance.cs` (around line 589-598) and `UpdateAgent()` method

---

## Save Failures

### General Save Failure Pattern

When a contract save fails, the system follows this pattern:

1. Validation errors are collected across all tabs
2. If any error (Severity >= Error) exists, the save is aborted and errors are returned on the data objects
3. If auth overrun or FSS records have errors, the save is also aborted
4. The message log contains error codes in the format `K_CTRME###` or `K_CTRMW###` (warnings)

### Diagnosing Save Failures

1. Check the **message log** for error codes starting with `K_CTRM`
2. Map error codes to validation rule files using the `QQPTMMessageTitleCodes.ContractMaintenance` constants
3. Read the validation rule source to understand the exact condition
4. Use diagnostic SQL queries to verify data state

---

## Amendment Issues

### Common Amendment Problems

| Problem | Likely Cause | Resolution |
|---|---|---|
| Cannot create amendment | No existing contract queried | Query the contract first |
| Amendment number incorrect | Sequence not incrementing | Check `GetNextAmendNo()` -- it queries max AmendNo + 1 from KCTRL_CTR |
| Amendment defaults wrong | Screen defaults not loaded | Verify `LoadScreenDefaultsOfContract()` ran successfully |
| Copy contract fails | AssignNo not reset | Copy action should reset AssignNo to 0 |
| Amendment description not shown | `IsHideAmendDescr` config | Check `AllowDefaultAmenDescr` global config |

---

## Location Issues

### Location Validation Quick Reference

| Validation | Rule File | What It Checks |
|---|---|---|
| Required attributes | `001_LocationsValidateRequireAttributes` | TOS/location attribute cross-reference |
| Threshold quantity | `002_LocationsValidateThresholdQuantity` | Threshold qty within valid range |
| Hourly measurement | `003_LocationsValidateHourlyMeasurementPenalty` | HNA attribute and measurement setup |
| Segments | `004_LocationsValidateSegments` | Valid segment configuration |
| Facility | `005_LocationsValidateFacility` | Facility assignment valid |
| Multi-contract delivery | `007_LocationsValidateDelLocationMultiplecontract` | Delivery loc not used on conflicting contracts |
| Ineffective date | `009_LocationsValidateIneffectiveDate` | Location effective dates match contract |
| Primary point pairs | `010_LocationsValidatePrimaryPointPairs` | PPP routing valid |
| Location row | `011_LocationsValidateLocationRow` | Row completeness (required fields) |
| Duplicate attributes | `012_LocationsValidateDuplicateAttributes` | No duplicate location rows |

---

## Attribute and Flat Table Issues

### Flat Table Out of Sync

**Symptoms:**
- Downstream processes (nominations, scheduling) behave as if attributes are wrong
- Attribute flags in KCTRL_CTR_ATTR_FLAT do not match KCTRL_CTR_ATTR

**Root Cause:**
- The flat table update failed silently (error caught in generic exception handler)
- A direct database update to KCTRL_CTR_ATTR bypassed the flat table update
- A new TOS attribute was added but not mapped in the switch statement

**Investigation Steps:**
1. Compare normalized attributes with flat table for the specific contract/amendment/date range
2. Check for exceptions in the error message: "Error saving KCTRL_CTR_ATTR_FLAT:"
3. Verify the attribute code is mapped in `ContractMaintenance_UpdateAttributeFlatTable.cs`

**Resolution:**
- Re-save the contract through the UI to trigger flat table regeneration
- If a new attribute code needs to be added, update the switch statement in `UpdateAttributeFlatTableHelper()`
- Run a bulk update script to regenerate flat table records for affected contracts

**Code Reference:** `ContractMaintenance_UpdateAttributeFlatTable.cs` -- the `UpdateAttributeFlatTableHelper()` method

---

## Rate and Billing Issues

### Rate Resolution Warning on PAL/ISS Save

**Symptoms:**
- Warning: "Rate Resolution Process returned zero rate" (`K_CTRMW047`)
- Warning: "Contract daily rate exceeds tariff rate" (`K_CTRME043`)

**Root Cause:**
- The BATCHID_DETDAILYRT batch process is configured but rate resolution returns no rate or a low rate
- The contract's daily rate exceeds the resolved tariff rate

**Investigation Steps:**
1. Check if BATCHID_DETDAILYRT process exists and is active
2. Verify rate schedule configuration for the TOS
3. Check BltranRateResInput records for the resolution attempt
4. Query SELECT_RATE_RESOLUTION SQL for the set ID

**Resolution:**
- Configure rate schedules correctly for the TOS
- Verify the rate TOC process cross-reference (KXREF_RATE_TOC_PROCESS)
- Adjust the contract daily rate if it legitimately exceeds tariff

**Code Reference:** `ValidateContractDailyRate()` in `QPTMServiceCore_ContractMaintenance.cs` (around line 1576)

---

## Performance Issues

### Slow Contract Query

**Symptoms:**
- Contract maintenance screen takes a long time to load
- Query returns but the screen rendering is slow

**Root Cause:**
- The `AddAdditionalPropertiesContractMaint()` method performs many supplemental queries (locations, seasonal profiles, contacts, text, schedule objects, ratchets, tax IDs)
- Large contracts with many locations or amendments amplify the issue

**Investigation Steps:**
1. Check the number of locations, agents, and text records on the contract
2. Monitor SQL query execution times for the supplemental queries
3. Check if seasonal profile or location queries are returning excessive data

**Resolution:**
- Optimize supplemental queries to use IN-clause batching (already implemented via `CreateInClauseFilters`)
- Consider caching frequently accessed reference data (seasonal profiles, location names)
- Limit the number of records returned via paging if applicable

---

## API Issues

### Contract API Returns Empty Results

**Symptoms:**
- GET `api/v1/Contracts?tsp={tsp}` returns empty data array
- GET `api/v1/Contracts/{tsp}/{id}/{amend_no}` returns no contract

**Root Cause:**
- The `asOfDate` parameter defaults to today, which may filter out expired or future contracts
- The contract does not exist for the specified TSP/CtrNo/AmendNo combination
- Filter parameters are invalid

**Investigation Steps:**
1. Try with `asOfDate=9000-12-31` to return all effective dates
2. Verify the contract exists in the database
3. Check filter parameter values against `ContractFilterEnum`

**Resolution:**
- Use `asOfDate=9000-12-31` to bypass effective date filtering
- Verify TSP, CtrNo, and AmendNo are correct
- Check the `ContractsAPIService` implementation for filter logic

**Code Reference:** `ContractsController.cs` in `Quorum.QPTM.Web.Controllers/APIControllers/`

---

## Diagnostic SQL Queries

### Query 1: Contract Header Details

```sql
-- Get contract header with QPTM extension
SELECT h.CTR_NO, h.BA_NO, h.ASSIGN_NO, h.EFF_DATE_FROM, h.EFF_DATE_TO,
       h.STATUS_CD, h.TYPE_CODE, h.SUB_TYPE_CODE, h.EXECUTED_DATE,
       q.TSP_NO, q.CTR_MDQ, q.FIXED_MDIQ_QTY, q.FIXED_MDWQ_QTY,
       q.CTR_MSQ, q.OVRD_CTR_MDQ
FROM SCTRL_CTR_HEADER h
INNER JOIN SEXTN_CTR_HEADER_QPTM q
  ON h.CTR_NO = q.CTR_NO AND h.ASSIGN_NO = q.ASSIGN_NO
  AND h.EFF_DATE_FROM = q.EFF_DATE_FROM
WHERE q.TSP_NO = @TspNo
  AND h.CTR_NO = @CtrNo;
```

### Query 2: All Amendments for a Contract

```sql
-- List all amendments with status
SELECT CTR_NO, AMEND_NO, TOS_CODE, CTR_STATUS_CODE, EFF_DATE_FROM, EFF_DATE_TO
FROM KCTRL_CTR
WHERE TSP_NO = @TspNo
  AND CTR_NO = @CtrNo
ORDER BY AMEND_NO;
```

### Query 3: Contract Locations with MDQ

```sql
-- Get contract locations and MDQ quantities
SELECT CTR_NO, AMEND_NO, ID_LOC_1, ID_LOC_2, ID_LOC_GRP_1, ID_LOC_GRP_2,
       FIXED_MDQ_QTY, SUMMER_MDQ_QTY, WINTER_MDQ_QTY, SHOULDER_MDQ_QTY
FROM KCTRL_CTR_LOC
WHERE TSP_NO = @TspNo
  AND CTR_NO = @CtrNo
  AND AMEND_NO = @AmendNo
ORDER BY ID_LOC_1, ID_LOC_2;
```

### Query 4: Attribute Flat Table vs Normalized Attributes

```sql
-- Compare flat table attributes with normalized attributes
SELECT af.CTR_NO, af.AMEND_NO, af.EFF_DATE_FROM,
       af.ATTR_IND_NOM, af.ATTR_IND_BIL, af.ATTR_IND_CAP, af.ATTR_IND_CIO,
       af.ATTR_IND_IMB, af.ATTR_IND_PPP, af.ATTR_IND_HNA, af.ATTR_IND_EVG
FROM KCTRL_CTR_ATTR_FLAT af
WHERE af.TSP_NO = @TspNo
  AND af.CTR_NO = @CtrNo;

-- Normalized attributes for comparison
SELECT TOS_ATTR_CODE, IS_ATTR_TRUE
FROM KCTRL_CTR_ATTR
WHERE TSP_NO = @TspNo
  AND CTR_NO = @CtrNo
  AND AMEND_NO = @AmendNo
  AND EFF_DATE_FROM = @EffDateFrom;
```

### Query 5: Contract Agents

```sql
-- Get contract agents with business associate info
SELECT a.CTR_NO, a.AGENT_BA_NO, a.CONSENTING_BP_NO,
       a.EFF_DATE_FROM, a.EFF_DATE_TO
FROM SCTRL_CTR_AGENT a
WHERE a.CTR_NO = @CtrNo
ORDER BY a.EFF_DATE_FROM;
```

### Query 6: Contract Status History

```sql
-- Track status changes for audit
SELECT CTR_NO, STATUS_CD, EFF_DATE_FROM, EFF_DATE_TO, EXECUTED_DATE, ASSIGN_NO
FROM SCTRL_CTR_HEADER
WHERE CTR_NO = @CtrNo
ORDER BY ASSIGN_NO, EFF_DATE_FROM;
```

### Query 7: Effective Date Range Check

```sql
-- Check for gaps or overlaps in effective date ranges
SELECT CTR_NO, ASSIGN_NO, EFF_DATE_FROM, EFF_DATE_TO
FROM KCTRL_CTR_EFF_DATE_RANGE_VW
WHERE TSP_NO = @TspNo
  AND CTR_NO = @CtrNo
ORDER BY EFF_DATE_FROM;
```

### Query 8: Auth Overrun Records

```sql
-- Check authorized overrun configuration
SELECT CTR_NO, DAILY_OVERRUN_QTY, EFF_DATE_FROM, EFF_DATE_TO
FROM KCTRL_AUTH_OVERRUN
WHERE TSP_NO = @TspNo
  AND CTR_NO = @CtrNo
ORDER BY EFF_DATE_FROM;
```

---

## Key Code Locations for Debugging

| Component | File Path | Key Method/Area |
|---|---|---|
| **Main Service** | `Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/QPTMServiceCore_ContractMaintenance.cs` | `UpdateSingleContractMaintenanceComplete()` - main save flow |
| **Flat Table Update** | `Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/ContractMaintenance_UpdateAttributeFlatTable.cs` | `UpdateAttributeFlatTableHelper()` - attribute mapping |
| **CtrNo Generation** | `Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/QPTMServiceCore_ContractMaintenance.cs` | `GetNextCtrNo()` - auto-numbering (around line 732) |
| **Screen Defaults** | `Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/QPTMServiceCore_ContractMaintenance.cs` | `LoadScreenDefaultsOfContract()` |
| **MVC Controller** | `Quorum.QPTM.Web.Core/Controllers/ContractMaintenanceController.cs` | `DoAction()` - handles New, Save, AddAmendment, Copy, Delete |
| **UI Controller** | `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerContractMaintenance.cs` | `SetNextAmendNo()`, `Query()` |
| **API Controller** | `Quorum.QPTM.Web.Controllers/APIControllers/ContractsController.cs` | `GetContractsCollection()`, `GetContractObject()` |
| **Complete DO** | `Quorum.QPTM.DataObject/ContractHeaderCompleteDOExt.cs` | Extension children (AuthOverrun, FSS), TransferChildTables |
| **Header DO** | `Quorum.QPTM.DataObject/ContractHeaderDOExt.cs` | `CHQPTM` property - shortcut to QPTM extension |
| **MDQ Change Event** | `Quorum.QPTM.Events.Contract/Detectors/QPTMContractMaintenanceMDQChangeEventDetector.cs` | `Evaluate()` - MDQ change detection |
| **Status Change Event** | `Quorum.QPTM.Events.Contract/Detectors/QPTMContractMaintenanceStatusCdChangeEventDetector.cs` | `Evaluate()` - status change detection |
| **Event Context** | `Quorum.QPTM.Events.Contract/Detectors/QPTMContractMaintenanceDetectorContext.cs` | Event data passed to detectors |
| **Header Validation (TOS)** | `Quorum.QPTM.Validations/Screens/ContractMaintenance/Validation Rules/HeaderValidations/QPTMContractMaintenace008_HeaderValidateTosCode.cs` | Additive vs Replacement amendment validation |
| **Location Validation** | `Quorum.QPTM.Validations/Screens/ContractMaintenance/Validation Rules/Locations/` | 12 location validation rules |
| **Date Validation** | `Quorum.QPTM.Validations/Screens/ContractMaintenance/Validation Rules/Dates/` | Status code, evergreen, date code validations |
| **Constants** | `Quorum.QPTM.CoreInterface/Constants.cs` | `ContractStatus`, `TOSAttribute`, `ContractMainDO`, `ContractMainTabs` |
| **Service Interface** | `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_ContractMaintenance.cs` | `ContractMaintenanceData` class |

---

## Historical Issues

### Template for Recording Historical Issues

When a contract issue is resolved, document it here using this template:

```
### WI #{number}: {title}

**Date Resolved:** YYYY-MM-DD
**Symptoms:** {what the user reported}
**Root Cause:** {why it happened}
**Resolution:** {what was changed}
**Files Changed:** {list of modified files}
**Related Validation Rule:** {if applicable}
```

### WI #206053: Contract Agent FK Error on New Contract Save

**Date Resolved:** (historical)
**Symptoms:** Save of a new contract with agents fails with a foreign key error
**Root Cause:** Contract agents were being saved as part of the same transaction before the contract header was committed, causing an FK violation on CTR_NO
**Resolution:** Implemented two-phase agent save: clear agents from the complete object before saving the header, then save agents separately via `UpdateAgent()` after the header is committed
**Files Changed:** `QPTMServiceCore_ContractMaintenance.cs` -- `UpdateSingleContractMaintenanceComplete()`

### Attribute Flat Table Error Pattern

**Date Resolved:** (ongoing)
**Symptoms:** Error message "Error saving KCTRL_CTR_ATTR_FLAT:" followed by exception details
**Root Cause:** The `UpdateAttributeFlatTableHelper()` method catches exceptions and re-throws with a prefixed message, which can mask the underlying cause (e.g., null reference, missing flat record)
**Resolution:** Check for null `ContractAttributeFlatDO`, verify CtrNo/AmendNo/TspNo are set, ensure the attribute code is mapped in the switch statement
**Files Changed:** `ContractMaintenance_UpdateAttributeFlatTable.cs`

---

*Last updated: 2026-03-03*

*Document version: 1.0*
