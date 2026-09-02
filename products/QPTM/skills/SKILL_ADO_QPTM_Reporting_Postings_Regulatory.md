# SKILL: QPTM Reporting / Postings / Regulatory — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline / Pipeline Transaction Management) | **Source:** Azure DevOps closed/resolved Bugs (QuorumSoftware org)
**Scope:** The **IPWS / EBB posting** pipeline and **regulatory reporting** — Notice Posting, Transactional Reporting (Firm / Interruptible / Capacity Release), Operationally Available Capacity (OAC) & Unsubscribed Capacity, Index of Customers (IOC), FERC Form 549D / RR30, NAESB Capacity-Release EDI notifications (CRAN/CROF Recall Notification Indicator), and IPWS application/Middle-Tier stability. The common thread: **QPTM runs a `CW*` export batch → drops an XML in a `…/Exports/IPWS/<area>` folder → the IPWS Middle Tier (MT) picks it up and imports it into the IPWS DB → it shows on the public EBB/IPWS site.** Most "not posting / wrong on the site" issues live at one of those hops.

> **Use When:** an L4/L2 case (or a dev) is about a `CW*` posting batch (`CWFIRMTRAN`, `CWINTRTRAN`, `CWCAPRTRAN`, `CWNIGHTLY`, `CWOPERCAP`, `CWUNSUBCAP`, `CWALLUNCAP`/`CAALLUNCAP`, `CWINDXCUST`, `PALOCEXP`, `CWGASQUAL`, `CWSEGOPAV`, `NTCPOSTNTC`), the **Notice Posting** screen / email notices, the **IPWS** site being down/slow/blank, a **FERC 549D / RR30** report, or a **NAESB CRAN/CROF** recall-notification EDI gap. Companion areas (out of scope here): nomination/scheduling validation, RFS/Offer/Bid/Capacity-Release *transaction* logic, contract maintenance, invoicing.

> **Evidence base:** WIQL over both bug branches — `…\Engineering\Energy Transportation` and `…\Engineering\Maintenance\Midstream and Transportation` (the Maintenance branch is **mixed QPTM + TIPS**) — Bug, State in (Closed, Resolved), title containing Report / IPWS / posting / EBB / FERC / 549D / RR30 / notification / regulatory. Broad title terms ("Report", "notification") matched **1008** items dominated by RFS/Offer/Bid noise; a narrowed pass on IPWS/EBB/FERC/549D/RR30/posting returned **280** genuinely in-area bugs. **~48 were deep-read** (description + repro + comment thread + linked PRs/SF case). Every root-cause/fix below cites a real ADO #, and an SF case (`YY-xxxxxxxx`) where one was linked. **`Microsoft.VSTS.Build.IntegrationBuild` is empty on essentially every one of these bugs** — fixed-in-build is therefore inferred from **iteration path (YY.NN → release)** and tags, and marked *(inferred — confirm in release notes)*. Many client-specific fixes ship as **hotfix/on-top patches** (e.g. `DTE.QPTM.Application.QPEC`), not a core GA.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [The Posting Pipeline & Vocabulary](#2-the-posting-pipeline--vocabulary)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Transactional Reporting duplicates / not posting (FT / IT / CR)](#4-cluster-a--transactional-reporting-duplicates--not-posting-ft--it--cr)
5. [Cluster B — Notice Posting (TSP routing, email, NTCPOSTNTC, variables)](#5-cluster-b--notice-posting)
6. [Cluster C — OAC & Unsubscribed Capacity posting](#6-cluster-c--oac--unsubscribed-capacity-posting)
7. [Cluster D — Index of Customers (IOC)](#7-cluster-d--index-of-customers-ioc)
8. [Cluster E — FERC Form 549D / RR30 regulatory report](#8-cluster-e--ferc-form-549d--rr30-regulatory-report)
9. [Cluster F — NAESB Capacity-Release EDI notifications (CRAN / CROF recall indicator)](#9-cluster-f--naesb-capacity-release-edi-notifications)
10. [Cluster G — IPWS application / Middle-Tier stability](#10-cluster-g--ipws-application--middle-tier-stability)
11. [Fix-Version Matrix](#11-fix-version-matrix)
12. [Diagnostic pointers (SQL / files / logs)](#12-diagnostic-pointers)
13. [Escalation Guidance](#13-escalation-guidance)
14. [Product-overlap caveats & dead ends](#14-product-overlap-caveats--dead-ends)

---

## 1. Quick Triage Table

| Symptom (what the user/case reports) | Likely cause | First check / cluster |
|---|---|---|
| Transactional report (FT/IT/CR) shows the **same offer/contract duplicated every nightly run** | Post Date / Gas Day / Cycle ID written into the XML/key → a new "version" each run | §4 — the #1366389 → #1739076 fix family (post-date should not update; one record per OfferNo) |
| CW*TRAN batch **"completed successfully" but nothing on IPWS** (file is in Processed/Failed folder) | XML rejected by IPWS MT (unique-key/null on import), or MT↔folder connection, or missing XML Import/Export Definition | §4 / §10 — open the XML in the Failed folder; check IPWS MT log |
| Transactional XML **blank / no data generated** | Missing **XML Import/Export Definition / Entity Link Setup** in client metadata layer (DEV↔PRD drift) | §4 — compare XML Import/Export Definition DEV vs PRD |
| Notice posts/emails to the **wrong (dashboard) TSP**, or duplicate subject lines for multi-TSP | Config `POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE` (= 0 in core), email-logging config | §5 |
| `NTCPOSTNTC` **fails** (esp. when 2nd user adds another TSP / simultaneous posts) | Process/data; or post-refresh wiped XML defs + sequence | §5 / §10 |
| Notice status stays **"Pending"** / email sent at wrong time | **Expected** — `NTCPOSTNTC` / `QEMAIL` scheduled job must run | §5 (expected behavior) |
| `@1COMPANY_NOTICE@2` shows **"Not Found"** in Web notice | Web (QFC) didn't resolve the `COMPANY_NOTICE` config var | §5 (fixed 2024.04, QFC) |
| OAC / Unsubscribed **intermittently** fails to post (file lands in **Failed** folder; manual run works) | **Two IPWS Middle-Tier instances** both grab the same XML → merged/invalid XML | §6 / §10 — reduce to ONE MT per version |
| Unsubscribed export → IPWS import "**Unable to enforce constants … TspNm DBNull**" | Export writes `TSP_NO` not `TSP_NM`; IPWS TSP-name cache miss for a TSP not configured on IPWS | §6 (#1668756) |
| `CWUNSUBCAP`/`CAALLUNCAP` completes but **XML blank** / dates = 1/1/1900 | View returns no rows; `GetLocationChangeDateRanges()` cache bug; wrong loc SQL | §6 (#1669924) |
| OAC **Total Scheduled Qty = 0** for everything | QPEC/service user set as **neither internal nor external** → process filters records out | §6 (#1455080) |
| IOC **not posting / agent missing / dates show 12/30/1899** | Setup (Negotiated/UOM attrs), OR IPWS unique-key rejects QPTM duplicates, OR 1899 date defect | §7 |
| FERC **549D/RR30 stops with unique-constraint PK error** | DTE-specific report SQL **LEFT JOIN** picks up a stale duplicate TOS row | §8 (#1320990) |
| Contract **missing from 549D/RR30** | Data/config — required contract fields not populated (not a defect, usually) | §8 (#1434873, #1452730) |
| 549D field wrong (date format / location name / qty sum) | Crystal/report-SQL defect, often **DTE-specific** | §8 (#1322098, #1629595, #1699870) |
| CRAN/CROF EDI out file **missing Intraday-3 (N9*48) recall indicator** or EDINCOMING errors on CROF | NAESB 3.1+ ID3 not implemented; CROF also missing TPA grammar config | §9 (#1756196, #1781005) |
| IPWS site **down / spinning / MT crashing / memory spike** | Un-purged `QTRAN_GAS_QUALITY*` (QARCHIVE off), file-share "too many changes" buffer overflow, second MT | §10 |

---

## 2. The Posting Pipeline & Vocabulary

```
[QPTM contracts / noms / offers / locations / gas analysis]
      │  (a CW* batch process, run manually or on the Schedule Manager / CWNIGHTLY)
      ▼
[CWRPTS_* view / QTRAN_*_POSTING table]  ──►  writes XML to  \\<fileshare>\…\<CLIENT>\…\AppFiles\QPTM\Exports\IPWS\<AREA>\
      │
      ▼  IPWS MIDDLE TIER (MT) — a FileSystemWatcher picks up the XML
[IPWS DB tables]  ──►  IPWS / EBB public web site (myquorumcloud.com / client EBB)
   ├─ success → XML moved to  …\Processed\
   └─ failure → XML moved to  …\Failed\   (import threw; data NOT on site)
```

### Key processes / `CW*` batch codes
| Process | Area / folder | What it posts |
|---|---|---|
| `CWFIRMTRAN` | FIRMTRAN | Firm Transactional Reporting (NAESB) |
| `CWINTRTRAN` (a.k.a. CWINTRTAN) | ITTRAN | Interruptible Transactional Reporting |
| `CWCAPRTRAN` / `CWCAPTRAN` | CAPREL | Capacity Release Transactional Reporting |
| `CWNIGHTLY` | (multiple) | Nightly EBB roll-up that calls the above |
| `CWOPERCAP` | OACY | Operationally Available Capacity (OAC) |
| `CWUNSUBCAP` (+ `CWUNSUBCAP2`) | UNSUBCAP | Unsubscribed Capacity export |
| `CAALLUNCAP` / `CWALLUNCAP` | (CAS step) | Generates unsubscribed-cap data feeding the view |
| `CWSEGOPAV` | (segment) | Segment Operational Available Capacity |
| `CWINDXCUST` | IOC | Index of Customers report |
| `PALOCEXP` | PALOCEXP | Pipeline/location export to EBB |
| `CWGASQUAL` | GAS_QUALITY | Gas Quality / analysis export |
| `NTCPOSTNTC` | NOTICE | Posts notices (flips status Pending → Posted, builds XML) |
| `QEMAIL` | — | Scheduled job that actually sends queued notice emails |

### Terms
- **IPWS** = Informational Posting Web Site (the FERC-mandated public EBB). **EBB** = Electronic Bulletin Board (same concept). Hosting: separate **IPWS Maintenance App** + **IPWS Middle Tier (MT)** + public web.
- **MT (Middle Tier)** = the IPWS service whose **FileSystemWatcher** consumes the exported XML. **Only ONE MT instance per release is supported** unless the multi-MT feature (2023.04+, tracked via `QTRAN_XML_IMPORT_STATUS`) is present. Two live MTs both grabbing a file is a top root cause (§6/§10).
- **XML Import/Export Definition** (a.k.a. Entity Link Setup) = the QPTM metadata that defines the export's columns/file path. Lives in the client **metadata layer**; frequently **drifts between DEV and PRD** after a refresh (a top "blank XML / not posting" cause).
- **TOC – Object Association** = which Types-of-Charge feed a `CW*TRAN` process (e.g. RES TOC for CWCAPTRAN). Adding more than the expected TOC → bad XML (§4, #1727477).
- **NAESB version** = the EDI/posting standard version (3.0 / 3.1 / 3.2 / 4.0). 3.1 introduced the **Intraday-3 Recall Notification Period Indicator (N9*48)** (§9).
- **549D / RR30** = the FERC Form 549D regulatory filing (a.k.a. RR30 report); a **client-specific Crystal/SQL report** (`RRRPTS_30_FERC_FORM_549D` table). Heavily DTE.
- **QARCHIVE** = the IPWS purge/archive job (>90-day records). If a client disables it, `QTRAN_GAS_QUALITY_*` bloats and the MT memory-spikes (§10).
- **QFC** = the newer Web/middle-tier stack ("Web"/QFC layer) vs the older Classic; several "works in Classic, broken in Web" bugs are QFC-layer gaps (§5).

---

## 3. Decision Tree

```
QPTM Reporting / Postings / Regulatory case
│
├─ Is it a POSTING that won't show on IPWS / EBB?  → GET: which CW* process, the XML in Exports\IPWS\<area>\Failed (or Processed), the IPWS MT log
│   ├─ Same record DUPLICATED every run (FT/IT/CR)             → §4 (post-date/gas-day in key; #1366389/#1739076)
│   ├─ Batch "successful" but XML BLANK / no data              → §4 (missing XML Import/Export Def / Entity Link; or view returns nothing → §6 for unsub)
│   ├─ XML present but IPWS rejects (unique key / null col)     → §4 (CR dup sections) / §6 (TspNm null) / §7 (IOC unique key)
│   ├─ Intermittent: scheduled run fails, MANUAL run works     → §6/§10 (two Middle Tiers grabbing the same file)
│   └─ Site itself down / spinning / MT crash / memory spike   → §10 (QARCHIVE off / gas-quality bloat / file-share buffer overflow)
│
├─ NOTICE Posting?
│   ├─ Posts/emails to wrong (dashboard) TSP / dup subject      → §5 (POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE config)
│   ├─ NTCPOSTNTC fails                                          → §5 (+ §10 if post-refresh wiped XML defs / sequences)
│   ├─ @1COMPANY_NOTICE@2 = "Not Found" in Web                  → §5 (QFC var fix, 2024.04)
│   └─ Status stays Pending / send time wrong                   → §5 EXPECTED (NTCPOSTNTC / QEMAIL must run)
│
├─ FERC 549D / RR30?
│   ├─ Stops with unique-constraint PK error                    → §8 (DTE LEFT→INNER join; bad TOS data)
│   ├─ A contract is MISSING                                     → §8 (usually contract-field config, not a bug)
│   └─ A field is wrong (date fmt / loc name / a qty)            → §8 (Crystal / report-SQL fix, often DTE-specific)
│
├─ CRAN / CROF EDI recall indicator missing / EDINCOMING errors on CROF  → §9 (NAESB 3.1+ ID3 N9*48; TPA grammar config)
│
└─ "How does it work" / audit / vague                           → likely config/expected; verify XML Import/Export Def + IPWS setup first
```

---

## 4. Cluster A — Transactional Reporting duplicates / not posting (FT / IT / CR)

The single largest signature in this area: a **Firm / Interruptible / Capacity-Release Transactional Report** that either **duplicates** on the IPWS site every run, or completes "successfully" but **never shows up**.

### A1 — Duplicates on every run (the marquee defect family)
**Symptom:** every nightly `CWFIRMTRAN`/`CWINTRTRAN`/`CWCAPRTRAN` (or `CWNIGHTLY`) run adds another copy of the same contract/offer to the IPWS transactional report, even though nothing changed.
**Root cause:** the export wrote the **Post Date/Time (and, for CR, Gas Day / Cycle Id)** into the record so each run looked like a *new* record. Records are supposed to be **static once posted** (so they can be purged after the 90-day requirement); only an *applicable change* to the contract/location should post a **new** record.
**Fix lineage:**
- **#1366389** (VGL — FT & IT Posting Behavior): the foundational fix — post date/time must not update on re-run; one record per key; a real change posts a new record. Files: `FirmTransNaesb30DatabaseWriterHandler.cs`, `InterruptibleTransNaesb30DatabaseWriterHandler.cs`, `IPWSServiceCore_FtPosting.cs`, `IPWSServiceCore_ItPosting.cs`. PRs **56796, 57963**. (repo `Quorum.IPWS.Web` / IPWS ServiceCore.)
- **#1739076** (HPE, SF **25-01018583**) + **#1775918**: the **Capacity Release** equivalent — the same "don't add a new record when Post Date changes" fix, plus changing the **XML Import/Export Definition to no longer include Gas Day and Cycle Id**, and de-duping so the result has **one object per unique OfferNo**. PRs **114762, 114853, 116819, 120039**. Iteration → **2025.10** *(inferred — confirm in release notes)*. NOTE: fixes are **going-forward only** — existing duplicate rows on the site must be deleted manually.

### A2 — "Completed successfully" but data not on the site (XML rejected on import)
**Symptom:** batch is green, the XML is in the **Processed** (or **Failed**) folder, but the IPWS site doesn't update.
**Root causes seen:**
- **Duplicate `<CapRelK>` / `<Ctr>` sections in the XML → IPWS unique-key constraint error → whole file rejected.** Drivers: locations with **MDQ Type = "Not Applicable" but "Count in MDQ" checked** on a replacement contract (#1556154, HPE/BBT SF **22-00293038**); `RATE_FORM_TYPE_CD` NULL **and** a value for the same offer; for IT, a **null `SURCH_IND_CD`** on the side of a path with no resolvable rate (#1453418, HPE SF **22-00257757**). Workaround = remove the offending N/A-MDQ locations / fix the rate so only one section is produced; the deeper fix is the #1366389 writer logic.
- **TOC–Object Association has more than the expected TOC** for `CWCAPTRAN` → multiple TOCs resolve to one object → bad XML (#1727472 / #1727477, PNG, first day live). Fix/recommendation = validate that only the intended TOC (e.g. RES) is tied; proposed a validation warning. Both **Rejected** (setup, no code).
- **Missing XML Import/Export Definition / Entity Link Setup** in the client metadata layer → XML generated **blank** or doesn't generate. Caused by DEV→PRD refresh drift (#1378465, REX/TEP SF **21-00203161**, **Verified**; #1416773 TEP PAWS — completed-with-warnings, blank XML, **Rejected**). Fix = re-add the definition; not core code.
- **PAL contracts excluded from IT reporting** (#1323617, CRW SF **21-00102934**): the IT report only read **MSQ from the General tab**; PAL contracts use the **PAL/ISS tab Deal Quantity**, which is greyed out, so they were dropped with a "no MSQ" warning. Fix = pull Deal Quantity from PAL/ISS for PAL/FSS/ISS. PR **63089**, IPWS PR **56796**. Iteration 21.25 → **2021.10/2022.04** *(inferred)*.
- **A field not populated in the CR XML** (`RATE_ID_CD`/`RATE_RES_BASIS_CD` for NNS/CMC-2 — #1451242 TEP): traced to a NULL in `CWRPTS_CR_POSTING`; concluded **setup/data**, matches v4.1, **Rejected**.

**Bug IDs:** #1366389, #1739076, #1775918, #1453418, #1556154, #1610894, #1727472, #1727477, #1378465, #1416773, #1323617, #1451242, #1607886, #1725942.
**Linked SF cases:** 25-01018583, 22-00257757, 22-00293038, 21-00102934, 21-00203161, 23-00907888.
**Clients:** VGL/VGP, HPE/BBT, PNG/PNGTS, CRW, TEP, GBG, APL.

**Related EBB segment case:** #1607886 (TEP Ruby, SF **23-00907888**) — Segment 10 exporting qty 0 / Segment 20 doubling on `CWSEGOPAV`: **scheduling-constraint setup** (set Segment 10 constraint before End10Ruby). Config, **Verified**.

**Fix recipe:** (1) get the **CW\* process name + the XML file from the `…\Exports\IPWS\<area>\Failed` folder + the IPWS MT log**. (2) If duplicating → confirm the #1366389/#1739076 build; for CR confirm the XML Import/Export Def no longer carries Gas Day/Cycle Id; **delete pre-existing dup rows on the site**. (3) If blank/not generating → compare the **XML Import/Export Definition** DEV vs PRD. (4) If IPWS rejects on unique key → open the XML, find the duplicate `<…K>` section, trace the driver (N/A-MDQ + Count-in-MDQ location; null SURCH_IND_CD/RATE_FORM_TYPE_CD); fix setup or escalate to the writer-logic fix. (5) If TOC issue → verify TOC–Object Association has only the intended TOC.

---

## 5. Cluster B — Notice Posting

Notice Posting (QPTM screen) builds a notice that is **emailed** to BA/contacts and **posted to IPWS** via `NTCPOSTNTC`. Most defects here are **config or QFC(Web)-vs-Classic gaps**, plus a few genuine code fixes.

### B1 — Notice/email goes to the wrong TSP (dashboard TSP instead of selected TSP)
**Symptom:** user is in dashboard TSP 26001 but creates a notice for TSP 27001; the notice/email still goes to 26001. Multi-TSP notices also produce **duplicate subject lines / multiple emails**.
**Root cause:** the global config **`POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE`** is **0 (false)** by default in core → the process uses only the **context (dashboard) TSP**. Set to **1 (true)** and it uses the TSP(s) selected on the Notice TSP/User Types tab. (`QARCH_NOTICE.USER_DATA_1` / `CWRPTS_NOTICE` carry the TSP the XML is built from.)
**Fixes/cases:** #1791297 (NJR, SF... — **Client Code Change**, PR **126169**, iter 26.08 → **2026.04** *(inferred)*; resolution was the config flip), #1411178 (WWM — config `POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE`), #1360582 (ONK SF **21-00103013** — email subject/DUNS using dashboard TSP, PR **61230**, iter 21.22 → **2021.10** *(inferred)*), #1629142 (ONK SF **23-00925515** — dup subject lines, dup of #1627279; relates to `USE_BULK_FOR_IMMEDIATE`).
**Workaround:** flip the config in the client's Global metadata layer (multi-TSP clients want it = 1).

### B2 — `NTCPOSTNTC` process fails
- **#1555578** (2022.10): NTCPOSTNTC fails when a *second* user adds another TSP then the notice is posted. PR **75959**, iter 22.21 → **2022.10/2023.04** *(inferred)*; later "working in RELQA," closed.
- **#1387729** (automation): fails only when several notices post **simultaneously** — reproducible only via headless automation; deemed not a realistic prod scenario, **Rejected** (permanent TODO workaround left in).
- **#1619772** (HPE, SF **23-00901658**): notice posting "stops processing on error" + email header missing the notice sub-type. Root cause was **multi-fold and mostly environmental**: a **DB refresh ran post-refresh scripts that wiped the XML Import/Export definitions and file paths** and de-synced the `QARCH_NOTICE.NOTICE_ID` IDENTITY → PK errors (fix = re-run post-refresh sequence-reseed scripts, `DBCC CHECKIDENT('QARCH_NOTICE', RESEED, …)`); plus a real code gap — **notice sub-type not set before save** (fixed in **#1452334**, not cherry-picked back to 2021.04). PR **89379**.

### B3 — `@1COMPANY_NOTICE@2` = "Not Found" in Web
**#1659603** (CMX, SF...): the Standard-Header `@1COMPANY_NOTICE@2` variable defaults to **NOT FOUND** in **Web** while Classic resolves it from config `COMPANY_NOTICE`. QFC-layer gap. Fix in **2024.04** (QFC), PRs **96988, 97075**; **not hotfixed backward**.

### B4 — Expected behavior (NOT defects)
- **#1738226** (QTR): "Notice Status stays Pending after Posting Date/Time passes" → **expected**; `NTCPOSTNTC` must run (manually or scheduled) to flip Pending→Posted.
- **#1559756** (ONG SF **22-00257361**) / **#1655602** (WWM SF **24-00948111**): "Send Email Date/Time ignored" → **expected**; the `QEMAIL` scheduled job (every ~30 min in core) governs send time; the screen time is the queue time. **Rejected**.

**Bug IDs:** #1791297, #1411178, #1360582, #1629142, #1627279, #1555578, #1387729, #1619772, #1452334, #1659603, #1738226, #1559756, #1655602, #1568554, #1570379, #1553313, #1605824, #1791152.
**Clients:** NJR, ONK, ONG, WWM, HPE, CMX, DOH, QTR.

**Fix recipe:** TSP-routing/dup-email → flip/check **`POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE`** (and `USE_BULK_FOR_IMMEDIATE`) in the client Global layer. NTCPOSTNTC failing after a refresh → re-run **post-refresh sequence-reseed scripts** and re-add the XML Import/Export defs. Web-only variable/format gaps → likely a QFC fix already in 2024.04+. "Pending"/send-time complaints → educate (scheduled job).

---

## 6. Cluster C — OAC & Unsubscribed Capacity posting

`CWOPERCAP` (Operationally Available Capacity) and `CWUNSUBCAP`/`CAALLUNCAP` (Unsubscribed Capacity) are scheduled, high-visibility regulatory postings.

| Issue | Root cause | Fix | Bug / SF |
|---|---|---|---|
| **Intermittent** posting failure — scheduled run lands XML in **Failed**, manual run works; file contains **two TSP structures** / "Could not find file" MT error | **Two IPWS Middle-Tier instances** both pick up the same XML and race to move/process it (only ONE MT per version is supported; multi-MT w/ `QTRAN_XML_IMPORT_STATUS` ownership tracking is a 2023.04 feature) | Reduce to **one MT** for the client/version (DevOps), or **stagger the schedules** (run TSPs minutes apart) as a workaround | #1665715, #1669390 (VGL/VGP, SF **24-00954823**); MT-limit tracked in #1667500/#1546435 |
| Unsubscribed export → IPWS import fails **"Unable to enforce constants … Column 'TspNm' does not allow DBNull"** | QPTM export writes **`TSP_NO` only, not `TSP_NM`**; IPWS keeps a TSP-name cache from `QCTRL_TSP`; for a TSP **not configured on the IPWS side**, the cache misses → NULL name → constraint blows | Added handling + a warning ("No record found for TSP No…"); root unblock = stop running `CWUNSUBCAP` for TSPs that don't exist on IPWS | #1668756 (HPE), PRs **101664/101951/101952/101953** |
| `CWUNSUBCAP` completes but **XML blank / file only has parent tag**; `CAALLUNCAP` fails | `CWRPTS_UNSUB_CAP_LOC_DTL_VW` returns nothing; **`GetLocationChangeDateRanges()` in `QResolverLocation.cpp`** set Eff dates to **1/1/1900** (cache bug), and SQL **`m_Sel_LocHdr` used `PACTRL_LOC_USC` instead of `PACTRL_LOC_FOR_TSP_NO`**; collateral from #1654964 | Replaced the loc SQL + bypassed the bad cache so dates resolve; view then returns rows | #1669924 (GBG, SF **24-00960168**), PRs **99042/99075/99076/101695/101696** |
| OAC **Total Scheduled Qty = 0** for all locations/cycles | **QPEC/service user configured as neither internal nor external (NULL external indicator)** → `CWOPERCAP` filters its records out | Set the QPEC user as **internal** in QFC security; the code change made was **reverted** (config was the real fix) | #1455080 (HPE, SF **22-00258568**), PR 69579 (reverted) |
| `CWOPERCAP` / `PALOCEXP` failing in TST | **Bad/duplicate TOS data** (OBA Rate Sched under both OBA and Transportation; dup IMB/OBA TOS), or location setup (County, Location Type, FERC CID effective-date range) | Clean the duplicate TOS data; fix location attrs / FERC CID eff dates | #873989, #873991 |

**Clients:** VGL/VGP, HPE, GBG.

**Fix recipe:** intermittent Failed-folder + manual-works = **classic two-MT race** → confirm only one MT enabled for the client/version (or stagger schedules). "Unable to enforce constants/TspNm" → the client is exporting a TSP that isn't set up on IPWS (and/or pre-#1668756 build). Blank unsub XML → check `CWRPTS_UNSUB_CAP_LOC_DTL_VW` returns rows and the loc-date resolver isn't stamping 1900. OAC TSQ=0 → check the QPEC/service user's internal/external flag.

---

## 7. Cluster D — Index of Customers (IOC)

`CWINDXCUST` builds the FERC Index of Customers and posts to IPWS. Staging proc: **`QPSStagIndxOfCust`**.

| Issue | Root cause | Fix / disposition | Bug / SF |
|---|---|---|---|
| IOC **not posting / not updating** on the site (XML processes "successfully", site stale) | Environment/setup-specific (DEV↔PRD), OR specific contracts cause the import to silently fail; often **not reproducible in DEV** because IPWS isn't set up there | Mostly setup/data; resolved per client. Reproduce by dropping the PRD XML into a DEV IPWS | #1316075 (CRW, SF **21-00106018**) |
| **Agent record not displaying** in IOC after a clean run | Setup of agent BP / affiliate indicators on the contract; staging query reads `KCTRL_CTR_AGENT` + `KCTRL_BP_*` | Confirm agent BP + affiliate setup; resolved via steps, no code | #1639588 (WWM, SF **24-00936650**) |
| IOC **Report Date / First-Day-of-Qtr show 12/30/1899** in XML & site instead of the entered params | Date params not propagated to the XML; **plus** IPWS has a **unique-key constraint on contracts/locations that QPTM lacks** → QPTM generated dup rows, IPWS rejected the insert, site stayed stale | Fixed date propagation; deleted duplicate QPTM rows | #1782581, PRs **124270/124671**, iter 26.05 → **2026.04** *(inferred)* |
| IPWS **Negotiated Rates Indicator = N (should be Y)** / wrong UOM ('B' vs 'T') | IOC reads "Negotiated" from the contract **Additional Attributes (Negotiated Rates) checkbox**; UOM from **TSP Preference (Energy UOM) → `SCODE_UOM.QPTM_FERC_UOM_CD`** | Setup — check the contract Negotiated Rates attribute + TSP Preference UOM; documented in the IPWS Configuration wiki | #1534334 (WWM, SF **22-00272088**) |
| IOC export blocked when specific contracts present (whole file won't load) | The flagged contracts created XML the IPWS unique key rejected (no warning surfaced) | Setup/data on those contracts; same pattern as #1782581 | #1316075 |

**Fix recipe:** "IOC not posting / stale" is almost always **(a)** the site rejecting QPTM-generated **duplicate** contract/location rows on its unique key (delete the dups in QPTM, regenerate) or **(b)** a setup attribute (Negotiated Rates checkbox, UOM on TSP Preference, agent BP/affiliate). Reproduce by dropping the **PRD XML into a DEV IPWS** (a normal DEV refresh won't reproduce because IPWS env isn't refreshed with QPTM).

---

## 8. Cluster E — FERC Form 549D / RR30 regulatory report

A **client-specific Crystal/SQL report** (table `RRRPTS_30_FERC_FORM_549D`), overwhelmingly **DTE**. Run from Report Execution → REGULATORY REPORTS → "RR30 FERC FORM 549D REPORT". Report SQL lives in client report procs (e.g. **`QSQL_PreReportProcessRR_DTE.cpp`**, proc `m_SEL_RRRPTS30_FORM_549D`); fixes ship as **client on-top patches** (`DTE.QPTM.Application.QPEC`).

| Issue | Root cause | Fix | Bug / SF |
|---|---|---|---|
| Report **stops with unique-constraint PK** error (`PK_RRRPTS_30_FERC_FORM_549D`) | The DTE report SQL **LEFT JOINs** `KCTRL_TOS`/`KCTRL_TOS_ATTR` and picks up a **stale duplicate TOS row** — a contract briefly had a different TOS during setup and the **rate kept the old TOS**, so two rows collide on the PK | Change the **LEFT JOIN → INNER JOIN** in the DTE report SQL (cuts results to only TOS-matched rows). Client-specific hotfix. PRs **58200/65087/65089** | #1320990 (DTE, SF **21-00106983**) |
| Date **fields 24/25 format YYYY/M** for single-digit months → FERC upload rejects | Crystal formula outputs `YYYY/M` not `YYYY/MM` | Crystal format change to zero-pad month (deprioritized Low; **Rejected/closed** for lack of feedback) | #1322098 (DTE, SF **21-00103610**) |
| A **contract is missing** from the report | **Not a defect** — contract must have required fields populated (Authorized Overrun Charge, Gas-In-Kind, a `KCTRL_CTR_USER_DEF` row in the date range; CTR MSQ/ACQ depending on rate schedule PAL/STO/TRN) | Populate the fields; report then includes the contract | #1434873 (SF **21-00200028**), #1452730 (SF **22-00256442**) — both **Rejected/Deferred** |
| Location **name** uses the begin-date description, not the latest within the date range (fields 29/29a/31/31a) | Report uses the **Rates-tab lookup (begin date)** rather than effective-date-range logic | Logged as **enhancement Feature #1640161**, not fixed as a bug | #1629595 (DTE, SF **23-00926590**) |
| Field 62 `CTR_USAGE_WD_QTY` **missing the SWOVW rate** (off vs IN58 report) | The report SQL's WHERE clause excluded the **SWOVW** TOC (data had quantity under NULL TOC_CD + SWOVW) | Add **SWOVW** to the `TOC_CD` WHERE in `m_SEL_RRRPTS30_FORM_549D` (`QSQL_PreReportProcessRR_DTE.cpp`). PR **104228**. Client-specific, hotfixed | #1699870 (DTE, SF **24-00985687**) |

**Fix recipe:** confirm whether it's the **process erroring** (PK/duplicate — almost always bad/duplicate TOS data from a mid-setup TOS change; LEFT→INNER join), **missing contract** (populate required fields — usually not a code fix), or a **wrong field value** (Crystal format / report-SQL WHERE — client-specific patch). These are DTE-specific: changes are low collateral risk to other clients but **always confirm in the DTE deliverable / release notes** since IntegrationBuild is empty.

---

## 9. Cluster F — NAESB Capacity-Release EDI notifications (CRAN / CROF recall indicator)

QPTM's outbound capacity-release EDI (CRAN = Capacity Release Award Notice; CROF = Capacity Release Offer) must carry NAESB-version-appropriate fields. NAESB **3.1 introduced the Intraday-3 (ID3) Recall Notification Period Indicator (`N9*48`)** that QPTM only supported through ID2.

| Issue | Root cause | Fix | Bug / SF |
|---|---|---|---|
| **CRAN out** file missing the **ID3 Recall Notification Period Indicator** for NAESB 3.1+ trading partners | `QEdiCRANOut31` (NAESB 3.1) never added ID3; only ID2 supported | Add ID3 to `QEdiCRANOut31` (cascades to 3.2 → 4.0 since they chain the base). PRs **117794/117800/117801**. iter 25.21 → **2025.10** *(inferred — cherry-picked forward)* | #1756196 (Enercross trading partner / multiple clients) |
| **EDINCOMING** errors generating the **CROF** out file; CROF also missing ID3 (`N9*48`), non-compliant with NAESB WGQ 5.4.24 | Two issues: (1) **missing CRNS grammar config in TPA Maintenance** caused the CROF dataset to be reused for the Notes/Special-Instruction outfile → runtime error; (2) ID3 not implemented in **`QEdiCROFOut18.cs`** | Add the TPA Maintenance grammar entry (client config, no script) + code change to add ID3 to `QEdiCROFOut18`. PRs **124880/125621/125622/125623**, cherry-picked to **2025.10 / current / develop** | #1781005 (QTR, SF **25-01060489**) |

**Clients:** QTR + any client with NAESB 3.1+ trading partners (Enercross).
**Fix recipe:** "recall indicator missing on CRAN/CROF" → confirm the partner's **NAESB version in TPA Maintenance** (the indicator is *correctly* absent for 3.0 and prior), confirm the build has #1756196 (CRAN) / #1781005 (CROF), and for CROF EDINCOMING errors add the **CRNS grammar config in TPA Maintenance**. Pair with the EDI troubleshooting skill for dataset/grammar mechanics.

---

## 10. Cluster G — IPWS application / Middle-Tier stability

The IPWS site is FERC-mandated to be up; outages are escalated hard. These are mostly **ops/infra + data-hygiene**, not core posting-logic bugs, but they masquerade as "posting not working."

| Issue | Root cause | Fix / workaround | Bug / SF |
|---|---|---|---|
| IPWS site **down / spinning / MT memory spikes / crashes** | **`QTRAN_GAS_QUALITY_HDR/_DTL` bloat** — IPWS keeps inserting versioned rows and only displays the latest; with **QARCHIVE disabled**, millions of stale rows load into a data object on query → memory spike → MT/web crash | Re-enable / run **QARCHIVE** (purge >90-day rows), or run a **purge script** of non-latest rows (no restart needed); recurs every ~2–3 months until QARCHIVE runs regularly | #1430532 (CRW, SF **22-00218709** RCA), #1567787, #1553698, #1671318 (HPE RCA) |
| IPWS MT throws **"too many changes at once in directory" / buffer-overflow**, "Directory … is invalid", crashes | The **Cohesity (`HDC2-COH-…`) file share** generates excessive FileSystemWatcher change events; `XmlFileWatcherObserverBase.NotAccessibleError` null-ref | Infra fix on the share + product error-handling hardening; track via #1671318 / #1667238 (error-handling overhaul, hotfixed for HPE 2023.04) | #1671318 (HPE), #1667238 |
| OAC/Unsub files in **Failed**, intermittent, manual works | **Two Middle Tiers** racing for the same file (see §6) | One MT per version / `QTRAN_XML_IMPORT_STATUS` (2023.04+) | #1665715/#1669390 |
| IPWS Maintenance App **Batch Process Execution screen blank** (no processes) | Client env / metadata setup | Setup; **Rejected** | #1623454 (VGP) |
| IPWS exception when **`QCODE_TARIFF_PAGES`** has no entries | Missing null/empty handling | Add null checks/error handling. PR **63831**, iter 22.01 → **2022.04** *(inferred)* | #1395518 |

**Fix recipe:** "IPWS is down/slow" → first check **QARCHIVE status + `QTRAN_GAS_QUALITY_*` row counts** (top cause), then **how many MT instances** are enabled, then the **file-share** (Cohesity) MT logs for buffer-overflow/"too many changes". Restarting services is only a temporary unblock; the durable fixes are QARCHIVE + single-MT.

---

## 11. Fix-Version Matrix

> IntegrationBuild is empty on all of these; "Fixed-in-build" is inferred from iteration path/tags unless a PR/comment names a release. **Confirm in `Quorum.QPTM`/`Quorum.IPWS` release notes before quoting to a client.**

| Bug | Symptom (short) | State | Fixed-in-build (inferred unless noted) | Repo / artifact | SF case |
|---|---|---|---|---|---|
| #1366389 | FT/IT transactional dup — post date updates each run | Closed | 2021.10–2022.04 *(inf)*; PRs 56796/57963 | `Quorum.IPWS.Web` (FtPosting/ItPosting writer handlers) | — |
| #1739076 | **CR** transactional dup every run | Closed | **2025.10** *(inf)*; PRs 114762/114853/116819/120039 | IPWS CR posting + XML Import/Export Def | 25-01018583 |
| #1775918 | CR dup (related to #1739076) | Closed | 2025.10 *(inf)* | as above | 25-01018583 |
| #1323617 | PAL contracts excluded from IT report | Closed | 21.25 → 2021.10/2022.04 *(inf)*; PR 63089 / IPWS PR 56796 | IPWS IT reporting | 21-00102934 |
| #1378465 | Transactional XML not generating (REX FTS) | Closed | env/metadata fix (no GA) | XML Import/Export Def (TEP metadata) | 21-00203161 |
| #1455080 | OAC Total Scheduled Qty = 0 | Closed | config (code reverted) | QFC security (QPEC user internal flag) | 22-00258568 |
| #1668756 | Unsub export missing TSP_NM → import constraint | Closed | 2024 hotfix *(inf)*; PRs 101951-953 | IPWS unsub import / QPTM unsub export | — |
| #1669924 | Unsub XML blank / CAALLUNCAP fail (1900 dates) | Closed | July/Aug 2024 hotfix *(inf)*; PRs 99042/99075/101695/101696 | `QResolverLocation.cpp` (`GetLocationChangeDateRanges`); loc SQL `m_Sel_LocHdr` | 24-00960168 |
| #1665715/#1669390 | OAC/Unsub intermittent (two MTs) | Closed | config/infra (reduce to 1 MT); multi-MT feature 2023.04 | IPWS Middle Tier / `QTRAN_XML_IMPORT_STATUS` | 24-00954823 |
| #1782581 | IOC dates 12/30/1899 + IPWS unique-key reject | Closed | 26.05 → **2026.04** *(inf)*; PRs 124270/124671 | `QPSStagIndxOfCust` / IOC report | — |
| #1534334 | IPWS Negotiated Rates Ind = N (should Y) | Closed | config (wiki documented) | IOC: contract Additional Attributes; `SCODE_UOM.QPTM_FERC_UOM_CD` | 22-00272088 |
| #1320990 | RR30/549D unique-constraint PK error | Closed | DTE on-top patch *(inf)*; PRs 58200/65087/65089 | `DTE.QPTM.Application.QPEC` report SQL (LEFT→INNER join) | 21-00106983 |
| #1699870 | 549D field 62 missing SWOVW | Closed | DTE hotfix *(inf)*; PR 104228 | `QSQL_PreReportProcessRR_DTE.cpp` (`m_SEL_RRRPTS30_FORM_549D`) | 24-00985687 |
| #1322098 | 549D fields 24/25 date format YYYY/M | Rejected | not fixed (Low, deprioritized) | DTE Crystal report | 21-00103610 |
| #1629595 | 549D location name not latest | Closed | → Feature #1640161 (enhancement, not bug) | DTE report | 23-00926590 |
| #1791297 | Notice posts to dashboard TSP not selected | Closed | 26.08 → **2026.04** *(inf)*; PR 126169 (config flip) | `POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE` | — |
| #1360582 | Notice email subject/DUNS = dashboard TSP | Closed | 21.22 → 2021.10 *(inf)*; PR 61230 | IPWS notice email | 21-00103013 |
| #1619772 | Notice posting stops on error + email header | Closed | patch-back of #1452334 + post-refresh scripts; PR 89379 | notice sub-type set-before-save (#1452334) | 23-00901658 |
| #1659603 | `@1COMPANY_NOTICE@2` = Not Found in Web | Closed | **2024.04** (QFC, not back-ported); PRs 96988/97075 | QFC notice variable resolution | — |
| #1756196 | CRAN out missing ID3 recall indicator (NAESB 3.1+) | Closed | 25.21 → **2025.10** *(inf)*; PRs 117794/117800/117801 | `QEdiCRANOut31` | — |
| #1781005 | CROF EDINCOMING errors + missing ID3 | Closed | cherry-picked **2025.10/current/develop**; PRs 124880/125621/125622/125623 | `QEdiCROFOut18.cs` + TPA Maintenance grammar | 25-01060489 |
| #1395518 | IPWS exception on empty QCODE_TARIFF_PAGES | Closed | 22.01 → 2022.04 *(inf)*; PR 63831 | IPWS null handling | — |
| #1727472/#1727477 | CR transactional not on site (TOC assoc) | Rejected | setup (TOC–Object Association) | — | — |
| #1556154 | CR transactional missing (HPE/BBT) | Verified | setup (N/A-MDQ + Count-in-MDQ locations) | — | 22-00293038 |
| #1453418 | IT transactional not posting (null SURCH_IND_CD) | Closed | merged to develop / GA *(inf)*; PRs 69352/69916/69917 | IT posting | 22-00257757 |

---

## 12. Diagnostic pointers

> **Caveat:** QPTM/IPWS run on per-client schemas (Oracle `ESUITE_Q<CLIENT>` / MSSQL). Table/column names below come from repro text, PRs and code search — **verify against the client schema and always verify-SELECT before any DELETE/UPDATE** (these are often regulatory tables).

**Files & folders (the #1 thing to grab):**
- Export folder: `\\<fileshare>\…\<CLIENT>\<ENV>\AppFiles\QPTM\Exports\IPWS\<AREA>\` with `\Processed\` and `\Failed\` subfolders. AREAs: `FIRMTRAN`, `ITTRAN`, `CAPREL`, `OACY`, `UNSUBCAP`, `IOC`, `GAS_QUALITY`, `NOTICE`, `PALOCEXP`. **The XML in `\Failed\` + the IPWS MT log is the fastest root cause.**
- IPWS MT log: `qtrace.QIPWS.MT.*.log` (and `qtrace.QIPWS.web.*.log`). Look for: *"Unable to enforce constants … DBNull"*, *"unique … constraint"*, *"too many changes at once in directory"*, *"Could not find file"*, *NotAccessibleError*.

**Useful tables/views (verify per client):**
```sql
-- IT transactional posting (the null-SURCH duplicate pattern, §4)
SELECT * FROM QTRAN_IT_POSTING_HDR WHERE TSP_PROP=:tsp AND GAS_DAY=:gd;
SELECT SURCH_IND_CD, MAX_TARIFF_RATE, RATE, LOC_ID_1, LOC_ID_2, *
FROM   CWRPTS_IT_POSTING WHERE CTR_NO=:ctr;     -- null SURCH_IND_CD = duplicate section risk

-- CR transactional posting (RATE_FORM_TYPE_CD null+value dup, §4)
SELECT * FROM CWRPTS_CR_POSTING WHERE OFFER_NO=:offer;  -- watch RATE_FORM_TYPE_CD NULL vs 1

-- Unsubscribed capacity view (blank-XML check, §6)
SELECT * FROM CWRPTS_UNSUB_CAP_LOC_DTL_VW WHERE TSP_NO=:tsp;  -- no rows => §6 #1669924

-- Notice TSP the XML is built from (wrong-TSP routing, §5)
SELECT NOTICE_ID, USER_DATA_1 FROM QARCH_NOTICE WHERE NOTICE_ID=:id;  -- USER_DATA_1 = TSP used
SELECT * FROM CWRPTS_NOTICE WHERE NOTICE_ID=:id;

-- 549D / RR30 table (PK collision, §8)
SELECT SR_CTR_NO, COUNT(*) FROM RRRPTS_30_FERC_FORM_549D
WHERE USER_ID=:u GROUP BY SR_CTR_NO HAVING COUNT(*)>1;  -- dup => bad TOS data / LEFT join

-- IPWS gas-quality bloat (MT memory spikes, §10)
SELECT COUNT(*) FROM QTRAN_GAS_QUALITY_HDR;   -- huge + QARCHIVE off => §10
SELECT COUNT(*) FROM QTRAN_GAS_QUALITY_DTL;
```

**Configs to check (QPTM Global / TSP layer):**
- `POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE` (0 in core; 1 for multi-TSP notice clients) — §5
- `USE_BULK_FOR_IMMEDIATE` — duplicate notice emails — §5
- `COMPANY_NOTICE` — the `@1COMPANY_NOTICE@2` variable source — §5
- **XML Import/Export Definition** screen — exists & matches the export file path; compare DEV vs PRD — §4/§5
- **TPA Maintenance** — partner NAESB version + CRNS grammar entry — §9
- **QARCHIVE** schedule enabled — §10

---

## 13. Escalation Guidance

**Route to Engineering (true Software Defect) when:**
- A transactional report **duplicates** despite no change → confirm/escalate the post-date writer fix (#1366389 FT/IT, #1739076 CR). Provide the **CW\* process, the Failed-folder XML, the IPWS MT log, the offer/contract #**.
- Unsub blank XML with **1900 dates** (#1669924) or **TspNm null** import error (#1668756); IOC **1899 dates** (#1782581); 549D **PK error / missing-SWOVW** (#1320990/#1699870); IPWS **null-handling crash** (#1395518); **CRAN/CROF ID3** gap (#1756196/#1781005).
- These ship as **GA + cherry-picks** or **client on-top patches**; IntegrationBuild is empty, so confirm the target build in release notes and the linked PRs.

**Handle as Configuration / Cloud Ops (no core code) when:**
- **Two Middle Tiers** racing (reduce to one per version) — the dominant intermittent OAC/Unsub failure (#1665715/#1669390).
- **XML Import/Export Definition / Entity Link Setup** missing or DEV↔PRD drift (#1378465, #1416773, post-refresh wipes in #1619772).
- **Notice TSP routing / dup emails** → `POST_NOTICES_TO_MULTIPLE_TSPS_IN_XML_FILE` / `USE_BULK_FOR_IMMEDIATE` (#1791297, #1411178, #1629142).
- **TOC–Object Association**, **N/A-MDQ + Count-in-MDQ** locations, **QPEC user internal flag** (OAC TSQ=0), **IOC Negotiated/UOM** attributes, **duplicate TOS data** (CWOPERCAP/PALOCEXP fail, 549D PK), required **contract fields** for 549D.
- **QARCHIVE** re-enable / gas-quality purge for IPWS instability (#1430532, #1671318) — restart only buys time.

**Handle as Expected behavior / education:**
- Notice status "Pending" until `NTCPOSTNTC` runs (#1738226); "Send Email Date/Time" governed by the `QEMAIL` scheduled job (#1559756, #1655602); CRAN/CROF recall indicator correctly absent for NAESB ≤ 3.0.

**Reproduction note:** IPWS env is **not** part of a normal QPTM DEV refresh — to reproduce a posting/site issue, **drop the PRD/UAT XML into a DEV IPWS import path** (per the KB "How To: Generate Data For IPWS"). A QPTM-only refresh will not surface IPWS-import failures.

---

## 14. Product-overlap caveats & dead ends

- **Branch overlap:** the `…\Engineering\Maintenance\Midstream and Transportation` area is **mixed QPTM + TIPS**. The functional terms here (IPWS, posting, FERC 549D, NAESB CRAN/CROF, Notice Posting) are QPTM-specific, so contamination was low, but the title term **"posting" also matches TIPS accounting "posting"** (Post Results / month posting). The following matched the query and were **dropped as TIPS/out-of-area:** #199752 (DGO "Posting Error for RPT_INV_A" — TIPS `QTIP_RPT_INVOICE_IMBAL` posting), #212249 (DGO "Rerun Month Posting Error" — TIPS imbalance accounting), #1663870 (SRB TIPS Posting Error), #1643221 (SRB Plant Performance Summary — TIPS report), #259578/#1387476 (TIPS volume import "rogue posting"), #100253 (IFERC fixed-price — trading). Treat any "month posting / Post Results / RPT_INV / QTIP_*" item with the **TIPS Settlement/Reporting** skills, not this one.
- **Term breadth:** "Report" and "notification" are too broad — the full WIQL returned **1008** items, most of them RFS/Offer/Bid/Contract-Maintenance (different QPTM skill area). The numbers cited (1008 matched / 48 deep-read) reflect this; the actionable in-area set is ~280 and clusters cleanly into §4–§10.
- **IntegrationBuild empty everywhere** — every fixed-in-build in §11 is inferred from iteration path/PR comments and is marked as such. Do not quote a build to a client without checking release notes.
- **Dead ends / "no code" closures:** many high-pressure (regulatory-compliance) IPWS tickets resolved as **setup/data or ops** after long threads — duplicate TOS data, missing XML defs, two MTs, QARCHIVE off, contract-field config. When an IPWS/EBB case is "critical, regulator is watching," check those five **before** assuming a product bug.
- **DTE = the 549D/RR30 client.** Nearly every 549D bug is DTE-specific report SQL/Crystal in `DTE.QPTM.Application.QPEC`; a fix for one DTE 549D field rarely affects core or other clients.

---

*Skill created 2026-06-14 from ADO QuorumSoftware bugs (Energy Transportation + Maintenance\Midstream and Transportation branches). ~48 bugs deep-read across Transactional Reporting (FT/IT/CR), Notice Posting, OAC/Unsubscribed Capacity, Index of Customers, FERC 549D/RR30, NAESB CRAN/CROF EDI, and IPWS MT stability. Key ADO items: #1366389, #1739076, #1323617, #1668756, #1669924, #1665715/#1669390, #1455080, #1782581, #1534334, #1320990, #1699870, #1791297, #1659603, #1756196, #1781005, #1430532, #1671318. Companion: SKILL_EDI_Troubleshooting (CRAN/CROF dataset mechanics), the QPTM Capacity-Release/RFS ADO skill (transaction-side logic), REPO_REFERENCE.md.*
