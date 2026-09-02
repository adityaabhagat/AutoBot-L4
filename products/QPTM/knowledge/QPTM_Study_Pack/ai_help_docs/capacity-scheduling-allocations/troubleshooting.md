---
title: Capacity Scheduling Allocations (CAS) - Troubleshooting Guide
category: troubleshooting
feature: Capacity Scheduling Allocations (CAS)
related_repos: Web, Batch
keywords: CAS, troubleshooting, issues, errors, diagnostic queries, solutions, debugging
last_updated: 2025-12-11
---

# Capacity Scheduling Allocations (CAS) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Capacity Scheduling Allocations (CAS) issues in QPTM. It includes common problems, diagnostic queries, error messages, and solutions.

For business concepts, see [Domain Documentation](./domain.md).
For technical details, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Diagnostic Queries](#diagnostic-queries)
3. [Error Messages](#error-messages)
4. [Investigation Workflow](#investigation-workflow)
5. [Performance Issues](#performance-issues)
6. [Data Integrity Issues](#data-integrity-issues)
7. [Historical Work Items](#historical-work-items)

---

## Common Issues

### Issue 1: Nominations Not Classified

**Symptoms:**
- Nominations appear in system but don't show up in CAS summary
- `CASTAG_OBJ_NOM_TRANS_GRP` table empty or incomplete for gas day/cycle
- CAS summary screen shows no data after query

**Root Causes:**
1. Classification batch process (`QPSNomClassificationAndTransGroupingSeg`) not run
2. Batch process failed with errors
3. No matching transaction groups for nomination attributes
4. Rule sets not configured for TSP/cycle
5. Nomination status prevents classification

**Investigation Steps:**
```sql
-- Check if batch process ran
SELECT * FROM tProcessQueue
WHERE sProcessCode = 'CANOMCLTG'
  AND dProcessDate >= DATEADD(day, -1, GETDATE())
ORDER BY dProcessDate DESC;

-- Check for errors in batch log
SELECT * FROM tMessage
WHERE sProcessCode = 'CANOMCLTG'
  AND dMessageDate >= DATEADD(day, -1, GETDATE())
  AND nMessageType = 1  -- Errors
ORDER BY dMessageDate DESC;

-- Check staging table population
SELECT COUNT(*)
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId;

-- Check if rule sets exist for TSP/cycle
SELECT * 
FROM CAXREF_SCHD_OBJ_RULE_SET
WHERE TSP_NO = @TspNo
  AND ID_CYCLE = @CycleId;
```

**Solutions:**
- Run classification batch process manually
- Fix batch process errors (check message log)
- Verify rule set configuration exists for TSP/cycle
- Check transaction group TOS filters match nomination TOS
- Verify nomination status is eligible for classification

---

### Issue 2: Incorrect Scheduled Quantities

**Symptoms:**
- Scheduled quantities don't match expected values
- Unexpected reductions applied
- Ratcheted quantities not working correctly

**Root Causes:**
1. Operational available capacity (OAC) set incorrectly
2. Transaction group ranks not configured properly
3. Reduction algorithm logic issue
4. Previous cycle quantities incorrect (affecting ratchet)
5. Manual adjustments overwritten

**Investigation Steps:**
```sql
-- Check OAC values
SELECT SCHD_OBJ_ID, SCHD_OBJ_TYPE_CD, OPER_AVAIL_CAP
FROM CACTRL_SUMMARY
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId;

-- Compare nominated vs scheduled
SELECT 
    SCHD_OBJ_ID,
    SCHD_OBJ_TYPE_CD,
    REC_QTY AS RecNominated,
    REC_SCHED_QTY AS RecScheduled,
    REC_CUT_QTY AS RecCut,
    DEL_QTY AS DelNominated,
    DEL_SCHED_QTY AS DelScheduled,
    DEL_CUT_QTY AS DelCut,
    OPER_AVAIL_CAP AS OAC,
    (REC_QTY + DEL_QTY) AS TotalNominated,
    (REC_QTY + DEL_QTY) - OPER_AVAIL_CAP AS OverNominatedAmount
FROM CACTRL_SUMMARY
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId
  AND (REC_QTY + DEL_QTY) > OPER_AVAIL_CAP;

-- Check transaction group ranks
SELECT 
    stg.SCHD_OBJ_ID,
    stg.TRANS_GRP_ID,
    stg.TRANS_GRP_RANK,
    SUM(stg.REC_QTY + stg.DEL_QTY) AS TotalQty
FROM CASTAG_OBJ_NOM_TRANS_GRP stg
WHERE stg.TSP_NO = @TspNo
  AND stg.GAS_DAY = @GasDay
  AND stg.ID_CYCLE = @CycleId
GROUP BY stg.SCHD_OBJ_ID, stg.TRANS_GRP_ID, stg.TRANS_GRP_RANK
ORDER BY stg.SCHD_OBJ_ID, stg.TRANS_GRP_RANK;

-- Check ratchet quantities
SELECT 
    TSP_NO,
    GAS_DAY,
    ID_CYCLE,
    SCHD_OBJ_ID,
    REC_PREV_CYCLE_SCHED_QTY,
    DEL_PREV_CYCLE_SCHED_QTY,
    REC_RATCH_PREV_CYCLE_SCHED_QTY,
    DEL_RATCH_PREV_CYCLE_SCHED_QTY
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId
  AND (REC_RATCH_PREV_CYCLE_SCHED_QTY > 0 OR DEL_RATCH_PREV_CYCLE_SCHED_QTY > 0);
```

**Solutions:**
- Verify OAC values are correct for gas day
- Re-run `QPSStageOperationalAvailableCapacity` process
- Check transaction group rank configuration
- Verify ratchet settings enabled in `CACTRL_SCHD_HDR`
- Re-run reduction process after fixing configuration
- Verify reduction algorithm configuration for scheduling object type

---

### Issue 3: CAS Summary Screen Empty

**Symptoms:**
- User opens CAS Summary Maintenance screen
- Screen loads but shows no data
- "No records found" message

**Root Causes:**
1. No data in staging table for selected parameters
2. Gas day/cycle combination invalid
3. Scheduling object type filter excludes all data
4. User doesn't have security access to data
5. Query parameters incorrect

**Investigation Steps:**
```sql
-- Check for any staging data
SELECT TOP 10 *
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
ORDER BY UPDT_DT DESC;

-- Check header exists
SELECT *
FROM CACTRL_SCHD_HDR
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId;

-- Check scheduling object types in staging
SELECT DISTINCT SCHD_OBJ_TYPE_CD
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId;

-- Check user security access
SELECT *
FROM SYSTBL_USER_BP_ACCESS
WHERE sUserID = @UserId
  AND nTspNo = @TspNo;
```

**Solutions:**
- Run classification batch process for gas day/cycle
- Verify gas day and cycle ID are correct
- Check scheduling object type filter includes valid types
- Verify user has BP access for TSP
- Check QOperationContext.Current.SecurityUser permissions

---

### Issue 4: Transaction Group Not Matching

**Symptoms:**
- Nomination classified to wrong transaction group
- Expected transaction group not assigned
- Multiple transaction groups assigned unexpectedly

**Root Causes:**
1. Rule set configuration incorrect
2. TOS filter excludes nomination
3. Path criteria don't match nomination path
4. Contract not eligible for transaction group
5. Rule set rank priority issue

**Investigation Steps:**
```sql
-- Check nomination TOS
SELECT 
    nh.ID_NOM,
    nh.TOS_CD,
    nh.SR_CTR_NO,
    nh.ID_REC_LOC,
    nh.ID_DEL_LOC
FROM NNCTRL_NOM_HDR nh
WHERE nh.TSP_NO = @TspNo
  AND nh.GAS_DAY = @GasDay
  AND nh.ID_CYCLE <= @CycleId
  AND nh.ID_NOM = @NomId;

-- Check transaction group TOS filters
SELECT 
    tg.TRANS_GRP_ID,
    tg.TRANS_GRP_NM,
    tgtos.TOS_CD
FROM PACTRL_TRANS_GRP tg
INNER JOIN PAXREF_TRANS_GRP_TOS tgtos ON tg.TSP_NO = tgtos.TSP_NO AND tg.TRANS_GRP_ID = tgtos.TRANS_GRP_ID
WHERE tg.TSP_NO = @TspNo;

-- Check rule set assignment
SELECT 
    rs.CAS_RULE_SET_ID,
    rs.CAS_RULE_SET_NM,
    rs.RULE_SET_RANK,
    tg.TRANS_GRP_ID,
    tg.TRANS_GRP_NM,
    tg.TRANS_GRP_RANK
FROM PACTRL_RULE_SET rs
INNER JOIN PACTRL_TRANS_GRP tg ON rs.TSP_NO = tg.TSP_NO AND rs.CAS_RULE_SET_ID = tg.CAS_RULE_SET_ID
WHERE rs.TSP_NO = @TspNo
ORDER BY rs.RULE_SET_RANK, tg.TRANS_GRP_RANK;

-- Check actual classification result
SELECT *
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId
  AND ID_NOM = @NomId;
```

**Solutions:**
- Verify TOS filters include nomination TOS code
- Check path criteria match nomination rec/del locations
- Verify rule set rank order is correct
- Add missing TOS to transaction group filters
- Review rule set configuration logic
- Re-run classification after configuration changes

---

### Issue 5: Batch Process Failures

**Symptoms:**
- Classification batch process fails
- Reduction batch process fails
- Error messages in message log

**Root Causes:**
1. Missing required parameters
2. Database connection issues
3. Data validation failures
4. Insufficient permissions
5. Code exceptions

**Investigation Steps:**
```sql
-- Check batch process status
SELECT *
FROM tProcessQueue
WHERE sProcessCode IN ('CANOMCLTG', 'SCREDUCE', 'SCOAC')
  AND dProcessDate >= DATEADD(day, -1, GETDATE())
ORDER BY dProcessDate DESC;

-- Check error messages
SELECT 
    m.nMessageID,
    m.sProcessCode,
    m.dMessageDate,
    m.sMessage,
    m.sStackTrace
FROM tMessage m
WHERE m.sProcessCode IN ('CANOMCLTG', 'SCREDUCE', 'SCOAC')
  AND m.dMessageDate >= DATEADD(day, -1, GETDATE())
  AND m.nMessageType = 1  -- Errors
ORDER BY m.dMessageDate DESC;

-- Check process parameters
SELECT *
FROM tProcessInputParameter
WHERE nProcessQueueID IN (
    SELECT nProcessQueueID
    FROM tProcessQueue
    WHERE sProcessCode IN ('CANOMCLTG', 'SCREDUCE', 'SCOAC')
      AND dProcessDate >= DATEADD(day, -1, GETDATE())
);
```

**Solutions:**
- Verify all required parameters provided
- Check database connectivity
- Review error messages for specific issue
- Verify user permissions for batch execution
- Check for data integrity issues in source tables
- Re-run batch process after fixing root cause

---

### Issue 6: Reduction Not Working Correctly

**Symptoms:**
- All nominations cut equally regardless of rank
- Higher priority nominations cut before lower priority
- Pro-rata reduction not proportional

**Root Causes:**
1. Transaction group ranks not set correctly
2. Reduction algorithm misconfiguration
3. Capacity type priorities ignored
4. Reduction group manager logic issue

**Investigation Steps:**
```sql
-- Verify transaction group ranks in staging
SELECT 
    SCHD_OBJ_ID,
    TRANS_GRP_ID,
    TRANS_GRP_RANK,
    COUNT(*) AS NomCount,
    SUM(REC_QTY + DEL_QTY) AS TotalNominated
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND ID_CYCLE = @CycleId
GROUP BY SCHD_OBJ_ID, TRANS_GRP_ID, TRANS_GRP_RANK
ORDER BY SCHD_OBJ_ID, TRANS_GRP_RANK;

-- Check scheduled quantities by rank
SELECT 
    s.SCHD_OBJ_ID,
    stg.TRANS_GRP_RANK,
    SUM(stg.REC_QTY + stg.DEL_QTY) AS TotalNominated,
    s.OPER_AVAIL_CAP,
    SUM(stg.REC_QTY + stg.DEL_QTY) - s.OPER_AVAIL_CAP AS Overage
FROM CASTAG_OBJ_NOM_TRANS_GRP stg
INNER JOIN CACTRL_SUMMARY s ON 
    stg.TSP_NO = s.TSP_NO AND 
    stg.GAS_DAY = s.GAS_DAY AND 
    stg.ID_CYCLE = s.ID_CYCLE AND 
    stg.SCHD_OBJ_ID = s.SCHD_OBJ_ID AND 
    stg.SCHD_OBJ_TYPE_CD = s.SCHD_OBJ_TYPE_CD
WHERE stg.TSP_NO = @TspNo
  AND stg.GAS_DAY = @GasDay
  AND stg.ID_CYCLE = @CycleId
GROUP BY s.SCHD_OBJ_ID, stg.TRANS_GRP_RANK, s.OPER_AVAIL_CAP
ORDER BY s.SCHD_OBJ_ID, stg.TRANS_GRP_RANK;

-- Check accounting method for transaction groups
SELECT 
    tg.TRANS_GRP_ID,
    tg.TRANS_GRP_NM,
    tg.ACCT_METH_CD
FROM PACTRL_TRANS_GRP tg
WHERE tg.TSP_NO = @TspNo;
```

**Solutions:**
- Verify transaction group rank values (lower = higher priority)
- Check accounting method code (PR = Pro-Rata)
- Verify reduction group manager implementation
- For special scheduling object types (Clay Basin), verify specific reduction logic
- Re-run `QPSSchedulingReductionSeg` after fixing configuration

---

### Issue 10: Rights Allocation Problems (SI/SO/P/N Quantities Incorrect)

**Symptoms:**
- Incorrect quantities in RightSplits (SI, SO, P, S, N categories)
- SI (SecondaryInPath) showing wrong values
- SO (SecondaryOutOfPath) not calculated correctly
- P (Primary) quantities exceeding contract MDQ
- N (Overrun) quantities appearing when they shouldn't

**Common Causes:**
- MDQ calculation errors (segMDQ vs primaryMDQ vs secondaryMDQ)
- Flow direction logic issues (forward vs backhaul)
- Scheduling object type confusion (Location vs Segment)
- Contract MDQ configuration problems
- Caching issues with m_RightSplitsCache
- **SI rights assigned without primary rights existing**
- **SO rights not applied for opposite direction nominations**
- Contract location matching logic changes (permissive vs strict matching)

**Investigation Steps:**

1. **Verify MDQ Calculations:**
   ```sql
   -- Check contract MDQ values
   SELECT 
       cl.CONTRACT_NO,
       cl.LOCATION_ID,
       cl.MDQ_QTY AS ContractMDQ,
       cl.PRIMARY_MDQ_QTY AS PrimaryMDQ,
       (cl.MDQ_QTY - cl.PRIMARY_MDQ_QTY) AS SecondaryMDQ
   FROM KCTRL_CTR_LOC cl
   WHERE cl.CONTRACT_NO = @ContractNo
     AND cl.LOCATION_ID = @LocationId;
   
   -- Check segment MDQ values
   SELECT 
       so.SCHD_OBJ_ID,
       so.SCHD_OBJ_TYPE_CD,
       so.SEGMENT_MDQ_QTY AS SegMDQ
   FROM PACTRL_SCHD_OBJ so
   WHERE so.SCHD_OBJ_ID = @SchedulingObjectId;
   ```

4. **Check Rights Evaluation Logic:**
   - For SI rights: Verify `secondaryMDQ = segMDQ - primaryMDQ`
   - For Location objects: SI rights only apply to locations, not segments
   - For Segment objects: Only P (Primary) and N (Overrun) rights apply
   - Check flow direction: `IsFlow` property affects rights assignment

5. **Debug EvaluateSegmentRights2 Function:**
   - Located in `TransGrpNomHelper.cs` around line 1742
   - Check if nomination quantity ≤ segment MDQ
   - Verify scheduling object type (Location vs Segment)
   - Check contract MDQ configuration
   - **Verify SI prerequisite**: Primary rights must exist before SI assignment
   - **Verify SO logic**: Opposite direction nominations get SO without primary rights requirement

4. **Clear Rights Cache:**
   - Rights are cached in `m_RightSplitsCache` by scheduling object ID
   - Clear cache if configuration changes aren't reflected

5. **Check Contract Location Matching Logic:**
   ```sql
   -- Verify contract location setup for scheduling object
   SELECT 
       cl.CONTRACT_NO,
       cl.ID_CTR_LOC,
       cl.ID_LOC1,
       cl.ID_LOC2,
       cl.MDQ_QTY,
       cl.PRIMARY_MDQ_QTY
   FROM KCTRL_CTR_LOC cl
   WHERE (cl.ID_LOC1 = @SchedulingObjectId OR cl.ID_LOC2 = @SchedulingObjectId)
     AND cl.CONTRACT_NO IN (
         SELECT DISTINCT SrCtrNo 
         FROM NNCTRL_NOM_DTL 
         WHERE GAS_DAY = @GasDay 
         AND (ID_REC_LOC = @SchedulingObjectId OR ID_DEL_LOC = @SchedulingObjectId)
     );
   ```
   - **Issue**: Modified logic allows primary rights to nominations that don't exactly match contract location endpoints
   - **Impact**: May over-allocate primary capacity if nomination paths don't align with contract setup

**Solutions:**
- Fix MDQ configuration in contract locations
- Verify scheduling object type settings
- Check flow direction logic in nomination processing
- Clear rights cache after configuration changes
- Re-run nomination classification process
- **Ensure SI rights only assigned when primary rights exist** - check PRIMARY_MDQ_QTY > 0 before SI assignment
- **Verify SO rights for opposite direction nominations** - check for forward route + 'B' contract or backward route + 'F' contract scenarios
- **Review contract location matching logic** - ensure nominations match contract endpoints for accurate primary rights allocation

---

## Diagnostic Queries

### Query 1: CAS Summary Overview

**Purpose**: Get complete view of CAS summary for gas day/cycle

```sql
SELECT 
    s.TSP_NO,
    s.GAS_DAY,
    s.ID_CYCLE,
    cy.CYCLE_NM,
    s.SCHD_OBJ_ID,
    s.SCHD_OBJ_TYPE_CD,
    so.SCHD_OBJ_NM,
    s.REC_QTY AS RecNominated,
    s.DEL_QTY AS DelNominated,
    s.REC_SCHED_QTY AS RecScheduled,
    s.DEL_SCHED_QTY AS DelScheduled,
    s.REC_CUT_QTY AS RecCut,
    s.DEL_CUT_QTY AS DelCut,
    s.OPER_AVAIL_CAP AS OAC,
    CASE 
        WHEN (s.REC_QTY + s.DEL_QTY) > s.OPER_AVAIL_CAP THEN 'Over-Nominated'
        ELSE 'OK'
    END AS Status,
    s.SCEN_STAT_CD,
    s.ID_SUBMIT_USER,
    s.SUBMIT_TIME
FROM CACTRL_SUMMARY s
LEFT JOIN CACTRL_SCHD_OBJ_VW so ON 
    s.TSP_NO = so.TSP_NO AND 
    s.SCHD_OBJ_ID = so.SCHD_OBJ_ID AND 
    s.SCHD_OBJ_TYPE_CD = so.SCHD_OBJ_TYPE_CD
LEFT JOIN PACTRL_CYCLE cy ON s.ID_CYCLE = cy.ID_CYCLE
WHERE s.TSP_NO = @TspNo
  AND s.GAS_DAY = @GasDay
  AND s.ID_CYCLE = @CycleId
ORDER BY s.SCHD_OBJ_ID;
```

### Query 2: Nomination Classification Details

**Purpose**: See how specific nominations were classified

```sql
SELECT 
    stg.ID_NOM,
    nh.SR_BP_NO,
    nh.SR_CTR_NO,
    nh.TOS_CD,
    stg.SCHD_OBJ_ID,
    stg.SCHD_OBJ_TYPE_CD,
    stg.TRANS_GRP_ID,
    tg.TRANS_GRP_NM,
    stg.TRANS_GRP_RANK,
    stg.REC_QTY,
    stg.DEL_QTY,
    stg.CAP_TYPE_CD,
    stg.DIRECTION_FLOW_CD,
    stg.CAS_RULE_SET_ID,
    rs.CAS_RULE_SET_NM
FROM CASTAG_OBJ_NOM_TRANS_GRP stg
LEFT JOIN NNCTRL_NOM_HDR nh ON 
    stg.TSP_NO = nh.TSP_NO AND 
    stg.ID_NOM = nh.ID_NOM
LEFT JOIN PACTRL_TRANS_GRP tg ON 
    stg.TSP_NO = tg.TSP_NO AND 
    stg.TRANS_GRP_ID = tg.TRANS_GRP_ID
LEFT JOIN PACTRL_RULE_SET rs ON 
    stg.TSP_NO = rs.TSP_NO AND 
    stg.CAS_RULE_SET_ID = rs.CAS_RULE_SET_ID
WHERE stg.TSP_NO = @TspNo
  AND stg.GAS_DAY = @GasDay
  AND stg.ID_CYCLE = @CycleId
  AND (@NomId IS NULL OR stg.ID_NOM = @NomId)
ORDER BY stg.SCHD_OBJ_ID, stg.TRANS_GRP_RANK, stg.ID_NOM;
```

### Query 3: Compare Cycles

**Purpose**: Compare scheduled quantities across cycles

```sql
SELECT 
    s1.SCHD_OBJ_ID,
    s1.SCHD_OBJ_TYPE_CD,
    cy1.CYCLE_NM AS Cycle1,
    s1.REC_SCHED_QTY AS Cycle1_RecSched,
    s1.DEL_SCHED_QTY AS Cycle1_DelSched,
    cy2.CYCLE_NM AS Cycle2,
    s2.REC_SCHED_QTY AS Cycle2_RecSched,
    s2.DEL_SCHED_QTY AS Cycle2_DelSched,
    s2.REC_SCHED_QTY - s1.REC_SCHED_QTY AS RecDelta,
    s2.DEL_SCHED_QTY - s1.DEL_SCHED_QTY AS DelDelta
FROM CACTRL_SUMMARY s1
INNER JOIN CACTRL_SUMMARY s2 ON 
    s1.TSP_NO = s2.TSP_NO AND 
    s1.GAS_DAY = s2.GAS_DAY AND 
    s1.SCHD_OBJ_ID = s2.SCHD_OBJ_ID AND 
    s1.SCHD_OBJ_TYPE_CD = s2.SCHD_OBJ_TYPE_CD
LEFT JOIN PACTRL_CYCLE cy1 ON s1.ID_CYCLE = cy1.ID_CYCLE
LEFT JOIN PACTRL_CYCLE cy2 ON s2.ID_CYCLE = cy2.ID_CYCLE
WHERE s1.TSP_NO = @TspNo
  AND s1.GAS_DAY = @GasDay
  AND s1.ID_CYCLE = @Cycle1Id
  AND s2.ID_CYCLE = @Cycle2Id
ORDER BY s1.SCHD_OBJ_ID;
```

### Query 4: Transaction Group Analysis

**Purpose**: Analyze transaction group configuration and usage

```sql
SELECT 
    rs.CAS_RULE_SET_ID,
    rs.CAS_RULE_SET_NM,
    rs.RULE_SET_RANK,
    tg.TRANS_GRP_ID,
    tg.TRANS_GRP_NM,
    tg.TRANS_GRP_RANK,
    tg.ACCT_METH_CD,
    COUNT(DISTINCT stg.ID_NOM) AS NomCount,
    SUM(stg.REC_QTY + stg.DEL_QTY) AS TotalQty
FROM PACTRL_RULE_SET rs
INNER JOIN PACTRL_TRANS_GRP tg ON 
    rs.TSP_NO = tg.TSP_NO AND 
    rs.CAS_RULE_SET_ID = tg.CAS_RULE_SET_ID
LEFT JOIN CASTAG_OBJ_NOM_TRANS_GRP stg ON 
    tg.TSP_NO = stg.TSP_NO AND 
    tg.TRANS_GRP_ID = stg.TRANS_GRP_ID AND 
    stg.GAS_DAY = @GasDay AND 
    stg.ID_CYCLE = @CycleId
WHERE rs.TSP_NO = @TspNo
GROUP BY 
    rs.CAS_RULE_SET_ID,
    rs.CAS_RULE_SET_NM,
    rs.RULE_SET_RANK,
    tg.TRANS_GRP_ID,
    tg.TRANS_GRP_NM,
    tg.TRANS_GRP_RANK,
    tg.ACCT_METH_CD
ORDER BY rs.RULE_SET_RANK, tg.TRANS_GRP_RANK;
```

### Query 5: Scheduling Object Configuration

**Purpose**: View scheduling object setup and capacity

```sql
SELECT 
    so.TSP_NO,
    so.SCHD_OBJ_ID,
    so.SCHD_OBJ_TYPE_CD,
    sot.SCHD_OBJ_TYPE_DESC,
    so.SCHD_OBJ_NM,
    so.EFF_DATE_FROM,
    so.EFF_DATE_TO,
    so.ID_UP_LOC,
    ul.LOC_NM AS UpLocName,
    so.ID_DN_LOC,
    dl.LOC_NM AS DnLocName,
    so.ID_LOC,
    l.LOC_NM AS LocName,
    so.LOC_GRP_CD,
    COUNT(DISTINCT sors.CAS_RULE_SET_ID) AS RuleSetCount
FROM CACTRL_SCHD_OBJ_VW so
LEFT JOIN PACTRL_SCHEDULE_OBJ_TYPE sot ON so.SCHD_OBJ_TYPE_CD = sot.SCHD_OBJ_TYPE_CD
LEFT JOIN PACTRL_LOC ul ON so.ID_UP_LOC = ul.ID_LOC
LEFT JOIN PACTRL_LOC dl ON so.ID_DN_LOC = dl.ID_LOC
LEFT JOIN PACTRL_LOC l ON so.ID_LOC = l.ID_LOC
LEFT JOIN CAXREF_SCHD_OBJ_RULE_SET sors ON 
    so.TSP_NO = sors.TSP_NO AND 
    so.SCHD_OBJ_ID = sors.SCHD_OBJ_ID AND 
    so.SCHD_OBJ_TYPE_CD = sors.SCHD_OBJ_TYPE_CD
WHERE so.TSP_NO = @TspNo
  AND @GasDay BETWEEN so.EFF_DATE_FROM AND so.EFF_DATE_TO
GROUP BY 
    so.TSP_NO, so.SCHD_OBJ_ID, so.SCHD_OBJ_TYPE_CD, sot.SCHD_OBJ_TYPE_DESC,
    so.SCHD_OBJ_NM, so.EFF_DATE_FROM, so.EFF_DATE_TO,
    so.ID_UP_LOC, ul.LOC_NM, so.ID_DN_LOC, dl.LOC_NM,
    so.ID_LOC, l.LOC_NM, so.LOC_GRP_CD
ORDER BY so.SCHD_OBJ_TYPE_CD, so.SCHD_OBJ_ID;
```

### Query 6: Ratchet Analysis

**Purpose**: Analyze ratcheted quantities

```sql
SELECT 
    stg.SCHD_OBJ_ID,
    stg.SCHD_OBJ_TYPE_CD,
    stg.ID_NOM,
    stg.REC_QTY AS CurrentNominated,
    stg.REC_PREV_CYCLE_SCHED_QTY AS PrevCycleScheduled,
    stg.REC_RATCH_PREV_CYCLE_SCHED_QTY AS RatchetedQty,
    CASE 
        WHEN stg.REC_RATCH_PREV_CYCLE_SCHED_QTY > stg.REC_QTY THEN 'RATCHETED'
        ELSE 'NOT RATCHETED'
    END AS RatchetStatus
FROM CASTAG_OBJ_NOM_TRANS_GRP stg
WHERE stg.TSP_NO = @TspNo
  AND stg.GAS_DAY = @GasDay
  AND stg.ID_CYCLE = @CycleId
  AND (stg.REC_RATCH_PREV_CYCLE_SCHED_QTY IS NOT NULL OR stg.DEL_RATCH_PREV_CYCLE_SCHED_QTY IS NOT NULL)
ORDER BY stg.SCHD_OBJ_ID, stg.ID_NOM;
```

---

## Error Messages

### Error: "More than 1 schedule header object was found when only one was expected"

**Cause**: Duplicate header records in `CACTRL_SCHD_HDR`

**Solution**:
```sql
-- Find duplicates
SELECT TSP_NO, GAS_DAY, ID_CYCLE, COUNT(*)
FROM CACTRL_SCHD_HDR
GROUP BY TSP_NO, GAS_DAY, ID_CYCLE
HAVING COUNT(*) > 1;

-- Delete duplicates (keep most recent)
DELETE FROM CACTRL_SCHD_HDR
WHERE UPDT_DT < (
    SELECT MAX(UPDT_DT)
    FROM CACTRL_SCHD_HDR h2
    WHERE h2.TSP_NO = CACTRL_SCHD_HDR.TSP_NO
      AND h2.GAS_DAY = CACTRL_SCHD_HDR.GAS_DAY
      AND h2.ID_CYCLE = CACTRL_SCHD_HDR.ID_CYCLE
);
```

### Error: "Unable to retrieve scheduling objects"

**Cause**: No scheduling objects defined or effective date range issue

**Solution**:
```sql
-- Check scheduling object configuration
SELECT *
FROM CACTRL_SCHD_OBJ_VW
WHERE TSP_NO = @TspNo
  AND @GasDay BETWEEN EFF_DATE_FROM AND EFF_DATE_TO;

-- If no results, create scheduling objects or adjust effective dates
```

### Error: "Parameter Tsp No is not provided"

**Cause**: Batch process missing required TSP_NO parameter

**Solution**: Verify batch process configuration includes TSP_NO parameter in QPEC

---

## Investigation Workflow

### Step-by-Step Investigation Process

**Step 1: Verify Data Exists**
```sql
-- Check if nominations exist
SELECT COUNT(*) FROM NNCTRL_NOM_HDR
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE <= @CycleId;

-- Check if classification ran
SELECT COUNT(*) FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId;

-- Check if summary exists
SELECT COUNT(*) FROM CACTRL_SUMMARY
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId;
```

**Step 2: Check Configuration**
- Verify scheduling objects configured
- Verify rule sets and transaction groups exist
- Verify TOS filters match nomination TOS codes
- Verify effective dates encompass gas day

**Step 3: Review Batch Process Logs**
- Check `tProcessQueue` for execution status
- Check `tMessage` for error messages
- Review batch process parameters

**Step 4: Analyze Classification Results**
- Query `CASTAG_OBJ_NOM_TRANS_GRP` for classification details
- Verify transaction groups assigned correctly
- Check transaction group ranks

**Step 5: Review Reduction Logic**
- Compare nominated vs OAC
- Analyze reduction by transaction group rank
- Verify pro-rata percentages

**Step 6: Test Manually**
- Re-run classification batch process
- Re-run reduction batch process
- Query CAS summary in web application

---

## Performance Issues

### Issue: Slow CAS Summary Query

**Symptoms**: CAS Summary Maintenance screen takes long time to load

**Investigation**:
```sql
-- Check table sizes
SELECT 
    OBJECT_NAME(i.object_id) AS TableName,
    SUM(p.rows) AS RowCount
FROM sys.indexes i
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
WHERE OBJECT_NAME(i.object_id) IN ('CASTAG_OBJ_NOM_TRANS_GRP', 'CACTRL_SUMMARY')
GROUP BY OBJECT_NAME(i.object_id);

-- Check for missing indexes
EXEC sp_helpindex 'CASTAG_OBJ_NOM_TRANS_GRP';
EXEC sp_helpindex 'CACTRL_SUMMARY';

-- Check query execution plan
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

-- Run slow query to analyze
SELECT * FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId;
```

**Solutions**:
- Add indexes on frequently queried columns
- Archive old staging data
- Optimize query filters
- Consider partitioning large tables
- Review execution plans and address table scans

### Issue: Batch Process Timeout

**Symptoms**: Classification or reduction batch process times out

**Investigation**:
- Check process execution time in `tProcessQueue`
- Review number of nominations being processed
- Check for database blocking/locking

**Solutions**:
- Increase batch process timeout setting
- Break processing into smaller gas day ranges
- Use incremental processing (NOM_ADD_SET_ID/NOM_UPD_SET_ID)
- Optimize database queries
- Run during off-peak hours

---

## Data Integrity Issues

### Issue: Orphaned Staging Records

**Symptoms**: Staging table contains old data from previous runs

**Investigation**:
```sql
-- Find old staging data
SELECT GAS_DAY, ID_CYCLE, COUNT(*)
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY < DATEADD(day, -7, GETDATE())
GROUP BY GAS_DAY, ID_CYCLE
ORDER BY GAS_DAY;
```

**Solution**:
```sql
-- Clean up old staging data
DELETE FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY < @CutoffDate;
```

### Issue: Inconsistent Summary Data

**Symptoms**: Summary totals don't match staging details

**Investigation**:
```sql
-- Compare summary vs staging totals
SELECT 
    'Summary' AS Source,
    SUM(REC_QTY) AS TotalRecQty,
    SUM(DEL_QTY) AS TotalDelQty
FROM CACTRL_SUMMARY
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId

UNION ALL

SELECT 
    'Staging' AS Source,
    SUM(REC_QTY) AS TotalRecQty,
    SUM(DEL_QTY) AS TotalDelQty
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId;
```

**Solution**: Re-run CAS summary generation service method

---

## Historical Work Items

### Work Item Categories

This section documents known historical work items related to CAS. Use this as a reference when investigating similar issues.

**Classification Issues**
- Nominations not classified due to missing rule sets
- Transaction group rank configuration errors
- TOS filter mismatches

**Reduction Issues**
- Incorrect reduction algorithm for Clay Basin scheduling objects
- Pro-rata reduction not working correctly
- Ratchet provisions not applied

**Performance Issues**
- Slow CAS summary queries due to missing indexes
- Batch process timeouts with large nomination volumes
- Staging table growth issues

**Configuration Issues**
- Scheduling object effective date gaps
- Missing transaction group TOS filters
- Rule set cycle assignment errors

---

## Tips and Best Practices

### Troubleshooting Tips

1. **Always check batch process logs first** - Most CAS issues stem from batch process failures
2. **Verify configuration before debugging code** - Many issues are configuration-related
3. **Use diagnostic queries to narrow down issue** - Don't assume root cause, verify with data
4. **Compare across cycles** - Often issues are cycle-specific
5. **Check effective dates** - Many "missing data" issues are date-related

### Prevention Best Practices

1. **Monitor batch process execution** - Set up alerts for failures
2. **Regular data cleanup** - Archive old staging data
3. **Configuration validation** - Validate rule set and transaction group setup
4. **Index maintenance** - Keep indexes optimized
5. **Documentation** - Document custom configurations and special cases

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts
- **Architecture**: [architecture.md](./architecture.md) - Technical implementation
- **QUICK_REFERENCE.md**: Feature mapping and keywords

---

*Last updated: 2025-12-11*  
*Document version: 1.0*
