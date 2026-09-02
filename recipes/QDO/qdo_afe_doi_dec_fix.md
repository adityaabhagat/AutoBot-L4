# Fix: Converted AFEs with NULL AFE_DOI_DEC / re-submittable Open AFEs — data correction scripts

## Steps
1. Verify the affected rows (verify-SELECT first, inside a transaction):
```sql
SELECT AFE_NO, BUS_UNIT_CD, OPER_BUS_SEG_CD, AFE_DOI_DEC, AFE_STAT_CD, WF_STATUS_CD, WF_INSTANCE_ID
FROM   QCTRL_AFE_HDR
WHERE  AFE_DOI_DEC IS NULL OR (WF_STATUS_CD IS NULL AND WF_INSTANCE_ID IS NULL AND AFE_STAT_CD = 'O');
```
2. **Recompute the header decimal as the average of the cost-center DOI** (per the 74170 walkthrough):
```sql
UPDATE QCTRL_AFE_HDR
SET    AFE_DOI_DEC = (SELECT AVG(C.DOI_DEC) FROM QCTRL_AFE_COST_CNTR C
                      WHERE C.AFE_NO = QCTRL_AFE_HDR.AFE_NO
                        AND C.BUS_UNIT_CD = QCTRL_AFE_HDR.BUS_UNIT_CD
                        AND C.OPER_BUS_SEG_CD = QCTRL_AFE_HDR.OPER_BUS_SEG_CD)
WHERE  AFE_DOI_DEC IS NULL;
```
3. **Stamp converted Open AFEs as already-approved** so the Submit button is removed:
```sql
UPDATE QCTRL_AFE_HDR
SET    WF_STATUS_CD = 'Approved', WF_INSTANCE_ID = 'CONVERSION'
WHERE  WF_STATUS_CD IS NULL AND WF_INSTANCE_ID IS NULL AND AFE_STAT_CD = 'O';
```
4. Confirm the client build carries the companion code change that suppresses the Submit button for these (PR #3043 / WI 74171).

## Verification
- The verify-SELECT from step 1 returns 0 rows.
- Converted Open AFEs no longer show the Submit button and cannot be re-submitted into workflow.

## Workaround
Until the script runs, instruct users not to Submit converted Open AFEs — re-submission pushes an already-live AFE back into workflow.

## Source
SKILL_ADO_QDO_DivisionOrder_Transfers.md §8 E1 (74170_Walkthrough.docx). ADO: 74170 (data script via SIR 174945), 74171 (PR #3043, Sprint 41).
