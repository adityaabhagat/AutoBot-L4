---
title: Capacity Release (CR) - Architecture
category: architecture
feature: Capacity Release (CR)
related_repos: Web, Batch
keywords: CR, architecture, code structure, services, controllers, validation, data objects, database tables, batch processes, wizard, API
last_updated: 2026-03-03
---

# Capacity Release (CR) - Architecture

## Overview

This document explains the **technical architecture** of the Capacity Release (CR) system in QPTM. It covers code structure, service layer design, controller and wizard implementations, validation rules, database schema, batch processes, and integration patterns.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Service Layer](#service-layer)
3. [Web Application Layer - Controllers and Wizards](#web-application-layer---controllers-and-wizards)
4. [API Layer](#api-layer)
5. [Validation Layer](#validation-layer)
6. [Data Model](#data-model)
7. [Database Schema](#database-schema)
8. [Batch Processes](#batch-processes)
9. [Caching](#caching)
10. [Integration Points](#integration-points)
11. [Key Processing Flows](#key-processing-flows)

---

## System Architecture

### Architectural Layers

```
+-------------------------------------------------------------+
|                    WEB APPLICATION LAYER                      |
|  +------------------+  +------------------+  +-------------+ |
|  | OfferWizardV2    |  | BidWizardV2      |  | CRAward     | |
|  | Controller       |  | Controller       |  | Controller  | |
|  | (12 states)      |  | (6 states)       |  |             | |
|  +--------+---------+  +--------+---------+  +------+------+ |
+-----------|----------------------|--------------------+-------+
            |                      |                    |
            v                      v                    v
+-------------------------------------------------------------+
|                      API LAYER                                |
|  +----------------------------------------------------------+|
|  | CapacityReleaseController (/api/v1.0/CapacityRelease)    ||
|  | GET /Awards, GET /Awards/Summary, GET /Awards/{tsp}/...  ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|                      SERVICE LAYER                            |
|  +----------------------------------------------------------+|
|  |    QPTMCapacityReleaseService.cs (~230KB)                ||
|  |    - Offer ops: SaveOffer, ValidateOffer, SubmitOffer,   ||
|  |      WithdrawOffer, QueryOffer, PrepareOffer             ||
|  |    - Bid ops: SaveBid, ValidateBid, SubmitBid,           ||
|  |      WithdrawBid                                          ||
|  |    - Award ops: ValidateAward, SaveAward, GetAward       ||
|  |    - Helpers: AddOfferApprovals, HandleBatchResult        ||
|  +--------+-------------------------------------------------+|
|  +----------------------------------------------------------+|
|  |  QPTMCapacityReleaseWidgetService                        ||
|  |    - GetBidsAwarded, GetAvailableOffers                  ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|                    VALIDATION LAYER                            |
|  +----------------------------------------------------------+|
|  | QCROfferValidationContext   (Offer rules)                ||
|  | QCRBidValidationContext     (Bid rules)                  ||
|  | QCRAwardValidationContext   (Award rules)                ||
|  | 312 total validation rules                               ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|                    DATA ACCESS LAYER                           |
|  +----------------------------------------------------------+|
|  | CROfferHeaderDO, CROfferDetailDO, CRBidHeaderDO,        ||
|  | CRBidDetailDO, CRAwardHeaderDO, CRAwardDetailDO,        ||
|  | CRTranOfferTimelineDO                                    ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|                        DATABASE                               |
|  CRCTRL_OFFER_HDR/DTL/APPR/DISC_RATE/TEXT,                   |
|  CRCTRL_BID_HDR/DTL/APPR,                                    |
|  CRCTRL_AWARD_HDR/DTL/AMEND,                                 |
|  CRTRAN_OFFER_TIMELINE                                        |
+-------------------------------------------------------------+
```

---

## Service Layer

### QPTMCapacityReleaseService.cs

**Location:** `Quorum.QPTM.ServiceCore.*` (approximately 230KB)

This is the primary service class for all Capacity Release business logic. It is one of the largest service files in the QPTM system.

#### Offer Operations

| Method | Purpose | Key Logic |
|--------|---------|-----------|
| **SaveOffer** | Persist offer header, details, approvals, discount rates, and text | Handles both insert and update scenarios; validates data integrity before save |
| **ValidateOffer** | Execute all offer validation rules via QCROfferValidationContext | Runs 312+ rules; returns validation results with rule codes |
| **SubmitOffer** | Post offer to bulletin board | Validates offer is in correct state, runs submission validations, updates status |
| **WithdrawOffer** | Remove offer from market | Validates offer can be withdrawn (no active bids/awards), updates status |
| **QueryOffer** | Search for offers by criteria | Supports filtering by TSP, status, release type, dates, shipper |
| **PrepareOffer** | Initialize a new offer with defaults | Sets default values based on TSP configuration and release type |
| **AddOfferApprovals** | Set up approval chain for offer | Creates approval records based on pipeline approval configuration |

#### Bid Operations

| Method | Purpose | Key Logic |
|--------|---------|-----------|
| **SaveBid** | Persist bid header and details | Validates bid against offer terms; handles insert/update |
| **ValidateBid** | Execute bid validation rules via QCRBidValidationContext | Validates rate, quantity, dates, location matching |
| **SubmitBid** | Submit bid for evaluation | Validates bidding window, bid state; updates status |
| **WithdrawBid** | Remove bid from evaluation | Validates bid can be withdrawn (not yet awarded) |

#### Award Operations

| Method | Purpose | Key Logic |
|--------|---------|-----------|
| **ValidateAward** | Execute award validation rules via QCRAwardValidationContext | Validates award against offer and bid terms |
| **SaveAward** | Persist award to database | Creates award records, updates offer/bid status |
| **GetAward** | Retrieve award details | Returns award header, details, and amendments |

#### Helper Methods

| Method | Purpose |
|--------|---------|
| **HandleBatchResult** | Process results from batch operations on CR data |
| **LocalContractCache** | Cache for contract data used during CR processing (avoids repeated DB lookups) |
| **LocalPipelineAdminCache** | Cache for pipeline admin configuration data |

### QPTMCapacityReleaseWidgetService

**Purpose:** Provides data for dashboard widgets and summary views.

| Method | Purpose |
|--------|---------|
| **GetBidsAwarded** | Retrieve summary of all bids that have been awarded |
| **GetAvailableOffers** | Retrieve list of offers currently available for bidding |

---

## Web Application Layer - Controllers and Wizards

### OfferWizardV2Controller

**Location:** `Quorum.QPTM.Web.Core/Controllers/`

The Offer Wizard uses a multi-state wizard pattern to guide users through the offer creation process. It contains **12 states**:

| State | Name | Purpose |
|-------|------|---------|
| 1 | **QStateQuery** | Initial query to find or create an offer |
| 2 | **QStateStart** | Offer header setup - release type, dates, basic info |
| 3 | **QStateContactInfo** | Contact information for the releasing shipper |
| 4 | **QStateIndicators** | Offer indicators and flags |
| 5 | **QStateDetail** | Offer detail lines - locations, quantities, dates |
| 6 | **QStateRateInfo** | Rate information - minimum rate, rate type |
| 7 | **QStateDiscountRate** | Discount rate schedules (if applicable) |
| 8 | **QStatePrearrangedBidder** | Prearranged bidder identification (prearranged deals only) |
| 9 | **QStateBiddingInfo** | Bidding window configuration (BidPerStartDate/EndDate) |
| 10 | **QStateRecallReput** | Recall and reput provisions |
| 11 | **QStateApproval** | Approval chain review and submission for approval |
| 12 | **QStateSummaryPage** | Final summary and submission |

**Wizard Flow:**
```
QStateQuery --> QStateStart --> QStateContactInfo --> QStateIndicators
    --> QStateDetail --> QStateRateInfo --> QStateDiscountRate
    --> QStatePrearrangedBidder (conditional) --> QStateBiddingInfo
    --> QStateRecallReput --> QStateApproval --> QStateSummaryPage
```

**Note:** QStatePrearrangedBidder is only displayed when the offer is for a prearranged deal. The wizard conditionally skips this state for standard auction offers.

### BidWizardV2Controller

**Location:** `Quorum.QPTM.Web.Core/Controllers/`

The Bid Wizard guides replacement shippers through the bid submission process. It contains **6 states**:

| State | Name | Purpose |
|-------|------|---------|
| 1 | **QStateQuery** | Search for available offers to bid on |
| 2 | **QStateStart** | Bid header setup - bidder info, rate |
| 3 | **QStateContactInfo** | Contact information for the replacement shipper |
| 4 | **QStateIndicators** | Bid indicators and flags |
| 5 | **QStateDetail** | Bid detail lines - locations, quantities |
| 6 | **QStateSummaryPage** | Final summary and submission |

**Wizard Flow:**
```
QStateQuery --> QStateStart --> QStateContactInfo --> QStateIndicators
    --> QStateDetail --> QStateSummaryPage
```

### CRAwardController

**Location:** `Quorum.QPTM.Web.Core/Controllers/`

The Award Controller manages the award processing screens.

**Security:** Requires `CapRelAward` security permission.

**Key Grids:**

| Grid | Purpose | Data Source |
|------|---------|-------------|
| **EvaluatedBids** | Displays bids ranked by evaluation criteria | QPTMCapacityReleaseService bid evaluation methods |
| **Awards** | Displays existing awards and their status | QPTMCapacityReleaseService.GetAward |

---

## API Layer

### CapacityReleaseController

**Location:** `Quorum.QPTM.Web.Controllers/APIControllers/`
**Route:** `/api/v1.0/CapacityRelease`

| Endpoint | Method | Purpose | Parameters |
|----------|--------|---------|------------|
| `/Awards` | GET | Retrieve list of awards | TSP, status, date range filters |
| `/Awards/Summary` | GET | Retrieve award summary data | TSP, date range filters |
| `/Awards/{tsp}/{id}/Details` | GET | Retrieve specific award details | TSP number, award ID |

**Response Format:** Standard QPTM API response envelope with data objects.

---

## Validation Layer

### Validation Contexts

The CR system uses **312 total validation rules** distributed across three validation contexts:

#### QCROfferValidationContext

Validates offer data before save and submission.

**Key Rule Categories:**
- **Header Validation**: Required fields, date ranges, release type consistency
- **Detail Validation**: Location matching, quantity ranges, effective dates
- **Rate Validation**: Rate within acceptable range, discount rate consistency
- **Recall/Reput Validation**: Recall/reput terms consistent with release type
- **Approval Validation**: Required approvals configured
- **Contract Validation**: Releasing shipper has valid, active contract with sufficient capacity
- **Nom-Ready Check (RuleCROF001590)**: Validates that awarded capacity will produce a nom-ready contract

#### QCRBidValidationContext

Validates bid data before save and submission.

**Key Rule Categories:**
- **Header Validation**: Required fields, bidder eligibility
- **Detail Validation**: Location matching with offer, quantity within offer limits
- **Rate Validation (RuleCRBD000080)**: Rate bid percentage does not exceed maximum (100% for long-term non-permanent)
- **Bidding Window Validation**: Bid submitted within valid window
- **Offer Reference Validation**: Referenced offer exists and is in valid state

#### QCRAwardValidationContext

Validates award data before creation.

**Key Rule Categories:**
- **Offer-Bid Consistency**: Award matches offer and bid terms
- **Quantity Validation**: Awarded quantity does not exceed bid or offer quantity
- **Rate Validation**: Award rate consistent with bid and offer rate terms
- **Status Validation**: Offer and bid in correct state for award

### Key Validation Rules

| Rule Code | Context | Description |
|-----------|---------|-------------|
| **RuleCROF001590** | Offer | Contract not nom-ready - validates that the released capacity can produce a nomination-ready contract |
| **RuleCRBD000080** | Bid | Rate bid exceeds maximum percentage - enforces 100% cap on PctMaxRateBid |
| **Other Offer Rules** | Offer | Offer detail validation, date validation, location validation |
| **Other Bid Rules** | Bid | Bid detail matching, quantity validation, bidding window enforcement |
| **Other Award Rules** | Award | Award-offer-bid consistency, quantity limits |

---

## Data Model

### Data Objects

| Data Object | Database Table | Purpose |
|-------------|---------------|---------|
| **CROfferHeaderDO** | CRCTRL_OFFER_HDR | Offer header - releasing shipper, release type, dates, status |
| **CROfferDetailDO** | CRCTRL_OFFER_DTL | Offer details - locations, quantities, effective dates |
| **(Offer Approval)** | CRCTRL_OFFER_APPR | Approval records for offers |
| **(Offer Discount Rate)** | CRCTRL_OFFER_DISC_RATE | Discount rate schedules for offers |
| **(Offer Text)** | CRCTRL_OFFER_TEXT | Free-form text associated with offers |
| **CRBidHeaderDO** | CRCTRL_BID_HDR | Bid header - bidder info, rate, status |
| **CRBidDetailDO** | CRCTRL_BID_DTL | Bid details - locations, quantities |
| **(Bid Approval)** | CRCTRL_BID_APPR | Approval records for bids |
| **CRAwardHeaderDO** | CRCTRL_AWARD_HDR | Award header - winning bid/offer reference, status |
| **CRAwardDetailDO** | CRCTRL_AWARD_DTL | Award details - locations, awarded quantities |
| **(Award Amendment)** | CRCTRL_AWARD_AMEND | Amendments to existing awards |
| **CRTranOfferTimelineDO** | CRTRAN_OFFER_TIMELINE | Timeline milestones for offers |

### Data Object Relationships

```
CROfferHeaderDO (CRCTRL_OFFER_HDR)
    |-- 1:N --> CROfferDetailDO (CRCTRL_OFFER_DTL)
    |-- 1:N --> CRCTRL_OFFER_APPR
    |-- 1:N --> CRCTRL_OFFER_DISC_RATE
    |-- 1:N --> CRCTRL_OFFER_TEXT
    |-- 1:N --> CRTranOfferTimelineDO (CRTRAN_OFFER_TIMELINE)
    |-- 1:N --> CRBidHeaderDO (CRCTRL_BID_HDR)
                    |-- 1:N --> CRBidDetailDO (CRCTRL_BID_DTL)
                    |-- 1:N --> CRCTRL_BID_APPR
                    |-- 1:1 --> CRAwardHeaderDO (CRCTRL_AWARD_HDR)
                                    |-- 1:N --> CRAwardDetailDO (CRCTRL_AWARD_DTL)
                                    |-- 1:N --> CRCTRL_AWARD_AMEND
```

---

## Database Schema

### Offer Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **CRCTRL_OFFER_HDR** | Offer header | TSP_NO, OFFER_NO, SR_BP_NO, SR_CTR_NO, RELEASE_TYPE_CD, AUCTION_TYPE_CD, BID_PER_START_DT, BID_PER_END_DT, OFFER_STAT_CD, RECALL_IND, REPUT_IND |
| **CRCTRL_OFFER_DTL** | Offer detail lines | TSP_NO, OFFER_NO, DTL_SEQ_NO, REC_LOC_ID, DEL_LOC_ID, RELEASE_QTY, EFF_START_DT, EFF_END_DT |
| **CRCTRL_OFFER_APPR** | Offer approvals | TSP_NO, OFFER_NO, APPR_SEQ_NO, APPR_USER_ID, APPR_STAT_CD, APPR_DT |
| **CRCTRL_OFFER_DISC_RATE** | Discount rates | TSP_NO, OFFER_NO, RATE_SEQ_NO, DISC_PCT, EFF_START_DT, EFF_END_DT |
| **CRCTRL_OFFER_TEXT** | Offer text/notes | TSP_NO, OFFER_NO, TEXT_SEQ_NO, TEXT_TYPE_CD, TEXT_CONTENT |

### Bid Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **CRCTRL_BID_HDR** | Bid header | TSP_NO, OFFER_NO, BID_NO, BIDDER_BP_NO, RATE_BID, PCT_MAX_RATE_BID, BID_STAT_CD |
| **CRCTRL_BID_DTL** | Bid detail lines | TSP_NO, OFFER_NO, BID_NO, DTL_SEQ_NO, REC_LOC_ID, DEL_LOC_ID, BID_QTY, EFF_START_DT, EFF_END_DT |
| **CRCTRL_BID_APPR** | Bid approvals | TSP_NO, OFFER_NO, BID_NO, APPR_SEQ_NO, APPR_USER_ID, APPR_STAT_CD |

### Award Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **CRCTRL_AWARD_HDR** | Award header | TSP_NO, OFFER_NO, BID_NO, AWARD_NO, AWARD_STAT_CD, AWARD_QTY, AWARD_RATE |
| **CRCTRL_AWARD_DTL** | Award detail lines | TSP_NO, OFFER_NO, BID_NO, AWARD_NO, DTL_SEQ_NO, REC_LOC_ID, DEL_LOC_ID, AWARD_QTY |
| **CRCTRL_AWARD_AMEND** | Award amendments | TSP_NO, OFFER_NO, BID_NO, AWARD_NO, AMEND_SEQ_NO, AMEND_TYPE_CD |

### Timeline Table

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **CRTRAN_OFFER_TIMELINE** | Offer lifecycle milestones | TSP_NO, OFFER_NO, MILESTONE_TYPE_CD, MILESTONE_DT, MILESTONE_USER_ID |

---

## Batch Processes

### CR Batch Jobs

| Process Code | Name | Purpose | Schedule |
|--------------|------|---------|----------|
| **CRMDQMSQVL** | CR MDQ/MSQ Validation | Validates Maximum Daily Quantity and Maximum Storage Quantity for capacity release offers against contract capacity | Periodic / On-demand |
| **CROFFRTIML** | CR Offer Timeline | Processes offer timeline milestones; advances offers through lifecycle stages based on date triggers (e.g., bidding window open/close) | Daily |
| **CRBIDGEN** | CR Bid Generation | Generates bids automatically based on prearranged deal terms or standing bid instructions | On-demand / Event-driven |
| **CRBGNNS** | CR Bid Generation - No Notification Suppression | Variant of bid generation without suppressing notification messages | On-demand |
| **CWCOFF** | CR Withdrawn/Cancelled Offers | Processes offers that have been withdrawn or cancelled; cleans up associated bid and approval records | Daily / On-demand |
| **CWOSEASPST** | CR Write-Off Seasonal Post | Processes seasonal release postings; handles end-of-season write-off and capacity return to releasing shipper | Seasonal / Periodic |

### Batch Process Flow

```
Daily Processing:

1. CROFFRTIML (Offer Timeline)
   |-- Checks all active offers for timeline milestones
   |-- Opens bidding windows when BidPerStartDate reached
   |-- Closes bidding windows when BidPerEndDate reached
   |-- Triggers evaluation when bidding closes
   |-- Records milestones in CRTRAN_OFFER_TIMELINE

2. CRMDQMSQVL (MDQ/MSQ Validation)
   |-- Validates offer quantities against contract MDQ
   |-- Ensures released quantity does not exceed available capacity
   |-- Flags offers with validation errors

3. CRBIDGEN / CRBGNNS (Bid Generation)
   |-- Generates automatic bids for prearranged deals
   |-- Creates bid records in CRCTRL_BID_HDR/DTL
   |-- Submits bids within the bidding window

4. CWCOFF (Withdrawn/Cancelled Offer Cleanup)
   |-- Processes withdrawn offers
   |-- Updates related bid statuses
   |-- Cleans up approval records

5. CWOSEASPST (Seasonal Post Processing)
   |-- Handles seasonal release expirations
   |-- Returns capacity to releasing shipper
   |-- Updates award statuses for expired seasonal releases
```

---

## Caching

### LocalContractCache

**Purpose:** Caches contract data used during CR processing to avoid repeated database lookups.

**Scope:** Request-scoped; created per service method invocation.

**Cached Data:**
- Contract header information
- Contract location details
- Contract rate schedules
- Contract MDQ values

**Usage:** Used extensively in SaveOffer, ValidateOffer, SaveBid, ValidateBid, and award operations to look up releasing shipper contract information without multiple database round-trips.

### LocalPipelineAdminCache

**Purpose:** Caches pipeline administration configuration data.

**Scope:** Request-scoped; created per service method invocation.

**Cached Data:**
- Pipeline-specific configuration settings
- Bidding window defaults
- Rate limits and caps
- Approval chain configurations
- FERC posting requirements

**Usage:** Used to retrieve pipeline-specific business rules and configuration during offer/bid processing.

---

## Integration Points

### Internal Integrations

| System | Integration | Direction |
|--------|------------|-----------|
| **Contracts (CTR)** | CR reads contract data to validate offers; awards create/update contracts | Bidirectional |
| **Nominations (NN)** | Awarded capacity enables nominations by replacement shipper | CR --> NN |
| **CAS (Scheduling)** | Released capacity included in scheduling calculations | CR --> CAS |
| **EDI** | CR postings and awards exchanged electronically | Bidirectional |
| **Security** | CapRelAward permission required for award processing | Security --> CR |

### External Integrations

| System | Integration | Protocol |
|--------|------------|----------|
| **Pipeline Bulletin Board** | Offer postings and bid results | EDI / Web Services |
| **FERC Reporting** | Regulatory compliance reporting | File-based / EDI |
| **NAESB Standards** | Capacity release data formats | NAESB standard EDI |

---

## Key Processing Flows

### Offer Creation Flow

```
User Action: Create New Offer via OfferWizardV2

1. QStateQuery
   --> User selects "New Offer" or queries existing offers

2. QStateStart
   --> PrepareOffer() called to initialize defaults
   --> User sets release type, contract, dates

3. QStateContactInfo through QStateRecallReput
   --> User enters offer details through wizard states
   --> Conditional states (PrearrangedBidder) shown/skipped

4. QStateApproval
   --> AddOfferApprovals() sets up approval chain
   --> User reviews and submits for approval

5. QStateSummaryPage
   --> ValidateOffer() runs all validation rules
   --> If valid: SubmitOffer() posts to bulletin board
   --> If invalid: Errors displayed, user corrects

6. Post-Submit
   --> Offer status set to Submitted/Posted
   --> CROFFRTIML batch tracks timeline milestones
   --> Bidding window opens per BidPerStartDate
```

### Bid Submission Flow

```
User Action: Submit Bid via BidWizardV2

1. QStateQuery
   --> User searches for available offers (GetAvailableOffers)
   --> Selects an offer to bid on

2. QStateStart through QStateDetail
   --> User enters bid details (rate, quantity, locations)
   --> System validates against offer terms in real-time

3. QStateSummaryPage
   --> ValidateBid() runs all validation rules
   --> Rate bid checked against PctMaxRateBid limit (RuleCRBD000080)
   --> Bidding window validated (BidPerStartDate <= now <= BidPerEndDate)
   --> If valid: SubmitBid() enters bid into competition
   --> If invalid: Errors displayed, user corrects
```

### Award Processing Flow

```
User Action: Process Awards via CRAwardController

1. View Evaluated Bids (EvaluatedBids grid)
   --> System displays bids ranked by BidEvalIndCode criteria
   --> Highest-ranking bid highlighted

2. Select Bid for Award
   --> ValidateAward() checks offer-bid-award consistency
   --> Quantity and rate validated

3. Save Award
   --> SaveAward() creates CRCTRL_AWARD_HDR/DTL records
   --> Offer status updated to Awarded
   --> Bid status updated to Awarded
   --> Contract created/updated for replacement shipper
   --> Timeline milestone recorded in CRTRAN_OFFER_TIMELINE
```

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts and terminology
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- **CAS Architecture**: [../capacity-scheduling-allocations/architecture.md](../capacity-scheduling-allocations/architecture.md) - Scheduling architecture
- **Nominations Architecture**: [../nominations/architecture.md](../nominations/architecture.md) - Nominations architecture
- **QUICK_REFERENCE.md**: Feature mapping and keywords for CR

---

*Last updated: 2026-03-03*
*Document version: 1.0*
