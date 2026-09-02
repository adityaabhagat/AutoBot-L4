# Fix: TIPS import / SFTP / file-path / batch connection failures

## Steps
Work these in order — almost all cases in this cluster are Application Configuration:
1. **Import/Export Definition**: verify the file path (e.g. `\\<server>\QFC17$\<CLIENT>\<ENV>\AppFiles\TIPS\Imports`, 25-01025681) and Backup Options — enable **"Append Date To Filename"** to prevent file-already-exists failures (25-01043424).
2. **Host definition / FTP folder structure**: compare the failing environment to PRD and correct drift (24-00964377 UAT host definition; 26-01091018 UAT FTP folder structure).
3. **QPEC user**: confirm the client's QPEC user is **active** — an inactive QPEC user presented as "SFTP not working" (24-00973935).
4. **Connection Management**: the .NET Connection Type (TIPSDSService) must **not** carry SQL-connection settings; after refreshes/deployments connections can revert (25-01016313, 26-01065785).
5. Restart the QPEC/TIPS services after connection changes, then re-run the import.

## Verification
- The import job picks up and processes the file; no "file already exists", SFTP, or connection error in the batch messages.

## Workaround
Place the file manually at the corrected path (or rename it with a date suffix) to get the current cycle through while the definition/host config is fixed.

## Source
SKILL_TIPS_Batch_Processing.md §10. Cases 24-00973935, 24-00964377, 24-00963134, 22-00875127, 25-01025681, 26-01091018, 25-01043424, 25-01016313, 26-01065785.
