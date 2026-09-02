# SKILL: QPTM Contracts Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Service-agreement / capacity contracts — Contract Maintenance (QCM/web/classic) screen, contract setup (K#, TOS/type-of-service, MDQ/MDIQ/MDWQ/MSQ, ratchets, seasonal profiles), amendments & enrollment, effective dating, contract paths/locations & segmentation, FSS/PAL/ISS/storage & imbalance contracts, RFS/Offer/Capacity-Release-into-contract, agent/BA changes, contract deletion, and contract reports/exports/IOC.
**Companions:** Capacity-release *bidding/offer/award* mechanics → **SKILL_Capacity_Release.md** (cross-refs noted). Nomination overlap/ghost & nom-delete scripts → **SKILL_Nominations.md**. Cycle deadlines/EDI → **SKILL_EDI_Troubleshooting.md**.

> Evidence base: ~776 QPTM Contracts SF cases; ~264 actionable (Root Cause = Software Defect 116 / Application Configuration 56 / Customer Error 43 / Training 48). Every root-cause claim cites a real SF case# and/or ADO work item. Verbatim contract-delete SQL captured from ADO attachments (#1601380, #1586886).

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Contract Concepts & Data Model](#2-contract-concepts--data-model)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Contract Maintenance Screen — UI / Save / Web-vs-Classic (HIGH FREQUENCY)](#4-contract-maintenance-screen--ui--save--web-vs-classic-high-frequency)
5. [Amendment / Enrollment / Effective-Date / Status](#5-amendment--enrollment--effective-date--status)
6. [MDQ / MDIQ / MDWQ / MSQ / Ratchet / Seasonal / NETMDQRES](#6-mdq--mdiq--mdwq--msq--ratchet--seasonal--netmdqres)
7. [TOS / Rate / Path / Location / Segmentation](#7-tos--rate--path--location--segmentation)
8. [Storage / FSS / PAL / ISS / Imbalance Contracts](#8-storage--fss--pal--iss--imbalance-contracts)
9. [RFS / Offer / Capacity-Release-into-Contract](#9-rfs--offer--capacity-release-into-contract)
10. [Agent / BA Change on a Contract](#10-agent--ba-change-on-a-contract)
11. [Contract Deletion / Bad-Contract / Duplicate (Ops Runbook + VERBATIM scripts)](#11-contract-deletion--bad-contract--duplicate-ops-runbook--verbatim-scripts)
12. [Contract Reports / Exports / Index of Customers (IOC)](#12-contract-reports--exports--index-of-customers-ioc)
13. [Expected Behavior / User Education](#13-expected-behavior--user-education)
14. [Key Code Files & Repos](#14-key-code-files--repos)
15. [Database Tables Reference](#15-database-tables-reference)
16. [Diagnostic SQL Queries](#16-diagnostic-sql-queries)
17. [Known Historical ADO Bugs](#17-known-historical-ado-bugs)
18. [Escalation Decision Tree](#18-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. EXACT error/message text? (e.g., "QUIControllerContractMaintenance.DoQuery error", "Effective dates overlap existing data", "Evergreen Term Allowed")
[ ] 2. TSP and Contract Number (K#)? (clients almost always supply the K#)
[ ] 3. Which screen/tab — Contract Maintenance (Header/Locations/Agents/Contacts/Imbalance/PAL-ISS/Sched-Cap-Ovrd/UDF), Ratchet Maint, Seasonal Profile Maint, RFS/Offer?
[ ] 4. Web or Classic (QCM)? A LARGE share of Contracts defects are Web-vs-Classic parity gaps (field shows in Classic, not Web).
[ ] 5. New contract or existing? Created in QCM Classic then opened in Web? (#25-01049936 / extension-data defect)
[ ] 6. Internal or External (shipper) user? Several are security/visibility (shipper sees another shipper's MDQ — 22-00607592).
[ ] 7. Amendment involved? What is the Amendment Effective Date From, and did it "roll back a day"? (22-00630726)
[ ] 8. Contract type — Transport (FT/IT), Storage/FSS, PAL/ISS, OBA, Pooling, Capacity-Release replacement?
[ ] 9. QPTM version (e.g., v16/v17, 2022.04, 2023.04, 2024.04, 2025.10) — most fixes are version-gated.
[ ] 10. Is the ask to DELETE a bad/duplicate contract? → §11 Ops runbook (verbatim script).
```

### Where does the issue live?
| Entry point | Likely cluster | First place to look |
|-------------|----------------|---------------------|
| Field missing / won't save / Web≠Classic on Contract Maint screen | §4 ContractMaint UI | Web vs Classic parity; metadata/field config |
| Amendment created wrong / too many / date rolled back | §5 Amendment/Enroll | `KVALD_CTR_AMEND`, enrollment process |
| MDQ/MDWQ/MSQ wrong, ratchet/seasonal IDs not incrementing | §6 MDQ/Ratchet | `SCTRL_CTR_HEADER` qty fields, NETMDQRES job |
| "TOS field broken", path/segment/location not valid on K | §7 TOS/Path/Loc | `KCTRL_CTR_LOC`, TOS Maintenance, segment validation |
| FSS/PAL/ISS/storage/imbalance setup | §8 Storage/PAL | PAL/ISS tab, OBA TOS attributes |
| RFS/Offer/CommPass error, award→contract wrong | §9 RFS/Offer | RFS/Offer screens, replacement-contract dates |
| Change BA/Agent on a K | §10 Agent/BA | Agents tab, amendment, `KCTRL_CTR_USER_DEF` |
| "Delete this contract / duplicate K#" | §11 Deletion | Confirm bad, run verbatim cascade delete |

---

## 2. Contract Concepts & Data Model

### What a "contract" (K) is in QPTM
A service agreement (a.k.a. **K#**, `CTR_NO`) between the TSP and a shipper/Business Associate (`BA_NO`), under a **Type of Service** (`TOS` — FT, IT, FSS, PAL, ISS, OBA, etc.). It carries quantities (**MDQ**, and for storage **MDIQ** inject / **MDWQ** withdraw / **MSQ** storage), one or more **locations/paths** (primary/secondary receipt & delivery points), **agents**, **contacts**, and a chain of **amendments** (each an effective-dated `HIST_IDX` slice).

### Contract record model (the tables you will touch)
- `SCTRL_CTR_HEADER` — **the contract header** (CTR_NO, TSP, BA_NO, TOS, status, EFF_DT_FROM/TO, MDQ). Parent row.
- `KVALD_CTR_AMEND` — **amendments** (each amendment = effective-dated revision; Amendment Seq #).
- `KCTRL_CTR_LOC` — **contract locations / paths** (rec/del points, primary vs secondary, segment, route).
- `KCTRL_CTR_ATTR` / `KCTRL_CTR_ATTR_FLAT` — **contract attributes** (TOS attributes, "Allow Imbalance Trading", "count in MDQ", Utilizes 858, etc.). `_FLAT` is the denormalized cache the Web screen binds to.
- `KCTRL_CTR_USER_DEF` — user-defined fields (UDF tab).
- `SEXTN_CTR_HEADER_QPTM` — QPTM extension data for the header (the "contract extension" rows; created when a K is scoped from QCM into QPTM — #25-01049936). On TIPS this is `SEXTN_CTR_HEADER_QRMTIPS`.
- `KXREF_CTR_XREF_NOTE` — contract notes / cross-ref notes.
- `KCTRL_CTR_AGG_QTY_SPLIT_HDR` — **agent / aggregate quantity split header** (drives "can't delete a meter/location" overlap errors — case 23-00928312).

### Status & effective dating
- Contract header status moves Pending → Executed → Active (status default behavior is configurable — 22-00547654).
- Effective dating is by amendment slice: each amendment row has `EFF_DT_FROM`/`EFF_DT_TO` + `HIST_IDX`. **Overlapping slices** are the root of most "Effective dates overlap existing data" and "can't delete" errors.
- **QCM (Quorum Contract Management) Classic vs QPTM Web** — contracts are often created/edited in QCM Classic and scoped into QPTM. Many defects are **parity gaps** where Web doesn't render or save what Classic does.

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| Field present in Classic but **missing/blank in Web** Contract Maintenance (Route CD, Heating Factor, Notes, Agent Name, contract name) | Web↔Classic parity gap / field not rendered | Code fix or metadata config | 23-00899977, 23-00934933, 23-00894916, 22-00561432, 25-01012898 |
| `QUIControllerContractMaintenance.DoQuery error` opening a K | Web query defect (often tied to Invoice Group / specific data shape) | Code fix | 23-00886181 |
| "**Amendment Effective Date From rolls back to the prior day**" when editing BA/TOS/end-date before changing the date | Amendment date-default defect (all TSPs) | Code fix | 22-00630726, 22-00630721, ADO #1397848 |
| Enrollment process generates **dozens of amendments** | Enrollment amendment-handling defect | Code fix / enhancement | 22-00570042, ADO #1413977 |
| **Duplicate contract record** (same K#, same amend seq/date) after adjusting start date | Save-instead-of-update / date-split defect (Web) | Code fix | 22-00821094, ADO #1383354, #1723832 (meter list) |
| `NETMDQRES` not netting down MDQ (esp. mid-month / cap-release K) | Batch eligibility defect | Code fix | 23-00933989, 24-00956689, 24-00965618 — ADO #1674954, #1720842 |
| MDQ/MSQ shows wrong **decimals / UOM rounding**; FIXED_MDQ wrong for Seasonal MDQ type | Display + UOM-rounding defect | Code fix | 24-00938556, 23-00922233, 23-00906822 |
| "**Type of Service field broken**" on Contract Maint | TOS x-ref / config | Config | 23-00904509, ADO #1613127 |
| "**Effective dates overlap existing data**" deleting a meter/location | Orphaned `KCTRL_CTR_AGG_QTY_SPLIT_HDR` / overlapping slice | Data script | 23-00928312 |
| Can **delete a contract that has nominations** (should be blocked) | Missing delete-guard validation | Code fix | 24-00982700, ADO #1696546/#1381390 |
| "Delete this **incorrect/duplicate K#**" | Customer-entered wrong K#; needs cascade delete | Data script (verbatim §11) | 23-00890782, 23-00902451 — ADO #1586886, #1601380 |
| Capacity-Release **replacement contract created with wrong dates** | Offer→contract date-copy defect | Code fix | 22-00638262, 22-00638240, 22-00638241 |
| RFS Query screen slow / infinite-load / no results | RFS query perf defect | Code fix | 23-00905913, 23-00903078, 27-00922439, 23-00927133 |
| Shipper can **see another shipper's MDQ / pool / RFS** | Security/visibility defect | Code fix | 22-00607592, 22-00607596, 22-00607599 |
| Audit History won't load for **conjunctive contracts w/ LCLs** | Audit-history defect | Code fix (hotfix) | 24-00979920, ADO #1699084 |
| Contract extension data can't be added to a K created in QCM Classic | `SEXTN_CTR_HEADER_QPTM` Web defect | Code fix | 25-01049936 |
| 700-series REX segments show **wrong direction**; segmentation bug | Segment direction data/defect | Data script / code | 22-00630693, 24-00968218 |

---

## 4. Contract Maintenance Screen — UI / Save / Web-vs-Classic (HIGH FREQUENCY)

This is the **single largest Contracts cluster (~56 actionable cases)**. The dominant theme is **Web↔Classic parity**: a field, tab, or behavior that works in QCM Classic does not render or save the same way in the myQuorum Web Contract Maintenance screen. The Web controller is `QUIControllerContractMaintenance.cs` (see §14).

### Sub-patterns & fixes
| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|-----------|
| Column/field missing in Web (Route CD, Scheduling Heating Factor, Contract Name, all Notes, Agent Name, Route column on Locations) | Field not rendered in Web | Code/metadata | 23-00899977, 23-00934933, 25-01012898, 23-00894916, 22-00561432, 24-00978218 |
| `QUIControllerContractMaintenance.DoQuery error` opening certain Ks | Query defect (Invoice-Group-linked data) | Code | 23-00886181 |
| MDQ/MSQ shows decimals it shouldn't, or field too small to see value | Display/format config | Config | 23-00922233, 23-00906822, 23-00907969 |
| Bulk Edit on Contacts tab errors on save | Bulk-edit save defect | Release upgrade | 23-00917366 |
| Agents tab not saving on a `<NEW>` contract; Agent Name not displayed | Agent-save defect | Code | 23-00908638, 22-00561432 |
| UDF tab: values don't save casing; picklists unsupported in Web | UDF Web defects | Code / Declined | 22-00555599, 22-00823919 |
| Contract Maint Attachment / DocGen save fails | Attachment/DocGen defect | Config / Code | 25-01005843, 24-00981066 |
| Contract picklist shows duplicate rows; contract "disappears" running report to Excel | Query/export defect | Code | 22-00693340, 22-00822559 |
| Location name change in Location Maint not reflecting on contract Location tab in Web (works in Classic) | Web sync defect | Code | 22-00824914 |
| Contacts widget loses navigation/context; tab security; extra/missing attributes; integrated defaults not working (v17) | v17 Web Contract Maint defects (broad) | Software updates | 22-00608154, 22-00555550, 22-00555492, 22-00555494, 22-00536821 |

### Diagnostic
1. **Reproduce in BOTH Web and Classic.** If Classic is correct and Web is wrong → parity defect → code/metadata.
2. Pull the contract header + the failing tab's backing table for the K#.
3. Check the client has no `<CLIENT>.QPTM.Web` override controller (e.g., `DTEContractMaintenanceController.cs`) before assuming base behavior.

```sql
SELECT CTR_NO, TSP_NO, BA_NO, TOS_CD, CTR_STAT_CD, EFF_DT_FROM, EFF_DT_TO,
       CTR_MDQ, OVRD_CTR_MDQ, HIST_IDX
FROM SCTRL_CTR_HEADER
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>'
ORDER BY EFF_DT_FROM;
```

---

## 5. Amendment / Enrollment / Effective-Date / Status

Contracts are revised via **amendments** (`KVALD_CTR_AMEND`), each an effective-dated slice. Two recurring defect families: (a) **amendment effective-date defaulting** and (b) **enrollment over-generating amendments**.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|-----------|
| **"Amendment Effective Date From rolls back to the prior day"** when you change BA/TOS/end-date before touching the date field (all TSPs; hurts intraday deals) | Date-default defect on the amendment editor | Code fix | 22-00630726, 22-00630721, ADO #1397848 |
| Enrollment process **generates dozens of amendments**, unclear eff-dating/active status, perf concern | Enrollment amendment-handling logic | Code fix / TRAP enhancement | 22-00570042, ADO #1413977 |
| Incomplete enrollment transactions | Enrollment process config | Config | 22-00826630 |
| **De-enrollment error** — second de-enrollment for same account/period blocked | Validation blocks repeat de-enrollment; **workaround = delete prior enrollment detail rows**; enhancement needed for valid multi-period case | Data script + enhancement | 22-00826285 |
| Cannot end-date a contract amendment seq | Amendment end-date defect/config | Config | 26-01070514 |
| Error end-dating contract for an Agent BA | Agent-end-date validation | Config | 24-00984929 |
| Term Extension / ST amendment throws error on Alternate Points tab; NNT error | Term-extension defect | Data script / software | 22-00588031, 22-00588087, 22-00588117 |
| Error moving contract status to "Executed"; status default Pending vs Active | Status-transition / default config | Config / Training | 22-00630742, 22-00547654 |
| Contract ended accidentally — needs re-open | Reverse the end-date via amendment | Workaround | 24-00961582 |
| Adding contract quantity at same time as a new timeslice doesn't retain the qty | Timeslice-save defect | Software update | 22-00693349 |

### Diagnostic
```sql
-- All amendment slices for a K (look for overlap / runaway count / bad EFF dates)
SELECT CTR_NO, AMEND_SEQ_NO, HIST_IDX, EFF_DT_FROM, EFF_DT_TO,
       CTR_STAT_CD, UPDT_DT, USER_ID
FROM KVALD_CTR_AMEND
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>'
ORDER BY EFF_DT_FROM, AMEND_SEQ_NO;
-- Red flags: many rows in a short window (enrollment defect 22-00570042);
-- EFF_DT_FROM one day earlier than the user entered (rollback defect 22-00630726).
```

---

## 6. MDQ / MDIQ / MDWQ / MSQ / Ratchet / Seasonal / NETMDQRES

Contract quantities: **MDQ** (max daily qty, transport), **MDIQ/MDWQ** (storage inject/withdraw), **MSQ** (max storage qty), with **ratchets** (seasonal step-downs) and **seasonal MDQ profiles**. The **NETMDQRES** batch nets down contract MDQ for capacity releases.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|-----------|
| `NETMDQRES` not netting down MDQ; misses cap-release K **starting mid-month** even with valid fuel rate; incorrectly applies net MDQ to rec-location MDQ | NETMDQRES eligibility/calc defect | Code fix | 23-00933989, 24-00956689, 24-00965618 — ADO #1674954, #1720842 |
| MDQ/MSQ **UOM rounding error**; FIXED_MDQ shows qty for a Seasonal MDQ type | Rounding + seasonal-type display defect | Code fix | 24-00938556 (defect) / 24-00938544 (config) |
| MDQ shows decimals it shouldn't; can't see full MSQ Min/Max value | Display/format config | Config | 23-00922233, 23-00906822, 23-00907969 |
| **Ratchet IDs / MDQ Seasonal Profile IDs not incrementing** (federation build); can't tie seasonal profile to contract | Identity/sequence not incrementing | Data script (reseed) | 22-00536963, 22-00536978 |
| Ratchet Maintenance: detail dates set incorrectly; IT column missing | Ratchet maint defects (v17) | Software update | 22-00555591, 22-00561425 |
| Billing on Override Contract MDQ (Ozark); cap-release contracts don't reflect LCLs in Sched Cap Override | Override-MDQ / LCL config & defect | Config / Code | 24-00946580, 24-00956762 |
| "exceeds capacity / not enough capacity but they do"; unsubscribed capacity miscalculated | MDQ/capacity aggregation defect or config | Code / Config | 22-00630577, 24-00971317, 24-00960168 |

### Diagnostic
```sql
-- Contract qty fields
SELECT CTR_NO, TOS_CD, CTR_MDQ, OVRD_CTR_MDQ, MDIQ, MDWQ, MSQ_MIN, MSQ_MAX,
       MDQ_TYPE_CD, EFF_DT_FROM, EFF_DT_TO
FROM SCTRL_CTR_HEADER
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>'
ORDER BY EFF_DT_FROM;

-- NETMDQRES eligibility: confirm a valid fuel rate exists and the K's EFF_DT_FROM
-- (mid-month start is the 24-00956689 trigger). Check the QARCH process params for NETMDQRES.
```
> NETMDQRES core fix shipped in DB migration `QPTM_17.0.00.0027.0000_*_1632004.sql` (Quorum.QPTM.Database) and release 2024.04.1.5 / 2025.10.

---

## 7. TOS / Rate / Path / Location / Segmentation

The contract's **Type of Service** governs allowed transaction types, paths, and attributes. Locations/paths live in `KCTRL_CTR_LOC` (primary/secondary, segment, route). Many cases are config (new TOS, add attribute) vs defect (TOS field broken, path/segment direction).

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| "**Type of Service field broken**" on Contract Maint | TOS x-ref / metadata | Config | 23-00904509 |
| Create new TOS (interruptible storage, G contracts, secondary service) | New-TOS setup | Config | 23-00903066, 24-00979725, 25-01004061, 26-01083212 |
| Add attribute to a TOS ("Allow Imbalance Trading" on OBA; Primary/Secondary Capacity Type dropdown) | TOS attribute config | Config | 23-00907114, 23-00904610 |
| Error assigning **non-default path** to a TPC contract; non-default path segment validation | Path/segment validation | Config / Code | 24-00940487, 22-00630753 |
| **Segmentation bug**; 700-series REX segments show wrong direction | Segment direction defect/data | Config / Data script | 24-00968218, 22-00630693 |
| Pool location can't be added to Location tab; alternate points not populating | Location/path config or defect | Config / Code | 22-00524836, 22-00588185 |
| Delivery point appearing in Loc Rec; locations still showing "End of Time" | Location data/config | Config | 26-01102037, 22-00592979 |
| Associate the appropriate path to a TOS (how-to) | Setup guidance | Training | 24-00960229 |
| Rates: one-sided rates; wheeling contract add-to-rate error; SRC surcharge question | Rate config / Q&A | Config / Answered | 24-00936635, 26-01089205, 26-01102924 |

### Diagnostic
```sql
-- Contract locations / paths (primary vs secondary, segment, route)
SELECT CTR_NO, ID_LOC, LOC_ROLE_CD, CAP_TYPE_CD, SEG_NO, ROUTE_CD,
       PRIMARY_IND, EFF_DT_FROM, EFF_DT_TO
FROM KCTRL_CTR_LOC
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>'
ORDER BY LOC_ROLE_CD, ID_LOC;

-- Contract attributes (TOS attributes incl. imbalance-trading, count-in-MDQ, Utilizes 858)
SELECT CTR_NO, TOS_ATTR_CD, IS_ATTR_TRUE, EFF_DT_FROM, EFF_DT_TO
FROM KCTRL_CTR_ATTR
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>';
-- The Web screen binds to KCTRL_CTR_ATTR_FLAT; if Web≠Classic, compare ATTR vs ATTR_FLAT.
```

---

## 8. Storage / FSS / PAL / ISS / Imbalance Contracts

Storage (FSS), Park-and-Loan (PAL), Interruptible Storage Service (ISS), and OBA/imbalance contracts have extra tabs (PAL/ISS tab, Imbalance tab) and aggregate validations (PALISS).

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| FSS contract location setup & ratchets; FSS effective dates | Storage setup config | Config | 26-01099619, 26-01103577 |
| Parameter errors creating FSS contracts (PRD17) | FSS-create defect | Software update | 22-00609198 |
| PAL injection not appearing in Contract Maintenance / RFS | PAL display defect | Software update | 23-00917071, 23-00917070 |
| PAL contract exceeding quantity — validation check; PAL/ISS Max/Min daily quantities | PAL validation config | Config | 25-01036451, 22-00630752 |
| **PALISS aggregate qty validation error** when updating posting status / Master PALS agg validation | PALISS aggregate validation (run KPALISS after changes — see SKILL_Nominations §15) | Config / NTF | 22-00638318, 23-00898228 |
| Imbalance Trade users can't generate storage contract; STGIMBTIPS warning cleanup | Imbalance-contract config / warning | Config / Software | 24-00964452, 24-00984406 |
| Imbalance issues from agent split mid-month (HIO9897) | Agent-split imbalance config | Config | 22-00536094 |
| PAL contracts excluded from IPWS interruptible reporting export | Report filter defect | Software update | 22-00820316 |

> **Cross-product note:** STGIMBTIPS / imbalance-trade storage contracts overlap with TIPS; for TIPS storage see the TIPS assistant. TIPS contract header is `SEXTN_CTR_HEADER_QRMTIPS` / `QCTRL_CONTRACT` (see §11 overlap-fix script).

---

## 9. RFS / Offer / Capacity-Release-into-Contract

RFS (Request For Service) and Offers create/extend contracts; Capacity Release awards create **replacement contracts**. (For the bidding/award workflow itself, see **SKILL_Capacity_Release.md** when present.)

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| **Replacement contract created with wrong dates** after copy-offer / bid-eval | Offer→contract date-copy defect | Code fix | 22-00638262, 22-00638240 (Offer Vanished), 22-00638241 (award missing) |
| RFS Query screen slow / infinite-load (QStateQuery) / no results / very long delay | RFS query perf defects | Code fix | 23-00905913, 23-00903078, 23-00922439, 23-00927133, 22-00592798 |
| RFS Evergreen Term Extension capacity problems; Min Final MDQ not updating on Copy Forward; Copy Forward throws error | Evergreen/copy-forward defects | Code fix | 23-00924067, 22-00588116, 22-00806209 |
| "No Base Contract — cannot validate RFS"; error preventing contract creation on REX | Base-contract / creation defect | Code fix | 22-00586303, 22-00638188 |
| CommPass / myCommPass: RFS description/cycle/accounting-period not populating; submit on wrong entity; index-rate cap release | CommPass Web defects | Code / Training | 22-00591407, 22-00591387, 22-00591386, 22-00599379, 22-00591418 |
| Capacity Release bid-window time must match NAESB; agent list in Cap Release wrong | Cap-rel config / defect | Config / Software | 24-00940053, 24-00960691 |
| Error sending RFS to Auction; RFS unique-constraint error | Auction/RFS defect; data | Code / Data script | 22-00830590, 25-01036613 |

### Diagnostic
- Reproduce the RFS/offer in the failing screen; capture the offer #, K#, and date range. For "replacement contract wrong dates," compare the **offer release dates** vs the created contract's `SCTRL_CTR_HEADER.EFF_DT_FROM/TO`.
- RFS perf cases: capture the slow query (clients often log SQL); escalate as perf code fix.

---

## 10. Agent / BA Change on a Contract

A frequent **operational** request: change the Business Associate (BA/shipper) or Agent on an existing K. Mostly Config/Training, occasionally a data fix.

| Issue | Handling | Case |
|-------|----------|------|
| Change/switch BA on a contract (#12889, #12294) | Done via amendment; provide steps or make the config change | 24-00951221, 22-00597425, 26-01093344 |
| Contracts Maintenance **Agent update rights** | Security/role config | 26-01102578 |
| Agents tab: can't add Agent w/ Penalty Pool at same time as the contract | Two-step entry by design / declined | 22-00693345 |
| Default Agents screen / Agents tab functionality questions | Documentation | 22-00586352, 22-00832137 |
| Posting Agent question | Answered | 23-00915440 |
| Update contract number for a large number of noms (after BA/K change) | Workaround / bulk update | 26-01091205 |
| Contract Save Failure — contact marked Inactive in PGS | Re-activate the contact upstream | 25-01058029 |

> **Tell-tale (Customer Error):** the client end-dated/ended the contract or contact themselves, then can't transact. Confirm the amendment chain before scripting.

---

## 11. Contract Deletion / Bad-Contract / Duplicate (Ops Runbook + VERBATIM scripts)

Clients open "Delete incorrect/duplicate contract" cases (Customer Error: wrong K# entered; or Software Defect: duplicate K# created). Resolution Type is almost always **Data Script Provided** (delete) or **Software Updated** (the delete-guard / duplicate-creation defect).

### Safe deletion procedure
1. **Get identifiers:** `TSP_NO`, exact `CTR_NO` (K#), and confirm there are **no nominations/transactions** on it (a clean, mis-entered K). A contract *with* nominations should normally be blocked from deletion — if it deleted anyway, that's defect 24-00982700.
2. **Verify first** with §16 SQL — confirm the K is the bad one and is empty.
3. **Provide the cascade-delete script to Cloud Ops** (verbatim template below). Delete strictly **child → parent** (locations/amendments/attrs/UDF/notes/extension → header), or FK constraints block you.
4. For "can't delete a meter/location: Effective dates overlap existing data" — the blocker is orphaned `KCTRL_CTR_AGG_QTY_SPLIT_HDR` rows (case 23-00928312); clear those for the K first.
5. Older/on-prem clients get this as a **PDM** (Production Data Modification) rather than a self-service script (22-00830872 PDM to correct Business Party on K# 55387).

### VERBATIM contract-delete cascade — QPTM (redacted)
> Source (verbatim): ADO **#1601380** `TEP_PRD_QPTM_1_Delete_Contract.sql` (TEP PRD, case 23-00902451 family) and ADO **#1586886** `TEP_UAT_QPTM_1_Delete_Contract.sql` (RUBY/TEP, case 23-00890782). Concrete K# replaced with `<CTR_NO>`; **real table names and the delete set are kept intact.** This is the standard QPTM single-contract hard-delete. Wrap in a transaction; verify the K is empty before deleting.

```sql
-- Standardized QPTM contract-delete cascade (redacted) — delete a mis-entered / duplicate K
-- Param: <CTR_NO> (the bad K#). Run the verify SELECT first; confirm NO nominations exist.
BEGIN TRAN;  -- verify counts before COMMIT

-- 0. VERIFY: confirm this is the bad, empty contract
SELECT CTR_NO, TSP_NO, BA_NO, TOS_CD, EFF_DT_FROM, EFF_DT_TO
FROM   SCTRL_CTR_HEADER WHERE CTR_NO = '<CTR_NO>';
-- (also confirm no rows in the nomination tables for this K — see SKILL_Nominations §16)

-- 1. Child / dependent rows FIRST
DELETE FROM KCTRL_CTR_LOC         WHERE CTR_NO = '<CTR_NO>';   -- contract locations / paths
DELETE FROM KVALD_CTR_AMEND       WHERE CTR_NO = '<CTR_NO>';   -- amendments
DELETE FROM KCTRL_CTR_USER_DEF    WHERE CTR_NO = '<CTR_NO>';   -- user-defined fields
DELETE FROM KCTRL_CTR_ATTR_FLAT   WHERE CTR_NO = '<CTR_NO>';   -- denormalized attr cache (Web binds here)
DELETE FROM KCTRL_CTR_ATTR        WHERE CTR_NO = '<CTR_NO>';   -- contract attributes
DELETE FROM SEXTN_CTR_HEADER_QPTM WHERE CTR_NO = '<CTR_NO>';   -- QPTM extension header
DELETE FROM KXREF_CTR_XREF_NOTE   WHERE CTR_NO = '<CTR_NO>';   -- contract notes (if present)

-- 2. Parent header LAST
DELETE FROM SCTRL_CTR_HEADER      WHERE CTR_NO = '<CTR_NO>';

-- COMMIT;  -- only after the counts above match expectations; else ROLLBACK;
```
> **Notes:** (1) The two source scripts list these same tables (ordering varied — #1586886 deleted the header first, which works only when no FK enforces child→parent; prefer the **child→parent** order above). (2) `KXREF_CTR_XREF_NOTE` appears in the PRD script but not the UAT one — include it only if notes exist. (3) Always scope by `CTR_NO` (+ `TSP_NO` if the schema is multi-TSP).

### VERBATIM overlapping-dates fix — TIPS/QCTRL (redacted)
> Source (verbatim): ADO **#1659058** `01_HPE_PRD_TIPS_FIX_OVERLAPPING_DATES_CONTRACT_PUR-MSC-0008.sql` (HPE PRD, TIPS schema). Instead of deleting, this **end-dates the overlapping slice** so the new amendment fits. Param the K#, the slice's `EFF_DT_FROM`/`HIST_IDX`, and the new `EFF_DT_TO`.

```sql
-- Fix overlapping contract date slices (TIPS / QCTRL_) — end-date the conflicting slice
UPDATE SEXTN_CTR_HEADER_QRMTIPS SET EFF_DT_TO = '<NEW_EFF_DT_TO>'
 WHERE CTR_NO = '<CTR_NO>' AND EFF_DT_FROM = '<SLICE_EFF_DT_FROM>' AND HIST_IDX = '<HIST_IDX_1>';

UPDATE QCTRL_CTR_ATTR_FLAT      SET EFF_DT_TO = '<NEW_EFF_DT_TO>'
 WHERE CTR_NO = '<CTR_NO>' AND EFF_DT_FROM = '<SLICE_EFF_DT_FROM>' AND HIST_IDX = '<HIST_IDX_2>';

UPDATE QCTRL_CONTRACT            SET EFF_DT_TO = '<NEW_EFF_DT_TO>'
 WHERE CTR_NO = '<CTR_NO>' AND EFF_DT_FROM = '<SLICE_EFF_DT_FROM>';
```
> QPTM analog uses `SEXTN_CTR_HEADER_QPTM` / `KCTRL_CTR_ATTR_FLAT` / `SCTRL_CTR_HEADER` with the same `EFF_DT_FROM`+`HIST_IDX` keying.

### Duplicate-contract defect
- A **duplicate K# record** (same amend seq + date range) created when the user adjusts the start date and the screen **saves instead of updating / date-splitting** — ADO **#1383354** (DTE), recurrence pattern; meter-list duplicate is **#1723832**. Remove the duplicate slice via the cascade (scoped to the duplicate's `HIST_IDX`/`AMEND_SEQ_NO`), not the whole K.
- Duplicate contract *records* in a reporting view were fixed by `Update PACTRL_AGG_VIEWER_VW ... Remove Duplicate Contract Records` — ADO **#237785**.

---

## 12. Contract Reports / Exports / Index of Customers (IOC)

Lower volume; usually report-config, registered-SQL, or export defects.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Missing info on CWX06; CW04 can't filter Transportation Contract picklist; Contract MDQ Comparison Report issues | Report config / defect | Config / Code | 25-01034161, 22-00822680, 22-00822922 |
| Contract MDQ missing from MDWQ Report (RPT_K14) | Report data/infra | Infra resolved | 24-00946473 |
| Index of Customers Contracts not populated / F29-F49-F50 missing from IOC list | IOC config / data | Config / Answered | 23-00920698, 23-00934229, 24-00995659 |
| New contract not appearing on Monthly Pooling Report (RPT_K67) | Report config / NTF | NTF | 22-00607647 |
| Contract XML exports without Rate ID code after C-Hub | Export config | Config | 22-00630587 |
| Force Majeure Preview button not saving report to override location | Report-save defect | Software update | 25-01036295 |
| Contract "disappears" when running report in Excel | Export defect | Software update | 22-00822559 |
| Shipper-list extract truncating city names | Export field defect | Software update | 22-00601161 |

---

## 13. Expected Behavior / User Education

Not every Contracts case is a defect. Root Cause = **Training / Customer Error / No Technical Fault Found** (~90+ cases). Recognize these to avoid unnecessary scripts/escalations.

| Reported as | Reality | Case |
|-------------|---------|------|
| "Amendment date rolled back a day" | Real defect — but educate that changing the **Amendment Effective Date From first** avoids it (workaround) | 22-00630726 |
| "Wrong/duplicate K# entered, delete it" | Customer entered the wrong contract number — Customer Error; provide delete script | 23-00890782, 23-00902451 |
| "Contract ended / can't transact" | Customer end-dated it themselves; reverse via amendment | 24-00961582 |
| "How do I end a contract / change a BA / remove amendments" | How-to → documentation | 24-00938756, 26-01093344, 24-00995638 |
| "Two records with different dates on same amendment" | By-design amendment slicing | 23-00886855 |
| "Allows new Contract Number when autonumber is on" | Expected with the config; educate | 25-01003753 |
| "Contract attribute Utilizes 858 not available" | Attribute not enabled for the TOS — config/educate | 23-00888258 |
| "MDQ only preventing updates in Web" | Working as designed (MDQ-only flag) — workaround | 26-01091674 |
| "Multiple Cap Release Offers can over-sell capacity" | Reviewed — No Technical Fault Found | 22-00588006 |
| "Contracts not showing in Web version" | Data/visibility, NTF | 22-00521809 |

**Tell-tale that it's user/expected:** the client created the situation (wrong K#, self end-dated, autonumber config), or the "error" is a correctly-firing validation / a by-design parity behavior.

---

## 14. Key Code Files & Repos

### Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
| File | Purpose |
|------|---------|
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerContractMaintenance.cs` | **Contract Maintenance Web controller — source of `DoQuery error`, save/parity defects (§4)** |
| `Quorum.QPTM.Web.Core/Controllers/ContractMaintenanceController.cs` | Web Core contract-maint controller |
| `Quorum.QPTM.UnitTests/ContractMaintenance/*` | Contract-maint unit tests (incl. ResolveSegmentRights) |
| `Quorum.QPTM.DataObject/CodeGen/SharedContractHeaderDO.cs` | Contract header DO (maps `SCTRL_CTR_HEADER`) |

### Client override repos
`<CLIENT>.QPTM.Web` override the base contract-maint controller — e.g. `DTE.QPTM.Web.Core/Controllers/DTEContractMaintenanceController.cs`, plus CNP/ENT custom contract-header DOs. **Always check for a client override before assuming base behavior** (code search `{"searchText":"ContractMaintenance repo:<CLIENT>.QPTM"}`).

### Classic / Batch
| File / process | Purpose |
|----------------|---------|
| `Quorum.QPTM.ClassicBatch/QPDllPipelineMgrCR/QSQL_ContractAmend.cpp` | Classic contract-amendment SQL (amendment generation — §5) |
| `NETMDQRES` (batch process) | Nets down contract MDQ for capacity releases (§6) — fix in DB migration `*_1632004.sql` |
| `KPALISS` (batch) | PAL/ISS aggregate-value sync (run after PAL/ISS changes — §8) |

### Database
| Repo | Purpose |
|------|---------|
| Quorum.QPTM.Database | QPTM schema + FluentMigrator scripts (e.g., NETMDQRES fix `QPTM_17.0.00.0027.0000_*_1632004.sql`) |
| Quorum.QPTM.Metadata | Contract field/process metadata (`QARCH_CTRL_PROCESS_PARAM.json` etc.) |

---

## 15. Database Tables Reference

| Table | Purpose |
|-------|---------|
| `SCTRL_CTR_HEADER` | **Contract header** (CTR_NO, TSP, BA_NO, TOS, status, EFF dates, MDQ/MDIQ/MDWQ/MSQ). Parent. |
| `KVALD_CTR_AMEND` | **Amendments** (effective-dated slices, Amend Seq #, HIST_IDX) |
| `KCTRL_CTR_LOC` | **Contract locations / paths** (primary/secondary, segment, route) |
| `KCTRL_CTR_ATTR` / `KCTRL_CTR_ATTR_FLAT` | **Contract attributes** (TOS attributes; `_FLAT` = Web-bound cache) |
| `KCTRL_CTR_USER_DEF` | User-defined fields (UDF tab) |
| `SEXTN_CTR_HEADER_QPTM` | QPTM extension header (scoped-from-QCM data; #25-01049936). TIPS: `SEXTN_CTR_HEADER_QRMTIPS` |
| `KXREF_CTR_XREF_NOTE` | Contract notes / cross-ref notes |
| `KCTRL_CTR_AGG_QTY_SPLIT_HDR` | Agent/aggregate-qty split header (blocks meter/location delete on overlap — 23-00928312) |
| `PACTRL_AGG_VIEWER_VW` | Reporting view (dedup fix — ADO #237785) |
| `QCTRL_CONTRACT` / `QCTRL_CTR_ATTR_FLAT` | **TIPS** contract header/attrs (overlap-fix script #1659058) |
| `QARCH_CTRL_PROCESS_PARAM` | Batch process params (e.g., NETMDQRES) |

---

## 16. Diagnostic SQL Queries

### A. Contract header + all amendment slices (the workhorse)
```sql
SELECT h.CTR_NO, h.TSP_NO, h.BA_NO, h.TOS_CD, h.CTR_STAT_CD,
       h.EFF_DT_FROM, h.EFF_DT_TO, h.CTR_MDQ, h.OVRD_CTR_MDQ, h.HIST_IDX
FROM SCTRL_CTR_HEADER h
WHERE h.TSP_NO = <TSP_NO> AND h.CTR_NO = '<K#>'
ORDER BY h.EFF_DT_FROM;

SELECT a.CTR_NO, a.AMEND_SEQ_NO, a.HIST_IDX, a.EFF_DT_FROM, a.EFF_DT_TO,
       a.CTR_STAT_CD, a.UPDT_DT, a.USER_ID
FROM KVALD_CTR_AMEND a
WHERE a.TSP_NO = <TSP_NO> AND a.CTR_NO = '<K#>'
ORDER BY a.EFF_DT_FROM, a.AMEND_SEQ_NO;
```

### B. Overlapping amendment slices (the "overlap existing data" root)
```sql
SELECT a1.CTR_NO, a1.AMEND_SEQ_NO, a1.EFF_DT_FROM, a1.EFF_DT_TO
FROM KVALD_CTR_AMEND a1
JOIN KVALD_CTR_AMEND a2
  ON a1.CTR_NO = a2.CTR_NO AND a1.TSP_NO = a2.TSP_NO
 AND a1.AMEND_SEQ_NO <> a2.AMEND_SEQ_NO
 AND a1.EFF_DT_FROM <= a2.EFF_DT_TO AND a1.EFF_DT_TO >= a2.EFF_DT_FROM
WHERE a1.TSP_NO = <TSP_NO> AND a1.CTR_NO = '<K#>'
ORDER BY a1.EFF_DT_FROM;
```

### C. Contract locations / paths
```sql
SELECT CTR_NO, ID_LOC, LOC_ROLE_CD, CAP_TYPE_CD, SEG_NO, ROUTE_CD,
       PRIMARY_IND, EFF_DT_FROM, EFF_DT_TO
FROM KCTRL_CTR_LOC
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>'
ORDER BY LOC_ROLE_CD, ID_LOC;
```

### D. Web≠Classic attribute mismatch (compare ATTR vs the FLAT cache)
```sql
SELECT 'ATTR' src, TOS_ATTR_CD, IS_ATTR_TRUE, EFF_DT_FROM, EFF_DT_TO
FROM KCTRL_CTR_ATTR      WHERE TSP_NO=<TSP_NO> AND CTR_NO='<K#>'
UNION ALL
SELECT 'FLAT' src, TOS_ATTR_CD, IS_ATTR_TRUE, EFF_DT_FROM, EFF_DT_TO
FROM KCTRL_CTR_ATTR_FLAT WHERE TSP_NO=<TSP_NO> AND CTR_NO='<K#>'
ORDER BY TOS_ATTR_CD, src;
-- Rows in ATTR but not FLAT (or stale FLAT) explain a Web-only display gap.
```

### E. Agent-qty-split rows blocking a meter/location delete (23-00928312)
```sql
SELECT * FROM KCTRL_CTR_AGG_QTY_SPLIT_HDR
WHERE TSP_NO = <TSP_NO> AND CTR_NO = '<K#>';
-- If present, these must be cleared before the location/meter can be removed.
```

### F. Confirm a contract is EMPTY before deleting (pair with SKILL_Nominations §16)
```sql
-- No noms on this K? (NNCTRL_NOM_DTL is the QPTM nom detail table)
SELECT COUNT(*) AS NOM_ROWS FROM NNCTRL_NOM_DTL
WHERE TSP_NO = <TSP_NO> AND SR_CTR_NO = '<K#>';
-- A non-zero count means do NOT hard-delete (see defect 24-00982700).
```

---

## 17. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1397848** | Bug / Closed | All TSPs — Amendment Effective Date From rolls back to prior day (DUPLICATE of TGL 21-00204176) | §5 Amendment | 22-00630726 |
| **#1413977** | Task / Closed | [TRAP] BLH Enrollment Process Contract Amendment Handling Enhancement | §5 Enrollment | 22-00570042 |
| **#1383354** | Bug / Closed | DTE — Nominations not retrieving / duplicate contracts error recurrence | §11 Duplicate | 22-00821094 |
| **#1723832** | Bug / Closed | QMCW — Duplicate Contract Meter List Records Created | §11 Duplicate | — |
| **#237785** | Database Change / Closed | Update PACTRL_AGG_VIEWER_VW to remove duplicate contract records | §11 Duplicate (report) | — |
| **#1674954** | Task / Closed | GBG — NETMDQRES does not update MDQ for cap-release K starting mid-month | §6 NETMDQRES | 24-00956689 |
| **#1720842** | Task / Closed | NETMDQRES incorrectly applying net MDQ to rec-location MDQ | §6 NETMDQRES | 24-00965618 |
| **#1699084** | Bug / Closed | GBG — Audit History screen not loading for conjunctive contracts w/ LCLs | §4 ContractMaint | 24-00979920 |
| **#1723096** | Bug / Closed | VGP — CWFIRMTRAN pulls contract eff-date range instead of active range | §12 Reports/Batch | 25-01012002 |
| **#1696546 / #1381390** | Bug / Closed | Contract deletable even though nominations existed (delete-guard) | §11 / §4 | 24-00982700 |
| **#1586886** | Bug / Closed (script attached) | TEP/RUBY — Incorrect contract number entered, **`Delete_Contract.sql`** | §11 Deletion | 23-00890782 |
| **#1601380** | Script Deployment / Closed (script attached) | TEP — Delete contract from PRD, **`Delete_Contract.sql`** | §11 Deletion | 23-00902451 |
| **#1659058** | Script Deployment / Closed (script attached) | HPE — fix overlapping dates for contract PUR-MSC-0008 (TIPS) | §11 Overlap | — |
| **#1613127 / #1603788** | Bug / Closed | Contract Maintenance — Type of Service field broken | §7 TOS | 23-00904509 |

> Takeaway: Contract **deletion / duplicate / overlap** cases are dispositioned operationally (verbatim cascade-delete or end-date scripts via Cloud Ops/PDM). The recurring **code** root causes are the **amendment date-rollback** (#1397848), **enrollment over-amendment** (#1413977), **NETMDQRES** eligibility (#1674954/#1720842), and **Web↔Classic parity** gaps in `QUIControllerContractMaintenance.cs`.

---

## 18. Escalation Decision Tree

```
Contracts case reported
│
├─ "Delete / duplicate / wrong K#"?  (§11)
│   ├─ Confirm K# is the BAD one and has NO nominations (§16-F) → if it has noms, that delete is a DEFECT (24-00982700)
│   ├─ Empty/mis-entered K → provide VERBATIM cascade-delete script (§11) to Cloud Ops / PDM
│   ├─ Overlapping date slices blocking save/delete → end-date the conflicting slice (§11 overlap script) or clear KCTRL_CTR_AGG_QTY_SPLIT_HDR (23-00928312)
│   └─ Duplicate created on save (same seq/date) → remove the dup slice; link ADO #1383354 / #1723832
│
├─ Field missing / won't save / Web ≠ Classic on Contract Maint?  (§4)
│   ├─ Reproduce in Classic — correct there, wrong in Web? → parity defect (code/metadata)
│   ├─ Check ATTR vs ATTR_FLAT (§16-D) for attribute display gaps
│   └─ Check for <CLIENT>.QPTM.Web override controller first
│
├─ Amendment created wrong / date rolled back / too many?  (§5)
│   ├─ "Eff Date From rolls back a day" → defect #1397848; workaround = set the date first
│   ├─ Enrollment spawning many amendments → #1413977
│   └─ Status/end-date transition error → config / training
│
├─ MDQ / MDWQ / MSQ / ratchet / seasonal / NETMDQRES?  (§6)
│   ├─ NETMDQRES not netting (mid-month K) → #1674954 / #1720842
│   ├─ Decimals/UOM rounding → display config or #24-00938556
│   └─ IDs not incrementing (federation) → reseed data script
│
├─ TOS / rate / path / location / segmentation?  (§7)
│   ├─ "TOS field broken" → config (#1613127)
│   ├─ New TOS / add attribute → config
│   └─ Path/segment direction → config or data script
│
├─ Storage / FSS / PAL / ISS / imbalance?  (§8)
│   └─ PAL/ISS tab, OBA attributes, PALISS aggregate validation (run KPALISS)
│
├─ RFS / Offer / Capacity-Release into contract?  (§9)
│   ├─ Replacement contract wrong dates → offer→contract date defect
│   ├─ RFS query slow/no-results → perf code fix
│   └─ Bidding/award workflow itself → SKILL_Capacity_Release.md
│
├─ Agent / BA change?  (§10)
│   └─ Usually amendment + config/training; confirm contact not inactive upstream
│
└─ Report / export / IOC?  (§12)
    └─ Report filter / registered SQL / export field config
```

---

*Skill created: 2026-06-01*
*Based on: ~264 actionable QPTM Contracts SF cases + ADO work items #1397848, #1413977, #1383354, #1723832, #237785, #1674954, #1720842, #1699084, #1723096, #1696546, #1586886, #1601380, #1659058, #1613127. Verbatim contract-delete SQL from ADO attachments #1601380 & #1586886; overlap-fix SQL from #1659058.*
*Companions: SKILL_Capacity_Release.md, SKILL_Nominations.md, SKILL_EDI_Troubleshooting.md. Applicable to all QPTM TSPs/clients (QCM Classic + myQuorum Web).*
