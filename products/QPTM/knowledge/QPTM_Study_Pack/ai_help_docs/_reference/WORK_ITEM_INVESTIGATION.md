---
title: Work Item Investigation - Required First Steps
category: process
applies_to: All Work Items
keywords: work items, ADO, Azure DevOps, investigation, troubleshooting, bugs, tickets
last_updated: 2025-12-11
---

# Work Item Investigation - Required First Steps

> **Scope**: This workflow applies when working on a specific Work Item (bug, ticket, issue). For general feature understanding without a WI, use `/load-process <CODE>` (Claude Code) or read the feature docs directly from `AI_Agent_Help_Docs/{feature}/`.

## Required Process

**When a Work Item number is mentioned, AI agents must follow these steps in order.**

### Trigger Condition
When user input contains ANY of these patterns:
- "WI #[number]"
- "Work Item [number]"
- "ticket [number]"
- "bug [number]"
- "issue [number]"
- "[number]" in context of Azure DevOps/ADO

### Mandatory Execution Flow

```
STEP 1: RETRIEVE WI (Use: azure-devops tools)
   ↓
STEP 2: EXTRACT details (Module, Title, Description, Comments)
   ↓
STEP 3: IDENTIFY FEATURE (Check: AI_Agent_Help_Docs/QUICK_REFERENCE.md keyword mapping)
   ↓
STEP 4: LOAD DOCS (Load ALL 3 docs in parallel)
   ├─→ AI_Agent_Help_Docs/{feature}/domain.md
   ├─→ AI_Agent_Help_Docs/{feature}/architecture.md
   └─→ AI_Agent_Help_Docs/{feature}/troubleshooting.md
   ↓
STEP 5: SEARCH historical WIs/issues (In troubleshooting doc)
   ↓
STEP 6: PROVIDE RESPONSE (With full context from docs)
```

**CRITICAL**: Steps 1-5 are MANDATORY. Never skip to Step 6 without executing 1-5 first.

---

## Why This Process Matters

### ❌ Without Work Item Details
- Waste time investigating the wrong problem
- Provide generic, unhelpful troubleshooting steps
- Miss critical context (customer, environment, specific symptoms)
- Cannot provide targeted solutions
- Duplicate investigation already done by others

### ✅ With Work Item Details
- Understand exact problem and scope
- Target specific code/data/configuration
- Leverage past investigation in comments
- Provide relevant, actionable guidance
- Focus efforts efficiently

---

## Required Workflow

### Step 1: Retrieve Work Item from Azure DevOps

When a user mentions a Work Item number (e.g., "WI #12345"), **immediately** search for it in Azure DevOps:

```bash
# Use Azure DevOps tools to retrieve WI details
# Project: QuorumSoftware
# Work Item ID: [number from user]
```

**Do NOT proceed with generic troubleshooting until you have the WI details.**

---

### Step 2: Extract Required Information

From the Work Item, extract and document:

#### Essential Fields

| Field | What to Extract | Why It Matters |
|-------|----------------|----------------|
| **Title** | Brief description | Understand the core issue |
| **Description** | Full problem statement | Get context and background |
| **Repro Steps** | How to reproduce | Know exact scenario to test |
| **Acceptance Criteria** | What defines success | Understand expected outcome |
| **Customer** | Which customer affected | Customer-specific configurations |
| **Environment** | PRD/UAT/UPG/etc. | Environment-specific behavior |
| **Module** | Scheduling/Nominations/etc. | Which code area to focus on |
| **State** | Active/Resolved/Closed | Current status of issue |
| **Resolution** | How it was fixed (if closed) | Learn from past solution |
| **Comments** | Investigation history | Avoid duplicating work |
| **Related WIs** | Linked issues | Related problems or dependencies |

#### Specific Technical Details

Extract these specifics from Description/Repro Steps:
- **Gas Days**: Specific dates affected
- **Contracts**: Contract numbers involved
- **Locations**: Receipt/delivery locations
- **TSP**: Which transportation service provider
- **Cycle**: Timely, Evening, Intraday
- **Quantities**: Expected vs. actual values
- **Error Messages**: Exact error text or warnings
- **Configuration**: Config settings mentioned
- **Process Codes**: Which batch processes (NNCLASSFY, SCREDUCE, etc.)
- **User Actions**: Specific UI interactions that trigger issue

---

### Step 3: Analyze and Categorize

Determine the type of issue:

#### Issue Categories

**Incorrect Data/Calculations**
- Wrong quantities calculated
- Missing records
- Incorrect scheduled quantities
- Bad capacity calculations

**Validation/Business Rule Failures**
- Classification errors
- Business validation errors
- Configuration not honored
- Rule set issues

**Performance Issues**
- Slow UI screens
- Timeout errors
- Batch process delays
- Memory issues

**Process Failures**
- Batch job fails
- Service layer errors
- Database errors
- Integration failures

**Missing Functionality**
- Feature request
- Enhancement
- Gap in current logic

---

### Step 4: Load Relevant Context

**Only after understanding the WI**, load the specific documentation needed:

#### If Issue is About a Specific Feature

Load the 3-doc set for that feature:
```
✓ AI_Agent_Help_Docs/{feature}/domain.md        - Business concepts
✓ AI_Agent_Help_Docs/{feature}/architecture.md   - Technical implementation
✓ AI_Agent_Help_Docs/{feature}/troubleshooting.md - Known issues & solutions
```

Example: For CAS issue
```
✓ AI_Agent_Help_Docs/capacity-scheduling-allocations/domain.md
✓ AI_Agent_Help_Docs/capacity-scheduling-allocations/architecture.md
✓ AI_Agent_Help_Docs/capacity-scheduling-allocations/troubleshooting.md
```

#### If Issue is Cross-Cutting

Load general documentation:
```
✓ CLAUDE.md - Project overview and routing table
✓ AI_Agent_Help_Docs/QUICK_REFERENCE.md - Feature/keyword mapping
```

#### If Issue Involves Multiple Areas

Load multiple feature doc sets based on related components mentioned in WI.

---

### Step 5: Search for Historical Issues

Check the troubleshooting document's "Common Issues" section:
- Look for similar symptoms
- Check if same error message appeared before
- Review resolutions of related issues
- Check linked/related WIs in Azure DevOps

---

### Step 6: Create Investigation Summary

Before proceeding with investigation, create a summary:

```markdown
## Work Item #[NUMBER] - Investigation Summary

**Title**: [WI Title]
**Customer**: [Customer Name]  
**Environment**: [PRD/UAT/UPG/etc.]
**Module**: [Scheduling/Nominations/etc.]
**Severity**: [Critical/High/Medium/Low]
**Status**: [Active/Resolved/Closed]

### Problem Statement
[2-3 sentences describing the core issue from Description]

### Specific Symptoms
- [Symptom 1 with specific details]
- [Symptom 2 with specific details]

### Expected vs. Actual Behavior
**Expected**: [What should happen]
**Actual**: [What is happening]

### Key Technical Details
- **Gas Days**: [dates]
- **Contracts**: [contract numbers]  
- **Error Messages**: [exact error text]
- **Configuration**: [relevant settings]
- **Processes**: [process codes]

### Related Work Items
- #[WI Number] - [Brief description]

### Investigation Focus
Based on the above, investigate:
1. [Specific code file/class to check]
2. [Specific data/table to query]
3. [Specific configuration to verify]

### Relevant Documentation
- [List specific docs loaded for this issue]
```

---

## Example: Correct vs. Incorrect Workflow

### ❌ INCORRECT Approach

```
User: "I have WI #12345 about CAS scheduled quantities being incorrect"

Agent Response:
"Here's a comprehensive checklist of 20 things to check:
1. Check CASTAG_OBJ_NOM_TRANS_GRP table
2. Check SCTRL_CA_SUMM table
3. Check transaction group configuration
4. Check rule sets
5. Check OAC values
... [15 more generic items]"
```

**Problems:**
- No understanding of actual issue
- Generic checklist not targeted to problem
- Wastes user's time with irrelevant checks
- Misses the real issue

---

### ✅ CORRECT Approach

```
User: "I have WI #12345 about CAS scheduled quantities being incorrect"

Agent Actions:
1. Search Azure DevOps for WI #12345 in QuorumSoftware project
2. Read WI details:
   - Title: "CAS Summary Shows Incorrect Scheduled Quantities for Clay Basin"
   - Description: "Scheduled quantities on CAS summary don't match expected reduction logic for Clay Basin type scheduling objects"
   - Environment: PRD
   - Gas Day: 2025-12-10
   - Scheduling Object Type: CBE (Clay Basin Entire Basin)
3. Map keywords: "CAS", "scheduled quantities", "Clay Basin", "reduction"
4. Load relevant docs:
   - domain/capacity-scheduling-allocations.md (reduction algorithms section)
   - architecture/capacity-scheduling-allocations.md (ReductionGroupMgrClayBasin)
   - troubleshooting/capacity-scheduling-allocations.md (common reduction issues)
5. Search troubleshooting doc: Find "Issue 6: Reduction Not Working Correctly" section
6. Provide targeted response:

Agent Response:
"I found WI #12345. This is about CAS scheduled quantities for Clay Basin 
scheduling objects not matching expected reduction logic in PRD for gas day 2025-12-10.

Clay Basin (CBE) uses a specialized reduction algorithm via ReductionGroupMgrClayBasin 
class. Based on similar historical issues, check:

1. Verify Clay Basin specific reduction logic:
   - Check ReductionGroupMgrClayBasin implementation in 
     Quorum.QPTM.ServiceCore.Scheduling/ReductionGroupMgrClayBasin.cs
   - Verify injection/withdrawal direction handling

2. Run diagnostic query to verify staging data:
```sql
SELECT 
    SCHD_OBJ_ID,
    SCHD_OBJ_TYPE_CD,
    DIRECTION_FLOW_CD,
    SUM(REC_QTY + DEL_QTY) AS TotalNominated,
    TRANS_GRP_RANK
FROM CASTAG_OBJ_NOM_TRANS_GRP
WHERE TSP_NO = @TspNo
  AND GAS_DAY = '2025-12-10'
  AND SCHD_OBJ_TYPE_CD = 'CBE'
GROUP BY SCHD_OBJ_ID, SCHD_OBJ_TYPE_CD, DIRECTION_FLOW_CD, TRANS_GRP_RANK
ORDER BY TRANS_GRP_RANK;
```

3. Check if reduction algorithm configuration is correct for Clay Basin:
   - Verify accounting method in PACTRL_TRANS_GRP
   - Check TSP-specific Clay Basin settings

Would you like me to investigate any of these areas further?"
```

**Benefits:**
- Understands exact issue from WI
- Provides targeted, relevant information
- References specific code locations
- Provides actionable diagnostic query
- Suggests next steps based on issue specifics
- Efficient use of time

---

## Templates

### Template: Initial WI Retrieval

```markdown
Let me retrieve the work item details first.

[Search Azure DevOps for WI #[NUMBER] in QuorumSoftware project]

From WI #[NUMBER]:
- **Issue**: [Brief summary]
- **Customer**: [Customer name]
- **Environment**: [Environment]
- **Status**: [Current status]

[If resolved]: This issue was already fixed. [Summary of resolution]
[If active]: Let me investigate this issue. [Next steps]
```

### Template: Investigation Plan

```markdown
Based on WI #[NUMBER], here's the targeted investigation plan:

**Problem**: [Specific issue from WI]

**Investigation Steps**:
1. [Specific step based on WI details]
2. [Specific step based on WI details]
3. [Specific step based on WI details]

**Code to Check**:
- [Specific file/class/method based on issue]

**Data to Verify**:
- [Specific query based on issue]

**Configuration to Review**:
- [Specific config setting based on issue]

Would you like me to proceed with step 1?
```

---

## Integration with Existing Documentation

This process should be the **first step** before using any feature-specific troubleshooting guide.

### Updated Workflow

```
1. User mentions Work Item
   ↓
2. Retrieve WI from Azure DevOps (THIS DOCUMENT)
   ↓
3. Extract details and understand issue (THIS DOCUMENT)
   ↓
4. Load relevant feature documentation
   ↓
5. Use feature-specific troubleshooting guide
   ↓
6. Provide targeted investigation/solution
```

### Document References

Link to this document from:
- `AI_Agent_Help_Docs/README.md` - Main documentation index
- `AI_Agent_Help_Docs/QUICK_REFERENCE.md` - Quick lookup guide
- All `{feature}/troubleshooting.md` files - Feature-specific guides
- `.github/copilot-instructions.md` - Main instructions
- `CLAUDE.md` - Claude Code auto-loaded routing

---

## Enforcement

**AI Agents/Copilot**: When a user mentions a Work Item number:
1. **STOP** - Do not provide generic guidance
2. **RETRIEVE** - Get WI details from Azure DevOps
3. **ANALYZE** - Extract and understand the issue
4. **PROCEED** - Use targeted investigation based on WI

**Human Developers**: Follow the same process:
1. Always read the full WI before investigating
2. Check comments for past investigation
3. Review related WIs
4. Document your findings in WI comments

---

## Related Documentation

- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Feature/keyword mapping
- [README.md](README.md) - Main documentation guide
- Feature troubleshooting: `{feature}/troubleshooting.md`

---

*Last updated: 2026-03-03*
*Document version: 2.0*
