# SKILL — QLS eCalendar & Obligations

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` schema
> **Coverage-plan group #3:** eCalendar & Obligations — 1,125 cases all-time, 275 actionable (Software Defect + Application Configuration)
> **Sources:** all-history Salesforce mining (7 SOQL inventory pages, 27 cases sampled in depth via Description + `Resolution__c`) + ADO work-item mining (org QuorumSoftware, projects `QuorumSoftware` + `Quorum`, area paths `Engineering\Maintenance\Upstream\Customer Service\Land`, `Engineering\Land\Committed Backlog`, `North America\Upstream\Land RnD`). Mined 2026-09-03.
> **Auto-Bot skill** — built by Aditya Bhagat. Every claim cited to SF case number or ADO work item ID. Customer employee names redacted.

---

## 1. Quick Triage

| Symptom (verbatim-style) | Cluster | Likely gate |
|---|---|---|
| "Payments/obligations/expirations missing from eCalendar" / "Inbox is empty" | C1 | G2 config or G4 bad data |
| "Event in a route but no desk assigned" / "orphaned records" / "In Progress with blank desk" | C2 | G3 version (ECALWF abort-detect fix) |
| "Assigned to wrong desk / one user instead of the group / inactive desk" | C3 | G2 config → G3 version |
| "Processed event re-entered the workflow" / "locked month got a new workflow" / "duplicate eCal events" | C4 | G3 version (Route Resolver fixes) |
| "eCalendar emails not being sent" / "ECALNTC fails" / "escalation email won't stop" | C5 | G2 config first |
| "Server Error on List view / Coordinator won't load / Inbox slow" | C6 | G5 code (known items) |
| "Recommendation missing / empty recommendation approved / can't pick approvers" | C7 | mixed — see cluster |
| "eCal remarks/comments not in QLS" / "obligation stuck Held by Production" | C8 | G3 version (legacy eCal deprecated) |
| "ECALWF/Pull Events not running / failing" | see `SKILL_QLS_Batch_MassChange.md` §3.2 (scheduled-process ops) + C1 below | G2 config (scheduling) |

Triage questions to ask first (from repeated case patterns):
1. **Which eCalendar?** Legacy eCal (deprecated) vs current eCalendar module — remark/comment sync bugs are legacy-only, fixed by upgrade to 2026.04 (SF 25-01037615).
2. **Is it ONE event or all events?** All events missing → batch scheduling (ALL_EVENT_ROLL / Pull Events / ECALWF not running — C1 below, plus `SKILL_QLS_Batch_MassChange.md` §3.2 for the scheduler itself). One event → route/limit/data problem (C2).
3. **Was the scrubber + Pull Events already run?** That combo clears most stuck-event states (SF 25-01023990, 24-00984507, 24-00994588) — if the issue *recurs weekly* after scrubbing, it is the known ECALWF abort defect, not user error (SF 24-00994588).
4. **Client build vs hotfix train** — most C2/C4 defects are fixed on 2022.04→2024.10 hotfix tags; check version before investigating code.

---

## 2. Decision Tree

```
Event(s) not visible in eCalendar?
├─ ALL events for everyone → scheduler check (SKILL_QLS_Batch_MassChange.md §3.2): is ECALWF / Pull Events / ALL_EVENT_ROLL scheduled & succeeding?
│   ├─ Pull Events not scheduled → configure schedule (30-min cycle used at one client) [26-01120369]
│   └─ ALL_EVENT_ROLL not scheduled → event dates never roll forward [24-00985081]
├─ Some users only → working-months / staging config (C1) [26-01099872, 26-01085381]
├─ One agreement/event →
│   ├─ WF_STATUS_CD says In Progress but desk blank → C2 orphaned assignment
│   │   ├─ On pre-fix build → G3: ECALWF abort-detect fix [24-00983058, 24-00994588]
│   │   └─ On fixed build → run scrubber + Pull Events, then check desk $ limits [ADO 1862769]
│   ├─ Agreement county/state invalid vs code table → inbox goes empty → G4 bad data [ADO 1751061]
│   └─ Stuck after approval → known defect, hotfixed on all trains [ADO 1702244]
Assignment goes to wrong desk/user?
├─ From Group Select shows stale user → QARCH_WF_TRAN_ROUTE_PREVIEW not refreshed [ADO 1699921]
├─ Multi-desk step routed to one user → user $ limits on the desks [24-00961941, ADO 1594305]
└─ Inactive desks receiving events → G5/known defect [25-01005081, ADO 1839727 (inactive users in picklists)]
Workflow re-created or duplicated after payment edit?
├─ Locked month re-opened → G3 [24-00958240, 25-01030739]
├─ EVENT_PROCESSED not null but workflow reset → G3 [24-00980776, ADO 1645056]
└─ Multiple payments same agreement scrambled into one eCal line → cleanup script + hotfix [26-01063827]
Emails not arriving?
├─ Specific users only → Security Group 50029 membership [26-01070529]
├─ Nobody, HTML mangled → QPCK_ECAL_EMAIL_CORE package fix / client override package [24-00989452]
└─ ECALNTC1 "fails" on some steps → steps with zero notifications to send; verify before alarm [24-00980062]
```

---

## 3. C1 — Events missing from eCalendar / empty Inbox

**Signature:** payments, obligations, or expirations that exist in QLS do not appear in the eCalendar Inbox, Calendar, or dashboard widget; or users see fewer months than expected.

**Root causes seen (in cheapest-first order):**
1. **Date-roll batch not scheduled.** 4 December annual payments missing because their event dates never rolled forward — `ALL_EVENT_ROLL` was not scheduled at all. Fix: set up a daily `ALL_EVENT_ROLL` job. (SF **24-00985081**, Resolution verbatim: "4 payment events needed to roll their dates forward with ALL_EVENT_ROLL. Found that ALL_EVENT_ROLL was not scheduled to run. Set up a daily job.")
2. **Events stuck in the eCal workflow.** Run the scrubber (payments/obligations variant as applicable) then **Pull Events**; this restored visibility. (SF **25-01023990** — "2 payments were stuck in the ecal workflow. We ran the scrubber for payments and then pull events"; same recipe in **24-00984507** after desk re-creation.)
3. **Working-months / staging config.** Users seeing only 1–3 months: one client fixed via script extending eCal future months to six (SF **26-01085381**); another by enabling the configuration that stages Producing Expirations (SF **26-01099872**). Coordinator calendar has a separate months-out setting from the user Calendar (SF **24-00969970**, months mismatch after re-running eCal config scripts).
4. **Bad reference data empties the whole inbox.** If an agreement's county no longer exists in the Counties code table, the assigned desk user's entire eCalendar Inbox rendered empty. ECALWF was updated to tolerate invalid State/County (event still assigned; state/county not displayed). (ADO **1751061** — QLS - eCalendar Inbox - Agreements are not visible.)
5. **Expirations missing from calendar** after upgrade — config-side (SF **24-00981925**); Inbox not populating at go-live — patch deployment (SF **24-00951322**).

**Fix recipe:**
- Confirm `ALL_EVENT_ROLL`, `ECALWF`, and Pull Events schedules exist and last ran clean.
- Run scrubber → Pull Events; re-check.
- Diff working-months/staging configs between a working and non-working user (per-user visibility difference is nearly always config, not code — SF 26-01099872).
- If a single desk user's inbox is empty, check agreement state/county validity vs code tables (G4) before escalating.

---

## 4. C2 — Orphaned / unassigned events: in route but no desk

**Signature:** event shows submitted to workflow, `In Progress`, assigned to a route, but Desk Assigned is blank; resubmit does nothing (screen loops "Query Successful"); or event is "floating unassigned."

**Root causes:**
1. **Aborted ECALWF runs left half-written assignments.** Fix (verbatim resolution on two cases): *"Added logic to ECALWF to detect events that were aborted and need to be resubmitted."* (SF **24-00983058** — route but no desk on a converted expiration and a non-converted obligation; SF **24-00994588** — weekly orphaned sub-assignments; scrubber+Pull Events was the interim workaround.) Related mass-cleanup case SF **24-00978110** (resubmit-to-delegate left records fully/partially/un-assigned — critical). Large-scale audit variant: SF **25-01039828** (records in routes never assigned a desk; QC exports inconsistent) — Resolution: "Sept '25 2023.04 HF" → **fixed in the 2023.04 hotfix train** (INFERRED build mapping from Resolution text).
2. **Desk dollar-limit gaps keep the event out of the route.** If any desk on a dollar-approval step has a non-zero but insufficient limit, ECALWF throws a warning and the event never enters the route — invisible to everyone (ADO **1594305**, DVN, fixed 2022.04+2023.04 HF). Current-gen variant: obligations unassigned with ECALWF warning "none of the desks have a limit that covers a budget of 0"; short-term fix = populate **Non-Payment Obligation Approval Amount** for the users; long-term fix in ADO **1862769** (DMB, state Develop as of 2026-09). Also note from 1862769: ECALWF only pulls events inside its date window — an event dated ahead of the run window is skipped, later events of the same STIP_KEY get routed.
3. **Payments stuck in inbox after approval** — users approve, payment stays on their desk (ADO **1702244**, DMB, `Engineering\Maintenance\Upstream\Customer Service\Land`; fixed and completed on 2022.04 / 2023.04 / 2024.04 / 2024.10 hotfix trains).
4. **Obligation stuck as "Held by Production"** — recommendation mis-set; scrubber + Pull Events did NOT clear it; no UI path to modify (SF **25-01003972**, Software Defect). Escalate for data fix.
5. **Resubmit silently fails** — "Query Successful" then nothing; workaround used: Pay/Drop to force the payment to PAY (SF **24-00972707**).

**Fix recipe:**
- Check client build vs the ECALWF abort-detect fix (delivered via patch; on 2023.04 HF train per 25-01039828). If pre-fix → G3 version issue; interim = scrubber + Pull Events.
- If on fixed build: pull the ECALWF process log/export and search for the event key; a missing event key + limit warning = desk limit gap (ADO 1862769 diagnostic path). Fix limits in User Limit Amount Admin / Non-Payment Obligation Approval Amount.
- Never hand-edit workflow tables without the scrubber first; ECALWFSCRUB exists specifically to delete orphaned workflow data tied to deleted/stale events (ADO **1693760**, hotfixed on all trains).

---

## 5. C3 — Wrong desk / wrong user routing

**Signature:** events assigned to the wrong desk, to only one user of a multi-user desk, to inactive desks, or approver dropdowns show stale users.

**Root causes:**
1. **From Group Select shows stale assigned user.** `QARCH_WF_TRAN_ROUTE_PREVIEW` is **not** updated when a desk assignment changes in Bulk Desk Maintenance, while `QARCH_WF_TRAN_INBOX_BASE` **is** — so the "Select Approval Desk" dropdown shows the old user until ECALWF re-runs for a new event. Also found: `MODULE_CD` null on `NAPVL_S1` route steps prevented the desk-update process from finding rows to update. (ADO **1699921**, HEC; fixed on all four hotfix trains.) Display-only in most cases — confirm whether actual assignment (INBOX_BASE) is correct before classifying severity.
2. **Multi-desk step routed to only one user** — user dollar limits on the desks decide who receives it; a $20k-limit user should not receive a >$20k payment (SF **24-00961941**, upgrade-era config). Verify User Limit Admin + User Limit Amount Admin rows (Workflow Usage = Payment Obligations) per ADO 1594305 repro.
3. **Events assigned to inactive desks/routes** (SF **25-01005081**); sibling defect: eCalendar User Limit Admin picklists show inactive users (ADO **1839727**, COP, Backlog/L4-Ready as of 2026-08).
4. **Mutual desk delegation = infinite loop.** Two desks delegating to each other in overlapping windows hung ECALWF/delegation (ADO **1608660**, OXY, fixed 2022.04 HF; validation now blocks overlapping delegation windows). Better route design per the work item: NApproval step with both desks, one approval required.
5. **Route Maintenance screen errors on save** — patched by adding "logic to check for a null object from the route simple cache" (SF **26-01086509**, Resolution verbatim). A cache-state defect: retry after app-pool recycle is the interim workaround, then patch.
6. **From Group Select multiple desks**: before the MRO change (ADO **1616149** / feature **1653352**, OCT 2023.04 HF), the step type "Mandatory Approval by Single Desk - From Group Select" allowed exactly one checked desk; also fixed there: ECALWF no longer depends on the `SEC_USER_ID` of whoever launches it.
7. **Route selection when multiple routes match** — clients repeatedly ask how the route is determined when an agreement meets criteria for more than one route (SF **24-00972333**); treat as expected-behavior/config until a specific mis-evaluation is shown.

**Fix recipe:** confirm desk activity flags + user limits first (G2), then check hotfix level against 1699921/1608660 (G3), then escalate with the ECALWF process export attached.

---

## 6. C4 — Processed events re-entering workflow / duplicates / locked-calendar leaks

**Signature:** a payment already paid (event processed) gets a new/reset workflow when the *next* period's amount is edited; locked payment calendars receive new workflows; eCal shows duplicated payment lines.

**Root causes & known fixes:**
1. **Amount edit resets a processed event's workflow.** Monthly payments with `EVENT_PROCESSED` not null were re-added to workflow when the next payment amount was modified (SF **24-00980776** — includes the customer's own diagnostic SQL, see §11). Same family: edit after calendar lock resubmitted the paid June-2024 payment into the locked June calendar (SF **24-00958240**); workflow restarted for payment changes in a locked month (SF **25-01030739**).
2. **Route Resolver fired twice on a payment amount change** (ADO **1645056**, fixed on 2022.04/2023.04/2024.04 HF trains, Performance-tagged).
3. **Saving multiple payments at once duplicated eCalendar events** (ADO **1691907**, SGY/GEC/DMB, fixed 2022.04/2023.04/2024.04 HF).
4. **Opposite failure:** a payment change that *should* have created a new workflow did not, and audit data was unclear — Resolution: "May 2025 Core Hotfix" (SF **24-00977855**, INFERRED = 2023.04-train hotfix delivered May 2025).
5. **Multiple payments on one agreement scrambled into a single inaccurate eCal line**; approval didn't flip QLS payment status to Pay. Fix: cleanup script for affected payments + latest hotfix for the long-term fix (SF **26-01063827**, Resolution verbatim).

**Fix recipe:** get exact client build; if pre-2024.10 HF, this whole family is G3 (already fixed — cite ADO 1645056/1691907/1702244 tags). Run §11 SQL to enumerate affected events for the cleanup script. Cleanup + hotfix is the standard pairing (26-01063827).

---

## 7. C5 — Email notifications & ECALNTC

**Signature:** users not receiving eCalendar task/reminder emails; notification batch shows step failures; unwanted escalation emails.

**Root causes:**
1. **Security group membership.** Four users received no eCal emails since Dec 2025 — they were absent from **Security Group 50029** (SF **26-01070529**, Resolution verbatim: "affected users are not receiving eCalendar email notifications due to their absence from Security Group 50029").
2. **Email PL/SQL package defect.** Core `QPCK_ECAL_EMAIL_CORE` was updated (leading line-break removed; HTML-compiling SQL condensed). Client override package exists per client, e.g. `ESUITE_QMER.QPCK_ECAL_EMAIL_MER` on MER DEV (SF **24-00989452**). ⇒ When emails break for one client only, diff the client override package against core.
3. **ECALNTC1 "fails on various steps"** — steps with no notifications to send report as failed; verify whether any notification was actually due before treating as defect (SF **24-00980062**, closed Application Configuration).
4. **Unapproved Events Escalation email** is system-generated and configurable — a client had it disabled on request (SF **26-01112324**). Setup-from-scratch requests (SF **25-01056440**, **25-01003481**) are config engagements, not defects.

**Fix recipe:** check group 50029 membership → check ECALNTC/notification schedule → diff `QPCK_ECAL_EMAIL_<CLIENT>` override vs `QPCK_ECAL_EMAIL_CORE` → only then treat as code.

---

## 8. C6 — Screen errors & performance (Inbox, Coordinator, List view, UBT)

1. **Random "Server Error" on eCal List view / approving events.** Root cause chain (SF **26-01063714**, quoting Quorum engineering guidance in the case): the list SQL uses `LISTAGG` to concatenate well numbers/names; when the string exceeds the 2k char field limit it errors. The three statements are `GET_EXP_LIST`, `GET_OBL_LIST`, `GET_PMT_LIST`, **not stored in the DB** — bundled in `Quorum.ECalendar.Resources` .dll in the eCalendar install directory on the web server, executing against the `LIS` schema. Fix was a patch adding listagg overflow handling; verification = check the .dll timestamp on the web server matches the patch.
2. **Coordinator screen won't load at record volume** (SF **24-00994867** — "Software update to fix the Ecal Coordinator screen load issue"); Coordinator Overdue tab errored on checking any record box (ADO **1649846**, OXY, 2023.04 HF).
3. **Inbox slow (~4s)** — `GetMultipleEventsForInbox` optimized (desk-query aggregation + ProtoBuf serialization), 2026.04 Hotfix Completed (ADO **1814133**). ECALWF now warns when a user exceeds 10k assigned records (ADO **1758256** history).
4. **Runaway eCalendar SQL consuming DB CPU** on Oracle PRD; RESULT_CACHE maintenance involved; fixed across all HF trains (ADO **1721573**, OXY).
5. **Grid defects:** Recommend/Approve fails when grid sorted by Agreement # (ADO **1665567**, 2023.04/2024.04 HF); "Calendar" column filter applied to CODE (PMT/OBL/EXP) instead of DESCRIPTION and Cost Center missing from the filter dictionary — `Quorum.QLS.ServiceCore\QQLSServiceCore_QQLSCalendarEventProvider.cs` (~lines 315-411, `dicReferenceTable`) (ADO **1578636**, state New); Inbox Undo doesn't revert edits (ADO **1838406**, 2026.04 HF).
6. **eCalendar UBT won't open — "This site can't be reached".** Citrix tile pointed at EWEB instead of WEB; fixing the tile config restored access (SF **26-01080105**, Resolution verbatim). Environment/access issue, not product.
7. **Read-only users can't save searches on eCal widgets** — security config (SF **24-00986832**); eCal widgets stopped working — config settings (SF **24-00985729**).

---

## 9. C7 — Recommendations & approvals

1. **Recommendations not displaying in PROD after a deployment** while identical process works in QA (SF **23-00935358**, Software Defect) — deployment-delta problem; compare eCal config scripts/build between environments first.
2. **Empty recommendations got approved** — audit red flag; a few payments/obligations passed workflow approval with no recommendation recorded (SF **24-00965590**, Software Defect; client supplied workflow-table exports for analysis).
3. **Ready-for-Recommendation gate lost in current eCalendar.** Legacy eCal honored config `EnableReadyForRecommendation` + `STIPULATION_OBLIGATIONS.READY_FOR_ECAL_REC_FL = 'Y'` before routing events; the gate was never carried into the current eCalendar route-assignment code — flag and config are wired in the Payment screen UI/persistence but never consulted as an eligibility filter (ADO **1867157**, EQC, escalated, Ready for Code Review as of 2026-09-03; root-cause text quoted from work-item history).
4. **Approver groups not editable from the front end** — new users' Approvers dropdown empty because existing approver sets were loaded via script; fix was another script adding the 11 approvers to the new users (SF **25-01055338**). Treat "can't select approvers for new user" as data-load pattern, not defect.
5. **Missing recommendation type** (e.g. "Acknowledged" for Obligations) after upgrade = config migration gap (SF **24-00946137**); recommendation not saving in test = config (SF **25-01033011**).
6. **Config location note:** eCalendar detail-view configs migrated from Legacy "eCalendar" key group to **eCalendarManagement** group; starting 24.04 a migration DB script copies Legacy values forward; clients can override on customer layers (ADO **1647330**, APA).

---

## 10. C8 — Obligation remarks / comments sync & legacy eCal

1. **eCal remarks not flowing to QLS.** Legacy eCal is deprecated; the remark-flow defect is not present in 2026.04 — "The functionality/fix will be available upon upgrade" (SF **25-01037615**, Resolution verbatim). Classify as G3 version issue.
2. **Historic eCal comments missing in QLS** — one-time script to copy eCalendar comments to QLS Notes (SF **24-00943542**); remark formatting fixed via script (SF **26-01070883**); old-environment comments appearing in a new eCalendar environment = migration defect (SF **24-00985917**).
3. **Obligation comment performance on eCal** — open Software Defect, Complete-Pending Delivery as of 2026-09 (SF **26-01080100**).
4. **Orphaned workflow metadata after agreement deletes** — deleting an agreement with INPROGRESS events left workflow rows behind; **ECALWFSCRUB** batch deletes orphaned workflow data tied to events (ADO **1693760**, fixed/completed on 2022.04→2024.10 HF trains, Performance-tagged).

---

## 11. Known ADO items (cite these before writing a new bug)

| ADO ID | Project | Title (abridged) | State / Fixed-in |
|---|---|---|---|
| 1702244 | QuorumSoftware | DMB - Payments stuck in eCalendar inbox | Closed; 2022.04/2023.04/2024.04/2024.10 HF Completed |
| 1693760 | QuorumSoftware | eCalendar Workflow - delete orphaned WF data (ECALWFSCRUB) | Closed; all 4 HF trains |
| 1699921 | QuorumSoftware | HEC - From Group Select assigned users not updating (QARCH_WF_TRAN_ROUTE_PREVIEW stale, MODULE_CD null) | Closed; all 4 HF trains |
| 1594305 | QuorumSoftware | DVN - desk $ limit keeps route from being assigned; ECALWF warning | Closed; 2022.04+2023.04 HF |
| 1862769 | Quorum | DMB - Scheduler not picking up all events ("no desk covers budget of 0") | Develop (2026-09); workaround: Non-Payment Obligation Approval Amount |
| 1645056 | QuorumSoftware | Route Resolver triggering twice on payment amount change | Closed; 2022.04/2023.04/2024.04 HF |
| 1691907 | QuorumSoftware | eCalendar payments duplicated when saving multiple at once | Closed; 2022.04/2023.04/2024.04 HF |
| 1751061 | QuorumSoftware | Inbox empty when agreement county invalid (ECALWF tolerance added) | Closed 2025-08+ |
| 1708993 | QuorumSoftware | SGY 24-00992376 eCalendar workflows payment processing | Closed; 2022.04/2024.04 HF |
| 1616149 / 1653352 | QuorumSoftware | MRO - From Group Select multiple desks (ECALWF QFC change; SEC_USER_ID independence) | Closed; OCT 2023.04 HF |
| 1608660 | QuorumSoftware | OXY - infinite loop, mutual desk delegation | Closed; 2022.04 HF |
| 1651009 | QuorumSoftware | ECALWF queries StipulationObligationsDO one-at-a-time (perf) | Closed; 2022.04/2023.04 HF |
| 1867157 | Quorum | EQC - Ready For Recommendation flag not honored in current eCal | Ready for Code Review (2026-09) |
| 1814133 | Quorum | Inbox slow — optimize GetMultipleEventsForInbox | Closed; 2026.04 HF |
| 1838406 | Quorum | Inbox Undo does not revert modified records | Closed; 2026.04 HF |
| 1721573 | QuorumSoftware | OXY - eCalendar SQL never completes, consumes CPU (RESULT_CACHE) | Closed; all 4 HF trains |
| 1665567 | QuorumSoftware | Inbox grid Recommend/Approve fails when sorted by Agreement # | Closed; 2023.04/2024.04 HF |
| 1650986 | QuorumSoftware | GEC - Calendar Type wrong for Expirations with Extension Payments | Closed; 2022.04→2024.04 HF |
| 1649846 | QuorumSoftware | OXY - Coordinator Overdue tab error on checkbox | Closed; 2023.04 HF |
| 1578636 | Quorum | eCalendar grid filters (Calendar/Cost Center) — QQLSServiceCore_QQLSCalendarEventProvider.cs dicReferenceTable | New (P1) |
| 1647330 | QuorumSoftware | APA - eCalendar detail views client-overridable; config group migration to eCalendarManagement | Closed; 2023.04 HF |
| 1695091 | QuorumSoftware | GIS link missing in Calendar/eCalendar actions | Closed; 2023.04→2024.10 HF |
| 1839727 | Quorum | COP - inactive users in eCalendar picklists (User Limit Admin) | Backlog, L4-Ready |
| 1708512 | QuorumSoftware | eCalendar Task List incorrect padding | Closed; Product-2024.10 |
| 1758256 | QuorumSoftware | EQC Perf - Inbox empty / no desks assigned; 10k-record ECALWF warning | Closed |

Hotfix-tag convention: `YYYY.MM Hotfix` / `... Completed` per train (2022.04, 2023.04, 2024.04, 2024.10, 2026.04). "Fixed in" claims above are CONFIRMED from work-item tags; mapping a tag to a specific client build number stays INFERRED until release notes are checked.

---

## 12. Diagnostic SQL (Oracle, `lis` schema)

**Verbatim customer diagnostic from SF 24-00980776** — find processed events whose workflow was touched afterward (processed-event-reset defect, C4):

```sql
select A.AGMT_NUM, E.EVNT_DATE, E.WF_STATUS_CD, E.WF_INSTANCE_ID,
       E.WF_ROUTE_NM_SELECTED, E.EVENT_STATUS, E.EVENT_PROCESSED,
       SF.STIP_FREQ_DESC, S.STIP_KEY, L.*
from EVENTS_LOG L
join EVENTS E                    on L.EVNT_KEY = E.EVNT_KEY
join STIPULATION_OBLIGATIONS S   on S.STIP_KEY = E.STIP_KEY
join STIPULATION_FREQUENCIES SF  on S.STIP_FREQ_CODE = SF.STIP_FREQ_CODE
join ALL_AGREEMENTS A            on E.ARRG_KEY = A.ARRG_KEY
where E.EVENT_PROCESSED < L.UPDT_DATE
  and SF.STIP_FREQ_DESC = 'Monthly'
order by L.UPDT_DATE;
```

**Derived checks (INFERRED — built strictly from tables/columns confirmed in the cases/work items above; verify against live schema before running):**

```sql
-- C2: events in a route with no desk (orphaned assignment signature)
select E.EVNT_KEY, E.WF_INSTANCE_ID, E.WF_ROUTE_NM_SELECTED, E.WF_STATUS_CD, E.EVENT_STATUS
from EVENTS E
where E.WF_ROUTE_NM_SELECTED is not null
  and E.WF_STATUS_CD = 'INPROGRESS'
  and not exists (select 1 from QARCH_WF_TRAN_INBOX_BASE B
                  where B.WF_INSTANCE_ID = E.WF_INSTANCE_ID);

-- C3: stale From Group Select preview rows (ADO 1699921 signature)
select * from QARCH_WF_TRAN_ROUTE_PREVIEW where MODULE_CD is null;

-- C7: Ready-for-Recommendation staging state (ADO 1867157)
select STIP_KEY, READY_FOR_ECAL_REC_FL from STIPULATION_OBLIGATIONS
where READY_FOR_ECAL_REC_FL = 'Y';
```

Confirmed workflow tables: `EVENTS`, `EVENTS_LOG`, `STIPULATION_OBLIGATIONS`, `STIPULATION_FREQUENCIES`, `ALL_AGREEMENTS`, `QARCH_WF_TRAN_INBOX_BASE`, `QARCH_WF_TRAN_ROUTE_PREVIEW`, plus batch log `EVENTS_WFBATCH_LOG` (named in ADO 1651009 history). ECALWF warning text seen in logs: "No WF_INSTANCE_ID" (SF 22-00825943).

---

## 13. Expected-Behavior FAQ

- **"ECALNTC1 shows failed steps"** — steps with zero notifications due can report as failures; confirm a notification was actually owed before classifying as defect (SF 24-00980062).
- **"An agreement matches two routes — which wins?"** — route resolution precedence is design behavior; ask for the specific route criteria and demonstrate the resolver decision before accepting "wrong route" as a bug (SF 24-00972333 pattern).
- **"Editing next year's payment amount re-triggered review"** — an amount/date change legitimately resubmits the *current* workflow; the defect is only when a **processed/locked** event resets (C4 boundary; ADO 1645056 history: change that doesn't meet resubmit criteria now logs an audit note instead).
- **"Scrubber + Pull Events fixed it — case closed?"** — once is fine; weekly recurrence = the ECALWF abort defect, escalate with build info (SF 24-00994588).
- **"Unapproved Events Escalation emails are unwanted"** — configurable; can be disabled per client (SF 26-01112324).
- **"QQM can't query eCalendar tables"** — QQM table access is unlocked via configuration, not a defect (SF 25-01041450).

---

## 14. Escalation

- **Escalation path:** L4 bug → area path `Quorum\North America\Upstream\Land RnD` (current) or `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` (maintenance history). Repos: `Quorum.QLS.ServiceCore` (e.g. `QQLSServiceCore_QQLSCalendarEventProvider.cs`, `QQLSServiceCore_EcalBatch.cs`), `Quorum.QLS.Web`, `Quorum.QLS.Metadata`, `QLS.Batch`; eCalendar list SQL lives in the `Quorum.ECalendar.Resources` .dll on the web server, not in the DB (SF 26-01063714).
- **Always attach:** client build + hotfix tag level, ECALWF process export (event-key search), scrubber run results, and the §12 verbatim SQL output for workflow-reset cases.
- **Data corrections** (stuck "Held by Production", scrambled multi-payment lines, approver loads, comment copies) are script-based per precedent — SF 25-01003972, 26-01063827, 25-01055338, 24-00943542 — route to the maintenance team with the precedent case number.
- **DEV-tier caveat:** schema/config findings from a DEV metadata connection are CONFIRMED anchors; client-PRD data-state claims stay INFERRED until run on the client environment.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
