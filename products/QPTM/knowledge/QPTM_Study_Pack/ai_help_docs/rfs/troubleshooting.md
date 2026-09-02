---
title: Request For Service (RFS) - Troubleshooting Guide
category: troubleshooting
feature: Request For Service (RFS)
related_repos: Web, Batch
keywords: RFS, troubleshooting, validation error, award failure, approval stuck, rate resolution, security, authorization, widget, performance, copy forward, KRFSTOCTR, present value, unsold capacity
last_updated: 2026-03-03
---

# Request For Service (RFS) - Troubleshooting Guide

## Overview

This document provides **troubleshooting guidance** for common RFS issues in the QPTM system. Each issue includes symptoms, root cause analysis, diagnostic SQL queries, code locations, and resolution steps.

For business concepts, see [Domain Documentation](./domain.md).
For technical implementation details, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Issue 1: RFS Validation Errors on Submit](#issue-1-rfs-validation-errors-on-submit)
2. [Issue 2: Award Fails - Contract Not Created](#issue-2-award-fails---contract-not-created)
3. [Issue 3: Approval Queue Not Showing RFS](#issue-3-approval-queue-not-showing-rfs)
4. [Issue 4: User Cannot See RFS - Security/Authorization](#issue-4-user-cannot-see-rfs---securityauthorization)
5. [Issue 5: Rate Resolution Errors](#issue-5-rate-resolution-errors)
6. [Issue 6: RFS Widget Not Displaying Activity](#issue-6-rfs-widget-not-displaying-activity)
7. [Issue 7: Copy Forward Not Available on Denied RFS](#issue-7-copy-forward-not-available-on-denied-rfs)
8. [Issue 8: Approval Notifications Not Sent](#issue-8-approval-notifications-not-sent)
9. [Issue 9: Multiple TOC Rates Found for Location](#issue-9-multiple-toc-rates-found-for-location)
10. [Issue 10: Present Value Calculation Incorrect](#issue-10-present-value-calculation-incorrect)
11. [Issue 11: RFS Wizard Tabs Missing or Wrong Order](#issue-11-rfs-wizard-tabs-missing-or-wrong-order)
12. [Issue 12: Award Stuck in Processing State](#issue-12-award-stuck-in-processing-state)
13. [Issue 13: Auto-Approval Not Working for Internal Users](#issue-13-auto-approval-not-working-for-internal-users)
14. [Issue 14: Contract Data Not Copying to RFS](#issue-14-contract-data-not-copying-to-rfs)
15. [Related Documentation](#related-documentation)

---

## Issue 1: RFS Validation Errors on Submit

### Symptoms
- User clicks Submit and receives validation error messages
- RFS status changes to PIN (Pending Invalid) instead of APR (Submitted)
- Error messages reference specific rule codes (K00xxx, KFK0xx)

### Root Cause
Validation runs in two phases: mandatory (ForeignKey level) and full (All level). Submit requires full validation to pass. Common causes:
- Missing required fields (BP, TOS, effective dates)
- Rate exceeds tariff maximum
- Location path invalid or inactive
- Date range conflicts

### Diagnostic SQL

```sql
-- Check RFS current status and data
SELECT h.TSP_NO, h.RFS_NO, h.EFF_DATE_FROM, h.EFF_DATE_TO,
       h.RFS_STATUS_CODE, h.REQ_TYPE_CODE, h.TOS_CODE, h.BP_NO, h.CTR_NO,
       h.SUBMIT_TIMESTAMP, h.ACTION_CODE
FROM RFS_HEADER h
WHERE h.TSP_NO = @TspNo AND h.RFS_NO = @RfsNo;

-- Check validation errors stored on the RFS
SELECT e.TSP_NO, e.RFS_NO, e.ERROR_MSG, e.IS_OVRD
FROM RFS_ERROR e
WHERE e.TSP_NO = @TspNo AND e.RFS_NO = @RfsNo;
```

### Code Location
- **Validation entry**: `QPTMRFSService.ValidateData()` (line ~2282)
- **Validation engine**: `QPTMRFSService.ValidateRFSContract()` (line ~389)
- **Rule files**: `Quorum.QPTM.Validations.Rules.RFS/LineRules/RuleK*.cs`
- **FK rules**: `Quorum.QPTM.Validations.Rules.RFS/ForeignKeyRules/RuleKFK*.cs`

### Resolution
1. Read the error message to identify the specific rule (rule code is usually in the message)
2. Locate the rule class in `Quorum.QPTM.Validations.Rules.RFS/`
3. Check if the rule validates against a DB reference table -- if so, check if the reference data exists
4. For overridable errors (`IsOvrd = true`), the user can override and resubmit
5. For non-overridable errors, the data must be corrected

---

## Issue 2: Award Fails - Contract Not Created

### Symptoms
- User clicks Award but no contract is created
- RFS status changes to AWI (Award Invalid)
- Error messages appear about validation failures on the CTR action

### Root Cause
The Award action (CTR) triggers full re-validation. Common causes:
- Data changed since last validation (stale data)
- Rate tariff boundaries changed
- User lacks security privilege for the award action
- KRFSTOCTR process queue failed

### Diagnostic SQL

```sql
-- Check RFS status after award attempt
SELECT h.TSP_NO, h.RFS_NO, h.RFS_STATUS_CODE, h.ACTION_CODE,
       h.IS_PROCESSING, h.UPDATE_DATE
FROM RFS_HEADER h
WHERE h.TSP_NO = @TspNo AND h.RFS_NO = @RfsNo;

-- Check if contract was created
SELECT c.TSP_NO, c.CTR_NO, c.EFF_DATE_FROM, c.EFF_DATE_TO, c.BP_NO
FROM CONTRACT c
WHERE c.TSP_NO = @TspNo AND c.BP_NO = @BpNo
  AND c.EFF_DATE_FROM = @EffDateFrom;

-- Check process queue for KRFSTOCTR
SELECT pq.*
FROM PROCESS_QUEUE pq
WHERE pq.TSP_NO = @TspNo
  AND pq.PROCESS_TYPE = 'KRFSTOCTR'
ORDER BY pq.CREATE_DATE DESC;

-- Check all approvals are complete
SELECT a.TSP_NO, a.RFS_NO, a.APPR_DEPT_CODE, a.APPR_ACTN_CODE, a.ORDER_NO
FROM RFS_APPROVAL a
WHERE a.TSP_NO = @TspNo AND a.RFS_NO = @RfsNo
ORDER BY a.ORDER_NO;
```

### Code Location
- **Award validation**: `QPTMRFSService.ValidateBeforeAward()` (line ~1063)
- **Action execution**: `QPTMRFSService.ExecuteRFSAction()` (line ~1628)
- **Security check**: `QPTMRFSService.IsActionAllowed()` (line ~2334)
- **Approval controller award**: `RFSApprovalController.DoAwardRFS()` (line ~370)
- **Post-award**: `RFSApprovalController.DoPostAwardRFS()` (line ~391)

### Resolution
1. Check `RFS_STATUS_CODE` -- if AWI, re-validate to find errors
2. Check `IS_PROCESSING` flag -- if true, a previous award may still be running
3. Verify all approvals have `APPR_ACTN_CODE = 'APR'` (not PEN or REJ)
4. Check user security: must have Execute permission on the award action's `IdObject`
5. Check PROCESS_QUEUE for KRFSTOCTR failures

---

## Issue 3: Approval Queue Not Showing RFS

### Symptoms
- Submitted RFS does not appear in the RFS Approval Queue
- User expects to see the RFS but queue is empty

### Root Cause
The approval queue has specific filters:
- Request type must have `IsShowReqQueue = true`
- RFS status must be in the active status list (or DEN with CopyForward)
- User must have TSP and BP authorization
- Date range filter must include the RFS effective dates

### Diagnostic SQL

```sql
-- Check if request type is configured for queue display
SELECT rt.REQ_TYPE_CODE, rt.REQ_TYPE_DESCR, rt.IS_SHOW_REQ_QUEUE
FROM CD_REQ_TYPE rt
WHERE rt.REQ_TYPE_CODE = @ReqTypeCode;

-- Check RFS status and whether it's active
SELECT s.CODE, s.DESCRIPTION, s.IS_ACTIVE
FROM RFS_STATUS s
WHERE s.CODE = @RfsStatusCode;

-- Check if user has TSP access
SELECT ut.TSP_NO, ut.ID_SEC_USER
FROM USER_TSP ut
WHERE ut.ID_SEC_USER = @UserId AND ut.TSP_NO = @TspNo;

-- Verify RFS dates fall within query range
SELECT h.TSP_NO, h.RFS_NO, h.EFF_DATE_FROM, h.EFF_DATE_TO,
       h.RFS_STATUS_CODE, h.REQ_TYPE_CODE, h.IS_COPY_FWD
FROM RFS_HEADER h
WHERE h.TSP_NO = @TspNo AND h.RFS_NO = @RfsNo;
```

### Code Location
- **Queue retrieval**: `QPTMRFSService.GetRFSApprovalQueueWithTsp()` (line ~684)
- **Web list retrieval**: `QPTMRFSService.GetRFSListForWeb()` (line ~794)
- **Security filtering**: `QPTMRFSService.FilterRfsListForSecurity()` (line ~532)

### Resolution
1. Verify the request type has `IS_SHOW_REQ_QUEUE = 1` in `CD_REQ_TYPE`
2. Verify the RFS status is in the active status list (`IS_ACTIVE = 1` in `RFS_STATUS`)
3. For denied RFS: it only shows if `IS_COPY_FWD = 1`
4. Check user TSP access and BP authorization
5. Ensure the date range filter includes the RFS effective dates

---

## Issue 4: User Cannot See RFS - Security/Authorization

### Symptoms
- User navigates to RFS but sees empty list
- Specific RFS is not visible to the user
- Error: "User is not valid for TSP and Module"

### Root Cause
RFS security depends on request type:
- **New Service**: User must be associated to BP or contracting agent
- **Existing Contract**: User must be associated to contract BP or contract-level agent
- **Internal Users**: Can see all RFS for their TSPs (unless widget BP filter applies)
- **External Users**: Only see RFS for their authorized BPs/agents

### Diagnostic SQL

```sql
-- Check if user is internal
SELECT u.ID_SEC_USER, u.IS_INTERNAL
FROM SECURITY_USER u
WHERE u.ID_SEC_USER = @UserId;

-- Check user BP associations
SELECT ubp.ID_SEC_USER, ubp.BP_NO
FROM USER_BP ubp
WHERE ubp.ID_SEC_USER = @UserId;

-- Check BP agent associations for the TSP
SELECT ba.BP_NO, ba.AGENT_BP_NO, ba.FUNC_CONTRACTS_CODE,
       ba.EFF_DATE_FROM, ba.EFF_DATE_TO
FROM BP_AGENT ba
WHERE ba.TSP_NO = @TspNo
  AND ba.BP_NO = @RfsBpNo
  AND ba.EFF_DATE_FROM <= @EffDateFrom
  AND ba.EFF_DATE_TO >= @EffDateFrom;

-- Check contract-level agent (for amendments)
SELECT ca.CTR_NO, ca.TSP_NO, ca.AGENT_BP_NO, ca.FUNC_CONTRACTS_CODE
FROM CONTRACT_AGENT ca
WHERE ca.TSP_NO = @TspNo AND ca.CTR_NO = @CtrNo;
```

### Code Location
- **Security check (service)**: `QPTMRFSService.IsUserAuthorizedForRfs()` (line ~551)
- **Security check (widget)**: `QPTMContractsWidgetService.IsUserAuthorizedForRfs()` (line ~390)
- **Security filtering**: `QPTMRFSService.RFSHeaderQueryDataSecurityCheck()` (line ~905)

### Resolution
1. Determine if user is internal or external
2. For external users, verify BP association via `USER_BP` table
3. For amendment requests, verify contract-level agent association
4. For new service requests, verify default contracting agent association
5. Check that the user has the TSP in their `USER_TSP` list

---

## Issue 5: Rate Resolution Errors

### Symptoms
- Rates show as null/blank after "Get Contract Info"
- Error message about rate resolution or "multiple applicable rates"
- Tariff Max/Min not populated on locations

### Root Cause
Rate resolution depends on:
- Rate schedule configuration for the TOS
- Type of Charge (TOC) setup for the security objects (GENERAL, LOCATIONS, DISCRATE, PAL1)
- MDQ calculation method (UseFirstDateMDQ vs UseMinMDQ)
- Location group vs. individual location rate matching

### Diagnostic SQL

```sql
-- Check TOC process xrefs for the TOS
SELECT rtpx.ID_PROCESS, rtpx.TOS_CODE, rtpx.TOC_CODE, rtpx.TSP_NO
FROM RATE_TOC_PROCESS_XREF rtpx
WHERE rtpx.TSP_NO = @TspNo AND rtpx.TOS_CODE = @TosCode
  AND rtpx.ID_PROCESS LIKE 'QVPSOAREQUESTFORSERVICE_%';

-- Check rate setup for the contract path
SELECT r.RATE_HDR_ID, r.TSP_NO, r.CTR_NO, r.LOC_ID_1, r.LOC_ID_2,
       r.TOC_CODE, r.RATE_TYPE_CODE, r.EFF_DATE_FROM, r.EFF_DATE_TO,
       r.RATE_AMT, r.PRICE_TYPE_CODE
FROM RATE r
WHERE r.TSP_NO = @TspNo AND r.CTR_NO = @CtrNo
  AND r.LOC_ID_1 = @LocId1 AND r.LOC_ID_2 = @LocId2;

-- Check MDQ calculation method
SELECT gc.KEY_VALUE
FROM GLOBAL_CONFIGURATION_CONTROL gc
WHERE gc.KEY_CATEGORY = 'CONTRACTS' AND gc.KEY_NM = 'RFS_GET_K_INFO_METHOD';
```

### Code Location
- **Rate resolution**: `QPTMRFSService.ResolveRate()` (line ~2438)
- **Multiple rate error**: Lines ~2835-2850 (throws exception for >1 TOC per path)
- **Rate service calls**: `IQPTMRateService.GetActualRate()` and `GetActualLocGrpRate()`

### Resolution
1. Check if TOC process xrefs exist for the TOS and security object
2. Verify rate records exist for the contract, path, and date range
3. If "multiple applicable rates" error: check that only one TOC applies per path per security object
4. Check the `RFS_GET_K_INFO_METHOD` global config (UseFirstDateMDQ uses EffDateFrom, UseMinMDQ uses EffDateTo)
5. For location groups, verify group-level rate lookup is returning correctly

---

## Issue 6: RFS Widget Not Displaying Activity

### Symptoms
- RFS Activity widget on dashboard shows zero counts
- Widget shows stale data
- Widget displays for some users but not others

### Root Cause
Widget data is cached and filtered:
- Cache expiration based on `WidgetCacheRfsActivity` global config
- Filter by recent activity days (`WidgetRecentActivityDays` TSP config)
- User must be valid for the TSP
- BP filtering for internal users controlled by `bFilterByBPForInternalUser`

### Diagnostic SQL

```sql
-- Check widget configuration
SELECT gc.KEY_NM, gc.KEY_VALUE
FROM GLOBAL_CONFIGURATION_CONTROL gc
WHERE gc.KEY_NM IN ('WidgetCacheRfsActivity', 'WidgetRecentActivityDays');

-- Check TSP-level override
SELECT tc.TSP_NO, tc.KEY_NM, tc.KEY_VALUE
FROM TSP_CONFIGURATION_CONTROL tc
WHERE tc.TSP_NO = @TspNo AND tc.KEY_NM = 'WidgetRecentActivityDays';

-- Check recent RFS activity
SELECT h.TSP_NO, h.RFS_NO, h.RFS_STATUS_CODE, h.UPDATE_DATE,
       h.EFF_DATE_FROM, h.EFF_DATE_TO
FROM RFS_HEADER h
WHERE h.TSP_NO = @TspNo
  AND (h.UPDATE_DATE >= DATEADD(DAY, -@DaysToRetrieve, GETDATE())
       OR (h.EFF_DATE_FROM <= @AsOfDate AND h.EFF_DATE_TO >= @AsOfDate))
ORDER BY h.UPDATE_DATE DESC;
```

### Code Location
- **Widget service**: `QPTMContractsWidgetService._GetRFSActivity_Get()` (line ~128)
- **Cache implementation**: `QPTMContractsWidgetService._GetRFSActivity_Cache()` (line ~81)
- **Activity counts**: `NewRFSActivityController.GetNewRFSActivityCounts()` (line ~64)

### Resolution
1. Check `WidgetCacheRfsActivity` -- if set too high, cache may serve stale data
2. Check `WidgetRecentActivityDays` -- if set too low, recent activity may be excluded
3. Verify user TSP access via `IsValidUserAndTsp`
4. For stale cache, the cache uses absolute expiration; wait for timeout or restart app pool
5. Check that RFS records have recent `UPDATE_DATE` values

---

## Issue 7: Copy Forward Not Available on Denied RFS

### Symptoms
- RFS is denied (status DEN) but Copy Forward button not visible
- User cannot create a new RFS from the denied request

### Root Cause
Copy Forward requires:
- RFS status must be DEN (Denied)
- Request type must have `IsAllowCopyFwd = true`
- The RFS must not already be a copy forward (`IsCopyFwd` check)
- The action must be configured in `RFS_STATUS_RFS_ACTION_XREF` for the status/request type

### Diagnostic SQL

```sql
-- Check request type CopyForward setting
SELECT rt.REQ_TYPE_CODE, rt.IS_ALLOW_COPY_FWD
FROM CD_REQ_TYPE rt
WHERE rt.REQ_TYPE_CODE = @ReqTypeCode;

-- Check action configuration for DEN status
SELECT xa.RFS_STATUS_CODE, xa.REQ_TYPE_CODE, xa.RFS_ACTN_CODE,
       xa.IS_EXT_HIDDEN, xa.BUTTON_SEQ_NO
FROM RFS_STATUS_RFS_ACTION_XREF xa
WHERE xa.RFS_STATUS_CODE = 'DEN' AND xa.RFS_ACTN_CODE = 'CPY'
  AND xa.TSP_NO = @TspNo;

-- Check if RFS is already a copy forward
SELECT h.TSP_NO, h.RFS_NO, h.RFS_STATUS_CODE, h.IS_COPY_FWD, h.ORIG_RFS_NO
FROM RFS_HEADER h
WHERE h.TSP_NO = @TspNo AND h.RFS_NO = @RfsNo;
```

### Code Location
- **Workflow check**: `RFSWorkflow.GetActiveActions()` (RFSWorkflow.cs line ~215)
- **Copy Forward action**: `QPTMRFSService.UpdateOrigRFSToCPY()` (line ~1303)
- **Wizard option**: `RFSWizardV2Controller.DoGetWizardOptions()` (line ~171)

### Resolution
1. Verify `IS_ALLOW_COPY_FWD = 1` on the request type
2. Verify CPY action exists in `RFS_STATUS_RFS_ACTION_XREF` for DEN status
3. Check if the user is external and the action has `IS_EXT_HIDDEN = 1`
4. If the RFS was already copied, the original status changes to COP

---

## Issue 8: Approval Notifications Not Sent

### Symptoms
- Approval decision submitted but next department not notified
- Email notifications not generated after approve/reject

### Root Cause
Notification logic checks:
- All current and prior-level approvals must be complete (no PEN records at or below the current order)
- For approvals: next sequential email (`IsSeqEmail`) departments are notified
- For rejections: rejection email (`IsRejectEmail`) recipients are notified

### Diagnostic SQL

```sql
-- Check approval department configuration
SELECT ac.TSP_NO, ac.REQ_TYPE_CODE, ac.TOS_CODE, ac.APPR_DEPT_CODE,
       ac.SEQ_NO, ac.IS_SEQ_EMAIL, ac.IS_REJECT_EMAIL
FROM RFS_APPROVAL_CONFIG_XREF ac
WHERE ac.TSP_NO = @TspNo AND ac.REQ_TYPE_CODE = @ReqTypeCode
ORDER BY ac.SEQ_NO;

-- Check current approval status
SELECT a.APPR_DEPT_CODE, a.APPR_ACTN_CODE, a.ORDER_NO,
       a.IS_SEQ_EMAIL, a.IS_REJECT_EMAIL
FROM RFS_APPROVAL a
WHERE a.TSP_NO = @TspNo AND a.RFS_NO = @RfsNo
ORDER BY a.ORDER_NO;

-- Check event log for notification events
SELECT el.*
FROM EVENT_LOG el
WHERE el.EVENT_TYPE_CD = 'K_RFS_APPR'
ORDER BY el.CREATE_DATE DESC;
```

### Code Location
- **Notification logic**: `QPTMRFSService.SubmitRFSApproval()` (line ~975, specifically ~1009-1041)
- **Send notification**: `QPTMRFSService.SendApprovalNotification()` (line ~1751)
- **Event context**: `QPTMRFSApprovalEventDetectorContext`

### Resolution
1. Check that `IS_SEQ_EMAIL = 1` on the next department's config
2. Verify all prior-level approvals are complete (no PEN at order <= current)
3. For rejection, check `IS_REJECT_EMAIL = 1` on the recipient departments
4. Check the event log for `K_RFS_APPR` events
5. Verify email configuration and event handler setup

---

## Issue 9: Multiple TOC Rates Found for Location

### Symptoms
- Error: "For {CtrNo} multiple applicable rates were found for {Loc1} to {Loc2}"
- Rate resolution fails for a specific path

### Root Cause
When `RFS_GET_K_INFO_METHOD = UseFirstDateMDQ`, the system retrieves rates from the first day of the range. If multiple TOCs apply to the same path for the same security object (LOCATIONS, LOCATIONS_FUEL, or LOCATIONS_OVERRUN), an error is thrown because only one TOC per path per category is allowed.

### Diagnostic SQL

```sql
-- Check TOCs that apply to the path
SELECT r.RATE_HDR_ID, r.TOC_CODE, r.LOC_ID_1, r.LOC_ID_2,
       r.RATE_TYPE_CODE, r.RATE_AMT, r.EFF_DATE_FROM, r.EFF_DATE_TO
FROM RATE r
WHERE r.TSP_NO = @TspNo
  AND (r.LOC_ID_1 = @LocId1 OR r.LOC_GRP_ID_1 = @LocGrpId1)
  AND (r.LOC_ID_2 = @LocId2 OR r.LOC_GRP_ID_2 = @LocGrpId2)
  AND r.EFF_DATE_FROM <= @EffDateFrom AND r.EFF_DATE_TO >= @EffDateFrom;

-- Check TOC process xref for applicable TOCs
SELECT rtpx.ID_PROCESS, rtpx.TOC_CODE
FROM RATE_TOC_PROCESS_XREF rtpx
WHERE rtpx.TSP_NO = @TspNo AND rtpx.TOS_CODE = @TosCode
  AND rtpx.ID_PROCESS = 'QVPSOAREQUESTFORSERVICE_LOCATIONS';
```

### Code Location
- **Multiple rate check**: `QPTMRFSService.ResolveRate()` (line ~2835)
- **Error message construction**: Lines ~2706-2708, thrown at ~2849

### Resolution
1. Identify which rate records are conflicting using the SQL above
2. One rate per path per security object category must apply
3. Adjust rate setup to ensure only one TOC matches each path
4. The error message includes the conflicting rate header IDs

---

## Issue 10: Present Value Calculation Incorrect

### Symptoms
- Present value on Long-Term Bid Viewer shows unexpected numbers
- Present value is null when expected to have a value

### Root Cause
Present value calculation uses:
- `RFSCalcHelper.GetRFSPresentValues(tariffMax, reqRate, effDateFrom, effDateTo, annualRate, calcType)`
- Annual interest rate from TSP configuration (`INTEREST_RATE`)
- Calculation type from `RfsPresentValueCalcType` config

### Diagnostic SQL

```sql
-- Check interest rate configuration
SELECT tc.TSP_NO, tc.KEY_CATEGORY, tc.KEY_NM, tc.KEY_VALUE
FROM TSP_CONFIGURATION_CONTROL tc
WHERE tc.TSP_NO = @TspNo AND tc.KEY_CATEGORY = 'TSP' AND tc.KEY_NM = 'INTEREST_RATE';

-- Check present value calc type
SELECT gc.KEY_NM, gc.KEY_VALUE
FROM GLOBAL_CONFIGURATION_CONTROL gc
WHERE gc.KEY_NM = 'RfsPresentValueCalcType';

-- Check RFS location present values
SELECT l.TSP_NO, l.RFS_NO, l.ID_RFS_LOC, l.PRESENT_VALUE,
       l.TARIFF_MAX, l.REQ_RATE, l.EFF_DATE_FROM, l.EFF_DATE_TO
FROM RFS_LOCATION l
WHERE l.TSP_NO = @TspNo AND l.RFS_NO = @RfsNo;
```

### Code Location
- **Calculation**: `RFSCalcHelper.GetRFSPresentValues()` (utility class)
- **Header-level**: `RFSHeaderDO.GetRFSPresentValues()` (RFSHeaderDOExt.cs)
- **Bid viewer**: `QPTMRFSService.SetMaxTariffRate()` (line ~1875)

### Resolution
1. Verify `INTEREST_RATE` is configured for the TSP (non-null, reasonable value)
2. Check that the request type has `IS_CALC_PRESENT_VALUE = 1`
3. Verify tariff max is populated (rate resolution must have succeeded)
4. Check the calc type configuration
5. Compare manual calculation with formula parameters

---

## Issue 11: RFS Wizard Tabs Missing or Wrong Order

### Symptoms
- Expected tabs not visible in the RFS wizard
- Tabs appear in unexpected order
- Tab shows for one TOS but not another

### Root Cause
Tab visibility and order are controlled by:
- `TYPE_OF_SERVICE_RFS_TAB` configuration per TSP + TOS
- `IsTabTrue` flag determines visibility
- `OrderNo` determines display order
- `IsMandatory` on `RFS_TAB` determines if tab must always show

### Diagnostic SQL

```sql
-- Check tab configuration for specific TOS
SELECT t.TSP_NO, t.TOS_CODE, t.RFS_TAB_CODE, t.IS_TAB_TRUE, t.ORDER_NO
FROM TYPE_OF_SERVICE_RFS_TAB t
WHERE t.TSP_NO = @TspNo AND t.TOS_CODE = @TosCode
ORDER BY t.ORDER_NO;

-- Check mandatory tabs
SELECT rt.CODE, rt.IS_MANDATORY
FROM RFS_TAB rt;

-- Check all TOS tab configurations for TSP
SELECT t.TSP_NO, t.TOS_CODE, t.RFS_TAB_CODE, t.IS_TAB_TRUE, t.ORDER_NO
FROM TYPE_OF_SERVICE_RFS_TAB t
WHERE t.TSP_NO = @TspNo
ORDER BY t.TOS_CODE, t.ORDER_NO;
```

### Code Location
- **Tab settings**: `QPTMRFSService.GetRFSTabSettings()` (line ~250)
- **Wizard tab order**: `RFSWizardV2Controller.DoGetSelectedWizardOptionUIDef()` (line ~47)
- **Tab state order**: `Constants.RFSState.GetAllStates()` with `uic.GetStateOrder()`

### Resolution
1. Check `TYPE_OF_SERVICE_RFS_TAB` for the specific TSP + TOS combination
2. Verify `IS_TAB_TRUE = 1` for the expected tab
3. Check `ORDER_NO` for correct sequencing
4. Mandatory tabs should always appear regardless of TOS config

---

## Issue 12: Award Stuck in Processing State

### Symptoms
- RFS shows `IsProcessing = true`
- Award action returns "RFS award is in progress" message
- Unable to approve or award the RFS

### Root Cause
The `IsProcessing` flag is set during the award process. If the KRFSTOCTR process queue item fails or hangs, the flag may not be cleared.

### Diagnostic SQL

```sql
-- Check IsProcessing flag
SELECT h.TSP_NO, h.RFS_NO, h.IS_PROCESSING, h.RFS_STATUS_CODE, h.UPDATE_DATE
FROM RFS_HEADER h
WHERE h.TSP_NO = @TspNo AND h.RFS_NO = @RfsNo;

-- Check process queue status
SELECT pq.PQID, pq.TSP_NO, pq.PROCESS_TYPE, pq.STATUS,
       pq.CREATE_DATE, pq.START_DATE, pq.END_DATE, pq.ERROR_MSG
FROM PROCESS_QUEUE pq
WHERE pq.TSP_NO = @TspNo AND pq.PROCESS_TYPE = 'KRFSTOCTR'
ORDER BY pq.CREATE_DATE DESC;
```

### Code Location
- **Processing check**: `RFSApprovalController.IsRFSUpdatable()` (line ~261)
- **Award trigger**: `RFSApprovalController.DoAwardRFS()` (line ~370)
- **Post-award**: `RFSApprovalController.DoPostAwardRFS()` (line ~391)

### Resolution
1. Check the process queue for the KRFSTOCTR entry
2. If the process queue item failed, investigate the error message
3. If stuck, manually reset `IS_PROCESSING = 0` on the RFS header (with caution)
4. Retry the award after clearing the processing flag

---

## Issue 13: Auto-Approval Not Working for Internal Users

### Symptoms
- Internal user submits RFS but approval departments are not auto-approved
- All departments show PEN (Pending) status

### Root Cause
Auto-approval requires:
- Global config `RFS_AUTO_APPROVE_SEC_USER` must be enabled
- User must be internal
- User must be a member of the approval department via `PA_APPROVAL_DEPT_USER_XREF`

### Diagnostic SQL

```sql
-- Check auto-approve global config
SELECT gc.KEY_NM, gc.KEY_VALUE
FROM GLOBAL_CONFIGURATION_CONTROL gc
WHERE gc.KEY_NM = 'RFS_AUTO_APPROVE_SEC_USER';

-- Check if user is in approval departments
SELECT adux.APPR_DEPT_CODE, adux.ID_SEC_USER, adux.IS_PROXY
FROM PA_APPROVAL_DEPT_USER_XREF adux
WHERE adux.TSP_NO = @TspNo AND adux.ID_SEC_USER = @UserId;

-- Check user internal flag
SELECT u.ID_SEC_USER, u.IS_INTERNAL
FROM SECURITY_USER u
WHERE u.ID_SEC_USER = @UserId;
```

### Code Location
- **Auto-approval logic**: `QPTMRFSService.GetApprovalRecords()` (line ~1456, specifically ~1497-1528)
- **Config check**: `GlobalConfigsAccess.RFSAutoApproveSecUser`

### Resolution
1. Verify `RFS_AUTO_APPROVE_SEC_USER` global config is set to true/1
2. Verify the user is marked as internal in `SECURITY_USER`
3. Verify the user is in `PA_APPROVAL_DEPT_USER_XREF` for the relevant departments
4. Auto-approval only covers departments the user belongs to; higher-sequence departments remain PEN
5. The `nextToNotifySeqNo` advances past auto-approved departments

---

## Issue 14: Contract Data Not Copying to RFS

### Symptoms
- "Get Contract Info" returns empty or partial data
- Error: "Contract {CtrNo} does not exist on this date"
- Error: "Contract {CtrNo} is not effective from {date} to {date}"
- Locations or rates not populated after contract data copy

### Root Cause
Contract data copy (`GetRFSContractFromCtr`) requires:
- Contract must be effective on the RFS start date
- Request type code must be provided
- For Termination (TRM): uses special `CopyCtrDataTRM` method
- Inactive locations optionally filtered by global config

### Diagnostic SQL

```sql
-- Check contract effectiveness
SELECT c.TSP_NO, c.CTR_NO, c.EFF_DATE_FROM, c.EFF_DATE_TO,
       c.BP_NO, c.TOS_CODE, c.CTR_STATUS_CODE
FROM CONTRACT c
WHERE c.TSP_NO = @TspNo AND c.CTR_NO = @CtrNo
  AND c.EFF_DATE_FROM <= @RfsEffDateFrom
  AND c.EFF_DATE_TO >= @RfsEffDateFrom;

-- Check contract locations
SELECT cl.CTR_NO, cl.LOC_ID_1, cl.LOC_ID_2, cl.EFF_DATE_FROM, cl.EFF_DATE_TO
FROM CONTRACT_LOCATION cl
WHERE cl.TSP_NO = @TspNo AND cl.CTR_NO = @CtrNo;

-- Check inactive location filter config
SELECT gc.KEY_VALUE
FROM GLOBAL_CONFIGURATION_CONTROL gc
WHERE gc.KEY_CATEGORY = 'CONTRACTS'
  AND gc.KEY_NM = 'RFS_COPY_INACTIVE_LOCATIONS_TO_NEW_REQUEST';
```

### Code Location
- **Contract data copy**: `QPTMRFSService.GetRFSContractFromCtr()` (line ~1330)
- **TRM copy**: `RFSHeaderDO.CopyCtrDataTRM()` (RFSHeaderDOExt.cs line ~35)
- **General copy**: `RFSHeaderDO.CopyCtrData()` (RFSHeaderDOExt.cs line ~169)
- **Inactive location filter**: `QPTMRFSService.RemovePathsWithInactiveLocations()` (line ~2415)
- **Contract validation**: `QPTMRFSService.ValidateContractEffective()` (service internal)

### Resolution
1. Verify the contract exists and is effective on the RFS effective start date
2. Check that Request Type Code is provided (not null/empty)
3. For TRM requests, ensure single contract record is used
4. Check `RFS_COPY_INACTIVE_LOCATIONS_TO_NEW_REQUEST` config -- if 0, inactive locations are removed
5. Check for errors logged to the RFS header via `AddErrorMsg("RFSServiceException", ...)`

---

## Related Documentation

- [Domain Documentation](./domain.md) - Business concepts and workflows
- [Architecture Documentation](./architecture.md) - Technical implementation details

---

*Last updated: 2026-03-03*

*Document version: 1.0*
