# SKILL: QPTM Customer Accounts, Inventory & Measurement Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Customer/BA inventory **account setup & accumulation** (INACCTACCM / CUSTACCTACCUM), **Authorization to Post Imbalances** screen, **imbalance inventory & trading** (Imbalance Trading Form / Date Range Trades), **storage inventory & Date Range Storage Transfer**, **pipeline/system inventory**, **cashout (CICO)**, **inventory adjustments**, **OBA/PAL (park-and-loan) balances**, and **measurement / meter volumes** that feed accounting (ALESVOLIMP, WHMEASIMP, CSUDAILOAD, FlowCal import).
**Companions:**
- Allocation engine logic (ALALLOCATE/ALNEWPREPR, prorate, gross vs alloc) → **SKILL_Allocations.md** — cross-linked, **not duplicated** here.
- Imbalance → invoice / cashout *billing* output → **SKILL_Billing.md**.
- Contract effective-date / TOS setup → **SKILL_Contracts.md**.
- Security/user login & Okta access (the "Customer Accounts" *user-admin* bucket) → **SKILL_Security_UserAdmin.md**.

> **Evidence base:** ~1,135 closed `My Quorum Gas Pipeline` cases in categories Customer Accounts / Inventory / Pipeline Inventory / Measurement. Of these, **654 are User Administration Requests** (security accounts — out of scope, see SKILL_Security_UserAdmin). The **actionable technical** set mined here is **176 cases** (Root Cause = Software Defect 87, Application Configuration 97, Customer Error 78, Training 63 across the four categories). Every root-cause claim cites a real SF case # and/or ADO work item. Verbatim fix SQL is reconstructed from real ADO attachments with concrete values redacted to `<PLACEHOLDER>`.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Concepts: Accounts, Inventory & Measurement Data Flow](#2-concepts-accounts-inventory--measurement-data-flow)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Customer/BA Inventory Account Setup & Accumulation (INACCTACCM)](#4-customerba-inventory-account-setup--accumulation-inacctaccm)
5. [Authorization to Post Imbalances Screen](#5-authorization-to-post-imbalances-screen)
6. [Imbalance Inventory & Trading (Imbalance Trading Form / Date Range Trades)](#6-imbalance-inventory--trading)
7. [Storage Inventory & Date Range Storage Transfer](#7-storage-inventory--date-range-storage-transfer)
8. [Cashout (CICO) & Inventory Adjustments](#8-cashout-cico--inventory-adjustments)
9. [OBA / PAL (Park-and-Loan) Balances](#9-oba--pal-park-and-loan-balances)
10. [Measurement / Meter Volumes Feeding Accounting](#10-measurement--meter-volumes-feeding-accounting)
11. [Inventory & Balancing Reports](#11-inventory--balancing-reports)
12. [Verbatim Fix Scripts (Redacted)](#12-verbatim-fix-scripts-redacted)
13. [Key Code Files & Repos](#13-key-code-files--repos)
14. [Database Tables Reference](#14-database-tables-reference)
15. [Diagnostic SQL Queries](#15-diagnostic-sql-queries)
16. [Known Historical ADO Bugs](#16-known-historical-ado-bugs)
17. [Expected Behavior / User Education](#17-expected-behavior--user-education)
18. [Escalation Decision Tree](#18-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. Which screen/process? (Auth to Post Imbalances, Customer Account Maint, Imbalance Trading Form,
        Date Range Storage Transfer, Inventory Adjustment, Measurement Entry, or a batch INACCTACCM/ALESVOLIMP/WHMEASIMP)
[ ] 2. TSP_NO and Customer/BA (BP_NO) + Inventory Account ID (INV_ACCT_ID) if known?
[ ] 3. Which Accounting Month (ACCTG_MTH) and/or Production Month? Is that month OPEN or CLOSED?
[ ] 4. Is the issue a balance VALUE (wrong qty / phantom record) or a SCREEN/PICKLIST behavior?
[ ] 5. Contract # and TOS (FT/IT/NNS/FSS/storage)? Note contract EFF_DT_FROM/EFF_DT_TO.
[ ] 6. Internal or External (shipper) user? (Auth-to-Post & trading rules differ by user type.)
[ ] 7. For measurement: which import path (FlowCal/eSuite → ALESVOLIMP, WHMEASIMP, CSUDAILOAD, SFTP)? Which gas days?
[ ] 8. Has month-end roll / cashout (IN_IMBALCI / CICO) already run for the period?
[ ] 9. Web or Classic? Several inventory screens are Web-rewrites with their own defects.
[ ] 10. QPTM version (2023.04 / 2024.04 / 1.5) — many fixes are version/hotfix-gated.
```

### Where does it live?
| Entry point | Cluster | First place to look |
|-------------|---------|---------------------|
| "Phantom"/stuck inventory balance; Auth-to-Post total wrong | §4, §5 | `INTRAN_ACCT_BAL` / `INTRAN_ACCT_ACTIVITY` for the INV_ACCT_ID |
| Contract missing/extra on Auth-to-Post or Trading picklist | §5, §6 | contract EFF_DT vs imbalance period; auth-to-post header table |
| Imbalance Trading Form errors / blank fields / can't confirm | §6 | trading rules config + screen table mappings |
| Storage transfer screen button/field broken | §7 | Date Range Storage Transfer (Web) defects |
| Wrong inventory after cashout / daily cashout | §8 | CICO qty, inventory adjustment, ALALLOCATE (Allocations skill) |
| Customer/BA account not auto-generating; accum wrong | §4 | INACCTACCM steps, INKASSIGN, upstream-fuel step |
| Meter data missing / measurement load failing | §10 | ALESVOLIMP / WHMEASIMP / CSUDAILOAD job log, meter eff dates |
| Report total wrong (IN51/IN53/IN62/IN40/IN02) | §11 | report registered-SQL / status filter |

---

## 2. Concepts: Accounts, Inventory & Measurement Data Flow

### The pipeline (measurement → allocation → inventory → cashout/bill)
```
[Meter / Plant]
   │  FlowCal / eSuite / SFTP file
   ▼
[Measurement Import]  ALESVOLIMP · WHMEASIMP · CSUDAILOAD     (§10)
   │  validated meter volumes by gas day
   ▼
[Allocation]          ALALLOCATE / ALNEWPREPR   → SKILL_Allocations.md
   │  ALLOC_REC_QTY / ALLOC_DEL_QTY per account
   ▼
[Customer Account Accumulation]  INACCTACCM (a.k.a. CUSTACCTACCUM)   (§4)
   │  rolls allocated volumes + nom/fuel into the inventory account
   ▼
[Inventory Account balances]  INTRAN_ACCT_BAL / INTRAN_ACCT_ACTIVITY (§4)
   │  imbalance position by account/month
   ├──► [Authorization to Post Imbalances] screen   (§5)
   ├──► [Imbalance Trading]  Imbalance Trading Form / Date Range Trades (§6)
   ├──► [Storage]  Date Range Storage Transfer       (§7)
   └──► [Cashout]  IN_IMBALCI (Cash In/Cash Out, CICO) (§8) → SKILL_Billing.md
```

### Account model
- **Inventory Account** = the per-customer (or OBA/pool/storage) balance bucket. Keyed by `INV_ACCT_ID` + `TSP_NO`, scoped by `ACCTG_MTH`. A customer/BA may legitimately have several (transport imbalance, storage, OBA) — but being **associated to more than one** for the *same* purpose is usually a setup warning (26-01079372).
- **Account header** (`*INCTRL_ACCT_HDR` family) defines the account; **balance** (`INTRAN_ACCT_BAL`) holds the monthly position; **activity** (`INTRAN_ACCT_ACTIVITY`) is the per-event ledger that accumulates into the balance. Phantom-balance cases are almost always a bad **activity** row that the balance keeps summing (23-00928558 / ADO #1632413).
- **Accounting Month vs Production Month:** measurement/PTR is keyed by *production* month; rolling/cashout is keyed by *accounting* month. The month-roll process must check PTR approval **before** rolling measurement, or it can close the wrong month (25-01010798).

---

## 3. Symptom → Root-Cause Matrix

| Symptom | Most common root cause | Fix type | Evidence |
|---------|------------------------|----------|----------|
| Long-outstanding "phantom" inventory record won't clear (e.g. 44 GJ) | Orphaned `INTRAN_ACCT_ACTIVITY` row left when a receipt point was switched OBA→allocatable; balance keeps re-summing it | **Data script (delete activity/bal row)** | 23-00928558, ADO **#1632413** |
| Auth-to-Post Activity-tab total miscalculates / contract shows wrong imbalance | INACCTACCM **Upstream-Fuel step** adding fuel into the account it shouldn't | **Config (remove upstream-fuel step from INACCTACCM)** | 25-01008982, 24-00966031, ADO **#1729655** |
| Auth-to-Post lists a contract's imbalance it shouldn't / auto-enabled | Authorization config / contract-to-account mapping | Config | 23-00921430, 25-01021561 |
| External shipper **deleted a contract** off Auth-to-Post screen | Customer error — header row removed | **Data script (restore header)** | 25-01009525, 24-00964901 |
| Imbalance Trading Form: **valid contract not in picklist** | Screen only lists *currently* active contracts; should allow contracts active when the imbalance was created | Code fix; **workaround: temporarily extend contract EFF_DT_TO** | 25-01044171 |
| Imbalance Trading Form: Object Reference / fields point to non-existent tables | Screen field mappings to `init_inctrl_acct_hdr` / `conf_inctrl_acct_hdr` wrong for client schema | Code/config fix | 24-00942344, ADO **#1804104** |
| Can't confirm imbalance trade — "Invalid Account Type Combination" | Account-type check on trade detail grid too strict | **Config (remove invalid account-type check)** | 23-00908119 |
| Trading processable as External user when it shouldn't be | Trading rule severity/permission | Code fix | 22-00671628 |
| Date Range Storage Transfer screen: missing Update button / can't toggle FROMINIT↔TOINIT / withdraw broken | Web rewrite defects on the new screen | Code fix | 24-00938769, 23-00935116, 24-00939902 |
| Storage transfer in **REJ status** still counted in storage inventory | Status filter defect in inventory calc | Code/data | 22-00601085 |
| Storage transfer blocked by capacity validation error | Storage-capacity validation logic | Code fix | 24-00986411, ADO **#1663406** |
| Daily cashout / CICO produces wrong inventory | CICO qty processed wrong → customer makes inventory adjustment | Customer adjustment / data | 24-00974087, 22-00692603 |
| IN51A double-counts CICO qty | Report calc defect | Code | 23-00902494, 25-01031777 |
| Customer/BA account not auto-generating (INKASSIGN/BLKINVGRP) | Web auto-gen defect | Code fix | 22-00671735, 22-00671736 |
| Measurement not coming in / load failing | Import job (ALESVOLIMP/WHMEASIMP/CSUDAILOAD) config, SFTP path, meter eff dates, or file format | Config / data script | 25-01040593, 24-00986798, 26-01087490, 24-00992058 |
| WHMEASIMP "not matching" warning uses **end-dated paper meters** | Import ignores meter effective dates | Code fix | 24-00992058, ADO **#1700341** |
| Accounting-month roll closes wrong month (no PTR check) | Roll process keys off measurement, not billing/PTR | Code fix | 25-01010798 |
| "Associated to more than one Inventory Account" warning | Contract mapped to multiple inventory accounts | Config | 26-01079372 |

---

## 4. Customer/BA Inventory Account Setup & Accumulation (INACCTACCM)

`INACCTACCM` (Customer Account Accumulation, also surfaced as **CUSTACCTACCUM** / "Customer Account Accum Job") rolls allocated volumes + nomination/fuel into each customer/BA inventory account. It is the engine behind the **Authorization to Post Imbalances** and **Customer Account Maintenance** numbers.

### 4a. Phantom / stuck inventory record (HIGH-VALUE, has verbatim script)
**Canonical case:** APL 23-00928558 / ADO **#1632413** (Bug, *Ready for Review*). A 44 GJ balance would not clear after a **receipt location was switched from an OBA to a normal allocatable point**, leaving an orphaned row in `INTRAN_ACCT_ACTIVITY` that the monthly balance (`INTRAN_ACCT_BAL`) kept re-summing forward.

**Diagnosis:** dump the activity ledger and the balance rows for the `INV_ACCT_ID` + `ACCTG_MTH` range; find the activity row whose qty equals the stuck delta (here `floor(ALLOC_DEL_QTY)=44`) with no valid source event. **Fix:** targeted delete of the bad activity row and the affected balance rows from that accounting month forward (verbatim script in **§12 Template A**).

### 4b. Upstream-Fuel step corrupting account totals (CONFIG fix)
**Cases:** 24-00966031, 25-01008982 / ADO **#1729655** (*Closed*, "Metadata Changes for INACCTACCM Upstream Fuel Step"). A hotfix had added an **Upstream Fuel calculation step** into INACCTACCM (code `QPSUpstreamFuelCalc.cpp`). For these clients the account should accumulate **TSP fuel or nomination fuel, not upstream fuel** — the extra step inflated the Auth-to-Post Activity-tab totals and slowed billing.
**Fix (Application Configuration):** **remove the Upstream Fuel process step from the INACCTACCM job definition** (metadata change). Re-run INACCTACCM for the affected months and re-verify the Auth-to-Post totals.

### 4c. Account not auto-generating
Customer Account (INKASSIGN) and Invoice Group (BLKINVGRP) failing to auto-generate in Web — Web rewrite defect (22-00671735, 22-00671736).

### Diagnostic — see §15 (A, B). Always confirm the OPEN accounting month first.

---

## 5. Authorization to Post Imbalances Screen

This screen lets a shipper authorize which contracts' imbalances post to their inventory account. It reads the account header + the accumulated balance.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Activity-tab totals miscalculate | INACCTACCM upstream-fuel step (see §4b) | Config | 25-01008982 |
| Screen shows a contract's daily imbalances it shouldn't | Contract/account mapping or accumulation scope | Config / education | 25-01021561, 23-00921430 |
| Auto-enabled authorization | Authorization default config | Config | 23-00921430 |
| **External shipper deleted a contract** off the screen | Customer error — header row gone; downstream jobs break | **Restore-header data script** (§12 Template B) | 25-01009525, 24-00964901 |
| Missing gas-day present in measurement but not on Auth-to-Post | Accumulation lag / not yet run | Education / re-run INACCTACCM | 26-01098494 |
| Auth Ind Desc field meaning | — | Education | 25-01048337 |

> **Tell-tale:** if a shipper "deleted" a contract or the totals jumped after a fuel/hotfix change, this is a **header-restore** (data script) or an **INACCTACCM config** issue, not a screen bug.

---

## 6. Imbalance Inventory & Trading

Two surfaces: **Imbalance Trading Form** (single trade) and **Date Range Trades** (bulk). Trades move an imbalance between accounts/contracts (in-kind) or cash it out.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| Valid contract not listed in trade picklist | Screen only lists **currently active** contracts; should include any contract active when the imbalance was created. Storage contract end-dated 8/31 wasn't selectable for an 08/2025 imbalance traded in 09/2025 | Code fix; **workaround: temporarily extend contract `EFF_DT_TO`, submit trade, revert** (proven in Trade ID 5553) | 25-01044171 |
| Object Reference error opening the form; **K-Init Trdr / K-Conf Trdr fields point to tables that don't exist** (`init_inctrl_acct_hdr` / `conf_inctrl_acct_hdr`) in the client schema | Screen field-to-table mapping wrong for that environment (not reproducible in Core) | Code/config fix | 24-00942344; ADO **#1804104** (*Closed*), **#1805069** |
| Cannot confirm trade — **"Invalid Account Type Combination"** | Account-type check in the in-kind trade rules too strict | **Config: remove invalid account-type check from the detail grid** (header check was flagging valid combos) | 23-00908119 |
| Trade processable by **External** user | Permission/severity on trading rule | Code fix | 22-00671628 |
| "Imb Type-Init Trdr" auto-populates "storage" instead of long/short | Field default config | Config | 23-00907229 |
| Net Position trade validation mishandles decimals | Rounding defect | Code fix | 22-00693274 |
| Date Range Trades copy function issues | Copy defect | Code | 22-00607123 |
| Trade window status confusion | Window config | Config | 25-01009846 |

> **Cross-link:** the *billing/invoice* side of a completed cashout-trade lives in **SKILL_Billing.md**; the *allocation* that created the imbalance lives in **SKILL_Allocations.md**.

---

## 7. Storage Inventory & Date Range Storage Transfer

The **Date Range Storage Transfer** screen (Web rewrite) had a cluster of defects in 2024 (TGL). It transfers storage inventory between INIT (initial) accounts over a date range; backed by the `INTRDTRANS` process.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| Missing **Update** button on the new screen | Web screen defect | Code fix | 24-00938769 |
| Can't change **FROMINIT → TOINIT** once clicked | Web field-state defect | Code fix | 23-00935116 |
| Withdraw functionality config | Screen config | Code/config | 24-00939902 |
| Storage-capacity validation blocks transfer | Capacity validation logic; INTRDTRANS to run on schedule | Code fix | 24-00986411, 24-00939433; ADO **#1663406** (*Ready for Review*), **#1671546** |
| Storage transfer in **REJ status** still counted in storage inventory for the day | Inventory calc not filtering rejected transfers | Code/data | 22-00601085 |
| Storage Transfer Quantity shown in DTH instead of GJ | Unit config | Config | 22-00601121 |
| Storage Transfer Form disabled for Operator persona | Menu/persona config | Config | 24-00981754 |

---

## 8. Cashout (CICO) & Inventory Adjustments

**CICO** = Cash In / Cash Out (`IN_IMBALCI`), the month-end settlement of an imbalance against the inventory account.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Daily cashout produces wrong inventory (multi-client) | **CICO quantity processed incorrectly** → customer makes an **inventory adjustment** to correct | Data/adjustment | 24-00974087 |
| IN51A / IN51 double-counts the CICO quantity | Report calc defect | Code | 23-00902494, 25-01031777 |
| Inventory accumulation deadlock during ALALLOCATE | ALNEWPREPR step deadlock — **fix adds a Lock to ALNEWPREPR** | Code fix | 22-00692603 |
| Inventory Adjustment deletable in a **closed month** | Missing closed-month guard | Code fix | 22-00603617 |
| Please delete inventory adjustments | Routine ops | Data script | 24-00962035 |
| Inventory Adjustment formatting / Adjust Qty | Formatting | Software updated | 23-00906309, 22-00563728 |

> **Cross-link:** the allocation deadlock (22-00692603, ALNEWPREPR Lock) belongs to the allocation engine — see **SKILL_Allocations.md**. Listed here because it manifests as "inventory accumulation" failing.

### Inventory-adjustment ground rules
- Adjustments must be blocked in a **closed accounting month** (22-00603617). If a client needs to adjust a closed month, the month must be **re-opened** first (controlled — see measurement re-open 25-01035611 / 24-00957708).
- A "wrong inventory after cashout" is frequently corrected by the **customer's own inventory adjustment** rather than a script (24-00974087) — confirm before scripting.

---

## 9. OBA / PAL (Park-and-Loan) Balances

- **OBA** (Operational Balancing Agreement) points: switching a receipt location **OBA → allocatable** is the documented trigger for the §4a phantom inventory record (23-00928558). When you see a stuck balance, ask whether an OBA→point conversion happened.
- **OPBUYSELL** inventory account header deleted and needing restore — data-script restore (24-00964901), same restore pattern as §5.
- Meter not showing on the **OBA letter** — config (25-01056321).
- **PAL / Park-and-Loan balances** on Customer Account Maintenance — config (26-01079475); PAL allocation **one-day lag** is **expected behavior** (26-01098863); PAL2 setup is config assistance (24-00981255).
- **APAL** (Canada) changes — config + report work (24-00994856 short-term, 25-01003926 long-term).

> Park-and-loan *validation rules* on the nom side live in **SKILL_Nominations.md §5 / SKILL_Allocations.md**; here we cover the *balance* surfacing on the account/OBA screens.

---

## 10. Measurement / Meter Volumes Feeding Accounting

The **largest cluster** (35+ actionable Measurement cases). Meter/plant volumes arrive via FlowCal / eSuite / SFTP and are loaded by batch jobs that feed allocation → inventory.

### Import jobs
| Job | Purpose | Notable defects/cases |
|-----|---------|-----------------------|
| **ALESVOLIMP** | eSuite volume import into QPTM | Runs too long / exits unexpectedly → needs scripts to push data ESUITE→QPTM (25-01040593); failing (25-01002331); launched from Loc Maint screen rework (ADO #1391737) |
| **WHMEASIMP** | Wellhead measurement import + matching check | **Uses end-dated *paper* meters in the not-matching warning check, ignoring meter effective dates** — code fix (24-00992058, ADO **#1700341** *Closed*) |
| **CSUDAILOAD** | Daily meter load | Failing / not importing meter data — config (24-00986798) |
| FlowCal / SFTP feed | File delivery | SFTP not communicating / batch job not picking up files (26-01093395, 26-01090513, 26-01087490); duplicate-key on import (25-00996037) |

### Common patterns
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Measurement not (fully) coming in from FlowCal | File not delivered / job config / cycle mapping | Config / education | 25-01042776, 25-01042490, 25-01028497, 25-01036928 |
| Import failing / duplicate key | Bad/duplicate records in file | **Clear bad records from SFTP**; data script | 24-00973101, 25-00996037, 26-01096489 |
| Measurement Entry screen missing decimals / fields | Screen/decimal config | Config | 26-01080124, 25-01029383, 23-00930159 |
| Location ID picklist not populating on Hourly Measurement Maint | Picklist/code-table config | Config | 26-01094999 |
| Two meters updated to wrong numbers | Mapping config | Software updated | 24-00953611 |
| Accounting-month roll closes wrong month (no PTR check) | Roll keys off measurement not billing/PTR | Code fix | 25-01010798 |
| BTU not rounding on close-out (81 accounts) | Rounding behavior | Workaround/education | 26-01099151 |
| 'Incomplete' Accuracy status after ALESVOLIMP | Accuracy-status config | Config | 26-01091501 |

> **Cross-link:** how loaded measurement is **allocated** (gross vs allocated qty) is **SKILL_Allocations.md**. This section stops at "volumes correctly loaded for the gas day."

### Diagnostic — see §15 (E). Always check **meter effective dates** vs the gas day (the WHMEASIMP defect, 24-00992058) and whether the **production month is open**.

---

## 11. Inventory & Balancing Reports

Lower volume; usually report-config / registered-SQL / status-filter issues. **Do not treat a report total mismatch as a balance corruption until you confirm the underlying `INTRAN_ACCT_BAL` is correct.**

| Report | Issue | Fix | Case / ADO |
|--------|-------|-----|------------|
| **IN51 / IN51A** Agreement Balancing Statement | Wrong delivery/receipt/grand totals; double-counts CICO | Code | 25-01031777, 23-00902494; ADO IN51 family #1800439/#1751514 |
| **IN53** | Produced data back to Day 1 (2015) | Code fix | 22-00581585 |
| **IN62 / INX62** | Historical run / favorites issues | Code/config | 22-00586719, 22-00599352 |
| **IN40** Daily Imbalance | Missing noms on report | Education | 25-01038399 |
| **IN15** | Terminated contracts show as errors | Config / education | 24-00980629, 22-00692493 |
| **IN02** | Can't run by Production Month | Education / config | 22-00565462 |
| **IN20 / IN63 / IN18** | Decimal/header/rounding | Config | 24-00937636, 22-00607059, 22-00555537 |
| Imbalance MTD Out of Tolerance | Report failed/error | Config | 24-00941760, 23-00926100 |

---

## 12. Verbatim Fix Scripts (Redacted)

> Reconstructed from **real ADO attachments**. Concrete IDs/dates/qtys → `<PLACEHOLDER>`; **real table & column names kept**. Always run the VERIFY SELECT and eyeball the row count **before** deleting; wrap in a transaction.

### Template A — Phantom inventory record delete (Customer Account / OBA)
> **Source (verbatim):** ADO **#1632413** attachments `delete_row_INTRAN_ACCT_BAL.sql`, `delete_row_INTRAN_ACCT_BAL_dates_starting_dec19.sql`, `INTRAN_ACCT_ACTIVITY_record.sql` (APL, case 23-00928558). Use when a stuck/phantom balance survives because of an orphaned activity row (e.g. after an OBA→allocatable point switch).

```sql
-- Params: <INV_ACCT_ID>, <TSP_NO>, <ACCT_ACTIVITY_ID>, <STUCK_QTY> (e.g. 44),
--         <START_MTH> (e.g. '2019-12-01 00:00:00.000'), <END_MTH>
-- 0. VERIFY FIRST — confirm the bad activity row (note the count)
SELECT * FROM INTRAN_ACCT_ACTIVITY
WHERE  INV_ACCT_ID = <INV_ACCT_ID> AND TSP_NO = <TSP_NO>
  AND  ACCTG_MTH BETWEEN '<START_MTH>' AND '<END_MTH>'
  AND  ACCT_ACTIVITY_ID = <ACCT_ACTIVITY_ID>;

-- 1. Delete the offending balance rows (single month, or month-forward)
DELETE FROM INTRAN_ACCT_BAL
WHERE INV_ACCT_ID = <INV_ACCT_ID> AND ACCTG_MTH = '<START_MTH>' AND floor(ALLOC_DEL_QTY) = <STUCK_QTY>;
-- ...or, to clear from a month forward (the "_dates_starting" variant):
DELETE FROM INTRAN_ACCT_BAL
WHERE INV_ACCT_ID = <INV_ACCT_ID> AND ACCTG_MTH >= '<START_MTH>' AND floor(ALLOC_DEL_QTY) = <STUCK_QTY>;

-- 2. Delete the orphaned activity row that the balance kept re-summing
DELETE FROM INTRAN_ACCT_ACTIVITY WHERE ACCT_ACTIVITY_ID = <ACCT_ACTIVITY_ID>;
-- Then re-run INACCTACCM to rebuild clean balances for the affected months.
```

### Template B — Restore a deleted Auth-to-Post / inventory account header
> **Pattern (no schema dumped in SF):** cases 25-01009525 ("Script to restore the header was deployed") and 24-00964901 (OPBUYSELL header deleted, "needs to be restored"). When an external shipper deletes a contract/header off the Authorization-to-Post screen, the fix is to **re-insert the header row** from a known-good snapshot, then re-run accumulation.

```sql
-- Restore a deleted inventory-account / auth-to-post header (account-header family table).
-- Identify the exact header table for the client schema first (varies: *INCTRL_ACCT_HDR /
-- INIT_INCTRL_ACCT_HDR / CONF_INCTRL_ACCT_HDR — see Imbalance Trading Form mapping 24-00942344).
-- 0. VERIFY it is gone
SELECT * FROM <ACCT_HDR_TABLE>
WHERE TSP_NO = <TSP_NO> AND INV_ACCT_ID = <INV_ACCT_ID> AND CTR_NO = '<CTR_NO>';
-- 1. Re-insert from backup/snapshot (values from the pre-deletion record)
INSERT INTO <ACCT_HDR_TABLE> ( <columns...> ) VALUES ( <values...> );
-- 2. Re-run INACCTACCM / re-query the Authorization to Post Imbalances screen.
```

> **Provenance:** Template A text is verbatim from ADO #1632413 SQL attachments. Template B is a structural reconstruction — concrete restore INSERT is environment-specific and was a binary/PDM in SF; confirm the exact header table from the client's schema (the Imbalance Trading Form mapping case 24-00942344 names `init_inctrl_acct_hdr` / `conf_inctrl_acct_hdr`).

> **Safety:** (1) always VERIFY-SELECT first; (2) inventory deletes are keyed by `INV_ACCT_ID` + `ACCTG_MTH` (+ `ACCT_ACTIVITY_ID` for the ledger row) — don't widen the month range; (3) **re-run INACCTACCM** after any delete/restore so balances rebuild; (4) only operate in an **open** accounting month, or re-open it first; (5) wrap in `BEGIN TRAN … COMMIT/ROLLBACK`.

---

## 13. Key Code Files & Repos

### Quorum.QPTM.ClassicBatch / `QPDllPipelineMgrIN`
| File / process | Purpose |
|----------------|---------|
| `QPSUpstreamFuelCalc.cpp` | **Upstream-fuel calc step** — the step removed from INACCTACCM (§4b, 24-00966031 / ADO #1729655); client variants `QPDllPipelineMgrIN_CNP`, `_SUI` |
| `QPSProrateCuvVolumes.cpp` | Volume proration (allocation-adjacent) |

### Batch processes (job definitions / metadata)
| Process | Purpose |
|---------|---------|
| **INACCTACCM** (CUSTACCTACCUM) | Customer account accumulation → inventory balances (§4) |
| **IN_IMBALCI** | Imbalance Cash In/Cash Out (CICO) (§8) |
| **ALESVOLIMP** | eSuite measurement volume import (§10) |
| **WHMEASIMP** | Wellhead measurement import + matching (§10) |
| **CSUDAILOAD** | Daily meter load (§10) |
| **INTRDTRANS** | Storage-transfer processing behind Date Range Storage Transfer (§7) |
| **INKASSIGN / BLKINVGRP** | Customer account / invoice-group auto-gen (§4c) |
| **ALALLOCATE / ALNEWPREPR** | Allocation engine (deadlock fix 22-00692603) → **SKILL_Allocations.md** |

### Web screens (Quorum.QPTM.Web)
| Screen | Notes |
|--------|-------|
| Authorization to Post Imbalances | §5; totals driven by INACCTACCM |
| Imbalance Trading Form / Date Range Trades | §6; field maps to `init_inctrl_acct_hdr` / `conf_inctrl_acct_hdr` (24-00942344, ADO #1804104) |
| Date Range Storage Transfer (Web rewrite) | §7; ADO #1663406, #1671546 (TGL) |
| Measurement Entry / Hourly Measurement Maintenance | §10 |

> **Always check for a `<CLIENT>.QPTM.*` override** (APL, TGL, ENT, NCG, Summit) before assuming base behavior — INACCTACCM metadata and the storage/trading screens are frequently client-customized.

---

## 14. Database Tables Reference

| Table | Purpose |
|-------|---------|
| **`INTRAN_ACCT_BAL`** | **Inventory account monthly balance** (keys: `INV_ACCT_ID`, `TSP_NO`, `ACCTG_MTH`; qty cols incl. `ALLOC_DEL_QTY`). Primary table for phantom-balance diagnosis. |
| **`INTRAN_ACCT_ACTIVITY`** | **Per-event activity ledger** that accumulates into `INTRAN_ACCT_BAL` (key `ACCT_ACTIVITY_ID`). Orphan rows here cause phantom balances (#1632413). |
| `*INCTRL_ACCT_HDR` / `INIT_INCTRL_ACCT_HDR` / `CONF_INCTRL_ACCT_HDR` | Inventory-account / trade-init / trade-conf **headers** (Auth-to-Post & Imbalance Trading Form). Deleted-header restore target (§5, §12B). |
| `INTRDTRANS` (process) backing tables | Storage-transfer records (§7) |
| Measurement / meter tables (per client; fed by ALESVOLIMP/WHMEASIMP/CSUDAILOAD) | Meter volumes by gas day; watch **meter effective dates** (24-00992058) |
| `QCODE_*` code tables | Picklist sources (empty code tables → blank dropdowns, 23-00922712) |

> Exact measurement table names are client/schema-specific; confirm from the import job definition. Allocation tables (ALLOC_*) → **SKILL_Allocations.md**.

---

## 15. Diagnostic SQL Queries

### A. Inventory account balance for an account + month range
```sql
SELECT INV_ACCT_ID, TSP_NO, ACCTG_MTH, ALLOC_REC_QTY, ALLOC_DEL_QTY,
       IMBAL_QTY, BEG_BAL_QTY, END_BAL_QTY
FROM   INTRAN_ACCT_BAL
WHERE  INV_ACCT_ID = <INV_ACCT_ID> AND TSP_NO = <TSP_NO>
  AND  ACCTG_MTH BETWEEN '<START_MTH>' AND '<END_MTH>'
ORDER BY ACCTG_MTH;
```

### B. Activity ledger (find the orphan / phantom row)
```sql
SELECT ACCT_ACTIVITY_ID, INV_ACCT_ID, TSP_NO, ACCTG_MTH,
       ALLOC_REC_QTY, ALLOC_DEL_QTY, ACTIVITY_TYPE_CD, SRC_CD, CTR_NO
FROM   INTRAN_ACCT_ACTIVITY
WHERE  INV_ACCT_ID = <INV_ACCT_ID> AND TSP_NO = <TSP_NO>
  AND  ACCTG_MTH BETWEEN '<START_MTH>' AND '<END_MTH>'
ORDER BY ACCTG_MTH, ACCT_ACTIVITY_ID;
-- Red flag: an activity row whose qty equals the stuck balance delta with no valid source event.
```

### C. Account header presence (deleted-header check, §5/§12B)
```sql
SELECT * FROM <ACCT_HDR_TABLE>   -- *INCTRL_ACCT_HDR / INIT_ / CONF_ per schema
WHERE TSP_NO = <TSP_NO> AND INV_ACCT_ID = <INV_ACCT_ID>;
```

### D. Contract effective dates vs imbalance period (trading-picklist issue, §6)
```sql
SELECT CTR_NO, TOS_CD, EFF_DT_FROM, EFF_DT_TO, IS_ACTIVE
FROM   NNCTRL_CTR
WHERE  TSP_NO = <TSP_NO> AND CTR_NO = '<CTR_NO>';
-- If EFF_DT_TO < the imbalance production month, the contract won't appear in the trade picklist (25-01044171).
```

### E. Measurement / meter volume by gas day (import validation, §10)
```sql
-- Confirm meter effective dates around the gas day (WHMEASIMP defect 24-00992058)
SELECT METER_ID, EFF_DT_FROM, EFF_DT_TO, IS_PAPER_METER, IS_ACTIVE
FROM   <METER_TABLE>
WHERE  TSP_NO = <TSP_NO> AND METER_ID = '<METER_ID>';
-- Loaded volume by gas day:
SELECT METER_ID, GAS_DAY, MEAS_QTY, ENERGY_QTY, ACCURACY_STATUS_CD, PROD_MTH
FROM   <MEAS_VOL_TABLE>
WHERE  TSP_NO = <TSP_NO> AND METER_ID = '<METER_ID>'
  AND  GAS_DAY BETWEEN '<BEG>' AND '<END>'
ORDER BY GAS_DAY;
```

### F. Accounting / production month open status (before any adjustment/delete)
```sql
SELECT TSP_NO, ACCTG_MTH, MTH_STATUS_CD, MEAS_STATUS_CD, BILL_STATUS_CD
FROM   <ACCTG_PERIOD_TABLE>
WHERE  TSP_NO = <TSP_NO> AND ACCTG_MTH = '<ACCTG_MTH>';
-- Never delete/adjust in a CLOSED month — re-open first (25-01035611, 24-00957708).
```

---

## 16. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1632413** | Bug / **Ready for Review** | APL — Auth to Post Imbalance — long-outstanding 44 GJ **phantom** record (has delete SQL attachments) | §4a/§5 | 23-00928558 |
| **#1729655** | Bug / **Closed** | Metadata changes for **INACCTACCM Upstream-Fuel step** (Summit) | §4b | 25-01012810 / 24-00966031 / 25-01008982 |
| **#1663406** | Bug / **Ready for Review** | TGL — Date Range Storage Transfer storage-capacity validation; INTRDTRANS on schedule | §7 | 24-00939433 |
| #1671546 | Task / **Active** | TGL — Date Range Storage Transfer HLE additional changes | §7 | — |
| **#1804104** | Bug / **Closed** | NCG — Object Reference error opening Imbalance Trading Form | §6 | 26-01095983 |
| #1805069 | Task / **Closed** | DEV — NCG Imbalance Trading Form object-reference fix | §6 | 26-01095983 |
| **#1700341** | Bug / **Closed** | ENT/TIPS — WHMEASIMP energy comparison on **non-paper / end-dated** meters | §10 | 24-00992058 |
| #1391737 | Requirement / **Closed** | ALESVOLIMP launch-from-Loc-Maint rework (TECO) | §10 | — |

> Takeaway: the two "code root cause" anchors are **#1729655** (INACCTACCM upstream-fuel — a *config/metadata* fix) and **#1632413** (phantom inventory — a *data script*). Most inventory cases are dispositioned as **Application Configuration** (remove a step, fix a mapping, extend a contract date) or a **targeted data script**, not a single product fix.

---

## 17. Expected Behavior / User Education

| Reported as | Reality | Case |
|-------------|---------|------|
| "PAL allocation is a day behind" | PAL allocation **one-day lag** is by design | 26-01098863 |
| "Contract not selectable for an imbalance trade" | Contract was end-dated before the trade window; **extend EFF_DT_TO** as workaround (real fix is the picklist defect) | 25-01044171 |
| "Auth-to-Post is missing a gas day that's in measurement" | INACCTACCM hasn't accumulated it yet — re-run / wait | 26-01098494 |
| "Terminated contracts show as errors on IN15" | Expected — terminated contracts surface; filter the report | 24-00980629 |
| "Can't run IN02 by Production Month" | Report runs by accounting period by design | 22-00565462 |
| "Wrong inventory after cashout" | CICO processed a qty the *customer* must adjust — not always a defect | 24-00974087 |
| "Associated to more than one Inventory Account" warning | Contract mapped to multiple accounts — review the mapping config | 26-01079372 |
| "FSS storage MDIQ/MDWQ not on the nom screen" | By design (see SKILL_Nominations §14) | 26-01102716 |
| BTU not rounding on close-out | Rounding behavior / expected | 26-01099151 |

**Tell-tales it's user/expected:** a contract was deliberately end-dated; the period hasn't accumulated yet; the "wrong" total is a correctly-firing report filter; or the customer changed their own setup (deleted a contract off Auth-to-Post, 25-01009525 → Customer Error).

---

## 18. Escalation Decision Tree

```
Customer-Account / Inventory / Measurement case
│
├─ Stuck / "phantom" inventory balance that won't clear?  (§4a)
│   ├─ Did a receipt point switch OBA→allocatable?  → likely orphaned INTRAN_ACCT_ACTIVITY row
│   ├─ Run §15 A+B → find the activity row matching the stuck delta
│   └─ Confirmed orphan? → §12 Template A delete script to Cloud Ops, then RE-RUN INACCTACCM
│
├─ Auth-to-Post totals wrong / billing slow after a fuel hotfix?  (§4b/§5)
│   └─ Check INACCTACCM job for an Upstream-Fuel step → remove it (config, ADO #1729655); re-run
│
├─ Contract deleted off Auth-to-Post / header missing?  (§5)
│   └─ Customer Error → §12 Template B restore header; confirm exact header table
│
├─ Imbalance Trading Form: picklist / object-ref / can't confirm?  (§6)
│   ├─ Contract not in picklist → extend EFF_DT_TO workaround (25-01044171)
│   ├─ Object Reference / field-to-table → code/config (#1804104)
│   └─ "Invalid Account Type Combination" → remove the account-type check (config, 23-00908119)
│
├─ Date Range Storage Transfer screen broken (button/field/withdraw/capacity)?  (§7)
│   └─ Web rewrite defect → code fix (ADO #1663406); check REJ-status inventory inclusion
│
├─ Cashout / inventory wrong, or adjustment in closed month?  (§8)
│   ├─ Re-open the month first if closed; CICO qty often a customer adjustment, not a defect
│   └─ Accumulation deadlock? → ALNEWPREPR Lock → SKILL_Allocations.md
│
├─ Measurement not coming in / load failing?  (§10)
│   ├─ Which job? ALESVOLIMP / WHMEASIMP / CSUDAILOAD → check job log, SFTP path, file format
│   ├─ "Not matching" warning? → verify meter EFFECTIVE DATES (WHMEASIMP #1700341)
│   └─ Duplicate-key on import → clear bad records from SFTP (data)
│
├─ Report total wrong (IN51/IN53/IN62/IN40/IN15/IN02)?  (§11)
│   └─ Verify INTRAN_ACCT_BAL is correct FIRST; then report registered-SQL / status filter
│
├─ Allocation gross-vs-alloc / proration?  →  SEE SKILL_Allocations.md
└─ Imbalance → invoice / cashout billing output?  →  SEE SKILL_Billing.md
```

---

*Skill created: 2026-06-01*
*Based on: ~176 actionable QPTM Customer-Accounts/Inventory/Pipeline-Inventory/Measurement SF cases + ADO #1632413, #1729655, #1663406, #1671546, #1804104, #1805069, #1700341, #1391737. Verbatim SQL from ADO #1632413 attachments.*
*Companions: SKILL_Allocations.md, SKILL_Billing.md, SKILL_Contracts.md, SKILL_Nominations.md, SKILL_Security_UserAdmin.md. Applicable to all QPTM TSPs/clients.*
