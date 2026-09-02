# Fix: MG stuck "Creating Group" / "QRA Middle Tier error" on save — restart RabbitMQ + QRA MT QPEC

## Steps
1. Confirm the symptom: Maintenance Group saves stall in **"Creating Group"/"Pending"**, or the user gets a sporadic **"QRA Middle Tier error"** (heaviest in PRD under load); SAP cannot connect on the callback so the MG stalls.
2. **Restart the RabbitMQ services.**
3. **Restart the QRA Middle Tier QPEC** (the messaging container QDO uses to call SAP-PRA and back).
4. Confirm the **web engines / QPEC** are up before re-testing (a down engine masquerades as a screen defect).
5. Have the user re-save / Retrieve the MG.

## Verification
- New MG saves complete without the QRA Middle Tier error and MGs advance past "Creating Group".
- Previously-stalled MGs progress after Retrieve/reopen.

## Workaround
Retry the save after the restart; no data is lost — the messaging layer stalled, the MG itself is intact. A long-term product fix is tracked (ADO 1784413).

## Source
SKILL_QDO_Division_Orders.md §7/§10. Cases: 26-01082277 (restart RabbitMQ + QRA MT QPEC, ADO 1784413), 23-00917440 (stuck "Creating Group").
