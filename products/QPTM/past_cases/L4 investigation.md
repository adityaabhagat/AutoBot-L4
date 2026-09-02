# L4 Detailed Investigation Report

**Case:** 25-01041489 | **ADO Bug:** #1775092
**Date:** 2026-05-26 | **Investigator:** L4 Support Investigation Agent
**Product:** QPTM | **Module:** Nominations

---

## TABLE OF CONTENTS

1. [Case Overview](#1-case-overview)
2. [Issue Understanding](#2-issue-understanding)
3. [Issue Classification](#3-issue-classification)
4. [ADO Work Item #1775092 — Full Details](#4-ado-work-item-1775092--full-details)
5. [Root Cause Analysis (Deep Dive)](#5-root-cause-analysis-deep-dive)
6. [Code Analysis — Repository, PRs & Changed Files](#6-code-analysis--repository-prs--changed-files)
7. [Complete Source Code Walkthrough (RuleNN00009965.cs)](#7-complete-source-code-walkthrough-rulenn00009965cs)
8. [Historical Case Timeline](#8-historical-case-timeline)
9. [ADO Discussion Thread (28 Comments — Full Chronology)](#9-ado-discussion-thread-28-comments--full-chronology)
10. [Relevant Database Tables & Configuration](#10-relevant-database-tables--configuration)
11. [Version & Environment Analysis](#11-version--environment-analysis)
12. [Attachments Inventory](#12-attachments-inventory)
13. [Related ADO Work Items & Links](#13-related-ado-work-items--links)
14. [Email Communication Trail](#14-email-communication-trail)
15. [Release Note (Approved)](#15-release-note-approved)
16. [Configuration Validation Steps (SQL Queries)](#16-configuration-validation-steps-sql-queries)
17. [Technical Investigation Steps](#17-technical-investigation-steps)
18. [Recommended Solution & Deployment Path](#18-recommended-solution--deployment-path)
19. [Open Issue: Override MDQ vs CtrMdqDisplayOnly](#19-open-issue-override-mdq-vs-ctrmdqdisplayonly)
20. [Escalation Recommendation](#20-escalation-recommendation)
21. [Risk / Impact Analysis](#21-risk--impact-analysis)
22. [Key People & Roles](#22-key-people--roles)
23. [Summary & Next Steps](#23-summary--next-steps)

---

## 1. Case Overview

| Field | Value |
|-------|-------|
| **Case Number** | 25-01041489 |
| **Subject** | AOS - Nom Validation Error |
| **Client** | WWM Operating, LLC (Whitewater Midstream) |
| **Status** | In Development Queue |
| **Priority** | High |
| **Owner** | Aditya Bhagat |
| **Created** | 2025-09-09 |
| **Last Modified** | 2026-05-26 |
| **Origin** | Web |
| **Resolution** | *(Pending — fix developed, secondary MDQ source issue discovered in UAT)* |
| **Salesforce ID** | 500UG00000Ty6OVYAZ |
| **Account ID** | 0015f00000S2jy2AAB |

### Description (Verbatim from Salesforce)

> Validation for Authorized overrun has an error if the total delivered quantity is above the shared MDQ regardless of if the excess is scheduled as AOS or not.

---

## 2. Issue Understanding

### What the Client Reports

The AOS (Authorized Overrun Service) nomination validation (Rule NN00009965) fires an error whenever the total delivered quantity exceeds the shared MDQ (Maximum Daily Quantity), regardless of whether the excess volume is actually scheduled as AOS (Transaction Type 02) or not.

### Detailed Breakdown of the Problem

The validation `NN00009965` ("Total Del Exceed Shared Ctr MDQ Exclude Pool To Pool") is designed to:
- Fire when non-AOS nominations on a shared MDQ contract group exceed the combined MDQ limit
- **Exclude** Authorized Overrun (AOS) nominations (Transaction Type 02) from the total
- **Exclude** Pool-to-Pool transactions (where both receipt and delivery locations have "Allow Title Transfer" = true)

**What is actually happening (pre-fix):**
1. The validation sums ALL path nominations on the contract, **incorrectly including** pool-to-pool and AOS transactions
2. The validation error displays on nominations with **0 quantity**, confusing users since those nominations did not contribute to the overrun
3. The MDQ source field reads from `OvrdCtrMdq` which returns 0 on some contracts, instead of the correct `CtrMdqDisplayOnly` or the Override Contract MDQ
4. Users cannot identify which specific nomination actually exceeded the shared MDQ

### Expected vs Actual Behavior

| Scenario | Expected | Actual (Bug) |
|----------|----------|--------------|
| AOS nomination (TT 02) above MDQ | No validation error (AOS excluded) | Validation fires incorrectly |
| Pool-to-pool (ATT=true on both locs) | No validation error (pool-to-pool excluded) | Validation fires incorrectly |
| Non-AOS, non-pool nomination above MDQ | Validation fires with correct qty | Validation fires but shows 0 qty on wrong nomination |
| Override MDQ differs from Contract MDQ | Compare against Override MDQ | Compares against wrong MDQ source |

---

## 3. Issue Classification

| Category | Assessment | Confidence |
|----------|-----------|------------|
| **Configuration/Setup** | No — TSP configuration settings are correctly set | High |
| **Data Issue** | No — contract and location data is correct | High |
| **Existing Defect** | **YES — Primary classification** | Confirmed by Engineering |
| **Code Enhancement Limitation** | Partially — original enhancement did not handle all scenarios | Medium |
| **Product Behavior** | No — this is a deviation from intended behavior | High |
| **Root Cause Category (ADO)** | Pre-existing Issue | Confirmed |
| **Work Item Outcome** | Core Code Change | Confirmed |

---

## 4. ADO Work Item #1775092 — Full Details

### Core Fields

| Field | Value |
|-------|-------|
| **ADO ID** | [#1775092](https://dev.azure.com/QuorumSoftware/QuorumSoftware/_workitems/edit/1775092) |
| **Title** | WWM - 25-01041489 -- MDQ Validation Error Displays Incorrect Quantities for AOS Nominations |
| **Type** | Bug |
| **State** | Active |
| **Reason** | Closed in Error (re-activated 2026-05-15) |
| **Severity** | 2 - High |
| **Priority** | 2 |
| **Product** | QPTM |
| **Module** | Nominations |
| **Area Path** | QuorumSoftware > Engineering > Maintenance > Midstream and Transportation > Customer Service > Pirates of Pipeline |
| **Iteration Path** | QuorumSoftware > Product Development > 26.09 |

### Assignment & Ownership

| Field | Value |
|-------|-------|
| **Assigned To** | Kunal Ugale (kunal.ugale@quorumsoftware.com) |
| **Created By** | SVC Mulesoft Integrations |
| **Created Date** | 2026-01-08 |
| **Changed By** | Aditya Bhagat (aditya.bhagat@quorumsoftware.com) |
| **Activated By** | Desiree Martin (2026-05-15) |
| **Customer** | Whitewater Midstream |
| **Issue Source** | Customer Service |
| **OA Customer ID** | 465 |
| **Salesforce Case** | 25-01041489 |
| **Salesforce ID** | 500UG00000Ty6OVYAZ |

### Technical Classification

| Field | Value |
|-------|-------|
| **Found in Environment** | WWM_HD_DEVA1_QPTM |
| **Found in Version** | 2024.04 |
| **Found in DB Vendor** | MSSQL |
| **Test DB Vendor** | MSSQL |
| **Components Affected** | Services |
| **Testable in Core** | Yes |
| **Unit Testable** | Yes |
| **Unit Test Written** | Yes |
| **Discovery Testing Cycle** | Customer Production |
| **Impact** | 3 - Few |
| **Risk** | Medium |
| **Blocked** | No |

### Approval Status

| Field | Value |
|-------|-------|
| **Development Approved** | Yes |
| **Development Approved By** | Christine Lee |
| **Development Approved Date** | 2026-01-30 |
| **PM Prioritization** | Prioritization Pending |
| **Product Management Approval** | Approved |
| **Release Note Indicator** | Yes |
| **Release Note Approved** | Yes |
| **Tech Writer Approved** | Yes |
| **QA Approved** | Yes (Approved by QA tag) |
| **Documented in TestRail** | Yes |

### SLO Tracking

| Field | Value |
|-------|-------|
| **SLO Start Date** | 2026-01-08 |
| **SLO Activate Date** | 2026-02-11 |
| **SLO Closed Date** | 2026-04-24 |
| **Desired Date** | 2026-04-23 |
| **Blocked Date** | 2026-01-27 |

### Release Versions (Fix Available In)

| Version | Type | Notes |
|---------|------|-------|
| **2026.04.1.0** | Latest major release | Merged to develop |
| **2024.04.1.47** | Hotfix for 2024.04.x | Cherry-picked via PR #126984 to hotfix/17.30.41 |
| **2025.10.1.6** | Hotfix for 2025.10.x | Cherry-picked via PR #127254 to hotfix/17.34.1 |

### Repro Steps (from ADO)

1. Create a nomination. MDQ for contract A-407-FT3001 is 150,000. So 150,000 + 10,000 = 160,000 > MDQ — the validation is expected.
2. Add a new nomination with Rec Qty = 0. Validation NN00009965 fires even though the excess is Pool-to-Pool with ATT attribute on both receipt and delivery. The validation chose a nomination with 0 Qty to show on.

### Acceptance Criteria (from ADO)

- When the MDQ validation triggers, the Errors tab must display the **correct Receipt Quantity and Delivery Quantity** for the noms exceeding MDQ
- The validation should **NOT display zero or unrelated quantities** that did not contribute to the MDQ being exceeded
- Users must be able to **clearly identify which nomination exceeded the shared MDQ** from the error details
- QA is core-testable. See comments for repro steps.

### ADO Description (from Engineering)

> MDQ validation is incorrectly triggered when total delivered quantity exceeds the shared MDQ, even when the excess quantity is scheduled as Authorized Overrun (AOS). This issue was reproduced in both the WWM's env and Core.

---

## 5. Root Cause Analysis (Deep Dive)

### Root Cause (from ADO Engineering — Verbatim)

> Previously, Shared MDQ validation summed all path nominations on the contract (excluding only Authorized Overrun), which incorrectly included pool-to-pool and unrelated paths, which caused validation NN00009965 to trigger unexpectedly.

### Detailed Technical Root Cause

The root cause has **three dimensions**:

#### Dimension 1: Pool-to-Pool Nominations Not Excluded from Total

**What was wrong:** The `dTotalNomQty` calculation (the LINQ `.Sum()` query) did not filter out nominations where **both** the receipt and delivery locations have the "Allow Title Transfer" (ATT) location attribute set to `true`. These are pool-to-pool transactions that should never count toward the shared MDQ.

**Impact:** Pool-to-pool nominations with delivery quantities were being added to the total, causing the sum to exceed the shared MDQ threshold even when the actual eligible nominations were within limits.

#### Dimension 2: Validation Error Attached to Wrong Nomination

**What was wrong:** The validation loop iterated through all nominations and attached the error message to whichever nomination it happened to be processing at the time — even if that nomination had 0 quantity and was a pool-to-pool transaction. The error should only be attached to nominations that actually contribute to the MDQ exceedance.

**Impact:** Users saw validation errors on nominations with `RecQty = 0` and `DelQty = 0`, which was confusing and made it impossible to identify the actual problem nomination.

#### Dimension 3: MDQ Source Field Issue (Discovered Later in UAT)

**What was wrong:** The original code read the shared MDQ from `ctr.OvrdCtrMdq` (Override Contract MDQ). During L4 investigation, this field was returning `0` on the test contracts, so the fix switched to `ctr.CtrMdqDisplayOnly`. However, in WWM's UAT environment, the Override Contract MDQ is correctly populated with a different value (e.g., 250,000) than the Contract MDQ (e.g., 375,000). The validation should use `OvrdCtrMdq` when populated.

**Impact:** After the initial fix was deployed to UAT, Sara Riano reported (Case 26-01099290) that the validation was checking against the wrong MDQ value. This is the **remaining open issue**.

**Latest plan (per Christine Lee, 2026-05-18):** Revert the MDQ source field back to `OvrdCtrMdq` while keeping the pool-to-pool exclusion logic in place. Planned for next sprint (beginning of June 2026).

### Resolution Applied (from ADO)

> Updated the shared MDQ source and Exclude pool-to-pool nominations from the dTotalNomQty. The validation now evaluates only eligible nominations against the Shared MDQ. As a result, RuleNN00009965 now behaves as expected and only triggers when valid nominations exceed the configured Shared MDQ.

---

## 6. Code Analysis — Repository, PRs & Changed Files

### Repository

| Field | Value |
|-------|-------|
| **Repo Name** | Quorum.QPTM.Web |
| **Repo ID** | 41e317c0-844c-4728-98da-529092957738 |
| **Web URL** | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Web |
| **Default Branch** | develop |
| **Size** | ~191 MB |

### Pull Request #123210 — Initial Fix (Merged to develop)

| Field | Value |
|-------|-------|
| **PR Title** | Proposed fixes for validation RuleNN00009965 |
| **Status** | Completed |
| **Created By** | Aditya Bhagat |
| **Created Date** | 2026-02-05 |
| **Closed Date** | 2026-02-18 |
| **Closed By** | Kunal Ugale |
| **Source Branch** | `feature/NN00009965_pool-to-pool-exclusion1` |
| **Target Branch** | `develop` |
| **Merge Strategy** | Squash |
| **Merge Commit** | `1a1b1c0a50fa3d97db11fd463124ea9be5857da9` |
| **Reviewers** | Kunal Ugale (Approved), Midstream Repo Merge Admin (Approved) |

**Files Changed (2 files edited):**

| File Path | Change | Purpose |
|-----------|--------|---------|
| `Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/RuleNN00009965.cs` | Edit | Core validation logic fix — pool-to-pool exclusion + LINQ filter |
| `Quorum.QPTM.UnitTests/NominationSubmission/NominationSubmissionTests_NoContext.cs` | Edit | Unit test updates for the fix |

### Pull Request #126984 — Cherry-pick to 2024.04 Hotfix

| Field | Value |
|-------|-------|
| **PR Title** | Proposed fixes for validation RuleNN00009965 [Quorum.QPTM.Web] [2024.04] |
| **Description** | Cherry-pick from !123210. UT not added since already on develop |
| **Status** | Completed |
| **Created By** | Geetali Bendale |
| **Created Date** | 2026-04-24 |
| **Closed Date** | 2026-04-24 |
| **Closed By** | Geetali Bendale |
| **Source Branch** | `feature/NN00009965_pool-to-pool-exclusion1-on-hotfix-17.30.41` |
| **Target Branch** | `hotfix/17.30.41` |
| **Merge Strategy** | Squash |
| **Merge Commit** | `4e2ba84281d13f3907b6d39a0371af5ec506e7d5` |
| **Reviewers** | Chetan Chauhan (Approved), Midstream Repo Merge Admin (Approved) |

**Files Changed (5 files — 4 edits + 1 add):**

| File Path | Change | Purpose |
|-----------|--------|---------|
| `Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/RuleNN00009965.cs` | Edit | Core validation fix (cherry-picked) |
| `Quorum.QPTM.Validations/QRuleDataNominationBase.cs` | **Add (new)** | New base class with cached lookups for contract, location, and attribute data |
| `Quorum.QPTM.Validations/QRuleDataNominationBusiness.cs` | Edit | Updated to inherit from new base class |
| `Quorum.QPTM.Validations/Quorum.QPTM.Validations.csproj` | Edit | Added new file reference |
| `Quorum.QPTM.UnitTests/NominationSubmission/NominationSubmissionTests.cs` | Edit | Unit test updates |

### Pull Request #127254 — Cherry-pick to 2025.10 Hotfix

| Field | Value |
|-------|-------|
| **PR Title** | Pool-to-pool exclusion on hotfix-17.34.1 |
| **Status** | Completed |
| **Source Branch** | `feature/NN00009965_pool-to-pool-exclusion1-on-hotfix-17.34.1` |
| **Target Branch** | `hotfix/17.34.1` |
| **Merge Commit** | `964889009bc939f62478378d094f401204cb8aa1` |

### All Fixed Commits

| # | Commit SHA | Date | Author/Committer | PR | Target Branch |
|---|-----------|------|-------------------|-----|---------------|
| 1 | `1a1b1c0a50fa3d97db11fd463124ea9be5857da9` | 2026-02-18 | Aditya Bhagat / Kunal Ugale | #123210 | develop |
| 2 | `4e2ba84281d13f3907b6d39a0371af5ec506e7d5` | 2026-04-24 | Geetali Bendale | #126984 | hotfix/17.30.41 (2024.04) |
| 3 | `964889009bc939f62478378d094f401204cb8aa1` | 2026-04-28 | — | #127254 | hotfix/17.34.1 (2025.10) |
| 4 | `c218e084a99e158d18a2e012b6ee167470f01e23` | 2026-04-28 | — | — | Additional fix |

### Build Integration

| Build ID | Date | Notes |
|----------|------|-------|
| #751175 | 2026-02-18 | First integration |
| #751348 | 2026-02-18 | — |
| #751390 | 2026-02-18 | — |
| #751428 | 2026-02-18 | — |
| #751681 | 2026-02-19 | — |
| #752150 | 2026-02-20 | — |
| #774085 | 2026-04-16 | — |
| #774795 | 2026-04-17 | — |
| #775136 | 2026-04-17 | — |
| #778259 | 2026-04-24 | Hotfix build |
| #778291 | 2026-04-24 | Hotfix build |
| #778317 | 2026-04-24 | Hotfix build |
| #779753 | 2026-04-28 | — |
| #782773 | 2026-05-05 | — |
| #787637 | 2026-05-15 | — |
| #788329 | 2026-05-18 | Latest |
| #788334 | 2026-05-18 | Latest |

---

## 7. Complete Source Code Walkthrough (RuleNN00009965.cs)

### File Location
`Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/RuleNN00009965.cs`

### Class Hierarchy
```
ValidationRuleBaseNominationBusiness
  └── RuleNN00009965
```

### Dependencies (Injected)
- `IMetadataCacheAccess` — Metadata lookup
- `ICycleCacheAccess` — Cycle data access
- `IContractCacheAccess` — Contract data (for related contracts)
- `IQPTMServiceInterface_TosNomValid` — TOS nomination validation service
- `IQValidationRuleHelper` — Helper for adding validation errors
- `ITspCacheAccess` — TSP configuration settings lookup

### Core Method: `Validate()`

**Signature:**
```csharp
public override bool Validate(IList<ActivityDetailDO> nominationCollection, DateTime begGasDay, QRuleDataNominationBusiness ruleData)
```

### Step-by-Step Logic Flow (Fixed Version)

**Step 1: Input Validation**
- Returns `false` if `nominationCollection` or `ruleData` is null

**Step 2: Initialize Tracking Structures**
- `ctrRelationMap` — Dictionary tracking processed contracts and their shared MDQ partners
- `sLocAttr` — Location attribute filter (from TSP config)
- `sTransTypeExclude` — Transaction type to exclude (from TSP config)
- `dSharedCtrQty` — Shared MDQ quantity threshold

**Step 3: For Each Nomination (Main Loop)**

3a. **Skip non-path records** — Only process nominations where `IsPathRecord == true`

3b. **Load TSP Configuration** — Reads two config keys per nomination's TSP:
- `NOM_RULE_NN00009965_LOC_ATTR_FILTER` → e.g., "Allow Title Transfer"
- `NOM_RULE_NN00009965_TRANS TYPE_FILTER` → e.g., "02"
- If loc attr config is null, skip this nomination

3c. **Pool-to-Pool Check (NEW FIX)** — For each location attribute in the comma-separated filter:
- Check if **receipt location** has ATT = true (`ruleData.IsLocationAttributeTrue()`)
- Check if **delivery location** has ATT = true
- If BOTH are true → **skip** (pool-to-pool, `continue`)

3d. **AOS Exclusion** — If `nom.TransTypeCode == sTransTypeExclude` (i.e., "02") → **skip** (`continue`)

3e. **Contract Relationship Lookup** — If contract not yet processed:
- Get the contract via `ruleData.GetContract()`
- Read `dSharedCtrQty = ctr.CtrMdqDisplayOnly` (this is the field being reconsidered)
- Skip if shared MDQ is not set or < 0
- Only process FTS or FTS-311 contracts
- Look up related contracts with `RelatedCtrRsnCode == "SharedMDQ"`
- Build the `ctrRelationMap`

3f. **Calculate Total Nomination Quantity (FIXED LINQ):**
```csharp
dTotalNomQty = nominationCollection
    .Where(x => (x.SrCtrNo == ctr.CtrNo || x.SrCtrNo == sRelCtrNo)
                && x.TransTypeCode != sTransTypeExclude        // Exclude AOS (TT 02)
                && x.IsPathRecord                               // Only path records
                && !(/* pool-to-pool check:
                      both receipt and delivery locations have
                      ALL specified ATT attributes = true */))
    .Sum(x => x.DelQty);
```

3g. **Compare Against Threshold:**
- If `dTotalNomQty > dSharedCtrQty` → Validation fails
- Error is attached to the current nomination via `ValidationRuleHelper.AddErrorToNomination()`
- Nomination status set to `BusinessInvalid`

### New Base Class: QRuleDataNominationBase.cs

Extracted from `QRuleDataNominationBusiness` to provide **cached lookups** that improve performance:

| Method | Purpose | Cache Key Format |
|--------|---------|-----------------|
| `GetContract()` | Cached contract lookup | `{CtrNo}_{TspNo}_{Date}` |
| `IsLocationAttributeTrue()` | Cached location attribute check | `{AttrName}_{LocId}_{TspNo}_{Date}` |
| `IsContractAttributeTrue()` | Cached contract attribute check | `{AttrName}_{CtrNo}_{TspNo}_{Date}` |
| `IsPathOnContract()` | Cached path-on-contract validation | `{RecLoc}_{DelLoc}_{RouteCode}_{CtrNo}_{Date}` |

**Internal caches:**
```csharp
private Dictionary<string, ContractDO> m_ContractCache
private Dictionary<string, bool> m_LocationAttributeCache
private Dictionary<string, bool> m_ContractAttributeCache
private Dictionary<string, bool> m_PathOnContractCache
```

---

## 8. Historical Case Timeline

### Complete Chronological View

```
2023-07-06  Case 23-00909370 created — "WWM - Nomination validation for AOS noms" (Enhancement)
   │        Requirements: Fire when shipper exceeds shared MDQ for TT 02 paths.
   │        Exclude pool-to-pool (ATT=true). Account for shared MDQ between contracts.
   │
2024-08-29  Case 24-00977780 created — "Patch 3 / Hotfix 3 October 2024"
   │        Bundled AOS nom validation with billing charge basis cases.
   │
2025-05-06  Case 25-01018455 created — "Nomination Validation NN00009965 for AOS Failing"
   │        FIRST BUG REPORT. Same client (WWM). Same exact issue.
   │        "Validation showing errors for any nominations over shared MDQ regardless of
   │        transaction or location type."
   │        Status: Closed - No Response. No confirmed resolution.
   │
2025-09-09  Case 25-01041489 created — "AOS - Nom Validation Error" (THIS CASE)
   │        Detailed testing docs attached by Scheduling Team.
   │
2025-09-17  Attachment: "AOS - Nom Validation 02" uploaded
2025-09-22  Attachment: "AOS - Nom Validation 02 & ATT" uploaded
2025-12-12  Attachment: "25-01041489 WWM Before Walkthrough" uploaded by Aditya Bhagat
2025-12-17  SF Task: "AOS - Nom Validation Error" completed by Anas Shaikh
   │
2026-01-08  ADO #1775092 created (via Mulesoft integration)
2026-01-09  Abhijit Todkar asks for Core repro confirmation
2026-01-12  Aditya Bhagat confirms repro in WWM_HD_DEVA1 and MSSQL2019_HD_MID_R1_SUP17
2026-01-12  Christine Lee requests L4 team review
2026-01-13  Anas Shaikh begins code change work
2026-01-15  Anas confirms Core validation works correctly (150000 qty displays correctly)
2026-01-16  Christine Lee asks about overridability as interim workaround
2026-01-27  Anas identifies the wrong-nomination-display issue
2026-01-27  Aditya Bhagat reproduces: validation triggers for RecQty/DelQty = 0 (incorrect)
2026-01-28  SF Task: "ADO #1775092 - Engineering as for L4 review" created
2026-01-28  Desiree Martin creates L4 worksheet task
2026-01-30  Anas Shaikh demonstrates fix: correct Rec/Del QTY now shown in error tab
2026-01-30  Christine Lee approves development
   │
2026-02-02  Anas uploads "L4 Triaged walkthrough" to ADO
2026-02-03  Anas requests pool-to-pool test case in web
2026-02-03  Aditya Bhagat clarifies pool-to-pool exclusion requirement
2026-02-05  Aditya Bhagat identifies root cause, implements fix, uploads code analysis doc
   │        "Shared MDQ was being read from ctr.OvrdCtrMdq (returning 0), pool-to-pool
   │        nominations were incorrectly included in dTotalNomQty"
2026-02-05  PR #123210 created → feature/NN00009965_pool-to-pool-exclusion1
2026-02-11  Christine Lee summarizes the fix and asks for QA
2026-02-18  PR #123210 merged to develop (squash merge by Kunal Ugale)
   │
2026-04-16  Vaishnavi Kolhe encounters issues during testing, Aditya assists
2026-04-21  Christine Lee flags this for Friday hotfix
2026-04-22  Vaishnavi Kolhe verifies fix on MSSQL RELQA env — PASSES
   │        "RuleNN00009965 now behaves as expected"
2026-04-24  PR #126984 created and merged → hotfix/17.30.41 (2024.04 cherry-pick)
2026-04-28  PR #127254 created and merged → hotfix/17.34.1 (2025.10 cherry-pick)
2026-04-28  Kunal confirms consumption for 2026.04 and 2025.10
   │
2026-05-07  Case 26-01099290 created — "AOS Nom Validation"
   │        UAT reveals MDQ source field issue: checking Contract MDQ instead of Override MDQ
   │        Closed: "Tied to Hotfix and patch deployed will be taken over case #25-01041489"
2026-05-07  Attachment: "AOS - Nom Validation - MDQ" uploaded by Scheduling Team
2026-05-08  Sara Riano emails client about ongoing review
2026-05-08  Sara Riano asks engineering to recheck MDQ source field issue
   │
2026-05-13  Christine Lee identifies the OvrdCtrMdq vs CtrMdqDisplayOnly discrepancy
   │        "OvrdCtrMdq was returning 0 on test contracts... Sara's testing contract
   │        M-403-FT001 has Override Contract MDQ set to 250,000"
2026-05-15  Desiree Martin re-activates ADO #1775092 (was closed in error)
2026-05-18  Christine Lee: "Plan is to revert MDQ source field back to OvrdCtrMdq while
   │        keeping pool-to-pool exclusion. Planned for next sprint (early June 2026)"
2026-05-26  Aditya Bhagat acknowledges plan, will keep client informed
```

### Related Cases Detail

#### Case 23-00909370 — Original Enhancement

| Field | Value |
|-------|-------|
| **Case Number** | 23-00909370 |
| **Subject** | WWM - Nomination validation for AOS noms |
| **Status** | Complete - Pending Delivery |
| **Created** | 2023-07-06 |
| **Owner** | Allison Brassette |
| **Resolution** | "Had to develop a nomination validation" |
| **Requirements** | Fire when shipper exceeds shared MDQ contract qty for TT 02 paths only. Account for shared MDQ between two contracts. Exclude pool-to-pool (ATT = true). Leverage existing Enterprise nom validations. |

#### Case 25-01018455 — First Bug Report

| Field | Value |
|-------|-------|
| **Case Number** | 25-01018455 |
| **Subject** | Nomination Validation NN00009965 for AOS Failing |
| **Status** | Closed - No Response |
| **Created** | 2025-05-06 |
| **Owner** | Abhijit Pradhan |
| **Description** | "Nomination Validation is showing errors for any nominations over shared MDQ regardless of transaction or location type. The validation should be excluding any locations with ATT, and any Authorized Overrun transactions (02)." |
| **Relevance** | Same exact issue. Closed without confirmed resolution. |

#### Case 24-00977780 — Hotfix Delivery

| Field | Value |
|-------|-------|
| **Case Number** | 24-00977780 |
| **Subject** | Patch 3 / Hotfix 3 October 2024 |
| **Status** | Closed |
| **Created** | 2024-08-29 |
| **Included Cases** | 23-00909370 (AOS Nom Validation), 23-00909368 (AOS MDQ Billing), 23-00924888 (AOS MSQ), 23-00924889 (AOS MDIQ), 23-00924891 (AOS MDWQ), 24-00977086 (Fail Storage AutoGen), 24-00977712 (CAS bug) |

#### Case 26-01099290 — UAT MDQ Source Issue

| Field | Value |
|-------|-------|
| **Case Number** | 26-01099290 |
| **Subject** | AOS Nom Validation |
| **Status** | Closed |
| **Created** | 2026-05-07 |
| **Owner** | Sara Riano |
| **Description** | "The new AOS validation was deployed to UAT, but it seems to be checking against the Contract MDQ instead of the Override Contract MDQ. This is causing incorrect flagging when there is a mismatch between the two." |
| **Resolution** | "Tied to Hotfix and patch deployed will be taken over the case #25-01041489., Not critical" |

---

## 9. ADO Discussion Thread (28 Comments — Full Chronology)

### Comment 1 — 2026-01-09 | Abhijit Todkar
Was this reproduced on Core/dev env? Please add the details.

### Comment 2 — 2026-01-12 | Aditya Bhagat
This issue has been successfully reproduced in the WWM_HD_DEVA1 environment. This issue is reproducible in the MSSQL2019_HD_MID_R1_SUP17 environment. The Northwest Pipeline Interconnect has ATT set to False, while Tecto Del 1 has ATT set to True.

### Comment 3 — 2026-01-12 | Christine Lee
Can the L4 team review this one? CC Aditya Bhagat, Abhijit Todkar

### Comment 4 — 2026-01-13 | Anas Shaikh
I am working on the testing by implementing a code change to the validation rule NN00009965.

### Comment 5 — 2026-01-15 | Anas Shaikh
The validation rule NN00009965 is working as expected in CORE: When I submitted nominations for Svc req 1 with qty 150000, the nominations were submitted with a BI error NN00009965. Again, I submitted 0 qty noms and observed that 150000 is displayed on the error tab for rule NN00009965. Core is working as expected.

### Comment 6 — 2026-01-16 | Christine Lee
Are you both testing differently, or Anas, is that with your suggested code change? Regardless, can they override the error in the meantime? They can adjust this in validation rule assignment by making the error 'overridable'.

### Comment 7 — 2026-01-22 | Christine Lee
Bumping this

### Comment 8 — 2026-01-26 | Desiree Martin
Can you please provide an update on this blocked item for next steps?

### Comment 9 — 2026-01-27 | Anas Shaikh
I tested this in MSSQL_CORE_HD_MID_DEV17 without code change and the issue is not reproducible. When I submitted the noms, the first nomination ID got picked up in the error with correct REC and DEL QTY, which is the expected behavior. Also, this rule ID NN00009965 was originally created only for WWM.

### Comment 10 — 2026-01-27 | Aditya Bhagat
I switched the values in MSSQL_CORE_HD_MID17. I set the Rec Qty to 0 for the Rec Loc Northwest Pipeline Interconnect and set the Rec Qty to 143,000 for Tetco Del, which exceeds the Total MDQ(103000). After that, I noticed the validation was triggering for Rec Qty and Del Qty = 0, which is incorrect. The validation "Total Del exceed shared CTR MDQ excl Pool to Pool and Auth Ovrn" (NN00009965 Wrong Nom) is firing correctly when the aggregate Del Qty exceeds the shared CTR MDQ. However, the validation is showing on the wrong nomination.

### Comment 11 — 2026-01-27 | Anas Shaikh
So we need the error to point to the exceeded QTY NOM ID instead of the top most nom ID. I will be working on the code change for this requirement and will update soon.

### Comment 12 — 2026-01-28 | Desiree Martin
I created the task and added to the L4 worksheet.

### Comment 13 — 2026-01-30 | Anas Shaikh
After the code change in RULENN00009965, the validation shows correct Rec and Del QTY in the error tab. Step 1: Submit 3 PNT nominations with the 0 qty nomination on top, followed by a qty nom (150) and an 80 qty. STEP 2: I've excluded the 0 qty noms in the code change and for each noms over the shared MDQ, there will be a validation error. I am preparing a detailed L4 walkthrough document with the suggested code change.

### Comment 14 — 2026-02-02 | Anas Shaikh
I have attached the L4 Triaged walkthrough.

### Comment 15 — 2026-02-03 | Aditya Bhagat
As per the add-on to this issue, the NN00009965 is being triggered for Pool-to-Pool nominations (both receipt and delivery locations have ATT = true). As per the requirement, Pool-to-Pool nominations should be excluded from Shared/Override MDQ validation, their quantities should not be counted toward total nominated delivery, and NN00009965 should not trigger in this scenario.

### Comment 16 — 2026-02-03 | Anas Shaikh
So I believe we need to take into consideration the pool-to-pool case scenario. Can we have a test case reproduced in web where there is a pool to pool nomination that is triggering the validation?

### Comment 17 — 2026-02-05 | Aditya Bhagat
I was able to identify the root cause and implemented code changes to fix validation RuleNN00009965, and it is now working as expected. The Shared MDQ is now pulled from `ctr.CtrMdqDisplayOnly`, and pool-to-pool nominations are excluded from `dTotalNomQty`. I have also created documentation covering all code changes and suggestions.

**Root cause identified:** Shared MDQ was being read from `ctr.OvrdCtrMdq` (returning 0), and pool-to-pool nominations were incorrectly included in `dTotalNomQty`.

### Comment 18 — 2026-02-11 | Christine Lee
**Summary:** An MDQ validation error was triggered by the wrong nomination, sometimes appearing on a record with zero quantity, making it look wrong to users. PR fix in place from L4 team with change details. Ask is to review and QA that validation RuleNN00009965 works according to the acceptance criteria.

### Comment 19 — 2026-04-16 | Vaishnavi Kolhe
Update: I am facing some issues so Aditya is looking into this.

### Comment 20 — 2026-04-21 | Christine Lee
I saw this was already active but just FYI, this is needed for a Friday HF. Please let me know if there's any blockers that would prevent this from completing.

### Comment 21 — 2026-04-22 | Vaishnavi Kolhe
Verified on MSSQL RELQA env. RuleNN00009965 now behaves as expected and only triggers when valid nominations exceed the configured Shared MDQ.

**Data used:** CTR - 1818, Shared MDQ - 2000, Rec Loc 0168193 - Non-pool (ATT unchecked), Del Loc 11180 - Pooling Loc (ATT Checked). 2nd pool to pool nomination is correctly excluded from Ctr shared MDQ and error is displayed for correct non-pool nomination. When the MDQ validation triggers, the Errors tab must display the correct Rec Qty and Del Qty.

### Comment 22 — 2026-04-28 | Kunal Ugale
Consumed in for 2026.04 and 2025.10. Let me know if want to cherry pick for other versions.

### Comment 23 — 2026-05-08 | Sara Riano
Can you kindly double-check this item from the functional/code side? The customer got back to us seeing a different behavior. I attached the WI testing they performed in UAT. Contract M-403-FT001 on Matterhorn — Contract MDQ is 375,000, but the Override Contract MDQ is set lower at 250,000. The validation flags an error when the nominated quantity exceeds Contract MDQ rather than Override MDQ.

### Comment 24 — 2026-05-13 | Aditya Bhagat
Just following up on this one. Please let me know if there are any updates or if anything is needed from my side regarding this issue.

### Comment 25 — 2026-05-13 | Christine Lee
The original walkthrough fix (correct nomination showing in errors tab) looks resolved. However Sara's UAT is about the source field. Aditya, in your investigation, the `OvrdCtrMdq` was returning 0 on the contracts you tested, which led to switching to `CtrMdqDisplayOnly`. Sara's testing contract M-403-FT001 has the Override Contract MDQ set to 250,000. Can you confirm whether `OvrdCtrMdq` wasn't populated on the test contracts used during investigation? If so, `OvrdCtrMdq` may be the correct field when populated.

### Comment 26 — 2026-05-15 | Desiree Martin
Bubbling this one back up, can we please get a status update and/or ETA?

### Comment 27 — 2026-05-18 | Christine Lee
The plan is to revert the MDQ source field back to `OvrdCtrMdq` while keeping the pool-to-pool exclusion logic in place. This is planned for next sprint, so expect this closer to the beginning of June. We'll keep you posted!

### Comment 28 — 2026-05-26 | Aditya Bhagat
Thank you for the update. Appreciate the clarification and the effort from the engineering team on this issue. We will keep the client informed and look forward to the changes planned for the next sprint.

---

## 10. Relevant Database Tables & Configuration

### Database Tables

| Table | Purpose | Key Columns | What to Verify |
|-------|---------|-------------|----------------|
| **NominationValidation** | Validation rule definitions | RuleId, RuleName, Active, ErrorLevel | Find NN00009965, check active status, check if set to Error or Warning/Overridable |
| **ActivityDetail** | Nomination records at path level | SrCtrNo, TransTypeCode, RecQty, DelQty, IdRecLoc, IdDelLoc, NomStatCode, IsPathRecord | Check quantities, transaction types, location IDs for affected nominations |
| **Contract** | Contract definitions with MDQ | CtrNo, AmendNo, TspNo, TosCode, CtrMdqDisplayOnly, OvrdCtrMdq | Compare CtrMdqDisplayOnly vs OvrdCtrMdq for M-403-FT001 and A-407-FT3001 |
| **RelatedContract** | Shared MDQ contract links | CtrNo, AmendNo, RelatedCtrNo, RelatedCtrRsnCode | Verify SharedMDQ relationships |
| **ContractLocation** | Contract path definitions | CtrNo, IdLoc1, IdLoc2, IdLocGrp1, IdLocGrp2, RouteCode | Verify path configuration |
| **LocationAttribute** | Location metadata | IdLoc, TspNo, AttributeName, AttributeValue | Verify "Allow Title Transfer" = true for pool locations |
| **TspConfigurationControl** | TSP-level config | TspNo, ModuleCode, KeyName, KeyValue | Verify NOM_RULE_NN00009965_* settings |
| **GlobalConfigurationControl** | Global config | ModuleCode, KeyName, KeyValue | Check VALIDATE_IGNORE_ROUTE_CODE |
| **TransactionType** | TT code definitions | TransTypeCode, TransTypeDesc | Confirm TT 02 = Authorized Contract Overrun |

### Key Configuration IDs & References

| Configuration | Value | Notes |
|--------------|-------|-------|
| **Nomination Validation Rule ID** | NN00009965 | Core rule being fixed |
| **Validation Full Name** | Total Del Exceed Shared Ctr MDQ Exclude Pool To Pool | — |
| **Transaction Type Filter** | 02 | Authorized Contract Overrun / AOS |
| **Location Attribute Filter** | Allow Title Transfer (ATT) | Pool location identifier |
| **TSP Config Key (Loc Attr)** | `NOM_RULE_NN00009965_LOC_ATTR_FILTER` | Module: NOMINATIONS |
| **TSP Config Key (Trans Type)** | `NOM_RULE_NN00009965_TRANS TYPE_FILTER` | Module: NOMINATIONS |
| **Contract (Test 1)** | A-407-FT3001 | MDQ = 150,000 |
| **Contract (UAT Test)** | M-403-FT001 | Contract MDQ = 375,000; Override MDQ = 250,000 |
| **Contract TOS Codes** | FTS, FTS-311 | Only these TOS codes trigger the rule |
| **Related Contract Reason** | SharedMDQ | Links shared MDQ contract pairs |
| **Test Rec Location** | Northwest Pipeline Interconnect | ATT = False |
| **Test Del Location** | Tecto Del 1 | ATT = True |
| **QA Test CTR** | 1818 | Shared MDQ = 2000 |
| **QA Rec Loc** | 0168193 | Non-pool (ATT unchecked) |
| **QA Del Loc** | 11180 | Pooling Loc (ATT Checked) |
| **TestRail Case** | [#89357](https://quorumsoftware.testrail.io/index.php?/cases/view/89357) | Documented test case |

---

## 11. Version & Environment Analysis

| Item | Value |
|------|-------|
| **Client Current Version** | 2024.04 (per ADO "Found in Version") |
| **Client Environment** | WWM_HD_DEVA1_QPTM |
| **Issue Reproduced in Core** | Yes (MSSQL2019_HD_MID_R1_SUP17, MSSQL_CORE_HD_MID_DEV17) |
| **Database Vendor** | MSSQL |
| **Fix Available in Version** | **2024.04.1.47** (hotfix), **2025.10.1.6** (hotfix), **2026.04.1.0** (major) |
| **Fix Status** | Pool-to-pool exclusion: COMPLETE. MDQ source field: PENDING (next sprint, June 2026) |
| **Current ADO State** | Active (re-activated 2026-05-15 by Desiree Martin) |
| **ADO Iteration** | 26.09 |

### Deployment Path

| If Client Is On... | Deploy... | Branch |
|---------------------|-----------|--------|
| 2024.04.x | Hotfix **2024.04.1.47** | hotfix/17.30.41 |
| 2025.10.x | Hotfix **2025.10.1.6** | hotfix/17.34.1 |
| Upgrade path | **2026.04.1.0** | develop |

**Note:** The MDQ source field revert (`OvrdCtrMdq` instead of `CtrMdqDisplayOnly`) is planned for the next sprint (early June 2026) and will require an additional hotfix cycle.

---

## 12. Attachments Inventory

### Salesforce Case Attachments (6)

| # | Title | Type | Size | Date | Author | SF Content ID |
|---|-------|------|------|------|--------|---------------|
| 1 | AOS - Nom Validation & Billing Charge Testing | docx | 1.0 MB | 2025-09-09 | Scheduling Team | 068UG00000R2Q8YYAV |
| 2 | AOS - Nom Validation 02 | docx | 374 KB | 2025-09-17 | Scheduling Team | 068UG00000RRColYAH |
| 3 | AOS - Nom Validation 02 & ATT | docx | 664 KB | 2025-09-22 | Scheduling Team | 068UG00000RfxvpYAB |
| 4 | 25-01041489 WWM Before Walkthrough | docx | 1.9 MB | 2025-12-12 | Aditya Bhagat | 068UH00000dKtZlYAK |
| 5 | AOS - Nom Validation - MDQ | docx | 330 KB | 2026-05-07 | Scheduling Team | 068UH00000m3cOiYAI |
| 6 | Case Analysis - 25-01041489 | html | 60 KB | 2026-05-07 | Claude Integration User | 068UH00000m43rrYAA |

### ADO Work Item Attachments (5)

| # | Title | Size | Date |
|---|-------|------|------|
| 1 | 25-01041489 WWM Before Walkthrough_L4-Triaged.docx | 2.6 MB | 2026-02-02 |
| 2 | WWM Nomination Validations AOS - Design.docx | 1.8 MB | 2026-02-03 |
| 3 | WWM Nom-Validation Dev Walkthrough.docx | 7.7 MB | 2026-02-03 |
| 4 | AOS Validation rule technical analysis & code change suggestion.docx | 2.6 MB | 2026-02-05 |
| 5 | AOS - Nom Validation - MDQ.docx | 330 KB | 2026-05-08 |

---

## 13. Related ADO Work Items & Links

### Child Tasks of #1775092

| ADO ID | Type | Title | State | Assigned To |
|--------|------|-------|-------|-------------|
| #1801107 | Task | — | Closed (Rejected) | Vaishnavi Kolhe |
| #1795572 | Task | — | Closed | Kunal Ugale |
| #1781979 | Task | — | Closed | Kunal Ugale |
| #1808122 | Task | — | *(Access restricted — QuorumServices project)* | — |

### Related Work Items

| ADO ID | Relation | Notes |
|--------|----------|-------|
| #1785465 | Related | Sara Riano mentioned #1775092 |
| #1801936 | Related | Branch tracker link |
| #1781977 | Related | — |
| #1809326 | Related | Branch tracker link |
| #1791810 | Related | Kseniia Mykhailova mentioned #1775092 (QuorumServices project) |
| #1748342 | Related | — |
| #1799867 | Related | Branch tracker link |

---

## 14. Email Communication Trail

### Salesforce Emails on Case 25-01041489

| Date | From | To | Subject | Summary |
|------|------|----|---------|---------|
| 2026-05-08 | Sara Riano (transportation.support@quorumsoftware.com) | quorumsupport@wwm-llc.com; jsoileau@wwm-llc.com; sshipos@wwm-llc.com; aditya.bhagat@quorumsoftware.com; lreece@wwm-llc.com; desiree.martin@quorumsoftware.com; max@wwm-llc.com | AOS - Nom Validation Error | Currently reviewing. Verifying packaging and whether Engineering should conduct additional evaluation. Will refer to Engineering after packaging verification. |
| 2026-05-08 | Darren Mosier (Auto-reply) | — | Automatic reply | Out at conference through Thursday. |

---

## 15. Release Note (Approved)

| Field | Content |
|-------|---------|
| **Title** | MDQ Validation Error (NN00009965) Now Correctly Excludes Authorized Overrun (AOS) Nominations |
| **Scope** | Nomination Submission, MDQ Validation (NN00009965) |
| **Release Note** | The validation now evaluates only eligible nominations against the Shared MDQ and only triggers when valid nominations exceed the configured Shared MDQ. |
| **Implementation Details** | Configured by Nomination Validation (NN00009965: Total Del Exceed Shared Ctr MDQ Exclude Pool To Pool) |
| **Approved** | Yes (Release Note Approved + Tech Writer Approved) |

---

## 16. Configuration Validation Steps (SQL Queries)

### Step 1: Verify TSP Configuration Settings
```sql
-- Check TSP config for the AOS validation rule
SELECT TspNo, ModuleCode, KeyName, KeyValue
FROM TspConfigurationControl
WHERE TspNo = [WWM_TSP_NUMBER]
  AND ModuleCode = 'NOMINATIONS'
  AND KeyName IN (
    'NOM_RULE_NN00009965_LOC_ATTR_FILTER',
    'NOM_RULE_NN00009965_TRANS TYPE_FILTER'
  );
```
**Expected:**
- `NOM_RULE_NN00009965_LOC_ATTR_FILTER` = "Allow Title Transfer"
- `NOM_RULE_NN00009965_TRANS TYPE_FILTER` = "02"

### Step 2: Verify Nomination Validation Rule is Active
```sql
SELECT *
FROM NominationValidation
WHERE RuleId = 'NN00009965';
-- Check: Active = 1, ErrorLevel, Overridable flag
```

### Step 3: Verify Contract MDQ Values (Critical for MDQ Source Issue)
```sql
-- Check BOTH MDQ fields for the test contracts
SELECT CtrNo, AmendNo, TspNo, TosCode,
       CtrMdqDisplayOnly,    -- Current code uses this
       OvrdCtrMdq            -- Should be used when populated (planned fix)
FROM Contract
WHERE CtrNo IN ('A-407-FT3001', 'M-403-FT001');
```

### Step 4: Verify Shared MDQ Contract Relationships
```sql
SELECT CtrNo, AmendNo, RelatedCtrNo, RelatedAmendNo, RelatedCtrRsnCode
FROM RelatedContract
WHERE CtrNo IN ('A-407-FT3001', 'M-403-FT001')
  AND RelatedCtrRsnCode = 'SharedMDQ';
```

### Step 5: Verify Location Attributes (ATT)
```sql
-- Check which locations are pool locations
SELECT IdLoc, TspNo, AttributeName, AttributeValue
FROM LocationAttribute
WHERE AttributeName = 'Allow Title Transfer'
  AND IdLoc IN ([receipt_loc_id], [delivery_loc_id]);
```

### Step 6: Check Nomination Data for Affected Transactions
```sql
-- Review nominations on the contract to see what was counted
SELECT NomId, SrCtrNo, TransTypeCode, RecQty, DelQty,
       IdRecLoc, IdDelLoc, NomStatCode, IsPathRecord
FROM ActivityDetail
WHERE SrCtrNo IN ('A-407-FT3001')
  AND GasDay = [affected_gas_day]
ORDER BY NomId;
```

---

## 17. Technical Investigation Steps

### Step 1: Verify Client Version and Hotfix Status
- Confirm WWM is running version **2024.04**
- Check if hotfix **2024.04.1.47** (which includes PR #126984) has been deployed
- If deployed: the pool-to-pool exclusion fix is active, but the MDQ source field issue may still exist
- If not deployed: both issues are present

### Step 2: Reproduce the Issue
**Scenario A — Pool-to-Pool False Positive (Fixed):**
1. Create a nomination on contract A-407-FT3001 (MDQ = 150,000) with total Del Qty > 150,000
2. Add a nomination with Rec Qty = 0 on a pool-to-pool path (ATT = true on both locations)
3. Pre-fix: NN00009965 fires incorrectly on the 0 qty nomination
4. Post-fix: NN00009965 should NOT fire because pool-to-pool is excluded

**Scenario B — MDQ Source Field (Open Issue):**
1. Use contract M-403-FT001 where Contract MDQ = 375,000 and Override MDQ = 250,000
2. Submit nominations with total Del Qty between 250,001 and 375,000
3. Current behavior: No validation error (compares against 375,000 from CtrMdqDisplayOnly)
4. Expected behavior: Validation error (should compare against 250,000 from OvrdCtrMdq)

### Step 3: Review Code Path
- Validation rule: `Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/RuleNN00009965.cs`
- Line to watch: `dSharedCtrQty = ctr.CtrMdqDisplayOnly ?? 0;`
- Planned change: Revert to `dSharedCtrQty = ctr.OvrdCtrMdq ?? 0;` (or use OvrdCtrMdq when populated, fallback to CtrMdqDisplayOnly)

### Step 4: Verify QA Test Results
- TestRail Case [#89357](https://quorumsoftware.testrail.io/index.php?/cases/view/89357)
- QA Environment: MSSQL RELQA
- QA Test Data: CTR 1818, Shared MDQ 2000, Rec Loc 0168193 (Non-pool), Del Loc 11180 (Pool)

---

## 18. Recommended Solution & Deployment Path

### Current Fix Status (Two Parts)

| Part | Status | Description |
|------|--------|-------------|
| **Part 1: Pool-to-pool exclusion + correct nom error display** | COMPLETE (QA Approved) | Pool-to-pool noms excluded from dTotalNomQty; error shows on correct nomination |
| **Part 2: MDQ source field revert (OvrdCtrMdq)** | PLANNED (Next Sprint — Early June 2026) | Revert from CtrMdqDisplayOnly back to OvrdCtrMdq |

### Deployment Options

| Option | Version | What It Includes | Notes |
|--------|---------|------------------|-------|
| **Option A** | Hotfix **2024.04.1.47** | Part 1 only | Client stays on 2024.04.x; Part 2 will need separate hotfix |
| **Option B** | Hotfix **2025.10.1.6** | Part 1 only | If client upgrades to 2025.10.x |
| **Option C** | Major release **2026.04.1.0** | Part 1 only | Full version upgrade |
| **Option D** | Wait for Part 2 | Parts 1 + 2 | Deploy after June 2026 sprint with complete fix |

### Recommendation
**Deploy Part 1 hotfix now** (fixes the most critical issues — pool-to-pool false positives and wrong nomination display), then apply Part 2 hotfix when available in June 2026.

### Interim Workaround (If Deployment Is Delayed)
- Make validation NN00009965 **overridable** instead of a hard error in the Validation Rule Assignment
- Users can then override the false positive and continue processing
- **Risk:** Legitimate overrun violations could be overridden accidentally

---

## 19. Open Issue: Override MDQ vs CtrMdqDisplayOnly

### Background
During L4 investigation (2026-02-05), Aditya Bhagat found that `ctr.OvrdCtrMdq` was returning `0` on the test contracts, so the fix switched to `ctr.CtrMdqDisplayOnly`.

### UAT Discovery
In WWM's UAT (reported 2026-05-08 by Sara Riano via Case 26-01099290):
- Contract **M-403-FT001** on Matterhorn pipeline
- Contract MDQ (`CtrMdqDisplayOnly`) = **375,000**
- Override Contract MDQ (`OvrdCtrMdq`) = **250,000**
- The validation should use **250,000** (Override) but currently uses **375,000** (Contract)

### Planned Resolution (per Christine Lee, 2026-05-18)
> "The plan is to revert the MDQ source field back to OvrdCtrMdq while keeping the pool-to-pool exclusion logic in place. This is planned for next sprint, so expect this closer to the beginning of June."

### Code Change Required
```csharp
// Current (needs to be reverted):
dSharedCtrQty = ctr.CtrMdqDisplayOnly ?? 0;

// Planned fix — use OvrdCtrMdq when populated:
dSharedCtrQty = ctr.OvrdCtrMdq ?? ctr.CtrMdqDisplayOnly ?? 0;
// OR simply:
dSharedCtrQty = ctr.OvrdCtrMdq ?? 0;
```

---

## 20. Escalation Recommendation

| Item | Status | Action |
|------|--------|--------|
| **Engineering Escalation** | Not needed for Part 1 | Fix complete. Part 2 planned for next sprint. |
| **Deployment Escalation** | **YES** | Coordinate with Delivery team to schedule Part 1 hotfix to WWM |
| **PM Escalation** | Not needed | PM approval obtained. Desiree Martin is actively tracking. |
| **Client Communication** | **YES** | Sara Riano should update client on: (1) Part 1 fix ready for deployment, (2) Part 2 expected early June 2026 |
| **Current Blocker** | MDQ source field issue | ADO re-activated 2026-05-15. Part 2 fix planned for 26.09 sprint |

---

## 21. Risk / Impact Analysis

| Risk Category | Impact | Severity |
|---------------|--------|----------|
| **Operational** | WWM shippers incorrectly blocked from submitting valid nominations, causing scheduling delays | High |
| **Financial** | Potential pipeline capacity underutilization if valid noms are rejected | Medium |
| **Workaround Risk** | Making NN00009965 overridable removes shared MDQ protection — legitimate overruns could go undetected | Medium |
| **Client Relationship** | 4 related cases over 12+ months (25-01018455, 25-01041489, 26-01099290) — high client frustration likely | High |
| **Broader Impact** | Rule NN00009965 was originally created only for WWM. Other clients unlikely affected. | Low |
| **Data Integrity** | No data corruption risk — validation-only issue. Blocks valid nominations but does not corrupt existing data. | None |
| **Regression Risk** | Part 2 (MDQ source revert) could affect contracts where OvrdCtrMdq is 0 but CtrMdqDisplayOnly is correct — needs careful QA | Medium |

---

## 22. Key People & Roles

| Role | Name | Email | Context |
|------|------|-------|---------|
| **Case Owner (SF)** | Aditya Bhagat | aditya.bhagat@quorumsoftware.com | SF case owner, ADO contributor, root cause identifier, PR author |
| **L4 Investigator** | Anas Shaikh | — | Initial L4 investigation, first code change attempt, walkthrough doc |
| **Developer (ADO Assignee)** | Kunal Ugale | kunal.ugale@quorumsoftware.com | PR reviewer/approver, merge admin |
| **Dev Approver / Engineering Lead** | Christine Lee | christine.lee@quorumsoftware.com | Development approval, sprint planning, MDQ source field decision |
| **Support Lead** | Sara Riano | — (via transportation.support@quorumsoftware.com) | Client communication, UAT testing, case 26-01099290 |
| **PM Contact** | Desiree Martin | desiree.martin@quorumsoftware.com | Re-activated ADO, escalation tracking |
| **QA Engineer** | Vaishnavi Kolhe | vaishnavi.kolhe@quorumsoftware.com | QA verification on RELQA env |
| **Cherry-pick Engineer** | Geetali Bendale | geetali.bendale@quorumsoftware.com | PR #126984 for 2024.04 hotfix |
| **Code Reviewer** | Chetan Chauhan | chetan.chauhan@quorumsoftware.com | Reviewed PR #126984 |
| **Initial Triage** | Abhijit Todkar | — | Asked for Core repro confirmation |
| **Original Enhancement Owner** | Allison Brassette | — | Case 23-00909370 owner |
| **Client Contacts** | quorumsupport@wwm-llc.com; jsoileau@wwm-llc.com; sshipos@wwm-llc.com; lreece@wwm-llc.com; max@wwm-llc.com | — | WWM stakeholders |

---

## 23. Summary & Next Steps

### Executive Summary

This is a **confirmed code defect** (pre-existing issue) in validation rule NN00009965 within the QPTM Nominations module. The validation incorrectly included pool-to-pool and AOS nominations in the shared MDQ total, causing false validation errors on the wrong nominations with incorrect quantities.

**Part 1 (Complete):** Pool-to-pool exclusion and correct nomination error display — developed, tested (TestRail #89357), QA-approved, cherry-picked to hotfix branches for 2024.04.1.47 and 2025.10.1.6.

**Part 2 (Pending):** MDQ source field revert from `CtrMdqDisplayOnly` to `OvrdCtrMdq` — planned for next sprint (early June 2026). Discovered during UAT when Override Contract MDQ differs from Contract MDQ.

### Immediate Next Steps

1. **Deploy Part 1 hotfix (2024.04.1.47)** to WWM's environment immediately
2. **Communicate to client** via Sara Riano's email chain:
   - Part 1 fix is ready (pool-to-pool exclusion + correct error display)
   - Part 2 fix (MDQ source field) expected early June 2026
3. **Monitor ADO #1775092** for Part 2 development in sprint 26.09
4. **Verify after Part 1 deployment** that pool-to-pool false positives are resolved

### Follow-up Actions (June 2026)

5. **Deploy Part 2 hotfix** once OvrdCtrMdq revert is complete and QA-verified
6. **Close Salesforce case 25-01041489** after both parts are deployed and client confirms
7. **Update Case 26-01099290** notes if it was not fully linked to the Part 2 resolution

---

*Investigation completed: 2026-05-26*
*Data Sources: Salesforce (Quorum Production), Azure DevOps (QuorumSoftware org), Quorum.QPTM.Web Git repository*
*Report generated by: L4 Support Investigation Agent*

---
---

# L4 Detailed Investigation Report — Case 26-01099834

**Case:** 26-01099834 | **Salesforce ID:** 500UH00000oJblTYAS
**Date:** 2026-05-26 | **Investigator:** L4 Support Investigation Agent
**Product:** QPTM | **Module:** EDI Nominations / Cycle Deadline Validation
**Client:** EQT Corporation | **TSP:** Equitrans (TSP 24)

---

## TABLE OF CONTENTS

1. [Case Overview](#1-case-overview)
2. [Issue Understanding](#2-issue-understanding)
3. [Issue Classification](#3-issue-classification)
4. [Root Cause Analysis](#4-root-cause-analysis)
5. [Code Analysis — EDI Inbound NMST Processing](#5-code-analysis--edi-inbound-nmst-processing)
6. [Code Analysis — Cycle Auto-Assignment](#6-code-analysis--cycle-auto-assignment)
7. [Code Analysis — Late Nomination Validation Rule](#7-code-analysis--late-nomination-validation-rule)
8. [Code Analysis — NMQR Error Response Generation](#8-code-analysis--nmqr-error-response-generation)
9. [ENMQR315 Error Code Definition](#9-enmqr315-error-code-definition)
10. [Cycle Deadline Architecture](#10-cycle-deadline-architecture)
11. [Historical ADO Work Items](#11-historical-ado-work-items)
12. [Historical Salesforce Cases](#12-historical-salesforce-cases)
13. [Attachments](#13-attachments)
14. [Database Tables & Configuration](#14-database-tables--configuration)
15. [Possible Root Causes](#15-possible-root-causes)
16. [Recommended Investigation Steps](#16-recommended-investigation-steps)
17. [SQL Diagnostic Queries](#17-sql-diagnostic-queries)
18. [Escalation Path](#18-escalation-path)
19. [Key People & Repos](#19-key-people--repos)

---

## 1. Case Overview

| Field | Value |
|-------|-------|
| **Case Number** | 26-01099834 |
| **Salesforce ID** | 500UH00000oJblTYAS |
| **Subject** | EDI Nomination Error |
| **Status** | In Progress |
| **Priority** | High |
| **Created Date** | 2026-05-11 |
| **Owner** | Aditya Bhagat |
| **Client** | EQT Corporation |
| **TSP** | Equitrans (TSP 24) |
| **Trading Partner** | EQT Energy LLC |

**Client Description:**
On gas day 9, EQT Energy submitted an EDI nomination at 2:45PM CST on Equitrans (TSP 24). They received the error `III*VAL*ENMQR315**LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED` on the NMQR response. Cycle ID3 was not closed yet and the nomination should have been submitted for cycle ID3. The Equitrans NMST EDI does not include the cycle indicator segment — it should automatically assign the cycle indicator.

---

## 2. Issue Understanding

### What Happened
1. EQT Energy LLC sent an inbound **NMST (Nomination Statement)** EDI file to Equitrans (TSP 24) at **2:45 PM CST** on **gas day 9**
2. The Equitrans NMST EDI format **does not include the CS (Cycle Indicator) segment** — the system is expected to auto-assign the correct cycle
3. The nomination was rejected with NAESB error **ENMQR315** — "LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED"
4. The client confirms that **Cycle ID3 was still open** at the time of submission (2:45 PM CST)

### What Should Have Happened
1. The system should have auto-assigned the nomination to **Cycle ID3** (the first open cycle)
2. The validation rule should have passed since ID3 deadline had not expired
3. The nomination should have been submitted successfully with an acceptance NMQR response

### The Gap
Either (a) the cycle auto-assignment picked a wrong/closed cycle, (b) the cycle deadline configuration for TSP 24 ID3 has an incorrect deadline time, or (c) there is a timing race condition between cycle assignment and validation.

---

## 3. Issue Classification

| Dimension | Classification |
|-----------|---------------|
| **Primary** | **Configuration / Data Issue** (most likely — cycle deadline times) |
| **Secondary** | Possible code defect (timing race condition) |
| **Tertiary** | Possible environment issue (server time zone mismatch) |

**Rationale:** The most common cause of this error is incorrect cycle deadline configuration in the `PACTRL_CYCLE_DEADLINE` table. If the ID3 deadline for TSP 24 is set earlier than when the EDI was received (2:45 PM CST), the system would correctly reject it. However, if the client confirms ID3 should be open at 2:45 PM, then either the deadline config is wrong or there's a code-level issue.

---

## 4. Root Cause Analysis

### Hypothesis 1: Cycle Deadline Misconfiguration (HIGH probability)
The `PACTRL_CYCLE_DEADLINE` table for Equitrans TSP 24, Cycle ID3, Deadline Category = "Nomination", Deadline Type = "OnTime" may have a deadline time that evaluates to **before 2:45 PM CST** on gas day 9. The `CalcDeadline()` method computes the actual deadline datetime from the gas day + configured offset. If this evaluates to, say, 2:30 PM CST, the system would correctly consider ID3 closed.

### Hypothesis 2: Timing Race Condition (MEDIUM probability)
The EDI inbound processing happens in two phases:
1. **Phase 1 (ReadFile):** `GetOpenCycleByDay()` is called to auto-assign cycle → may return ID3
2. **Phase 2 (ProcessData → PrepareAndSubmit → SubmitNominations):** Validation rule `RuleNN00009011` re-checks the deadline

If there is a delay between Phase 1 and Phase 2 (e.g., due to large file, fuel calculation, merge/split processing), the cycle could close between assignment and validation. At 2:45 PM CST, if the deadline is very close (e.g., 2:50 PM), a few minutes of processing could cause the race condition.

### Hypothesis 3: Server Time Zone Mismatch (LOW probability)
The `CycleManager.GetFirstOpenCycle()` uses `DateTimeService.Now()` (which resolves to `Utilities.NowS` / `QDateTime.NowS`). If the server's clock or time zone configuration differs from the expected CST, the deadline comparison could be off. For example, if the server runs in UTC and the deadline is configured in CST without proper conversion.

### Hypothesis 4: External vs Internal User Type (LOW probability)
The validation rule `RuleNN00009011` checks `ValidationRuleHelper.IsUserInternal(ruleData.ValidatingUserID)` and uses different deadline types (internal vs external). EDI submissions use the TPA context security user. If this user is classified differently than expected, it could hit different deadline windows.

---

## 5. Code Analysis — EDI Inbound NMST Processing

### File: `Quorum.QPTM.EDI.DataSets/G873NMST/QEdiNMSTIn18.cs`
### Repo: `Quorum.QPTM.Batch` (e024d80b-5c45-411c-93e1-78e2798ed885)

This class handles the complete inbound NMST EDI lifecycle:

**Processing Flow:**
```
ReadFile() → ParseDTM() → Auto-assign cycle via GetOpenCycleByDay()
    ↓
ProcessData() → CalculateFuel() → PrepareAndSubmit()
    ↓
PrepareAndSubmit() → SplitIntoMonths() → SplitNonTimelyRecords()
    → GetNominations() → SplitAndMerge() → SubmitNominations()
    ↓
SubmitNominations() → [Middle Tier runs validation rules including RuleNN00009011]
    → Returns noms with errors → CreateQuickResponse() → Sends NMQR
```

**Key Cycle Assignment Code (Proc_873_Area_2_Loop_DTM, ~line 430):**
```csharp
// Auto-assign cycle when NMST does not include CS/N9 cycle indicator segment
IQPTMCycleService service = QServiceContainer.GlobalInstance.GetService<IQPTMCycleService>();
short[] openCyclesByDay = service.GetOpenCycleByDay(
    currDO.TspNo,
    currDO.BegGasDay,
    Constants.DeadlineCategory.Nomination,
    Constants.DeadlineType.OnTime);
OpenCycles.Add(sYearMonth, openCyclesByDay);

// Assign the open cycle for this gas day
currDO.IdCycle = OpenCycles[sYearMonth][currDO.BegGasDay.Day - 1];
```

**Critical Observation:** The CS/N9 (Cycle Indicator) segment handling is **commented out**:
```csharp
//else if (sSegmentID == "N9") // Cycle Indicator - mutually agreed
//{
//}
```
This confirms Equitrans does NOT send cycle indicator in the NMST EDI, and the system relies entirely on `GetOpenCycleByDay()` for auto-assignment.

---

## 6. Code Analysis — Cycle Auto-Assignment

### File: `Quorum.QPTM.DataCache/CycleManager.cs`
### Repo: `Quorum.QPTM.Web` (41e317c0-844c-4728-98da-529092957738)

**`GetFirstOpenCycle()` (~line 150):**
```csharp
DateTime currentDateTime = DateTimeService.Now();
foreach (CycleDeadlineDO cycleDeadline in view)
{
    DateTime newGasDay = cycleDeadline.CalcDeadline(date);
    if (currentDateTime > newGasDay)
    {
        continue; // This cycle's deadline has passed, try next
    }
    cycles.Add(date, cycleDeadline.IdCycle); // First open cycle found
    break;
}
```

**`GetCycleStatusByDay()` (~line 460) — Used by `GetOpenCycleByDay`:**
```csharp
DateTime currentDateTime = Utilities.NowS;
foreach (CycleDeadlineDO cycleDeadline in view)
{
    DateTime newGasDay = cycleDeadline.CalcDeadline(gasDay);
    cycleProcessed.Add(cycleDeadline.IdCycle, currentDateTime <= newGasDay);
}
```

**Key Logic:**
- Iterates through cycle deadlines sorted by `IdCycle` (ascending: ID1, ID2, ID3, etc.)
- For each cycle, calls `CalcDeadline(gasDay)` to compute the actual deadline datetime
- Compares with `currentDateTime` — if current time > deadline, cycle is CLOSED
- Returns the **first cycle where `currentDateTime <= deadline`** (i.e., still open)
- If ALL cycles are closed, returns -1, which gets reassigned to `GetLastCycle()` (retroactive)

**If `GetOpenCycleByDay` returns cycle > ID3 (e.g., ID4 or the last cycle), it means ID3 deadline had already passed according to the server clock and deadline config.**

---

## 7. Code Analysis — Late Nomination Validation Rule

### File: `DUT.QPTM.Validation.Rules.Nomination/LineValidations/RuleNN00009011.cs`
### (Base QPTM rule — EQT uses the standard version, no EQT-specific override found)

**Rule ID:** NN00009011
**Rule Type:** `ValidationRuleBaseNominationLine` (Line-level validation → NomStatCode = "LI" on failure)
**NAESB Code:** ENMQR315

**Validation Logic:**
```csharp
if (activityDetailDO.IdCycle.HasValue && activityDetailDO.HasChangesCompareColsOnly)
{
    short nCycleID = ValidationRuleHelper.GetFirstOpenCycle(activityDetailDO);
    
    // Determine user type for deadline lookup
    string sUserType = Constants.ExternalUserType; // default
    if (ValidationRuleHelper.IsUserInternal(ruleData.ValidatingUserID))
        sUserType = Constants.InternalUserType;
    
    // Get cycle deadline for the assigned cycle
    cycleDeadline = cycleCache.GetCycleDeadline(
        nCycleID, activityDetailDO.TspNo,
        Constants.DeadlineType.OnTime,
        Constants.DeadlineCategory.Nomination,
        sUserType, begGasDay);
    
    // Check contract attributes for extended deadlines (EXT, ELC)
    // ... checks for altCycleDeadline ...
    
    // THE CRITICAL CHECK:
    DateTime currentDateTime = Utilities.NowS;
    DateTime deadline = cycleDeadline.CalcDeadline(begGasDay);
    
    if (currentDateTime > deadline)
    {
        bIsValid = false; // LATE NOMINATION - triggers ENMQR315
    }
}
```

**Important Details:**
1. The rule calls `ValidationRuleHelper.GetFirstOpenCycle()` **independently** to get the current open cycle — this is a separate check from the EDI auto-assignment
2. It checks for contract attributes "EXT" (Extended) and "ELC" (Electronic) which may provide alternate/extended deadlines
3. The user type (Internal vs External) affects which deadline is used
4. The `CalcDeadline()` method on `CycleDeadlineDO` computes the actual deadline datetime from the gas day and the stored offset/time configuration

---

## 8. Code Analysis — NMQR Error Response Generation

### File: `Quorum.QPTM.EDI.DataSets/G873NMST/QEdiNMSTIn18.cs`
### Method: `CreateQuickResponse()` (~line 1815)

When `SubmitNominations()` returns noms with errors:
```csharp
foreach (ActivityDetailErrorDO err in nom.ActivityDetailError)
{
    if (!err.IsOvrd) // Don't add overridden errors
    {
        EDQRErrorDO QRerr = new EDQRErrorDO();
        QRerr.TspNo = EdiControlDataQPTM.TspNo;
        QRerr.RefId = IdNomRef;
        QRerr.CtrNo = nom.SrCtrNo;
        QRerr.BegGasDay = nom.BegGasDay;
        QRerr.EndGasDay = nom.EndGasDay;
        
        // Map validation rule to NAESB error code
        RuleDO rule = this.EdiDataCacheQPTM.GetRule(err.FuncAreaCode, err.ValdRuleCode);
        QRerr.NaesbErrorCode = rule.NaesbCode; // "ENMQR315"
        QRerr.ErrorDesc = rule.ValdRuleDescr;  // "LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED"
    }
}
```

The NAESB error code mapping comes from the **metadata** (`QARCH_VALD_RULE` table) — the validation rule NN00009011 is configured with `NaesbCode = "ENMQR315"` and `ValdRuleDescr = "LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED"`.

The error flows back to the trading partner in the **G874NMQR (Nomination Quick Response)** EDI:
```
III*VAL*ENMQR315**LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED
```

---

## 9. ENMQR315 Error Code Definition

### NAESB Standard Definition
| Field | Value |
|-------|-------|
| **Code** | ENMQR315 |
| **Section** | DTL (Detail) |
| **Severity** | E (Error) |
| **NAESB Description** | "Time Stamp is outside of acceptable range" |
| **QPTM Description** | "LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED" |
| **Source File** | `NAESB_1_8_NMQR_Msgs.txt` |
| **DB Table** | `QCODE_ED_ERROR` |

### Related NAESB Cycle Codes
| Code | Description |
|------|-------------|
| ENMQR320 | Invalid Cycle Indicator |
| ENMQR321 | Missing Cycle Indicator |
| WNMQR304 | Cycle Indicator not used |
| WNMQR305 | Invalid Cycle Indicator (warning) |
| WNMQR306 | Missing Cycle Indicator (warning) |
| WNMQR300 | Timestamp outside of acceptable range for Timely nominations (warning) |

---

## 10. Cycle Deadline Architecture

### How Cycle Deadlines Work in QPTM

1. **`PACTRL_CYCLE_DEADLINE` table** stores the deadline configuration per TSP, per cycle, per deadline category (Nomination/Confirmation/Scheduling), per deadline type (OnTime/EXT/ELC), per user type (Internal/External)

2. **`CycleDeadlineDO.CalcDeadline(gasDay)`** computes the actual deadline datetime:
   - Takes the gas day date
   - Applies the configured offset (days before/after gas day + time of day)
   - Returns the absolute datetime when that cycle closes

3. **Cycle evaluation flow:**
   ```
   CycleCache.GetCycleDeadline(IdCycle, TspNo, DeadlineType, DeadlineCategory, UserType, GasDay)
       → Returns CycleDeadlineDO with EffDateFrom, EffDateTo, and deadline offset
   CycleDeadlineDO.CalcDeadline(gasDay)
       → Returns DateTime (the actual deadline moment)
   Compare: DateTime.Now <= deadline → cycle is OPEN
   Compare: DateTime.Now > deadline → cycle is CLOSED
   ```

4. **NAESB Standard Cycles for Gas Pipelines:**
   | Cycle | Typical Timely Deadline (CCT) |
   |-------|------------------------------|
   | Timely (ID1) | Day before gas day, ~11:30 AM |
   | Evening (ID2) | Day before gas day, ~6:00 PM |
   | Intraday 1 (ID3) | Gas day, ~10:00 AM |
   | Intraday 2 (ID4) | Gas day, ~2:30–5:00 PM |
   | Intraday 3 (ID5) | Gas day, ~7:00–9:00 PM |

   **Note:** Exact deadlines vary by TSP. Equitrans (TSP 24) may have custom deadline times.

---

## 11. Historical ADO Work Items

### Directly Related
| ADO # | Type | State | Title |
|-------|------|-------|-------|
| #1609881 | Bug | Closed | Late Nomination Rule not firing for external users when editing certain fields (Case 23-00902666) |
| #1788796 | Incident | Closed | EQC - EQT Corporation - QPTM PRD - TP EQT Energy LLC receiving "Error: The operation has timed out" while sending noms via EDI on Equitrans (24) and MVP (8925) - 3/16/2026 |

### Related — Cycle Indicator Issues
| ADO # | Type | State | Title |
|-------|------|-------|-------|
| #1368705 | Bug | — | EDI OACY uses Cycle ID instead of NAESB cycle indicator (Tallgrass/TEP) |
| #1366933 | Bug | — | Cycle indicator related |
| #1366929 | Bug | — | Cycle indicator related |

### Key Insight from #1609881
Bug #1609881 specifically addresses the scenario where **RuleNN00009011 (late nomination rule) was NOT firing correctly for external users** when editing certain fields. It was fixed, but this confirms the rule has had issues with user type evaluation before.

### Key Insight from #1788796
EQT had EDI timeout issues on Equitrans (TSP 24) in March 2026 — indicates potential infrastructure/performance issues that could contribute to timing-related problems.

---

## 12. Historical Salesforce Cases

| Case | Status | Date | Subject |
|------|--------|------|---------|
| **26-01099834** | In Progress | 2026-05-11 | **EDI Nomination Error** (THIS CASE) |
| 26-01087132 | Closed | 2026-03-16 | EQT Energy receiving "The operation has timed out" while sending noms via EDI |
| 25-01016771 | Closed | 2025-04-28 | EQT QPTM - Weekly Office Hours |
| 25-01001265 | Closed | 2025-01-31 | BI Error - Late Nominations not showing up on Nom Error Report (NN12) |
| 23-00913556 | Closed | 2023-08-02 | Shipper EQT is not able to submit EDI for nominations |
| 23-00892922 | Closed | 2023-03-28 | EQT - EDI - REX not submitting & No NMQRs |

**Case 26-01087132** is particularly relevant — EQT had EDI timeout issues on the same TSP (Equitrans 24) just 2 months before this case, linked to ADO #1788796.

---

## 13. Attachments

| # | File | Type | Size | Description |
|---|------|------|------|-------------|
| 1 | EDI Transactions.png | PNG | 155 KB | Screenshot of EDI transactions showing the error |
| 2 | Equitrans NMQR EDI.txt | TEXT | 653 B | The NMQR response EDI file containing ENMQR315 |
| 3 | NomEdi_ReferenceNum_327176.txt | TEXT | 779 B | The inbound NMST EDI file (Reference #327176) |
| 4 | Case Analysis - 26-01099834.html | HTML | 47 KB | Initial case analysis document |
| 5 | ID3.png | PNG | 38 KB | Screenshot showing ID3 cycle was still open |

---

## 14. Database Tables & Configuration

### Critical Tables to Check

| Table | Purpose |
|-------|---------|
| `PACTRL_CYCLE_DEADLINE` | Cycle deadline configuration — **PRIMARY investigation target** |
| `PACTRL_CYCLE` | Cycle definitions (ID1, ID2, ID3, etc.) per TSP |
| `QCODE_CYCLE_TYPE` | Cycle type metadata |
| `EDTRAN_QR_ERROR` | EDI Quick Response errors logged |
| `EDTRAN` | EDI transaction log |
| `NNCTRL_NOM_DTL` | Nomination detail records |
| `QCODE_ED_ERROR` | EDI error code definitions |
| `QARCH_VALD_RULE` | Validation rule definitions (maps NN00009011 → ENMQR315) |
| `QARCH_GLOBAL_CONFIG` | Global configs (SEND_NMST_QUICK_RESPONSE, etc.) |
| `NNCTRL_TPA` | Trading Partner Agreement — determines TPA context user |

### Key Configuration IDs
| Config | Description |
|--------|-------------|
| TSP_NO = 24 | Equitrans TSP number |
| Validation Rule = NN00009011 | Late nomination/retroactive nom check |
| NAESB Code = ENMQR315 | NAESB error code mapping |
| Deadline Category = "Nomination" | Category filter for cycle deadline lookup |
| Deadline Type = "OnTime" | Type filter for cycle deadline lookup |
| EDI Reference = 327176 | Inbound NMST reference number |

---

## 15. Possible Root Causes

### Most Likely → Cycle Deadline Configuration Issue
**Probability: HIGH**

The `PACTRL_CYCLE_DEADLINE` for TSP 24, Cycle ID3, may have a deadline time that is **earlier than 2:45 PM CST**. The NAESB standard for Intraday 1 (ID3) is typically around 10:00 AM CCT, but many TSPs have extended deadlines. If Equitrans's ID3 deadline is, say, 2:30 PM CST, then 2:45 PM would be after deadline.

**Action:** Query `PACTRL_CYCLE_DEADLINE WHERE TSP_NO = 24 AND ID_CYCLE = 3` and verify the actual deadline time.

### Second Likely → EDI Processing Delay + Race Condition
**Probability: MEDIUM**

If the EDI file was received at 2:45 PM CST and the ID3 deadline is very close (e.g., 2:50 PM CST):
1. `GetOpenCycleByDay()` at 2:45 PM sees ID3 as open → assigns ID3
2. Processing takes several minutes (fuel calc, merge, submit)
3. `RuleNN00009011` fires at, say, 2:52 PM → ID3 is now closed → ENMQR315

**Action:** Check EDTRAN log for file received time vs. SubmitNominations execution time. Check MSG_LOG for processing duration.

### Third → Server Time Zone Issue
**Probability: LOW**

If the application server runs in UTC and deadline calculations don't properly convert to the TSP's local time zone, the deadline comparison could be off by hours.

**Action:** Verify `Utilities.NowS` / `QDateTime.NowS` returns the correct time in the expected time zone.

---

## 16. Recommended Investigation Steps

### Step 1: Verify Cycle Deadline Configuration (Database)
```
Query PACTRL_CYCLE_DEADLINE for TSP 24, Cycle ID3
Confirm the deadline time and calculate what CalcDeadline() would return for gas day 9
```

### Step 2: Check EDI Transaction Log
```
Query EDTRAN for Reference #327176 to get exact received timestamp
Query EDTRAN_QR_ERROR for the ENMQR315 error details
Check MSG_LOG for processing duration and any warnings
```

### Step 3: Check Cycle Status at Time of Submission
```
Query PACTRL_CYCLE to see all cycle statuses for TSP 24, gas day 9
Verify which cycle was actually open at 2:45 PM CST
```

### Step 4: Check Validation Rule Configuration
```
Query QARCH_VALD_RULE for NN00009011
Confirm NaesbCode = ENMQR315
Check if the rule is configured as Line or Business level
```

### Step 5: Check TPA User Configuration
```
Query NNCTRL_TPA for EQT Energy's TPA on TSP 24
Check the TPA context security user
Verify if user is classified as Internal or External
```

### Step 6: If Configuration is Correct → Escalate as Code Defect
If the deadline config shows ID3 should be open at 2:45 PM CST, then this is a timing/code issue. Escalate to development with:
- Evidence that ID3 deadline > 2:45 PM CST
- EDTRAN timestamps showing file receipt vs. processing times
- Request investigation of `GetOpenCycleByDay` vs. `RuleNN00009011` timing discrepancy

---

## 17. SQL Diagnostic Queries

### Query 1: Cycle Deadline Configuration for Equitrans ID3
```sql
SELECT cd.TSP_NO, cd.ID_CYCLE, cd.DEADLINE_CATEGORY, cd.DEADLINE_TYPE,
       cd.USER_TYPE_CD, cd.EFF_DT_FROM, cd.EFF_DT_TO,
       cd.DEADLINE_DAY_OFFSET, cd.DEADLINE_TIME,
       cd.DEADLINE_TZ, cd.UPDT_DT
FROM PACTRL_CYCLE_DEADLINE cd
WHERE cd.TSP_NO = 24
  AND cd.ID_CYCLE = 3
  AND cd.DEADLINE_CATEGORY = 'NOM'
ORDER BY cd.DEADLINE_TYPE, cd.USER_TYPE_CD, cd.EFF_DT_FROM DESC;
```

### Query 2: All Cycle Deadlines for Equitrans
```sql
SELECT cd.TSP_NO, cd.ID_CYCLE, ct.CYCLE_TYPE_DESCR,
       cd.DEADLINE_CATEGORY, cd.DEADLINE_TYPE, cd.USER_TYPE_CD,
       cd.DEADLINE_DAY_OFFSET, cd.DEADLINE_TIME, cd.DEADLINE_TZ,
       cd.EFF_DT_FROM, cd.EFF_DT_TO
FROM PACTRL_CYCLE_DEADLINE cd
JOIN QCODE_CYCLE_TYPE ct ON cd.ID_CYCLE = ct.ID_CYCLE AND cd.TSP_NO = ct.TSP_NO
WHERE cd.TSP_NO = 24
  AND cd.DEADLINE_CATEGORY = 'NOM'
  AND cd.DEADLINE_TYPE = 'ONT'
ORDER BY cd.ID_CYCLE, cd.USER_TYPE_CD;
```

### Query 3: EDI Transaction Log for Reference #327176
```sql
SELECT et.EDI_TRANS_ID, et.TSP_NO, et.TPA_ID, et.REF_ID,
       et.DIRECTION_CD, et.DATASET_NM, et.STATUS_CD,
       et.RECV_DT, et.PROC_DT, et.UPDT_DT
FROM EDTRAN et
WHERE et.TSP_NO = 24
  AND et.REF_ID = '327176'
ORDER BY et.RECV_DT DESC;
```

### Query 4: QR Errors for This Transaction
```sql
SELECT qr.TSP_NO, qr.EDI_TRANS_ID, qr.REF_ID, qr.TRACK_ID,
       qr.CTR_NO, qr.BEG_GAS_DAY, qr.END_GAS_DAY,
       qr.NAESB_ERROR_CD, qr.ERROR_DESCR
FROM EDTRAN_QR_ERROR qr
WHERE qr.TSP_NO = 24
  AND qr.REF_ID = '327176'
ORDER BY qr.SEQ_NO;
```

### Query 5: Nomination Detail for Gas Day 9
```sql
SELECT nd.TSP_NO, nd.SR_CTR_NO, nd.BEG_GAS_DAY, nd.ID_CYCLE,
       nd.NOM_STAT_CD, nd.REC_QTY, nd.DEL_QTY,
       nd.SUBMIT_DT, nd.USER_ID, nd.UPDT_DT
FROM NNCTRL_NOM_DTL nd
WHERE nd.TSP_NO = 24
  AND nd.BEG_GAS_DAY = '2026-05-09'
  AND nd.SR_BP_NO IN (SELECT BA_NO FROM NNCTRL_TPA WHERE TSP_NO = 24 AND TPA_NM LIKE '%EQT%')
ORDER BY nd.ID_CYCLE, nd.SUBMIT_DT;
```

### Query 6: Validation Rule Definition
```sql
SELECT vr.FUNC_AREA_CD, vr.VALD_RULE_CD, vr.VALD_RULE_DESCR,
       vr.NAESB_CD, vr.IS_ALLOW_OVRD, vr.IS_ACTIVE,
       vr.VALD_RULE_TYPE_CD
FROM QARCH_VALD_RULE vr
WHERE vr.VALD_RULE_CD = 'NN00009011';
```

### Query 7: TPA Configuration for EQT on Equitrans
```sql
SELECT tpa.TSP_NO, tpa.TPA_ID, tpa.TPA_NM, tpa.BA_NO,
       tpa.SECURITY_USER_ID, tpa.USER_TYPE_CD,
       tpa.IS_ACTIVE, tpa.EFF_DT_FROM, tpa.EFF_DT_TO
FROM NNCTRL_TPA tpa
WHERE tpa.TSP_NO = 24
  AND (tpa.TPA_NM LIKE '%EQT%' OR tpa.BA_NO IN (
    SELECT DISTINCT SR_BP_NO FROM NNCTRL_NOM_DTL
    WHERE TSP_NO = 24 AND SYS_SRC_CD = 'EDI'
    AND BEG_GAS_DAY = '2026-05-09'))
ORDER BY tpa.TPA_NM;
```

---

## 18. Escalation Path

### If Configuration Issue (Hypothesis 1 confirmed):
1. Work with EQT/Equitrans pipeline operations to verify correct ID3 deadline time
2. Update `PACTRL_CYCLE_DEADLINE` if incorrect
3. Resubmit the EDI nomination
4. Document the configuration fix in Salesforce case notes

### If Code Defect (Hypothesis 2 confirmed):
1. Create ADO Bug work item in QuorumSoftware project
2. Tag: QPTM, EDI, Nominations, Cycle Validation
3. Assign to QPTM development team
4. Reference this investigation report
5. Proposed fix: Either (a) use the cycle assigned during ReadFile phase for validation instead of re-evaluating, or (b) add a grace period buffer to `RuleNN00009011`

### If Time Zone Issue (Hypothesis 3 confirmed):
1. Infrastructure team investigation needed
2. Verify `QDateTime.NowS` returns correct time zone for the QPTM service
3. May require environment configuration fix

---

## 19. Key People & Repos

### Key Repositories
| Repo | ID | Purpose |
|------|----|---------|
| Quorum.QPTM.Batch | e024d80b-5c45-411c-93e1-78e2798ed885 | EDI inbound NMST processing |
| Quorum.QPTM.Web | 41e317c0-844c-4728-98da-529092957738 | Nomination service, cycle management, validation |
| EQT.QPTM.Web | f29cf1be-dcaa-45ec-b721-dc4a5f06bfa8 | EQT client-specific code (no late nom overrides) |
| Quorum.QGM.Database | 8bfba59c-f3dd-46ea-8d0a-f2687a763258 | QCODE_ED_ERROR table definitions |
| DUT.QPTM.Web | (reference) | RuleNN00009011 source code example |

### Key Source Files
| File | Location |
|------|----------|
| QEdiNMSTIn18.cs | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G873NMST/ |
| QPTMNominationService.cs | Quorum.QPTM.Web/Quorum.QPTM.ServiceCore.Nomination/ |
| CycleManager.cs | Quorum.QPTM.Web/Quorum.QPTM.DataCache/ |
| RuleNN00009011.cs | DUT.QPTM.Web/DUT.QPTM.Validation.Rules.Nomination/LineValidations/ |
| QCODE_ED_ERROR.sql | Quorum.QGM.Database/Common/Oracle/EDI Base Data Setup/CodeTables/ |
| NAESB_1_8_NMQR_Msgs.txt | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G874NMQR/ |

### Related ADO Bug Fix
| ADO # | Description |
|-------|-------------|
| #1609881 | Late Nomination Rule not firing for external users (closed/fixed) |

---

*Investigation completed: 2026-05-26*
*Data Sources: Salesforce (Quorum Production), Azure DevOps (QuorumSoftware org), Quorum.QPTM.Web/Batch/QGM Git repositories*
*Report generated by: L4 Support Investigation Agent*
*Next Action: Run SQL diagnostic queries against EQT PRD database to verify cycle deadline configuration for Equitrans TSP 24*

---
---
---

# L4 Detailed Investigation Report — Case 26-01088177

**Case:** 26-01088177 | **Salesforce ID:** 500UH00000l8tUCYAY
**Date:** 2026-05-26 | **Investigator:** L4 Support Investigation Agent
**Product:** QPTM | **Module:** Financial Accounting — Invoice Group Maintenance
**Client:** MountainWest Pipeline, LLC (WWM) | **Contact:** Dave Reeder (Williams)

---

## TABLE OF CONTENTS

1. [Case Overview](#1-case-overview)
2. [Issue Understanding](#2-issue-understanding)
3. [Issue Classification](#3-issue-classification)
4. [Root Cause Analysis](#4-root-cause-analysis)
5. [Code Analysis](#5-code-analysis)
6. [Historical ADO Work Items](#6-historical-ado-work-items)
7. [Historical Salesforce Cases](#7-historical-salesforce-cases)
8. [Attachments](#8-attachments)
9. [Database Tables & Configuration](#9-database-tables--configuration)
10. [Version & Fix Availability](#10-version--fix-availability)
11. [Diagnostic SQL Queries](#11-diagnostic-sql-queries)
12. [Recommended Next Steps](#12-recommended-next-steps)
13. [Escalation Path](#13-escalation-path)
14. [Key People & Repos](#14-key-people--repos)

---

## 1. Case Overview

| Field | Value |
|-------|-------|
| **Case Number** | 26-01088177 |
| **Salesforce ID** | 500UH00000l8tUCYAY |
| **Subject** | MW \| Laura Johnson \| Invoice Group error on MyQuorum |
| **Status** | In Progress |
| **Priority** | Medium |
| **Created Date** | 2026-03-19 |
| **Owner** | Aditya Bhagat |
| **Client** | MountainWest Pipeline, LLC |
| **Contact** | Dave Reeder (david.reeder@williams.com) — Commercial Technology Lead |

**Client Description:**
> There is a difference in functionality between the web and classic versions of QPTM when trying to update the invoice group. The classic version easily allows the addition of a new contract but the web is throwing errors. See attached.

---

## 2. Issue Understanding

### What Happened
The client (MountainWest) is trying to add a new contract to an existing Invoice Group using the **web version** (MyQuorum) of QPTM. When they attempt this, the web application throws errors. The same operation works without issue in the **classic (Citrix) version** of the application.

### What Should Have Happened
Adding a contract to an Invoice Group in the web version should behave identically to the classic version — the user should be able to select a contract from the picklist, add it to the Invoice Group's Contracts tab, and save successfully.

### The Gap
There is a functional parity gap between the classic QPTM client and the web (MyQuorum) version for the Invoice Group Maintenance screen's contract management. The web version either:
1. Shows errors when adding/saving contracts to an invoice group, OR
2. Has a more restrictive validation/picklist filtering than classic, OR
3. Has a different contract picklist registration/SQL that filters out valid contracts

---

## 3. Issue Classification

| Dimension | Classification |
|-----------|---------------|
| **Primary** | **Defect** — Web/Classic functional parity issue |
| **Secondary** | Configuration (possible picklist SQL or screen registration issue) |

**Rationale:** This is a known pattern in QPTM — the web version of Invoice Group Maintenance has had multiple reported defects regarding contract handling that differ from classic behavior. ADO has a history of bugs where the Contract tab picklist has incorrect filtering logic, contracts don't display properly, or auto-generation processes don't fire in web. The root cause is most likely a defect in the web layer's picklist registration or validation logic for the Invoice Group Maintenance Contracts tab.

---

## 4. Root Cause Analysis

### Hypothesis 1: Contract Tab Picklist SQL Filtering Issue
**Probability: HIGH**

The registered SQL for Invoice Group Maintenance's Contract tab picklist has known issues:
- **ADO #1576190** (Closed): Documented that the picklist SQL had a bad join causing as-of-date filtering to be bypassed, and the as-of-date was using current date instead of the invoice group's effective date
- The picklist may be filtering out valid contracts that the user needs to add based on date logic or join conditions
- Classic doesn't use the same picklist registration — it uses native SQL that doesn't have these restrictions

### Hypothesis 2: Web Validation Rules More Restrictive Than Classic
**Probability: MEDIUM**

The web version runs through `QPTMInvoiceGroupMaintenanceCompleteValidationContext` validation on save, which includes:
- `QPTMInvoiceGroupMaintenance005_ValidateInvGrpCopy` — Copy validation
- `QPTMInvoiceGroupMaintenance006_ValidateInvoiceGroupId` — Invoice Group ID validation
- `QPTMInvoiceGroupMaintenance006_ValidateMandatory` — Mandatory field validation

The classic version may have fewer or different validation rules, allowing operations that the web blocks.

### Hypothesis 3: Contract BindingList Add/Save Issue in Web Controller
**Probability: MEDIUM**

Looking at the `InvoiceGroupMaintenanceController.ContractsGridAddNewRow()` method:
```csharp
return GridAdd(id, uic =>
{
    if (!objectId.IsValid())
    {
        return (BillingInvoiceGroupContractDO)uic.BillingInvoiceGroup
            .BillingInvoiceGroupContractBindingList.AddNew();
    }
    // clone logic...
});
```
The `AddNew()` call creates a blank contract row. If the `BillingInvoiceGroup` is null or not properly loaded (e.g., after a query that returned empty), the BindingList operation could fail. The controller's `ContractsGridGetData` also has a null-check pattern:
```csharp
var invGrpCtrList = Enumerable.Empty<BillingInvoiceGroupContractDO>();
if(uic.BillingInvoiceGroup?.BillingInvoiceGroupContract?.Any() ?? false)
{
    invGrpCtrList = uic.BillingInvoiceGroup.BillingInvoiceGroupContract;
}
```
This suggests there were past issues with null references in this area.

### Hypothesis 4: Effective Date Handling on Save
**Probability: LOW**

The `DoSave()` method in `QUIControllerInvoiceGroupMaintenance` normalizes dates:
```csharp
BillingInvoiceGroupComplete.EffectiveDatedItems.FirstOrDefault().EffDateFrom = 
    BillingInvoiceGroupComplete.EffectiveDatedItems.FirstOrDefault().EffDateFrom.GetAsFirstDayOfMonth();
BillingInvoiceGroupComplete.EffectiveDatedItems.FirstOrDefault().EffDateTo = 
    BillingInvoiceGroupComplete.EffectiveDatedItems.FirstOrDefault().EffDateTo.GetAsLastDayOfMonth();
```
The `ValidateBeforeSave()` checks if effective dates changed and shows a warning dialog. If the effective date normalization conflicts with the contract's date range, it could cause validation errors on save.

---

## 5. Code Analysis

### File 1: `InvoiceGroupMaintenanceController.cs`
**Repo:** Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
**Path:** `/Quorum.QPTM.Web.Core/Controllers/InvoiceGroupMaintenanceController.cs`

This is the MVC controller for the Invoice Group Maintenance screen. Key findings:
- **ContractsGridAddNewRow** — Adds a new contract row to the BindingList. Uses `AddNew()` or `CloneAsNew()` pattern
- **ContractsGridUpdate** — Updates contract fields via `GridUpdate` helper
- **ContractsGridDeleteRow** — Removes from BindingList
- **ContractsGridGetData** — Has null-safety checks suggesting past null reference issues
- **Save action** calls `ValidateBeforeSave` via JavaScript before the actual save

### File 2: `QUIControllerInvoiceGroupMaintenance.cs`
**Repo:** Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
**Path:** `/Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerInvoiceGroupMaintenance.cs`

This is the UI controller (business logic layer). Key findings:
- **DoNew()** — Creates a new `BillingInvoiceGroupCompleteDO` with TSP, calls `SetDocDefaults()`
- **DoQuery()** — Calls `Service.GetSingleInvoiceGroupMaintenanceComplete()`. If null returned, falls through to `DoNew()`
- **DoSave()** — Normalizes EffDateFrom/To to first/last day of month, then delegates to `Service.UpdateSingleInvoiceGroupMaintenanceComplete()`
- **DoValidate()** — Delegates to `Service.ValidateSingleInvoiceGroupMaintenanceComplete()`
- **OnPropertyChanged** — Sets default `FinalInvoiceDelMethCode` and `PpaMatAmt` from `BillingTspConfig` when the invoice group changes
- **CheckJdeExists()** — Validates JDE key if global config `ValidateJDE` is enabled

### File 3: `QPTMServiceCore_InvoiceGroupMaintenance.cs`
**Repo:** Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
**Path:** `/Quorum.QPTM.ServiceCore/QPTMServiceCore_InvoiceGroupMaintenance.cs`

This is the service core layer. Key findings:
- **UpdateSingleInvoiceGroupMaintenanceComplete** — Auto-assigns InvoiceGrpId via `QPTMServiceUtility.GetNextSeqNo()` if it's 0, then validates, then persists
- **ValidateSingleInvoiceGroupMaintenanceCompleteInternal** — Clears errors, then runs `QPTMInvoiceGroupMaintenanceCompleteValidationContext` validators
- **AddAdditionalPropertiesInvoiceGroupMaintenanceComplete** — Complex join logic that enriches contract data with `CtrMinMaxEffDt`, copy data with contacts/addresses, and document data with descriptions. **This is a potential failure point** — if any of these joins fail (e.g., contract not found in the joined list), the resulting data could be incomplete

### File 4: `InvoiceGroupMaintenance.js` (Client-side)
**Path:** `/Quorum.QPTM.Web/Scripts/InvoiceGroupMaintenance/InvoiceGroupMaintenance.js`

- **ValidateBeforeSave** function — Makes AJAX call to `ValidateBeforeSave` controller action, shows warning dialog if JDE exists or effective dates changed, then proceeds with save callback or shows EffectiveDateSplitDialog

---

## 6. Historical ADO Work Items

| ADO # | Type | State | Title | Relevance |
|-------|------|-------|-------|-----------|
| **#1576190** | Bug | Closed | Invoice Group Maintenance's Contract tab picklist filter — bad join, wrong as-of-date | **HIGHLY RELEVANT** — Documented the exact picklist SQL issue |
| **#1635227** | Bug | Closed | XCL - Web Contract Maintenance – Invoice Tab not displaying Invoice Group for numerous contracts | Related — Web/Classic parity |
| **#1404635** | Bug | Closed | HPE - Invoice Groups (BLKINVGRP) aren't Autogenerated in web | Related — Web/Classic parity for invoice groups |
| **#1757627** | Bug | Closed | DSU - Invoice Group Maintenance – Documents tab - cannot insert row for certain groups - WEB | Related — Web-specific insert issues |
| **#1406174** | Task | Closed | DEV - Replacement contract is not linked to invoice group after awarding offer in web | Related — Contract-invoice group linkage in web |
| **#1684492** | Bug | Proposed | HPE - Billing invoice reports blank for external user when EFF DT TO is different on Invoice Group vs Contract | Related — Effective date mismatch |
| **#1781167** | Requirement | Proposed | Verify Add/Update/Delete time slice in Invoice Group Maintenance screen | Active work on this screen |

---

## 7. Historical Salesforce Cases

| Case | Status | Date | Subject | Relevance |
|------|--------|------|---------|-----------|
| **26-01102409** | New | 2026-05-21 | 2025.10 - QPTM - Invoice Group Screen Clear | Same screen, clear/requery error |
| **26-01099273** | New | 2026-05-07 | UPG26 Can't create new Invoice Group without Contract | Invoice Group creation issue post-upgrade |
| **26-01080311** | Closed | 2026-02-12 | Lauren_Minze needs permissions to add JIB Invoice Grouping | Permissions related |
| **25-01024522** | Closed | 2025-06-11 | PNGTS: Invoice Group Pay Codes | Pay codes on invoice group |
| **24-00985962** | Closed | 2024-10-22 | Invoice grouping (ADO #1694704) | General invoice grouping feature |
| **24-00957946** | Closed | 2024-05-15 | Setting Up an Invoice Group - No Invoice Group ID in the List | Invoice Group ID picklist empty |

**Note:** Case **26-01099273** is very similar — client can't create Invoice Group without a contract in UAT (post-upgrade), but production allows it. This suggests a regression or new validation in recent versions.

---

## 8. Attachments

| # | File | Type | Size | Description |
|---|------|------|------|-------------|
| 1 | Invoice Group Issue Support | PDF | 1.2 MB | Client-provided evidence showing the error (screenshots) |
| 2 | Case Analysis - 26-01088177 | HTML | 32 KB | Previous case analysis document |

**Action Required:** Review the PDF attachment for exact error messages and screenshots showing which operation fails and what error is displayed.

---

## 9. Database Tables & Configuration

### Critical Tables
| Table | Purpose |
|-------|---------|
| **BLCTRL_INVOICE_GRP** | Main invoice group header — InvoiceGrpId, TspNo, EffDateFrom, EffDateTo, BpNo, InvGrpCtgry, BillFreqCode, PayTermsCode |
| **BLCTRL_INVOICE_GRP_CTR** | Invoice group-to-contract mapping — CtrNo, TspNo, InvoiceGrpId |
| **BLCTRL_INVOICE_GRP_COPY** | Invoice group copy/distribution — ContactId, FinalInvoiceDelMethCode |
| **BLCTRL_INVOICE_GRP_DOC** | Invoice group document types — InvoiceDocCode, IsAttrTrue |
| **BLCTRL_TSP_CONFIG** | TSP billing configuration — PayTermsCode, AcctAdjMethCode, InvoiceDelMethCode, PpaMatAmt |
| **BLCTRL_TSP_CONFIG_DOC** | TSP document configuration defaults |

### Key Configuration
| Config | Value | Description |
|--------|-------|-------------|
| **ValidateJDE** | true/false | Global config — if true, `CheckJdeExists()` validates JDE key before save |
| **QueryBtnText** | varies | Global config for Query button label |
| **BLCTRL_INVOICE_GRP.INVOICE_GRP_ID** | sequence | Auto-assigned via `GetNextSeqNo()` on new invoice groups |

### Screen Registration
| Grid ID | Purpose |
|---------|---------|
| `InvoiceGrpMaintContractsGrid` | Contracts tab grid — registered picklist SQL for contract selection |
| `InvoiceGrpMaintDocumentsGrid` | Documents tab grid |
| `InvoiceGrpMaintCopiesGrid` | Copies tab grid |

---

## 10. Version & Fix Availability

| Version | Contains Fix? | Notes |
|---------|--------------|-------|
| 2021.04 | Partial | Bug #1404635 (auto-generation in web) was fixed |
| 2021.10 | Partial | Bug for contract not linked to invoice group after award was fixed |
| 2023.xx | Partial | Bug #1576190 (picklist SQL bad join) — may or may not be fully fixed |
| 2025.10+ | **Unknown** | Recent cases 26-01099273 and 26-01102409 suggest issues still exist or regressed |

**Key Finding:** The recent case 26-01099273 (May 2026) reports that post-UPG26, users can't create Invoice Group without a contract — but production allows it. This suggests a **possible regression** in the upgrade or a new validation was introduced.

---

## 11. Diagnostic SQL Queries

### Query 1: Check Invoice Group Configuration for MountainWest
```sql
SELECT ig.TSP_NO, ig.INVOICE_GRP_ID, ig.INVOICE_GRP_NM, 
       ig.BP_NO, ig.EFF_DT_FROM, ig.EFF_DT_TO,
       ig.INV_GRP_CTGRY, ig.BILL_FREQ_CODE, ig.PAY_TERMS_CODE
FROM BLCTRL_INVOICE_GRP ig
WHERE ig.TSP_NO = <MW_TSP_NO>
ORDER BY ig.INVOICE_GRP_ID, ig.EFF_DT_FROM;
```

### Query 2: Check Contracts Linked to Invoice Group
```sql
SELECT igc.TSP_NO, igc.INVOICE_GRP_ID, igc.CTR_NO, 
       igc.EFF_DT_FROM, igc.EFF_DT_TO, igc.PPA_MAT_AMT
FROM BLCTRL_INVOICE_GRP_CTR igc
WHERE igc.TSP_NO = <MW_TSP_NO>
  AND igc.INVOICE_GRP_ID = <INVOICE_GRP_ID>
ORDER BY igc.CTR_NO;
```

### Query 3: Check TSP Billing Configuration
```sql
SELECT tc.TSP_NO, tc.EFF_DT_FROM, tc.EFF_DT_TO,
       tc.PAY_TERMS_CODE, tc.ACCT_ADJ_METH_CODE, 
       tc.INVOICE_DEL_METH_CODE, tc.PPA_MAT_AMT
FROM BLCTRL_TSP_CONFIG tc
WHERE tc.TSP_NO = <MW_TSP_NO>
  AND tc.EFF_DT_FROM <= SYSDATE
  AND tc.EFF_DT_TO >= SYSDATE;
```

### Query 4: Check Contract Picklist Registration SQL
```sql
SELECT sr.SCREEN_REG_CD, sr.GRID_ID, sr.PICKLIST_ID,
       sr.SQL_TEXT, sr.FILTER_PARAMS
FROM QARCH_SCREEN_REG sr
WHERE sr.SCREEN_REG_CD = 'InvoiceGroupMaintenance'
  AND sr.GRID_ID = 'InvoiceGrpMaintContractsGrid';
```

### Query 5: Verify Contract Exists and Has Valid Date Range
```sql
SELECT c.TSP_NO, c.CTR_NO, c.CTR_NM, c.CTR_TYPE_CD,
       c.EFF_DT_FROM, c.EFF_DT_TO, c.CTR_STAT_CD
FROM NNCTRL_CTR c
WHERE c.TSP_NO = <MW_TSP_NO>
  AND c.CTR_NO = '<CONTRACT_BEING_ADDED>'
  AND c.CTR_STAT_CD NOT IN ('X', 'D');
```

### Query 6: Check Screen Validation Rules Enabled
```sql
SELECT vr.VALD_RULE_CD, vr.VALD_RULE_DESCR, 
       vr.IS_ACTIVE, vr.SEVERITY_CD
FROM QARCH_VALD_RULE vr
WHERE vr.FUNC_AREA_CD = 'BL'
  AND vr.IS_ACTIVE = 1
ORDER BY vr.VALD_RULE_CD;
```

### Query 7: Check ValidateJDE Global Config
```sql
SELECT gc.CONFIG_KEY, gc.CONFIG_VALUE
FROM QARCH_GLOBAL_CONFIG gc
WHERE gc.CONFIG_KEY LIKE '%JDE%'
   OR gc.CONFIG_KEY LIKE '%InvoiceGroup%';
```

---

## 12. Recommended Next Steps

1. **Review the PDF attachment** — Extract exact error messages and identify which specific operation fails (add new contract row, select contract from picklist, or save after adding contract)

2. **Check the Contract Picklist SQL** — Run Query 4 to get the registered SQL for the contract picklist on the Invoice Group Maintenance screen. Verify if the join logic has the known bug from ADO #1576190 (bad as-of-date join)

3. **Reproduce in a test environment** — Open Invoice Group Maintenance in web, query an existing invoice group, attempt to add a contract via the Contracts tab. Compare behavior with classic.

4. **Check MW's QPTM version** — Determine if MountainWest has the fix from ADO #1576190 deployed. If their version predates the fix, the picklist SQL issue is the likely root cause.

5. **Compare with Case 26-01099273** — This recent case (May 2026) reports similar web-only Invoice Group issues post-upgrade. Check if both cases share the same root cause.

6. **Run diagnostic queries** — Execute Queries 1-7 against MW's database to understand the current data state.

7. **If picklist SQL is the issue** — The fix involves correcting the JOIN condition in the registered SQL to properly filter contracts by the invoice group's effective date (not the current date).

---

## 13. Escalation Path

### If Configuration/Picklist SQL Issue:
1. Check `QARCH_SCREEN_REG` for the contract picklist SQL
2. Verify the JOIN logic matches the fix from ADO #1576190
3. If the SQL is still using the old bad join — apply the corrected SQL via database script
4. If the SQL is correct but still filtering out valid contracts — may need a new picklist registration

### If Code Defect:
1. Create ADO Bug: "MW - 26-01088177 - Invoice Group Maintenance - Error when adding contract in Web"
2. Link to ADO #1576190 (picklist SQL), #1635227 (web display), #1404635 (auto-generation)
3. Assign to QPTM Billing/Invoice team
4. Key files to investigate:
   - `InvoiceGroupMaintenanceController.cs` — ContractsGridAddNewRow, ContractsGridUpdate
   - `QUIControllerInvoiceGroupMaintenance.cs` — DoSave, DoValidate
   - `QPTMServiceCore_InvoiceGroupMaintenance.cs` — UpdateSingleInvoiceGroupMaintenanceComplete, AddAdditionalPropertiesInvoiceGroupMaintenanceComplete
   - Picklist SQL registration for `InvoiceGrpMaintContractsGrid`

### If Same Issue as 26-01099273:
1. Consolidate both cases under one ADO bug
2. Investigate whether UPG26 introduced a new validation or regression
3. Check release notes for Invoice Group changes in recent versions

---

## 14. Key People & Repos

### Key Repositories
| Repo | ID | Purpose |
|------|----|---------|
| Quorum.QPTM.Web | 41e317c0-844c-4728-98da-529092957738 | Core web — controllers, UI controllers, service core, validations |
| WWM.QPTM.Database | d47cc2d6-f37a-49bd-8c95-b9ec655cf8e7 | MountainWest DB scripts |
| WWM.QPTM.Metadata | 7c6b83f8-1463-4cfa-a799-de0d548d7aaf | MountainWest metadata |

**Note:** MountainWest (WWM) does NOT have a custom `WWM.QPTM.Web` repo — they use the base Quorum.QPTM.Web code for all web functionality.

### Key Source Files
| File | Location |
|------|----------|
| InvoiceGroupMaintenanceController.cs | Quorum.QPTM.Web/Quorum.QPTM.Web.Core/Controllers/ |
| QUIControllerInvoiceGroupMaintenance.cs | Quorum.QPTM.Web/Quorum.QPTM.Web.Controllers/UIControllers/ |
| QPTMServiceCore_InvoiceGroupMaintenance.cs | Quorum.QPTM.Web/Quorum.QPTM.ServiceCore/ |
| QPTMService_InvoiceGroupMaintenance.cs | Quorum.QPTM.Web/Quorum.QPTM.ServiceCore/ |
| InvoiceGroupMaintenance.js | Quorum.QPTM.Web/Quorum.QPTM.Web/Scripts/InvoiceGroupMaintenance/ |
| InvoiceGroupMaintenance.cshtml | Quorum.QPTM.Web/Quorum.QPTM.Web/Views/InvoiceGroupMaintenance/ |
| _InvoiceGroupMaintenance_ContractsTab.cshtml | Quorum.QPTM.Web/Quorum.QPTM.Web/Views/InvoiceGroupMaintenance/ |

### Related Cases & Contacts
| Name | Role | Contact |
|------|------|---------|
| Dave Reeder | MountainWest Contact / Commercial Technology Lead | david.reeder@williams.com |
| Laura Johnson | MountainWest User (reported the issue) | Via Dave Reeder |

---

*Investigation completed: 2026-05-26*
*Data Sources: Salesforce (Quorum Production), Azure DevOps (QuorumSoftware org), Quorum.QPTM.Web Git repository*
*Report generated by: L4 Support Investigation Agent*
*Next Action: Review PDF attachment for exact error messages, then run diagnostic SQL queries against MW database to verify picklist SQL and contract data*

---
---
---

# L4 Detailed Investigation Report — Case 26-01096401

**Case:** 26-01096401 | **Salesforce ID:** 500UH00000nRlEmYAK
**Date:** 2026-05-26 | **Investigator:** L4 Support Investigation Agent
**Product:** QPTM | **Module:** EDI — Inbound RRFC (Confirmation Response)
**Client:** MountainWest Pipeline, LLC (WWM) — **Receiver-side issue at TallGrass Ruby**
**Reporter:** Annette Bennion (via Dave Reeder, Williams)
**Owner:** Abhijit Pradhan

---

## TABLE OF CONTENTS

1. [Case Overview](#1-case-overview-1)
2. [Issue Understanding](#2-issue-understanding-1)
3. [Issue Classification](#3-issue-classification-1)
4. [Root Cause Analysis](#4-root-cause-analysis-1)
5. [Code Analysis](#5-code-analysis-1)
6. [Historical ADO Work Items](#6-historical-ado-work-items-1)
7. [Historical Salesforce Cases](#7-historical-salesforce-cases-1)
8. [Attachments](#8-attachments-1)
9. [Database Tables & Configuration](#9-database-tables--configuration-1)
10. [Version & Fix Availability](#10-version--fix-availability-1)
11. [Diagnostic SQL Queries](#11-diagnostic-sql-queries-1)
12. [Recommended Next Steps](#12-recommended-next-steps-1)
13. [Escalation Path](#13-escalation-path-1)
14. [Key People & Repos](#14-key-people--repos-1)

---

## 1. Case Overview

| Field | Value |
|-------|-------|
| **Case Number** | 26-01096401 |
| **Salesforce ID** | 500UH00000nRlEmYAK |
| **Subject** | MW \| Annette Bennion \| EDI Receiver not processing RRFC Correctly |
| **Status** | In Review |
| **Priority** | High |
| **Created Date** | 2026-04-27 |
| **Owner** | Abhijit Pradhan |
| **Client** | MountainWest Pipeline, LLC (sender) → **TallGrass Ruby** (receiver, affected) |
| **Predecessor Case** | 25-01047182 (Closed; fixed via ADO #1770476) |

**Client Description:**
> This is a new issue that came out of resolving case 25-01047182.
>
> On the receiver side (TallGrass Ruby), the manual RRFC is being interpreted incorrectly, where only the first SLN record is processed, which then incorrectly reduces the nomination to zero.
>
> This new behavior appears to be related to how the receiver application processes the manual RRFC file.

---

## 2. Issue Understanding

### Background — The Prior Case (25-01047182)
The prior case was about MWP sending a **manual RRFC** to Ruby in which the **outbound generated file** had records with mismatched SLN numbers (e.g., `SLN*34 @ 55,000` and `SLN*100031 @ 0` — instead of the same SLN with two volumes like the auto-response). The fix (ADO #1770476, PR !125626) targeted the **sender side** — specifically the inbound RRFC processing on MWP's system that updates the `IdConfTrk` when a manual RRFC arrives with the same quantity but a different Confirmation Tracking ID.

### What Happened (Current Case)
After the fix in the prior case was deployed, MWP resumed sending manual RRFCs. Now Ruby (the **receiver**) is seeing a new behavior:
- The manual RRFC file from MWP is **interpreted incorrectly** by Ruby's system
- Only the **first SLN record** in the file is processed
- This causes nominations to be **incorrectly reduced to zero**

### What Should Have Happened
Ruby should process **all SLN records** in the inbound manual RRFC, applying confirmation quantities to each location/cycle/contract entity correctly. The two SLN records (one for PT contract @ 0 Dth, one for PNT contract @ 55,000 Dth) should both be honored, not just the first.

### The Gap
The fix from the prior case adjusted how the system handles inbound RRFC records when `IdConfTrk` differs but quantity is the same (preserve and update `IdConfTrk` on existing record). But the fix may have introduced — or exposed — a regression in the **SLN loop processing** logic, where subsequent SLN records in the same DTM block are not being matched/applied to their respective confirmation entities. Specifically, the file structure produced by the sender now (after the fix) may differ from what Ruby's parser expects.

---

## 3. Issue Classification

| Dimension | Classification |
|-----------|---------------|
| **Primary** | **Defect (Regression)** — Receiver-side RRFC SLN-loop processing |
| **Secondary** | EDI parity issue — sender/receiver code generated different SLN structures |

**Rationale:** The case description explicitly states this is "a new issue that came out of resolving case 25-01047182." The prior fix was on the inbound RRFC processing in `CFProcessDataHelper.cs` (added handling for same qty + different `IdConfTrk`). When the sender's output file structure changed as a consequence, the receiver's SLN-loop logic in `QEdiCFMain.cs` / `CFSegmentReader.cs` is failing to match all SLN records to their respective contract/entity rows — only the first SLN is matched, then subsequent SLN records get cut to zero because no matching QPTM confirmation is found.

---

## 4. Root Cause Analysis

### Hypothesis 1: SLN Loop — First SLN consumes match, subsequent SLNs unmatched
**Probability: HIGH**

In `QEdiCFMain.cs` (lines 142-258), the SLN loop processes one SLN at a time. When the loop completes one SLN (next segment is not another SLN_N1), it calls:
- `processDataHelper.ValidateAndSetEntityInfo(currDO, ...)` to identify the conf entity
- `InboundSwitchTSPtoOperator(currDO, ...)` to swap TSP/operator
- `GetLocIdfromDRN(...)` / `GetLocIdfromProprietary(...)` to resolve location
- Then constructs a `nextDO` for the next SLN, copying over header info

If the **matching logic in `GetFilteredList()`** (CFProcessDataHelper.cs lines 28+) fails for the second SLN, the system would treat it as unmatched. Looking at the match logic:
```csharp
foreach (ConfirmationSummaryDO currQptmDO in qptmConfirmations)
{
    if (!string.IsNullOrEmpty(ediRecordToMatch.SrCtrNo) && nCycleId == currQptmDO.IdConfCycle)
    {
        ContractDO k = ediDataCacheQPTM.GetContract(currQptmDO.TspNo, ediRecordToMatch.SrCtrNo, (DateTime)ediRecordToMatch.BegDateTime);
        if (!(k == null && ... && ediRecordToMatch.SrCtrNo != currQptmDO.SrcSrCtrNo && bCtrIsMatch == false))
        {
            bCtrIsMatch = true;
            break;
        }
    }
}
```
If the sender's file now produces SLN records with different `IdConfTrk` but the **same SrCtrNo**, the first match would set `bCtrIsMatch = true` and `break` — meaning the second SLN's distinct cycle/contract data may be lost.

### Hypothesis 2: ProRateReduction applies cut to all origRecs from first SLN
**Probability: HIGH**

In `CFProcessDataHelper.cs.ProRateReduction()` (lines 530-595), when an inbound confirmation arrives, the method iterates over **all origRecs** and applies the reduction:
```csharp
if (totalQty <= dRedQty)
{
    foreach (ConfirmationSummaryDO rec in origRecs)
    {
        decimal origConfQty = rec.ConfQty;
        totalCutQty += this.CutConfRec(rec, 0, sUserID, sTxnTypeCode);  // <-- ZEROES OUT THE REC

        if (rec.ConfQty != origConfQty)
        {
            this.UpdateConfColumnValues(ediDO, rec, sTxnTypeCode);
            rec.EndEdit();
            updatedRecs.Add(rec);
        }
        // WI 1770476 - If qty unchanged but Conf Trk Id is different, only update IdConfTrk
        else if (!string.IsNullOrEmpty(ediDO.IdConfTrk) && ediDO.IdConfTrk != rec.IdConfTrk)
        {
            rec.IdConfTrk = ediDO.IdConfTrk;
            rec.EndEdit();
            updatedRecs.Add(rec);
        }
    }
}
```
If the inbound EDI has only ONE SLN at the entity level (with confirmed qty 0 because of PT contract), and the system sees `totalQty (0+55000=55000) <= dRedQty (0)` is FALSE for the auto-response case but **TRUE** for the manual case (because parsing of subsequent SLNs is failing), then **all** original records (both PT and PNT) get cut to zero.

The fact that the message says "only the first SLN record is processed" strongly suggests the parser is not iterating to the second SLN, leaving the system to interpret as if total received qty was just the first SLN's value (0), and then `CutConfRec(rec, 0, ...)` is called on every original record — zeroing both PT and PNT noms.

### Hypothesis 3: Cycle Indicator (CS segment) handling differs between manual and auto-RRFC
**Probability: MEDIUM**

The manual RRFC may not include the same `CS` (Contract Summary) segment that the auto-RRFC includes. The parser handles `DTM;CS` (line 138 in QEdiCFMain.cs) separately from `DTM;SLN` (line 142). If the manual RRFC structure omits the CS segment, the cycle determination logic in `CFProcessDataHelper.GetCycleFromInbound()` may default to a different cycle than expected, causing the SLN records to match against a different set of QPTM confirmations.

### Hypothesis 4: Tracking ID update fix (#1770476) changes how IdConfTrk is reused
**Probability: MEDIUM**

The fix in WI 1770476 added this logic to `ProRateReduction`:
```csharp
else if (!string.IsNullOrEmpty(ediDO.IdConfTrk) && ediDO.IdConfTrk != rec.IdConfTrk)
{
    rec.IdConfTrk = ediDO.IdConfTrk;
    rec.EndEdit();
    updatedRecs.Add(rec);
}
```
This means even when quantity is unchanged, the receiver updates `rec.IdConfTrk` to match the inbound. If the manual RRFC has a different `IdConfTrk` for SLN #2 than the existing QPTM record, this update could cause the second SLN's match to fail on a subsequent pass — but this should only manifest at the sender, not the receiver.

---

## 5. Code Analysis

### File 1: `QEdiCFMain.cs` (Main RRFC inbound processor)
**Repo:** Quorum.QPTM.Batch (`e024d80b-5c45-411c-93e1-78e2798ed885`)
**Path:** `/Quorum.QPTM.EDI.DataSets/G873RRFC/QEdiCFMain.cs`
**Lines:** 1052 total

Key SLN-loop logic (lines 142-258):
```csharp
else if (sLoopSection == m_sArea_2_Loop_DTM_SLN)
{
    currDO.ExtraInfo["SrBpSegExists"] = "N";
    bReturn &= base.Proc_873_Area_2_Loop_DTM_SLN(eCurrSeg, currDO, ref ediErrList);
}
else if (sLoopSection == m_sArea_2_Loop_DTM_SLN_N1)
{
    base.Proc_873_Area_2_Loop_DTM_SLN_N1(eCurrSeg, currDO, ref ediErrList);
    // ... End-of-SLN handling ...
    if (eNextSeg.LoopSection != m_sArea_2_Loop_DTM_SLN_N1)
    {
        // entity validation, location lookup, error checks
        if (bValidConfEntities)
        {
            listInConfRespRows.Add(currDO);  // <-- Add to list of confs to process
        }
        // ... initialize nextDO and copy header fields if next SLN coming ...
    }
}
```

### File 2: `CFSegmentReader.cs` (SLN segment parser)
**Repo:** Quorum.QPTM.Batch (`e024d80b-5c45-411c-93e1-78e2798ed885`)
**Path:** `/Quorum.QPTM.EDI.DataSets/G873RRFC/CFSegmentReader.cs`
**Lines:** 1002 total

Key SLN parsing (lines 432-493):
```csharp
protected bool Proc_873_Area_2_Loop_DTM_SLN(ediDataSegment eCurrSeg, ...)
{
    if (sSegmentID == m_sArea_2_Loop_DTM_SLN)  // "SLN"
    {
        currDO.IdConfTrk = eCurrSeg.get_DataElementValue(1, 0);  // SLN tracking ID
        if (currDO.IdConfTrk == "N/A") currDO.IdConfTrk = string.Empty;

        if (eCurrSeg.get_DataElementValue(3, 0) == "I")  // Item Operation = Information
        {
            decimal dQty;
            if (decimal.TryParse(eCurrSeg.get_DataElementValue(4, 0), out dQty))
            {
                if (dQty >= 0)
                {
                    // UOM conversion (G8 → MMBtu, GV → ...)
                    currDO.RecConfQty = dQty;
                    currDO.DelConfQty = dQty;
                }
                else { ediErrList.Add("ECRQR502"); ... }
            }
            if (dQty < 0) { ediErrList.Add("ECRQR503"); }
        }
    }
    // LQ and N9 handling...
}
```

### File 3: `CFProcessDataHelper.cs` (Match & reduction logic — **CHANGED BY FIX**)
**Repo:** Quorum.QPTM.Batch (`e024d80b-5c45-411c-93e1-78e2798ed885`)
**Path:** `/Quorum.QPTM.EDI.DataSets/G873RRFC/CFProcessDataHelper.cs`
**Lines:** 1202 total

**The fix from WI 1770476 (in `ProRateReduction`, lines 530-595):**
```csharp
// Existing logic: cut records that don't have qty change matching inbound
foreach (ConfirmationSummaryDO rec in origRecs)
{
    decimal origConfQty = rec.ConfQty;
    totalCutQty += this.CutConfRec(rec, 0, sUserID, sTxnTypeCode);
    if (rec.ConfQty != origConfQty)
    {
        this.UpdateConfColumnValues(ediDO, rec, sTxnTypeCode);
        rec.EndEdit();
        updatedRecs.Add(rec);
    }
    // *** WI 1770476 NEW CODE *** - update IdConfTrk even if qty unchanged
    else if (!string.IsNullOrEmpty(ediDO.IdConfTrk) && ediDO.IdConfTrk != rec.IdConfTrk)
    {
        rec.IdConfTrk = ediDO.IdConfTrk;
        rec.EndEdit();
        updatedRecs.Add(rec);
    }
}
```

The `CutConfRec(rec, 0, ...)` call **always cuts the record to 0** first, then the if-check decides whether to mark it updated. If the inbound only had ONE SLN that the parser captured (e.g., the 0 qty PT-contract SLN), then `dRedQty = 0` after reduction, and `totalQty (existing 55000) > dRedQty (0)` is true → falls into the `else` branch (`ProgressiveRounder`), which proportionally reduces — but with `dRedQty = 0`, **every record gets cut to zero**.

### File 4: `QEdiRRFCIn18.cs` and related NAESB-version-specific inbound files
There are ~30 versioned RRFC inbound parsers for different NAESB versions and feature combinations (PackageID, NomAgent). The base class methods in `QEdiRRFCInBase` and `CFSegmentReader` are shared. The version-specific subclasses only override version-specific elements.

---

## 6. Historical ADO Work Items

| ADO # | Type | State | Title | Relevance |
|-------|------|-------|-------|-----------|
| **#1770476** | Bug | **Closed** | QTR - 25-01047182 -- RUBY EDI manual RRFC creating different SLN records | **THE PRIOR FIX** — introduced this regression |
| **#1789466** | Task | Closed | QA - QTR - 25-01047182 -- (QA task for above) | QA task for the prior fix |
| **#1775521** | Patch | Packaged for Delivery | QTR - Patch 5 on 2025.04 - QPTM | Patch containing the fix |
| **#1779425** | Requirement | Closed | QTR - 2025.04 Hotfix #X - March 2026 - QPTM | Hotfix release |
| **#1799867** | Release | Closed | QPTM 2026.04.1.0 | GA release with the fix |
| **#1791477** | Release | Proposed | QPTM 2025.04.1.12 | Next 2025.04 patch |
| **#1771011** | Bug | **Proposed (open)** | GBG - 25-00999001 -- NWPL EDI RRFC File is not separating confirmation data by both UP ID and Service Requester ID | **RELATED** — receiver-side RRFC separation issue, still open |
| **#1713859** | Bug | Closed | GBG - Compare EDI code for RQCF and RRFC Outbound vs Inbound Datasets | Code review of RRFC datasets |
| **#1719524** | Bug | Closed | TEP - 24-00995059 RQCF between TSP Cheyenne and Rockies not giving RRFC after Running EDI RQCF | Related RRFC processing bug |
| **#1736037** | Task | Closed | Test Coverage Review — EDI Incoming → RRFC | Test coverage |
| **#1736064** | Task | Closed | Test Coverage Review — EDI Outgoing → RRFC | Test coverage |

**Critical:** No ADO item has been opened yet for case 26-01096401. Recommend opening one and linking to #1770476.

---

## 7. Historical Salesforce Cases

| Case | Status | Date | Subject | Relevance |
|------|--------|------|---------|-----------|
| **25-01047182** | Closed | 2025-10-07 | RUBY EDI manual RRFC creating different SLN records | **PREDECESSOR** — Whose fix introduced this regression |
| **25-01060024** | Closed | 2025-12-10 | EGWest - Questar - EDI error when receiving RRFC from MWP | **VERY RELATED** — Also receiver-side RRFC errors from MWP. Resolution noted: "errors not found after December 2025" — but might be the same underlying issue |
| 26-01097340 | Closed | 2026-04-29 | [Maintenance] SLNG Q2 Non-Prod planned maintenance | Unrelated (SLNG, not SLN) |

---

## 8. Attachments

| # | File | Type | Size | Description |
|---|------|------|------|-------------|
| 1 | **33744136** | UNKNOWN (likely EDI .txt file) | 2.3 KB | Manual RRFC EDI file from MWP causing the issue. **CRITICAL — must be reviewed to see SLN structure** |
| 2 | Case Analysis - 26-01096401 | HTML | 41.8 KB | Previous case analysis document |

**Action Required:** Open the attached EDI file (`33744136`) to inspect the actual SLN segment structure. Specifically check:
- How many SLN segments are present
- Each SLN's tracking ID (SLN*N), item operation code (`I`), and quantity
- Whether `CS` (Contract Summary) segments are present
- Whether `N1` Name segments separate the SLNs as expected
- Compare against an auto-response RRFC file (from the prior case 25-01047182) to identify the structural difference

---

## 9. Database Tables & Configuration

### Critical Tables
| Table | Purpose |
|-------|---------|
| **CFCTRL_CONF_SUMM** | Confirmation summary — `IdConfTrk`, `ConfQty`, `RecConfQty`, `DelConfQty`, `IdConfCycle`, `GasDay`, `TspNo`, `IdLoc`, `SrCtrNo` |
| **CFCTRL_CONF_SUMM_EXT** | Extension for non-receipt info on EDI confs |
| **NNCTRL_NOM_HDR** | Nomination header — linked via `IdNom` |
| **EDTRAN_QR_ERROR** | EDI error records (ECRQR*** codes) |
| **EDLOG_INBOUND** | Inbound EDI file log |
| **QCODE_ED_ERROR** | EDI error code definitions (ECRQR502, ECRQR503, ECRQR506) |

### Key EDI Error Codes (from CFSegmentReader.cs)
| Code | Meaning |
|------|---------|
| ECRQR502 | The input Quantity is missing |
| ECRQR503 | Negative quantity |
| ECRQR506 | Mandatory field SrCtrNo does not have a valid CtrNo |

### Process Type Codes
| Code | Description |
|------|-------------|
| **RRFC** | Receive Receipt/Final Confirmation (inbound 873) |
| **RQCF** | Request Confirmation (outbound 873) |
| **CFPSTRESP** | Confirmation Post-Process Response |
| **CFNOMSYNCH** | Confirmation/Nomination Synchronization step |

---

## 10. Version & Fix Availability

| Version | Contains Prior Fix (#1770476)? | Notes |
|---------|------------------------------|-------|
| 2025.04.1.10 and earlier | **No** | Pre-fix — old bug present |
| 2025.04.1.11 | **Yes** | Released 2026-03 via #1775441 |
| 2025.04 Patch 5 (QTR) | **Yes** | #1775521 |
| 2025.04 Hotfix March 2026 | **Yes** | #1779425 |
| 2026.04.1.0 | **Yes** | #1799867 |

**Critical Question:** What QPTM version is **TallGrass Ruby (receiver)** running? If they have the prior fix deployed but are still seeing this new behavior, the regression is real. If they don't have the fix, the issue might be that MWP (sender) was upgraded but Ruby was not — meaning the sender is now producing a file structure Ruby's older code can't parse.

---

## 11. Diagnostic SQL Queries

### Query 1: Find the affected confirmation records on Ruby's side
```sql
SELECT cs.TSP_NO, cs.GAS_DAY, cs.ID_CONF_CYCLE, cs.ID_LOC,
       cs.SR_CTR_NO, cs.ID_CONF_TRK, cs.CONF_QTY,
       cs.REC_CONF_QTY, cs.DEL_CONF_QTY, cs.K_FLO_CODE,
       cs.CONF_UPDT_DATE, cs.ID_CONF_USER
FROM CFCTRL_CONF_SUMM cs
WHERE cs.TSP_NO = <RUBY_TSP_NO>          -- TallGrass Ruby TSP
  AND cs.GAS_DAY BETWEEN <START_DATE> AND <END_DATE>
  AND cs.SR_CTR_NO IN ('<MWP_CTR_1>', '<MWP_CTR_2>')
ORDER BY cs.GAS_DAY, cs.ID_CONF_CYCLE, cs.ID_LOC;
```

### Query 2: Recent inbound EDI files from MWP
```sql
SELECT ei.ID_INBOUND, ei.FILE_NAME, ei.RECEIVE_DATE,
       ei.SENDER_DUNS, ei.RECEIVER_DUNS, ei.PROCESS_STAT_CD,
       ei.PROCESS_TYPE_CD
FROM EDLOG_INBOUND ei
WHERE ei.TSP_NO = <RUBY_TSP_NO>
  AND ei.PROCESS_TYPE_CD = 'RRFC'
  AND ei.SENDER_DUNS = '<MWP_DUNS>'
  AND ei.RECEIVE_DATE > SYSDATE - 30
ORDER BY ei.RECEIVE_DATE DESC;
```

### Query 3: EDI errors logged for these inbound files
```sql
SELECT qe.TSP_NO, qe.REF_ID, qe.NAESB_ERROR_CD,
       qe.ERROR_DESCR, qe.CTR_NO, qe.BEG_GAS_DAY,
       qe.SEQ_NO
FROM EDTRAN_QR_ERROR qe
WHERE qe.TSP_NO = <RUBY_TSP_NO>
  AND qe.NAESB_ERROR_CD IN ('ECRQR502', 'ECRQR503', 'ECRQR506')
  AND qe.BEG_GAS_DAY > SYSDATE - 30
ORDER BY qe.BEG_GAS_DAY DESC, qe.SEQ_NO;
```

### Query 4: Verify which version Ruby is running
```sql
SELECT * FROM QARCH_VERSION_INFO ORDER BY APPLIED_DATE DESC;
-- Or check release table:
SELECT VERSION_NO, APPLIED_DATE FROM QARCH_REL_INFO ORDER BY APPLIED_DATE DESC FETCH FIRST 5 ROWS ONLY;
```

### Query 5: Compare original noms vs after-RRFC qty
```sql
SELECT n.TSP_NO, n.BEG_GAS_DAY, n.ID_CYCLE, n.SR_CTR_NO,
       n.ID_LOC, n.K_FLO_CODE, n.NOM_QTY, n.CONF_QTY,
       n.NOM_STAT_CD
FROM NNCTRL_NOM_HDR n
WHERE n.TSP_NO = <RUBY_TSP_NO>
  AND n.BEG_GAS_DAY = '<GAS_DAY>'
  AND n.SR_BP_NO = '<MWP_BP_NO>'
ORDER BY n.SR_CTR_NO, n.ID_LOC;
```

### Query 6: Trace updates to CFCTRL_CONF_SUMM around the RRFC arrival time
```sql
SELECT cs.TSP_NO, cs.GAS_DAY, cs.ID_LOC, cs.SR_CTR_NO,
       cs.CONF_QTY, cs.ID_CONF_TRK, cs.CONF_UPDT_DATE,
       cs.ID_CONF_USER
FROM CFCTRL_CONF_SUMM cs
WHERE cs.TSP_NO = <RUBY_TSP_NO>
  AND cs.GAS_DAY = '<GAS_DAY>'
  AND cs.CONF_UPDT_DATE BETWEEN <RRFC_TIME> - INTERVAL '5' MINUTE
                            AND <RRFC_TIME> + INTERVAL '5' MINUTE
ORDER BY cs.CONF_UPDT_DATE, cs.ID_LOC;
```

### Query 7: Check if both PT and PNT noms exist for the example case
```sql
SELECT n.SR_CTR_NO, n.CTR_NO, c.CTR_TYPE_CD, n.NOM_QTY, n.CONF_QTY
FROM NNCTRL_NOM_HDR n
JOIN NNCTRL_CTR c ON c.TSP_NO = n.TSP_NO AND c.CTR_NO = n.CTR_NO
WHERE n.TSP_NO = <RUBY_TSP_NO>
  AND n.BEG_GAS_DAY = '<GAS_DAY>'
  AND n.SR_CTR_NO IN ('<MWP_CTR_PT>', '<MWP_CTR_PNT>')
ORDER BY c.CTR_TYPE_CD;
```

---

## 12. Recommended Next Steps

1. **Open the attached EDI file (33744136)** — Compare the SLN structure to a working auto-response RRFC file. Look for:
   - Number of SLN segments per DTM block
   - SLN tracking IDs (do they differ from auto-response?)
   - Presence/absence of CS segments
   - N1 segment placement

2. **Confirm Ruby's QPTM version** — Run Query 4 against Ruby's database to determine if they have the #1770476 fix deployed. This is the **most important diagnostic** — it tells us whether this is a regression in the fix, or a sender/receiver version mismatch.

3. **Reproduce in DEV** — Take the attached manual RRFC file and replay it against a DEV environment with the current code. Capture the parser state at each SLN segment to confirm Hypothesis 1 or 2.

4. **Open a new ADO Bug** — Title: `MW/Ruby - 26-01096401 - EDI Receiver not processing manual RRFC SLN records correctly`
   - Link to #1770476 (predecessor fix)
   - Link to #1771011 (NWPL related issue, still proposed)
   - Link to #1713859 (RRFC outbound vs inbound code review)
   - Assign to the QPTM EDI Confirmation team (who owned #1770476)

5. **Compare with case 25-01060024** — That EGWest case ("EDI error when receiving RRFC from MWP") was closed with note "errors not found after December 2025" — but if the prior fix landed around the same time (cherry-picked from #121145 in 2025 hotfix track), there may be a connection. Worth checking whether EGWest's case actually resolved or just stopped getting reported.

6. **Verify both sender (MWP) and receiver (Ruby) versions are aligned** — A fix on the sender's outbound logic may produce file structures the receiver's older inbound code can't parse. Recommend ensuring both sides are on the same patch level (#1775521 or later).

7. **Inspect `ProRateReduction` carefully** — The code at line 535: `totalCutQty += this.CutConfRec(rec, 0, sUserID, sTxnTypeCode);` always cuts the record to 0 before checking if quantity actually changed. If `origRecs` contains both the PT and PNT confirmation records, but the inbound DTM block was misinterpreted to have only one SLN (the PT @ 0), then both records get cut to zero. **This is the most likely code-level cause.**

---

## 13. Escalation Path

### If Regression from #1770476 Fix:
1. Reopen #1770476 or open a new related bug
2. Engineer to review the SLN-loop logic in `QEdiCFMain.cs` (lines 142-258) and the matching logic in `CFProcessDataHelper.GetFilteredList()` and `ProRateReduction()`
3. Consider whether the fix should differentiate between "manual RRFC" and "auto-RRFC" code paths
4. Add test case using the actual EDI file from attachment 33744136 in `Quorum.QPTM.AT.Tests` EDI test suite

### If Sender/Receiver Version Mismatch:
1. Document required minimum QPTM versions for the sender/receiver to align
2. Schedule Ruby to deploy QPTM 2025.04 Patch 5 or 2026.04 GA
3. Re-test the manual RRFC flow once both sides are aligned

### If Multi-Tenant EDI Standards Issue:
1. Engage NAESB standards reviewer to determine if MWP's manual RRFC file format complies with NAESB 1.8/1.9/2.0/3.0/3.1/3.2/4.0
2. Determine which NAESB version both TPAs are using
3. May need to negotiate Trading Partner Agreement (TPA) details

---

## 14. Key People & Repos

### Key Repositories
| Repo | ID | Purpose |
|------|----|---------|
| **Quorum.QPTM.Batch** | `e024d80b-5c45-411c-93e1-78e2798ed885` | Inbound RRFC processor (G873RRFC) |
| **Quorum.QPTM.ClassicBatch** | `0587e2fb-0f37-4614-991b-1d4072eb0255` | Classic C++ batch RRFC code |
| **Quorum.EDI.Framework** | `02742829-b8c5-4531-bb27-163f9a501621` | EDI framework base classes |
| **Quorum.QGM.Database** | `8bfba59c-f3dd-46ea-8d0a-f2687a763258` | QCODE_ED_ERROR table |
| **Quorum.QGM.Batch** | `f6a6c380-ed74-4860-835b-d58c462c3e9f` | NAESB message definitions |

### Key Source Files
| File | Location | Purpose |
|------|----------|---------|
| **QEdiCFMain.cs** | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G873RRFC/ | Main RRFC inbound orchestrator |
| **CFSegmentReader.cs** | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G873RRFC/ | SLN, LQ, N9, CS segment parser |
| **CFProcessDataHelper.cs** | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G873RRFC/ | **Match/reduction logic — CHANGED BY #1770476** |
| **QEdiRRFCIn18.cs ... In40.cs** | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G873RRFC/ | Version-specific NAESB parsers |
| **NAESB_1_8_NMQR_Msgs.txt** | Quorum.QPTM.Batch/Quorum.QPTM.EDI.DataSets/G874NMQR/ | NAESB error code definitions |

### Key PRs (Prior Fix #1770476)
| PR # | Repo | Title |
|------|------|-------|
| **!125626** | Quorum.QPTM.Batch | [2/2] Update IdConfTrk in RQCF Processing if Conf Trk Id is different [develop] |
| !125191 | Quorum.QPTM.Batch | Original PR (cherry-pick source) |
| !125624 | Quorum.QPTM.Batch | Cherry-pick to hotfix branch |
| !125625 | Quorum.QPTM.Batch | Cherry-pick to release branch |
| !121145 | Quorum.QPTM.ClassicBatch | Original ClassicBatch C++ fix |
| !121578 | Quorum.QPTM.ClassicBatch | Cherry-pick to hotfix/17.33.2 |
| !121579 | Quorum.QPTM.ClassicBatch | Additional cherry-pick |

### Related Cases & Contacts
| Name | Role | Contact |
|------|------|---------|
| Annette Bennion | MountainWest Reporter | Via Dave Reeder |
| Dave Reeder | MW Commercial Technology Lead | david.reeder@williams.com |
| Abhijit Pradhan | Case Owner | abhijit.pradhan@quorumsoftware.com |

---

*Investigation completed: 2026-05-26*
*Data Sources: Salesforce (Quorum Production), Azure DevOps (QuorumSoftware org), Quorum.QPTM.Batch Git repository*
*Report generated by: L4 Support Investigation Agent*
*Next Action: (1) Review attached EDI file 33744136 for SLN structure; (2) confirm Ruby's QPTM version; (3) reproduce in DEV with the actual EDI file*

---
---

## Case 26-01099543 — EGWest Questar PDA correction request

| Field | Value |
|---|---|
| Subject | EGWest - Questar - NEED PDA's corrected or deleted allowing me to fix |
| Status / Priority | **Pending Customer** (since 2026-05-27) / Medium |
| Client / Account | Questar Gas Company (EGWest) |
| Created / Owner | 2026-05-08 / Abhijit Pradhan |
| Attachments | 1 — Case Analysis HTML (no client screenshots in SF; check email/HTML for screenshots) |

### Current status (refreshed 2026-06-05)
Ball is with the **customer** — Abhijit moved it to Pending Customer on 2026-05-27 after a 5/26–5/27 back-and-forth (status flipped Pending Customer ↔ Pending Quorum 3×). **Still no client screenshots, comments, or emails synced into Salesforce** — only our own auto-generated "Case Analysis" HTML (created 5/08, minutes after intake). The 10 contract numbers + wrong→right shipper-BP mapping the customer promised are **not in SF**, so the case is blocked on that input. No similar PDA "wrong Service Requester" case exists in SF history (the only Questar-adjacent prior is closed 26-01098270 nom→CAS). Open age: 28 days.

### Issue
User did 10 PDAs and assigned **Service Requester = end user** when it should be **Service Requester = shipper**. Wants the 10 contracts' PDAs either deleted (so she can redo) or updated to the correct shipper BP.

### Classification
**Data correction (user error)** — not a code defect. No system bug to fix. Action is a DB update/delete + re-entry.

### Most likely root cause
Operator error during PDA entry. No code path to investigate. The PDA Maintenance screen does allow editing the Service Requester (BP_NO field on `ALCTRL_PDA_HDR`), but the user is asking for backend correction probably because:
- The 10 PDAs may already be referenced by allocations / settlements and the UI blocks the edit, OR
- Bulk fix is faster than 10 individual screen edits

Validation rules that may be blocking UI edit: `Quorum.QPTM.Validations.Rules.PDA/` (RuleAL00000010, RuleAL00000050, RuleAL00000250, RuleAL00000470, RuleAL00000480). See [SKILL_QPTM_Nomination_Validation.md](SKILL_QPTM_Nomination_Validation.md) for rule type semantics (LI vs BI).

### History — relevant
| Ref | Status | Why it matters |
|---|---|---|
| No prior ADO/SF cases on PDA "service requester wrongly assigned" | — | First report of this scenario for Questar |
| 26-01098270 (EGWest Questar, Closed) | — | Adjacent Questar nom issue — confirms allocation flow is otherwise healthy |

### Diagnostic queries
Get the 10 PDAs in question — needs contract list from the case attachment/email first.
```sql
-- 1. List Questar PDAs likely affected (filter by gas day / TSP / contracts the user identifies)
SELECT h.TSP_NO, h.CTR_NO, h.BEG_GAS_DAY, h.END_GAS_DAY,
       h.BP_NO        AS CURRENT_SR_BP,   -- the "wrong" one she set
       h.BP_NM        AS CURRENT_SR_NM,
       h.PDA_HDR_NO, h.LAST_UPDT_DT, h.LAST_UPDT_USER
FROM ALCTRL_PDA_HDR h
WHERE h.TSP_NO = <QUESTAR_TSP_NO>
  AND h.CTR_NO IN ('<10 CTR NOS FROM ATTACHMENT>')
ORDER BY h.CTR_NO, h.BEG_GAS_DAY;

-- 2. Check if any are already locked by downstream allocation/settlement
SELECT a.TSP_NO, a.CTR_NO, a.GAS_DAY, a.ALLOC_STAT_CD, a.IS_POST
FROM ALCTRL_ALLOC a
WHERE a.TSP_NO = <QUESTAR_TSP_NO>
  AND a.CTR_NO IN ('<10 CTR NOS>')
  AND a.GAS_DAY BETWEEN <PDA_START> AND <PDA_END>;

-- 3. Audit history of who/when set the wrong SR
SELECT * FROM ALCTRL_PDA_HDR_AUDIT
WHERE PDA_HDR_NO IN (<from query 1>)
ORDER BY UPDT_DATE DESC;
```

### Next steps
1. **Get the 10 contract numbers** from the case attachment (Case Analysis HTML) or ask user — required input
2. **Run Query 1 & 2** — confirm current state and whether any PDAs are locked (posted)
3. **If unlocked:** Easier path = give user the steps to correct in UI (PDA Maintenance → edit BP_NO field per contract). Confirm whether the UI lets her edit existing PDAs in her version
4. **If locked or volume too large:** Submit DB script request to update `ALCTRL_PDA_HDR.BP_NO` and `BP_NM` for the 10 PDAs to the correct shipper BP. Get DBA approval + signed-off mapping (wrong-BP → correct-BP) from the user
5. **Confirm with user**: delete-and-recreate vs in-place correct — recommend in-place correct to preserve audit trail and any downstream allocations

---
---

## Case 26-01092431 — PEP TIPS Propane Bantry totals off by 0.1

| Field | Value |
|---|---|
| Subject | TIPS: Total propane produced value discrepancies |
| Status / Priority | In Progress / High |
| Client / Plant / Product | Pivotal Energy Partners (PEP) / Bantry / Propane |
| Created / Owner | 2026-04-09 / Raphael Guarin |
| Predecessor | **26-01087872** (Closed) — Liquid Recovery negative-inventory fix; resolution = *"use Outlet Analysis MTR No when meters use Liquid Recovery custom rule"* |
| Related open ADO | **#1804089** — PEP DEVA1 refresh from PRDA1 (In Progress) — needed to reproduce |
| Linked open SF | **26-01092079** — PEP Hotfix Patch #6 on 2023.04 |

### Issue
After applying the prior case's workaround (switch to **Outlet Analysis MTR No** for the Liquid Recovery custom rule), the Bantry **Propane produced totals are off by 0.1** on the WIO statement. Auto-calculation paths produce slightly different values now. Multiple walkthroughs attached (Mar–Apr 2026 statements + calc spreadsheet).

### Classification
**Defect (very low impact / rounding)** — most likely a precision/rounding mismatch between the two allocation paths (original meter vs Outlet Analysis MTR) introduced by the workaround. Not a config issue — user already followed the prescribed fix from the prior case.

### Most likely root cause — Liquid Recovery custom calc, two precision paths
**Repo:** `Quorum.TIPS.ClassicBatch` (`5b7becfb-1d08-4652-956c-ab992b1d762d`)
**Files:** `QPDllPipelineMgrAL/QPSAlloc.cpp`, `QPipelineMgrLib_AL/QAllocationsUtility.cpp` and `QSQL_AllocationsUtility.cpp`
**Client overrides to check:** `PEP.TIPS.ClassicBatch` (`964946d6-71c6-472a-910a-7ca6171de67a`) and `PEP.TIPS.Database` (`cad24b7a-fc8a-4b83-ab84-ef4a7d775caf`) — PEP has custom DB + ClassicBatch, no custom Application.QPEC overrides for allocation logic visible

Symptom (off by **0.1**) is the classic signature of:
- Rounding applied at **two different stages** when the Outlet Analysis MTR path is used vs the original meter path (e.g., one path rounds at GPM, the other at recovered-volume), OR
- **UoM conversion** loss: SCT-1364378-style propane GPM precision change (1 decimal vs 4 decimals) — see ADO #1232991 ("Display Propane when SI Units at 20C is selected") and #1364378 (Propane GPM change between runs)

Off-by-0.1 across months (Feb-final, March-ADJ, etc.) consistently → not a one-off data anomaly → systemic precision issue in the Outlet Analysis MTR calculation path.

### History — relevant
| Ref | Status | Why it matters |
|---|---|---|
| SF **26-01087872** | Closed | Predecessor — workaround is the root cause of this discrepancy |
| SF **26-01086773** | Closed | PEP CHKNEGVOL negative liquid volumes — same Bantry / Propane area |
| ADO **#1364378** | Closed | SCT Propane GPM precision change between runs — same precision-loss family |
| ADO **#1232991** | Closed | Propane SI Units at 20C — display/calc precision |
| ADO **#1570630 / #1637002 / #1637004** | Closed | Williams custom Propane CTL calc — custom-rule precision bugs (pattern match) |
| ADO **#1804089** | In Progress | PEP DEVA1 refresh — required before reproducing |

### Diagnostic queries
```sql
-- 1. Compare allocated volumes via the two paths for the impacted gas month
SELECT a.PLANT_NO, a.MTR_NO, a.GAS_DAY, a.PROD_CODE, a.PROD_GROUP,
       a.GROSS_VOL_QTY, a.RECOV_VOL_QTY, a.GPM_VAL,
       a.ALLOC_RULE_CD, a.LAST_UPDT_DT
FROM ALCTRL_PDA_DTL a
WHERE a.PLANT_NO = <BANTRY_PLANT>
  AND a.PROD_CODE = 'C3'        -- Propane
  AND a.GAS_DAY BETWEEN '2026-02-01' AND '2026-03-31'
  AND a.MTR_NO IN ('Q40664', '<OUTLET_ANALYSIS_MTR>')
ORDER BY a.GAS_DAY, a.MTR_NO;

-- 2. Check allocation rule registration for the meter
SELECT m.MTR_NO, m.OUTLET_ANALYSIS_MTR_NO, m.ALLOC_RULE_CD,
       m.EFF_DT_FROM, m.EFF_DT_TO
FROM ALCTRL_MTR_RULE m
WHERE m.PLANT_NO = <BANTRY_PLANT>
  AND m.MTR_NO IN ('Q40664', '<OUTLET_ANALYSIS_MTR>')
ORDER BY m.EFF_DT_FROM DESC;

-- 3. Compare Mar-2026 (ADJ) vs Feb-2026 (FINAL) propane totals — confirm the 0.1 delta
SELECT s.PLANT_NO, s.STMT_PERIOD, s.STMT_TYPE_CD,
       s.PROD_CODE, SUM(s.NET_VOL_QTY) AS TOTAL_PROPANE
FROM ALCTRL_WIO_STMT s
WHERE s.PLANT_NO = <BANTRY_PLANT>
  AND s.PROD_CODE = 'C3'
  AND s.STMT_PERIOD IN ('2026-02', '2026-03')
GROUP BY s.PLANT_NO, s.STMT_PERIOD, s.STMT_TYPE_CD, s.PROD_CODE
ORDER BY s.STMT_PERIOD;

-- 4. Check column precision/scale on key volume/GPM fields
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_PRECISION, DATA_SCALE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME IN ('ALCTRL_PDA_DTL','ALCTRL_MTR_RULE','ALCTRL_WIO_STMT')
  AND COLUMN_NAME LIKE '%QTY%' OR COLUMN_NAME LIKE '%GPM%';
```

### Next steps
1. **Wait for PEP DEVA1 refresh** (ADO #1804089) → once landed, reproduce Feb/Mar 2026 PRD run in DEVA1
2. **Run Query 1 & 2** — confirm which meter the allocator is using and the GPM precision actually stored
3. **Open the spreadsheet** `Calcualtions with the allocation query.xlsx` + walkthrough doc `PEP - L4 bfr walkthrough - 26-01092431 v2.docx` — these have the user's exact arithmetic showing where the 0.1 emerges
4. **Trace `QPSAlloc.cpp` Liquid Recovery branch** in Quorum.TIPS.ClassicBatch — specifically where it switches to Outlet Analysis MTR No. Look for `ROUND(...)` or implicit `DECIMAL(p,s)` truncation that differs from the original-meter path
5. **Open ADO Bug** linked to predecessor #/case 26-01087872 once root cause confirmed — title: `PEP - 26-01092431 - Liquid Recovery (Outlet Analysis MTR) precision mismatch causes 0.1 propane total delta`
6. **Confirm fix path with PEP**: a rounding fix may need a Hotfix Patch #7 on 2023.04 (Patch #6 currently with customer per SF 26-01092079)

---
---

## Case 26-01093703 — IACX POP Statement Pentanes Plus shrink ≠ Settled Products

| Field | Value |
|---|---|
| Subject | TIPS: POP Statement Pentanes Plus Shrink Does Not Match Settled Products Amt |
| Status / Priority | In Progress / High — **TRIGGERING AUDITS** |
| Client / Plant / Meter | IACX Energy LLC (Cimarron) / Meter 34628-00 / Product C5+ |
| Created / Owner | 2026-04-15 (42d) / Raphael Guarin |
| Has L4 escalation doc? | **YES** — `L4_Escalation_IACX_26-01093703.docx` (532 KB, 2026-05-14) — read first |
| In-flight IACX hotfix | **SF #26-01101133** "IACX Hotfix #7 - May 2026" — Development In Progress |

> **2026-06-08 — REWRITTEN after reading the actual source.** Prior entry below the line was hypothesis-only and named non-existent `ALCTRL_*` tables. The mechanism below is proven from `sp_qtip_rpt_gas_stmt.sql`.

### Issue
POP (Percentage of Proceeds) Gas Statement shows a **Pentanes Plus (C5+) shrink volume** that does not match the **Settled Products query** for meter 34628-00. Customer adds that it does **not** match the **Allocated Products** figure "as it should" either. High priority — the variance is triggering audits.

### Classification
**Expected behaviour / Configuration — NOT a code defect.** The statement and the Settled Products query read **different bases by design**. The C5+ divergence is produced by a deliberate, long-standing override (internal **Issue 64669**, added 2008) inside the statement-build proc — not a calculation bug. Whether the statement *should* match the customer's *Allocated* number is a **config (formula-mapping)** question.

### Root cause — PROVEN from source
The two screens read two different tables, and the statement's C5+ value is deliberately overwritten:

- **Settled Products query** → live **`QTRAN_SETTLE_PROD`** → the **settled** shrink (`APPLIED_VOL_HV`=MMBtu, `APPLIED_VOL_GAS_VOL`=MCF).
- **POP Gas Statement** → snapshot **`QTIP_RPTS_SETTLE_STMT`** (via view `qtip_rpts_gas_stmt_vw`), built by **`sp_qtip_rpt_gas_stmt.sql`** (`IAC.TIPS.Database/Client/Oracle/Procs/`).

Inside that proc:
1. **Baseline** — cursor `C_PRODUCT_CSR` (L137) sets the snapshot shrink columns `PROD_CTR_SHRK_MMB_n / _MCF_n` to the **settled** value `PROD.APPLIED_VOL_HV / APPLIED_VOL_GAS_VOL` **from `QTRAN_SETTLE_PROD`** (L154-155). At this point statement == Settled Products.
2. **Override** — cursors `C_GALC5_CSR` (L590, Pentanes Plus) and `C_CALNAT_CSR` (L656, natural gasoline); update loops L3646-3720 / L3765-3837. For any contract whose **`CTR_UOM_CD='GALC5+'`** (or `'GALNAT'`), the matching product's shrink column is **overwritten** with the **allocated** value — `SUM(HEAT_VALUE)/SUM(GAS_VOL)` from **`QTRAN_ALLOC_VOL`**, scoped to products mapped to user-defined formula `FORMULA_ID='GALC5+'` in **`QCTRL_UDEF_FORMULA_DTL`** (`PLANT_NO='ALL'`).
3. The override fires **only when settled ≠ allocated**: `WHERE A.APPLIED_VOL_HV <> C.HEAT_VALUE AND A.CTR_UOM_CD='GALC5+' AND A.MTR_SFX <> '@'` (L646-651).

**Net effect for C5+:** wherever a GALC5+ contract's settled applied volume differs from its allocated volume, the statement shows the **allocated** C5+ shrink while Settled Products shows the **settled** C5+ shrink → the two **cannot** tie. By design.

**Why it may not match the *Allocated* query either:** the override's number is **not** a raw allocated total — it is `SUM(QTRAN_ALLOC_VOL.HEAT_VALUE)` restricted to the exact `PROD_CD/DISP_CD` set mapped to the **`GALC5+` formula**. If the customer's Allocated Products screen sums a different product/disposition scope, it won't match. **`QCTRL_UDEF_FORMULA_DTL` `GALC5+` is the config that decides which allocated products feed the statement.**

### Key files (verified this session)
| File | Role |
|---|---|
| `IAC.TIPS.Database / Client/Oracle/Procs/sp_qtip_rpt_gas_stmt.sql` | **Snapshot populator** — baseline shrink (C_PRODUCT_CSR L137-155) + **GALC5+/GALNAT override** (C_GALC5_CSR L590, C_CALNAT_CSR L656, loops L3646-3837) |
| `IAC.TIPS.Database / Client/Oracle/Views/qtip_rpts_gas_stmt_vw.sql` | Report view — reads `QTIP_RPTS_SETTLE_STMT` snapshot, **not** `QTRAN_SETTLE_PROD` |
| `IAC.TIPS.Reports / .../Client/QIAC/GAS_STMT.txt` | Crystal report — `@shrk_mmb_1..7` read `PROD_CTR_SHRK_MMB_n`; `tot_shrk_mmb` sums them |

### Tables (corrected — prior entry named non-existent ALCTRL_* tables)
| Table | Purpose |
|---|---|
| `QTRAN_SETTLE_PROD` | **Settled** products — what the Settled Products query reads (`APPLIED_VOL_HV`=shrink MMBtu) |
| `QTRAN_ALLOC_VOL` | **Allocated** volumes — source the override sums for GALC5+/GALNAT |
| `QTIP_RPTS_SETTLE_STMT` | **Statement snapshot** the POP report renders (`PROD_CTR_SHRK_MMB_n`) |
| `QCTRL_UDEF_FORMULA_DTL` | **Config** — `FORMULA_ID='GALC5+'/'GALNAT'` maps which `PROD_CD/DISP_CD` feed the override |
| `QCODE_PRODUCT` | Product descriptions (`PROD_DESCR` drives which `PROD_CODE_n` slot is overwritten) |

### ADO / history
No ADO work item governs this — **Issue 64669** is a 2008 pre-ADO internal number, and the case is not linked to ADO (work-item search returned 0). The override has been in the client proc since 2008.

### Diagnostic SQL (Oracle, IACX — substitute :RUN_ID = the statement's settlement run)
```sql
-- 1. SETTLED shrink for the meter (what the Settled Products query shows)
SELECT TRNX_ID, MTR_NO, MTR_SFX, PROD_CD, DISP_CD, CTR_UOM_CD,
       APPLIED_VOL_HV       AS SETTLED_SHRK_MMB,
       APPLIED_VOL_GAS_VOL  AS SETTLED_SHRK_MCF
FROM   QTRAN_SETTLE_PROD
WHERE  MTR_NO = '34628' AND RUN_ID = :RUN_ID
ORDER  BY MTR_SFX, PROD_CD;

-- 2. STATEMENT snapshot shrink (what the POP report shows) — find the 'PENTANES +' slot
SELECT MTR_NO, MTR_SFX, TRNX_ID, RUN_ID,
       PROD_CODE_1, PROD_CTR_SHRK_MMB_1, PROD_CTR_SHRK_MCF_1,
       PROD_CODE_2, PROD_CTR_SHRK_MMB_2, PROD_CTR_SHRK_MCF_2,
       PROD_CODE_3, PROD_CTR_SHRK_MMB_3, PROD_CTR_SHRK_MCF_3,
       PROD_CODE_4, PROD_CTR_SHRK_MMB_4, PROD_CTR_SHRK_MCF_4,
       PROD_CODE_5, PROD_CTR_SHRK_MMB_5, PROD_CTR_SHRK_MCF_5
FROM   QTIP_RPTS_SETTLE_STMT
WHERE  MTR_NO = '34628' AND RUN_ID = :RUN_ID;

-- 3. The OVERRIDE's allocated SUM (what the statement is really showing for GALC5+)
SELECT A.MTR_NO, A.MTR_SFX, A.TRNX_ID,
       SUM(A.HEAT_VALUE) AS ALLOC_SHRK_MMB,
       SUM(A.GAS_VOL)    AS ALLOC_SHRK_MCF
FROM   QTRAN_ALLOC_VOL A
JOIN   QCTRL_UDEF_FORMULA_DTL B
       ON A.PROD_CD = B.PROD_CD AND A.DISP_CD = B.DISP_CD
      AND B.FORMULA_ID = 'GALC5+' AND B.PLANT_NO = 'ALL'
WHERE  A.RUN_ID = :RUN_ID AND A.MTR_NO = '34628'
GROUP  BY A.MTR_NO, A.MTR_SFX, A.TRNX_ID;

-- 4. Which products feed the override (explains divergence from a raw Allocated total)
SELECT FORMULA_ID, PLANT_NO, PROD_CD, DISP_CD
FROM   QCTRL_UDEF_FORMULA_DTL
WHERE  FORMULA_ID IN ('GALC5+','GALNAT')
ORDER  BY FORMULA_ID, PROD_CD, DISP_CD;
```
**Expected:** #2 == #3 (statement = override allocated SUM) and #2 ≠ #1 (settled) → confirms the override, not a bug. If instead #2 == #1, the override didn't fire (check `CTR_UOM_CD`, `MTR_SFX='@'`, settled==allocated). Variance = #1 − #3.

### Resolution path (depends on what the statement *should* show — confirm with the business)
- **A. Statement should equal Settled Products** → remove/gate the GALC5+/GALNAT override loops (L3646-3837) in the client proc. Code change, `IAC.TIPS.Database`. **Caution:** the override is intentional (Issue 64669) and affects *all* GALC5+ statements — confirm IACX truly wants the settled basis first.
- **B. Statement should equal Allocated Products (customer's stated expectation)** → override intent is right but its **product scope** is the problem: correct the `QCTRL_UDEF_FORMULA_DTL` `GALC5+` membership so the summed allocated products equal the Allocated Products screen. **Configuration, no code.** Most likely the answer.
- **C. Difference is legitimate** → settlement applied a contractual/theoretical C5+ volume different from raw allocation; statement (allocated) vs Settled Products (settled) differ by design. **Education only** — explain the basis difference to the auditors.

### Next steps
1. Run Diagnostic SQL #1-#4 for meter 34628 + the statement's RUN_ID. Confirm statement == allocated override (#2==#3) and capture the exact variance vs settled (#1).
2. Inspect #4 (`GALC5+` formula membership) vs the customer's Allocated Products query scope — that comparison decides A vs B vs C.
3. Rule out staleness: confirm the on-screen statement's RUN_ID is the latest settlement run (a re-settlement / SETTLEREV after the statement was built leaves the snapshot stale).
4. Same-day customer update (audit urgency): the statement intentionally shows the **allocated** C5+ shrink while Settled Products shows the **settled** value; we're confirming whether the formula scope needs correction. Interim source-of-truth = the basis the auditors require (settled vs allocated), per #2 above.

---
---

## Case 26-01067755 — EQT QEMAIL warning: sending to QPEC_SCHEDULER (no email)

| Field | Value |
|---|---|
| Subject | QEMAIL process attempting to send email to QPEC_SCHEDULER account — results in warning |
| Status / Priority | In Progress / Medium |
| Client | EQT Corporation |
| Created / Owner | 2026-01-21 (127d) / Aditya Bhagat |
| Attachments hint | Event Detector Setup screens + Event Notice Queue query → **NOT** scheduled-report email, it's **Event Notification** |

### Issue
QEMAIL ends in WARNING (not failure) each cycle because it's trying to email **QPEC_SCHEDULER** (a service account with no email). Customer wants the warning gone — either stop sending to it, or skip cleanly.

### Classification
**Configuration first → Code defect if config doesn't fix it.** Recipient should not be QPEC_SCHEDULER; the system should also defensively skip recipients with no email address.

### Most likely root cause
This is the **Event Detector** path (not Scheduled Reports). Attached screenshots are "EMAIL Event Detector Setup" and "Event Notice Queue query" → the trigger is a row in `QARCH_EVENT_NOTICE_QUEUE`. An Event Detector is configured with QPEC_SCHEDULER as a recipient (or sending to "the user who triggered the event" where the triggering user is QPEC_SCHEDULER service account).

**Code: `Quorum.QFC.CPP.GUI/QFC/QDBEventDetector.cpp` + `QEventNotification.cpp`** — the classic-GUI event detector enqueues notifications. Likely no null/empty-email guard on recipient.

### Key files / tables / codes
| Item | Where |
|---|---|
| **Code (classic)** | `Quorum.QFC.CPP.GUI/QFC/QDBEventDetector.cpp` |
| **Code (classic)** | `Quorum.QFC.CPP.GUI/QFC/QEventNotification.cpp` |
| Table — event queue | `QARCH_EVENT_NOTICE_QUEUE` (same table as TransGas case #26-01069500) |
| Table — event detector cfg | `QARCH_EVENT_DETECTOR` / `QARCH_EVENT_DETECTOR_RCPT` |
| Table — user master | `QARCH_USER` (USER_ID, EMAIL — likely NULL for QPEC_SCHEDULER) |
| Config | `EMAIL_PASSWORD`, `USER_AUTHENTICATE_IND` (the SMTP-side ones — probably NOT relevant here) |

### History — relevant
| Ref | State | Why it matters |
|---|---|---|
| ADO **#1635802** | Closed | UAT QEMAIL password reset — **NOT this issue** (SMTP auth) |
| ADO **#1785999, #1789443, #1784351, #1769407, #1760971, #1772282** | Closed | All SMTP connectivity/auth bugs — **NOT this issue** |
| → | — | **No existing ADO bug matches "QEMAIL sending to recipient with no email"**. Open new one if config fix doesn't work. |

### Diagnostic SQL
```sql
-- 1. Confirm QPEC_SCHEDULER has no email and is a service account
SELECT USER_ID, USER_NM, EMAIL, IS_SVC_ACCT, IS_ACTIVE, BP_NO
FROM QARCH_USER
WHERE USER_ID = 'QPEC_SCHEDULER';

-- 2. Find which Event Detector has QPEC_SCHEDULER as a recipient
SELECT ed.EVENT_DETECTOR_CD, ed.EVENT_DETECTOR_DESCR,
       rcpt.USER_ID, rcpt.EMAIL_OVERRIDE
FROM QARCH_EVENT_DETECTOR ed
JOIN QARCH_EVENT_DETECTOR_RCPT rcpt
  ON rcpt.EVENT_DETECTOR_CD = ed.EVENT_DETECTOR_CD
WHERE rcpt.USER_ID = 'QPEC_SCHEDULER'
   OR ed.NOTIFY_TRIGGERING_USER_IND = 1;   -- "send to triggering user" flag

-- 3. Look at the actual queued events involving QPEC_SCHEDULER
SELECT EVENT_NOTICE_QUEUE_ID, EVENT_DETECTOR_CD, TRIGGERING_USER_ID,
       RECIPIENT_USER_ID, STATUS_CD, ATTEMPT_DT, ERROR_MSG
FROM QARCH_EVENT_NOTICE_QUEUE
WHERE (RECIPIENT_USER_ID = 'QPEC_SCHEDULER'
       OR TRIGGERING_USER_ID = 'QPEC_SCHEDULER')
  AND ATTEMPT_DT > SYSDATE - 7
ORDER BY ATTEMPT_DT DESC;

-- 4. See the warning text the QEMAIL batch emits
SELECT * FROM QARCH_LOG_MSG
WHERE PROCESS_TYPE_CD = 'QEMAIL'
  AND MSG_TEXT LIKE '%QPEC_SCHEDULER%'
  AND CREATE_DT > SYSDATE - 7;
```

### Next steps
1. **Run Query 1 + 2** — confirms (a) QPEC_SCHEDULER has no email, and (b) WHICH event detector(s) target it
2. **Config fix path (try first, no code needed):**
   - If Query 2 shows a detector with QPEC_SCHEDULER explicit → remove it from `QARCH_EVENT_DETECTOR_RCPT`
   - If Query 2 shows detector with `NOTIFY_TRIGGERING_USER_IND = 1` and QPEC_SCHEDULER is triggering events → either set the flag to 0, or set an `EMAIL_OVERRIDE` on the recipient row, or assign a forwarding email to QPEC_SCHEDULER in `QARCH_USER.EMAIL`
3. **If customer wants permanent fix** (warning should never fire even if a future svc account gets misconfigured) → open new ADO Bug:
   - Title: `EQT - 26-01067755 - QEMAIL should skip recipients with NULL/empty email instead of warning`
   - Code site: `Quorum.QFC.CPP.GUI/QFC/QEventNotification.cpp` — add guard `if (recipient.email.empty()) continue;` before send
   - Not a security/SMTP family bug — distinct from #1785999 etc.
4. **Reply to customer** with the config fix steps + offer to apply if they grant DB access; otherwise hand them the queries
5. **Easy-mode workaround for customer** in the meantime: assign a dummy email (e.g., `noreply@eqt.com`) to QPEC_SCHEDULER in `QARCH_USER.EMAIL` → warning vanishes

---

## Case 26-01063725 — ENT ALR24M shows PPA fuel Qty with no change in Fuel Rate / Alloc Qty

| Field | Value |
|-------|-------|
| Case | 26-01063725 (SF Id 500UH00000gQukjYAC) |
| Client | Enterprise Products Operating LLC (contacts Lali, Diane; CSM Sara Riano) |
| Subject | ALR24M shows PPA fuel Qty when there was no change in Fuel Rate and Allocated Qty |
| Status / Priority | In Progress / **P1** |
| Opened | 2026-01-05 (~148d) |
| Predecessor | Case **25-01033013** / ADO Bug **#1753672** — **Closed "could not reproduce" (NOT fixed)** |

### Issue
On a reversal/restate cycle the ALR24M (ALRPT_24) report shows a **PPA fuel quantity even though neither the fuel rate nor the allocated quantity changed**. Spurious variance appears in `ALHIST_ALLOC_LATEST_VW` between the reversal and restate snapshots. Now **reproducible**: ENT recreated it under the **TMV plant after a TIPS rerun** — PPA Fuel then shows on TMV in QPTM. (Triggers audits → flagged High.)

### Most likely root cause
PPA fuel is being **re-stamped on the restate path even when its inputs are unchanged**, driven by the TIPS→QPTM allocation re-sync rather than a "no change → carry prior fuel forward" path.
- **H1 (primary): TIPS pointer-alloc re-sync re-fires PPA fuel.** ENT-specific `ENT.QPTM.ClassicBatch /QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync_PRM.cpp` syncs TIPS pointer allocations back into QPTM. A TIPS rerun re-pushes allocation, and the PPA event re-generates a non-zero fuel delta even when rate × alloc qty is identical. Matches customer's "TIPS/QPTM process is contributing" + TMV-plant repro.
- **H2 (secondary): report pre-process recompute.** `Quorum.QPTM.ClassicBatch /QPDllPipelineMgrRPT/QSQL_PreReportProcessRR.cpp` (RR = reversal/restate) reads `ALHIST_ALLOC_LATEST_VW`; if it recomputes PPA fuel instead of carrying the latest history row, the report shows fuel with no underlying change.
- Earlier customer guess "result of rounding" is **unconfirmed** — the TMV repro suggests a real recompute, not rounding.

### Related history
| Item | Note |
|------|------|
| ADO Bug #1753672 | Same symptom; closed 2025-10 because customer agreed to close & reopen with fresh data cut — **no fix shipped**. Dev (Christine/Grayson Lee) was blocked on reproduction (PQID/message logs purged after 2 months). |
| PQID 23264883 / 23464883 | Process queue ids = source of the PPA event records in DEV (from #1753672 thread) |
| Key code | `QPSTIPSPtrAllocSync_PRM.cpp` (ENT), `QSQL_PreReportProcessRR.cpp`, `QPSResolveUdefPPAMeters.cpp` (TIPS UDEF PPA meters) |
| Tables/views | `ALHIST_ALLOC_LATEST_VW`, PPA event/alloc history; report = ALRPT_24 |
| Env | PSTA (ENT test, nightly refresh) — usable for repro |

### Diagnostic queries
```sql
-- 1. Reversal vs restate fuel delta with rate & alloc qty held constant (TMV plant)
SELECT BA_NO, PLANT, RCPT_MTR_NO, ACCT_PERIOD, ALLOC_QTY, FUEL_RATE, PPA_FUEL_QTY, ACTION_CD
FROM   ALHIST_ALLOC_LATEST_VW
WHERE  BA_NO = 11319 AND RCPT_MTR_NO = '873078'
ORDER  BY ACCT_PERIOD, ACTION_CD;   -- expect identical ALLOC_QTY/FUEL_RATE but differing PPA_FUEL_QTY

-- 2. Confirm the PPA event records generated by the TIPS rerun (process queue)
SELECT * FROM QPROC_QUEUE_HIST WHERE PROC_QUEUE_ID IN (23264883, 23464883);

-- 3. Did the TIPS pointer-alloc sync touch these meters on the rerun?
SELECT * FROM ALCTRL_PPA_EVENT WHERE RCPT_MTR_NO = '873078' AND PLANT = 'TMV'
ORDER  BY CREATE_TS DESC;
```

### Next steps
1. **Reopen against the live repro** — this is the data cut Dev needed before. Capture the TMV-plant / TIPS-rerun example in PSTA before it refreshes and have DBAs preserve it.
2. Trace `QPSTIPSPtrAllocSync_PRM.cpp` on rerun: confirm whether it re-emits a PPA fuel event when alloc qty/fuel rate are unchanged (H1).
3. Check `QSQL_PreReportProcessRR.cpp` for recompute-vs-carry-forward of PPA fuel (H2).
4. **Open a NEW ADO bug** (don't reuse closed #1753672) linking it as predecessor; title: `ENT - 26-01063725 - ALR24M shows PPA fuel with no change in fuel rate/alloc qty (restate re-stamps PPA fuel on TIPS rerun)`.
5. Quantify the delta to rule rounding in/out per the customer's earlier theory.

### Code confirmation (2026-06-05) — H1 CONFIRMED, H2 ruled out
**Source:** `ENT.QPTM.ClassicBatch` repo (`3be6f2b9-48fc-4999-b873-a37a0cce97ac`) `/QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync_PRM.cpp` (2077 lines).

**Driving config keys (read in `Execute()` setup, lines 95–145):**
- `PLANT_PTR / ENT_DAILY_VOL_LOGIC_CHANGE_DT` (global, DATE; line 125) — the pivot. Sets `m_dtChangeDt`. Job hard-fails if missing.
- Accounting-month lag (`GetAcctgMthLagTime`, TSP level; lines 105–110) → `m_dtProdMth = acctg month − lag`.
- `TSP / TIPS_PROCESS_CONTROLS_PRM` (line 153) — gate; sync no-ops if off.
- `TSP / REALLOC_APPROVAL_IND` (line 1618) — whether the reallocation row needs approval.
- `PLANT_PTR / SYNC_FUTURE_GAS_DAYS` (line 132) + gas-day offset — day scope.

**Root cause path (override writer ≈ lines 1325–1505):**
- `bIsPPAMonth = dtProdMth < m_dtProdMth` (1335) → any rerun of a month earlier than the process month is treated as a PPA.
- `bNewLogic = ProdMonth >= m_dtChangeDt` (1354). **Pre-change-date months take the legacy branch and write the override into the FUEL column** `crALLOC_FUEL_ENG_QTY_OVRD` (1370); on/after the change date write the newer `ALLOC_PTR_ENG_QTY_OVRD` (1366).
- On rerun, when the recomputed override qty differs from the stored value, or one side is null (1412–1458), `bIsPPA=true` and the row is re-written → **fuel override re-stamped** + warning "The PTR allocation will result in PPA for the production month = …" (1480).
- `DoReAllocation()` (1526) inserts `ALTRAN_REALLOC_SEL` with `PPA_SRC_CD = CDTBLVAL_PPA_SRC_PTR`, `TRIGGER_SRC_CD = PTR` (1655–1665) → the PPA-fuel reallocation the report shows.
- `HandleMissingPTROnDailyNoms()` (≈1888) "Always NULL out fuel override if no corresponding PTR from TIPS" → fuel re-applied when a TIPS PTR exists, nulled when it doesn't → the appearing/disappearing spurious fuel across reruns.
- **Guard that should have prevented it** (1023 / 1138 / 1192): `if (dtProdMth < m_dtProdMth && !mapTIPSPlantProdMonthProcessed.Find(...)) continue;` — skips PPA months unless the plant was actually rerun in TIPS. **Re-running the TMV plant in TIPS satisfies the map, the guard passes, and the override writer fires** = exactly the TMV-after-TIPS-rerun repro.

**H2 ruled out:** `Quorum.QPTM.ClassicBatch /QPDllPipelineMgrRPT/QSQL_PreReportProcessRR.cpp` (3814 lines) only **reads** `ALHIST_ALLOC` / `ALHIST_ALLOC_LATEST_VW` to build the RRR-12 deliveries/storage/linepack report aggregates (no fuel/PPA writes). The recompute is solely in the ENT pointer-alloc sync.

### Walkthrough confirmation (2026-06-10) — DETERMINISTIC REPRO + STX-variant code RCA
**Artifact:** `Case 26-01063725 Before Walkthrough ENTPPA (1).docx` (Sara Riano / Santiago Berrones). 15 numbered steps + 15 screenshots (extracted to `…\Temp\ppa_wt\`). System ENT HD DEVA1. TSP **30051**, open acctg month **2/1/2026**, prior PRD month **1/1/2026**, plant **TMV (Thompsonville)**, company **GTT**.

**The repro isolates the proximate trigger to ONE step.** ALR24M run after the normal QPTM allocation + WGT-to-TIPS (steps 4–7) shows **NO PPA under TMV**. Then: TIPS MeasVol import (8) → TIPS Accounting Date Maint, open Jan for billing (9–10) → **TIPS Facility batch "Revision due to liquid value adjustments"** for PRD 1/1 and 2/1 (11) → **QPTM "PTR Overlay Synchronization" (step 12)** → re-run ALR24M (13) → **PPA Fuel now appears under TMV** (14). Verbatim from the doc: *"the PPA REC QTY and the PPA PtR QTY it is the same, however the PPA Fuel Qty is still generating a value."* PPA Status row count is unchanged (11 under PRD 1/1, steps 3 & 15). **Expected result per doc: "User may successfully get the report with no Fuel PPA added."**

**TMV = South Texas, so the live process is `ALPTRSYNC` = `QPSTIPSPtrAllocSync.cpp` (NON-`_PRM`)** — the standard/STX twin of the Permian `_PRM` file analyzed above. (`_PRM`/`ALPTRSYNCP` is Permian per ADO #1369311; the split is PR #47758.) I read this file (1649 lines, repo `3be6f2b9-…`, `/QPDllPipelineMgrAL_ENT/`). It corroborates H1 and **sharpens it into two compounding defects**:

- **Defect A — ALPTRSYNC force-reallocates with NO value-change gate.** `Execute()` (134) → `ComputeOverrides` (543) → `UpdateOverrides` (835) → **`DoReAllocation` (1072)**. In `AllocateSubTotalsToDailyNom` the override is set **unconditionally** — `SetSchdEngQtyOverride(...)` at **1547** (and `=0` at **1561**) — with no comparison to the currently-booked qty. That setter flips `m_bIsPPA=true` (header line 55), and `IsOverride()` just returns `m_bIsPPA` (header 37). `DoReAllocation` then inserts an `ALTRAN_REALLOC_SEL` row (`TRIGGER_SRC_CD=PTR`, `PPA_SRC_CD=CDTBLVAL_PPA_SRC_PTR`, lines **1196/1199**) and launches a **synchronous `ALALLOCATE` with `REALLOC_IND=true`** (1248–1278) for **every** override nom — gated only on `IsOverride()` (**1158**), never on whether the recomputed PTR actually differs. So an **idempotent** PTR re-sync (TIPS re-sent the same PTR after the liquid-value rerun) still forces a full reallocation of those paths.
- **Defect B — fuel doesn't net to zero on the restate (in ALALLOCATE, not this file).** Note `UpdateOverrides` here writes **only `SCHD_ENG_QTY_OVRD`** (952/991); it *reads* `ALLOC_FUEL_ENG_QTY_OVRD`/`ALLOC_PTR_ENG_QTY_OVRD` solely for the null check (`CheckOvrdQuantitiesAreNull`, 1054) and **never writes fuel/rec/ptr**. So for TMV the spurious fuel is **not** stamped by the override writer (unlike the `_PRM` legacy-fuel-column path at _PRM:1370) — it is produced **downstream when `ALALLOCATE` re-runs**: REC and PtR re-derive identically (net 0), but **Fuel (= alloc × fuel rate, progressively rounded) is recomputed/re-rounded and yields a non-zero delta** → booked as PPA fuel in PRD 1/1 within open acctg 2/1. The PTR Overlay feature explicitly modified ALALLOCATE (ADO **#1617125**), so the recompute lives there. This is why the customer's 2025 "rounding" guess (#1753672) was *close* — fuel is re-rounded on a reallocation that should never have fired.

**Net:** H1 confirmed and split — the *trigger* defect is in `QPSTIPSPtrAllocSync.cpp` (no idempotency gate before reallocating); the *fuel-delta* defect is in `ALALLOCATE`'s fuel recompute not netting to zero on a no-op restate. File last changed Jan-2024 (PR 92582) — defect is latent, no fix in flight. This is the same family as case **26-01081678** (QPTM reallocation paths lacking value-change guards → spurious PPA churn).

**Recommended fix (rank):**
1. **(Primary, lowest-risk) Add an idempotency gate in `QPSTIPSPtrAllocSync`** — before flipping `m_bIsPPA`/inserting the realloc row, compare the recomputed override to the currently-booked alloc within `msc_dCOLUMN_PRECISION_10`; skip when equal. Stops *all* spurious PPA (not just fuel) and mirrors the 26-01081678 "use a value-change guard" recommendation.
2. **(Secondary) Make `ALALLOCATE` carry-forward fuel** when REC and PTR net to zero on a restate, instead of recompute-and-re-round. Higher blast radius (core engine) — only if (1) is insufficient.

**ADO action:** clone/reopen **#1753672** (closed "not reproducible" 2025-10) attaching this deterministic walkthrough + screenshots as the data cut Dev was missing. Suggested title: `ENT - 26-01063725 - PTR Overlay Sync (ALPTRSYNC) force-reallocates with no idempotency gate → ALALLOCATE re-rounds non-netting PPA fuel (TMV, no change in rate/alloc qty)`.

**Repro runbook for Aditya (PSTA or a refreshed ENT test env):** TSP 30051, set open acctg = a month whose prior PRD month is closed-then-reopened; (1) run QPTM Allocation (Reallocate+Unallocate) + WGT-to-TIPS, confirm ALR24M shows no TMV PPA; (2) in TIPS run Facility job **"Revision due to liquid value adjustments"** for the TMV plant (PRD = prior month and current); (3) run **QPTM PTR Overlay Synchronization**; (4) re-run ALR24M → PPA Fuel appears under TMV with REC=PtR delta 0, Fuel≠0. Capture `ALTRAN_REALLOC_SEL` rows with `TRIGGER_SRC_CD=PTR` created by step 3 and the `ALALLOCATE` PQID, and preserve before the env refreshes.

---

## Case 26-01103004 — MW flex credit didn't roll up to parent contract K241

| Field | Value |
|-------|-------|
| Case | 26-01103004 (SF Id 500UH00000pJhwkYAC) |
| Client | MountainWest Pipeline (MW = ex-Questar = **QTR** codebase) — contact Dave Reeder, submitter Laura |
| Subject | Flex Credit issue on K#241 |
| Status / Priority | In Progress / **High** · Owner Abhijit Pradhan · opened 2026-05-26 |
| Related | 26-01070658 "MW Capacity Release Flex Credits" (different problem — GL account breakout of parent credits to a separate Oracle acct; same domain) |

### Issue
On a capacity release, child (replacement) contract **K8038** had flex activity but **no flex credit rolled up to the parent (releasing) contract K241**. K241 had **5 capacity releases** in April. Customer has seen *partial* credits before but never a *complete absence* — wants to know why the code didn't roll the credit up. (Excel reconciliation + HTML "Case Analysis" + screenshot + Word doc attached; binary, not readable via SF connector.)

### Classification
**Code Defect (probable)** in the releasing-shipper flex-credit roll-up, possibly **Data** (missing/mismatched staging keys). Confirm with the diagnostics below.

### Code path — `QTR.QPTM.ClassicBatch /QPDllPipelineMgrBL_QTR/QPSReleasingShipperFlexing.cpp` (648 lines)
Process `BLRELFLEX`; `Execute()` = `PopulateFlexItem()` → `DetermineReplFlexRate()` → `CreateInvoiceRates()`. The credit is computed in `DetermineReplFlexRate` only if a `QFlexItem` was added in `PopulateFlexItem`. A **complete absence** means **no flex item was created** for K8038. `PopulateFlexItem` (257-512) creates a flex item only when ALL of these line up:
1. `GetBLCapRel` row (`BLSTAG_INVOICE_CAP_REL`: `REL_CTR_NO`=K241, `REPL_CTR_NO`=K8038, `LOC_ID_1/2`, `ROUTE_CD`, `ACTIVITY_DT`).
2. `GetInvoiceInputRate(sRelCtrNo, locId1, locId2, route, activityDt)` returns input rates for the **releasing** contract (else outer `continue`, ~497).
3. Charge row: `CHARGE_BASIS_CD` in (MDQD,MDQR) & `TOC_CD` not empty (366).
4. `GetInvoiceSupp(sReplCtrNo, activityDt)` supp row whose displaced loc == `LOC_ID_1` **and** `LOC_ID_2` **and** `NET_RATE != 0` (382-385) → else `vRateCharge` stays null → `continue`.
5. **Credit loop: `CR_CHARGE_TYPE_CD == 'REL_CREDIT'` AND `sInputRateReplCtrNo == sReplCtrNo` (427)** — the REL_CREDIT input-rate row must carry `REPL_CTR_NO` = K8038.
6. MAXT TOC resolvable: `FindTypeOfChargeThatApply` + `BuildRateDetailByRateType` for the releasing ctr at that loc/route/TOC/amend/date (429-444) → only then `m_FlexItemArray.Add(pFlexItem)`.

### Root-cause hypotheses (ranked)
- **H1 (primary): REL_CREDIT input-rate row's `REPL_CTR_NO` ≠ K8038** (line 427). With 5 releases under one parent, the credit row may carry a blank/other child → equality fails → credit never built. Cleanly explains "partial before, complete absence now" (depends how many children's credit rows carry the matching REPL_CTR_NO).
- **H2: supp/displaced-location mismatch or `NET_RATE = 0`** (382-385) → charge side never captures `vRateCharge` for K8038's flex point → credit loop never reached.
- **H3: no input rate staged for the releasing contract** at the flex loc/route (step 2) → outer `continue`.
- **H4: MAXT demand-tariff rate not buildable** for K241 at that loc/route/TOC/amend (step 6).

### Diagnostic SQL (MW TSP_NO, April acctg mth; verify exact column names vs schema)
```sql
-- A) the 5 cap-rel staging rows for K241 (expect one with REPL_CTR_NO='K8038')
SELECT REL_CTR_NO, REPL_CTR_NO, LOC_ID_1, LOC_ID_2, ROUTE_CD, ACTIVITY_DT
FROM   BLSTAG_INVOICE_CAP_REL
WHERE  REL_CTR_NO='K241' AND ACTIVITY_DT BETWEEN '2026-04-01' AND '2026-04-30';

-- B) H1: REL_CREDIT input-rate rows for the releasing ctr — does REPL_CTR_NO match K8038?
SELECT INVOICE_INPUT_ID, CR_CHARGE_TYPE_CD, CHARGE_BASIS_CD, TOC_CD, REPL_CTR_NO,
       RATE, AMEND_NO, ACCTG_MTH, LOC_ID_1, LOC_ID_2, ROUTE_CD
FROM   BLTRAN_INVOICE_INPUT_RATE
WHERE  CTR_NO='K241' AND CR_CHARGE_TYPE_CD='REL_CREDIT'
  AND  ACTIVITY_DT BETWEEN '2026-04-01' AND '2026-04-30';

-- C) H2: supp rows for the replacement ctr — NET_RATE and displaced location
SELECT DISPLACED_CTR_LOC_ID, NET_RATE, SUPP_RATE, SUPP_DISC_RATE, DISPLACED_RATE, SUPP_ENG_QTY, SUPP_DISC_IND
FROM   BLTRAN_INVOICE_SUPP
WHERE  CTR_NO='K8038' AND ACTIVITY_DT BETWEEN '2026-04-01' AND '2026-04-30';
```

### Next steps
1. Run A/B/C against MW (prod data as of 2026-05-18 per customer). B confirms/eliminates H1; C confirms/eliminates H2.
2. If H1: fix the credit↔child association so each release's REL_CREDIT matches its `REPL_CTR_NO` under a multi-release parent (or relax the equality where the credit legitimately rolls to the parent across releases).
3. No prior ADO bug found (WIQL "flex credit"/"releasing shipper" = none relevant; WI 1770922 = HEP MDQ, unrelated). Open a new ADO bug once a hypothesis is confirmed.
4. DUT.QPTM.ClassicBatch has the identical file — fix applies to both client variants.

---
---

## Case 26-01081678 — ENT/MVP Measurement Interface re-triggers TR_ALCTRL_MEAS_VOL_D reallocations every run

| Field | Value |
|-------|-------|
| Case | 26-01081678 (SF Id 500UH00000jSIoAYAW) |
| Client | EQT Corporation (Equitrans / **ENT**) — contact via project team |
| Subject | QPTM: Measurement Interface Issue |
| Status / Priority | **Development In Progress** / High · Origin Web |
| Opened | 2026-02-19 (~109d) |
| Scope | **TSP 24** (Equitrans, mixed meter types — best repro), **TSP 8925** (MVP, bi-directional parent locations), **PNG NOFT** contract |
| Linked ADO | **None** — full-text WI search for `26-01081678` = 0 hits. SF status is "Dev In Progress" but no ADO item is linked by case number. **Open one.** |

### Issue (verbatim recap from case)
After each measurement interface run (noon & 6PM), reallocation records **regenerate on the "Reallocations to Process" tab even after PANightly clears them**, each batch **re-timestamped** to the run time (customer saw 9/2 → 11:26PM batch, cleared, then 17:24PM batch, etc.). Customer correctly names the trigger: **`TR_ALCTRL_MEAS_VOL_D`**. Fires **for parent locations but not non-parent** locations. Causes **incorrect reductions to customers' imbalances** and **imbalance PPAs** (PNG NOFT contract too). Open since Sept 2025.

### Classification
**Code Defect (by design interaction)** — the interface's routine parent-row refresh spuriously satisfies an AFTER-DELETE reallocation trigger. **A config lever exists** (`ALLOW_MASS_DELETE_IND`) as a candidate workaround.

### Root cause — confirmed at code level
> **2026-06-08 CORRECTION:** an earlier note here said "only an AFTER DELETE trigger exists / no `_I` or `_U`." That was wrong (bad fetch → TF401174). **All three triggers exist** (`_D`, `_I`, `_U`), all insert into `ALTRAN_REALLOC_SEL`. The real defect is that the parent refresh uses DELETE+INSERT, which routes through the two triggers that have **no change-detection**, bypassing the one (`_U`) that does.

The loop: **interface DELETE+INSERTs the parent row every run → `_D` (on delete) and `_I` (on insert) each log a reallocation with no value-change check → PANightly makes a PPA and clears the realloc → next run delete+inserts again → dedup passes → fresh re-timestamped realloc.** Repeats every cycle.

1. **Interface refreshes PARENT rows by DELETE-then-INSERT (not UPDATE), unconditionally.** `Quorum.QPTM.Batch /…/DailyMeasImport/QPTMMeterVolumeSubscriber.cs` parent path (Issue 45823): `if(volumes.Count==0) return; … DeleteParentMeasRowsSQL(volumes); ExecuteNonQuery(sql); … IntializeParentDataRow(dsParent, volumes); Update(dsParent);`. No "did the aggregated volume change?" check — the parent row is dropped and re-inserted on every run with child data, even when the rolled-up value is identical. (Child meters use "update only if different" — Issue 45867 — so they route through `_U` instead; see "Why parent only".)
2. **THREE triggers on `ALCTRL_MEAS_VOL`, all → `ALTRAN_REALLOC_SEL` (`PROC_CD='IMT'`, `PPA_SRC_CD='LOC'`):**
   - `TR_ALCTRL_MEAS_VOL_U` (AFTER UPDATE): **change-aware** — only logs a realloc when `UPDATE(VOL_QTY) OR UPDATE(ENG_QTY)` **and** `COALESCE(INS.VOL_QTY,0)!=COALESCE(DEL.VOL_QTY,0) OR …ENG_QTY…`. No gate needed; it self-suppresses no-ops.
   - `TR_ALCTRL_MEAS_VOL_D` (AFTER DELETE): **no value check.** Gates: `ALTRAN_ALLOC_STAT` (alloc run), `GAS_DAY ≥ BILLING_PPA_CUTOFF_DT`, `ACCTG_MTH ≥ MIN OPEN BILL mth`, dedup `REALLOC.LOC_ID IS NULL`, `VOL_SRC_CD!='MAN'`, **and mass-delete suppression** `(ALLOW_DEL.TSP_NO IS NULL OR ALLOW_MASS_DELETE_IND=0)`.
   - `TR_ALCTRL_MEAS_VOL_I` (AFTER INSERT): **no value check, NO open-month gate, NO mass-delete gate.** Gates only: `ALTRAN_ALLOC_STAT`, `GAS_DAY ≥ BILLING_PPA_CUTOFF_DT`, dedup, `VOL_SRC_CD!='MAN'`. **Mislabels its rows `TRIGGER_SRC_DTL='TR_ALCTRL_MEAS_VOL_D'`** (copy-paste) — so `_I`-sourced rows are indistinguishable from `_D` in the data.
3. **Both `_D` and `_I` carry the row's `PROD_MTH` (production month) AND `ACCTG_MTH`.** `_D`'s open-month gate forces `ACCTG_MTH ≥` the open BILL month. So the realloc row = prior `PROD_MTH` + current/open `ACCTG_MTH` = the PPA signature.
4. **Realloc → PPA:** PANightly's `QPDllPipelineMgrAL/QSQL_Selection.cpp` joins `ALTRAN_REALLOC_SEL ARS` (L1498-1502, `ARS.ACCTG_MTH <= @0ACCTG_MTH`), selects the gas day for reallocation when an ARS row exists (L1511, *"Previous and/or Prior Period gas days … triggered for reallocations"*), and flags **`PPA_IND = CASE WHEN SUB.GAS_DAY < @0LAG_PROD_MTH THEN 1 ELSE 0`** (L1451). A prior-production-month gas day → `PPA_IND=1` → QPSAlloc books a PPA for that location in the open accounting month.

### Solution
**Primary (code fix) — route the parent refresh through in-place UPDATE instead of DELETE+INSERT** in `QPTMMeterVolumeSubscriber.cs` (Issue 45823 parent path). UPDATE the existing parent aggregate row (`SET VOL_QTY/ENG_QTY = new rollup WHERE LOC_ID/TSP_NO/GAS_DAY`), INSERT only genuinely-new rows, DELETE only rows that should disappear. Then **`TR_ALCTRL_MEAS_VOL_U`'s existing change-guard** (`INS.VOL_QTY != DEL.VOL_QTY OR …ENG_QTY…`) suppresses no-op refreshes automatically while still logging a reallocation when the volume truly changes. Smallest change; mirrors the child path (Issue 45867); leverages a trigger that is already correct.

**⚠️ The config lever `ALLOW_MASS_DELETE_IND = 1` does NOT fix this** (corrected 2026-06-08). It gates **only `_D`**. On the same refresh the re-INSERT fires **`_I`, which has no mass-delete gate and no value check**, so the reallocation is still created — and `_I` mislabels it `TRIGGER_SRC_DTL='TR_ALCTRL_MEAS_VOL_D'`, so it looks identical. If anyone already tried this config and saw no change, this is why. (To make the config approach work you'd also have to add the mass-delete + value guards to `_I`, which is more code than just fixing the interface.)

**Do NOT** broaden the triggers' `VOL_SRC_CD != 'MAN'` exclusion to also skip PGS/MPS — that would kill legitimate interface-driven reallocations globally.

### Why parent locations only (answers the customer's open question)
It's not that the triggers behave differently by location — it's that the interface **touches the two location types with different DML**:
- **Child/detail meters** → interface **UPDATEs in place** ("update only if different", Issue 45867) → fires `TR_ALCTRL_MEAS_VOL_U` → its value-change guard suppresses no-ops → **no churn.**
- **Parent aggregate locations** (`PRNT_AGGR_LOC_ID`) → interface **DELETE+re-INSERTs** → fires `_D`/`_I`, which have **no value-change guard** → reallocation every run.

So the asymmetry is a consequence of the parent path using the destructive refresh that escapes the only change-aware trigger.

### Related history
| Item | State | Why it matters |
|------|-------|----------------|
| ADO **#1797289** "ENT — Daily Allocation Maintenance (Web) Reallocations not Respecting TSP Config" | Closed/**Rejected** 2026-06-02 | **Same defect family** — Web spuriously inserts `ALTRAN_REALLOC_SEL` "for every gas day that has a modified allocation row… even for open accounting months" (Grayson Lee 2026-04-21). Different entry path (DAM override screen). Rejected because ENT stopped seeing it *on that screen* — does **not** cover the measurement-interface path. |
| ADO **#1773031** "ENT — Reallocation Trigger Events for all gflow Screens" | Closed/Verified | ENT Defect 110 — opposite direction (wanted realloc to trigger on *more* web screens to match Classic). |
| ADO **#1761005** "ONI — Reallocation … not triggering after Measurement Entry update" | Closed | Adjacent (realloc not firing). |
| ADO **#1711133** "ONM — Reallocation Mode doesn't update derived meter volumes" | Proposed | Adjacent. |

### Diagnostic SQL (TSP 24 / 8925)
```sql
-- 1. The regenerated reallocations + their trigger source & timestamp (run after an interface, then after PANightly)
SELECT LOC_ID, GAS_DAY, TSP_NO, ACCTG_MTH, PROC_CD, PPA_SRC_CD,
       APPROVAL_IND, TRIGGER_SRC_CD, TRIGGER_SRC_DTL, USER_ID, UPDT_DT
FROM   ALTRAN_REALLOC_SEL
WHERE  TSP_NO IN (24, 8925) AND TRIGGER_SRC_DTL = 'TR_ALCTRL_MEAS_VOL_D'
ORDER  BY UPDT_DT DESC;

-- 2. Confirm every regenerated LOC_ID is a PARENT aggregate location (PRNT_AGGR_LOC_ID = self)
SELECT DISTINCT s.LOC_ID, mv.PRNT_AGGR_LOC_ID,
       CASE WHEN s.LOC_ID = mv.PRNT_AGGR_LOC_ID THEN 'PARENT' ELSE 'CHILD' END AS LOC_ROLE
FROM   ALTRAN_REALLOC_SEL s
JOIN   ALCTRL_MEAS_VOL mv ON mv.LOC_ID = s.LOC_ID AND mv.TSP_NO = s.TSP_NO
WHERE  s.TSP_NO = 24 AND s.TRIGGER_SRC_DTL = 'TR_ALCTRL_MEAS_VOL_D';

-- 3. State of the (ineffective) mass-delete flag — only gates _D, NOT _I, so it cannot stop the loop
SELECT TSP_NO, ALLOW_MASS_DELETE_IND FROM ALCTRL_REALLOC_MASS_DELETE WHERE TSP_NO IN (24, 8925);

-- 3b. Confirm all three triggers exist and are ENABLED (the loop requires _D and _I to be active)
SELECT name, is_disabled FROM sys.triggers WHERE parent_id = OBJECT_ID('ALCTRL_MEAS_VOL');
-- Expect: TR_ALCTRL_MEAS_VOL_D, _I, _U all present; is_disabled = 0

-- 4. Why open months get hit
SELECT TSP_NO, MIN(ACCTG_MTH) OPEN_ACCTG_MTH FROM QCTRL_ACCTG_MTH
WHERE  ACCTG_ROLL_TYPE_CD='BILL' AND OPEN_IND=1 AND TSP_NO IN (24,8925) GROUP BY TSP_NO;

-- 5. Billing PPA cutoff
SELECT TSP_NO, BILLING_PPA_CUTOFF_DT FROM PACTRL_TSP_PREF WHERE TSP_NO IN (24,8925);
```

### Next steps
1. **Empirically confirm the loop:** run Query 1 right after a measurement interface run, then again after PANightly — rows reappear with a fresh `UPDT_DT` each cycle (matches the 11:26PM → 17:24PM re-timestamping). Query 2 should show **all** regenerated LOC_IDs are parents. Note Query 1's `TRIGGER_SRC_DTL = 'TR_ALCTRL_MEAS_VOL_D'` filter catches rows from **both** `_D` and `_I` — `TR_ALCTRL_MEAS_VOL_I` hard-codes the `_D` literal (copy-paste bug, line 41 of the insert), so the INSERT-side rows are mislabeled as delete-side.
2. **⚠️ `ALLOW_MASS_DELETE_IND = 1` will NOT stop this loop — do not offer it as a workaround.** That flag is only referenced by `TR_ALCTRL_MEAS_VOL_D` (its `LEFT JOIN ALCTRL_REALLOC_MASS_DELETE ... AND (ALLOW_DEL.ALLOW_MASS_DELETE_IND = 0)` gate). The parent refresh is a **DELETE + re-INSERT**, so even with the flag set the DELETE side is suppressed but `TR_ALCTRL_MEAS_VOL_I` **still fires on the re-insert** — and `_I` has **no mass-delete gate and no open-month gate**. Net effect: the reallocation is still written every run (just stamped via the insert path, mislabeled `_D`). There is **no effective config-only lever**; this needs a code/interface change.
3. **Proper fix options for Dev** (preference order): **(a) PRIMARY — have the interface `UPDATE` the parent aggregate row in place instead of delete-and-reinsert.** This routes the refresh through `TR_ALCTRL_MEAS_VOL_U`, whose existing change guard (`IF (UPDATE(VOL_QTY) OR UPDATE(ENG_QTY))` + `WHERE COALESCE(INS.VOL_QTY,0) != COALESCE(DEL.VOL_QTY,0) OR COALESCE(INS.ENG_QTY,0) != COALESCE(DEL.ENG_QTY,0)`) **already suppresses no-op refreshes** — this is exactly how child locations avoid the loop today. (b) If the delete-and-reinsert pattern must stay, add an equivalent change-detection guard to `_I`/`_D`; **caveat** — in a delete+reinsert neither statement can see both the old and new value (`_D` sees only `DELETED`, `_I` sees only `INSERTED`), so a simple "skip unchanged" guard is not straightforward on this path, which is why (a) is preferred. (c) Exclude interface-sourced refreshes (`VOL_SRC_CD` from the `QPTMMeterVolumeSubscriber` import) from generating reallocations for OPEN months.
4. **Open a NEW ADO bug** (none linked). Suggested title: `ENT - 26-01081678 - Measurement Interface delete-and-reinsert of parent ALCTRL_MEAS_VOL rows re-fires TR_ALCTRL_MEAS_VOL_D/_I every run → repeated open-month reallocations / imbalance PPAs (parent locations only)`. Call out in the body that `ALLOW_MASS_DELETE_IND` does **not** mitigate (the `_I` path has no gate) and that `_I` mislabels its rows as `_D`. Link **#1797289** as related (same `ALTRAN_REALLOC_SEL` spurious-insert family, different path).
5. Note for the customer-facing update: confirmed root cause + parent-only explanation; fix requires a Dev/interface change (route the parent refresh through an in-place UPDATE), not yet released; be honest that there is **no effective config-only workaround** in the interim (the `ALLOW_MASS_DELETE_IND` flag does not stop it).

---

# Case 26-01103733 — WWM (Whitewater): Web Contract Maintenance blocks ALL updates when Total Receipt MDQ ≠ Total Delivery MDQ

**Date investigated:** 2026-06-09 · **Account:** WWM Operating, LLC · **Category:** Contracts · **Priority:** High · **Status:** In Review

> **Update 2026-06-10 (live SF re-check):** Case re-activated today — Aditya flipped Status **In Review → In Progress** at 12:27 UTC; CaseHistory shows **no new customer reply, comments, or attachments** since the original 2026-05-28 submission (EmailMessage/CaseComment unreadable via connector, but the history audit confirms no external touch). **RCA below unchanged.** Fix version now **pinned** (see #1764767 detail): Web fix shipped in **`2024.04.1.42`** (2024.04 line) and **`2026.04.1.0`** (2026.04 line). An ADO title search for `RFSME020` / `VALIDATE_MDQ_REC_DEL` / `Rec MDQ` returns **only #1764767** — no separate or newer WWM defect.

## Issue
Whitewater runs contracts where Total Receipt MDQ ≠ Total Delivery MDQ (by design). In the **Web** Contract Maintenance screen, any save on such a contract is blocked with error **K_RFSME020** ("Rec MDQ does not equal Del MDQ"). The same edit succeeds in **Classic**. WWM calls this a critical blocker to moving off Classic.

**Client-confirmed specifics (2026-06-10):** Env = **PRD**; Pipeline = **Whistler**, **TSP 601**; BA = **Targa**; Contract = **B-420-FT3004** (eff. 10/1/2026); error **K_RFSME020**. Client's explicit ask: *"Is there a code table or means to update this functionality to allow create/update of contracts without Total Receipt and Total Delivery MDQ being equal?"* → **Yes: the `VALIDATE_MDQ_REC_DEL` config (group `CONTRACTS`, Boolean, default `1`=enforce). Set `0` for TSP 601.** Per-TSP override, so global stays `1`. (Confirmed in code: `QPTMTspOrGlobalConfigs.cs ValidateMDQRECDEL(tspNo)` → `TspOrGlobalConfigSettingDefaultHelper(tspNo,"CONTRACTS","VALIDATE_MDQ_REC_DEL","1")`.)

> **⛔ BUILD GATE RESOLVED — PRD is on `2021.04` (client-confirmed 2026-06-10): config alone will NOT unblock Web.** Verified #1764767's delivery branches directly: the only completed cherry-picks are **PR #122604 → `hotfix/17.30.37`** (titled "[2024.04]" → released **`2024.04.1.42`**) and **PR #119945 → `develop`** (→ **`2026.04.1.0`**). **There is NO 2021.04 backport** — the earliest build where the Web Contract Maintenance / Capacity Release screens honor `VALIDATE_MDQ_REC_DEL` is two major lines above the client's PRD. So on `2021.04`, **Web ignores the flag and will keep throwing K_RFSME020 even after setting it to `0`** (that IS the #1764767 symptom). **Determined path:** (1) upgrade PRD to ≥ `2024.04.1.42` (2024.04 line) or ≥ `2026.04.1.0` (2026.04 line); **then** (2) set `VALIDATE_MDQ_REC_DEL = 0` for TSP 601. **Interim:** **Classic** honors the flag on every build, so WWM's existing unbalanced-contract create/update workflow in Classic is unaffected — this is the no-upgrade workaround until they move to Web. This reclassifies the case for WWM from "quick config fix" to **"version upgrade required, then config."**

> **🔧 CORRECTION (2026-06-10, later) — PRD/dev re-reported as `2024.04`, not `2021.04`; the question collapses to PATCH level.** Consultant now reports **`WWM_HD_DEVA1` and `hd_prd` are both on the 2024.04 line** — this **supersedes the `2021.04` framing** in the BUILD GATE note directly above (reconcile which is right via Help → About / the deployment-dashboard build column; the two readings give opposite answers). **On 2024.04 the gate is no longer the major line — it's the patch.** The Web fix (#1764767) landed at exactly **`2024.04.1.42`** (PR #122604 → `hotfix/17.30.37`, completed **2026-01-23**). Two outcomes:
> - **If DEVA1 / `hd_prd` ≥ `2024.04.1.42`** → **config works, NO upgrade needed.** The K_RFSME020 they hit today is just the default `VALIDATE_MDQ_REC_DEL = 1` enforcing equality; set it to `0` for **TSP 601**, refresh MT + pipeline caches, and the Web save on **B-420-FT3004** succeeds. **Pure config fix.**
> - **If DEVA1 / `hd_prd` < `.42`** → Web still ignores the flag (the #1764767 symptom verbatim); land a ≥ `.42` build first — the **April 2026 / Hotfix 7** line (**#1785465** / SF **26-01083603**, which post-dates the 2026-01-23 merge) — **then** set the flag. WWM's last *delivered* 2024.04 hotfix was **July 2025** (25-01027686, pre-`.42`), so an env can be "on 2024.04" yet still below `.42`.
> **Fastest way to settle it empirically:** in **DEVA1**, set `VALIDATE_MDQ_REC_DEL = 0` for TSP 601 and attempt the Web Contract Maintenance save on **B-420-FT3004**. **Success ⇒ DEVA1 ≥ `.42` ⇒ PRD works too** (if on the same/newer patch). **Still K_RFSME020 ⇒ DEVA1 < `.42` ⇒ hotfix first.** Either way, capture the exact patch digits for **both** DEVA1 and `hd_prd` — that single number decides config-only vs. upgrade-then-config. **NB:** the `## Resolution path` and `## Customer update` sections below still read `2021.04` — refresh them once the patch is confirmed.

> **🔑 Upgrade vehicle already in flight — do NOT ask the client about it (SF, 2026-06-10):** WWM is **mid-adoption of the 2024.04 line**, not a cold upgrade ask. SF for this account (`0015f00000S2jy2AAB`) shows recurring 2024.04 support hotfixes — **25-01027686** "QPTM: July 2025 Support Hotfix to 2024.04" (Closed) and **26-01083603** "QPTM: April 2026 Support Hotfix to 2024.04" = **`Complete - Pending Delivery`** (owner **Sara Riano**, desc: *"…coordinate UAT and PRD deployments"*) — plus heavy active-UAT cases. So PRD `2021.04` is almost certainly **pre-cutover** (UAT already on 2024.04). **The in-flight 2024.04 PRD cutover IS the resolution vehicle for this case**, because the Web fix (#1764767) ships on the 2024.04 line as of **`2024.04.1.42`** (Jan 2026) — content a hotfix packaged ~Apr 2026 carries forward. **Verify internally (Sara Riano / account-delivery — NOT the client):** (1) PRD→2024.04 cutover date; (2) the build PRD lands on is ≥ `2024.04.1.42`. Then per-TSP `VALIDATE_MDQ_REC_DEL=0` completes it. **Reconcile the version note:** confirm the client tested K_RFSME020 in PRD (2021.04 → expected, pre-fix); if they actually hit it in a 2024.04 UAT, that's a *different* problem (build < .42, or residual) and would need escalation.

> **🧪 Test bed identified — `WWM_HD_DEVA1` on 2024.04 (consultant, 2026-06-10):** WWM's dev env **`WWM_HD_DEVA1`** is on the **2024.04 line** (PRD still 2021.04 → confirms dev is ahead of PRD, as expected). ⚠️ **Line ≠ patch — do not assume the fix is there.** The Web fix (#1764767) is in **`2024.04.1.42`** (completed 2026-01-23). The most recently *delivered* 2024.04 hotfix to WWM is the **July 2025** one (25-01027686, Closed) → **pre-`.42`, does NOT contain the Web fix**; the **April 2026** hotfix (26-01083603, *Complete - Pending Delivery*) is the likely vehicle for ≥ `.42`. **So `DEVA1` may be on 2024.04 yet still pre-`.42` and would still throw K_RFSME020 in Web even with the flag off.** **Action:** read `DEVA1`'s exact patch (Help → About / version banner, or ask Sara Riano). **If ≥ `2024.04.1.42`** → set `VALIDATE_MDQ_REC_DEL=0` for TSP 601 in `DEVA1` and retest the Web Contract Maintenance save on **B-420-FT3004** (expect success — this proves the full fix end-to-end and de-risks the PRD cutover). **If < `.42`** → land the April 2026 hotfix on `DEVA1` first, then test. This is the cleanest way to give WWM a working demo before PRD moves.

> **📦 ADO upgrade scan (2026-06-10) — WWM is mid-flight `2024.04 → 2026.04`; THAT is the resolution vehicle (better than a 2024.04 patch).** Active ADO items found: **#1790409** "WWM - Build Upgrade to **2026.04 GA** - QPTM" = **Delivered to Customer** (owner Kyle Johnson; target was 2026-05-08); **#1809328** "[Whitewater Midstream] Upgrade Midstream from 2024.04 → 2026.04 **ASAP**" = Closed (Cloud Ops, Vinayak Gite); **#1780061** "Provision New Environment for **`WWM_HD_PRDA1`** … Midstream EDI **2026.04** v17" = **Grooming** (owner **Sangram Dhaybar**, myQuorum Cloud) → the **upcoming 2026.04 production env, not yet live**. UAT **`WWM_HD_UATA1`** is already on **2026.04** with **Patch 1 (#1809220)** and **Patch 2 (#1811047, *Packaged for Delivery* 6/10)** + 2026.04 Hotfix #1 (#1807443) / #2 (#1813122). The **2024.04 line is being wound down** — Patch 8 (#1737768) & Patch 9 (#1791810) on 2024.04 are **Abandoned**; April-2026 2024.04 Hotfix 7 (#1785465 = SF 26-01083603) was the last. **Impact on THIS case:** the Web fix (#1764767) ships in **`2026.04.1.0`**, so WWM's in-flight 2026.04 upgrade **inherently carries it** — once `WWM_HD_PRDA1` goes live the Web screen honors `VALIDATE_MDQ_REC_DEL` with **no extra patch**. **Revised test bed: `WWM_HD_UATA1` (2026.04) — not `DEVA1` (2024.04)** — is the right place to prove it now: set `VALIDATE_MDQ_REC_DEL=0` for TSP 601 in UATA1, retest the Web save on **B-420-FT3004** (expect success). **PRD go-live date is the open item** — #1780061 still in Grooming and there's active churn (Patch 2 rolled back 6/8 #1819237, redeployed 6/9 #1820051), so the schedule is fluid; get the date from **Sangram Dhaybar / Vinayak Gite / Sara Riano**.

## Classification: **Configuration + Known Defect (already fixed in product)** — NOT a new defect, NOT pure expected behavior.

The Rec=Del MDQ check is gated by config key **`VALIDATE_MDQ_REC_DEL`** (global + per-TSP override). `1` = enforce equality; `0` = allow unequal Rec/Del. Precedent: case **25-01026204** resolved exactly this by setting `VALIDATE_MDQ_REC_DEL = 0` for the customer's TSP (Midship), leaving `1` global/elsewhere (`Configuration Changed`).

**The Web wrinkle (the real reason WWM is stuck):** ADO Bug **#1764767** (HEP, case 25-01042893, **Closed 2025-12-18**) — *"Web does not let user update even though VALIDATE_MDQ_REC_DEL is turned off."* With the flag at `0`, Classic honored it but **Web still threw K_RFSME020**. Fixed in the validation `ContractMaintenance0008` (Quorum.QPTM.Web, PRs #119945/#119978/#122604). **Fix shipped in versions `2024.04.1.42` and `2026.04.1.0`** (Found-in version 2024.04). Official release note — *"Contract Maintenance Honors Override Contract MDQ Validation Configuration in Web"*: "Contract Maintenance in the web application honors the VALIDATE_MDQ_REC_DEL configuration when updating Override Contract MDQ values. When the validation is disabled, users can update the Override Contract MDQ even if total receipt and delivery MDQs are not equal." (Scope: Contract Maintenance, Capacity Release.)

So the outcome for WWM depends entirely on their build:
- **On/after the fix — build ≥ `2024.04.1.42` (2024.04 line) or ≥ `2026.04.1.0` (2026.04 line)** → just set `VALIDATE_MDQ_REC_DEL = 0` for WWM's TSP(s), refresh MT cache + all pipeline caches in Web. Done (config-only).
- **Before the fix (e.g. a 2024.04 patch < .42 lacking the cherry-pick)** → setting the flag won't help in Web (that's the #1764767 symptom verbatim). They need the build with the fix **plus** the config change.

## Resolution path (recommended) — UPDATED 2026-06-10 (later): env re-reported on `2024.04` → now patch-level dependent (see 🔧 CORRECTION above)
DEVA1 and `hd_prd` are on the **2024.04 line** (superseding the earlier `2021.04` reading). The deciding factor is the **patch**: the Web fix is in **`2024.04.1.42`**. Path is **config-only if ≥ `.42`**, else **hotfix-then-config**:
1. **Confirm the patch** on DEVA1 / `hd_prd` (Help → About / deployment dashboard), or test empirically: set `VALIDATE_MDQ_REC_DEL = 0` for TSP 601 in **DEVA1** and try the Web save on **B-420-FT3004**. **Succeeds ⇒ ≥ `.42` ⇒ config-only (skip step 2).** **Still K_RFSME020 ⇒ < `.42` ⇒ do step 2 first.**
2. **Upgrade path to use Web:** move PRD to ≥ **`2024.04.1.42`** (2024.04 line) or ≥ **`2026.04.1.0`** (2026.04 line) — these carry #1764767 (verified via PR #122604→hotfix/17.30.37 and PR #119945→develop).
3. **After upgrade:** set `VALIDATE_MDQ_REC_DEL = 0` for TSP 601 in UAT first, refresh MT cache + all pipeline caches, retest the Web save on an unequal Rec/Del contract, then roll the config to PRD.
4. **Interim / no-upgrade workaround:** continue unbalanced-contract create/update in **Classic** Contract Maintenance — Classic honors the flag on `2021.04`, so WWM's current workflow is unaffected. (This is the lever that lets WWM keep operating while an upgrade is scheduled.)

## Related cases
- **26-01091674** (MLGT, Closed) — same symptom; resolved `Training` / "Workaround Provided" = use Classic. That was a stopgap, not the real fix.
- **25-01026204** (Closed) — the config recipe: `VALIDATE_MDQ_REC_DEL = 0` per-TSP.
- **#1682045** (ADO, WWM) — different MDQ issue (Shared MDQ SRC validation not firing in Web); same client, not this defect.

## Diagnostic SQL (verify the flag for WWM's TSP)
```sql
-- Confirm current value of the gating key globally and per-TSP
SELECT CONFIG_KEY, TSP_NO, CONFIG_VALUE
FROM   SCONFIG_CONFIG_VALUE        -- (config table; confirm name in client schema)
WHERE  CONFIG_KEY = 'VALIDATE_MDQ_REC_DEL'
ORDER  BY TSP_NO;
```
Code: validation `ContractMaintenance0008`; controller `QUIControllerContractMaintenance.cs` (repo Quorum.QPTM.Web, id 41e317c0-844c-4728-98da-529092957738).

## Customer update (paste-ready) — revised 2026-06-10 (later): version numbers REMOVED per consultant (dev ≈ prod, same 2024.04 build → DEVA1 test proves PRD)
Yes — there is a configuration setting that controls the requirement for Total Receipt MDQ to equal Total Delivery MDQ, and it can be set for the Whistler pipeline specifically, so other pipelines keep the standard validation. With it turned off for Whistler, you'll be able to create and update contracts where the total receipt and delivery MDQs differ.

Our plan is to apply this setting for Whistler in a non-production environment first and have you confirm that create and update work as expected, then promote the same change to production. In the meantime, the Classic Contract Maintenance screen already honors this setting, so you can continue creating and updating these unbalanced contracts in Classic without interruption.

*(Internal note: DEVA1 and hd_prd are on the same 2024.04 build, so the DEVA1 validation is a faithful proxy for PRD — if the Web save on B-420-FT3004 succeeds there with `VALIDATE_MDQ_REC_DEL=0`, PRD is guaranteed; if it still throws K_RFSME020 the shared build is < `2024.04.1.42` and BOTH need the ≥`.42` hotfix first. Version numbers kept out of the client text per style.)*

---

# Case 26-01063725 — Enterprise (EPCO/ENT): ALR24M shows PPA fuel Qty with no change in fuel rate or allocated qty

**Date investigated:** 2026-06-09 · **Account:** Enterprise Products Operating LLC · **Contact:** Diane Duong / Lali Joseph · **Category:** Allocations · **Priority:** High · **Status:** In Progress

## Issue
The ALR24M (Monthly PPA allocation) report shows a **PPA fuel quantity** for a receipt meter even though **neither the fuel rate nor the allocated quantity changed**. The variance is a mismatch between the **reversal** and **restate** PPA fuel rows, visible in **`ALHIST_ALLOC_LATEST_VW`**. Originally seen on contract 7570ITSA (Rec 873078 → Del PP050066) for Feb/Apr/May 2025; now recurred and surfaces under the **TMV plant** after a **TIPS rerun**.

## Status of prior work (important)
- First ticket **25-01033013** → closed `Customer Error` / "not reproducible"; ADO Bug **#1753672** opened and **Closed** for the same reason. SKILL_Allocations.md §13 currently lists this symptom as "working as designed (fuel revision flagged as PPA)" — **that classification is now stale and should be revisited.**
- This recurrence (26-01063725) is **reproduced by Quorum**: per the 2026-05-14 email, after the testing/rerun in TIPS the PPA fuel appears under the TMV plant in QPTM. Already escalated to L4.

> **⚠️ Reconciliation note (2026-06-10):** The customer walkthrough docx (analyzed in the `## Case 26-01063725` entry above — see "Walkthrough confirmation (2026-06-10)") gives a **deterministic repro that isolates the proximate trigger to the QPTM "PTR Overlay Synchronization" step (ALPTRSYNC)**, whose `ALTRAN_REALLOC_SEL` rows carry `PROC_CD=MANUAL` / `PPA_SRC_CD=PTR` — **not** the measurement-import path's `PROC_CD='IMT'` / `PPA_SRC_CD='LOC'` described below. So for *this* recurrence the **PTR-Overlay path (entry above) is the confirmed trigger**, and the "supersedes the PTR-overlay hypothesis" claim in this entry is itself superseded. The measurement-import delete+reinsert chain below remains a **valid sibling path** in the same defect family (no value-change gate before reallocating) and may explain the original 2025 7570ITSA scenario, but is not what the walkthrough fired. Both fixes converge on the same recommendation: gate the reallocation on a real value change.

## Classification: **Software Defect — confirmed at code level (2026-06-09 L4 analysis)**
Spurious reallocation generated by a *no-op measurement refresh*. NOT customer error, NOT (primarily) rounding, NOT "working as designed." (For trigger-path attribution on the 2026 recurrence, see the reconciliation note directly above.)

## Root cause (code-confirmed)
Same defect family as the `ALCTRL_MEAS_VOL` reallocation-trigger gap (cf. 26-01081678). Chain for THIS case:

1. **TIPS rerun (TMV plant)** → the ENT TIPS→QPTM warehouse measurement import **`QWhMeasImportSeg`** (`ENT.TIPS.Batch` / `ENT.TIPS.QPDllInterface`) rebuilds the QPTM measured-volume set from the plant allocation (`QptmStagPermWhAllocDO`) and writes it back into QPTM **`ALCTRL_MEAS_VOL`** via the measured-volume DAL `SaveList()`.
2. That write is a **DELETE + re-INSERT**, not an in-place UPDATE: `QWhMeasImportTest.cs` (L480–481) asserts the import emits existing rows in `DataObjectState.Deleted` for the affected prod dates before re-inserting the refreshed set. So even an **identical** re-push removes and recreates the rows. (The imported rows carry a non-`MAN` `VOL_SRC_CD`, so the triggers' only content filter does not skip them.)
3. The DELETE fires **`TR_ALCTRL_MEAS_VOL_D`** and the INSERT fires **`TR_ALCTRL_MEAS_VOL_I`**. **Neither trigger compares old-vs-new volume** — only `TR_ALCTRL_MEAS_VOL_U` has that guard (`COALESCE(INS.VOL_QTY,0) != COALESCE(DEL.VOL_QTY,0) ...`). Both fire unconditionally and insert into **`ALTRAN_REALLOC_SEL`** (`PROC_CD='IMT'`, `PPA_SRC_CD='LOC'`) carrying the **prior `PROD_MTH` + current `ACCTG_MTH`**.
4. **PANightly** consumes `ALTRAN_REALLOC_SEL` (`QSQL_Selection.cpp`): because the reallocated gas day's production month is earlier than the open accounting month — `CASE WHEN SUB.GAS_DAY < @0LAG_PROD_MTH THEN 1 ELSE 0 END AS PPA_IND` (L1451) — it books a **PPA** (a **reversal + restate** pair) for the prior production month in the **current open accounting month**.
5. The reallocation rewrites fuel/retainage for those gas days, so the reversal+restate fuel rows surface in **`ALHIST_ALLOC_LATEST_VW`** and on **ALR24M** — even though fuel rate and allocated qty never changed. This matches the 2025 description verbatim: "PPA for 2/2025 and 4/2025 when run by accounting Months 5/2025 and 6/2025."

**Why 2025 was "not reproducible":** the spurious PPA only appears when the measurement is **refreshed** (a TIPS rerun / re-import). With no rerun the rows aren't delete+reinserted and no PPA is generated — so it looked intermittent and was guessed to be "rounding."

**Possible secondary effect (verify, not the headline):** the customer reported "a few MMBtu" residuals between reversal and restate. If the two legs don't net to exactly zero, that is a separate rounding/precision question in the fuel recompute — but the PRIMARY defect is that a PPA is generated **at all** for an unchanged refresh.

## Diagnostic SQL (run on the reproduced data — `CLNT_ENT_ENGS_PSTA`)
```sql
-- A. UPSTREAM: was a reallocation enqueued for the TMV-plant meter with NO real change?
SELECT TSP_NO, LOC_ID, GAS_DAY, ACCTG_MTH, PROD_MTH, PROC_CD, PPA_SRC_CD,
       TRIGGER_SRC_CD, TRIGGER_SRC_DTL, USER_ID, UPDT_DT
FROM   ALTRAN_REALLOC_SEL
WHERE  LOC_ID = <TMV receipt meter>          -- orig case: 873078
ORDER  BY UPDT_DT DESC;
-- NOTE: TRIGGER_SRC_DTL reads 'TR_ALCTRL_MEAS_VOL_D' even for INSERT-side rows (the _I trigger mislabels them).

-- B. Confirm the three triggers exist & are enabled
SELECT name, is_disabled FROM sys.triggers WHERE parent_id = OBJECT_ID('ALCTRL_MEAS_VOL');

-- C. DOWNSTREAM: reversal vs restate fuel where alloc qty & rate are unchanged
SELECT PLANT_NO, LOC_ID, CTR_NO, ACCTG_MTH, PROD_DT, ALLOC_TYPE,
       ALLOC_QTY, FUEL_QTY, FUEL_RATE, PTR_QTY, UPDT_DT, USER_ID
FROM   ALHIST_ALLOC_LATEST_VW
WHERE  LOC_ID = <meter> AND PROD_DT IN (/* prior prod months */)
ORDER  BY PROD_DT, UPDT_DT;
-- Expect ALLOC_QTY & FUEL_RATE identical across reversal/restate; the PPA fuel exists purely because the row was reallocated.
```

## Recommended next steps
1. **Open a NEW ADO bug** (or reopen #1753672 with the reproduced data cut — it was closed not-repro, which is no longer true). Frame the root cause as the **import-side delete+reinsert** re-firing the non-change-aware `_D`/`_I` triggers — NOT rounding, NOT customer error. Suggested title: `ENT - 26-01063725 - QWhMeasImportSeg delete+reinsert of ALCTRL_MEAS_VOL on TIPS rerun re-fires TR_ALCTRL_MEAS_VOL_D/_I → spurious PPA fuel (no change in rate/alloc qty)`.
2. **Primary fix (cleanest):** make `QWhMeasImportSeg` **skip rows whose VOL/ENG qty is unchanged**, or write them via an **in-place UPDATE** so the change-aware `TR_ALCTRL_MEAS_VOL_U` guard suppresses the no-op (instead of delete+reinsert). Stops the spurious reallocation at the source. Same fix shape recommended for 26-01081678.
3. **Do NOT rely on `ALLOW_MASS_DELETE_IND`** — it only gates `_D`; the re-insert still fires `_I` (no gate). No effective config-only workaround.
4. Confirm the data cut is preserved (customer agreed to capture one on recurrence) and attach it to the bug.
5. Verify the secondary rounding question (reversal vs restate fuel residual) once the spurious-PPA path is fixed.
6. **Correct SKILL_Allocations.md §13** — move this symptom out of "Expected Behavior / working as designed"; confirmed defect.

## Related ADO / cases
- **#1753672** (Closed not-repro — reopen/clone). Same `ALTRAN_REALLOC_SEL` spurious-insert family as **#1797289** and **26-01081678**. (Earlier PTR-overlay leads — #1777938 / 24-00974145 — are **not** the driver here.)

---
### ⚠️ Earlier hypothesis (2026-06-09, now superseded — kept for traceability)
Initial read attributed the variance to a reversal-vs-restate fuel delta from (1) fuel recompute precision/rounding, (2) ENT PTR/fuel-split overlay re-derivation (#1777938 `BLXREF_REALLOC_PPA`), or (3) prod/acctg-month time-slice mismatch. Code analysis shows the real driver is the no-op measurement refresh re-firing the reallocation triggers; rounding (if present) is at most a minor secondary effect.

---

### 🔄 Status refresh — 2026-06-12 (Case 26-01063725)

**Case state:** In Progress / High. Contact: Diane Duong (Enterprise Products Operating LLC). Last modified 2026-06-11 — **internal-only** (no new EmailMessage, CaseComment, or attachment since 2026-06-05; likely a field/owner touch).

**ADO #1753672:** still **Closed / Rejected** (state unchanged since 2025-10-15). The reopen/clone recommended above has **not** happened yet.

**New evidence in hand — customer walkthrough analyzed (2026-06-10/11):** `Case 26-01063725 Before Walkthrough ENTPPA (1).docx` (Sara Riano / Santiago Berrones, env ENT HD DEVA1, TSP 30051) — extracted to `Case_26-01063725_Walkthrough.md` + 14 screenshots. It is a clean end-to-end repro of the trigger chain documented above:

1. **BEFORE:** Allocation Process + Allocation WGT to TIPS (Realloc+Unalloc IND, acct 2/2026) → ALR_24M report clean, no PPA under TMV (queue 25069883).
2. **TRIGGER:** TIPS PTR–MeasVolImportProcess → Accounting Date Maint (open 2/2026 Billing, Jan prod date, rerun) → Facility Batch Job TMV "Revision due to liquid value adjustments" (Measurement Standardization → ARAP, PRD 1/1 + 2/1) → QPTM PTR Overlay Synchronization (queue 25069885, completed w/ warning).
3. **AFTER (queue 25069910):** Plant TMV / Proc K 12514 shows paired RES/REV PPA rows per receipt loc — **PPA Rec and PPA PtR net exactly 0** (50/(50), 650/(650), 154/(154)…) **but PPA Fuel leaves (4)** for Prod Mth 01/01/2026 (per-loc fuel pairs 1/(2), 7/(8), 1/(2)). PPA Status still shows the same 11 unprocessed records — no real PPA was created.

This quantifies the defect signature: a **no-op measurement restate** (unchanged VOL/ENG quantities re-imported via delete+reinsert) re-fires `TR_ALCTRL_MEAS_VOL_D/_I`, seeds `ALTRAN_REALLOC_SEL`, and the forced reallocation re-rounds fuel asymmetrically across the RES/REV pair — visible fuel residual with zero net allocation change. Consistent with (and evidence for) next-steps #1/#2 above.

**Action queue (unchanged, now unblocked by evidence):** open new ADO bug / reopen #1753672 attaching the walkthrough + BEFORE/AFTER report queue IDs (25069883 vs 25069910) as the agreed data cut. Awaiting consultant go-ahead for the ADO write.

---

## Case 26-01095518 — Tallgrass: Shipper released 2× contract MDQ via two pre-arranged offers

**Date investigated:** 2026-06-15 · **Account:** Tallgrass MLP Operations · **Contact:** Sarah Starke · **Product:** QPTM · **Category:** Capacity Release · **Priority:** High · **Status:** In Progress · **Root_Cause__c:** (null)

### Issue
Releasing shipper **Gulfport (BA# 10054)** released **10,000 dth OVER** their contract MDQ on **K#949016** (MDQ = 10,000). Two **non-biddable, pre-arranged** offers were created for the *full* 10,000 MDQ each — **Offer 7201** (3/26/26) and **Offer 7210** (3/27/26) — and **both were awarded on 3/27/26 → 20,000 dth released**. Customer's expectation: a releasing shipper must never be able to offer/release more than the available capacity on the releasing contract; the system should block multiple offers that together exceed the releasing contract MDQ.

### Classification: **Code Defect** — missing cumulative-capacity validation on capacity-release offer/award.
Not config, not data, not expected behavior. (Distinct from the nomination "over-MDQ" items NN00003072 segmentation / NN00009965 AOS — those are nom validations, not capacity release.)

### Root cause (hypothesis, code-grounded — HIGH)
Capacity-release offer validation validates **each offer in isolation** (offer qty ≤ releasing contract MDQ) and has **no aggregate check** that the **sum of outstanding + already-awarded released capacity** on the releasing contract stays ≤ the contract's **available (un-released) MDQ**. Because the offers are **pre-arranged / non-biddable**, they auto-award at the award step, so two offers each = full MDQ both pass individual validation and both award → 2× MDQ released.
- Offer validation rules: `Quorum.QPTM.Validations.Rules.CapacityRelease/Offers/RuleCROF000xxx.cs` (repo Quorum.QPTM.Web `41e317c0-…`), driven by `QCROfferValidationContext` / `QUIControllerCROfferV2.cs`. (The "available capacity" code-search hits RuleCROF001240/001250 are offer **text** validations, not quantity — ruled out.)
- Pre-arranged award → replacement-contract generation: `Quorum.QPTM.ClassicBatch /QPDllPipelineMgrCR/QPSContractGen.cpp` (same file as the S2S→P2P hardcode bug #1607331). The cumulative cap check is missing on either the offer-create side, the award-eval (`CRBIDEVAL`/`CRK_GEN`), or both.

### ADO / history
- **No ADO bug linked** — WIQL `[System.Title] CONTAINS '26-01095518'` = 0 hits. The 8 "available capacity" bugs (#1759474/#1654650/#131931/#278938/#1369698/#1388651/#1550771/#130063) are all **IPWS Operationally Available Capacity** posting-report issues — unrelated. **No documented skill cluster** for "multiple offers exceed releasing MDQ" → appears to be a **net-new defect**. Recommend opening one.

### Attachments (10) — key, unread (binary via connector)
- **"Case 26-01095518 Before Walkthrough"** (Word, 2026-06-12) — recent L4 repro doc; **extract and read first**.
- **"Shipper Released Over Contract MDQ_UAT Config Change Testing"** (Word, 2026-05-28) — implies a **config lever was trialed in UAT**; determine whether a global/TSP config (e.g. validate offer qty against available capacity) mitigates, or whether it confirmed code is required.
- **"Additional UAT Testing_Release Over Path MDQ"** (Excel, 2026-04-23) — also tests release over **Path** MDQ (a related dimension).
- Two **OFFER DOWNLOAD (EXTERNAL)** PDFs (72775386, 72775407) = the two offers; original "Shipper Released Over Contract MDQ" Word; image.png; 3× Case Analysis HTML.

### Next steps
1. **Extract the two walkthrough docs** (Before Walkthrough + UAT Config Change Testing) — they contain the deterministic repro and whether a config mitigation exists. (Offer to do this — same method as the ENT PPA walkthrough.)
2. **Confirm the validation gap in code:** read the CR offer validation rules (RuleCROF000xxx) and the award/CRK_GEN path for any existing "available capacity to release" aggregation; identify whether the missing check belongs at offer-create (block creating an offer whose qty + already-offered/awarded > available) or at award (block awarding beyond remaining capacity). Check the releasing contract's available-capacity source (released vs. recalled vs. remaining).
3. **Diagnostic SQL** (verify the data): list all offers + awards on K#949016 and sum released qty.
4. **Open a new ADO bug** (none exists): `TGL - 26-01095518 - Capacity Release allows total awarded release > releasing contract MDQ via multiple pre-arranged offers (K#949016, 2×10k=20k)`. Link as a sibling of the CR offer/award validation family.
5. **Check the "Path MDQ" angle** (Excel attachment) — the same missing-aggregate-check may also let releases exceed *path* MDQ, not just contract MDQ; scope the fix to cover both.

### Diagnostic SQL (verify; confirm column/table names vs client schema)
```sql
-- All offers on the releasing contract and their awarded/released qty
SELECT o.TSP_NO, o.OFFER_NO, o.REL_CTR_NO, o.REL_BP_NO, o.OFFER_QTY,
       o.PREARR_IND, o.BIDDABLE_IND, o.OFFER_STAT_CD, o.POST_DT
FROM   CRCTRL_OFFER o
WHERE  o.REL_CTR_NO = '949016' AND o.REL_BP_NO = '10054'
ORDER  BY o.POST_DT;

-- Awarded/released capacity vs releasing contract MDQ (expect SUM(released) = 20000 > 10000 MDQ)
SELECT a.REL_CTR_NO, SUM(a.AWARD_QTY) AS TOTAL_RELEASED
FROM   CRCTRL_AWARD a
WHERE  a.REL_CTR_NO = '949016'
GROUP  BY a.REL_CTR_NO;

-- Releasing contract MDQ for comparison
SELECT CTR_NO, CTR_MDQ_DISPLAY_ONLY, OVRD_CTR_MDQ FROM KCTRL_CTR_HDR WHERE CTR_NO = '949016';
```

### RCA & Fix — 2026-06-15 (code-confirmed)

**Enforcement mechanism (confirmed in source):** the offer's MDQ/available-capacity check is a **per-offer batch validation, `CRMDQMSQVL`**. `QPTMCapacityReleaseService.GetAvailableCapacity(offer)` (`Quorum.QPTM.ServiceCore.CapacityRelease/QPTMCapacityReleaseService.cs:1810`, repo Quorum.QPTM.Web, branch develop) saves the offer then calls `bps.LaunchCRMDQMSQVL_CRValidateMDQMSQ(offerNew.TspNo, offerNew.OfferNo, false)` — note it is launched with a **single OfferNo** and adds a "cap avail" error to that one offer's details. So the capacity check evaluates **one offer at a time** against the releasing contract's available capacity. (GUI entry `Quorum.QPTM.ClassicGUI /Native/PipelineMgrCR/QVpCapRelOffer.cpp`; the CRMDQMSQVL batch body lives in `QPDllPipelineMgrCR` — body not read this pass.)

**Root cause (HIGH confidence):** available capacity is computed as *releasing contract MDQ − already-AWARDED/active releases* and is validated **per individual offer**, with **no reservation/aggregation across other outstanding (submitted, pending-award) offers** on the same releasing contract/path/term, and **no re-validation at award** that the *cumulative* award stays ≤ MDQ. Because offers 7201/7210 are **non-biddable pre-arranged** (auto-award): 7201 was submitted 3/26 but not yet awarded; when 7210 was created 3/27, CRMDQMSQVL still saw the full 10,000 available (7201 wasn't awarded yet) → 7210 passed; both awarded together 3/27 → 20,000 = **2× MDQ**. It is a point-in-time, single-offer check — the exact "no cumulative/aggregate guard" defect family as 26-01081678 / 26-01063725.

**Fix (ranked):**
1. **Primary — hard gate at AWARD (authoritative):** at award / `CRK_GEN` (and on pre-arranged auto-award), re-validate `SUM(active awarded releases on the contract for the overlapping term/path) + this award ≤ releasing contract available MDQ`; reject/hold any award that would exceed. Posting multiple offers can be allowed, but awarding beyond capacity must be blocked. (Award/contract-gen path: `Quorum.QPTM.ClassicBatch /QPDllPipelineMgrCR/QPSContractGen.cpp` + the CRBIDEVAL/CRK_GEN award-eval.)
2. **Secondary — offer-time prevention:** make CRMDQMSQVL's available-capacity computation **net out other OUTSTANDING offers** (submitted / pending-award, excluding withdrawn/expired/rejected) on the same releasing contract + path + overlapping term — not just awarded releases — so creating/submitting the second full-MDQ offer fails "cap avail" up front.
3. **Cover Path MDQ** as well (per the "Additional UAT Testing_Release Over Path MDQ" attachment) — the same aggregation gap likely lets releases exceed *path* MDQ, not just contract MDQ. Scope the fix to both contract- and path-level.
4. **Config check:** code search found **no** `VALIDATE_*` capacity/offer config key governing this → likely **no config-only lever** exists (consistent with a "UAT Config Change Testing" doc that presumably did not fully resolve it). Read that doc to confirm what was trialed before committing to code-only.

**Confidence / to-confirm:** RCA mechanism confirmed via `GetAvailableCapacity` → per-offer `CRMDQMSQVL` launch. Still to confirm by reading the CRMDQMSQVL batch body (`QPDllPipelineMgrCR`) and the award path: (a) the exact available-capacity SQL (does it already join awards only?), (b) whether the cleanest gate is in the batch validation vs. the award step. The two binary walkthrough docs would pin the offer/award timestamps and the UAT config result. **No ADO bug exists — open one (net-new).**

---

### RCA & Fix — 2026-06-15 (Case 26-01099834, code-confirmed mechanism)

**Validation code read (`RuleNN00009011.cs`, DUT/QTR client pattern — EQT uses the standard logic; repo DUT.QPTM.Web `58c3259a-…`, branch develop):**
- Rule fires only when `activityDetailDO.IdCycle.HasValue && HasChangesCompareColsOnly` (L34). **L33 comment:** *"if the IdCycle is not set, then the user is letting this be 'defaulted' which will set it to the correct open cycle."* → if cycle is left unset, the system rolls it to the correct open cycle and the rule is skipped.
- **But an inbound NMST without a CS/cycle-indicator segment gets `IdCycle` AUTO-ASSIGNED in Phase-1 `ReadFile` via `GetOpenCycleByDay()`** (`QPTMNominationService` / `CycleManager`). So by validation time `IdCycle.HasValue` is TRUE → the "let it default / roll forward" safety branch is **bypassed**.
- L43 re-derives `nCycleID = GetFirstOpenCycle(activityDetailDO)` (independent of the assigned cycle); L54 gets that cycle's `OnTime` deadline for the user-type (L47-51: defaults **External**, Internal only if `IsUserInternal(ValidatingUserID)`); L110/123: `currentDateTime = Utilities.NowS; if (Utilities.NowS > cycleDeadline.CalcDeadline(begGasDay)) bIsValid = false` → **ENMQR315**.
- `GetFirstOpenCycle`/`GetCycleStatusByDay` return the first cycle whose deadline hasn't passed; **if ALL cycles are closed → -1 → reassigned to `GetLastCycle` (retroactive)** → NOW > its deadline → ENMQR315.

**RCA:** At the moment the nom was validated, the system evaluated **no open nomination cycle** for TSP 24 / that gas day (every configured cycle deadline already passed per the deadline config + server clock), so it treated the auto-assigned cycle as retroactive and raised ENMQR315. The customer believes ID3 was open at 2:45 PM CST; the system's deadline math disagreed. Three things drive that disagreement (ranked):
1. **Timezone (HIGH):** **Equitrans is an Appalachian/Eastern pipeline.** If its cycle deadlines are in **ET** and the shipper quoted **2:45 PM CST (= 3:45 PM ET)**, the nom was genuinely past an early-afternoon ID deadline by the pipeline's clock. Also verify the QPTM server/`Utilities.NowS` timezone vs the deadline timezone.
2. **Cycle-deadline config (HIGH):** `PACTRL_CYCLE_DEADLINE` for TSP 24 may have the ID3 (and later intraday) `OnTime` deadlines set earlier than Equitrans's true NAESB times, or be **missing the later intraday cycle rows** so nothing is open after mid-afternoon.
3. **User-type (MEDIUM):** the rule uses the **External** deadline set unless the validating user is internal; the EDI TPA-context user must resolve to the correct user type. Precedent: **#1609881** (late-nom rule user-type evaluation bug, Closed) — confirm EQT's build has it.

**Fix (ranked):**
1. **Most likely — CONFIG/timezone (no code):** verify `PACTRL_CYCLE_DEADLINE` for TSP 24 (all nom cycles, OnTime, External+Internal) against Equitrans's published NAESB deadlines **in the pipeline's own timezone**, and confirm the server/`NowS` timezone. Correct the deadline time(s) or add the missing later-intraday cycle row(s). Reconcile the shipper's "2:45 CST" vs the pipeline's ET deadline — if 3:45 ET is genuinely past ID3, this is **expected behavior + shipper education** (submit to the next open cycle or earlier).
2. **Product-behavior candidate (CODE) — only if config is correct and a later cycle WAS open:** for an NMST with **no cycle indicator**, when the early cycle is closed the system should **auto-roll to the next OPEN intraday cycle** rather than assigning the last (closed) cycle and rejecting as retroactive. Today the EDI auto-assign sets `IdCycle`, which defeats the rule's own "leave it unset → default to correct open cycle" path (L33). Fix = when `GetOpenCycleByDay` finds the requested/earliest cycle closed but a later cycle open, assign the **next open** cycle (or leave `IdCycle` unset so the rule's roll-forward applies) instead of `GetLastCycle`. This aligns with NAESB roll-to-next-open behavior.
3. **Consistency hardening:** the EDI auto-assign (`GetOpenCycleByDay`) and the validation re-derivation (`GetFirstOpenCycle`) should use the **same** open-cycle determination and the **EDI receipt timestamp** (not processing-time `Utilities.NowS`) so a slow-processing-but-on-time-at-receipt nom isn't failed by a deadline that elapsed mid-processing.

**Cannot fully close from here (need from consultant/client):** (a) the inbound EDI file `NomEdi_ReferenceNum_327176.txt` — exact submission timestamp + confirm no cycle segment (connector returns VersionData as a URL, not bytes → **ask consultant to paste the two EDI .txt files**); (b) `PACTRL_CYCLE_DEADLINE` rows for TSP 24 (diagnostic SQL already in this case's §17); (c) the QPTM server timezone. These three decide config/timezone (fix #1) vs the roll-forward code fix (#2). **No ADO bug is linked to 26-01099834 — open one only if (b)+(c) prove the config is correct and a later cycle was open.**

### ⚠️ Correction — 2026-06-15 (Case 26-01099834): cycle-deadline table name

**`PACTRL_CYCLE_DEADLINE` does NOT exist** (consultant-confirmed against live schema). The earlier diagnostic SQL in this case (§14/§16/§17) used a wrong, inferred name. **The real table is `PACTRL_CYCLE_DEADLINE`** (verified from `Quorum.QPTM.DAL/CodeGen/CycleDeadlineDAL.cs`: `TABLE = "PACTRL_CYCLE_DEADLINE"`, repo Quorum.QPTM.Web, branch develop). Verified columns (from `CycleDeadlineDO.cs` CodeGen): `TSP_NO, CYCLE_ID, DEADLINE_CTGRY_CD, DEADLINE_TYPE_CD, USER_TYPE_CD, GAS_DAY_RELATIVE, DEADLINE_SEC, DEADLINE, EFF_DT_FROM, EFF_DT_TO, HIST_IDX, UPDT_DT, USER_ID`. **No timezone column** — the deadline time is interpreted in the server/TSP clock (reinforces the timezone hypothesis). `CalcDeadline(gasDay) = (gasDay + GAS_DAY_RELATIVE days) at the DEADLINE_SEC time-of-day`.

**Corrected diagnostic (run on EQT/Equitrans PRD):**
```sql
SELECT CYCLE_ID, DEADLINE_CTGRY_CD, DEADLINE_TYPE_CD, USER_TYPE_CD,
       GAS_DAY_RELATIVE, DEADLINE_SEC, DEADLINE, EFF_DT_FROM, EFF_DT_TO, UPDT_DT
FROM   PACTRL_CYCLE_DEADLINE
WHERE  TSP_NO = 24
ORDER  BY CYCLE_ID, DEADLINE_CTGRY_CD, DEADLINE_TYPE_CD, USER_TYPE_CD;
```
Identify the Nomination-category / OnTime rows, compute each cycle's deadline for gas day 2026-05-09 (`GAS_DAY_RELATIVE` days + `DEADLINE_SEC`), and compare to the NMQR validation moment **14:45 ET**. Any cycle with deadline ≥ 14:45 (in the server TZ) = was open → code/roll-forward path; all earlier = correctly late → config/timezone path. Also confirm the QPTM server timezone (no per-row TZ exists).

### ✅ RCA CONFIRMED — 2026-06-15 (Case 26-01099834): code defect, config ruled out

Client-run `PACTRL_CYCLE_DEADLINE` (TSP 24, NOM/ONT, current eff 2025-01-01) — decoded:
| CYCLE_ID | GAS_DAY_RELATIVE | DEADLINE_SEC | Deadline | NAESB | Open at 14:45 gas-day? |
|---|---|---|---|---|---|
| 1 | −1 | 46800 | day-1 13:00 | Timely | closed |
| 2 | −1 | 64800 | day-1 18:00 | Evening | closed |
| 3 | 0 | 36000 | gas-day 10:00 | Intraday 1 | closed |
| 4 | 0 | 52200 | gas-day 14:30 | Intraday 2 | closed (by 12 min) |
| **6** | **0** | **68400** | **gas-day 19:00** | **Intraday 3 (ID3)** | **OPEN** |
| 7 | +1 | 27000 | next-day 07:30 | late/final | open (next-day) |

**Conclusion (airtight):** ID3 (CYCLE_ID 6, gas-day-relative 0, OnTime EXT deadline 19:00) was OPEN when EQT's nom (ref 327176, NMST 14:42, NMQR/validation 14:45 on gas day 2026-05-09) was validated. A correct open-cycle determination returns cycle 6 and the nom passes. It instead returned ENMQR315 → the EDI auto-assign / `GetFirstOpenCycle` did NOT roll the no-cycle-indicator nom forward to the open ID3; it latched on the just-closed ID2 (cycle 4, 14:30). **Config and timezone are RULED OUT** (19:00 deadline > 14:45 in any TZ). **Confirmed product defect.** Strong trigger: TSP 24 has **non-contiguous cycle IDs (1,2,3,4,6,7 — no 5)** + a day-relative (+1) cycle 7 — the non-standard/non-contiguous cycle-ID condition behind ADO **#1611244**.

**Fix:** in EDI inbound cycle auto-assignment (`GetOpenCycleByDay`/`GetCycleStatusByDay`, `QPTMNominationService`/`CycleManager`), a no-cycle-indicator NMST must be assigned the **next cycle whose OnTime deadline has not passed** (ID3 here), and the iteration must be robust to **non-contiguous CYCLE_IDs** (skip missing 5) and day-relative offsets — or leave `IdCycle` unset so `RuleNN00009011`'s own default-to-open-cycle path applies. Confirm whether #1611244's fix is in EQT's build; if present, log a new sibling bug.

### 🔎 RCA refinement — 2026-06-15 (senior input: "client relies on a mechanism that picks the current open cycle")

The senior's note resolves *why* the open cycle wasn't chosen. QPTM's "pick the current open cycle" behavior = its **cycle-defaulting**, which runs **only when the nomination's cycle is left UNSET** — the exact branch `RuleNN00009011` documents (code comment L33: *"if the IdCycle is not set, then the user is letting this be defaulted, which will set it to the correct open cycle"*). Manual/Web noms leave cycle blank → this defaulting picks the current open cycle (ID3) → accepted.

**The EDI inbound path bypasses that mechanism.** `QEdiNMSTIn18.ReadFile` **force-assigns** the cycle (`currDO.IdCycle = OpenCycles[sYearMonth][day-1]` via `GetOpenCycleByDay`) before submission. So at validation `IdCycle.HasValue == true` → `RuleNN00009011` runs the hard late-check against the *assigned* cycle instead of deferring to the open-cycle defaulting. On TSP 24 (non-contiguous cycle IDs 1,2,3,4,6,7 — no 5; + day-relative cycle 7) the force-assign resolved to a **closed** cycle (ID2/cycle 4, just passed at 14:30) → ENMQR315 — even though ID3 (cycle 6, 19:00) was open and the defaulting mechanism *would* have chosen it.

**Net:** same defect, now precisely located — the EDI auto-assign pre-sets the cycle and **defeats the client's relied-upon "current open cycle" defaulting**. 

**Fix (refined, preferred):** on the EDI inbound path, for an NMST with **no cycle indicator**, **leave `IdCycle` unset** so the standard cycle-defaulting (the "pick current open cycle" mechanism the client relies on, via `RuleNN00009011`'s default branch) selects the cycle — instead of force-assigning it in `ReadFile`. Alternatively, make `GetOpenCycleByDay` use the **identical** current-open-cycle selection as the manual path and be robust to **non-contiguous CYCLE_IDs**. Either way the EDI path then behaves like manual entry and rolls to the open ID3. (Still confirm whether ADO #1611244's non-contiguous-cycle-ID fix is in EQT's build.)


### Reverse-engineering pass (code-confirmed, 2026-06-15) — Offer Summary + Award + MDQ validation

Confirmed firsthand from Quorum.QPTM.Web @develop (commit fdcffc48):

**Web layer**
- Offer Summary screen = OfferViewerController.cs ([QScreenSecurityObject("QUCCROfferViewer")]) -> QUIControllerOfferViewer + OfferSummaryVM; read/query grids GetOffers (CROfferHeaderVM, uic.Offers) + GetDetails (CROfferDetailVM, uic.OfferDetails). Grid IDs OfferGrid/DetailsGrid.
- Award screen = CRAwardController.cs ([QScreenSecurityObject(SecurityObjectIDs.CapRelAward)]) -> QUIControllerCRAward + CRAwardRootVM; two grids EvaluatedBidsGridGetData(uic.AvailableToAward) + AwardsGridGetData(uic.SelectedToAward), both CRBidAwardHelperVM. Manual award: user moves bids Available->Selected, Save=Submit.

**Service layer (Quorum.QPTM.ServiceCore.CapacityRelease/QPTMCapacityReleaseService.cs)**
- ValidateOffer L552 / SubmitOffer L599 / GetAvailableCapacity L1810 all call bps.LaunchCRMDQMSQVL_CRValidateMDQMSQ(offer.TspNo, offer.OfferNo, ...) with a SINGLE OfferNo. The MDQ/MSQ compare is the CRMDQMSQVL batch (C++ QPDllPipelineMgrCR, not in this repo); result written to CRCTRL_OFFER_DTL.CAP_AVAIL_QTY (CapAvailQty).
- SaveAward L2656 validates via QCRAwardValidationContext (throws if awards span >1 OfferNo, L2670-2674); ExecuteBatchProcesses runs CRK_GEN/CRK_ALL to generate replacement K.

**Validation context = the gap**
- QCROfferValidationContext carries ONLY OfferHeader (one offer); no other-offer/award list, no contract MDQ -> no offer rule can do a cumulative check.
- QCRAwardValidationContext.GetExistingAwardHeaders() filters awards by **OfferNo only** (Filter OfferNo EqualTo OfferNo) -> sees other awards on the SAME offer, never other offers on the same releasing contract.

**Data model**: CROfferHeaderDO=CRCTRL_OFFER_HDR (CrStatusCode, PrearrDealCode, RelBpNo, RelStart/EndDate; no qty/RelCtrNo). CROfferDetailDO=CRCTRL_OFFER_DTL (RelCtrNo=REL_CTR_NO, BidQtyLoc/BidQtyCtr, MaxOfferQtyCtr/Loc, MinOfferQtyCtr/Loc, CapAvailQty=CAP_AVAIL_QTY). CRAwardHeaderDO=CRCTRL_AWARD_HDR (AwardNo,OfferNo,BidNo); award qty/ReplSrCtrNo on CRAwardDetailDO=CRCTRL_AWARD_DTL.

**Verdict**: aggregate-offers-vs-MDQ check is MISSING at all three layers (offer validate, batch CRMDQMSQVL launched per-offer, award validate scoped per-offer). Confirms the prior RCA. RuleCROF000750 (the prompt seed) is a virtual-receipt-loc check, NOT quantity. No C# RuleCROF/RuleCRAW does the qty-vs-MDQ compare (it is the C++ CRMDQMSQVL batch).

---

## Case 26-01094568 — IPL (Inter Pipeline / IPF): TIPS Settlement Report doubles GJ & $ on first page

**Date:** 2026-06-15 · **Account:** Inter Pipeline Ltd. (client code **IPF**, Canadian — GJ units) · **Contact:** Alla Ovcharenko · **Product:** TIPS · **Category:** Reporting/Settlement · **Priority:** Medium · **Status:** In Progress

### Issue
The Settlement Report (Report Distribution package 99835, April 2025) **doubles the GJ and $ amounts on the first (summary) page** for 5 shippers: Access Gas, Ovintiv, PG&E, Portland General Electric, Puget. Detail pages are correct. Attachments: "Walkthrough - IPF Doubling GJ's - Settlement Statement" (docx), the 5 shipper settlement PDFs, package PDF.

### Classification: **Code / report defect — client-specific IPF view** (NOT data; underlying settlement is correct).

### RCA — confirmed at code level (CORRECTED 2026-06-22 after examining the actual report)
**The report the customer runs is `Settlement Statement`, registry `RPT_ID 43154`** (`IPF.TIPS.Metadata/STANDARD 16.0/QARCH_RPTS_DEFINE.json`: `RPT_FILE_NM = SETTLEMENTSTATEMENT.RPT`, `CONNECTION_ID QIPFDataHelper`, updated 2025-11-06). Its `QARCH_RPTS_TBL_MAP` binds it to **`QRPTS_SETTLEMENT_STMT_VW`** + **`QRPTS_SETTLEMENT_STMT_FEE_VW`** (MAP_TYPE 1; posted MAP_TYPE 2 → `QPOST_*`). **It does NOT use `QRPTS_SETTLEMENT_SUM_VW`** — that view belongs to a *different* report (`SettlementSummary.RPT`); my 2026-06-15 entry analysed the wrong view. (`SUM_VW` does have an analogous latent gap — see "Secondary" below — but it is not what doubles RPT_43154.)

**The doubling is inside `QRPTS_SETTLEMENT_STMT_VW` itself**, not the Crystal layer. Source: `IPF.TIPS.Database/Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_VW.sql`, develop (re-read 2026-06-22). Structure: CTE `TRANSACTIONS` (current, from `QTRAN_*`) and CTE `POSTED` (prior, from `QPOST_*`), joined in the final SELECT as `CURRENT_TRANSACTIONS LEFT JOIN POSTED_TRANSACTIONS` (**L452-453**) to drive current-vs-previous columns.

In the `TRANSACTIONS` CTE:
- `INNER JOIN QTRAN_SETTLE_PROD AS PROD ON PROD.TRNX_ID=S.TRNX_ID AND PROD.MTR_SFX=S.MTR_SFX AND PROD.REC_STATUS_CD IN ('CO','OR')` (**L68-71**).
- Per-product **GJ** = `SUM(CASE WHEN PROD.DISP_CD IN ('PROD','INLT','PRFS') THEN PROD.APPLIED_VOL_HV_PR … END) AS APPLIED_VOL_HV_PR` and per-product **$** = `SUM(… PROD.VALUE_PR …) AS VALUE_PR` (**~L34-37**).
- Settlement totals = `MAX(S.TOT_VALUE_PR)`, `MAX(S.TOT_NET_VALUE_PR)` … (**L39-43**).
- `GROUP BY` (**L168**) groups at PLANT/CTR/PROD_DT/PROD_CD/DISP_CD — **`REC_STATUS_CD` is NOT a grouping key** (and is hardcoded to `' '` on output, L416). The `POSTED` CTE mirrors all of this (PROD filter **L260**, group by **~L357**).

**Mechanism (precise):** when a settlement is revised, `QTRAN_SETTLE_PROD` keeps **both** an `'OR'` (original) and a `'CO'` (corrected) row for the same product — both pass `IN ('CO','OR')`. Because `REC_STATUS_CD` is not in the `GROUP BY`, the two rows fall into **one** group and their GJ/$ are **`SUM`-med together → exactly 2×**. The settlement *totals* use `MAX(S.TOT_*)`, so they pick a single revision and stay correct — that is why **only the GJ and $ (the per-product `SUM` columns) double**, not the net total. The Crystal report then re-sums these already-doubled values for its first-page/group totals: `Summary: Sum({QRPTS_SETTLEMENT_STMT_VW.APPLIED_VOL_HV_PR},{PROD_CD})` (report def **L590**) and `Sum({…VALUE_PR},{PROD_CD})` (**L594**), grouped by `PROD_CD`. So the first page shows 2× GJ and 2× $. Affects only the 5 shippers whose April-2025 settlement was revised (single-revision shippers have one product row → `SUM` of 1 → correct).

### Fix
Collapse the per-product GJ/$ to a **single effective revision** in `QRPTS_SETTLEMENT_STMT_VW` (both the `TRANSACTIONS` and `POSTED` CTEs) and the posted mirror `QPOST_RPTS_SETTLEMENT_STMT_VW`, consistent with the `MAX`-based totals (which already take one revision). Recommended shape — dedupe `QTRAN_SETTLE_PROD` to one row per (`TRNX_ID, MTR_SFX, PROD_CD, DISP_CD`) before the `SUM`, preferring the corrected revision:
```sql
-- replace the bare  INNER JOIN QTRAN_SETTLE_PROD AS PROD ON … AND PROD.REC_STATUS_CD IN ('CO','OR')
INNER JOIN (
    SELECT *, ROW_NUMBER() OVER (
               PARTITION BY TRNX_ID, MTR_SFX, PROD_CD, DISP_CD
               ORDER BY CASE REC_STATUS_CD WHEN 'CO' THEN 0 ELSE 1 END) AS RN
    FROM QTRAN_SETTLE_PROD
    WHERE REC_STATUS_CD IN ('CO','OR')
) AS PROD
   ON PROD.TRNX_ID = S.TRNX_ID AND PROD.MTR_SFX = S.MTR_SFX AND PROD.RN = 1
```
View-only change in `IPF.TIPS.Database` (client-specific); **no Crystal change, no data fix** — underlying settlement values are correct. Ships as an IPF client patch.

> **Business-rule to confirm first (diagnostic #1):** the fix assumes `'CO'` *supersedes* `'OR'` (take one), which is what the `MAX(S.TOT_*)` totals already do. If, instead, `'OR'`+`'CO'` are meant to be *additive* (a delta model), then the totals — not the product breakdown — would be wrong, and the fix differs. The `MAX`-on-totals design strongly implies supersede, but verify in data before coding. If verification shows the prior revision is reversed to `'R'` rather than kept as `'OR'`, then a leaked `'R'`/duplicate is the cause and the same dedup still resolves it.

### Diagnostic SQL (run in the IPF client DB)
```sql
-- 1. KEY CHECK: do OR and CO coexist per product for the doubling shippers? (drives the fix)
SELECT P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD,
       COUNT(*) AS TOTAL_ROWS,
       SUM(CASE WHEN P.REC_STATUS_CD='OR' THEN 1 ELSE 0 END) AS OR_ROWS,
       SUM(CASE WHEN P.REC_STATUS_CD='CO' THEN 1 ELSE 0 END) AS CO_ROWS,
       SUM(CASE WHEN P.REC_STATUS_CD='R'  THEN 1 ELSE 0 END) AS R_ROWS,
       SUM(P.VALUE_PR) AS VALUE_SUM, MAX(P.VALUE_PR) AS VALUE_MAX
FROM   QTRAN_SETTLE_PROD P
JOIN   QTRAN_PAYSTATION  PS ON PS.TRNX_ID=P.TRNX_ID AND PS.MTR_SFX=P.MTR_SFX
WHERE  PS.RUN_ID = <april_2025_settlement_run_id>
  AND  PS.CTR_PARTY_BA_NM IN (...Access Gas, Ovintiv, PG&E, Portland General, Puget...)
  AND  P.REC_STATUS_CD IN ('CO','OR')
GROUP BY P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD
HAVING COUNT(*) > 1            -- any rows here = a product summed across >1 revision = the doubling set
ORDER BY P.TRNX_ID, P.PROD_CD, P.DISP_CD;

-- 2. Prove the view itself already doubles for one shipper (compare product SUM vs the MAX-based total)
SELECT CTR_NO, PROD_CD, DISP_CD, APPLIED_VOL_HV_PR AS GJ, VALUE_PR AS DOLLARS, TOT_NET_VALUE_PR
FROM   QRPTS_SETTLEMENT_STMT_VW
WHERE  CTR_PARTY_NM LIKE '%Puget%' AND PROD_DT = '2025-04-01'
ORDER BY PROD_CD, DISP_CD;   -- GJ/$ here will be ~2× the true per-product value; TOT_NET_VALUE_PR stays single.
```

### Fix availability — checked 2026-06-22: **NO existing fix anywhere**
- **No ADO work item tracks this case/issue** — WIQL on `26-01094568`, "Doubling GJ", "Settlement Report Doubles" → 0 hits. Nothing is in flight for the doubling.
- **Current & latest-deployed view is the unfixed version.** Commit history of `QRPTS_SETTLEMENT_STMT_VW.sql` (develop): last 4 changes (PR 120958 2025-12, PR 121647 2026-01, PR 126604 2026-04-20) are all the **unrelated** `QCODE_TOS → QCODE_SERVICE_CLASS` code-table swap (bugs 1755144 / 1799519 / 1787313; "TOS_DESCR alias preserved"). The newest deployment script `QTIP_17.0.00.0031…_1799519.sql` still has `INNER JOIN QTRAN_SETTLE_PROD … AND PROD.REC_STATUS_CD IN ('CO','OR')` with **no `REC_STATUS_CD` in GROUP BY and no `ROW_NUMBER`** → the `SUM`-over-revisions defect is fully present.
- **No other copy to borrow from.** The view is IPF-specific (`CREATE VIEW QRPTS_SETTLEMENT_STMT_VW` exists only in IPF.TIPS.Database); no client/base variant uses `ROW_NUMBER`/dedup. → The fix is **net-new**; nothing to "just deploy."
- **Coordinate:** sibling bug **#1787313** ("IPF — 26-01084662 — Settlement Report Package Differences", *Acceptance*, dev Snehal Thorat) is actively editing this same view / same report package (but for the Processed-Volumes contract-class issue, not the doubling). Land the doubling fix alongside it to avoid view-merge conflicts.

### Re-verification 2026-06-23
Re-checked live; RCA and fix unchanged. (1) Independently re-read the `QRPTS_SETTLEMENT_STMT_VW` DDL — PROD join `REC_STATUS_CD IN ('CO','OR')` (L68-71), no `REC_STATUS_CD` in `GROUP BY` (L168), GJ/$ via `SUM` (L34/L36) vs totals via `MAX(S.TOT_*)` (L39-43): confirms the SUM-over-revisions doubling. (2) WIQL on `26-01094568` / "Doubling GJ" / "Settlement Report Doubles" → still **0** work items; the doubling remains untracked in ADO. (3) Sibling **#1787313** still **Acceptance** (Snehal Thorat, iteration April Wk3, last changed 2026-04-22) — same view, coordinate the fix. SF case still **In Progress**. Next action: file the IPF bug (write-up drafted) and align with Snehal on the shared view edit.

**Walkthrough doc corroboration (2026-06-23, "Walkthrough - IPF Doubling GJ's - Settlement Statement", author Bailey Coates):** The customer's own evidence pins the aggregation behavior and confirms the RCA a third way — **rate is correct, volume is doubled, $ doubled (= rate × doubled volume)**. This matches the view exactly: `APPLIED_VOL_HV_PR` and `VALUE_PR` are `SUM` (→2×) while `APPLIED_PRICE` is **`AVG` (L35) → unchanged**. (So the case's "GJ and $" double; the unit rate does not — the $ doubles only because volume does.) Customer verified **DB / Query Suite / Calculation Summary all show the true (½) values** → data correct, report over-sums. Repro: env **IPF_HD_DEVA1**, plant **CEP**, **May-2025 acct / Apr-2025 prod** (acct≠prod ⇒ adjustment rows; matches view filter `ACCT_DT <> PROD_DT` L471). Affected contracts: Access Gas **1103**, Ovintiv **1027**, PG&E **1033**, Portland General **1011/1116/1154**, Puget **1095**. The dedup fix resolves all three figures (post-dedup: `SUM` of 1 row = true volume/value; `AVG` of 1 row = true rate).

### Secondary (separate report, not RPT_43154)
The summary view `QRPTS_SETTLEMENT_SUM_VW` (used by `SettlementSummary.RPT`) has a related latent gap: its 7 per-product `LEFT JOIN QTRAN_SETTLE_PROD` (L98-144) carry **no `REC_STATUS_CD` filter at all** and the view has no `GROUP BY` — so a reversed/duplicate product row would fan it out there too. Same in posted mirror `QPOST_RPTS_SETTLEMENT_SUM_VW` (L95-144). Fix if that report is also reported wrong: add `AND <alias>.REC_STATUS_CD IN ('CO','OR')` to each product-join `ON` (keep it in `ON` to preserve the outer join) + dedup. **Not required to resolve this case.**

---

# Case 25-01053969 — MWP | AUTOCONF cuts path-threaded TSP3 nom to zero
**Investigated 2026-06-23.** Account: MountainWest Pipeline, LLC. Contact: Scott Whitaker (reporter: scheduler Heather Walter). Status: In Progress, High. Created 2025-11-10.

### Symptom
Path-threaded AUTOCONF cuts the **TSP3 (MWP) nom on contract K6959, DXT at MAP receipt LOC 869, to zero**, even though the matching **TSP4 (MWOP) nom on K3927 (REX/Rockies) at LOC 10008** confirms in full and the noms line up. Recurs every gas day (started GD9/GD10).

### Classification: **Configuration** (interconnect / AUTOCONF matching) — *not* a contract-model defect.

### History & why the first RCA was wrong
- **First RCA (Feb–Apr 2026):** diagnosed as PNT↔PT contract-model mismatch (K3927 set to PT, K6959 left PNT) → `CONF_RUN_PATH_BAL_FOR_PNT=1` firing PBL/CPR path-balancing cuts. Fix delivered = set **`CONF_RUN_PATH_BAL_FOR_PNT = 0`** for TSP3 / amend K6959 to PT.
- **Customer rebuttal 2026-05-26 (Scott):** *"K3927… has already been set to PT… Setting K6959 to PT did not fix this. Volumes are still cut to 0."* → contract model is **ruled out**. Both legs are PT and the cut persists. The PBL/CPR theory does not explain the current behavior.

### Corrected root cause (high confidence)
This is the **CFAUTOCONF cross-TSP interconnect match-to-zero** behavior. AUTOCONF gathers interconnect locations via `GetInterconnectLocations()` (**`QPTMNominationService.cs:14268`**, verified in cached source): it returns only IC-attribute locations that **share an Interconnect DRN** (location-association type `DRE`), and logs *"is an interconnect location, but does not have a DRN specified"* / *"more than one location… with same Interconnect DRN"* when linkage is wrong. `MatchRelatedConfirmations()` then requires the two sides' **Up/Dn business party and Up/Dn contract to align like pool balancing** (`DEP_BP_NO` must match `REC_BP_NO` on the upstream side). When 869 (TSP3) and 10008 (TSP4) **don't share a matching DRN, or the BP/contract data elements don't align, AUTOCONF cannot group the two confirmations and collapses the TSP3 side to 0.**

### Decisive precedent — same client, same scenario
- **ADO #1716241 "QTR – MWP CFAUTOCONF Is Not Updating Quantities After Cut"** (Closed). Repro = nominate TSP3 w/ DnK, TSP4 w/ UpK, cut TSP3, run CFAUTOCONF → no change. Eng (Grayson Lee) root cause: (a) `ONLY_AUTO_CONFIRM_LEASE`=true was making **non-lease noms be ignored**; (b) the **DRNs on the two locations did not match**. Eng (Annie Sanna) **made it work in DEVA1** by: *"updated the 'ONLY AUTO CONFIRM LEASE' config setting to 0 and tied the DRN from the location in TSP 4 to the Interconnect DRN field"* → cut on TSP3 + CFAUTOCONF then confirmed correctly. Closed (blocked) only because the lease config is QTR-specific and tangled with a separate AUTOCONF enhancement — **the config remedy is documented and proven for this client.**
- **ADO #1396176 "WWM – Automatic Confirmation issue at interconnects"** (Closed). Same engine. Findings: set `ONLY_AUTO_CONFIRM_LEASE`=0 and `LEASE_NOM_CONFIRM_ACROSS_TSPS`=0; AUTOCONF level must match on both TSPs; a **receipt location erroneously stamped Interconnect** was itself being cut to 0; **resolved by re-entering the Confirmation Plan & Level records** (originals weren't being picked up).
- **ADO #1377828 (ENT)** — the canonical RCA; product treats TSP-scoping as enhancement. Workaround when sides genuinely can't be made to match: **end-date the offending IC location's DRN** so AUTOCONF stops matching/zeroing.

### THE FIX (config; no code change) — apply on the affected env, then re-confirm
1. **Interconnect DRN linkage (primary):** confirm LOC **869 (TSP3/MWP)** and LOC **10008 (TSP4/MWOP)** both have the **Interconnect location attribute = true** and **share the same Interconnect DRN** (`DRE` association). Tie the TSP4 location's DRN into the Interconnect DRN field on the TSP3 side so the two match. *(This was the change that fixed #1716241.)*
2. **Lease autoconf config:** the path noms are **non-lease**, so confirm **`ONLY_AUTO_CONFIRM_LEASE = 0`** (and **`LEASE_NOM_CONFIRM_ACROSS_TSPS = 0`**) for the TSPs involved — with true, non-lease interconnect noms are skipped and cut to 0. If MWP relies on lease autoconf elsewhere, **scope** the change rather than flipping it globally; fixing the DRN match (step 1) is the lease-safe lever.
3. **Receipt-location attribute:** ensure the TSP3 **receipt** location feeding the path is **not itself flagged Interconnect** (an over-stamped receipt loc is auto-cut to 0 — #1396176).
4. **Data-element alignment:** verify the K6959 (TSP3) and K3927 (TSP4) noms carry matching **Up/Dn BP and Up/Dn contract** across the interconnect (UpK/DnK populated and consistent) so `MatchRelatedConfirmations` groups them.
5. **If still cutting:** **re-enter (re-submit) the Confirmation Plan & Confirmation Level** records for both TSPs and confirm the **AUTOCONF level matches** on both (#1396176 final fix).
6. **Last resort** (sides truly cannot be matched): **end-date the IC location's DRN** so AUTOCONF stops grouping and the leg is hand-confirmed (#1377828 workaround).

### Diagnostic SQL (run for the affected gas day/cycle to confirm the cut + method)
```sql
SELECT gas_day, conf_cycle_id, tsp_no, loc_id, sr_bp_no, sr_ctr_no,
       REC_NOM_QTY, REC_CONF_QTY, REC_CONF_METH_CD, REC_REDUCT_RSN_CD,
       DEL_NOM_QTY, DEL_CONF_QTY, DEL_CONF_METH_CD, DEL_REDUCT_RSN_CD
FROM QPTM.CFCTRL_CONF
WHERE gas_day = '<GD>' AND conf_cycle_id = <CYC>
  AND loc_id IN (869, 10008)
  AND (REC_CONF_METH_CD = 'AUT' OR DEL_CONF_METH_CD = 'AUT')
ORDER BY tsp_no, loc_id;
```
Then verify in Location Maintenance: Interconnect attribute + Interconnect DRN on 869 vs 10008 must match; check `ONLY_AUTO_CONFIRM_LEASE` / `LEASE_NOM_CONFIRM_ACROSS_TSPS` config values; confirm the receipt loc isn't IC-flagged.

### ADO recommendation
No ADO item is linked to 25-01053969 (Desiree requested one 2026-04-27). Recommend **linking this case to #1716241** (same client/scenario) and re-opening or filing a follow-up referencing the #1716241 DEVA1 config remedy, since the prod env still exhibits it.

### Attachments on case (not machine-readable here)
"problem walkthrough" (Word, Heather, 2025-11-13); "Case Analysis - 25-01053969" (HTML, 2026-04-02 — mirrors the PBL/CPR RCA now superseded); images 36/42/44/45/46/51 (latest 2026-06-17). The 4/2 RCA text is captured in the case feed.

### Code-verified update (2026-06-23) — exact engine, plus two corrections from adversarial review
**Engine located in live source:** CFAUTOCONF = `QAutoConfSeg : QPTMSegregatedProcessBase` in **`Quorum.QPTM.Batch /Quorum.QPTM.QPDllConfirmations/QAutoConfSeg.cs`** (develop). The earlier note pointed at `QPTMNominationService.cs` — that file only holds `GetInterconnectLocations()` (the IC-grouping feeder, `:14268`); the cut happens in `QAutoConfSeg`.

**Verified mechanics:**
- Config reads (both GLOBAL-only, no per-TSP override): `ONLY_AUTO_CONFIRM_LEASE` (`:81`) and `LEASE_NOM_CONFIRM_ACROSS_TSPS` (`:80`), group `CONFIRMATIONS`. **QTR/MWP ships `ONLY_AUTO_CONFIRM_LEASE = 1`** (`QTR.QPTM.Metadata QARCH_CNFG_CTRL.json:498`) vs STANDARD `0`.
- Lease skip: `if (m_bOnlyAutoConfirmLease && confSum.SrcOrigSrcCode != "LS") continue;` (`:385-388`).
- PT-path gate: a path record that isn't BOTH Up and Dn is skipped (`:390-394`); transaction-type exclusion (`:396-400`, from Feature #1668215).
- One-sided gate `if (bUpRecFound==false || bDnRecFound==false)` (`:559`) → zero-out `unrelatedConf.ConfQty = 0` + reason **CPR** (`:631-636`).
- Match key `BuildHashKey` (`:1102`): shared **Interconnect DRN** + autoconf-LEVEL column set + cross-paired Up/Dn BP + Up/Dn contract + `matchRecLocID` (opposite-TSP loc sharing the DRN, `:1136`). IC grouping needs `IC` attribute + shared DRN (`QPTMNominationService.cs:14286-14344`); association type code **`DRE`** (`:60` / `:14358`), read gas-day-effective-dated.

**Correction 1 — symptom decides the lever.** With BOTH legs *non-lease* and the key `=1`, both sides are `continue`-skipped, nothing is written → CFAUTOCONF is a **no-op** (the literal #1716241 "no changes to TSP3" symptom), NOT an active CPR cut. An **active** cut-to-0 at `:633` requires one side matched while its partner is **absent/unmatched** (DRN/DRE not shared, autoconf level mismatch, PT Up/Dn flags, or partner has no CFCTRL_CONF row). **Read `RED_RSN_CD` on the TSP3 row first**: `CPR` ⇒ active one-sided cut (data-alignment fix); no AUT action ⇒ no-op (lease-skip/level/eligibility).

**Correction 2 — `ONLY_AUTO_CONFIRM_LEASE=0` is global and Eng objected.** #1716241 was Closed **Rejected (blocked >3wks)**; the `ONLY_AUTO_CONFIRM_LEASE=0` + DRN-tie recipe worked **in DEVA1 only**, never promoted to MWP prod. Eng (Annie Sanna, comment 13052177) explicitly **did not want it off for QTR** ("a config created for QTR… the enhancement needs to work with it on. What is it about the noms… not meeting the lease nom criteria?"). The key is **global** → flipping it makes *every* non-lease interconnect on the instance eligible for the `:633` cut. **Lead with the DATA fix (DRE/DRN tie + level match, effective-dated to the gas day); treat the global key flip as a last resort or scope via lease classification / `LEASE_NOM_LOC_ATTR` (BALANCING, per-TSP).**

**No code fix exists.** Only CFAUTOCONF change shipped = Feature **#1668215** "Exclude Noms Based on Transaction Type" (builds 2025.04.1.2 / 2025.04.1.4 / 2025.10.1.0) — adds a transaction-type *exclusion* param only; does NOT fix interconnect matching. Open follow-ups **#1753674** (Acceptance) and **#1760460** (Proposed) show the TSP3 cut still reproduces on 2025.04. So config/data alignment is the only path.

**Verification expectation correction:** the fix confirms each side to the **lesser of the two matched quantities** (`AutoConfirmRelatedConfirmations :661`/ProRateReduction `:790-827`; #1716241 AC = "update to lesser of between the two") — *full* only if K6959 receipt and K3927 delivery qty are equal.

### Code-fix check (2026-06-25) — CONFIRMED: no code fix exists
Independently re-verified against live ADO (work items + #1753674 full comment thread). **No matcher code fix shipped, in-flight, or in any PR/branch.** The cut-to-zero of an unmatched interconnect side is engine-by-design.
- **#1753674** (State Acceptance) `WorkItemOutcome = "Not an Issue"`, RootCause Unknown, **no PR/commit relation** (parent #1668215; only child = investigate-task #1758761; rest are .docx walkthroughs). Brian Huang 10/10: *"Test Case 3 may be a Maintenance bug… Our code would not impact the results in that scenario"*; future work *"as a TRAP Feature, not a bug ticket."* Maheshkumar Paul 10/9: the cut *"isn't caused by the enhancement… it's a pre-existing issue."* TC#3 expected outcome (verbatim): *"Interconnect location in TSP 3 is cut. Meter bounce nomination without a match is cut to zero."*
- **#1760460** (State Proposed, never triaged, no PR/commit) AcceptanceCriteria: cuts to TSP3 *"cut to zero due to mismatched nominations."*
- Only shipped CFAUTOCONF change = **#1668215** (transaction-type exclusion param; builds 2025.04.1.2 / 2025.10.1.0) — does not touch `MatchRelatedConfirmations`/`BuildHashKey`/`GetInterconnectLocations`.
**Implication:** no upgrade resolves it; config/data alignment (DRE/Interconnect DRN + autoconf level + Up/Dn BP/contract, effective-dated) is the only fix. Auto-pairing imperfectly-aligned threaded sides = enhancement/TRAP request, not a bug.


---

## Case 26-01093642 — Tallgrass: shippers set up on Event Detector 11014 not receiving reports (no Event Log entry)

| Field | Value |
|---|---|
| Case | 26-01093642 (SF Id 500UH00000ml7iNYAQ) |
| Client | Tallgrass MLP Operations, LLC |
| Subject | Shippers set up in the Event Detector are not receiving their reports |
| Status / Priority | In Progress / High |
| Owner / Created | Tushar Patil / 2026-04-15 |
| Example | Event Detector **11014**, BPID **9867 (DCP)**: **5** recipients set up, **3** receive, **2** do not — the 2 have **no Event Log entry** (no send attempt). Also reported for **Koch** on the same ED 11014 (attachment). |

### Issue
A "cut report" event detector (ED 11014) fans out to multiple operators/shippers. Two configured recipients never receive it, and critically there is **no Event Log / Event Notice Queue row** for them — i.e. the report was never even *attempted* for those two. That signature means the recipients are being dropped **upstream of the send pipeline** (never resolved into the notice queue), not failing at SMTP/delivery. (Contrast: cases where the log shows "sent" but mail doesn't arrive are email-format/SMTP problems — a different symptom.)

### Classification
**Configuration (most likely) → rule out Expected Behavior first → Defect only if both are clean.** Not an SMTP/delivery problem.

### Root cause — ranked hypotheses
**H1 — Recipient-setup / config gap (most likely).** The 2 non-receiving recipients are not being *resolved* into the recipient list at trigger time. QPTM event-detector notification resolution (process **UTILSCHNOT**) only includes a recipient who is **active, has an email, is tied to the reporting BP/TSP on the BA Contact screen, is actually on the detector's Contacts tab, and whose security group grants the event-notification type.** Any one of those missing → recipient is silently dropped → no queue/log row → no send attempt. Strong support:
- **Same client, same detector precedent: case 23-00921160 (2023)** — *"Users from SWN (GID 10482) stopped receiving cut reports (event detector 11014)."* The only recorded Quorum action was checking the Event Detector Setup → Contacts tab for ED 11014 and finding two named users *not present in the Contacts tab* (email from M. Lizarazo, 2023-09-25). NB: `Resolution__c` is null and there are no case comments, so the confirmed final fix isn't in the record — but Quorum's diagnosis pointed squarely at the recipient/Contacts-tab setup. Also note 23-00921160 was **SWN/GID 10482**, a *different* BP than this case's **DCP/BPID 9867** — same detector, same symptom, different party.
- **Sibling resolutions (all config):** Pembina 26-01084250 → *"added the event notification type to the security group"*; MountainWest 26-01080390 → *"turned on the event detector for email"*; EQT 26-01067520 → recipient already existed (PK violation).
- **Mechanism documented by ADO #113963** (Closed, fixed 2019.07.1.1, QLNG cargo path): scheduled-notification recipient resolution honors the **BP + TSP tie** — a contact only receives the notice if the TSP is defined on their BA Contact for that BP. Verified verbatim in `QSQL_PipelineScheduleNotification.cpp` (QSQLIDs `m_sel_SecUserBaNo` / `m_sel_ContactBpNo`; filters `INACTIVE_IND=0`, `SCTRL_USER_TSP.TSP_NO=@TSP`, `SXREF_CONTACT_ROLE_TSP.TSP_NO=@TSP`, `BA_NO/PRIMARY_BP_NO IN (...)`). *Caveat: those exact QSQLIDs live in the QLNG TerminalMgr (Composite ADP) variant; the QPTM cut-report path is the sibling `Quorum.QPTM.ClassicBatch /QPDllPipelineMgrUtil/QSQL_PipelineScheduleNotification.cpp` + `m_Sel_NotifyOperators` — same filter mechanism, different file.*

**H2 — Expected behavior post-#1756997 (CHECK THIS FIRST — cheapest to confirm).** If ED 11014 drives the **CAX_14 "Scheduled Quantity for Operator" cut report** (or a CAX-family operator cut report), ADO **#1756997** (QPTM/Notifications, Closed, fixed **2024.04.1.42 / 2025.04.1.12 / 2025.10.1.2 / 2026.04.1.0**) changed the report so it sends **only to operators whose location was actually cut/confirmed that cycle** — it no longer blasts every contact on the detector. RCA verbatim: *"m_Sel_NotifyOperators query returned all OPR/OPA contacts system-wide… now query returns only contacts from staging table… Event Detector validates, resulting in correct single notification."* So if Tallgrass is on a build that contains this fix, the 2 "missing" recipients may simply have had **no cut/reduction on their locations** during those cycles → no report generated for them → no log entry. **This is working as designed, not a bug or a config error.** Must be excluded before any config/defect work.

**H3 — Defect (least likely).** No currently-open defect matches the *under-send / no-log* symptom. #1756997 is Closed and its bug direction was *over-send*; #113963 is old QLNG. Residual risk: if Tallgrass's build **predates the #1756997 fix on its release line**, CAX_14 recipient behavior could be off. Only if H1 and H2 are both clean (recipients fully configured AND a cut occurred on their location AND still no queue row) should this be escalated as a **fresh** defect — do not reuse the closed bugs.

### Related history
| Ref | Type / State | Why it matters |
|---|---|---|
| SF **23-00921160** | Closed (2023) | **Same client + same ED 11014**; Quorum diagnosed missing recipients in the Contacts tab. The "solution Quorum found before" the customer references. |
| SF 26-01084250 (Pembina) | Closed | "Not receiving" fixed by adding the **event-notification type to the security group**. |
| SF 26-01080390 (MountainWest) | Closed | Fixed by **turning on the event detector for email**. |
| SF 26-01067520 (EQT) | Closed | Recipient already existed (PK violation) — "added but not showing." |
| ADO **#1756997** | Bug / Closed | QPTM/Notifications CAX_14 cut report → **only impacted operators** now notified (`m_Sel_NotifyOperators`). Fixed 2024.04.1.42 / 2025.04.1.12 / 2025.10.1.2 / 2026.04.1.0. Drives **H2**. |
| ADO **#113963** | Bug / Closed | Documents the **BP+TSP-tie** recipient-resolution rule (fixed 2019.07.1.1, QLNG). Drives **H1** mechanism. |

### Diagnostic SQL (DB MCP unavailable from this machine — hand to an engineer with PRD read access)
> Table/column names below are **placeholders** following `QARCH_EVENT_DETECTOR*` conventions. **Verify each against Tallgrass's schema** by code-searching `EVENT_DETECTOR` in the client's `<CLIENT>.QPTM.Database` migration before running. SQL-Server date syntax shown; use `SYSDATE-30` on Oracle.

```sql
-- (1) Configured recipients on ED 11014: active + has email?
SELECT r.EVENT_DETECTOR_NO, r.RECIPIENT_NO, r.USER_NO,
       u.USER_NAME, u.EMAIL_ADDRESS /*?*/, r.ACTIVE_FLAG /*?*/, r.RECIPIENT_TYPE /*?*/
FROM   QARCH_EVENT_DETECTOR_RCPT r
JOIN   QARCH_USER u ON u.USER_NO = r.USER_NO
WHERE  r.EVENT_DETECTOR_NO = 11014
ORDER  BY r.RECIPIENT_NO;
-- Any recipient inactive or with NULL/blank email is a config gap (H1).

-- (2) DECISIVE: configured recipients with NO queue row in the last 30 days (the actual "missing 2")
SELECT r.USER_NO
FROM   QARCH_EVENT_DETECTOR_RCPT r
WHERE  r.EVENT_DETECTOR_NO = 11014
  AND NOT EXISTS (
        SELECT 1 FROM QARCH_EVENT_NOTICE_QUEUE q
        WHERE q.EVENT_DETECTOR_NO = r.EVENT_DETECTOR_NO
          AND q.USER_NO = r.USER_NO
          AND q.TRIGGER_DATE >= DATEADD(DAY,-30,GETDATE()) );
-- USER_NOs here = configured but never enqueued -> cause is UPSTREAM of the queue
-- (recipient never resolved). Then decide H1 vs H2 with (3) + (4).

-- (3) BP/TSP tie on the BA Contact screen vs the detector's TSP (the #113963 filter)
--     Confirm join key + the BA-contact-TSP link table name first.
-- SELECT r.USER_NO, ed.TSP_NO AS ed_tsp, bct.TSP_NO AS contact_tsp,
--        CASE WHEN bct.TSP_NO IS NULL THEN 'NO TSP on BA Contact -> filtered out'
--             WHEN bct.TSP_NO <> ed.TSP_NO THEN 'TSP mismatch -> filtered out'
--             ELSE 'OK' END AS diagnosis
-- FROM QARCH_EVENT_DETECTOR ed
-- JOIN QARCH_EVENT_DETECTOR_RCPT r ON r.EVENT_DETECTOR_NO = ed.EVENT_DETECTOR_NO
-- LEFT JOIN <BA_CONTACT_TSP link> bct ON bct.USER_NO = r.USER_NO AND bct.BP_NO = ed.BP_NO
-- WHERE ed.EVENT_DETECTOR_NO = 11014;

-- (4) Security-group grant for ED 11014's event-notification type (the Pembina 26-01084250 pattern)
--     FUNCTION_CODE / notice-type code is the least-certain placeholder; confirm it for ED 11014.
SELECT u.USER_NO, u.SEC_GROUP_NO, g.SEC_GROUP_NAME, gr.FUNCTION_CODE, gr.GRANTED_FLAG
FROM   QARCH_USER u
LEFT JOIN QARCH_SEC_GROUP g  ON g.SEC_GROUP_NO = u.SEC_GROUP_NO
LEFT JOIN QARCH_SEC_GROUP_GRANT gr
       ON gr.SEC_GROUP_NO = u.SEC_GROUP_NO AND gr.FUNCTION_CODE = '<ED_11014_NOTICE_TYPE>'
WHERE  u.USER_NO IN ( /* the 2 missing USER_NOs from query (2) */ );
```

### Next steps
1. **Identify which report ED 11014 drives and confirm Tallgrass's QPTM build** against the #1756997 fix lines (2024.04.1.42 / 2025.04.1.12 / 2025.10.1.2 / 2026.04.1.0). This decides whether **H2 (expected behavior)** is even in play.
2. **Run query (2)** — did the 2 recipients ever get an Event Notice Queue row? *No row* ⇒ never resolved (H1 or H2). *Rows exist but no mail* ⇒ SMTP/email-format, not this case.
3. If no row: was there an actual **cut/reduction on those 2 recipients' locations** in the affected cycles? **Yes + still no row ⇒ H1 config gap** → run (1)/(3)/(4) to find which filter dropped them (inactive, no email, BP/TSP tie missing, not on Contacts tab, or security-group grant missing — the 23-00921160 / Pembina pattern). **No cut on their locations ⇒ H2 expected behavior** → educate customer.
4. If recipients are fully configured AND a cut occurred AND still no queue row → escalate as a **new** defect (fresh investigation; do not reuse #1756997 / #113963).
5. Reply to customer (draft below).

### Notes / limitations
- Case has **13 attachments** (incl. "DCP Event 11014", "Koch not receiving their Event Detector 11014", "Case 26-01093642 Before Walkthrough", recipient-setup screenshots) and **no SF email/comment records** exposed via the connector. Attachment **binaries are not retrievable** through the SF MCP (VersionData returns an authenticated URL, not bytes) — review the Word/PNG attachments in Salesforce directly; they likely already show the 2 recipients' setup and resolve H1 vs H2 quickly.
- Event-detector table names above are from prior L4 work (EQT 26-01067755) and #113963's QLNG variant — **verify against the Tallgrass `*.QPTM.Database` EVENT_DETECTOR migration** before relying on column names.


---

## Case 26-01109441 — TIPS/Hess: Unable to add PPAs to the reprocessing of 6/2024 (posted-period block)

**Investigated:** 2026-07-02 · **Product:** TIPS · **Account:** Hess Corp. · **Owner:** Aditya Bhagat · **Status:** In Progress (customer-deprioritized to Low) · **Version:** Production on the **2025.04** line · **Repro env:** AHS_DEVA1 (Nicky Grewal walkthrough).

### Issue
On **Monthly > PPA Approval** (Company 057 HESS BAKKEN INVESTMENTS II, Facility **TIOGA GAS PLANT 330**), Hess sets Activity = **"Rerun – Update Measured Volume Only"** on two meters (**975182**, **975473**) for prod date **6/1/2024** and clicks Update. It fails:

> **#1** "PPAs cannot be approved when the production date has been posted. Production date 06-01-2024 has already been posted for Accounting date 08-01-2024."

The same activity change **succeeds** for 9/2024 PPAs, and adding 6/2024 as a rerun month in Accounting Date Maintenance **did not help**. A workaround attempt on **Input Prices > Measured Volumes** hit a second error:

> **#2** "Meter '975182' is an Internal meter and the volume record cannot be modified in TIPS." — even though Meter Definition shows Meas. Source = **EXTERNAL || E** (effective 4/1/2025).

Customer's real question: *"why is this happening — we'll have PPAs in Sept–Dec."*

### Classification
**Expected Behavior (working as designed) — Config/Data**, both errors. No code defect. A product **enhancement** is defensible but optional. This is a full code trace, not a string match — every symbol below was read from live ADO source and re-verified by an independent adversarial pass.

### Root cause — ERROR #1 (the actual blocker), code-verified
The PPA-Approval posted-date guard is **conditional on posting state, not on activity type**. In `QVpPPAApproval_MeasVol::ValidateMandatory` (comment `//Issue: 96765`):

- **`Quorum.TIPS.ClassicGUI` → `/Native/QTipsCoreMonthly/QVpPPAApproval_MeasVol.cpp:264-278`** loops over `GetDetailData()->GetModifyNewArray()` (changed rows only — that's why editing the Activity column triggers it) and blocks when `pParentWndM->IsPPAPosted(dtProdDt, &dtAcctDt)` returns true.
- **`IsPPAPosted` — `QVpPPAApproval.cpp:1196-1208`** is a pure map lookup: key = `ACCT_DT@PROD_DT` against `m_PPAPostedMap`.
- The map is built in **`PreUpdateValidate` (`QVpPPAApproval.cpp:1152-1191`)** from registered query **`Select_ProdDt_For_Posted_PPA` (`QQryReg_PPAApproval.cpp:74-78`)**:
  ```sql
  SELECT * FROM QTRAN_PLANT_STATUS_UNIQUE_VW
  WHERE POSTED_IND = 1 AND PLANT_NO = @0PLANT_NO AND UNIT_TM_CD = 'M'
  ```
- The query and the guard **never reference `ACTIVITY_CD` or `RERUN_IND`.** The gate keys purely on `QTRAN_PLANT_STATUS_UNIQUE_VW.POSTED_IND = 1` (monthly) for the plant. (`QTRAN_PLANT_STATUS_UNIQUE_VW` = `SELECT * FROM QTRAN_PLANT_STATUS WHERE PATH_NO = 'ALL'`.)
- **The .NET Web path is functionally identical:** `Quorum.TIPS.Web → /Quorum.TIPS.Validation/PpaApproval/ValidationRules/QTIPSValidationPpaApproval001_MeasVolPPAApprove.cs:32-44` + base rule `QTIPSValidationPpaApprovalBase.cs:17-40,46-62` — same `IsPosted==true` + `UnitTmCode==Monthly` filter, same `AcctDate|ProdDate` key, changed rows only, no activity branch. (The `ActivityCode` argument in `AddError` only names the grid column to attach the error to — it is not a condition.)
- **No unit test** in `PpaApprovalUnitTest.cs` combines a Rerun activity with a genuinely posted period through the live rule — consistent with this edge going unnoticed.

### Why 6/2024 fails but 9/2024 succeeds (the customer's question)
- **6/2024** production has already been posted → there is a `QTRAN_PLANT_STATUS` row with `POSTED_IND=1, UNIT_TM_CD='M', PROD_DT=06/01/2024, ACCT_DT=08/01/2024`. Its key `08/01/2024@06/01/2024` is in the posted map → `IsPPAPosted` = true → **blocked**. (The "Accounting date 08-01-2024" in the message is simply the `ACCT_DT` stored on that posted row — printed for context, not a comparison.)
- **9/2024** production has **not** been posted → no `POSTED_IND=1` row → key absent → guard passes → the identical "Rerun – Update Measured Volume Only" change **saves**.
- **Adding 6/2024 as a rerun month didn't help** because that only sets `RERUN_IND=1` on `QCTRL_CURRENT_ACCT_DT_PROD_DT` (feeding a *separate* "rerun in progress" path, `m_bInRerunDoNotApprove`). The posted-date guard never reads `RERUN_IND`, so the `POSTED_IND=1` row still matches and still blocks. **The only way to clear this gate is to reverse/un-post the 6/2024→08/2024 posting (reopen the period).**

### Root cause — ERROR #2 (the workaround dead-end), code-verified
"Internal meter … cannot be modified in TIPS" is an **unrelated** validation on the Measured-Volumes edit path, gated by config key `INTEGRATION / RESTRICT_INTERNAL_METER_UPDATE` (default false; ON in Hess's env):
- **`Quorum.TIPS.ClassicGUI → /Native/QTipsCoreMonthly/QVpMeasuredVolume.cpp:74-75,860-867`** → `QMeterValidator::IsInternal(plant, mtr, dtProdDt)`.
- **`/Native/GatheringShared/QMeterValidator.cpp:125-162`** resolves the meter row **as-of the production date** via `Validate_MeterWithEffectiveDate` (`QQryReg_Meter.cpp:51`: `... WHERE EFF_DT_FROM <= @1EFF_DT_FROM AND EFF_DT_TO >= @1EFF_DT_FROM`, bound to the prod date), reads that row's `MEAS_SRC_CD`, then `SELECT INTERNAL_IND FROM QCODE_MEAS_SRC WHERE MEAS_SRC_CD = ...`.
- **The contradiction resolves as an as-of-date lookup:** the EXTERNAL source you see is effective **4/1/2025** — a *different, later* `QCTRL_METER` row. For a **6/1/2024** volume the effective row's `MEAS_SRC_CD` still has `INTERNAL_IND=1`. It is Measurement Source (not Accounting Meter Type, not a cache), just resolved for the wrong period. (Web mirror: `QMeterValidator.cs:43-56` → `GetSingleMtrBetweenDates` → `MeasSrcDO.IsInternal`.)

### Corrections to the prior automated analysis (the HTML attached to the case)
The attached "Case Analysis – 26-01109441" was **string-search only and never read the code**; three of its conclusions are wrong or imprecise:
1. **"Guard fires unconditionally for all activity types" → WRONG.** It is conditional on `POSTED_IND`. Activity type is irrelevant; the discriminator is per-month posting state. (This is what actually explains 9/2024-works vs 6/2024-fails — which the "unconditional" story cannot.)
2. **Error #2 = "session-state / needs re-query" → WRONG.** It is an **as-of-production-date** meter-source resolution. The External toggle must be **effective on/before the production month** being edited (4/1/2025 doesn't cover 6/2024).
3. **[1690828] "possible compounding defect / check Hess's build" → CLOSED, not applicable.** [1690828] is a **batch ALLOCHECK** stored-proc fix (`QPIBN_INIT_BATCH_CHK_ALLOCATE`, repo `Quorum.TIPS.Database`, PR 101726; shipped 2024.04.1.11 / 2024.10.1.1 / **2025.04.1.0**) — a different code path from the approval-screen guard. Hess is on **2025.04**, so they already have it, and it does not touch this guard.

### Correct workaround (if 6/2024 volumes must be edited manually)
The toggle workaround only works if the meter is EXTERNAL **as of the production month**. For each affected meter:
1. Meter Definition → add/adjust a `QCTRL_METER` effective slice so **Meas. Source = EXTERNAL is effective on/before 6/1/2024** (not 4/1/2025). Save.
2. Input Prices > Measured Volumes → re-query meter/prod date 6/1/2024 → set/override Qty → save.
3. **Revert** the meter's Measurement Source back to its correct (Internal) value for that period — **mandatory**; leaving it External corrupts subsequent allocation runs.
4. Re-run the month.

But note this edits *volumes*; it does **not** clear the ERROR #1 posted-period block on PPA Approval. To actually re-approve/rerun 6/2024 PPAs, the **6/2024→08/2024 posting must be reversed/reopened** so `POSTED_IND` no longer matches — the rerun-month flag alone cannot bypass `IsPPAPosted`.

### Confirm on data (DB MCP is blocked from this machine — run in AHS_DEVA1 / PRD)
```sql
-- ERROR #1: is 6/2024 posted (and 9/2024 not)?
SELECT PLANT_NO, PROD_DT, ACCT_DT, UNIT_TM_CD, POSTED_IND, FIRST_APPROVED_IND, RERUN_IND, ARCHIVE_IND, PATH_NO
FROM   QTRAN_PLANT_STATUS
WHERE  PLANT_NO = '330' AND UNIT_TM_CD = 'M'
  AND  PROD_DT IN (DATE '2024-06-01', DATE '2024-09-01')
ORDER BY PROD_DT, ACCT_DT;                 -- expect POSTED_IND=1, ACCT_DT=2024-08-01 for 6/2024; none for 9/2024

-- current open PPA accounting month + any rerun designations
SELECT ACCT_DT, OPEN_IND, PPA_IND, PLANT_NO, CO_CD FROM QCTRL_CURRENT_ACCT_DT WHERE PPA_IND = 1 AND OPEN_IND = 1;
SELECT p.PROD_DT, p.RERUN_IND FROM QCTRL_CURRENT_ACCT_DT a
  JOIN QCTRL_CURRENT_ACCT_DT_PROD_DT p ON a.SEQ_NO = p.SEQ_NO WHERE a.OPEN_IND = 1;

-- ERROR #2: which meter slice is effective for 6/2024, and is that source Internal?
SELECT MTR_NO, EFF_DT_FROM, EFF_DT_TO, MEAS_SRC_CD FROM QCTRL_METER
WHERE  PLANT_NO = '330' AND MTR_NO IN ('975182','975473')
  AND  EFF_DT_FROM <= DATE '2024-06-01' AND EFF_DT_TO >= DATE '2024-06-01';
SELECT MEAS_SRC_CD, INTERNAL_IND FROM QCODE_MEAS_SRC;   -- expect INTERNAL_IND=1 for the 6/2024 code
```

### Recommendation
1. **Answer Hess (working as designed):** the block is because **6/2024 is already posted** (to accounting 08/2024). Reruns are gated on posting state, not on the activity type, so a "Rerun – Update Measured Volume Only" flag can't bypass it and neither can designating 6/2024 a rerun month — those don't un-post the period. The reason 9/2024 works is that it isn't posted yet. **Prevention for Sept–Dec:** perform any needed reprocessing **before** each month is posted; once posted, the period must be reopened/un-posted to rerun. No code fix is required.
2. **Optional enhancement (ready-to-paste ADO):**
   - **Title:** PPA Approval — allow "Rerun – Update Measured Volume Only" on posted production months (exempt from the `IsPPAPosted` block, or add a permission-gated reopen path)
   - **Type:** Enhancement · **Product:** TIPS · **Area:** Maintenance\Midstream and Transportation
   - **Problem:** The posted-period guard (`Issue: 96765`) in `QVpPPAApproval_MeasVol::ValidateMandatory` blocks *all* changed rows whose `(ACCT_DT, PROD_DT)` is posted (`QTRAN_PLANT_STATUS_UNIQUE_VW.POSTED_IND=1`), with no exemption for rerun activities and no read of `RERUN_IND`. Clients reprocessing a historical month that has since been posted have no supported in-product path.
   - **Proposed fix:** branch the guard on PPA Activity — exempt `R` / "Update Measured Volume Only" from the `IsPPAPosted` block (or route to a permission-controlled reopen). Must be applied consistently across **all four** `QVpPPAApproval_*.cpp` variants (MeasVol, Meter, Contract, UDEF) **and** the Web rule `QTIPSValidationPpaApproval001` + base. Keep the block unconditional for *new* PPA creation on posted periods. Add unit coverage for Rerun-against-posted (currently none).
   - **Files:** `Quorum.TIPS.ClassicGUI /Native/QTipsCoreMonthly/{QVpPPAApproval_MeasVol.cpp:264-278, QVpPPAApproval.cpp:1152-1208, QQryReg_PPAApproval.cpp:74-78}` · `Quorum.TIPS.Web /Quorum.TIPS.Validation/PpaApproval/ValidationRules/{QTIPSValidationPpaApproval001_MeasVolPPAApprove.cs:32-44, QTIPSValidationPpaApprovalBase.cs:17-62}`
3. **No prior Hess precedent** for this mechanism: of 26-01089308 / 26-01087709 / 26-01071255 / 25-01050878, the closest (26-01089308) was a duplicate SPLIT allocation-group timeline (config), not the posted-period approval block.

### Files (code-verified via ADO)
- `Quorum.TIPS.ClassicGUI` — `/Native/QTipsCoreMonthly/QVpPPAApproval_MeasVol.cpp` (264-278), `QVpPPAApproval.cpp` (1152-1208), `QQryReg_PPAApproval.cpp` (74-78)
- `Quorum.TIPS.ClassicGUI` — `/Native/QTipsCoreMonthly/QVpMeasuredVolume.cpp` (74-75, 860-867), `/Native/GatheringShared/QMeterValidator.cpp` (125-162), `QQryReg_Meter.cpp` (51), `QTipsUtility.cpp` (GetCurrentPPAAcctDt ~670)
- `Quorum.TIPS.Web` — `.../QTIPSValidationPpaApproval001_MeasVolPPAApprove.cs` (32-44), `QTIPSValidationPpaApprovalBase.cs` (17-62), `QMeterValidator.cs` (43-56), `.../QTIPSValidationMeasuredVolume0001_RestrictInternalMeter.cs` (15-18), `Strings.resx` (key `VALIDATE_PPAAPPROVAL_POSTED_REC`)
- `Quorum.TIPS.Database` — `/Common/MSSQL/Views/QTRAN_PLANT_STATUS_UNIQUE_VW.sql`
- ADO **[1690828]** (Bug/Closed, batch ALLOCHECK, PR 101726) — related domain, **not** this fix.

---

## Case 26-01106039 — EQT/Equitrans: LPS-F "PPA does not generate billing adjustment" (missing DB object `BLSTAG_PAL_EXT`)

**Customer:** EQT Corporation (EQC / Equitrans) · **Product:** QPTM · **Owner:** Aditya Bhagat · **Priority:** Medium · **Opened:** 2026-06-08 · **ADO:** #1836277 (Bug, Proposed) · **Investigated:** 2026-07-07

### Issue
Park-and-Loan (Type of Service **LPS-F**, "Service Lending and Parking Service – Financial") contracts on **TSP 24 and 241** complete the whole PPA lifecycle — retro nom → reallocation → PPA record → PAN "processed" → shows on Customer Account Main — but **no daily parking-charge billing adjustment is generated**. Customer manually calculates the daily charge from the revised daily ending imbalance and enters an LGA on the contract. Reproduced in DEV/UAT/PRD. Screenshot (invoice 260675, contract 1269.2278): PMA/imbalance change = **114 dth**, **Adj = 0**.

### Classification
**Code / DB-deployment defect (missing database object in the client environment).** Not customer-config; not a missing code branch. The invoice-generation code path exists and is correct — it fails because a required staging object is absent from EQC's schema.

### Root cause — source-verified
Invoice Generation (`BLINVGEN`) runs the PAL daily invoice-document SQL, which references staging object **`BLSTAG_PAL_EXT`** ("Billing STAGing – PAL EXTension"). That object **does not exist in EQC DEV/UAT/PRD**, so the batch throws SQL 208 *"Invalid object name 'BLSTAG_PAL_EXT'"* → *"PAL statement records were not successfully inserted"* → no billing line is written and no adjustment appears.

ADO #1836277 (LeWebster Lacy, 2026-07-01) captured the exact batch error:
```
[COM Error] File: QFCCPPBatchCore\QADOCommand.cpp, Line 1287, OLE DB, Description: Invalid object name 'BLSTAG_PAL_EXT'.
[ADO Error] -2147217865  SQLState 42S02  NativeError 208
Error in registered SQL: QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY
PAL statement records were not successfully inserted. / CreateNewData function failed.
Host: QDDDEVSQL04.QDEV.NET\SQL2017    Found-in version: 2024.04 (MSSQL)
```
Jimmy Nguyen (bug comments): *"The object doesn't exist in UAT either. The last script that ran was a DROP VIEW script from version 3.0.00 in QPTM"* … *"review with DevOps if the object is needed and if it is, is it a CORE change or a client-specific change, then go through the CORE DB Changes to get it integrated."* → **the fix is stuck on the CORE-vs-client decision.**

### Execution path (code-verified)
`BLSTAG_PAL_EXT` is the staging table for the **PAL Extension** daily park-and-loan billing feature. Comment (verbatim): *"a record for each activity day for each PAL inventory account that contains that day's PAL extension … write the records from BLSTAG_PAL_EXT where the PAL day count equals the PAL extension period into BLTRAN_INVOICE_GEN_QTY."*

1. **Populate** — `CalcPALExtension` writes one row/activity-day/inventory-account into `BLSTAG_PAL_EXT` (cols: TSP_NO, PROCESS_QUEUE_ID, INV_ACCT_ID, PROD_MTH, ACTIVITY_DT, ACCT_BAL, PAL_EXT_PERIOD, EXT_DAY_COUNT, …; archive group STAG_CORE, PK_BLSTAG_PAL_EXT). Code: `QPSCalcPALExtension.cpp` / `QSQL_CalcPALExtension.cpp`.
2. **Bill qty** — `INSERT INTO BLTRAN_INVOICE_GEN_QTY … SELECT … 'PEX' CHARGE_BASIS_CD … FROM BLSTAG_PAL_EXT PAL … WHERE PAL.EXT_DAY_COUNT = PAL.PAL_EXT_PERIOD` (charge basis **PEX** = PAL Extension).
3. **Invoice doc** — CORE `QPSGenerateDocuments.cpp`: `LEFT OUTER JOIN BLSTAG_PAL_EXT D …`, gated by config `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` and `PALDailyOrMonthly` ("DAY" → member `QSQLID_GenerateDocuments::m_INS_SEL_INVOICE_DOC_PAL_DAY`, the registered SQL in the error). ← **fails here for EQC.**

Repos/files:
- CORE `Quorum.QPTM.ClassicBatch` — `/QPDllPipelineMgrBL/QPSGenerateDocuments.cpp`, `/QPDllPipelineMgrBL/QSQL_GenerateDocuments.cpp` (registered SQL `m_INS_SEL_INVOICE_DOC_PAL_DAY`).
- `DTE.QPTM.ClassicBatch` (client) + `Quorum.QLNG.ClassicBatch` (TerminalMgr) — `QPSCalcPALExtension.cpp` / `QSQL_CalcPALExtension.cpp`.
- `Quorum.QDBManager` — QPTM build **3.1.00.0069** release scripts (ST# 50950 / 50552, orig. David Blanco) **DROP** `BLSTAG_PAL_EXT` as both **TABLE** (`..._CORE_QPTMSCR_04_62349.sql`) and **XMOD_VIEW** (`..._CORE_QPTM_15/16_62349.sql`) and remove its `UTIL_VIEW_SOURCE_LIST` / `QARCH_CTRL_ARCHIVE_DEFINE` entries.
- **No CREATE (table or view) for `BLSTAG_PAL_EXT` exists in any indexed repo** (incl. `EQC.QPTM.Database`). It was historically a STAG_CORE staging table (since 2011) that a QPTM 3.x cleanup dropped; the recreate never landed for EQC. It has appeared in the wild as a base TABLE (DTE/DTM schema: `PK_BLSTAG_PAL_EXT`) and, in one release path, as a client X-mod VIEW — the ambiguity behind the CORE-vs-client question.

### Corrections to the prior automated Case Analysis (HTML on the case, 2026-06-08)
- It guessed the missing write target was `BLSTAG_INVOICE_PPA_CTR` and hypothesized *"BLINVGEN has no code path for DPC charge basis / LPS-F."* **Both are wrong.** The code path exists; the failure is a **missing DB object** `BLSTAG_PAL_EXT` (SQL 208). The relevant charge basis is **PEX** (PAL Extension), not DPC (DPC is the separate demand/parking charge that *does* bill — the $1,858.41 line).
- It stated *"ADO Ticket: None logged."* An ADO bug now exists: **#1836277** (logged 2026-07-01).

### Related history
- **25-01058356** (prior case, same subject) — opened 2025-12-03, **Closed 2026-06-08**; transferred into this non-project case exactly as the description says.
- **#1638997** "DTE – IBS PAL Extension Fee Count Error" (Closed, *Client Specific*) — DTE exercises this same PAL-extension billing path with `BLSTAG_PAL_EXT` present; confirms the feature works when the object exists.

### Fix
1. **Engineering/DevOps decision (the blocker):** is `BLSTAG_PAL_EXT` a CORE object or client-specific? Evidence points to a **STAG_CORE staging TABLE** (runtime `QADORSetWriterDB` INSERTs into it; DTE/DTM carry it as a base TABLE with PK). Recommend **re-create it as the base staging table via the CORE DB Changes process**, matching the DTE/DTM definition (STAG_CORE column set + `PK_BLSTAG_PAL_EXT`), and re-register its archive/view-source entries the 3.1.00.0069 scripts deleted.
2. Deploy to **EQC DEV → UAT → PRD**.
3. Re-run **CalcPALExtension + Invoice Generation ("Run All PPAs")** for the affected LPS-F months (May 2026 forward on TSP 24 & 241) to generate the retroactive billing adjustments — **coordinate volume/timing with EQT first**.
4. Confirm `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` and `PALDailyOrMonthly=DAY` are the intended EQC settings (they are what triggers the path).

### Immediate workaround (in place)
Manual: calculate the daily parking charge from the revised daily ending imbalance and enter an LGA on the contract, per affected contract on TSP 24 & 241. Functional but fully manual — revenue-accuracy/audit risk while unresolved (defect open since Dec 2025).

### Notes / limitations
- DB MCP is blocked from this machine; the "object missing in EQC" state is confirmed by the ADO batch error + Jimmy Nguyen's DEV/UAT/PRD checks rather than a direct query. To confirm on data: `SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT')` in EQC PRD (expect NULL), and check `BLTRAN_PPA_EVENT` / `BLTRAN_INVOICE_GEN_QTY` for contract 1269.2278, prod month May 2026.
- Exact source line numbers can be pulled on request for the ADO write-up (repos/files/symbols above are verified).

### Resolution update (found 2026-07-09) — fix is a DB-object deploy, already proven in DEV
The "solution already in production" claim checks out: `BLSTAG_PAL_EXT` **exists in other instances/production**, so the fix is to replicate the object — not to write code.

- **WI 1836447** (myQuorum Cloud › Data Services, *Request Global Cloud Ops*, Closed/Successful 2026-07-02): refreshed `EQC_DEV17MID` from **`EQC_PRD1715MID`**. DEV still threw the `BLSTAG_PAL_EXT` error afterward → confirms **PRD is also missing the object** (and, per LeWebster, "all the QPTM configs" were missing in the refreshed DEV).
- **WI 1836679** (myQuorum Cloud › DevOps, Closed/**Successful** 2026-07-06, "EDC.DEV17MID – DB Error BLSTAG_PAL_EXT"): **Resolution = "Inserted `BLSTAG_PAL_EXT` from a different instance."** Done by DevOps (Timothy Zhou / Kevin Pitsenbarger) with LeWebster Lacy / Desiree Martin. Attachment `EQC DEV DB Configs_1836679.docx` lists the missing configs. This fixed **DEV only** (`EQC_DEV17MID`), unblocking the walkthrough "After" test.
- No CREATE DDL for `BLSTAG_PAL_EXT` exists in the product source repos (confirmed again) — it survives only as a live object in instances that predate the QPTM 3.x drop. That's why DevOps copied it from another instance rather than running a product script.

**Current state (2026-07-09):**
- ✅ **DEV** (`EQC_DEV17MID`): object inserted, error cleared (WI 1836679).
- ❌ **PRD** (`EQC_PRD1715…`): **still missing** — customer's production billing still fails; Bug #1836277 still says "invalid object name in DEV **and PRD**" and is **Proposed/untriaged**. Any future DEV refresh from PRD will re-break DEV until PRD is fixed.

**Remaining actions:**
1. **Deploy `BLSTAG_PAL_EXT` (+ the other missing QPTM configs from the 1836679 doc) to EQC PRD** via a Cloud Ops Script Deployment — same "insert from an instance that has it" approach used for DEV.
2. **Formalize via Bug #1836277** so the object is added through CORE (or EQC-specific) DB Changes and survives future refreshes — resolve Jimmy Nguyen's CORE-vs-client question (evidence favors a STAG_CORE base staging table).
3. After PRD deploy, **re-run Invoice Generation ("Run All PPAs") for the affected LPS-F months** (May 2026 fwd, TSP 24 & 241) to emit the retroactive billing adjustments — coordinate invoice volume with EQT.
4. Have LeWebster complete the walkthrough **"After"** in the fixed DEV as verification evidence before the PRD deploy.

### Status check — 2026-07-23 (re-verified live)
- **SF case:** still **In Progress** (owner Aditya Bhagat; last modified 2026-07-22). No new customer comment/email since the 2026-07-14 survey-notice email — no fresh customer input, case not closed.
- **Bug #1836277:** still **Proposed / untriaged** — *zero* movement since 2026-07-02. Last comment is still Jimmy Nguyen asking DevOps to decide CORE-vs-client before integrating through DB Changes. **The fix has been stalled ~3 weeks on that triage decision.**
- **DEV (WI #1836679):** **Closed/Successful** 2026-07-06 (object inserted from another instance) — DEV only.
- **PRD:** **still missing `BLSTAG_PAL_EXT` → EQT production LPS billing still failing.** Customer remains on the manual-LGA workaround.
- **Drop re-confirmed in live source:** `Quorum.QDBManager` build **3.1.00.0069**, `..._CORE_QPTM_15_62349.sql` — `DROP VIEW dbo.BLSTAG_PAL_EXT` (objectClass `XMOD_VIEW`), plus deletes from `UTIL_VIEW_SOURCE_LIST` and `QARCH_CTRL_ARCHIVE_DEFINE`. Header: `SirTracker Issue: 50950`, `@VISSUEID=62349`, originator **David Blanco**. Config bypass key `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` confirmed present in `Quorum.QPTM.ClassicBatch/QPDllPipelineMgrBL/QPSGenerateDocuments.cpp` and `QARCH_CNFG_CTRL.json`.
- **Recommendation:** the CORE-vs-client question does **not** need to block PRD relief. Escalate #1836277 out of Proposed, and in parallel unblock EQT PRD now via **Option A** (Cloud Ops DDL deploy of the object from EQC_UPG/CORE_REL baseline — precedent WI #1836679) **or Option B** (flip `USE_DTE_BLRPTS_10_INVOICE_DOC_PAL`=0). Resolve CORE-vs-client separately as the long-term FluentMigrator fix. Then rerun Invoice Generation "Run All PPAs" for LPS-F months May 2026 → present on TSP 24 & 241.


---
---

# Case 26-01109441 — TIPS: Unable to add PPAs to reprocessing of 6/2024 PPA

**Date:** 2026-07-09 | **Product:** TIPS | **Client:** Hess Corp. (co 057 – Hess Bakken Investments II) | **Facility:** Tioga Gas Plant (plant 330)
**Status:** In Progress (owner: Aditya Bhagat) | **ADO:** none logged | **Classification:** Working as designed (process/config) — **not a code defect**

## What the customer hit
Trying to add two PPAs (meters **975182** AN-Evenson, **975473** HA-Grimestad) for **prod date 06/01/2024** on **Monthly > PPA Approval**, activity **"Rerun – Update Measured Volume Only"**. Two blocks:
1. **PPA Approval:** *"PPAs cannot be approved when the production date has been posted. Production date 06-01-2024 has already been posted for Accounting date 08-01-2024."* (Image 1)
2. **Input Prices > Measured Volumes** (their workaround attempt): *"Meter '975182' is an Internal meter and the volume record cannot be modified in TIPS."* (Image 2)

Nicky Grewal's DEV (AHS_DEVA1) testing: 9/1/2024 PPAs set to Rerun **succeed**; 6/1/2024 **fails**; **adding 6/2024 as a rerun month in Accounting Date Maintenance did NOT clear the error.**

## Root cause — verified in live `develop` source

**Block 1 — posted-date guard (Issue 96765).** All in `Quorum.TIPS.ClassicGUI`:
- `/Native/QTipsCoreMonthly/QVpPPAApproval_MeasVol.cpp` → `ValidateMandatory()` loops modified rows and calls `pParentWndM->IsPPAPosted(dtProdDt,&dtAcctDt)`; if true it emits the exact error and `return false`. **No PPA-activity-type check** — Rerun is treated identically to a new PPA.
- `/Native/QTipsCoreMonthly/QVpPPAApproval.cpp` → `PreUpdateValidate()` runs registered query `PPA_Approval/Select_ProdDt_For_Posted_PPA`, caching every posted `acct_dt@prod_dt` into `m_PPAPostedMap`; `IsPPAPosted()` blocks on a map hit.
- `/Native/QTipsCoreMonthly/QQryReg_PPAApproval.cpp` → the query reads **`QTRAN_PLANT_STATUS_UNIQUE_VW WHERE POSTED_IND = 1 AND PLANT_NO = @plant AND UNIT_TM_CD = 'M'`**. So "posted" = **`POSTED_IND = 1`** on the monthly plant-status row. Prod 6/2024 is posted (under acct 8/2024) → guard fires.

Why the rerun-month designation didn't help: the guard reads **`POSTED_IND`**, which the rerun-month flag in Accounting Date Maintenance does **not** clear. Why 9/2024 works: it isn't `POSTED_IND=1` yet.

**Block 2 — internal-meter volume guard.** In `Quorum.TIPS.Web`:
- `/Quorum.TIPS.Validation/MeasuredVolumes/ValidationRules/QTIPSValidationMeasuredVolume0001_RestrictInternalMeter.cs` blocks any changed measured-volume row where `QMeterValidator.IsInternal(PlantNo, MtrNo, ProdDate)` is true.
- `/Quorum.TIPS.Validation/Validators/QMeterValidator.cs` → `IsInternal()` loads the meter def **effective on the production date** (`GetSingleMtrBetweenDates(..., prodDate)`), reads its `MeasSrcCode`, and returns `QCODE_MEAS_SRC.INTERNAL_IND`. So it checks the **measurement source (`MEAS_SRC_CD → INTERNAL_IND`), NOT accounting meter type.**
- **Key nuance:** it reads the meter def effective **for 6/2024**, not today's record. Image 2 shows Meas. Source = EXTERNAL only because that record is effective **4/1/2025**; for prod 6/2024 the meter's meas src was **Internal**, so the guard correctly fires. (This — not "session-state re-query" as the prior auto-analysis guessed — is the real reason.)

## Solution

The system is behaving correctly: TIPS refuses a second PPA against a production month already **posted** in the active accounting period, and refuses manual volume edits on internal-source meters.

**Supported path (recommended) — reprocess in the current OPEN accounting month:**
1. Confirm the plant's active PPA accounting date. If it still sits on the posted month (08/2024), **roll it forward** (Accounting Date Maintenance / ROLLACCTDT) to the current open month. Once the active month is one where 6/2024 is not `POSTED_IND=1`, the PPA Approval guard clears and the 6/2024 rerun PPAs can be approved as prior-period adjustments that post in the open month.
2. For the two **internal-source** meters, their 6/2024 volumes cannot be hand-edited in TIPS. Either correct the volumes at the source and let the rerun pull them, or make the meter's **measurement-source effective-dated record External for the period being reprocessed** if volumes are genuinely maintained in TIPS.

**Confirmed workaround (customer already used for 6/2024) — fragile:** Meter Definition → set Meas. Source Internal→External (for the effective period covering the prod date) → save → Input Prices>Measured Volumes → re-query meter/prod date → set Qty → save → **revert Meas. Source to Internal** → save → re-run. The revert is mandatory; leaving it External corrupts later allocations. This edits volumes outside the PPA audit path, so prefer the supported path.

## Sept–Dec recurrence (customer's real question)
The block hits **any production month already `POSTED_IND=1` in the active accounting period.** To avoid it: do reprocessing while the target months are still in an **open** accounting period, or roll the accounting date forward and post the reruns into the current open month. "Designate as rerun month before posting" (the earlier suggestion) is insufficient once the month is posted — verified by Nicky's DEV test.

## Open items
- **Confirm Hess's TIPS build.** Related note **[1690828]** ("Rerun Production Month PPA Status…", batch ALLOCCHECK status-reset — a *different* code path) is reportedly first in ~2024.10.1.1 / 2025.04.1.0. If Hess is pre-that, the batch side may reset rerun PPA status to APP and prevent a clean reprocess even after the screen is unblocked. (Build values inferred from release notes — confirm before quoting.)
- **Enhancement (optional, backlog):** have `IsPPAPosted`/`ValidateMandatory` branch on PPA activity type to allow Rerun activities a controlled path on posted periods. Would touch all four `QVpPPAApproval_*.cpp` variants (MeasVol/Meter/Contract/UDEF) + .NET equivalents. Not required to resolve this case.

### Hotfix search (2026-07-14) — NO shipped hotfix exists; why UPG works; a shipped no-code bypass found
Exhaustive sweep (33 candidates, 12 adversarially verified — ADO work items all 3 projects, all 835 FluentMigrator migrations in Quorum.QPTM.Database, EQC.QPTM.Database client migrations, QDBManager release folders, ClassicBatch branch/commit history, wikis, EQC patch stream):

**1. No hotfix/patch/migration creates `BLSTAG_PAL_EXT`.** Zero CREATE DDL in any indexed repo/branch/commit. EQC's patch stream is ruled out decisively: Patch 15 on 2024.04 (WI 1767211, core hotfix 2024.04.1.39→1.41, DB pkg EQCM-MID-2024.04.QDBMgr.Package.15) was on UAT by 2026-03-12 (WI 1787912), yet #1836277 confirms the object still missing in UAT on 2026-07-02. Rejected look-alikes: WI 180797/SIRT 106950 (LPS/PAL PPA double-count → BLSTAG_INVOICE_CTR_DT dups, fixed QPTM 4.1 — different failure), #1638997/#1680461/#1635501 (DTE-only CalcPALExtension counter fixes in DTE.QPTM.ClassicBatch).

**2. Why UPG works = DB baseline lineage, not a fix.** EQC_HD_UPG17 (2024.04 GA + patches, MT 17.29.21) descends from the 2024.04 **fresh-install** core release DB `CORE_REL17MID_QPTM` (QHOUDB32\SQL02) via UBT (refresh WI 1721958 EQC_UPG ← EQC_UBT1715MID) — fresh-install baselines still contain `BLSTAG_PAL_EXT`. PRD/UAT are **in-place upgrades of the legacy Equitrans schema** that passed through QPTM 3.1.00.0069, whose script dropped it. Also proves the object can sit **empty** and billing works: core ships no CalcPALExtension step (DTE/QLNG only), so nothing populates the table at EQC — the LEFT JOIN just yields NULL DATE_DIFF.

**3. Shipped no-code bypass (code-verified, commit 0cc1cbce develop):** in `QPSGenerateDocuments.cpp` the BLSTAG_PAL_EXT join is only injected when config `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` = true (**coded default true when the row is absent** — likely why EQC errors). The else-branch runs the identical PAL-day SQL with `SEL_DATE_DIFF='NULL'`, `JOIN_DATE_DIFF=''` — no reference to the object. Setting that key to 0/false is a shipped code path that fully bypasses the missing table, with output identical to UPG's (DATE_DIFF NULL either way at EQC).

**PRD remediation options (either closes the customer issue):**
- **A. DDL deploy:** script `BLSTAG_PAL_EXT` out of `EQC_UPG17MID_QPTM` (or `CORE_REL17MID_QPTM`) into `EQC_PRD1715MID_QPTM` via Cloud Ops — exact precedent WI 1836679 (DEV, Successful 2026-07-06).
- **B. Config flip:** insert/set `QCTRL_CNFG_CTRL` KEY_GRP_NM='BILLING', KEY_NM='USE_DTE_BLRPTS_10_INVOICE_DOC_PAL' = 0 — no DDL, uses shipped code.
- Verify first (1 query each in PRD & UPG): `SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT')` and `SELECT * FROM QCTRL_CNFG_CTRL WHERE KEY_NM='USE_DTE_BLRPTS_10_INVOICE_DOC_PAL'` — tells you which mechanism makes UPG work and confirms EQC PRD state.
- **Long-term (Bug #1836277):** author a FluentMigrator migration in Quorum.QPTM.Database recreating the table (+ UTIL_VIEW_SOURCE_LIST / QARCH_CTRL_ARCHIVE_DEFINE registrations) so in-place-upgraded environments stop diverging from fresh-install baselines; column spec available from QPSCalcPALExtension.cpp and any healthy instance.
- After PRD fix: rerun Invoice Generation "Run All PPAs" for LPS-F months May 2026 fwd (TSP 24 & 241); use the now-working DEV/UPG for the walkthrough "After".

---

# Case 26-01112643 — CWCAPRTRAN fails on scheduled evening cycle, works on manual re-run
**Account:** Lighthouse Midstream Services, LLC (QCloud tenant **HPE**, pod **HPEP_HD_PRDA1** — historically Third Coast Midstream) | **Priority:** High | **Status:** In Progress | **Investigated:** 2026-07-21
**Chain (7-month recurrence, never resolved):** 25-01047412 ("17 CWCAPRTRAN ERRORS", closed No Action) → 25-01057583 (closed No Response 2026-06-30) → **26-01112643**. PRD PQIDs on case: 36291964, 36304053.

## Classification: **Configuration** (schedule/metadata gap) — NOT a code defect, NOT cycle-timing, NOT orphan CR data.

## Decisive evidence — actual message log (case attachment "CWCAPRTRAN Error".xlsx = QARCH_PROCESS_MSG_LOG export, UAT run PQID 35454685):
- **Step CWTRANXML:** `QXMLEXPORT::EXPORTANXMLFILE: COULD NOT OPEN THE FILE \QCUSHDFS501\QFC17$\HPE\HPEP_HD_UATA1\APPFILES\IPWS\CAPREL\CWCAPRTRAN.XML TO WRITE THE XML` (QXMLEXPORT.CPP:230)
- **Step SFTP_D:** `NO SUCH HOST IS KNOWN ... SFTP SERVER N/A` / `FAILED TO CONNECT TO SFTP SERVER N/A` / `NO PASSWORD OR PRIVATEKEY` → `QPSSFTP FAILED EXECUTE` → `CONTINUE ON FAIL = FALSE ... PROCESS WILL STOP`
- **UAT Setup doc (case attachment):** third error `COULD NOT FIND A DEFINITION FOR CWCRXML;CWCRXML2;CWCRXML3`; fix steps = add XML I/E def **CWCRXML3**, set file path, set **FTP Transfer ID CWCAPREL** local path, **unhide the IMPORT/EXPORT ID parameter** on batch process CWCAPRTRAN, **attach the XML ID to the Schedule Definition**.

## Root cause
The **scheduled** invocation of CWCAPRTRAN does not carry the **Import/Export (XML) ID** linkage a **manual** Batch Process Execution run supplies → scheduled run can't resolve the CWCRXML/CWCRXML2/**CWCRXML3** XML export definition (or resolves to a blank path) → CWTRANXML can't open/write `CWCAPRTRAN.XML`; the CWCAPREL SFTP step then fails/stops. Manual run works because the operator picks the Import/Export ID interactively.
- Corroboration: **ADO #1595701** — scheduled CW* jobs (incl CWCAPRTRAN) routinely missing `QARCH_CTRL_PROC_SCHED_PARAM` PARAM_IDs **26004 & 26853**. **#1766101** (HPE PRDA1) — correct CAPREL path is `\QCPHPEFSZA02\QFC17$\HPE\HPEP_HD_PRDA1\APPFILES\QPTM\EXPORTS\IPWS\CAPREL` (UAT doc path omitted the `\QPTM\Exports\` segment). **#1667238** — HPE PRD CAPREL FileNotFound. Pipeline step (from #1692301): CWCAPRTRAN step **TRANSENDCR** "Transfer CR Trans Data to IPWS".

## CORRECTION to prior auto-RCA (Case Analysis 26-01112643, 2026-07-07)
That RCA was explicitly blocked on the message-log text and guessed (A) CurrentCycleAssignment() cycle-timing and (B) unconditional CWRPTS_CR_POSTING DELETE / orphan data — and declared "File I/O ruled out" after reading only QPSCapRelTransRpt.cpp (the DB report-gen step). The actual log shows the failure is entirely at the **XML-export (CWTRANXML) + SFTP (SFTP_D)** output steps it never examined. Both prior hypotheses are unsupported.

## Fix (Config)
1. **Confirm branch:** `SELECT PROCESS_QUEUE_ID,SEQ_NO,MSG_TYPE_CD,MSG_TEXT FROM QARCH_PROCESS_MSG_LOG WHERE PROCESS_QUEUE_ID IN (36291964,36304053) ORDER BY 1,2;` (expect "COULD NOT FIND A DEFINITION" or "COULD NOT OPEN THE FILE"/SFTP — same as captured UAT log).
2. **Schedule/param (primary):** unhide **IMPORT/EXPORT ID** param on CWCAPRTRAN (correct env metadata layer); add the **XML ID** to the CWCAPRTRAN **Schedule Definition**; verify `QARCH_CTRL_PROC_SCHED_PARAM` for that SCHEDULE_ID carries the I/E ID (+ 26004/26853 per #1595701). Apply same to CWFIRMTRAN/CWINTRTRAN if co-scheduled.
3. **Def + path (secondary):** ensure XML I/E def **CWCRXML3** exists in-env; set its file path AND the **CWCAPREL** FTP transfer local path to the CAPREL folder **including `\QPTM\Exports\`**; verify CWCAPREL FTP connection has valid host + key/password (UAT showed "N/A"). Stale path after refresh → delete + re-add the path object (SKILL_Integration §8).
4. **Verify:** run scheduled CWCAPRTRAN ≥2 consecutive evening cycles; confirm XML lands in CAPREL and posts to IPWS.

**Not this symptom (output-correctness IPWS bugs on tenant, for reference):** dup #1739076/#1775918; missing/GAS_DAY-null #1774746/#1759366; multi-TOC feature #1728306. Infra variant to rule out if PQIDs show QUE/never-claimed: #1837718 (QMPLAUNCH worker-pool hang leaving CW* in QUE).
