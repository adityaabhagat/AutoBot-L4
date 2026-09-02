# SKILL: QPTM Cycle Deadline Quick Reference

**Version:** 1.0 | **Created:** 2026-05-26
**Use When:** Any case involving cycle timing, late noms, retroactive noms, or ENMQR315

---

## Cycle Deadline Lookup — Step-by-Step

### Step 1: Identify the Parameters
```
TSP_NO    = ?    (e.g., 24 for Equitrans)
GAS_DAY   = ?    (e.g., 2026-05-09)
CYCLE_ID  = ?    (e.g., 3 for ID3)
SUBMIT_TIME = ?  (e.g., 2:45 PM CST)
```

### Step 2: Query the Deadline
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

### Step 3: Calculate the Actual Deadline
```
Deadline DateTime = GAS_DAY + DEADLINE_DAY_OFFSET days + DEADLINE_TIME in DEADLINE_TZ

Example:
  GAS_DAY = 2026-05-09
  DEADLINE_DAY_OFFSET = 0  (same day as gas day)
  DEADLINE_TIME = 14:30:00
  DEADLINE_TZ = CST
  → Deadline = 2026-05-09 14:30:00 CST
```

### Step 4: Compare
```
If SUBMIT_TIME <= Deadline → Cycle is OPEN → Nom should be accepted
If SUBMIT_TIME >  Deadline → Cycle is CLOSED → ENMQR315 is correct
```

---

## NAESB Standard Cycles

| Cycle ID | NAESB Name | Typical Deadline (CCT) | Day Offset |
|----------|-----------|------------------------|------------|
| 1 | Timely | ~11:30 AM Day-1 | -1 |
| 2 | Evening | ~6:00 PM Day-1 | -1 |
| 3 | Intraday 1 (ID1) | ~10:00 AM Gas Day | 0 |
| 4 | Intraday 2 (ID2) | ~2:30-5:00 PM Gas Day | 0 |
| 5 | Intraday 3 (ID3) | ~7:00-9:00 PM Gas Day | 0 |

**CRITICAL:** These are NAESB guidelines. Each TSP sets its own actual deadlines.

---

## Deadline Type Variants

| Type Code | Name | Who Gets It | Notes |
|-----------|------|------------|-------|
| ONT | OnTime | Default for all | Standard deadline |
| EXT | Extended | Contracts with EXT attribute | Later deadline |
| ELC | Electronic | Contracts with ELC attribute | Even later deadline |

### Checking for Extended Deadlines
```sql
-- Does the contract have extended deadline attributes?
SELECT ca.CTR_NO, ca.TOS_ATTR_CD, ca.IS_ATTR_TRUE
FROM NNCTRL_CTR_ATTR ca
WHERE ca.TSP_NO = <TSP_NO>
  AND ca.CTR_NO = '<CONTRACT>'
  AND ca.TOS_ATTR_CD IN ('EXT', 'ELC')
  AND ca.IS_ATTR_TRUE = 1;
```

If the contract has EXT=true, the system uses the EXT deadline (usually later).
If ELC=true, it uses the ELC deadline.

---

## User Type Impact

| User Type | Code | Typical Deadline | Source |
|-----------|------|-----------------|--------|
| External | EXT | Earlier (stricter) | Standard TPA users |
| Internal | INT | Later (more lenient) | Pipeline operator users |

### How User Type Is Determined
```
EDI submissions → TPA Security User → check QARCH_SECURITY_USER.USER_TYPE_CD
UI submissions → Logged-in user → check QARCH_SECURITY_USER.USER_TYPE_CD
```

### Checking the TPA User Type
```sql
SELECT tpa.TPA_NM, tpa.SECURITY_USER_ID,
       su.USER_NM, su.USER_TYPE_CD
FROM NNCTRL_TPA tpa
JOIN QARCH_SECURITY_USER su ON tpa.SECURITY_USER_ID = su.SECURITY_USER_ID
WHERE tpa.TSP_NO = <TSP_NO>
  AND tpa.IS_ACTIVE = 1;
```

---

## Auto-Assignment vs. Manual Cycle

### When Cycle Is Auto-Assigned (EDI without CS segment):
1. `QEdiNMSTIn18.Proc_873_Area_2_Loop_DTM()` calls `GetOpenCycleByDay()`
2. Returns first open cycle for each day of the month
3. Assigned to `currDO.IdCycle`
4. Cached per year+month — NOT re-evaluated per nomination

### When Cycle Is Specified (UI or EDI with CS segment):
1. The specified cycle is used directly
2. Validation rule still checks if that cycle's deadline has passed
3. If deadline passed → ENMQR315

### When All Cycles Are Closed (Retroactive):
1. `GetOpenCycleByDay()` returns -1
2. System assigns `GetLastCycle()` (highest cycle number)
3. Validation rule fires → ENMQR315 (retroactive nom not allowed)
4. Unless retroactive noms are explicitly allowed for the TSP/config

---

## Race Condition Scenario

```
Timeline:
  2:45:00 PM — EDI file received
  2:45:05 PM — ReadFile: GetOpenCycleByDay() → ID3 is OPEN → assigns ID3
  2:45:10 PM — CalculateFuel() processing...
  2:49:30 PM — PrepareAndSubmit() → GetNominations()...
  2:50:00 PM — *** ID3 DEADLINE PASSES ***
  2:50:15 PM — SubmitNominations() → RuleNN00009011 checks deadline
  2:50:15 PM — DateTime.Now (2:50:15) > deadline (2:50:00) → ENMQR315!
```

**Detection:** Compare EDTRAN.RECV_DT (file received) vs. processing duration in MSG_LOG.

---

## All Cycles for a TSP — Complete View
```sql
-- Shows all nomination deadlines organized by cycle
SELECT cd.ID_CYCLE,
       ct.CYCLE_TYPE_DESCR,
       cd.DEADLINE_TYPE,
       cd.USER_TYPE_CD,
       CASE cd.DEADLINE_DAY_OFFSET
           WHEN -1 THEN 'Day Before Gas Day'
           WHEN 0 THEN 'Gas Day'
           WHEN 1 THEN 'Day After Gas Day'
       END AS DEADLINE_DAY,
       cd.DEADLINE_TIME,
       cd.DEADLINE_TZ,
       cd.EFF_DT_FROM,
       cd.EFF_DT_TO
FROM PACTRL_CYCLE_DEADLINE cd
LEFT JOIN QCODE_CYCLE_TYPE ct
  ON cd.ID_CYCLE = ct.ID_CYCLE AND cd.TSP_NO = ct.TSP_NO
WHERE cd.TSP_NO = <TSP_NO>
  AND cd.DEADLINE_CATEGORY = 'NOM'
  AND GETDATE() BETWEEN cd.EFF_DT_FROM AND cd.EFF_DT_TO
ORDER BY cd.ID_CYCLE, cd.DEADLINE_TYPE, cd.USER_TYPE_CD;
```

---

## Cycle Status Check — Point-in-Time
```sql
-- "Was cycle X open at time Y for gas day Z?"
-- Manual calculation:

-- 1. Get the deadline config
SELECT cd.DEADLINE_DAY_OFFSET, cd.DEADLINE_TIME, cd.DEADLINE_TZ
FROM PACTRL_CYCLE_DEADLINE cd
WHERE cd.TSP_NO = <TSP_NO>
  AND cd.ID_CYCLE = <CYCLE>
  AND cd.DEADLINE_CATEGORY = 'NOM'
  AND cd.DEADLINE_TYPE = 'ONT'  -- or EXT/ELC
  AND cd.USER_TYPE_CD = 'EXT'   -- or INT
  AND '<GAS_DAY>' BETWEEN cd.EFF_DT_FROM AND cd.EFF_DT_TO;

-- 2. Calculate: deadline = GAS_DAY + offset + time
-- 3. Compare: was SUBMIT_TIME <= deadline?
```

---

*Quick reference for cycle deadline investigations*
*See SKILL_EDI_Troubleshooting.md for full EDI error reference*