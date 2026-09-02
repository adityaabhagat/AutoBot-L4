# SKILL: QCA Joint Interest Billing (JIB) Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Cost Accounting (QCA — upstream oil-and-gas joint-interest accounting; the JIB module within the myQuorum / On Demand Upstream suite)
**Scope:** The JIB billing cycle end-to-end — GL/AP/AR interface into the JIB cost transaction file (CTF), **Property Allocation**, **Owner Allocation**, **Producing / Drilling / Completion overhead** rebill, **Rebill** (reverse/rebill, current-DOI rebill), **Prepay / Cash Calls**, **Finalize & Post** (journalization to QCFS/GL), and **export to EnergyLink / JIBLink**. Driven mostly through the **JB005 Process of JIB** screen and the **JBxxx** batch processes.
**Companion areas (separate skills if/when mined):** QCFS GL/AP/AR core accounting, DOI/Ownership (QDO), AFE module, Revenue (owner revenue distribution). This skill *consumes* coded GL/AP transactions + DOI master + billing decks (tiers) + overhead rates and *produces* owner JIB invoices, journal entries, and the EnergyLink/JIBLink export. **When a JIB number is wrong, the cause is usually upstream master data (DOI, property type, AFE status, billing deck tier, BA address) — JIB is the messenger.**

> **Evidence base:** 1,263 closed QCA JIB cases. Root-cause split: (blank) 276, **Training 169**, **Customer Error 138**, **Software Defect 116**, **Application Configuration 89**, Customer Cancelled 70, Business Change 67, Hardware/Software Change 54, Performance 53, ChangeConfig 8, others. This skill mines the **213 actionable** cases (Software Defect 116 + Application Configuration 89 + ChangeConfig 8) for fix recipes, plus ~40 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — JIB process timeouts (QPEC / CommandTimeout / chunk size) — HIGHEST FREQUENCY](#4-cluster-a--jib-process-timeouts)
5. [Cluster B — JBXRF_KEYWORD_DERIVATION / code-block / event setup (JB084, JB500, GL013/GL105)](#5-cluster-b--jbxrf_keyword_derivation--code-block--event-setup)
6. [Cluster C — JIB out of balance / GL does not tie / interface staging gaps](#6-cluster-c--jib-out-of-balance--gl-does-not-tie)
7. [Cluster D — Owner Allocation errors (DOI cartesian doubling, CE/SPE failures)](#7-cluster-d--owner-allocation-errors)
8. [Cluster E — Property Allocation & Rebill (reverse/rebill, PA-rebill rollback)](#8-cluster-e--property-allocation--rebill)
9. [Cluster F — Producing / Drilling / Completion Overhead rebill](#9-cluster-f--producing--drilling--completion-overhead-rebill)
10. [Cluster G — Duplicate transactions / duplicate reversals / CTF dups (Archive & Purge)](#10-cluster-g--duplicate-transactions--duplicate-reversals)
11. [Cluster H — EnergyLink / JIBLink export (PRT/state, path, memory)](#11-cluster-h--energylink--jiblink-export)
12. [Cluster I — Prepay / Cash Calls (JB340)](#12-cluster-i--prepay--cash-calls-jb340)
13. [Cluster J — CTF failure holds (JB390/JB350) & property-type / DOI key errors](#13-cluster-j--ctf-failure-holds--property-type--doi-key-errors)
14. [Cluster K — V16/V17/Permian/MEW upgrade regressions (client-layer drift)](#14-cluster-k--upgrade-regressions--client-layer-drift)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Key Code, Processes & Repos](#18-key-code-processes--repos)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| JIB step "**Stopped Processing on Error**" / "**Timeout exceeded while waiting for execution of this Batch**" after ~1 hr (JBREBILL, JBLDJE2CAS Finalize & Post, JBROLLDATE, JBJOURNAL) | **QPEC command-timeout reset** (very common after a patch) and/or data volume | **§4** — check `CommandTimeout` in `QPEC.ini`/`QPEC.exe.config` (default 3600 → set 18000), global `COMMAND_TIMEOUT_SECONDS`, chunk-size keys; confirm QPEC restarted |
| "**Event and Entry type not defined in JBXRF_KEYWORD_DERIVATION for event …**" | Missing decision field / event setup | **§5** — add the event/entry in **JB084** (ACCOUNTING CODE decision field) and intercompany Cr/Dr lines in **JB500** |
| JIB Close fails "**code block item not allowed for account**" / "amounts … do not sum to zero" | Code-block (`GL013`/`GL105`) column set to NOT ALLOWED for the JE code type | **§5/§6** — flip the offending column (SURPLUS / TIER / OWNER NO / DO TYPE) to **Optional** in GL105 |
| JIB / GL out of balance, `GL014` ≠ `JB080`, missing I/C lines | Interface records didn't stage `SSTAG/STRAN_CORE_INTFC`; bad LOS/Archive&Purge run | **§6** — restage the missing `STRAN_CORE_INTFC` rows by SOURCE_CTF_ID range; rerun JBGLIMPORT/QCFSIMPCYC |
| Owner Allocation **CE / SPE** "Failed to retrieve DO info" / decimals doubled for an owner | DOI has two interest types (DI+WI or WI+MI) on the **same Interest Type Sequence No** → cartesian join | **§7** — split the interest types onto distinct **Interest Type Sequence Numbers** (or end-date the DI row) |
| Property Allocation SPE / DOI validation error on rebill | Service date predates the billing-deck tier eff date, or PA-rebill functionality | **§8** — back-date the DOI tier; note PA-rebill was **rolled back** (use owner-property rebill) |
| Producing/Drilling/Completion OH rebill wrong, triplicated, or duplicate reversals | OH rate/suffix setup, or reversal SQL not joining on accounting date | **§9/§10** — JB010 rate/suffix uniqueness; duplicate-reversal is a known defect (join on acctg date) |
| Duplicate lines in CTF / JIB out of balance from dups | ADO/COM connection drop mid-process, or Archive&Purge collateral | **§10** — dedupe `JBTRN_CTF`; root cause is connection loss or A&P |
| EnergyLink/JIBLink export missing an owner (no **PRT** line) | BA address incomplete — **State** (or City/Country/ZIP) is null | **§11** — populate the State field on the BA (export proc skips PRT if any address field null) |
| JIBLink **out of memory** / "can't get record count" | Client override of JBINVJIBLK dropped the Fetch_Size/Fetch_Order params | **§11** — add Fetch_Size/Fetch_Order as Environment Specific; or export staging table to flat file |
| Prepay/Cash Call not on JB340 / not applied to invoice | Prepay account config (Tangible flag, JE code type), or negative prepay balance | **§12** — JBCDE_PREPAY_ACCOUNT code table; prepay balance must not be negative |
| CTF failure hold (JB390) reason code I or D | Operated/Balancing-Interest mismatch (I) or DOI tier deleted after posting (D) | **§13** — fix property Operated flag / DOI, or GL/AP reversal+reclass; move via JB350/JB390 |
| Process erroring/odd only after a V16/V17/Permian/MEW upgrade | **Client-layer (CEN/QFC) metadata not synced** from core; config reset on patch | **§14** — sync missing client-layer rows from DEVA1; re-check in the client layer so patches don't wipe it |

---

## 2. Pipeline & Concepts

```
[GL / AP / AR coded transactions]  +  [DOI master (QDO)]  +  [Property master (PR005)]  +  [Billing decks/tiers + AFE + Overhead rates (JB010)]
      │
      ▼  JBGLIMPORT / QCFSIMPCYC  → stage to CTF (cost transaction file = JBTRN_CTF / JB080)
[CTF]  → JB350 Reassign Deck / JB390 CTF Failure holds
      │
      ▼  JB005 "Process of JIB":  Property Allocation → Owner Allocation → Invoice Preparation → (Rebill variants) → Finalize & Post (JBLDJE2CAS) → Roll Date (JBROLLDATE)
[JBTRN_OWNR_ALLOC, JBTRN_JIB_JOURNAL, JBTRN_INVOICE_HEADER]
      │
      ├──► JOURNALIZE to QCFS/GL  (Finalize & Post creates the billing journal → posts to GL)
      └──► EXPORT  (JBINVJIBLK → JBSTG_JIBLINK_EXPORT_FINAL → EnergyLink / JIBLink file)
```

### Key terms (Quorum / QCA upstream vocabulary)
- **JIB** = Joint Interest Billing — billing each working-interest owner their share of operated-property costs (and crediting their revenue/prepay).
- **CTF** = Cost Transaction File (tables `JBTRN_CTF` / `JB080`). Every billable GL/AP transaction lands here before allocation. "JIB out of balance" almost always means CTF vs GL (`GL014`) drift.
- **DOI** = Division of Interest (QDO module, screens DO004 etc.; tables `DONL_DO_DETAIL`). Defines each owner's decimal interest by **Property + Tier + Interest Type + Interest Type Sequence No**. **A single owner with two interest types (e.g. DI Balancing-Interest + WI Working-Interest, or WI + MI Unleased-Mineral) on the *same* Interest Type Sequence No causes a cartesian double in Owner Allocation** (§7) — the #1 Owner-Alloc data trap.
- **Billing deck / Tier** = the DOI version effective for a service date. Rebills fail if the **service date predates the tier's effective date** (no approved tier found) — §8.
- **JB005** = "Process of JIB" control screen; you roll/run each step from here. Steps: Initiate Billing Cycle, Property Allocation, Owner Allocation, Invoice Preparation, Rebill (Property/Owner), Finalize & Post, Roll Date. **All JIB steps are rerunnable EXCEPT Finalize & Post.**
- **Process codes (JBxxx)** — `JBGLIMPORT` (import GL→CTF), `QCFSIMPCYC` (QCFS import cycle), `JBPREPROOF` (proof billables into CTF), `JBPROPALLC`/`JBPROPALLOC` (Property Allocation), `JBOWNALLOC` / `JBOAMAIN` (Owner Allocation), `JBREBILL` (Rebill Allocation; `JBREBREVNW` = rebill reversal new), `PAREBILL`/`JBOA…` rebill steps, `JBLDJE2CAS` (Finalize & Post / load JE to QCFS), `JBVALCDBLK` (Validate Code Block), `JBROLLDATE` (roll the JIB month; `JBJEHISTNW` moves journal → history), `JBPREPAY` (prepay), `JBINVJIBLK` (export to JIBLink), `JBCTFDOI` (DOI CTF failure reversal), `LOSEXTCHLD`/LOS import.
- **QPEC** = the Quorum batch process engine (server processes). JIB steps run as parent + child QPEC jobs. **`QPEC.ini` / `QPEC.exe.config` `CommandTimeout`** and global key **`COMMAND_TIMEOUT_SECONDS`** gate how long a step may run. A patch deployment frequently **resets these to the 900/3600 default** → mass timeouts (§4).
- **Code block / keyword derivation** — JIB maps each transaction to GL accounts via **events/entry types** (`JBXRF_KEYWORD_DERIVATION`), configured on **JB084** (decision fields incl. ACCOUNTING CODE) and **JB500** (event Cr/Dr account lines, intercompany). Missing setup → "Event and Entry type not defined…" (§5). **GL013** = chart-of-accounts JE code type; **GL105** = the code-block column rules (TIER / OWNER NO / DO TYPE / SURPLUS = Allowed/Optional/Not Allowed) — a column set to **NOT ALLOWED** blocks Finalize & Post with "code block item not allowed for account."
- **PRT line** = the owner header (number/name/address) line in the EnergyLink/JIBLink file. The export proc (`UPS_JIB_LINK_EXPORT_CORE`) **omits PRT — and the owner — if any of Address1/City/State/Country/ZIP is null** (§11). The State field is the usual culprit.
- **Client layer (CEN/QFC/QCEN, "UPS")** — per-client metadata/config layer over core (UPS). **Fixes or config checked into core but NOT into the client layer get wiped on the next patch/upgrade** — the root cause of most "broke after upgrade" cases (§14).

---

## 3. Decision Tree

```
QCA JIB case
│
├─ A JIB step crashed / "Stopped Processing on Error" / timeout?  →  GET PQID + STEP NAME + EXACT ERROR (read Batch Process Msgs)
│   ├─ "Timeout exceeded…" / SQL command timeout after ~1 hr        → §4  (QPEC CommandTimeout / COMMAND_TIMEOUT_SECONDS / chunk size; usually a post-patch reset)
│   ├─ "Event and Entry type not defined in JBXRF_KEYWORD_DERIVATION"→ §5  (JB084 decision field + JB500 event lines)
│   ├─ "code block item not allowed for account" / not sum to zero  → §5/§6 (GL105 column NOT ALLOWED → Optional; or §6 staging gap)
│   ├─ "Failed to retrieve DO info" / Owner Alloc CE/SPE            → §7  (DOI interest-type-sequence cartesian)
│   ├─ Property Allocation SPE / DOI validation on rebill          → §8  (tier eff-date / PA-rebill rolled back)
│   ├─ Process held by LOCKS / "system canceled NO LOCK"           → release lock in QP110 Active Lock Monitor, rerun (§17)
│   └─ "Continue Process on Failed Execute is FALSE for …"         → upstream step failed first; fix that step; (also a corrupted QPEC.ini key, 24-00984191)
│
├─ JIB output WRONG (process didn't crash)?
│   ├─ JIB / GL out of balance, GL014 ≠ JB080, missing I/C lines    → §6  (restage STRAN_CORE_INTFC; rerun JBGLIMPORT)
│   ├─ Recon report JBR033/JBR055 don't tie                         → §6/§10 (orphaned JBTRN_OWNR_ALLOC from a cancelled rebill; dedupe)
│   ├─ Owner decimals doubled                                       → §7  (DOI interest-type-sequence)
│   ├─ Producing/Drilling/Completion OH wrong / triplicated / dup   → §9/§10
│   └─ Duplicate CTF lines                                          → §10 (connection drop or A&P collateral)
│
├─ Export to EnergyLink/JIBLink?
│   ├─ Owner missing / no PRT line                                  → §11 (BA State/address null)
│   ├─ Out of memory / "can't get record count"                     → §11 (Fetch_Size/Fetch_Order; flat-file workaround)
│   └─ File won't land / path blank                                 → §11 (set Import/Export Definition path; create JIBLINK folder)
│
├─ Prepay / Cash Call?                                              → §12 (JB340; JBCDE_PREPAY_ACCOUNT; negative balance blocks application)
│
├─ CTF failure HOLD (JB390) / property-type / DOI tier?            → §13 (reason code I = Operated+Balancing; D = DOI tier deleted)
│
├─ Started right after a V16/V17/Permian/MEW upgrade?              → §14 (client-layer metadata not synced; config reset on patch)
│
└─ "How do I…", warning-only, audit, "why didn't X bill?"         → §17 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — JIB process timeouts

**The single largest actionable signature.** A JIB step (most often **JBREBILL**, **Finalize & Post = `JBLDJE2CAS`**, **`JBROLLDATE`**, or **`JBJOURNAL`**) runs ~1 hour and dies with **"Timeout exceeded while waiting for execution of this Batch of Processes"** or a SQL command-timeout. The cause is almost always a **timeout-config value reset by a patch**, sometimes amplified by genuine data volume.

**Root causes & fixes seen:**
- **Patch deployment reset the QPEC command timeout to the default.** Set **`CommandTimeout` in `QPEC.ini` AND `QPEC.exe.config`** from 3600 → **18000** (5 hr) on **all** QPEC servers, then do a **graceful QPEC restart**. This must be re-done after **every** patch for that client. (26-01104563, 26-01064034 JBREBREVNW step, 26-01068706, 25-01057580/25-01053574 JBLDJE2CAS, 25-01041819 JBROLLDATE→7200s.)
- **Global config keys** rather than the ini: **`COMMAND_TIMEOUT_SECONDS`** raised to 14400 (25-01006930) / **`DATABASE_COMMAND_TIMEOUT`** 900→1900 (25-01031905); these live at client layer and reset to 900 if not checked into the client layer (25-01024015 — "resolved in V16, updated at core UPS, never checked into CEN client layer, reset to 900").
- **Chunk-size keys** for the journal insert: **`INS_SUBMIT_JOURNAL_CHUNK_SIZE`** raised to 20 for `INS_SubmitJournals` (25-01024308); JB_Journal chunk processing modified (25-01029948).
- **Child-job throughput** (true volume, not just timeout): JBREBILL/JEREBILL launches one child per rebill; if only N run in parallel they can't finish inside the parent's 4-hr wait. Fix = **(1) reduce rebill volume**, **(2) dedicate more QPECs to the child job** (e.g. 12 of 16), and **global key `JB_OWNERALLOC`/`JB_GLOBAL`** sizing (24-00978503, 24-00977632 — 360M-record stage from un-purged data, 24-00982962 Owner Alloc → Patch 21 perf SQL `m_SEL_OwnerAllocStageSvcDt` + QPEC.ini 28800, 24-00942090 `JB_OWNERALLOC`=500).
- **`MAX_IDLE_MEMORY_MB`** raised 750→1000 to stop QPEC graceful restarts from killing `QCFSIMPCYC` (22-00653763).

**Fix recipe:**
1. Get **PQID + failing step name + exact error**. "Timeout exceeded…" or a named registered-SQL timeout = config, not a code bug.
2. **Check the timeout values first** (they reset on patches): `QPEC.ini` + `QPEC.exe.config` `CommandTimeout`; global `COMMAND_TIMEOUT_SECONDS` / `DATABASE_COMMAND_TIMEOUT`. Raise to the client's known-good value (commonly 18000), on **all** QPEC servers, then **graceful-restart QPEC**.
3. **Make the change at the client layer** so the next patch doesn't wipe it (25-01024015).
4. If still slow, it's genuine volume → raise chunk size (`INS_SUBMIT_JOURNAL_CHUNK_SIZE`), dedicate more QPECs to the child job, reduce rebill count, and pursue an **Archive & Purge** project (un-purged CTF/interface history is the usual volume driver, 24-00977632).
5. Versions **before the "P&S" (performance & stability) JIB work** (≤2022.04 / 2023.04) will keep timing out — recommend upgrade; raising the ini is the stopgap (25-01057580/25-01053574, 25-01057922).

---

## 5. Cluster B — JBXRF_KEYWORD_DERIVATION / code-block / event setup

Pure **Application Configuration** in the JIB code-block / event-derivation setup screens. JIB can't post a transaction because there's no rule telling it which GL accounts the event/entry maps to.

| Error / symptom | Root cause | Fix | Case |
|---|---|---|---|
| "Event and Entry type not defined in **JBXRF_KEYWORD_DERIVATION** for event **INTERCO** and entry type C" | Company has no INTERCO Cr/Dr rule; missing ACCOUNTING CODE decision field | **JB084** → Event 35 INTERCO → add ACCOUNTING CODE decision field at precedence 6; add Cr(C)/Dr(D) lines for the company in **JB500** | 24-00949118, 23-00906511 (co 950), 23-00922620 (co 74), 25-01030970 (accts 0141.026/.081) |
| "…for event **ARCLEAR** entry type C" | Missing decision fields in JB084 for the new ARCLEAR event | **JB084** → Event 113 ARCLEAR → add decision fields Capital AFE Ind=3, Project/AFE Type=4, Property Type=5, Account Code=6, JIB Group Code=7 | 24-00949799 |
| "…for event **PREPAY**" | ACCOUNTING CODE missing in JB084 for PREPAY | **JB084** → Event 34 PREPAY → step into last line, add ACCOUNTING CODE at precedence 6, Update | 25-01050452 |
| JIB Close "**code block item not allowed for account**" (lists accounts) | The JE code type's column (SURPLUS / TIER / MAJ PROP CODE / DO TYPE / OWNER NO) is set **NOT ALLOWED** in GL105 | Find the account's **JE CODE TYPE** in **GL013** (e.g. LEASE, WIPACCR), then in **GL105** for the Global Company flip that column from **Not Allowed → Optional**, Save, rerun | 23-00908848 (SURPLUS/LEASE), 25-01006299 (WIPACCR TIER/OWNER NO), 25-01019591 (overhead accts) |
| Drilling Overhead not interfacing to AFE module | Gross-value formula = "GROSS=0"; AFE Interface checkbox off | **MT100** AFE Config tab: change Gross Value Formula Id 20004→20003 ("Gross Amount"); **MF035**: check AFE Interface for each overhead type | 22-00828758 |

**Fix recipe:** the error text names the **event** and **entry type**. Open **JB084**, select that event, and ensure the required **decision fields** (esp. **ACCOUNTING CODE**) exist at the right precedence; then ensure **JB500** has the Cr/Dr account lines for the affected company (intercompany needs both sides). For "code block item not allowed," trace account → JE code type in **GL013** → flip the blocked column to **Optional** in **GL105**. These are guided config changes, not defects.

---

## 6. Cluster C — JIB out of balance / GL does not tie

JIB Close blocks (or recon reports JBR033/JBR055 mismatch) because not all interface records made it into the JIB tables, leaving missing intercompany offset lines.

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Batch fails "amounts … do not sum to zero"; missing I/C lines | A subset of records didn't transfer from **`STRAN_CORE_INTFC`** into the `BATCHJOURNALENTRY` tables during `QCFSIMPCYC` (chunking/grouping flaw) | Delete the incomplete batch, **restage the missing `STRAN_CORE_INTFC` rows by `SOURCE_CTF_ID` range**, rerun QCFSIMPCYC → balanced batch | 25-01047112 |
| `GL014` ≠ `JB080` (CTF) by a small amount | Records staged from `SSTAG_CORE_INTFC` into `STRAN_CORE_INTFC`/`SEXTN_CORE_INTFC_JIB` failed (temp table created, no rows moved) | Script to recreate the temp table and stage the rows per the SQL trace; rerun | 25-01031905, 25-01028155 (deadlock isolation, see §7/ADO 1739552) |
| Future-dated batch processed by Prepay set `PROCESS_IND=0` → JIB never pulls it; GL014 vs JB080 off | Prepay job flips the indicator on future-dated accounting months | Restage missing `JB080` rows, rerun JBGLIMPORT | 26-01066700 |
| Recon JBR055/JBR033 don't tie | **Cancelled JBREBILL left orphaned rows in `JBTRN_OWNR_ALLOC`** → data corruption | Data-cleaning script to remove the orphans | 25-01053103 (Customer Error), 23-00929023 (SSTAG→STRAN split) |
| Wrong LOS_IMPORT re-interfaced history into `QSTAG_CORE_INTFC_IMP` → out of sequence/purged → missing Nov transactions | Incorrect interface-process execution | Engineering remediation scripts: identify qualifying JIB txns, **include allocation cost centers, validate BOTH voucher no AND business unit**; rerun JBGLIMPORT | 25-01059370 (long-term code fix pending hotfix) |

**Fix recipe:** "out of balance / doesn't tie" = an **interface staging gap**, not a calc bug. Pull the **SQL trace** for the PQID (`QARCH_QFCBATCH_SQL_TRACE`), find where rows stopped flowing (`SSTAG_CORE_INTFC` → `STRAN_CORE_INTFC` → `SEXTN_CORE_INTFC_JIB` → `BATCHJOURNALENTRYLINE`), delete the incomplete batch, **restage the missing rows by `SOURCE_CTF_ID` range scoped to the BU**, and rerun the import. Verify-SELECT before any delete/insert. If a **cancelled rebill** is suspected, check `JBTRN_OWNR_ALLOC` for orphans.

---

## 7. Cluster D — Owner Allocation errors

Owner Allocation (`JBOWNALLOC` / `JBOAMAIN`, JB005 step 200) failing with status **CE** or **SPE**, "Failed to retrieve DO info," or producing **doubled decimals** for an owner. The dominant root cause is a **DOI data shape the allocation SQL doesn't expect**, not a code bug — though the underlying recursive join is a long-standing fragility.

**Root cause (the recurring trap):** an owner who has **two interest types on the SAME `INT_TYPE_SEQ_NO`** with overlapping effective dates in `DONL_DO_DETAIL` — e.g. **DI (Balancing Interest) + WI (Working Interest)**, or **WI + MI (Unleased Mineral Interest)**. The JIB Owner-Allocation SQL has a recursive join meant to *combine* an owner's lines across sequence numbers and **does not join on the interest-type column**, so two types on one sequence produce a **cartesian join → the owner's decimal is doubled** (or the allocation errors). (26-01104274, 25-01043760 WI+MI → CE, 25-01043578 SPE "Continue Process … FALSE for JBOAMAIN".)

**Fix (workaround = the resolution in every case):** put the differing interest types on **distinct Interest Type Sequence Numbers** via DO maintenance. Options:
1. **End-date the DI row** so it no longer overlaps the WI, or
2. Have the DO team **assign the "DI" (or "MI") owners to Interest Type Sequence 2**, or
3. If no DI/MI row is needed, **remove it** from the DO setup.

**Other Owner-Allocation issues:**
- **Performance/timeout** (ran 6+ hrs then failed): Patch 21 perf change to registered SQL **`m_SEL_OwnerAllocStageSvcDt`** + raise QPEC.ini; query-timeout on **`m_INS_PopulateJEStaging` / `m_INS_PopulateJEStaging_Special`** (ADO 1671837). (24-00982962, 24-00983665, 22-00660024 index applied via patch.)
- **Deadlock victims** during balance refresh (25-01028155): ADO **1739552** isolated JIB jobs from the generic `BUSSVCRUN` into new process IDs (`BSVCLOSE`, `BSVCRFRSH`, `PSTWKBAL`) with locks to prevent overlaps; SM006 now launches the new IDs.
- **"NO RECORD FOUND IN OWNER ALLOCATION STAGING TABLE" warning** — often **invalid/benign**; billable charges processed correctly, JIB posted (22-00640510). All JIB steps are rerunnable except Finalize & Post.

**Fix recipe:** "Failed to retrieve DO info" or doubled decimals → inspect `DONL_DO_DETAIL` for that property/owner for **two interest types on one `INT_TYPE_SEQ_NO`** (§16 query E); resolve via DO maintenance (distinct sequence numbers). Pure long-runtime/timeout → §4 + Patch 21 perf SQL. Deadlocks → confirm ADO 1739552 process-isolation is deployed.

---

## 8. Cluster E — Property Allocation & Rebill

Property Allocation (`JBPROPALLC`/`JBPROPALLOC`) and the **Rebill** family (reverse/rebill, "Rebill Property Allocation," "Rebill Owner Allocation").

**Most important fact:** **"Rebill Property Allocation" (PA-rebill) was rolled back / removed across all versions** because it caused JIB collateral. Clients should **rebill based on owner-property** instead. The **PAREBILL** step should NOT appear in JB005 — if it reappears (e.g. re-added by a QDBMgr package), run a script to remove it. (26-01071359, 25-01029822 "PA rebill rolled back due to JIB collateral," 25-01031382 / 25-01062955 "remove PAREBILL from JB005," 23-00916835 bug **#1609783** hotfix in 2022.04.)

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Rebill SPE / **DOI validation error** | Service date on the original record is **before the new billing-deck tier's effective date** → no approved DOI tier found | **Back-date the troublesome DOI tiers** identified by the query | 22-00852586 (ChangeConfig), 1607218, 1459297 |
| Property Allocation **SPE / Query Timeout** | Volume / timeout (`CMD_PropAllocHld`) | §4 timeout config; hotfix (22-00705040) | 22-00705040, 1558159 (Oct-2022 PropAlloc timeout) |
| Rebill-of-rebill creating **incorrect entries** | Registered SQL defect | Registered SQL modified | 25-01027776 |
| **Duplicate reversals** for rebills created in JB020 + drilling OH | Reversal SQL not joining on accounting date (cartesian) | See §9/§10 (`m_SEL_DrillingOverheadReverse` joins on acctg date) | 25-01011716 |
| Rebill changes to JB010/JB020 tabs didn't reset dependent jobs | Dependency reset gap | ADO **1661305** — JB010/JB020 rebill-tab updates now trigger dependency reset of all JIB jobs | 24-00956003 |
| Rebill Owner Allocation warning / partial rebills | Incomplete/partial rebills left behind | **Rerun JBREBILL** to clear partial rebills | 24-00967041 |
| PAREBILL `m_CMD_InsertOAIdTempTable` slow | Performance | Patch 05 (CNR) perf change to PAREBILL step | 26-01080602 |

**Fix recipe:** for rebill DOI-validation failures, the fix is **master-data** — back-date the DOI tier so an approved tier covers the original service date. If a user is trying to use **Property-Allocation rebill**, redirect them: that path is **removed**; use owner-property rebill. For partial/warning rebills, simply **rerun JBREBILL**.

---

## 9. Cluster F — Producing / Drilling / Completion Overhead rebill

A persistent **Software Defect** family around overhead (OH) calculation and rebill/reversal. Implemented in `Quorum.Upstream.QCA.ClassicBatch /QPDllCostAcctgJIB/` (`QPSJIBDrillingOverhead.cpp`, `QPSJIBPercentOverhead.cpp`, `QPSJIBConstructionOverhead.cpp`, `QPSJIBCatastropheOverhead.cpp`).

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Duplicate reversal entries** in `JBTRN_CTF` and `JBADT_DRILLING_OH_AUDIT` when rebilling JB020 periods + running drilling OH | Reversal registered SQL **`m_SEL_DrillingOverheadReverse`** didn't join on **accounting date** → cartesian/duplicate rows | Hotfix: updated the reversal SQL to **join on accounting date** | 25-01011716 |
| Producing & Drilling OH processes **rely on DESCR fields** for rebills/reversals (fragile matching) | Reversal matching keyed on description text | ADO **1756221** (Proposed) — stop relying on DESCR fields | (open) |
| **Producing OH rebill rates missing** | OH rebill rate data not loaded | DB script to load corrected producing-OH rates into **JB010**; later hotfix | 23-00910833, 22-00867172, 23-00893607 |
| **Producing Overhead report triplicated** results | Audit report (`JBR020_Producing_Overhead_Audit`) not joining on Country+State | Aug hotfix updated the report join | 22-00832094 |
| **DCOH escalation** causing producer-OH issue; OH escalation rate bug | Escalation calc defect | ADO **Bug 113455** "Overhead Escalation Rate Bug" (Closed) | 22-00660006, 22-00655402 |
| Producer Overhead Maintenance "Input string not in correct format" / unhandled exception | Screen defect (older version) | Software upgrade | 22-00852712, 22-00686824 |
| Various Producing OH rebill "not working" | Patch / script | Included in Nov/SEP patches; script to correct POH rebills | 22-00583813, 22-00577352, 22-00577380, 22-00577347 |
| Customer set **duplicate Rate Suffixes** in JB010 → Producer OH Maintenance error | Customer Error (config) | Make Rate Suffixes unique; correct historical rows | 25-01052904 |

**Fix recipe:** OH rebill duplicates → confirm the **`m_SEL_DrillingOverheadReverse` accounting-date-join hotfix** (25-01011716) is in the build; otherwise dedupe `JBTRN_CTF`/`JBADT_DRILLING_OH_AUDIT` and apply the patch. Missing/triplicated OH → check **JB010** rate/suffix setup (must be unique) and report joins. Escalation wrong → ADO 113455 family.

---

## 10. Cluster G — Duplicate transactions / duplicate reversals

Duplicate rows block JIB Close (out of balance) or inflate reports. Two distinct origins.

| Origin | Symptom | Fix | Case |
|---|---|---|---|
| **ADO/COM connection drop** mid-process | CTF records duplicating; JIB out of balance / pre-lim won't go to final | Script to remove dups from **`JBTRN_CTF`**; manual tie-out. Mitigation: **QPEC auto-recovery patch (package 67)** for ADO/COM errors | 22-00572195, 22-00579681, 22-00520502, 22-00518326, 22-00553519, 22-00579691 |
| **Archive & Purge collateral** | Duplicate batch imports introduced by the A&P effort; PRGCOREINT generating dup data | Flip batch statuses / back out interfaced transactions; restage missing `JBTRN_PROCESS_ACTIVITY` row | 25-01014595, 25-01042074, 25-01043790, 25-01023695 (missing `JBTRN_PROCESS_ACTIVITY` insert), 25-00998756 |
| Drilling-OH reversal cartesian | See §9 | `m_SEL_DrillingOverheadReverse` acctg-date join | 25-01011716 |
| Duplicate I/C lines (JB350 metadata) | JBR036 balance / JB350 metadata recon | Script | 22-00655414, 22-00649143 (`JBDEPPRG` step deleting CTF rows added by EBS INT-2051) |

**Fix recipe:** identify the origin first. **Connection-drop dups** → script-delete from `JBTRN_CTF` keyed on the duplicated batch + manual tie-out; recommend the QPEC auto-recovery patch. **A&P collateral** → check `JBTRN_PROCESS_ACTIVITY` for a missing process row (a failed `JBPREPROOF` in the prior version inserts CTF rows without the activity row, 25-01023695) and restage. Always verify-SELECT in a transaction before deleting.

---

## 11. Cluster H — EnergyLink / JIBLink export

`JBINVJIBLK` builds the EnergyLink/JIBLink file from `JBSTG_JIBLINK_EXPORT_FINAL` via stored proc **`UPS_JIB_LINK_EXPORT_CORE`** (a.k.a. `USP_JIB_LINK_EXPORT`).

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| An owner / invoice **missing from the file (no PRT line)** | The export proc populates the **PRT (owner) line only if Address1, City, State, Country AND ZIP are all NOT NULL**; the BA had a null **State** | Populate the BA address (usually the **State** field; choose "Unknown" if truly unknown) on the Business Associate screen, re-export | 24-00977565, 26-01104038, 26-01080854, 22-00867475 (State field), 24-00942767 (rerun Invoice Prep) |
| **Out of Memory** / "Can't get record count for recordset" (`Select_Fields_From_Table`) | A **client override of JBINVJIBLK dropped the `Fetch_Size` / `Fetch_Order` params** that core uses to chunk the data | Add `Fetch_Size`/`Fetch_Order` from core as **Environment Specific** to the client override | 26-01085608 |
| JBINVJIBLK SPE on system source **"OA"** (works for "REB") | Data volume on the OA pull | **Workaround:** export `JBSTG_JIBLINK_EXPORT_FINAL` to a flat file (SSMS Export Data wizard) and import to JIBLink manually | 24-00968435 |
| File won't land / "File Path" blank / no JIBLINK folder | Import/Export Definition path not set, or folder doesn't exist on the FS server | Maintenance App → Import/Export → Import/Export Definition → set path for **JIBLINKEXP**; have Qcloud create the **JIBLINK** folder (KB 000002743) | 23-00888244, 23-00933703, 25-01043582, 25-01060821, 25-01037203 |
| Export error after a patch changed the SP | Patch altered `USP_JIB_LINK_EXPORT_CORE` | Revert the SP to pre-patch version, **re-generate the `USP_JIB_LINK_EXPORT` sysgen object**, rerun JBINVJIBLK, refresh env snapshot | 25-00996367 |
| One value omitted from JIBLink; advances duplicating | Address null / advances logic | RCA: address field; advances dup resolved in 2020 build | 24-00977565, 22-00618219 |

**Fix recipe:** "missing owner in EnergyLink" is **almost always a null BA address field (State)** — the export proc silently skips owners without a complete PRT. Memory errors → the client override is missing the core **Fetch_Size/Fetch_Order** chunking params, or fall back to the flat-file export. Path errors → set the **JIBLINKEXP** Import/Export Definition path and have Qcloud create the folder.

---

## 12. Cluster I — Prepay / Cash Calls (JB340)

Prepayments and AFE cash calls flow to **JB340 (Prepay/Prepayment Maintenance)** via **`JBPREPAY`**, then are applied as credits during Owner Allocation.

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Prepay entries for a BA **didn't move to JB340** | GL entries with property+owner detail were treated as **Direct Bill** instead of Prepayment accounts | Reverse impacted GL batches; remove Prepay JIB group code from prepayment account in **GL013**; create offsetting AR076 zero-invoice entries (0300.006 / 0300.005); rerun JBPREPROOF → JBPREPAY; manage holds in JB360/JB355; rerun JB005 prop-alloc→owner-alloc | 26-01091354 |
| **Cash Calls tied to AFE not populating JB340** | Prepay account code-table flag | Update Code Table **34034 (JBCDE_PREPAY_ACCOUNT)** — set **Tangible Flag = N** | 25-01041614 |
| **Cash calls not applied to JIB invoices** (no auto-application) | Prepay **balance is negative** → won't advance to Owner Allocation | Prepay balance must not be negative; correct the balance so it applies | 25-01046394 (Training) |
| Rebill credits not returned to prepay balance / excluded from EnergyLink | Billing-owner amount summed to zero → activity suppressed; credits weren't from a prepayment so no prepay balance to attach to | Working as designed — update the EnergyLink balance manually as done in v16 | 25-01016987 |
| JB340 Prepayment Maintenance won't filter | Screen defect | Worked by Core Engineering (Spring 2023); MEW upgrade | 22-00868097, 22-00832219 |
| Prepay reporting (GL025-originated prepay adjustments not summed) | Reporting defect | Reporting fix | 23-00877522, 23-00917690, 23-00891848 (fixed 2021.10) |

**Fix recipe:** prepay "not showing / not applying" → check (a) the account is configured as a **prepayment account** (not Direct Bill) with correct JIB group code, (b) **JBCDE_PREPAY_ACCOUNT (code table 34034)** flags, and (c) the **prepay balance is not negative** (negative balances are skipped by Owner Allocation). For AR076/credit reconciliation, remember JIB suppresses zero-sum billing activity (§17).

---

## 13. Cluster J — CTF failure holds & property-type / DOI key errors

Transactions land on a **CTF failure hold** (visible/reversible in **JB390: CTF Failure Reversal** and **JB350: Reassign Deck**) when the property/DOI setup is inconsistent with the voucher coding.

| Failure / symptom | Root cause | Fix | Case |
|---|---|---|---|
| CTF Failure reason code **I** — "Balancing Interest DOI Booked as Operated" | Charge booked to an **Operated** property whose DOI includes a **Balancing Interest** owner → JIB tries to allocate only part of the amount | **Either** make the property **Non-Operated** (PR005, uncheck Operated, set operator BA) and rebook with Non-Operated voucher; **or** have DO maintenance change the owner from **DI Balancing Interest → WI Working Interest**, then move the charge from the failure side to the CTF side in **JB390** | 25-01020495 |
| CTF Failure reason code **D** / "invalid DO Key combination" | **DOI tier was deleted after the entry posted but before JIB import** | **Either** recreate the JIB DOI for that Property/Tier, **or** do a **GL/AP reversal + reclass to a valid tier** | 26-01069550 |
| "Failed to retrieve DO info for PropNo…" in Owner Alloc | DOI interest-type-sequence overlap | See §7 | 26-01104274 |
| Cost on hold after property mistakenly set to Allocation Type | Property type set wrong in PR004 | In **JB350: Reassign Deck**, select the line → Links → **"Ready to Bill"** → Update | 25-01045998 |
| Allocation hold can't be released; property type can't change after CTF | Property placed on hold in JB350; type locked once in CTF | Reset property type to **AL**, book a reversal (nets to zero), change to **PR**, rebook the expense | 24-00950762 |
| "code block item not allowed" at Finalize & Post | See §5 (GL105) | GL105 column → Optional | 25-01006299 |

**Fix recipe:** read the **CTF Failure Reason Code** in JB390. **I** = Operated property + Balancing-Interest DOI mismatch → fix the property Operated flag *or* the owner interest type. **D** = DOI tier deleted post-posting → recreate the DOI *or* GL/AP reversal+reclass. Use **JB350 "Ready to Bill"** to release a hold once the underlying setup is corrected. Note: deleting a DOI tier after posting is not blocked by validation (26-01069550) — a known gap, not a bug to fix per-case.

---

## 14. Cluster K — Upgrade regressions / client-layer drift

A large share of post-upgrade JIB cases (V16→V17, Permian/PNR/MEW/Centennial upgrades) trace to **the client metadata/config layer not being in sync with core (UPS)**, or a fix existing in core but never checked into the client layer.

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Timeout reset to 900s after upgrade; "resolved in V16 but reset" | Timeout value updated at **core (UPS)** but **never checked into the client (CEN) layer** → wiped on patch | Set the value at the **client layer** so patches don't overwrite it | 25-01024015, 26-01104563, 26-01068706 |
| GL025 / Security groups / processes erroring after cutover | Missing client-layer rows (e.g. `QXRF_SECGRPID_CDTBL_ID`, `QXRF_AFE_VALID_POST_STATUS`) not synced from DEVA1 | **Sync the missing rows from DEVA1** to the client env | 25-01022895, 25-01000811 (sysgen collision `TR_RI_SCODE_CURRENCEY_D`) |
| Report templates reverted to older version after patch | Custom reports not in the patched layer / manually changed | Confirm patch report templates match; check reports into the correct layer | 23-00905057 |
| Imbalance after upgrade because a job errored in V16 pre-cutover | An errored V16 job wasn't corrected before restarting JIB in V17 | Script to reset the data in V17 so the errored process can rerun, then normal JIB | 25-01023424, 25-01023695 |
| JBROLLDATE / Finalize & Post timeouts after upgrade | Timeout / P&S work not in the client's version | §4 timeout config; upgrade for P&S improvements | 25-01006930, 24-00978503 (QCloud 1.0/v16) |
| MT100 import setup wrong after upgrade | MT100 GL\|QCFS import checkbox/config | Check the import box + setup in MT100; rerun QCFSIMPCYC | 25-01045248, 25-01045163 |
| Dynamic Docs config wrong after upgrade | Incorrect Dynamic Docs parameter mapping | Remove the incorrect config | 25-01006932, 25-01050090 |

**Fix recipe:** for any "worked before the upgrade" JIB case, **compare the client layer (CEN/QFC/QCEN) against core/DEVA1** for the affected metadata/config, and **sync the missing rows**. Re-apply timeout/config at the **client layer** so the next patch doesn't reset it. This is the single most important habit for upgrade-season JIB triage.

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1739552** | Bug / **Closed** | POSTWKFL — Account Balance deadlock prevention (new process IDs BSVCLOSE/BSVCRFRSH/PSTWKBAL) | §7/§10 | 25-01028155 |
| **#1661305** | Requirement / **Closed** | JB010 & JB020 rebill-tab updates trigger dependency reset of all JIB jobs | §8 | 24-00956003 |
| **#1671837** | Requirement / **Closed** | JIB Owner Allocation query timeout — `m_INS_PopulateJEStaging` / `_Special` | §7 | (Owner Alloc perf) |
| **#1609783** | Bug / **Closed** | EQCU — Rebill Property Allocation minimum-hold/release errors & cost subledger (PA-rebill) | §8 | 22-00824179, 23-00916835 |
| **#1611528** | Patch / **Completed** | CNR — Patch 3 on 2022.04 Upstream (carried the PA-rebill hotfix) | §8 | 23-00916835 |
| **#1607218** | Bug / **Closed** | MAC A1 — JB300 property-allocation rebill DOI validation error | §8 | (rebill tier eff-date) |
| **#1459297** | Bug / **Closed** | EQC — JIB property allocation rebill not processing | §8 | — |
| **#1558159** | Bug / **Closed** | ERF — Oct-2022 JIB Property Allocation SPE Query Timeout | §8/§4 | 22-00294331 |
| **#1756221** | Bug / **Proposed** | Producing & Drilling Overhead rely on DESCR fields for rebills/reversals | §9 | 25-01011716 (related) |
| **#113455** | Bug / **Closed** | Overhead Escalation Rate Bug | §9 | 22-00655402, 22-00660006 |
| **#1372009** | Bug / **Closed** | Display correct error messages for process JBREBILL | §8 | — |
| **#1645389** | Bug / **Closed** | CEN — JBREBILL is failing | §4/§8 | (CEN rebill) |
| **#1568338** | Requirement / **Closed** | OOC Upstream 2020.03 Hotfix Dec-2022 (ERF) | §8 | 22-00826253 |
| **#1693814** | (feature) | 2026.04.1.0 — JB300 "Rebill Current DOI" column | §8/§17 | 26-01099218 |
| **#1661305 / 1671837 / 1735085** | Closed | JBOWNALLOC/JBREBILL statistics + dependency work | §7/§8 | 24-00982962 |

> Several actionable cases were dispositioned **operationally** (data script / config / timeout change) with no single product WI: QPEC `CommandTimeout` resets (26-01104563, 26-01064034, 25-01057580), interface restage by `SOURCE_CTF_ID` (25-01047112, 25-01059370), `m_SEL_DrillingOverheadReverse` acctg-date hotfix (25-01011716), `JBCDE_PREPAY_ACCOUNT` Tangible flag (25-01041614). Confirm exact build/patch in the QCA release notes / patch tracker when stating fix availability. (Patches 7/8/10/11/12/18/21 are referenced across cases — patch numbering is per-client.)

---

## 16. Diagnostic SQL

> **Caveat:** QCA runs on SQL Server, per-client databases (e.g. `QCA`, `CEN_PRDA1UPS_QFC`). Table/column names below are taken from case repro text and code search; **verify against the client DB before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. The SQL trace for a failing JIB process (find where staging stopped / which registered SQL timed out)
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = '<PQID>' ORDER BY 1;

-- B. CTF vs GL out-of-balance check (JB080/JBTRN_CTF vs GL014) for a process period
SELECT BUS_UNIT_CD, SUM(AMOUNT) ctf_amt
FROM   JBTRN_CTF            -- a.k.a. JB080
WHERE  PROCESS_PERIOD = '<MM/01/YYYY>'
GROUP  BY BUS_UNIT_CD;

-- C. Incomplete interface batch — missing STRAN_CORE_INTFC rows by SOURCE_CTF_ID range (the 25-01047112 pattern)
SELECT * FROM STRAN_CORE_INTFC
WHERE  SOURCE_CTF_ID BETWEEN <lo> AND <hi> AND BUS_UNIT_CD = '<BU>';
-- compare against SSTAG_CORE_INTFC / QSTAG_CORE_INTFC_IMP / SEXTN_CORE_INTFC_JIB upstream.

-- D. Orphaned owner-allocation rows from a cancelled JBREBILL (recon JBR055/JBR033 won't tie, 25-01053103)
SELECT PROCESS_PERIOD, COUNT(*) FROM JBTRN_OWNR_ALLOC
WHERE  PROCESS_PERIOD = '<MM/01/YYYY>' GROUP BY PROCESS_PERIOD;

-- E. DOI interest-type-sequence cartesian trap (Owner Alloc "Failed to retrieve DO info"/doubled decimals, §7)
--    Red flag: same owner, same INT_TYPE_SEQ_NO, TWO interest types (DI+WI or WI+MI) with overlapping eff dates.
SELECT PROP_NO, BILLING_DECK, OWNER_NO, INT_TYPE_SEQ_NO, INT_TYPE_CD, EFF_DT, END_DT, DECIMAL_INT
FROM   DONL_DO_DETAIL
WHERE  PROP_NO = '<PROP>' AND DOI_TYPE = 'JIB'
ORDER  BY OWNER_NO, INT_TYPE_SEQ_NO, EFF_DT;

-- F. Active locks blocking a JIB step (clear in QP110 Active Lock Monitor, lock type e.g. ARC_INT_JB)
SELECT * FROM <active lock table / QP110 view> WHERE LOCK_TYPE_CD = 'ARC_INT_JB';

-- G. EnergyLink/JIBLink missing-PRT check — BA with an incomplete address (§11)
SELECT BA_NO, ADDR_LINE_1, CITY, STATE_CD, COUNTRY_CD, POSTAL_CD
FROM   <BA / business associate table>
WHERE  BA_NO = '<BA>';   -- any of STATE_CD/CITY/COUNTRY/POSTAL null → owner dropped from export

-- H. Missing process-activity row after a failed JBPREPROOF (A&P duplicate-import collateral, 25-01023695)
SELECT * FROM JBTRN_PROCESS_ACTIVITY
WHERE  PROCESS_ID = 'JBPREPROOF' AND PROCESS_PERIOD = '<MM/01/YYYY>' AND OPER_BUS_SEG_CD = '<SEG>';

-- I. AFE not valid for posting (Finalize & Post "AFE … not a valid status for posting", 25-01053579)
SELECT * FROM QXREF_AFE_VALID_POST_STATUS;   -- AFE status must match (Open=O); CLD/CAN are non-posting
```

---

## 17. Expected-Behavior / User-Education FAQ

~169 Training + ~138 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Owner Allocation **CE/SPE** — Failed to retrieve DO info" / "decimals doubled" | **DOI data setup** — owner has two interest types (DI+WI / WI+MI) on one Interest Type Sequence No → cartesian. Put them on distinct sequence numbers (DO maintenance) | 26-01104274, 25-01043760, 25-01043578 |
| "JBREBILL **completed with a Timeout WARNING** on JBOAMAIN — can I continue?" | **Yes** — a warning is not a failure. All child steps completed. **All JIB steps are rerunnable except Finalize & Post** | 26-01069392, 22-00628326, 22-00640510 |
| "Process **system canceled / NO LOCK** / step won't start" | A prior process holds a **lock**. Release it in **QP110 Active Lock Monitor** (Links → Active Lock Release), then rerun | 25-01055861, 23-00928396, 22-00646201 |
| "Owner missing from **EnergyLink** file" / "PRT line missing" | BA **address incomplete** — populate **State** (and City/Country/ZIP) on the BA; export skips owners without a full PRT | 26-01104038, 26-01080854, 24-00977565 |
| "**JB520 is empty / Critical**" | **JBROLLDATE** moves `JBTRN_JIB_JOURNAL` → `JBADT_JIB_JOURNAL_HISTORY` (step `JBJEHISTNW`) and clears the live table. Prior months live in the history table — working as designed | 25-01053136 |
| "Why didn't invoice X go through JIB?" | If it's an **AR** batch, AR doesn't normally feed CTF (GL/AP do). Check JIB Group / prepay config | 26-01102587, 25-01042243 |
| "**April hit the wrong tier**" / "how is the deck defaulted?" | Tier defaults: (1) AFE-coded expense → AFE master default tier; (2) no AFE → the JIB **Base Tier** checked on the DOI master | 26-01101429 |
| "**Cash calls not applied** to JIB invoices" | Prepay **balance must not be negative**; a negative balance won't advance through Owner Allocation, so it can't apply | 25-01046394 |
| "Rebill credits not in EnergyLink / invoice shows nothing" | JIB **suppresses zero-sum billing activity** (owners with no interest change get no rebill invoice); update the EnergyLink balance manually | 25-01016987 |
| "Cost on **hold** after I fixed the property type" | Release it in **JB350 Reassign Deck → Links → Ready to Bill**; if already in CTF you must reverse (AL) then re-book as PR | 25-01045998, 24-00950762 |
| "Error setting value for column POSTAL / DO key combination" | **Data hygiene** — trailing space in BA ZIP (delete it); or DOI tier deleted post-posting (recreate DOI or GL/AP reversal+reclass) | 26-01087703, 26-01069550 |
| "Finalize & Post — **AFE closed** / not a valid status for posting" | AFE status must be Open (O); CLD/CAN aren't valid for posting (`QXREF_AFE_VALID_POST_STATUS`). Change AFE status or reclass | 25-01053579, 25-01036426 |
| "Running **CSL/JBCTFDOI resets my completed Rebill steps**" | **Intentional dependency** (data-integrity guardrail) across Upstream releases — editing any of ~17 JIB setup/maintenance screens mid-cycle forces downstream reruns. Enhancement request → User Voice | 26-01091078 |
| "New **'Rebill Current DOI'** column on JB300 — what does it do?" | 2026.04.1.0 feature (WI 1693814): unchecked = resolve deck by **service date** (standard); checked = use **current DOI** for retroactive ownership changes. Does **not** enable Property-Allocation rebill | 26-01099218 |
| "JB390/JB330 **'maximum records shown'**" / can't copy to Excel | Not a bug — narrow the filter or click "More" (5000-row guard); copy via right-click grid → copy → Excel paste | 25-01045689, 23-00921889, 25-01044514 |
| "How do I set up allocation groups / multi-property AFE costs?" | Training — import templates (QCA AFE Cost Center, JIB Allocation Group Header/Detail); allocation defaults to Prorata when service date is future | 26-01079447, 26-01069484, 23-00924614 |

**Tell-tale it's user/expected:** an Owner-Alloc failure that traces to **DOI interest-type-sequence** setup; a **warning** (not an error) on a rerunnable step; a **lock** to release; an EnergyLink owner dropped for a **null BA State**; a "missing" journal because **JBROLLDATE** archived it; a tier/AFE-status question. **Verify the DOI/property/BA master data and whether the step merely warned, before treating it as a defect.**

---

## 18. Key Code, Processes & Repos

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **JBGLIMPORT / QCFSIMPCYC** | Import GL/AP/AR → stage to CTF | Out-of-balance usually here (STRAN_CORE_INTFC staging gap, §6) |
| **JBPREPROOF** | Proof billable transactions into CTF | Failed run can leave CTF rows without `JBTRN_PROCESS_ACTIVITY` (§10) |
| **JBPROPALLC / JBPROPALLOC** | Property Allocation (JB005 step) | SPE/timeout (§8) |
| **JBOWNALLOC / JBOAMAIN** | Owner Allocation (JB005 step 200) | DOI cartesian (§7); perf SQL `m_SEL_OwnerAllocStageSvcDt`, `m_INS_PopulateJEStaging` |
| **JBREBILL** (steps incl. `JBREBREVNW`, `PAREBILL`) | Rebill Allocation (reverse/rebill) | PA-rebill **removed** (§8); timeouts (§4) |
| **JBLDJE2CAS** | **Finalize & Post** — load JE to QCFS/GL | **NOT rerunnable**; `JBVALCDBLK` validates code block; timeouts (§4) |
| **JBROLLDATE** (`JBJEHISTNW`, `JBUPDSTAT`) | Roll the JIB month | Moves journal → `JBADT_JIB_JOURNAL_HISTORY`, clears `JBTRN_JIB_JOURNAL` (§17) |
| **JBPREPAY** | Bring AR prepay/cash-call entries to JB340 | Prepay config (§12) |
| **JBINVJIBLK** | Export to JIBLink/EnergyLink | Proc `UPS_JIB_LINK_EXPORT_CORE`; PRT/state, Fetch_Size (§11) |
| **JBCTFDOI** | DOI CTF Failure Reversal | Runs with CSL; resets rebill steps by design (§17) |
| **POSTWKFL / BUSSVCRUN** | Post workflow / balance refresh | Deadlock isolation → BSVCLOSE/BSVCRFRSH/PSTWKBAL (ADO 1739552, §7) |

### Key screens
`JB005` Process of JIB · `JB010`/`JB020` overhead rates & rebill tabs · `JB084` keyword-derivation decision fields · `JB300` Rebill Request · `JB310` · `JB330`/`JB410` invoice inquiry/detail · `JB340` Prepay Maintenance · `JB350` Reassign Deck (Ready to Bill) · `JB355`/`JB360` failure purge/hold · `JB390` CTF Failure Reversal · `JB500` event Cr/Dr account setup · `JB520` JIB Journal · `GL013` JE code type · `GL105` code-block column rules · `GL025` JE creation · `PR004`/`PR005` Property master · `DO004` DOI · `MT100`/`MF035` import & AFE-interface config · `AR076`/`AR173` JIB import/AR · `QP110` Active Lock Monitor · `SM006` business-entity period.

### Code locations (confirmed via ADO code search)
| Symbol / area | Repo / path |
|---|---|
| JIB allocation, overhead, journals, keyword resolution (C++) | **`Quorum.Upstream.QCA.ClassicBatch`** → `/QPDllCostAcctgJIB/` (`QPSJIBCreateJournals.cpp`, `QPSJIBDrillingOverhead.cpp`, `QPSJIBPercentOverhead.cpp`, `QPSJIBConstructionOverhead.cpp`, `QPSJIBCatastropheOverhead.cpp`, `QJIBPropAllocDBWriter.cpp`, `QPSJIBVehicleCalculation.cpp`, `QSQL_DrillConstrCatastOverhead.cpp` / `QSQLID_…h`) |
| JIB GUI screens (keyword resolution etc.) | **`Quorum.Upstream.QCA.ClassicGUI`** → `/Quorum.QCA.JIB/` (`QFrmKeywordResolution.cs/.Designer.cs`) |
| JIBLink export proc | `UPS_JIB_LINK_EXPORT_CORE` / `USP_JIB_LINK_EXPORT` (client `QCA` DB + UPS metadata) |
| SQL/metadata (registered SQL, archive) | **`SUM.Upstream.Metadata`** / `<CLIENT>.Upstream.Metadata` (e.g. `QARCH_SQL.json`, STANDARD 16.0) |

### Layers / repos
- **Core = UPS** (`SUM.Upstream.*`, `Quorum.Upstream.QCA.*`). **Client layer = CEN/QFC/QCEN** (`<CLIENT>.Upstream.Metadata`, e.g. `CEN_PRDA1UPS_QFC`). **Fixes/config must be checked into the client layer or they are wiped on patch/upgrade** (§14). Always compare client layer vs core/DEVA1 for post-upgrade issues.

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **calculation/reversal** is provably wrong on correct inputs: drilling-OH duplicate reversals not joining on accounting date (25-01011716 → `m_SEL_DrillingOverheadReverse`), OH escalation rate (ADO 113455), rebill-of-rebill incorrect entries (25-01027776), Owner-Alloc deadlocks (ADO 1739552).
- A **batch step** crashes from a code/proc bug, not data/timeout: QCFSIMPCYC chunking dropping I/C lines (25-01047112), JB330 1-second filter (25-01033662), picklist DOI defect (24-00957177).
- Provide: **PQID + failing step + exact error**, client + BU + process period, the property/owner/account, the **SQL trace** (`QARCH_QFCBATCH_SQL_TRACE`), and a repro. Confirm fix availability and the linked WI's target patch.

**Route to Cloud Ops / handle as Configuration when:**
- **Timeouts** — `QPEC.ini`/`QPEC.exe.config` `CommandTimeout`, `COMMAND_TIMEOUT_SECONDS`, chunk-size keys; re-apply at the **client layer** after patches (§4). Most JIB "Stopped Processing on Error" cases are this.
- **Code-block / event setup** — JB084 decision fields, JB500 Cr/Dr lines, GL105 column rules (§5).
- **Client-layer drift** after an upgrade — sync missing metadata rows from DEVA1/core (§14).
- **Export path / folder** — JIBLINKEXP Import/Export Definition path; Qcloud-created JIBLINK folder (§11).
- **Data fixes** — restage missing interface rows by `SOURCE_CTF_ID`, dedupe `JBTRN_CTF`, remove orphaned `JBTRN_OWNR_ALLOC`, restore `JBTRN_PROCESS_ACTIVITY`. Always verify-SELECT in a transaction (§6/§10).

**Handle as Training / Expected behavior (no fix):** see §17 — DOI interest-type-sequence setup, warning-only on a rerunnable step, locks to release (QP110), null BA State dropping EnergyLink owners, JBROLLDATE archiving the live journal, tier/AFE-status questions, the CSL/JBCTFDOI dependency reset, and the JB300 "Rebill Current DOI" column. **Verify DOI/property/BA master data and the warning-vs-error distinction first.**

---

*Skill created: 2026-06-14.*
*Based on: 1,263 closed QCA JIB SF cases — 213 actionable (Software Defect 116 + Application Configuration 89 + ChangeConfig 8) mined for fix recipes, plus ~40 Training/Customer-Error cases for the FAQ. ADO work items #1739552, #1661305, #1671837, #1609783, #1611528, #1607218, #1459297, #1558159, #1756221, #113455, #1372009, #1645389, #1568338, #1693814. Code in Quorum.Upstream.QCA.ClassicBatch (/QPDllCostAcctgJIB/) and Quorum.Upstream.QCA.ClassicGUI (/Quorum.QCA.JIB/).*
*Companion (future): SKILL_QCA_QCFS_GL_AP_AR.md, SKILL_QCA_DOI_Ownership.md, SKILL_QCA_AFE.md, SKILL_QCA_Revenue.md, REPO_REFERENCE.md.*
