---
title: Capacity Release (CR) - Troubleshooting Guide
category: troubleshooting
feature: Capacity Release (CR)
related_repos: Web, Batch
keywords: CR, troubleshooting, issues, errors, diagnostic queries, solutions, debugging, validation, offers, bids, awards, recall, reput
last_updated: 2026-03-03
---

# Capacity Release (CR) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Capacity Release (CR) issues in QPTM. It includes common problems, diagnostic queries, error messages, and solutions.

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

### Issue 1: Contract Not Nom-Ready After Award (RuleCROF001590)

**Symptoms:**
- Award processing completes but the replacement shipper's contract is not nomination-ready
- Nominations fail against the awarded capacity
- Validation rule RuleCROF001590 fires during offer validation
- Error message: "Contract not nom-ready" or similar

**Root Causes:**
1. Released capacity contract missing required configuration fields
2. Contract location setup incomplete for replacement shipper
3. Rate schedule not transferred properly to new contract
4. Contract effective dates not aligned with release dates
5. Missing contract-level data required for nominations (e.g., TOS, rate schedule, path configuration)

**Investigation Steps:**
```sql
-- Check the offer and its contract reference
SELECT
    oh.TSP_NO,
    oh.OFFER_NO,
    oh.SR_CTR_NO,
    oh.RELEASE_TYPE_CD,
    oh.OFFER_STAT_CD,
    oh.EFF_START_DT,
    oh.EFF_END_DT
FROM CRCTRL_OFFER_HDR oh
WHERE oh.TSP_NO = @TspNo
  AND oh.OFFER_NO = @OfferNo;

-- Check the releasing shipper's contract for required fields
SELECT
    kh.CTR_NO,
    kh.CTR_STAT_CD,
    kh.EFF_START_DT,
    kh.EFF_END_DT,
    kh.TOS_CD,
    kh.MDQ_QTY,
    kh.NOM_READY_IND
FROM KCTRL_CTR_HDR kh
WHERE kh.CTR_NO = @ContractNo
  AND kh.TSP_NO = @TspNo;

-- Check contract locations for completeness
SELECT
    cl.CTR_NO,
    cl.ID_CTR_LOC,
    cl.ID_LOC1,
    cl.ID_LOC2,
    cl.MDQ_QTY,
    cl.EFF_START_DT,
    cl.EFF_END_DT
FROM KCTRL_CTR_LOC cl
WHERE cl.CTR_NO = @ContractNo
  AND cl.TSP_NO = @TspNo;
```

**Solutions:**
- Verify releasing shipper's contract has all required fields populated
- Check that contract locations are properly configured with MDQ quantities
- Ensure rate schedules exist for the contract
- Verify contract effective dates encompass the release period
- Re-validate the offer after correcting contract data
- Check for missing path configuration on the contract

---

### Issue 2: Rate Bid Exceeds 100% (RuleCRBD000080)

**Symptoms:**
- Bid validation fails with RuleCRBD000080
- Error message indicates rate bid percentage exceeds maximum
- Replacement shipper cannot submit bid

**Root Causes:**
1. PctMaxRateBid value set above 100% for a long-term non-permanent release
2. Incorrect rate calculation in bid entry
3. Offer rate terms mismatched with bid rate type
4. Pipeline-specific rate cap configuration not applied correctly

**Investigation Steps:**
```sql
-- Check the bid rate details
SELECT
    bh.TSP_NO,
    bh.OFFER_NO,
    bh.BID_NO,
    bh.RATE_BID,
    bh.PCT_MAX_RATE_BID,
    bh.BID_STAT_CD
FROM CRCTRL_BID_HDR bh
WHERE bh.TSP_NO = @TspNo
  AND bh.OFFER_NO = @OfferNo
  AND bh.BID_NO = @BidNo;

-- Check the offer rate terms
SELECT
    oh.TSP_NO,
    oh.OFFER_NO,
    oh.MIN_RATE,
    oh.MAX_RATE,
    oh.RELEASE_TYPE_CD,
    oh.AUCTION_TYPE_CD
FROM CRCTRL_OFFER_HDR oh
WHERE oh.TSP_NO = @TspNo
  AND oh.OFFER_NO = @OfferNo;

-- Check pipeline rate cap configuration
-- (Pipeline admin tables vary by TSP configuration)
```

**Solutions:**
- Ensure PctMaxRateBid does not exceed 100% for applicable release types
- Verify rate bid is expressed in correct units matching the offer
- Check pipeline-specific rate cap settings
- If bid rate is legitimate, verify offer rate terms are configured correctly
- Review whether the release qualifies for an exemption from the 100% cap

---

### Issue 3: Offer Detail Not Found for Bid

**Symptoms:**
- Bid creation or validation fails because offer details cannot be found
- Error message: "Offer detail not found" or location matching failure
- Bid wizard cannot load offer detail data

**Root Causes:**
1. Offer detail records deleted or corrupted
2. Bid references incorrect offer number or detail sequence
3. Offer detail effective dates do not overlap with bid dates
4. Location IDs in bid do not match any offer detail locations

**Investigation Steps:**
```sql
-- Check if offer details exist
SELECT
    od.TSP_NO,
    od.OFFER_NO,
    od.DTL_SEQ_NO,
    od.REC_LOC_ID,
    od.DEL_LOC_ID,
    od.RELEASE_QTY,
    od.EFF_START_DT,
    od.EFF_END_DT
FROM CRCTRL_OFFER_DTL od
WHERE od.TSP_NO = @TspNo
  AND od.OFFER_NO = @OfferNo
ORDER BY od.DTL_SEQ_NO;

-- Check bid detail location references
SELECT
    bd.TSP_NO,
    bd.OFFER_NO,
    bd.BID_NO,
    bd.DTL_SEQ_NO,
    bd.REC_LOC_ID,
    bd.DEL_LOC_ID,
    bd.BID_QTY,
    bd.EFF_START_DT,
    bd.EFF_END_DT
FROM CRCTRL_BID_DTL bd
WHERE bd.TSP_NO = @TspNo
  AND bd.OFFER_NO = @OfferNo
  AND bd.BID_NO = @BidNo;

-- Compare locations between offer and bid
SELECT
    od.DTL_SEQ_NO AS OfferDtlSeq,
    od.REC_LOC_ID AS OfferRecLoc,
    od.DEL_LOC_ID AS OfferDelLoc,
    bd.DTL_SEQ_NO AS BidDtlSeq,
    bd.REC_LOC_ID AS BidRecLoc,
    bd.DEL_LOC_ID AS BidDelLoc
FROM CRCTRL_OFFER_DTL od
LEFT JOIN CRCTRL_BID_DTL bd
    ON od.TSP_NO = bd.TSP_NO
    AND od.OFFER_NO = bd.OFFER_NO
    AND od.REC_LOC_ID = bd.REC_LOC_ID
    AND od.DEL_LOC_ID = bd.DEL_LOC_ID
WHERE od.TSP_NO = @TspNo
  AND od.OFFER_NO = @OfferNo;
```

**Solutions:**
- Verify offer details exist in CRCTRL_OFFER_DTL for the referenced offer
- Ensure bid location IDs exactly match offer detail locations
- Check that bid effective dates fall within offer detail effective dates
- If offer details were deleted, the offer may need to be re-created
- Verify the offer is in the correct status for bidding

---

### Issue 4: Bid Detail Not Found for Award

**Symptoms:**
- Award processing fails because bid details cannot be found
- Error message: "Bid detail not found" during award creation
- Award validation fails on bid-to-award consistency checks

**Root Causes:**
1. Bid detail records missing or corrupted
2. Award references incorrect bid number or detail sequence
3. Bid was withdrawn after evaluation but before award processing
4. Data integrity issue between CRCTRL_BID_HDR and CRCTRL_BID_DTL

**Investigation Steps:**
```sql
-- Check if bid details exist
SELECT
    bd.TSP_NO,
    bd.OFFER_NO,
    bd.BID_NO,
    bd.DTL_SEQ_NO,
    bd.REC_LOC_ID,
    bd.DEL_LOC_ID,
    bd.BID_QTY
FROM CRCTRL_BID_DTL bd
WHERE bd.TSP_NO = @TspNo
  AND bd.OFFER_NO = @OfferNo
  AND bd.BID_NO = @BidNo;

-- Check bid header status
SELECT
    bh.TSP_NO,
    bh.OFFER_NO,
    bh.BID_NO,
    bh.BID_STAT_CD,
    bh.UPDT_DT
FROM CRCTRL_BID_HDR bh
WHERE bh.TSP_NO = @TspNo
  AND bh.OFFER_NO = @OfferNo
  AND bh.BID_NO = @BidNo;

-- Check for any existing award attempts
SELECT
    ah.TSP_NO,
    ah.OFFER_NO,
    ah.BID_NO,
    ah.AWARD_NO,
    ah.AWARD_STAT_CD
FROM CRCTRL_AWARD_HDR ah
WHERE ah.TSP_NO = @TspNo
  AND ah.OFFER_NO = @OfferNo
  AND ah.BID_NO = @BidNo;
```

**Solutions:**
- Verify bid details exist in CRCTRL_BID_DTL
- Check bid status - bid must be in Evaluated state for award
- Ensure bid was not withdrawn between evaluation and award
- If data integrity issue, investigate when/how bid details were removed
- Re-evaluate bids if necessary before attempting award

---

### Issue 5: Offer Doesn't Exist

**Symptoms:**
- Bid submission fails with "Offer does not exist" error
- Offer query returns no results for a known offer number
- Offer wizard cannot load a previously saved offer

**Root Causes:**
1. Offer was withdrawn or deleted
2. Incorrect TSP number in the query
3. Offer number entered incorrectly
4. Offer exists in a different environment (test vs production)
5. CWCOFF batch process cleaned up the offer

**Investigation Steps:**
```sql
-- Search for the offer in all statuses
SELECT
    oh.TSP_NO,
    oh.OFFER_NO,
    oh.OFFER_STAT_CD,
    oh.RELEASE_TYPE_CD,
    oh.SR_CTR_NO,
    oh.CREAT_DT,
    oh.UPDT_DT
FROM CRCTRL_OFFER_HDR oh
WHERE oh.OFFER_NO = @OfferNo;

-- Check if offer was processed by CWCOFF batch
SELECT
    pq.sProcessCode,
    pq.dProcessDate,
    pq.nProcessStatus
FROM tProcessQueue pq
WHERE pq.sProcessCode = 'CWCOFF'
  AND pq.dProcessDate >= DATEADD(day, -7, GETDATE())
ORDER BY pq.dProcessDate DESC;

-- Check offer timeline for withdrawal milestone
SELECT
    ot.TSP_NO,
    ot.OFFER_NO,
    ot.MILESTONE_TYPE_CD,
    ot.MILESTONE_DT,
    ot.MILESTONE_USER_ID
FROM CRTRAN_OFFER_TIMELINE ot
WHERE ot.OFFER_NO = @OfferNo
ORDER BY ot.MILESTONE_DT;
```

**Solutions:**
- Verify the correct TSP number and offer number
- Check if offer was withdrawn or cancelled (check OFFER_STAT_CD)
- Review CRTRAN_OFFER_TIMELINE for withdrawal milestones
- If offer was cleaned up by CWCOFF, it may need to be re-created
- Verify you are connected to the correct environment

---

### Issue 6: No Security for Bid Update

**Symptoms:**
- User cannot edit or update a bid
- Security error when accessing bid maintenance
- CRAwardController returns authorization failure

**Root Causes:**
1. User does not have CapRelAward or relevant CR security permission
2. Bid belongs to a different business party than user's assigned party
3. User role does not include bid update capability
4. Security configuration changed after bid was created

**Investigation Steps:**
```sql
-- Check user security permissions
SELECT
    ua.sUserID,
    ua.nTspNo,
    ua.sBPNo,
    ua.sSecurityRole
FROM SYSTBL_USER_BP_ACCESS ua
WHERE ua.sUserID = @UserId
  AND ua.nTspNo = @TspNo;

-- Check bid ownership
SELECT
    bh.TSP_NO,
    bh.OFFER_NO,
    bh.BID_NO,
    bh.BIDDER_BP_NO,
    bh.CREAT_USER_ID,
    bh.UPDT_USER_ID
FROM CRCTRL_BID_HDR bh
WHERE bh.TSP_NO = @TspNo
  AND bh.OFFER_NO = @OfferNo
  AND bh.BID_NO = @BidNo;
```

**Solutions:**
- Grant user the appropriate CR security permissions (e.g., CapRelAward)
- Verify user's business party assignment matches the bid's bidder
- Check security role configuration for bid update capabilities
- Review QOperationContext.Current.SecurityUser for the user session

---

### Issue 7: Batch Job Failures

**Symptoms:**
- CR batch processes fail (CRMDQMSQVL, CROFFRTIML, CRBIDGEN, CRBGNNS, CWCOFF, CWOSEASPST)
- Error messages in process queue or message log
- Offers not advancing through lifecycle stages
- Bidding windows not opening or closing automatically

**Root Causes:**
1. Missing or invalid batch parameters
2. Database connectivity issues
3. Data validation failures in batch processing
4. Deadlock or timeout during batch execution
5. Invalid data in CR tables causing processing errors

**Investigation Steps:**
```sql
-- Check batch process status for all CR processes
SELECT
    pq.sProcessCode,
    pq.dProcessDate,
    pq.nProcessStatus,
    pq.dStartTime,
    pq.dEndTime,
    DATEDIFF(SECOND, pq.dStartTime, pq.dEndTime) AS DurationSeconds
FROM tProcessQueue pq
WHERE pq.sProcessCode IN ('CRMDQMSQVL', 'CROFFRTIML', 'CRBIDGEN', 'CRBGNNS', 'CWCOFF', 'CWOSEASPST')
  AND pq.dProcessDate >= DATEADD(day, -7, GETDATE())
ORDER BY pq.dProcessDate DESC;

-- Check error messages for CR batch processes
SELECT
    m.sProcessCode,
    m.dMessageDate,
    m.nMessageType,
    m.sMessage,
    m.sStackTrace
FROM tMessage m
WHERE m.sProcessCode IN ('CRMDQMSQVL', 'CROFFRTIML', 'CRBIDGEN', 'CRBGNNS', 'CWCOFF', 'CWOSEASPST')
  AND m.dMessageDate >= DATEADD(day, -7, GETDATE())
  AND m.nMessageType = 1  -- Errors
ORDER BY m.dMessageDate DESC;

-- Check batch input parameters
SELECT
    pip.nProcessQueueID,
    pq.sProcessCode,
    pip.sParameterName,
    pip.sParameterValue
FROM tProcessInputParameter pip
INNER JOIN tProcessQueue pq ON pip.nProcessQueueID = pq.nProcessQueueID
WHERE pq.sProcessCode IN ('CRMDQMSQVL', 'CROFFRTIML', 'CRBIDGEN', 'CRBGNNS', 'CWCOFF', 'CWOSEASPST')
  AND pq.dProcessDate >= DATEADD(day, -3, GETDATE())
ORDER BY pq.dProcessDate DESC;
```

**Solutions:**
- Verify all required batch parameters are provided (TSP_NO, date ranges, etc.)
- Check database connectivity and resolve any connection issues
- Review error messages and stack traces for specific failures
- Look for deadlocks in SQL Server logs during batch execution windows
- Re-run failed batch processes after correcting root cause
- For CROFFRTIML failures, manually check offers that should have had timeline milestones triggered

---

### Issue 8: Bidding Window Issues

**Symptoms:**
- Bids rejected because bidding window is not open
- Bidding window appears to have wrong dates
- Offers stuck in submitted status because bidding window never opened
- CROFFRTIML batch not advancing offer timeline

**Root Causes:**
1. BidPerStartDate or BidPerEndDate set incorrectly on the offer
2. CROFFRTIML batch process not running or failing
3. Time zone differences between client and server
4. Offer timeline milestone not recorded for bidding window open
5. Pipeline configuration for minimum bidding window not met

**Investigation Steps:**
```sql
-- Check offer bidding window dates
SELECT
    oh.TSP_NO,
    oh.OFFER_NO,
    oh.BID_PER_START_DT,
    oh.BID_PER_END_DT,
    oh.OFFER_STAT_CD,
    GETDATE() AS CurrentServerTime,
    CASE
        WHEN GETDATE() < oh.BID_PER_START_DT THEN 'Not Yet Open'
        WHEN GETDATE() BETWEEN oh.BID_PER_START_DT AND oh.BID_PER_END_DT THEN 'Open'
        WHEN GETDATE() > oh.BID_PER_END_DT THEN 'Closed'
    END AS BiddingWindowStatus
FROM CRCTRL_OFFER_HDR oh
WHERE oh.TSP_NO = @TspNo
  AND oh.OFFER_NO = @OfferNo;

-- Check timeline milestones for bidding window
SELECT
    ot.TSP_NO,
    ot.OFFER_NO,
    ot.MILESTONE_TYPE_CD,
    ot.MILESTONE_DT
FROM CRTRAN_OFFER_TIMELINE ot
WHERE ot.TSP_NO = @TspNo
  AND ot.OFFER_NO = @OfferNo
ORDER BY ot.MILESTONE_DT;

-- Check if CROFFRTIML has run recently
SELECT TOP 5
    pq.sProcessCode,
    pq.dProcessDate,
    pq.nProcessStatus,
    pq.dStartTime,
    pq.dEndTime
FROM tProcessQueue pq
WHERE pq.sProcessCode = 'CROFFRTIML'
ORDER BY pq.dProcessDate DESC;
```

**Solutions:**
- Verify BidPerStartDate and BidPerEndDate are correct on the offer header
- Ensure CROFFRTIML batch process is scheduled and running successfully
- Check for time zone discrepancies between server and client
- Manually update bidding window dates if incorrectly set
- Verify the bidding window meets FERC minimum posting requirements
- Re-run CROFFRTIML if timeline milestones were missed

---

### Issue 9: Location Matching Failures

**Symptoms:**
- Bid validation fails with location matching errors
- Offer detail locations do not align with contract locations
- Award processing fails because locations cannot be matched between offer, bid, and contract

**Root Causes:**
1. Offer detail locations do not match the releasing shipper's contract locations
2. Bid locations entered incorrectly (typo or wrong location ID)
3. Location IDs changed or deactivated after offer creation
4. Contract location configuration missing the receipt/delivery pair
5. Location zone or group mismatches

**Investigation Steps:**
```sql
-- Check offer detail locations against contract locations
SELECT
    od.OFFER_NO,
    od.REC_LOC_ID AS OfferRecLoc,
    od.DEL_LOC_ID AS OfferDelLoc,
    cl.ID_LOC1 AS ContractLoc1,
    cl.ID_LOC2 AS ContractLoc2,
    CASE
        WHEN od.REC_LOC_ID = cl.ID_LOC1 AND od.DEL_LOC_ID = cl.ID_LOC2 THEN 'Match'
        WHEN od.REC_LOC_ID = cl.ID_LOC2 AND od.DEL_LOC_ID = cl.ID_LOC1 THEN 'Reverse Match'
        ELSE 'No Match'
    END AS MatchStatus
FROM CRCTRL_OFFER_DTL od
CROSS JOIN KCTRL_CTR_LOC cl
WHERE od.TSP_NO = @TspNo
  AND od.OFFER_NO = @OfferNo
  AND cl.CTR_NO = (SELECT SR_CTR_NO FROM CRCTRL_OFFER_HDR WHERE TSP_NO = @TspNo AND OFFER_NO = @OfferNo)
  AND cl.TSP_NO = @TspNo;

-- Check location master data
SELECT
    l.ID_LOC,
    l.LOC_NM,
    l.LOC_TYPE_CD,
    l.LOC_STAT_CD,
    l.EFF_START_DT,
    l.EFF_END_DT
FROM PACTRL_LOC l
WHERE l.ID_LOC IN (@RecLocId, @DelLocId)
  AND l.TSP_NO = @TspNo;
```

**Solutions:**
- Verify offer detail locations exist in the releasing shipper's contract
- Ensure bid locations exactly match offer detail locations
- Check location master data for deactivated or changed locations
- Validate location effective dates cover the release period
- Correct location IDs in offer or bid as needed

---

### Issue 10: Seasonal Date Validation Errors

**Symptoms:**
- Seasonal release offer fails validation on date fields
- Error message about seasonal dates being inconsistent
- Seasonal release dates extend beyond contract term

**Root Causes:**
1. Seasonal start date is after seasonal end date
2. Seasonal dates extend beyond the releasing shipper's contract term
3. Seasonal dates overlap with existing releases on the same contract
4. Seasonal dates do not align with gas month boundaries (if required by pipeline)
5. Offer detail effective dates inconsistent with header seasonal dates

**Investigation Steps:**
```sql
-- Check offer header dates and contract dates
SELECT
    oh.OFFER_NO,
    oh.EFF_START_DT AS OfferStart,
    oh.EFF_END_DT AS OfferEnd,
    oh.RELEASE_TYPE_CD,
    kh.EFF_START_DT AS ContractStart,
    kh.EFF_END_DT AS ContractEnd,
    CASE
        WHEN oh.EFF_START_DT < kh.EFF_START_DT THEN 'Offer starts before contract'
        WHEN oh.EFF_END_DT > kh.EFF_END_DT THEN 'Offer ends after contract'
        WHEN oh.EFF_START_DT > oh.EFF_END_DT THEN 'Start after end'
        ELSE 'Dates OK'
    END AS DateValidation
FROM CRCTRL_OFFER_HDR oh
INNER JOIN KCTRL_CTR_HDR kh ON oh.TSP_NO = kh.TSP_NO AND oh.SR_CTR_NO = kh.CTR_NO
WHERE oh.TSP_NO = @TspNo
  AND oh.OFFER_NO = @OfferNo;

-- Check for overlapping releases on same contract
SELECT
    oh1.OFFER_NO AS CurrentOffer,
    oh2.OFFER_NO AS OverlappingOffer,
    oh2.EFF_START_DT,
    oh2.EFF_END_DT,
    oh2.OFFER_STAT_CD
FROM CRCTRL_OFFER_HDR oh1
INNER JOIN CRCTRL_OFFER_HDR oh2
    ON oh1.TSP_NO = oh2.TSP_NO
    AND oh1.SR_CTR_NO = oh2.SR_CTR_NO
    AND oh1.OFFER_NO != oh2.OFFER_NO
WHERE oh1.TSP_NO = @TspNo
  AND oh1.OFFER_NO = @OfferNo
  AND oh2.OFFER_STAT_CD NOT IN ('WITHDRAWN', 'CANCELLED')
  AND oh1.EFF_START_DT <= oh2.EFF_END_DT
  AND oh1.EFF_END_DT >= oh2.EFF_START_DT;

-- Check offer detail dates against header dates
SELECT
    od.DTL_SEQ_NO,
    od.EFF_START_DT AS DetailStart,
    od.EFF_END_DT AS DetailEnd,
    oh.EFF_START_DT AS HeaderStart,
    oh.EFF_END_DT AS HeaderEnd,
    CASE
        WHEN od.EFF_START_DT < oh.EFF_START_DT THEN 'Detail starts before header'
        WHEN od.EFF_END_DT > oh.EFF_END_DT THEN 'Detail ends after header'
        ELSE 'OK'
    END AS Validation
FROM CRCTRL_OFFER_DTL od
INNER JOIN CRCTRL_OFFER_HDR oh ON od.TSP_NO = oh.TSP_NO AND od.OFFER_NO = oh.OFFER_NO
WHERE od.TSP_NO = @TspNo
  AND od.OFFER_NO = @OfferNo;
```

**Solutions:**
- Correct seasonal start/end dates to be within contract term
- Ensure start date is before end date
- Resolve any overlapping releases on the same contract
- Align offer detail dates with header dates
- Check pipeline-specific requirements for gas month alignment

---

### Issue 11: Award Quantity vs Available Quantity Mismatch

**Symptoms:**
- Award fails because awarded quantity exceeds available quantity
- Multiple awards on same offer exceed total offered quantity
- Partial award quantities do not sum correctly

**Root Causes:**
1. Multiple bids awarded on the same offer detail without quantity tracking
2. Award quantity exceeds bid quantity or offer quantity
3. Concurrent award processing creates race condition
4. Previous partial awards not accounted for in remaining available quantity

**Investigation Steps:**
```sql
-- Check total awarded vs offered quantity by location
SELECT
    od.OFFER_NO,
    od.DTL_SEQ_NO,
    od.REC_LOC_ID,
    od.DEL_LOC_ID,
    od.RELEASE_QTY AS OfferedQty,
    ISNULL(SUM(ad.AWARD_QTY), 0) AS TotalAwardedQty,
    od.RELEASE_QTY - ISNULL(SUM(ad.AWARD_QTY), 0) AS RemainingQty
FROM CRCTRL_OFFER_DTL od
LEFT JOIN CRCTRL_AWARD_DTL ad
    ON od.TSP_NO = ad.TSP_NO
    AND od.OFFER_NO = ad.OFFER_NO
    AND od.REC_LOC_ID = ad.REC_LOC_ID
    AND od.DEL_LOC_ID = ad.DEL_LOC_ID
LEFT JOIN CRCTRL_AWARD_HDR ah
    ON ad.TSP_NO = ah.TSP_NO
    AND ad.OFFER_NO = ah.OFFER_NO
    AND ad.BID_NO = ah.BID_NO
    AND ad.AWARD_NO = ah.AWARD_NO
    AND ah.AWARD_STAT_CD NOT IN ('CANCELLED', 'RECALLED')
WHERE od.TSP_NO = @TspNo
  AND od.OFFER_NO = @OfferNo
GROUP BY od.OFFER_NO, od.DTL_SEQ_NO, od.REC_LOC_ID, od.DEL_LOC_ID, od.RELEASE_QTY
HAVING od.RELEASE_QTY < ISNULL(SUM(ad.AWARD_QTY), 0);
```

**Solutions:**
- Verify remaining available quantity before processing award
- Check for and resolve duplicate awards on the same offer detail
- Ensure award processing is serialized to prevent race conditions
- Reconcile awarded quantities with offered quantities across all active awards

---

### Issue 12: Approval Status Blocking Offer Submission

**Symptoms:**
- Offer cannot be submitted because approvals are incomplete
- Approval chain shows pending approvals
- Approver cannot access the approval screen

**Investigation Steps:**
```sql
-- Check offer approval status
SELECT
    oa.TSP_NO,
    oa.OFFER_NO,
    oa.APPR_SEQ_NO,
    oa.APPR_USER_ID,
    oa.APPR_STAT_CD,
    oa.APPR_DT,
    oh.OFFER_STAT_CD
FROM CRCTRL_OFFER_APPR oa
INNER JOIN CRCTRL_OFFER_HDR oh ON oa.TSP_NO = oh.TSP_NO AND oa.OFFER_NO = oh.OFFER_NO
WHERE oa.TSP_NO = @TspNo
  AND oa.OFFER_NO = @OfferNo
ORDER BY oa.APPR_SEQ_NO;
```

**Solutions:**
- Check which approval step is pending and notify the appropriate approver
- Verify approver has access and correct security permissions
- If approver is unavailable, update approval chain via pipeline admin configuration
- For stuck approvals, check if the approval workflow can be reset

---

## Diagnostic Queries

### Query 1: Offer Lifecycle Overview

**Purpose:** Get a complete view of an offer's lifecycle status and associated bids/awards.

```sql
SELECT
    oh.TSP_NO,
    oh.OFFER_NO,
    oh.SR_CTR_NO,
    oh.RELEASE_TYPE_CD,
    oh.AUCTION_TYPE_CD,
    oh.OFFER_STAT_CD,
    oh.BID_PER_START_DT,
    oh.BID_PER_END_DT,
    oh.EFF_START_DT,
    oh.EFF_END_DT,
    oh.RECALL_IND,
    oh.REPUT_IND,
    (SELECT COUNT(*) FROM CRCTRL_OFFER_DTL od WHERE od.TSP_NO = oh.TSP_NO AND od.OFFER_NO = oh.OFFER_NO) AS DetailCount,
    (SELECT COUNT(*) FROM CRCTRL_BID_HDR bh WHERE bh.TSP_NO = oh.TSP_NO AND bh.OFFER_NO = oh.OFFER_NO) AS BidCount,
    (SELECT COUNT(*) FROM CRCTRL_AWARD_HDR ah WHERE ah.TSP_NO = oh.TSP_NO AND ah.OFFER_NO = oh.OFFER_NO) AS AwardCount,
    oh.CREAT_DT,
    oh.UPDT_DT
FROM CRCTRL_OFFER_HDR oh
WHERE oh.TSP_NO = @TspNo
  AND (@OfferNo IS NULL OR oh.OFFER_NO = @OfferNo)
ORDER BY oh.UPDT_DT DESC;
```

### Query 2: Award vs Available Quantity

**Purpose:** Compare total awarded quantity against total offered quantity per offer.

```sql
SELECT
    od.TSP_NO,
    od.OFFER_NO,
    od.DTL_SEQ_NO,
    od.REC_LOC_ID,
    od.DEL_LOC_ID,
    od.RELEASE_QTY,
    ISNULL(awarded.TotalAwarded, 0) AS TotalAwarded,
    od.RELEASE_QTY - ISNULL(awarded.TotalAwarded, 0) AS Remaining,
    CASE
        WHEN ISNULL(awarded.TotalAwarded, 0) >= od.RELEASE_QTY THEN 'Fully Awarded'
        WHEN ISNULL(awarded.TotalAwarded, 0) > 0 THEN 'Partially Awarded'
        ELSE 'Not Awarded'
    END AS AwardStatus
FROM CRCTRL_OFFER_DTL od
LEFT JOIN (
    SELECT
        ad.TSP_NO, ad.OFFER_NO, ad.REC_LOC_ID, ad.DEL_LOC_ID,
        SUM(ad.AWARD_QTY) AS TotalAwarded
    FROM CRCTRL_AWARD_DTL ad
    INNER JOIN CRCTRL_AWARD_HDR ah
        ON ad.TSP_NO = ah.TSP_NO AND ad.OFFER_NO = ah.OFFER_NO
        AND ad.BID_NO = ah.BID_NO AND ad.AWARD_NO = ah.AWARD_NO
    WHERE ah.AWARD_STAT_CD NOT IN ('CANCELLED', 'RECALLED')
    GROUP BY ad.TSP_NO, ad.OFFER_NO, ad.REC_LOC_ID, ad.DEL_LOC_ID
) awarded ON od.TSP_NO = awarded.TSP_NO AND od.OFFER_NO = awarded.OFFER_NO
    AND od.REC_LOC_ID = awarded.REC_LOC_ID AND od.DEL_LOC_ID = awarded.DEL_LOC_ID
WHERE od.TSP_NO = @TspNo
  AND od.OFFER_NO = @OfferNo;
```

### Query 3: Bid Validation Summary

**Purpose:** Summarize all bids for an offer with their validation and status information.

```sql
SELECT
    bh.TSP_NO,
    bh.OFFER_NO,
    bh.BID_NO,
    bh.BIDDER_BP_NO,
    bh.RATE_BID,
    bh.PCT_MAX_RATE_BID,
    bh.BID_STAT_CD,
    (SELECT COUNT(*) FROM CRCTRL_BID_DTL bd WHERE bd.TSP_NO = bh.TSP_NO AND bd.OFFER_NO = bh.OFFER_NO AND bd.BID_NO = bh.BID_NO) AS DetailCount,
    (SELECT SUM(bd.BID_QTY) FROM CRCTRL_BID_DTL bd WHERE bd.TSP_NO = bh.TSP_NO AND bd.OFFER_NO = bh.OFFER_NO AND bd.BID_NO = bh.BID_NO) AS TotalBidQty,
    bh.CREAT_DT,
    bh.UPDT_DT
FROM CRCTRL_BID_HDR bh
WHERE bh.TSP_NO = @TspNo
  AND bh.OFFER_NO = @OfferNo
ORDER BY bh.RATE_BID DESC, bh.BID_NO;
```

### Query 4: Timeline Milestones

**Purpose:** View all timeline milestones for an offer to track its lifecycle progression.

```sql
SELECT
    ot.TSP_NO,
    ot.OFFER_NO,
    ot.MILESTONE_TYPE_CD,
    ot.MILESTONE_DT,
    ot.MILESTONE_USER_ID,
    oh.OFFER_STAT_CD AS CurrentOfferStatus,
    oh.BID_PER_START_DT,
    oh.BID_PER_END_DT
FROM CRTRAN_OFFER_TIMELINE ot
INNER JOIN CRCTRL_OFFER_HDR oh ON ot.TSP_NO = oh.TSP_NO AND ot.OFFER_NO = oh.OFFER_NO
WHERE ot.TSP_NO = @TspNo
  AND ot.OFFER_NO = @OfferNo
ORDER BY ot.MILESTONE_DT;
```

### Query 5: Approval Status

**Purpose:** Check approval chain status for offers and bids.

```sql
-- Offer approvals
SELECT
    'Offer' AS Type,
    oa.OFFER_NO AS ReferenceNo,
    NULL AS BidNo,
    oa.APPR_SEQ_NO,
    oa.APPR_USER_ID,
    oa.APPR_STAT_CD,
    oa.APPR_DT,
    oh.OFFER_STAT_CD AS ParentStatus
FROM CRCTRL_OFFER_APPR oa
INNER JOIN CRCTRL_OFFER_HDR oh ON oa.TSP_NO = oh.TSP_NO AND oa.OFFER_NO = oh.OFFER_NO
WHERE oa.TSP_NO = @TspNo
  AND oa.OFFER_NO = @OfferNo

UNION ALL

-- Bid approvals
SELECT
    'Bid' AS Type,
    ba.OFFER_NO,
    ba.BID_NO,
    ba.APPR_SEQ_NO,
    ba.APPR_USER_ID,
    ba.APPR_STAT_CD,
    ba.APPR_DT,
    bh.BID_STAT_CD AS ParentStatus
FROM CRCTRL_BID_APPR ba
INNER JOIN CRCTRL_BID_HDR bh ON ba.TSP_NO = bh.TSP_NO AND ba.OFFER_NO = bh.OFFER_NO AND ba.BID_NO = bh.BID_NO
WHERE ba.TSP_NO = @TspNo
  AND ba.OFFER_NO = @OfferNo

ORDER BY Type, ReferenceNo, APPR_SEQ_NO;
```

---

## Error Messages

### Error: "Contract not nom-ready" (RuleCROF001590)

**Cause:** The released capacity cannot produce a nomination-ready contract for the replacement shipper.

**Solution:** See [Issue 1](#issue-1-contract-not-nom-ready-after-award-rulecrof001590) above. Verify contract configuration, locations, rates, and effective dates.

### Error: "Rate bid exceeds maximum percentage" (RuleCRBD000080)

**Cause:** PctMaxRateBid value exceeds the allowed maximum (100% for long-term non-permanent releases).

**Solution:** See [Issue 2](#issue-2-rate-bid-exceeds-100-rulecrbd000080) above. Reduce rate bid to within allowed limits.

### Error: "Offer detail not found"

**Cause:** Bid references an offer whose detail records are missing or do not match.

**Solution:** See [Issue 3](#issue-3-offer-detail-not-found-for-bid) above. Verify offer details exist and bid locations match.

### Error: "Bid detail not found"

**Cause:** Award references a bid whose detail records are missing.

**Solution:** See [Issue 4](#issue-4-bid-detail-not-found-for-award) above. Verify bid details exist and bid is in correct state.

### Error: "Offer does not exist"

**Cause:** Referenced offer cannot be found in the database.

**Solution:** See [Issue 5](#issue-5-offer-doesnt-exist) above. Verify TSP number, offer number, and offer status.

### Error: "Not authorized for bid update"

**Cause:** User lacks required security permissions for CR bid operations.

**Solution:** See [Issue 6](#issue-6-no-security-for-bid-update) above. Grant appropriate CR security permissions.

---

## Investigation Workflow

### Step-by-Step Investigation Process

**Step 1: Identify the CR Entity**
```sql
-- Determine if the issue is with an offer, bid, or award
-- Check the status of the entity
SELECT oh.OFFER_NO, oh.OFFER_STAT_CD, 'Offer' AS EntityType FROM CRCTRL_OFFER_HDR oh WHERE oh.TSP_NO = @TspNo AND oh.OFFER_NO = @OfferNo
UNION ALL
SELECT CAST(bh.BID_NO AS VARCHAR) + ' (Offer ' + CAST(bh.OFFER_NO AS VARCHAR) + ')', bh.BID_STAT_CD, 'Bid' FROM CRCTRL_BID_HDR bh WHERE bh.TSP_NO = @TspNo AND bh.OFFER_NO = @OfferNo
UNION ALL
SELECT CAST(ah.AWARD_NO AS VARCHAR) + ' (Offer ' + CAST(ah.OFFER_NO AS VARCHAR) + ')', ah.AWARD_STAT_CD, 'Award' FROM CRCTRL_AWARD_HDR ah WHERE ah.TSP_NO = @TspNo AND ah.OFFER_NO = @OfferNo;
```

**Step 2: Check Timeline and History**
- Query CRTRAN_OFFER_TIMELINE for milestone history
- Review process queue for any batch job failures
- Check message log for errors related to the offer/bid/award

**Step 3: Validate Data Integrity**
- Verify header-detail consistency (offer details match header, bid details match bid header)
- Check foreign key relationships (bid references valid offer, award references valid bid)
- Confirm location and quantity data consistency

**Step 4: Review Validation Results**
- Re-run validation for the entity (ValidateOffer, ValidateBid, ValidateAward)
- Check specific rule codes in the validation results
- Look up rule descriptions for any failing rules

**Step 5: Check Batch Processing**
- Verify relevant batch jobs have run (CROFFRTIML, CRMDQMSQVL, etc.)
- Check for batch failures in tProcessQueue
- Review batch error messages in tMessage

**Step 6: Verify Configuration**
- Check pipeline admin configuration for CR settings
- Verify user security permissions
- Review approval chain configuration

---

## Performance Issues

### Issue: Slow Offer Query

**Symptoms:** QueryOffer or offer list screens take a long time to load.

**Investigation:**
```sql
-- Check offer table sizes
SELECT
    OBJECT_NAME(i.object_id) AS TableName,
    SUM(p.rows) AS RowCount
FROM sys.indexes i
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
WHERE OBJECT_NAME(i.object_id) IN (
    'CRCTRL_OFFER_HDR', 'CRCTRL_OFFER_DTL', 'CRCTRL_BID_HDR',
    'CRCTRL_BID_DTL', 'CRCTRL_AWARD_HDR', 'CRCTRL_AWARD_DTL',
    'CRTRAN_OFFER_TIMELINE'
)
GROUP BY OBJECT_NAME(i.object_id);
```

**Solutions:**
- Ensure indexes exist on TSP_NO, OFFER_NO, and status columns
- Archive old, completed offers and associated data
- Optimize query filters to limit result set
- Review execution plans for table scans

### Issue: QPTMCapacityReleaseService Memory Usage

**Symptoms:** High memory consumption during CR processing, especially with the 230KB service class.

**Solutions:**
- Monitor LocalContractCache and LocalPipelineAdminCache sizes during processing
- Ensure caches are properly disposed after processing completes
- Break large batch operations into smaller chunks
- Review for unnecessary data loading in service methods

---

## Historical Work Items

### Work Item Categories

**Offer Issues:**
- Offer validation failures due to contract configuration
- Seasonal date validation errors
- Approval chain configuration problems
- Recall/reput provision inconsistencies

**Bid Issues:**
- Rate bid exceeding maximum percentage
- Location matching failures between bid and offer
- Bidding window timing problems
- Prearranged bidder matching issues

**Award Issues:**
- Award quantity exceeding offered quantity
- Contract creation failures after award
- Nom-ready status not set after award
- Award amendment processing errors

**Batch Issues:**
- CROFFRTIML not advancing offer timeline
- CRMDQMSQVL validation failures on large datasets
- CWCOFF cleanup affecting active data
- CWOSEASPST seasonal write-off timing

---

## Tips and Best Practices

### Troubleshooting Tips

1. **Always check the offer status first** - Most CR issues stem from the offer being in an unexpected state
2. **Review the timeline** - Query CRTRAN_OFFER_TIMELINE to see the full history of the offer
3. **Verify batch processing** - Many lifecycle issues are caused by CROFFRTIML not running
4. **Check validation rules** - Run ValidateOffer/ValidateBid/ValidateAward to identify specific rule failures
5. **Verify bidding windows** - Time-sensitive issues often relate to BidPerStartDate/BidPerEndDate configuration

### Prevention Best Practices

1. **Monitor batch jobs** - Set up alerts for CROFFRTIML and other CR batch process failures
2. **Validate before submission** - Always run validation before submitting offers or bids
3. **Review contract setup** - Ensure releasing shipper contracts are fully configured before creating offers
4. **Test seasonal dates** - Validate seasonal date ranges before creating seasonal offers
5. **Security audit** - Regularly verify user CR security permissions are appropriate

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts and terminology
- **Architecture**: [architecture.md](./architecture.md) - Technical implementation details
- **CAS Troubleshooting**: [../capacity-scheduling-allocations/troubleshooting.md](../capacity-scheduling-allocations/troubleshooting.md) - Related CAS issues
- **Nominations Troubleshooting**: [../nominations/troubleshooting.md](../nominations/troubleshooting.md) - Nomination issues after award
- **QUICK_REFERENCE.md**: Feature mapping and keywords for CR

---

*Last updated: 2026-03-03*
*Document version: 1.0*
