---
title: Rate Management (RATE) - Domain Concepts
category: domain
feature: Rate Management (RATE)
related_repos: Web, Batch
keywords: RATE, rate management, rate schedule, rate resolution, TOC, type of charge, tier, tiered rates, fuel, fuel preference, seasonal, rate type, price type, FIX, PCT, FRM, IDX, SSN, TR, LMP, rate contract, rate detail, rate header, rate maintenance, discount, tariff
last_updated: 2026-03-03
---

# Rate Management (RATE) - Domain Concepts

## Overview

This document explains the **business concepts** behind Rate Management in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, rate resolution logic, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Rate Schedules and Rate Headers](#rate-schedules-and-rate-headers)
3. [Rate Types and Rate Type Categories](#rate-types-and-rate-type-categories)
4. [Price Types](#price-types)
5. [Type of Charge (TOC) Hierarchy](#type-of-charge-toc-hierarchy)
6. [TOC Rules and Validation](#toc-rules-and-validation)
7. [Rate Resolution Process](#rate-resolution-process)
8. [Tiered Rates](#tiered-rates)
9. [Seasonal Rate Profiles](#seasonal-rate-profiles)
10. [Fuel Preference and Fuel Calculation](#fuel-preference-and-fuel-calculation)
11. [Rate-to-Contract Relationship](#rate-to-contract-relationship)
12. [Rate-to-TOS Relationship](#rate-to-tos-relationship)
13. [Discount Rate Validation](#discount-rate-validation)
14. [Charge Period and Daily Conversion](#charge-period-and-daily-conversion)
15. [Location Matrix and Location Groups](#location-matrix-and-location-groups)
16. [Key Business Rules](#key-business-rules)
17. [Glossary](#glossary)
18. [Related Documentation](#related-documentation)

---

## System Overview

### What is Rate Management?

**Rate Management (RATE)** is the subsystem within QPTM that defines, maintains, and resolves the transportation rates charged for moving natural gas through the pipeline system. Rates are the foundation for billing, fuel calculation, and financial settlement across all transportation activities.

**Business Purpose:**
- Define tariff and negotiated rates for pipeline transportation services
- Maintain rate schedules with effective-dated rate headers and location-based rate details
- Resolve the correct applicable rate for a given nomination, contract, TOC, location, and gas day
- Calculate fuel retention percentages based on rate configurations
- Support tiered, seasonal, formula-based, and index-based pricing
- Enforce FERC tariff compliance through max/min tariff rate type validation
- Associate rates to contracts and types of service (TOS)

### Key Business Value

- **Accurate Billing**: Ensures correct rates are applied to transportation charges
- **Regulatory Compliance**: Enforces FERC tariff maximum and minimum rate boundaries
- **Flexible Pricing**: Supports fixed, percentage, formula, index, seasonal, tiered, and lump sum pricing
- **Automated Fuel Calculation**: Resolves fuel retention rates for nomination processing
- **Rate-Contract Linkage**: Ties rates to specific contracts or types of service for precise billing

---

## Rate Schedules and Rate Headers

### Rate Schedule

A **Rate Schedule** (`RTCTRL_RATE_SCHD`) is the top-level organizational grouping for rates. It represents a named collection of rate configurations published by the pipeline (e.g., "FT-1" for Firm Transportation Schedule 1).

### Rate Header

A **Rate Header** (`RTCTRL_RT_HDR`) defines the core properties of a rate:

| Field | Description |
|-------|-------------|
| `RATE_HDR_ID` | Unique identifier for the rate header |
| `TSP_NO` | Transporter number |
| `TOC_CD` | Type of Charge code this rate applies to |
| `RATE_TYPE_CD` | Rate type (TMX, TMN, DIS, NEG) |
| `PRICE_TYPE_CD` | Price type (FIX, PCT, FRM, IDX, SSN, TR, LMP) |
| `CHARGE_PER_CD` | Charge period (DAY or MTH) |
| `UOM_TYPE_CD` | Unit of measure type (VOL or ENG) |
| `EFF_DT_FROM` / `EFF_DT_TO` | Effective date range |
| `RATE_NM` | Descriptive name of the rate |
| `IS_OVERRIDE` | Override indicator for ranking priority |
| `RATE_SCHD_CD` | Associated rate schedule code |
| `ID_CONTACT` | Contact person identifier |
| `ID_ASSOC_OFFER` | Associated discount offer ID |

Rate headers are **effective-dated**, meaning multiple time slices can exist for the same `RATE_HDR_ID` to track rate changes over time.

---

## Rate Types and Rate Type Categories

### Rate Types (`RATE_TYPE_CD`)

Rate types classify the purpose or nature of a rate:

| Code | Name | Description |
|------|------|-------------|
| `TMX` | Max Tariff | Maximum tariff rate allowed by FERC |
| `TMN` | Min Tariff | Minimum tariff rate (floor) |
| `DIS` | Discount | Negotiated discount rate below tariff maximum |
| `NEG` | Negotiated | Negotiated rate agreed between parties |

### Rate Type Categories (`RATE_TYPE_CTGRY_CD`)

Rate type categories group rate types for resolution purposes:

| Code | Name | Description |
|------|------|-------------|
| `MAXT` | Max Tariff | Category for maximum tariff rates |
| `MINT` | Min Tariff | Category for minimum tariff rates |
| `BLLD` | Billed | Category for rates actually used in billing |
| `DISC` | Discount | Category for discount rates |

During rate resolution, the system uses the rate type category to filter which rate types are eligible. For example, fuel calculation uses `BLLD` to find the billed rate.

---

## Price Types

Price types define HOW the rate amount is determined. Each rate header has exactly one price type.

| Code | Name | Description | Key Fields |
|------|------|-------------|------------|
| `FIX` | Fixed | A fixed monetary amount per unit | `FIXED_RATE` on rate detail |
| `PCT` | Percent | A percentage of quantity retained (fuel) | `QTY_RETAINED_PCT` on rate detail |
| `FRM` | Formula | Rate calculated via a user-defined formula | `RATE_FORMULA_CD`, `ID_INDEX`, `ID_INDEX2`, `ID_INDEX3` |
| `IDX` | Index | Rate tied to a published price index | `ID_INDEX` on rate detail |
| `SSN` | Seasonal | Rate varies by season/time of year | `ID_SEASONAL_PROF` on rate detail |
| `TR` | Tier | Rate varies by volume tier (block/step) | `ID_RATE_TIER` on rate detail |
| `LMP` | Lump Sum | A flat lump-sum charge | `FIXED_RATE` used as lump sum |

### Price Type Resolution

When the system resolves a rate, it reads the price type from the rate header and applies the corresponding logic:
- **FIX**: Returns `FixedRate` directly from the rate detail
- **PCT**: Returns `QtyRetainedPct` as a percentage value
- **FRM**: Evaluates the formula using index prices as variables (`INDEX_PRICE`, `INDEX_PRICE2`, `INDEX_PRICE3`)
- **IDX**: Looks up the index price for the as-of date from `RTCTRL_INDEX_HDR` / `RTCTRL_INDEX_DTL`
- **SSN**: Matches the gas day to a seasonal profile date range and applies the season-specific rate
- **TR**: Invokes the tier rate resolution manager to determine the applicable tier

---

## Type of Charge (TOC) Hierarchy

### What is a TOC?

A **Type of Charge (TOC)** (`RTCTRL_TOC`) classifies the nature of a transportation charge. TOCs define what is being charged (e.g., reservation charge, commodity charge, fuel charge) and include properties like:

| Field | Description |
|-------|-------------|
| `TOC_CD` | Unique charge type code |
| `TSP_NO` | Transporter number |
| `CHARGE_BASIS_CD` | Charge basis (e.g., receipt-based or delivery-based) |
| `FUEL_PREF_CD` | Fuel preference code for fuel-related TOCs |
| `SCALE` | Decimal precision for rate amounts |

### TOC-TOS-Rule Cross Reference

The system uses a cross-reference structure to determine which TOCs apply to a given Type of Service (TOS):

1. **`RTCTRL_TOS_TOC_RULE_XREF`**: Links TOS codes to TOC codes with effective dates
2. **`RTCTRL_TOC_RULE`**: Defines inclusion/exclusion rules for each TOC
3. **`RTCTRL_TOC_OBJECT_XREF`**: Maps TOCs to specific processes (billing, fuel calc, etc.) with rate type categories

### TOC Attributes

TOC attributes (`RTCTRL_TOC_ATTR`) provide boolean flags on a TOC (e.g., "GTH" for gathering attribute). These are used in special rule validation to determine if a TOC applies to specific location configurations.

---

## TOC Rules and Validation

### Include/Exclude Logic

Each TOC can have multiple rules (`RTCTRL_TOC_RULE`) with an `INCLUDE_TYPE_CD` of:
- **`I` (Include)**: The TOC applies only when this rule matches
- **`E` (Exclude)**: The TOC does NOT apply when this rule matches

**Logic**: A TOC is excluded if any Exclude rule matches, or if Include rules exist but none match.

### Rule Criteria

TOC rules can filter on any combination of:

| Criterion | Description |
|-----------|-------------|
| `ROUTE_CD` | Route code must match |
| `RATE_FORM_TYPE_CD` | Rate form type must match |
| `LOC_ATTR_CD_1` / `LOC_ATTR_CD_2` | Receipt/Delivery location attributes |
| `IS_LOC_ATTR_TRUE_1` / `IS_LOC_ATTR_TRUE_2` | Whether the location attribute should be true or false |
| `INV_ADJ_TYPE_CD` | Inventory adjustment type |
| `REC_CTR_TOS_CD` / `DEL_CTR_TOS_CD` | Receipt/Delivery contract TOS |
| `TOS_ATTR_CD` / `IS_TOS_ATTR_TRUE` | TOS attribute matching (against contract or TOS default) |
| `QTY_SIGN` / `PPA_IND_CD` | Used only for CICO TOCs in billing |
| `PENALTY_TYPE_CD` | Penalty type (billing-only) |
| `TRANS_TYPE_CD` | Transaction type |
| `OPER_IMP_AREA_CD` | Operational imbalance area |
| `REC_REGION_CD` / `DEL_REGION_CD` | Receipt/Delivery region codes |
| `REC_PIPELINE_SYS_CD` / `DEL_PIPELINE_SYS_CD` | Receipt/Delivery pipeline system codes |

### Special Rules (Gathering)

The system applies a special rule for the "GTH" (gathering) TOC attribute. If a TOC does NOT have the GTH attribute set to true, it checks whether both receipt and delivery locations belong to the same gathering system location group. If they do, the TOC is excluded (same-gather-system exclusion).

---

## Rate Resolution Process

Rate resolution is the core algorithm that determines which rate detail applies for a given combination of inputs. The process follows a **ranking-based selection** strategy.

### Input Parameters

| Parameter | Description |
|-----------|-------------|
| `TspNo` | Transporter number |
| `TocCd` | Type of Charge code |
| `CtrNo` | Contract number |
| `TosCd` | Type of Service code |
| `AsOfDt` | Gas day / as-of date |
| `LocId1` / `LocId2` | Receipt / Delivery location IDs |
| `RouteCd` | Route code |
| `RateTypeCtgryCd` | Rate type category (e.g., BLLD) |

### Resolution Algorithm

The algorithm in `RateResolutionMgr.FindLowestRankingRateDetail()` works as follows:

1. **Retrieve Candidate Rates**: Get all rate details from cache matching the TOC, TSP, as-of date, and location/location group criteria
2. **Filter by Price Type** (optional): If supported price types are specified, discard non-matching rates
3. **Calculate Three-Level Rank** for each candidate:
   - **Rate Type Rank**: Based on the rate type's configured rank within the rate type category
   - **Header Rank**: Based on contract/TOS association (see below)
   - **Detail Rank**: Based on location specificity (see below)
4. **Select Lowest Rank**: The rate detail with the lowest combined rank wins
5. **Handle Ties**: If multiple rates have identical ranks, an exception is thrown ("Multiple rates found")
6. **Handle No Match**: Returns null if no rate matches

### Header Ranking (Contract/TOS Priority)

The header rank determines priority based on how the rate is associated:

| Rank | Association | Override? |
|------|------------|-----------|
| 1 | Contract-specific | Yes (override) |
| 2 | TOS-specific | Yes (override) |
| 3 | Contract-specific | No |
| 4 | TOS-specific | No |

**Important**: Header rank (contract/TOS specificity) has priority OVER rate type rank. A contract-specific rate always beats a TOS-specific rate, regardless of rate type ranking.

### Detail Ranking (Location Specificity)

The detail rank is calculated from location group properties:

```
Rank = (CtgryRank1 + CtgryRank2) * 1,000,000
     + (TypeRank1 + TypeRank2)   * 10,000
     + (Level1 + Level2)         * 100
     + RouteCodePenalty
```

Where:
- **CtgryRank**: Location group category rank (from `QCODE_LOC_GRP_CTGRY`)
- **TypeRank**: Location group type rank (from `QCODE_LOC_GRP_TYPE`)
- **Level**: System level number for the location group type
- **RouteCodePenalty**: 1 if the nomination has a route code but the rate detail does not; 0 otherwise

A **lower** rank means a more specific match. A rate tied to an individual location ranks lower (better) than one tied to a broad location group.

---

## Tiered Rates

### Overview

Tiered rates allow the rate to vary based on the volume (quantity) being transported. The tier configuration determines which rate applies based on where the input quantity falls within defined ranges.

### Tier Methods

| Method | Code | Description |
|--------|------|-------------|
| Block | `B` | The entire quantity is priced at the tier rate where the basis quantity falls |
| Step | `S` | Quantity is split across tiers (NOT currently supported in web) |

### Tier Resolution Process

1. Get the tier header (`RTCTRL_TIER`) and tier details (`RTCTRL_TIER_DTL`) from cache
2. Determine the **Tier Basis Quantity** based on the tier's basis configuration
3. For Block method (`B`):
   - Find the tier detail where `TierStart <= BasisQty <= TierEnd`
   - Apply the tier's fixed price to the entire input quantity
   - If the basis quantity cannot be retrieved, use the last tier as fallback
4. The tier price type currently supports only `FIX`; `FRM` and `IDX` are not supported for tier pricing

### Tier Basis

The tier basis determines what quantity drives tier selection:

| Basis Code | Description |
|------------|-------------|
| `DEL` | Allocated deliveries |
| `REC` | Allocated receipts |
| `DELK` | Allocated deliveries (contract level) |
| `RECK` | Allocated receipts (contract level) |
| `COREC` / `CODEL` | CO-based receipt/delivery |
| `CO2R` / `CO2D` | CO2-based receipt/delivery |
| `N2R` / `N2D` | N2-based receipt/delivery |

### Tier Types

| Type | Code | Description |
|------|------|-------------|
| Discrete | `D` | Tier ranges are absolute quantity values |
| Percent | `P` | Tier ranges are percentages (not fully supported) |

---

## Seasonal Rate Profiles

Seasonal rate profiles (`RTCTRL_SEASONAL_PROF_HDR` / `RTCTRL_SEASONAL_PROF_DTL`) allow rates to vary by time of year.

### How Seasonal Rates Work

1. A rate detail with price type `SSN` references a seasonal profile via `ID_SEASONAL_PROF`
2. Each profile contains detail records with `BEGIN_MONTH_DAY` and `END_MONTH_DAY` (format: MMDD)
3. During resolution, the gas day is matched to the applicable season
4. Three matching cases handle wrap-around seasons (e.g., Nov-Mar spanning year boundary):
   - Normal: `0101 --- Beg --- GasDay --- End --- 1231`
   - Year-end wrap: `0101 --- End --- Beg --- GasDay --- 1231`
   - Year-start wrap: `0101 --- GasDay --- End --- Beg --- 1231`
5. Each seasonal detail has its own price type (`FIX`, `FRM`, `IDX`) and rate values

---

## Fuel Preference and Fuel Calculation

### Fuel Preference

Fuel preference determines HOW fuel is collected for a nomination. It is resolved from the contract configuration.

| Code | Name | Description |
|------|------|-------------|
| `FIK` | Fuel In-Kind | Fuel is retained as a quantity percentage |
| `TIK` | Transport In-Kind | Transport fuel retained in-kind |
| `CFF` | Cash For Fuel | Fuel is paid in cash (no fuel TOCs apply) |

### Fuel Preference Resolution Order

1. Check `NNCTRL_CTR_PREF` for a contract-specific fuel preference
2. If not found, use the contract's default `FUEL_PREF_CD`

### Fuel Calculation Process

1. Resolve fuel preference for the contract
2. If `CFF`, return zero (no in-kind fuel)
3. Find all fuel-related TOCs that apply using `TOCResolutionMgr.FindFuelTypeOfChargesThatApply()`
4. Validate all matched TOCs have the same charge basis (cannot mix receipt and delivery fuel)
5. For each applicable fuel TOC, resolve the fuel rate using `RateResolutionMgr.GetFuelPercent()`
6. Sum all fuel percentages across applicable TOCs
7. Return the total fuel percentage and charge basis code

---

## Rate-to-Contract Relationship

Rates can be associated with specific contracts through `RTCTRL_RT_CTR` (Rate Contract association):

- A rate header can be linked to one or more contracts
- Contract-specific rates have higher priority during resolution (header rank 1 or 3)
- Rate contract associations are effective-dated
- When saving a discount rate with a contract association, the system validates against tariff max/min rates

---

## Rate-to-TOS Relationship

Rates can also be associated with Types of Service through `RTCTRL_RT_TOS` (Rate TOS association):

- A rate header can be linked to one or more TOS codes
- TOS-specific rates have lower priority than contract-specific rates (header rank 2 or 4)
- TOS associations are effective-dated

---

## Discount Rate Validation

When a rate with `RATE_TYPE_CD = 'DIS'` (Discount) is saved, the system runs the `RTVALDDSRT` batch process to validate:

1. The discount rate does not exceed the **maximum tariff** rate for the same TOC/location/date
2. The discount rate does not fall below the **minimum tariff** rate
3. If validation fails, error messages are added to the rate complete object:
   - "The discount rate...is invalid because it is above the tariff maximum rate"
   - "The discount rate...is invalid because it is below the tariff minimum rate"

---

## Charge Period and Daily Conversion

### Charge Periods

| Code | Name | Description |
|------|------|-------------|
| `DAY` | Daily | Rate is expressed per day |
| `MTH` | Monthly | Rate is expressed per month |

### Monthly-to-Daily Conversion

When a rate has `CHARGE_PER_CD = 'MTH'`, the system converts it to a daily rate using:

- **Average Method** (`RT_CONV_BASIS_CD = 'AVG'`): `DailyRate = MonthlyRate / 30.4167`
- **Calendar Method** (default): `DailyRate = MonthlyRate / DaysInMonth`

The conversion basis is configured on the contract (`KCTRL_CTR_HDR.RT_CONV_BASIS_CD`).

---

## Location Matrix and Location Groups

### Location Matrix Display

The Rate Maintenance screen supports a **matrix display** mode where rate details are displayed as a receipt-location vs. delivery-location grid. This is controlled by:
- `IS_MATRIX_DISPLAY` flag on the rate header
- Receipt and delivery location group type configurations

### Location Groups in Rate Details

Rate details can reference locations directly (`ID_LOC_1`, `ID_LOC_2`) or via location groups (`ID_LOC_GRP_1`, `ID_LOC_GRP_2`). During resolution, the system:
1. Gets all location groups that a specific location belongs to
2. Matches rate details against both direct location IDs and location group memberships
3. Ranks more specific matches (individual location) higher than broad matches (location group)

---

## Key Business Rules

1. **Single Best Rate**: The resolution algorithm must find exactly one best-ranked rate. Multiple rates with identical rank produce an error.
2. **No Rate Found**: If no rate matches, the system returns null (no error thrown for simple lookups, but fuel calculation will clear output parameters).
3. **Mixed Charge Basis**: A nomination cannot have both receipt-based and delivery-based fuel charges on the same path. This throws an exception.
4. **Effective Date Integrity**: Rate headers and details must have valid, non-overlapping effective date ranges.
5. **Contract Specificity Priority**: Contract-specific rates always take precedence over TOS-specific rates in resolution.
6. **Override Rates**: Rates marked as override (`IS_OVERRIDE = true`) rank higher than non-override rates at the same association level.
7. **Route Code Matching**: If a rate detail has a route code, it must match the nomination's route code. If the nomination has a route code but the rate does not, the rate receives a ranking penalty.
8. **PPA Cutoff Date**: Rate queries are not allowed before the PPA (Prior Period Adjustment) cutoff date configured in TSP preferences.
9. **Discount Validation**: Discount rates are validated against max/min tariff rates via the `RTVALDDSRT` batch process on save.
10. **Rate Detail in Rate Stat**: Before modifying rate details, the system checks if they are referenced in `CATRAN_RATE_STAT` (billing transaction rate statistics).

---

## Glossary

| Term | Definition |
|------|-----------|
| **TOC** | Type of Charge - classifies the nature of a transportation charge |
| **TOS** | Type of Service - the service category (e.g., firm, interruptible) |
| **TSP** | Transporter - the pipeline company |
| **Rate Schedule** | Named collection of rate configurations (e.g., FT-1) |
| **Rate Header** | Core rate definition with type, price type, charge period, and effective dates |
| **Rate Detail** | Location-specific rate values (fixed rate, percentage, tier, etc.) |
| **Rate Resolution** | Algorithm to find the single best applicable rate for given inputs |
| **Fuel Preference** | How fuel is collected: in-kind (FIK/TIK) or cash (CFF) |
| **Charge Basis** | Whether a charge is based on receipt or delivery quantities |
| **Charge Period** | Whether the rate is per day (DAY) or per month (MTH) |
| **Tier** | Volume-based pricing where rate varies by quantity range |
| **Seasonal Profile** | Time-of-year-based pricing with seasonal date ranges |
| **Override Rate** | A rate flagged to take priority in resolution ranking |
| **PPA** | Prior Period Adjustment - retroactive billing corrections |
| **Discount Rate** | A negotiated rate below the maximum tariff |
| **Location Group** | A named collection of locations used for rate matching |
| **Rate Type Rank** | Configured ranking of a rate type within a rate type category |
| **Header Rank** | Priority based on contract/TOS association (1-4 scale) |
| **Detail Rank** | Specificity rank based on location/location group properties |

---

## Related Documentation

- [Architecture Documentation](./architecture.md) - Technical implementation details
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and diagnostic queries

---

*Last updated: 2026-03-03*

*Document version: 1.0*
