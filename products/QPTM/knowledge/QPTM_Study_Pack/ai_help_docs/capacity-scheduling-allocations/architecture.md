---
title: Capacity Scheduling Allocations (CAS) - Architecture
category: architecture
feature: Capacity Scheduling Allocations (CAS)
related_repos: Web, Batch
keywords: CAS, architecture, code structure, services, batch processes, database tables, implementation
last_updated: 2025-12-11
---

# Capacity Scheduling Allocations (CAS) - Architecture

## Overview

This document explains the **technical architecture** of the Capacity Scheduling Allocations (CAS) system in QPTM. It covers code structure, service layer design, batch process implementation, database schema, and integration patterns.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Web Application Layer](#web-application-layer)
3. [Service Layer](#service-layer)
4. [Batch Process Layer](#batch-process-layer)
5. [Data Model](#data-model)
6. [Key Classes and Interfaces](#key-classes-and-interfaces)
7. [Processing Flow](#processing-flow)
8. [Rights Allocation Implementation](#rights-allocation-implementation)
9. [Integration Points](#integration-points)

---

## System Architecture

### Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB APPLICATION LAYER                     │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ CASummary      │  │ ViewModels      │  │ JavaScript/  │ │
│  │ Maintenance    │  │ (CASummaryVM,   │  │ UI Controls  │ │
│  │ Controller     │  │ CAScheduleVM)   │  │              │ │
│  └────────┬───────┘  └────────┬────────┘  └──────────────┘ │
└───────────┼──────────────────┼────────────────────────────┘
            │                  │
            ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │         QPTMSchedulingService (Main Service)            ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ - ClassifyNominations()                                 ││
│  │ - GetSummarySchedulings()                               ││
│  │ - DoPrelimCut()                                         ││
│  │ - SubmitSchedulings()                                   ││
│  │ - GetSchedulingHeader()                                 ││
│  └────────┬──────────────────────────────┬─────────────────┘│
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                        │
│  ┌──────────────────────┐  ┌────────────────────────────┐  │
│  │ TransGroupMgr        │  │ NomClassificationHelper    │  │
│  │ ReductionGroupMgr    │  │ NomDetailBalancingHelper   │  │
│  │ CapTypeMgr           │  │ PipelineModelMgr           │  │
│  └──────────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    BATCH PROCESS LAYER                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ QPSNomClassificationAndTransGroupingSeg                │ │
│  │ QPSSchedulingReductionSeg                              │ │
│  │ QPSStageOperationalAvailableCapacity                   │ │
│  │ QPSDefaultRoutePathAutomationSeg                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ CAScheduleHeader, CAScheduleObject, CAStagObjNomTransGrp│ │
│  │ CASummary, CANominationDetail, PARuleSet, PATransGroup│ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                        DATABASE                              │
│  CACTRL_SCHD_HDR, CACTRL_SCHD_OBJ_VW,                       │
│  CASTAG_OBJ_NOM_TRANS_GRP, CACTRL_SUMMARY,                  │
│  PACTRL_RULE_SET, PACTRL_TRANS_GRP                          │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Web Layer**: User interface for CAS summary maintenance, query, and submission  
**Service Layer**: Business logic orchestration, nomination classification, capacity calculations  
**Business Logic Layer**: Domain-specific algorithms (reduction, balancing, classification)  
**Batch Layer**: Automated processing (classification, reduction, OAC staging)  
**Data Access Layer**: Database operations, data object management  
**Database**: Persistent storage of CAS configuration and results

---

## Web Application Layer

### Controllers

#### CASummaryMaintenanceController

**Location**: `Quorum.QPTM.Web.Core/Controllers/CASummaryMaintenanceController.cs`

**Purpose**: Main web controller for CAS Summary Maintenance screen

**Key Methods:**

```csharp
public class CASummaryMaintenanceController : SchedulingControllerBase<QUIControllerCASummaryMaintenance, CASummaryMaintenanceRootVM>
{
    // Query CAS summary data
    public override IEnumerable<ActionItemVM> GetActions(string uiControllerId)
    
    // Execute actions (Query, Submit, Restart, PrelimCut)
    protected override ActionResult DoAction(string actionName, string uiControllerId)
    
    // Set read-only fields based on parameters
    [HttpGet]
    public JsonResult SetReadOnlyFields([QUIWebContextId]string id)
    
    // Determine flow direction for scheduling object
    [HttpGet]
    public JsonResult SetFlowDirection([QUIWebContextId]string id)
    
    // Query scheduling data
    [HttpPost]
    public ActionResult Query([QUIWebContextId] string id, CASummaryMaintenanceRootVM model)
    
    // Submit scheduled quantities
    [HttpPost]
    public ActionResult Submit([QUIWebContextId] string id, CASummaryMaintenanceRootVM model)
    
    // Perform preliminary capacity reduction
    [HttpPost]
    public ActionResult PrelimCut([QUIWebContextId] string id, CASummaryMaintenanceRootVM model)
}
```

**Actions Supported:**
- **Query**: Retrieve CAS summary data for gas day/cycle
- **Submit**: Submit scheduled quantities to TSP
- **Restart**: Re-run CAS classification and reduction
- **PrelimCut**: Apply preliminary capacity reduction
- **Report**: Generate CAS reports
- **LaunchSyncContract**: Synchronize contract data
- **LaunchSyncOutOfDateNom**: Synchronize out-of-date nominations

**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.CASMaintenanceSummary)]`

### View Models

#### CASummaryMaintenanceRootVM

**Location**: `Quorum.QPTM.Web.Core/ViewModels/CASummaryMaintenanceRootVM.cs`

**Properties:**
```csharp
public class CASummaryMaintenanceRootVM : QViewModelBase
{
    public DateTime? GasDay { get; set; }
    public string SchdObjTypeCode { get; set; }
    public int? IdCycle { get; set; }
    public string CASQueryOption { get; set; }
    public bool RatchetedEnabled { get; set; }
    public string ScenStatCode { get; set; }
    public string EngUomCode { get; set; }
    public string VolUomCode { get; set; }
    public string EbxInjectionWithdrawal { get; set; }
    public int? IdSubmitUser { get; set; }
    public DateTime? SubmitTime { get; set; }
    public bool IsAutoBalance { get; set; }
    public bool EnableCASPathBalancing { get; set; }
    public bool IsQueried { get; set; }
    
    // Grid data
    public IEnumerable<CASummaryVM> CASummary { get; set; }
}
```

#### CASummaryVM

**Location**: `Quorum.QPTM.Web.Core/ViewModels/CodeGen/CASummaryVM.cs`

**Key Properties:**
```csharp
public class CASummaryVM : QViewModelBase
{
    public short TspNo { get; set; }
    public DateTime GasDay { get; set; }
    public short IdCycle { get; set; }
    public string SchdObjId { get; set; }
    public string SchdObjTypeCode { get; set; }
    public string SchdObjNm { get; set; }
    public decimal RecQty { get; set; }           // Receipt nominated quantity
    public decimal DelQty { get; set; }           // Delivery nominated quantity
    public decimal RecSchedQty { get; set; }      // Receipt scheduled quantity
    public decimal DelSchedQty { get; set; }      // Delivery scheduled quantity
    public decimal RecRatchSchedQty { get; set; } // Receipt ratcheted scheduled quantity
    public decimal DelRatchSchedQty { get; set; } // Delivery ratcheted scheduled quantity
    public decimal RecCutQty { get; set; }        // Receipt cut quantity
    public decimal DelCutQty { get; set; }        // Delivery cut quantity
    public decimal OperAvailCap { get; set; }     // Operational available capacity
    public string ScenStatCode { get; set; }      // Scenario status (P=Proposed, S=Submitted)
    public int? IdSubmitUser { get; set; }
    public DateTime? SubmitTime { get; set; }
}
```

### UI Controller

#### QUIControllerCASummaryMaintenance

**Location**: `Quorum.QPTM.Web.Core/Controllers/QUIControllerCASummaryMaintenance.cs`

**Purpose**: Manages server-side state for CAS Summary Maintenance screen

**Key Responsibilities:**
- Manage query parameters (gas day, cycle, scheduling object type)
- Execute CAS summary queries
- Handle submission workflow
- Coordinate with scheduling service
- Manage ratchet and balancing settings

---

## Service Layer

### QPTMSchedulingService

**Location**: `Quorum.QPTM.ServiceCore.Scheduling/QPTMSchedulingService.cs`

**Purpose**: Core service for all CAS/Scheduling operations

**Key Methods:**

#### Classification

```csharp
// Classify nominations into transaction groups
public QSchedulingClassifyReturnMessage ClassifyNominations(QSchedulingClassifyRequest request)

// Internal classification logic
public virtual List<List<NomClassSplitDO>> ClassifyNominations(
    short nTspNo, 
    DateTime dtGasDay, 
    int idCycle, 
    List<ActivityDetailDO> inNominationCollection)
```

**Process:**
1. Filter nominations to latest cycle
2. Populate nomination helpers (path analysis)
3. Create contract helpers
4. Build rule sets and transaction groups
5. Match nominations to transaction groups
6. Return classification results

#### Scheduling Summary

```csharp
// Get CAS summary data (new or historical)
public QSchedulingSummaryReturnMessage GetSummarySchedulings(QSchedulingSummaryRequest request)

// Internal method - new summary calculation
public virtual List<CASummaryDO> GetNewSummarySchedulings(
    short nTspNo, 
    DateTime gasDay, 
    int idCycle, 
    bool bIsAutoCASProcess)

// Internal method - historical summary retrieval
public virtual List<CASummaryDO> GetExistingSummarySchedulings(
    short nTspNo, 
    DateTime gasDay, 
    int idCycle)
```

**Process:**
1. Query staging table (`CASTAG_OBJ_NOM_TRANS_GRP`)
2. Aggregate quantities by scheduling object and transaction group
3. Calculate scheduled quantities (considering OAC)
4. Generate `CASummaryDO` objects
5. Include nomination detail breakdowns

#### Preliminary Reduction (Cut)

```csharp
// Apply preliminary capacity reduction
public QSchedulingSummaryReturnMessage DoPrelimCut(QSchedulingSummaryRequest request)

// Internal reduction logic
public virtual List<CASummaryDO> DoPrelimCut(
    List<CASummaryDO> schdSumList, 
    bool bIsBatchCut, 
    out string sWarnMsg)
```

**Process:**
1. Rebuild object relationships (parent-child)
2. Enable path balancing if configured
3. Group nominations by scheduling object
4. Calculate available capacity
5. Apply reduction algorithms
6. Update scheduled quantities

#### Submission

```csharp
// Submit scheduled quantities
public QSchedulingSummaryReturnMessage SubmitSchedulings(QSchedulingSubmitRequest request)

// Update schedule header status
public virtual bool UpdateScheduleHeader(
    short nTspNo, 
    DateTime gasDay, 
    int idCycle, 
    string scenStatCode, 
    int idSubmitUser)
```

**Process:**
1. Validate submission pre-conditions
2. Save `CASummary` records to database
3. Update `CAScheduleHeader` status to "Submitted"
4. Generate confirmation records
5. Trigger EDI transmission (if applicable)

### Helper Classes

#### TransGroupMgr

**Location**: `Quorum.QPTM.ServiceCore.Scheduling/TransGroupMgr/TransGroupMgr.cs`

**Purpose**: Manage transaction group matching and classification logic

**Key Methods:**
```csharp
public class TransGroupMgr
{
    // Find matching transaction groups for nominations
    public void FindMatches(
        PathTempCache pathTempCache,
        short nTspNo,
        DateTime dtGasDay,
        PATransGroupDO transGroup,
        int nTransGroupRank,
        List<NomClassNomHelper> arNomHelpers,
        List<NomClassCtrPathHelper> ctrPathHelper,
        NomClassBuySellHelper nomClassBuySellHelper,
        bool bUsePipelineModel,
        bool bSecondaryMatchForPathed,
        bool bUseLocGrpScheduling,
        bool bCreateNonPathedFromPathed,
        List<AggregateContractHelper> aggregateContracts,
        int nTspEngScale)
}
```

#### ReductionGroupMgr

**Location**: `Quorum.QPTM.ServiceCore.Scheduling/ReductionGroupMgr.cs`

**Purpose**: Manage capacity reduction across transaction groups

**Implementations:**
- **ReductionGroupMgrBase**: Base reduction logic
- **ReductionGroupMgrClayBasin**: Clay Basin specific reduction
- **ReductionGroupMgrMDQPercentage**: MDQ percentage-based reduction

#### NomDetailBalancingHelper

**Location**: `Quorum.QPTM.ServiceCore.Scheduling/NomDetailBalancingHelper/`

**Purpose**: Balance nomination details across receipt/delivery points

**Key Methods:**
```csharp
// Balance nomination quantities
public static void BalanceNominationDetails(
    List<CANominationDetailDO> nomDetailList,
    bool enableCASPathBalancing)

// Generate balancing keys for grouping
public static string GenerateNomDtlBalKey(CANominationDetailDO nomDtl)
```

#### PipelineModelMgr

**Location**: `Quorum.QPTM.ServiceCore.Scheduling/PipelineModelMgr.cs`

**Purpose**: Manage pipeline model for path routing

**Key Methods:**
```csharp
// Get shortest path between locations
public List<LocationPathSegmentDO> GetShortestPath(
    short nTspNo,
    int idUpLoc,
    int idDnLoc,
    DateTime gasDay)

// Get all possible paths
public List<List<LocationPathSegmentDO>> GetAllPaths(
    short nTspNo,
    int idUpLoc,
    int idDnLoc,
    DateTime gasDay)
```

---

## Batch Process Layer

### Batch Process Architecture

**Location**: `Quorum.QPTM.QPDllScheduling/` (in Batch repository)

All batch processes inherit from `QPTMQPSSegregatedProcessBase` which provides:
- Lifecycle management (Initialize → Execute → Cleanup)
- Parameter handling
- Logging and error handling
- Transaction management
- Inter-process communication

### Key Batch Processes

#### QPSNomClassificationAndTransGroupingSeg

**File**: `QPSNomClassificationAndTransGroupingSeg.cs`

**Purpose**: Classify nominations and assign transaction groups

**Parameters:**
- `TSP_NO`: Transportation service provider number
- `NOM_ADD_SET_ID` (optional): Nomination add set ID for incremental processing
- `NOM_UPD_SET_ID` (optional): Nomination update set ID for incremental processing
- `GAS_DAY_OFFSET` (optional): Offset from current gas day

**Process Steps:**
1. **Initialize**: Extract parameters, validate inputs
2. **Execute**: 
   - Call `NomClassificationAndTransGroupingHelper.ClassifyAndAssignTransGroup()`
   - Load scheduling objects and rule sets
   - Match nominations to transaction groups
   - Save results to `CASTAG_OBJ_NOM_TRANS_GRP`
3. **Cleanup**: Release resources

**Info Object**: `QNomClassificationAndTransGroupingInfo`

**Key Code:**
```csharp
public class QPSNomClassificationAndTransGroupingSeg : QPTMQPSSegregatedProcessBase
{
    public override bool Initialize()
    {
        // Extract TSP_NO, GAS_DAY_OFFSET, NOM_ADD_SET_ID, NOM_UPD_SET_ID
        // Validate parameters
        // Initialize Info object
    }
    
    public override bool Execute()
    {
        // Call helper to classify and assign trans groups
        NomClassificationAndTransGroupingHelper helper = new NomClassificationAndTransGroupingHelper();
        helper.ClassifyAndAssignTransGroup(
            NomClassificationAndTransGroupingInfo.TspNo,
            dtGasDay,
            idCycle,
            idTimelyCycle,
            srBpNo,
            srCtrNoList,
            NomClassificationAndTransGroupingInfo.UserID);
    }
}
```

#### QPSSchedulingReductionSeg

**File**: `QPSSchedulingReductionSeg.cs`

**Purpose**: Apply capacity reduction when nominated quantities exceed available capacity

**Parameters:**
- `TSP_NO`: Transportation service provider number
- `GAS_DAY_OFFSET` (optional): Offset from current gas day
- `GAS_DAY` (optional): Specific gas day to process

**Process Steps:**
1. **Initialize**: Extract parameters, get current gas day if not provided
2. **Execute**:
   - Call `QSchedulingReductionSeg.DoSchedulingReduction()`
   - Load staging data from `CASTAG_OBJ_NOM_TRANS_GRP`
   - Load scheduling objects and OAC values
   - Apply reduction algorithms by transaction group rank
   - Update staged scheduled quantities
3. **Cleanup**: Commit transaction, release resources

**Info Object**: `QSchedulingReductionInfo`

**Key Code:**
```csharp
public class QPSSchedulingReductionSeg : QPTMQPSSegregatedProcessBase
{
    public override bool Execute()
    {
        QSchedulingReductionSeg reduction = new QSchedulingReductionSeg(
            SchedulingReductionInfo.TspNo,
            SchedulingReductionInfo.CurrentGasDay,
            SchedulingReductionInfo.UserID,
            ServiceProvider);
            
        return reduction.DoSchedulingReduction();
    }
}
```

#### QPSStageOperationalAvailableCapacity

**File**: `QPSStageOperationalAvailableCapacity.cs`

**Purpose**: Stage operational available capacity (OAC) values for scheduling cycle

**Parameters:**
- `TSP_NO`: Transportation service provider number
- `GAS_DAY_OFFSET` (optional): Offset from current gas day
- `GAS_DAY` (optional): Specific gas day to process

**Process Steps:**
1. **Initialize**: Extract parameters
2. **Execute**:
   - Call `QStageOperationalAvailableCapacity.StageOAC()`
   - Retrieve current OAC values for all scheduling objects
   - Store staged values for reduction process
   - Handle forward and backhaul capacity separately
3. **Cleanup**: Commit transaction

**Info Object**: `QStageOperationalAvailableCapacityInfo`

#### QPSDefaultRoutePathAutomationSeg

**File**: `QPSDefaultRoutePathAutomationSeg.cs`

**Purpose**: Automatically determine default routing paths for nominations

**Process Steps:**
1. Analyze nomination receipt and delivery points
2. Use pipeline model to find optimal path
3. Set default route path on nomination
4. Consider backhaul vs forward flow

### Batch Helper Classes

#### NomClassificationAndTransGroupingHelper

**File**: `NomClassificationAndTransGroupingHelper.cs`

**Purpose**: Core helper for classification logic (shared between batch and service)

**Key Methods:**
```csharp
public class NomClassificationAndTransGroupingHelper
{
    // Main classification entry point
    public void ClassifyAndAssignTransGroup(
        short nTspNo,
        DateTime dtGasDay,
        int idCycle,
        int idTimelyCycle,
        string SrBpNo,
        List<string> SrCtrNoList,
        string sUserId)
    
    // Load scheduling objects
    private void LoadSchedulingObjects(
        short nTspNo,
        DateTime dtGasDay,
        int idCycle,
        int idTimelyCycle,
        string sUserId,
        int nTspEngScale = 0)
    
    // Process nominations and assign trans groups
    private void LoadAndProcessRecords(
        short nTspNo,
        DateTime dtGasDay,
        int idCycle,
        string SrBpNo,
        string sUserId,
        List<string> SrCtrNoList)
}
```

#### SchedulingObject Classes

**Files**: `SchedulingObject*.cs`

**Purpose**: Represent different types of scheduling objects with object-oriented design

**Class Hierarchy:**
```
ISchedulingObject (interface)
└─→ SchedulingObjectBase (abstract base class)
    ├─→ SchedulingObjectSegment        (SEG)
    ├─→ SchedulingObjectLocation       (LOC)
    ├─→ SchedulingObjectLocationGroup  (LGP)
    ├─→ SchedulingObjectClayBasinEntireBasin     (CBE)
    ├─→ SchedulingObjectClayBasinBySides         (CBS)
    ├─→ SchedulingObjectLeaseBoundaryLocation    (LBL)
    ├─→ SchedulingObjectLeaseContractCapacity    (LCC)
    ├─→ SchedulingObjectMultiGroup               (MLT)
    └─→ SchedulingObjectBiDirectionalPair        (BDP)
```

**Common Methods:**
```csharp
public interface ISchedulingObject
{
    // Split nomination into transaction group components
    List<TransGrpNomHelperOutput> Split(TransGrpNomHelper nomHelper);
    
    // Calculate capacity for the object
    decimal GetCapacity(DateTime gasDay);
    
    // Validate nomination against object rules
    bool Validate(TransGrpNomHelper nomHelper);
}
```

---

## Data Model

### Core Database Tables

#### CACTRL_SCHD_HDR (CA Schedule Header)

**Purpose**: Header record for each scheduling cycle

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `GAS_DAY` (PK): Gas day
- `ID_CYCLE` (PK): Cycle identifier
- `SCEN_STAT_CD`: Scenario status (P=Proposed, S=Submitted, F=Final)
- `ID_SUBMIT_USER`: User who submitted
- `SUBMIT_TIME`: Submission timestamp
- `RATCH_ENABLED_IND`: Ratcheting enabled flag
- `USER_ID`: Last update user
- `UPDT_DT`: Last update timestamp

#### CACTRL_SCHD_OBJ_VW (CA Schedule Object)

**Purpose**: Configuration for scheduling objects

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `SCHD_OBJ_ID` (PK): Scheduling object identifier
- `SCHD_OBJ_TYPE_CD` (PK): Scheduling object type code
- `SCHD_OBJ_NM`: Scheduling object name
- `EFF_DATE_FROM`: Effective start date
- `EFF_DATE_TO`: Effective end date
- `ID_UP_LOC`: Upstream location (for segments)
- `ID_DN_LOC`: Downstream location (for segments)
- `ID_LOC`: Location (for location objects)
- `LOC_GRP_CD`: Location group code (for location groups)
- `USER_ID`: Last update user
- `UPDT_DT`: Last update timestamp

#### CAXREF_SCHD_OBJ_RULE_SET (CA Schedule Object Rule Set)

**Purpose**: Links scheduling objects to rule sets for specific cycles

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `SCHD_OBJ_ID` (PK): Scheduling object identifier
- `SCHD_OBJ_TYPE_CD` (PK): Scheduling object type code
- `CAS_RULE_SET_ID` (PK): Rule set identifier
- `ID_CYCLE` (PK): Cycle identifier
- `USER_ID`: Last update user
- `UPDT_DT`: Last update timestamp

#### CASTAG_OBJ_NOM_TRANS_GRP (Staging - Object Nomination Transaction Group)

**Purpose**: Staging table for classified nominations (temporary processing data)

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `SEQ_NO` (PK): Sequence number (unique per TSP)
- `GAS_DAY`: Gas day
- `ID_CYCLE`: Cycle identifier (cycle name, not ID)
- `SCHD_OBJ_ID`: Scheduling object identifier
- `SCHD_OBJ_TYPE_CD`: Scheduling object type code
- `ID_NOM`: Nomination identifier
- `TRANS_GRP_ID`: Transaction group identifier
- `TRANS_GRP_RANK`: Transaction group rank
- `REC_QTY`: Receipt quantity
- `DEL_QTY`: Delivery quantity
- `CAP_TYPE_CD`: Capacity type code (FT, IT, SR, etc.)
- `DIRECTION_FLOW_CD`: Direction of flow (FWD, BKH)
- `FLOW_TYPE_CD`: Flow type
- `RATE`: Rate
- `CAS_RULE_SET_ID`: Rule set identifier
- `EVAL_METH_CD`: Evaluation method code
- `REC_PREV_CYCLE_SCHED_QTY`: Previous cycle receipt scheduled quantity
- `DEL_PREV_CYCLE_SCHED_QTY`: Previous cycle delivery scheduled quantity
- `REC_RATCH_PREV_CYCLE_SCHED_QTY`: Previous cycle receipt ratcheted scheduled quantity
- `DEL_RATCH_PREV_CYCLE_SCHED_QTY`: Previous cycle delivery ratcheted scheduled quantity
- `SEGMENT_IND`: Segment indicator (boolean)
- `MAX_RATE`: Maximum rate
- `DISC_OFFER_ID`: Discount offer identifier
- `USER_ID`: Last update user
- `UPDT_DT`: Last update timestamp

**Note**: This table is populated by batch classification process and consumed by web application for CAS summary display.

#### CACTRL_SUMMARY (CA Summary)

**Purpose**: Summary of scheduled quantities by scheduling object (final result)

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `GAS_DAY` (PK): Gas day
- `ID_CYCLE` (PK): Cycle identifier
- `SCHD_OBJ_ID` (PK): Scheduling object identifier
- `SCHD_OBJ_TYPE_CD` (PK): Scheduling object type code
- `REC_QTY`: Total receipt nominated quantity
- `DEL_QTY`: Total delivery nominated quantity
- `REC_SCHED_QTY`: Receipt scheduled quantity
- `DEL_SCHED_QTY`: Delivery scheduled quantity
- `REC_RATCH_SCHED_QTY`: Receipt ratcheted scheduled quantity
- `DEL_RATCH_SCHED_QTY`: Delivery ratcheted scheduled quantity
- `REC_CUT_QTY`: Receipt cut quantity
- `DEL_CUT_QTY`: Delivery cut quantity
- `OPER_AVAIL_CAP`: Operational available capacity
- `SCEN_STAT_CD`: Scenario status
- `ID_SUBMIT_USER`: User who submitted
- `SUBMIT_TIME`: Submission timestamp
- `USER_ID`: Last update user
- `UPDT_DT`: Last update timestamp

#### PACTRL_RULE_SET (Rule Set)

**Purpose**: Rule sets for classification logic

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `CAS_RULE_SET_ID` (PK): Rule set identifier
- `CAS_RULE_SET_NM`: Rule set name
- `CAS_RULE_SET_DESC`: Rule set description
- `RULE_SET_RANK`: Rule set rank (priority)
- `EFF_DATE_FROM`: Effective start date
- `EFF_DATE_TO`: Effective end date

#### PACTRL_TRANS_GRP (Transaction Group)

**Purpose**: Transaction groups for nomination classification

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `TRANS_GRP_ID` (PK): Transaction group identifier
- `CAS_RULE_SET_ID`: Rule set identifier
- `TRANS_GRP_NM`: Transaction group name
- `TRANS_GRP_DESC`: Transaction group description
- `TRANS_GRP_RANK`: Transaction group rank (priority)
- `ACCT_METH_CD`: Accounting method code (PR=Pro-Rata, FC=FCFS, etc.)

#### PAXREF_TRANS_GRP_TOS (Transaction Group Type of Service)

**Purpose**: Filter transaction groups by Type of Service

**Key Columns:**
- `TSP_NO` (PK): Transportation service provider
- `TRANS_GRP_ID` (PK): Transaction group identifier
- `TOS_CD` (PK): Type of Service code

### Data Object Classes

#### CAScheduleHeaderDO

**Location**: `Quorum.QPTM.DataObject/CodeGen/CAScheduleHeaderDO.cs`

**Properties**: Match `CACTRL_SCHD_HDR` table

#### CAScheduleObjectDO

**Location**: `Quorum.QPTM.DataObject/CodeGen/CAScheduleObjectDO.cs`

**Properties**: Match `CACTRL_SCHD_OBJ_VW` table

#### CAStagObjNomTransGrpDO

**Location**: `Quorum.QPTM.DataObject/CodeGen/CAStagObjNomTransGrpDO.cs`

**Properties**: Match `CASTAG_OBJ_NOM_TRANS_GRP` table

#### CASummaryDO

**Location**: `Quorum.QPTM.DataObject/CodeGen/CASummaryDO.cs`

**Properties**: Match `CACTRL_SUMMARY` table, plus related child collections

**Extended Properties** (in `CASummaryDOExt.cs`):
```csharp
public partial class CASummaryDO
{
    // Child collections
    public List<CANominationDetailDO> CANominationDetailDOList { get; set; }
    public List<CANominationDetailDO> UpDownNominationDetailDOList { get; set; }
    
    // Calculated properties
    public bool IsOverNominated { get; }
    public decimal AvailableCapacity { get; }
}
```

#### PARuleSetDO / PATransGroupDO

**Location**: `Quorum.QPTM.DataObject/CodeGen/`

**Properties**: Match `PACTRL_RULE_SET` and `PACTRL_TRANS_GRP` tables

**Relationships**:
- `PARuleSetDO.PATransGroups` - Collection of transaction groups for the rule set
- `PATransGroupDO.PATransGroupTos` - Collection of TOS filters for the trans group

---

## Key Classes and Interfaces

### Interface Definitions

#### IQPTMSchedulingService

**Location**: `Quorum.QPTM.ServiceInterface/IQPTMSchedulingService.cs`

**Purpose**: Service contract for CAS/Scheduling operations

**Key Methods:**
```csharp
public interface IQPTMSchedulingService
{
    // Classification
    QSchedulingClassifyReturnMessage ClassifyNominations(QSchedulingClassifyRequest request);
    
    // Summary
    QSchedulingSummaryReturnMessage GetSummarySchedulings(QSchedulingSummaryRequest request);
    
    // Reduction
    QSchedulingSummaryReturnMessage DoPrelimCut(QSchedulingSummaryRequest request);
    
    // Submission
    QSchedulingSummaryReturnMessage SubmitSchedulings(QSchedulingSubmitRequest request);
    
    // Header
    CAScheduleHeaderDO GetSchedulingHeader(short nTspNo, DateTime gasDay, int idCycle);
}
```

### Request/Response Classes

#### QSchedulingClassifyRequest

```csharp
public class QSchedulingClassifyRequest
{
    public short TspNo { get; set; }
    public DateTime GasDay { get; set; }
    public int IdCycle { get; set; }
    public List<ActivityDetailDO> ActivityDetails { get; set; }
}
```

#### QSchedulingSummaryRequest

```csharp
public class QSchedulingSummaryRequest
{
    public short TspNo { get; set; }
    public DateTime GasDay { get; set; }
    public int IdCycle { get; set; }
    public bool IsHistoricalData { get; set; }
    public bool IsAutoCASProcess { get; set; }
    public List<CASummaryDO> CASummaries { get; set; }
}
```

#### QSchedulingSummaryReturnMessage

```csharp
public class QSchedulingSummaryReturnMessage
{
    public List<CASummaryDO> CASummaries { get; set; }
    public string WarnMsg { get; set; }
    public bool Success { get; set; }
}
```

---

## Processing Flow

### End-to-End CAS Processing Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. NOMINATION SUBMISSION (User/External System)              │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. BATCH: QPSNomClassificationAndTransGroupingSeg            │
│    - Load nominations for gas day/cycle                      │
│    - Load scheduling objects and rule sets                   │
│    - Match nominations to transaction groups                 │
│    - Save to CASTAG_OBJ_NOM_TRANS_GRP                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. BATCH: QPSStageOperationalAvailableCapacity               │
│    - Retrieve OAC values for all scheduling objects          │
│    - Stage OAC data for reduction process                    │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. BATCH: QPSSchedulingReductionSeg (if over-nominated)      │
│    - Load staging data                                       │
│    - Compare nominated vs OAC                                │
│    - Apply reduction algorithms                              │
│    - Update staged scheduled quantities                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. WEB: CASummaryMaintenanceController.Query()              │
│    - User opens CAS Summary Maintenance screen               │
│    - Call QPTMSchedulingService.GetSummarySchedulings()     │
│    - Load from CASTAG_OBJ_NOM_TRANS_GRP                    │
│    - Aggregate by scheduling object                          │
│    - Display in grid                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. WEB: User Reviews and Optionally Edits                   │
│    - Review scheduled quantities                             │
│    - Make manual adjustments if needed                       │
│    - Click "PrelimCut" to re-run reduction                  │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. WEB: CASummaryMaintenanceController.Submit()             │
│    - User clicks "Submit" button                             │
│    - Call QPTMSchedulingService.SubmitSchedulings()         │
│    - Save to CACTRL_SUMMARY (permanent table)                │
│    - Update header status to "Submitted"                     │
│    - Generate confirmations                                  │
│    - Trigger EDI transmission (if configured)                │
└──────────────────────────────────────────────────────────────┘
```

### Classification Detail Flow

```
ClassifyNominations()
├─→ FilterNominations() - Latest cycle filtering
├─→ PopulateNomClassNomHelpers() - Path analysis
│   ├─→ Get nomination details
│   ├─→ Analyze receipt/delivery points
│   └─→ Build path segments
├─→ PopulateNomClassCtrHelpers() - Contract analysis
│   ├─→ Get contract details
│   ├─→ Build contract paths
│   └─→ Link nominations to contracts
├─→ PopulateRuleSetRanks() - Load rule sets
│   ├─→ Get rule sets for TSP/cycle
│   ├─→ Get transaction groups
│   └─→ Sort by rank
└─→ For each contract
    └─→ For each rule set rank
        └─→ For each transaction group
            ├─→ Filter by TOS
            ├─→ TransGroupMgr.FindMatches()
            │   ├─→ Match path criteria
            │   ├─→ Match capacity type
            │   ├─→ Create NomClassSplitDO
            │   └─→ Set transaction group rank
            └─→ Store classification results
```

### Reduction Detail Flow

```
DoPrelimCut()
├─→ ReBuildList() - Restore object relationships
├─→ For each CASummaryDO
│   ├─→ Get CANominationDetailDO list
│   ├─→ Group by scheduling object
│   └─→ Calculate total nominated quantities
├─→ Compare nominated vs OAC
│   └─→ If nominated > OAC, apply reduction
│       ├─→ Sort transaction groups by rank
│       ├─→ For each trans group (highest rank first)
│       │   ├─→ Calculate pro-rata reduction %
│       │   ├─→ Apply reduction to each nomination
│       │   └─→ Update scheduled quantities
│       └─→ Verify total scheduled ≤ OAC
├─→ Handle ratcheting (if enabled)
│   ├─→ Get previous cycle scheduled quantities
│   ├─→ Compare to current nominated
│   └─→ If prev_sched > nominated, use prev_sched
└─→ Return updated CASummaryDO list
```

---

## Rights Allocation Implementation

### Rights Evaluation Architecture

**Rights allocation** determines how nominated quantities are categorized (Primary, Secondary In Path, Secondary Out of Path, None) based on capacity availability and contract limits.

### Core Rights Functions

**1. EvaluateSegmentRights2 (Batch Layer)**
- **Location**: `TransGrpNomHelper.cs` (line ~1742)
- **Purpose**: Main rights evaluation logic for batch processing
- **Input**: Nomination details, scheduling object info, contract data
- **Output**: Dictionary<string, decimal> RightSplits (e.g., {"SI": 978, "SO": 500})
- **Caching**: Results cached in `m_RightSplitsCache` by scheduling object ID

**2. EvaluateSegmentRights (Batch Layer)**
- **Location**: `TransGrpNomHelper.cs` (line ~1530)
- **Purpose**: Retrieves cached rights and returns quantity for specific rights type
- **Input**: Transaction group attribute (e.g., "SI" for SecondaryInPath)
- **Output**: decimal quantity for the requested rights type
- **Flow**: Calls EvaluateSegmentRights2 → caches result → returns specific quantity

**3. EvaluateSegmentRights (Web Layer)**
- **Location**: `QPTMSchedulingServiceExt_RoutePath.cs` (line ~857)
- **Purpose**: Web service version of rights evaluation
- **Input**: Same as batch version
- **Output**: Dictionary<string, decimal> RightSplits
- **Differences**: Simpler logic, no batch processing complexity

### Rights Allocation Flow

```
Rights Evaluation Process:

1. Nomination Classification
   ├─→ Nomination enters transaction group processing
   └─→ Transaction group has rights-based attributes

2. Rights Evaluation Call
   ├─→ EvaluateSegmentRights() called for each rights attribute
   ├─→ Checks cache first (m_RightSplitsCache)
   └─→ If not cached, calls EvaluateSegmentRights2()

3. Rights Calculation Logic
   ├─→ Compare dNomQty vs segMDQ vs ctrMDQ
   ├─→ Check flow direction (IsFlow property)
   ├─→ Calculate primaryMDQ, secondaryMDQ
   └─→ Build RightSplits dictionary

4. Rights Assignment
   ├─→ RightSplits["P"] = primary quantity
   ├─→ RightSplits["SI"] = secondary in path (locations only)
   ├─→ RightSplits["SO"] = secondary out of path
   ├─→ RightSplits["S"] = total secondary
   └─→ RightSplits["N"] = overrun quantity

5. Output Processing
   ├─→ GetOutputSplits() assigns rights quantities to output
   ├─→ newOutSplit.SegmentRightsQty = dQtyForRightSplit
   └─→ Rights become scheduled capacity allocations
```

### Key Rights Logic Implementation

**Location vs Segment Logic:**
```csharp
// In EvaluateSegmentRights2
if (SchdObjTypeCode == Constants.SchedulingObjectType.Segment || 
    SchdObjTypeCode == Constants.SchedulingObjectType.MultiGroup)
{
    // Segments: No SI rights, only P, S, SO, N
    RightSplits.Add(Constants.SegmentRights.Primary, segMDQ);
    RightSplits.Add(Constants.SegmentRights.Secondary, ctrMDQ - segMDQ);
}
else  // Locations: Include SI rights
{
    if (secondaryMDQ != null)
    {
        RightSplits.Add(Constants.SegmentRights.SecondaryInPath, (secondaryMDQ ?? 0));
    }
}
```

**Secondary MDQ Calculation:**
```csharp
// What remains after primary MDQ is secondary for location
secondaryMDQ = segMDQ - (primaryMDQ ?? 0);
```

**Opposite Direction Logic:**
```csharp
// Check for opposite direction nominations
bool bNomIsOppositeDirection = 
    (IsFlowForward && ContractSegmentDirection == "B") || 
    (!IsFlowForward && ContractSegmentDirection == "F");

// If opposite direction WITHOUT primary rights, assign SO
if (bNomIsOppositeDirection && (primaryMDQ == null || primaryMDQ == 0))
{
    // Force secondary out of path classification
    RightSplits.Add(Constants.SegmentRights.Secondary, dNomQty);
    RightSplits.Add(Constants.SegmentRights.SecondaryOutOfPath, dNomQty);
    return RightSplits;
}
```

**Flow Direction Check:**
```csharp
// Early return for opposite flow direction
if (bNomIsOppositeDirection)
{
    // Force secondary out of path classification
    RightSplits.Add(Constants.SegmentRights.Secondary, dNomQty);
    if (SchdObjTypeCode == Constants.SchedulingObjectType.Location)
    {
        RightSplits.Add(Constants.SegmentRights.SecondaryOutOfPath, dNomQty);
    }
    return RightSplits;
}
```

### Rights Constants and Codes

**Rights Code Constants:**
- `Constants.SegmentRights.Primary` = "P"
- `Constants.SegmentRights.SecondaryInPath` = "SI"
- `Constants.SegmentRights.SecondaryOutOfPath` = "SO"
- `Constants.SegmentRights.Secondary` = "S"
- `Constants.SegmentRights.None` = "N"

**Rights Attribute Matching:**
- Transaction groups have attributes like `SEGMENT_RIGHTS = "SI"`
- Nominations match groups where rights are available
- Rights quantities determine allocation priority

### Caching Implementation

**Rights Cache Structure:**
```csharp
private Dictionary<string, Dictionary<string, decimal>> m_RightSplitsCache = 
    new Dictionary<string, Dictionary<string, decimal>>();
```

**Cache Key:** `SchdObjID + Separator + FlowDirection`
**Cache Value:** Dictionary of rights codes to quantities
**Cache Purpose:** Performance optimization for repeated rights lookups

### Rights in Output Processing

**GetOutputSplits Integration:**
- `EvaluateSegmentRights` returns `dQtyToUse` for specific rights
- `GetOutputSplits` assigns to `newOutSplit.SegmentRightsQty`
- Rights quantities become the scheduled capacity allocations
- Rights determine reduction priority during capacity constraints

### Rights Validation and Error Handling

**Validation Checks:**
- Contract must exist and be valid
- Scheduling object must be on nominated path
- Flow direction must match contract setup
- MDQ values must be properly configured

**Error Scenarios:**
- Missing contract: Exception thrown
- Invalid path: Exception thrown
- Cache corruption: Recalculated on next access
- Invalid rights code: Returns false (no match)

---

## Integration Points

### Integration with Other QPTM Modules

**Nominations (NN)**
- **Input**: CAS receives nominations as input
- **Table**: `NNCTRL_NOM_HDR`, `NNCTRL_NOM_DTL`
- **Flow**: Nominations → Classification → Scheduling

**Allocations (AL)**
- **Output**: CAS scheduled quantities used for allocation calculations
- **Table**: `ALCTRL_ALLOC`, `ALTRAN_ALLOC`
- **Flow**: Scheduled Qty → Allocation → Actual Flow Distribution

**Contracts (K)**
- **Input**: CAS uses contract MDQ and TOS for classification
- **Table**: `KCTRL_CTR_HDR`, `KCTRL_CTR_LOC`, `KCTRL_CTR_QTY`
- **Flow**: Contract Rules → Classification Logic

**EDI**
- **Output**: CAS generates EDI transactions for scheduled quantities
- **Standards**: NAESB WGQ standards for capacity release
- **Flow**: Scheduled Qty → EDI Generator → TSP System

### External System Integration

**TSP Systems (Pipeline Operator)**
- **Method**: EDI, API, or manual file exchange
- **Data**: Scheduled quantities, capacity allocations
- **Frequency**: Per nomination cycle (Timely, Evening, Intraday)

### Batch Process Integration

**QPEC Framework**
- CAS batch processes run within QPEC (Quorum Process Execution Controller)
- Process definitions stored in QPEC database tables
- Scheduling and dependencies managed by QPEC

**Process Dependencies:**
```
Nomination Import/Validation
   ↓
QPSNomClassificationAndTransGroupingSeg
   ↓
QPSStageOperationalAvailableCapacity
   ↓
QPSSchedulingReductionSeg (if needed)
   ↓
CAS Summary Generation (Web or Batch)
   ↓
EDI Transmission (if configured)
```

---

## Configuration

### TSP Configuration Settings

**Configuration Table**: `PACFG_TSP_CONFIG_CONTROL`

**Key Settings:**
- `PIPELINE_MODEL_DEFINED`: Use pipeline model for path routing (1=Yes, 0=No)
- `NOM_CLASS_PATHED_FROM_NONPATHED`: Create pathed from non-pathed nominations
- `NOM_CLASS_NONPATHED_FROM_PATHED`: Create non-pathed from pathed nominations
- `USE_LOC_GRP_TRANS`: Use location group transaction logic
- `ENABLE_CAS_PATH_BALANCING`: Enable path balancing in CAS

### Global Configuration Settings

**Configuration Table**: `PACFG_GLOBAL_CONFIG_CONTROL`

**Key Settings:**
- `USE_LOC_GRP_SCHEDULING`: Use location group scheduling logic
- `CAS_AUTO_BALANCE`: Enable automatic balancing in CAS

---

## Performance Considerations

### Optimization Strategies

**1. Query Optimization**
- Use indexes on `CASTAG_OBJ_NOM_TRANS_GRP` (TSP_NO, GAS_DAY, ID_CYCLE)
- Filter by gas day early to reduce dataset size
- Use parameterized queries to enable query plan caching

**2. Caching**
- Cache TSP configuration settings (`TspCacheAccess`)
- Cache location and contract data (`LocationCacheAccess`, `ContractCacheAccess`)
- Cache rule sets and transaction groups (`RuleCacheAccess`)

**3. Parallel Processing**
- Classification can be parallelized by contract
- Multiple gas days can be processed in parallel (separate batch jobs)

**4. Memory Management**
- Stream large datasets instead of loading all into memory
- Dispose DataObjects properly after use
- Use `TransactionScope` carefully to avoid long-held locks

**5. Batch Processing**
- Run classification and reduction during off-peak hours
- Use incremental processing (NOM_ADD_SET_ID, NOM_UPD_SET_ID) when possible
- Monitor batch job execution times and optimize bottlenecks

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts and terminology
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- **QUICK_REFERENCE.md**: Feature mapping and keywords for CAS

---

*Last updated: 2025-12-30*  
*Document version: 1.0*
