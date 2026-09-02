---
title: Rate Management (RATE) - Troubleshooting Guide
category: troubleshooting
feature: Rate Management (RATE)
related_repos: Web, Batch
keywords: RATE, troubleshooting, issues, errors, diagnostic queries, solutions, debugging, rate resolution, fuel calculation, TOC, tier, multiple rates, no rate found, discount validation, rate maintenance, charge basis, seasonal, formula, index
last_updated: 2026-03-03
---

# Rate Management (RATE) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Rate Management issues in QPTM. It includes common problems, diagnostic queries, error messages, and solutions.

For business concepts, see [Domain Documentation](./domain.md).
For technical details, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Diagnostic Queries](#diagnostic-queries)
3. [Error Messages](#error-messages)
4. [Investigation Workflow](#investigation-workflow)
5. [Performance Issues](#performance-issues)
6. [Historical Work Items](#historical-work-items)

---

## Common Issues

### Issue 1: Multiple Rates Found During Resolution

**Symptoms:**
- Exception thrown: "Multiple rates (N) found for TOC_CD: XXX nomination on contract YYY from LOC1 to LOC2"
- Fuel calculation fails for a nomination
- Billing produces errors during rate resolution

**Root Causes:**
1. Multiple rate details have identical ranking (header rank, rate type rank, and detail rank are all equal)
2. Overlapping location group memberships causing a location to match multiple rate details
3. Duplicate rate detail records with same effective dates and locations
4. Rate headers with same TOC but different contract/TOS associations that resolve to the same rank

**Investigation Steps:**
```sql
-- Find all rate details for the given TOC, TSP, and date range
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.TOC_CD, rh.RATE_TYPE_CD, rh.PRICE_TYPE_CD,
       rh.IS_OVERRIDE, rh.EFF_DT_FROM, rh.EFF_DT_TO,
       rd.RATE_DTL_ID, rd.ID_LOC_1, rd.ID_LOC_2, rd.ID_LOC_GRP_1, rd.ID_LOC_GRP_2,
       rd.FIXED_RATE, rd.QTY_RETAINED_PCT, rd.ROUTE_CD
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID
     AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
WHERE rh.TSP_NO = @TspNo
  AND rh.TOC_CD = @TocCd
  AND rh.EFF_DT_FROM <= @AsOfDate
  AND rh.EFF_DT_TO >= @AsOfDate
  AND rd.EFF_DT_FROM <= @AsOfDate
  AND rd.EFF_DT_TO >= @AsOfDate
ORDER BY rh.RATE_HDR_ID, rd.RATE_DTL_ID;

-- Check which location groups the receipt/delivery locations belong to
SELECT lgl.LOC_GRP_ID, lgl.LOC_ID, lg.LOC_GRP_NM, lg.LOC_GRP_TYPE_CD
FROM PACTRL_LOC_GRP_LOC lgl
JOIN PACTRL_LOC_GRP lg ON lgl.LOC_GRP_ID = lg.ID_LOC_GRP AND lgl.TSP_NO = lg.TSP_NO
WHERE lgl.TSP_NO = @TspNo
  AND lgl.LOC_ID IN (@LocId1, @LocId2)
  AND lgl.EFF_DT_FROM <= @AsOfDate
  AND lgl.EFF_DT_TO >= @AsOfDate
  AND lgl.INCLUDE_TYPE_CD = 'I';
```

**Resolution:**
- Review location group memberships to ensure no unintended overlaps
- Adjust rate detail location specificity (use specific locations instead of groups)
- Check if override flag should be set on one of the rate headers
- Remove duplicate rate details
- Verify contract-specific vs TOS-specific association is correctly set

**Code Location:** `RateResolutionMgr.FindLowestRankingRateDetail()` in `Quorum.QPTM.ServiceCore.Rate/RateResolutionMgr.cs` (lines ~598-809)

---

### Issue 2: No Rate Found / Fuel Percentage is Zero

**Symptoms:**
- Fuel percentage returns 0 on nominations
- `GetFuelPercent()` returns 0 with `bRateFound = false`
- Nomination fuel fields are empty or null after fuel calculation
- Trace output: "FuelDataMgr: **FAILED** to find a single best rate in 0 rates"

**Root Causes:**
1. No rate detail exists matching the TOC, date, and locations
2. TOC rules exclude the TOC for the given nomination context
3. Fuel preference is "CFF" (Cash For Fuel), so no fuel TOCs apply
4. Rate detail effective dates do not cover the gas day
5. No TOS-TOC rule cross reference exists linking the TOS to the fuel TOC
6. Contract not found for the specified date range
7. Rate type is not in the BLLD (Billed) rate type category

**Investigation Steps:**
```sql
-- 1. Check if any rate headers exist for the TOC
SELECT * FROM RTCTRL_RT_HDR
WHERE TSP_NO = @TspNo AND TOC_CD = @TocCd
  AND EFF_DT_FROM <= @GasDay AND EFF_DT_TO >= @GasDay;

-- 2. Check the contract fuel preference
SELECT kh.CTR_NO, kh.FUEL_PREF_CD, cp.FUEL_PREF_CD AS CTR_PREF_FUEL
FROM KCTRL_CTR_HDR kh
LEFT JOIN NNCTRL_CTR_PREF cp ON kh.CTR_NO = cp.CTR_NO AND kh.TSP_NO = cp.TSP_NO
WHERE kh.TSP_NO = @TspNo AND kh.CTR_NO = @CtrNo
  AND kh.EFF_START_DT <= @GasDay AND kh.EFF_END_DT >= @GasDay;

-- 3. Check TOS-TOC rule cross reference
SELECT * FROM RTCTRL_TOS_TOC_RULE_XREF
WHERE TSP_NO = @TspNo AND TOS_CD = @TosCd
  AND EFF_DT_FROM <= @GasDay AND EFF_DT_TO >= @GasDay;

-- 4. Check if rate type is in BLLD category
SELECT rt.RATE_TYPE_CD, rt.RATE_TYPE_RANK, rtc.RATE_TYPE_CTGRY_CD
FROM QCODE_RATE_TYPE rt
JOIN QCODE_RATE_TYPE_CTGRY rtc ON rt.RATE_TYPE_CD = rtc.RATE_TYPE_CD
WHERE rtc.RATE_TYPE_CTGRY_CD = 'BLLD';
```

**Resolution:**
- Ensure rate details exist covering the gas day and matching locations
- Verify TOS-TOC rule cross reference is configured
- Check that the fuel preference is not CFF
- Ensure the rate type belongs to the correct rate type category
- Add the missing rate detail or extend effective dates

**Code Location:** `RateResolutionMgr.GetFuelPercent()` in `RateResolutionMgr.cs` (lines ~31-55), `QPTMRateService.CalculateFuel()` in `QPTMRateService.cs` (lines ~219-269)

---

### Issue 3: TOC Not Resolving for Nomination

**Symptoms:**
- `FindTypeOfChargesThatApply()` returns empty list
- `FindFuelTypeOfChargesThatApply()` returns empty list
- Fuel calculation shows `bTocFound = false`
- Expected charges are missing from billing

**Root Causes:**
1. TOC include rules do not match the nomination's properties
2. TOC exclude rule matches and excludes the TOC
3. TOS attribute mismatch between TOC rule and contract attributes
4. Location attribute mismatch (receipt or delivery)
5. Missing TOC-process cross reference for the target process
6. Gathering special rule excludes the TOC (same gathering system group)
7. Route code mismatch in TOC rules
8. Trans type code mismatch

**Investigation Steps:**
```sql
-- Check TOC rules for the specific TOC
SELECT tr.TOC_CD, tr.INCLUDE_TYPE_CD, tr.ROUTE_CD, tr.RATE_FORM_TYPE_CD,
       tr.LOC_ATTR_CD_1, tr.IS_LOC_ATTR_TRUE_1, tr.LOC_ATTR_CD_2, tr.IS_LOC_ATTR_TRUE_2,
       tr.INV_ADJ_TYPE_CD, tr.REC_CTR_TOS_CD, tr.DEL_CTR_TOS_CD,
       tr.TOS_ATTR_CD, tr.IS_TOS_ATTR_TRUE, tr.TRANS_TYPE_CD,
       tr.REC_REGION_CD, tr.DEL_REGION_CD, tr.REC_PIPELINE_SYS_CD, tr.DEL_PIPELINE_SYS_CD
FROM RTCTRL_TOC_RULE tr
WHERE tr.TOC_CD = @TocCd AND tr.TSP_NO = @TspNo;

-- Check TOC-process cross reference
SELECT * FROM RTCTRL_TOC_OBJECT_XREF
WHERE TSP_NO = @TspNo AND TOC_CD = @TocCd
  AND EFF_DT_FROM <= @GasDay AND EFF_DT_TO >= @GasDay;

-- Check location attributes for receipt and delivery locations
SELECT la.ID_LOC, la.LOC_ATTR_CD, la.IS_ATTR_TRUE
FROM PACTRL_LOC_ATTR la
WHERE la.TSP_NO = @TspNo
  AND la.ID_LOC IN (@RecLocId, @DelLocId);

-- Check gathering system location groups
SELECT slgl.ID_LOC, slgl.LOC_GRP_ID, slgl.LOC_GRP_TYPE_CD
FROM PACTRL_SYS_LOC_GRP_LOC slgl
WHERE slgl.TSP_NO = @TspNo
  AND slgl.LOC_GRP_TYPE_CD = 'GTH'
  AND slgl.ID_LOC IN (@RecLocId, @DelLocId)
  AND slgl.EFF_DT_FROM <= @GasDay AND slgl.EFF_DT_TO >= @GasDay;
```

**Resolution:**
- Review and correct TOC rules (include/exclude) for the target TOC
- Ensure TOS-TOC rule cross reference exists for the TOS and date
- Add or correct location attributes
- Verify TOS attribute configuration on the contract
- Check gathering system group configuration

**Code Location:** `TOCResolutionMgr.AreTOCRulesValid()` in `TOCResolutionMgr.cs` (lines ~163-415), `TOCResolutionMgr.AreTOCSpecialRulesValid()` (lines ~421-440)

---

### Issue 4: Incorrect Rate Amount Resolved

**Symptoms:**
- Billing charges use wrong rate
- Rate Query shows unexpected rate for a given date/location
- Fuel percentage is wrong value

**Root Causes:**
1. Wrong rate detail wins the ranking competition due to location group ranking misconfiguration
2. Override flag incorrectly set on a rate header
3. Monthly rate not correctly converted to daily
4. Formula evaluation returns incorrect value (wrong index prices)
5. Seasonal profile date ranges misconfigured (wrong season matched)
6. Rate effective dates allow an old rate to apply instead of the expected new one

**Investigation Steps:**
```sql
-- Check all candidate rate details and their ranking factors
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.RATE_TYPE_CD, rh.IS_OVERRIDE,
       rd.RATE_DTL_ID, rd.ID_LOC_1, rd.ID_LOC_GRP_1, rd.ID_LOC_2, rd.ID_LOC_GRP_2,
       rd.FIXED_RATE, rd.QTY_RETAINED_PCT, rd.ROUTE_CD,
       rh.CHARGE_PER_CD, rh.PRICE_TYPE_CD,
       rc.CTR_NO, rtos.TOS_CD
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
LEFT JOIN RTCTRL_RT_CTR rc ON rh.RATE_HDR_ID = rc.RATE_HDR_ID AND rh.TSP_NO = rc.TSP_NO
LEFT JOIN RTCTRL_RT_TOS rtos ON rh.RATE_HDR_ID = rtos.RATE_HDR_ID AND rh.TSP_NO = rtos.TSP_NO
WHERE rh.TSP_NO = @TspNo AND rh.TOC_CD = @TocCd
  AND rh.EFF_DT_FROM <= @AsOfDate AND rh.EFF_DT_TO >= @AsOfDate
  AND rd.EFF_DT_FROM <= @AsOfDate AND rd.EFF_DT_TO >= @AsOfDate
ORDER BY rh.IS_OVERRIDE DESC, rc.CTR_NO, rtos.TOS_CD;

-- Check location group ranking
SELECT lg.ID_LOC_GRP, lg.LOC_GRP_TYPE_CD,
       lgt.LOC_GRP_TYPE_RANK, lgt.LOC_GRP_CTGRY_CD, lgt.SYS_LEVEL_NO,
       lgc.LOC_GRP_CTGRY_RANK
FROM PACTRL_LOC_GRP lg
JOIN QCODE_LOC_GRP_TYPE lgt ON lg.LOC_GRP_TYPE_CD = lgt.LOC_GRP_TYPE_CD
JOIN QCODE_LOC_GRP_CTGRY lgc ON lgt.LOC_GRP_CTGRY_CD = lgc.LOC_GRP_CTGRY_CD
WHERE lg.TSP_NO = @TspNo
  AND lg.ID_LOC_GRP IN (@LocGrpId1, @LocGrpId2);
```

**Resolution:**
- Review the ranking of all candidate rate details to understand why the wrong one wins
- Adjust location group types/categories to reflect correct specificity ranking
- Verify override flags on rate headers
- Check formula definitions and index prices for formula-based rates
- Verify seasonal profile date ranges for seasonal rates
- Correct rate effective dates

**Code Location:** `RateResolutionMgr.CalculateHeaderRank()` (lines ~823-856), `RateResolutionMgr.CalculateDetailRank()` (lines ~866-947)

---

### Issue 5: Mixed Charge Basis Error

**Symptoms:**
- Exception: "Cannot have receipt fuel charge basis and delivery fuel charge basis on contract XXX from LOC1 to LOC2"
- Fuel calculation fails for a specific path

**Root Causes:**
1. Multiple fuel TOCs resolve for the same nomination path, but they have different charge basis codes (e.g., one is receipt-based and another is delivery-based)
2. TOC rules not properly constraining which fuel TOCs apply to a given path direction

**Investigation Steps:**
```sql
-- Check charge basis for all fuel-related TOCs that could apply
SELECT toc.TOC_CD, toc.CHARGE_BASIS_CD, toc.FUEL_PREF_CD
FROM RTCTRL_TOC toc
JOIN RTCTRL_TOS_TOC_RULE_XREF xref ON toc.TOC_CD = xref.TOC_CD AND toc.TSP_NO = xref.TSP_NO
WHERE toc.TSP_NO = @TspNo
  AND xref.TOS_CD = @TosCd
  AND xref.EFF_DT_FROM <= @GasDay AND xref.EFF_DT_TO >= @GasDay
  AND toc.FUEL_PREF_CD = @FuelPrefCd;
```

**Resolution:**
- Review fuel TOC configurations to ensure consistent charge basis
- Add TOC rules to exclude one direction's fuel TOC from the other
- Ensure only one charge basis type applies per nomination path

**Code Location:** `QPTMRateService.CalculateFuel()` in `QPTMRateService.cs` (lines ~219-269)

---

### Issue 6: Tier Rate Not Resolving

**Symptoms:**
- Rate resolution returns `bRateFound = false` for a tier (TR) price type
- Trace output: "tier method is not supported" or "tier id is not supported"
- Billing shows zero amount for tiered rate

**Root Causes:**
1. Tier ID on rate detail does not match any `RTCTRL_TIER` record
2. No tier detail records exist for the tier ID
3. Tier method is "S" (Step), which is not supported
4. Tier basis quantity cannot be retrieved
5. Tier type is "P" (Percent), which is not fully supported
6. Input quantity falls outside all tier ranges and basis was successfully retrieved
7. Tier charge period is "MTH" (not supported, only "DAY" is supported)

**Investigation Steps:**
```sql
-- Check tier header
SELECT * FROM RTCTRL_TIER
WHERE RATE_TIER_ID = @TierId AND TSP_NO = @TspNo;

-- Check tier details (ranges)
SELECT * FROM RTCTRL_TIER_DTL
WHERE RATE_TIER_ID = @TierId AND TSP_NO = @TspNo
ORDER BY TIER_START;

-- Check the rate detail's tier reference
SELECT rd.RATE_DTL_ID, rd.ID_RATE_TIER, rh.PRICE_TYPE_CD
FROM RTCTRL_RT_DTL rd
JOIN RTCTRL_RT_HDR rh ON rd.RATE_HDR_ID = rh.RATE_HDR_ID AND rd.TSP_NO = rh.TSP_NO AND rd.EFF_DT_FROM = rh.EFF_DT_FROM
WHERE rd.TSP_NO = @TspNo AND rd.ID_RATE_TIER = @TierId
  AND rd.EFF_DT_FROM <= @AsOfDate AND rd.EFF_DT_TO >= @AsOfDate;
```

**Resolution:**
- Ensure tier header and details exist and are properly configured
- Verify tier method is "B" (Block)
- Verify tier charge period is "DAY"
- Check that tier ranges cover the expected quantity values
- Ensure tier type is "D" (Discrete)

**Code Location:** `TierRateResolutionMgr.GetTierRateResult()` in `TierRateResolutionMgr.cs` (lines ~28-113)

---

### Issue 7: Discount Rate Validation Failure on Save

**Symptoms:**
- Error on save: "The discount rate...is invalid because it is above the tariff maximum rate"
- Error on save: "The discount rate...is invalid because it is below the tariff minimum rate"
- Rate cannot be saved despite valid-looking data

**Root Causes:**
1. Discount rate exceeds the maximum tariff rate for the same TOC/location
2. Discount rate is below the minimum tariff rate
3. Tariff rate does not exist for comparison (may need to be set up first)
4. Tariff rate has different effective dates not covering the discount period

**Investigation Steps:**
```sql
-- Check max tariff rates for the same TOC and locations
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.RATE_TYPE_CD, rd.FIXED_RATE, rd.ID_LOC_1, rd.ID_LOC_2
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
WHERE rh.TSP_NO = @TspNo AND rh.TOC_CD = @TocCd AND rh.RATE_TYPE_CD = 'TMX'
  AND rh.EFF_DT_FROM <= @AsOfDate AND rh.EFF_DT_TO >= @AsOfDate;

-- Check min tariff rates
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.RATE_TYPE_CD, rd.FIXED_RATE, rd.ID_LOC_1, rd.ID_LOC_2
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
WHERE rh.TSP_NO = @TspNo AND rh.TOC_CD = @TocCd AND rh.RATE_TYPE_CD = 'TMN'
  AND rh.EFF_DT_FROM <= @AsOfDate AND rh.EFF_DT_TO >= @AsOfDate;

-- Check discount validation results
SELECT * FROM BLTRAN_INVALID_DISC bid
JOIN BLTRAN_INVALID_DISC_INPUT bidi ON bid.SET_ID = bidi.SET_ID AND bid.INVALID_DISC_INPUT_ID = bidi.INVALID_DISC_INPUT_ID
WHERE bidi.TSP_NO = @TspNo AND bidi.RATE_HDR_ID = @RateHdrId
ORDER BY bidi.SET_ID DESC;
```

**Resolution:**
- Adjust the discount rate to fall within tariff max/min boundaries
- Set up or update tariff max/min rates to cover the discount period
- Review the specific location detail being validated

**Code Location:** `QPTMServiceCore.InsertInvalidDiscInput()` and `QPTMServiceCore.ProcessRateCompletePostProcessRun()` in `QPTMServiceCore_RateMaintenance.cs` (lines ~889-1025)

---

### Issue 8: Rate Detail Exists in Rate Stat (Cannot Modify)

**Symptoms:**
- PPA reallocation dialog appears after saving
- Warning that rate details are referenced in billing transactions
- Cannot freely modify rate details that have been billed

**Root Causes:**
1. Rate detail records have been used in billing and exist in `CATRAN_RATE_STAT`
2. Modifying these rates may require PPA (Prior Period Adjustment) processing

**Investigation Steps:**
```sql
-- Check if rate details exist in rate stat
SELECT crs.TSP_NO, crs.RATE_HDR_ID, crs.RATE_DTL_ID, crs.GAS_DAY
FROM CATRAN_RATE_STAT crs
WHERE crs.TSP_NO = @TspNo
  AND crs.RATE_HDR_ID = @RateHdrId
  AND crs.GAS_DAY BETWEEN @EffDateFrom AND @EffDateTo;
```

**Resolution:**
- This is expected behavior for billed rates
- Use PPA processing to handle retroactive rate changes
- If the rate should not have been billed, investigate the billing process

**Code Location:** `QPTMServiceCore.CheckRateDetailExistsInRateStat()` in `QPTMServiceCore_RateMaintenance.cs` (lines ~346-368)

---

### Issue 9: Formula or Index Price Returns Null

**Symptoms:**
- Rate resolution returns null for a formula (FRM) or index (IDX) price type
- Billing charge shows zero or is skipped for formula/index rates

**Root Causes:**
1. No index header record exists for the specified index ID and date
2. No index detail record exists covering the as-of date
3. Formula definition not found or formula evaluation fails
4. All three index prices are null (index headers 1, 2, and 3)

**Investigation Steps:**
```sql
-- Check index header
SELECT * FROM RTCTRL_INDEX_HDR
WHERE TSP_NO = @TspNo AND INDEX_ID = @IndexId
  AND EFF_DT_FROM <= @AsOfDate AND EFF_DT_TO >= @AsOfDate;

-- Check index detail prices
SELECT * FROM RTCTRL_INDEX_DTL
WHERE TSP_NO = @TspNo AND INDEX_ID = @IndexId
  AND INDEX_START_DT <= @AsOfDate AND INDEX_END_DT >= @AsOfDate;

-- Check rate detail index references
SELECT rd.RATE_DTL_ID, rd.ID_INDEX, rd.ID_INDEX2, rd.ID_INDEX3, rd.RATE_FORMULA_CD
FROM RTCTRL_RT_DTL rd
WHERE rd.TSP_NO = @TspNo AND rd.RATE_HDR_ID = @RateHdrId
  AND rd.EFF_DT_FROM <= @AsOfDate AND rd.EFF_DT_TO >= @AsOfDate;
```

**Resolution:**
- Ensure index headers and details exist and cover the relevant date range
- Add or update index detail price records
- Verify the formula code is valid and defined in the formula library
- Check that the rate detail references the correct index ID(s)

**Code Location:** `RateResolutionMgr.GetFormulaPrice()` (lines ~170-226), `RateResolutionMgr.GetIndexPrice()` (lines ~306-326)

---

### Issue 10: Seasonal Profile Date Mismatch

**Symptoms:**
- Seasonal rate resolves to wrong price for a given gas day
- Rate returns null when it should have a seasonal rate
- Different rate than expected during season transition periods

**Root Causes:**
1. Seasonal profile detail records have gaps between `BEGIN_MONTH_DAY` and `END_MONTH_DAY`
2. Date wrap-around not properly configured for cross-year seasons (e.g., November to March)
3. No seasonal detail record matches the gas day's MMDD
4. Seasonal profile ID on rate detail is incorrect

**Investigation Steps:**
```sql
-- Check seasonal profile configuration
SELECT sph.SEASONAL_PROF_ID, spd.BEGIN_MONTH_DAY, spd.END_MONTH_DAY,
       spd.PRICE_TYPE_CD, spd.FIXED_PRICE, spd.INDEX_ID, spd.FORMULA_CD
FROM RTCTRL_SEASONAL_PROF_HDR sph
JOIN RTCTRL_SEASONAL_PROF_DTL spd ON sph.SEASONAL_PROF_ID = spd.SEASONAL_PROF_ID AND sph.TSP_NO = spd.TSP_NO
WHERE sph.TSP_NO = @TspNo AND sph.SEASONAL_PROF_ID = @SeasonalProfId
ORDER BY spd.BEGIN_MONTH_DAY;

-- Check rate detail seasonal reference
SELECT rd.RATE_DTL_ID, rd.ID_SEASONAL_PROF, rh.PRICE_TYPE_CD
FROM RTCTRL_RT_DTL rd
JOIN RTCTRL_RT_HDR rh ON rd.RATE_HDR_ID = rh.RATE_HDR_ID AND rd.TSP_NO = rh.TSP_NO AND rd.EFF_DT_FROM = rh.EFF_DT_FROM
WHERE rd.TSP_NO = @TspNo AND rh.PRICE_TYPE_CD = 'SSN'
  AND rd.EFF_DT_FROM <= @AsOfDate AND rd.EFF_DT_TO >= @AsOfDate;
```

**Resolution:**
- Ensure seasonal profile details cover all 365 days without gaps
- Properly configure cross-year seasons (e.g., `BEGIN_MONTH_DAY = '1101'`, `END_MONTH_DAY = '0331'`)
- Verify the rate detail references the correct seasonal profile ID

**Code Location:** `RateResolutionMgr.GetSeasonalPrice()` in `RateResolutionMgr.cs` (lines ~228-304)

---

### Issue 11: Contract Not Found During Rate Resolution

**Symptoms:**
- Exception: "Unable to find the contract: XXX"
- Exception: "Contract XXX does not exist on this date"
- Fuel calculation fails with contract-related error

**Root Causes:**
1. Contract does not exist for the specified TSP and date
2. Contract effective dates do not cover the gas day
3. Contract cache is stale and does not reflect recent changes

**Investigation Steps:**
```sql
-- Check contract existence and effective dates
SELECT kh.CTR_NO, kh.TOS_CD, kh.EFF_START_DT, kh.EFF_END_DT,
       kh.CTR_STAT_CD, kh.FUEL_PREF_CD, kh.RT_CONV_BASIS_CD
FROM KCTRL_CTR_HDR kh
WHERE kh.TSP_NO = @TspNo AND kh.CTR_NO = @CtrNo
ORDER BY kh.EFF_START_DT DESC;
```

**Resolution:**
- Verify the contract exists and has the correct effective dates
- Extend contract dates if the gas day falls outside the current range
- Refresh the application cache if recent contract changes are not reflected

**Code Location:** `RateResolutionMgr.ResolveFuelPreference()` (lines ~58-103), `RateResolutionMgr.GetPossibleRatesForContract()` (lines ~493-586)

---

### Issue 12: Rate Query Returns No Results Before PPA Cutoff

**Symptoms:**
- Exception: "As of date range cannot be before PPA Cutoff Date"
- Rate Query screen returns error for historical dates

**Root Causes:**
1. The requested date range falls before the TSP's configured PPA cutoff date
2. This is a designed safeguard to prevent rate queries on finalized periods

**Investigation Steps:**
```sql
-- Check PPA cutoff date
SELECT TSP_NO, BILLING_PPA_CUTOFF_DT
FROM TSCTRL_TSP_PREF
WHERE TSP_NO = @TspNo;
```

**Resolution:**
- Use dates after the PPA cutoff for rate queries
- If the cutoff date needs adjustment, update via TSP Preferences (requires authorization)

**Code Location:** `QPTMRateService.ResolveRates()` in `QPTMRateService.cs` (lines ~370-461)

---

## Diagnostic Queries

### Query 1: Complete Rate Configuration for a TOC

```sql
-- View complete rate setup for a TOC including header, details, and associations
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.TOC_CD, rh.RATE_TYPE_CD, rh.PRICE_TYPE_CD,
       rh.CHARGE_PER_CD, rh.UOM_TYPE_CD, rh.IS_OVERRIDE,
       rh.EFF_DT_FROM AS HDR_EFF_FROM, rh.EFF_DT_TO AS HDR_EFF_TO,
       rd.RATE_DTL_ID, rd.ID_LOC_1, rd.ID_LOC_2, rd.ID_LOC_GRP_1, rd.ID_LOC_GRP_2,
       rd.FIXED_RATE, rd.QTY_RETAINED_PCT, rd.ROUTE_CD,
       rd.ID_INDEX, rd.RATE_FORMULA_CD, rd.ID_RATE_TIER, rd.ID_SEASONAL_PROF,
       rc.CTR_NO, rtos.TOS_CD
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
LEFT JOIN RTCTRL_RT_CTR rc ON rh.RATE_HDR_ID = rc.RATE_HDR_ID AND rh.TSP_NO = rc.TSP_NO AND rh.EFF_DT_FROM = rc.EFF_DT_FROM
LEFT JOIN RTCTRL_RT_TOS rtos ON rh.RATE_HDR_ID = rtos.RATE_HDR_ID AND rh.TSP_NO = rtos.TSP_NO AND rh.EFF_DT_FROM = rtos.EFF_DT_FROM
WHERE rh.TSP_NO = @TspNo AND rh.TOC_CD = @TocCd
ORDER BY rh.RATE_HDR_ID, rh.EFF_DT_FROM, rd.RATE_DTL_ID;
```

### Query 2: TOC Rules and Attribute Configuration

```sql
-- View all TOC rules and attributes for a specific TOC
SELECT toc.TOC_CD, toc.CHARGE_BASIS_CD, toc.FUEL_PREF_CD, toc.SCALE,
       tr.INCLUDE_TYPE_CD, tr.ROUTE_CD, tr.LOC_ATTR_CD_1, tr.IS_LOC_ATTR_TRUE_1,
       tr.LOC_ATTR_CD_2, tr.IS_LOC_ATTR_TRUE_2, tr.TOS_ATTR_CD, tr.IS_TOS_ATTR_TRUE,
       tr.TRANS_TYPE_CD, tr.REC_REGION_CD, tr.DEL_REGION_CD,
       ta.TOC_ATTR_CD, ta.IS_ATTR_TRUE
FROM RTCTRL_TOC toc
LEFT JOIN RTCTRL_TOC_RULE tr ON toc.TOC_CD = tr.TOC_CD AND toc.TSP_NO = tr.TSP_NO
LEFT JOIN RTCTRL_TOC_ATTR ta ON toc.TOC_CD = ta.TOC_CD AND toc.TSP_NO = ta.TSP_NO
WHERE toc.TSP_NO = @TspNo AND toc.TOC_CD = @TocCd;
```

### Query 3: Rate Resolution Candidates for a Contract Path

```sql
-- Find all rates that could apply for a specific contract and path
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.TOC_CD, rh.RATE_TYPE_CD, rh.PRICE_TYPE_CD,
       rh.IS_OVERRIDE, rd.RATE_DTL_ID,
       rd.ID_LOC_1, rd.ID_LOC_2, rd.ID_LOC_GRP_1, rd.ID_LOC_GRP_2,
       rd.FIXED_RATE, rd.QTY_RETAINED_PCT,
       CASE WHEN rc.CTR_NO IS NOT NULL AND rh.IS_OVERRIDE = 1 THEN 1
            WHEN rtos.TOS_CD IS NOT NULL AND rh.IS_OVERRIDE = 1 THEN 2
            WHEN rc.CTR_NO IS NOT NULL THEN 3
            WHEN rtos.TOS_CD IS NOT NULL THEN 4
       END AS HEADER_RANK
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
LEFT JOIN RTCTRL_RT_CTR rc ON rh.RATE_HDR_ID = rc.RATE_HDR_ID AND rh.TSP_NO = rc.TSP_NO AND rc.CTR_NO = @CtrNo
LEFT JOIN RTCTRL_RT_TOS rtos ON rh.RATE_HDR_ID = rtos.RATE_HDR_ID AND rh.TSP_NO = rtos.TSP_NO AND rtos.TOS_CD = @TosCd
WHERE rh.TSP_NO = @TspNo AND rh.TOC_CD = @TocCd
  AND rh.EFF_DT_FROM <= @AsOfDate AND rh.EFF_DT_TO >= @AsOfDate
  AND rd.EFF_DT_FROM <= @AsOfDate AND rd.EFF_DT_TO >= @AsOfDate
  AND (rc.CTR_NO IS NOT NULL OR rtos.TOS_CD IS NOT NULL)
ORDER BY HEADER_RANK, rd.RATE_DTL_ID;
```

### Query 4: Tier Configuration Verification

```sql
-- View complete tier setup
SELECT t.RATE_TIER_ID, t.TIER_METH_CD, t.TIER_TYPE_CD,
       t.TIER_CHARGE_PER_CD, t.TIER_CHARGE_BASIS_CD,
       t.TIER_BASIS_PROD_MTH_OFFSET,
       td.TIER_DTL_ID, td.TIER_START, td.TIER_END,
       td.FIXED_PRICE, td.PRICE_TYPE_CD
FROM RTCTRL_TIER t
JOIN RTCTRL_TIER_DTL td ON t.RATE_TIER_ID = td.RATE_TIER_ID AND t.TSP_NO = td.TSP_NO
WHERE t.TSP_NO = @TspNo AND t.RATE_TIER_ID = @TierId
ORDER BY td.TIER_START;
```

### Query 5: Fuel Resolution Audit Trail

```sql
-- Trace fuel resolution by checking TOC xrefs, fuel TOCs, and rates
-- Step 1: Get the contract TOS
SELECT kh.CTR_NO, kh.TOS_CD, kh.FUEL_PREF_CD
FROM KCTRL_CTR_HDR kh
WHERE kh.TSP_NO = @TspNo AND kh.CTR_NO = @CtrNo
  AND kh.EFF_START_DT <= @GasDay AND kh.EFF_END_DT >= @GasDay;

-- Step 2: Get TOS-TOC mappings
SELECT xref.TOS_CD, xref.TOC_CD
FROM RTCTRL_TOS_TOC_RULE_XREF xref
WHERE xref.TSP_NO = @TspNo AND xref.TOS_CD = @TosCd
  AND xref.EFF_DT_FROM <= @GasDay AND xref.EFF_DT_TO >= @GasDay;

-- Step 3: Get fuel TOCs matching fuel preference
SELECT toc.TOC_CD, toc.CHARGE_BASIS_CD, toc.FUEL_PREF_CD
FROM RTCTRL_TOC toc
WHERE toc.TSP_NO = @TspNo AND toc.FUEL_PREF_CD = @FuelPrefCd
  AND toc.TOC_CD IN (/* from step 2 */);

-- Step 4: For each fuel TOC, check rate details with BLLD category
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.RATE_TYPE_CD,
       rd.RATE_DTL_ID, rd.QTY_RETAINED_PCT, rd.ID_LOC_1, rd.ID_LOC_2
FROM RTCTRL_RT_HDR rh
JOIN RTCTRL_RT_DTL rd ON rh.RATE_HDR_ID = rd.RATE_HDR_ID AND rh.TSP_NO = rd.TSP_NO AND rh.EFF_DT_FROM = rd.EFF_DT_FROM
WHERE rh.TSP_NO = @TspNo AND rh.TOC_CD = @FuelTocCd
  AND rh.EFF_DT_FROM <= @GasDay AND rh.EFF_DT_TO >= @GasDay
  AND rd.EFF_DT_FROM <= @GasDay AND rd.EFF_DT_TO >= @GasDay;
```

### Query 6: Rate Change History

```sql
-- View rate header time slices (effective date changes)
SELECT rh.RATE_HDR_ID, rh.RATE_NM, rh.EFF_DT_FROM, rh.EFF_DT_TO,
       rh.RATE_TYPE_CD, rh.PRICE_TYPE_CD, rh.CHARGE_PER_CD,
       rh.USER_ID, rh.UPDATE_DT
FROM RTCTRL_RT_HDR rh
WHERE rh.TSP_NO = @TspNo AND rh.RATE_HDR_ID = @RateHdrId
ORDER BY rh.EFF_DT_FROM DESC;
```

---

## Error Messages

| Error Message | Cause | Resolution |
|---------------|-------|------------|
| "Multiple rates (N) found for TOC_CD: XXX nomination on contract YYY from LOC1 to LOC2" | Multiple rate details have identical ranking | See Issue 1 |
| "Cannot have receipt fuel charge basis and delivery fuel charge basis on contract XXX" | Mixed charge basis across fuel TOCs | See Issue 5 |
| "Unable to find the contract: XXX" | Contract not in cache for date | See Issue 11 |
| "Contract XXX does not exist on this date" | Contract effective date mismatch | See Issue 11 |
| "Could not resolve Type of Charge for contract XXX" | TOC lookup returned null | Check TOC configuration for TSP |
| "Could not get next Rate Header Id!" | Sequence generation failure | Check RTCTRL_RATE_HDR.RATE_HDR_ID sequence |
| "As of date range cannot be before PPA Cutoff Date" | Query date before PPA cutoff | See Issue 12 |
| "The discount rate...is invalid because it is above the tariff maximum rate" | Discount exceeds tariff max | See Issue 7 |
| "The discount rate...is invalid because it is below the tariff minimum rate" | Discount below tariff min | See Issue 7 |
| "Exactly 1 Type of charge attribute was expected..." | Multiple TOC attributes match criteria | Check RTCTRL_TOC_ATTR for duplicates |
| "*** XYZ tier method is not supported ***" | Unsupported tier method (Step) | Reconfigure tier to use Block method |
| "*** XYZ price type is not supported ***" | Unsupported price type in context | Check rate header price type configuration |

---

## Investigation Workflow

### Step-by-Step Rate Issue Investigation

1. **Identify the Context**: Collect TSP number, contract number, gas day, receipt location, delivery location, TOC code
2. **Check Rate Headers**: Query `RTCTRL_RT_HDR` for matching TOC and date range
3. **Check Rate Details**: Query `RTCTRL_RT_DTL` for matching locations and dates
4. **Check Associations**: Query `RTCTRL_RT_CTR` and `RTCTRL_RT_TOS` for contract/TOS links
5. **Check TOC Rules**: Query `RTCTRL_TOC_RULE` to verify include/exclude logic
6. **Check Location Groups**: Query `PACTRL_LOC_GRP_LOC` to understand location group memberships
7. **Simulate Ranking**: Calculate header rank (contract vs TOS), rate type rank, and detail rank manually
8. **Check Cache**: If data looks correct in DB but resolution fails, consider cache staleness
9. **Enable Tracing**: The resolution engine writes to `System.Diagnostics.Trace` with detailed resolution info

### Key Trace Messages to Watch For

| Trace Message | Meaning |
|---------------|---------|
| `"**SUCCESS** Found a single best rate: ..."` | Resolution succeeded |
| `"FuelDataMgr: **FAILED** to find a single best rate in N rates"` | Resolution failed |
| `"TOC_CD is a valid TOC for contract: XXX"` | TOC passed all rule validation |
| `"*** price type is not supported ***"` | Unsupported price type encountered |
| `"*** tier method is not supported ***"` | Step tier or unknown tier method |
| `"Resolving fuel rates for TOC_CD: XXX Charge basis: YYY"` | Fuel resolution in progress |

---

## Performance Issues

### Slow Rate Resolution

**Symptoms:** Rate resolution or fuel calculation takes excessive time

**Investigation:**
1. Check the number of rate detail records for the TOC (high count = slow)
2. Check the number of location groups per location (high count = many candidates)
3. Check if RateCache is being refreshed too frequently

**Mitigation:**
- Optimize location group structure to reduce candidate rate details
- Ensure cache is properly warmed and not being refreshed unnecessarily
- Consider rate detail consolidation if too many overlapping details exist

### Rate Maintenance Screen Load Time

**Symptoms:** Rate Maintenance screen loads slowly

**Investigation:**
1. Check the number of rate detail records being loaded (Location Details grid)
2. Check the AddAdditionalProperties method which performs multiple joins
3. Check location name resolution queries

**Mitigation:**
- Use query filters to limit the number of records loaded
- Ensure database indexes on `RTCTRL_RT_DTL` are optimized

---

## Historical Work Items

### Template for Recording Rate Issues

```
### WI #XXXXX: [Brief Description]

**Date:** YYYY-MM-DD
**Customer/TSP:** [Customer name / TSP number]
**Environment:** [Production/UAT/etc.]

**Symptoms:**
- [Observed behavior]

**Root Cause:**
- [What was actually wrong]

**Resolution:**
- [What was changed/fixed]

**Code Changes:**
- [Files modified, if applicable]

**Lessons Learned:**
- [What to watch for in the future]
```

---

*Last updated: 2026-03-03*

*Document version: 1.0*
