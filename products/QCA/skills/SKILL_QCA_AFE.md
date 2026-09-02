# SKILL: QCA — AFE (Authorization for Expenditure) Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Cost Accounting (QCA) — upstream oil-and-gas accounting suite (myQuorum / On Demand / QCloud)
**Scope:** The **AFE** subsystem — AFE creation/supplements, the **AFE approval workflow** (routes, desks, approval limits, inboxes), **AFE status lifecycle** (EST → PEN → O/Open → CLD/Closed; IA), AFE **reclass** (AFERECLASS / WIP-to-NET), AFE **import** (AFEEXTIMP from Execute, AFE_IMPORT, AFE_HDRUPL), **AFE ↔ DOI working-interest sync** (AFE_SYNCDOI), **notification emails**, **document attachments**, AFE **subledger / account / line-category** setup, and the **V17 / QCloud upgrade** fallout that dominates this category. Adjacent QCA areas (JIB, GL/AP vouchers, DOI master) appear only where an AFE case touches them.
**Companion skills:** JIB / billing decks → SKILL_QCA_JIB.md (planned); DOI / ownership master → SKILL_QCA_DOI.md (planned); GL/AP/JE → SKILL_QCA_GL_AP.md (planned). AFE *consumes* DOI ownership (working interest), cost-center/property master, and AFE-Type/account/line-category config, and *produces* budget + the AFE subledger that JIB and GL reclass read. **When a working-interest or account number is wrong on an AFE, fix the upstream DOI / AFE-Type / account-line-category config first — the AFE is usually the messenger.**

> **Evidence base:** 1,094 closed QCA AFE cases. Root-cause split: (blank) 345, Training 110, Customer Error 78, Other 72, **Application Configuration 71**, **Software Defect 71**, Customer Cancelled 69, Hardware/Software Change 56, Business Change 40, … **ChangeConfig 3**. This skill mines the **145 actionable** cases (Software Defect 71 + Application Configuration 71 + ChangeConfig 3) for fix recipes, plus ~35 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts, Status Lifecycle & Pipeline](#2-concepts-status-lifecycle--pipeline)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — AFE stuck in Pending after final approval (HIGHEST FREQUENCY)](#4-cluster-a--afe-stuck-in-pending-after-final-approval)
5. [Cluster B — AFE Reclass / WIP-to-NET process failures](#5-cluster-b--afe-reclass--wip-to-net-process-failures)
6. [Cluster C — Notification emails not generating](#6-cluster-c--notification-emails-not-generating)
7. [Cluster D — AFE Import (AFEEXTIMP / AFE_IMPORT / AFE_HDRUPL) failures](#7-cluster-d--afe-import-failures)
8. [Cluster E — V17 / QCloud upgrade fallout (usernames, desks, ValidatePropBusUnit)](#8-cluster-e--v17--qcloud-upgrade-fallout)
9. [Cluster F — Working Interest doubling / WI ≠ DOI (AFE_SYNCDOI)](#9-cluster-f--working-interest-doubling--wi--doi)
10. [Cluster G — Document attachment errors](#10-cluster-g--document-attachment-errors)
11. [Cluster H — Security / access / personas / web down](#11-cluster-h--security--access--personas--web-down)
12. [Cluster I — AFE Subledger / account / line-category mapping](#12-cluster-i--afe-subledger--account--line-category-mapping)
13. [Cluster J — Route / Desk maintenance & approval limits](#13-cluster-j--route--desk-maintenance--approval-limits)
14. [Cluster K — Reopen / close / cancel AFE status changes](#14-cluster-k--reopen--close--cancel-afe-status-changes)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Key Code, Processes & Repos](#18-key-code-processes--repos)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| "AFE NNNNNN stuck in **Pending** status after all approvals / after Cancel Workflow" | Timeout during `HandleFinalApproval` or during a Cancel-Workflow action left the AFE in PEN; the workflow instance is gone | §4 — confirm route fully approved, then **status-reset script** to OPEN (clears WF + populates open-date fields); long-term = upgrade |
| AFE **route has full approval but won't move to Open**; "Workflow Instance ID no longer available" / "Workflow does not exist" | Same family as above (orphaned/aborted WF) | §4 — cancel & restart WF, or status-reset script |
| **AFERECLASS / AFE Reclass** process fails / "won't run" / "DOI KEY is invalid" | Bad DOI/Tier/DO-Type/account/BU data feeding the reclass; missing BU pick-list; bad data carried from V16→V17 | §5 — validate PROP_NO/TIER/DO_TYPE combo & account; clean AFE_SL and retry |
| **AFE approval emails not generating** (esp. post-upgrade) | Missing/changed `WORKFLOW` global-config URL keys; missing Event Detector; email not run | §6 — check `WORKFLOW` global config keys + Event Detector Setup + run QEMAIL (QP063) |
| **AFEEXTIMP / AFE_IMPORT failing** | Missing **Event Detector** for `AFE_EXTIMP` (no user on Users tab); bad XML data; long AFE-no length | §7 — add Event Detector + user, restart QPECS; check XML for dup/unique-key |
| **Working Interest doubling** on AFE Cost Center tab vs DOI (>1) | `AFE_SYNCDOI` inflated WI for AFEs with **multiple affiliates/cost centers on different internal BAs**; or Cartesian join over un-dated `GONL_PROP_EFF_DT` time-slices in registered SQL | §9 — confirm fix build (2024.04+); workaround = registered-SQL date filter or hotfix |
| **Can't open / query an AFE** in Web ("Query returned no results"), but it exists in DB | A validation (e.g. duplicate-supplement date/time, or `ValidatePropBusUnit` runtime lookup) blocks the load | §8/§11 — clean dup supplements; or disable the `ValidatePropBusUnit` object |
| **Validation `AFEMaintNNNNNN` fires incorrectly** ("Operated checkbox should not be checked", "Prop/BU invalid") though SQL data is correct | Runtime validation-lookup bug (fixed 2025.04); or stale Web cache | §8 — disable `ValidatePropBusUnit` / `ValidatePropBusUnit` object use; refresh cache; replace cost center as interim |
| Post-**upgrade**: blank AFE Inbox / no widget count / no Approval button / "Workflow does not exist" | Desks not re-pointed to new AD/Okta accounts; old→new **username** not converted in `QARCH_WF%` & security tables; missing approval limits | §8 — username-conversion script + reconfigure desks/approval limits |
| **Can't attach a document** to an AFE; ".PNG not supported" | File-extension validation is **case-sensitive** (`.PNG` rejected, `.png` accepted) | §10 — rename to lower-case as workaround; code fix makes it case-insensitive |
| "No Personas" in AFE Web / can't reach AFEs / rights error saving AFE | Missing **Modules in SC010 (User Assignment)** or missing/removed security group/object | §11 — assign modules/security group/object |
| **QCA web down / 404 / can't access** | App service needs restart; service-account NTFS perms; URL config | §11 — restart QCA Web / QPECS; verify config & perms |
| **AFE Subledger** wrong / account not pulling / line-category blank | AFE-Type **account** config or **AFE Line Category** missing the account; subledger restage | §12 — add account to AFE Type / AFE Line Category |
| **Can't inactivate an AFE Route / delete an assigned desk** | A validation blocks it; older-build defect | §13 — relax the validation entry, or upgrade (fix in V17) |
| Need to **reopen / close / cancel** an AFE blocked by status validation | Status change requires a script (missing DOI/tier/property fields block reopen) | §14 — status-change script, or create a replacement AFE |

---

## 2. Concepts, Status Lifecycle & Pipeline

```
[DOI ownership (WI/NRI)] + [Property / Cost Center master] + [AFE Type → Accounts / Line Categories] + [Workflow Route + Desks]
      │
      ▼  AFE CREATION (Web "AFE Maintenance" / Classic GLAFE) — header + Cost Center tab + Supplements
      │      └─ AFE_SYNCDOI pulls WI from DOI onto the AFE Cost Center tab
      ▼  APPROVAL WORKFLOW (Route → Desks → Approval Limits; AFE Inbox / Full Inbox)
      │      EST (Estimate) ─submit→ PEN (Pending) ─final approval→ O (Open/Approved)
      │      REJ (Rejected) ; IA (Inactive/In-Approval) ; CLD (Closed) ; CANCELLED
      ▼  BOOKING — GL/AP transactions code to the AFE's Cost Center(s)
      ▼  AFERECLASS (WIP→NET) → AFE Subledger (QTRAN_AFE_SL / AFE_SL) → JIB / GL
```

### Key terms (Quorum/QCA vocabulary)
- **AFE** = Authorization for Expenditure; header in **`QCTRL_AFE_HDR`**, detail/budget in **`QCTRL_AFE_DETAIL`**, supplements in supplement tables, subledger in **`QTRAN_AFE_SL` / AFE_SL**.
- **AFE status codes:** `EST` Estimate (draft), `PEN` Pending (in workflow), `O`/Open (approved & bookable), `IA` Inactive/In-Approval, `REJ` Rejected, `CLD` Closed, `CANCELLED`. The recurring defect is an AFE **stuck in PEN** after full approval (§4).
- **AFE Type** = template that drives which **Accounts** and **Line Categories** are valid, the **DOI rule** (Required / Not Allowed), and budget behavior. "Account not budgeted for this AFE" almost always means the account isn't on the AFE Type (§12, §17).
- **AFE Line Category** = maps an account → a category description shown on the AFE; a new GL account won't appear until added here (AFE → Maintenance → AFE Line Category) (26-01064040, 25-01038651).
- **Workflow Route / Desk / Approval Limit:** a **Route** is an ordered set of steps; each step targets a **Desk** (a role inbox) with a **step type** — e.g. *Approval Limit by Single Desk*, *Approval Limit by All Desks in Group*, *Mandatory if Over ($)*. Approvers act in the **AFE Inbox / AFE Full Inbox**. Misconfigured step types cause approval-limit errors and "mandatory-if-over skipped" (§13, §17).
- **Cost Center (CC010)** = the property/cost unit an AFE books to; carries Property, Tier, DO Type, Internal BA, and the working interest. Multiple CCs per AFE are supported.
- **Affiliate AFEs** = the same AFE replicated across affiliated **Business Units (BUs)**; affiliate records follow the **primary BU's** workflow. Multiple supplement/affiliate rows are *expected* (26-01091430).
- **AFERECLASS** (a.k.a. AFE Reclass / WIP-to-NET) = batch process that reclasses work-in-progress to net working interest and writes the **AFE subledger**; keyed on PROP_NO + TIER + DO_TYPE + account + BU.
- **AFEEXTIMP** = import of AFEs **from Execute** (drilling/ops) **into QCA Upstream** via SFTP file + an **Event Detector** (`AFE_EXTIMP`). **AFE_IMPORT / AFE_HDRUPL** = bulk header/detail upload processes.
- **AFE_SYNCDOI** = "Sync JIB DOI Decimal to QCA AFE" process; pulls working interest from DOI onto the AFE. Bug family: it doubled WI when an AFE spanned multiple affiliates/CCs on different internal BAs (§9).
- **Event Detector / `QARCH_EVENT_NOTICE_EMAIL`** = the notification engine that, on a workflow event (e.g. `AFE_FNLAPR`, `AFE_EXTIMP`), generates an email row; the **QEMAIL** process (screen **QP063**) actually sends queued emails.
- **`WORKFLOW` global config keys** = environment-specific config (Classic: Maintenance → Configuration Settings → Global) holding the **AFE Web / Inbox URLs** baked into approval emails: `AFEAPPROVAL_INBOX_URL`, `QCA_INBOX_URL`, `AFEAPPROVAL_INBOX_ITEM_URL`, `QCA_INBOX_ITEM_URL`. Stale after an upgrade/site move → emails point at the old site or stop (§6).
- **`ValidatePropBusUnit`** = a validation **object use** (under parent `GLAFE [UPS]`, app layer `QCEN`) in `QARCH_CTRL_OBJECT_USE`. Disabling it is the repeated unblock for "can't reclass / can't save / can't open AFE" Permian-upgrade cases (§5, §8).
- **DD** = Document Distribution (attachment store). **QPECS** = the Quorum process/event control service that must be restarted after Event-Detector/notification config changes. **QCloud 1.0 → 1.5** username format change underlies many upgrade tickets.

---

## 3. Decision Tree

```
QCA AFE case
│
├─ AFE STUCK after approval / workflow gone? (PEN won't move to Open; "Workflow Instance ID no longer available")
│     → §4  Get AFE_NO + BUS_UNIT_CD; confirm route fully approved; status-reset script to OPEN (clears WF, sets open-date fields)
│
├─ A PROCESS failed?
│   ├─ AFERECLASS / "won't run" / "DOI KEY invalid" / "no BU pick list"      → §5  (DOI/Tier/DO_TYPE/account/BU data; clean AFE_SL; retry; disable ValidatePropBusUnit)
│   ├─ AFEEXTIMP / AFE_IMPORT / AFE_HDRUPL failing or never finishes          → §7  (Event Detector + user; restart QPECS; XML dup/unique-key)
│   └─ AFE_SYNCDOI inflating Working Interest                                 → §9  (multi-affiliate/CC WI doubling; fix build 2024.04+)
│
├─ EMAILS?  AFE approval/notification emails not sending / point at old site → §6  (WORKFLOW global config URLs + Event Detector + run QEMAIL/QP063)
│
├─ UPGRADE (V17 / QCloud / 2024.10) fallout?
│   ├─ Blank inbox / no widget / no approve button / "workflow does not exist" → §8  (re-point desks to AD/Okta; username-conversion script; approval limits)
│   ├─ Validation fires wrongly / can't open AFE / can't reclass               → §8  (disable ValidatePropBusUnit; refresh cache; bad V16→V17 data scripts)
│   └─ Desk IDs / DESK ID code table / convert AFE Desk usernames              → §8  (set up desk codes; convert usernames)
│
├─ Can't ATTACH a document (".PNG not supported", performance)               → §10 (lower-case file ext workaround; case-insensitive code fix; DD perf)
│
├─ ACCESS / SECURITY?  no Personas / rights error / web down / 404           → §11 (SC010 Modules; security group/object; restart QCA Web/QPECS)
│
├─ SUBLEDGER / ACCOUNT wrong / line category blank                          → §12 (add account to AFE Type / AFE Line Category; restage AFE_SL)
│
├─ ROUTE / DESK / APPROVAL-LIMIT can't-configure                            → §13 (relax validation to inactivate route; correct step type; approver vs author)
│
├─ Need to REOPEN / CLOSE / CANCEL an AFE (status validation blocks)        → §14 (status-change script, or create replacement AFE)
│
└─ "How do I…", supplement question, account-not-budgeted, WI looks off     → §17 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — AFE stuck in Pending after final approval

**The single largest actionable AFE signature (≈15 cases, recurring across JNE, FMO, MAC, RLY, PRM, NOG, Solaris, Seneca).** An AFE route receives **all required approvals** (or a user clicks **Cancel/Abort Workflow**), but the AFE **does not transition PEN → Open**, and the workflow instance is gone, so it can't be actioned from the UI.

**Symptoms (verbatim):**
- "AFE 261080 stuck in pending like our last instance. Is a script needed to fix this system error?" (26-01092076)
- "We are unable to use this AFE unless it moves to approved status. It is currently stuck in pending status." (25-01032800, AFE 250766)
- "the user next in line… encountered an error indicating that the **Workflow Instance ID was no longer available**." (25-01028638)
- "Pending AFE's are stuck — **Workflow does not exist** error" (25-01054714, post-upgrade).

**Root cause:** a **timeout during the final-approval handler** (the `HandleFinalApproval` path) or during a **Cancel-Workflow** action commits the approval but fails to flip the status and populate the open-date / open fields; the workflow instance is then orphaned. Confirmed in 25-01018400 ("Code was not properly filtering the event type" for `AFE_ONLNEM` when changing IA→O) and 24-00960832 ("**code changes are made to handle time out on the HandleFinalApproval method**").

**Fix recipe:**
1. Get **AFE_NO + BUS_UNIT_CD** (+ OPER_BUS_SEG_CD). Confirm in `QARCH_WF%` that the route is fully approved and no live workflow instance remains.
2. **Status-reset script** — the standard unblock. Two variants seen:
   - Reset to **OPEN** and populate the fields that normally get set on open ("…move the AFE to the OPEN status… and all other fields that get populated when an AFE moves into the OPEN status", 26-01088131; also 26-01083498, 26-01092076, 25-01032800, 25-01030296, 24-00952367).
   - Reset to **EST** so the user can re-send through workflow (25-01052321, 25-01053199 for a REJ AFE with no inbox).
3. Alternatively **cancel and restart the workflow** to push it back to draft and onto a fresh route (25-01028638).
4. **Long-term:** the timeout/handler defects are fixed in newer builds — recommend the client upgrade (25-01032800, 25-01054714 resolved by upgrade-WF scripts). ADO: RLY **#1699362/#1720965/#1721437** and MAC **#1761278/#1761279** (all Closed) are the canonical "AFEs stuck in Pending — Script Approval / Abort Workflow" items.

> **Tell-tale:** "stuck in pending **like last time**" — this is repeat operational toil at high-volume clients (Jonah especially). The script is routine; capture AFE_NO + BU and verify-SELECT before UPDATE.

---

## 5. Cluster B — AFE Reclass / WIP-to-NET process failures

**≈12 actionable cases, very heavy in the Permian Resources V17 upgrade and Solaris.** The **AFERECLASS** (a.k.a. AFE Reclass / WIP-to-NET) process errors or "won't run."

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| "DOI KEY is invalid. Property X Tier 4 DO Type JIB" running AFERECLASS | The PROP_NO/TIER/DO_TYPE combo didn't exist — Tier 4 was a **REV** DO Type, not JIB; GL batches defaulted to Tier 4 | **Reverse the GL batches, clean up AFE_SL, retry** the process after data is corrected | 25-01046200 |
| AFE Reclass for BU 600 fails / "doesn't run successfully" / "no BU pick list" | Bad data carried from **V16 → V17** during mock cutover; missing BU setup | Apply the **same V16 data-fix scripts to V17 PRD**; ready for retest | 24-00995408 |
| Permian Upgrade AFE Reclass Company 600 failed / "Reclass not picking up Account" | Validation object blocking + account config | **Disable object use `GLAFE [UPS] → ValidatePropBusUnit`** (see SQL in §16); fix account mapping | 25-01017092, 25-01006922, 25-01026683, 25-00998951, 25-01003297 |
| "WIP to NET — Not Working" | AFERECLASS didn't load data | **Data script** to load the records the process missed | 22-00583822 |
| Critical AFE reclass process issue; records didn't reach AFE_SL | Staging gap in AFE_IMPORT/reclass | **Script to restage** records that didn't make it to AFE_SL | 22-00853225 |
| BU 610 AFE reclass will not run | Config/data | **Script** (reviewed via ADO #1814008) | 26-01104716 |
| WIP→NET reclass account mapping (REOP) | Account config per AFE type | Loaded accounts per AFE type into PRD | 26-01086097 |

**Fix recipe:**
1. Get the **exact error + the PROP_NO / TIER / DO_TYPE / account / BU** in it. The "DOI KEY is invalid" error means that key combination isn't valid in DOI — verify with the DOI team whether the Tier/DO_TYPE is REV vs JIB (25-01046200).
2. If data is bad: **reverse any GL batches that posted with the wrong key, clean the AFE_SL, and retry**. For upgrade clients, check whether **bad V16 data was carried into V17** and re-apply the V16 fix scripts (24-00995408).
3. For Permian-style "reclass won't run / can't save," **disable the `ValidatePropBusUnit` object use** (§16 SQL) — this is the repeated unblock (25-01006922, 25-01017092, 25-01026683). ADO **#1699780** ("Long Term — ARS — Missing validation for AFE RECLASS") tracks the proper validation fix.

---

## 6. Cluster C — Notification emails not generating

**≈9 actionable cases.** AFE approval/notification emails stop, or (post-upgrade) point at the **old site**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| AFE final-approval emails not generating post-upgrade | Missing **`WORKFLOW` global-config URL keys** | Add `AFEAPPROVAL_INBOX_URL`, `QCA_INBOX_URL`, `AFEAPPROVAL_INBOX_ITEM_URL`, `QCA_INBOX_ITEM_URL` (Env-Specific layer, Key Group `WORKFLOW`); update & restart app | 26-01079663 |
| Approval emails reference the **old site** | Stale `WORKFLOW` URL config after site move | Update the `WORKFLOW` env-layer config keys | 24-00946620, 25-01032654 |
| AFE notifications not sending / not working | Notifications off + bad email links; email not run | **Turn on AFE notifications, fix email links**; run **QEMAIL (QP063)**; set the approver's email in **Route Maintenance** | 24-00952566, 22-00825917, 23-00887193 |
| No `QARCH_EVENT_NOTICE_EMAIL` item created for a submitted AFE | Event Detector / event-role wiring missing | Run **QEMAIL (QP063)** + set user email in Route Maintenance; set up **event role definition tied to the event detector** | 23-00887193, 24-00965188 |
| `AFE_FNLAPR` email shows the wrong data | Event-type / template config | Correct the event-type config | 22-00828601 |
| Password for the email account expired (emails silently stop) | Mail-account credential | **Update the email password** | 25-01049046 |

**Fix recipe:** for "emails stopped" walk this order — (1) is the **email account password** valid (25-01049046)? (2) are the **`WORKFLOW` global-config URL keys** present and pointing at the *current* site (26-01079663, 24-00946620, 25-01032654)? (3) is there an **Event Detector** + event-role tied to the event (24-00965188, 26-01083886 for AFE_EXTIMP)? (4) is the approver's **email set in Route Maintenance** and is the **QEMAIL process (QP063)** running to flush the queue (22-00825917, 23-00887193)? Restart the app/QPECS after config changes.

---

## 7. Cluster D — AFE Import failures

**≈9 actionable cases.** Imports from Execute (**AFEEXTIMP**) and bulk uploads (**AFE_IMPORT / AFE_HDRUPL**) fail.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| AFEEXTIMP process failing | **Missing Event Detector for `AFE_EXTIMP`** — and crucially **no user on the Users tab** (process fails if it has no one to notify) | Maintenance → Notification → **Event Detector Setup**: add `AFE_EXTIMP`, assign Event ID, set app **Environment Specific**, **add a user on the Users tab**, restart **QPECS**, rerun | 26-01083886, 26-01088281 / ADO **#1789253** |
| AFEEXTIMP fails on long AFE numbers (e.g. 2670311000) | AFE-no length handling | Code (proposed) | ADO **#1775353** (Proposed) |
| AFEEXTIMP "Violation of UNIQUE KEY `AK_QCTRL_AFE_DETAIL`" | **Duplicate key in the source XML file** | Fix the XML data (client-side); not a product bug | 25-01031183 |
| AFE_IMPORT fails / SPEs on communication errors | Import-handler defect ("infinite loop"); also ACQ AFE Type formula not updated for Fast Calc | **Code changes to handle import failure** (24-00957017); update `AFE_CALC` formula with **double equals** for Fast Calc (25-01003297) | 24-00957017, 22-00669767, 25-01003297 / ADO **#1624582, #1628458** (AFE_IMPORT perf in `AFE_IMPVLD` step) |
| AFE_HDRUPL never finishes / stuck in processing | Process hang | Investigate/clear stuck process (Parsley) | 22-00690450 |
| AFE Upload process issues | Upload defect | Code/build | 22-00825518 |

**Fix recipe:** for **AFEEXTIMP failing**, the #1 cause is a **missing Event Detector for `AFE_EXTIMP` with no user assigned** — add it (Maintenance → Notification → Event Detector Setup), **make sure a user is on the Users tab**, set Environment Specific, **restart QPECS**, rerun (26-01083886, 26-01088281). For unique-key/`AK_QCTRL_AFE_DETAIL` violations, the **source XML has duplicates** — fix the file (25-01031183). For AFE_IMPORT with the ACQ type, confirm the `AFE_CALC` formula uses **`==`** (Fast Calc syntax) since the switch off UCALC (25-01003297).

---

## 8. Cluster E — V17 / QCloud upgrade fallout

**≈13 actionable cases — the dominant *Application Configuration* theme.** Upgrades (V16→V17, QCloud 1.0→1.5, 2024.10) break AFE because **usernames/desks/security weren't re-mapped** and stale **validations/cache** block the new Web.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Blank AFE Inbox / no widget count / no Approve button after OnPrem migration | Desks not re-pointed to **new AD accounts**; admin **approval limits** missing | Manually reconfigure desks to new AD accounts + create admin approval limits → inbox/widget/approve all work | 24-00955766 |
| Pending AFEs "Workflow does not exist" after upgrade | QCloud **1.0 usernames** not converted to **1.5** in `QARCH_WF%` tables | **Run username-conversion script** for `QARCH_WF%` | 25-01020756, 25-01054714 |
| AFE Desk ID code-table error / convert AFE Desk ID usernames | Desk codes from prior acquisitions not set up; usernames in old format | Set up the missing **desk codes**; convert usernames | 25-01025959, 25-01023885 (orig desk `SRDRLENG` → `NOTIFY1`) |
| Old user IDs still on desks / can't submit / no submitter desks / supplement-approver DeskId null | Security **user-ID format** changed on migration | **Update all tables** to change old user-ID formats → new IDs | 23-00932191, 23-00932331, 23-00932908, 23-00932917 |
| Can't open AFE / validation fires wrongly / reclass won't run (Permian) | Stale validation **object** `GLAFE [UPS] → ValidatePropBusUnit` | **Disable the object use** (§16 SQL); also `ValidatePropBusUnit` / `ValidatePropBusUnit` per 26-01104716, 25-01006922 | 25-01006922, 25-01017092, 25-01026683, 26-01104716 |
| Validation `AFEMaint000570` "Operated checkbox should not be checked" though SQL is correct | **Runtime validation-lookup bug** (fixed **2025.04**) | Interim: **inactivate the bad cost-center property and create a replacement**; long-term: upgrade to 2025.04 | 26-01098185 |
| Missing app / can't see QCA after user-ID change | Permissions need reprovisioning; browser cache | QCloud **delete & reprovision** permissions; user clears browser history; verify email address | 24-00963015, 24-00954681 |
| User can't access MyQuorum AFE | Two active accounts with `SEC_AUTH_MODE_CD = 4` after Okta name change | Resolve duplicate security accounts | 22-00566301 |
| Reports show pre-upgrade data | User querying the **old (pre-upgrade) database** in QQM | Point user at the upgraded DB | 25-01047050 (Training) |

**Fix recipe (the upgrade checklist):**
1. **Desks → AD/Okta:** confirm every AFE desk is re-pointed to the new account; create **approval limits** for admins (24-00955766).
2. **Username conversion:** run the **QCloud 1.0→1.5 username script** across `QARCH_WF%` and security tables (25-01020756) — symptom is "Workflow does not exist" / null DeskId.
3. **Desk codes:** set up desk codes for any acquired/legacy entities (25-01025959).
4. **Stale validations:** disable `GLAFE [UPS] → ValidatePropBusUnit` if save/reclass/open fails post-upgrade (§16); refresh **Web cache** (Cache Maintenance screen, 25-01027359) for line-category/UI staleness.
5. **Data:** verify bad V16 data wasn't carried into V17 (re-apply V16 fix scripts — 24-00995408).

---

## 9. Cluster F — Working Interest doubling / WI ≠ DOI

**≈6 actionable cases (EQT, Surge, Spur, Jonah).** The **Property Working Interest** on the AFE Cost Center tab is **higher than DOI** — often literally **doubled** (e.g. 1.5% vs 0.75%, or >1).

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| `AFE_SYNCDOI` ("Sync JIB DOI Decimal to QCA AFE") sets `AFE_DOI_DEC` > 1 | For AFEs with **multiple affiliates + cost centers on different internal BAs**, the sync inflated WI | **AFE_SYNCDOI corrected** so total WI ≤ 1 for multi-affiliate/CC AFEs; validated in EQCU_HD_DEV17 | 24-00960960 / ADO **#1647957, #1732977** |
| "Value 1.5 is invalid for Property Working Interest" though NRI is .75 | **Cartesian product** — a JOIN in the registered SQL doesn't date-filter `GONL_PROP_EFF_DT` time-slices, so two records combine to 1.5 | Fixed **2024.04**; non-GA client got a **registered-SQL workaround** to date-filter the join | 25-01032201 |
| WI differs Header vs Cost Center tab / vs QDO; "doubling" when using CC vs DOI filter | Same WI-sync/display family | **Patch #12 / hotfix** (e.g. 2020.09) deployed; or registered-SQL update | 24-00940492, 24-00964715, 24-00994917 / ADO **#1704522, #1710486** |
| Prop WI ≠ DOI NRI for an unknown number of AFEs | Identify scope | Provided **list of AFEs with out-of-sync WI/NRI** for cleanup | 24-00955179 |
| Multiple Operator BAs cause WI mismatch | Query/join logic over multiple BAs | Registered-SQL / build fix | 25-01032201, ADO **#1457883** (RLY — Prop WI not populating with CC filter) |

**Fix recipe:** when WI > NRI or > 1, the cause is the **DOI→AFE sync** mishandling **multiple affiliates/cost centers/BAs** or an **un-dated time-slice join** producing a Cartesian product (25-01032201). For GA clients confirm the build is **2024.04+** (or the relevant hotfix/Patch #12 for older streams, 24-00964715). For non-GA clients the **interim is a registered-SQL change** to date-filter `GONL_PROP_EFF_DT` in the offending JOIN. To scope cleanup, run the diagnostic in §16 to list all AFEs with `AFE_DOI_DEC` not matching DOI.

> **Verify upstream first:** if a single AFE's WI is wrong, confirm the **DOI setup** is actually correct before assuming the sync bug — several "wrong WI" cases were correct DOI mis-pick by the user (re-pick from the Cost Center pick-list fixed it, 24-00955179).

---

## 10. Cluster G — Document attachment errors

**≈5 actionable cases.** Users can't attach files to an AFE.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| ".PNG file type not supported" / "only lower-case format files are attachable" | The file-extension validation is **case-sensitive** — `.PNG` rejected, `.png` accepted | Workaround: **rename extension to lower-case**; code fix makes the validation **case-insensitive** | 25-01041181, 25-01041741 |
| Attaching a document is **very slow / times out** | On each attach the code **loops all existing DD documents** to dedupe; large DD volume = slow | Workaround: **move AFE documents to a separate DD folder**; long-term perf WI logged | 22-00811001 |
| Unable to view/attach PDFs on AFE | DD file location / service-account perms | QCloud **copied files to the path the app expects** (23-00905932); added **service account to NTFS perms** (22-00854777) | 22-00571477, 23-00905932, 22-00854777 |

**Fix recipe:** for "file type not supported," check the **case of the extension** (`.PNG` vs `.png`) — rename as the immediate fix (25-01041181); the case-insensitive code fix is the permanent one (25-01041741). For slow attaches, **segregate AFE documents into their own DD folder** to shrink the dedupe loop (22-00811001). For "can't view," it's usually **DD file-path or NTFS service-account permissions** (23-00905932, 22-00854777).

---

## 11. Cluster H — Security / access / personas / web down

**≈12 actionable cases.** "Can't get to my AFEs" — access, persona, or service problems.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| AFE Web shows **No Personas** so approver can't reach AFEs | Missing required **Modules in SC010: User Assignment** | Assign the missing modules in SC010 | 25-01047488 |
| "Doesn't have rights to Save/Update AFE" though assigned AFE roles | Security group/permissions were **removed before a cutoff date** (visible in Audit) | **Revert** the removed group/permissions (e.g. group 2200 AFE ADMIN) per Audit table | 24-00969338 |
| Can't add budget when AFE is Open | Missing object | Add object **`AFE_SPECIAL_UPDATE`** to the user | 23-00935986 |
| Unable to add Supplements to AFE | Missing security group | **Add the security group** | 24-00939810 |
| QCA web **down / 404 / can't access PRD** | App service stopped | **Restart QCA Web / QPECS** (often after a config change) | 22-00628236, 22-00672620, 22-00523350, 24-00941625 |
| Can't access QCA UAT after entity change | Email/User-ID in Classic security (SC100) wrong | Update the User ID's **email in SC100** | 24-00954681 |
| Excel report won't save / VDA | VDA/Windows patch level | Cloud Ops **upgraded VDA + applied MS patch** (KB5043050) | 24-00984314 |

**Fix recipe:** "No Personas / can't see AFEs" → **SC010 Modules** (25-01047488). "Rights error" → check the **Audit table** for recently-removed groups/objects and **revert** (24-00969338); specific powers map to specific objects (`AFE_SPECIAL_UPDATE` to add budget on an Open AFE — 23-00935986). "Web down / 404" → **restart QCA Web / QPECS** (22-00628236, 22-00672620). Many of these are pure ops, not code.

---

## 12. Cluster I — AFE Subledger / account / line-category mapping

**≈8 actionable cases.** AFE subledger wrong, an account won't pull, or line-category fields are blank.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| New GL account's **Line Category Description / Account Name not showing** on the AFE | Account not added to **AFE Line Category** | AFE → Maintenance → **AFE Line Category**: add row with BU + account + description; save | 25-01038651, 26-01064040 |
| AFE Subledger not pulling NET GL entries; account mapping wrong | **Account configuration** on the AFE Type / subledger setup | Account configuration updates | 25-01056003, 23-00913937, 23-00934565 (add accounts to MTS) |
| AP document on AFE Subledger wrong after a **voucher reversal** | Subledger reversal handling | Subledger fix (engineering) | 22-00875026 |
| Duplicate/double subledger entries (incl. intercompany JIB) | Dup rows in AFE_SL | **Script to eliminate dup/double/triple entries** | 22-00808422, 22-00809684 |
| AFE Line Category Summary Assignment screen returns no data | Config/data gap | Config (resolution pattern unclear from mined notes) | 25-01051599 |

**Fix recipe:** "account/line-category not showing on the AFE" → it isn't on the **AFE Line Category** (per BU + account) — add it (25-01038651, 26-01064040). "Subledger not pulling / wrong account" → **account config on the AFE Type** (25-01056003, 23-00913937). Duplicate subledger rows → **dedup script** on AFE_SL (22-00808422, 22-00809684). For "account not budgeted for this AFE," see §17 — it's the **AFE Type → Accounts** list, not a subledger bug.

---

## 13. Cluster J — Route / Desk maintenance & approval limits

**≈7 actionable cases.** Can't configure a route/desk or approval limits behave unexpectedly.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Can't **inactivate an AFE Route** (V17 upgrade) | A validation entry blocks inactivation | **Relax the validation entry** to allow inactivation; or create a new route and inactivate the old one | 25-01043571, 25-01031204 |
| Unable to **delete an assigned desk** in AFE Route Admin (build 16.54) | Older-build defect | **Fixed in V17** — needs build upgrade | 22-00612449 |
| "Approval Limit" step needs an amount even for an author | **AFE author** vs **approver** — only approvers need a limit | Set the user as an **AFE approver** (an author isn't asked for a limit) | 23-00882015 |
| AFE Group-Select Approval Limit error | Step type vs single approver | Set a **$0 approval limit** (or use *Approval Limit by Single Desk* when only one approver); long-term WI logged | 22-00667662 |
| Route Preview shows a different name than the desk's assigned user | Duplicate/ambiguous desk names | Workaround: **rename desks to unique names**; "View Route" display bug fixed in latest version | 22-00523380, 25-01008530 |

**Fix recipe:** "can't inactivate a route" → **relax the blocking validation** or create-new-and-inactivate-old (25-01043571, 25-01031204). Approval-limit errors are usually **step-type vs single-approver** mismatches — switch *Approval Limit by All Desks in Group* → *by Single Desk* when the step has one approver, or set a **$0 limit** (22-00667662; Training analogs 25-01042608, 26-01065496). "Delete assigned desk" needs **V17** (22-00612449).

---

## 14. Cluster K — Reopen / close / cancel AFE status changes

**≈6 actionable cases.** A status change is blocked by validation and needs a script (or a workaround).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Reopen CANCELLED → OPEN | Status validation | **Script to change status** | 24-00988160 |
| Reopen blocked because AFE is **missing DOI/Tier/Property/Internal BA** on the CC tab | Reopen validation requires those fields | Options: **create a new AFE**, or **OOS script** to add the missing values | 24-00985045 |
| Change AFEs to **CLOSED (CLD)** status in bulk | Bulk status update | **Script to set CLD** | 22-00587440 |
| Cancelled AFE blocking JIB from running; needs reopen | Cancelled status blocks downstream | **Script** deployed (DEV/UAT/PRD) | 23-00909307 |
| Supplements need to show as cancelled / no longer needed | Stale supplement + workflow rows | **Script** to update supplement + clear queued workflows | 22-00587546 |

**Fix recipe:** status transitions that the UI won't allow are done by **scoped data script** on `QCTRL_AFE_HDR` (status code) + the fields that status normally populates (open-date on reopen). If a **reopen** is blocked by missing CC-tab data (DOI/Tier/Property/BA), the cleaner option is often a **new AFE** rather than back-filling (24-00985045). Always verify-SELECT and wrap in a transaction. (Many "change CC after Open" requests are *expected behavior* — see §17.)

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1761278 / #1761279** | Bug / Script Review / **Closed** | MAC — QCA — AFEs Stuck in Pending Status / Abort Workflow / WF not appearing | §4 | 26-01092076 family |
| **#1699362 / #1720965 / #1721437** | Bug / **Closed** | RLY — AFEs stuck in Pending status, workflow does not exist (Script Approval) | §4 | 25-01010935, 25-01012284 |
| **#1555429 (#1555741/#1560283/#1569663)** | Bug + Task / **Closed** | QCA web — AFE Inbox — not able to see records in "Pending approval" | §4/§11 | — |
| **#1699780** | Bug / **Closed** | Long Term — ARS — Missing validation for AFE RECLASS | §5 | — |
| **#1814008** | Script Review / **Closed** | CNR — Business Unit 610 AFE reclass will not run | §5 | 26-01104716 |
| **#1757491** | Script Deployment / **Closed** | ARS — Upstream UAT — 25-01041495 — AFERECLASS error | §5 | 25-01041495 |
| **#1789253** | Bug / **Closed** | GEC — 26-01083886 — AFEEXTIMP is Failing | §7 | 26-01083886 |
| **#1775353** | Bug / **Proposed** | AFEEXTIMP — failed when AFE no is long length (e.g. 2670311000) | §7 | — |
| **#1624582 / #1628458 / #1671214** | Requirement / Feature / **Closed** | AFE_IMPORT — Performance in the AFE_IMPVLD step; PQID/SOURCE_LINE_ID | §7 | — |
| **#1647957** | Bug / **Closed** | JNE — Working Interest in AFE screen does not match Working Interest in QDO | §9 | 24-00940492 |
| **#1732977** | Bug / **Closed** | MST — AFE doubling property WI if >1 PROP_EFF_DT record | §9 | 25-01032201 |
| **#1704522 / #1710486** | Bug / Requirement / **Closed** | SGY — AFE Working Interest displayed at Header vs Cost Center tab differ (24-00994917) | §9 | 24-00994917 |
| **#1457883** | Bug / **Closed** | RLY — AFE Cost Center — Property WI not populating with Cost Center filter | §9 | — |
| **#1575278** | Bug / **Closed** | V2UI — QCA Web — AFE Creation/Approval — Cost Centers tab — Override WI | §9/§17 | — |
| **#1647988** | Bug / **Proposed** | AFE Creation/Approval — incorrect message for Operator working interest | §9/§17 | — |

> Many actionable AFE cases were dispositioned **operationally** (status-reset / dedup / username-conversion / restage script, or config) with no single product WI: AFE-stuck-in-Pending status scripts (26-01092076, 26-01088131, 25-01032800), QCloud username conversion (25-01020756), `ValidatePropBusUnit` disable (25-01006922/017092/026683), AFEEXTIMP Event-Detector add (26-01083886/088281), `.PNG` case-insensitive fix (25-01041741), AFE_SYNCDOI WI fix (24-00960960). Confirm exact build/patch in `Quorum.Upstream.QCA.ReleaseNotes` when stating fix availability.

---

## 16. Diagnostic SQL

> **Caveat:** QCA Upstream runs on **SQL Server** (note `GETDATE()`, `dbo.` schema, `[UPS]` app layer). Per-client DBs exist (`<CLIENT>.Upstream.Database`). **Verify table/column names against the client DB before scripting**, and always run a verify-SELECT before any UPDATE/DELETE, wrapped in a transaction.

```sql
-- A. AFE header status + key fields (§4 stuck-in-Pending; §14 status changes)
SELECT AFE_NO, BUS_UNIT_CD, OPER_BUS_SEG_CD, AFE_STAT_CD, AFE_DESC, OPEN_DT, UPDT_DT
FROM   dbo.QCTRL_AFE_HDR
WHERE  AFE_NO = '<AFE_NO>' AND BUS_UNIT_CD = '<BU>';
-- AFE_STAT_CD stuck at 'PEN' after full approval = the §4 signature.

-- B. AFEs not in a valid posting status (Training pre-close check, 25-01062722)
DECLARE @StartAcctgMonth date = '2025-12-01';
SELECT s.BUS_UNIT_CD, s.OPER_BUS_SEG_CD, s.PROP_NO, s.AFE_NO, s.ACCTG_MTH,
       h.AFE_STAT_CD,
       CASE WHEN v.AFE_STAT_CD IS NULL THEN 1 ELSE 0 END AS WillFail_NotListedForPosting
FROM   dbo.JBTRN_CORE_INTFC_EXP s
LEFT JOIN dbo.QCTRL_AFE_HDR h
       ON h.AFE_NO = s.AFE_NO AND h.OPER_BUS_SEG_CD = s.OPER_BUS_SEG_CD AND h.BUS_UNIT_CD = s.BUS_UNIT_CD
LEFT JOIN dbo.QXREF_AFE_VALID_POST_STATUS v
       ON v.AFE_STAT_CD = h.AFE_STAT_CD
WHERE  s.ACCTG_MTH >= @StartAcctgMonth AND s.AFE_NO IS NOT NULL
ORDER BY s.AFE_NO, s.ACCTG_MTH;

-- C. Working Interest > 1 on AFE cost centers (§9 AFE_SYNCDOI doubling). Verify column names per client.
SELECT AFE_NO, BUS_UNIT_CD, PROP_NO, TIER, DO_TYPE, INTERNAL_BA_NO, AFE_DOI_DEC
FROM   dbo.QCTRL_AFE_DETAIL          -- or the AFE cost-center/detail table in the client schema
WHERE  AFE_DOI_DEC > 1
ORDER BY AFE_NO;

-- D. Duplicate AFE detail rows (the AK_QCTRL_AFE_DETAIL unique-key collision, §7)
SELECT AFE_NO, BUS_UNIT_CD, <key cols>, COUNT(*) dup_ct
FROM   dbo.QCTRL_AFE_DETAIL
GROUP BY AFE_NO, BUS_UNIT_CD, <key cols>
HAVING COUNT(*) > 1;

-- E. Disable the ValidatePropBusUnit validation object (§5/§8 Permian-upgrade unblock; from 25-01026683)
--    ENABLED_IND = 0 disables it. Insert if the row doesn't exist, else UPDATE ENABLED_IND=0.
SELECT OBJECT_USE_NM, USE_SEGMENT, APP_LAYER_CD, ENABLED_IND, OBJECT_DEF_NM
FROM   QARCH_CTRL_OBJECT_USE
WHERE  OBJECT_DEF_NM = 'ValidatePropBusUnit';
-- INSERT INTO QARCH_CTRL_OBJECT_USE (OBJECT_USE_NM, USE_SEGMENT, APP_LAYER_CD, ENABLED_IND,
--   OBJECT_DEF_NM, OBJECT_USE_DESCR, USER_ID, UPDT_DT)
-- SELECT 'ValidatePropBusUnit','Validation','QCEN',0,'ValidatePropBusUnit',NULL,'<USER>',GETDATE();

-- F. WORKFLOW global-config URL keys (§6 email links). Key Group = WORKFLOW, Env-Specific layer.
SELECT KEY_GROUP, KEY_NM, KEY_VALUE
FROM   <global config table>          -- Maintenance > Configuration Settings > Global
WHERE  KEY_GROUP = 'WORKFLOW'
  AND  KEY_NM IN ('AFEAPPROVAL_INBOX_URL','QCA_INBOX_URL','AFEAPPROVAL_INBOX_ITEM_URL','QCA_INBOX_ITEM_URL');

-- G. Pending email notifications not yet sent (§6). Run QEMAIL (QP063) to flush.
SELECT * FROM QARCH_EVENT_NOTICE_EMAIL WHERE EMAIL_SENT_IND = 'N' ORDER BY CREATE_DT DESC;

-- H. Duplicate AFE supplements with same date/time (blocks AFE Web load, 25-00995777)
SELECT AFE_NO, SUPLMT_DT, COUNT(*) ct
FROM   <supplement table>
GROUP BY AFE_NO, SUPLMT_DT
HAVING COUNT(*) > 1;
-- Resolution kept only the latest SUPLMT_SEQ_NO per (AFE_NO, SUPLMT_DT).

-- I. Workflow rows for an AFE (§4 orphaned WF; §8 username conversion)
SELECT * FROM QARCH_WF_INSTANCE  WHERE OBJECT_KEY LIKE '%<AFE_NO>%';   -- table names vary by version
-- Old QCloud 1.0 usernames in QARCH_WF% / security tables must be converted to 1.5 format.
```

---

## 17. Expected-Behavior / User-Education FAQ

~110 Training + ~78 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "**Account not budgeted for this AFE**" / "account NNNN-NNNN is not budgeted" error in a GL/AP batch | The account isn't on the **AFE Type → Accounts** list — add it on the AFE Type screen, Accounts section | 26-01098090, 25-01020090 |
| "New account's **Line Category / Account Name not showing** on the AFE" | Add the account to **AFE → Maintenance → AFE Line Category** (BU + account + description) | 26-01064040, 26-01081766 |
| "Need to **change the Cost Center** on an AFE" / "wrong AFE Type selected" | If the AFE is **Open with transactions booked**, you **cannot** simply swap — add the new CC, **reclass costs via manual JE**, inactivate the old CC; or close & create a new AFE | 25-01033094, 25-01035914, 25-01023608, 26-01103294 |
| "Do I need a **supplement**? Multiple supplement records are showing" | Only **one supplement** can be in EST/REJ/PEN at a time; **update the rejected supplement** rather than creating a new one. Multiple records are *expected* for **affiliate AFEs** across BUs | 26-01091430, 25-01028228 |
| "**Mandatory if Over ($)** step skipped / asks the wrong approver" | Step-type config — use **Approval Limit by All Desks in Group** / **by Single Desk** correctly; the route defaults to the **lowest Lookup Sequence Number** | 26-01065496, 26-01097560, 25-01043103, 25-01042608 |
| "Can't create a **NON-OP AFE** — purchaser/operator not in the list" | The Business Associate is missing the **Operator BA Type usage** (BA → Addresses → Usages → add Operator) | 25-01050349 |
| "How do I **reassign AFEs** from an out-of-office user's inbox?" | **Desk Maintenance → Delegation Desks** (or Desk Delegation Admin) — add the delegate desk with eff dates | 25-01038752 |
| "How do I add **multiple cost centers** to an AFE?" | Supported — configure CCs in **CC010**, then use the green **+** on the AFE Cost Center tab | 25-01054779 |
| "Override **Operator AFE** field — what do I enter?" | Free-text/`N/A` is acceptable; the **Override Working Interest** checkbox is gated by the `AFEEditWiPct` security object | 26-01085272, 26-01098185 |
| "BO/QQM **AFE01 report** gives different results with same criteria" | One user is on the **pre-upgrade DB** in QQM — point them to the upgraded DB | 25-01047050 |
| "**Web line-category description** looks wrong/stale" | Refresh via the **Cache Maintenance** screen | 25-01027359 |
| "How do I make a **non-bill / G&A AFE**?" | Use an account **without a JIB Group Code** in GL013, or set the AFE Type **DOI rule = Not Allowed** so it ties to CCs without required Properties/DOIs | 25-01038542, 23-00916505 |
| "Property WI on the AFE doesn't match — is it a bug?" | Often a **user mis-pick** — re-select WI from the Cost Center **pick-list**; only treat as the §9 sync bug if it's >1 or spans multiple affiliates/BAs | 24-00955179 |

**Tell-tale it's user/expected:** an "account not budgeted" error (AFE Type config), a "can't change CC/AFE Type after Open" request (transactions already booked — reclass, don't swap), a supplement question on an affiliate AFE (multiple rows are normal), a "mandatory-if-over" surprise (step-type config), a report discrepancy (pre-upgrade DB), or a WI that's a user pick-list mistake. **Verify AFE-Type/account/line-category config and DOI before treating it as a defect.**

---

## 18. Key Code, Processes & Repos

### Processes / batch steps
| Process | Purpose | Notes |
|---|---|---|
| **AFE Approval Workflow** | Route AFE EST→PEN→Open via desks/approval-limits | `HandleFinalApproval` timeout → stuck PEN (§4); `AFE_FNLAPR`/`AFE_ONLNEM` events |
| **AFERECLASS** (AFE Reclass / WIP→NET) | Reclass WIP to net working interest → AFE subledger | DOI/Tier/DO_TYPE/account/BU keyed; clean AFE_SL + retry (§5); ADO #1699780 |
| **AFEEXTIMP** | Import AFEs from **Execute** via SFTP + Event Detector | Needs `AFE_EXTIMP` Event Detector **with a user** + QPECS restart (§7) |
| **AFE_IMPORT / AFE_HDRUPL** | Bulk AFE header/detail upload | `AFE_IMPVLD` validation step; `AK_QCTRL_AFE_DETAIL` unique key; Fast Calc `AFE_CALC` `==` (§7) |
| **AFE_SYNCDOI** | "Sync JIB DOI Decimal to QCA AFE" — pull WI from DOI onto AFE | WI-doubling bug for multi-affiliate/CC AFEs (§9) |
| **QEMAIL (QP063)** | Send queued notification emails | Run to flush `QARCH_EVENT_NOTICE_EMAIL` (§6) |

### Key tables
`QCTRL_AFE_HDR` (header/status), `QCTRL_AFE_DETAIL` (detail/budget; `AK_QCTRL_AFE_DETAIL` unique key), `QTRAN_AFE_SL` / AFE_SL (subledger), `QARCH_CTRL_OBJECT_USE` (validation objects incl. `ValidatePropBusUnit`), `QARCH_EVENT_NOTICE_EMAIL` (email queue), `QARCH_WF%` (workflow instances/usernames), `QXREF_AFE_VALID_POST_STATUS` (valid posting statuses), `JBTRN_CORE_INTFC_EXP` (JIB interface), `GONL_PROP_EFF_DT` (property eff-date time-slices — Cartesian source, §9).

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `QSQL_QcaAFESyncDOI.cpp` (AFE_SYNCDOI) | `Quorum.Upstream.QCA.ClassicBatch /QPDllCostAcctgAFE/` | §9 |
| `ValidatePropBusUnit` object use (`GLAFE [UPS]`, layer `QCEN`) | `QARCH_CTRL_OBJECT_USE` / `*.Upstream.Metadata /STANDARD 16.0/QARCH_CTRL_OBJECT_USE*.json` | §5/§8 |
| AFERECLASS process/step metadata | `*.Upstream.Metadata /STANDARD 16.0/QARCH_CTRL_PROC_PROCSTEP.json`, `QARCH_CTRL_PROCESS_STEP.json` | §5 |

### Repos (Quorum Upstream QCA)
- **`Quorum.Upstream.QCA.Web`** / **`.Application.Web`** / **`.Application.MiddleTier`** / **`.Application.APIHost`** — AFE Web UI (AFE Maintenance, Inbox, Route screens), Personas/security.
- **`Quorum.Upstream.QCA.ClassicGUI`** — Classic GLAFE / maintenance screens (SC010/SC100, Event Detector, Global Config).
- **`Quorum.Upstream.QCA.ClassicBatch`** — C++ batch (`QPDllCostAcctgAFE`: AFE_SYNCDOI, reclass, import).
- **`Quorum.Upstream.QCA.Batch`** — managed batch.
- **`Quorum.Upstream.QCA.Database`** / **`Quorum.Upstream.QCA.Metadata`** (per-product) and **`Quorum.Upstream.Database`** / **`.ESuite.Database`** — schema, procs, object-use & process-step metadata.
- **`Quorum.Upstream.Application.QPEC`** — QPECS process/event service (restart after Event-Detector/notification changes).
- **`Quorum.Upstream.QCA.Events`** / **`.DocumentManagement.EventHandlers`** — notification events, DD attachments.
- **`Quorum.Upstream.QCA.ReleaseNotes`** — confirm fix build/patch here.
- **`<CLIENT>.Upstream.QCA.ClassicBatch` / `.Database` / `.Metadata`** (e.g. `MEW.Upstream.QCA.ClassicBatch`, `MAC.Upstream.Database`) — **client overrides; always check the client repo/DB first** (many fixes are client-specific scripts/metadata).

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- The **final-approval handler / workflow** leaves AFEs stuck in PEN from a timeout/abort code path (24-00960832 `HandleFinalApproval`; 25-01018400 `AFE_ONLNEM` event filtering) — provide AFE_NO + BU + the exact action and timing. ADO #1761278, #1699362.
- **AFE_SYNCDOI doubles WI** for multi-affiliate/CC AFEs, or a **Cartesian join** over `GONL_PROP_EFF_DT` inflates WI (24-00960960, 25-01032201) — confirm build vs 2024.04. ADO #1647957, #1732977.
- **AFEEXTIMP** fails on long AFE numbers (#1775353) or **AFE_IMPORT** loops/SPEs (24-00957017) — provide PQID + file.
- A **validation fires at runtime though SQL is correct** (26-01098185, fixed 2025.04) — provide the validation code (`AFEMaint…`) + the record.
- **Document attachment** validation is case-sensitive / DD-dedupe perf (25-01041741, 22-00811001).
- Provide: **AFE_NO + BUS_UNIT_CD + OPER_BUS_SEG_CD**, the process + PQID, exact error text, client + build, and a repro. Confirm fix availability in `Quorum.Upstream.QCA.ReleaseNotes`.

**Handle as Configuration / Cloud Ops when:**
- **Notification** breakage — `WORKFLOW` global-config URL keys, Event Detector + user, email password, run QEMAIL/QP063 (26-01079663, 24-00946620, 25-01049046, 24-00952566).
- **AFEEXTIMP** missing **Event Detector + user** → add it, restart QPECS (26-01083886, 26-01088281).
- **Upgrade fallout** — re-point desks to AD/Okta, **username-conversion script** for `QARCH_WF%`, desk-code setup, approval limits, **disable `ValidatePropBusUnit`**, refresh Web cache (24-00955766, 25-01020756, 25-01006922).
- **AFE-Type / account / line-category** config — "account not budgeted," missing line category, subledger account mapping (26-01098090, 25-01038651, 25-01056003).
- **Security** — SC010 Modules/Personas, security groups/objects (`AFE_SPECIAL_UPDATE`), revert audited removals (25-01047488, 24-00969338, 23-00935986).
- **Service** — restart QCA Web / QPECS for "down/404"; VDA/Windows patches (22-00628236, 24-00941625, 24-00984314).

**Handle with a scoped data script (verify-SELECT + transaction):**
- **Status resets** for stuck/reopen/close/cancel AFEs on `QCTRL_AFE_HDR` (§4, §14).
- **Dedup** AFE detail / supplement / subledger rows (`AK_QCTRL_AFE_DETAIL`, dup supplements, double/triple AFE_SL — 25-00995777, 22-00808422).
- **Restage** records that didn't reach AFE_SL after import/reclass (22-00853225, 22-00583822).
- **DOI KEY / Tier-DO_TYPE** cleanup before retrying AFERECLASS (25-01046200) — reverse GL batches first.

**Handle as Training / Expected behavior (no fix):** see §17 — "account not budgeted" (AFE Type), can't-change-CC-after-Open (reclass via JE), supplement/affiliate questions, mandatory-if-over step-type config, pre-upgrade-DB report discrepancies, and WI pick-list mistakes. **Verify AFE-Type/account/line-category config and DOI before treating it as a defect.**

---

*Skill created: 2026-06-14.*
*Based on: 1,094 closed QCA AFE SF cases — 145 actionable (Software Defect 71 + Application Configuration 71 + ChangeConfig 3) mined for fix recipes, plus ~35 Training/Customer-Error cases for the FAQ. ADO work items #1761278/#1761279, #1699362/#1720965/#1721437, #1555429, #1699780, #1814008, #1757491, #1789253, #1775353, #1624582/#1628458/#1671214, #1647957, #1732977, #1704522/#1710486, #1457883, #1575278, #1647988.*
*Companion (planned): SKILL_QCA_JIB.md, SKILL_QCA_DOI.md, SKILL_QCA_GL_AP.md.*
