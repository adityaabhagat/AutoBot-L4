# Salesforce Knowledge Articles — Quorum QPTM & TIPS (and adjacent products)

**Collected:** 2026-06-13 · **Source org:** Quorum production Salesforce (`quorumsw.file.force.com`) via read-only MCP connector · **API:** v64.0
**Scope:** Salesforce Knowledge (Lightning Knowledge). Read-only. No credentials in this file.

---

## 0. Executive summary / what was found

- Salesforce **Knowledge IS enabled** in this org. The standard objects `Knowledge__kav` and `KnowledgeArticleVersion` both return data. (Note: `getObjectSchema` with no params does NOT list Knowledge objects in its index — they are queryable directly even though they don't appear in the index, and `getObjectSchema('Knowledge__kav')` times out, so the field set below was discovered empirically.)
- **2,209** published English article versions total (`PublishStatus='Online' AND Language='en_US'`).
- The corpus is **dominated by EC (Energy Components)** client-specific runbooks (`EC:CHEVRON:...`, `EC:PETRONAS:...`, etc.) which are upstream production-accounting, NOT QPTM/TIPS.
- There is a **large, clean, directly-relevant cluster** for midstream/transaction products, identifiable by product-prefix in the Title:
  - **QPTM** — `My Quorum (Gas) Pipeline Transaction Management (QPTM):` — ~60 articles. (Title contains a zero-width char in "Pi​peline" on many records; see query note.)
  - **TIPS** — `My Quorum TIPS:` / `TIPS:` / `myQ TIPS:` — ~140 articles (a handful are false hits, e.g. "Jasper Report **Tips**").
  - **QGM** (Quorum Gas Marketing) — `Quorum Gas Marketing (QGM):` — ~40 articles, frequently paired with **QCM** (Quorum Contract Management).
  - Smaller adjacents: **QCFS** (Core Financials), **QGM+QCM**, **FLOWCAL↔TIPS** integration, **QCM**.
- **Body field:** the rich-text body is the custom field **`Article_Body__c`** (HTML). There is one Knowledge article type; `Summary` (standard) holds the abstract.

---

## 1. How to query the articles (working SOQL)

The connector times out on large result sets and on `getObjectSchema('Knowledge__kav')`. Keep `LIMIT` small (≤25), avoid `ORDER BY LastPublishedDate` over the full 2,209 rows unless you also filter, and fetch full bodies **one or two records at a time**.

### Confirmed-working field set on `Knowledge__kav`
`Id, ArticleNumber, Title, Summary, UrlName, Article_Body__c, LastPublishedDate, FirstPublishedDate, VersionNumber, IsLatestVersion, LastModifiedDate, ArticleCaseAttachCount`
(Fields that do NOT exist here: `ArticleType`, `Body__c`, `Solution__c`, `Resolution__c`, `Content__c`, `Description__c`.)

```sql
-- Count of all published English articles
SELECT COUNT(Id) total
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND Language = 'en_US'

-- Recent articles (works fast at small limit)
SELECT Id, ArticleNumber, Title, LastPublishedDate
FROM Knowledge__kav
WHERE PublishStatus = 'Online' AND Language = 'en_US'
ORDER BY LastPublishedDate DESC
LIMIT 25

-- QPTM cluster (the "(QPTM)" token survives the zero-width-char issue)
SELECT Id, ArticleNumber, Title, LastPublishedDate
FROM Knowledge__kav
WHERE PublishStatus = 'Online' AND Language = 'en_US'
  AND Title LIKE '%(QPTM)%'
ORDER BY LastPublishedDate DESC LIMIT 60

-- TIPS cluster
SELECT Id, ArticleNumber, Title, LastPublishedDate
FROM Knowledge__kav
WHERE PublishStatus = 'Online' AND Language = 'en_US'
  AND Title LIKE '%TIPS%'
ORDER BY LastPublishedDate DESC LIMIT 80      -- page with OFFSET 80 for the rest

-- QGM cluster
SELECT Id, Title FROM Knowledge__kav
WHERE PublishStatus='Online' AND Language='en_US' AND Title LIKE '%(QGM)%'
ORDER BY LastPublishedDate DESC LIMIT 40

-- Fetch ONE full body (do not batch many at once — payload timeouts)
SELECT Id, ArticleNumber, Title, Summary, UrlName, LastPublishedDate, Article_Body__c
FROM Knowledge__kav
WHERE Id = '<18-char Id>'
```

**Notes / gotchas**
- `KnowledgeArticleVersion` and `Knowledge__kav` share the same record `Id`s (the `Knowledge__kav` is the article-type view that exposes `Article_Body__c`).
- `Title LIKE '%QPTM%'` returns ~306 (inflated — matches body-less acronym hits and the literal substring); prefer `'%(QPTM)%'` for a clean cluster.
- SOQL has no `ContentSize`/file traversal here; article images are stored as `rtaImage` links to `quorumsw.file.force.com` (referenced inside `Article_Body__c`).

---

## 2. Index of relevant QPTM / TIPS / QGM articles

Relevance: **High** = core QPTM/TIPS/QGM how-to or troubleshooting an L4 will reuse; **Med** = adjacent (env/refresh/security/reporting). Full body for the ★ rows is in Section 3.

### 2a. QPTM (My Quorum Pipeline Transaction Management)

| Title | ArticleNumber / Id | Updated | One-line summary | Rel |
|---|---|---|---|---|
| ★ What is CAS in QPTM and how does it work? | 000004811 / ka0UG0000005WthYAE | 2025-11-20 | CAS = engine that validates/allocates/schedules noms vs capacity, MDQ, cycle deadlines; cut logic configurable | High |
| ★ How to troubleshoot when CAS doesn't schedule a nomination? | 000004813 / ka0UG0000005WwvYAE | 2025-11-20 | Checklist: path/location, MDQ/entitlement, txn group, cycle cutoff, rule conflict; use Scheduler Exception Report + CAS audit logs | High |
| Pro-Rata vs Priority scheduling models in CAS | 000004815 / ka0UG0000005X09YAE | 2025-12-16 | Difference between the two CAS scheduling models | High |
| Can I override CAS scheduling results manually? | 000004814 / ka0UG0000005WyXYAU | 2025-12-16 | Manual override of CAS results | High |
| Understanding Capacity Release in QPTM | 000004816 / ka0UG0000005X1lYAE | 2025-12-16 | Capacity Release concept | Med |
| ★ How to Troubleshoot Missing Activity in the QPTM Scheduler? | 000004685 / ka0UG0000005EOvYAM | 2025-09-25 | Flow date / cleared filters / contract status / nom-inquiry / logs escalation path | High |
| ★ How to Troubleshoot a Contract Not Triggering a Validation Rule? | 000004635 / ka0UG00000055GnYAI | 2025-09-24 | Rule won't fire when contract TOS not on the Validation Rule Cross Reference; add TOS, reprocess | High |
| ★ What is Validation Rule KFK016 (PAL Contracts)? | 000004765 / ka0UG0000005OxlYAE | 2025-10-23 | KFK016 enforces one rate record per Eff-Date+TOC and one PAL qty record per Inj/Wdl on the RFS; not a qty-limit rule | High |
| Basic understanding of PAL Contract Validation Rules | 000004764 / ka0UG0000005OuXYAU | 2025-10-23 | PAL contract validation-rule overview | High |
| ★ What are the key parameters of the Allocation Process? | 000004758 / ka0UG0000005NnBYAU | 2025-10-23 | Full parameter reference: Gas Day, Acct Month, Reallocate/Unallocated, Force Acct Month, Ignore PDA, Recalc Fuel, TSP No, etc. | High |
| ★ Concept of Gas Day Cycles and Nomination Timing | 000004759 / ka0UG0000005NonYAE | 2025-10-23 | NAESB gas day 9AM-9AM CST; TIM/EVE/ID1/ID2/ID3 cycles, deadlines, single-day vs range, record stacking | High |
| ★ Identify incorrect EDI File Paths after a UAT refresh from PRD | 000004617 / ka0UG0000004wbhYAA | 2025-08-26 | EDI errors after refresh: Global Config → Env/EDI/%Path%; compare UAT vs PRD, recover via Deleted→History; post-refresh scripts | High |
| EDI Trading Partner Configuration Template (INTERNAL) | 000004760 / ka0UG0000005O4vYAE | 2025-10-22 | Internal EDI trading-partner config template | High |
| Resolve Gas Analysis not posting from QPTM into IPWS | 000004763 / ka0UG0000005OcnYAE | 2025-10-23 | Gas analysis → IPWS posting failure | High |
| Manual IOC Footnote .txt/.xml not reflecting in IPWS | 000004479 / ka0UG0000005OkrYAE | 2025-10-22 | IOC footnote file changes not surfacing in IPWS | Med |
| Troubleshoot Transactional Reporting not posting to IPWS (tips) | 000003857 / ka0UG0000002dOfYAI | 2024-12-18 | IPWS transactional-reporting posting troubleshooting | High |
| How To Generate Data for IPWS | 000004610 / ka0UG0000004uhxYAA | 2025-09-03 | Generate IPWS posting data | Med |
| G873OACY / Operational Capacity Dataset | 000004750 / ka0UG0000005MW9YAM | 2025-10-22 | What the G873OACY (OACY) operational-capacity dataset is | High |
| EPSQ button not visible on Nomination Submission screen | 000004636 / ka0UG00000055IPYAY | 2025-09-24 | Get EPSQ button to appear on Nom Submission | High |
| What can cause a Transaction Type to be missing from Nom Submission | 000004625 / ka0UG0000004xj3YAA | 2025-09-03 | Missing txn type on Nomination Submission | High |
| How to Set Up / View-Edit a TOC; assign TOC to Rate Schedule | 000004680 / 000004695 / 000004682 | 2025-09-24 | Type-of-Charge setup, edit, and rate-schedule assignment | High |
| What is Rate Maintenance? / Rate Seasonal Profiles / List of charges | 000004771 / 000004675 / 000004770 | 2025-09–10 | Rate maintenance, seasonal profiles, charge types in QPTM | High |
| How to Track Down a Failed Batch | 000004678 / ka0UG0000005EC1YAM | 2025-09-24 | Locate/diagnose failed QPTM batch | High |
| Validate SQL queries used in QPTM case research | 000004679 / ka0UG0000005EDdYAM | 2025-09-24 | How to validate research SQL | High |
| Different ways of running the ALESVOLIMP process | 000004674 / ka0UG0000005DxVYAU | 2025-09-24 | ALESVOLIMP run modes | High |
| Validate whether a customer was properly billed / charges on invoice | 000004686 / 000004687 | 2025-09-24 | Billing validation + which charges show on invoice | High |
| Confirm if a Service Agreement is ready for billing | 000004683 / ka0UG0000005ELhYAM | 2025-09-24 | Billing-readiness check for an SA | High |
| Calculate Unsubscribed Capacity | 000004673 / ka0UG0000005DvtYAE | 2025-09-24 | Unsubscribed capacity calc | Med |
| Setup Child Location for a Parent Location | 000004684 / ka0UG0000005ENJYA2 | 2025-09-24 | Parent/child location config | Med |
| Security: User Setup / Security Groups / Privileges tab / Security Objects | 000004619 / 000004761 / 000004618 / 000004611 | 2025-09 | QPTM security setup family | Med |
| Useful Security Objects in myQuorum v17 | 000004672 / ka0UG0000005DuHYAU | 2025-09-24 | Security-object reference (v17) | Med |
| On-Prem vs QCloud: DB mgmt / QPECS / script & patch deploys | 000004613 / 000004615 / 000004614 | 2025-08/09 | Operational differences On-Prem vs QCloud | Med |
| Hidden column on Measurement Entry screen (web) | 000004574 / ka0UG0000004grtYAA | 2025-08-21 | Unhide a column on Measurement Entry | Med |
| Confirmation Response screen usage | 000004621 / ka0UG0000004xcbYAA | 2025-09-03 | Using the Confirmation Response screen | Med |
| Notice posting/distribution; create Notice Subtype | 000004612 / 000004766 | 2025-09/10 | Notice posting + subtype creation | Med |
| Login troubleshooting; Report Favorites for external users; create external test user | 000004677 / 000004767 / 000004749 | 2025-09/10 | Access + external-user/reporting setup | Med |

### 2b. TIPS (My Quorum TIPS / TIPS Classic)

| Title | ArticleNumber / Id | Updated | One-line summary | Rel |
|---|---|---|---|---|
| ★ Understanding TIPS (Process Definition & rerun criteria) | 000003103 / ka0UG0000000bSbYAI | 2024-02-14 | The TIPS batch flow Measurement→Allocate→Settle→Revenue→Imbalance→Journal→PostResult and what forces a rerun of each | High |
| ★ Understanding the Batch Job Sequences | 000002907 / ka0UG00000008f7YAA | 2024-02-13 | Code Table 24176 holds job order/approval/daily-vs-monthly; SQL against QCODE_BATCH_JOB | High |
| TIPS Batch Processes and Steps | 000003104 / ka0UG0000005ainYAA | 2025-12-09 | Catalogue of batch processes/steps | High |
| ★ How PPA triggers | 000004785 / ka0UG0000005S3hYAE | 2025-12-15 | PPAs fire from Measured Vol/CCT/UDEF/Meter Def/Split/List changes; Code Tables 24711 & 24712 map object→PPA type | High |
| Prior Months: PPA's vs Re-Runs | 000003136 / ka0UG0000005acLYAQ | 2025-12-09 | When to PPA vs full rerun | High |
| Re-running a production month after PPA Processing | 000004727 / ka0UG0000005GXBYA2 | 2025-12-17 | Rerun sequence post-PPA | High |
| How To Purge PPA (Meter/Contract) | 000004781 / ka0UG0000005RafYAE | 2025-12-17 | Purge PPA records | High |
| How to Purge Records for a Rerun | 000004550 / ka0UG0000004bx3YAA | 2025-12-17 | Purge before rerun | High |
| ★ Reprocess all Allocations (amounts missing on invoices/reports) | 000003480 / ka0UG0000001XwPYAU | 2025-05-05 | Uncheck Realloc on Facility Lock screen then rerun allocate to force full reallocation | High |
| Overview of Reallocation Indicator Functionality | 000004443 / ka0UG00000043nJYAQ | 2025-06-23 | What the reallocation indicator does | High |
| Set up batch step CLREALLOC to auto-clear Reallocation Flag | 000003864 / ka0UG0000002dgPYAQ | 2025-12-23 | Automate clearing of realloc flag | High |
| ★ What is a Nom Hash ID? | 000003144 / ka0UG0000000kAvYAI | 2024-03-01 | Unique key of SR/REC/DEL BA+Meter+Contract+TxnType+PkgID fields used to tie noms→allocations | High |
| What is a Transaction ID? / What is a RUN ID? | 000003110 / 000003109 | 2024-02-14 | TIPS identifier definitions | High |
| How to Create a Nominatable Contract | 000004362 / ka0UG0000003rB3YAI | 2025-12-17 | Make a contract nominatable | High |
| How To - View the Validation Rules for Nominations | 000003045 / ka0UG0000000V0bYAE | 2024-03-01 | Find nom validation rules | High |
| Cannot Enter Nomination for Gas Day | 000002745 / ka05f0000029m7pAAA | 2025-03-11 | Why nom entry is blocked for a gas day | High |
| Error - "Allocation Effective % Contribution Too Large" | 000003140 / ka0UG0000000jjVYAQ | 2024-03-01 | Allocation contribution % error fix | High |
| Error - "Index Not Found for Production Date MM/DD/YYYY" | 000003139 / ka0UG0000000jhtYAA | 2024-03-01 | Production-date index error | High |
| Troubleshoot Missing Transactional Data | 000003138 / ka0UG0000000jgHYAQ | 2024-03-01 | Missing transactional data diagnosis | High |
| Correct Error: QRMTIPS.FK4_QVALD_METER Violated (Parent Key Not Found) | 000004408 / ka0UG0000003wfNYAQ | 2025-12-17 | FK violation on QVALD_METER | High |
| Contract Meter List SplitAction Error | 000004669 / ka0UG0000005C3lYAE | 2025-12-17 | SplitAction error on Contract Meter List | High |
| Contract Agent error "agent must be the holder of the primary contract" | 000004722 / ka0UG0000005GIfYAM | 2025-12-17 | Contract-agent holder error | High |
| Error - Meter Is Not Valid for Plant (Contract Meter List) | 000002744 / ka05f0000029m7kAAA | 2024-02-13 | Meter-not-valid-for-plant fix | High |
| Resolve "Plant or Company are locked for processing — Cannot create the PPA" | 000003604 / ka0UG0000001sxdYAA | 2025-02-05 | Lock blocks PPA creation | High |
| Resolve ORA-01722 Invalid Number / ORA-01489 string concat too long | 000004616 / 000003853 | 2025 | Common Oracle errors in TIPS | High |
| How to Monitor Batch Jobs and Retrieve Their Logs | 000004296 / ka0UG0000003caDYAQ | 2025-04-27 | Batch monitoring + logs | High |
| Review Batch Job Errors and Warnings in the Application | 000002858 / ka0UG00000003abYAA | 2024-07-16 | Read batch errors/warnings in UI | High |
| Troubleshoot Import Processes When Data Is Not Loading into TIPS | 000003583 / ka0UG0000001o4PYAQ | 2025-04-30 | Import data-not-loading diagnosis | High |
| Resolve "Did not find a queued process for the given Process Queue ID" | 000004640 / ka0UG00000057KDYAY | 2025-11-03 | Process-queue-id error | High |
| Core Gas Statement Overview / Minimum-Volume Penalty / Cumulative Factor | 000003133 / 000003166 / 000003155 | 2024-03 | Settlement/statement concepts | High |
| Convert Natural Gas Gallons to Shrink (MMBTU) during Settlement | 000003147 / ka0UG0000000kndYAA | 2024-03-01 | Shrink conversion in settlement | High |
| Gas Plant Accounting Glossary / TIPS Glossary / Industry Acronyms | 000003167 / 000003169 / 000003148 | 2024-03 | Reference glossaries | High |
| New Meter Setup Checklist / Meter End-Dating Checklist / Meter Types | 000003170 / 000003171 / 000003111 | 2024-03 | Meter lifecycle references | High |
| How to Expire a Meter / Shared Mass Change Meter end-date | 000004736 / 000003071 | 2024-25 | Meter expiry tools | High |
| Find the Open Accounting Date / Roll Acct Month Forward / Acct Date Maintenance | 000003137 / 000003054 / 000003592 | 2024-25 | Accounting-period control | High |
| Unlock a Facility / Facility Status Query / Facility History Purge | 000003123 / 000003053 / 000002906 | 2024 | Facility ops | High |
| 'Exiting QPEC gracefully…too much memory' error | 000003055 / ka0UG0000000W9ZYAU | 2024-02-13 | QPEC OOM error | High |
| 'Cannot start TIPS Middle Tier' after on-prem DB refresh | 000003056 / ka0UG0000000WBBYA2 | 2024-02-13 | Middle-tier won't start post-refresh | High |
| Reports not loading / widgets not loading / interactive reports won't load | 000004456 / 000002754 / 000003723 | 2025 | TIPS web reporting failures | Med |
| Overview of Escalation Schedules / Reallocation Indicator / Journal Setup | 000003124 / 000004443 / 000003105 | 2024-25 | Config overviews | Med |
| TIPS MER — Unable to add Timeslice in Shared Meter Definition | 000002814 / ka05f0000029mtDAAQ | 2025-12-09 | MER timeslice add issue | High |

### 2c. QGM (Quorum Gas Marketing) and QGM+QCM

| Title | ArticleNumber / Id | Updated | One-line summary | Rel |
|---|---|---|---|---|
| ★ Why Is My Deal Not Appearing in the Nomination Creation Screen? | 000004076 / ka0UG0000002zPBYAY | 2025-02-20 | "Confirm Only" checkbox on the deal hides it from Nom Creation; uncheck to restore | High |
| How to enter nominations in QGM? | 000004801 / ka0UG0000005VxdYAE | 2025-11-20 | Nomination entry walkthrough | High |
| How to resolve duplicate nominations or overlaps in QGM? | 000004830 / ka0UG0000005ZA1YAM | 2025-11-21 | Dedup/overlap resolution | High |
| How to create a deal in QGM? | 000004828 / ka0UG0000005Z6nYAE | 2025-11-21 | Deal creation | High |
| QGM handle imbalances and balancing / month-end settlements | 000004805 / 000004810 | 2025-11-20 | Imbalance + settlement handling | High |
| Does QGM support Park & Loan Gas Transactions? / swing contracts | 000004809 / 000004803 | 2025-11-20 | PAL + swing contract behavior | High |
| Transportation contract not on Nomination Creation screen (QGM+QCM) | 000004587 / ka0UG0000004ltBYAQ | 2025-08-21 | TC missing from Nom Creation | High |
| Deal unavailable to nominate — reason & resolution (QGM+QCM) | 000003816 / ka0UG0000002WTdYAM | 2024-11-23 | Deal not nominatable diagnosis | High |
| Troubleshoot common errors in allocation profile running JAIMBJESGC | 000004024 / ka0UG0000002stxYAA | 2025-01-15 | JAIMBJESGC allocation-profile errors | High |
| Verify/Update Type of Charge (TOC) in a Transportation Contract Invoice | 000004109 / ka0UG00000034ezYAA | 2025-02-20 | TOC verify/update on TC invoice | High |
| Demand Charge not pulling right volume (QGM+QCM) | 000004115 / ka0UG00000035HhYAI | 2025-02-20 | Demand-charge volume issue | High |
| Failed to Connect to SFTP server | 000004565 / ka0UG0000004g77YAA | 2025-08-21 | QGM SFTP connect error | Med |
| How to set up Fixed Swap Deal / NYMEX index for Base Swap | 000004167 / 000004166 | 2025-03 | Swap deal/index setup | Med |
| RATCHET utilization / TSP Group / Zone screen / Contract Type screen | 000003835 / 000004031 / 000003914 / 000004395 | 2024-25 | QGM/QCM config concepts | Med |

### 2d. Adjacent products (sampled, lower priority for QPTM/TIPS L4)

| Title | ArticleNumber / Id | Product | Rel |
|---|---|---|---|
| Add a new Quorum user into PRD/UAT (QPTM/QCM/QGM/ESUITE) | 000003873 / ka0UG0000002eEHYAY | cross | Med |
| Save a report from PRD when getting a restriction (QPTM/QCM/QGM) | 000004001 / ka0UG0000002q2XYAQ | cross | Med |
| FLOWCAL: Ways we send data to TIPS from FLOWCAL | 000004501 / ka0UG0000004IJJYA2 | FLOWCAL↔TIPS | High |
| QCFS: increase column width in Unprocessed Invoices view | 000004861 / ka0UG0000005cmDYAQ | QCFS | Low |

---

## 3. Full body text — top relevant articles

> Bodies are stored as HTML in `Article_Body__c`; reproduced below as readable prose/lists with HTML stripped. Image placeholders (screenshots stored on `quorumsw.file.force.com`) are noted as **[screenshot]**.

### 3.1 ★ QPTM — What is CAS in QPTM and how does it work? (000004811)
**Summary:** Capacity Allocation Scheduling (CAS) manages resource distribution for optimal utilization and efficient scheduling.

**Q:** What is Capacity Allocation and Scheduling (CAS) in QPTM, and what does it do?
**A:** CAS in QPTM is the engine that validates, allocates, and schedules gas nominations based on capacity availability, contractual entitlements, and business rules. It automatically determines which nominations can be scheduled in full or need to be cut based on system constraints such as **contract MDQ, pipeline segment limitations, and cycle deadlines**. CAS can be configured to apply different scheduling models, prioritization rules, and cut logic.

---

### 3.2 ★ QPTM — How to troubleshoot when CAS doesn't schedule a nomination? (000004813)
**Q:** Why isn't my nomination being scheduled by CAS, and how do I resolve it?
**A:** If a nomination is not scheduled after CAS runs, consider these common causes:
- **Missing Path or Location Setup** — ensure both receipt and delivery points are fully mapped and active.
- **MDQ or Entitlement Exceeded** — check if the nomination exceeds contract limits.
- **Invalid Transaction Group** — verify the nomination belongs to a valid, active Transaction Group.
- **Cycle Cutoff Reached** — make sure the cycle has not been finalized or locked.
- **Rule Set Conflict** — a misconfigured rule set may prevent proper allocation.

Use the **Exception Report** in the Scheduler Workbench and the **CAS Audit Logs** to identify and resolve specific failures.

---

### 3.3 ★ QPTM — How to Troubleshoot Missing Activity in the QPTM Scheduler? (000004685)
**Issue:** If data isn't appearing in the QPTM scheduler, it's usually due to filtering or contract configuration. Verifying flow dates, contract status, and service type is key.

**Steps:**
1. **Check the Flow Date** — confirm the selected flow date matches the active nomination window.
2. **Clear Filters** — remove any saved filters (location, contract ID, etc.) in the Scheduler module.
3. **Validate Contract Setup** — ensure the service agreement is active and linked to the correct rate schedule.
4. **Verify Nomination Exists** — check the Nomination Inquiry screen to confirm it was submitted.
5. **Review Logs** (if needed) — if the nom exists but doesn't populate, consult batch job logs / check for scheduling errors.
6. **Escalate to Product Support** — if it persists, capture screenshots and provide detailed environment info.

---

### 3.4 ★ QPTM — Contract Not Triggering a Validation Rule (000004635)
**Issue:** A validation rule does not trigger during nominations/scheduling because the contract is not linked to the correct **Type of Service (TOS)**.

**Steps to verify & resolve:**
1. Navigate to the **Contract Maintenance** screen in QPTM.
2. Confirm the **Type of Service** assigned to the contract. **[screenshot]**
3. Go to the **Validation Rule Cross Reference** screen.
4. Query the affected **Validation Rule ID**.
5. On the **Type of Service** tab, review the list of TOS associated with the rule.
6. If the contract's TOS is not listed, add it: select the required TOS from the left panel and move it to the right-hand (assigned) column. **[screenshot]**
7. Save changes and reprocess the transaction to confirm the rule now applies.

**Notes (red):** Always validate with the business team which TOS should be enforced per rule. **Misalignment between contract TOS and validation rules is one of the most common causes for rules not triggering.**

---

### 3.5 ★ QPTM — Validation Rule KFK016 for PAL Contracts (000004765)
Users asked whether **KFK016** enforces PAL contract quantity limits / prevents over-nominations or duplicate quantity records.

**KFK016 does NOT directly enforce PAL contract quantity limits.** Instead it performs two validations within the **Rate Forecast Setup (RFS)**:
1. **Rate Record Validation** — ensures only **one rate record** exists on the RFS for a given **Effective Date From** and **TOC (Type of Charge) Code**.
2. **PAL Quantity Record Validation** — ensures only **one PAL quantity record** exists on the RFS for **Injection** or **Withdrawal** for a given **Effective Date From** and **Beginning Flow Date**.

The rule focuses on **data consistency** and preventing duplicate entries for the same period. It preserves RFS integrity by preventing duplicate rate/PAL-quantity records with overlapping effective dates; it does **not** validate against total PAL contract quantities.

---

### 3.6 ★ QPTM — Key Parameters of the Allocation Process (000004758)
**What it is:** The Allocations Process distributes volumes (gas/fuel) to locations based on predefined criteria; parameters control which data is processed and how allocations are calculated. **[screenshot of params grid]**

**Key parameters:**
- **Gas Day** — gas day(s) to allocate; defaults to current gas day.
- **Accounting Month** — targets a specific accounting month; defaults to current month.
- **Location ID** — limits allocation to specific location(s).
- **Reallocate Indicator** — reallocates both prior-period adjustments and previously processed records.
- **Unallocated Indicator** — triggers reallocation of unallocated volumes; usually redundant (unallocated processed by default).
- **Gas Day Offset** — adjusts gas day by an offset; ignored if Gas Day is set.
- **Allocate Entire Month Indicator (Required)** — allocates all gas days from start of month to the specified/current gas day.
- **Accounting Month Offset (Required)** — computes acct month from an offset; ignored if Accounting Month is set.
- **Force Accounting Month Indicator** — allows allocation in a **closed** accounting month; use only under specific guidance.
- **LPR Measurement Process Queue ID** — restricts to measurement locations with that queue ID.
- **Location Group ID** — limits to locations within a group.
- **Ignore PDA Indicator** — ignores pre-determined allocations, allocating purely on confirmed nominations (caution).
- **Recalculate Fuel Indicator** — recalculates fuel for a location; only works if **Location ID** is specified.
- **TSP No (Required)** — allocates only to locations under the specified Transportation Service Provider; hidden by default.
- **Only Allocation Locations from MIPS** — measurement locations only; hidden/disabled by default.
- **Penalty Daily Indicator** — daily allocation for penalty allocation groups; hidden by default.

**Using parameters together:** Gas Day + Allocate Entire Month → allocates 1st-of-month through the gas day. Recalculate Fuel needs a specific Location ID (Group ID can't substitute). Reallocate + Unallocated can be combined; Reallocate heavily impacts performance.

**Best practices:** Always specify **both Gas Day and Location ID** for manual runs; use Reallocate carefully (long runtimes); avoid Force Accounting Month unless instructed; recalculating fuel with missing rates errors but allocation still completes with fuel=0.

**Notes:** Gas Day and Location ID accept multiple entries. **Manual runs ignore approval statuses for reallocations — parameter specificity is crucial.**

---

### 3.7 ★ QPTM — Gas Day Cycles and Nomination Timing (000004759)
**Gas Day:** Per NAESB, a gas day runs **9:00 AM CST to 9:00 AM CST** the next day, divided into five nomination cycles, each with flow start times and nomination deadlines.

**Cycle overview:**
| Cycle | Flow start | Notes |
|---|---|---|
| **TIM** | 9:00 AM CST (start of gas day) | Usually the current open cycle; future noms typically submitted as TIM |
| **EVE** | Later in the gas day | Single-day records only |
| **ID1** | Following EVE | Single-day; intraday adjustments start here |
| **ID2** | Later intraday | Single-day only |
| **ID3** | Last intraday before next gas day | Final nomination adjustments; single-day only |

**How noms work:** Future noms submitted in **TIM** flow the entire gas day (nom 100 Dth in TIM → 100 Dth flows full day). Adjusting later (e.g., 100→150 in ID1) updates records so the new total is met by day end.

**Adjustment example:** Open Nom Submission at 2:00 PM CST → default cycle **ID1**. A TIM nom of 100 Dth appears; override to 150 in ID1 and the DB records BOTH a TIM=100 and an ID1=150. Flow increases after ID1 to reach 150 by day end.

**Single-day vs range:** **TIM** can be single-day or a range (e.g., 3/1 9AM → 4/1 9AM). **EVE/ID1/ID2/ID3** are single gas day only.

**Notes:** Future-month Nom Submission defaults query cycle to **TIM**; a past gas day defaults to **ID3** (last open cycle). It's possible (uncommon) to have an ID1 record without a TIM record. Multiple records can coexist for the same gas day+location. Adjusting later cycles does **not replace** earlier noms — it adds to the record set.

---

### 3.8 ★ QPTM — Identify Incorrect EDI File Paths After a UAT Refresh from PRD (000004617)
**Error:** EDI errors after a UAT refresh from PRD (because QFC tables and post-refresh scripts are excluded). **[screenshot of error]**

1. Go to the **Global Configurations** screen in Classic; filter **Metadata Layer = Environment, Key Group = EDI, Key = %Path%**. **[screenshot]**
   *Note:* First verify file paths are NOT pointing to PRD. If they are, post-refresh scripts must be applied (there can be more unidentified paths pointing to PRD).
2. Open the Global Configurations screen in Classic **for PRD** with the same filters. **[screenshot]**
   *Note:* Look for disparities between the **Decrypted** and **Encrypted** file paths in UAT vs PRD. **[screenshot]**
3. To recover the pre-refresh path: highlight the incorrect file path → **Links → Deleted History**. **[screenshot]**
4. In the **Deleted Records** dialog, locate the file path → **History**. **[screenshot]**
5. The **Change History** dialog shows recent changes (e.g., path updated via post-refresh scripts on 8/14/2025). **[screenshot]**
   *Note:* The correct path resembles PRD's but is never identical (different servers for PRD vs UAT).
6. Copy the identified path and update it in the Global Configuration screen. **[screenshot]**
   *Note:* If errors persist you may refresh the middle-tier cache, but it isn't necessary.

---

### 3.9 ★ TIPS — Understanding TIPS: Process Definition & Step Rerun Criteria (000003103)
TIPS is a **gas plant allocation system**. A plant can only be run for the Accounting Date/Production Date combinations set up in the **Accounting Date Maintenance** screen. The batch flow and rerun triggers:

- **Measurement** — creates initial (physical) Paystation records (sets Meter Definition info) and standardizes volume/analysis. **Rerun when:** a volume/analysis is changed or added; meter definition changes; a change is made to the PPA Approval screen (triggering/approving/unapproving a PPA).
- **Allocate** — takes meter data + allocation group info → theoretical & allocated volumes; creates contractual Paystation info (Contract, CCT), pulls tax-exempt decimals, pulls current decimal from QDOD (if integrated); builds plant-performance data, Total Contract Volumes, and Weighted Avg Residue Price (if used). **Rerun when:** CDP (Central Delivery Point) allocation changes; tax-exempt decimal changes; QDOD Division Order Group split changes/added; any Meter Split changes; Contract Header (e.g., CCT) or meter list changes.
- **Settle** — uses Allocate records + CCT to compute amount due to producers; builds invoices, entitlements, gas statements, and the Processor's Gross Margin Report. **Rerun when:** Rate Schedule changes (price/fee); CCT setup changes; Weighted Average Sales Price screen changes; plant/contract tolerance changes on Facility Definition; POP/Penalty Override Release Notification changes.
- **Revenue** — applies Revenue Control screen keywords to create the file transferred to QDOD. **Rerun when:** Revenue Control setup changes; meter checked/unchecked on Revenue Override.
- **Imbalance** *(only if the plant has imbalances)* — uses Settle entitlement records + delivery records to calc imbalance per contract rate terms; creates AR/AP files from cashout. **Rerun when:** Contract Rates setup changes; Imbalance tab missing on Contract Header; Customer Account Maintenance not set up/changes.
- **Journal** — uses Revenue records + Journal Control setup (e.g., displaced gas) to create the ERP Journal Entry (reclass for fees, gas cost, intercompany, tax, control accounts). **Rerun when:** Journal Control setup changes.
- **Contract Journal** *(only if imbalances)* — uses Imbalance records for manual cashouts / carried imbalance to create the Journal Entry. **Rerun when:** Journal Control setup changes (Contract Type Journal Entry only).
- **PostResult** — transfers monthly transactional tables to posted tables (locks down the run). Can only run **once** per Accounting/Production Date combination. **Never cancel this job once kicked off.**

---

### 3.10 ★ TIPS — Understanding the Batch Job Sequences (000002907)
1. Navigate to **Maintenance → Code Table → Code/Decode Value Maintenance** and query **Code Table ID 24176**. Sort by Plant # to find a plant's jobs; if a plant isn't listed, its batch jobs fall under **Global/ALL**. This table also identifies Daily vs Monthly batch jobs. **[screenshot]**
2. **Approval jobs** have a checkmark in the **Approval** column.
3. **Company-Level** batch jobs are identified in the **Company** column.
4. The **Sequence Number** column gives the run order.
5. SQL to identify the sequence for a plant/company:
```sql
SELECT APPROVAL_IND, A.CO_CD, A.PLANT_NO, A.*
FROM QCODE_BATCH_JOB A
WHERE CO_CD = 'INSERT COMPANY CODE'
   OR PLANT_NO = 'INSERT PLANT NUMBER'   -- if plant not in code table 24176, use 'ALL'
ORDER BY A.PLANT_NO, A.SEQ_NO ASC;
```

---

### 3.11 ★ TIPS — How PPA Triggers (000004785)
In TIPS, PPAs can be created for **meter, contracts, user-defined formula, and measured volume.**

PPAs are **triggered whenever there are changes logged** in the Measured Volume screen, CCT, User-Defined Formula, Meter Definition, Meter Split, or Meter List. A code table maps which PPA triggers for a change event on a given screen/object. **[screenshot of code table]**

- **Code Table 24711** — determines **which type of PPA** should be triggered; trigger condition = any action on a specific TIPS object; maps TIPS object/screen → PPA type (Meter, Contracts, UDEF).
- **Code Table 24712** — determines (1) whether a PPA should be logged, and (2) which screen/object attribute causes the PPA.

---

### 3.12 ★ TIPS — Reprocess All Allocations When Amounts Are Missing on Invoices/Reports (000003480)
For performance, TIPS Gathering avoids reallocating every day of the month on each allocate run — **only meters with updated volumes reallocate automatically.** Some scenarios require a full reallocation. Unchecking the **reallocation checkbox** on the **Facility Lock** screen queues a complete (per-day) reallocation. **Always run allocations afterward.** Best practice when making mass changes to a month's volumes/allocations/meters.

- Search the **"Facility Lock"** screen and clear the reallocation mark. **[screenshot]**
- **Note:** You need security permission to update the Facility Lock screen (web and/or classic).
- After unchecking all "Realloc" checkboxes, save and rerun allocation (or wait for the next scheduled batch).
- **TIPS Classic:** System → Facility Lock; query the Plant Number + Accounting Date + Production Date combination **[screenshot]**, select **Update**, and rerun allocation (or wait for the scheduled run).

---

### 3.13 ★ TIPS — What Is a Nom Hash ID? (000003144)
The **Nom Hash ID** is used in **TIPS Gathering** and is a unique combination of:
- Service requester BA Number (`SR_BA_NO`)
- Receipt meter number (`REC_MTR_NO`)
- Delivery meter number (`DEL_MTR_NO`)
- Service requester contract number (`SR_CTR_NO`)
- Receipt / Delivery BA number (`REC_BA_NO`, `DEL_BA_NO`)
- Receipt / Delivery contract number (`REC_CTR_NO`, `DEL_CTR_NO`)
- Nomination transaction type code (`NOM_TRANS_TYPE_CD`)
- Package ID, Receipt/Delivery Package ID (`PKG_ID`, `REC_PKG_ID`, `DEL_PKG_ID`)
- Receipt / Delivery BA name (`REC_BA_NM`, `DEL_BA_NM`)

**Use:** When users submit nominations, the Nom Hash ID is generated from these fields. Knowing the Nom Hash ID for a set of nominations helps **tie allocation results back to the original nominations** during troubleshooting.

---

### 3.14 ★ QGM — Why Is My Deal Not Appearing in the Nomination Creation Screen? (000004076)
A user found Deals not displaying as purchases in the **Nomination Creation** screen.

**Cause:** Comparing similar deals, the visible deal had the **"Confirm Only"** checkbox **unchecked**, while the missing deal had **"Confirm Only" checked**. This setting restricts the deal's availability to confirmation processes only, hiding it from Nomination Creation.

**Resolution:**
1. Navigate to the deal.
2. Locate the **"Confirm Only"** checkbox.
3. **Uncheck** the box.
4. Save and refresh the Nomination Creation screen.

The deal will then be available for nominations.

---

## 4. Notes for future collection runs

- To pull additional full bodies, query one `Id` at a time with the Section-1 field set (batching ≥3 bodies risks a connector timeout).
- The EC (`EC:CLIENT:...`) articles are out of scope for QPTM/TIPS L4 but are the bulk of the 2,209; filter them out with `AND (NOT Title LIKE 'EC:%') AND (NOT Title LIKE 'EC %')` when you want only the Quorum midstream products.
- `KnowledgeArticleVersion` is the right object for counts/`PublishStatus`/`Language`; `Knowledge__kav` is the right object for `Article_Body__c` content.
- ContentDocument fallback was **not needed** — a real Knowledge base exists. (If ever needed, `ContentDocument`/`ContentVersion` are present in this org for shared docs.)
