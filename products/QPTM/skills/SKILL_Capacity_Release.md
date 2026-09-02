# SKILL: QPTM Capacity Release Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** FERC secondary-capacity-market workflow — Offer creation/posting, Bid submission (incl. prearranged), Award/evaluation, Recall/Reput, replacement-contract generation, IPWS / informational-postings (EBB) publication, seasonal/permanent/segmented release, CR rates (max-tariff/index), CR validation rules (`RuleCROF*`), CR reports.
**Companion:** For the replacement/releasing *contract* mechanics that overlap with general contract setup see **SKILL_Contracts.md**; for noms placed on replacement contracts see **SKILL_Nominations.md**. Do not duplicate those — cross-references noted below.

> Evidence base: ~430 closed QPTM Capacity Release cases (`Case_Category__c IN ('Capacity Release','Capacity Release (CR)')`). Actionable root causes: **Software Defect 71, Application Configuration 36, Training 32, Customer Error 17.** Every root-cause claim cites a real SF case number and/or ADO work item.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Capacity Release Concepts & Workflow](#2-capacity-release-concepts--workflow)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Offer Creation & Submission (HIGH FREQUENCY)](#4-offer-creation--submission-high-frequency)
5. [Bid / Award / Prearranged](#5-bid--award--prearranged)
6. [Recall / Reput / Withdraw](#6-recall--reput--withdraw)
7. [IPWS / Informational Postings (EBB)](#7-ipws--informational-postings-ebb)
8. [Seasonal / Permanent / Segmented Release](#8-seasonal--permanent--segmented-release)
9. [Replacement Contracts, Rates & Invoicing](#9-replacement-contracts-rates--invoicing)
10. [CR Validation Rules (RuleCROF*)](#10-cr-validation-rules-rulecrof)
11. [CR Reports](#11-cr-reports)
12. [Expected Behavior / User Education](#12-expected-behavior--user-education)
13. [Key Code Files & Repos](#13-key-code-files--repos)
14. [Database Tables Reference](#14-database-tables-reference)
15. [Diagnostic SQL Queries](#15-diagnostic-sql-queries)
16. [Known Historical ADO Bugs](#16-known-historical-ado-bugs)
17. [Escalation Decision Tree](#17-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. Which CR phase failed — Offer, Bid, Award, Recall/Reput, or IPWS posting?
[ ] 2. What is the EXACT error/message or Rule code? (e.g., RuleCROF000250, RuleCROF001570, RuleCROF000150, "Value cannot be null")
[ ] 3. The Offer # / Bid # / Award # involved? (clients almost always supply this — e.g., "Offer 6368", "Offer 266/267/268")
[ ] 4. Which TSP and Releasing K# (releasing contract)? Replacement K# if past award?
[ ] 5. Release type: Biddable vs Non-biddable; Temp vs Permanent; AMA; Segmented; Seasonal-dated?
[ ] 6. Web (Offer Wizard) or Classic (Citrix/PipelineMgrCR)? Several bugs are Web-only or Classic-only.
[ ] 7. Internal (TSP) or External (releasing/replacement shipper / CommPass) user?
[ ] 8. Is there a posting/bid/award deadline on the case? (CR cases are often CRITICAL & deadline-boxed)
[ ] 9. Is it failing to publish to IPWS / your EBB (informational posting)?
[ ] 10. QPTM version (e.g., 2022.04, 2023.04, 2024.04, 2024.10, 2025.10) — many CR fixes are version-gated/hotfixed.
```

### Where does the issue live?
| Entry point | Likely cluster | First place to look |
|-------------|----------------|---------------------|
| Offer Wizard won't submit / field blank / "Value cannot be null" | §4 Offer | `CRCTRL_OFFER_HDR/_DTL`; rate resolution; RuleCROF* |
| Bid won't submit / prearranged bid errors | §5 Bid/Award | `CRCTRL_BID_HDR/_DTL`; bid status |
| Award wrong / over-allocated / 2nd-place bid awarded | §5 Award | `CRCTRL_AWARD_HDR/_DTL`, `CRCTRL_AWARD_AMEND` |
| Can't recall/reput; stuck recall record | §6 Recall | `CRCTRL_RECALL_REPUT` |
| Offer/award not on IPW(S) / duplicate rows in IPWS | §7 IPWS | `QPSCapRelTransRpt` / `CWCAPRTRAN_*.XML` |
| Seasonal/permanent release dates wrong | §8 Seasonal | `USE_SEASNL_DATES`, RuleCROF000250 |
| Replacement K missing from invoice / wrong rate | §9 Contracts/Rates | TOS attrs, Rate Resolution batch |
| Validation blocking offer/bid | §10 Rules | `RuleCROF*` in `Quorum.QPTM.Validations.Rules.CapacityRelease` |

---

## 2. Capacity Release Concepts & Workflow

Capacity Release is the **FERC-regulated secondary market** where a firm shipper (the **releasing shipper**, holding the **Releasing K#**) temporarily or permanently releases capacity to an **acquiring/replacement shipper** (gets a **Replacement K#**). QPTM models the lifecycle as:

```
OFFER  --(post to IPWS/EBB)-->  BID window  -->  AWARD/evaluation  -->  Replacement Contract generated
   \                                                                          |
    \--- Recall / Reput (releaser pulls capacity back / re-releases) <--------/
```

### Lifecycle objects & tables
| Phase | Object | Primary table(s) |
|-------|--------|------------------|
| Offer | Header + detail + text + disc-rate + timeline | `CRCTRL_OFFER_HDR`, `CRCTRL_OFFER_DTL`, `CRCTRL_OFFER_TEXT`, `CRCTRL_OFFER_DISC_RATE` |
| Bid | Header + detail (incl. prearranged) | `CRCTRL_BID_HDR`, `CRCTRL_BID_DTL` |
| Award | Header + detail + amendment | `CRCTRL_AWARD_HDR`, `CRCTRL_AWARD_DTL`, `CRCTRL_AWARD_AMEND` |
| Recall/Reput | Recall/reput record | `CRCTRL_RECALL_REPUT` |
| History | Historical offer/bid/timeline | `CRHIST_*` (e.g., hist offer hdr, hist bid hdr/dtl, hist timeline) |

### Key terms
- **Biddable vs Non-biddable** — biddable offers go to a bid window & competitive evaluation; non-biddable (incl. **prearranged**) go straight to a known taker.
- **Prearranged deal** — releaser & taker pre-agree; a prearranged **bid** is matched to the offer (RuleCROF & rate-form/type rules apply — §5).
- **ROFR** (Right Of First Refusal) — existing shipper's right to match a competing bid.
- **Recall / Reput** — releaser recalls released capacity (and may *reput* it back).
- **AMA** (Asset Management Arrangement) — a permanent-release flavor (cases 25-01035262, 22-00607999).
- **IPWS / IPW / EBB** — Informational Postings / Electronic Bulletin Board where offers/awards must publish (FERC posting obligation). QPTM emits a transactional file `CWCAPRTRAN_*.XML` via the CR transactional-report batch.
- **Seasonal dates** — release detail can carry seasonal start/end dates; behavior gated by config `USE_SEASNL_DATES` (§8).
- **Releasing K# / Replacement K#** — the source contract and the generated acquirer contract.

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| Offer Wizard "Value cannot be null" on save/submit | Max-Tariff rate not resolved (Rate Resolution batch not run) | Config (run Rate Resolution batch) | 24-00953290, 22-00609196 |
| Releasing K# picklist empty / can't choose Rel K | Offer-screen picklist defect; Rel K must be set on **Details** tab | Code fix / Training | 22-00807710, 22-00620254, **22-00807721 (user-error: enter Rel K on Details tab)** |
| Permanent release read-only field not populating in Web | Web offer-workflow defect (fixed 2022.10; hotfixed to 2022.04) | Code fix | 23-00883871, 23-00885105 |
| Seasonal dates wrong on replacement contract / RuleCROF000250 blocks | Seasonal-date logic when `USE_SEASNL_DATES=false` set dates wrong | Code fix + config | 24-00990888, 24-00991839, 25-01050402, 26-01080121 |
| Award accepts total biddable qty > Max offer qty; full qty not split among acceptable bids | Award/evaluation allocation defect | Code fix | 23-00907781 (#1612026), 25-01005999, 25-01049577 |
| Offer/Award not posting to IPWS / IPW | Release start date > gas day + offset (expected) **or** posting/TOC-object defect | Config/Training or Code | 25-01042897 (expected), 25-01047150 (#1759366), 26-01081035 |
| Duplicate CR rows in IPWS / transactional reporting duplicating each run | IPWS transactional-report dedup defect | Code fix | 25-01047872, 25-01018583 (#1739076), 1727477 |
| Stuck/incorrect Recall record; cancelled-recall leftover AWARD_AMEND_IDs | Recall process left orphan rows | PDM / data script | 22-00661770, 22-00661775, 22-00875593 |
| LCL on releasing contract not adjusted during release | Missing batch step | Code fix (new `CRKLCLGEN` step) | 23-00925472 |
| NETMDQRES does not update CR receipt MDQs | MDQ-update batch defect for CR contracts | Code fix | 24-00956219 (#1663622), 24-00956689 (#1664390) |
| Replacement contracts missing from invoice | TOS attribute / invoice-group config | Config / Training | 24-00973063, 24-00992572 |
| Index-based CR not allowed on FT-1 / index offers | Core requirement / TOS attribute | Code (requirement) | 23-00900447 (#1612026), 1791163 |
| Copy Offer succeeds with past start date / details not copying forward | Copy-offer defects | Code fix | 24-00972809, 23-00928893, 23-00911973 |
| Recalled offer shows incorrect award time; cycle question | Display/timezone or expected cycle behavior | Training | 26-01067976, 25-01016858, 23-00905294 |

---

## 4. Offer Creation & Submission (HIGH FREQUENCY)

The **single largest cluster** (~58 actionable cases). Offers are built in the **Offer Wizard** (Web) or the Classic PipelineMgrCR screens, written to `CRCTRL_OFFER_HDR` + `CRCTRL_OFFER_DTL` (+ `_TEXT`, `_DISC_RATE`, `_TIMELINE`), and validated by the `RuleCROF*` rule set (§10) before posting to IPWS (§7).

### Top failure modes & fixes
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| "Value cannot be null" submitting offer | Max-Tariff rate unresolved | **Run the Rate Resolution batch separately** to tie in Max Tariff Rate, then resubmit | 24-00953290 |
| Max Tariff rate not auto-populating (Citrix) | Rate-resolution/auto-populate defect | Code fix / run rate resolution | 22-00609196, 24-00994097 |
| Contract numbers not populating when creating offer | Rel-K picklist data/config | Config | 24-00945385 |
| Can't choose Releasing K / Rel K picklist failing | Picklist defect (Web/Classic) | Code fix; **on Copy Existing, Rel K MUST be entered on the Details tab or the copy saves invalid** | 22-00620254, 22-00807710, 22-00807721 |
| Permanent release: read-only field not populating, blocks creation | Web offer-workflow defect | Fixed 2022.10, hotfixed to 2022.04 | 23-00883871, 23-00885105 |
| Permanent Capacity Release as AMA — error prevents offer creation | Core validation on AMA permanent release | Workaround / core fix | 25-01035262 (#1760280) |
| Copy Offer allows past start date; "Offer Details not copying forward" | Copy-offer defects | Code fix | 24-00972809, 23-00928893 |
| Unable to add Virtual Locations to offer | Offer-location defect | Hotfix deployed | 25-01047874 |
| Offer failing to submit for contract with 'CAP' attr | Contract-attribute handling | Config | 23-00920460 |
| Unable to create index-based CR on FT-1 contract | Index-based CR requirement / TOS attr | Core requirement | 23-00900447 (#1612026) |
| >200 detail records can't submit; mass-edit blocked by Loc/QTI Desc | Offer detail-grid limits | Code fix | 22-00630735, 22-00630733, 22-00630736 |
| Discount Indicator / Offer Wizard option wrong; Recall/Reput tab defaults | Offer Wizard config | Config | 25-01011770, 23-00891159, 23-00911630 |
| Offer screen showing 1's instead of Yes; UOM format wrong in Web | Display/format config | Config | 23-00931083, 23-00928887 |

### Diagnostic
```sql
-- Pull the offer header + detail the client referenced by Offer #
SELECT OFFER_ID, TSP_NO, REL_CTR_NO, OFFER_STAT_CD, IS_BIDDABLE, IS_PERMANENT,
       REL_BEG_DT, REL_END_DT, POST_DT, MAX_TARIFF_RATE, REL_RATE, CRT_DT, UPDT_DT
FROM CRCTRL_OFFER_HDR
WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>;

SELECT OFFER_ID, OFFER_DTL_SEQ_NO, REC_LOC_ID, DEL_LOC_ID, BID_QTY_LOC,
       SEASNL_START_DT, SEASNL_END_DT, MAX_TARIFF_RATE, REL_RATE, DISC_IND
FROM CRCTRL_OFFER_DTL
WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>
ORDER BY OFFER_DTL_SEQ_NO;
```
> If "Value cannot be null" — check `MAX_TARIFF_RATE` is populated on `_DTL`; if NULL, the **Rate Resolution batch** hasn't tied in the max tariff (24-00953290).

---

## 5. Bid / Award / Prearranged

Bids land in `CRCTRL_BID_HDR/_DTL`; awards in `CRCTRL_AWARD_HDR/_DTL` with amendments in `CRCTRL_AWARD_AMEND`. Two recurring themes: **prearranged-bid field/visibility defects**, and **award allocation/quantity** defects.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Award accepts total biddable qty **greater than** Max offer qty | Award qty-validation defect | Core requirement | 23-00907781 → **ADO #1612026** |
| **Full offer qty not awarded among multiple acceptable bids** (2nd-place bid got full qty on Ruby) | Award allocation defect | Script to fix data now; long-term fix tracked | 25-01049577 + 25-01063069 (data); **25-01005999 (long-term)** |
| Prearranged bid: Rate Form/Type Desc flips Volumetric↔Reservation | Bid rate-form defect | Code fix | 22-00630768, 22-00630737 |
| Releaser phone # not auto-populating → prearranged bid errors | Auto-populate defect | Config | 23-00906945 |
| External users can't view / bids unavailable for prearranged bidder | Visibility/security defect | Code fix | 22-00609367, 22-00569499, 23-00904384 |
| "% Max Tariff requires different numbers on offer vs prearranged bid" | Rate-percent handling | Code fix | 22-00630757 |
| Could not match a competitive bid for offer | Bid-matching defect | Code fix | 22-00630762 |
| Awarding a Storage Release offer failed with SQL errors | Storage-award defect | Code fix | 24-00971144 |
| Heat factors / Rate Form-Type missing after Award (CommPass) | Post-award data defect | Code fix | 22-00591416, 22-00630737 |
| Inconsistent data on Query Existing Bid screen (Web) | Web bid-query display defect | Code fix | 24-00993525 |

### Diagnostic
```sql
-- Bids for an offer
SELECT BID_ID, OFFER_ID, BID_STAT_CD, IS_PREARRANGED, ACQ_BA_NO,
       BID_RATE, RATE_FORM_TYPE_CD, BID_QTY, CRT_DT
FROM CRCTRL_BID_HDR
WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>
ORDER BY BID_ID;

-- Award + amendments for an offer (look for over-allocation / wrong bid awarded)
SELECT a.AWARD_ID, a.OFFER_ID, a.BID_ID, a.AWARD_QTY, a.AWARD_STAT_CD,
       am.AWARD_AMEND_ID, am.AMEND_TYPE_CD, am.UPDT_DT
FROM CRCTRL_AWARD_HDR a
LEFT JOIN CRCTRL_AWARD_AMEND am ON a.TSP_NO = am.TSP_NO AND a.AWARD_ID = am.AWARD_ID
WHERE a.TSP_NO = <TSP_NO> AND a.OFFER_ID = <OFFER_ID>;
```

> **Ruby (offers 266/267/268) playbook:** when an award allocates incorrectly across multiple acceptable bids, L4 deploys a **targeted data script** to correct the award rows (25-01049577, 25-01063069) while the product fix is tracked under 25-01005999. Confirm the intended winning bid(s) and qty split with the client before scripting.

---

## 6. Recall / Reput / Withdraw

The releaser pulls back released capacity (recall) and may re-release (reput). State lives in `CRCTRL_RECALL_REPUT`. Recurring problem: **orphaned/incorrect recall records** left after a cancelled or retroactive recall, which then block further action.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Need to delete a stuck Capacity Release Recall record | Orphan recall row | **PDM/script deleting from `CRCTRL_RECALL_REPUT`** | 22-00661770 |
| Cancelled-recall left bad `AWARD_AMEND_ID`s | User-cancelled recall process leftover | PDM to clear the bad recall/amend rows | 22-00661775 |
| Orphan contract locations after CR recall | Recall left orphan contract-loc rows | Data script to delete orphan contract records | 22-00875593 |
| Recall/Reput/Withdraw — deks missing from releasing & replacement K | Qty mismatch on recall | Config | 22-00638277 |
| Can't recall/reput via Web | Web recall defect | Code fix | 22-00630744 |
| External recall notifications not sent (CAPRELK / replacement shippers) | Notification defect | Code fix | 22-00666837, 22-00588162 |
| Unsubscribed capacity in IPWS wrong after recall | IPWS recall-qty defect | Data script | 23-00905758 |
| Recall capacity "not available" | Recall-availability defect | Workaround | 22-00569498 |

### Diagnostic & fix (verbatim PDM pattern from case 22-00661770)
```sql
-- VERIFY the recall/reput row(s) before any delete (confirm you target the bad record)
SELECT *
FROM   CRCTRL_RECALL_REPUT
WHERE  REPL_SR_CTR_NO = <REPLACEMENT_CTR_NO>
  AND  CR_STATUS_CD   = '<STATUS>'      -- e.g. 'RC' (recalled)
  AND  UPDT_DT        = '<UPDT_DT>';    -- pin the exact row by its update timestamp

-- DELETE (deployed as a PDM / Cloud Ops script after the count is confirmed)
DELETE FROM CRCTRL_RECALL_REPUT
WHERE  REPL_SR_CTR_NO = <REPLACEMENT_CTR_NO>
  AND  CR_STATUS_CD   = '<STATUS>'
  AND  UPDT_DT        = '<UPDT_DT>';
```
> **Provenance:** the `WHERE REPL_SR_CTR_NO = … AND CR_STATUS_CD = 'RC' AND UPDT_DT = …` predicate is taken **verbatim** from the PDM described in case 22-00661770 (concrete contract #/timestamp redacted to `<PLACEHOLDER>`). For cancelled-recall amend cleanup (22-00661775) the PDM clears the corresponding bad `AWARD_AMEND_ID`s in `CRCTRL_AWARD_AMEND`. Always pin by `UPDT_DT`/ID so you delete exactly one bad row, and wrap in a transaction.

---

## 7. IPWS / Informational Postings (EBB)

FERC requires offers/awards to publish to the pipeline's Informational Postings (IPWS / IPW / EBB). QPTM emits a **transactional posting file `CWCAPRTRAN_<date>_<time>.XML`** via the CR transactional-report batch (`QPSCapRelTransRpt.cpp`, the `PipelineMgrCW` / "CW" report family). This is a high-recency cluster (2025-2026).

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| Offer/Release **not posting** to IPW | **Release start date > gas day (or gas-day offset)** → offer correctly excluded | **Expected** — educate | 25-01042897 (Training) |
| Capacity Release #43 not posting to IPWS | Posting defect | Workaround + secondary case for the offer issue | 25-01047150 → **#1759366** |
| **Duplicate** CR rows in IPWS | Transactional-report dedup defect | Code fix | 25-01047872; HPE 25-01018583 → **#1739076** |
| Transactional Reporting in folder but not showing on IPW; TOC-Object Association setup bad | IPWS TOC-object config/defect | Code/config | PNG #1727472, IPWS #1727477 |
| 2025.10 transactional posting issues | Release-item regression | Software update | 26-01098608, HPE #1806705 |
| CR offer notice posting question | Posting-config / notice setup | Workaround / Training | 26-01081035, 25-01051327 |

### Diagnostic
- Pull the latest `CWCAPRTRAN_*.XML` from the IPWS output folder and confirm the offer/award row is present and not duplicated.
- If **missing**, first check the **release start date vs gas day + offset** before assuming a defect (25-01042897 was expected behavior).
- If **duplicated**, suspect the transactional-report dedup defect (#1739076 / 25-01047872) — check whether the report was re-run.
- Verify the **TOC-Object Association** setup for the CR transactional report object (#1727477) if rows land in the folder but don't show on the IPW.

---

## 8. Seasonal / Permanent / Segmented Release

Special release flavors with their own date/validation logic.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| **Seasonal dates wrong on replacement contract** | When `USE_SEASNL_DATES=false`, seasonal start/end weren't forced to the Release Start/End dates | **Code: set Seasonal Dates = Release Start/End when `USE_SEASNL_DATES` is false** | 24-00990888, **24-00991839 (RCA)**, 25-01050402 |
| `RuleCROF000250` blocks offer (seasonal start/end ≠ release start/end) | Seasonal-date validation firing | Rule deactivated so process could run (interim) | **26-01080121** |
| Permanent release field not populating (Web) | Web offer-workflow defect | Fixed 2022.10, hotfixed 2022.04 | 23-00883871, 23-00885105 |
| Permanent CR as AMA — error prevents offer creation | AMA permanent-release validation | Workaround / core fix | 25-01035262 (#1760280) |
| Permanent release on REX auto-approved | Approval-config defect | Config | 22-00638167 |
| Prem release offer over a year validation | Term validation | Config (HF) | 24-00945655 |
| Segmented Release scenario design/setup | Setup/config | Config | 23-00933278 |

> **RuleCROF000250** (source: `Quorum.QPTM.Validations.Rules.CapacityRelease/Offers/RuleCROF000250.cs`): *"when using seasonal Dates, the Seasonal Start and End Date must be equal to the Release Start and End Date."* It iterates `context.OfferHeader.CROfferDetail` and compares `SeasnlStartDate`/`SeasnlEndDate` to the release range. It only fires when `context.UsingSeasonalDates` is true — i.e. it's driven by the `USE_SEASNL_DATES` config. The RCA (24-00991839) fixed the underlying date-set logic; case 26-01080121 worked around a stuck offer by **temporarily deactivating the rule**.

### Diagnostic
```sql
-- Is USE_SEASNL_DATES on, and do offer-detail seasonal dates match the release range?
SELECT OFFER_DTL_SEQ_NO, SEASNL_START_DT, SEASNL_END_DT, REL_BEG_DT, REL_END_DT
FROM CRCTRL_OFFER_DTL
WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>;
-- Compare to the global/TSP config value of USE_SEASNL_DATES (QARCH_GLOBAL_CONFIG / TSP config).
```

---

## 9. Replacement Contracts, Rates & Invoicing

After award, QPTM generates the **Replacement K#** and must carry rates/charges through to billing. (For general contract setup see SKILL_Contracts.md.)

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Replacement contracts (RF) **missing from invoice** | TOS attribute config: RF TOS using "Bill on Contract MDQ" attrs | **Set RF TOS to NOT use Bill-on-Contract-MDQ-level attrs; remove Bill-MDQ-on-Contract-Level attr; switch RF TOS to MDQR charge basis** | 24-00973063 |
| Capacity Releases missing from invoices | Replacement K not in an invoice group | **Add replacement (RFS) contracts to an invoice group** | 24-00992572 |
| Volumetric charge needs adding to replacement contracts | Charge-config | Config | 24-00978815 |
| RF TOS "Index of Customers" attribute setup | TOS-attr config | Config | 24-00967842 |
| Max-tariff rate not loading / "Value cannot be null" | Rate Resolution batch not run | Run Rate Resolution | 24-00994097, 24-00953290 |
| LCL on releasing contract impacted/not adjusted during release | Missing batch step | New batch step **`CRKLCLGEN`** to check/adjust LCL qty during release | 23-00925472 |
| NETMDQRES does not update CR receipt MDQs / contract MDQs | MDQ-update batch defect for CR contracts | Code fix | 24-00956219 (#1663622), 24-00956689 (#1664390), 24-00956762 (#1670588) |
| Unsold Capacity configuration issues | Unsold-capacity config | Code fix | 22-00824870 |
| Available Capacity not reflecting offers; calculating incorrectly for overlapping offers | Available-cap calc defect | Code fix | 24-00986294, EQT #1696946 |

---

## 10. CR Validation Rules (RuleCROF*)

CR offer validations live in **`Quorum.QPTM.Validations.Rules.CapacityRelease/Offers/RuleCROF######.cs`** (≈159 rules, `RuleCROF000010`–`RuleCROF001590`), driven by `QCROfferValidationContext` / `QCROfferValidationContainer` and the base `QOfferValidationBase`. Rules are configured/cross-referenced like other QPTM validations (`QARCH_VALD_RULE`, and the metadata `QARCH_CTRL_OBJECT_*` JSON).

| Rule | What it checks | Case |
|------|----------------|------|
| **RuleCROF000150** | Offer error-indicator validation | 22-00565468 (WWM) |
| **RuleCROF000250** | Seasonal start/end must equal release start/end (when using seasonal dates) | 24-00990888, 26-01080121 |
| **RuleCROF001570** | Surcharge ID Description required on offer | 22-00666957, 23-00883833 |

### Investigation
1. Get the **exact RuleCROF code** from the screen error.
2. Find the rule file: code search `{"searchText":"RuleCROF000250"}` → `.../Offers/RuleCROF000250.cs`; read its `Validate(QCROfferValidationContext)` to see the precise condition.
3. Check whether the rule is **correctly firing** (bad/missing offer data = Training/Config) vs a **defect** (rule firing on valid data).
4. Confirm whether the client has a **`<CLIENT>.QPTM.Web` override** of the rule before assuming base behavior (e.g., TEP).
5. As an **interim unblock** only, the rule can be deactivated (26-01080121 did this for RuleCROF000250) — but fix the underlying data/config.

---

## 11. CR Reports

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Transactional Reporting duplicating CR data every run | Report dedup defect | Code fix | 25-01018583 (#1739076) |
| Negotiated Rate Summary Report (CRO7) issue | Report defect | Non-software | 22-00661826 |
| RPT_CAX15 Scheduled Quantity report broken | Report defect | Code fix | 22-00813523 |
| Award Download for an offer needs fixing | Award-download/data | Data script | 24-00943432 |
| Pre-report process for CR generic award/bid/offer | `QPSPreReportProcessCRGenericAward/Bid/Offer.cpp` (ClassicBatch RPT) | — | (code reference) |

---

## 12. Expected Behavior / User Education

Root Cause = **Training / Customer Error** (~49 cases). Recognize these to avoid unnecessary scripts/escalations.

| Reported as | Reality | Case |
|-------------|---------|------|
| "Offer not posting to IPW" | Release start date > gas day (+ offset) → correctly excluded | 25-01042897 |
| "Required fields on offer not saving" (Copy Existing) | On **Copy Existing**, the **Rel K# must be entered on the Details tab** or the copy saves invalid | 22-00807721 |
| "RuleCROF001570 Surcharge ID Description Required" | Validation correctly requiring the surcharge description | 22-00666957, 23-00883833 |
| "Recalled offer has incorrect award time" | Cycle/time displayed as designed | 26-01067976, 23-00905294 |
| "Capacity Releases missing from invoices" | Replacement (RFS) contracts not added to an invoice group | 24-00992572 |
| "CommPass pulling wrong amendment" | Amendment-selection question, not a defect | 26-01080112 |
| "Double Bid" | Working as designed / user workflow question | 23-00898705 |
| "Need to set up CR notice/notification" | Provide notification setup documentation | 25-01051327, 24-00970475 |
| Permanent CR / AMA "how do I" | Provide steps/scoped-screen docs | 22-00638276, 22-00607999, 22-00601779 |

**Tell-tale that it's user/expected:** the offer was correctly excluded from posting due to date logic; a required field (surcharge desc, Rel K on Details tab) was genuinely missing; or the client copied an offer without completing the Details tab.

---

## 13. Key Code Files & Repos

### Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
| File / area | Purpose |
|-------------|---------|
| `Quorum.QPTM.Validations.Rules.CapacityRelease/Offers/RuleCROF######.cs` | **~159 CR offer validation rules** (e.g., 000150, 000250, 001570) |
| `Quorum.QPTM.Validations.Rules.CapacityRelease/Offers/QCROfferValidationContext.cs`, `QCROfferValidationContainer.cs`, `QOfferValidationBase.cs` | CR validation context/container/base |
| `Quorum.QPTM.DataAccess/QCapacityReleaseDataAccess.cs` | **CR data access (offers/bids/awards/recall)** |
| `Quorum.QPTM.DataObject/CodeGen/CR*DO.cs` | CR data objects → table map (§14) |
| `Quorum.QPTM.DAL/CodeGen/CRRecallReputDAL.cs` | Recall/Reput DAL |
| `Quorum.QPTM.UnitTests/OfferWizard/CapacityReleaseTests.cs`, `BidWizard/`, `AwardAmendments/` | CR unit tests (good for expected behavior) |

### Quorum.QPTM.ClassicGUI (PipelineMgrCR)
| File | Purpose |
|------|---------|
| `Native/PipelineMgrCR/QVpRecallReput.cpp` | Classic Recall/Reput screen |
| `Native/PipelineMgrShared/Queries/QQryRegCRRecallReput.cpp` | Classic recall/reput query |
| `Native/PipelineMgrKInt/QVpContractMaintenance.cpp` | Replacement-contract maintenance (CR posting hooks) |

### Quorum.QPTM.ClassicBatch
| File / process | Purpose |
|----------------|---------|
| `QPDllPipelineMgrCR/QPSContractAmend.cpp`, `QSQL_ContractAmend.cpp` | CR contract amend (recall/award) batch |
| `QPDllPipelineMgrCW/QPSCapRelTransRpt.cpp` | **CR transactional posting → `CWCAPRTRAN_*.XML`** (IPWS) |
| `QPDllPipelineMgrRPT/QPSPreReportProcessCRGenericOffer/Bid/Award.cpp` | CR pre-report processes |
| `CRKLCLGEN` (batch step) | Adjust releasing-contract LCL during release (added per 23-00925472) |
| `NETMDQRES` | MDQ-reservation update (CR-MDQ defects 24-00956219/689/762) |
| Rate Resolution batch | Resolves Max Tariff Rate onto offers (run before submit — 24-00953290) |

### Override repos
`<CLIENT>.QPTM.*` override base CR behavior — e.g. **`TEP.QPTM.ClassicBatch/QPDllPipelineMgrCR_TEP/QPSContractAmend_TEP.cpp`**, client `*.QPTM.Metadata` (`QARCH_CTRL_OBJECT_*`, `QARCH_CTRL_PROCESS_PARAM.json`), `*.QPTM.Database` migrations. **Always check for a client override before assuming base behavior.**

---

## 14. Database Tables Reference

(Table names confirmed from `Quorum.QPTM.DataObject/CodeGen/CR*DO.cs`.)

| Table | Purpose |
|-------|---------|
| `CRCTRL_OFFER_HDR` | **Offer header** (Rel K, biddable/permanent flags, post date, rates, status) |
| `CRCTRL_OFFER_DTL` | **Offer detail** (locations, BID_QTY_LOC, seasonal start/end, max-tariff/rel rate, disc ind) |
| `CRCTRL_OFFER_TEXT` | Offer text / additional terms / notes |
| `CRCTRL_OFFER_DISC_RATE` | Offer discount rates |
| `CRCTRL_BID_HDR` / `CRCTRL_BID_DTL` | **Bid header/detail** (incl. prearranged; rate form/type) |
| `CRCTRL_AWARD_HDR` / `CRCTRL_AWARD_DTL` | **Award header/detail** (award qty, status) |
| `CRCTRL_AWARD_AMEND` | **Award amendments** (recall/cancel leftovers — 22-00661775) |
| `CRCTRL_RECALL_REPUT` | **Recall/Reput records** (orphan-row deletes — 22-00661770) |
| `CRHIST_*` (hist offer/bid hdr/dtl, hist timeline) | CR history |
| `QARCH_VALD_RULE` | Validation rule definitions (incl. RuleCROF*) |
| `QARCH_CTRL_OBJECT_DEFINITION` / `_USE` / `_USE_RELATION` | Metadata controlling CR objects/screens (per-client JSON in `*.QPTM.Metadata`) |
| `QARCH_CTRL_PROCESS_PARAM` | Process params (CR transactional report / IPWS) |
| `QARCH_GLOBAL_CONFIG` / TSP config | Config incl. `USE_SEASNL_DATES` |

> Note: CR detail tables key on `OFFER_ID` / `BID_ID` / `AWARD_ID` (+ `TSP_NO` and a sequence). Field names above (e.g. `MAX_TARIFF_RATE`, `SEASNL_START_DT`, `CR_STATUS_CD`, `REPL_SR_CTR_NO`) are confirmed from DO/code/case text; verify against the client's schema version before scripting.

---

## 15. Diagnostic SQL Queries

### A. Offer header + detail (by Offer #)
```sql
SELECT OFFER_ID, TSP_NO, REL_CTR_NO, OFFER_STAT_CD, IS_BIDDABLE, IS_PERMANENT,
       REL_BEG_DT, REL_END_DT, POST_DT, MAX_TARIFF_RATE, REL_RATE
FROM CRCTRL_OFFER_HDR WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>;

SELECT OFFER_DTL_SEQ_NO, REC_LOC_ID, DEL_LOC_ID, BID_QTY_LOC,
       SEASNL_START_DT, SEASNL_END_DT, MAX_TARIFF_RATE, DISC_IND
FROM CRCTRL_OFFER_DTL WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>
ORDER BY OFFER_DTL_SEQ_NO;
```

### B. Bids + Award for an offer (allocation check)
```sql
SELECT BID_ID, BID_STAT_CD, IS_PREARRANGED, ACQ_BA_NO, BID_RATE, BID_QTY
FROM CRCTRL_BID_HDR WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID> ORDER BY BID_ID;

SELECT AWARD_ID, BID_ID, AWARD_QTY, AWARD_STAT_CD
FROM CRCTRL_AWARD_HDR WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>;
-- Red flags: SUM(AWARD_QTY) > offer Max qty (23-00907781); full qty on a 2nd-place bid (25-01049577).
```

### C. Award amendments (cancelled-recall leftovers)
```sql
SELECT AWARD_AMEND_ID, AWARD_ID, AMEND_TYPE_CD, UPDT_DT
FROM CRCTRL_AWARD_AMEND WHERE TSP_NO = <TSP_NO> AND AWARD_ID = <AWARD_ID> ORDER BY UPDT_DT;
```

### D. Recall/Reput rows (verify before delete — §6)
```sql
SELECT * FROM CRCTRL_RECALL_REPUT
WHERE REPL_SR_CTR_NO = <REPLACEMENT_CTR_NO> AND CR_STATUS_CD = '<STATUS>';
```

### E. Seasonal-date mismatch (RuleCROF000250)
```sql
SELECT OFFER_DTL_SEQ_NO, SEASNL_START_DT, SEASNL_END_DT, REL_BEG_DT, REL_END_DT
FROM CRCTRL_OFFER_DTL WHERE TSP_NO = <TSP_NO> AND OFFER_ID = <OFFER_ID>;
```

### F. Active CR validation rules
```sql
SELECT VALD_RULE_CD, VALD_RULE_DESCR, VALD_RULE_TYPE_CD, SEVERITY_CD, IS_ALLOW_OVRD, IS_ACTIVE
FROM QARCH_VALD_RULE WHERE VALD_RULE_CD LIKE 'CROF%' AND IS_ACTIVE = 1 ORDER BY VALD_RULE_CD;
```

---

## 16. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1612026** | Requirement / Closed | GBG 2023.04 HF01 — CR award qty / index-based CR on FT-1 (award accepts qty > max) | §5 Award / §4 Index | 23-00907781, 23-00900447 |
| **#1716133** | Bug / Closed | QTR 2024.10 — Offer viewable before Rel Req Post Date has passed | §4 Offer | 25-01047776 |
| **#1759366** | Bug / Closed | HEP — Capacity Release #43 not posting to IPWS | §7 IPWS | 25-01047150 |
| **#1739076** | Bug / Closed | HPE — Transactional Reporting CR duplicating data every run | §7 IPWS / §11 | 25-01018583 |
| #1727472 | Bug / Closed | PNG PRDA1 — CR transactional reporting in folder but not on IPW | §7 IPWS | — |
| #1727477 | Bug / Closed | IPWS — CR Transactional Reporting TOC-Object Association causing bad data | §7 IPWS | — |
| #1806705 | Bug / Closed | HPE 2025.10 — IPWS CR transactional posting | §7 IPWS | 26-01098608 |
| #1760280 | Bug / Closed | TEP — Long-Term Permanent CR as AMA — core validation error | §8 Permanent/AMA | 25-01035262 |
| #1663622 | Bug / Closed | GBG — NETMDQRES does not update CR receipt MDQs | §9 Rates/MDQ | 24-00956219 |
| #1664390 | Bug / Closed | GBG — NETMDQRES does not update MDQ for CR contracts | §9 Rates/MDQ | 24-00956689 |
| #1670588 | Bug / Resolved | GBG — CR contracts don't reflect LCLs in Sched Cap Overr | §9 Rates/LCL | 24-00956762 |
| #1696946 | Bug / Closed | EQT — Capacity Available calculating incorrectly for overlapping offers | §9 Available cap | — |
| #1791163 | Bug / Resolved | 2026.04 Beta — Offers Index "Allow for Index-Based CR" | §4/§8 | — |

> **Takeaways:** (1) The **IPWS/transactional-posting cluster (2025-2026)** is the most active CR defect area — `QPSCapRelTransRpt` / `CWCAPRTRAN_*.XML`, dedup & TOC-object setup. (2) **Award allocation** defects (over-max, 2nd-place-bid) are dispositioned with a **data script now + product fix tracked** (Ruby offers 266/267/268 → 25-01049577/25-01063069/25-01005999). (3) **Recall cleanup** is operational — PDM/script against `CRCTRL_RECALL_REPUT` / `CRCTRL_AWARD_AMEND`. (4) Many "Software Update" CR cases were **version-gated hotfixes** (e.g., permanent-release field fixed 2022.10, hotfixed to 2022.04).

---

## 17. Escalation Decision Tree

```
Capacity Release case reported
│
├─ Offer won't create/submit?  (§4)
│   ├─ "Value cannot be null" → run RATE RESOLUTION batch (Max Tariff) → resubmit (24-00953290)
│   ├─ Rel K picklist empty / Copy Existing → confirm Rel K entered on Details tab (22-00807721)
│   ├─ RuleCROF### thrown → read the rule file; is it firing correctly? (§10)
│   └─ Permanent/AMA/index/virtual-loc defect → check version; hotfix/core (23-00885105, 25-01035262, 25-01047874)
│
├─ Bid / Award issue?  (§5)
│   ├─ Award qty > max, or full qty to one acceptable bid → award allocation defect → DATA SCRIPT + track product fix (#1612026, 25-01005999)
│   ├─ Prearranged bid field/visibility → code/config (22-00630768, 23-00906945)
│   └─ External user can't see bids → visibility/security defect
│
├─ Recall / Reput?  (§6)
│   ├─ Stuck/orphan recall record → VERIFY then PDM/script CRCTRL_RECALL_REPUT (22-00661770)
│   └─ Cancelled-recall leftover amends → clear bad AWARD_AMEND_IDs (22-00661775)
│
├─ Not posting / duplicating in IPWS?  (§7)
│   ├─ NOT posting → check Release start date vs gas day(+offset) FIRST (expected — 25-01042897)
│   ├─ Still not posting → posting defect (#1759366); check TOC-Object Association (#1727477)
│   └─ DUPLICATE rows → transactional-report dedup defect (#1739076 / 25-01047872)
│
├─ Seasonal / permanent / segmented?  (§8)
│   └─ Seasonal dates wrong → check USE_SEASNL_DATES + RuleCROF000250 (24-00991839 RCA)
│
├─ Replacement K / rate / invoice?  (§9)
│   ├─ Missing from invoice → TOS attr (Bill-on-MDQ) / add RFS to invoice group (24-00973063, 24-00992572)
│   ├─ MDQ not updating → NETMDQRES defect (#1663622/#1664390)
│   └─ LCL not adjusted → CRKLCLGEN batch step (23-00925472)
│
├─ Report (transactional / CRO7 / RPT_CAX15)?  (§11)
│   └─ Report dedup / registered-SQL / pre-report process
│
└─ "How do I…" / correctly-firing validation / posting-date exclusion?  →  §12 Expected Behavior (Training)
```

---

*Skill created: 2026-06-01*
*Based on: ~430 closed QPTM Capacity Release SF cases + ADO work items #1612026, #1716133, #1759366, #1739076, #1727472, #1727477, #1806705, #1760280, #1663622, #1664390, #1670588, #1696946, #1791163 + QPTM source (`Quorum.QPTM.Validations.Rules.CapacityRelease`, `QCapacityReleaseDataAccess.cs`, `QPSCapRelTransRpt.cpp`, `CR*DO.cs`).*
*Companion: SKILL_Contracts.md (replacement/releasing contracts), SKILL_Nominations.md (noms on replacement K). Applicable to all QPTM TSPs/clients.*
