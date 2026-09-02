---
title: Contracts (CTR) - Architecture & Implementation
category: architecture
feature: Contracts (CTR)
related_repos: Web, Batch
keywords: QPTMServiceCore_ContractMaintenance, ContractMaintenanceController, ContractsController, ContractHeaderCompleteDO, ContractHeaderDO, ContractHeaderQPTMDO, KCTRL_CTR_HDR, KCTRL_CTR_QPTM, KCTRL_CTR_ATTR_FLAT, validation, attribute flat table, amendment, API
last_updated: 2026-03-03
---

# Contracts (CTR) - Architecture & Implementation

## Overview

This document describes the **technical architecture** of the Contract Maintenance feature in QPTM Web. It covers code structure, key classes, database schema, algorithms, and service dependencies.

For business concepts, see [Domain Documentation](./domain.md).
For troubleshooting, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Layer Architecture](#layer-architecture)
2. [Service Layer](#service-layer)
3. [Controller Layer](#controller-layer)
4. [API Layer](#api-layer)
5. [Validation Engine](#validation-engine)
6. [Data Objects](#data-objects)
7. [Database Schema](#database-schema)
8. [Data Access Layer](#data-access-layer)
9. [Event System](#event-system)
10. [Key Algorithms](#key-algorithms)
11. [UI Controller](#ui-controller)
12. [Configuration](#configuration)

---

## Layer Architecture

```
+-------------------------------------------------------------------+
| WEB LAYER                                                         |
|  Quorum.QPTM.Web.Core/Controllers/                               |
|    ContractMaintenanceController.cs        (188KB - MVC primary)  |
|  Quorum.QPTM.Web.Controllers/APIControllers/                     |
|    ContractsController.cs                  (REST API)             |
+-------------------------------------------------------------------+
| UI CONTROLLER LAYER                                               |
|  Quorum.QPTM.Web.Controllers/UIControllers/                      |
|    QUIControllerContractMaintenance.cs     (screen state manager) |
+-------------------------------------------------------------------+
| SERVICE LAYER                                                     |
|  Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/    |
|    QPTMServiceCore_ContractMaintenance.cs  (2774 lines - primary) |
|    ContractMaintenance_UpdateAttributeFlatTable.cs (flat table)   |
+-------------------------------------------------------------------+
| VALIDATION LAYER                                                  |
|  Quorum.QPTM.Validations/Screens/ContractMaintenance/            |
|    Context/   (validation context classes)                        |
|    Validation Rules/                                              |
|      Agents/             (5 rules)                                |
|      AuthorizedOverrun/  (5 rules)                                |
|      Contacts/           (8 rules)                                |
|      ContractQuantity/   (4 rules)                                |
|      Dates/              (6 rules)                                |
|      FSSSchedule/        (1 rule)                                 |
|      General/            (16 rules)                               |
|      HeaderValidations/  (12 rules)                               |
|      Imbalance/          (10 rules)                               |
|      InjWithDrawPeriod/  (3 rules)                                |
|      Locations/          (12 rules)                               |
|      PALISSTrade/        (15 rules)                               |
|      RelatedContracts/   (5 rules)                                |
|      Text/               (2 rules)                                |
+-------------------------------------------------------------------+
| EVENT LAYER                                                       |
|  Quorum.QPTM.Events.Contract/                                    |
|    Detectors/                                                     |
|      QPTMContractMaintenanceMDQChangeEventDetector.cs             |
|      QPTMContractMaintenanceStatusCdChangeEventDetector.cs        |
|    Handlers/                                                       |
|      (email notification handlers)                                |
+-------------------------------------------------------------------+
| DATA ACCESS LAYER                                                 |
|  Quorum.QPTM.DataAccess/                                         |
|    IQESUITEDataAccess_ContractHeaderComplete (complete obj DA)    |
|    IQESUITEDataAccess_ContractHeader         (header DA)          |
|    IQPTMDataAccess_ContractStatus            (status codes)       |
|    IQPTMDataAccess_ContractAttributeFlat     (flat table DA)      |
|    IQPTMDataAccess_CtrAttribute              (attributes DA)      |
|    IQPTMDataAccess_Contract                  (contract query DA)  |
+-------------------------------------------------------------------+
| DATA OBJECTS                                                      |
|  Quorum.QPTM.DataObject/                                         |
|    ContractHeaderCompleteDOExt.cs    (complete DO extensions)     |
|    ContractHeaderDOExt.cs            (header DO extensions)       |
|    ContractHeaderQPTMDOExt.cs        (QPTM header extensions)    |
|    ContractAgentDOExt.cs             (agent DO extensions)        |
|    ContractLocationDOExt.cs          (location DO extensions)     |
|    + CodeGen/ folder                 (auto-generated DOs)         |
+-------------------------------------------------------------------+
| DATABASE                                                          |
|  SCTRL_CTR_HEADER      (ESuite contract header)                  |
|  SEXTN_CTR_HEADER_QPTM (QPTM extension header)                  |
|  KCTRL_CTR_ATTR_FLAT   (attribute flat table)                    |
|  KCTRL_CTR_LOC         (contract locations)                      |
|  KCTRL_CTR_ATTR        (contract attributes)                     |
|  SCTRL_CTR_AGENT       (contract agents)                         |
|  KCTRL_AUTH_OVERRUN    (authorized overrun)                      |
|  KCTRL_FSS             (FSS schedule)                            |
+-------------------------------------------------------------------+
```

---

## Service Layer

### QPTMServiceCore_ContractMaintenance

**File:** `Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/QPTMServiceCore_ContractMaintenance.cs`
**Lines:** ~2774
**Class:** `QPTMServiceCore` (partial class implementing `IQPTMService_ContractMaintenance`)

This is the primary service class for contract maintenance. It is a partial class extension of `QPTMServiceCore`.

#### Key Methods

**Query Methods:**

| Method | Purpose |
|---|---|
| `GetSingleContractMaintenanceComplete()` | Retrieves a single contract with all child objects by CtrNo, AssignNo, TspNo, EffDateFrom |
| `GetMultipleContractMaintenance()` | Retrieves multiple contract headers with filtering, sorting, and paging |
| `GetMultipleContractMaintenanceComplete()` | Retrieves multiple complete contract objects |
| `AddAdditionalPropertiesContractMaintenanceComplete()` | Enriches the complete DO with billing invoice, rate resolution, injection/withdrawal periods, agents, auth overrun, FSS, PAL/ISS cumulative data |
| `AddAdditionalPropertiesContractMaint()` | Enriches individual contract header with locations, seasonal profiles, contacts, text, schedule cap overrides, ratchet schedules, tax IDs |

**Update Methods:**

| Method | Purpose |
|---|---|
| `UpdateSingleContractMaintenanceComplete()` | Main save method -- validates, generates CtrNo, updates flat table, saves header and child objects in a transaction |
| `UpdateAgent()` | Saves contract agents separately (two-phase save for FK constraint avoidance) |
| `UpdateAuthOverrun()` | Saves authorized overrun records |
| `UpdateFss()` | Saves FSS schedule records |

**Validate Methods:**

| Method | Purpose |
|---|---|
| `ValidateSingleContractMaintenanceComplete()` | Validates a single complete contract object |
| `ValidateMultipleContractMaintenanceCompleteInternal()` | Core validation -- creates `QContractMaintenanceValidationContextComplete` and invokes the validation engine |
| `ValidateContractDailyRate()` | Validates PAL/ISS daily rate against rate resolution process |

**Helper Methods:**

| Method | Purpose |
|---|---|
| `LoadScreenDefaultsOfContract()` | Loads screen defaults, TOS lists, attributes, rate schedules, seasonal profiles, contract status list, location attribute list |
| `GetNextAmendNo()` | Calculates next amendment number (max existing + 1) |
| `GetNextCtrNo()` | Auto-generates contract number using global sequence, optionally prefixed with TSP/TOS |
| `GetNewContractPrefix()` | Looks up contract number prefix from `SXREF_ORG_CTR` hierarchy |
| `GetNextIdSet()` | Gets next ID set for batch processes |
| `PostprepareForUpdateLocations()` | Identifies delivery locations with MDQ changes for event detection |

### ContractMaintenance_UpdateAttributeFlatTable

**File:** `Quorum.QPTM.ServiceCore/QPTMServiceCore_ContractMaintenance/ContractMaintenance_UpdateAttributeFlatTable.cs`
**Class:** `ContractMaintenance_UpdateAttributeFlatTable` implementing `IContractMaintenance_UpdateAttributeFlatTable`

**Purpose:** Synchronizes normalized `CtrAttributeDO` records to the `ContractAttributeFlatDO` flat table.

**Algorithm:**
1. Iterate through each `ContractHeaderDO` in the complete object
2. Get or create the `ContractAttributeFlatDO` record for the time slice
3. For each `CtrAttributeDO` attribute, switch on `TosAttrCode` and set the corresponding flat column
4. The flat record is saved as part of the parent complete object save

**Mapped attributes (29 total):** ADO, AST, BIL, BKL, CAP, CIO, HNA, IMB, IOC, NOM, NSD, NSR, OPR, PPP, EVG, PMF, BHA, BSC, EXN, LDN, LOC, ENS, NCA, NGT, SEM, RCR, PIT, LLF, DIS, ESL

---

## Controller Layer

### ContractMaintenanceController

**File:** `Quorum.QPTM.Web.Core/Controllers/ContractMaintenanceController.cs`
**Class:** `ContractMaintenanceController` inherits `BillingControllerBase<QUIControllerContractMaintenance, ContractMaintenanceRootVM>`
**Security:** `[QScreenSecurityObject(Constants.SecurityObjectIDs.ContractMaintenance)]`

#### Actions

| Action | Description |
|---|---|
| Query | Queries contracts by filter criteria |
| Save | Validates and saves the contract (with `ValidateBeforeSave` override and `IsShowPPAReallocationDialog` post-callback) |
| New | Creates a new contract (sets defaults, amendment 0, status from screen defaults) |
| AddAmendment | Creates a new amendment (calculates next AmendNo, sets status) |
| Copy | Copies an existing contract (resets AmendNo to 0) |
| Delete | Deletes a contract (with `ValidateBeforeDelete` override) |
| CurrentMdiqMdwq | Launches the Current MDIQ/MDWQ batch process |
| Close | Closes the screen |

#### Tab Rendering Methods

The controller renders multiple tabs, each as a partial view:

| Tab Method | Partial View | Purpose |
|---|---|---|
| `GeneralTab()` | General | MDQ, MDIQ, MDWQ, ratchets, seasonal profiles, TOS attributes |
| `LocationsTab()` | Locations | Receipt and delivery locations with MDQ by location |
| `AgentsTab()` | Agents | Contract agent management |
| `ContactsTab()` | Contacts | Notice party / contact override management |
| `DatesTab()` | Dates | Contract dates, evergreen terms, status code |
| `RatesTab()` | Rates | Rate resolution and rate contract assignments |
| `TextTab()` | Text | Contract text / pre-approved text |
| `RelatedKTab()` | RelatedK | Related contracts |
| `ImbalanceTab()` | Imbalance | Imbalance settings and tied contracts |
| `InvoiceTab()` | Invoice | Billing invoice group association |
| `InjWthPeriodsTab()` | InjWthPeriods | Injection/withdrawal periods for storage |
| `ContractQuantityTab()` | ContractQuantity | PITS quantity configuration |
| `PALIssTradeTab()` | PALISSTrade | Park and Loan deal configuration |
| `AuthorizedOverrunTab()` | AuthorizedOverrun | Authorized overrun management |
| `FSSScheduleTab()` | FSSSchedule | Firm Storage Service schedule |
| `PALISSCumulativeTab()` | PALISSCumulative | PAL/ISS cumulative quantities |
| `SegmentCapacityTab()` | SegmentCapacity | Segment capacity overview |
| `ZoneSegmentCapacityTab()` | ZoneSegmentCapacity | Zone-based segment capacity |
| `SchdCapOvrdTab()` | SchdCapOvrd | Schedule capacity overrides |
| `UserDefinedFieldsTab()` | UserDefined | Custom user-defined fields (UserDef1-20) |

#### Grid Operations

The controller provides CRUD grid operations for:
- **Contacts Grid**: `GetContractContacts`, `ContractContactGridUpdate`, `ContractContactGridAddNewRow`
- **Locations Grid**: `ContractLocationsGrid`
- **Other grids** for agents, related contracts, text, etc.

#### Link Navigation

The controller defines navigation links to related screens:
- Business Associate
- Invoice Group Maintenance
- Location Maintenance
- Location Group Maintenance
- TOS Maintenance
- Rate Maintenance
- Index Maintenance
- Tier Maintenance
- Formula Editor
- Rate Seasonal Profile Maintenance
- Contract Seasonal Profile Maintenance
- RFS Wizard V2

#### Parameter Transfer

`SetModelParameters()` transfers extensive data from the UI controller to the view model, including:
- Contract header fields (CtrNo, TspNo, BaNo, AssignNo, dates)
- General tab fields (MDQ, MDIQ, MDWQ, seasonal profiles, ratchets, BTU factor)
- Imbalance fields
- Location totals (TotalReceiptMDQ, TotalDeliveryMDQ)
- User-defined fields (UserDef1 through UserDef20)
- PAL/ISS trade fields
- FSS schedule fields
- Tab permissions (delete permissions for agents, locations, related K)
- Rate and date fields

---

## API Layer

### ContractsController

**File:** `Quorum.QPTM.Web.Controllers/APIControllers/ContractsController.cs`
**Route Prefix:** `api/v1/Contracts`
**Class:** `ContractsController` extends `ContractsControllerBase`
**Service:** `IContractsAPIService` / `ContractsAPIService`

#### API Endpoints

| HTTP Method | Route | Method | Description |
|---|---|---|---|
| GET | `api/v1/Contracts` | `GetContractsCollection()` | Get all contracts for a TSP with optional filters, embeds, and data shaping |
| GET | `api/v1/Contracts/Summary` | `GetContractsSummaryCollection()` | Get contract summary by summary type |
| GET | `api/v1/Contracts/EnumeratedParameterValues` | `GetContractEnumeratedParameterValuesCollection()` | Get enumerated parameter values for contract filters |
| GET | `api/v1/Contracts/{tsp}/{id}/{amend_no}` | `GetContractObject()` | Get a specific contract by TSP, contract ID, and amendment number |
| GET | `api/v1/Contracts/{tsp}/{id}/{amend_no}/contacts` | `GetContractContactsCollection()` | Get contacts for a specific contract |
| GET | `api/v1/Contracts/{tsp}/{id}/{amend_no}/locations` | `GetContractLocationsCollection()` | Get locations for a specific contract |

#### API Parameters

- **tsp** (required): Transportation Service Provider ID
- **asOfDate** (optional): As-of date for effective dating; default is today; `9000-12-31` returns all
- **filter** (optional): Comma-separated list of `ContractFilterEnum` values
- **embed** (optional): Comma-separated list of `ContractEmbeddedObjects` (sub-resources to include)
- **summary** (optional): `ContractSummaryEnum` value for summary queries
- **include/exclude** (optional): Data shaping -- properties to include or exclude from response

#### API Resource Types

- `ContractCollectionResource` - Collection of contract objects
- `ContractSummaryCollectionResource` - Collection of contract summaries
- `ContractContactCollectionResource` - Collection of contract contacts
- `ContractLocationCollectionResource` - Collection of contract locations
- `EnumeratedValuesCollectionResource` - Enumerated parameter values

---

## Validation Engine

### Validation Context

**File:** `Quorum.QPTM.Validations/Screens/ContractMaintenance/Context/QPTMValidationContext_ContractMaintenance.cs`
**Class:** `QContractMaintenanceValidationContextComplete`

The validation context wraps the list of `ContractHeaderCompleteDO` objects to validate, plus the TspNo. All validation rules receive this context.

### Validation Rule Base

**Class:** `QPTMContractMaintenanceValidationContextBase`

All contract validation rules extend this base class, which provides helper methods for data access (e.g., `GetTypeOfServiceByTosCode`, `GetContractsByCtrNo`, `CreateInClauseFilters`).

### Validation Rules by Category

**Header Validations (12 rules):**

| Rule | File | Purpose |
|---|---|---|
| 001 | `QPTMContractMaintenace001_HeaderValidateCtrCompany.cs` | Validate contract company |
| 002 | `QPTMContractMaintenace002_HeaderValidateBackDate.cs` | Validate back-dating restrictions |
| 003 | `QPTMContractMaintenace003_HeaderValidateIntegratedNewContract.cs` | Validate new contract in integrated mode |
| 004 | `QPTMContractMaintenace004_HeaderValidateBASuf.cs` | Validate business associate suffix |
| 005 | `QPTMContractMaintenace005_HeaderValidateBusinessParty.cs` | Validate business party exists |
| 006 | `QPTMContractMaintenace006_HeaderValidateInactiveBusinessParty.cs` | Warn if business party is inactive |
| 007 | `QPTMContractMaintenace007_HeaderValidateInactiveTosCode.cs` | Warn if TOS code is inactive |
| 008 | `QPTMContractMaintenace008_HeaderValidateTosCode.cs` | Validate amendment handling (Additive vs Replacement) and amendment status ordering |
| 009 | `QPTMContractMaintenace009_HeaderValidateNominationReady.cs` | Validate nomination readiness requirements |
| 010 | `QPTMContractMaintenace010_HeaderValidatePreDelete.cs` | Pre-delete validation checks |
| 012 | `QPTMContractMaintenance012_HeaderDateGapValidation.cs` | Validate no gaps in effective date ranges |

**Key Validation: TOS Code (Rule 008)**
This is one of the most complex validations. It checks:
- For **Additive** amendment handling: all previous amendments must be Executed or Active
- For **Replacement** amendment handling: amendment 0 must be Executed or Active
- Warns if future amendments are already Executed
- Prevents duplicate effective date time slices

**Location Validations (12 rules):**
Validates TOS/location attribute cross-references, threshold quantities, hourly measurement penalties, segments, facilities, delivery location multi-contract usage, ineffective dates, primary point pairs, location row completeness, and duplicate attributes.

---

## Data Objects

### Primary Data Objects

| Data Object | Table | Purpose |
|---|---|---|
| `ContractHeaderCompleteDO` | (composite) | Complete contract with all children -- the primary object for query, save, and validate |
| `ContractHeaderDO` | `SCTRL_CTR_HEADER` | ESuite contract header (CtrNo, BaNo, AssignNo, EffDateFrom, EffDateTo, StatusCode, TypeCode, SubTypeCode) |
| `ContractHeaderQPTMDO` | `SEXTN_CTR_HEADER_QPTM` | QPTM extension header (TspNo, MDQ, MDIQ, MDWQ, MSQ, seasonal profiles, ratchets, SRC, imbalance settings) |
| `ContractAttributeFlatDO` | `KCTRL_CTR_ATTR_FLAT` | Flat table of boolean attribute flags |
| `CtrAttributeDO` | `KCTRL_CTR_ATTR` | Normalized contract attributes (TosAttrCode, IsAttrTrue) |
| `CtrLocationDO` | `KCTRL_CTR_LOC` | Contract receipt/delivery locations with MDQ quantities |
| `ContractAgentDO` | `SCTRL_CTR_AGENT` | Contract agents (extends ESuite ContractAgentDO) |
| `ContractStatusDO` | `QCODE_CTR_STATUS` | Contract status code definitions |
| `ContractDO` | `KCTRL_CTR` | Lightweight contract query object (TspNo, CtrNo, AmendNo, TosCode, CtrStatusCode) |
| `ContractDatesDO` | `KCTRL_CTR_DATES_QPTM` | Contract date tracking records |
| `ContractTextDO` | `KCTRL_CTR_TEXT` | Contract text records with pre-approved text links |
| `ContractInjWdPeriodDO` | `KCTRL_CTR_INJ_WD_PERIOD` | Injection/withdrawal period definitions |
| `ContractUserDefinedDO` | `KCTRL_CTR_USER_DEF` | User-defined fields (UserDef1-20) |
| `KctrlAuthOverrunDO` | `KCTRL_AUTH_OVERRUN` | Authorized overrun records |
| `KctrlFssDO` | `KCTRL_FSS` | FSS schedule records |
| `PalIssDealDO` | `KCTRL_PAL_ISS_DEAL` | PAL/ISS trade deal records |
| `RelatedContractDO` | `SCTRL_REL_CTR` | Related contract linkages |
| `ContractNoticePartyDO` | (contact table) | Contract notice party / contact overrides |
| `BillingInvoiceGroupContractDO` | (billing table) | Billing invoice group association |
| `RateResolutionDO` | (rate table) | Rate resolution results |
| `ContractHeaderValdDO` | `SCTRL_CTR_HEADER_VALD` | Contract header validation results |
| `ContractLetterAgreementDO` | (letter agreement table) | Contract letter agreement records |

### ContractHeaderCompleteDO Hierarchy

The `ContractHeaderCompleteDO` is the root object. It is an effective-dated container:

```
ContractHeaderCompleteDO
  |-- CtrNo (string)
  |-- tspNo (short)
  |-- ContractHeader (QBindingList<ContractHeaderDO>)
  |     |-- CtrNo, BaNo, AssignNo, EffDateFrom, EffDateTo, StatusCode
  |     |-- SubTypeCode (TOS code), TypeCode
  |     |-- BaName, ExecutedDate
  |     |-- CHQPTM (ContractHeaderQPTMDO) [1:1 extension]
  |     |     |-- TspNo, CtrMdqDisplayOnly, FixedMdiqQty, FixedMdwqQty
  |     |     |-- CtrMsq, CtrMsqMin, OvrdCtrMdq
  |     |     |-- IdSeasonalProf, IdMdiqRatchet, IdMdwqRatchet
  |     |     |-- SrcSeasonalProfId, SrcQty
  |     |     |-- CtrAttribute (QBindingList<CtrAttributeDO>)
  |     |     |-- ContractAttributeFlat (QBindingList<ContractAttributeFlatDO>)
  |     |     |-- CtrLocation (QBindingList<CtrLocationDO>)
  |     |     |-- ContractText (QBindingList<ContractTextDO>)
  |     |     |-- CtrSchdCapOvrd (QBindingList)
  |     |     |-- PalIssDeal (QBindingList<PalIssDealDO>)
  |     |     |-- ContractUserDefined (ContractUserDefinedDO)
  |     |     |-- ContractList (List<ContractDO>) [related K children]
  |     |-- ContractNoticeParty (QBindingList)
  |     |-- ContractDates (QBindingList)
  |     |-- ContractHeaderQPTM (QBindingList<ContractHeaderQPTMDO>)
  |-- ContractAgent (QBindingList<ContractAgentDO>)
  |-- ContractStatus (QBindingList<ContractStatusDO>)
  |-- ContractStatusHistory (QBindingList)
  |-- ContractInjWdPeriod (QBindingList<ContractInjWdPeriodDO>)
  |-- RelatedContract (QBindingList<RelatedContractDO>)
  |-- KctrlAuthOverrun (QBindingList<KctrlAuthOverrunDO>) [extension child]
  |-- KctrlFss (QBindingList<KctrlFssDO>) [extension child]
  |-- BillingInvoiceList (QBindingList<BillingInvoiceGroupContractDO>) [additional]
  |-- RateResolutionList (QBindingList<RateResolutionDO>) [additional]
  |-- ContractInjWdPeriodOverallList (List<ContractInjWdPeriodDO>) [additional]
  |-- PalIssNetQuantityList (QBindingList<PalIssNetQuantityDO>) [additional]
  |-- PALISSCumulativeMonthlyList (List<PALISSCumulativeMonthlyDO>) [additional]
```

### Extension Pattern (DOExt)

Contract data objects follow the **DOExt pattern** -- CodeGen files are never modified; extensions go in `*DOExt.cs` files:

- `ContractHeaderDOExt.cs` adds `TosCd` property and the `CHQPTM` shortcut property (auto-creates the first ContractHeaderQPTMDO if needed)
- `ContractHeaderCompleteDOExt.cs` adds `BillingInvoiceList`, `RateResolutionList`, `ContractInjWdPeriodOverallList`, `PalIssNetQuantityList`, `PALISSCumulativeMonthlyList`, `tspNo`, `TotalContractReceiptMDQ`, `TotalContractDeliveryMDQ`, `GlobalAsOfDate`, `RateResolutionProcess`
- `ContractHeaderCompleteDOExt.cs` also adds `KctrlAuthOverrun` and `KctrlFss` as extension children with full binding list support and flat list hierarchy building

---

## Database Schema

### Primary Tables

| Table | Purpose | Key Columns |
|---|---|---|
| `SCTRL_CTR_HEADER` | ESuite contract header | CTR_NO, BA_NO, ASSIGN_NO, EFF_DATE_FROM, EFF_DATE_TO, STATUS_CD, TYPE_CODE, SUB_TYPE_CODE |
| `SEXTN_CTR_HEADER_QPTM` | QPTM extension header | TSP_NO, CTR_NO, ASSIGN_NO, EFF_DATE_FROM, EFF_DATE_TO, CTR_MDQ, FIXED_MDIQ_QTY, FIXED_MDWQ_QTY, CTR_MSQ, OVRD_CTR_MDQ |
| `KCTRL_CTR_ATTR_FLAT` | Attribute flat table | TSP_NO, CTR_NO, AMEND_NO, EFF_DATE_FROM, EFF_DATE_TO, ATTR_IND_NOM, ATTR_IND_BIL, ATTR_IND_CAP, ... |
| `KCTRL_CTR_ATTR` | Normalized contract attributes | TSP_NO, CTR_NO, AMEND_NO, EFF_DATE_FROM, EFF_DATE_TO, TOS_ATTR_CODE, IS_ATTR_TRUE |
| `KCTRL_CTR_LOC` | Contract locations | TSP_NO, CTR_NO, AMEND_NO, ID_LOC_1, ID_LOC_2, ID_LOC_GRP_1, ID_LOC_GRP_2, FIXED_MDQ_QTY, SUMMER_MDQ_QTY, WINTER_MDQ_QTY |
| `SCTRL_CTR_AGENT` | Contract agents | CTR_NO, AGENT_BA_NO, CONSENTING_BP_NO, EFF_DATE_FROM, EFF_DATE_TO |
| `KCTRL_AUTH_OVERRUN` | Authorized overrun | TSP_NO, CTR_NO, DAILY_OVERRUN_QTY, EFF_DATE_FROM, EFF_DATE_TO |
| `KCTRL_FSS` | FSS schedule | TSP_NO, CTR_NO, MSQ_QTY, EFF_DATE_FROM, EFF_DATE_TO |
| `KCTRL_PAL_ISS_DEAL` | PAL/ISS trade deals | TSP_NO, CTR_NO, DEAL_TYPE_CODE, TOTAL_VOL, TRADE_TIMESTAMP, CTR_DAILY_RATE |
| `KCTRL_CTR_INJ_WD_PERIOD` | Injection/withdrawal periods | TSP_NO, CTR_NO, EFF_DATE_FROM, EFF_DATE_TO |
| `KCTRL_CTR_USER_DEF` | User-defined fields | TSP_NO, CTR_NO, USER_DEF_1 through USER_DEF_20 |
| `KCTRL_CTR_TEXT` | Contract text | TSP_NO, CTR_NO, ID_TEXT |
| `SCTRL_REL_CTR` | Related contracts | CTR_NO, REL_CTR_NO |

### Reference/Lookup Tables

| Table | Purpose |
|---|---|
| `QCODE_CTR_STATUS` | Contract status code definitions (ACT, DFT, EXE, EXP, INA, PEN, PRO, TRM) |
| `QCODE_TOS_ATTR` | TOS attribute code definitions |
| `KCTRL_CTR` | Contract summary view (TSP_NO, CTR_NO, AMEND_NO, TOS_CODE, CTR_STATUS_CODE) |
| `KCTRL_CTR_EFF_DATE_RANGE_VW` | Contract effective date range view |
| `KCTRL_CTR_EFF_DATE_RANGE_GS_VW` | Gas storage contract effective date range view |
| `SXREF_ORG_CTR` | Organization/contract type cross-reference (for CtrNo prefix) |
| `SXREF_ORG_CTR_SUB_CTR` | Organization/sub-contract type cross-reference |
| `SXREF_ORG_CTR_SUB_CTR_SETTLE` | Organization/sub-contract/settle cross-reference |
| `KXREF_TOS_LOC_ATTR` | TOS/location attribute cross-reference |

---

## Data Access Layer

### Key Data Access Interfaces

| Interface | Purpose |
|---|---|
| `IQESUITEDataAccess_ContractHeaderComplete` | CRUD for complete contract objects (header + all children) |
| `IQESUITEDataAccess_ContractHeader` | CRUD for contract headers only |
| `IQPTMDataAccess_ContractStatus` | Query contract status codes |
| `IQPTMDataAccess_ContractAttributeFlat` | CRUD for attribute flat table |
| `IQPTMDataAccess_CtrAttribute` | CRUD for normalized attributes |
| `IQPTMDataAccess_Contract` | Query lightweight contract records |
| `IQPTMDataAccess_KctrlAuthOverrun` | CRUD for authorized overrun |
| `IQPTMDataAccess_KctrlFss` | CRUD for FSS schedule |
| `IQPTMDataAccess_PalIssDeal` | CRUD for PAL/ISS deals |
| `IQPTMDataAccess_PALocation` | Query pipeline locations |
| `IQPTMDataAccess_PALocationGroup` | Query location groups |
| `IQPTMDataAccess_SeasonalProfile` | Query seasonal profiles |
| `IQPTMDataAccess_RatchetSchedule` | Query ratchet schedules |
| `IQPTMDataAccess_BusinessAssociate` | Query business associates |
| `IQPTMDataAccess_Contact` | Query contacts |
| `IQPTMDataAccess_BATaxId` | Query BA tax IDs |
| `IQPTMDataAccess_InventoryAccountHeader` | CRUD for inventory account headers |

---

## Event System

### Event Detectors

Contract maintenance fires events via the `ExecuteAndHandleEvents()` pattern. Two detectors are registered:

**1. QPTMContractMaintenanceMDQChangeEventDetector**
- **File:** `Quorum.QPTM.Events.Contract/Detectors/QPTMContractMaintenanceMDQChangeEventDetector.cs`
- **Trigger:** `context.IsMDQChange == true` (OldContractMDQ != NewContractMDQ and affected delivery locations exist)
- **Event Type:** `ContractLocationMDQChange`
- **Event Data:** CtrNo, EffDtFrom, EffDtTo, BpNm, OldContractMDQ, NewContractMDQ, ChangedMDQDelLocList
- **Message:** "As of {date}, MDQ for {BP} contract {CtrNo} was increased/decreased to {new} from previous value of {old}. Delivery location(s): {list}."

**2. QPTMContractMaintenanceStatusCdChangeEventDetector**
- **File:** `Quorum.QPTM.Events.Contract/Detectors/QPTMContractMaintenanceStatusCdChangeEventDetector.cs`
- **Trigger:** `StatusCodeOriginal != StatusCode` or new amendment has different status
- **Event Type:** `ContractStatusChange`
- **Event Data:** CtrNo, EffDtFrom, EffDtTo, BpNm, CtrStatusCd, CtrStatusDescr, TspNo
- **Properties Exposed:** BP_NM, CTR_NO, CTR_STATUS, EFF_DT_FROM, EFF_DT_TO, TSP_NO

### Event Context

**File:** `Quorum.QPTM.Events.Contract/Detectors/QPTMContractMaintenanceDetectorContext.cs`

```csharp
[QEventGroup("QPTMContractMaintenanceMDQChangeEventDetector")]
[QEventGroup("QPTMContractMaintenanceStatusCdChangeEventDetector")]
public class QPTMContractMaintenanceDetectorContext
{
    public ContractHeaderDO ContractHeader { get; set; }
    public ContractHeaderDO NewContractHeader { get; set; }
    public bool IsMDQChange { get; set; }
    public string CtrStatusDescr { get; set; }
    public string NewCtrStatusDescr { get; set; }
    public short TspNo { get; set; }
    public decimal OldContractMDQ { get; set; }
    public decimal NewContractMDQ { get; set; }
    public List<string> ChangedMDQDelLocList { get; set; }
}
```

---

## Key Algorithms

### Algorithm 1: Contract Save (UpdateSingleContractMaintenanceComplete)

```
1. Clone the complete object for notification comparison
2. Validate the complete object (Save context)
3. If validation errors exist -> return with errors
4. If auth overrun or FSS has errors -> return with errors
5. If BATCHID_DETDAILYRT process exists -> validate daily rate
6. If CtrNo is new or "<NEW>" ->
   a. Get next sequence number (GetNextCtrNo)
   b. Optionally prefix with TSP/TOS code
7. If new ContractHeaderQPTM -> clone attributes as new
8. BEGIN TRANSACTION
9. If integrated mode -> update QCM header with primary agent info
10. Execute within event detection context:
    a. Check if all headers being deleted
    b. If deleting all -> delete child objects first, then recreate
    c. Else -> update agents separately (FK constraint avoidance)
    d. Update attribute flat table (ContractMaintenance_UpdateAttributeFlatTable)
    e. Clear agents from main save (avoid FK error)
    f. Save complete object via DataAccess
    g. Re-save agents separately
    h. Update auth overrun and FSS
11. COMMIT TRANSACTION
12. Remove extra time slices (keep only the most current)
13. Return updated complete object
```

### Algorithm 2: Attribute Flat Table Update

```
For each ContractHeaderDO in the complete object:
  1. Get ContractHeaderQPTMDO (CHQPTM)
  2. Get or create ContractAttributeFlatDO for the time slice
  3. If new -> set CtrNo, AmendNo, TspNo, EffDateFrom, EffDateTo
  4. For each CtrAttributeDO:
     Switch on TosAttrCode:
       "ADO" -> set AttrIndAdo = IsAttrTrue
       "AST" -> set AttrIndAst = IsAttrTrue
       "BIL" -> set AttrIndBil = IsAttrTrue
       ... (29 attributes mapped)
  5. Record is saved as part of parent complete object
```

### Algorithm 3: Next Contract Number Generation (GetNextCtrNo)

```
1. Get SubTypeCode and TypeCode from first contract header
2. Look up contract prefix from SXREF_ORG_CTR hierarchy
3. If UseTSPTOSContractPrefix global config is enabled:
   a. Build prefix sequence key: "{TspNo}_{SubTypeCode}_CTR_NO"
   b. Get next global sequence number
   c. Build CtrNo: "{TspNo}{TosPrefix}-{SeqNo}"
   d. If length <= 12 -> use this format
   e. If length > 12 -> fall through to standard format
4. Standard format: get next sequence for "CTR_NO"
5. Return sequence number as CtrNo
```

### Algorithm 4: Amendment Processing (SetNextAmendNo / AddAmendment)

```
1. Query KCTRL_CTR for existing amendments of the contract
2. Next AmendNo = max(existing AmendNo) + 1
3. Create new time slice with:
   a. New AmendNo
   b. Status from ContractMaintenanceData.StatusCd
   c. ExecutedDate set if status is Executed
4. Default AmendDescr = "Original Contract" for AmendNo 0
5. Copy TOS and effective dates from previous amendment as defaults
```

---

## UI Controller

### QUIControllerContractMaintenance

**File:** `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerContractMaintenance.cs`

The UI controller manages screen state between HTTP requests. Key responsibilities:

- **MyParams** - Stores current query parameters (TspNo, CtrNo, AssignNo, EffDateFrom, etc.)
- **ContractHeader** / **ContractHeaderQPTM** - Current contract data objects
- **ContractHeaderComplete** - Full contract with children
- **ContractMaintenanceData** - Screen defaults and lookup data
- **Query()** - Executes the query using service layer
- **SetNextAmendNo()** - Calculates and sets the next amendment number
- **Tab visibility** - Controls which tabs are shown based on TOS configuration
- **Permission checks** - Controls delete permissions for agents, locations, related K
- **Integrated mode** - Supports both standalone and integrated (with QCM) contract management

---

## Configuration

### Global Configs

| Config | Purpose |
|---|---|
| `UseTSPTOSContractPrefix` | Whether to prefix auto-generated contract numbers with TSP and TOS codes |
| `CtrIsIntegratedMode` | Whether contract maintenance runs in integrated mode with QCM |
| `AllowDefaultAmenDescr` | Whether to allow default amendment description |
| `UsePostingStatusForTransRpt` | Whether to use posting status for transaction report |
| `IsAllowNewIntegrationContracts` | Whether to allow creating new contracts in integrated mode |
| `QueryBtnText` | Custom text for the query button |

### Screen Defaults

Screen defaults are loaded from the `ScreenDefaultDO` system for the "QVPCONTRACTMAINTENANCE_GENERAL" screen:
- Default `STATUS_CD` for new contracts (typically "PEN")
- Other field defaults as configured

### Security

- Screen-level security: `Constants.SecurityObjectIDs.ContractMaintenance`
- Tab-level permissions: separate security objects for agents, locations, related K delete operations
- Link security: each navigation link has its own security object ID

---

*Last updated: 2026-03-03*

*Document version: 1.0*
