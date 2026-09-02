# Fix: Export producing triple/duplicate values — set EXP_OVERWRITE_FILE_IND = 1

## Steps
1. Verify the flag on the affected export definitions first:
```sql
SELECT IMPEXP_ID, APP_LAYER_CD, EXP_OVERWRITE_FILE_IND
FROM   QARCH_CTRL_IMPEXP
WHERE  IMPEXP_ID IN ('<IMPEXP_ID_1>','<IMPEXP_ID_2>');   -- e.g. 'CSURDD','CSUPCC'
```
   `EXP_OVERWRITE_FILE_IND = 0` means each run APPENDS to the output file — the triple/duplicate-values signature.
2. Apply the verbatim fix (source: ADO **#1705697** attachment `1705697 - CSURDD and CSUPCC Overwrite - Oracle.sql`, deployed as a QDBMGR MDC script for case 24-00992623):
```sql
BEGIN
  UPDATE QARCH_CTRL_IMPEXP
     SET EXP_OVERWRITE_FILE_IND = 1,
         UPDT_DT = TO_DATE('<YYYY-MM-DD HH24:MI:SS>','YYYY-MM-DD HH24:MI:SS'),
         USER_ID = '<USER_ID>'
   WHERE IMPEXP_ID = '<IMPEXP_ID_1>' AND APP_LAYER_CD = '<APP_LAYER_CD>';

  UPDATE QARCH_CTRL_IMPEXP
     SET EXP_OVERWRITE_FILE_IND = 1,
         UPDT_DT = TO_DATE('<YYYY-MM-DD HH24:MI:SS>','YYYY-MM-DD HH24:MI:SS'),
         USER_ID = '<USER_ID>'
   WHERE IMPEXP_ID = '<IMPEXP_ID_2>' AND APP_LAYER_CD = '<APP_LAYER_CD>';
END;
/
```
3. Delete/clear the already-appended output file so the next run starts clean.

## Verification
```sql
SELECT IMPEXP_ID, EXP_OVERWRITE_FILE_IND FROM QARCH_CTRL_IMPEXP
WHERE  IMPEXP_ID IN ('<IMPEXP_ID_1>','<IMPEXP_ID_2>');
```
Both rows must show `EXP_OVERWRITE_FILE_IND = 1`; the next scheduled run must produce a file with single (non-duplicated) values.

## Workaround
Until the flag is set, the downstream consumer should take only the FIRST occurrence of each record in the file, or the file can be regenerated manually once per day after deleting the old one. The underlying QPTM data was always correct — only the exported file accumulated repeats.

## Source
SKILL_Integration_Processing.md §16 Script A — ADO #1705697 (verbatim), SF case 24-00992623 (CSU RDD/PCC exports).
