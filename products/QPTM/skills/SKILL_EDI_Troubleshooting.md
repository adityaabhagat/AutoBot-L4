# SKILL: EDI Nomination Troubleshooting Guide (QPTM)

**Version:** 1.0 | **Created:** 2026-05-26 | **Product:** QPTM
**Scope:** Inbound NMST, Outbound NMQR, Cycle Deadlines, EDI Error Codes, Late/Retro Nominations

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [EDI Architecture Overview](#2-edi-architecture-overview)
3. [Inbound NMST Processing Flow](#3-inbound-nmst-processing-flow)
4. [Cycle Deadline System](#4-cycle-deadline-system)
5. [Common EDI Error Codes (ENMQR)](#5-common-edi-error-codes-enmqr)
6. [Late Nomination / Retroactive Nom (ENMQR315)](#6-late-nomination--retroactive-nom-enmqr315)
7. [Cycle Indicator Issues (ENMQR320/321)](#7-cycle-indicator-issues-enmqr320321)
8. [Contract & Location Errors (ENMQR301/525-538)](#8-contract--location-errors)
9. [Quantity Errors (ENMQR502-506)](#9-quantity-errors)
10. [Header Errors (ENMQR100-116)](#10-header-errors-enmqr100-116)
11. [EDI Transport Errors (EEDM)](#11-edi-transport-errors-eedm)
12. [LI vs BI Error Blocking](#12-li-vs-bi-error-blocking)
13. [Key Code Files & Repos](#13-key-code-files--repos)
14. [Database Tables Reference](#14-database-tables-reference)
15. [Diagnostic SQL Queries](#15-diagnostic-sql-queries)
16. [Global Configs Affecting EDI](#16-global-configs-affecting-edi)
17. [TSP-Specific EDI Behaviors](#17-tsp-specific-edi-behaviors)
18. [Common Root Causes & Fixes](#18-common-root-causes--fixes)
19. [Escalation Decision Tree](#19-escalation-decision-tree)
20. [ADO Search Patterns](#20-ado-search-patterns)

---

## 1. Quick Triage Checklist

When an EDI nomination error case comes in, answer these questions first:

```
[ ] 1. What is the EXACT error code? (e.g., ENMQR315, ENMQR301, EEDM105)
[ ] 2. Which TSP? (TSP_NO)
[ ] 3. Which Trading Partner / Shipper? (BP_NO / TPA name)
[ ] 4. What gas day and time was the nomination submitted?
[ ] 5. Which cycle was it targeting? (or was cycle auto-assigned?)
[ ] 6. Does the TSP's NMST EDI include the Cycle Indicator (CS/N9) segment?
[ ] 7. Is this a one-time issue or recurring?
[ ] 8. What NAESB version? (1.8, 1.9, 2.0)
[ ] 9. Is the client on Web or Classic?
[ ] 10. What QPTM version is the client running?
```

### Error Code Quick Lookup
| Error Prefix | Category | Likely Area |
|-------------|----------|-------------|
| ENMQR1xx | Header-level | TSP/SR identity, timestamps |
| ENMQR3xx | Detail-level | Contract, dates, cycle, model type |
| ENMQR5xx | Sub-detail-level | Locations, quantities, transaction types |
| WNMQR3xx | Detail warnings | Non-blocking warnings |
| EEDM1xx | Transport-level | HTTP/connectivity, file format |
| SUBDTL998/999 | Batch-level | LI blocking error cascade |

---

## 2. EDI Architecture Overview

### System Components
```
[External Shipper] --NMST EDI--> [Quorum.EDIServ (InboundServer)]
    --> [EDINCOMING Batch Process]
    --> [Quorum.QPTM.Batch (QEdiNMSTIn18)]
        --> Phase 1: ReadFile (parse, auto-assign cycle)
        --> Phase 2: ProcessData (fuel calc, merge, submit)
            --> [Quorum.QPTM.Web (QPTMNominationService.SubmitNominations)]
                --> Validation Engine runs rules (RuleNN*)
                --> Returns errors
            --> CreateQuickResponse
    --> [G874NMQR outbound] --NMQR EDI--> [External Shipper]
```

### EDI Message Types (Nomination)
| Code | Name | Direction | Purpose |
|------|------|-----------|---------|
| G873NMST | Nomination Statement | Inbound | Shipper submits nominations |
| G874NMQR | Nomination Query Response | Outbound | System returns validation results |
| G874OACY | Operational Capacity | Outbound | System sends scheduled quantities |

### Key Service Interfaces
| Interface | Purpose |
|-----------|---------|
| `IQPTMNominationService` | Submit noms, get noms, calculate fuel/MDQ/EPSQ |
| `IQPTMCycleService` | Get open cycles, cycle deadlines, cycle status |
| `IEDIService` | Queue/save EDI files, launch batch processes |
| `IEdiDataCache` | Cached lookups for contracts, rules, locations |

---

## 3. Inbound NMST Processing Flow

### Phase 1: ReadFile (QEdiNMSTIn18.ReadFile)

**Purpose:** Parse the EDI segments and create ActivityDetailDO objects

```
1. Parse BGN segment → Extract reference ID (IdNomRef)
2. Parse DTM segment → Set SubmitDate = DateTime.Now
3. Parse N1 loop → Identify TSP (BY) and Service Requester (SJ)
   → Validate TSP (ENMQR109/110), SR (ENMQR111/112/113/115)
4. Parse Area 2 DTM → Extract gas day range (BegGasDay, EndGasDay)
   → AUTO-ASSIGN CYCLE via GetOpenCycleByDay()
5. Parse CS segment → Get contract, model type (PT/PNT)
   → Validate contract (ENMQR301/302), model type (ENMQR305/306/307)
6. Parse DTM;CS segment → Cycle indicator (if present)
   → NOTE: Many TSPs don't send this segment
7. Parse SLN segment → Get quantities, transaction type, tracking ID
   → Validate quantity (ENMQR502/503), trans type (ENMQR512/513)
8. Parse N1 loop in SLN → Get receipt/delivery locations
   → Validate locations (ENMQR525-538)
```

### Phase 2: ProcessData (QEdiNMSTIn18.ProcessData)

```
1. CalculateFuel() → Apply fuel rates to nominations
2. PrepareAndSubmit():
   a. SplitIntoMonths() → Group noms by month
   b. SplitNonTimelyRecords() → Split multi-day noms where cycle changes
   c. For each month:
      - GetNominations() → Get existing noms
      - SplitAndMerge() → Merge new with existing
      - SubmitNominations() → Call middle tier
        → Middle tier runs ALL validation rules
        → Returns noms with NomStatCode (VI/BI/LI)
      - Handle LI errors → Block remaining noms
      - Launch NNPSTCREAT batch process
3. CreateQuickResponse() → Build NMQR with errors
4. LaunchQuickResponse() → Send NMQR outbound
```

### Cycle Auto-Assignment Logic
```csharp
// In Proc_873_Area_2_Loop_DTM:
short[] openCyclesByDay = service.GetOpenCycleByDay(
    currDO.TspNo,
    currDO.BegGasDay,
    Constants.DeadlineCategory.Nomination,  // "NOM"
    Constants.DeadlineType.OnTime);          // "ONT"

currDO.IdCycle = OpenCycles[sYearMonth][currDO.BegGasDay.Day - 1];
```

**The cycle is cached per year+month.** If the same EDI file has nominations for multiple days in the same month, they all use the same cycle lookup result. This is efficient but means the cycle assignment is based on the time when the FIRST nom for that month is processed.

---

## 4. Cycle Deadline System

### How Cycles Work

NAESB defines nomination cycles for gas pipeline scheduling:

| Cycle | NAESB Name | Typical Deadline (CCT) | Purpose |
|-------|-----------|------------------------|---------|
| 1 (ID1) | Timely | Day-1 ~11:30 AM | Primary nomination window |
| 2 (ID2) | Evening | Day-1 ~6:00 PM | Evening update |
| 3 (ID3) | Intraday 1 | Gas day ~10:00 AM | First intraday update |
| 4 (ID4) | Intraday 2 | Gas day ~2:30-5:00 PM | Second intraday update |
| 5 (ID5) | Intraday 3 | Gas day ~7:00-9:00 PM | Third intraday update |

**IMPORTANT:** Exact deadlines vary significantly by TSP. Always check `PACTRL_CYCLE_DEADLINE` for the specific TSP.

### Deadline Evaluation Logic (CycleManager.cs)

```csharp
// CycleManager.GetFirstOpenCycle():
DateTime currentDateTime = DateTimeService.Now();
foreach (CycleDeadlineDO cycleDeadline in sortedCycles)  // sorted by IdCycle ASC
{
    // Check effective dates
    if (date >= cycleDeadline.EffDateFrom && date <= cycleDeadline.EffDateTo)
    {
        DateTime deadline = cycleDeadline.CalcDeadline(date);  // gas day + offset + time
        if (currentDateTime <= deadline)
        {
            return cycleDeadline.IdCycle;  // FIRST OPEN CYCLE
        }
        // else: this cycle is closed, try next
    }
}
return -1;  // ALL CYCLES CLOSED → retroactive
```

### CalcDeadline Method
`CycleDeadlineDO.CalcDeadline(gasDay)` computes:
```
deadline = gasDay + DEADLINE_DAY_OFFSET days + DEADLINE_TIME
```
Example: If gas day = 2026-05-09, offset = 0, time = 14:30 CST:
→ deadline = 2026-05-09 14:30:00 CST

### Key Database Table: PACTRL_CYCLE_DEADLINE
```
TSP_NO           - TSP number
ID_CYCLE         - Cycle ID (1=Timely, 2=Evening, 3=ID1, 4=ID2, etc.)
DEADLINE_CATEGORY - NOM (Nomination), CNF (Confirmation), SCH (Scheduling)
DEADLINE_TYPE    - ONT (OnTime), EXT (Extended), ELC (Electronic)
USER_TYPE_CD     - INT (Internal), EXT (External)
DEADLINE_DAY_OFFSET - Days relative to gas day (0=same day, -1=day before)
DEADLINE_TIME    - Time of day for the deadline
DEADLINE_TZ      - Time zone
EFF_DT_FROM      - Effective date start
EFF_DT_TO        - Effective date end
```

### Open vs. Closed Cycle Determination
```
currentTime <= CalcDeadline(gasDay)  → OPEN  (can submit)
currentTime >  CalcDeadline(gasDay)  → CLOSED (late nomination)
```

---

## 5. Common EDI Error Codes (ENMQR)

### Header Level (HDR) — Area 1 Parsing Errors
| Code | Description | Common Cause |
|------|------------|--------------|
| ENMQR100 | Invalid transaction set purpose code (BGN01) | Wrong BGN segment |
| ENMQR104 | Invalid Time Stamp | Malformed timestamp |
| ENMQR105 | Missing Time Stamp | Missing DTM segment |
| ENMQR109 | Invalid Transportation Service Provider | TSP not found in system |
| ENMQR110 | Missing Transportation Service Provider | N1*BY segment missing |
| ENMQR111 | Invalid Service Requester | SR/shipper not found |
| ENMQR112 | Missing Service Requester | N1*SJ segment missing |
| ENMQR113 | Other Service Requester error | SR lookup issue |
| ENMQR115 | Inactive Service Requester | SR is deactivated |
| ENMQR116 | Inactive Transportation Service Provider | TSP is deactivated |

### Detail Level (DTL) — Area 2 Parsing/Validation Errors
| Code | Description | Common Cause |
|------|------------|--------------|
| ENMQR301 | Invalid Service Requester Contract | Contract not found for SR/TSP/gas day |
| ENMQR302 | Missing Service Requester Contract | CS segment missing contract |
| ENMQR303 | Service Requester Contract is locked | Contract locked for edits |
| ENMQR305 | Invalid Model Type | Unknown model type code |
| ENMQR307 | Incorrect Model Type for contract | Nom model doesn't match contract |
| ENMQR310 | Invalid nomination Beg/End Date/Time | Bad date range |
| ENMQR311 | Missing nomination Beg/End Date/Time | Missing DTM |
| ENMQR312 | Nom Beg/End outside contract terms | Gas day outside contract period |
| **ENMQR315** | **Time stamp outside acceptable range** | **LATE NOMINATION / RETRO NOM** |
| ENMQR316 | Invalid Beginning Time | Bad start time |
| ENMQR320 | Invalid Cycle Indicator | Bad cycle ID in CS segment |
| ENMQR321 | Missing Cycle Indicator | CS segment present but no cycle |

### Sub-Detail Level (SDT) — Line Item Errors
| Code | Description | Common Cause |
|------|------------|--------------|
| ENMQR501 | Missing Nominator's Tracking ID | SLN01 empty |
| ENMQR502 | Invalid Quantity | Non-numeric or negative qty |
| ENMQR503 | Missing Quantity | QTY segment missing |
| ENMQR504 | Nom Quantity exceeds daily contract quantity | MDQ exceeded |
| ENMQR512 | Invalid Transaction Type | Bad trans type code |
| ENMQR525 | Invalid Receipt Location | Rec loc not found |
| ENMQR526 | Missing Receipt Location | Rec loc empty |
| ENMQR527 | Receipt Location invalid for contract | Loc not on contract path |
| ENMQR532 | Invalid Delivery Location | Del loc not found |
| ENMQR534 | Delivery Location invalid for contract | Loc not on contract path |
| ENMQR539 | Path invalid for contract | Path doesn't exist on contract |
| ENMQR571 | Contract is out of balance | Rec/Del imbalance |

### Warnings (non-blocking)
| Code | Description |
|------|-------------|
| WNMQR300 | Timestamp outside acceptable range for Timely noms |
| WNMQR302 | Incorrect Ending Time, defaulted to end of gas day |
| WNMQR303 | Beginning Time Not Processed |
| WNMQR304 | Cycle Indicator not used |
| WNMQR305 | Invalid Cycle Indicator |
| WNMQR306 | Missing Cycle Indicator |

### Batch/System Errors
| Code | Description |
|------|-------------|
| SUBDTL998 | Nom not submitted due to LI error (NAESB < 1.8) |
| SUBDTL999 | Nom not submitted due to LI error (NAESB 1.8+) |
| ENMQR999 | Temporary Error Code - message follows |

---

## 6. Late Nomination / Retroactive Nom (ENMQR315)

### Validation Rule: RuleNN00009011
- **Type:** `ValidationRuleBaseNominationLine` (Line-level → "LI" on failure)
- **NAESB Code:** ENMQR315
- **Description:** "LATE NOMINATION OR RETROACTIVE NOM IS NOT ALLOWED"
- **Fires when:** `currentDateTime > cycleDeadline.CalcDeadline(begGasDay)`

### How the Rule Works
```
1. Check if nomination has IdCycle set AND has meaningful changes
2. Get the first open cycle for the nom's TSP/gas day
3. Determine user type (Internal vs External) from ValidatingUserID
4. Lookup cycle deadline from CycleCache:
   - Check for contract attribute "EXT" → use extended deadline
   - Check for contract attribute "ELC" → use electronic deadline
   - Otherwise use standard "ONT" (OnTime) deadline
5. Calculate actual deadline: cycleDeadline.CalcDeadline(begGasDay)
6. Compare: if DateTime.Now > deadline → FAIL (bIsValid = false)
```

### Investigation Steps for ENMQR315

**Step 1: Get the exact deadline time**
```sql
SELECT cd.ID_CYCLE, cd.DEADLINE_TYPE, cd.USER_TYPE_CD,
       cd.DEADLINE_DAY_OFFSET, cd.DEADLINE_TIME, cd.DEADLINE_TZ,
       cd.EFF_DT_FROM, cd.EFF_DT_TO
FROM PACTRL_CYCLE_DEADLINE cd
WHERE cd.TSP_NO = <TSP_NO>
  AND cd.DEADLINE_CATEGORY = 'NOM'
  AND cd.DEADLINE_TYPE IN ('ONT', 'EXT', 'ELC')
  AND '<GAS_DAY>' BETWEEN cd.EFF_DT_FROM AND cd.EFF_DT_TO
ORDER BY cd.ID_CYCLE, cd.DEADLINE_TYPE;
```

**Step 2: Check which cycle was assigned**
```sql
SELECT et.EDI_TRANS_ID, et.RECV_DT, et.PROC_DT
FROM EDTRAN et
WHERE et.TSP_NO = <TSP_NO> AND et.REF_ID = '<REF_ID>';

SELECT qr.NAESB_ERROR_CD, qr.ERROR_DESCR, qr.BEG_GAS_DAY, qr.CTR_NO
FROM EDTRAN_QR_ERROR qr
WHERE qr.TSP_NO = <TSP_NO> AND qr.REF_ID = '<REF_ID>';
```

**Step 3: Check if contract has extended deadline attributes**
```sql
SELECT ca.CTR_NO, ca.TOS_ATTR_CD, ca.IS_ATTR_TRUE
FROM NNCTRL_CTR_ATTR ca
WHERE ca.TSP_NO = <TSP_NO>
  AND ca.CTR_NO = '<CONTRACT_NO>'
  AND ca.TOS_ATTR_CD IN ('EXT', 'ELC');
```

**Step 4: Check TPA user type**
```sql
SELECT tpa.TPA_NM, tpa.SECURITY_USER_ID, su.USER_TYPE_CD
FROM NNCTRL_TPA tpa
JOIN QARCH_SECURITY_USER su ON tpa.SECURITY_USER_ID = su.SECURITY_USER_ID
WHERE tpa.TSP_NO = <TSP_NO> AND tpa.TPA_NM LIKE '%<SHIPPER>%';
```

### Common Root Causes for ENMQR315

| # | Root Cause | Fix |
|---|-----------|-----|
| 1 | Cycle deadline config is actually correct — shipper submitted AFTER deadline | Inform shipper of correct deadlines |
| 2 | Cycle deadline config has wrong time/offset | Update PACTRL_CYCLE_DEADLINE |
| 3 | Cycle deadline effective dates expired/gap | Update EFF_DT_TO or add new row |
| 4 | TPA user classified as External, hits shorter deadline | Check if Internal user type is appropriate |
| 5 | Contract missing EXT/ELC attribute for extended window | Add contract attribute |
| 6 | Server time zone mismatch | Infrastructure fix — verify QDateTime.NowS |
| 7 | Processing delay caused race condition | Code fix — buffer or single-point evaluation |
| 8 | Cycle not defined in PACTRL_CYCLE for the gas day | Add cycle definition |

### Known Historical Bugs
| ADO # | Issue | Status |
|-------|-------|--------|
| #1609881 | RuleNN00009011 not firing for external users editing certain fields | Closed/Fixed |

---

## 7. Cycle Indicator Issues (ENMQR320/321)

### When Cycle Indicator Is Sent But Invalid
- **ENMQR320:** The CS segment has a cycle indicator but it doesn't match any valid cycle for the TSP
- **ENMQR321:** The CS segment is present but the cycle indicator value is missing

### When Cycle Indicator Is NOT Sent
- Most common scenario — system auto-assigns via `GetOpenCycleByDay()`
- The N9 segment for cycle indicator is commented out in `QEdiNMSTIn18.cs`
- Auto-assignment uses `Constants.DeadlineCategory.Nomination` + `Constants.DeadlineType.OnTime`

### TSPs That Typically Don't Send Cycle Indicator
Many TSPs rely on auto-assignment. Check the inbound NMST file structure to confirm:
- If no CS segment with cycle indicator → auto-assigned
- If CS segment present → uses the specified cycle

### Related Warnings
- **WNMQR304:** "Cycle Indicator not used" — sent when system ignores the provided cycle
- **WNMQR305/306:** Warnings for invalid/missing cycle indicator

---

## 8. Contract & Location Errors

### ENMQR301 — Invalid Service Requester Contract
**Investigation:**
```sql
SELECT c.CTR_NO, c.CTR_NM, c.TOS_CD, c.NOM_MODEL_CD,
       c.EFF_DT_FROM, c.EFF_DT_TO, c.IS_ACTIVE
FROM NNCTRL_CTR c
WHERE c.TSP_NO = <TSP_NO>
  AND c.CTR_NO = '<CONTRACT_FROM_EDI>'
  AND '<GAS_DAY>' BETWEEN c.EFF_DT_FROM AND c.EFF_DT_TO;
```
**Common causes:** Contract expired, wrong contract number in EDI, contract not effective yet

### ENMQR525-538 — Location Errors
**Investigation:**
```sql
-- Check location exists
SELECT l.ID_LOC, l.LOC_NM, l.IS_ACTIVE
FROM NNCTRL_LOC l
WHERE l.TSP_NO = <TSP_NO> AND l.ID_LOC = '<LOCATION_ID>';

-- Check location is on contract path
SELECT cp.CTR_NO, cp.ID_REC_LOC, cp.ID_DEL_LOC
FROM NNCTRL_CTR_PATH cp
WHERE cp.TSP_NO = <TSP_NO>
  AND cp.CTR_NO = '<CONTRACT>'
  AND (cp.ID_REC_LOC = '<LOC>' OR cp.ID_DEL_LOC = '<LOC>');
```

---

## 9. Quantity Errors

### ENMQR502 — Invalid Quantity
Non-numeric, negative, or otherwise malformed quantity value in QTY segment.

### ENMQR504 — Nom Quantity Exceeds Daily Contract Quantity
**Investigation:**
```sql
SELECT c.CTR_NO, c.CTR_MDQ, c.OVRD_CTR_MDQ
FROM NNCTRL_CTR c
WHERE c.TSP_NO = <TSP_NO> AND c.CTR_NO = '<CONTRACT>';

SELECT SUM(nd.REC_QTY) AS TOTAL_REC, SUM(nd.DEL_QTY) AS TOTAL_DEL
FROM NNCTRL_NOM_DTL nd
WHERE nd.TSP_NO = <TSP_NO>
  AND nd.SR_CTR_NO = '<CONTRACT>'
  AND nd.BEG_GAS_DAY = '<GAS_DAY>';
```

---

## 10. Header Errors (ENMQR100-116)

These occur during Area 1 parsing before any nomination data is processed.

### ENMQR109/110 — TSP Errors
```sql
SELECT t.TSP_NO, t.TSP_NM, t.IS_ACTIVE FROM NNCTRL_TSP t
WHERE t.TSP_NO = <TSP_NO>;
```

### ENMQR111/112 — Service Requester Errors
```sql
SELECT bp.BA_NO, bp.BA_NM, bp.IS_ACTIVE FROM NNCTRL_BP bp
WHERE bp.TSP_NO = <TSP_NO>
  AND bp.BA_NO = '<SR_BP_NO_FROM_EDI>';
```

---

## 11. EDI Transport Errors (EEDM)

These occur at the InboundServer level BEFORE the NMST is parsed.

| Code | Description | Investigation |
|------|-------------|--------------|
| EEDM100 | Missing 'from' Common Code | Check ISA/GS sender ID |
| EEDM101 | Missing 'to' Common Code | Check ISA/GS receiver ID |
| EEDM102 | Missing Input Format | Check file format specification |
| EEDM103 | Missing data file | Empty or corrupt file |
| EEDM105 | Invalid 'from' Common Code | Sender not in TPA config |
| EEDM106 | Invalid 'to' Common Code | Receiver mismatch |
| EEDM107 | Invalid input format | Wrong format type |
| EEDM999 | System Error | Check InboundServer logs |

**EEDM errors don't reach the NMST parser.** They are returned before any nom processing.

---

## 12. LI vs BI Error Blocking

### Error Classification
| NomStatCode | Level | Source | Blocks Others? |
|-------------|-------|--------|---------------|
| **VI** | Valid | All rules passed | No |
| **BI** | Business Invalid | `IValidationRuleBaseNominationBusiness` | Configurable |
| **LI** | Line Invalid | `IValidationRuleBaseNominationSecurity` or `IValidationRuleBaseNominationForeignKey` | **YES — blocks ALL noms in batch** |

### LI Blocking Behavior
When ANY nom in a submission batch gets `NomStatCode = "LI"`:
1. The LI nom is saved with its error
2. **All other noms in the same batch that are NOT LI** get a secondary error:
   - NAESB 1.8+: `SUBDTL999` — "This nomination was not submitted due to the presence of an LI error"
   - NAESB < 1.8: `SUBDTL998`
3. This is controlled by the `BlockBINomSubmission` config — when true, BI errors also trigger blocking

### Impact on EDI
A single late nomination (ENMQR315/LI) in an EDI file can block ALL other valid nominations in the same file. The client sees SUBDTL999 errors on noms that are otherwise valid.

**Fix strategy:** If only some gas days are late, the system's `SplitNonTimelyRecords()` method should separate timely from non-timely days. However, if ALL days in the file are for the same closed cycle, all will fail.

---

## 13. Key Code Files & Repos

### Quorum.QPTM.Batch (e024d80b-5c45-411c-93e1-78e2798ed885)
| File | Purpose |
|------|---------|
| `Quorum.QPTM.EDI.DataSets/G873NMST/QEdiNMSTIn18.cs` | **Inbound NMST parser & processor** |
| `Quorum.QPTM.EDI.DataSets/G874NMQR/QEdiNMQROut18.cs` | Outbound NMQR writer |
| `Quorum.QPTM.EDI.Framework/QEdiControlDataQPTM.cs` | EDI control data (configs) |
| `Quorum.QPTM.EDI.Framework/AQEdiInboundDataset.cs` | Base class for inbound datasets |
| `Quorum.QPTM.EDI.Framework/NomPrepHelper.cs` | Merge/split nomination helpers |

### Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
| File | Purpose |
|------|---------|
| `Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService.cs` | **Nomination service (submit, validate, cycle)** |
| `Quorum.QPTM.DataCache/CycleManager.cs` | **Cycle deadline evaluation** |
| `Quorum.QPTM.DataCacheImpl/CycleCache.cs` | Cycle data caching |
| `Quorum.QPTM.Validations/ValidationRuleHelper/ValidationRuleHelper.cs` | Validation helper utilities |
| `Quorum.QPTM.ServiceCore/QPTMServiceCore.cs` | Core service methods |
| `Quorum.QPTM.ServiceInterface/Interfaces/IQPTMCycleService.cs` | Cycle service interface |
| `Quorum.QPTM.ServiceInterface/Interfaces/IQPTMNominationService.cs` | Nomination service interface |
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerNominationSubmissionBase.cs` | UI submission controller |

### Validation Rules (various client repos)
| File | Repo | Purpose |
|------|------|---------|
| `RuleNN00009011.cs` | DUT.QPTM.Web / QTR.QPTM.Web | **Late nomination check** |
| `RuleNN00009016.cs` | NMGC.QPTM.Web / NMG.QPTM.Web | Client-specific late nom variant |
| `RuleDOHNN6001.cs` | DOH.QPTM.Web | DOH-specific late nom variant |

### Quorum.EDIServ (30cdad90-e4ae-405c-8d67-747955bcf870)
| File | Purpose |
|------|---------|
| `Quorum.EDIServ/InboundServer.cs` | HTTP inbound handler (EEDM errors) |
| `Quorum.EDIServ/OutboundServer.cs` | HTTP outbound handler |

### Quorum.EDI.Framework (02742829-b8c5-4531-bb27-163f9a501621)
| File | Purpose |
|------|---------|
| `Quorum.EDI.Framework/EdiBase/EdiGlobals.cs` | NAESB date/time formats |
| `Quorum.EDI.Framework/EdiBase/EdiUtility.cs` | EDI utility methods |
| `Quorum.EDI.Framework/Dataset/AEdiInboundDataset.cs` | Base inbound dataset |

### Database Repos
| Repo | Purpose |
|------|---------|
| Quorum.QGM.Database (8bfba59c-f3dd-46ea-8d0a-f2687a763258) | QCODE_ED_ERROR definitions |
| APL.QPTM.Database (2e1fb9e5-a46a-4257-b99a-fd47721dd399) | QPTM schema + migrations |

---

## 14. Database Tables Reference

### EDI Processing Tables
| Table | Purpose |
|-------|---------|
| `EDTRAN` | EDI transaction log (inbound/outbound) |
| `EDTRAN_QR_ERROR` | Quick Response error records |
| `EDTRAN_FILE` | EDI file storage |
| `QCODE_ED_ERROR` | EDI error code definitions (NAESB standard) |

### Nomination Tables
| Table | Purpose |
|-------|---------|
| `NNCTRL_NOM_DTL` | Nomination detail records |
| `NNCTRL_NOM_HDR` | Nomination headers |
| `NNCTRL_NOM_ERROR` | Nomination validation errors |

### Cycle Tables
| Table | Purpose |
|-------|---------|
| `PACTRL_CYCLE` | Cycle definitions per TSP |
| `QCODE_CYCLE_TYPE` | Cycle type metadata |
| `PACTRL_CYCLE_DEADLINE` | **Cycle deadline configuration** |

### Configuration Tables
| Table | Purpose |
|-------|---------|
| `NNCTRL_TSP` | TSP definitions |
| `NNCTRL_BP` | Business Partner definitions |
| `NNCTRL_TPA` | Trading Partner Agreements |
| `NNCTRL_CTR` | Contracts |
| `NNCTRL_CTR_ATTR` | Contract attributes (EXT, ELC, ATT, etc.) |
| `NNCTRL_CTR_PATH` | Contract paths (receipt/delivery locations) |
| `NNCTRL_LOC` | Location definitions |
| `NNCTRL_LOC_ATTR` | Location attributes |
| `QARCH_VALD_RULE` | Validation rule definitions |
| `QARCH_GLOBAL_CONFIG` | Global configuration settings |
| `QARCH_TSP_CONFIG` | TSP-specific configuration settings |

---

## 15. Diagnostic SQL Queries

### A. EDI Transaction Investigation
```sql
-- Find EDI transaction by reference number
SELECT et.EDI_TRANS_ID, et.TSP_NO, et.TPA_ID, et.REF_ID,
       et.DIRECTION_CD, et.DATASET_NM, et.STATUS_CD,
       et.RECV_DT, et.PROC_DT, et.UPDT_DT, et.FILE_NM
FROM EDTRAN et
WHERE et.TSP_NO = <TSP_NO>
  AND et.REF_ID = '<REF_ID>'
ORDER BY et.RECV_DT DESC;
```

### B. QR Errors for a Transaction
```sql
SELECT qr.SEQ_NO, qr.REF_ID, qr.TRACK_ID, qr.CTR_NO,
       qr.BEG_GAS_DAY, qr.END_GAS_DAY,
       qr.NAESB_ERROR_CD, qr.ERROR_DESCR
FROM EDTRAN_QR_ERROR qr
WHERE qr.TSP_NO = <TSP_NO>
  AND qr.REF_ID = '<REF_ID>'
ORDER BY qr.SEQ_NO;
```

### C. All Cycle Deadlines for a TSP
```sql
SELECT cd.ID_CYCLE, ct.CYCLE_TYPE_DESCR,
       cd.DEADLINE_CATEGORY, cd.DEADLINE_TYPE, cd.USER_TYPE_CD,
       cd.DEADLINE_DAY_OFFSET, cd.DEADLINE_TIME, cd.DEADLINE_TZ,
       cd.EFF_DT_FROM, cd.EFF_DT_TO
FROM PACTRL_CYCLE_DEADLINE cd
LEFT JOIN QCODE_CYCLE_TYPE ct
  ON cd.ID_CYCLE = ct.ID_CYCLE AND cd.TSP_NO = ct.TSP_NO
WHERE cd.TSP_NO = <TSP_NO>
  AND cd.DEADLINE_CATEGORY = 'NOM'
ORDER BY cd.ID_CYCLE, cd.DEADLINE_TYPE, cd.USER_TYPE_CD;
```

### D. Specific Cycle Deadline Check
```sql
SELECT cd.ID_CYCLE, cd.DEADLINE_TYPE, cd.USER_TYPE_CD,
       cd.DEADLINE_DAY_OFFSET, cd.DEADLINE_TIME, cd.DEADLINE_TZ,
       cd.EFF_DT_FROM, cd.EFF_DT_TO
FROM PACTRL_CYCLE_DEADLINE cd
WHERE cd.TSP_NO = <TSP_NO>
  AND cd.ID_CYCLE = <CYCLE_ID>
  AND cd.DEADLINE_CATEGORY = 'NOM'
  AND '<GAS_DAY>' BETWEEN cd.EFF_DT_FROM AND cd.EFF_DT_TO
ORDER BY cd.DEADLINE_TYPE, cd.USER_TYPE_CD;
```

### E. Nomination Details for a Gas Day
```sql
SELECT nd.SR_CTR_NO, nd.BEG_GAS_DAY, nd.END_GAS_DAY,
       nd.ID_CYCLE, nd.NOM_STAT_CD, nd.TRANS_TYPE_CD,
       nd.ID_REC_LOC, nd.ID_DEL_LOC, nd.REC_QTY, nd.DEL_QTY,
       nd.SUBMIT_DT, nd.USER_ID, nd.SYS_SRC_CD
FROM NNCTRL_NOM_DTL nd
WHERE nd.TSP_NO = <TSP_NO>
  AND nd.BEG_GAS_DAY = '<GAS_DAY>'
  AND nd.SR_BP_NO = '<SHIPPER_BP_NO>'
ORDER BY nd.ID_CYCLE, nd.SR_CTR_NO;
```

### F. TPA and User Type Check
```sql
SELECT tpa.TPA_ID, tpa.TPA_NM, tpa.BA_NO, tpa.SECURITY_USER_ID,
       su.USER_TYPE_CD, su.USER_NM
FROM NNCTRL_TPA tpa
JOIN QARCH_SECURITY_USER su ON tpa.SECURITY_USER_ID = su.SECURITY_USER_ID
WHERE tpa.TSP_NO = <TSP_NO>
  AND tpa.IS_ACTIVE = 1
  AND (tpa.TPA_NM LIKE '%<SHIPPER>%' OR tpa.BA_NO = '<BP_NO>');
```

### G. Validation Rule Configuration
```sql
SELECT vr.FUNC_AREA_CD, vr.VALD_RULE_CD, vr.VALD_RULE_DESCR,
       vr.NAESB_CD, vr.IS_ALLOW_OVRD, vr.IS_ACTIVE,
       vr.VALD_RULE_TYPE_CD, vr.SEVERITY_CD
FROM QARCH_VALD_RULE vr
WHERE vr.VALD_RULE_CD LIKE 'NN%'
  AND vr.IS_ACTIVE = 1
ORDER BY vr.VALD_RULE_CD;
```

### H. Contract Attribute Check (Extended Deadlines)
```sql
SELECT ca.CTR_NO, ca.TOS_ATTR_CD, ca.IS_ATTR_TRUE, ca.EFF_DT_FROM, ca.EFF_DT_TO
FROM NNCTRL_CTR_ATTR ca
WHERE ca.TSP_NO = <TSP_NO>
  AND ca.CTR_NO = '<CONTRACT_NO>'
  AND ca.TOS_ATTR_CD IN ('EXT', 'ELC', 'ATT');
```

### I. Recent EDI Errors for a TSP
```sql
SELECT qr.NAESB_ERROR_CD, COUNT(*) AS ERROR_COUNT,
       MIN(qr.BEG_GAS_DAY) AS FIRST_GAS_DAY,
       MAX(qr.BEG_GAS_DAY) AS LAST_GAS_DAY
FROM EDTRAN_QR_ERROR qr
WHERE qr.TSP_NO = <TSP_NO>
  AND qr.BEG_GAS_DAY >= DATEADD(month, -1, GETDATE())
GROUP BY qr.NAESB_ERROR_CD
ORDER BY ERROR_COUNT DESC;
```

---

## 16. Global Configs Affecting EDI

| Config Key | Purpose | Impact |
|------------|---------|--------|
| `SEND_NMST_QUICK_RESPONSE` | Controls whether NMQR is sent | 0=no NMQR sent (errors still logged) |
| `USE_TT_BUY_SELL` | Title Transfer Buy/Sell conversion | Affects ActnCode for TT noms |
| `DEFAULT_NOM_SUBSEQUENT_TO_TRUE` | Auto-set IsNomSubsCycle flag | When no nom subsequent specifier in EDI |
| `BLOCK_BI_NOM_SUBMISSION` | Treat BI like LI for blocking | When true, BI errors block other noms |
| `ALLOW_RECALC_HEATING_FACTOR` | Recalculate heating factor on EDI | TSP-specific, adds processing time |
| `NOM_RULE_NN00009011_ENABLED` | Enable/disable late nom rule | If disabled, late noms pass validation |

**To check configs:**
```sql
SELECT gc.CONFIG_KEY, gc.CONFIG_VALUE, gc.CONFIG_DESCR
FROM QARCH_GLOBAL_CONFIG gc
WHERE gc.CONFIG_KEY LIKE '%EDI%' OR gc.CONFIG_KEY LIKE '%NMST%'
   OR gc.CONFIG_KEY LIKE '%LATE%' OR gc.CONFIG_KEY LIKE '%BLOCK%BI%'
   OR gc.CONFIG_KEY LIKE '%QUICK_RESPONSE%';

-- TSP-specific config overrides:
SELECT tc.TSP_NO, tc.CONFIG_KEY, tc.CONFIG_VALUE
FROM QARCH_TSP_CONFIG tc
WHERE tc.TSP_NO = <TSP_NO>;
```

---

## 17. TSP-Specific EDI Behaviors

### Things That Vary by TSP
1. **Cycle deadline times** — Each TSP defines its own deadlines
2. **NAESB version** — 1.8, 1.9, or 2.0 (affects segment parsing)
3. **Cycle indicator usage** — Some TSPs send it, many don't
4. **Model types** — PT (Pathed), PNT (Point-to-Point), N (Non-Pathed)
5. **Extended deadline attributes** — EXT, ELC contract attributes
6. **Fuel calculation** — Some TSPs require it, others don't
7. **Buy/Sell conversion** — USE_TT_BUY_SELL config
8. **Nom Subsequent flag** — DEFAULT_NOM_SUBSEQUENT_TO_TRUE config

### Client-Specific Repos
Many clients have their own repos with custom validation rules:
```
<CLIENT>.QPTM.Web      - Custom web/validation code
<CLIENT>.QPTM.Database  - Custom DB scripts
<CLIENT>.QPTM.Metadata  - Custom metadata/configs
<CLIENT>.QPTM.Batch     - Custom batch processing (rare)
```

**Always check if the client has a custom override of the standard validation rules** by searching:
```
curl "https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults?api-version=7.0"
  -d '{"searchText": "<RuleID> repo:<CLIENT>.QPTM", "$top": 10}'
```

---

## 18. Common Root Causes & Fixes

### EDI Error → Root Cause Matrix

| Error | Most Common Cause | Second Most Common | Investigation Priority |
|-------|------------------|-------------------|----------------------|
| ENMQR315 | Cycle deadline config | Timing race condition | Check PACTRL_CYCLE_DEADLINE first |
| ENMQR301 | Contract expired/inactive | Wrong contract # in EDI | Check NNCTRL_CTR effective dates |
| ENMQR307 | Model type mismatch | Wrong CS05 in EDI | Compare nom vs contract model |
| ENMQR525/532 | Location deactivated | Location not on contract | Check NNCTRL_LOC + CTR_PATH |
| ENMQR504 | Legitimate over-MDQ | Shared MDQ not calculated | Check CTR_MDQ / OVRD_CTR_MDQ |
| ENMQR109 | TSP deactivated | Wrong N1 ID in EDI | Check NNCTRL_TSP |
| ENMQR111 | Shipper deactivated | TPA expired | Check NNCTRL_BP + NNCTRL_TPA |
| EEDM105/106 | TPA config wrong | Common code mismatch | Check NNCTRL_TPA ISA/GS codes |
| SUBDTL999 | Another nom has LI error | - | Find the root LI error first |

### Fix Categories
1. **Data/Config fix** — Update DB table rows (deadline, contract, location, TPA)
2. **EDI file fix** — Client needs to correct their EDI format/data
3. **Code fix** — Requires ADO bug, development PR, QA, deployment
4. **Infrastructure fix** — Server time, connectivity, timeout settings

---

## 19. Escalation Decision Tree

```
EDI Error Reported
│
├─ Is it a Transport Error (EEDM)?
│  ├─ YES → Check InboundServer logs, TPA config, network
│  └─ NO → Continue
│
├─ Is it a Header Error (ENMQR1xx)?
│  ├─ YES → Check TSP/SR setup, TPA configuration
│  └─ NO → Continue
│
├─ Is it ENMQR315 (Late Nom)?
│  ├─ YES → Check cycle deadline config for TSP/cycle
│  │  ├─ Deadline config says cycle should be open → POSSIBLE CODE BUG
│  │  │  → Check EDTRAN timestamps for processing delay
│  │  │  → Check server time zone
│  │  │  → If confirmed → Create ADO Bug
│  │  └─ Deadline config says cycle was closed → EXPECTED BEHAVIOR
│  │     → Inform client of correct deadline times
│  │     → Check if EXT/ELC attribute should apply
│  └─ NO → Continue
│
├─ Is it ENMQR301-307 (Contract/Model)?
│  ├─ YES → Check contract setup, effective dates, model type
│  └─ NO → Continue
│
├─ Is it ENMQR5xx (Location/Quantity)?
│  ├─ YES → Check location setup, contract paths, MDQ
│  └─ NO → Continue
│
├─ Is it SUBDTL999 (Blocked by LI)?
│  ├─ YES → Find the ROOT LI error in the same submission
│  │  → Fix that error; all SUBDTL999 errors will resolve
│  └─ NO → Continue
│
└─ Unknown/Other error
   → Check QCODE_ED_ERROR for error definition
   → Search code for error code string
   → Escalate if needed
```

---

## 20. ADO Search Patterns

### Searching for Related Work Items
```bash
# WIQL queries via ADO REST API:
POST https://dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/wit/wiql?api-version=7.0

# By error code:
{"query": "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.Title] CONTAINS '<ERROR_CODE>' ORDER BY [System.CreatedDate] DESC"}

# By client + EDI:
{"query": "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.Title] CONTAINS '<CLIENT>' AND [System.Title] CONTAINS 'EDI' ORDER BY [System.CreatedDate] DESC"}

# By TSP name:
{"query": "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.Title] CONTAINS '<TSP_NAME>' ORDER BY [System.CreatedDate] DESC"}
```

### Searching Code
```bash
# Code search across all repos:
POST https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults?api-version=7.0
{"searchText": "<SEARCH_TERM>", "$top": 25, "$skip": 0}

# Code search in specific repo:
{"searchText": "<SEARCH_TERM> repo:<REPO_NAME>", "$top": 25, "$skip": 0}
```

### Key ADO Connection Details
```
Organization: QuorumSoftware
URL: https://dev.azure.com/QuorumSoftware
Project: QuorumSoftware
Search API: https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults
```

---

*Skill created: 2026-05-26*
*Based on: Case 26-01099834 investigation, QPTM source code analysis*
*Applicable to: All QPTM EDI nomination issues across all TSPs and clients*