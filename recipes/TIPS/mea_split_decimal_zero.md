# Fix: Zero/missing Split Decimal zeroing settlement volumes

## Steps
1. Confirm the signature on the affected meter/month:
```sql
SELECT MTR_NO, PROD_DT, S_DECIMAL
FROM   QTRAN_PAYSTATION
WHERE  PROD_DT = '{prod_mth}'
  AND  (S_DECIMAL = 0 OR S_DECIMAL IS NULL);
```
   S_DECIMAL = 0 or NULL on the affected meter (while other meters show 1) is the 26-01091612 signature.
2. On the **Meter Split** screen, set the Split Decimal correctly for the affected meter/contract — it should be 1 unless the volume is intentionally split.
3. **Rebuild the split** so the decimals flow into Meter Split (24-00937128 pattern: "rebuild the split so decimals come into Meter Split").
4. Also verify a **CCT exists for the production month** on the meter split — a missing CCT produces the same "meter not settling / 0 on allocated-volume query" symptom (26-01100577).
5. Re-run the plant/settlement for the month.

## Verification
- Re-run the Step 1 query: no zero/NULL S_DECIMAL rows remain for the affected meter and {prod_mth}.
- The settlement / gas statement now shows the expected NGLS / wellhead volumes (settlement views multiply by the split decimal, e.g. `NVL(ALLOC.WHDV_VOL * PAY.S_DECIMAL, 0)` — a non-zero decimal restores the volume).

## Workaround
None at the report level — the zero flows from the data. The fix (correct split decimal + rebuild + rerun) is itself quick; communicate that dollar amounts on the statement were driven by the same data and will restate with the rerun.

## Source
SKILL_TIPS_Measurement_Ticketing.md §9 and §18-B. SF cases 26-01091612 (OXY — Split Decimal = 0 zeroed NGLS on `OXYPOST_SETTLE_GAS_STMT_VW`), 24-00937128 (IACX — rebuild split restored wellhead volumes), 26-01100577 (missing CCT for prod month).
