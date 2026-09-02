---
title: Request For Service (RFS) - Domain Concepts
category: domain
feature: Request For Service (RFS)
related_repos: Web, Batch
keywords: RFS, request for service, contract, award, submit, approve, deny, withdraw, copy forward, resubmit, capacity, TOS, type of service, PAL, park and lend, evergreen, long-term bid, approval queue, wizard
last_updated: 2026-03-03
---

# Request For Service (RFS) - Domain Concepts

## Overview

This document explains the **business concepts** behind Request For Service (RFS) in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [RFS Lifecycle](#rfs-lifecycle)
3. [Request Types](#request-types)
4. [RFS Actions and State Machine](#rfs-actions-and-state-machine)
5. [RFS Status Codes](#rfs-status-codes)
6. [Approval Workflow](#approval-workflow)
7. [RFS-to-Contract Conversion (Award)](#rfs-to-contract-conversion-award)
8. [RFS Wizard Modes](#rfs-wizard-modes)
9. [RFS Tabs and Data Sections](#rfs-tabs-and-data-sections)
10. [Capacity Request Types and Quantities](#capacity-request-types-and-quantities)
11. [Rate Resolution](#rate-resolution)
12. [Long-Term Bid Viewer](#long-term-bid-viewer)
13. [Evergreen Contracts](#evergreen-contracts)
14. [Security and Authorization](#security-and-authorization)
15. [Key Business Rules](#key-business-rules)
16. [Glossary](#glossary)
17. [Related Documentation](#related-documentation)

---

## System Overview

### What is Request For Service (RFS)?

**Request For Service (RFS)** is the mechanism within QPTM through which shippers (Business Partners) request new pipeline transportation service or amendments to existing contracts. An RFS captures the service details -- capacity, locations, rates, dates, and type of service -- and routes them through an approval workflow before ultimately being awarded and converted into a contract.

**Business Purpose:**
- Enable shippers to request new transportation service contracts
- Support amendments to existing contracts (quantity changes, date extensions, rate modifications)
- Manage termination requests for existing contracts
- Enforce multi-department approval workflows
- Convert approved RFS requests into executable contracts
- Track the full lifecycle from initial request through award
- Support competitive bidding for long-term unsold capacity

### Key Business Value

- **Standardized Intake**: Provides a structured process for all service requests
- **Approval Governance**: Multi-department approval ensures proper review before contract creation
- **Regulatory Compliance**: Supports FERC requirements for capacity request handling
- **Audit Trail**: Complete history of request, approval, and award actions
- **Rate Validation**: Automatic tariff rate resolution and validation
- **Capacity Management**: Tracks unsold capacity across locations, zones, and facilities

---

## RFS Lifecycle

### End-to-End Flow

The RFS lifecycle follows a defined sequence from initial request through contract creation:

```
RFS Lifecycle:

1. Request Creation
   +-- Shipper or internal user initiates a new RFS
   +-- Selects request type (New, Amendment, Termination, etc.)
   +-- System assigns RFS Number (auto-generated sequence)
   +-- Initial status: PND (Pending)

2. Data Entry
   +-- General tab: BP, TOS, dates, facility, quantities
   +-- Locations tab: Receipt/delivery points, MDQ quantities
   +-- Rates tab: Header-level and location-level rates
   +-- Text tab: Contract clauses (pre-approved and custom)
   +-- Contacts tab: Contact information for the request
   +-- PAL tab: Park and Lend specifics (if applicable)
   +-- Injection/Withdrawal tab: Storage period details

3. Validation
   +-- Mandatory rules checked on every save (FK rules, required fields)
   +-- Full validation on Submit/Award (line rules, business rules)
   +-- Status transitions: PND -> PIN (if invalid) or PND -> VLD (if valid)

4. Submit
   +-- RFS submitted for approval (status: APR)
   +-- Approval records generated based on TSP configuration
   +-- Notifications sent to first-in-sequence approval departments
   +-- Submit timestamp recorded

5. Approval
   +-- Each configured department reviews and approves/rejects
   +-- Sequential processing based on department order number
   +-- Notifications advance to next department upon approval
   +-- If any department rejects, notification sent to reject-email list

6. Award (Contract Conversion)
   +-- Once all approvals complete, RFS can be awarded
   +-- System validates RFS data one final time
   +-- Award action (CTR) triggers conversion to contract
   +-- Contract created with data from the RFS
   +-- RFS status: CRE (Created/Awarded)

7. Post-Award
   +-- Contract available in contract maintenance
   +-- RFS record preserved for audit trail
   +-- Denied RFS may be copied forward for resubmission
```

### State Transitions Summary

```
PND (Pending) --[Save/Update]--> PND
PND --[Validate, valid]--> VLD (Pending Valid)
PND --[Validate, invalid]--> PIN (Pending Invalid)
PND/VLD/PIN --[Submit]--> APR (Submitted)
APR --[All departments approve + Award]--> CRE (Created/Awarded)
APR --[Award fails validation]--> AWI (Award Invalid)
APR --[Deny]--> DEN (Denied)
APR --[Withdraw]--> WTD (Withdrawn)
DEN --[Copy Forward]--> COP (Copy Forward) --> new PND RFS
APR --[Resubmit]--> APR (Re-submitted, for Long-Term Unsold)
AWI --[Resubmit]--> APR
```

---

## Request Types

Request types are configured per TSP and stored in the `CD_REQ_TYPE` table. Each request type defines key behavioral attributes.

### Common Request Types

| Code | Description | IsNewService | IsCalcPresentValue | IsAllowCopyFwd | IsShowReqQueue |
|------|-------------|:------------:|:------------------:|:--------------:|:--------------:|
| C1   | New Contract | Yes | No | Yes | Yes |
| AM   | Amendment | No | No | Yes | Yes |
| TRM  | Termination | No | No | No | Yes |
| NLT  | Long-Term Unsold Bid | No | Yes | No | Yes |
| PAM  | PAL Amendment | No | No | Yes | Yes |

### Request Type Attributes

- **IsNewService**: When true, the request creates a brand new contract (no existing CtrNo). Security checks use BP association rather than contract-level authorization.
- **IsCalcPresentValue**: When true, present value calculations are performed for rate bidding (used in Long-Term Unsold Bid scenarios).
- **IsAllowCopyFwd**: When true, a denied RFS can be copied forward to create a new request with the same data.
- **IsLifeOfCtr**: When true, the request covers the entire remaining life of the contract.
- **IsSegment**: Indicates whether the request is for a segment of a contract.
- **IsAllowIntradayReq**: When true, intraday request cycles are available.
- **IsShowReqQueue**: When true, the request type appears in the RFS approval queue.
- **AuctionCtgryCode**: Links to auction category for competitive bidding scenarios.

---

## RFS Actions and State Machine

### Action Types (RFSActionType Enum)

The RFS screen supports the following actions, each mapped to a specific workflow transition:

| Code | Enum Value | Action | Description |
|------|:----------:|--------|-------------|
| DNY  | 0 | Deny | Reject the RFS request |
| UPD  | 1 | Update | Save/add changes to the RFS |
| VLD  | 2 | Validate | Validate RFS data without saving |
| SUB  | 3 | Submit | Submit RFS for approval |
| CPY  | 4 | Copy Forward | Create new RFS from denied RFS |
| CTR  | 6 | Award | Convert RFS to contract |
| WTH  | 7 | Withdraw | Withdraw the submitted RFS |
| RES  | 8 | Resubmit | Resubmit (Long-Term Unsold) |
| SVO  | 9 | Service Order Preview | Preview the resulting service order |
| CNT  | 10 | Continue | Continue button in web wizard |

### Action Configuration

Actions are configured per TSP through the `RFS_STATUS_RFS_ACTION_XREF` table, which maps:
- **Status + Request Type + Action** to determine which buttons are visible
- **IsExtHidden**: Whether the action is hidden from external users
- **ButtonSeqNo**: Button display order

### Workflow Matrix

The workflow is a 4-dimensional matrix:
1. **Request Type** (Non-LT vs Long-Term)
2. **User Type** (Internal vs External)
3. **Current RFS Status**
4. **Available Actions**

For example, when status is "Submitted" (APR):
- **Internal users**: Update, Award, Withdraw, Deny (Non-LT) or Update, Award, Resubmit, Deny (Long-Term)
- **External users**: Withdraw only (Non-LT) or Resubmit only (Long-Term)

---

## RFS Status Codes

| Code | Constant Name | Description | IsActive |
|------|---------------|-------------|:--------:|
| PND  | Pending | Initial state, data entry in progress | Yes |
| PIN  | PendingInvalid | Validation failed | Yes |
| VLD  | PendingValid | Validation passed | Yes |
| APR  | Submitted | Submitted for approval | Yes |
| DEN  | Denied | Rejected by approver | No* |
| CRE  | Created | Awarded / converted to contract | No |
| AWI  | AwardInvalid | Award validation failed | Yes |
| COP  | CopyForward | Original RFS that was copied forward | No |
| WTD  | Withdrawn | Withdrawn by requestor | No |

*Denied with Copy Forward checked (`IsCopyFwd = true`) is treated as active for queue display purposes.

---

## Approval Workflow

### Multi-Department Approval

RFS approval is configured per TSP through the `RFS_APPROVAL_CONFIG_XREF` table:

1. **Approval Departments**: Each TSP configures which departments must approve requests
2. **Sequence Order (SeqNo)**: Determines the sequential order of approval
3. **Department Users**: `PA_APPROVAL_DEPT_USER_XREF` maps security users to departments
4. **Email Notifications**: `IsSeqEmail` and `IsRejectEmail` control when notifications are sent

### Approval Flow

```
RFS Submitted (APR)
  |
  v
Department 1 (lowest SeqNo)
  |-- Approve --> Notify Department 2
  |-- Reject  --> Notify reject-email list, RFS stays APR
  |
Department 2 (next SeqNo)
  |-- Approve --> Notify Department 3 (if exists)
  |-- Reject  --> Notify reject-email list
  |
  ...
  |
All Departments Approved
  |
  v
Ready for Award (CTR action)
```

### Approval Action Codes

| Code | Description |
|------|-------------|
| PEN  | Pending (not yet reviewed) |
| APR  | Approved |
| REJ  | Rejected |

### Auto-Approval

When the global configuration `RFS_AUTO_APPROVE_SEC_USER` is enabled and the submitting user is an internal user who belongs to one or more approval departments, those departments are automatically approved at submit time.

### Proxy Approval

Approval departments support proxy users who can approve on behalf of the primary user. The `MarkApprovalsWithProxyInd` method identifies proxy approvals at save time.

---

## RFS-to-Contract Conversion (Award)

### Award Process

The Award action (RFSActionType.CTR) converts an approved RFS into a contract:

1. **Pre-Award Validation**: Full validation executed with action code "CTR"
2. **Security Check**: Verifies user has privileges for the award action via `IsActionAllowed`
3. **Status Update**: On success, RFS status set to the action's configured success status
4. **Contract Creation**: The award process triggers the `KRFSTOCTR` process queue item
5. **Post-Award**: `DoPostAwardRFS` completes contract setup after async processing

### Data Copied to Contract

- Business Partner (BpNo)
- Type of Service (TosCode)
- Effective dates
- Locations with MDQ quantities
- Negotiated rates
- Contract text (pre-approved and custom)
- Evergreen attributes
- Contact information
- Facility assignments

### Award from Approval Queue

The `RFSApprovalController` supports awarding directly from the approval screen:
- `DoAwardRFS`: Triggers the award action
- `DoAutoApproval`: Approves and awards in a single operation when auto-award is configured
- `DoPostAwardRFS`: Handles post-award processing with the process queue ID

---

## RFS Wizard Modes

The web-based RFS Wizard (V2) supports four modes of operation:

| Mode | Constant | Description |
|------|----------|-------------|
| New | `NEW` | Create a new contract request (IsNewService = true) |
| Amend | `AMEND` | Amend an existing contract |
| Query | `QUERY` | View/query an existing RFS |
| Copy Forward | `COPYFORWARD` | Create new RFS from a denied request |

The wizard navigates through tabs in a configurable order based on the TSP and Type of Service configuration.

---

## RFS Tabs and Data Sections

### Configurable Tabs

Each RFS consists of multiple tabs/sections, configurable per TSP and Type of Service:

| Tab Code | Name | Description |
|----------|------|-------------|
| QRY | Query | RFS search/query interface |
| START | Start | Initial wizard selection |
| GEN | General | Core request data: BP, TOS, dates, quantities |
| EVG | Evergreen | Evergreen contract attributes and termination details |
| QRT | Quantity/Rates | Header-level rate information |
| LOC | Locations | Receipt/delivery point pairs with path-level MDQ and rates |
| DIS | Alternate Points | Discount/negotiated rates for alternate delivery points |
| CON | Contacts | Contact information for the request |
| TXT | Text | Contract text clauses (pre-approved and new) |
| PAL | PAL | Park and Lend action dates and quantities |
| INJ | Injection/Withdrawal | Storage injection/withdrawal period details |
| UNC | Unsold Capacity | Location, zone, and facility unsold capacity views |
| APR | Approval | Approval department status and actions |
| ERR | Errors | Validation error display |
| SUM | Summary | Request summary for review |

### Tab Visibility

Tab visibility is controlled by:
- `TYPE_OF_SERVICE_RFS_TAB` configuration table
- `IsTabTrue` flag per TOS + Tab combination
- `OrderNo` determines tab display order
- `IsMandatory` flag on the `RFS_TAB` table

---

## Capacity Request Types and Quantities

### Quantity Fields on RFS Header

| Field | Description |
|-------|-------------|
| OvrdRfsMdq | Override MDQ (Maximum Daily Quantity) |
| MsqQty | Maximum Storage Quantity |
| MsqQtyMin | Minimum Storage Quantity |
| MdiqFixedQty | Maximum Daily Injection Quantity (Fixed) |
| MdwqFixedQty | Maximum Daily Withdrawal Quantity (Fixed) |

Each quantity has a "Current" counterpart (CurrOvrdRfsMdq, CurrMsqQty, etc.) representing the current contract values. The difference between current and requested values indicates a capacity change request.

### Capacity Change Detection

The `IsCapacityChangeRequested()` method on `RFSHeaderDO` detects changes by comparing current vs. requested quantities at both the header and location level. This determines whether capacity-change-specific approval departments need to be involved.

### Location-Level Quantities

Each `RFSLocationDO` contains:
- **FixedMdqQty**: Requested fixed MDQ for the path
- **CurrFixedMdq**: Current contract MDQ for the path
- **ReqChangeFixedMdq**: Requested change amount
- **MdqTypeCode**: Fixed (FIX) or Not Applicable (NA)
- **CapTypeCode**: Capacity type (PP = Primary Point)
- **IsIncludeMdq**: Whether to include in MDQ calculations

---

## Rate Resolution

### Rate Calculation Process

The `ResolveRate` method on `QPTMRFSService` resolves tariff and billed rates for all RFS data:

1. **Header Rates**: Resolved by Type of Charge (TOC) for the GENERAL security object
2. **Location Rates**: Resolved per path using LOCATIONS, LOCATIONS_FUEL, and LOCATIONS_OVERRUN security objects
3. **Discount Rates**: Resolved for the DISCRATE security object
4. **PAL Rates**: Resolved for the PAL1 security object

### Rate Types

| Rate Type Code | Description |
|----------------|-------------|
| MAXT | Maximum Tariff Rate |
| MINT | Minimum Tariff Rate |
| BLLD | Billed Rate |
| DIS | Discount Rate |
| NEG | Negotiated Rate |

### Price Types

| Code | Description |
|------|-------------|
| FIX | Fixed price |
| FRM | Formula-based price |
| PCT | Percentage-based price |

### Present Value Calculations

For Long-Term Unsold Bid requests (`IsCalcPresentValue = true`), the system calculates net present value using:
- `RFSCalcHelper.GetRFSPresentValues(tariffMax, reqRate, effDateFrom, effDateTo, annualRate, calcType)`
- Annual interest rate from TSP configuration (`INTEREST_RATE`)
- Calculation type from TSP/global configuration

---

## Long-Term Bid Viewer

The Long-Term Bid Viewer displays competitive bids for long-term unsold capacity:

- **Filters**: Only shows bids with present values, request type NLT, status Submitted (APR)
- **Competing Bids**: Linked through `K_TRAN_RFS_COMPETE_BIDS` by CompeteId
- **Security**: External users only see bids for their authorized BPs/contracts
- **Update**: Users can modify requested rates and end dates, triggering present value recalculation
- **Compete Round End Time**: Tracks auction timing for competitive rounds

---

## Evergreen Contracts

Evergreen contracts have special handling in RFS:

- **Open End Date**: Uses 9000-12-31 as the effective end date
- **IsEvg Flag**: Set based on the EVG contract attribute
- **Termination Fields**: EvergreenClause, PrimaryTerminationNotice, TerminationDate, TerminationNotice, RenegotiationDate
- **CtrEffDateFrom**: Stores the termination date for evergreen contracts
- **Date Handling**: When IsEvg is true, effective date changes update CtrEffDateFrom instead of EffDateTo

---

## Security and Authorization

### User Authorization for RFS

Authorization differs based on request type:

**New Service Requests (IsNewService = true):**
- User must be associated to the BP on the RFS header, OR
- User must be associated to the default Contracting agent for that BP

**Existing Contract Requests (IsNewService = false):**
- User must be associated to the BP on the contract, OR
- User must be associated to the contract-level Contracting agent

### Internal vs. External Users

- **Internal Users**: Can see all RFS requests for their authorized TSPs
- **External Users**: Can only see RFS requests where they have BP or agent association
- **Widget Filtering**: Even internal users are filtered by BP for widget displays (`bFilterByBPForInternalUser`)

---

## Key Business Rules

### General Rules

1. **RFS Number Assignment**: Auto-generated per TSP from the `RFS_NO` sequence
2. **Effective Date Range**: EffDateFrom must be less than or equal to EffDateTo
3. **Contract Validation**: For amendments, the referenced contract must be effective on the requested start date
4. **Type of Service**: Must be valid for the TSP and effective date range
5. **Business Partner**: Must be a valid, active business associate

### Submit Rules

1. **Submit Timestamp**: Set to server time on first submit; preserved on subsequent saves
2. **Approval Records**: Generated at submit time based on TSP approval configuration
3. **Cycle Validation**: The first open cycle must be valid for the gas day and request type
4. **Full Validation**: All mandatory and non-mandatory rules must pass

### Award Rules

1. **All Approvals Required**: All configured departments must have approved status before award
2. **Security Privilege**: User must have Execute permission on the award security object
3. **Validation**: Full re-validation with action code CTR before award
4. **Inactive Locations**: Optionally filtered based on `RFS_COPY_INACTIVE_LOCATIONS_TO_NEW_REQUEST` configuration

### Copy Forward Rules

1. **Only from Denied**: Copy Forward only available when status is DEN and `IsAllowCopyFwd` is true on the request type
2. **Original RFS Update**: The original RFS status is set to the CPY action's success status
3. **New RFS Created**: A new RFS is created with the same data and a new RFS number

---

## Glossary

| Term | Definition |
|------|------------|
| **RFS** | Request For Service - a formal request to create or modify a pipeline transportation contract |
| **RFS Number (RfsNo)** | Unique identifier for each RFS, auto-generated per TSP |
| **TSP (TspNo)** | Transportation Service Provider - the pipeline company |
| **BP (BpNo)** | Business Partner - the shipper or customer requesting service |
| **TOS (TosCode)** | Type of Service - defines the service category (Firm, Interruptible, PAL, etc.) |
| **TOC (TocCode)** | Type of Charge - defines the charge category for rate resolution |
| **MDQ** | Maximum Daily Quantity - the maximum amount of gas per day |
| **MSQ** | Maximum Storage Quantity - the maximum amount in storage |
| **MDIQ** | Maximum Daily Injection Quantity |
| **MDWQ** | Maximum Daily Withdrawal Quantity |
| **PAL** | Park and Lend - a storage service where gas is parked or lent |
| **Evergreen** | A contract that auto-renews unless terminated with notice |
| **Award** | The act of converting an approved RFS into a contract |
| **Tariff Max/Min** | Maximum and minimum rates from the published tariff schedule |
| **Present Value** | Net present value of rate differentials, used in long-term bid evaluation |
| **Approval Department** | A configured group of users who must review and approve RFS requests |
| **Copy Forward** | Creating a new RFS from a previously denied request |
| **Contract Agent** | A business partner authorized to act on behalf of another BP for contract matters |

---

## Related Documentation

- [Architecture Documentation](./architecture.md) - Technical implementation details
- [Troubleshooting Guide](./troubleshooting.md) - Known issues and resolution steps

---

*Last updated: 2026-03-03*

*Document version: 1.0*
