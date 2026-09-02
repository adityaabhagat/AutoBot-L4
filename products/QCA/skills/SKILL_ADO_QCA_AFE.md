# SKILL: QCA / AFE Defect & Fix Reference (from ADO)

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** Quorum Upstream — **QCA** (Cost Accounting) / **AFE** (Authorization for Expenditure)
**Source:** Azure DevOps Bugs under Area Path `QuorumSoftware\Engineering\Financials` (+ sub-areas: Committed Backlog, Maintenance and Overhead, Customer Service, Performance), `WorkItemType = Bug`, `State IN (Closed, Resolved)`, title containing AFE / "Authorization for Expenditure" / "cost center" / "capital".
**Use When:** an AFE / cost-center / AFE-import / AFE-report / AFE-workflow issue comes in and you need to know (a) is this a known defect, (b) what was the root cause, (c) which PR/build fixed it, (d) is there a config/data workaround, or (e) is it By Design. ADO-flavored companion to the SF-based Upstream skills.

> **Evidence base:** WIQL returned **329** Closed/Resolved Financials bugs matching the AFE/cost-center/capital filter. **62** were deep-read (description + repro + relations/PRs + dev comments) spanning every cluster below. Reason split of the 329: **Ready-for-QA 171, Rejected 98, Verified 17, Validation-Test-Passed 13, Duplicate 11, Acceptance 10, Split 6, Ready-for-Review 3** — i.e. ~**201 have a real code fix**, ~**98 are By Design / not-reproducible / duplicate**. Every root-cause/fix claim below cites a real ADO bug ID and (where present) PR number, iteration, and linked SF case observed during mining.
>
> **CRITICAL caveat on "fixed-in-build":** the `Microsoft.VSTS.Build.IntegrationBuild` field is **empty on all 329 bugs**. Fix-version below is therefore inferred from the **IterationPath** (e.g. `…\Product Development\23.05` ⇒ the 2023.04/2023.05 dev cycle) and **release tags** (e.g. `2022.10 GA QA`, `MAR 2022.04`, `Robot RN 2026.04`, `Release Note Reviewed`). **Always confirm the actual shipped build** from the linked PR's target branch / `Quorum.Upstream.*` release notes before telling a client "it's fixed in X." Iteration "23.xx" = 2023 dev sprints, "24.xx" = 2024, "25.xx" = 2025, etc. (sprint number, not the marketing release).

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts & Code Map](#2-concepts--code-map)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — AFE workflow status / approve-reject / orphan inbox](#4-cluster-a)
5. [Cluster B — AFE Inbox / Full Inbox display & history](#5-cluster-b)
6. [Cluster C — Cost center: validation, picklist, coding population](#6-cluster-c)
7. [Cluster D — AFE Import / External Import / batch processes (QP053)](#7-cluster-d)
8. [Cluster E — AFE reports (Exago / AFE019 / AFE020 / drilldown)](#8-cluster-e)
9. [Cluster F — Budget / WI / DOI / Affiliate / Supplement calculations](#9-cluster-f)
10. [Cluster G — AFE Type / AFE numbering / attribute save](#10-cluster-g)
11. [Cluster H — Notifications / final-approve email (QFC)](#11-cluster-h)
12. [Cluster I — V2UI / Kendo / Bulk AFE Header UI remediation](#12-cluster-i)
13. [Cluster J — Performance (validation, search, dashboard)](#13-cluster-j)
14. [Cluster K — QDO cost-center maintenance (ORGCOSTGEN) — area overlap](#14-cluster-k)
15. [Fix-Version Matrix](#15-fix-version-matrix)
16. [Diagnostic pointers (SQL & trace)](#16-diagnostic-pointers)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cluster / cause | First check |
|---|---|---|
| AFE approved but **status stays PENDING**, not OPEN | §A — async-refresh (By Design) **or** a status-change validation blocking PENDING→OPEN during WF completion (#1583340) | Did it eventually flip after a minute? If never: confirm build has #1583340 fix |
| Approve/Reject leaves **orphan inbox**; widgets/inboxes load 0 records | §A — orphan WF inbox row when send-for-comment/route-return to same desk then reject (#1555429); or null WF instance in header (#1710580) | Run the orphan-inbox SQL in §16; confirm build ≥ 2022.10 GA |
| "**Workflow … no longer available or does not exist**" on approve | §A — desk Notice Delivery = "Email & Widget" (only EMAIL supported) (#1552303) | Set desk Notice Delivery = Email; confirm `QARCH_WF_CODE_DELIVERY_TYPE` cleanup |
| **Duplicate REJECT rows** in History / Rejected tab | §B — #1571201 (real, still open-ish) vs #1447155 (user tied to multiple desks = expected) | Is the user tied to >1 desk? then likely expected |
| **AFE Reclass / AFERECLASS** process fails "Conversion failed converting varchar to int" | §D — alphanumeric BUS_UNIT_CD into integer-typed proc (#1624997/#262185) | Is the BU code varchar (e.g. R0001)? confirm fix #1624997 (iter 23.20) |
| **AFEEXTIMP / AFE External Import** fails / re-import not inserting | §D — re-run delete-without-reinsert (#1372042); or **event-detector setup** missing (#1655235/#1651193 = config, not code) | Is it a notification/email CE step? then setup, not a bug |
| **Cost center** add throws SQL error (`SELECT IDBEOWNER FROM ACCOUNT…`) on AR076/AP055 | §C — #1718881 (fixed `QCFSJECodeTypeUtility.cs`, iter 25.06) | Confirm build; also affected AP055 |
| **Cost center coding not populating** Internal BA/Tier/DOI | §F — JIB deck with multiple INT_TYPE_SEQ_NO (#1640913) | Workaround: manually pick Internal BA; fix iter 25.26 (2026.04) |
| AFE / report **budget = N× actual** (doubled/tripled) with multiple cost centers | §E — cartesian in report view (#249042 fixed; #1624042 not-repro) | Review `VW_AFE_DETAIL_REPORT` / `AFE_DRILL_DOWN` SQL for CC join |
| AFE **Search by Cost Center slow** (40+ s) | §J — #1566911 (Seneca, SF 22-00868517), PR 114500 | Confirm perf build (Robot RN 2026.04) |
| AP055 **Validate** runs hours on huge non-op voucher | §J — per-row `XREF_COSTCNTR_ACCTATTRIB` / `QXREF_AFE_VALID_POST_STATUS` query (#1721402) | Caching fix iter 25.08; also break up the batch |
| **AFE Type save** SQL/FK error | §G — bulk-edit FK on `FK_QCODE_AFE_RULE` (#57257/58); or metadata/code build skew (#66440) | Consume latest QCA packages |
| AFE **final-approve email** missing data / wrong inbox URL | §H — `QAFEFinalApproveEmailData.cs` (#227150 url; #1560451 budget data) | Confirm event AFE_FNLAPR (100109); QEMAIL not-sending is separate infra |
| V2UI / Kendo screen: action buttons dead, alignment, dirty-mode | §I — UI remediation cluster (route to UX team) | Tag V2UI / V2UI QCA; mostly cosmetic |
| QDO **Cost Center Maintenance** "ORGCOSTGEN process failed" | §K — process-launch service contract (#1704488/#1705774) | iter 25.02; metadata script + move launch to Web tier |

---

## 2. Concepts & Code Map

- **AFE** = Authorization for Expenditure (capital project authorization in QCA). **Primary AFE** vs **Affiliate AFE** (auto-created for non-operated / other-BU owners). **Supplement** = a budget increase to an existing AFE. **Project AFE** rolls up **Related AFEs**.
- **Cost Center (CC)** = the coding dimension on an AFE/voucher tying budget to a property/org. CC picklists, hierarchy, and CC→account XREFs are recurring problem areas.
- **DOI / Tier** = Division-of-Interest deck + tier driving owner interest; **INT_TYPE_SEQ_NO** = interest sequence (multiple sequences for one internal owner is a known edge case).
- **Workflow (WF)** = submit → route/desk → approve / reject / final-reject; managed by **QFC** (Quorum Foundation Classes) workflow engine. Inbox rows live in `QARCH_WF_TRAN_INBOX_BASE` + `QWF_TRAN_INBOX_AFE`; header WF state in `QCTRL_AFE_HDR`.
- **Screens / processes:** AFE Creation/Approval, AFE Full Inbox, AFE Monitor/Maintenance, AFE Subledger, AFE Search Widget, Bulk AFE Header (V2UI). Classic process launcher = **QP053** (QCA) / **QP073** (QCFS); batch processes **AFEEXTIMP** (external import), **AFERECLASS**, **COMMITCOST**, **AFE_AFLSUP** (affiliate supplement split), **POSTWKFL**, **ORGCOSTGEN** (QDO cost-center org gen).
- **Key tables:** `QCTRL_AFE_HDR`, `QCTRL_AFE_DETAIL`, `QCTRL_AFE_SUPLMT`, `QCODE_AFE_LINE_CTGY`, `QCODE_AFE_RULE`, `QXREF_AFE_AFFILIATES`, `QXREF_AFE_VALID_POST_STATUS`, `XREF_COSTCNTR_ACCTATTRIB`, `QSTAG_AFE_DETAIL_IMP`, `QARCH_WF_*`, `QARCH_EVENT*`.
- **Repos (confirmed via PR links):** `Quorum.Upstream.QCA.Web` (QCA web + events: `Quorum.QCA.Events/Detectors/QAFEFinalApproveEmailData.cs`, `QAFEWFContextInfo.cs`), `Quorum.Upstream.QCA.Application.MiddleTier` (`QCAServiceCore`, `QCAServiceClient`, `QUIControllerAFEFullInbox`, `QUIControllerAFETypeSetup`), QCFS web (`Quorum.QCFS.BS\Base\QCFSJECodeTypeUtility.cs`), `Quorum.QFC.Database` / QFC metadata (workflow code tables), client report repos (`<CLIENT>.UPSTREAM.Reports\QCA\AFE`). PR IDs in this skill are ADO PullRequestIds in the QuorumSoftware project.

---

## 3. Decision Tree

```
QCA / AFE issue
│
├─ A WORKFLOW ACTION misbehaves (approve/reject/route/submit)?
│   ├─ Status not flipping to OPEN              → §A  (#1583340 validation; or async-refresh = expected #1414437/#1439453)
│   ├─ Orphan inbox / widgets show 0 / "WF does not exist" → §A  (#1555429 orphan; #1710580 null instance; #1552303 Email&Widget desk)
│   └─ Duplicate reject/history rows            → §B  (#1571201 real; #1447155 multi-desk = expected)
│
├─ INBOX / FULL INBOX display?                  → §B  (grid refresh #1373226; checkbox-needed #1387645; not-repro #195849)
│
├─ COST CENTER?
│   ├─ Add CC throws SQL error (AR076/AP055)    → §C  (#1718881)
│   ├─ CC coding (BA/Tier/DOI) not populating   → §F  (#1640913 multi INT_TYPE_SEQ_NO)
│   ├─ CC picklist wrong / not filtering        → §C  (#99223 wrong picklist; #1687630/#1722406 = By Design no BU validation)
│   └─ CC validation / search slow              → §J  (#1721402, #1566911)
│
├─ IMPORT / BATCH PROCESS fails (QP053)?
│   ├─ AFERECLASS "varchar→int"                 → §D  (#1624997 / #262185 — alphanumeric BU)
│   ├─ AFEEXTIMP re-import not inserting         → §D  (#1372042)
│   ├─ Import "fails" on notification step       → §D  (#1655235/#1651193 = event-detector SETUP, not code)
│   └─ POSTWKFL QXREF_AFE_VALID_POST_STATUS err  → §D  (#1445857 — missing sysgens on wrong metadata layer)
│
├─ REPORT amounts wrong (Exago / AFE019/020 / drilldown)?  → §E  (cartesian per cost center / unsummed line categories)
│
├─ CALC wrong (budget/WI/DOI/affiliate/supplement)?        → §F
│
├─ SAVE error on AFE Type / numbering / attribute?         → §G
│
├─ Email notification missing/wrong?                        → §H  (QFC event data; or infra/event-detector = not software)
│
├─ V2UI / Kendo cosmetic / dead control?                    → §I  (route to UX)
│
└─ QDO Cost Center Maintenance ORGCOSTGEN error?            → §K
```

---

## 4. Cluster A
### AFE workflow status / approve-reject / orphan inbox

The single richest real-defect cluster. Three distinct root causes plus an "expected behavior" trap.

| Bug | Symptom | Root cause | Fix | Iter / release | Workaround | SF |
|---|---|---|---|---|---|---|
| **#1583340** | After approval, AFE status stays `PEN`, WF status not "Approved" | New status-change validation `AFEMaint000670.cs` (added by #1574879) blocked PENDING→OPEN **even when completing the workflow** | Skip that validation for the WF-completion case (PENDING→OPEN / FINAL REJECTED). PRs **81821, 81823** | 23.05 (2023.04 regression) | — | — |
| **#1555429** | Reject/final-reject leaves an **orphan inbox**; inbox widgets then load 0 records | Route-return / send-for-comment **to your own desk** creates a 2nd inbox; on reject the send-for-comment inbox isn't closed → orphan row in `QARCH_WF_TRAN_INBOX_BASE` with `INBOX_STATUS_CD <> 'SYSTEMCOMPLETE'` while header WF fields are cleared → inbox load fails | (1) on reject, close the send-for-comment inbox + create rejection inboxes; (2) **validation blocking route-return/delegate/send-for-comment to the same desk**. PRs **76467, 76464, 76458**; required QFC platform fix #1557815 / #1569254 | 23.01 (2022.10 GA) | Manual cleanup SQL (see §16) | — |
| **#1710580** | AFE Inbox / Full Inbox + widget show **0 records** though eligible AFEs exist | An AFE with **two WF instances** (one final-rejected/cleared, one still `QUEUE`) leaves a **null instance ID in `QCTRL_AFE_HDR`**, so `GetMultipleAfesForInbox` throws `Filter Name 'RouteSimpleStep.Rou…'` | PR **107996** | 25.05 | Clean up the dangling QUEUE instance | — |
| **#1552303** | "Workflow: Instance ID '…' is no longer available or does not exist" on approve (AFE + Voucher) | Approval desk **Notice Delivery = "Email & Widget"**; only **EMAIL** is supported. Invalid values reappeared in QFC core table `QARCH_WF_CODE_DELIVERY_TYPE` | QFC core DB cleanup of `QARCH_WF_CODE_DELIVERY_TYPE` + FK `QARCH_WF_DESK`; remove invalid values from QFC metadata. PRs **75714, 75952** | 22.23 (2022.10 GA) | **Set the approval desk's Notice Delivery to "Email"** | — |
| **#130936** | "Workflow does not exist" approving a brand-new AFE+WF | WF lookup in `QWFManager` (QCA MT) | Fixed (Maint Sprint 65, "QA Complete") | — | — | CCI |
| **#1564569** | Can't **resubmit** AFE after Open→Cancel→Estimate | Intentional — system does not support resubmit after cancel | **By Design / Rejected** (UserVoice idea raised) | — | — | 22-00866245 (BRM) |
| **#1414437 / #1439453** | Status doesn't refresh to OPEN immediately after approve | WF actions are **asynchronous**; UI refreshed before backend committed | **By Design / Rejected** — not reproducible consistently; status flips after a short delay | — | wait / Retrieve again | — (SRCU) |
| **#1439683** | Can delete an attachment after AFE submitted to WF | Attachments were never locked by WF status | **By Design / Rejected** | — | — | — |

**Fix recipe:** capture (a) the AFE_NO + BU, (b) the WF route/desk, (c) the exact action sequence, (d) the desk's **Notice Delivery type**. If "WF does not exist" → check Notice Delivery = Email (#1552303). If widgets/inbox show 0 → run the orphan-inbox SQL (§16) and look for an orphan/null WF instance (#1555429 / #1710580). If status just lags → it's the async refresh (expected). Confirm the build carries #1583340 before treating a stuck PENDING→OPEN as new.

---

## 5. Cluster B
### AFE Inbox / Full Inbox display & history

| Bug | Symptom | Root cause / disposition | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#1571201** | History tab shows **duplicate REJECT rows** (AP & AFE) | Real — duplicate REJECT history logged on reject (confirmed reproducible, "still an issue in 2025.04") | **Recommend Open** (Duplicate-resolved against related items) — confirm latest build | — | 22-00866963 (SRC) |
| **#1447155** | Duplicate rows in Rejected tab on reject/resubmit | Only reproduces when **user is tied to multiple desks** (grid omits DESK_NM); not repro in core | **By Design / Rejected** | — | — (GLE) |
| **#1373226** | Rejected grid data appears only after **Refresh** | Grid refresh timing | Fixed | 21.16 | — |
| **#1387645** | Approve icon "not clickable" with a pending record | **Not a bug** — you must **check the row checkbox** in the Full Inbox grid first | **By Design** (test-script clarity) | — | — |
| **#195849** | After approve, Pending grid doesn't auto-repopulate | Intermittent grid refresh; dev couldn't reproduce | **Closed not-reproducible** | 20.11 | — |
| **#66189** | AfeFullInbox issues multiple read ops on load | Redundant grid reads | Fixed (perf) | — | — |

**Tell-tale it's expected:** duplicate inbox/rejected rows when the user is on **multiple desks**; an approve icon that "won't click" until a grid row is checked.

---

## 6. Cluster C
### Cost center: validation, picklist, coding population

| Bug | Symptom | Root cause | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#1718881** | AR076 (and AP055) **error adding a cost center**: `CommandText: SELECT IDBEOWNER FROM ACCOUNT WHERE ID=…` | Error tripped in `QCFSJECodeTypeUtility.cs → AddAccountsToIdAccountToIdBeOwner` (QCFS.Web BS) on add of account/code-block attributes | PRs **108552, 108553** | 25.06 | — |
| **#99223** | AFE Search widget Cost Center field uses **wrong picklist** | Picklist ID **49058** shared by two different picklists on different layers; AFE Attribute (QCA) should be a unique ID | Fixed (PR 8492) | Maint Spr 55 | — |
| **#67608** | Can't query by cost center "JBPROP" on Search widget | CC query handling | Fixed | — | — |
| **#1687630** | AP055 cost-center picklist **doesn't filter by Business Unit** | **By Design** — no validation prevents a CC on a different BU; BU only validated when property/DOI is filled | **Rejected** | 25.11 | — |
| **#1722406** | AR086 invoice CC/Prop column blank in GL distribution | **By Design** — controlled by GL105 + Group Definition | **Rejected** | — | — |
| **#111630** | Notify user when CC on AFE header updated via SAP interface | Enhancement (notification) | Customer Service | — | — |
| **#1583750** | Approval blocked "Cost Center JBPROP is inactive" even though AFE uses a **different** CC | Move-to-next-AFE logic loaded the wrong AFE/inbox after submit | PRs **81923, 81927** | 23.05 (2023.04 regression) | — |
| **#1688464** | CC code not addable by manual typing; console error | Transient build regression — resolved by latest artifacts (no single root-cause PR) | resolved via latest artifacts | 24.20 | — |

**Fix recipe:** "error adding cost center" on AR076/AP055 = #1718881 (confirm build ≥ iter 25.06). A CC picklist that "won't filter by BU" is **expected** (#1687630). A blank GL-distribution Prop/CC column is **GL105/Group-Definition config** (#1722406), not a bug.

---

## 7. Cluster D
### AFE Import / External Import / batch processes (QP053)

| Bug | Symptom | Root cause | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#1624997** | **AFERECLASS** process fails with DB errors when BU code is varchar (e.g. R0001) | Proc assumes **integer `BUS_UNIT_CD`** (`m_QcaAFE_INS_PeriodDetailsForClosing`); "Conversion failed when converting varchar value to data type int" | PR **89952** (column work) | 23.20 | — |
| **#262185** | Same "varchar→int" error on QP053 AFE Reclass | Duplicate of the above; some code paths expect integer BUS_UNIT_CD | **Duplicate** of #1584608 | — | — |
| **#1372042** | **AFEEXTIMP** fails updating existing AFEs — `QCTRL_AFE_DETAIL` deleted but **not re-inserted**; "No records were inserted into QCTRL_AFE_HDR or QCTRL_AFE_SUPLMT" | Re-import delete-without-reinsert when there's no supplement change | Multiple PRs **60632, 67797, 67798, 68377, 68378, 69430, 72351** | 21.21 | — |
| **#1655235** | QP053 AFE External Import "fails" | **Setup, not code** — process CE's on the **notification step**; missing/inactive **event detector `AFE_EXTIMP`**; validation errors in the XML file ("Invalid cost center; property must have a DOI") | No code fix — fix test/setup; valid element class `QcaAFEXmlImportHeader.cs` | 24.06 | — |
| **#1651193** | AFE Import / Update process fails | **Setup, not code** — CE on notification step; event detector `AFE_UPDEML` not active | No code fix — activate event detector | — | — |
| **#1445857** | QCFS **POSTWKFL** (QP073) completes with errors re `QXREF_AFE_VALID_POST_STATUS` | Missing **sysgens** defined on the wrong **ENGS metadata layer** instead of the UPS/QCFS layer | Move 9 items from ENGS layer → UPS/QCFS layer; update DB snapshot. PRs **67465/67466, 68046/68047** | 22.06 | — |
| **#1318976** | ERF AFE Detail Spreadsheet Upload (QP053) times out on ~6000 rows | Not reproducible; suspected env blocking; possible missing index on `QSTAG_AFE_DETAIL_IMP (PROCESS_QUEUE_ID, ID)` | **Rejected** — never reliably reproduced | — | — (ERF) |
| **#96477** | AFE Committed Cost Import rejects whole file on bad rows | Enhancement — allow valid rows to import | Customer Service | — | — |
| **#1408868** | APHU primary/affiliate supplement error with line categories | `AFE_AFLSUP` process fails when supplement has a line category on the **primary BU not set up on the affiliate BU** | **Rejected / Recommend Close** (setup-driven) | — | — (APHU) |

**Fix recipe:** for "import/process failed," first **read the batch log for the failing step**. If it dies on the **notification/email step**, it's almost always a **missing/inactive event detector** (`AFE_EXTIMP`, `AFE_UPDEML`, `AFE_FNLAPR`) — a setup fix, not a defect (#1655235, #1651193). A "varchar→int" conversion = alphanumeric BUS_UNIT_CD hitting an integer-typed proc (#1624997). AFEEXTIMP re-run losing detail rows = #1372042.

---

## 8. Cluster E
### AFE reports (Exago / AFE019 / AFE020 / drilldown)

The recurring report defect is **amounts multiplied by the number of cost centers** (a cartesian in the report view) or **line categories not summed**.

| Bug | Symptom | Root cause | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#249042** | Exago "AFE Budget to Actuals" gross/net **don't match the screen** for an AFE with **2 cost centers** | `AFE_DRILL_DOWN` view duplicated gross/net per cost center; CC_COUNT in the group-by | Modified GRS/NET BUDGET & ACT calc; removed `CCS.CC_COUNT` from group-by, added `HDR.AFE_DOI_DEC`. PR **42717** | 21.01 | — |
| **#1624042** | SGY "AFE Budget vs Actual Expenditures Summary" **triples** budget & actuals | Suspected cartesian in `VW_AFE_DETAIL_REPORT` (core report `AFE020`) | **Rejected** — not reproducible after ~2 yrs; close | — | — (SGY) |
| **#1364847** | TPW **AFE020 / AFE019** Equip/Tie amount shows only the **first line category**, not the sum | Report not summing multiple line-category codes with the same dates | Fixed (client TPW report `…\TPW.UPSTREAM.Reports\QCA\AFE`) | 21.14 | — (TPW) |
| **#197060** | Web QCA Project AFE budget **excludes Related-AFE budgets** | Project rollup not including related AFE amounts | `Quorum.Upstream.QCA.Web` 17.18.1 / MiddleTier 17.19.1. PRs **31714, 31810, 32289, 32342** | 20.10 (2020.03) | — |
| **#249067 / #256812 / #1355061 / #1355076 / #1452425 / #1323635 / #1324531** | Exago AFE report formatting / drilldown / "No Data Qualified" / title issues | Report formatting / view drilldown | Fixed (various Exago) | 21.01 / 21.xx | — |
| **#139137 / #177217 / #1097508** | Cover Sheet Report params not prepopulating / frowny-face | Report parameter linking | Fixed | 20.xx | — |

**Fix recipe:** when AFE report amounts ≠ the AFE Creation/Approval screen and the AFE has **multiple cost centers (or line categories)**, suspect a **cartesian / unsummed join in the report view** (`AFE_DRILL_DOWN`, `VW_AFE_DETAIL_REPORT`, core `AFE020`). Get the launch parameters from `QARCH_QUEU_PROCESS`. If the report is a **client override** (TPW/SGY etc.), the fix is in `<CLIENT>.UPSTREAM.Reports\QCA\AFE`.

---

## 9. Cluster F
### Budget / WI / DOI / Affiliate / Supplement calculations

| Bug | Symptom | Root cause | Fix / disposition | Iter | SF |
|---|---|---|---|---|---|
| **#1640913** | New AFE: cost-center coding (Internal BA, Tier, DOI Dec) **not auto-populating** for some CCs | The JIB deck has **multiple `INT_TYPE_SEQ_NO`** for the internal owner → coding not auto-filled, save error "A property is required…" | Auto-populate DOI info (pick one sequence) when multiple INT_TYPE_SEQ_NO. PR **121305** | 25.26 (target 2026.04, Recommend Open) | **Manually select Internal BA No** to populate | — (SGY) |
| **#1378490** | AFE **WI decimal** doesn't sum to full interest for an internal owner with **multiple owner sequences** | AFE picks one sequence's interest instead of summing | **Backlog / deprioritized** (suspected long-standing) | — | — |
| **#197060** | Project AFE budget excludes Related-AFE budgets | (see §E) | Fixed | 20.10 | — |
| **#1386819** | Affiliate **close date** not updating when only the primary's close date changes | Incomplete dev from #140241 — sync only fired on status/open-date change | PRs **58818, 59016** | 21.19 (2021.10) | also change status/open date | — |
| **#105371** | Tier change on primary **doesn't sync down** to affiliate | Intentional — affiliates are defaults; non-overlapping ownership across tiers would break JIB if forced | **By Design / Rejected** | — | — (ATR) |
| **#1453098** | Expired-owner affiliates (Eff-To in past) still created | Intentional — affiliate creation **does not look at Eff-To date**; user deletes unneeded affiliates | **By Design / Rejected** (enhancement) | — | — (RLY) |
| **#57231** | Rounding error fires `AFEMaint000590` incorrectly for non-round WI | Insufficient detail | **Rejected** (no repro) | — | — |

**Fix recipe:** "coding won't populate / save says property required" on a CC = **multiple INT_TYPE_SEQ_NO** on the deck (#1640913); workaround = manually pick the Internal BA. Affiliate sync gaps are mostly **By Design** (#105371, #1453098) — only the **close-date sync** (#1386819) was a real fix.

---

## 10. Cluster G
### AFE Type / AFE numbering / attribute save

| Bug | Symptom | Root cause | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#57257** | AFE Type grid **bulk-edit** lets you save garbage in "Allow DOI Rule" → `FK_QCODE_AFE_RULE` FK violation on save | Bulk-edit didn't validate the DOI rule field (inline add did) | Validate in `QCAServiceClient.UpdateMultipleAfeTypeSetup`. PRs 1394/1396/1398/3556/3557 | — | — |
| **#57258** | AFE Type Accounts grid save throws raw SQL "Failed to enable constraints" when columns blank | Missing not-null/FK handling on the screen | Fixed with #57257 | — | — |
| **#66440** | AFE Type screen "Save failed due to an error" | **Build skew** — metadata validations shipped without the matching code | Consume latest QCA packages (Shared + QCA web) | — | — |
| **#222213** | New AFE Type not on AFE Creation/Approval after cache refresh | Cache/metadata | Fixed | — | — |
| **#139119** | New AFE Type not available after cache refresh | Cache | Fixed | — | — |
| **#100647** | Can't save AFE with **sequence-digit config = 0** ("Error occurred generating AFE Smart Number") | Manual AFE numbering with `AFE_SEQ_DIGITS=0` not handled | Fixed (PR 8046, Maint Spr 54) | — | — (PRC) |
| **#57230** | Year prepended to auto AFE number though `AFE_SEQ_PREPEND_YEAR=0` | Config not honored | **Rejected** (proposed) | — | — |
| **#102445** | AFE checkbox attribute (e.g. soft-close) **not written to DB** if left unchecked | Checkbox control wrote nothing when not toggled | Force new checkbox records to 0 and persist on save | Maint Spr 55 | — |
| **#57005** | Copy AFE carries over **Selected Route**, ignoring Route Mappings on submit | `WfRouteNmSelected` not nulled on copy (`GetCloneForAfe`) | Fixed under #1537632 | — | 190334 |
| **#62161** | Attachments copied on AFE copy even when "Include Attachments" unchecked | Pre-save artifact | **Rejected** — not an issue in v17 (cleared on save) | — | — |

**Fix recipe:** AFE Type save SQL/FK errors = the bulk-edit validation gap (#57257/#57258) or **metadata/code build skew** (#66440 → consume latest QCA packages). Numbering save errors trace to `AFE_SEQ_DIGITS` / `AFE_SEQ_PREPEND_YEAR` config handling.

---

## 11. Cluster H
### Notifications / final-approve email (QFC)

| Bug | Symptom | Root cause | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#227150** | AFE Final-Approve email has **invalid inbox URL** | `QAFEFinalApproveEmailData.cs` needed the same INBOX_URL resolution chain (WF_USAGE_CD/MODULE_CD/global) as #227136 | PRs **34946, 34966, 34969, 34972** (event 100109) | 20.18 (2020.09) | — |
| **#1560451** | AFE Final-Approval notification **missing budget data** | Budget fields not mapped to the AFE_FNLAPR event context (`AfeHeader.TotalGrossBudget/TotalNetBudget` in `QAFEFinalApproveEmailData.cs` / `QAFEWFContextInfo.cs`) | PR **123634** (Recommend Open) | 26.04 | open SF case (SRC) |
| **#1784351** | (split from #1560451) QEMAIL **not generating** the email | Duplicate/redundant email-address setup in `QARCH_EVENT_NOTICE_EMAIL_QUEUE`; SMTP — **data/infra** | Separate ticket; setup/infra | — | — |
| **#178212** | No email after Final Approve | **Infra, not software** — event detector not Active + CORE_TST email server | **Rejected** — activate event detector / fix SMTP | 20.06 | — |
| **#212271 / #217235** | QFC final-approve email body blank / dead link / missing logo | Email template/formatting | Fixed (Classic QFC) | — | — |

**Fix recipe:** missing **content** in the email → QFC event-data mapping (`QAFEFinalApproveEmailData.cs`, event `AFE_FNLAPR` / 100109). Email **not arriving at all** → check the **event detector is Active** and the **QEMAIL/SMTP** setup (`QARCH_EVENT_NOTICE_QUEUE` / `QARCH_EVENT_NOTICE_EMAIL_QUEUE`) — that's setup/infra, not a code defect (#178212, #1784351).

---

## 12. Cluster I
### V2UI / Kendo / Bulk AFE Header UI remediation

A very large but mostly **cosmetic/interaction** cluster from the V2UI migration, the Kendo grid upgrade, and the new **Bulk AFE Header** screen. ~50+ bugs (e.g. #1568974, #1572192-1572203, #1570337-1570480, #1574238-1575273, #1601266/1601273, #1711725-1711752, #1584296/1584304). Representative:

| Bug | Symptom | Disposition |
|---|---|---|
| **#1568974** | V2UI AFE Creation/Approval INBOX tab — action button (3 dots) does nothing | Fixed after multiple rounds (PRs 78835/79298/79299/79471/79521); flagged as **V2UI** → routed to UX team; reparented under V2UI remediation #1391237 | 23.02 |
| **#1572192–1572203** | V2UI Full Inbox: actions enabled with no selection, filter data cut, double scrollbars | Fixed (V2UI QCA) | — |
| **#1574238–1575273** | Bulk AFE Header: pagination missing, scrollbars, notes formatting, group-by, delete dialog, lock-by-other-user | Fixed (Bulk AFE Header rollout) | — |
| **#1711725–1711752** | Kendo upgrade: header alignment, dimmed fields, history rows wrongly "edited", border cut | Fixed (Kendo upgrade) | — |

**Disposition note:** if a screen issue is present in **V2UI but not V1UI**, it is tagged `V2UI` / `V2UI QCA` / `V2UI UPS` and worked by the **UX team**, not core QCA dev. Most are alignment/dirty-mode/console-error polish — low functional risk. When triaging a client report, confirm whether they're on V1UI or V2UI before matching.

---

## 13. Cluster J
### Performance (validation, search, dashboard)

| Bug | Symptom | Root cause | Fix | Iter | SF |
|---|---|---|---|---|---|
| **#1721402** | AP055 **Validate** on a 420k-line non-op JIBLink voucher runs **4+ hrs** | `SELECT 1 FROM XREF_COSTCNTR_ACCTATTRIB` issued **per row** (70k+ times); also `QXREF_AFE_VALID_POST_STATUS` re-queried per AFE row | **Cache** the account/cost-center XREF + AFE-valid-post-status lookups. PRs **109328, 109334, 109404, 109438**; checked into 2023.04, 2024.10, Develop | 25.08 | — (MIT) |
| **#1566911** | AFE Search by **Cost Center** takes 40+ s | Search query perf on CC | PR **114500** | 25.15 (Robot RN 2026.04, Recommend Open) | 22-00868517 (Seneca/SRC) |
| **#108425** | QCA AFE processing slow in QCLOUD PROD | Optimization recommendation | Customer Service | — | — |
| **#1725894 / #1725889 / #1645818 / #1757514 / #1734942** | Dashboard / View-AFE-Full-Inbox / AP-AFE degradation in load tests (2024.04 / 2025.04) | Load-test regressions | **Rejected** — closed off latest perf-test rounds (no fix needed) | 24.09 / — | — |

**Fix recipe:** AP055 validate hangs on huge non-op vouchers = the per-row XREF query (#1721402) — confirm the caching fix is in the client build **and** advise breaking very large (100k+ line) JIB batches up. AFE-search-by-CC slowness = #1566911. The dashboard load-test bugs were **closed without a fix** after re-testing — don't quote them to clients as defects.

---

## 14. Cluster K
### QDO Cost Center Maintenance (ORGCOSTGEN) — area overlap

These are **QDO** (Division Order) bugs that surfaced via the "cost center" filter — noted for completeness; route to the QDO skill if you have one.

| Bug | Symptom | Root cause | Fix | Iter |
|---|---|---|---|---|
| **#1704488** | QDO (Web) Cost Center Maintenance save → "Upstream Process **ORGCOSTGEN** failed" (CC still created) | ESuite launched ORGCOSTGEN via `IQGlobalProcessLauncherService` for module QRA, but the service contract was removed from MT in a profile/module change → endpoint not found | Move the process-launch logic to the **Web tier** (`QUIControllerCostCenterMaintenance` → QDO MT via broker) | 25.02 |
| **#1705774** | Classic QDO (CC010) Cost Center Maintenance update → same ORGCOSTGEN error | Metadata for the process on the `ESUITE_QFC` catalog | Metadata script + PR **105401** | 25.02 |

---

## 15. Fix-Version Matrix

> Iteration ⇒ approximate release; **always verify the shipped build from the PR target branch / release notes** (IntegrationBuild was blank on every bug).

| Bug | Cluster | Symptom (short) | State / Reason | PR(s) | Iter ⇒ ~release | SF |
|---|---|---|---|---|---|---|
| #1583340 | A | Status stuck PENDING after approval | Closed / fixed | 81821, 81823 | 23.05 ⇒ 2023.04 | — |
| #1555429 | A | Orphan inbox on reject (same desk) | Closed / fixed | 76467, 76464, 76458 | 23.01 ⇒ 2022.10 GA | — |
| #1710580 | A | Inbox shows 0 records (null WF instance) | Closed / fixed | 107996 | 25.05 | — |
| #1552303 | A | "WF does not exist" (Email&Widget desk) | Closed / fixed | 75714, 75952 | 22.23 ⇒ 2022.10 GA | — |
| #1564569 | A | Resubmit after cancel | Rejected / **By Design** | — | — | 22-00866245 |
| #1414437 | A | Status async-refresh | Rejected / not-repro | — | — | — |
| #1571201 | B | Duplicate REJECT history | Closed / **Recommend Open** | — | — | 22-00866963 |
| #1447155 | B | Duplicate rejected rows (multi-desk) | Rejected / **By Design** | — | — | — |
| #1373226 | B | Rejected grid needs Refresh | Closed / fixed | — | 21.16 | — |
| #1718881 | C | AR076/AP055 add-CC SQL error | Closed / fixed | 108552, 108553 | 25.06 | — |
| #99223 | C | Search CC wrong picklist (49058) | Closed / fixed | 8492 | Maint Spr 55 | — |
| #1583750 | C | "CC JBPROP inactive" on approve | Closed / fixed | 81923, 81927 | 23.05 ⇒ 2023.04 | — |
| #1687630 | C | AP055 CC picklist not filtering by BU | Rejected / **By Design** | — | 25.11 | — |
| #1722406 | C | AR086 Prop/CC column blank | Rejected / **By Design** | — | — | — |
| #1624997 | D | AFERECLASS varchar→int | Closed / fixed | 89952 | 23.20 | — |
| #262185 | D | AFE Reclass varchar BU error | **Duplicate** (#1584608) | — | — | — |
| #1372042 | D | AFEEXTIMP re-import no insert | Closed / fixed | 60632, 67797/8, 68377/8, 69430, 72351 | 21.21 | — |
| #1655235 | D | AFE External Import "fails" | Closed / **setup** (event detector) | — | 24.06 | — |
| #1651193 | D | AFE Import/Update "fails" | Closed / **setup** (event detector) | — | — | — |
| #1445857 | D | POSTWKFL QXREF_AFE_VALID_POST_STATUS | Closed / fixed | 67465/6, 68046/7 | 22.06 ⇒ 2022.04 | — |
| #1318976 | D | AFE Detail Spreadsheet Upload timeout | Rejected / not-repro | — | — | — (ERF) |
| #249042 | E | Exago Budget-to-Actuals × CC mismatch | Closed / fixed | 42717 | 21.01 | — |
| #1624042 | E | SGY report tripling amounts | Rejected / not-repro | — | — | — (SGY) |
| #1364847 | E | TPW AFE019/020 unsummed line cat | Closed / fixed | — (client report) | 21.14 | — (TPW) |
| #197060 | E/F | Project AFE excludes Related budgets | Closed / fixed | 31714, 31810, 32289, 32342 | 20.10 ⇒ 2020.03 | — |
| #1640913 | F | CC coding not populating (multi seq) | Closed / fixed | 121305 | 25.26 ⇒ ~2026.04 | — (SGY) |
| #1378490 | F | AFE WI decimal not summing sequences | Closed / backlog | — | — | — |
| #1386819 | F | Affiliate close date not syncing | Closed / fixed | 58818, 59016 | 21.19 ⇒ 2021.10 | — |
| #105371 | F | Primary→affiliate tier sync | Rejected / **By Design** | — | — | — (ATR) |
| #1453098 | F | Expired-owner affiliates created | Rejected / **By Design** | — | — | — (RLY) |
| #57257/#57258 | G | AFE Type bulk-edit FK errors | Closed / fixed | 1394/1396/1398/3556/3557 | — | — |
| #66440 | G | AFE Type save (build skew) | Closed / consume packages | — | — | — |
| #100647 | G | AFE seq-digits=0 save error | Verified / fixed | 8046 | Maint Spr 54 | — (PRC) |
| #102445 | G | Checkbox attribute not saved | Verified / fixed | 8745 | Maint Spr 55 | — |
| #57005 | G | Copy AFE carries route | Closed / fixed (#1537632) | — | — | 190334 |
| #227150 | H | Final-approve email bad inbox URL | Closed / fixed | 34946, 34966, 34969, 34972 | 20.18 ⇒ 2020.09 | — |
| #1560451 | H | Final-approval email missing budget | Closed / **Recommend Open** | 123634 | 26.04 | open SF (SRC) |
| #178212 | H | No final-approve email | Rejected / **infra** | — | 20.06 | — |
| #1568974 | I | V2UI INBOX tab action dead | Closed / fixed (UX) | 78835, 79298/9, 79471, 79521 | 23.02 | — |
| #1721402 | J | AP055 validate 4+ hrs (per-row XREF) | Closed / fixed; in 2023.04/2024.10/Develop | 109328/334/404/438 | 25.08 | — (MIT) |
| #1566911 | J | AFE Search by CC 40+ s | Acceptance / fixed | 114500 | 25.15 ⇒ ~2026.04 | 22-00868517 |
| #1725894/#1725889/#1645818 | J | Dashboard load-test degradation | Rejected / no fix | — | 24.09 / — | — |
| #1704488 | K | QDO ORGCOSTGEN (Web) | Acceptance / fixed | 104409, 104597 | 25.02 | — |
| #1705774 | K | QDO ORGCOSTGEN (Classic) | Acceptance / fixed | 105401 | 25.02 | — |

---

## 16. Diagnostic pointers

> **Caveat:** Upstream is SQL Server; databases are per-module/per-client (e.g. `CORE_TST161UPS_QCA`). Table names below come from repro text and dev comments — verify against the client DB and always run a verify-SELECT before any UPDATE/DELETE, in a transaction.

```sql
-- A. Orphan AFE workflow inbox (the #1555429 signature: header WF cleared but inbox left open)
SELECT B.AFE_NO, A.*
FROM   QARCH_WF_TRAN_INBOX_BASE A
JOIN   QWF_TRAN_INBOX_AFE       B ON A.ID_WF_INBOX = B.ID_WF_INBOX
JOIN   QCTRL_AFE_HDR            C ON B.AFE_NO = C.AFE_NO AND B.BUS_UNIT_CD = C.BUS_UNIT_CD
WHERE  C.AFE_STAT_CD LIKE 'FREJ%'
AND    A.INBOX_STATUS_CD <> 'SYSTEMCOMPLETE';
-- Manual cleanup (per #1555429): UPDATE QARCH_WF_TRAN_INBOX_BASE SET INBOX_STATUS_CD='SYSTEMCOMPLETE' WHERE ... (scope to the orphan ID)

-- B. AFE with >1 WF instance / null instance in header (the #1710580 "0 records" signature)
SELECT WF_INSTANCE_ID, WF_ROUTE_NM_SELECTED, WF_ROUTE_NM_OVERRIDE, AFE_NO, AFE_STAT_CD
FROM   QCTRL_AFE_HDR WHERE AFE_NO IN ('<AFE_NO>');   -- look for null WF_INSTANCE_ID with a lingering QUEUE instance

-- C. Invalid desk Notice Delivery values (the #1552303 "WF does not exist" signature)
SELECT * FROM QARCH_WF_CODE_DELIVERY_TYPE;           -- should be EMAIL only; Widget / Email&Widget are invalid
-- Then check the approval desk's delivery type in QARCH_WF_DESK.

-- D. Alphanumeric Business Unit feeding an integer-typed proc (the #1624997/#262185 reclass error)
SELECT BUS_UNIT_CD FROM <BU/company table> WHERE BUS_UNIT_CD NOT LIKE '%[^0-9]%' ;  -- find non-numeric BU codes (e.g. R0001)

-- E. AFE report cartesian by cost center (the #249042/#1624042 doubling/tripling)
--    Compare report view output vs the Budget tab; the view is the suspect.
--    Core report = AFE020 / view AFE_DRILL_DOWN / VW_AFE_DETAIL_REPORT (client override may exist).
SELECT COUNT(*) cc_count FROM QCTRL_AFE_DETAIL WHERE AFE_NO='<AFE>' GROUP BY AFE_NO; -- N CCs ⇒ amounts may be ×N

-- F. AFE detail not re-inserted on AFEEXTIMP re-run (the #1372042 signature)
SELECT COUNT(*) FROM QCTRL_AFE_DETAIL WHERE AFE_NO='<AFE>';   -- 0 after a re-import = the bug

-- G. Event detector active? (import/notification "failures" that are really setup — #1655235/#1651193/#178212)
SELECT ACTIVE_IND, EVENT_TYPE_CD FROM QARCH_EVENT
WHERE  EVENT_TYPE_CD IN ('AFE_EXTIMP','AFE_UPDEML','AFE_FNLAPR');

-- H. Per-row XREF perf (the #1721402 AP055-validate hang) — confirm via trace, then confirm caching build
--    Trace shows: SELECT 1 FROM XREF_COSTCNTR_ACCTATTRIB ... executed thousands of times.
```

**Trace files:** middle-tier traces under `\\<server>\…\Services\Quorum.Upstream.QCA.Application.MiddleTier`. For batch failures, get the **Process Queue ID** from `QARCH_QUEU_PROCESS` and read the batch-process-execution-monitor log for the failing step.

---

## 17. Escalation Guidance

**Route to Engineering (real code defect) when:**
- A workflow action mis-states or orphans an inbox: status validation blocking WF completion (#1583340), orphan inbox (#1555429), null WF instance (#1710580). Provide AFE_NO + BU + route/desk + exact action sequence + desk Notice Delivery type.
- A batch proc fails on **data type / data**: AFERECLASS varchar→int (#1624997), AFEEXTIMP re-import (#1372042), POSTWKFL layer/sysgen (#1445857). Provide the PQID + failing step + exact error.
- A **calculation/report** is provably wrong on correct inputs: report cartesian-by-CC (#249042), unsummed line categories (#1364847), Project-vs-Related budget (#197060), CC coding not populating with multiple sequences (#1640913). Provide the AFE_NO and the screen-vs-report comparison.
- Confirm fix availability from the **linked PR's target branch** and `Quorum.Upstream.*` release notes — do **not** quote IntegrationBuild (blank) or assume the iteration number is the marketing release.

**Handle as Configuration / Setup (not a code bug) when:**
- "Import/process failed" but it dies on the **notification step** → missing/inactive **event detector** (`AFE_EXTIMP`, `AFE_UPDEML`, `AFE_FNLAPR`) (#1655235, #1651193).
- "No email received" → event detector inactive and/or **QEMAIL/SMTP** infra (#178212, #1784351).
- Approve fails "WF does not exist" → set the **desk Notice Delivery to Email** (#1552303).
- AFE Type save "Save failed due to an error" right after an upgrade → **consume the latest QCA packages** (metadata/code skew, #66440).

**Handle as Expected Behavior / By Design (no fix):**
- Status not flipping instantly after approve = **async refresh** (#1414437, #1439453) — it commits shortly.
- Duplicate inbox/rejected rows when the user is on **multiple desks** (#1447155); approve icon "not clickable" until a grid row is **checked** (#1387645).
- CC picklist not filtering by BU (#1687630); blank GL-distribution Prop/CC column controlled by GL105 (#1722406).
- Affiliate **tier** not syncing from primary (#105371); affiliates created for **expired-Eff-To** owners (#1453098) — user deletes unneeded affiliates; resubmit after cancel not supported (#1564569).
- Deleting attachments after submit (#1439683).

**V2UI / Kendo (route to UX team):** cosmetic alignment, dirty-mode, dead-control, scrollbar, and Bulk-AFE-Header polish present in V2UI but not V1UI (§12). Confirm the client's UI version before matching.

---

*Skill created 2026-06-14. Source: 329 Closed/Resolved ADO Bugs under `QuorumSoftware\Engineering\Financials` matching AFE / cost center / capital; 62 deep-read. Build numbers inferred from IterationPath + release tags (IntegrationBuild empty on all) — verify against PR target branch / Quorum.Upstream.* release notes before quoting to a client. Companion: Upstream QRA/QDO/QCFS ADO skills, REPO_INVENTORY, CONFIG_REFERENCE.*
