# Fix: EDI GPG decrypt failures — "Invalid argument" / "GPG command has exceeded timeout"

Intermittent EDINCOMING failures where the inbound EDI file cannot be decrypted. Log signatures: `gpg: error creating '...dec': Invalid argument` → `Failed to decrypt encrypted file`, and later `Could not start GPG ... GPG command has exceeded timeout`. Two compounding causes: (1) the EDI decrypted-file path lives on a Cohesity share GPG cannot write to reliably; (2) the GPG `PROCESS_TIME_OUT` defaults to 5000 ms (5 s) in code — too low under load. This is a Cloud-Ops + metadata fix, NOT a core code change.

## Steps
1. Pull the QPEC GatherLogs (`qtrace.QPTM.QPEC.*.segregated.log` in the Managed Steps folder) and confirm the gpg error lines above — EDI runtime errors are QPEC errors, not EDIServ errors.
2. Check where the EDI decrypted-file path points. If it is a Cohesity share (e.g. `\\HDC2-COH-QCSFS01\QFC17$` pattern), have Cloud Ops move the path off the Cohesity share to reliable storage.
3. Add the QPTM global config override `EDI / PROCESS_TIME_OUT = 15000`. This is metadata — deliver via a DB upgrade / client metadata hotfix, or a manual `QARCH_CNFG_CTRL` insert for the key.
4. Restart QPEC so the new timeout takes effect.
5. Reprocess the failed inbound EDI files.

## Verification
- Re-run EDINCOMING for a trading partner file and confirm the QPEC segregated log shows successful decrypt (no `gpg: error creating` / timeout lines).
- Confirm the trading partner receives the NMQR/response files again.
- Note: any remaining `CE` errors after the fix were legitimate business errors in the HPE case — do not chase them as decrypt failures.

## Workaround
Until the config lands: manually re-run EDINCOMING for the failed files (the failure is intermittent/load-dependent, so retries often succeed). Ask Cloud Ops to prioritize moving the share, which removed most failures in the source case.

## Source
SKILL_ADO_QPTM_Nominations_EDI.md §4 (Cluster A4). ADO #1672049 (HPE/Skippingstone, SF 24-00964519); delivered via QHPE.QPTM.Metadata hotfix (inferred).
