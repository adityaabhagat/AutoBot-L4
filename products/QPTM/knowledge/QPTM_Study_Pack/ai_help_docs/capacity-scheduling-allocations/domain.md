---
title: Capacity Scheduling Allocations (CAS) - Domain Concepts
category: domain
feature: Capacity Scheduling Allocations (CAS)
related_repos: Web, Batch
keywords: CAS, scheduling, allocations, capacity, nomination classification, transaction grouping, reduction, scheduled capacity, rule sets, segments, MDQ
last_updated: 2025-12-11
---

# Capacity Scheduling Allocations (CAS) - Domain Concepts

## Overview

This document explains the **business concepts** behind Capacity Scheduling Allocations (CAS) in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [CAS Flow Summary](#cas-flow-summary)
3. [Core Business Concepts](#core-business-concepts)
4. [Nomination Classification](#nomination-classification)
5. [Transaction Grouping](#transaction-grouping)
6. [Scheduled Capacity](#scheduled-capacity)
7. [Capacity Reduction](#capacity-reduction)
8. [Rights Allocation](#rights-allocation)
9. [Operational Available Capacity](#operational-available-capacity)
10. [Business Workflows](#business-workflows)
11. [Glossary](#glossary)

---

## System Overview

### What is CAS?

**Capacity Scheduling Allocations (CAS)** is the process of managing pipeline capacity scheduling, nomination classification, and allocation of available capacity across multiple shippers, contracts, and transactions on a natural gas pipeline.

**Business Purpose:**
- Classify nominations into transaction groups based on contractual rules
- Determine scheduled quantities for each scheduling object (segment, location, contract)
- Apply reduction logic when nominated quantities exceed available capacity
- Generate scheduled capacity allocations that respect priority rules
- Support regulatory reporting and pipeline balancing

### Key Business Value

- **Capacity Management**: Ensures efficient use of pipeline capacity
- **Fair Allocation**: Applies priority rules to allocate scarce capacity fairly
- **Regulatory Compliance**: Maintains FERC and NAESB compliance for capacity scheduling
- **Operational Visibility**: Provides clear view of scheduled vs nominated quantities
- **Imbalance Prevention**: Helps prevent operational imbalances through proper scheduling

---

## CAS Flow Summary

This section provides a concise overview of key concepts, flow rules, path definitions, and rights allocation logic in the Contractual Allocation System (CAS).

### 1. Default Paths, Non-Default Paths, and Nominations

- **Default Path:**  
  The standard, contract-specified route from a receipt location to a delivery location. All nominations assigned to the default path follow this segment route unless otherwise specified.

- **Non-Default (Alternate/Indirect) Path:**  
  Some contracts may be configured with non-default (alternate) paths. If a nomination is made and not enough segment capacity exists on the default path, or the contract specifically defines a different path, the nomination may flow along this alternate path.

- **Nominations:**  
  Shippers nominate gas movement from a receipt to a delivery. Shippers may nominate along the default path, along a contract-specified non-default path, or (in rarer cases) along a path that goes partially or wholly outside their contract path (triggering secondary rights).

### 2. Primary vs. Secondary Rights

- **Primary (Firm) Rights:**  
  - Awarded for segments/paths that match those specified on the contract in the specified direction (usually Receipt → Delivery).
  - These nominations have the highest priority and protected capacity up to the contract's MDQ (Maximum Daily Quantity).

- **Secondary Rights:**  
  - For flows outside of the contract path, against the path direction, or that go further "out of path" than the contract specifies.
  - These are "as available" and are only scheduled if segment/system capacity remains after all primary rights are honored.

- **Backhaul (B Direction):**  
  - Any nomination moving in the reverse direction of the contract (Delivery → Receipt), or using contract points in the wrong direction, is treated as backhaul and scheduled as secondary.
  - Backhaul nominations are only scheduled if allowed by the system and available capacity exists.

### 3. In Path and Out Path Definitions

- **In Path ("In-Path"):**
  - The contract-specified, forward-direction sequence from receipt to a given point.
  - Nominations from the contract's receipt to any point along this path (including delivery) are "in-path" and have primary rights.

- **Out Path ("Out-of-Path"):**
  - Segments and points not included in the contract's nominated path, typically including points upstream, in the opposite direction, or on alternate branches/looped pipeline positions.
  - Nominations along these are "out-of-path" and use secondary rights.

### 4. Secondary In Path vs. Secondary Out of Path (SI/SO)

| Code | Meaning              | Scope                   | Formula                             | Priority        |
|------|----------------------|-------------------------|-------------------------------------|-----------------|
| SI   | Secondary In Path    | Within nominated/contract path | `SegmentMDQ - PrimaryMDQ`         | Higher secondary|
| SO   | Secondary Out of Path| Outside contract path   | `ContractMDQ - PrimaryMDQ - SI`     | Lower secondary |

- **Secondary In Path (SI):**  
  Surplus capacity within the contract/nomination path _above the primary rights_.

- **Secondary Out of Path (SO):**  
  Surplus capacity available to the contract in segments _outside_ its nominated path, subject to broader system availability.

### 5. Nomination and Rights Assignment Cases (Examples)

| Case/Contract | Contract Path (C.path) | Nom Path         | Scheduled Path           | Primary Segments            | Secondary Segments             |
|---------------|------------------------|------------------|--------------------------|-----------------------------|-------------------------------|
| K1 (Default)  | 0→1→2→3→6              | 0→6              | 0→1→2→3→6                | 0,1,2,3,6                   | None                          |
| K1 (Default)  | 0→1→2→3→6              | 0→7              | 0→1→2→3→6→7              | 0,1,2,3,6                   | 7                             |
| K2 (Non-Def)  | 0→4→5→6                | 0→6              | 0→4→5→6                  | 0,4,5,6                     | None                          |
| K2 (Non-Def)  | 0→4→5→6                | 0→7              | 0→1→2→3→6→7 (default path, since 7 not on K2) | 0,6 (intersection)   | 1,2,3,7 (not on K2 path)      |

#### Special Case: Contract/Nomination Mismatch Example
- **Contract path:** 44413 (Rec) → 42228 (Del)
- **Nomination:** 42234 (Rec) → 44413 (Del)

**Result:** This nomination is **not "in-path" nor "out-path" per contract**; it is entirely _out of path_ and thus is assigned only **secondary rights** (if allowed).

### 6. Scheduling, Cuts, and Proration

- If total nominations for a segment exceed its capacity, the scheduler first honors all primary rights and then reduces (cuts) secondary and interruptible nominations—usually pro-rata across all affected shippers.
- **Pro-rating** ensures all shippers suffer the same proportional reduction during oversubscription.
- If downstream cuts are necessary, upstream nominations are also cut to match (you can't send more into an upstream segment than the downstream can take).

### 7. Path Builder Logic

- The system contains a "path builder" to select the appropriate route for each nomination—using the contract's specified default or non-default path, not simply the shortest or most direct physical route.

### 8. General Rules

- **Primary rights = contract path and direction.**
- **Secondary rights = any divergence from contract path or direction.**
- **In-path = within contract route, forward.**
- **Out-path = outside contract route, reverse or off-branch.**
- **Cuts follow segment priorities: primary scheduled to max, then secondary, then interruptible.**

### 9. Useful Terminology

- **Default Path Nom:** Nomination traveling along the contract's default path.
- **Non-Default Path Nom:** Nomination assigned to a contract's explicitly-approved alternate path.
- **Backhaul (B direct):** Movement against normal contract direction; always considered secondary.
- **NomPath:** The actual segment sequence the system will schedule for the nomination—either default or custom.
- **In Path/Out Path:** Used to define rights eligibility (primary vs. secondary) for any nomination under any contract.

---

## Core Business Concepts

### 1. Scheduling Objects

**Scheduling Objects** represent physical or logical components of the pipeline where capacity must be scheduled and allocated.

**Types of Scheduling Objects:**

| Type | Code | Description | Business Purpose |
|------|------|-------------|------------------|
| **Segment** | SEG | Physical pipeline segment between two points | Track capacity usage along pipeline sections |
| **Location** | LOC | Specific receipt or delivery point | Manage point-specific capacity constraints |
| **Location Group** | LGP | Grouping of multiple locations | Aggregate capacity for related locations |
| **Clay Basin - Entire Basin** | CBE | Storage facility (entire basin view) | Manage storage injection/withdrawal capacity |
| **Clay Basin - By Sides** | CBS | Storage facility (by sides view) | Track capacity separately by basin sides |
| **Lease Boundary Location** | LBL | Lease boundary constraint point | Enforce lease-specific capacity limits |
| **Lease Contract Capacity** | LCC | Lease contract capacity limit | Manage capacity under lease agreements |
| **Multi-Group** | MLT | Multiple group aggregation | Complex capacity allocation scenarios |
| **Bi-Directional Pair** | BDP | Two-way flow location pair | Manage bidirectional capacity |

**Key Attributes:**
- **Scheduling Object ID**: Unique identifier for the object
- **Effective Dates**: When the scheduling object is active
- **Capacity Limits**: MDQ, OAC, and other capacity constraints
- **Rule Sets**: Which classification rules apply to this object

### 2. Gas Day and Cycles

**Gas Day**: The operational period for pipeline operations (typically 9 AM to 9 AM).

**Nomination Cycles**: Different submission windows throughout the day:
- **Timely Cycle**: Primary day-ahead nominations
- **Evening Cycle**: Evening adjustments
- **Intraday Cycles (ID1, ID2, ID3)**: Day-of adjustments

**Business Rule**: CAS processing occurs for each gas day and cycle combination, with later cycles potentially revising earlier scheduled quantities.

### 3. Contract Capacity and MDQ

**MDQ (Maximum Daily Quantity)**: The maximum amount of gas a shipper can transport under a contract on a given day.

**Key Concepts:**
- **Firm Capacity**: Guaranteed capacity that cannot be interrupted
- **Interruptible Capacity**: Capacity that can be interrupted based on system needs
- **Ratchet Provisions**: Ability to exceed MDQ under certain conditions
- **Capacity Release**: Temporary transfer of capacity from one shipper to another

**Business Rule**: Scheduled quantities should not exceed contract MDQ unless ratchet provisions or capacity release arrangements apply.

### 4. Service Requester and Business Parties

**Service Requester (SR)**: The shipper who requested the transportation service.

**Counterparty (CP)**: The business party on the other side of the transaction.

**Business Rule**: CAS must track capacity usage by service requester to ensure individual shippers do not exceed their contracted capacity.

---

## Nomination Classification

### What is Nomination Classification?

**Nomination Classification** is the process of analyzing nominations and assigning them to appropriate **transaction groups** based on contractual rules, path information, and scheduling logic.

### Classification Process

**Step 1: Nomination Gathering**
- Retrieve all active nominations for the gas day and cycle
- Filter to latest cycle for each nomination
- Include only nominations eligible for scheduling

**Step 2: Path Analysis**
- Determine physical path (receipt point → pipeline → delivery point)
- Identify which pipeline segments the nomination traverses
- Calculate path-specific capacity requirements

**Step 3: Rule Evaluation**
- Match nomination attributes against **rule sets**
- Apply **Type of Service (TOS)** filters
- Consider contract-specific rules
- Evaluate capacity type requirements

**Step 4: Transaction Group Assignment**
- Assign nomination to appropriate **transaction group(s)**
- Set **transaction group rank** for prioritization
- Store classification results in staging table (`CASTAG_OBJ_NOM_TRANS_GRP`)

### Classification Attributes

Each classified nomination includes:
- **Transaction Group ID**: Which group it belongs to
- **Transaction Group Rank**: Priority within the group
- **Receipt/Delivery Quantities**: Quantity at each point
- **Capacity Type**: IT (Interruptible), FT (Firm), SR (Secondary Firm), etc.
- **Flow Direction**: Forward, Backhaul
- **Segment Indicator**: Whether nomination uses specific segment

### Business Rules for Classification

1. **TOS Matching**: Nomination TOS must match transaction group TOS filters
2. **Path Requirements**: Nomination path must match transaction group path criteria
3. **Contract Eligibility**: Contract must be eligible for the transaction group
4. **Capacity Type Precedence**: Firm capacity classifications take priority over interruptible
5. **Latest Cycle Wins**: Latest cycle nomination overrides earlier cycles for same nomination ID

---

## Transaction Grouping

### What are Transaction Groups?

**Transaction Groups** are logical groupings of nominations that share common characteristics and should be scheduled together under specific capacity allocation rules.

### Transaction Group Structure

**Components:**
- **Transaction Group ID**: Unique identifier
- **Transaction Group Rank**: Priority order (lower rank = higher priority)
- **Rule Set**: Set of classification rules that define the group
- **TOS Filters**: Which Types of Service are eligible
- **Accounting Method**: How to allocate capacity (pro-rata, first-come-first-served, etc.)

### Rule Sets

**Rule Sets** define the classification logic for transaction groups.

**Key Rule Set Attributes:**
- **Rule Set ID**: Unique identifier
- **Rule Set Rank**: Priority order for evaluating rules
- **Cycle Assignment**: Which nomination cycle(s) the rule set applies to
- **Evaluation Method**: How to evaluate multiple matching rules

**Common Rule Set Types:**
- **Path-Based Rules**: Match based on receipt/delivery path
- **Contract-Based Rules**: Match based on specific contracts
- **TOS-Based Rules**: Match based on Type of Service
- **Capacity-Type-Based Rules**: Match based on firm vs interruptible

### Transaction Group Ranks

**Transaction Group Rank** determines priority when capacity is constrained:

| Rank Range | Typical Usage | Priority Level |
|------------|---------------|----------------|
| 1-100 | Firm transport, system capacity | Highest |
| 101-200 | Secondary firm, ratcheted capacity | High |
| 201-300 | Interruptible transport | Medium |
| 301-400 | Secondary interruptible | Low |
| 401+ | Lowest priority services | Lowest |

**Business Rule**: Lower rank numbers receive capacity allocation before higher rank numbers when capacity is insufficient.

---

## Scheduled Capacity

### What is Scheduled Capacity?

**Scheduled Capacity** is the final determined quantity that will be scheduled for each nomination, scheduling object, and transaction group after considering all capacity constraints and business rules.

### Scheduling Process

**Step 1: Aggregate Nominated Quantities**
- Sum all nominated quantities by scheduling object
- Group by transaction group and rank
- Separate receipt and delivery quantities

**Step 2: Compare to Available Capacity**
- Retrieve **Operational Available Capacity (OAC)** for each scheduling object
- Compare total nominated quantities to OAC
- Identify over-nominated scheduling objects

**Step 3: Apply Reduction Logic (if needed)**
- If nominated > available, apply reduction algorithm
- Reduce quantities by transaction group rank (highest rank cut first)
- Apply proportional reduction within transaction groups
- Respect minimum quantity requirements

**Step 4: Calculate Scheduled Quantities**
- Determine final scheduled quantity for each nomination
- Update `CA_SUMMARY` table with scheduled quantities
- Generate scheduled capacity reports

### Scheduled vs Nominated Quantities

**Nominated Quantity**: What the shipper requested  
**Scheduled Quantity**: What will actually be transported  
**Cut Quantity**: Difference between nominated and scheduled (reduction amount)

**Example:**
```
Nomination A: 10,000 Dth (Nominated)
Segment Capacity: 8,000 Dth (Available)
Two nominations of equal priority

Result:
- Nomination A: 4,000 Dth (Scheduled) - 50% pro-rata reduction
- Nomination B: 4,000 Dth (Scheduled) - 50% pro-rata reduction
- Each cut by 6,000 Dth (60% reduction)
```

### Ratcheted Quantities

**Ratcheting** allows nominations to exceed contracted MDQ under certain conditions:

**Ratchet Conditions:**
- Previous cycle scheduled quantity exceeds current nominated quantity
- Ratchet provisions enabled in contract or TSP configuration
- Sufficient capacity available for ratcheted amount

**Business Rule**: Ratcheted quantities help maintain stable flow rates and reduce operational volatility by preventing large cycle-to-cycle changes.

---

## Capacity Reduction

### When is Reduction Needed?

**Capacity Reduction** occurs when total nominated quantities exceed available capacity for a scheduling object.

**Triggers:**
- Sum of nominations > Operational Available Capacity
- Physical pipeline constraints
- Contractual limitations
- Regulatory capacity limits

### Reduction Methods

**1. Transaction Group Rank Reduction**
- Process transaction groups in rank order (highest rank first)
- Cut lower priority groups before higher priority groups
- Within each rank, apply proportional reduction

**2. Pro-Rata Reduction**
- Reduce all nominations in a transaction group proportionally
- Each nomination cut by same percentage
- Maintains relative proportions between shippers

**3. First-Come-First-Served (FCFS)**
- Honor nominations in time-stamp order
- First submitted nominations scheduled in full
- Later nominations cut or denied

**4. Contract-Specific Reduction**
- Apply contract-specific reduction rules
- Consider contractual priority clauses
- Honor firm vs interruptible distinctions

### Reduction Order Example

```
Available Capacity: 100,000 Dth

Transaction Group A (Rank 100, Firm): 60,000 Dth nominated
Transaction Group B (Rank 200, Secondary): 40,000 Dth nominated  
Transaction Group C (Rank 300, Interruptible): 30,000 Dth nominated

Total Nominated: 130,000 Dth
Reduction Needed: 30,000 Dth

Reduction Process:
1. Group A (Rank 100): 60,000 Dth scheduled (no cut - highest priority)
2. Group B (Rank 200): 40,000 Dth scheduled (no cut - sufficient capacity)
3. Group C (Rank 300): 0 Dth scheduled (fully cut - lowest priority)

Result: 30,000 Dth cut from Group C only
```

### Reduction Algorithms

**Clay Basin Reduction**: Special algorithm for storage facilities
- Considers injection/withdrawal direction
- Applies basin-specific capacity rules
- Handles multi-side basin allocation

**MDQ Percentage Reduction**: Reduces based on % of contracted MDQ
- Nominations using higher % of MDQ cut first
- Preserves base capacity for all shippers
- Fair allocation when capacity tight

**Location Group Reduction**: Reduces across location groups
- Aggregates capacity across multiple locations
- Applies group-level reduction rules
- Considers location-specific constraints

---

## Rights Allocation

### What are Rights?

**Rights** determine how nominated quantities are categorized and allocated when capacity constraints exist. Rights classification affects priority and allocation rules during capacity reduction.

### Rights Categories

| Right Code | Name | Description | Business Purpose |
|------------|------|-------------|------------------|
| **P** | Primary | Within segment MDQ capacity | Highest priority - guaranteed capacity |
| **SI** | Secondary In Path | Available secondary capacity within segment path | Second priority - in-path secondary capacity |
| **SO** | Secondary Out of Path | Secondary capacity outside segment path | Third priority - out-of-path secondary capacity |
| **S** | Secondary | Any secondary capacity (SI + SO combined) | General secondary capacity |
| **N** | None/Overrun | Quantity exceeding contract MDQ | Lowest priority - excess capacity |

### Rights Allocation Logic

**Primary Rights (P)**:
- Quantity within the segment's MDQ capacity
- Guaranteed allocation (cannot be interrupted)
- Highest scheduling priority

**Secondary In Path Rights (SI)**:
- Available secondary capacity within the segment path
- Calculated as: `segMDQ - primaryMDQ`
- Second-highest priority after primary rights
- Only applies to locations (not segments)

**Secondary Out of Path Rights (SO)**:
- Secondary capacity outside the segment path
- Remaining contract capacity after primary and SI allocation
- Assigned when nominations are in opposite direction without primary rights
- Applies to opposite direction scenarios:
  - Nomination flows forward on segment but contract segments are 'B' (backward)
  - Nomination flows backward on segment but contract segments are 'F' (forward)
- Third priority in allocation hierarchy
- Does not require primary rights to exist
- Third priority in allocation hierarchy
- Does not require primary rights to exist

**Secondary Rights (S)**:
- Combined SI + SO capacity
- General secondary capacity category
- Used for overall secondary allocation calculations

**None/Overrun Rights (N)**:
- Nominated quantity exceeding contract MDQ
- Lowest priority - subject to complete reduction
- Represents capacity that cannot be scheduled

### Contract Location Matching Logic

**Critical Business Rule**: Primary rights allocation requires precise matching between nomination locations and contract location endpoints.

**Original Logic (Pre-Change)**:
```csharp
// Nomination gets primary rights ONLY if contract location exactly matches
if ((ctrLoc.IdLoc1 == nom.RecLoc && ctrLoc.IdLoc1 == SchdObjID) ||
    (ctrLoc.IdLoc2 == nom.DelLoc && ctrLoc.IdLoc2 == SchdObjID))
```
**Business Impact**: Strict matching ensures primary rights are only allocated to nominations that exactly match the contract's location configuration.

**Modified Logic (Current)**:
```csharp
// Nomination gets primary rights if EITHER receipt OR delivery location matches
if (nom.RecLoc == SchdObjID || nom.DelLoc == SchdObjID)
```
**Business Impact**: Permissive matching allows primary rights allocation to any nomination touching the scheduling object, potentially over-allocating primary capacity if contract locations don't align with nomination paths.

3. Apply Rights to Transaction Groups
   ├─→ Each transaction group has rights-based attributes
   ├─→ Nomination matches groups based on rights availability
   └─→ Rights determine allocation priority during reduction

4. Generate Scheduled Quantities
   └─→ Rights quantities become scheduled capacity allocations
```

### Business Rules for Rights

1. **Location vs Segment Logic**: SI rights only apply to locations, not segments
2. **Flow Direction Impact**: Opposite flow direction forces secondary out-of-path classification
3. **Capacity Hierarchy**: P > SI > SO > N (Primary takes precedence over all secondary)
4. **Contract Boundaries**: Rights cannot exceed contract MDQ limits
5. **Path Requirements**: SI rights require nomination to be within the segment path

### Rights in Capacity Reduction

**During Reduction Scenarios:**
- **Primary Rights**: Never reduced (guaranteed capacity)
- **Secondary In Path**: Reduced after primary rights fully allocated
- **Secondary Out of Path**: Reduced after SI rights allocated
- **None/Overrun**: Completely eliminated first

**Example Rights Allocation:**
```
Contract MDQ: 10,000 Dth
Segment MDQ: 8,000 Dth
Primary MDQ: 6,000 Dth
Nomination: 9,500 Dth

Rights Allocation:
- Primary (P): 6,000 Dth (within primary MDQ)
- Secondary In Path (SI): 2,000 Dth (segMDQ - primaryMDQ)
- Secondary Out of Path (SO): 1,500 Dth (remaining to contract MDQ)
- None (N): 500 Dth (exceeds contract MDQ)
```

### Rights and Transaction Groups

**Rights-Based Classification:**
- Transaction groups can specify rights requirements (P, SI, SO, etc.)
- Nominations match transaction groups based on available rights
- Rights determine which transaction group a nomination qualifies for
- Higher rights (P) match higher-priority transaction groups

**Business Impact:**
- Rights ensure fair capacity allocation
- Primary rights holders get guaranteed capacity
- Secondary rights provide overflow capacity
- Rights hierarchy prevents gaming of the system

---

## Operational Available Capacity

### What is Operational Available Capacity (OAC)?

**Operational Available Capacity (OAC)** is the actual capacity available for scheduling after considering:
- Physical pipeline capacity limits
- Operational constraints (pressures, temperatures, etc.)
- Maintenance and planned outages
- Contractual limitations
- Regulatory requirements

### OAC vs MDQ

| Concept | Definition | Scope | Changes |
|---------|------------|-------|---------|
| **MDQ** | Maximum Daily Quantity on a contract | Contract-specific | Rarely changes |
| **OAC** | Operational Available Capacity on a segment/location | System-wide | Can change daily |

**Key Difference**: MDQ is what a shipper contracted for; OAC is what the pipeline can physically deliver on a given day.

### OAC Calculation

**Factors Affecting OAC:**
- Physical pipeline capacity (diameter, pressure, compression)
- Temperature and gas composition
- Maintenance activities and outages
- Flow direction (forward vs backhaul)
- Regulatory capacity postings
- Real-time operational conditions

**Business Rule**: Scheduled quantities should never exceed OAC, even if total contracted MDQs exceed OAC.

### Staging OAC Data

**Process:**
1. Retrieve current OAC values for all scheduling objects
2. Store in staging table for scheduling cycle processing
3. Use staged OAC values for capacity reduction calculations
4. Update OAC if operational conditions change mid-cycle

---

## Business Workflows

### Daily Scheduling Workflow

```
Daily CAS Process:

1. Nomination Submission (Before Timely Deadline)
   └─→ Shippers submit nominations for gas day

2. Nomination Classification (After Timely Deadline)
   ├─→ Batch Process: QPSNomClassificationAndTransGroupingSeg
   ├─→ Classify nominations into transaction groups
   └─→ Store results in CASTAG_OBJ_NOM_TRANS_GRP

3. Operational Capacity Staging
   ├─→ Batch Process: QPSStageOperationalAvailableCapacity
   ├─→ Stage current OAC values
   └─→ Prepare for reduction calculations

4. Capacity Reduction (If Needed)
   ├─→ Batch Process: QPSSchedulingReductionSeg
   ├─→ Compare nominated vs available capacity
   ├─→ Apply reduction algorithms by transaction group rank
   └─→ Calculate scheduled quantities

5. CAS Summary Generation
   ├─→ Service: QPTMSchedulingService.GetSummarySchedulings
   ├─→ Generate CA_SUMMARY records
   ├─→ Calculate scheduled vs nominated quantities
   └─→ Prepare for submission to TSP

6. CAS Summary Review (Web UI)
   ├─→ Controller: CASummaryMaintenanceController
   ├─→ Users review scheduled quantities
   ├─→ Make manual adjustments if needed
   └─→ Approve for submission

7. Scheduled Capacity Submission
   ├─→ Submit scheduled quantities to TSP systems
   ├─→ Generate EDI transactions (if required)
   └─→ Update nomination status to "Scheduled"

8. Confirmation Receipt (After Flow Day)
   ├─→ Receive confirmations from TSP
   ├─→ Compare scheduled vs confirmed quantities
   └─→ Calculate variances for allocation
```

### Month-End Workflow

**Month-End Considerations:**
- Final scheduling for billing cycle
- Reconciliation of scheduled vs confirmed quantities
- Allocation of capacity variances
- Preparation for next month's capacity postings

### Special Handling Scenarios

**Scenario 1: Pipeline Maintenance**
- Reduce OAC for affected segments
- Re-run classification and reduction
- Notify affected shippers of cuts

**Scenario 2: Emergency Capacity Reduction**
- Issue operational flow order (OFO)
- Apply emergency reduction algorithms
- Prioritize critical service nominations

**Scenario 3: Capacity Release**
- Update contract capacity for released capacity
- Re-classify affected nominations
- Adjust scheduled quantities for replacement shippers

---

## Glossary

### Terms and Abbreviations

| Term | Definition |
|------|------------|
| **CAS** | Capacity Scheduling Allocations - the system for scheduling pipeline capacity |
| **OAC** | Operational Available Capacity - actual available capacity for a gas day |
| **MDQ** | Maximum Daily Quantity - contracted capacity limit |
| **TOS** | Type of Service - contract service classification (FT, IT, etc.) |
| **Transaction Group** | Logical grouping of nominations for scheduling purposes |
| **Rule Set** | Set of classification rules applied to nominations |
| **Scheduled Quantity** | Final quantity allocated after capacity reduction |
| **Nominated Quantity** | Quantity requested by shipper |
| **Cut Quantity** | Amount by which nomination was reduced (nominated - scheduled) |
| **Timely Cycle** | Primary nomination cycle for day-ahead scheduling |
| **Intraday Cycle** | Same-day nomination cycle for adjustments |
| **Ratchet** | Provision allowing quantity to exceed nominated amount |
| **Pro-Rata** | Proportional allocation/reduction method |
| **FCFS** | First-Come-First-Served allocation method |
| **Segment** | Physical section of pipeline between two points |
| **Classification** | Process of assigning nominations to transaction groups |
| **Reduction** | Process of cutting nominated quantities when capacity insufficient |
| **Staging Table** | Temporary table for intermediate CAS processing results |

### Related Processes

- **Nominations (NN)**: Input to CAS process
- **Confirmations (CF)**: Output validation of CAS scheduled quantities
- **Allocations (AL)**: Uses CAS results for actual flow allocation
- **Billing (BL)**: Uses CAS scheduled quantities for invoicing
- **EDI**: Exchanges CAS data with TSPs electronically

---

## Business Rules Summary

### Critical Business Rules

1. **Latest Cycle Priority**: Latest cycle nomination overrides earlier cycles for same nom ID
2. **Rank-Based Reduction**: Lower transaction group ranks receive capacity before higher ranks
3. **OAC Limit**: Scheduled quantities cannot exceed Operational Available Capacity
4. **MDQ Enforcement**: Nominated quantities should not exceed contract MDQ (without ratchet)
5. **Pro-Rata Fairness**: Within same transaction group, reductions are proportional
6. **Firm Priority**: Firm capacity nominations scheduled before interruptible
7. **Path Integrity**: Nominations must traverse valid pipeline paths
8. **TOS Matching**: Transaction group TOS filters must match nomination TOS
9. **Effective Date Validation**: Scheduling objects must be active for gas day
10. **Ratchet Conditions**: Ratcheted quantities require previous cycle scheduled > current nominated

---

## Related Documentation

- **Architecture**: [architecture.md](./architecture.md) - Technical implementation details
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- **QUICK_REFERENCE.md**: Feature mapping and keywords for CAS

---

*Last updated: 2025-12-30*  
*Document version: 1.0*
