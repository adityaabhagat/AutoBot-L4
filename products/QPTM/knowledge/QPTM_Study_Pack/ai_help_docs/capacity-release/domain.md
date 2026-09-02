---
title: Capacity Release (CR) - Domain Concepts
category: domain
feature: Capacity Release (CR)
related_repos: Web, Batch
keywords: CR, capacity release, offer, bid, award, recall, reput, auction, prearranged, seasonal, permanent, bidding window, evaluation, RFS, ROFR, right of first refusal
last_updated: 2026-03-03
---

# Capacity Release (CR) - Domain Concepts

## Overview

This document explains the **business concepts** behind Capacity Release (CR) in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [CR Lifecycle](#cr-lifecycle)
3. [Release Types](#release-types)
4. [Auction Types](#auction-types)
5. [Offers](#offers)
6. [Bidding](#bidding)
7. [Bid Evaluation and Award Processing](#bid-evaluation-and-award-processing)
8. [Recall and Reput](#recall-and-reput)
9. [Rate Bidding](#rate-bidding)
10. [Timeline Milestones](#timeline-milestones)
11. [Approval Workflows](#approval-workflows)
12. [Offer and Bid Status Codes](#offer-and-bid-status-codes)
13. [Business Rules Summary](#business-rules-summary)
14. [Glossary](#glossary)
15. [Related Documentation](#related-documentation)

---

## System Overview

### What is Capacity Release?

**Capacity Release (CR)** is the FERC-regulated process by which existing firm capacity holders (releasing shippers) make their contracted pipeline transportation capacity available to other parties (replacement shippers) through an auction or prearranged deal mechanism.

**Business Purpose:**
- Allow shippers to release unused pipeline capacity to the market
- Enable replacement shippers to obtain capacity through competitive bidding
- Support prearranged deals between known parties
- Manage recall and reput rights for releasing shippers
- Enforce FERC regulatory requirements for capacity release transactions
- Track the full lifecycle from offer creation through award and recall

### Key Business Value

- **Market Efficiency**: Ensures unused pipeline capacity reaches parties who need it
- **Regulatory Compliance**: Maintains FERC and NAESB compliance for capacity release transactions
- **Revenue Recovery**: Allows releasing shippers to recover costs on unused capacity
- **Transparent Auctions**: Provides fair, competitive bidding process for available capacity
- **Operational Flexibility**: Supports seasonal, permanent, and prearranged release mechanisms
- **Recall Protection**: Preserves releasing shipper rights through recall/reput provisions

---

## CR Lifecycle

### End-to-End Flow

The Capacity Release lifecycle follows a defined sequence of stages from initial offer creation through final award (and potential recall):

```
CR Lifecycle:

1. Offer Creation
   ├── Releasing shipper creates an offer to release capacity
   ├── Defines release type (permanent, seasonal, prearranged)
   ├── Specifies quantity, locations, dates, and rate terms
   └── Adds recall/reput provisions if applicable

2. Offer Validation & Submission
   ├── System validates offer against business rules (312 total rules)
   ├── Offer goes through approval workflow (if required)
   └── Offer is submitted and posted for bidding

3. Bidding Window Opens
   ├── Bidding window defined by BidPerStartDate / BidPerEndDate
   ├── Replacement shippers submit bids on available offers
   ├── Bids validated against offer terms and business rules
   └── Multiple bids may be submitted per offer

4. Bid Evaluation
   ├── System evaluates bids based on BidEvalIndCode criteria
   ├── Bids ranked by rate, quantity, and matching rules
   └── Best bid(s) identified for award

5. Award Processing
   ├── Awards generated for winning bid(s)
   ├── Award validated against offer and bid terms
   ├── Contract created or updated for replacement shipper
   └── Capacity transferred to replacement shipper

6. Recall / Reput (if applicable)
   ├── Releasing shipper exercises recall right
   ├── Replacement shipper may exercise reput right
   └── Capacity returned or re-released as applicable
```

### Lifecycle State Transitions

```
Offer:   Draft → Validated → Submitted → Posted → Awarded → Completed
                                                 → Withdrawn
Bid:     Draft → Validated → Submitted → Evaluated → Awarded → Completed
                                                    → Not Awarded
Award:   Pending → Validated → Awarded → Active → Completed
                                                → Recalled
```

---

## Release Types

### Permanent Release

A **permanent release** transfers capacity rights for the remaining term of the releasing shipper's contract.

**Characteristics:**
- Capacity rights transferred permanently to replacement shipper
- Releasing shipper gives up all rights to the released capacity
- No recall or reput rights apply
- Rate bid capped at maximum tariff rate (PctMaxRateBid up to 100% for long-term non-permanent releases)
- Replacement shipper assumes all obligations of the capacity

**Business Rule:** Permanent releases cannot include recall or reput provisions. Once awarded, the releasing shipper has no mechanism to recover the capacity.

### Seasonal Release

A **seasonal release** transfers capacity for a defined period shorter than the full contract term.

**Characteristics:**
- Release effective for a specific date range within the contract term
- Start and end dates define the seasonal period
- Capacity returns to releasing shipper automatically when the seasonal period ends
- May include recall/reput provisions
- Seasonal date validation ensures dates fall within contract term
- Can span multiple gas flow months

**Business Rule:** Seasonal release dates must fall within the effective dates of the releasing shipper's underlying contract. The system validates that seasonal start/end dates are consistent and do not extend beyond the contract term.

### Prearranged Deals

A **prearranged deal** is a capacity release where the releasing shipper has pre-identified the replacement shipper.

**Characteristics:**
- Releasing shipper names a specific replacement shipper (prearranged bidder)
- Still posted on the bulletin board per FERC requirements
- Other parties may submit competing bids
- If competing bids meet or exceed the prearranged deal terms, the prearranged bidder has the right to match
- Right of First Refusal (ROFR) may apply to the prearranged bidder
- Requires the prearranged bidder identifier in the offer

**Business Rule:** Even prearranged deals must be posted for a minimum bidding window (typically at least one business day for releases of more than one calendar month) to allow competing bids, per FERC regulations. Short-term releases (one calendar month or less) may have abbreviated posting requirements.

---

## Auction Types

### CapacityRelease (Standard Auction)

The standard **CapacityRelease** auction is the primary mechanism for releasing capacity to the open market.

**Characteristics:**
- Open to all eligible replacement shippers
- Competitive bidding process
- Bids evaluated based on rate and other criteria
- Award goes to highest-ranking bid(s)
- Subject to full FERC posting and bidding requirements

### RequestForService (RFS)

A **Request for Service** auction allows a potential shipper to request specific capacity from the pipeline.

**Characteristics:**
- Initiated by a party seeking capacity rather than a releasing shipper
- Pipeline or releasing shipper may respond with an offer
- Different workflow from standard capacity release
- May result in a prearranged deal if a releasing shipper agrees to terms

### RightOfFirstRefusal (ROFR)

**Right of First Refusal** is a mechanism that gives an existing replacement shipper the right to match any competing bid to retain released capacity.

**Characteristics:**
- Applies when an existing replacement shipper's release is expiring
- Existing replacement shipper has the right to match the best competing bid
- If matched, the existing replacement shipper retains the capacity
- ROFR rights are part of the original release agreement
- Timeline-driven: ROFR holder must respond within defined window

---

## Offers

### Offer Structure

An offer to release capacity contains the following key elements:

**Header Information (CROfferHeaderDO / CRCTRL_OFFER_HDR):**
- TSP number and offer identification
- Releasing shipper (service requester) and contract number
- Release type (permanent, seasonal, prearranged)
- Auction type (CapacityRelease, RFS, ROFR)
- Bidding window dates (BidPerStartDate, BidPerEndDate)
- Rate terms and minimum acceptable rate
- Recall/reput provisions
- Prearranged bidder identification (if applicable)
- Offer status code

**Detail Information (CROfferDetailDO / CRCTRL_OFFER_DTL):**
- Receipt and delivery locations
- Quantity released at each location pair
- Effective dates for the release
- Location-specific terms and conditions

**Additional Components:**
- **Approvals (CRCTRL_OFFER_APPR):** Approval chain for offer submission
- **Discount Rates (CRCTRL_OFFER_DISC_RATE):** Discounted rate schedules
- **Text (CRCTRL_OFFER_TEXT):** Free-form text and notes

### Offer Operations

| Operation | Description | Business Context |
|-----------|-------------|------------------|
| **SaveOffer** | Persist offer data to database | Draft creation or editing |
| **ValidateOffer** | Run validation rules against offer | Pre-submission checks |
| **SubmitOffer** | Post offer for bidding | Makes offer visible to market |
| **WithdrawOffer** | Remove offer from market | Cancel before award |
| **QueryOffer** | Search for existing offers | Offer lookup and review |
| **PrepareOffer** | Initialize offer with defaults | New offer setup |
| **AddOfferApprovals** | Set up approval chain | Workflow initialization |

---

## Bidding

### Bid Structure

A bid to acquire released capacity contains:

**Header Information (CRBidHeaderDO / CRCTRL_BID_HDR):**
- TSP number and bid identification
- Replacement shipper (bidder) information
- Reference to the offer being bid on
- Rate bid and rate type
- Bid status code

**Detail Information (CRBidDetailDO / CRCTRL_BID_DTL):**
- Receipt and delivery locations matching offer details
- Quantity bid at each location pair
- Effective dates for the bid

### Bidding Windows

The bidding window defines when bids can be submitted for an offer:

- **BidPerStartDate**: Earliest date/time bids can be submitted
- **BidPerEndDate**: Latest date/time bids can be submitted (bidding closes)

**Business Rules:**
- Bids cannot be submitted before BidPerStartDate
- Bids cannot be submitted after BidPerEndDate
- The bidding window must meet minimum FERC posting requirements
- Short-term releases (one calendar month or less) may have shortened bidding windows
- Long-term releases require longer bidding windows

### Bid Operations

| Operation | Description | Business Context |
|-----------|-------------|------------------|
| **SaveBid** | Persist bid data to database | Draft creation or editing |
| **ValidateBid** | Run validation rules against bid | Pre-submission checks |
| **SubmitBid** | Submit bid for evaluation | Enters bid into competition |
| **WithdrawBid** | Remove bid from evaluation | Cancel before award |

### Matching Rules

Bids must match the offer terms to be valid:

1. **Location Matching**: Bid receipt/delivery locations must match or be a subset of offer locations
2. **Quantity Matching**: Bid quantity cannot exceed offered quantity at any location pair
3. **Date Matching**: Bid effective dates must fall within offer release dates
4. **Rate Matching**: Bid rate must meet or exceed the offer minimum rate (if specified)
5. **Eligibility**: Bidder must be an eligible replacement shipper for the pipeline

---

## Bid Evaluation and Award Processing

### Bid Evaluation

Bids are evaluated using the **BidEvalIndCode** (Bid Evaluation Indicator Code) which determines the evaluation methodology:

**Evaluation Criteria:**
- **Highest Rate**: Bids ranked by offered rate (highest rate wins)
- **Net Revenue**: Bids evaluated based on total revenue (rate x quantity x duration)
- **Present Value**: Bids evaluated on present value of future revenue stream
- **Quantity**: Priority given to bids requesting the full offered quantity

**Evaluation Process:**
1. Collect all valid, submitted bids for the offer
2. Apply the BidEvalIndCode methodology to rank bids
3. Determine winning bid(s) based on ranking
4. If prearranged deal, check if competing bids beat prearranged terms
5. If ROFR applies, allow ROFR holder to match best competing bid
6. Generate award for winning bid(s)

### Award Processing

**Award Structure (CRAwardHeaderDO / CRCTRL_AWARD_HDR):**
- TSP number and award identification
- Reference to winning offer and bid
- Awarded quantity and rate
- Award status code

**Award Detail (CRAwardDetailDO / CRCTRL_AWARD_DTL):**
- Location-specific awarded quantities
- Effective dates for the award

**Award Amendment (CRCTRL_AWARD_AMEND):**
- Modifications to existing awards
- Amendment history tracking

**Award Operations:**
| Operation | Description | Business Context |
|-----------|-------------|------------------|
| **ValidateAward** | Run validation rules against award | Pre-award checks |
| **SaveAward** | Persist award to database | Award creation |
| **GetAward** | Retrieve award details | Award lookup and review |
| **GetBidsAwarded** | List all awarded bids | Award summary reporting |
| **GetAvailableOffers** | List offers available for award | Award processing queue |

### Award-to-Contract Flow

When an award is finalized:
1. System creates or updates a contract for the replacement shipper
2. Capacity quantities transferred from releasing shipper's contract
3. Nom-ready status set on the new contract (must pass RuleCROF001590)
4. Replacement shipper can begin nominating against the awarded capacity

---

## Recall and Reput

### Recall

**Recall** is the right of a releasing shipper to take back released capacity before the release term ends.

**Characteristics:**
- Must be specified in the original offer
- Defined recall terms (notice period, conditions)
- Releasing shipper must provide notice per recall terms
- Recalled capacity returns to releasing shipper's contract
- Replacement shipper loses access to recalled capacity

**Recall Process:**
1. Releasing shipper initiates recall per offer terms
2. System validates recall against offer recall provisions
3. Notice sent to replacement shipper
4. After notice period, capacity returned to releasing shipper
5. Award status updated to reflect recall

### Reput

**Reput** is the right of a replacement shipper to return released capacity to the releasing shipper before the release term ends.

**Characteristics:**
- Must be specified in the original offer
- Defined reput terms (notice period, conditions)
- Replacement shipper initiates reput when capacity no longer needed
- Capacity returns to releasing shipper's contract
- Replacement shipper relieved of capacity obligations

**Reput Process:**
1. Replacement shipper initiates reput per offer terms
2. System validates reput against offer reput provisions
3. Notice sent to releasing shipper
4. After notice period, capacity returned to releasing shipper
5. Award status updated to reflect reput

### Recall/Reput Business Rules

1. Recall/reput rights must be defined at offer creation time
2. Permanent releases cannot include recall/reput provisions
3. Recall notice periods must be honored
4. Recalled/reput capacity becomes available for re-release
5. Active nominations on recalled capacity must be handled (cut or transferred)

---

## Rate Bidding

### PctMaxRateBid

**PctMaxRateBid** (Percent of Maximum Rate Bid) defines the bid rate as a percentage of the maximum tariff rate.

**Key Rules:**
- **Long-term non-permanent releases**: PctMaxRateBid can be up to **100%** of the maximum tariff rate
- **Short-term releases**: May have different rate caps depending on FERC policy
- **Minimum rate**: Offers may specify a minimum acceptable rate (floor)
- **Rate negotiation**: Prearranged deals may negotiate rates below the maximum

### Rate Types

| Rate Type | Description | Usage |
|-----------|-------------|-------|
| **Reservation Rate** | Fixed rate for reserving capacity | Most common for firm releases |
| **Usage Rate** | Rate per unit of throughput | Applied to actual gas flow |
| **Surcharge** | Additional charges on top of base rate | Pipeline-specific add-ons |
| **Negotiated Rate** | Rate agreed between parties | Prearranged deals |

### Rate Validation Rules

- Bid rate cannot exceed the maximum tariff rate (100% cap for applicable releases)
- Bid rate must meet or exceed offer minimum rate
- Rate must be expressed in the correct units (per Dth, per MMBtu, etc.)
- Discount rate schedules must be consistent with offer terms
- Rule RuleCRBD000080 enforces rate bid percentage limits

---

## Timeline Milestones

### Offer Timeline (CRTRAN_OFFER_TIMELINE / CRTranOfferTimelineDO)

The offer timeline tracks key milestones throughout the capacity release process:

| Milestone | Description | Business Significance |
|-----------|-------------|----------------------|
| **Offer Created** | Initial offer creation date/time | Start of process |
| **Offer Validated** | All validation rules passed | Ready for submission |
| **Offer Submitted** | Posted to bulletin board | Visible to market |
| **Bidding Opens** | BidPerStartDate reached | Bids accepted |
| **Bidding Closes** | BidPerEndDate reached | No more bids accepted |
| **Evaluation Complete** | Bids ranked and winner identified | Ready for award |
| **Award Issued** | Winning bidder awarded capacity | Capacity transferred |
| **Release Effective** | Capacity release begins | Gas flow under new shipper |
| **Release Expires** | Capacity release ends (seasonal) | Capacity returns |
| **Recall Initiated** | Releasing shipper recalls capacity | Recall process begins |
| **Recall Effective** | Recall takes effect | Capacity returned |

### Timeline Tracking

The `CRTRAN_OFFER_TIMELINE` table records each milestone with:
- Milestone type code
- Date and time of milestone
- User who triggered the milestone
- Associated offer, bid, or award reference
- Status at time of milestone

---

## Approval Workflows

### Offer Approval

Offers may require approval before submission, depending on pipeline and organizational rules.

**Approval Chain (CRCTRL_OFFER_APPR):**
1. Offer creator submits for approval
2. System routes to configured approver(s)
3. Each approver reviews and approves/rejects
4. All approvals must be complete before offer can be submitted
5. Rejected offers returned to creator for correction

**Approval Considerations:**
- Approval requirements may vary by release type
- Large quantity releases may require additional approval levels
- Prearranged deals may have different approval chains
- Approval status tracked in offer approval records

### Bid Approval

Bids may also require internal approval before submission:

**Approval Chain (CRCTRL_BID_APPR):**
1. Bid creator submits for approval
2. Internal reviewers validate bid terms
3. Approved bids eligible for submission
4. Rejected bids returned for revision

---

## Offer and Bid Status Codes

### Offer Status Codes

| Status | Description | Next Valid States |
|--------|-------------|-------------------|
| **Draft** | Offer created but not yet validated | Validated, Withdrawn |
| **Validated** | All validation rules passed | Submitted, Draft (edit), Withdrawn |
| **Submitted** | Posted for bidding | Awarded, Withdrawn |
| **Posted** | Active on bulletin board with open bidding window | Awarded, Withdrawn |
| **Awarded** | Winning bid selected and awarded | Completed, Recalled |
| **Withdrawn** | Offer removed from market | (Terminal state) |
| **Completed** | Release term fulfilled | (Terminal state) |

### Bid Status Codes

| Status | Description | Next Valid States |
|--------|-------------|-------------------|
| **Draft** | Bid created but not validated | Validated, Withdrawn |
| **Validated** | All validation rules passed | Submitted, Draft (edit), Withdrawn |
| **Submitted** | Entered into competition | Evaluated, Withdrawn |
| **Evaluated** | Ranked by evaluation criteria | Awarded, Not Awarded |
| **Awarded** | Won the auction | Completed |
| **Not Awarded** | Did not win the auction | (Terminal state) |
| **Withdrawn** | Bid removed from competition | (Terminal state) |

---

## Business Rules Summary

### Critical Business Rules

1. **Bidding Window Enforcement**: Bids can only be submitted within the BidPerStartDate to BidPerEndDate window
2. **Rate Cap**: PctMaxRateBid cannot exceed 100% for long-term non-permanent releases
3. **Location Matching**: Bid locations must match offer locations
4. **Quantity Limits**: Bid quantity cannot exceed offered quantity
5. **Date Validation**: Release dates must fall within contract effective dates
6. **Seasonal Validation**: Seasonal release dates must be internally consistent
7. **Recall/Reput Terms**: Must be defined at offer time; not available for permanent releases
8. **FERC Posting**: All releases must be posted for minimum required bidding window
9. **Prearranged Matching**: Prearranged bidder has ROFR to match competing bids
10. **Nom-Ready Contract**: Awarded capacity must produce a nom-ready contract (RuleCROF001590)
11. **Approval Completion**: All required approvals must be complete before submission
12. **Offer Existence**: Bids can only reference existing, active offers

---

## Glossary

### Terms and Abbreviations

| Term | Definition |
|------|------------|
| **CR** | Capacity Release - the system for releasing pipeline capacity |
| **Releasing Shipper** | The firm capacity holder who is releasing (offering) their capacity |
| **Replacement Shipper** | The party acquiring released capacity through bidding |
| **FERC** | Federal Energy Regulatory Commission - regulates interstate pipeline capacity |
| **NAESB** | North American Energy Standards Board - sets standards for capacity release |
| **Offer** | A releasing shipper's formal posting of capacity available for release |
| **Bid** | A replacement shipper's formal request to acquire offered capacity |
| **Award** | The result of evaluating bids; winning bid receives the capacity |
| **Recall** | Releasing shipper's right to reclaim released capacity |
| **Reput** | Replacement shipper's right to return released capacity |
| **ROFR** | Right of First Refusal - existing shipper's right to match competing bids |
| **RFS** | Request for Service - a capacity request initiated by a seeking party |
| **Prearranged Deal** | A release where the replacement shipper is pre-identified |
| **BidEvalIndCode** | Bid Evaluation Indicator Code - determines bid ranking methodology |
| **PctMaxRateBid** | Percent of Maximum Rate Bid - bid rate as percentage of max tariff |
| **BidPerStartDate** | Start of the bidding window |
| **BidPerEndDate** | End of the bidding window |
| **Permanent Release** | Release for full remaining contract term, no recall rights |
| **Seasonal Release** | Release for a defined period within the contract term |
| **MDQ** | Maximum Daily Quantity - contracted capacity limit |
| **Nom-Ready** | Status indicating a contract is ready for nominations |
| **Bulletin Board** | Public posting location for capacity release offers |
| **TSP** | Transportation Service Provider (pipeline company) |
| **Dth** | Dekatherms - standard unit of energy for natural gas |

### Related Processes

- **Contracts (CTR)**: Underlying contracts that capacity is released from
- **Nominations (NN)**: Replacement shipper nominations against awarded capacity
- **Capacity Scheduling (CAS)**: Scheduling of released capacity
- **Confirmations (CF)**: Confirmation of flows on released capacity
- **EDI**: Electronic data interchange for capacity release postings and transactions

---

## Related Documentation

- **Architecture**: [architecture.md](./architecture.md) - Technical implementation details
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- **CAS Domain**: [../capacity-scheduling-allocations/domain.md](../capacity-scheduling-allocations/domain.md) - Capacity scheduling concepts
- **Nominations Domain**: [../nominations/domain.md](../nominations/domain.md) - Nomination concepts
- **QUICK_REFERENCE.md**: Feature mapping and keywords for CR

---

*Last updated: 2026-03-03*
*Document version: 1.0*
