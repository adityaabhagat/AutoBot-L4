# SKILL: QPTM Nomination Validation Engine Reference

**Version:** 1.0 | **Created:** 2026-05-26
**Use When:** Any nomination validation error, understanding why a nom was rejected, BI/LI errors

---

## Validation Engine Overview

### How Nominations Are Validated

```
SubmitNominations() called
    │
    ├─ Set cycles for noms without IdCycle
    ├─ Create time slices (split multi-day noms into daily records)
    │
    ├─ Run Validation Rules (ordered by rule type):
    │   │
    │   ├─ 1. LINE RULES (IValidationRuleBaseNominationLine)
    │   │     → Fail = NomStatCode "LI" (Line Invalid)
    │   │     → Cannot be overridden
    │   │     → Example: RuleNN00009011 (late nom)
    │   │
    │   ├─ 2. SECURITY RULES (IValidationRuleBaseNominationSecurity)
    │   │     → Fail = NomStatCode "LI"
    │   │     → Cannot be overridden
    │   │
    │   ├─ 3. FOREIGN KEY RULES (IValidationRuleBaseNominationForeignKey)
    │   │     → Fail = NomStatCode "LI"
    │   │     → Cannot be overridden
    │   │
    │   └─ 4. BUSINESS RULES (IValidationRuleBaseNominationBusiness)
    │         → Fail = NomStatCode "BI" (Business Invalid)
    │         → CAN be overridden by user
    │         → Example: RuleNN00009965 (shared MDQ)
    │
    ├─ Save nomination records
    └─ Return results with errors
```

### NomStatCode Values
| Code | Name | Meaning | Overridable? |
|------|------|---------|-------------|
| **VI** | Valid | All rules passed | N/A |
| **BI** | Business Invalid | Business rule failed | YES |
| **LI** | Line Invalid | Line/Security/FK rule failed | NO |

---

## Validation Rule Types

### Line Validation Rules (`ValidationRuleBaseNominationLine`)
- **Signature:** `Validate(ActivityDetailDO, DateTime begGasDay, QRuleDataNominationLine ruleData)`
- **Validates:** One nom at a time, one gas day at a time
- **Failure:** NomStatCode = "LI" (blocks entire batch in EDI)
- **Override:** NOT allowed

**Common Line Rules:**
| Rule ID | Description | NAESB Code |
|---------|-------------|------------|
| NN00009011 | Late nomination / retroactive nom check | ENMQR315 |

### Business Validation Rules (`ValidationRuleBaseNominationBusiness`)
- **Signature:** `Validate(IList<ActivityDetailDO> nominationCollection, DateTime begGasDay, QRuleDataNominationBusiness ruleData)`
- **Validates:** Collection of noms together (can check totals, MDQ, etc.)
- **Failure:** NomStatCode = "BI"
- **Override:** Allowed (user can override and resubmit)

**Common Business Rules:**
| Rule ID | Description | NAESB Code |
|---------|-------------|------------|
| NN00009965 | Shared MDQ with pool-to-pool exclusion | ENMQR504 |
| NN00009016 | Client-specific late nom variants | ENMQR315 |

### Security Validation Rules (`ValidationRuleBaseNominationSecurity`)
- **Validates:** User permissions, contract access
- **Failure:** NomStatCode = "LI"
- **Override:** NOT allowed

### Foreign Key Validation Rules (`ValidationRuleBaseNominationForeignKey`)
- **Validates:** Data integrity (location exists, contract exists, etc.)
- **Failure:** NomStatCode = "LI"
- **Override:** NOT allowed

---

## Validation Rule Configuration

### QARCH_VALD_RULE Table
```sql
SELECT vr.FUNC_AREA_CD,        -- Functional area (NN = Nomination)
       vr.VALD_RULE_CD,        -- Rule code (e.g., NN00009011)
       vr.VALD_RULE_DESCR,     -- Human-readable description
       vr.NAESB_CD,            -- NAESB error code mapping (e.g., ENMQR315)
       vr.IS_ALLOW_OVRD,       -- Can user override? (0/1)
       vr.IS_ACTIVE,           -- Is rule enabled? (0/1)
       vr.VALD_RULE_TYPE_CD,   -- Rule type (LINE/BUSINESS/SECURITY/FK)
       vr.SEVERITY_CD          -- Error severity
FROM QARCH_VALD_RULE vr
WHERE vr.FUNC_AREA_CD = 'NN'
  AND vr.IS_ACTIVE = 1
ORDER BY vr.VALD_RULE_CD;
```

### TSP-Specific Rule Enable/Disable
Some rules can be enabled/disabled per TSP via global/TSP config:
```sql
SELECT tc.CONFIG_KEY, tc.CONFIG_VALUE
FROM QARCH_TSP_CONFIG tc
WHERE tc.TSP_NO = <TSP_NO>
  AND tc.CONFIG_KEY LIKE '%NN%';
```

---

## Validation Data Dependencies

### QRuleDataNominationLine (Line Rule Data)
| Property | Description |
|----------|-------------|
| `ValidatingUserID` | User performing the submission |

### QRuleDataNominationBusiness (Business Rule Data)
| Property | Description |
|----------|-------------|
| `ValidatingUserID` | User performing the submission |
| `LatestCycleData` | Cycle information |
| `InventoryData` | Inventory/storage data |
| `NominationSubset` | Subset of noms being validated |

### QRuleDataNominationBase (Cached Lookups)
| Method | Description |
|--------|-------------|
| `GetContract()` | Cached contract lookup |
| `IsLocationAttributeTrue()` | Cached location attribute check |
| `IsContractAttributeTrue()` | Cached contract attribute check |
| `IsPathOnContract()` | Cached path-on-contract check |

---

## Finding Validation Errors

### From Salesforce Case
1. Get the gas day, TSP, and shipper from the case
2. Check the NMQR EDI file for error codes
3. Map NAESB code → validation rule via QARCH_VALD_RULE

### From Database
```sql
-- Nomination errors for a specific gas day
SELECT ne.TSP_NO, ne.BEG_GAS_DAY, ne.ID_CYCLE,
       ne.VALD_RULE_CD, ne.ERROR_MSG,
       ne.IS_OVRD, ne.NOM_STAT_CD
FROM NNCTRL_NOM_ERROR ne
WHERE ne.TSP_NO = <TSP_NO>
  AND ne.BEG_GAS_DAY = '<GAS_DAY>'
  AND ne.SR_BP_NO = '<SHIPPER>'
ORDER BY ne.VALD_RULE_CD;
```

### From EDI QR Errors
```sql
SELECT qr.NAESB_ERROR_CD, qr.ERROR_DESCR, qr.CTR_NO,
       qr.BEG_GAS_DAY, qr.END_GAS_DAY, qr.TRACK_ID
FROM EDTRAN_QR_ERROR qr
WHERE qr.TSP_NO = <TSP_NO>
  AND qr.REF_ID = '<EDI_REF>'
ORDER BY qr.SEQ_NO;
```

---

## Client-Specific Validation Overrides

### Pattern
Many clients have custom validation rule implementations in their own repos:
```
<CLIENT>.QPTM.Web/<CLIENT>.QPTM.Validation.Rules.Nomination/
    BusinessRules/     → Custom business rules
    LineValidations/   → Custom line rules
```

### How to Check
```bash
# Search for a specific rule in client repo
POST https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults
{"searchText": "class RuleNN00009011 repo:<CLIENT>.QPTM"}

# If count = 0 → client uses base QPTM rule
# If count > 0 → client has custom override
```

### Known Client-Specific Rules
| Client | Rule | Description |
|--------|------|-------------|
| DUT | RuleNN00009011 | Custom late nom check with EXT/ELC attribute support |
| QTR | RuleNN00009011 | Custom late nom check |
| NMGC | RuleNN00009016 | Client-specific late nom variant |
| NMG | RuleNN00009016 | Client-specific late nom variant |
| DOH | RuleDOHNN6001 | DOH-specific late nom with custom logic |
| EQT | (none) | Uses base QPTM rules — no overrides found |

---

## Validation Error Override Flow (UI Only)

```
1. User submits nomination → gets BI error
2. Error shown on screen with "Override" option
3. User checks override checkbox → resubmits
4. System sets ActivityDetailErrorDO.IsOvrd = true
5. Validation re-runs but skips overridden rules
6. Nom saves as VI (valid) with overridden error logged
```

**Note:** LI errors CANNOT be overridden. The nomination must be corrected.

**Note:** EDI submissions CANNOT override errors. All errors are returned in the NMQR.

---

## Key Code Paths

### Validation Engine Execution (QPTMNominationService.cs ~line 3990)
```csharp
foreach (IValidationRule rule in rules)
{
    bool isValid;
    if (rule is IValidationRuleBaseNominationBusiness)
    {
        isValid = ((IValidationRuleBaseNominationBusiness)rule).Validate(
            nominationCollection, begGasDay, businessRuleData);
    }
    else if (rule is IValidationRuleBaseNominationLine)
    {
        isValid = ((IValidationRuleBaseNominationLine)rule).Validate(
            activity, begGasDay, lineRuleData);
    }
    // ... other rule types
    
    if (!isValid)
    {
        ActivityDetailErrorDO error = new ActivityDetailErrorDO();
        error.ValdRuleCode = rule.RuleXRef.ValdRuleCode;
        error.ErrorMsg = rule.RuleXRef.ValdRuleDescr;
        error.IsAllowOvrd = rule.RuleXRef.IsAllowOvrd;
        
        if (rule is IValidationRuleBaseNominationBusiness)
            error.NomStatCode = "BI";
        else
            error.NomStatCode = "LI";
    }
}
```

### ValidationRuleHelper Key Methods
| Method | Purpose |
|--------|---------|
| `GetFirstOpenCycle(activityDetailDO)` | Get first open cycle for a nom |
| `IsUserInternal(userId)` | Check if user is internal type |
| `UseSrK99999OnPntBuysSells` | Config for PNT buy/sell handling |

---

*Reference for QPTM nomination validation investigations*
*See SKILL_EDI_Troubleshooting.md for EDI-specific error reference*
*See SKILL_Cycle_Deadline_Reference.md for cycle deadline details*