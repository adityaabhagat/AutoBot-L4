---
title: Rate Management (RATE) - Architecture
category: architecture
feature: Rate Management (RATE)
related_repos: Web, Batch
keywords: RATE, architecture, code structure, services, controllers, validation, data objects, database tables, rate resolution, TOC resolution, tier resolution, caching, RateResolutionMgr, TOCResolutionMgr, TierRateResolutionMgr, RateMaintenanceController, QPTMServiceCore_RateMaintenance
last_updated: 2026-03-03
---

# Rate Management (RATE) - Architecture

## Overview

This document explains the **technical architecture** of the Rate Management system in QPTM. It covers code structure, service layer design, resolution algorithms, controller implementations, validation rules, database schema, caching, and integration patterns.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Rate Resolution Engine](#rate-resolution-engine)
3. [TOC Resolution Engine](#toc-resolution-engine)
4. [Tier Rate Resolution Engine](#tier-rate-resolution-engine)
5. [Service Layer](#service-layer)
6. [Web Application Layer](#web-application-layer)
7. [Validation Layer](#validation-layer)
8. [Data Model](#data-model)
9. [Database Schema](#database-schema)
10. [Caching](#caching)
11. [Configuration](#configuration)
12. [Integration Points](#integration-points)
13. [Key Processing Flows](#key-processing-flows)

---

## System Architecture

### Architectural Layers

```
+---------------------------------------------------------------+
|                    WEB APPLICATION LAYER                        |
|  +---------------------------+  +---------------------------+  |
|  | RateMaintenanceController |  | TypeOfChargeMaintenance   |  |
|  | (1122 lines)              |  | Controller                |  |
|  | - GeneralTab              |  | TierMaintenanceController |  |
|  | - LocationDetailsTab      |  |                           |  |
|  | - RateContractAssocTab    |  |                           |  |
|  | - RateInventoryAssocTab   |  |                           |  |
|  | - RateTosAssocTab         |  |                           |  |
|  | - LocationMatrixTab       |  |                           |  |
|  +------------+--------------+  +---------------------------+  |
+---------------|------------------------------------------------+
                |
                v
+---------------------------------------------------------------+
|                      SERVICE LAYER                              |
|  +---------------------------+  +---------------------------+  |
|  | QPTMServiceCore            |  | QPTMRateService           |  |
|  | _RateMaintenance           |  | (IQPTMRateService,        |  |
|  | (1207 lines)               |  |  IQPTMFuelCalcService)    |  |
|  | - CRUD for Rate/Complete   |  | - CalculateFuel()         |  |
|  | - Validation orchestration |  | - GetActualRate()         |  |
|  | - Discount validation      |  | - ResolveRates()          |  |
|  +---------------------------+  | - FindTypeOfChargesThat   |  |
|                                  |   Apply()                 |  |
|                                  +---------------------------+  |
+---------------------------------------------------------------+
                |
                v
+---------------------------------------------------------------+
|                    RESOLUTION ENGINE                            |
|  +---------------------------+  +---------------------------+  |
|  | RateResolutionMgr         |  | TOCResolutionMgr          |  |
|  | - FindLowestRankingRate   |  | - FindTypeOfChargesThat   |  |
|  |   Detail()                |  |   Apply()                 |  |
|  | - GetActualRate()         |  | - FindFuelTypeOfCharges   |  |
|  | - GetFuelPercent()        |  |   ThatApply()             |  |
|  | - GetRate()               |  | - AreTOCRulesValid()      |  |
|  | - GetPossibleRatesFor     |  | - AreTOCSpecialRules      |  |
|  |   Contract()              |  |   Valid()                 |  |
|  +---------------------------+  +---------------------------+  |
|  +---------------------------+                                  |
|  | TierRateResolutionMgr     |                                  |
|  | - GetTierRateResult()     |                                  |
|  | - BuildRateDetailTier     |                                  |
|  |   Block()                 |                                  |
|  +---------------------------+                                  |
+---------------------------------------------------------------+
                |
                v
+---------------------------------------------------------------+
|                    DATA ACCESS LAYER                            |
|  +---------------------------+  +---------------------------+  |
|  | IQPTMDataAccess_Rate       |  | IQPTMDataAccess_          |  |
|  | IQPTMDataAccess_RateComplete| |  RTTypeOfCharge           |  |
|  +---------------------------+  +---------------------------+  |
+---------------------------------------------------------------+
                |
                v
+---------------------------------------------------------------+
|                    CACHE LAYER                                  |
|  +---------------------------+  +---------------------------+  |
|  | RateCache                  |  | ContractCache             |  |
|  | - GetRateDetails()         |  | - GetTypeOfCharge()       |  |
|  | - GetRateTOC()             |  | - GetContract()           |  |
|  | - GetRateTier()            |  | - GetContractPreference() |  |
|  | - GetRateTierDetailList()  |  +---------------------------+  |
|  | - GetRateSchedule()        |  +---------------------------+  |
|  | - GetRateTosTocRuleXref()  |  | LocationCache             |  |
|  | - GetRateTocObjectXref()   |  | - GetLocation()           |  |
|  +---------------------------+  | - GetLocationGroup()      |  |
|                                  | - GetLocationGroupType()  |  |
|                                  +---------------------------+  |
+---------------------------------------------------------------+
```

### Key Source File Locations

| Component | File Path | Lines |
|-----------|-----------|-------|
| Rate Resolution Manager | `Quorum.QPTM.ServiceCore.Rate/RateResolutionMgr.cs` | ~1000 |
| TOC Resolution Manager | `Quorum.QPTM.ServiceCore.Rate/TOCResolutionMgr.cs` | ~483 |
| Tier Rate Resolution Manager | `Quorum.QPTM.ServiceCore.Rate/TierRateResolutionMgr.cs` | ~367 |
| Rate Resolution Interface | `Quorum.QPTM.ServiceCore.Rate/IRateResolutionMgr.cs` | ~17 |
| TOC Resolution Interface | `Quorum.QPTM.ServiceCore.Rate/ITOCResolutionMgr.cs` | ~14 |
| Rate Service | `Quorum.QPTM.ServiceCore.Rate/QPTMRateService.cs` | ~489 |
| Service Core (Rate Maintenance) | `Quorum.QPTM.ServiceCore/QPTMServiceCore_RateMaintenance.cs` | ~1207 |
| Rate Maintenance Controller | `Quorum.QPTM.Web.Core/Controllers/RateMaintenanceController.cs` | ~1122 |
| UIController | `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerRateMaintenance.cs` | Variable |
| Validation Context | `Quorum.QPTM.Validations/Screens/RateMaintenance/Context/QPTMRateMaintenanceValidationContext.cs` | ~120 |

---

## Rate Resolution Engine

### `RateResolutionMgr` (implements `IRateResolutionMgr`)

**File**: `Quorum.QPTM.ServiceCore.Rate/RateResolutionMgr.cs`

This is the core rate resolution engine. It is instantiated via DI and used by `QPTMRateService`.

#### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `GetActualRate()` | `decimal? GetActualRate(short nTspNo, string sCtrNo, string sLocId1, string sLocId2, DateTime dtAsOfDt, string sTocCd, string sRouteCd, string sTosCd, string sRateTypeCtgryCd, out string sRateTypeCd, out string sChargePeriod, out int? nRateHdrId, out string sPriceTypeCd)` | Resolves a rate amount for a given TOC, handling FIX/PCT/FRM/SSN price types |
| `GetFuelPercent()` | `decimal GetFuelPercent(short nTspNo, string sTocCd, string sCtrNo, string sTOSCd, DateTime dtAsOfDt, string sLocId1, string sLocId2, string sRouteCd, out bool bRateFound)` | Resolves fuel retention percentage using BLLD rate type category |
| `GetRate()` | `bool GetRate(short nTspNo, string sCtrNo, string sLocId1, string sLocId2, DateTime dtAsOfDt, string sTocCd, string sRouteCd, string sTosCd, string sRateTypeCtgryCd, string sProcessID, double dInputQty, out RateResultsDO rateResults)` | Full rate resolution with quantity input, supports FIX/PCT/TR price types and monthly-to-daily conversion |
| `ResolveFuelPreference()` | `string ResolveFuelPreference(short tspNo, string contractNo, DateTime gasDay)` | Returns fuel preference code (FIK/TIK/CFF) from contract preference or contract default |
| `GetPossibleRatesForContract()` | `IEnumerable<RateResolutionDO> GetPossibleRatesForContract(short tspNo, string ctrNo, DateTime gasDayFrom, DateTime gasDayTo, string tocCd, string IdLoc)` | Returns all possible rate details for a contract over a date range, used for Rate Query display |

#### `FindLowestRankingRateDetail()` - Core Algorithm

```
Private method: ~220 lines
Location: RateResolutionMgr.cs, line ~598

Algorithm:
1. Build location group lists from LocationCache
2. Get rate details from RateCacheAccess matching TOC, TSP, date, locations
3. Sort by TOC code
4. For each rate detail:
   a. Filter by supported price types (if specified)
   b. Calculate RateType rank via _RateCacheAccess.GetRateTypeRank()
   c. Calculate Header rank via CalculateHeaderRank() [1-4 scale]
   d. Calculate Detail rank via CalculateDetailRank() [composite formula]
   e. Skip if any rank is null (no match)
   f. Track lowest rank across all three levels
   g. Priority order: HeaderRank > RateTypeRank > DetailRank
5. Return single best rate or throw on ties
```

#### `CalculateHeaderRank()` - Header Ranking Logic

```csharp
// Returns nullable int rank based on contract/TOS match:
// 1 = Contract match + Override
// 2 = TOS match + Override
// 3 = Contract match + Non-override
// 4 = TOS match + Non-override
// null = No match (rate excluded)
```

#### `CalculateDetailRank()` - Detail Ranking Formula

```csharp
decimal rank = ((nCtgryRank1 + nCtgryRank2) * 1000000)  // Location group category rank
             + ((nTypeRank1 + nTypeRank2)   * 10000)     // Location group type rank
             + ((nLevel1 + nLevel2)         * 100)        // System level number
             + (nExpectRouteCd);                          // Route code penalty (0 or 1)
```

#### Formula Price Resolution

```
GetFormulaPrice():
1. Get index headers (up to 3) from RateDataAccess.GetIndexHdr()
2. For each index, find detail where EffDateFrom <= AsOfDate <= EffDateTo
3. Build formula variables: INDEX_PRICE, INDEX_PRICE2, INDEX_PRICE3
4. Evaluate formula via QUserDefinedFormulaService.GetFormulaDefinition()
```

#### Seasonal Price Resolution

```
GetSeasonalPrice():
1. Load seasonal profile header via QPTMService_RateSeasonalProfileMaintenance
2. For each seasonal detail, match gas day (MMDD) against BeginMonthDay/EndMonthDay
3. Handle three date-wrap scenarios for cross-year seasons
4. Apply the matching season's price type (FIX, FRM, IDX)
```

---

## TOC Resolution Engine

### `TOCResolutionMgr` (implements `ITOCResolutionMgr`)

**File**: `Quorum.QPTM.ServiceCore.Rate/TOCResolutionMgr.cs`

Determines which Types of Charge apply to a given transaction context.

#### Key Methods

| Method | Description |
|--------|-------------|
| `FindFuelTypeOfChargesThatApply()` | Finds fuel-related TOCs matching a TOS and fuel preference code. Used by fuel calculation. |
| `FindTypeOfChargesThatApply()` | Finds TOCs by process ID and TOS, applying all TOC rules. Used by billing and rate query. |

#### TOC Resolution Flow

```
FindTypeOfChargesThatApply():
1. Get RateTocProcessXRef from cache (by TSP, ProcessID, TOS, RateTypeCategory)
2. Also get records with empty TOS (wildcard match) - Issue 40706
3. Get RateTosTocRuleXref from cache (by TSP, TOS, date)
4. Cross-reference: Only TOCs that appear in BOTH xref lists are candidates
5. For each candidate TOC:
   a. AreTOCRulesValid() - Apply include/exclude rule logic
   b. AreTOCSpecialRulesValid() - Apply gathering special rule
6. Return list of valid TOC codes
```

#### `AreTOCRulesValid()` - Rule Evaluation

```
For each TOC rule in RTTypeOfChargeRule:
1. Track Include/Exclude rule matches separately
2. Check each rule criterion (RouteCode, RateFormType, LocAttr1, LocAttr2,
   InvAdjType, RecCtrTos, DelCtrTos, TosAttr, QtySign, PpaInd,
   PenaltyType, TransType, OperImpArea, RecRegion, DelRegion,
   RecPipelineSys, DelPipelineSys)
3. If criterion is specified on rule but doesn't match input, skip (continue)
4. If all specified criteria match:
   - Include rule: set bIncludeValid = true
   - Exclude rule: set bExcludeValid = true
5. Final result: Invalid if excluded OR (includes exist but none valid)
```

---

## Tier Rate Resolution Engine

### `TierRateResolutionMgr`

**File**: `Quorum.QPTM.ServiceCore.Rate/TierRateResolutionMgr.cs`

Handles tiered rate resolution when a rate detail has price type `TR`.

#### Key Method: `GetTierRateResult()`

```
1. Get TierDO from RateCache.GetRateTier()
2. Get TierDetailDO list from RateCache.GetRateTierDetailList()
3. Get TOC to determine charge basis code and scale
4. Get tier basis quantity via GetTierBasis()
5. Switch on TierMethCode:
   - "B" (Block): BuildRateDetailTierBlock()
   - "S" (Step): Not supported, returns false
6. Return RateResultsDO with tier details
```

#### `BuildRateDetailTierBlock()` - Block Tier Logic

```
For each tier detail:
  If basis qty successfully retrieved AND != 0:
    Check if TierBasisQty falls between TierStart and TierEnd
    If match: Use entire input qty at this tier's price
  Else (basis not available):
    Put all input qty into the LAST tier (fallback behavior)
```

#### Floating-Point Comparison

The tier engine uses a custom `CompareValue()` method with precision `5e-11` to handle floating-point comparison issues.

---

## Service Layer

### `QPTMRateService` (Rate Runtime Service)

**File**: `Quorum.QPTM.ServiceCore.Rate/QPTMRateService.cs`

Implements `IQPTMFuelCalcService` and `IQPTMRateService`. This is the entry point for runtime rate operations.

| Method Group | Key Methods |
|-------------|-------------|
| Fuel Calculation | `CalculateFuel()` (multiple overloads for single/list/month), `CalculateFuelForMonth()` |
| Rate Query | `GetActualRate()`, `GetDailyRate()`, `FindRatesThatApply()`, `ResolveRates()` |
| TOC Resolution | `FindTypeOfChargesThatApply()` |
| Rate Lookup | `GetRate()`, `GetRateSchedule()`, `GetTosTocRuleXRefByTosToc()` |

#### Fuel Calculation Flow

```
CalculateFuel(nominations, gasDay):
  For each path nomination:
    1. Get RecCtrTos and DelCtrTos from contract cache
    2. Call CalculateFuel(tspNo, ctrNo, locId1, locId2, ...) which:
       a. ResolveFuelPreference() -> FuelPrefCd
       b. FindFuelTypeOfChargesThatApply() -> TOCList
       c. Validate charge basis consistency
       d. For each TOC: GetFuelPercent() -> accumulate
    3. Set nom.FuelPct, nom.FuelPrefCode, nom.ChargeBasisCode
```

### `QPTMServiceCore (partial class for Rate Maintenance)`

**File**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_RateMaintenance.cs`

Implements `IQPTMService_RateMaintenance`. This is the CRUD service for the Rate Maintenance screen.

#### Method Groups

| Group | Methods | Description |
|-------|---------|-------------|
| **Rate Header CRUD** | `GetSingleRateMaintenance()`, `GetMultipleRateMaintenance()`, `UpdateSingleRateMaintenance()` | Basic rate header operations |
| **Rate Complete CRUD** | `GetSingleRateMaintenanceComplete()`, `UpdateSingleRateMaintenanceComplete()` | Complete object operations (header + details + associations) |
| **Validation** | `ValidateSingleRateMaintenance()`, `ValidateMultipleRateMaintenance()`, `ValidateSingleRateMaintenanceComplete()` | Validation orchestration |
| **TOC Queries** | `GetRTTypeOfChargeByTspNo()` | Fetch TOC lookup data |
| **Location Matrix** | `GetLocationMatrixSearchData()`, `GetPALocationGroupsByLocGrpTypeCode()`, `GetLocGrpLocListByLocGrpId()` | Location matrix population |
| **Rate Stat Check** | `CheckRateDetailExistsInRateStat()` | Check if rate details are used in billing |
| **Discount Validation** | `InsertInvalidDiscInput()`, `ProcessRateCompletePostProcessRun()` | Discount rate tariff validation via batch |

#### Update Flow for RateCompleteDO

```
UpdateSingleRateMaintenanceComplete():
1. Validate via ValidateSingleRateMaintenanceComplete()
2. If errors exist, return without saving
3. Generate RATE_HDR_ID if new (via GetNextSeqNo)
4. If discount rate type: InsertInvalidDiscInput() for batch validation
5. If post-validation errors exist, return
6. Execute save within event context (QPTMRateMaintenanceDetectorContext)
7. Update associated discount offer status to ACCEPTED if applicable
8. Return only the most current time slice
```

---

## Web Application Layer

### `RateMaintenanceController`

**File**: `Quorum.QPTM.Web.Core/Controllers/RateMaintenanceController.cs`

MVC controller for the Rate Maintenance screen. Inherits from `RateControllerBase<QUIControllerRateMaintenance, RateMaintenanceRootVM>`.

#### Security

```csharp
[QScreenSecurityObject(Constants.SecurityObjectIDs.RateMaintenance)]
```

#### Controller Actions

| Action | HTTP | Description |
|--------|------|-------------|
| **Tabs** | | |
| `GeneralTab()` | GET | Returns `_RateMaintenance_GeneralTab` partial view |
| `LocationDetailsTab()` | GET | Returns `_RateMaintenance_LocationDetailsGridTab` partial view |
| `LocationDetailsMatrixTab()` | GET | Returns `_RateMaintenance_LocationDetailsMatrixTab` partial view |
| `RateContractAssocTab()` | GET | Returns `_RateMaintenance_RateContractAssocTab` partial view |
| `RateInventoryAssocTab()` | GET | Returns `_RateMaintenance_RateInventoryAssocTab` partial view |
| `RateTosAssocTab()` | GET | Returns `_RateMaintenance_RateTosAssocTab` partial view |
| `GetMatrixGrid()` | GET | Returns `_RateMaintenance_LocationDetailsMatrixGrid` partial view |
| **Field Updates** | | |
| `RateMaintenanceFieldUpdate()` | POST | Handles rate header field changes |
| `RateMaintenanceGeneralFieldUpdate()` | POST | Handles general tab field changes |
| `LocationMatrixFieldUpdate()` | POST | Handles matrix field changes |
| **Location Details Grid** | | |
| `LocationDetailsGridGetData()` | POST | Kendo grid data read |
| `LocationDetailGridUpdate()` | POST | Grid row update |
| `LocationDetailGridAddNewRow()` | POST | Add/clone row |
| `LocationDetailGridDeleteRow()` | POST | Delete row |
| `LocationDetailGridBulkEdit()` | GET/PUT | Bulk edit export/import |
| `LocationDetailGridExcelExport()` | GET/POST | Excel export |
| `LocationDetailGridExcelImport()` | POST | Excel import |
| **Location Matrix Grid** | | |
| `LocationMatrixGridGetData()` | POST | Matrix grid data read |
| `LocationMatrixGridUpdate()` | POST | Matrix cell update (with PCT / 100 conversion) |
| **Rate/Contract Grid** | | |
| `RateContractAssocGridGetData()` | POST | Contract association grid read |
| `RateContractAssocGridUpdate()` | POST | Contract association update |
| **Rate/TOS Grid** | | |
| `RateTosAssocGridGetData()` | POST | TOS association grid read (expected) |
| **Rate/Inventory Grid** | | |
| `RateInventoryAssocGridGetData()` | POST | Inventory association grid read (expected) |

#### Navigation Links

The controller provides links to related screens:

| Link | Target Screen | Parameters |
|------|--------------|------------|
| Location Group Maintenance | `LocationGroupMaintenance` | `LocId` from selected rate detail |
| Location Maintenance | `LocationMaintenance` | `LocId` from rate detail |
| Rate Query | `RateQuery` | `RateHeaderID`, `OfferId` |
| Seasonal Profile Maintenance | `RateSeasonalProfileMaintenance` | - |
| TOS Maintenance | `TOSMaintenance` | `RateHeaderID` (hidden link) |
| Tier Maintenance | `TierMaintenance` | - |

### UIController: `QUIControllerRateMaintenance`

**File**: `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerRateMaintenance.cs`

Manages screen state including:
- `Rate` (RateCompleteDO) - The main data object
- `MyParams` - Screen parameters (IdRateHdr, RateNm, EffDateFrom, EffDateTo)
- `LocationMatrix` - Matrix display data
- `EnableAssocOfferID`, `EnableTOC`, `EnableMatrixDisplay` - Feature flags
- `QtyRetainedPctScale` - Decimal scale for percentage display
- `ChargeBasisCode` - Current charge basis
- `IsSrLevel` - Whether Sr Level IND is enabled (makes location columns read-only)
- `ScreenAsOfDate` - Current as-of date

### View Models

| ViewModel | File | Description |
|-----------|------|-------------|
| `RateMaintenanceRootVM` | `Quorum.QPTM.Web.Core/ViewModels/RateMaintenanceRootVM.cs` | Root view model with header fields and feature flags |
| `RateDetailVM` | `Quorum.QPTM.Web.Core/ViewModels/CodeGen/RateDetailVM.cs` | Location details grid row view model |
| `RateContractVM` | Generated | Rate/Contract association grid view model |
| `RateVM` | `Quorum.QPTM.Web.Core/ViewModels/CodeGen/RateVM.cs` | Rate header view model |

---

## Validation Layer

### Validation Context

**File**: `Quorum.QPTM.Validations/Screens/RateMaintenance/Context/QPTMRateMaintenanceValidationContext.cs`

```csharp
[QValidationGroup("QPTMRateMaintenanceComplete")]
public class QPTMRateMaintenanceValidationContext : QPTMValidationContextBase
```

Key properties:
- `DataToValidate` - `IEnumerable<RateCompleteDO>`
- `ContractList` - Lazy-loaded contracts referenced by rate contract associations
- `TocAttributeMapping` - Pre-populated TOC attribute mapping for validation rules
- `ValidationHelper` - `QValidationRateMaintenanceHelper` instance

### Validation Rules

| Rule | File | Description |
|------|------|-------------|
| `QPTMValidationRateMaintenance012` | `General/QPTMValidationRateMaintenance012_GenChkDuplicateError.cs` | Check for duplicate rate header records |
| `QPTMValidationRateMaintenance014` | `RateTOSAssociation/QPTMValidationRateMaintenance014_RateTOSKeyRecordIntegrity.cs` | TOS association key integrity |
| `QPTMValidationRateMaintenance018` | `RateTOSAssociation/QPTMValidationRateMaintenance018_RateTOSKeyRecordIntegrity.cs` | TOS key record integrity |
| `QPTMValidationRateMaintenance031` | `RateContractAssociation/QPTMValidationRateMaintenance031_ContractValidateRateContractisActive.cs` | Validate rate contract is active |
| `QPTMValidationRateMaintenance035` | `RateContractAssociation/QPTMValidationRateMaintenance035_ContractValidateAmendment.cs` | Validate contract amendment |
| `QPTMValidationRateMaintenance045` | `RateContractAssociation/QPTMValidationRateMaintenance045_ContractValidateAmendNoisRequiredforPAL.cs` | Validate amend number for PAL |
| `QPTMValidationRateMaintenance051` | `LocationDetails_Grid/QPTMValidationRateMaintenance051_LocDtlGridChkDuplicate.cs` | Check for duplicate location details |
| `QPTMValidationRateMaintenance052` | `LocationDetails_Grid/QPTMValidationRateMaintenance052_LocDtlGridChkIsMatchFoundinCtrAssoc.cs` | Verify location detail matches contract association |
| `QPTMValidationRateMaintenance057` | `LocationDetails_Grid/QPTMValidationRateMaintenance057_LocDtlGridTocRTComboChk.cs` | TOC and rate type combination check |
| `QPTMValidationRateMaintenance080` | `LocationDetails_Grid/QPTMValidationRateMaintenance080_LocDtlGridChkLocIdandLocGrpIdisValid.cs` | Location ID and Location Group ID validity |

### Validation Base

**File**: `Quorum.QPTM.Validations/Screens/RateMaintenance/Validation Rules/QPTMRateMaintenanceValidationBase.cs`

Base class for all rate maintenance validation rules.

---

## Data Model

### Core Data Objects

| Data Object | File | Description |
|-------------|------|-------------|
| `RateDO` | `Quorum.QPTM.DataObject/CodeGen/RateDO.cs` + `RateDOExt.cs` | Rate header with all header-level properties |
| `RateDetailDO` | `Quorum.QPTM.DataObject/CodeGen/RateDetailDO.cs` + `RateDetailDOExt.cs` | Rate detail (location-level) with rates, locations, tiers |
| `RateCompleteDO` | `Quorum.QPTM.DataObject/CodeGen/RateCompleteDO.cs` | Complete rate object wrapping header, details, and associations |
| `RateContractDO` | `Quorum.QPTM.DataObject/CodeGen/RateContractDO.cs` + `RateContractDOExt.cs` | Rate-to-contract association |
| `RateTypeOfServiceDO` | Generated | Rate-to-TOS association |
| `RateInvQtyXRefDO` | Generated | Rate-to-inventory quantity cross reference |
| `RateResultsDO` | `Quorum.QPTM.DataObject/RateResultsDO.cs` | Rate resolution output (rate, qty, amount, tier results) |
| `RateResultsTierDO` | `Quorum.QPTM.DataObject/RateResultsTierDO.cs` | Tier-level resolution results |
| `RateResolutionDO` | Generated | Rate resolution display object (for Rate Query) |
| `RTTypeOfChargeDO` | `Quorum.QPTM.DataObject/CodeGen/RTTypeOfChargeDO.cs` | Type of Charge header |
| `RTTypeOfChargeRuleDO` | `Quorum.QPTM.DataObject/CodeGen/RTTypeOfChargeRuleDO.cs` | TOC rule record |
| `RTTypeOfChargeAttributeDO` | `Quorum.QPTM.DataObject/CodeGen/RTTypeOfChargeAttributeDO.cs` | TOC attribute |
| `TierDO` | `Quorum.QPTM.DataObject/CodeGen/TierDO.cs` | Tier header |
| `TierDetailDO` | `Quorum.QPTM.DataObject/CodeGen/TierDetailDO.cs` | Tier detail (start/end ranges, prices) |
| `RateTosTocRuleXRefDO` | `Quorum.QPTM.DataObject/CodeGen/RateTosTocRuleXRefDO.cs` | TOS-TOC rule cross reference |
| `RateTocProcessXRefDO` | Generated | TOC-Process cross reference |
| `RateScheduleDO` | Generated | Rate schedule definition |

### RateResultsDO Properties

| Property | Type | Description |
|----------|------|-------------|
| `Rate` | `decimal?` | Resolved rate (may be converted to daily) |
| `ActualRate` | `decimal?` | Original rate before daily conversion |
| `Qty` | `double` | Input quantity |
| `Amount` | `double` | Calculated amount (Rate * Qty) |
| `ChargePerCd` | `string` | Charge period code |
| `TocCd` | `string` | Type of charge code |
| `RateHdrId` | `int` | Resolved rate header ID |
| `RateDtlId` | `int` | Resolved rate detail ID |
| `UOMCd` | `string` | Unit of measure code |
| `RateTypeCd` | `string` | Rate type code |
| `RateResultsTiers` | `List<RateResultsTierDO>` | Tier-level breakdown (for TR price type) |

### RateDetailDO Extension Properties

| Property | Description |
|----------|-------------|
| `RateHeader` | Parent `RateDO` reference |
| `TocCode` | Delegated to `RateHeader.TocCode` |
| `Loc1Name` / `Loc2Name` | Display names for locations |
| `LocGrp1Name` / `LocGrp2Name` | Display names for location groups |
| `QtyRetainedPctExt` | Extended property that multiplies/divides by 100 for display |

---

## Database Schema

### Primary Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `RTCTRL_RT_HDR` | Rate header | `RATE_HDR_ID`, `TSP_NO`, `EFF_DT_FROM`, `TOC_CD`, `RATE_TYPE_CD`, `PRICE_TYPE_CD`, `CHARGE_PER_CD` |
| `RTCTRL_RT_DTL` | Rate detail (locations and rates) | `RATE_DTL_ID`, `RATE_HDR_ID`, `TSP_NO`, `ID_LOC_1`, `ID_LOC_2`, `ID_LOC_GRP_1`, `ID_LOC_GRP_2`, `FIXED_RATE`, `QTY_RETAINED_PCT` |
| `RTCTRL_RT_CTR` | Rate-to-contract association | `RATE_HDR_ID`, `CTR_NO`, `TSP_NO`, `EFF_DT_FROM` |
| `RTCTRL_RT_TOS` | Rate-to-TOS association | `RATE_HDR_ID`, `TOS_CD`, `TSP_NO`, `EFF_DT_FROM` |
| `RTCTRL_RT_INV_QTY_XREF` | Rate-to-inventory xref | `RATE_HDR_ID`, `TSP_NO`, `EFF_DT_FROM` |
| `RTCTRL_TOC` | Type of Charge | `TOC_CD`, `TSP_NO`, `CHARGE_BASIS_CD`, `FUEL_PREF_CD`, `SCALE` |
| `RTCTRL_TOC_RULE` | TOC rules (include/exclude) | `TOC_CD`, `TSP_NO`, `INCLUDE_TYPE_CD`, `ROUTE_CD`, `LOC_ATTR_CD_1`, etc. |
| `RTCTRL_TOC_ATTR` | TOC attributes | `TOC_CD`, `TSP_NO`, `TOC_ATTR_CD`, `IS_ATTR_TRUE` |
| `RTCTRL_TOS_TOC_RULE_XREF` | TOS-to-TOC rule cross reference | `TSP_NO`, `TOS_CD`, `TOC_CD`, `EFF_DT_FROM` |
| `RTCTRL_TOC_OBJECT_XREF` | TOC-to-process cross reference | `TSP_NO`, `TOC_CD`, `PROCESS_ID`, `RATE_TYPE_CTGRY_CD` |
| `RTCTRL_TIER` | Tier header | `RATE_TIER_ID`, `TSP_NO`, `TIER_METH_CD`, `TIER_TYPE_CD`, `TIER_CHARGE_PER_CD` |
| `RTCTRL_TIER_DTL` | Tier detail (ranges and prices) | `TIER_DTL_ID`, `RATE_TIER_ID`, `TIER_START`, `TIER_END`, `FIXED_PRICE`, `PRICE_TYPE_CD` |
| `RTCTRL_RATE_SCHD` | Rate schedule | `RATE_SCHD_CD` |
| `RTCTRL_INDEX_HDR` | Index header | `INDEX_ID`, `TSP_NO` |
| `RTCTRL_INDEX_DTL` | Index detail (prices by date) | `INDEX_ID`, `EFF_DT_FROM`, `EFF_DT_TO`, `PRICE` |
| `RTCTRL_SEASONAL_PROF_HDR` | Seasonal profile header | `SEASONAL_PROF_ID`, `TSP_NO` |
| `RTCTRL_SEASONAL_PROF_DTL` | Seasonal profile detail | `SEASONAL_PROF_ID`, `BEGIN_MONTH_DAY`, `END_MONTH_DAY`, `PRICE_TYPE_CD`, `FIXED_PRICE` |
| `CATRAN_RATE_STAT` | Billing rate statistics | `RATE_HDR_ID`, `RATE_DTL_ID`, `TSP_NO`, `GAS_DAY` |
| `BLTRAN_INVALID_DISC_INPUT` | Discount validation input | `SET_ID`, `TSP_NO`, `TOC_CD`, `RATE_HDR_ID`, `RATE_DTL_ID` |
| `BLTRAN_INVALID_DISC` | Discount validation results | `SET_ID`, `INVALID_DISC_INPUT_ID` |

### Supporting Tables

| Table | Description |
|-------|-------------|
| `NNCTRL_CTR_PREF` | Contract preferences (fuel preference) |
| `KCTRL_CTR_HDR` | Contract header (TOS, fuel pref default, RT_CONV_BASIS_CD) |
| `PACTRL_LOC_GRP_LOC` | Location group membership |
| `PACTRL_LOC_GRP_LOC_GRP` | Location group to location group mapping |
| `QCODE_LOC_GRP_TYPE` | Location group type (rank, category, system level) |
| `QCODE_LOC_GRP_CTGRY` | Location group category (rank) |
| `QCODE_RATE_TYPE` | Rate type definitions (rank) |
| `QCODE_RATE_TYPE_CTGRY` | Rate type category definitions |

---

## Caching

### Rate Cache (`RateCache`)

Accessed via `SingletonCache<RateCache>.Instance`. Provides:

| Method | Description |
|--------|-------------|
| `GetRateDetails()` | Get rate details by TOC, TSP, date, locations, and location groups |
| `GetRateDetailsInDateRange()` | Get rate details across a date range |
| `GetRateTOC()` | Get TOC by TSP and TOC code |
| `GetRateTier()` | Get tier header by tier ID and TSP |
| `GetRateTierDetailList()` | Get tier details by tier ID and TSP |
| `GetRateTosTocRuleXrefByTosCd()` | Get TOS-TOC rule xref by TOS code and date |
| `GetRateTocObjectXref()` | Get TOC-process xref by process ID, TOS, rate type category |
| `GetRateSchedule()` | Get rate schedule by code |
| `GetMultipleRates()` | Get multiple rates by TSP, contract, TOC list, rate type, price type |

### Contract Cache (`ContractCache`)

Accessed via `SingletonCache<ContractCache>.Instance`. Provides:

| Method | Description |
|--------|-------------|
| `GetContract()` | Get contract by number, TSP, and date |
| `GetContractPreference()` | Get contract fuel preference |
| `GetTypeOfCharge()` | Get TOC definition including rules and attributes |

### Location Cache (`LocationCache`)

Accessed via `SingletonCache<LocationCache>.Instance`. Provides:

| Method | Description |
|--------|-------------|
| `GetLocation()` | Get location by ID, TSP, and date |
| `GetLocationGroup()` | Get location group by ID and TSP |
| `GetLocationGroupType()` | Get group type (rank, category) |
| `GetLocationGroupCategory()` | Get group category (rank) |
| `GetLocationGroupsAsStringList()` | Get all groups a location belongs to |
| `GetSystemLocationGroupByType()` | Get system location group by type code |
| `IsLocationAttributeTrue()` | Check location attribute value |

### Cache Refresh

The rate cache can be refreshed via `IRateCacheAccess.RefreshEntireCache()`. This is triggered when `CalculateFuel()` is called with `bRefresh = true`.

---

## Configuration

### TSP Configuration Settings

| Setting | Key | Description |
|---------|-----|-------------|
| Accounting Month Lag Time | `TSP > ACCTG_MTH_LAG_TIME` | Used in tier basis calculation to offset the accounting month |

### Contract-Level Configuration

| Field | Table | Description |
|-------|-------|-------------|
| `RT_CONV_BASIS_CD` | `KCTRL_CTR_HDR` | Rate conversion basis (AVG or calendar) |
| `FUEL_PREF_CD` | `KCTRL_CTR_HDR` | Default fuel preference code |

### TSP Preferences

| Field | Description |
|-------|-------------|
| `BillingPpaCutoffDate` | PPA cutoff date - rate queries not allowed before this date |
| `EngUomCode` | Energy UOM code |
| `VolUomCode` | Volume UOM code |

---

## Integration Points

### Consumers of Rate Resolution

| System | Usage |
|--------|-------|
| **Fuel Calculation** | `IQPTMFuelCalcService.CalculateFuel()` - called during nomination processing |
| **Billing** | `IQPTMRateService.GetRate()` - called to resolve rates for invoice line items |
| **RFS (Receipt/Delivery Fuel Scheduling)** | Uses `GetActualRate()` with supported price type filtering (FIX, PCT only) |
| **Rate Query Screen** | Uses `ResolveRates()` and `GetPossibleRatesForContract()` for display |
| **Capacity Release** | Rate bidding uses rate resolution for bid evaluation |
| **Discount Validation** | `RTVALDDSRT` batch process validates discount rates against tariff |

### Batch Processes

| Process ID | Name | Description |
|------------|------|-------------|
| `RTVALDDSRT` | Rate Validate Discount Sort | Validates discount rate inputs against tariff max/min rates. Launched synchronously during rate save. |

### Events

| Event Context | Description |
|--------------|-------------|
| `QPTMRateMaintenanceDetectorContext` | Detects rate changes during save for PPA reallocation |

---

## Key Processing Flows

### Rate Maintenance Save Flow

```
User clicks Save
  -> RateMaintenanceController (ValidateBeforeSave JS callback)
  -> QPTMServiceCore.UpdateSingleRateMaintenanceComplete()
    1. ValidateSingleRateMaintenanceComplete()
       -> QPTMRateMaintenanceValidationContext
       -> Execute all QPTMValidationRateMaintenance rules
    2. Generate RATE_HDR_ID if new
    3. If Discount type: InsertInvalidDiscInput() -> RTVALDDSRT batch
    4. ExecuteAndHandleEvents(QPTMRateMaintenanceDetectorContext)
       -> dataAccess.UpdateSingleRateComplete()
    5. Update associated discount offer status
    6. Return updated RateCompleteDO
  -> IsShowPPAReallocationDialog (post-save callback)
```

### Fuel Calculation Flow

```
Nomination Processing
  -> QPTMRateService.CalculateFuel(nominations, gasDay)
    For each path nomination:
      1. ResolveFuelPreference(tspNo, ctrNo, gasDay) -> fuelPrefCd
      2. TOCResolutionMgr.FindFuelTypeOfChargesThatApply(...) -> TOCList
      3. Validate charge basis consistency across TOCs
      4. For each fuel TOC:
         RateResolutionMgr.GetFuelPercent(tspNo, tocCd, ctrNo, ...)
           -> FindLowestRankingRateDetail(... "BLLD")
           -> Return QtyRetainedPct
      5. Sum fuel percentages
      6. Set nom.FuelPct, nom.FuelPrefCode, nom.ChargeBasisCode
```

---

*Last updated: 2026-03-03*

*Document version: 1.0*
