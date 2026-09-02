# Case 26-01093642 — L4 Investigation

**Subject:** Shippers set up in the Event Detector are not receiving their reports
**Client:** Tallgrass MLP Operations, LLC · **Priority/Status:** High / In Progress · **Owner:** Tushar Patil
**Created:** 2026-04-15 · **SF Id:** 500UH00000ml7iNYAQ
**Example given:** Event Detector **11014**, BPID **9867 (DCP)** — **5** parties set up, **3** receive the report, **2** do not. The 2 have **no entry in the Event Log** (no send attempt). Same problem also reported for **Koch** on ED 11014.

---

## 1. The issue and the key diagnostic signal

Certain parties configured to receive a cut report via Event Detector 11014 are not getting it. The decisive detail is that **there is no Event Log row for the two affected parties** — the system never even *attempted* to send to them. This rules out an email/SMTP delivery failure (which would leave a "sent/failed" log row) and points to the recipients being **dropped before the send pipeline** — i.e. they are never *resolved* into the notification batch.

The customer notes this happened before and Quorum found a solution. That precedent is real: **SF case 23-00921160 (2023)** — *same Tallgrass account, same Event Detector 11014* ("Users from SWN / GID 10482 have stopped receiving cut reports (event detector 11014)"). The only recorded Quorum action there was checking the Event Detector Setup → Contacts tab for event 11014 and finding two named users **not present in the Contacts tab**. `Resolution__c` is blank and there are no case comments, so the confirmed final fix is not in the record — but Quorum's diagnosis pointed squarely at recipient setup. (Note: 2023 was for SWN, a different business party than this case's DCP/BPID 9867 — same detector, same symptom, different party.)

---

## 2. How event-detector cut-report notifications resolve recipients (verified live source)

Process: **UTILSCHNOT** (scheduled-notification utility). Repo **`Quorum.QPTM.ClassicBatch`**, folder **`/QPDllPipelineMgrUtil/`**. Dispatch is in `QPSPipelineScheduleNotification::Execute()` (`QPSPipelineScheduleNotification.cpp:498`); for the operator scheduled-quantity cut report (event types `EVENTTYPEID_CA_OPR_SCHED_QTY_X` / `_X_2`) it runs the path below. The shipper-facing cut report uses the sibling query `m_Sel_NotifyServiceRequester` with the same structure (see §6).

A configured recipient must pass **two independent gates** to actually receive — and be logged for — a notice. Failing either gate produces **no notice-queue row, no Event Log entry, and no send attempt** — exactly the reported symptom.

### Gate A — the recipient-selection query (`m_Sel_NotifyOperators`)
`QSQL_PipelineScheduleNotification.cpp:165-179`, verbatim:

```sql
SELECT DISTINCT STAG.CONF_PARTY_CONTACT_ID AS CONTACT_ID
    ,KC.PRIMARY_BP_NO
    ,KBE.BP_NM
FROM CFRPTS_CYCLE_ACTIVITY_LOC STAG
JOIN KCTRL_CONTACT KC
    ON KC.CONTACT_ID = STAG.CONF_PARTY_CONTACT_ID
    AND KC.EMAIL_ADDR IS NOT NULL
JOIN KCTRL_BP_ENTITY_HDR KBE
    ON KBE.BP_NO = KC.PRIMARY_BP_NO
    AND KBE.INACTIVE_IND = 0
JOIN SCTRL_BA_CONTACT_ROLE ROLE
    ON ROLE.CONTACT_ID = KC.CONTACT_ID
WHERE ROLE.CONTACT_TYPE_CD IN ('OPR', 'OPA')
    AND STAG.PROCESS_QUEUE_ID = @0PROCESS_QUEUE_ID
    AND STAG.TSP_NO = @0TSP_NO
```

A contact is selected **only if all four are true**:
1. **They have a row in the staging table `CFRPTS_CYCLE_ACTIVITY_LOC` for this run's `PROCESS_QUEUE_ID` and `TSP_NO`** — i.e. their location actually had cut/confirm activity *in that cycle*. The staging table is populated by the pre-process `PROCID_CFRPTSCYCL` (`QPSPreReportProcessCFGenericCycleActvLoc.cpp`), launched at `QPSPipelineScheduleNotification.cpp:578-579`; its queue id is captured (`m_StagedDataPQID`, `:3468`) and bound to `@0PROCESS_QUEUE_ID` at `:586`.
2. **`KCTRL_CONTACT.EMAIL_ADDR IS NOT NULL`** — the contact has an email address.
3. **`KCTRL_BP_ENTITY_HDR.INACTIVE_IND = 0`** — the contact's primary business party is active.
4. **`SCTRL_BA_CONTACT_ROLE.CONTACT_TYPE_CD IN ('OPR','OPA')`** — the contact holds the Operator / Operator-Agent role (for the operator report; the shipper report filters on the Service-Requester role instead).

> This staging-table restriction is the fix from ADO #1756997 (see §5). The pre-fix query (still present, commented out, `:156-163`) read `PACTRL_LOC_OPERATOR_VW` filtered only by TSP + effective date + email — i.e. **every** operator on the TSP, regardless of whether their location was cut. The fix narrowed it to **only contacts with activity this cycle.**

### Gate B — the Event Detector cross-reference (`Notify()`)
The selected rows are looped in `QPSPipelineScheduleNotification::ExecuteSchedule(...)` (the 4-arg overload, `:1357`). Recipient mode is set to **`enCrossRef`** (`:1418`) — i.e. validate against the Event Detector's eligible recipient list. Per row it builds `notifMessage`, adds the contact (`AddContact`, `:1451-1452`), then:

```cpp
if(notifMessage.Notify())   // :1456 — Event Detector cross-ref gate
{
    ... // :1457-1480 build + send the internal LOGGED notice
    notifInternalMsg.Notify();   // :1475 — this is what creates the Event Log / notice-queue row
}
```

If the contact is **not on the Event Detector's recipient list**, `notifMessage.Notify()` returns false, the block is skipped, **no internal logged notice is created, and no send is attempted.** If no contact passes for the whole run, the batch logs only `"No notifications were sent."` (`:1485-1489`). **This gate is exactly the 2023 finding — a recipient missing from the detector's Contacts tab is dropped here with no log row.**

### Verified tables / columns
| Table | Columns used | Role in resolution |
|---|---|---|
| `CFRPTS_CYCLE_ACTIVITY_LOC` (staging) | `CONF_PARTY_CONTACT_ID`, `PROCESS_QUEUE_ID`, `TSP_NO` | Which contacts had cut activity *this cycle* (Gate A #1) |
| `KCTRL_CONTACT` | `CONTACT_ID`, `EMAIL_ADDR`, `PRIMARY_BP_NO` | Contact + email check (Gate A #2) |
| `KCTRL_BP_ENTITY_HDR` | `BP_NO`, `INACTIVE_IND`, `BP_NM` | BP active check (Gate A #3) |
| `SCTRL_BA_CONTACT_ROLE` | `CONTACT_ID`, `CONTACT_TYPE_CD` (`'OPR'`/`'OPA'`) | Role check (Gate A #4) |
| Event Detector recipient config | (verify name in client `*.QPTM.Database` `EVENT_DETECTOR` migration) | Cross-ref recipient list (Gate B) |

---

## 3. Root-cause analysis — three ranked hypotheses, mapped to the gates

**H1 — Configuration / recipient-setup gap (most likely).** The 2 parties fail Gate A or Gate B:
- **Gate B (most likely, matches 2023):** they are not on Event Detector 11014's recipient/Contacts list, so `Notify()` rejects them. Fix = add them to the detector's contacts. May also require the **event-notification type to be granted to their security group** (sibling case 26-01084250, Pembina).
- **Gate A:** they have no email (`EMAIL_ADDR` null), their BP is inactive, or — notably — **they lack the role the report filters on.** The case says *shippers*; if ED 11014 is the operator report (`OPR`/`OPA` filter), a shipper contact without that role would never be selected. Confirm the report's recipient class vs the contacts' roles.

Support: same client + same detector precedent (23-00921160); sibling resolutions all configuration — Pembina 26-01084250 ("added the event notification type to the security group"), MountainWest 26-01080390 ("turned on the event detector for email"), EQT 26-01067520 (recipient already existed / PK violation).

**H2 — Expected behavior post-#1756997 (cheapest to confirm; check first).** If Tallgrass is on a build containing the #1756997 fix, the cut report only goes to parties with a staging row for that cycle — i.e. **only those whose locations were actually cut that cycle.** If the 2 "missing" parties had no qualifying cut activity on their locations in the cycles reviewed, they correctly receive nothing and get no Event Log entry. **This is working as designed, not a fault.** It must be excluded before any config or defect work.

**H3 — Defect (least likely).** No currently-open defect matches the *under-send / no-log* symptom. #1756997 is Closed and its bug direction was *over*-send; #113963 is old QLNG. Escalate as a **new** defect only if the 2 parties are fully configured (pass Gate A roles/email/BP and are on the detector list) **and** a cut occurred on their locations **and** there is still no notice-queue row — do not reuse the closed bugs.

---

## 4. Evidence — SF and ADO

| Ref | Type / State | Relevance |
|---|---|---|
| SF **23-00921160** | Closed (2023) | **Same client + same ED 11014.** Quorum found recipients missing from the Contacts tab (Gate B). The "solution found before" the customer recalls. |
| SF 26-01084250 (Pembina) | Closed | "Not receiving" → fixed by granting the **event-notification type to the security group**. |
| SF 26-01080390 (MountainWest) | Closed | Fixed by **enabling the event detector for email**. |
| SF 26-01067520 (EQT) | Closed | "Added but not showing" → recipient already existed (PK violation). |
| ADO **#1756997** | Bug / Closed | QPTM/Notifications, CAX_14 operator cut report. Found **2020.03**; fixed **2024.04.1.42 / 2025.04.1.12 / 2025.10.1.2 / 2026.04.1.0**. Changed recipient selection to the staging table (Gate A #1). Drives **H2**. RCA (verbatim): *"m_Sel_NotifyOperators query returned all OPR/OPA contacts system-wide (20+)… Now query returns only contacts from staging table… Event Detector validates, resulting in correct single notification."* |
| ADO **#113963** | Bug / Closed | QLNG Composite ADP cargo; fixed **2019.07.1.1**. Documents the BP+TSP-tie recipient rule (analogous mechanism, different product/path). |

---

## 5. Code-level analysis (first-hand, live `develop`)

Repo `Quorum.QPTM.ClassicBatch`, folder `/QPDllPipelineMgrUtil/`:
- `QSQLID_PipelineScheduleNotification.h` — declares the notify queries. Cut-report-relevant siblings: **`m_Sel_NotifyOperators`** (operator), **`m_Sel_NotifyServiceRequester`** (shipper / Service Requester), `m_SelOperNotifications`, `m_Sel_ServReqNotifications`, and the cut trigger **`m_Sel_CheckForConfCuts`**.
- `QSQL_PipelineScheduleNotification.cpp:165-179` — `m_Sel_NotifyOperators` SQL (verbatim in §2). Pre-#1756997 version commented at `:156-163` (`PACTRL_LOC_OPERATOR_VW`).
- `QPSPipelineScheduleNotification.cpp` — `Execute()` `:498` (operator block `:573-607`: staging launch `:578-579`, `PROCESS_QUEUE_ID` bind `:586`, `ExecuteSchedule` calls `:593-604`); `ExecuteSchedule(...)` 4-arg runner `:1357` (`enCrossRef` `:1418`, query `:1421`, recipient loop `:1437-1482`, `AddContact` `:1451-1452`, **drop gate `if(notifMessage.Notify())` `:1456`**, logged notice `notifInternalMsg.Notify()` `:1475`, "No notifications were sent" `:1485-1489`); `LaunchRptStagingProcess(...)` `:3390-3473` (`m_StagedDataPQID` set `:3468`).
- Staging table `CFRPTS_CYCLE_ACTIVITY_LOC` populated by `/QPDllPipelineMgrRPT/QPSPreReportProcessCFGenericCycleActvLoc.cpp`; DDL in `Quorum.QPTM.Database/Common/{MSSQL,Oracle}/Tables/QPTM_SCR/CFRPTS_CYCLE_ACTIVITY_LOC.sql`.

> Caveat for handoff: `m_Sel_NotifyOperators` was read verbatim. The shipper path (`m_Sel_NotifyServiceRequester`) is the same two-gate structure but its exact SELECT was not read line-by-line — confirm which query ED 11014 uses (operator vs Service Requester) when the event type is known. There is **no** `/QPDllTerminalMgrUtil/` path in this repo; the `m_Sel_*` notification logic is QPTM-only in `/QPDllPipelineMgrUtil/`.

---

## 6. Diagnostic plan + SQL

DB MCP is unavailable from this workstation — hand to an engineer with PRD read access. Table names in §2 are **verified** from source; the Event Detector recipient/config table name (Gate B, Q4) must be confirmed against the client `*.QPTM.Database` `EVENT_DETECTOR` migration. SQL-Server date syntax shown; use `SYSDATE` on Oracle.

**Step 0 — scope it.** Identify which report/event type ED 11014 drives and whether recipients are **operators (`OPR`/`OPA`)** or **shippers (Service Requester)** — this selects `m_Sel_NotifyOperators` vs `m_Sel_NotifyServiceRequester`. Also confirm the **Tallgrass QPTM build** against the #1756997 fix lines (2024.04.1.42 / 2025.04.1.12 / 2025.10.1.2 / 2026.04.1.0) — decides whether H2 is in play. Get the **CONTACT_IDs** of the 2 non-receiving parties.

```sql
-- Q1 (Gate A config): for the 2 affected contacts — email present, BP active, and do they hold the report's role?
SELECT KC.CONTACT_ID, KC.EMAIL_ADDR, KC.PRIMARY_BP_NO,
       KBE.INACTIVE_IND                                AS bp_inactive,
       (SELECT COUNT(*) FROM SCTRL_BA_CONTACT_ROLE R
         WHERE R.CONTACT_ID = KC.CONTACT_ID
           AND R.CONTACT_TYPE_CD IN ('OPR','OPA'))     AS opr_opa_roles   -- swap to the SR role code for shipper report
FROM   KCTRL_CONTACT KC
LEFT JOIN KCTRL_BP_ENTITY_HDR KBE ON KBE.BP_NO = KC.PRIMARY_BP_NO
WHERE  KC.CONTACT_ID IN (<contact_id_1>, <contact_id_2>);
-- Drop at Gate A if: EMAIL_ADDR null, bp_inactive <> 0, or the required role count = 0.

-- Q2 (Gate A staging / H2): did the 2 contacts have cut activity in the affected cycle(s)?
SELECT STAG.PROCESS_QUEUE_ID, STAG.TSP_NO, STAG.CONF_PARTY_CONTACT_ID
FROM   CFRPTS_CYCLE_ACTIVITY_LOC STAG
WHERE  STAG.CONF_PARTY_CONTACT_ID IN (<contact_id_1>, <contact_id_2>)
  AND  STAG.TSP_NO = <ED 11014 TSP>;
-- No rows for a contact in the relevant run = no cut on their locations that cycle = H2 (expected, no fault).

-- Q3 (the exact resolution the batch would compute): run m_Sel_NotifyOperators for the cycle's
-- PROCESS_QUEUE_ID + TSP and see which of the 5 configured parties it returns. The ones it omits
-- are dropped at Gate A; cross-check the omitted CONTACT_IDs against Q1/Q2 to see which clause did it.

-- Q4 (Gate B): are the 2 contacts on Event Detector 11014's recipient list / Contacts tab,
--      and does their security group grant the event-notification type? (the 2023 + Pembina checks)
--      Verify the ED recipient + security-group table names in the client EVENT_DETECTOR migration first.
```

---

## 7. Possible solution

There is **no code fix or upgrade** that resolves this as a defect — the symptom is configuration or expected behavior, and no open defect matches it. The fix is to make the two parties resolve through both gates (or to confirm there is nothing to fix). Apply per what the diagnostics show:

1. **If no cut activity on their locations (Q2 empty) → no fix; educate.** On a fixed build the report intentionally goes only to parties whose locations were cut that cycle. Confirm with the customer that the cycles they cited had no qualifying cut for those parties.
2. **If missing from the Event Detector recipient list (Gate B) → add them to ED 11014's Contacts tab.** This is the 2023 fix on this exact detector. If access to the event is also blocked, **grant the event-notification type to their security group** (the Pembina 26-01084250 fix).
3. **If dropped at Gate A:**
   - **No email** → add a valid `EMAIL_ADDR` to the contact (`KCTRL_CONTACT`).
   - **BP inactive** → reactivate / correct the contact's primary BP.
   - **Missing role** → assign the correct role on the BA Contact Role screen — `OPR`/`OPA` for the operator report, or the Service-Requester role for the shipper report. (If the report and the parties' roles don't match — e.g. shippers configured against an operator report — that mismatch is itself the root cause.)
4. **Only if all of the above are clean** (parties pass Gate A roles/email/BP, are on the detector list, and a cut occurred on their locations) **and there is still no notice-queue row → escalate a new defect** with the Q2/Q3 evidence. Do not reuse #1756997 / #113963.

After the corrective config, validate on the next firing where a cut occurs on the affected locations: the parties should appear in the notice queue and receive the report. (Status: cause not yet confirmed against live data — the diagnostics above pinpoint which gate applies.)

---

## 8. Confirmed vs. needs live data · limitations

- **Confirmed:** the recipient-resolution mechanism and exact drop conditions (verified source, §2/§5); the same-client/same-detector precedent and its diagnosis (SF 23-00921160); the #1756997 behavior change and its fix builds; no open defect matches the symptom.
- **Needs live data:** which report/event type ED 11014 drives and the recipient class (operator vs shipper); Tallgrass's deployed build vs the #1756997 fix lines; whether a cut occurred on the 2 parties' locations; the 2 parties' contact setup (email/BP/role) and detector-list membership.
- **Limitations:** the case has 13 attachments (recipient-setup screenshots, "DCP Event 11014", "Koch not receiving their Event Detector 11014", "Before Walkthrough") that **cannot be pulled as files through the Salesforce connector** (binary data isn't exposed) — reviewing them directly in Salesforce will likely settle Gate-A-vs-Gate-B and H1-vs-H2 immediately. The Event Detector recipient/security-group table names (Gate B) must be confirmed against the client's `*.QPTM.Database` `EVENT_DETECTOR` migration before running Q4.
