# SKILL: QDO Division Orders Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Division Order (QDO) — Upstream Accounting (myQuorum / On Demand). Front-ends the QRA (Quorum Revenue Accounting) division-order engine; integrates downstream to SAP-PRA and QCFS GL.
**Scope:** The Division Order subsystem — **DOI Setup / DOI Worksheet** (decimal-interest build, precision/NRI), **Maintenance Groups** (the transactional container for transfers, pay-code changes, exemption changes), **Interest Transfers & the Combine flag**, **Owner Funds Release / suspense / funds-only transfers**, **PPN (Prior Period Notification) generation** incl. impairment, **DO mailing reports** (DOR003/008/009/015, QP088), **Owner Search**, **Bearer Group / Market (Exemption) Group setup**, and **integration** out to SAP-PRA / QCFS / QRA Middle Tier.
**Boundary:** QDO is the *maintenance & ownership* layer. When the *number* (revenue $, impairment, PPA) is wrong it is usually QRA/revenue/PPA upstream that is the messenger — verify the DOI/Market-Group setup and the upstream revenue process first. Companion areas (separate skills if/when mined): QRA revenue distribution / PPA / impairment engine, QCFS GL, SAP-PRA property/BA interface mechanics.

> **Evidence base:** 1,291 closed QDO/Division_Orders cases. Root-cause split: **Software Defect 216**, Customer Error 173, (blank) 171, Customer Cancelled 141, **Application Configuration 114**, Training 105, Business Change 50, No Action 44, others. This skill mines the **333 actionable** cases (Software Defect 216 + Application Configuration 114 + ChangeConfig 3) for fix recipes, plus ~44 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts & Flow](#2-concepts--flow)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Interest Transfer & the Combine flag](#4-cluster-a--interest-transfer--the-combine-flag)
5. [Cluster B — PPN generation (unexpected PPNs, impairment, staging)](#5-cluster-b--ppn-generation)
6. [Cluster C — Owner Funds Release / suspense / funds not moving](#6-cluster-c--owner-funds-release--suspense--funds-not-moving)
7. [Cluster D — Maintenance Group lifecycle (stuck/locked/won't delete)](#7-cluster-d--maintenance-group-lifecycle)
8. [Cluster E — DOI Setup / DOI Worksheet / decimal precision & NRI](#8-cluster-e--doi-setup--doi-worksheet--decimal-precision--nri)
9. [Cluster F — DO mailing reports (DOR003/008/009/015, QP088)](#9-cluster-f--do-mailing-reports)
10. [Cluster G — Integration: SAP-PRA / QCFS / QRA Middle Tier / BA & Property](#10-cluster-g--integration)
11. [Cluster H — Web upgrade: screen / security-object / access errors](#11-cluster-h--web-upgrade-screen--security--access)
12. [Cluster I — Bearer Group / Market & Exemption Group (MEG) setup](#12-cluster-i--bearer-group--market--exemption-group-setup)
13. [Cluster J — Owner Search screen](#13-cluster-j--owner-search-screen)
14. [Known ADO Items](#14-known-ado-items)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Expected-Behavior / User-Education FAQ](#16-expected-behavior--user-education-faq)
17. [Key Code, Processes, Screens & Repos](#17-key-code-processes-screens--repos)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| "I checked **Combine** but the lines didn't combine" / got split into 2 sequenced lines | Combine validation requires the candidate lines to match **exactly**; a differing **suspense reason / settlement code / interest type / lease tie / MEG** blocks the combine (by design) OR a combine defect | §4 — confirm what differs; several combine defects are fixed (1368887, 1625458, 1644404) |
| Combine erased the **MEG / lease cross-reference / market group** info, or combined different settlement codes | Combine-on-transfer defect that dropped attributes | §4 (22-00634665/667 → ADO 1329807/1358440; 22-00634666) |
| **PPN created when none expected** (owner-exemption / bearer-group / PD41 market-rep PPN on a plain interest transfer) | PPN-staging defect — wrong reason-code query fires; preview vs approval mismatch | §5 — known query/staging defects (24-00952414 PD41/LD43, 24-00973008, 24-00977860); WA = exclude PPNs on PN025 |
| **LD17/LD18 PPN fails** with `302 Impairment - remaining amount is not zero` / `311 Impairment - remaining Total Tax Decimal not zero` | Impairment/remaining-decimal mismatch (often bad Market-Group setup or RDCALCNEW) | §5 — verify Market Group; WA `RUN_RDCALCNEW=disabled` (25-01014688); often customer setup (25-01059135) |
| **OFR did not move the money** / only moved part / left funds under old owner | OFR-not-staging-all-funds defect, or accounting locked the period, or run OFR not yet posted | §6 — confirm MG staged 100% of funds; defects fixed 24-00972858, ADO 1534578/1541765 |
| **Trapped suspense** / funds "held by another release" with no MG | Orphaned funds-release lock | §6 — find & clear the orphan lock (24-00968393); stuck DO129 OFR (ADO 1584263) |
| MG **won't delete** / "partially deleted" / empty MG can't be removed | MG cleanup gap — child rows deleted but header stuck | §7 — cleanup script (24-00977396); fixed Oct-2025 HF (25-01049845) |
| MG **locked** / can't release via DO025 | MG **approved twice** (frontend didn't disable the button under load) | §7 (24-00987497, 25-01020794) |
| MG stuck **"Creating Group"** / "Pending" / **QRA Middle Tier error** on save | Web-engine/QPEC or RabbitMQ/QRA-MT messaging stall (esp. PRD under load) | §7/§10 — restart RabbitMQ + QRA MT QPEC (26-01082277 → ADO 1784413) |
| Removing **errored DOIs** from a MG deletes **all** DOIs/transactions | MG remove-errored-rows defect | §7 (24-00942776, 24-00942776) |
| **DOI Worksheet ignores PRECISION** / NRI saved past 8 decimals → GWI/BG approval fails | Worksheet not rounding to global `PRECISION` config on import/bulk-edit | §8 (25-01012855 → ADO 1727280; 22-00676548; small-decimal loader 1625151/1760270) |
| **DO / Transfer Order form duplicates the owner's interest** (shows twice) | DOR003/QP088 report defect (duplicate interest line) | §9 (22-00512731, 22-00711295, 24-00980159) |
| DO mailing report: NRI **rounds to 8 / last 2 digits "00"**, address missing, exhibit A mismatched | Report-template defect | §9 (23-00892160, 24-00976197 DOR015 Exhibit A, 22-00647279) |
| QP043 export **ran but didn't reach QCFS GL** / out of balance | MT100 config cleared → orphaned staging; or COA missing JE Code Type | §10 (24-00950935 MT100; 23-00915272 COA) |
| BA / Property **integration error from SAP** (filter, timeout, sync stuck "Approved") | BA-list filter, SMICM timeout, or DOI Sync Status not flipping to Completed | §10 (25-01019764, 25-01030423 SMICM, 25-01051115) |
| Web screen "**Not Authorized to access security object**" / Save greyed out after upgrade | Missing security-object grant in the user's security group | §11 — add the object to the group (24-00966898, 23-00933550) |
| **DOI Copy** function missing or erroring in Web | Feature not enabled, hotfix, or env/engine down | §7/§11 (23-00915459, 24-00973279, 25-01059649) |
| **Owner Search** no results / wrong fund total / can't export >1000 lines | Owner Search query/grid defect | §13 (25-01024762, 24-00987231, 25-01004578, 24-00973290) |

---

## 2. Concepts & Flow

```
[Well / Property + Well Completion → DOI Xref]
        │
        ▼  DOI SETUP / DOI WORKSHEET  (build the Division of Interest: owners, decimal interests/NRI, interest types,
        │                              Bearer Groups (GWI), Market Groups / MEGs, suspense/pay codes)  → DOI must be APPROVED
        ▼
   MAINTENANCE GROUP (MG)  — the unit of work. Holds Transactions (interest Transfer, Pay-Code change,
        │                    Exemption change, Funds-only transfer). Create → add transactions → PREVIEW → submit → APPROVE.
        │                    Approval runs COPY_DVDS2 / COPY_DVD_W to commit DOI History + funds.
        ├──► generates PPNs (Prior Period Notifications) where prior-period revenue must be re-distributed/recouped
        ├──► OWNER FUNDS RELEASE (OFR / OFRS)  — moves suspended funds from the "from" owner to the "to" owner
        └──► DOI Sync to SAP-PRA (event per DOI) ; revenue/GL export to QCFS (QP043)
        ▼
   REPORTS (DOR003/008/009/015 via QP088): Division Order / Transfer Order forms for mailing to owners
```

### Key terms (QDO / upstream-accounting vocabulary)
- **DOI** = Division of Interest — the ownership deck on a property/tier: owners (BA # + Sub), **interest type** (WI, RI, ORRI/OR, NRI, etc.), **decimal interest / NRI** to `PRECISION` places. Keyed by `PROP_NO / DO_TYPE_CD (REV/RRV) / DO_MAJ_PROD_CD / TIER / INT_TYPE_CD / INT_TYPE_SEQ_NO / EFF_DT_FROM`. Must be **Approved** to be live.
- **Maintenance Group (MG)** = transactional container. Status flow: *Creating Group → (open) → Submitted for Approval → Approved → Completed*. Approval physically commits via stored procs **COPY_DVDS2 / COPY_DVD_W** (`Quorum.QRA.Process.QPDllDivisionOrder`). Tables: `DONL_DVD_GRP` (header), `DONL_DVD_DO_DETAIL`, `DONL_DVD_DO_HIST`, `DONL_DVD_DO_OWNR_LSE`.
- **Combine flag** = on a transfer, merge the "to" lines into a single sequence **only if all attributes match exactly** (suspense reason, settlement code, interest type, lease tie, MEG). A mismatch correctly prevents the combine (warning) — this is the single most common "is it a bug?" question (§4).
- **Transfer / Pay-Code change / Modify** — transaction types in a MG. **Transfer** moves ownership/NRI; **Pay-Code (PC) change** changes pay status; **Modify** is the best-practice path for a **MEG/market change** (a Transfer for a MEG-only change is the wrong tool — 25-01042027).
- **PPN** = Prior Period Notification. Created when a maintenance action requires re-distributing/recouping prior-period revenue. Reason codes seen: **LD17/LD18** (recoup), **LD43/LD45**, **PD41** (Market Group Rep change). Generating a PPN when nothing relevant changed is a recurring defect (§5).
- **OFR / OFRS** = Owner Funds Release (Service). Moves suspended funds owner→owner on a transfer; writes JE100/JE101 and subledger. Run/posted via QP043 / DO129 / DO130. "Money didn't move" = §6.
- **Bearer Group (BG) / GWI** = the group that bears another owner's costs; **GWI Calc must total 1.0**. Missing BG assignment fails DOI Approval (26-01100831). Config `AUTO_CREATE_BEARER_GROUP` controls auto-creation (25-01008529); `User Maintained Bearer Group` checkbox keeps user-entered BG numbers (25-01059575).
- **Market Group / MEG (Market Exemption Group)** = severance/market exemption grouping. Tract-level market groups need a corresponding Unit-level market group (25-01045698). Bad Market-Group setup → 302 impairment (§5).
- **Impairment / RDCALCNEW** = the revenue-distribution remaining-decimal check. `302 Impairment` = remaining distribution decimal ≠ 0; `311 Impairment` = remaining tax decimal ≠ 0. `RUN_RDCALCNEW` global config toggles the new RD calc engine (WA: disable — 25-01014688).
- **PRECISION** = global config for decimal places (core default 8). DOI Worksheet/grids must round to it (§8).
- **QRA Middle Tier (QRA MT) / QPEC / RabbitMQ** = the messaging layer QDO uses to call SAP-PRA and back. PRD stalls on save = restart these (§10).
- **QCFS / QP043 / MT100** = GL export path. **MT100** screen holds Journal/Trans definitions; it has a known V16-and-older bug that silently clears settings when queried — must be Q-managed (§10).
- **DO screens**: DO005/DO006/DO007 (DOI setup/detail), DO010 (copy), DO025 (MG release), DO034/Workspace (transfer), DO129/DO130 (funds release), DOR0xx (reports). RD010 (reversal decks), CA020 (open CA), PN025 (PPN exclude), VL031/VL100 (revenue/PPA value lines).

---

## 3. Decision Tree

```
QDO / Division Order case
│
├─ A transaction/process FAILED or STALLED?
│   ├─ MG stuck "Creating Group" / "Pending" / "QRA Middle Tier error" on save → §7/§10 (restart QRA MT QPEC + RabbitMQ; web engines up?)
│   ├─ MG won't delete / "partially deleted" / empty MG                          → §7 (cleanup script; fixed Oct-2025 HF)
│   ├─ MG locked / can't release DO025                                           → §7 (approved twice under load)
│   ├─ Workspace/transfer SQL insert error (NULL into GRP_NO, missing sequence)  → §4/§7 (data/seq fix: TRANS_GRP_SEQ_NO 25-01060843)
│   ├─ DOI Sync stuck "Approved" / PK or duplicate-transaction error to SAP      → §10 (SMICM timeout; SAP side; revert+re-approve)
│   └─ QP043 export ran but not in QCFS GL                                        → §10 (MT100 cleared; COA JE Code Type)
│
├─ OUTPUT WRONG but nothing crashed?
│   ├─ Combine didn't combine / split & sequenced                                → §4 (what differs? suspense/settle/int-type/MEG = by design or known defect)
│   ├─ Combine erased MEG / lease-xref / settlement code                          → §4 (combine-on-transfer defect)
│   ├─ PPN created when not expected (exemption/BG/PD41 PPN)                       → §5 (PPN-staging/query defect; WA = exclude on PN025)
│   ├─ OFR didn't move all the funds / left funds on old owner                     → §6 (OFR-not-staging defect; or period locked)
│   ├─ DO/TO form duplicates interest, NRI rounds to 8, address missing            → §9 (report-template defect)
│   └─ DOI Worksheet ignores PRECISION / NRI > 8 decimals                          → §8 (worksheet rounding defect → ADO 1727280)
│
├─ IMPAIRMENT errors (302 / 311) on PPN / process?
│   └─ Verify Market Group / Bearer Group setup FIRST; WA RUN_RDCALCNEW off       → §5 (often customer setup, sometimes defect)
│
├─ Web "Not Authorized to security object" / Save greyed / feature missing post-upgrade? → §11 (grant security object; enable feature)
│
├─ Owner Search no results / wrong totals / >1000 export?                          → §13
│
└─ "How do I…" / setup / "is this a bug?" / cycle-roll / template upload           → §16 Expected-Behavior FAQ
```

---

## 4. Cluster A — Interest Transfer & the Combine flag

**The single largest defect family.** A transfer in a Maintenance Group can optionally **Combine** the resulting "to" lines into one sequence. The engine combines **only when the candidate lines match on every attribute** (suspense reason, settlement code, interest type, lease tie, MEG). Most "combine didn't work" tickets are *by design* (something differs) — but there is also a real cluster of combine **defects**: lines that *should* combine don't, or the combine **drops** attributes.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Combine **erases the Lease Cross-Reference** on transfer | Combine-on-transfer dropped lease tie | Code fix | 22-00634665 / **ADO 1329807** |
| Combine **erases MEG information** after transfer | Combine dropped MEG attributes | Code fix | 22-00634667 / **ADO 1358440** |
| Transfer **combines different settlement codes** (293 transfer) | Combine ignored settlement-code difference | Code fix | 22-00634666 / **ADO 1358439** |
| Transfer **combines owners with different suspense reason codes** during Preview DOI | Combine didn't consider suspense-reason difference | Now blocks combine when suspense reason differs | 24-00972847 |
| Combine checked but interests **split into 2 sequenced lines** instead of combining | Combine match-logic defect (Workspace Maintenance) | Code fix | 25-01012302, 23-00892160-family / **ADO 1625458** |
| **Many-to-many transfer fails *without* the Combine flag** | Transfer engine defect on M:N without combine | Code fix | **ADO 1368887** |
| 100% **Non-WI→Non-WI already on DOI** transfer: "to" owners not combining | Combine path for already-present owner | Code fix + new requirement | 23-00xxxxx / **ADO 1381101, 1569116** |
| **NMA updated incorrectly** when included in an NRI transfer with Combine checked (MRO) | Combine miscomputed Net Mineral Acres | Code fix | **ADO 1644404** |
| DOI Transfer with Combine checked **not combining** at all | Combine flag not honored | Patch (client) | 22-00547095, 22-00669781 (Camino), 22-00547095 (GLE) |
| Combine across **multiple effective-date ranges** even when data identical | Combine blocked across date breaks | Code fix | 22-00704990 |
| Workspace transfer **SQL insert error** `Cannot insert NULL into GRP_NO` (`DONL_DVD_DO_OWNR_LSE`) on MEG/BG change | Missing group-no on owner-lease insert | Data/code fix | 22-00807794 |
| Pay-code change errors: **`TRANS_GRP_SEQ_NO` sequence missing after cutover** | DB sequence dropped during cutover | Qcloud re-created the sequence; Products tracking so it isn't dropped again | 25-01060843 |
| Combining sequences / "combine for same owner" | Combine-sequence behavior | Patch | 22-00711280, 23-00900594 (REV side) |

**Fix recipe:**
1. First decide **by-design vs defect**: ask what differs between the lines the user expected to combine — **suspense reason, settlement code, interest type, lease tie, MEG/market group**. If any differs, the warning is correct (24-00972847) → educate (§16).
2. If the lines are genuinely identical and still won't combine, or the combine **dropped** an attribute (lease xref, MEG, settlement code), it is a **defect** — most are fixed (ADO 1329807, 1358439, 1358440, 1625458, 1368887, 1644404). Confirm the client's build/hotfix carries the fix.
3. Workspace insert errors (`NULL into GRP_NO`, missing `TRANS_GRP_SEQ_NO`) are **data/DDL** — check for null group columns and missing DB sequences post-cutover (22-00807794, 25-01060843).
4. Reproduce in DEV with the exact owners/property; capture the Workspace #, MG #, and the COM/SQL error verbatim.

---

## 5. Cluster B — PPN generation

Two sub-families: **(B1) PPNs created when none should be** (the recurring defect), and **(B2) PPN process *fails* with 302/311 impairment errors** (usually Market-Group setup, sometimes engine).

### B1 — Unexpected PPNs
| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **PD41 (Market Group Rep change) PPNs created** on a transfer/PC with no market-rep change | **Three queries were creating PPNs with reason PD41 instead of LD43** | Queries modified to use correct reason code | 24-00952414 |
| Working-interest transfer created a **bearer-group-change PPN** (recoup unchecked, PPN tab empty at review) | PPN-staging defect | NOV hotfix | 24-00973008 |
| One-to-one transfer + paycode keeps creating an **Owner Exemptions change PPN** (no exemption changed) | PPN-staging defect | Fix | 24-00977860 |
| PC + funds transfer MG **unintentionally generated PPNs** (WI owners) | PPN-staging defect | WA: exclude PPNs on **PN025** (drops them from VL100/CA020), delete the incorrect market groups from **RD010**; long-term fix logged | 25-01029286 / **ADO 1742419** |
| **Preview vs Approval PPN creation mismatch / staging** (broad rework) | Preview and Approval used different PPN-creation paths | Re-architecture: **merge Preview & Approval PPN creation**, move `USPD_DO_RVS_CREATION` | **ADO 1729989, 1764539, 1754316** (DO PPN Staging Logic 20/21/06) |
| **LD18 / LD45 PPN behavior changes** | Reason-code logic | Development requirements | **ADO 1771847 (LD18), 1772635 (LD45)** |
| **DO PPN Notifications** — MG PPN's tab + event-notification batch | Screen/notification gaps | Requirements | **ADO 1565994, 1567320, 1580306** |
| Preview PPN **reversal date** wrong | `m_GetDOsForReversalDVDNew` used wrong date | Date corrected in the query | 25-01004578 |
| Big-Pool / SOD owner PPN issue on original processing | SOD/pool PPN defect | Fix | 23-00886116 |

### B2 — Impairment failures (302 / 311)
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **LD17/LD18 PPNs fail**: `302 Impairment - remaining amount is not zero` / `311 Impairment - remaining Total Tax Decimal not zero` | Remaining distribution/tax decimal ≠ 0 — usually bad Market-Group or RD setup | **WA: set `RUN_RDCALCNEW` global config to disabled**; open RCA case for DB copy | 25-01014688 (→ related 25-01019939) |
| 302 impairments on PPN processing | **Incorrect Market Group setup** | Correct Market Group; submit products 204 & 400 together from VL100 | 25-01059135 (Customer Error) |
| PPA wiped out RRV DOI Details so remaining PPAs failed | Multiple PPAs on same DOI/prod-date; posting one cleared RRV DOI Details | Script the RRV DOI Details back in | 25-01038379 (Customer Error) |

**Fix recipe:**
1. **Unexpected PPN** → identify the PPN **reason code** (PD41/LD43/LD17/LD18/LD45/exemption/BG). If it fired with no corresponding change, it is the B1 defect family (24-00952414, 24-00973008, 24-00977860). **WA to unblock month-close:** exclude the bad PPNs on **PN025**, which removes them from **VL100/CA020**; delete bad market groups from **RD010** (25-01029286). Confirm the build carries the PPN-staging rework (ADO 1729989/1764539/1754316).
2. **302/311 impairment** → this is the *revenue-distribution* check; verify **Market Group** and **Bearer Group** setup first (it is frequently customer setup — 25-01059135). If setup is correct, WA is `RUN_RDCALCNEW=disabled` (25-01014688) and escalate for RCA with a DB copy.
3. Always capture the DOI key (`PROP/DO_TYPE/MAJ_PROD/TIER/INT_TYPE/SEQ`), production dates, MG #, and the exact 30x impairment lines.

---

## 6. Cluster C — Owner Funds Release / suspense / funds not moving

"I approved the transfer but the money didn't move" — the highest-volume *funds* signature. Real defects exist (OFR not staging 100%), but also period-timing, not-yet-posted, and orphaned-lock causes.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **OFRS moved $0** on approved OH transfers; full amount still in suspense on old owner | OFR not staging/moving funds | Fix; meanwhile DO130 manual | 24-00956739 |
| OFR **not moving 100%** — leaves current-month rev or random eff-dates on old owner | MG transfer didn't include all selected funds | **Fixed: MG transfers now transfer all funds selected on the DOI transfer** | 24-00972858 |
| MG **does not stage the funds** that were selected / stages wrong amount (e.g. shows 87,842.12 instead of −117,792.65) | Funds-staging defect | Code fix | 24-00974458, **ADO 1682315 (DAY)** |
| **Funds Release failing** (PRD) | OFR failure | Code fix | **ADO 1534578 (CNXU)** |
| Owner Funds Release **completing with errors** | OFR error path | Code fix | **ADO 1541765 (Ovintiv/ECA)** |
| OFR under **DO129 "stuck"** | Stuck funds-release | Code fix | **ADO 1584263 (GLE, 23-00888898)** |
| **Trapped suspense** "held by another funds release" but no MG / can't find the release # | Orphaned funds-release lock | Identify & clear the orphan lock (script) | 24-00968393 |
| **Funds Release created two JE100 records** | Extra metadata layers (QECA + ECA + QRA) for BKRVNU/OFR | Deleted QECA & ECA metadata layers for Book Revenue and OFR | 24-00982893 |
| DO130 short by a few dollars after preview / money pulls then comes up short | Funds calc/rounding on DO130 | Investigate | 24-00981277 |
| Funds-only release "**Query returned no results**" though suspense shows in subledger | Funds-only transfer path | Investigate | 25-01025564 |
| **Auto-Post OFR** automation | Enhancement | Requirement | **ADO 1536812; 1739649 (SGY AT tests)** |

**Fix recipe:**
1. Confirm the MG actually **staged 100% of the selected funds** (Funds tab vs JE101/subledger). If the MG transfer dropped funds, it is the fixed defect family (24-00972858, ADO 1534578/1541765/1682315) — confirm build.
2. If funds are present but **not posted**, the user may simply need to **run/post OFR via QP043** (25-01054811 is the training version) — not a defect.
3. **Trapped suspense / phantom lock** with no MG (24-00968393) → find the orphaned release lock and clear it (script; verify-SELECT first).
4. **Duplicate JE100** → check for extra **metadata layers** (QECA/ECA vs QRA) on the Book-Revenue/OFR process and remove the redundant ones (24-00982893).
5. Capture Workspace #, MG #, JE100/JE101 screenshots, and the from/to owner BA#+Sub.

---

## 7. Cluster D — Maintenance Group lifecycle

The MG is the transactional container; a large config/defect cluster is the MG getting **stuck, locked, or undeletable**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| MG **won't delete / "partially deleted"** — header searchable but DOI/Transactions/PPN tabs empty | MG-delete left orphaned header | **Cleanup script** to delete the empty MG; behavior fixed in Oct-2025 HF | 24-00977396, 25-01049845 |
| Removing **errored DOIs** from a MG deletes **ALL** DOIs/transactions (even successful ones) | Remove-errored-rows defect | Code fix | 24-00942776 |
| MG **details disappear** when removing errored DOIs | Same family | Code fix | 24-00942776 |
| MG **locked**, can't release via **DO025** | **Approved twice** — frontend didn't disable the Approve button under perf load | Unlock/clear; root issue is double-approval under slowness | 24-00987497, 25-01020794 |
| MG stuck **"Creating Group"** until Retrieve / reopen | Web-engine refresh defect | Friday update resolved MG + related functions | 23-00917440 |
| MGs **routinely stuck in "Creating Group"** | Web-engine/QPEC | Update | 23-00917440 |
| MG **4513 stopped in Pending** (SAP-PRA integration, only 11 of 87 tiers processed) | SAP side; partial integration | **Revert MG to Submitted and re-approve** (run `COPY_DVDS2` for the partially-completed groups first) | 25-01051115 |
| **Multiple `COPY_DVD_W` started within 1–2 seconds** | Duplicate job launch | Investigate/serialize | 25-01037001 |
| myQDO preview process **blocks other jobs** | Preview serialization/perf | Perf fix | 25-01035543, **ADO 1668275 (GEC)** |
| Workspace **stored-procedure errors** | SP defect | Fix | 22-00664569 |
| MG **completed but left out a transaction** with error / split transaction not linked | Split wrote DOI history **without a valid Transaction Group Number** → unlinked from MG view | Not consistently reproducible; trace if recurs | 22-00641233, 25-01050592 |

**Fix recipe:**
1. **Won't delete / empty MG** → cleanup script to remove the orphaned `DONL_DVD_GRP` header (24-00977396); the underlying behavior is fixed in the Oct-2025 hotfix (25-01049845).
2. **Locked / DO025 can't release** → almost always **double-approval** under perf load (24-00987497). Unlock, and treat the slowness separately.
3. **Stuck "Creating Group"/"Pending"** → check **web engines / QPEC / QRA MT** are up (§10); restart if needed. For SAP-integration partial completes, **run `COPY_DVDS2`, revert to Submitted, re-approve** (25-01051115).
4. **Removing errored DOIs nuking the whole MG** is a confirmed defect (24-00942776) — escalate with the MG #.

---

## 8. Cluster E — DOI Setup / DOI Worksheet / decimal precision & NRI

The DOI build layer. The dominant defect is **decimal precision** — the Worksheet/grids not honoring the global `PRECISION` config, which then breaks GWI/Bearer-Group approval.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **DOI Worksheet ignores `PRECISION`** (8 by core default), accepts/saves 10 decimals | Worksheet didn't round to `PRECISION` on Excel import & bulk-edit | **Code updated to round NRI to `PRECISION` on import & bulk-edit** | 25-01012855 / **ADO 1727280** |
| DOI/Bearer-Group grids round display to 8 but **save >9 decimals** → BG Approval & GWI Calc fail | Grid save vs display mismatch (`DONL_DO_DETAIL`, `DONL_BEARER_GRP_DETAIL`) | Precision fix | 22-00676548 |
| DOI **Worksheet Excel loader fails on small decimals** | Loader precision/parse defect | Code fix | **ADO 1625151 (CNR), 1760270 (APH/CNR, USPD_DO_RVS_CREATION SP)** |
| MRO DOI Setup/Bearer-Group grids allow **import past precision config** | Precision validation gap | Code fix | 22-00676548 |
| DOI Worksheet **Arrg key missing** in grid | Grid column defect | Code fix | **ADO 1644077 (GEC, issue 198)** |
| DOI Worksheet **Default Effective-To date** should default to end-of-month/EOT | Default-date defect | Code fix | **ADO 1664868** |
| Unable to **update Historical DOI field** / approved-DOI attributes (web vs classic) | Validation prevents update of approved DOI | Fix / security (see §11) | 25-01003450, 22-00676536, 23-00904198 |
| **DOI Copy** errors / "copy a single DOI to same property" fails | Copy SP defect | Fix | 23-00915459, 25-01049022 |
| Can't add/remove owner on **copied DOI** via DO010 | Copy-edit defect | Fix | 22-00821108 |
| DOI Setup screen DO007 **data not populating** for new user | Security/role (see §11) | Grant access | 25-01034810 |
| New **DOI tier** number auto-generating / errors creating tiers | Tier-creation defect | Fix | 25-01060824, 22-00683988, 22-00655367 |

**Fix recipe:** for any "interest is off / GWI won't total 1 / BG approval fails" tied to **decimals**, check the **global `PRECISION` config** and whether the Worksheet/grid rounded to it on import/bulk-edit (25-01012855 → ADO 1727280; 22-00676548). The fix is to round to `PRECISION` on save. For copy/tier/Worksheet-loader failures, the implementing proc is **`USPD_DO_RVS_CREATION`** / the QRA DO procs (ADO 1760270) — escalate with the property/DOI and the import file.

---

## 9. Cluster F — DO mailing reports

Division Order / Transfer Order forms for mailing to owners — **DOR003, DOR008, DOR009, DOR015 (Exhibit A)**, run via **QP088**. The signature defect is **duplicated interest** on the form.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **DO form duplicates the owner's interest** (decimal shows twice → owner appears to own 2×) | Report query duplicates the interest line | Report fix | 22-00512731, 22-00711295, 24-00980159 (QP088/DOR003), 22-00512731 |
| DO/TO forms show 10 decimals but **NRI rounds to 8 / last 2 digits "00"** | Report-template rounding (post-2022.04 build) | Template fix | 23-00892160 |
| **Exhibit A (DOR015)**: From-owner combined but To-owner shows only one sequence (NRI decimals differ) | Exhibit A sub-report mismatch | **Updated `DOR015_Exhibit_A_PNR.rpt`** so From & To show identical NRI decimals | 24-00976197 |
| DOR003 **first owner missing address** / name+address not generating | Report template/address defect | Template fix | 22-00647279, 22-00569485, 22-00688849 (international address) |
| **DOR009 prints multiple times / multiple sequence numbers** | Report duplication | Template fix | 22-00647280, 24-00977426 |
| **DOR003 not working / won't open in Launcher** | Report deploy/param | Fix / config | 22-00826296, 23-00904185, 25-01018385 |
| `RPT_DOR02A` has a **BA_NO parameter it doesn't use** | Report param wiring | Fix | 22-00512608 |
| DOR009 doesn't work (QUP291/FSTR5477) | Report defect | Fix | 22-00512973 |
| Consolidated DO Report by Owner Number — metadata/report changes | Enhancement | Metadata + report change | 24-00981307, 25-01007374 |
| Report errors after **Patch 71** (LOV missing / dropped config) | Patch dropped report config | Re-apply config | 24-00981048, 24-00980918 |
| DO/TO for mailing **not generating** from Approved DOIs screen | `DEFAULT_MDO_BA_NO` config + stray SEP metadata layer params | Set `DEFAULT_MDO_BA_NO`; remove bad SEP metadata layer params | 25-01044604 (Customer Error) |

**Fix recipe:** "DO form duplicates interest" is a known report defect family (22-00512731, 22-00711295, 24-00980159) — confirm the client's report build. For NRI rounding / Exhibit-A mismatch, the fix is a **report-template (.rpt) replacement** (24-00976197 `DOR015_Exhibit_A_PNR.rpt`; 23-00892160). For "report won't run from Approved DOIs," check **`DEFAULT_MDO_BA_NO`** and stray SEP metadata-layer params (25-01044604). After any **patch**, re-verify report config wasn't dropped (24-00981048/918).

---

## 10. Cluster G — Integration

QDO integrates **out** to SAP-PRA (DOI/BA/property sync via QRA Middle Tier + RabbitMQ) and **out** to QCFS GL (QP043 export). This cluster is config/data/environment far more than core defect.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| QP043 export ran but **didn't reach QCFS GL** / out of balance | **MT100** Journal/Trans config cleared (V16-and-older bug clears settings when the screen is queried) → records orphaned in **SEXTN** staging without Journal/Trans definition | Reload MT100 from DEV; restage orphaned data (delete from staging + rerun **QCFSIMPCYC**); MT100 must be **Q-managed** | 24-00950935 / 24-00948961 |
| QCFS export successful in QRA but **not in QCFS GL** | **COA missing the appropriate JE Code Type** | Add JE Code Type to COA | 23-00915272 |
| QRA→QCFS **out of balance** (BU 107/108) | Imbalance | Script provided; QRA team RCA | 22-00674480, 22-00680638 |
| **BA Integration error from SAP** `Filter Name 'Contact.PrimaryBpNo': Invalid filter for an IN type query` | BA-list not validated before contact lookup | **Applied check to validate BA list before getting contact details** | 25-01019764 |
| **DOI Sync Status stuck "Approved"** (DOI updates in QDO/QDO History/SAP but Sync never flips to Completed; MG fails with PK/duplicate-transaction) | SAP-PRA callback timeout | **Increased timeout in SMICM** (SAP) | 25-01030423 |
| **QRA Middle Tier error** sporadic on MG changes (PRD); SAP can't connect on callback → MG stalls | RabbitMQ / QRA-MT messaging stall under PRD load | **Restart RabbitMQ services + restart QRA MT QPEC**; long-term WI logged | 26-01082277 / **ADO 1784413** |
| MG 4513 stopped in Pending (SAP), 11/87 tiers done | SAP-side partial integration | Run `COPY_DVDS2`, revert MG, re-approve | 25-01051115 |
| **SAP Property Interface errors** | Core property interface bug | June hotfix (22-00262330) | 22-00819402, 22-00676473 (funds call not integrating to SAP) |
| Well Completion → Prop DOI Xref **inserting incorrect product codes into PRA** | Xref integration defect | Code fix | 22-00819971 |
| Property webpage **saving date attributes in new format (yyyy-mm-dd)** breaking downstream integration | Web date-format change | Fix | 22-00634668 |
| Property venture-status / well import loaders not working | Loader defect | Fix | 22-00676454, 24-00941844 |

**Fix recipe:**
1. **QP043 → GL gap:** check **MT100** Journal/Trans config (it gets silently cleared if a client touches the V16 screen — keep Q-managed); if records orphaned in **SEXTN** staging, restage (delete + rerun **QCFSIMPCYC**) after fixing MT100 (24-00950935). Also verify the **COA has the JE Code Type** (23-00915272).
2. **SAP sync stuck / QRA MT error:** restart **RabbitMQ + QRA MT QPEC** (26-01082277); if the callback times out, raise **SMICM** timeout on the SAP side (25-01030423). For partial MG completes, `COPY_DVDS2` + revert + re-approve (25-01051115).
3. **BA/property interface errors** are usually validation/format (25-01019764 BA-list filter; 22-00634668 date format) — code fixes; confirm the hotfix.

---

## 11. Cluster H — Web upgrade: screen / security / access

A steady config cluster during **2021.04 / 2022.04 / 2023.04 / 2024.04 / 2025.04** web upgrades and cutovers: missing **security-object grants**, web-vs-classic gaps, and engine/env issues that masquerade as defects.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Bulk-edit DOI headers: **Save greyed out**, payout status deleted on exit | Missing security-object grant | **Add `QFRMDIVISIONORDERHEADERQUERY` to security group 48100** | 24-00966898 |
| "**Not authorized to access security object**" navigating screens (`QVpDashboardQDO`, `QRAWidgetAccess`, `QUCDashboardEditor`) | Security objects not granted to the role | Grant the objects to the user's security group | 23-00933550, 23-00909049 (Security Errors), 23-00904191 (Unapprove security) |
| DO007 **data not populating for a new user** | Role/security missing | Grant access | 25-01034810 |
| **Approval rights / DOI Unapprove** in UAT | Security config | Configure rights | 25-01042470, 25-01035327, 25-01024645, 23-00904191 |
| **Editable fields differ web vs classic** on approved DOI | Web validation/parity gap | Align validation | 23-00904198, 25-01031226, 25-01003450 |
| **DOI Copy / functions missing** in Web UAT | Feature not enabled / engine down | Enable feature; confirm web engines up | 24-00973279, 24-00957751, 25-01059649 |
| **Web Widgets failing HTTP 404** in PRDA1 | Widget deployment | Redeploy/config | 26-01068541 |
| **Two users can't access Quorum Web** | Access/env | Config | 22-00942134 → (typo) 24-00942134 |
| QDO Web functional issues (critical) / object reference errors | Web defect | Hotfix | 24-00966898, 24-00992770 |
| **Patch dropped configuration** (Patch 71 / patching overwrote myQDO settings) | Patch collateral | Re-apply config | 24-00980918, 23-00907112 |
| Maintenance Group 17 / Group-creation errors in UAT | Upgrade build defect/config | Fix/config | 26-01081859, 25-01041858, 26-01067775 |

**Fix recipe:** the default move for "Not Authorized / Save greyed / screen empty for some users" is **grant the named security object to the user's security group** (24-00966898 `QFRMDIVISIONORDERHEADERQUERY`→48100; 23-00933550 dashboard objects). Before calling a missing feature a defect, confirm the **web engines/QPEC are up** and the feature is **enabled** in that environment (25-01059649 turned out to be env, not a bug). After any **patch**, re-verify QDO settings/report config weren't dropped (23-00907112, 24-00980918).

---

## 12. Cluster I — Bearer Group / Market & Exemption Group (MEG) setup

Setup-and-config of the cost-bearing (Bearer/GWI) and market/exemption groups. Mostly **Application Configuration** and training, with a few defects.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Bearer Group should auto-create but didn't** (testing) | `AUTO_CREATE_BEARER_GROUP` config off | Enable config to auto-create, else create BG manually | 25-01008529 |
| BG numbers **revert to 1** even though different numbers entered | Need **`User Maintained Bearer Group`** checkbox | Check the box to keep user-entered BG #s | 25-01059575 (Customer Error) |
| DOI Approval fails — **GWI Bearer Group # not assigned** to a non-WI owner | Missing BG assignment | Assign GWI Bearer Group # before Approval | 26-01100831 (Customer Error) |
| **Bulk Edit not working** for Bearer Group Maintenance when BG details have **date breaks** | Bulk-edit defect across date breaks | Code fix | 24-00965362 |
| Bearer Group **header vs detail update dates** don't match (MRO) | Date-sync defect | Fix | 22-00676541 |
| **Bearer Group Effective Date** change | Config/ChangeConfig | Apply eff-date change | 23-00886515, 22-00569450 |
| **MEG / Market Exemption Group** can't be deleted from owner / updating existing MEGs | MEG maintenance | Fix / guidance | 22-00641203, 25-01044050 |
| MEG change: use **Modify, not Transfer** | Wrong tool | Best practice = Modify for MEG change | 25-01042027 (Training) |
| **Tract-level Market Group** needs a corresponding **Unit-level Market Group** (Unit-to-Tract) | Missing unit-level group | Create the unit-level market group | 25-01045698 |
| Market Exemptions report `RPT_DOR023` "no valid picklist" error | Picklist/metadata | Config | 23-00905191 |
| Preview DOI fails on **100% transfer when owner has market exemptions** | Market-exemption transfer defect | Fix | 23-00923316 |
| `FK_DONL_DVD_MKT_EXMPT_*` / `FK_DONL_MKT_EXMPLT_DONL_DETAIL` FK errors deleting DO007 records | Orphaned market-exemption child rows | Data fix (clear orphans) | 24-00988060, 22-00512479 |

**Fix recipe:** most BG/MEG tickets are **config**: `AUTO_CREATE_BEARER_GROUP`, the `User Maintained Bearer Group` checkbox, assigning the **GWI Bearer Group #** before Approval (GWI must total 1.0), and creating the **Unit-level** market group to pair a Tract-level one. For **MEG changes use Modify, not Transfer**. FK errors on DO007 delete = orphaned `DONL_*_MKT_EXMPT*` rows → scoped data cleanup.

---

## 13. Cluster J — Owner Search screen

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Owner Search **returns no results** though the owner is on the DOI | Owner Search query defect | Latest **hotfix** addresses it | 25-01024762 |
| Owner Search **fund total wrong** (suspense/payable) vs transfer screen | Fund-aggregation defect | Fix | 26-01064498, 24-00973290 |
| Funds in transfer screen **don't match** Owner Search; **can't export >1000 lines** | Grid row-limit + mismatch | Fix / raise limit | 24-00987231 |
| Owner Search **column filtering** issues | Grid filter defect | Fix | 25-01004578, 24-00968014 (MG DOI tab filter), 23-00922219 (UAT search) |
| DO Owner **Search errors** / "ALT Q" picklist shortcut broken | Search/keyboard defect | Fix | 26-01066911, 23-00918318 |
| Owner **Lease Xref** query spins indefinitely (MRO) | Query perf | Perf fix | 22-00676503 |

**Fix recipe:** Owner Search "no results / wrong totals / filter broken" is a recurring web-grid defect family largely cleared by hotfixes (25-01024762, 25-01004578). Confirm the build/hotfix; for >1000-line exports, it is a grid row-limit (24-00987231). Reproduce with the specific owner/well and capture the build.

---

## 14. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **1329807** | Bug / Closed | Combine on transfer erases Lease Cross-Reference | §4 | 22-00634665 |
| **1358439** | Bug / Closed | 293 transfer combines different settlement codes | §4 | 22-00634666 |
| **1358440** | Bug / Closed | MEG information disappears after combine transfer | §4 | 22-00634667 |
| **1368887** | Bug / Closed | Many-to-Many transfer fails without Combine flag | §4 | — |
| **1381101 / 1569116** | Bug / Requirement / Closed | 100% Non-WI→Non-WI already-on-DOI: to-owners not combining | §4 | — |
| **1625458** | Bug / Closed | Classic QDO Workspace: interests didn't combine as expected | §4 | 25-01012302 |
| **1644404** | Bug / Closed | MRO — NMA updated incorrectly in NRI xfer w/ Combine | §4 | — |
| **1727280** | Bug / Closed | DOI Worksheet ignores PRECISION global config | §8 | 25-01012855 |
| **1625151 / 1760270** | Bug / Closed | Web Grid Excel Loader fails on small decimals; DOI Worksheet fails on `USPD_DO_RVS_CREATION` SP | §8 | 23-00924182, APH/CNR |
| **1644077** | Bug / Closed | GEC — DOI worksheet/Lease-Xref Arrg key missing in grid | §8 | — |
| **1664868** | Bug / Closed | DOI worksheet — default Effective-To date to EOM/EOT | §8 | — |
| **1729989 / 1764539 / 1754316** | Requirement / Closed | DO PPN Staging Logic — merge Preview & Approval PPN creation; migrate `USPD_DO_RVS_CREATION` | §5 | — |
| **1565994 / 1567320 / 1580306** | Requirement/Task / Closed | DO PPN Notifications — MG PPN's tab + event-notification batch | §5 | — |
| **1771847 / 1772635** | Requirement / Closed | LD18 / LD45 PPN changes — development | §5 | — |
| **1742419** | (long-term fix WI) | Unintended PPNs on PC+funds MG (WA: exclude on PN025) | §5 | 25-01029286 |
| **1534578** | Bug / Closed | CNXU — Owner Funds Release failing (PRD) | §6 | — |
| **1541765** | Bug / Closed | Ovintiv/ECA — OFR completing with errors | §6 | — |
| **1584263** | Bug / Closed | GLE — OFR under DO129 "stuck" | §6 | 23-00888898 |
| **1682315** | Bug / Closed | DAY — Maintenance group does not stage the correct funds | §6 | — |
| **1536812 / 1739649** | Requirement / Closed/Proposed | Auto-Post Owner Funds Release; SGY AT tests | §6 | — |
| **1668275** | Bug / Closed | GEC — perf: MG screen slow after Preview | §7 | — |
| **1658203** | Bug / Closed | APA/MRO — Unit-to-Tract add-link to MG | §7/§12 | — |
| **1700063** | Requirement / Closed | Enable Maintenance on Inactive DOIs (Revenue Active column) | §7 | — |
| **1784413** | (long-term fix WI) | QRA Middle Tier sporadic error on MG changes | §10 | 26-01082277 |

> Many actionable cases were dispositioned **operationally** (cleanup/data scripts, config, hotfix) with no single product WI: empty-MG cleanup (24-00977396), MT100 reload + QCFSIMPCYC restage (24-00950935), `TRANS_GRP_SEQ_NO` re-create after cutover (25-01060843), `DEFAULT_MDO_BA_NO` for DO mailing (25-01044604), security-object grants (24-00966898). Confirm exact build/patch (NOV HF, Oct-2025 HF, Patch 71, 2023.04/2024.04/2025.04) in the Upstream release notes before stating fix availability.

---

## 15. Diagnostic SQL

> **Caveat:** QDO/QRA is SQL Server, schema `<CLIENT>_<ENV>UPS_QRA` (e.g. `APH_PRD17UPS_QRA`, `ECA_TQA17UPS_QRA`, `PNR_PRD16UPS_QRA`). Table/column names below come from case repro text and code search — **verify against the client DB** and always run a verify-SELECT inside a transaction before any DELETE/UPDATE.

```sql
-- A. Maintenance Group header + status (stuck/locked/empty MG, §7)
SELECT GRP_NO, GRP_ST_CD, MAINT_REASON_CD, MAINT_STATUS, CREATE_USER, CREATE_DT, UPDT_DT
FROM   DONL_DVD_GRP
WHERE  GRP_NO = '<MG#>';          -- GRP_ST_CD 3 = committed back into QDO (per 25-01051115)

-- B. Does the MG have child rows? (empty/partially-deleted MG, §7)
SELECT (SELECT COUNT(*) FROM DONL_DVD_DO_DETAIL WHERE GRP_NO='<MG#>') detail_rows,
       (SELECT COUNT(*) FROM DONL_DVD_DO_HIST   WHERE GRP_NO='<MG#>') hist_rows;

-- C. DOI detail for a property/tier (decimal precision / NRI, §8) — count places vs global PRECISION
SELECT PROP_NO, DO_TYPE_CD, DO_MAJ_PROD_CD, TIER, BA_NO, BA_SUB, INT_TYPE_CD, INT_TYPE_SEQ_NO,
       NRI_DEC, EFF_DT_FROM
FROM   DONL_DVD_DO_DETAIL
WHERE  PROP_NO = '<PROP>' AND DO_TYPE_CD IN ('REV','RRV')
ORDER BY TIER, BA_NO, INT_TYPE_SEQ_NO;

-- D. Global PRECISION / key configs (§8/§5/§12)
SELECT PARM_NM, PARM_VALUE FROM <client config/parameter table>
WHERE  PARM_NM IN ('PRECISION','RUN_RDCALCNEW','AUTO_CREATE_BEARER_GROUP','DEFAULT_MDO_BA_NO');

-- E. PPNs created by a MG + reason code (unexpected PPN, §5)
SELECT PROP_NO, PPN_REASON_CD, MAJ_PROD_CD, PROD_DT, GRP_NO, CREATE_DT
FROM   <PPN table>     -- e.g. RD/PN notification table; confirm name in client schema
WHERE  GRP_NO = '<MG#>'
ORDER BY PROD_DT;       -- red flag: PD41 / exemption / BG reason with no corresponding change

-- F. Suspended funds for an owner (OFR didn't move money / trapped suspense, §6)
SELECT OWNER_NO, BA_NO, BA_SUB, PROD_DT, SUSP_REASON_CD, SETTLE_CD, AMT
FROM   <subledger/JE101 funds table>
WHERE  BA_NO = '<from owner>' AND PROP_NO = '<PROP>'
ORDER BY PROD_DT;

-- G. Orphaned reversal-deck data blocking RD010 delete (25-01045698 family)
SELECT * FROM GXRF_DESKID_DO_CRTN  WHERE DESK_ID = '<deskid>';
SELECT * FROM GXRF_DESKID_DO_MAINT WHERE DESK_ID = '<deskid>';
SELECT * FROM GXRF_DESKID_RVNU_VAL WHERE DESK_ID = '<deskid>';

-- H. Missing DB sequence after cutover (pay-code change error, §4 / 25-01060843)
SELECT * FROM sys.sequences WHERE name = 'TRANS_GRP_SEQ_NO';   -- absent = re-create it

-- I. Orphaned QCFS staging when MT100 was cleared (§10 / 24-00950935)
SELECT * FROM <SEXTN staging table> WHERE <no Journal/Trans definition> ;  -- restage via QCFSIMPCYC after MT100 reload
```

---

## 16. Expected-Behavior / User-Education FAQ

~105 Training + ~173 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "I checked **Combine** but it didn't combine / split into 2 lines" | **By design** when the lines differ on suspense reason, settlement code, interest type, lease tie, or MEG — they must match exactly to combine | 24-00972847 (defect side §4); 25-01048790 (transfer options) |
| "Money didn't move after my transfer / records stuck in suspense" | Often the **OFR just hasn't been run/posted** — run OFR in **QP043** to release the unprocessed funds | 25-01054811, 26-01093248, 25-01054811 |
| "**Recent/Pending Maintenance** widget is missing my completed item" | The widget shows only **true DOI maintenance** (transfers/pay-code/exemption); a **Funds-Only Transfer** doesn't touch the DOI so it isn't listed | 25-01043451 |
| "How do I generate the Division Order for mailing?" | Run **`RPT_DOR003 - DOI Report for Mailing to Owners`** (walkthrough provided) | 26-01084834, 26-01081138 |
| "MEG / Market change is doing the wrong thing" | Use **Modify, not Transfer**, for a MEG/market change (best practice); Tract-level market group needs a **Unit-level** counterpart | 25-01042027, 25-01046803, 25-01045698 |
| "Bearer Group numbers revert to 1 / BG didn't auto-create" | Check **`User Maintained Bearer Group`** to keep entered #s; enable **`AUTO_CREATE_BEARER_GROUP`** to auto-create, else create manually | 25-01059575, 25-01008529 |
| "DOI Approval failed" | Usually **GWI Bearer Group # not assigned** to a non-WI owner, or GWI doesn't total 1.0 — fix setup then re-approve | 26-01100831 |
| "302 / 311 impairment errors on PPN" | Verify **Market Group setup** (tract/unit, products submitted together from VL100); often customer setup, not a bug | 25-01059135, 25-01055406 |
| "MG / DOI screen **timeout** / can't delete MG" | Perf/lock — a different user/session can often complete it; or wait for the running process | 25-01062649, 25-01042458 |
| "MG created PPNs for 300+ old properties / processes slow" | Someone **accidentally ran `COPY_DVD_W`** for a large historical set — let it finish | 26-01090998 |
| "How many transactions / digits can a Maintenance Group hold?" | No practical cap; MG # length bounded only by integer max — not a concern | 26-01094895 |
| "Estimate-to-Actual / converting an estimated DOI" | Converting an approved **estimated** DOI to **actual** via DOI Worksheet **re-requires approval** | 26-01084964 |
| "Errors creating transactions in a MG" / "failed to assign batch number" | Often **setup**: property was **inactivated**, or a **new BA** is set up wrong | 26-01094541, 26-01092878 |
| "DOI Worksheet / DOI import errors" | Use the **correct DOI Worksheet upload template** (provided); precision must fit `PRECISION` | 25-01046267, 25-01036573, 25-01062744 |
| "Can't delete reversal decks (RD010)" | **Bad data** in `GXRF_DESKID_DO_CRTN/_DO_MAINT/_RVNU_VAL` — cleanup script then delete | 25-01045698 |

**Tell-tale it's user/expected:** a combine that won't merge lines that genuinely differ; "money didn't move" that just needs OFR run via QP043; a widget that legitimately excludes funds-only transfers; a 302/311 impairment from client Market-Group setup; a BG that needs the `User Maintained`/`AUTO_CREATE` config; or a "how do I…/how much can it hold" question. **Verify the DOI/Market-Group/Bearer-Group setup and whether OFR was posted before treating a funds/impairment case as a defect.**

---

## 17. Key Code, Processes, Screens & Repos

### Screens / processes
| Screen / process | Purpose | Notes |
|---|---|---|
| **DOI Worksheet / DO005-DO007** | Build/edit the DOI (decimal interest, NRI, BG, MEG) | Must round to global `PRECISION`; import template-driven (§8) |
| **DO010** | DOI Copy | Copy-SP defects (§8) |
| **Maintenance Group screen / DO034 / Workspace** | Container for transfers, PC changes, exemption changes | Approval runs `COPY_DVDS2`/`COPY_DVD_W` |
| **DO025** | MG release/approve | Lock from double-approval (§7) |
| **DO129 / DO130 / QP043** | Owner Funds Release run/post; GL+LOS export to QCFS | §6 / §10 |
| **PN025 / VL100 / VL031 / CA020 / RD010** | PPN exclude / value lines / PPA upload / open CA / reversal decks | PPN WA path (§5) |
| **QP088 → DOR003/008/009/015** | DO/TO forms for mailing | Duplicate-interest & template defects (§9) |
| **MT100** | QCFS Journal/Trans definitions | V16 bug clears it when queried — keep Q-managed (§10) |
| **QCFSIMPCYC** | Re-interface QCFS staging records | Restage after MT100 fix (§10) |
| **INITMG / COPY_DVDS2 / COPY_DVD_W** | MG init & commit procs | Recovery: COPY_DVDS2 then revert+re-approve (§7) |

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `USPD_DO_RVS_CREATION.sql` | `Quorum.Upstream.QRA.Database /Stored Procedures/` (PPN reversal/preview creation SP) | §5/§8 |
| `COPY_DVD_W` / `COPY_DVDS2` / `QPSCopy2LiveJob.cs` | `Quorum.Upstream.QRA.Batch /Quorum.QRA.Process.QPDllDivisionOrder/` | §7 MG commit |
| `QSQL_IntTransfer.cpp` (interest transfer / combine) | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgDO/` | §4 transfer/combine |
| `QDOConstants.cs` + QDO core interface | `Quorum.Upstream.Shared.Web /Quorum.Upstream.Shared.CoreInterface/QDO/` | §4/§7 web |
| Security objects, picklists, process steps, code messages | `SUM.Upstream.Metadata` (`QARCH_CTRL_*`, `QARCH_CODE_MSG_TITLE`) | §11/§5 |
| `DOR015_Exhibit_A_PNR.rpt` & DOR templates | report metadata (client report set) | §9 |

### Repos
- **`Quorum.Upstream.QRA.Database` / `Quorum.Upstream.QRA.Database` (+ `Quorum.Upstream.Database` FluentMigrator)** — the DO/QRA stored procs (`USPD_DO_*`, `COPY_DVD*`), core DB requests, migrations. **Most QDO logic lives here.**
- **`Quorum.Upstream.QRA.Batch`** — managed batch (`Quorum.QRA.Process.QPDllDivisionOrder`: MG commit, copy-to-live, OFR).
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ revenue-accounting DO batch (`QPDllRevenueAcctgDO`: interest transfer/combine, impairment).
- **`Quorum.Upstream.Shared.Web` / `Quorum.Upstream.Shared.CoreInterface`** — QDO web screens, DOI Worksheet, Owner Search, dashboards, QDO constants.
- **`SUM.Upstream.Metadata`** — metadata, security objects/groups, picklists, process-step definitions, code messages.
- **`<CLIENT>_<ENV>UPS_QRA`** SQL Server schemas — per-client data. **Check the client schema first** — many fixes are scripts/config (MT100, sequences, orphan cleanup).

---

## 18. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **transfer/combine** drops or miscomputes attributes on identical lines: lease-xref/MEG/settlement-code dropped (ADO 1329807/1358439/1358440), combine won't merge identical lines (1625458), M:N fails without combine (1368887), NMA miscalc (1644404).
- A **PPN is created with no corresponding change** (PD41/exemption/BG reason) — PPN-staging defect family (24-00952414, 24-00973008, 24-00977860; rework 1729989/1764539/1754316).
- **OFR / MG does not stage all the funds** that were selected (24-00972858, ADO 1534578/1541765/1682315).
- **DOI Worksheet ignores `PRECISION`** / loader fails on small decimals (1727280, 1625151, 1760270).
- **Removing errored DOIs deletes the whole MG** (24-00942776).
- Provide: **MG #, Workspace #, property/DOI key, production dates, from/to owner BA#+Sub, exact COM/SQL/impairment error, build/hotfix**, and a DEV repro. Confirm fix availability + target build in the Upstream release notes.

**Handle as Configuration / Cloud Ops when:**
- **Security-object grant** missing (24-00966898 `QFRMDIVISIONORDERHEADERQUERY`→48100; 23-00933550 dashboard objects) — add to the security group.
- **BG/MEG config**: `AUTO_CREATE_BEARER_GROUP`, `User Maintained Bearer Group`, Unit-vs-Tract market groups, GWI Bearer Group assignment.
- **MT100 / QCFS** config cleared → reload MT100 + restage via QCFSIMPCYC (24-00950935); COA JE Code Type (23-00915272).
- Report config: `DEFAULT_MDO_BA_NO`, stray SEP metadata layers, template (.rpt) replacement (25-01044604, 24-00976197).
- After any **patch/upgrade**, re-verify dropped config (Patch 71 — 24-00980918; 23-00907112).

**Handle as Data fix (script, verify-SELECT in a transaction) when:**
- Empty/orphaned **MG header** can't delete (24-00977396); orphaned reversal-deck rows in `GXRF_DESKID_*` (25-01045698); missing **`TRANS_GRP_SEQ_NO`** sequence post-cutover (25-01060843); orphaned `DONL_*_MKT_EXMPT*` FK rows (24-00988060, 22-00512479); trapped-suspense orphan lock (24-00968393).

**Restart / environment first (no code):**
- MG stuck "Creating Group"/"Pending" or **QRA Middle Tier error** → restart **RabbitMQ + QRA MT QPEC**; confirm **web engines/QPEC** up (26-01082277, 23-00917440). SAP sync stuck "Approved" → raise **SMICM** timeout (25-01030423); partial MG complete → `COPY_DVDS2` + revert + re-approve (25-01051115).

**Handle as Training / Expected behavior (no fix):** see §16 — combine that correctly won't merge differing lines, "money didn't move" needing OFR run via QP043, widgets excluding funds-only transfers, 302/311 from client Market-Group setup, BG config toggles, and "how do I / how much" questions. **Verify DOI/Market-Group/Bearer-Group setup and OFR posting before treating funds/impairment cases as defects.**

---

*Skill created: 2026-06-14.*
*Based on: 1,291 closed QDO/Division_Orders SF cases — 333 actionable (Software Defect 216 + Application Configuration 114 + ChangeConfig 3) mined for fix recipes, plus ~44 Training/Customer-Error cases for the FAQ. ADO work items: 1329807, 1358439, 1358440, 1368887, 1381101/1569116, 1625458, 1644404, 1727280, 1625151/1760270, 1644077, 1664868, 1729989/1764539/1754316, 1565994/1567320/1580306, 1771847/1772635, 1742419, 1534578, 1541765, 1584263, 1682315, 1536812/1739649, 1668275, 1658203, 1700063, 1784413.*
*Repos: Quorum.Upstream.QRA.Database, Quorum.Upstream.QRA.Batch (Quorum.QRA.Process.QPDllDivisionOrder), Quorum.Upstream.QRA.ClassicBatch (QPDllRevenueAcctgDO), Quorum.Upstream.Shared.Web / .CoreInterface, SUM.Upstream.Metadata.*
