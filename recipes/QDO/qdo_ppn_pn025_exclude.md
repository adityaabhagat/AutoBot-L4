# Fix: Unexpected PPNs generated (PD41 / exemption / bearer-group reason with no change) — exclude on PN025

## Steps
1. Identify the PPN **reason code** on the unwanted notifications (PD41 / LD43 / LD17 / LD18 / LD45 / exemption / BG). Confirm nothing corresponding actually changed on the transfer/pay-code MG — that makes it the PPN-staging defect family, not user error.
2. To unblock month-close: **exclude the incorrect PPNs on PN025** — this removes them from **VL100 / CA020**.
3. **Delete the incorrect market groups from RD010** (reversal decks) created by the bad PPNs.
4. Confirm whether the client build carries the PPN-staging rework (Preview & Approval PPN creation merged — ADO 1729989 / 1764539 / 1754316); if not, log/attach to the long-term fix (ADO 1742419).

## Verification
- VL100 / CA020 no longer show the excluded PPN value lines.
- Re-running the preview/approval for an equivalent MG no longer stages the spurious PPN reason codes (on a fixed build).

## Workaround
The PN025 exclusion IS the sanctioned workaround (field-proven on 25-01029286) — it is non-destructive to the underlying DOI history and lets revenue close proceed while the code fix is scheduled.

## Source
SKILL_QDO_Division_Orders.md §5 B1. Cases: 25-01029286 (WA), 24-00952414 (PD41 instead of LD43), 24-00973008, 24-00977860. ADO: 1742419 (long-term), 1729989/1764539/1754316 (staging rework).
