---
title: Location Management (LOC) - Troubleshooting Guide
category: troubleshooting
feature: Location Management (LOC)
related_repos: Web, Batch
keywords: LOC, location, meter, troubleshooting, PACTRL_LOC, SEXTN_MTR_HEADER_QPTM, PACTRL_LOC_CONTACT, PACTRL_LOC_AGGREGATE, operator ID, confirm party, location attribute, validation error, save failure, location resolution, bidirectional, capacity rate area, integration, MPS, mass change, child location, effective date
last_updated: 2026-03-03
---

# Location Management (LOC) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for common issues encountered in the Location Management feature. It includes diagnostic SQL queries, code locations, and resolution steps.

For business concepts, see [Domain Documentation](./domain.md).
For technical architecture, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Issue 1: Operator ID or Confirm Party Not Displaying](#issue-1-operator-id-or-confirm-party-not-displaying)
2. [Issue 2: Location Save Fails with Validation Errors](#issue-2-location-save-fails-with-validation-errors)
3. [Issue 3: Tabs Not Showing or Showing Incorrectly](#issue-3-tabs-not-showing-or-showing-incorrectly)
4. [Issue 4: Child Location Effective Date Errors](#issue-4-child-location-effective-date-errors)
5. [Issue 5: Bidirectional Location Configuration Errors](#issue-5-bidirectional-location-configuration-errors)
6. [Issue 6: Location Fields Are Read-Only Unexpectedly](#issue-6-location-fields-are-read-only-unexpectedly)
7. [Issue 7: Capacity/Rate Area Grid Issues](#issue-7-capacityrate-area-grid-issues)
8. [Issue 8: Location Resolution Not Triggering Batch Process](#issue-8-location-resolution-not-triggering-batch-process)
9. [Issue 9: Flat Attribute Table Out of Sync](#issue-9-flat-attribute-table-out-of-sync)
10. [Issue 10: Location Contact Mass Change Not Saving](#issue-10-location-contact-mass-change-not-saving)
11. [Issue 11: Location Data Not Loading After Link Navigation](#issue-11-location-data-not-loading-after-link-navigation)
12. [Issue 12: Oracle Error on Location Delete](#issue-12-oracle-error-on-location-delete)
13. [Issue 13: Affidavit Curtailment Warning Not Showing](#issue-13-affidavit-curtailment-warning-not-showing)
14. [Issue 14: Duplicate Contact Type Validation Errors](#issue-14-duplicate-contact-type-validation-errors)
15. [Diagnostic SQL Queries](#diagnostic-sql-queries)

---

## Issue 1: Operator ID or Confirm Party Not Displaying

### Symptoms
- The Operator ID and/or Confirm Party fields on the Location Maintenance header are blank
- The location has contacts configured but the header fields do not display them

### Root Cause
The Operator ID and Confirm Party are derived from the Contacts grid, not stored as separate fields. They are populated in `AddAdditionalPropertiesLocationMaintenanceComplete()` by matching contacts with `ContactTypeCode` of `OPR` and `CNF` respectively.

### Diagnostic Steps

1. Check if contacts exist for the location:

```sql
SELECT lc.ID_LOC, lc.TSP_NO, lc.EFF_DT_FROM, lc.CONTACT_TYPE_CODE, lc.ID_CONTACT,
       c.FIRST_NM, c.LAST_NM, c.PRIMARY_BP_NO, ba.BP_NM
FROM PACTRL_LOC_CONTACT lc
JOIN KCTRL_CONTACT c ON lc.ID_CONTACT = c.ID_CONTACT
LEFT JOIN KCTRL_BUSINESS_ASSOCIATE ba ON c.PRIMARY_BP_NO = ba.BP_NO
WHERE lc.ID_LOC = '<LocationId>'
  AND lc.TSP_NO = <TspNo>
ORDER BY lc.EFF_DT_FROM DESC, lc.CONTACT_TYPE_CODE;
```

2. Check for Operator and Confirm Party specifically:

```sql
SELECT lc.CONTACT_TYPE_CODE, c.PRIMARY_BP_NO, ba.BP_NM
FROM PACTRL_LOC_CONTACT lc
JOIN KCTRL_CONTACT c ON lc.ID_CONTACT = c.ID_CONTACT
LEFT JOIN KCTRL_BUSINESS_ASSOCIATE ba ON c.PRIMARY_BP_NO = ba.BP_NO
WHERE lc.ID_LOC = '<LocationId>'
  AND lc.TSP_NO = <TspNo>
  AND lc.CONTACT_TYPE_CODE IN ('OPR', 'CNF')
  AND lc.EFF_DT_FROM <= SYSDATE
ORDER BY lc.EFF_DT_FROM DESC;
```

### Code Location
- **Population logic**: `QPTMServiceCore_LocationMaintenance.cs` lines ~756-770
  ```csharp
  if (contact.ContactTypeCode.IsEqualTo(Constants.ContactType.ConfirmingParty))
      meterHeaderQPTM.ConfirmParty = $"{contact.PrimaryBpNo} | {contact.BpNm}";
  if (contact.ContactTypeCode.IsEqualTo(Constants.ContactType.Operator))
      meterHeaderQPTM.OperatorID = $"{contact.PrimaryBpNo} | {contact.BpNm}";
  ```
- **View model transfer**: `LocationMaintenanceController.cs` lines ~351-352

### Resolution
- Ensure the location has a contact with `ContactTypeCode = 'OPR'` for Operator ID
- Ensure the location has a contact with `ContactTypeCode = 'CNF'` for Confirm Party
- Verify the contact's `ID_CONTACT` maps to a valid `KCTRL_CONTACT` record with a valid `PRIMARY_BP_NO`
- Verify the `PRIMARY_BP_NO` maps to a valid `KCTRL_BUSINESS_ASSOCIATE` record

---

## Issue 2: Location Save Fails with Validation Errors

### Symptoms
- Save operation returns validation errors
- Error messages may reference specific validation rules

### Diagnostic Steps

1. Identify the validation rule from the error message. All location validation rules are numbered 001-052.
2. Review the specific rule class in `Quorum.QPTM.Validations/Screens/LocationMaintenance/Validation Rules/`.

### Common Validation Failures

| Rule | Error | Common Cause |
|---|---|---|
| 001 | Effective date invalid | EffDateFrom > EffDateTo or overlapping slices |
| 005 | TSP/Meter validation | TspNo or MtrNo is blank or invalid |
| 010 | Child/parent eff date mismatch | Child location dates outside parent range |
| 018 | Duplicate confirm party | Multiple contacts with type CNF |
| 020 | Duplicate operator | Multiple contacts with type OPR |
| 031 | Bidirectional config invalid | BiDirectLocId set without matching config |
| 035 | Ownership percentage | Total ownership percentage exceeds 100% |
| 042-050 | CRA mandatory fields | Capacity/Rate Area missing required fields |

### Code Location
- **Validation entry point**: `QPTMServiceCore_LocationMaintenance.cs` line ~902
  ```csharp
  var issues = this.Validate(new QPTMLocationMaintenanceCompleteValidationContext(validateList, tspNo), context);
  ```
- **Validation rules directory**: `Quorum.QPTM.Validations/Screens/LocationMaintenance/Validation Rules/`

### Resolution
- Read the specific validation rule class to understand exact conditions
- Fix the data according to the rule's requirements
- For CRA (Capacity/Rate Area) validations (042-050), ensure all mandatory location group fields are populated

---

## Issue 3: Tabs Not Showing or Showing Incorrectly

### Symptoms
- The Brokers, Child Locations, Supplier Location, or Child Location For Allocation tabs are missing
- Tabs that should be hidden are visible

### Root Cause
Tab visibility is controlled by location attributes:
- **Brokers**: `END` (End User Transportation) must be true
- **Child Locations**: `AGR` (Aggregate) must be true
- **Supplier Location**: `MP` (Master Pins) must be true
- **Child Loc for Allocation**: `ACM` or `AAF` must be true
- **LDC tab**: Only visible when `IQPTMService_Utility.IsLDC()` returns true

### Diagnostic Steps

```sql
SELECT la.ID_LOC, la.TSP_NO, la.EFF_DT_FROM, la.LOC_ATTR_CODE, la.IS_ATTR_TRUE,
       qa.LOC_ATTR_DESCR
FROM PACTRL_LOC_ATTR la
JOIN QCODE_LOC_ATTR qa ON la.LOC_ATTR_CODE = qa.LOC_ATTR_CODE AND la.TSP_NO = qa.TSP_NO
WHERE la.ID_LOC = '<LocationId>'
  AND la.TSP_NO = <TspNo>
  AND la.LOC_ATTR_CODE IN ('END', 'AGR', 'MP', 'ACM', 'AAF')
ORDER BY la.EFF_DT_FROM DESC;
```

### Code Location
- **Tab visibility logic**: `LocationMaintenanceController.cs` lines ~2310-2345 (`GetLocationAttribute` method)
- **LDC tab**: `LocationMaintenanceController.cs` line ~2277 (`ShowHideTabsBasedOnLocTypeCode`)

### Resolution
- Toggle the appropriate location attribute on the Details tab
- Refresh the screen after changing attributes
- For LDC tab, verify the TSP is configured for LDC mode

---

## Issue 4: Child Location Effective Date Errors

### Symptoms
- Validation errors when saving child location (aggregate) records
- Messages about child effective dates being outside parent range

### Root Cause
Multiple validation rules enforce child-parent effective date consistency:
- Rule 010: `ValidateChildParentEffDt` -- child dates must be within parent range
- Rule 017: `ValidateChildLocEffDt` -- child location effective date validation

### Diagnostic Steps

```sql
-- Check parent location effective dates
SELECT IdLoc, TspNo, EffDateFrom, EffDateTo
FROM PACTRL_LOC
WHERE IdLoc = '<ParentLocationId>'
  AND TspNo = <TspNo>
ORDER BY EffDateFrom;

-- Check child location effective dates
SELECT la.ID_LOC, la.ID_CHILD_LOC, la.TSP_NO, la.EFF_DT_FROM, la.EFF_DT_TO
FROM PACTRL_LOC_AGGREGATE la
WHERE la.ID_LOC = '<ParentLocationId>'
  AND la.TSP_NO = <TspNo>
ORDER BY la.EFF_DT_FROM;

-- Check child location's own effective dates
SELECT IdLoc, TspNo, EffDateFrom, EffDateTo
FROM PACTRL_LOC
WHERE IdLoc = '<ChildLocationId>'
  AND TspNo = <TspNo>
ORDER BY EffDateFrom;
```

### Code Location
- `Quorum.QPTM.Validations/Screens/LocationMaintenance/Validation Rules/QPTMLocationMaintenance010_ValidateChildParentEffDt.cs`
- `Quorum.QPTM.Validations/Screens/LocationMaintenance/Validation Rules/QPTMLocationMaintenance017_ValidateChildLocEffDt.cs`

### Resolution
- Ensure child location aggregate records have `EffDateFrom` >= parent `EffDateFrom`
- Ensure child location aggregate records have `EffDateTo` <= parent `EffDateTo`
- Verify the child location itself (in `PACTRL_LOC`) has overlapping effective date ranges

---

## Issue 5: Bidirectional Location Configuration Errors

### Symptoms
- Validation errors related to bidirectional configuration (rules 031, 032)
- CAScheduleObjectCustom records not being created
- Bidirectional pair locations not found

### Root Cause
Bidirectional locations require:
1. Both locations must have `BiDirectLocId` pointing to each other
2. Effective date ranges must overlap
3. `QPTMGlobalConfigs.BidirectionalPOV` must be enabled
4. One location must be Receipt (R) and the other Delivery (D)

### Diagnostic Steps

```sql
-- Check bidirectional configuration
SELECT mh.MTR_NO, mh.TSP_NO, mh.EFF_DT_FROM, mh.EFF_DT_TO,
       mh.POV_CODE, mh.BI_DIRECT_LOC_ID
FROM SEXTN_MTR_HEADER_QPTM mh
WHERE mh.MTR_NO IN ('<LocationId1>', '<LocationId2>')
  AND mh.TSP_NO = <TspNo>
ORDER BY mh.MTR_NO, mh.EFF_DT_FROM;

-- Check CAScheduleObjectCustom records
SELECT *
FROM PACTRL_CA_SCHD_OBJ_CUST
WHERE TSP_NO = <TspNo>
  AND (ID_SCHD_OBJ LIKE '%<LocationId1>%' OR ID_SCHD_OBJ LIKE '%<LocationId2>%')
  AND SCHD_OBJ_TYPE_CODE = 'BP';
```

### Code Location
- **CAScheduleObject management**: `QPTMServiceCore_LocationMaintenance.cs` lines ~1303-1407 (`AddDeleteCAScheduleObjectCustom`)
- **Config check**: `QPTMServiceCore_LocationMaintenance.cs` lines ~1611-1623 (`ValdBidirectionalPOV`)
- **Validation**: `QPTMLocationMaintenance031_ValidateBidirectional.cs`, `QPTMLocationMaintenance032_ValidateBidirectionalEffDate.cs`

### Resolution
- Ensure both locations reference each other via `BiDirectLocId`
- Verify `BidirectionalPOV` config is enabled: `QPTMGlobalConfigs.BidirectionalPOV`
- Ensure effective dates overlap between the two locations
- Verify POV codes: one must be R (Receipt) and one must be D (Delivery)
- If CAScheduleObject is not being created, check if `ValdBidirectionalPOV` returns true

---

## Issue 6: Location Fields Are Read-Only Unexpectedly

### Symptoms
- Fields on the Location Maintenance screen are read-only when they should be editable
- Certain grid rows are read-only

### Root Cause

There are several scenarios that make fields read-only:

1. **Integration mode**: When `IsIntegrationMode` is true and fields are in `IntegrationScreenFields[SrcModuleCode]`
2. **MPS Source**: When `SourceCode = "MPS"` (Measurement Information Process System), contact fields and capacity fields become read-only
3. **Attribute read-only flag**: When `LocAttrDO.IsScreenReadOnly = true`, the attribute row is read-only (except NOM and ALL)
4. **Capacity/Rate Area in integration mode**: When `IsIntegrationMode && CheckIstheSystemIntegrated` and record is `Unchanged`

### Diagnostic Steps

```sql
-- Check location source module
SELECT mh.MTR_NO, mh.SRC_MODULE_CODE
FROM MTR_HEADER mh
WHERE mh.METER_NO = '<LocationId>';

-- Check contact source codes
SELECT lc.ID_LOC, lc.CONTACT_TYPE_CODE, lc.SOURCE_CODE
FROM PACTRL_LOC_CONTACT lc
WHERE lc.ID_LOC = '<LocationId>'
  AND lc.TSP_NO = <TspNo>;

-- Check attribute read-only configuration
SELECT LOC_ATTR_CODE, LOC_ATTR_DESCR, IS_SCREEN_READ_ONLY
FROM QCODE_LOC_ATTR
WHERE TSP_NO = <TspNo>
ORDER BY LOC_ATTR_CODE;
```

### Code Location
- **Integration field control**: `LocationMaintenanceController.cs` lines ~272-291 (`SetControlStates`)
- **Contact MPS check**: `LocationMaintenanceController.cs` lines ~843-860 (`ContactsGridUpdateControlStates`)
- **Capacity MPS check**: `LocationMaintenanceController.cs` lines ~1150-1162 (`CapacityGridUpdateControlStates`)
- **Attribute read-only**: `LocationMaintenanceController.cs` lines ~2354-2366 (`DetailsAttributeUpdateControlStates`)

### Resolution
- Check `MTR_HEADER.SRC_MODULE_CODE` to determine if the location is integration-sourced
- Verify `PACTRL_LOC_CONTACT.SOURCE_CODE` for individual contact rows
- Review `QCODE_LOC_ATTR.IS_SCREEN_READ_ONLY` for attribute configuration
- For CRA grid, check if integration mode is active

---

## Issue 7: Capacity/Rate Area Grid Issues

### Symptoms
- Capacity/Rate Area grid not loading data
- Missing location group names or type descriptions
- CRA validation errors on save (rules 042-050)

### Diagnostic Steps

```sql
-- Check location group memberships
SELECT slgl.ID_LOC, slgl.TSP_NO, slgl.ID_LOC_GRP, slgl.LOC_GRP_TYPE_CODE,
       slgl.EFF_DT_FROM, slgl.EFF_DT_TO,
       lg.LOC_GRP_NM, lgt.DESCRIPTION
FROM PACTRL_SYS_LOC_GRP_LOC slgl
JOIN PACTRL_LOC_GRP lg ON slgl.TSP_NO = lg.TSP_NO AND slgl.ID_LOC_GRP = lg.ID_LOC_GRP
JOIN QCODE_LOC_GRP_TYPE lgt ON lg.LOC_GRP_TYPE_CODE = lgt.CODE
WHERE slgl.ID_LOC = '<LocationId>'
  AND slgl.TSP_NO = <TspNo>
ORDER BY slgl.EFF_DT_FROM DESC;

-- Check location group type configuration
SELECT CODE, DESCRIPTION, IS_LOC_SCREEN, IS_LOC_SCREEN_DEFAULT, APP_LAYER_CODE, RANK
FROM QCODE_LOC_GRP_TYPE
WHERE IS_LOC_SCREEN = 1
ORDER BY RANK;
```

### Code Location
- **CRA data loading**: `QPTMServiceCore_LocationMaintenance.cs` lines ~700-703, ~856-859
- **CRA grid controller**: `LocationMaintenanceController.cs` lines ~1280-1455
- **CRA validation rules**: `Quorum.QPTM.Validations/Screens/LocationMaintenance/Validation Rules/QPTMLocationmaintenance042_CRAValidationMandatory.cs` through `050`

### Resolution
- Verify that `QCODE_LOC_GRP_TYPE` has records with `IS_LOC_SCREEN = 1`
- Check that `MetadataModuleDefinition` records exist for the user's profile and module
- Ensure location group records exist in `PACTRL_LOC_GRP`
- For mandatory field errors, review which fields are required by rules 042-050

---

## Issue 8: Location Resolution Not Triggering Batch Process

### Symptoms
- After saving location changes, downstream processes (batch resolution) do not run
- Location group assignments appear correct but are not reflected in other modules

### Root Cause
Location resolution is triggered by inserting into `PATRAN_LOC_RES_RANGE_STATUS`. The `IsDetailsLocResolve` check determines if resolution is needed, and `isUpdateLocResStatus` determines if the status should be updated.

### Diagnostic Steps

```sql
-- Check if resolution status was inserted
SELECT *
FROM PATRAN_LOC_RES_RANGE_STATUS
WHERE TSP_NO = <TspNo>
  AND TABLE_NAME = 'PACTRL_SYS_LOC_GRP_LOC'
ORDER BY EFF_DATE DESC;

-- Check LocGrpOther configuration
SELECT *
FROM PACTRL_LOC_GRP_OTHER
WHERE TSP_NO = <TspNo>;
```

### Code Location
- **Resolution check**: `QPTMServiceCore_LocationMaintenance.cs` lines ~1574-1607 (`IsDetailsLocResolve`)
- **Status update**: `QPTMServiceCore_LocationMaintenance.cs` lines ~1180-1192 (`UpdateLocResStatus`)
- **Group update**: `QPTMServiceCore_LocationMaintenance.cs` lines ~1270-1300 (`UpdatePAlocationGroupDO`)

### Resolution
- Verify that `LocGrpOther` records exist with valid `LocAttrCode` values
- Check that changes to attributes or header fields are actually being detected
- Verify `PATRAN_LOC_RES_RANGE_STATUS` records are being created
- Check batch process configuration and scheduling

---

## Issue 9: Flat Attribute Table Out of Sync

### Symptoms
- Location attributes show different values in the UI versus in reports/queries
- Queries on `PACTRL_LOC_ATTR_FLAT` return stale data
- Allocation or nomination processes use wrong attribute values

### Root Cause
The flat attribute table (`PACTRL_LOC_ATTR_FLAT`) is a denormalized copy of `PACTRL_LOC_ATTR`. It is updated via reflection in `UpdateFlatAttributeValues()`. If this process fails or is bypassed (e.g., direct database edits), the tables can become out of sync.

### Diagnostic Steps

```sql
-- Compare attribute table to flat table
SELECT la.ID_LOC, la.TSP_NO, la.EFF_DT_FROM, la.LOC_ATTR_CODE, la.IS_ATTR_TRUE,
       af.*
FROM PACTRL_LOC_ATTR la
LEFT JOIN PACTRL_LOC_ATTR_FLAT af
  ON la.ID_LOC = af.LOC_ID AND la.TSP_NO = af.TSP_NO AND la.EFF_DT_FROM = af.EFF_DT_FROM
WHERE la.ID_LOC = '<LocationId>'
  AND la.TSP_NO = <TspNo>;
```

### Code Location
- **Flat update logic**: `QPTMServiceCore_LocationMaintenance.cs` lines ~1467-1515 (`UpdateFlatAttributeValues`)

### Resolution
- Re-save the location through the UI to trigger the flat attribute sync
- If bulk correction is needed, the flat table columns are named `ATTRIND{CODE}` (e.g., `ATTRINDNOM`, `ATTRINDALL`)
- Ensure no direct database modifications bypass the service layer

---

## Issue 10: Location Contact Mass Change Not Saving

### Symptoms
- Changes made on the Location Contact Mass Change screen are lost after save
- Newly added rows disappear

### Root Cause
The mass change screen uses `BulkContainer` for managing changes. The `LocationContactMassChangeGetData` method uses `WriteAccess` to capture filters and sorts. If the bulk container state is not properly maintained, changes may be lost.

### Code Location
- **Controller**: `LocationContactMassChangeController.cs`
- **Grid data**: Line ~100-117 (`LocationContactMassChangeGetData`)
- **Bulk edit import**: Line ~244-256 (`LocationContactMassChangeBulkEdit` PUT)

### Resolution
- Verify the query parameters (IdContact, IdLoc, LocSrc, LocContactType) are set correctly
- Check that the `BulkContainer.Items` collection is properly populated after query
- Ensure the save action triggers the correct update path through the UI controller

---

## Issue 11: Location Data Not Loading After Link Navigation

### Symptoms
- Navigating to Location Maintenance from another screen (e.g., Contract Maintenance) shows blank data
- Parameters not being passed correctly

### Root Cause
The `DoUICLink` method processes incoming link parameters. It expects specific parameter names matching constant values from `QMeterHeaderQPTMConstants.ColumnNames` or `QPALocationConstants.PropertyNames`.

### Diagnostic Steps
1. Check the link parameters being passed
2. Verify they match the expected constant names

### Code Location
- **Link parameter handling**: `LocationMaintenanceController.cs` lines ~156-233 (`DoUICLink`)
- **Expected parameter names**:
  - TSP_NO or TspNo
  - LocId or Loc_Id or MeterNo
  - EFF_DT_FROM or EffDateFrom
  - EFF_DT_TO or EffDateTo
  - LocNm

### Resolution
- Ensure the calling screen passes parameters using the correct constant names
- For date range links, both EffDateFrom and EffDateTo must be provided for the `GetLatestLocationByDateRange` logic to work
- Verify that the MeterNo/LocId value is valid and not equal to `Constants.NewIdString`

---

## Issue 12: Oracle Error on Location Delete

### Symptoms
- Oracle error when deleting a location record
- Error related to temp tables in distributed transactions
- Error occurs in triggers on `SEXTN_MTR_HEADER_QPTM`

### Root Cause
This is a known issue documented in the code. When all effective date slices of a location are deleted, Oracle can encounter errors related to temp table access within distributed transactions.

### Code Location
- **Comment in code**: `QPTMServiceCore_LocationMaintenance.cs` lines ~515-517
  ```
  // TLA: Commenting out the outer transaction scope here. This is to get around an Oracle error
  // handling temp tables in distributed transactions.
  // After discussion with Engineering, adding this back in since "Delete" is when this happens
  // most often and is a rare scenario of users deleting locations
  ```
- **Transaction handling**: Lines ~518-546

### Resolution
- The current code uses `TransactionScope(RequiresNew, ReadCommitted)` which should handle most cases
- If Oracle errors persist on delete, check database triggers on `SEXTN_MTR_HEADER_QPTM`
- This is primarily a concern when all time slices of a location are being deleted simultaneously

---

## Issue 13: Affidavit Curtailment Warning Not Showing

### Symptoms
- Saving affidavit records with dates outside the curtailment period does not trigger a warning
- Expected confirmation dialog does not appear

### Root Cause
The curtailment check depends on:
1. The affidavit tab not being hidden (`IsAffidavitTabHidden()`)
2. Curtailment period configuration being set (`CurtailPeriodFrom`/`CurtailPeriodTo` not equal to `DateTime.MinValue`)
3. The affidavit record being in `Added` or `Modified` state

### Diagnostic Steps

Check TSP curtailment period configuration:
```sql
-- The curtailment dates are stored in TSP configuration
-- Check QPTMTspConfigs.CurtailPeriodFrom and CurtailPeriodTo for the TSP
```

### Code Location
- **Curtailment check**: `LocationMaintenanceController.cs` lines ~2368-2409 (`CheckCurtailment`)
- **Configuration**: `QPTMTspConfigs.CurtailPeriodFrom(tspNo)` and `QPTMTspConfigs.CurtailPeriodTo(tspNo)`

### Resolution
- Verify `CurtailPeriodFrom` and `CurtailPeriodTo` TSP configurations are set
- The client-side code must call `CheckCurtailment` before the actual save
- Verify the affidavit tab is not hidden for the current location type

---

## Issue 14: Duplicate Contact Type Validation Errors

### Symptoms
- Validation error about duplicate contacts of a single-instance type (OPR, CNF, LOC, ACM, OPA)
- Error occurs even when only one contact of that type appears in the grid

### Root Cause
The validation rules 018-024 check for unique contact types. If a deleted contact record still exists in the data (with `DataObjectState.Deleted`), it might cause false positives depending on the validation logic, or a save via integration may have introduced duplicates.

### Diagnostic Steps

```sql
SELECT ID_LOC, TSP_NO, EFF_DT_FROM, CONTACT_TYPE_CODE, ID_CONTACT, SOURCE_CODE
FROM PACTRL_LOC_CONTACT
WHERE ID_LOC = '<LocationId>'
  AND TSP_NO = <TspNo>
  AND CONTACT_TYPE_CODE IN ('OPR', 'CNF', 'LOC', 'ACM', 'OPA')
ORDER BY EFF_DT_FROM, CONTACT_TYPE_CODE;
```

### Code Location
- `QPTMLocationMaintenance018_ValidateContactTypeConfirmParty.cs`
- `QPTMLocationMaintenance019_ValidateContactTypeLocationAnalyst.cs`
- `QPTMLocationMaintenance020_ValidateContactTypeOperator.cs`

### Resolution
- Remove duplicate contacts of the single-instance types
- If contacts were created via integration (MPS), verify the integration is not creating duplicates
- Ensure only one active contact per single-instance type per effective date

---

## Diagnostic SQL Queries

### General Location Lookup

```sql
-- Full location record
SELECT mh.METER_NO, mh.METER_NAME, mh.STATUS_CODE, mh.EFF_DT_FROM, mh.EFF_DT_TO,
       mhq.TSP_NO, mhq.POV_CODE, mhq.LOC_TYPE_CODE, mhq.LOC_PURP_CODE,
       mhq.BI_DIRECT_LOC_ID, mhq.SHADOW_LOC_ID, mhq.TRANSFER_LOC_ID,
       mhq.FACILITY_ID, mhq.FIELD_CODE, mhq.SUBSEQ_NO
FROM MTR_HEADER mh
JOIN SEXTN_MTR_HEADER_QPTM mhq ON mh.METER_NO = mhq.MTR_NO AND mh.EFF_DT_FROM = mhq.EFF_DT_FROM
WHERE mh.METER_NO = '<LocationId>'
  AND mhq.TSP_NO = <TspNo>
ORDER BY mh.EFF_DT_FROM DESC;
```

### Location Attributes

```sql
SELECT la.ID_LOC, la.LOC_ATTR_CODE, qa.LOC_ATTR_DESCR, la.IS_ATTR_TRUE, la.EFF_DT_FROM
FROM PACTRL_LOC_ATTR la
JOIN QCODE_LOC_ATTR qa ON la.LOC_ATTR_CODE = qa.LOC_ATTR_CODE AND la.TSP_NO = qa.TSP_NO
WHERE la.ID_LOC = '<LocationId>'
  AND la.TSP_NO = <TspNo>
ORDER BY la.EFF_DT_FROM DESC, la.LOC_ATTR_CODE;
```

### Location Contacts with Business Associate Details

```sql
SELECT lc.ID_LOC, lc.TSP_NO, lc.CONTACT_TYPE_CODE, lc.ID_CONTACT, lc.SOURCE_CODE,
       lc.EFF_DT_FROM, c.FIRST_NM, c.LAST_NM, c.PRIMARY_BP_NO, ba.BP_NM
FROM PACTRL_LOC_CONTACT lc
LEFT JOIN KCTRL_CONTACT c ON lc.ID_CONTACT = c.ID_CONTACT
LEFT JOIN KCTRL_BUSINESS_ASSOCIATE ba ON c.PRIMARY_BP_NO = ba.BP_NO
WHERE lc.ID_LOC = '<LocationId>'
  AND lc.TSP_NO = <TspNo>
ORDER BY lc.EFF_DT_FROM DESC, lc.CONTACT_TYPE_CODE;
```

### Aggregate (Parent-Child) Relationships

```sql
-- Children of a parent
SELECT la.ID_LOC AS PARENT_LOC, la.ID_CHILD_LOC, la.EFF_DT_FROM, la.EFF_DT_TO,
       pl.LOC_NM AS CHILD_LOC_NAME
FROM PACTRL_LOC_AGGREGATE la
LEFT JOIN PACTRL_LOC pl ON la.ID_CHILD_LOC = pl.ID_LOC AND la.TSP_NO = pl.TSP_NO
  AND la.EFF_DT_FROM BETWEEN pl.EFF_DT_FROM AND pl.EFF_DT_TO
WHERE la.ID_LOC = '<ParentLocationId>'
  AND la.TSP_NO = <TspNo>
ORDER BY la.EFF_DT_FROM DESC, la.ID_CHILD_LOC;

-- Parent of a child
SELECT la.ID_LOC AS PARENT_LOC, la.ID_CHILD_LOC, la.EFF_DT_FROM, la.EFF_DT_TO,
       pl.LOC_NM AS PARENT_LOC_NAME
FROM PACTRL_LOC_AGGREGATE la
LEFT JOIN PACTRL_LOC pl ON la.ID_LOC = pl.ID_LOC AND la.TSP_NO = pl.TSP_NO
  AND la.EFF_DT_FROM BETWEEN pl.EFF_DT_FROM AND pl.EFF_DT_TO
WHERE la.ID_CHILD_LOC = '<ChildLocationId>'
  AND la.TSP_NO = <TspNo>
ORDER BY la.EFF_DT_FROM DESC;
```

### Location Group Memberships

```sql
SELECT slgl.ID_LOC, slgl.TSP_NO, slgl.ID_LOC_GRP, slgl.LOC_GRP_TYPE_CODE,
       slgl.EFF_DT_FROM, slgl.EFF_DT_TO,
       lg.LOC_GRP_NM, lgt.DESCRIPTION AS LOC_GRP_TYPE_DESCR
FROM PACTRL_SYS_LOC_GRP_LOC slgl
JOIN PACTRL_LOC_GRP lg ON slgl.TSP_NO = lg.TSP_NO AND slgl.ID_LOC_GRP = lg.ID_LOC_GRP
LEFT JOIN QCODE_LOC_GRP_TYPE lgt ON lg.LOC_GRP_TYPE_CODE = lgt.CODE
WHERE slgl.ID_LOC = '<LocationId>'
  AND slgl.TSP_NO = <TspNo>
ORDER BY slgl.EFF_DT_FROM DESC, slgl.LOC_GRP_TYPE_CODE;
```

### Bidirectional Location Pair Check

```sql
SELECT mh1.MTR_NO AS LOC1, mh1.POV_CODE AS LOC1_POV, mh1.BI_DIRECT_LOC_ID AS LOC1_BIDIR,
       mh2.MTR_NO AS LOC2, mh2.POV_CODE AS LOC2_POV, mh2.BI_DIRECT_LOC_ID AS LOC2_BIDIR,
       mh1.EFF_DT_FROM AS LOC1_FROM, mh1.EFF_DT_TO AS LOC1_TO,
       mh2.EFF_DT_FROM AS LOC2_FROM, mh2.EFF_DT_TO AS LOC2_TO
FROM SEXTN_MTR_HEADER_QPTM mh1
LEFT JOIN SEXTN_MTR_HEADER_QPTM mh2 ON mh1.BI_DIRECT_LOC_ID = mh2.MTR_NO
  AND mh1.TSP_NO = mh2.TSP_NO
WHERE mh1.MTR_NO = '<LocationId>'
  AND mh1.TSP_NO = <TspNo>;
```

### Location Resolution Status

```sql
SELECT TSP_NO, TABLE_NAME, EFF_DATE, IS_CHANGE
FROM PATRAN_LOC_RES_RANGE_STATUS
WHERE TSP_NO = <TspNo>
ORDER BY EFF_DATE DESC;
```

### Flat Attribute Verification

```sql
SELECT LOC_ID, TSP_NO, EFF_DT_FROM, EFF_DT_TO,
       ATTRINDNOM, ATTRINDALL, ATTRINDAGR, ATTRINDPL, ATTRINDIC,
       ATTRINDSTR, ATTRINDEND, ATTRINDMP, ATTRINDACM, ATTRINDAAF
FROM PACTRL_LOC_ATTR_FLAT
WHERE LOC_ID = '<LocationId>'
  AND TSP_NO = <TspNo>
ORDER BY EFF_DT_FROM DESC;
```

---

*Cross-references:*
- [Domain Documentation](./domain.md) -- Business concepts and rules
- [Architecture Documentation](./architecture.md) -- Technical implementation details

*Last updated: 2026-03-03*

*Document version: 1.0*
