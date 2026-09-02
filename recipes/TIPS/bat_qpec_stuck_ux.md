# Fix: Stuck/hung TIPS batch job (QPEC) — service restart + 'UX' status reset

## Steps
1. Get the **Master PQID** of the stuck run from the batch screen and confirm in the process queue / QPEC log that the run is genuinely dead (no progress).
2. Request Cloud Ops to **restart the QPEC / QTIPS services** for {client} (hosted clients). This alone resolved multiple cases, including "emails not being received from TIPS" (a hung QTIPS service).
3. **Script all processes left in a processing status to 'UX'** before re-running — the standard pairing with the restart ("a script was applied to set the stuck processes to 'UX'", 24-00974530).
4. Re-run the batch job.
5. If the same job hangs again, have the DBA **gather statistics** (24-00975612 — stats gather cleared hung jobs) and check CALC_STATS coverage.
6. If the job calls a customer-owned stored procedure, the hang is the customer's to fix (24-00985269).

## Verification
- A new submission no longer fails with "duplicate process error"; the job completes and the plant leaves Facility Lock status.
- The process queue shows no rows left in a processing status for the old Master PQID.

## Workaround
Do not re-submit the job until the stuck statuses are cleared — the duplicate-process guard will keep blocking. There is no user-side workaround; the restart + UX reset is the operational answer (stuck-in-QUEUE where even Cancel will not cancel is a long-standing product gap, 25-01033454 / 22-00263967).

## Source
SKILL_TIPS_Batch_Processing.md §4, §18-G. Cases 24-00974530, 23-00890868, 24-00986899, 24-00975612, 22-00516202, 22-00512698, 26-01097581, 26-01066599, 26-01091247.
