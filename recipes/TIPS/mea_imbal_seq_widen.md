# Fix: Imbalance activity sequence overflow — widen ACCT_ACTIVITY_DTL_ID

## Steps
1. Confirm the state: sequence `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` has passed 10,000,000,000 (11 digits) while `ACCT_ACTIVITY_DTL_ID` is `NUMBER(10)`:
```sql
SELECT QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ.NEXTVAL FROM DUAL;
SELECT TABLE_NAME, COLUMN_NAME, DATA_PRECISION
FROM   ALL_TAB_COLUMNS
WHERE  COLUMN_NAME = 'ACCT_ACTIVITY_DTL_ID'
  AND  TABLE_NAME IN ('QTRAN_IMBAL_ACCT_ACTIVITY_DTL','QPOST_IMBAL_ACCT_ACTIVITY_DTL');
```
2. **Interim customer workaround (verbatim from 25-01014345, ETP)** — cover **all three** tables (QTRAN + QPOST + the CAW-schema copy):
```sql
ALTER TABLE QRMTIPS_CAW.QTRAN_IMBAL_ACCT_ACTIVITY_DTL MODIFY ACCT_ACTIVITY_DTL_ID NUMBER(11);
ALTER TABLE QRMTIPS.QPOST_IMBAL_ACCT_ACTIVITY_DTL    MODIFY ACCT_ACTIVITY_DTL_ID NUMBER(11);
ALTER TABLE QRMTIPS.QTRAN_IMBAL_ACCT_ACTIVITY_DTL    MODIFY ACCT_ACTIVITY_DTL_ID NUMBER(11);
```
3. **Product-standard fix:** the shipped change widens precision 10 → **NUMBER(19)** (ADO #1723573; DB PRs 110407/110411/110413 + regenerated `ImbalAcctActivityDtlDO` codegen) — confirm/schedule the client patch so the interim NUMBER(11) is superseded.
4. Re-run the failed INACCTACCM / imbalance activity step.

## Verification
- The Step 1 precision query shows the widened precision on all three tables (11 interim, 19 after the product patch).
- INACCTACCM completes without `PL/SQL: numeric or value error: number precision too large`.

## Workaround
The NUMBER(11) ALTER above is the sanctioned interim workaround; it buys one more order of magnitude only — the product NUMBER(19) patch is the durable fix.

## Source
SKILL_TIPS_Master_Data_Contracts.md §5 and §16-D (verbatim ALTER script from SF case 25-01014345, ETP); SKILL_ADO_TIPS_MasterData_Contracts_CCT_Meter.md §4-B (ADO #1723573).
