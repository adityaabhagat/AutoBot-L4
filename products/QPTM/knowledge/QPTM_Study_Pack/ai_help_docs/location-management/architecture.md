---
title: Location Management (LOC) - Technical Architecture
category: architecture
feature: Location Management (LOC)
related_repos: Web, Batch
keywords: LOC, LocationMaintenanceController, LocationPathMaintenanceController, LocationContactMassChangeController, QPTMServiceCore_LocationMaintenance, MeterHeaderQPTMDO, MeterHeaderCompleteDO, PALocationDO, PACTRL_LOC, SEXTN_MTR_HEADER_QPTM, PACTRL_LOC_AGGREGATE, PACTRL_LOC_CONTACT, validation, PACTRL_LOC_ATTR, QUIControllerLocationMaintenance, LocationMaintenanceData
last_updated: 2026-03-03
---

# Location Management (LOC) - Technical Architecture

## Overview

This document covers the **technical implementation** of the Location Management feature in QPTM. It details the code structure, data objects, service methods, validation rules, and database tables.

For business concepts, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Controller Layer](#controller-layer)
3. [Service Layer](#service-layer)
4. [Data Objects](#data-objects)
5. [Database Tables](#database-tables)
6. [Validation Rules](#validation-rules)
7. [UI Controller](#ui-controller)
8. [View Models](#view-models)
9. [Configuration](#configuration)
10. [Events and Notifications](#events-and-notifications)
11. [Key Code Flows](#key-code-flows)
12. [API Reference](#api-reference)

---

## Architecture Overview

```
Web Layer (MVC Controllers)
  LocationMaintenanceController.cs          (2444 lines) - Main location screen
  LocationPathMaintenanceController.cs      (247 lines)  - Path maintenance screen
  LocationContactMassChangeController.cs    (260 lines)  - Contact mass change screen

UI Controllers (Business Logic Orchestration)
  QUIControllerLocationMaintenance          - Main screen orchestrator
  QUIControllerLocationPathMaintenance      - Path screen orchestrator
  QUIControllerLocationContactMassChange    - Mass change orchestrator

Service Layer
  QPTMServiceCore_LocationMaintenance.cs    (1768 lines) - Core service methods

Validation Layer
  52+ validation rules (QPTMLocationMaintenance001 through 052)
  QPTMLocationMaintenanceCompleteValidationContext
  QPTMLocationMaintenanceValidationContextBase

Data Objects
  MeterHeaderQPTMDO / MeterHeaderDO / MeterHeaderCompleteDO
  PALocationDO, PALocationAggregateDO, PALocationContactDO
  PALocationAttributeDO, PALocationAttributeFlatDO
  PALocationOwnerDO, PALocationProducerDO, PALocationInterconnectDO
  PALocationAssociationDO, PALocationAffidavitDO
  PAEutBrokerDO, PALocSupplierPinsDO, PALocationCapDO
  PASysLocGroupLocationDO, PALocationCtrChildDO
  PALocationPathHdrDO, PALocationPathDO
  LocationMaintenanceData (screen state)

Data Access Interfaces
  IQPTMDataAccess_MeterHeaderQPTM
  IQESUITEDataAccess_MeterHeaderComplete
  IQPTMDataAccess_PALocation, IQPTMDataAccess_PALocationAggregate
  IQPTMDataAccess_PALocationContact, IQPTMDataAccess_PALocGroup
  (and many more)
```

---

## Controller Layer

### LocationMaintenanceController

**File**: `Quorum.QPTM.Web.Core/Controllers/LocationMaintenanceController.cs` (2444 lines)
**Namespace**: `Quorum.QPTM.Web.Controllers`
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.LocationMaintenance)]`
**Base Class**: `LocationControllerBase<QUIControllerLocationMaintenance, LocationMaintenanceRootVM>`

This is the primary MVC controller for the Location Maintenance screen. It manages 16+ tabs and their associated grid operations.

#### Actions and Links

| Method | Description |
|---|---|
| `GetActions()` | Returns Query, Save (with `ValidateBeforeSave` override), Delete, Close, New, Copy |
| `GetLinks()` | Returns links to Allocation Plan Maintenance, Measurement Results, Location Group Lookup |
| `DoUICLink()` | Handles incoming link parameters (TspNo, MeterNo, EffDateFrom, EffDateTo) |

#### Tab Rendering Methods

Each tab has an `HttpGet` method returning a partial view:

| Method | View Path | Tab Name |
|---|---|---|
| `DetailsTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Details.cshtml` | Details |
| `ContactsTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Contacts.cshtml` | Contacts |
| `GeographicTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Geographic.cshtml` | Geographic |
| `AssociatedNamesTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_AssociatedNames.cshtml` | Associated Names |
| `ChildLocationsTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_ChildLocations.cshtml` | Child Locations |
| `BrokersTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Brokers.cshtml` | Brokers |
| `AffidavitTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Affidavit.cshtml` | Affidavit |
| `ChildLocationForAllocationTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_ChildLocationForAllocation.cshtml` | Child Loc for Allocation |
| `OwnershipTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Ownership.cshtml` | Ownership |
| `ProducersTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Producers.cshtml` | Producers |
| `InterConnectTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_InterConnect.cshtml` | Interconnect |
| `CapacityTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_Capacity.cshtml` | Capacity |
| `CapacityRateAreaTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_CapacityRateArea.cshtml` | Capacity/Rate Area |
| `UserDefinedTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_UserDefined.cshtml` | User Defined |
| `SupplierLocationTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_SupplierLocation.cshtml` | Supplier Location |
| `LDCTab()` | `~/Views/LocationMaintenance/_LocationMaintenance_LDC.cshtml` | LDC |

#### Field Update Methods

| Method | Target Data Object |
|---|---|
| `LocationMaintenanceFieldUpdate()` | `uic.MeterHeader` |
| `MeterHeaderQPTMFieldUpdate()` | `uic.MeterHeaderQPTM` |
| `UserDefinedFieldUpdate()` | `uic.MeterHeaderQPTM.PALocationUserDefine` |
| `PALocationInterconnectFieldUpdate()` | `uic.MeterHeaderQPTM.PALocationInterconnect` |
| `LDCLocationMaintenanceFieldUpdate()` | `uic.MeterHeader.MeterHeaderLDCBindingList` |

#### Grid Operations (per tab)

Each grid tab follows the standard pattern with these operations:

| Operation Pattern | Method Name Pattern |
|---|---|
| Get Data | `Get{TabName}()` or `{TabName}GridGetData()` |
| Update Row | `{TabName}GridUpdate()` |
| Add New Row | `{TabName}GridAddNewRow()` |
| Delete Row | `{TabName}GridDeleteRow()` |
| Bulk Edit (GET) | `{TabName}GridBulkEdit()` (GET) |
| Bulk Edit (PUT) | `{TabName}GridBulkEdit()` (PUT) |
| Excel Export | `{TabName}GridExcelExport()` |
| Excel Import | `{TabName}GridExcelImport()` |

**Grid IDs** (from `Constants.GridIDs`):
- `LocMainDetailsAttrGrid` - Details/Attributes grid
- `LocMainContactsGrid` - Contacts grid
- `LocMainChildLocationsGrid` - Child Locations grid
- `LocMainBrokersGrid` - Brokers grid
- `LocMainCapacityGrid` - Capacity grid
- `LocMainCapacityRateAreaGrid` - Capacity/Rate Area grid
- `LocMainOwnershipGrid` - Ownership grid
- `LocMainProducersGrid` - Producers grid
- `LocMainChildLocationForAllocationGrid` - Child Locations for Allocation grid
- `LocMainAffidavitGrid` - Affidavit grid
- `LocMainSupplierLocationGrid` - Supplier Location grid
- `ParentLocationHistoryGrid` - Parent Location History grid

#### Helper Methods

| Method | Description |
|---|---|
| `ShowHideTabsBasedOnLocTypeCode()` | Returns dictionary of tab visibility based on location type and LDC mode |
| `GetLocationAttribute()` | Returns attribute-based control states and tab visibility flags |
| `CheckCurtailment()` | Validates affidavit dates against curtailment periods before save |
| `FillDefault()` | Fills default values on the screen |

### LocationPathMaintenanceController

**File**: `Quorum.QPTM.Web.Core/Controllers/LocationPathMaintenanceController.cs` (247 lines)
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.LocationPathMaintenance)]`
**Base Class**: `SystemSetupControllerBase<QUIControllerLocationPathMaintenance, LocationPathMaintenanceRootVM>`

Manages path maintenance with a single grid for path details.

| Method | Description |
|---|---|
| `LocationPathMaintenanceFieldUpdate()` | Updates path header fields |
| `LocationPathMaintenanceGridGetData()` | Gets path grid data |
| `LocationPathMaintenanceGridUpdate()` | Updates path grid row |
| `LocationPathMaintenanceGridAddNewRow()` | Adds new path row (with clone support) |
| `LocationPathMaintenanceGridDeleteRow()` | Deletes path row |
| `LocationPathMaintenanceGridExcelExport()` | Excel export |
| `LocationPathMaintenanceGridExcelImport()` | Excel import |
| `LocationPathMaintenanceGridBulkEdit()` | Bulk edit (GET/PUT) |
| `ValidateBeforeSave()` | Checks if effective dates have changed |

### LocationContactMassChangeController

**File**: `Quorum.QPTM.Web.Core/Controllers/LocationContactMassChangeController.cs` (260 lines)
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.LocationContactMassChange)]`
**Base Class**: `QMvcQPTMBaseScreenController<QUIControllerLocationContactMassChange, LocationContactMassChangeRootVM>`

Supports bulk contact operations with select/deselect functionality.

| Method | Description |
|---|---|
| `LocationContactMassChangeGetData()` | Gets contact data via `BulkContainer.Items` |
| `LocationContactMassChangeUpdate()` | Updates contact row |
| `LocationContactMassChangeAddNewRow()` | Adds/clones contact row |
| `LocationContactMassChangeDeleteRow()` | Deletes single row |
| `LocationContactMassChangeAddSelectedRow()` | Clones all selected rows |
| `LocationContactMassChangeDeleteSelectedRow()` | Deletes all selected rows |
| `LocationContactMassChangeHeaderSelectedObjectsChanged()` | Handles row selection changes |
| `LocationContactMassChangeExcelExport()` | Excel export |
| `LocationContactMassChangeBulkEdit()` | Bulk edit (GET/PUT) |

---

## Service Layer

### QPTMServiceCore_LocationMaintenance

**File**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_LocationMaintenance/QPTMServiceCore_LocationMaintenance.cs` (1768 lines)
**Class**: `QPTMServiceCore` (partial class)
**Implements**: `IQPTMService_LocationMaintenance`

The service layer is organized into two major sections:

#### MeterHeaderQPTM Methods (Simple Location Data)

| Method | Description |
|---|---|
| `GetSingleLocationMaintenance(mtrNo, effDateFrom)` | Gets a single `MeterHeaderQPTMDO` by meter number and effective date |
| `GetMultipleLocationMaintenance(filters, sortList, numRecords)` | Gets multiple `MeterHeaderQPTMDO` records with filtering and pagination |
| `UpdateSingleLocationMaintenance(updateItem)` | Validates and saves a single `MeterHeaderQPTMDO` |
| `UpdateMultipleLocationMaintenance(updateList)` | Validates and saves multiple `MeterHeaderQPTMDO` records |
| `ValidateSingleLocationMaintenance(validateItem, context)` | Validates a single record |
| `ValidateMultipleLocationMaintenance(validateList, context)` | Validates multiple records |

#### MeterHeaderQPTMComplete Methods (Full Location with Children)

| Method | Description |
|---|---|
| `GetSingleLocationMaintenanceComplete(locationMaintenanceData)` | Gets a complete location record with all child objects (contacts, attributes, aggregates, brokers, etc.) |
| `GetLatestLocationByDateRange(tspNo, filters)` | Gets the latest location record within a date range using the location cache |
| `UpdateSingleLocationMaintenanceComplete(updateItem)` | Full save workflow: PreSave -> Validate -> Transaction (Update, FlatAttr, LocResStatus, CAScheduleObj) |
| `ValidateSingleLocationMaintenanceComplete(validateItem, context)` | Validates via `QPTMLocationMaintenanceCompleteValidationContext` |
| `GetAggregateLocationHistory(filters)` | Gets aggregate location history with LDC enrollment dates |

#### Key Helper Methods

| Method | Description |
|---|---|
| `AddAdditionalPropertiesLocationMaintenanceComplete()` | ~300 lines. Joins and enriches the complete location with contacts, locations, business associates, field details, contract data, interconnects, capacity rates, and supplier pins |
| `LoadScreenDefaults(locationMaintenanceData)` | Loads default values for the screen: company address, location attributes, confirm party dict, curtailment dates, association types, location group types |
| `UpdateAndHandleEvents(updateItem, ...)` | Executes update within event detection context. Handles delete-all-slices scenario, flat attribute updates, and clone for notifications |
| `AddDeleteCAScheduleObjectCustom(updateItem)` | Creates/deletes bidirectional scheduling objects based on BiDirectLocId and PovCode |
| `UpdateFlatAttributeValues(updateItem)` | Uses reflection to update `PALocationAttributeFlat` columns from `PALocationAttribute` records |
| `UpdateLocResStatus(tspNo)` | Inserts `PatranLocResRangeStatus` record to trigger batch resolution |
| `UpdatePAlocationGroupDO(locGrpOtherList)` | Updates `PALocGroup` records with new SetId for batch processing |
| `IsDetailsLocResolve(updateItem, otherAttrs)` | Determines if location changes require resolution processing |
| `GetLocAttrList(tspNo)` | Gets location attribute configuration for a TSP |
| `GetLocationAttrDOList(locDOList)` | Converts `LocAttrDO` to `PALocationAttributeDO` for screen display |
| `GetDefaultCnfParty()` | Gets all contacts with business associate names for confirm party selection |

#### Streaming Methods

All public service methods have a `*Streaming` counterpart (e.g., `GetSingleLocationMaintenanceStreaming`) that serializes/deserializes via `QStreamedMessage` for WCF service communication.

---

## Data Objects

### Primary Data Objects

| Data Object | Database Table | Description |
|---|---|---|
| `MeterHeaderDO` | `MTR_HEADER` | ESuite meter header (base location record) |
| `MeterHeaderQPTMDO` | `SEXTN_MTR_HEADER_QPTM` | QPTM extension of meter header with pipeline-specific fields |
| `MeterHeaderCompleteDO` | (Composite) | Complete location object containing all child collections |
| `PALocationDO` | `PACTRL_LOC` | Pipeline admin location record |
| `LocationMaintenanceData` | (No DB - screen state) | Screen state object for Location Maintenance |

### Child Data Objects on MeterHeaderQPTMDO

| Data Object | Database Table | Description |
|---|---|---|
| `PALocationContactDO` | `PACTRL_LOC_CONTACT` | Location contacts (operator, confirm party, etc.) |
| `PALocationAttributeDO` | `PACTRL_LOC_ATTR` | Location attributes (boolean flags) |
| `PALocationAttributeFlatDO` | `PACTRL_LOC_ATTR_FLAT` | Denormalized attribute flat table |
| `PALocationOwnerDO` | `PACTRL_LOC_OWNER` | Location ownership records |
| `PALocationInterconnectDO` | `PACTRL_LOC_INTERCONNECT` | Interconnect configuration |
| `PALocationAssociationDO` | `PACTRL_LOC_ASSOCIATION` | Associated names (interconnect loc, DRN, etc.) |
| `PALocationUserDefineDO` | `PACTRL_LOC_USER_DEFINE` | User-defined fields |

### Child Data Objects on MeterHeaderCompleteDO

| Data Object | Database Table | Description |
|---|---|---|
| `PALocationAggregateDO` | `PACTRL_LOC_AGGREGATE` | Parent-child aggregate relationships |
| `PALocationAggregateLDCDO` | `PACTRL_LOC_AGGREGATE_LDC` | LDC enrollment data for aggregates |
| `PAEutBrokerDO` | `PACTRL_EUT_BROKER` | End-user transportation broker records |
| `PALocationAffidavitDO` | `PACTRL_LOC_AFFIDAVIT` | Affidavit records |
| `PALocationCtrChildDO` | `PACTRL_LOC_CTR_CHILD` | Child locations for allocation |
| `PALocationProducerDO` | `PACTRL_LOC_PRODUCER` | Producer associations |
| `PASysLocGroupLocationDO` | `PACTRL_SYS_LOC_GRP_LOC` | Location group memberships |
| `PALocSupplierPinsDO` | `PACTRL_LOC_SUPPLIER_PINS` | Supplier pin associations |
| `PALocationCapDO` | `PACTRL_LOC_CAP` | Capacity records |

### Supporting Data Objects

| Data Object | Description |
|---|---|
| `PALocGroupDO` | Location group definition |
| `LocationGroupTypeDO` | Location group type code table |
| `LocAttrDO` | Location attribute code table configuration |
| `LocGrpOtherDO` | Location group other attributes |
| `AssocLocationTypeDO` | Associated location type code table |
| `ContactDO` | Contact master record |
| `BusinessAssociateDO` | Business associate master record |
| `ContractHeaderValdDO` | Contract header validation data |
| `BATaxIdDO` | Business associate tax ID (for FERC CID) |
| `FieldDO` | Geographic field code lookup |
| `CAScheduleObjectCustomDO` | Custom scheduling object for bidirectional pairs |
| `PatranLocResRangeStatusDO` | Location resolution range status |
| `TspConfigurationControlDO` | TSP configuration control |
| `MetadataModuleDefinitionDO` | Metadata module definition for profile-based config |
| `PALocationPathHdrDO` | Location path header |
| `PALocationPathDO` | Location path detail |
| `CapTypeDO` | Capacity type code table |

### MeterHeaderCompleteDO Extension

**File**: `Quorum.QPTM.DataObject/MeterHeaderCompleteDOExt.cs`

Adds the `SetId` property for tracking location group resolution batch IDs.

---

## Database Tables

### Core Tables

| Table | Key Columns | Description |
|---|---|---|
| `MTR_HEADER` | MeterNo, EffDateFrom | Base meter/location header (ESuite) |
| `SEXTN_MTR_HEADER_QPTM` | MtrNo, TspNo, EffDateFrom | QPTM extension with PovCode, LocTypeCode, LocPurpCode, BiDirectLocId, etc. |
| `PACTRL_LOC` | IdLoc, TspNo, EffDateFrom | Pipeline admin location master record |
| `PACTRL_LOC_CONTACT` | IdLoc, TspNo, EffDateFrom, ContactTypeCode | Location contacts |
| `PACTRL_LOC_ATTR` | IdLoc, TspNo, EffDateFrom, LocAttrCode | Location attribute flags |
| `PACTRL_LOC_ATTR_FLAT` | LocId, TspNo, EffDateFrom | Denormalized attribute columns (ATTRIND*) |
| `PACTRL_LOC_AGGREGATE` | IdLoc, TspNo, IdChildLoc, EffDateFrom | Parent-child aggregate relationships |
| `PACTRL_LOC_AGGREGATE_LDC` | (child of AGGREGATE) | LDC enrollment dates |
| `PACTRL_LOC_OWNER` | (child of SEXTN_MTR_HEADER_QPTM) | Location ownership |
| `PACTRL_LOC_INTERCONNECT` | (child of SEXTN_MTR_HEADER_QPTM) | Interconnect configuration |
| `PACTRL_LOC_ASSOCIATION` | (child of SEXTN_MTR_HEADER_QPTM) | Associated names |
| `PACTRL_LOC_USER_DEFINE` | (child of SEXTN_MTR_HEADER_QPTM) | User-defined fields |
| `PACTRL_EUT_BROKER` | LocId, TspNo, BpNo, EffDateFrom | End-user transportation brokers |
| `PACTRL_LOC_AFFIDAVIT` | IdLoc, TspNo, AffidavitBpNo, EffDateFrom | Affidavit records |
| `PACTRL_LOC_CTR_CHILD` | LocId, TspNo, ChildLocId, EffDateFrom | Child locations for allocation |
| `PACTRL_LOC_PRODUCER` | IdLoc, TspNo, BpNo, EffDateFrom | Producer associations |
| `PACTRL_SYS_LOC_GRP_LOC` | IdLoc, TspNo, IdLocGrp, EffDateFrom | Location group memberships |
| `PACTRL_LOC_GRP` | IdLocGrp, TspNo | Location group definition |
| `PACTRL_LOC_SUPPLIER_PINS` | LocId, TspNo, SupplierLocId, EffDateFrom | Supplier pin associations |
| `PACTRL_LOC_CAP` | (child of MeterHeaderComplete) | Capacity records |

### Code Tables

| Table | Description |
|---|---|
| `QCODE_LOC_ATTR` | Location attribute code definitions |
| `QCODE_POV` | Point of View codes (R, D, B) |
| `QCODE_LOC_GRP_TYPE` | Location group type codes |
| `QCODE_CONTACT_TYPE` | Contact type codes (OPR, CNF, LOC, etc.) |
| `QCODE_ASSOC_LOC_TYPE` | Associated location type codes |
| `QCODE_LOC_QTY_TYPE_IND` | Location quantity type indicators |
| `QCODE_CAP_TYPE` | Capacity type codes |

### Supporting Tables

| Table | Description |
|---|---|
| `KCTRL_CONTACT` | Contact master record |
| `KCTRL_BUSINESS_ASSOCIATE` | Business associate master |
| `KCTRL_BA_TAX_ID` | Business associate tax IDs (FERC CID lookup) |
| `PATRAN_LOC_RES_RANGE_STATUS` | Location resolution status tracking |
| `PACTRL_CA_SCHD_OBJ_CUST` | Custom scheduling objects (bidirectional pairs) |
| `PACTRL_LOC_GRP_OTHER` | Location group other attributes |
| `PACTRL_LOC_PATH_HDR` | Location path header |
| `PACTRL_LOC_PATH` | Location path detail |

---

## Validation Rules

All validation rules inherit from `QPTMLocationMaintenanceValidationContextBase` which extends `QPTMValidationBase<QPTMLocationMaintenanceCompleteValidationContext>`.

**Validation Context**: `QPTMLocationMaintenanceCompleteValidationContext`
- Located at: `Quorum.QPTM.Validations/Screens/LocationMaintenance/Context/`
- Implements `IQQPTMEffectiveDatedItemsProviderCollection`
- Created with the complete object list and TSP number

### Validation Rule Index

| Rule | Class | Description |
|---|---|---|
| 001 | `ValidateEfftDate` | Validates effective date consistency |
| 002 | `ValidateLocationAttribute` | Validates location attribute values |
| 003 | `ValidateChildLocation` | Validates child location configuration |
| 004 | `ValidateLocationContract` | Validates location-contract relationships |
| 005 | `ValidateTspAndMtr` | Validates TSP number and meter number combination |
| 006 | `ValidateMtrIntegration` | Validates meter integration fields |
| 007 | `ValidateLocationSource` | Validates location source code |
| 008 | `ValidateBrokerEffDt` | Validates broker effective dates |
| 009 | `ValidateChildrenDelete` | Validates deletion of child records |
| 010 | `ValidateChildParentEffDt` | Validates child-parent effective date ranges |
| 011 | `ValidateChildLocActive` | Validates child location active status |
| 012 | `ValidateChildLocOperator` | Validates child location operator |
| 013 | `ValidateLocationOperImpArea` | Validates location operator impact area |
| 014 | `ValidateChildPovParentBidirect` | Validates child POV against parent bidirectional |
| 015 | `ValidateChildLocId` | Validates child location ID |
| 016 | `ValidateAllocAttribute` | Validates allocation attribute settings |
| 017 | `ValidateChildLocEffDt` | Validates child location effective dates |
| 018 | `ValidateContactTypeConfirmParty` | Validates confirm party contact type uniqueness |
| 019 | `ValidateContactTypeLocationAnalyst` | Validates location analyst contact type uniqueness |
| 020 | `ValidateContactTypeOperator` | Validates operator contact type uniqueness |
| 021 | `ValidateContactEffDtChange` | Validates contact effective date changes |
| 022 | `ValidateContactTypeOprSync` | Validates operator contact type sync |
| 023 | `ValidateContactDelete` | Validates contact deletion impacts |
| 024 | `ValidateContactTypeChange` | Validates contact type changes |
| 025 | `ValidateNomLocationAttribute` | Validates nominatable location attribute |
| 026 | `ValidateCurrentCompanyCd` | Validates current company code |
| 027 | `ValidatePOI` | Validates Point of Interconnection |
| 028 | `ValidateAttrCode` | Validates attribute code consistency |
| 029 | `ValidateFuelSubSequenceValue` | Validates fuel subsequence values |
| 030 | `ValidateAllocatePhysicalAttr` | Validates allocate physical attribute |
| 031 | `ValidateBidirectional` | Validates bidirectional location configuration |
| 032 | `ValidateBidirectionalEffDate` | Validates bidirectional effective date ranges |
| 033 | `IsOtherLocationAssociated` | Checks if other locations are associated |
| 034 | `ValidateChangeOfDate` | Validates date changes |
| 035 | `ValidateOwnerShipPercentage` | Validates ownership percentage totals |
| 036 | `ValidateProducersEffectiveDate` | Validates producer effective dates |
| 037 | `ValidateCapacitySourceCode` | Validates capacity source code |
| 038 | `ValidateCapacityEffectiveDateRange` | Validates capacity effective date ranges |
| 039 | `ValidateChildLocForAllocKey` | Validates child location for allocation key |
| 040 | `ValidateAffidavitCurtailmentDates` | Validates affidavit curtailment dates |
| 041 | `ValidateSupplierPinDuplicate` | Validates supplier pin duplicates |
| 042-049 | `CRAValidationMandatory` (various) | Capacity/Rate Area mandatory field validations |
| 050 | `CRARequiredFieldValidation` | Capacity/Rate Area required field validation |
| 051 | `ValidateAggregateLocationAttribute` | Validates aggregate location attribute consistency |
| 052 | `ValidateIntegrationScreenFields` | Validates integration screen field restrictions |

**Validation file location**: `Quorum.QPTM.Validations/Screens/LocationMaintenance/Validation Rules/`

---

## UI Controller

### QUIControllerLocationMaintenance

The UI controller manages screen state and orchestrates data loading.

**Key Properties:**

| Property | Type | Description |
|---|---|---|
| `MeterHeader` | `MeterHeaderDO` | ESuite meter header record |
| `MeterHeaderQPTM` | `MeterHeaderQPTMDO` | QPTM extension record (contains contacts, attributes, owners, etc.) |
| `MeterHeaderComplete` | `MeterHeaderCompleteDO` | Complete object (contains aggregates, brokers, affidavits, etc.) |
| `LocationMaintenanceData` | `LocationMaintenanceData` | Screen defaults and configuration |
| `MyParams` | (custom) | Screen parameters: TspNo, MeterNo, EffDateFrom, EffDateTo, AsOfDate, child/allocation/affidavit/capRate/supplierPins AsOfDates |
| `TspNo` | `short` | Current TSP number |
| `AsOfDate` | `DateTime` | Current effective date |
| `HiddenTabsList` | `Dictionary<string, bool>` | Tab visibility flags |
| `IsIntegrationMode` | `bool` | Integration mode flag |
| `IntegrationScreenFields` | `Dictionary<string, Collection<string>>` | Fields read-only per source module |
| `IsEnableUOM` | `bool` | UOM enabled flag |
| `AvailableAssocLocation` | `IEnumerable<AssocLocationTypeDO>` | Available association types for Associated Names tab |
| `ParentLocationHistory` | `Collection<PALocationAggregateDO>` | Parent location history records |

**Key Methods:**

| Method | Description |
|---|---|
| `Query()` | Executes search and loads complete location |
| `FillDefault()` | Fills default values for new locations |
| `ValidateBeforeSave()` | Pre-save validation returning effective date change flags |
| `IsCapacityRateAreaGridReadOnly(dataObject)` | Determines if CRA grid row is read-only |
| `IsAffidavitTabHidden()` | Checks if affidavit tab should be hidden |

### QUIControllerLocationPathMaintenance

| Property | Description |
|---|---|
| `PALocationPathHdr` | Path header data object |
| `TspPreference` | TSP preference (energy/volume UOM) |

### QUIControllerLocationContactMassChange

| Property | Description |
|---|---|
| `BulkContainer` | Container for bulk contact operations |
| `PALocationContact` | Contact data object |
| `Filters` / `Sorts` | Applied grid filters and sorts |

---

## View Models

### LocationMaintenanceRootVM

Root view model containing all header fields and screen state. Key properties include:
- MeterNo, MeterName, TspNo, EffDateFrom, EffDateTo
- PovCode, LocPurpCode, StatusCode, LocTypeCode
- ParentLoc, OperatorID, ConfirmParty
- Details tab: DrnNo, FacilityId, TransferLocId, ShadowLocId, BiDirectLocId, etc.
- Geographic tab: IsHideAbstractAndCertificate, IsShowLongPrepadZeroes, LatLongDecimalPostion, etc.
- Interconnect tab: InterconnectBaNo, InterconnectLoc, InterconnectBaNm, etc.
- Various AsOfDate filters for child tabs
- IsIntegration, DisableLocNameAutoLookup

### Grid View Models

| View Model | Data Object | Grid |
|---|---|---|
| `PALocationAttributeVM` | `PALocationAttributeDO` | Details Attributes |
| `PALocationContactVM` | `PALocationContactDO` | Contacts |
| `PALocationAggregateVM` | `PALocationAggregateDO` | Child Locations |
| `PAEutBrokerVM` | `PAEutBrokerDO` | Brokers |
| `PALocationCapVM` | `PALocationCapDO` | Capacity |
| `PASysLocGroupLocationVM` | `PASysLocGroupLocationDO` | Capacity/Rate Area |
| `PALocationAssociationVM` | `PALocationAssociationDO` | Associated Names (Selected) |
| `AssocLocationTypeVM` | `AssocLocationTypeDO` | Associated Names (Available) |
| `PALocationCtrChildVM` | `PALocationCtrChildDO` | Child Location for Allocation |
| `PALocationProducerVM` | `PALocationProducerDO` | Producers |
| `PALocationOwnerVM` | `PALocationOwnerDO` | Ownership |
| `PALocationAffidavitVM` | `PALocationAffidavitDO` | Affidavit |
| `PALocSupplierPinsVM` | `PALocSupplierPinsDO` | Supplier Location |
| `MeterHeaderLDCVM` | (Multiple) | LDC tab |
| `LocationPathMaintenanceRootVM` | `PALocationPathHdrDO` | Path Maintenance |
| `PALocationPathVM` | `PALocationPathDO` | Path grid |
| `LocationContactMassChangeRootVM` | `PALocationContactDO` | Contact Mass Change |

---

## Configuration

### Global Configuration Flags

| Configuration | Property | Description |
|---|---|---|
| `QPTMGlobalConfigs.BidirectionalPOV` | `ValdBidirectionalPOV` | Enables bidirectional location validation and CAScheduleObject management |
| `QPTMGlobalConfigs.AllowCapacityEffDate` | `AllowCapacityEffDate` | Allows capacity records to have different effective dates from the parent |
| `QPTMGlobalConfigs.QueryBtnText` | N/A | Customizable text for the Query button |

### TSP-Level Configuration

| Configuration | Method | Description |
|---|---|---|
| Curtailment Period From | `QPTMTspConfigs.CurtailPeriodFrom(tspNo)` | Start of normal affidavit update period |
| Curtailment Period To | `QPTMTspConfigs.CurtailPeriodTo(tspNo)` | End of normal affidavit update period |

### Metadata Configuration

Location group types are configured via `MetadataModuleDefinition` records, which control which group types appear on the screen based on the user's profile and module.

---

## Events and Notifications

### Location Maintenance Event Detection

The `UpdateAndHandleEvents` method uses `QPTMLocationMaintDetectorContext` to detect and fire domain events:

```csharp
context.MeterHeaderComplete = updateItem;
context.MeterHeader = (MeterHeaderDO)updateItem.MeterHeader.FirstOrDefault();
context.TspName = tspInfo?.TspName;
context.MeterName = updateItem.MeterHeader.FirstOrDefault().MeterName;
context.LocationActive = null; // Set if status changed
context.CapTypeList = this.GetCapTypeList();
```

Events are fired for:
- Location status changes (active/inactive)
- Location data modifications
- Screen changes tracked via `GenericScreenChange` and `GenericScreenChangeDetail`

### Screen Change Tracking

The `CreateScreenChange` method generates a `GenericScreenChange` object that tracks changes across all child objects:
- PAEutBroker, PALocationAffidavit, PALocationAggregate
- PALocationCtrChild, PALocationProducer, PASysLocGroupLocation
- PALocSupplierPins, PALocationCap
- MeterHeader, MeterHeaderQPTM (and nested: Association, Attribute, Contact, Interconnect, Owner, UserDefine)

---

## Key Code Flows

### Location Query Flow

```
1. Controller.DoUICLink() or Query action
2. UIC.Query() -> Service.GetSingleLocationMaintenanceComplete(locationMaintenanceData)
3. Service builds filters: MeterNo, TspNo, AsOfDate, aggregate, CtrChild, producer, broker, affidavit, SysLocGroupLoc, SupplierPins
4. DataAccess.GetMultipleMeterHeaderComplete(filters)
5. Service.AddAdditionalPropertiesLocationMaintenanceComplete() enriches with:
   - Parent location name (from PALocationAggregate + PALocation join)
   - Field descriptions (geographic)
   - Location attribute descriptions and read-only flags
   - Location names for shadow/transfer/bidirectional
   - Contact details with business associate names
   - Operator ID and Confirm Party display strings
   - Ownership contract validation data
   - Associated names descriptions
   - Interconnect details (BA name, DUNS, FERC CID)
   - Broker names, Affidavit names, Producer names
   - Child location allocation details
   - Child location operator contacts
   - Capacity rate area group names and types
   - Supplier pin location names and BA details
6. Controller.InitializeMyViewModel() transfers data to view model
7. Controller.SetModelParameters() maps UIC state to VM properties
```

### Location Save Flow

```
1. Controller CheckCurtailment() or Save action
2. UIC -> Service.UpdateSingleLocationMaintenanceComplete(updateItem)
3. LocationMaintenance_PreSave.PreSave(updateItem)
4. Service.ValidateSingleLocationMaintenanceComplete(updateItem, Save)
   -> Creates QPTMLocationMaintenanceCompleteValidationContext
   -> Runs all 52 validation rules
5. If errors, return without saving
6. Determine isUpdateLocResStatus and isDetailsLocResolve
7. TransactionScope(RequiresNew, ReadCommitted):
   a. UpdateAndHandleEvents():
      - Check for full delete scenario (all slices deleted)
      - UpdateFlatAttributeValues() (reflection-based attribute sync)
      - Clone for notifications
      - DataAccess.UpdateSingleMeterHeaderComplete() -> database save
   b. If isDetailsLocResolve:
      - UpdatePAlocationGroupDO() -> GetNextSeqNo for SetId
   c. AddDeleteCAScheduleObjectCustom() -> bidirectional pair management
   d. If isUpdateLocResStatus:
      - UpdateLocResStatus() -> insert PatranLocResRangeStatus
8. scope.Complete()
9. Return updated item with SetId
```

### Flat Attribute Update Flow

```
1. For each MeterHeaderQPTM in updateItem:
2. Find PALocationAttribute records with DataObjectState.Added or Modified
3. For each changed attribute:
   a. Find matching PALocationAttributeFlatDO (by LocId, EffDateFrom, TspNo)
   b. If not found, create new flat record
   c. Use reflection to find property named "ATTRIND{CODE}" (e.g., ATTRINDNOM)
   d. Set the flat column value to the attribute's IsAttrTrue value
```

---

## API Reference

### LocationMaintenanceController Routes

All routes use MVC convention: `/LocationMaintenance/{Action}`

| Route | HTTP | Description |
|---|---|---|
| `/LocationMaintenance/DetailsTab` | GET | Renders Details tab |
| `/LocationMaintenance/ContactsTab` | GET | Renders Contacts tab |
| `/LocationMaintenance/LocationMaintenanceFieldUpdate` | POST | Updates MeterHeader fields |
| `/LocationMaintenance/MeterHeaderQPTMFieldUpdate` | POST | Updates QPTM extension fields |
| `/LocationMaintenance/GetLocationDetails` | POST | Gets attribute grid data |
| `/LocationMaintenance/GetContacts` | POST | Gets contacts grid data |
| `/LocationMaintenance/GetAggregates` | POST | Gets child locations grid data |
| `/LocationMaintenance/GetBrokers` | POST | Gets brokers grid data |
| `/LocationMaintenance/GetCapacity` | POST | Gets capacity grid data |
| `/LocationMaintenance/GetCapacityRateArea` | POST | Gets capacity/rate area grid data |
| `/LocationMaintenance/GetChildLocationAllocation` | POST | Gets child allocation grid data |
| `/LocationMaintenance/GetProducers` | POST | Gets producers grid data |
| `/LocationMaintenance/GetOwnership` | POST | Gets ownership grid data |
| `/LocationMaintenance/GetAffidavit` | POST | Gets affidavit grid data |
| `/LocationMaintenance/GetSupplierLocation` | POST | Gets supplier pins grid data |
| `/LocationMaintenance/ShowHideTabsBasedOnLocTypeCode` | POST | Gets tab visibility |
| `/LocationMaintenance/GetLocationAttribute` | GET | Gets attribute-driven control states |
| `/LocationMaintenance/CheckCurtailment` | POST | Pre-save curtailment validation |
| `/LocationMaintenance/FillDefault` | GET | Fills default values |

### LocationPathMaintenanceController Routes

| Route | HTTP | Description |
|---|---|---|
| `/LocationPathMaintenance/LocationPathMaintenanceFieldUpdate` | POST | Updates path header |
| `/LocationPathMaintenance/LocationPathMaintenanceGridGetData` | POST | Gets path grid data |
| `/LocationPathMaintenance/ValidateBeforeSave` | POST | Pre-save validation |

### LocationContactMassChangeController Routes

| Route | HTTP | Description |
|---|---|---|
| `/LocationContactMassChange/LocationContactMassChangeGetData` | POST | Gets contact grid data |
| `/LocationContactMassChange/LocationContactMassChangeAddSelectedRow` | POST | Clone selected rows |
| `/LocationContactMassChange/LocationContactMassChangeDeleteSelectedRow` | POST | Delete selected rows |

---

*Cross-references:*
- [Domain Documentation](./domain.md) -- Business concepts and rules
- [Troubleshooting Guide](./troubleshooting.md) -- Known issues and resolutions

*Last updated: 2026-03-03*

*Document version: 1.0*
