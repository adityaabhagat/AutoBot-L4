# SKILL: QCFS Import / Export / Integration Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QCFS (My Quorum Financial Accounting — upstream oil-and-gas GL/AP/AR core financials, part of myQuorum / On Demand / UBT)
**Scope:** The data-movement layer of QCFS core financials — **inbound import** (Excel/spreadsheet `QSTAGXLSIM`, Open Invoice / ADP invoice & image `ADPUPLOAD`, the core integration cycle `QCFSIMPCYC` / `QCFSIMP` that pulls JIB/AR, JIB/GL, QRA/GL into QCFS batches, JE/voucher imports, bank-statement & well/AFE imports), **outbound export** (AP check files `APDYNEXP`/`FTPR`/`SFTPR`, Positive Pay, 1099 `INT1099EXP`, HFM/GL extracts), and the **plumbing** that carries them (SFTP/FTP host definitions, Global config file paths, process locks, QPEC scheduler/engines).
**Companion skills:** GL/AP/AR posting & period-close mechanics → core-financials posting skill; QRA (revenue accounting) and QDO (division order) internals → their own skills (many "Integration"-category cases are actually **QRA→QCFS** or **QDO** records — see §2 scope note). This skill *moves* data into and out of QCFS; when the *number itself* is wrong, fix the producing module (QRA/QLS/JIB/Land) first — the import is usually the messenger.

> **Evidence base:** 742 closed QCFS Import/Export/Integration cases (Case_Category__c IN Integration 318, Import/Export 267, Import / Export 105, Data Hub 52). Root-cause split: (blank) 97, **Application Configuration 84**, Hardware/Software Env Change 67, Training 59, Customer Error 49, Business Change 46, **Software Defect 46**, Customer Cancelled 44, Platform 38, Performance 26, … **ChangeConfig 9**. This skill mines the **139 actionable** cases (App-Config 84 + Software Defect 46 + ChangeConfig 9) for fix recipes, plus a sample of Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline, Processes & Vocabulary](#2-pipeline-processes--vocabulary)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — SFTP / FTP / file-path / bank-export plumbing (LARGEST CONFIG CLUSTER)](#4-cluster-a--sftp--ftp--file-path--bank-export-plumbing)
5. [Cluster B — QSTAGXLSIM Excel / spreadsheet import](#5-cluster-b--qstagxlsim-excel--spreadsheet-import)
6. [Cluster C — QCFSIMPCYC / QCFSIMP core integration cycle (QRA/JIB/GL → QCFS)](#6-cluster-c--qcfsimpcyc--qcfsimp-core-integration-cycle)
7. [Cluster D — ADPUPLOAD / Open Invoice invoice & image import (duplicate / doubled amounts)](#7-cluster-d--adpupload--open-invoice-invoice--image-import)
8. [Cluster E — AP check export / Positive Pay / bank adaptor & encryption](#8-cluster-e--ap-check-export--positive-pay--bank-adaptor--encryption)
9. [Cluster F — Process locks not releasing / QPEC scheduler & engines](#9-cluster-f--process-locks-not-releasing--qpec-scheduler--engines)
10. [Cluster G — BA / vendor / customer master not set up for the interface](#10-cluster-g--ba--vendor--customer-master-not-set-up-for-the-interface)
11. [Cluster H — 1099 export / staging](#11-cluster-h--1099-export--staging)
12. [Cluster I — Period / BU / fiscal-year config blocking import-created batches](#12-cluster-i--period--bu--fiscal-year-config-blocking-import-created-batches)
13. [Cluster J — Connectivity / DB gateway / VPN / environment refresh](#13-cluster-j--connectivity--db-gateway--vpn--environment-refresh)
14. [Known ADO Items](#14-known-ado-items)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Expected-Behavior / User-Education FAQ](#16-expected-behavior--user-education-faq)
17. [Key Code, Processes & Repos](#17-key-code-processes--repos)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| Import/export **process fails immediately** with "No path or filename passed in / defined for this process to imp/exp" or "Date Type import without a specified column format" | **Global config / Import-Export definition file path or date format is blank or wrong** | §4 — Maintenance App: Global config file-path param + the Import/Export definition for that process |
| AP check / bank file export fails with **"Algorithm negotiation fail"**, "encryption algorithm not found", SFTP won't connect after a patch | SFTP/SSH config: `USE_SSH_NET` not enabled; `FTPR` deprecated → `SFTPR`; changed SFTP password/host | §4/§8 — enable `USE_SSH_NET`; update FTP Host Definition; restart QPEC |
| Files sit in SFTP and never reach `Unprocessed` / never import | SFTP connection/folder mapping changed (patch, FTP 1.0→1.5 migration, expired account) | §4 — verify FTP Host Definition + Import File Location list; reactivate/relink FTP account |
| **Open Invoice / ADP invoices doubled** (amounts 2×) | Two import jobs both inserted into `QSTAG_CORE_INTFC_EXTERNAL_IMP`; first job failed/half-marked, second combined both | §7 — known `ADPUPLOAD` defect (24-00990215 / ADO #1699577); scripts to reverse + restage; upgrade has PQID-locking fix |
| **Doubled / duplicated batches from QCFSIMPCYC** (line-level dups) | Failed run left data in `QSTAG_CORE_INTFC_IMP` not marked processed; next run re-moved it | §6 — 25-01001987 reverse+restage script pattern; run archive/purge; check for orphaned locks |
| `QSTAGXLSIM` Excel upload ignores a field (DO Type/Tier, Quantity/`TRANS_VOL`), or posts to wrong BU | Excel-import field-mapping defect or a Global config (e.g. `AR_DEFAULT_DOI`) interfering; one-digit BU bug | §5 — toggle the interfering config; known defects 24-00966324, 25-01004336, 1789601 |
| Batch stuck in **"Post Pending"** after import; POSTWKFL fails | Target **fiscal year / BU period not created (SM006)** or BU inactive, or a missing bank account for the code block | §12 — create the period (SM006) / delete the offending reversal batch; code now catches the exception (Patch 12) |
| Import/export **process won't start; previous run still "locked"** | Process locks not released after a prior failure/outage | §9 — release locks in QP110 / QP073; reboot QPEC/MT engines if crashing |
| Import error "Business Associate … is not valid" / "Expected 1 instance of Customer … found 0" / vendor not publishing | **BA not flagged Use-as-vendor/customer, or missing from the vendor table / GLOBAL_BUSINESS** | §10 — set the flag on the BA Core Financials tab; sync/insert vendor rows |
| 1099 export errors / 1099s not created | 1099 file-path config blank; missing indexes; data not linked | §11 — set `INT1099EXP` path; create indexes; script the data link |
| "Can't connect to SQL/Oracle gateway", "secure gateway access error" | Network/VPN/ACL — IP outside allowed range, route stale, firewall policy expired | §13 — Cloud Ops/IT: bounce VPN tunnel, add IP to ACL, renew firewall policy |
| After a UAT **refresh/upgrade**, import/export paths point to PROD or connections missing | Post-refresh scripts not applied; process-definition **override paths** still PROD; metadata not checked in | §4/§13 — apply post-refresh scripts; fix process-definition override paths per env; check param into client metadata repo |

---

## 2. Pipeline, Processes & Vocabulary

```
INBOUND
  Excel/CSV templates ──QSTAGXLSIM──► QSTAG_*_IMP staging ──QCFSIMPCYC(step QCFSIMP)──► QCFS batches (GL025/AP055/AR076) ──POSTWKFL──► GL
  Open Invoice / ADP  ──ADPUPLOAD───► QSTAG_CORE_INTFC_EXTERNAL_IMP ──QCFSIMP──► AP batches (invoices + images)
  QRA / JIB / QLS / Land ──(publish)──► STRAN_CORE_INTFC + SEXTN_CORE_INTFC_CFS ──QCFSIMPCYC──► QSTAG_CORE_INTFC_IMP ──► QCFS batches
  Bank statement ──BK030──► ; Well/AFE ──INT_QLSWL / AFE_IMPORT──►

OUTBOUND
  AP checks ──APDYNEXP / FTPR|SFTPR / GPGENCRYPT──► bank SFTP        Positive Pay ──BK010──► bank
  1099 ──INT1099STG / INT1099EXP──► IRS file        HFM/GL ──HFMACCTBAL──► consolidation
```

**Scope note (important for clustering):** the SF `Case_Category__c` values Integration / Import/Export / Data Hub on product *My Quorum Financial Accounting* are dominated by **core-financials data movement** (the clusters below). A large secondary slice of "Integration"/"Software Defect" rows are actually **QDO (Division Order) and QRA (Revenue Accounting)** records that share the category — DOI/Maintenance-Group/PPN/transfer cases (e.g. 24-009xxxx Gulfport/CNX/Apache "Upgrade Project: QDO"). Those belong to the QDO/QRA skills; this skill covers them only at the **QRA→QCFS integration boundary** (§6). If a case is about Maintenance Groups, PPNs, owner transfers, DOI setup, or funds release, route it to the QDO/QRA skill.

### Key terms (Quorum / QCFS vocabulary)
- **QCFS** = Quorum Core Financial System — the GL/AP/AR/bank core. Screens are `xxNNN` codes: **GL025** (JE batch), **AP055/AP061/AP175** (AP voucher/check), **AR076/AR173** (AR/JIB-AR batch), **BK010/BK012/BK030** (bank/Positive Pay/bank statement), **SM006** (fiscal-year/BU period), **SM093** (segregation-of-duties draft/approve/post), **SM270/SM275/SM400** (import xref / voucher template config), **QP073** (run process), **QP110** (process locks / lock release), **GL105** (account setup, cost-center required flag).
- **QSTAGXLSIM** (a.k.a. `QSTAGXLSIMP`) = the **Excel/spreadsheet staging import**. User loads a template (JE, AR076, voucher), runs `QSTAGXLSIM` under Process Type **QCFS** in QP073, then the import cycle creates the batch. ClassicGUI form `QFrmQSTAGXLSIM.cs`.
- **QCFSIMPCYC** = the **core integration import cycle**; its main step is **QCFSIMP** (batch creation). It drains `QSTAG_CORE_INTFC_IMP` into real QCFS batches and marks source rows `PROCESS_IND = 1`. The producing modules first publish into **`STRAN_CORE_INTFC` + `SEXTN_CORE_INTFC_CFS`**; the cycle moves un-imported rows into `QSTAG_CORE_INTFC_IMP` and builds batches. Implemented in `QPSQCFSImport.cs`.
- **ADPUPLOAD** = the **Open Invoice / ADP** invoice-and-image upload (third-party AP invoices + scanned images). Stages into `QSTAG_CORE_INTFC_EXTERNAL_IMP`.
- **PRGCOREINT** = **archive & purge** for the core-integration tables. If mis-defined it either purges live data (24-01064867) or, if *not* run, lets the staging tables grow and import jobs time out (25-01001987).
- **APDYNEXP / FTPR / SFTPR / GPGENCRYPT** = AP **dynamic export** of check/payment files: build the file (`APDYNEXP`, helper exes `MOVEDYEXP.exe`/`ARCHEDYEXP.exe`), transfer over FTP/SFTP (`FTPR` legacy, **`SFTPR`** current), PGP-encrypt (`GPGENCRYPT`). **`USE_SSH_NET`** global config switches to the modern SSH library that negotiates algorithms with newer banks.
- **QPEC** = the batch **scheduler/engine tier** (with the QRMMT middle tier). Jobs run here; a QPEC restart is required after FTP/host-definition changes; crashing QPEC/MT engines need a server reboot.
- **Global config / Import-Export definition / Process Definition override** = three layers where a **file path** lives. Per-process IMP/EXP file path (Maintenance App), the export-definition data (`QARCH_EXP_DEF_DATA_DERIVED`), and **process-definition Override paths** (per metadata layer `QEQC`/`QCNR`/…). After a refresh these commonly still point at PROD.
- **Client metadata layer / repo** = `<CLIENT>.Upstream.Metadata` (e.g. `QEQC`, `QCNR`, `QSPR`). Process params (e.g. **QSTAGXLSIM param 36611**) and process overrides live here; if a fix is only made on the front end and not checked into the client repo, it regresses at the next upgrade (24-00937324).

---

## 3. Decision Tree

```
QCFS Import / Export / Integration case
│
├─ Is it really QCFS core financials?  (NO → if Maintenance Group / PPN / DOI / owner transfer / funds release → QDO/QRA skill)   §2
│
├─ Process FAILS at launch / file plumbing
│   ├─ "No path/filename passed", "Date type without column format", wrong folder           → §4 (Global config path + Import/Export def + process-definition Override path)
│   ├─ "Algorithm negotiation fail" / encryption / SFTP won't connect (esp. after patch)     → §4/§8 (enable USE_SSH_NET; FTPR→SFTPR; update FTP Host Definition + QPEC restart)
│   ├─ Files stuck on SFTP, never reach Unprocessed                                           → §4 (FTP account 1.0→1.5 / reactivate; folder mapping; Import File Location list)
│   └─ Bank/check export validation blocks (10+ digit check, casing, TRUST/key)              → §8 (bank adaptor formatting; BK012 casing; GnuPG TRUST)
│
├─ Data is DOUBLED / DUPLICATED
│   ├─ Open Invoice / ADP amounts 2×                                                          → §7 (QSTAG_CORE_INTFC_EXTERNAL_IMP; ADO #1699577; reverse+restage; PQID-lock fix)
│   └─ QCFSIMPCYC produced duplicate batches/lines                                            → §6 (failed run left rows un-marked; 25-01001987 reverse+restage; run PRGCOREINT)
│
├─ Excel upload (QSTAGXLSIM) wrong/missing field or wrong BU                                  → §5 (field-mapping defect; toggle interfering config e.g. AR_DEFAULT_DOI; one-digit-BU bug 1789601)
│
├─ Imported batch stuck "Post Pending" / POSTWKFL fails                                       → §12 (SM006 fiscal-year/BU period missing; BU inactive; missing bank account for code block) 
│
├─ "Process locked" / won't start / engines crashing                                         → §9 (release locks QP110/QP073; reboot QPEC + QRMMT)
│
├─ "BA/vendor/customer not valid" on import                                                  → §10 (set Use-as-vendor/customer on BA Core Financials tab; vendor/GLOBAL_BUSINESS rows)
│
├─ 1099 export error / 1099s not created                                                     → §11 (INT1099EXP path; indexes; script data link)
│
└─ Can't connect to SQL/Oracle / gateway / after refresh                                      → §13 (VPN/ACL/firewall; post-refresh connection scripts)
```

---

## 4. Cluster A — SFTP / FTP / file-path / bank-export plumbing

**The single largest actionable cluster (Application Configuration).** Almost every "the import/export process suddenly fails / files don't move" case resolves to a **file-path or SFTP configuration** that changed (a patch, a refresh, an FTP migration, a rotated password) — **not** a code bug.

**Signatures & fixes seen:**
- **"No path or filename passed in or defined for this process to imp/exp. Exiting Process."** → the per-process **IMP/EXP File Path is blank** in the Maintenance App. Set it (1099: 24-00984928; 23-00935283 INT1099EXP "IMP/EXP filepath definition was missing").
- **"DATE TYPE IMPORT WITHOUT A SPECIFIED COLUMN FORMAT, SOME ERRORS COULD OCCUR"** (ADPUPLOAD) → the **Import/Export definition lacked a date-format config**; add an explicit date format to the definition (25-01035235).
- **"Algorithm negotiation fail" running SFTP (Capital One, etc.)** → **enable the `USE_SSH_NET` global config**; the modern SSH library negotiates with newer banks (25-01039812). Same family: "SFTP Client encryption algorithm not found" cleared by a **QPEC restart** (26-01083076).
- **`FTPR` deprecated → `SFTPR` after a 2025.04 HF; check export "all FAILED"** → the legacy `FTPR` process was retired; for CNR a `FTPR` override on the `QCNR` layer plus correcting the **`CHECK_FILE` global config** path restored exports (26-01092339). General rule post-patch: confirm whether the client moved to `SFTPR` and re-point the bank folder.
- **SFTP password / host rotated** → jobs using that host fail until updated: Maintenance App → Maintenance → FTP → **FTP Host Definition** → update HostID/Address/Login/password → **QPEC restart** (25-01013547 WellsFargo; 23-00917301 HFMACCTBAL).
- **FTP account 1.0 → 1.5 migration / disabled account** → relink the Upstream app to the **1.5 FTP account** (25-01022593) or reactivate the disabled 1.0 account (25-01018272).
- **Files going to PROD from UAT / paths hard-coded** → the **process-definition Override paths** (Batch Process → Process Definition → query process under the client metadata layer `QEQC`, Parameters tab) still point at PROD even though the exes are correct; fix `OVERRIDE EXPORT/SUCCESS/FAILED PATH` per env (24-00985205; 24-00951436; 24-00986912 `DYNEXP|EXPORT_FILE_PATH`; 25-01022791 `APDLINKSITE` not updated to V17 path).
- **Import File Location list wrong / folders missing** → add the FTP folders to the app (25-01013208); recreate drop folders (23-00902908); after Cloud maintenance, permissions let users delete JIBLINK/ADP folders — **lock the folders** (24-00985460).
- **Image upload path** → set the **`AP_IMAGE_UNPROCESSED`** global config path (25-01012671).

**Fix recipe:**
1. Identify the process (`APDYNEXP`, `FTPR`/`SFTPR`, `ADPUPLOAD`, `INT1099EXP`, `HFMACCTBAL`, `QSTAGXLSIM`) and whether it changed after a **patch / refresh / FTP migration / password rotation** — that is the cause >80% of the time.
2. Check the **three path layers**: (a) per-process **IMP/EXP File Path** (Maintenance App), (b) **process-definition Override paths** for the env's metadata layer, (c) the relevant **Global config** path (`CHECK_FILE`, `DYNEXP|EXPORT_FILE_PATH`, `AP_IMAGE_UNPROCESSED`, `AP_*_UNPROCESSED`).
3. For SFTP/SSH errors: **enable `USE_SSH_NET`**, then verify the **FTP Host Definition** (host/login/password) and **restart QPEC**.
4. For bank export specifically also see §8 (adaptor format, key casing/TRUST).

---

## 5. Cluster B — QSTAGXLSIM Excel / spreadsheet import

User loads an Excel template (JE → GL025, JIB-AR → AR076, voucher) via **`QSTAGXLSIM`** (Process Type QCFS, run in QP073), then `QCFSIMPCYC` builds the batch. Cases here are **field-mapping defects** or a **config interfering with the mapping** — and a few concurrency/BU-format bugs.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| QSTAGXLSIM **ignores DO Type & Tier** on a GL025 JE upload | The newly-enabled **`AR_DEFAULT_DOI`** global config (meant for AR uploads) forced the upload to take the JIB Base Flag default from DOI setup | Hotfix so JE vs AR uploads both honor the template; interim WA = disable `AR_DEFAULT_DOI` | 24-00966324 (HF in Oct patch, PRD 11/22/2024) |
| AR076 **Quantity (`TRANS_VOL`) not populated** by the spreadsheet upload | Quantity field on the GL Distribution Coding tab not mapped in the import | Defect — automate Quantity mapping (manual entry was the WA) | 25-01004336 |
| **Post-To BU wrong when BU is one digit** | One-digit BU mis-parsed | Bug fix | 1789601 (RRC, Closed) |
| **Difference between classic and web** for QSTAGXLSIM-uploaded batches (2025.04) | Behavior divergence classic vs web | Bug fix | 1729515 (Closed) |
| Cannot run **multiple QSTAGXLSIM jobs simultaneously** (expected after upgrade) | Job-level locking / no chunking | `QIMPEXP` chunking added for QSTAGXLSIMP | 25-01005979 / 1809078 (Closed) |
| `QSTAGXLSIM` **stopped working after upgrade** | Param **36611** for QSTAGXLSIM was **not checked into the client metadata repo** | Add the param on the front end (immediate); **check it into the client metadata repo** (long-term) | 24-00937324 |
| Excel import brought in **JE with incorrect Do Type/Tier**, or wrong sum | Mapping / template config | Hotfix / template fix | 24-00966324, 22-00559156 ("JE — not sum to zero": GL line missing → re-type/add line/post; AR076 locked in AR173 → approve) |

**Fix recipe:** reproduce with the client's exact template. If a field is dropped, check (a) whether a **Global config** (`AR_DEFAULT_DOI`, etc.) is overriding template values — toggle it to isolate; (b) whether the **process param is present in the client metadata layer** (the 36611 regression pattern) — front-end fix is temporary unless checked in; (c) known field defects (Quantity 25-01004336, one-digit BU 1789601). For "can't run in parallel," confirm the build includes the `QIMPEXP` chunking change (1809078).

---

## 6. Cluster C — QCFSIMPCYC / QCFSIMP core integration cycle (QRA/JIB/GL → QCFS)

The cycle that drains the producing modules (QRA/GL, JIB/GL, JIB/AR, QLS) through `STRAN_CORE_INTFC` + `SEXTN_CORE_INTFC_CFS` → `QSTAG_CORE_INTFC_IMP` → QCFS batches. Most actionable cases are **duplicate/missing batches from a half-completed run**, or **archive/purge mis-definition**, and **performance**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Doubling of entries** (line-level duplicate GL & AR batches) | A planned DB outage hit while QCFSIMPCYC was mid-run; the QPEC was not disabled first; orphaned lock left rows in `QSTAG_CORE_INTFC_IMP`; next run re-moved un-marked rows → duplicated batches | **3-script recipe:** (1) set the duplicate **GL reversal batches** to Post Pending so POSTWKFL reverses them; (2) insert a **negated duplicate of the JIB/AR** data into `STRAN_CORE_INTFC`; (3) **restage** `STRAN_CORE_INTFC` from the original source (JIB/AR, JIB/GL, QRA/GL). Also: client was **not running archive/purge**, inflating query times | 25-01001987 |
| `QCFS import brought in old batches` | **`PRGCOREINT` archive-and-purge definition** wrong | Fixed in September hotfix | 25-01039511 |
| `Data Integration Issues — STRAN_CORE_INTFC` (client says data missing) | **Archive & Purge was purging the data** the client expected to see | Correct the purge definition | 26-01064867 |
| `QSTAGXLSIM Import process error` / `QCFS Import Cycle Failing` | Engineering code changes to the cycle | Included in next patch | 23-00925179, 24-00972339 |
| **Long runtimes** when an open item is applied to an AR batch; batch-creation perf | Cycle performance | Perf improvements | 1724602, 1683641, 1565787 (all Closed) |
| **Missing timeout override on DELETE** statements within `QPSQCFSImport` | No timeout override → rollbacks under load | Bug fix | 1374816 (Closed) |
| `QRA Import JE — Not Sum to Zero` / `QRAREV could not post & QRANET posting pending` | $0 netting entries from QRA broke A/R open-item logic | **Changed QCFSExport to exclude $0 netting entries from QRA** | 22-00552670; 22-00559156 |
| Rev batch **stuck Post Pending when imported through QCFSIMPCYC and BU is inactive** | Inactive BU | Bug fix | 1752121 (APH, Closed) |
| `QCFSGLCONV not loading to GL025` / `QCA Imports into QCFS failed` | Cycle/conversion config | Config | 24-00972739, 22-00680633 |

**Fix recipe (duplicate/missing batches — the dominant pattern):**
1. Establish **what failed and when** (PQID, the outage/lock event). The hallmark is a **failed/interrupted run that left rows in `QSTAG_CORE_INTFC_IMP` not marked `PROCESS_IND=1`**, so the next run re-imports them.
2. Use the **reverse-then-restage** pattern (25-01001987): reverse the duplicated GL batches (set the reversal batch Post Pending → POSTWKFL), negate-and-reinsert duplicated AR into `STRAN_CORE_INTFC`, then restage from the original source. **Always verify-SELECT in a transaction first.**
3. Confirm **archive/purge (`PRGCOREINT`) is correctly defined and actually running** — both *over*-purging (26-01064867, 25-01039511) and *under*-purging (25-01001987 → timeouts) are real failure modes.
4. Before any planned outage, **disable the QPEC** so the cycle isn't interrupted mid-run.

---

## 7. Cluster D — ADPUPLOAD / Open Invoice invoice & image import

Third-party AP invoices (Open Invoice / ADP) plus scanned images, staged via **`ADPUPLOAD`** into `QSTAG_CORE_INTFC_EXTERNAL_IMP`. The marquee defect here is **doubled invoice amounts**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Open Invoice import doubled all amounts** (payment system taken down) | First import job **failed/half-marked** its rows in `QSTAG_CORE_INTFC_EXTERNAL_IMP`; the **second job inserted again and combined both** into one invoice at the QCFSIMP step — doubling every invoice in the file | Newer **`ADPUPLOAD` no longer launches a child job per file and locks jobs by PQID**, preventing the duplicate; HF ticket 24-00991971 | 24-00990215 / 24-00990689 (RCA) / **ADO #1699577 (TGNR)**, **#1710825 (APH SI144124)** |
| `Duplicate Invoice Uploads` | Tables not cleared before re-upload | **Purge definition to clear tables before upload** (WA); long-term: removed unnecessary return from the draft workflow (Jan hotfix) | 22-00828612 |
| `ADPUPLOAD process failing with Object reference error when coded to control account` | Control-account coding null-ref | Bug fix | 1744756 (APH, Closed) |
| `ADPUPLOAD cross reference file error` / `Attachments with same filename causing ADP Import to fail` | Xref / filename collision | Config / defect | 25-01013559, 25-01011474 |
| `ADPUPLOAD ERROR IN PRD` | ADP **mapping configuration** | Script updated the ADP integration mapping | 26-01065176 |
| `ADPUPLOAD — Date Type import without specified column format` | Import/Export def missing date format | Add date format to the def | 25-01035235 (see §4) |
| ADP folders / credentials | Read/Write creds to ImageUnproc / InvoiceUnproc / ImageMetadataUnproc | Grant folder creds | 24-00979462, 25-01023292 |
| `ADPUPLOAD — Update statements within loop` (perf) | Loop-level update inefficiency | Perf fix | 1700169 (Closed) |

**Fix recipe:** for **doubled amounts**, this is the known `ADPUPLOAD` defect (24-00990215, ADO #1699577/#1710825). Confirm the build predates the **PQID-locking / no-child-job-per-file** fix; if so, push the HF (24-00991971) and clean up with the reverse+restage approach. As an operational guard, ensure a **purge definition clears `QSTAG_CORE_INTFC_EXTERNAL_IMP` before re-uploading** (22-00828612). For "failing to import," check ADP **mapping config**, **folder permissions/credentials**, **duplicate filenames**, and the **date-format** definition.

---

## 8. Cluster E — AP check export / Positive Pay / bank adaptor & encryption

Outbound AP/payment files to banks (check files via `APDYNExp`/`FTPR`/`SFTPR`, Positive Pay via BK010, encrypted with `GPGENCRYPT`). Mostly **bank-adaptor formatting** and **encryption-key configuration**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Positive Pay export blocks all checks under a BU** when a check is 10+ digits | The **CitiBank bank adaptor** was set up with implied-decimal formatting (decimal not counted in the 10-char width); after switching to CSV the decimal counts as a char, so large checks trip a validation | WA: script flips **"sent to bank" = 1** to release outstanding checks (large check added to file manually). Long-term enhancement roadmapped | 24-00980402 |
| **Encryption / PGP key** issues for Positive Pay (BRM/JPMC) | (1) BK012 screen auto-uppercases the assembly name → key unreadable; (2) key imported under a name not on the public key ring → `GPGENCRYPT` fails; (3) key lacked **TRUST** | (1) script to preserve casing in backend; (2) rename via Code Value Editor (suffix old `_old`, set new to ring name); (3) `gpg --edit <hex>; trust; 5; y` to grant **Ultimate trust** in GnuPG | 24-00966526 |
| `APDYNEXP` error **"Index and length must refer to a location within the string … substring"** | Export def derived **Zip code** element is String; a **foreign BA had no zip** → substring out of range | Set the foreign BA zip to **00000** (data); check `QARCH_EXP_DEF_DATA_DERIVED` | 24-00993395 |
| `APDYNEXP failing in UAT` | Series of config issues | Update Global config paths + set up **KEY pair** to bank | 25-01036183 |
| `Negative amount on JPM check file` / `Remittance not appearing` / `JPM check file failures` | Bank-file formatting / adaptor | Config (resolution pattern varies; treat as adaptor format) | 25-01013273, 25-01012934, 25-01012353 |
| `Check Export Path Incorrect` | `DYNEXP|EXPORT_FILE_PATH` global config wrong | Re-point to `\…\AppFiles\Upstream\JPMC\` | 24-00986912 |
| New **Positive Pay adapter** requests (REP, CTE) | New client bank | Feature build | 1766026 (Closed), 1820238 (Proposed) |
| `FTPR Process not working with bank test FTP site` | Older build | Software upgrade / PS assistance | 22-00876501 |

**Fix recipe:** distinguish (a) **transport** (SFTP/SSH — §4: `USE_SSH_NET`, host definition, QPEC restart), (b) **file format** (bank adaptor — char widths, implied vs explicit decimal, CSV vs fixed; e.g. CitiBank 24-00980402), and (c) **encryption** (PGP key naming/casing/TRUST — 24-00966526). For the "substring/Index and length" error, look for a **derived field (zip) that is null on a foreign BA** (24-00993395).

---

## 9. Cluster F — Process locks not releasing / QPEC scheduler & engines

Import/export jobs that won't start because a prior run's **lock** was never released, or because the **QPEC/QRMMT engine tier** is down/crashing.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| `AFE Import process failing since November` | **Process locks acquired by the previous process were not released on completion** | **Release the locks in PRD via QP110** | 25-01061459 |
| `Locks not releasing for scheduled jobs when failing` / `Active Lock Release` | Failed jobs leave locks | Release locks (QP110/QP073) | 22-00645827, 24-00989273 |
| `QCFSIMPCYC` left orphaned locks after a DB outage (SXL status until lock released) | QPEC not disabled before outage | See §6 (25-01001987) — release lock, reverse+restage | 25-01001987 |
| `QPEC Middle Tier Engines down — repeatedly crash` | Engine-tier instability | **Reboot BOTH the QRMMT (BDRQRMMT) and QPEC (BDRQPEC) servers** | 22-00669869 |
| `QPEC SYSTEM ERROR in UAT trying to run check run` | QPEC error | Restart/config | 23-00914839 |
| `SFTP Client encryption algorithm not found … QPEC restart` | Engine needs restart after SFTP change | QPEC restart | 26-01083076 |
| `Enable scheduled jobs in PRDA1` / `Schedule POSTWKFL, QCFSIMPCYC, QEMAIL` | Schedule indicator off after upgrade | Set the schedule **active** indicator | 26-01069225, 25-01017757, 23-00931653 |

**Fix recipe:** if a process "won't start / says it's still running," it's almost always a **stale lock** — release it in **QP110** (lock-release screen) or QP073, then re-run. If the **engines themselves** are crashing, reboot **both** the QRMMT middle-tier and QPEC servers (22-00669869). After any FTP/host change, **QPEC restart** is mandatory. After an upgrade, re-enable **scheduled job active indicators** (jobs silently stop).

---

## 10. Cluster G — BA / vendor / customer master not set up for the interface

Imports validate the **Business Associate (BA)** against vendor/customer setup; the most common "import failed" cause after file plumbing is a **BA not flagged or not published** to the vendor/customer tables.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| `eONE Import Error: Expected 1 instance of Customer with Userkey=… found 0` | BA **not set up as customer** | BA screen → **Core Financials tab → "Use as customer"** → save → reimport | 25-01002301 |
| `Unable to Save BA … use as vendor flag` | BA lost **GLOBAL_BUSINESS** records for the BA/USERKEY when created | Script to **recreate/associate the missing vendor rows** | 25-01019914; RCA/long-term in **Patch 15** (25-01020116 — code fix: don't corrupt vendor table when BA screen not closed after New) |
| `Vendors Setup in BA Maintenance Not Publishing to Both Global Companies` | Vendor not in the vendor table for the 2nd company | **Set up the vendor in the vendors table** | 23-00923513 |
| `BK030 bank-statement upload: "Business Associate is not valid"` (4k+ rows) | 3 **BA-Suf combinations not set up in ESUITE** (so no bank account to associate) | Set up the missing BA-Sufs → reimport | 25-01014016 |
| `BA Not Going to QLS` (DATAPUBLSH) | Foreign BA had **no State/Zip** → blocked from interface | State/Zip not required for foreign BAs — relax the interface requirement | 22-00678367 |
| **Same invoice number for same BA posted to multiple BUs** | Duplicate-invoice validation (AP175 level) wasn't preventative across BUs | Fixed in **Patch 11 & 12** (Nov 2023) | 24-00942635 |
| **BA auto-numbering** starts at an existing number / wrong scheme | `QARCH_TRAN_SEQ` last-used number not aligned; PUBBA adapter not updated to Web at cutover | Update `QARCH_TRAN_SEQ` last user number; **update PUBBA adapter via script** to the Web adapter | 25-01023079; 24-00989661 (no driver table — it's the sequence) |
| `Can't see BU 700 after creating new company` | Defect on old build | Script + fixed in >2020.03 | 22-00690574 |

**Fix recipe:** when an import says a BA/vendor/customer is "not valid / not found," open the **BA screen → Core Financials tab** and confirm the **Use-as-vendor / Use-as-customer** flag and that **vendor/GLOBAL_BUSINESS rows exist for the right company/BU** (25-01002301, 25-01019914, 23-00923513). For bank-statement imports, the offending BA-Suf may simply not exist in ESUITE (25-01014016). For **BA auto-numbering**, fix `QARCH_TRAN_SEQ` and confirm the **Web PUBBA adapter** is in use after a V17 cutover (25-01023079).

---

## 11. Cluster H — 1099 export / staging

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| `INT1099EXP error` / `1099 Export: No path or filename passed` | **IMP/EXP file-path definition blank** | Set the path (Maintenance App) | 23-00935283, 24-00984928 |
| `1099 NEC Process Error` | Missing indexes | **Script to create indexes**; request Feb hotfix for remaining items | 22-00664566 |
| `INT1099STG — Integrated 1099 Export (Staging) Error` | Older-build defect | **Patch 5 on 2020.03** (case 21-00198795) | 22-00669745 |
| `1099s did not get created for the new QCFS / Land integration invoices` | Data not linked across the QCFS/Land integration | **Data fixed via script** | 23-00887206 |

**Fix recipe:** 1099 failures are usually the same **blank file path** as the rest of §4 (set it), or **missing indexes** on the staging tables (22-00664566). For "1099s not created," check the **QCFS↔Land/AP invoice linkage** and script the data link (23-00887206).

---

## 12. Cluster I — Period / BU / fiscal-year config blocking import-created batches

Imported batches that land in **"Post Pending"** and won't post — usually a **missing period or inactive BU**, not a bad file.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| AP batch stuck **Post Pending**, acct date in a future year (2028 / 2052) | **Fiscal year / BU period not created in SM006** → exception thrown, batch hangs | Create the period; **code now catches the missing-BU-period exception** (Patch 12) | 25-01007270, 25-00999714 |
| `POSTWKFL Error: No bank account found for Account 'PAYABLE-TRADE' … codeblock values=()` | A **reversal voucher** stuck Post Pending had no resolvable bank account for its code block | **Delete the offending reversal batch** → POSTWKFL completes | 26-01084388 |
| `Voids & Suspense QCFS Posting Failed: Cost Center is required …` | Account 2401-100% has **Cost Center = Required in GL105**; Land leases missing cost center | Customer sets a cost center on the leases (or relax the GL105 requirement) | 26-01065596 |
| Rev batch **Post Pending — BU inactive** (imported via QCFSIMPCYC) | Inactive BU | Activate BU / bug fix | 1752121 (Closed) |
| `JBVOUCHIMP not importing for a BU` | **SM400 (Template Config) and SM270 (Import Xref Config) not set up for that BU** | Set up both screens for the BU | 24-00995015 |

**Fix recipe:** a batch that **imports but won't post** is rarely an import bug. Check, in order: (1) **SM006** fiscal-year/BU period exists for the batch's accounting date; (2) the **BU is active**; (3) **GL105** required-field config (cost center) is satisfied for the accounts; (4) for voucher imports, **SM400 + SM270** are configured for that BU. A single bad **reversal batch** can block the whole POSTWKFL run — delete/correct it (26-01084388).

---

## 13. Cluster J — Connectivity / DB gateway / VPN / environment refresh

Pure infrastructure/Cloud-Ops cases that arrive as "import/export can't run" but are network or post-refresh setup. Handle with Cloud Ops / IT, not Engineering.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| `Secure Gateway Access Error` / `Unable to connect to SQL Server/Oracle gateway` | Source IP **outside the accepted range**; route stale; **VPN rekey** failed; **firewall policy expired** | Add IP to **VPN/ACL** (24-00949870); **bounce the VPN tunnel** to re-inject routes (25-01027894/27937); renew firewall policy (25-01014503) | 24-00949870, 25-01027894, 25-01027937, 25-01014503 |
| `v17 UPS UAT Missing Land Connections` / connection tables empty after refresh | **Post-refresh scripts not applied** | Apply post-refresh scripts to the Upstream **connection-management tables** | 25-01026719 |
| `Test files going to Prod folders` after refresh | Path overrides still PROD | Fix the file paths / process-definition overrides (see §4) | 24-00951436, 24-00985205 |
| `Hidden Default Values Not Updating from Maint App to Upstream App` | App cache | **Service restart** | 23-00924738 |
| `Access Denied placing files on server to test import/export` | File-share vs SFTP path | Place files via **import from the SFTP site** | 25-01045888 |
| `Quorum FTP down / account disabled` | 1.0 account disabled / migration | Reactivate / relink to 1.5 (see §4) | 25-01018272, 25-01022593 |
| `Database Change Tracking request` / Snowflake CDC discussion | Customer data-platform request | Enable change tracking on tables / scoping discussion | 26-01103555, 24-00987269 |

**Fix recipe:** if the error is **"can't reach SQL/Oracle/gateway,"** it is network — engage Cloud Ops/IT to check **IP/ACL range, VPN routes (bounce the tunnel), and firewall policy expiry**. After any **environment refresh**, expect **connection/path config** to be missing or pointing at PROD — apply post-refresh scripts and re-verify the three path layers from §4.

---

## 14. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1699577** | Bug / **Closed** | TGNR (CCI) — 24-00990215 — Invoice Amounts Doubled on Open Invoice Import | §7 | 24-00990215 |
| **#1710825** | Bug / **Closed** | APH — Invoice SI144124 from Open Invoice doubled the amount | §7 | (APH OI dup) |
| **#1374816** | Bug / **Closed** | QCFSIMPCYC — Missing Timeout Override on DELETE within `QPSQCFSImport` | §6 | — |
| **#1565787** | Requirement / **Closed** | QCFSIMPCYC — Performance improvements (quick wins) | §6 | — |
| **#1683641** | Requirement / **Closed** | QCFSIMPCYC step QCFSIMP — batch-creation-time perf review | §6 | — |
| **#1724602** | Bug / **Closed** | QCFSIMPCYC long runtimes when an open item is applied to an AR batch | §6 | — |
| **#1752121** | Bug / **Closed** | APH — Rev batch stuck Post Pending via QCFSIMPCYC when BU inactive | §6/§12 | — |
| **#1729515** | Bug / **Closed** | 2025.04 — classic-vs-web behavior diff for QSTAGXLSIM uploaded batches | §5 | — |
| **#1789601** | Bug / **Closed** | RRC — QSTAGXLSIM Post-To BU wrong when BU is one digit | §5 | — |
| **#1809078** | Bug / **Closed** | QIMPEXP chunking for QSTAGXLSIMP (run multiple jobs) | §5 | 25-01005979 |
| **#1700169** | Requirement / **Closed** | ADPUPLOAD — ADPIMPALLV step — update statements within loop (perf) | §7 | — |
| **#1744756** | Bug / **Closed** | APH — ADPUPLOAD object-reference error when coded to control account | §7 | — |
| **#1766026** | Feature / **Closed** | REP — Riley Exploration Permian — AP Positive Pay Adapter creation | §8 | — |
| **#1820238** | Feature / **Proposed** | CTE — CTOC Energy — AP & Revenue Positive Pay Adapter | §8 | — |

> Several actionable cases were dispositioned **operationally** (config / data script / HF) with the fix tracked in a patch rather than a single discoverable WI: ADPUPLOAD doubling HF **24-00991971**; SM093 SOD draft/approve/post HF **11 for 2023.04** (26-01107018); missing-BU-period exception handling **Patch 12** (25-01007270, 25-00999714); BA-vendor-table corruption **Patch 15** (25-01020116); duplicate-invoice-across-BU **Patch 11 & 12** (24-00942635); APQLS validations promoted to CORE in **Patch 16 / 25-01024394** (25-01004752); QSTAGXLSIM Do-Type/Tier HF in the **Oct 2024 patch** (24-00966324); `PRGCOREINT` purge fix **September hotfix** (25-01039511). Confirm exact build/patch in the Upstream release notes before quoting fix availability.

---

## 15. Diagnostic SQL

> **Caveat:** QCFS lives in per-client SQL Server databases (e.g. `[<CLIENT>_PRD..UPS]` / `..QRA`) and Oracle (QLS) — names below are taken from case repro text and code search; **verify against the client DB before scripting**, and always run a verify-SELECT before any UPDATE/DELETE, wrapped in a transaction.

```sql
-- A. Un-marked rows left in core-integration staging (the QCFSIMPCYC duplicate pattern, §6)
--    Rows present but PROCESS_IND not 1 get re-imported on the next cycle → duplicate batches.
SELECT PROCESS_IND, COUNT(*) AS rows_ct
FROM   STRAN_CORE_INTFC          -- and SEXTN_CORE_INTFC_CFS, QSTAG_CORE_INTFC_IMP
WHERE  ACCT_MTH = '<ACCT_MTH>'
GROUP BY PROCESS_IND;

-- B. Open Invoice / ADP external staging — duplicate signature (§7)
SELECT SOURCE_FILE_NM, INVOICE_NO, COUNT(*) AS dup_ct, SUM(INVOICE_AMT) AS total_amt
FROM   QSTAG_CORE_INTFC_EXTERNAL_IMP
WHERE  SOURCE_FILE_NM = 'QUORUM-INVOICE-<yyyymmddhhmmss>.csv'
GROUP BY SOURCE_FILE_NM, INVOICE_NO
HAVING COUNT(*) > 1;

-- C. Batches stuck in Post Pending and their accounting date / BU (§12)
SELECT BATCH_NO, BU_NO, BATCH_TYPE, BATCH_STATUS, ACCT_DT
FROM   <AP/GL batch header table>
WHERE  BATCH_STATUS LIKE 'POST%PEND%'
ORDER BY ACCT_DT;
-- Then confirm the period exists:  SM006 fiscal-year/BU-period for BU_NO + YEAR(ACCT_DT).

-- D. Is a process lock orphaned? (§9) — release via QP110 if the owning PQID is dead.
SELECT * FROM <process-lock / QARCH lock table>
WHERE  PROCESS_ID IN ('QCFSIMPCYC','ADPUPLOAD','AFE_IMPORT','QSTAGXLSIM','APDYNEXP');

-- E. BA not set up as vendor/customer for the interface (§10)
SELECT BA_NO, BA_SUF, USE_AS_VENDOR_IND, USE_AS_CUSTOMER_IND
FROM   <BA / business-associate table>
WHERE  BA_NO = '<BA_NO>';
-- And vendor / GLOBAL_BUSINESS rows exist for the right company:
SELECT * FROM <vendor table> WHERE BA_NO = '<BA_NO>';

-- F. BA auto-numbering sequence (§10) — last used vs scheme
SELECT * FROM QARCH_TRAN_SEQ WHERE SEQ_NM LIKE '%BA%';

-- G. Export-definition derived fields (the APDYNEXP substring/zip error, §8)
SELECT * FROM QARCH_EXP_DEF_DATA_DERIVED WHERE EXP_DEF_ID = '<id>';
-- Red flag: a derived Zip (String) with a foreign BA that has no zip → "Index and length" error (24-00993395).

-- H. Find the failing import/export step + error by Process Queue ID
--    Get the PQID from QP073/QP110, then read the batch message/log for that PQID + step.
```

---

## 16. Expected-Behavior / User-Education FAQ

A large share of Integration/Import-Export cases are **Training / Customer Error** — recognize these before scripting or escalating.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Import suddenly stopped working, I changed nothing" (path/filename error) | Almost always a **config that changed** elsewhere — a patch, a refresh, an **SFTP password rotation**, or an FTP 1.0→1.5 migration. Check the three path layers + FTP Host Definition first (§4) | 23-00898270, 25-01013547 |
| "How do I configure SFTP / FTP host / update the bank password?" | Training — Maintenance App → Maintenance → **FTP → FTP Host Definition**, then **QPEC restart** | 25-01013547, 25-01023653, 25-01023577 |
| "Imported batch is stuck in Post Pending" | Not an import bug — check **SM006 period**, **BU active**, **GL105 required fields** (§12); a bad reversal batch can block POSTWKFL | 25-01007270, 26-01084388 |
| "BA / vendor / customer not valid on import" | Customer setup — set **Use-as-vendor / Use-as-customer** on the BA Core Financials tab; foreign BAs may lack zip/bank account (§10) | 25-01002301, 25-01014016 |
| "Process won't start / says it's still running" | **Stale lock** from a prior failure — release in **QP110** (§9) | 25-01061459, 22-00645827 |
| "Same invoice number posted to two BUs — is that allowed?" | Standard for split-across-BU invoices; the cross-BU duplicate-block was tightened in Patch 11/12 (§10) | 24-00942635 |
| "BA auto-number doesn't match our scheme" | The autonumber is driven by **`QARCH_TRAN_SEQ`**, not a config table — align the last-used number; confirm Web PUBBA adapter after V17 (§10) | 24-00989661, 25-01023079 |
| "Where do I set the export/import file path?" / "Help button doesn't open the fileshare" | Training — per-process IMP/EXP path + Global config; User-Help doc link is a config value (§4) | 24-00984928, 24-00969942 |
| "Need a JIB voucher / EnergyLink upload template/format" | Provide the standard Import/Export definition + template file (§5) | 24-00952932 |
| "Can we incrementally load Quorum ERP data (Snowflake / CDC)?" | Capability/scoping discussion; change tracking can be enabled per table | 24-00987269, 26-01103555 |
| **QDO/QRA-looking cases** (Maintenance Group failing, PPNs, owner transfer, DOI setup, funds release) miscategorized as Integration | **Not QCFS core financials** — route to the **QDO / QRA** skill (§2 scope note) | 24-00977396, 24-00978244, 25-01031226 |

**Tell-tale it's config/training (not a defect):** an import/export that "broke with no change" right after a **patch, refresh, or password rotation**; a batch that **imports fine but won't post** (period/BU/GL105); a **BA not flagged** for the interface; a **stale lock**; or a case that is really about **Maintenance Groups / PPNs / DOIs** (wrong skill). Verify file paths, SFTP, BA setup, and period config before treating it as code.

---

## 17. Key Code, Processes & Repos

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **QSTAGXLSIM** (`QSTAGXLSIMP`) | Excel/CSV staging import → GL025/AR076/voucher | Run Process Type **QCFS** in QP073; param **36611** must be in client metadata; `QIMPEXP` chunking enables parallel runs (§5) |
| **QCFSIMPCYC** (step **QCFSIMP**) | Core integration cycle — QRA/JIB/GL/QLS → QCFS batches | Drains `QSTAG_CORE_INTFC_IMP`, marks `PROCESS_IND=1`; duplicate batches if a run is interrupted (§6) |
| **ADPUPLOAD** (steps incl. `ADPIMPALLV`) | Open Invoice / ADP invoice + image import | Stages `QSTAG_CORE_INTFC_EXTERNAL_IMP`; PQID-locking fix prevents doubling (§7) |
| **PRGCOREINT** | Archive & purge of core-integration tables | Mis-definition over- or under-purges (§6) |
| **APDYNEXP** / `MOVEDYEXP.exe` / `ARCHEDYEXP.exe` | AP dynamic check/payment export | Override paths per env; derived zip field (§8) |
| **FTPR / SFTPR / GPGENCRYPT** | Transfer + PGP-encrypt bank files | `FTPR` legacy → `SFTPR`; `USE_SSH_NET`; GnuPG TRUST (§4/§8) |
| **INT1099STG / INT1099EXP** | 1099 staging & export | Blank file path / missing indexes (§11) |
| **POSTWKFL** | Post-workflow (posts approved batches) | Fails on missing period / bad reversal batch (§12) |
| **BK010 / BK030 / HFMACCTBAL** | Positive Pay export / bank-statement import / HFM extract | Bank adaptor + SFTP (§4/§8) |
| **QPEC + QRMMT** | Scheduler/engine + middle tier | Restart after FTP changes; reboot both if crashing (§9) |

### Code locations (confirmed via ADO code search)
| Symbol / table | Repo / path | Cluster |
|---|---|---|
| `QPSQCFSImport.cs` | `Quorum.Upstream.QCFS.Batch / Quorum.Upstream.QCFS.QCFSBatchCore/` | §6 core integration (DELETE timeout #1374816) |
| `QSTAG_CORE_INTFC_IMP` BL/DAL/DO + `QCFSUpstreamDBExternalDataAccess.cs` | `Quorum.Upstream.QCFS.Web / Quorum.QCFS.Upstream/{BL,DAL,ExternalImport}/` | §6/§7 staging |
| `QPSDataConversion.cs` | `Quorum.Upstream.QCFS.Batch / Quorum.Upstream.QCFS.UpstreamBatch/` | §6 conversion (`QCFSGLCONV`) |
| `QFrmQSTAGXLSIM.cs` | `Quorum.Upstream.QCFS.ClassicGUI / Quorum.QCFS.SM/` | §5 Excel import |
| `StagCoreIntfcImpDO.cs` / `QstagCoreIntfcImpDO.cs` | `Quorum.Upstream.Shared.Web / Quorum.QCA.DataObject/`, `Quorum.QRA.DataObject/` | §6 QRA/QCA→QCFS boundary |
| `QARCH_CTRL_PROCESS*` / `QARCH_CTRL_PROCESS_STEP` (process & param config) | `<CLIENT>.Upstream.Metadata / STANDARD 16.0/` | §4/§5 process params & overrides |

### Repos
- **`Quorum.Upstream.QCFS.Batch`** — managed batch engine for the import/export/integration processes (`QCFSBatchCore` = `QPSQCFSImport`; `UpstreamBatch` = conversion/export).
- **`Quorum.Upstream.QCFS.Web`** / **`Quorum.Upstream.QCFS.ClassicGUI`** — QCFS screens (AP/AR/GL/BK/SM) and the QSTAGXLSIM classic form.
- **`Quorum.Upstream.Shared.Web`** — shared QCA/QRA data objects at the integration boundary.
- **`<CLIENT>.Upstream.Metadata`** (e.g. `QEQC`, `QCNR`, `QSPR`, `BRM`, `GEC`, `SUM`, `ATR`, `BEP`) — **process params, process-definition overrides, file paths**. **Always check the client metadata layer first** — many regressions are a param/override not checked into the client repo (the 36611 / FTPR-override / PUBBA-adapter pattern). Client DBs are per-tenant SQL Server (`UPS`/`QRA`) + Oracle (`QLS`).

---

## 18. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A process **doubles or duplicates** data from a code path, not a re-run: Open Invoice doubling (24-00990215 / #1699577 / #1710825), QCFSIMPCYC line dups from un-marked staging (25-01001987), duplicate-invoice-across-BU not blocked (24-00942635 / Patch 11&12).
- An **exception hangs a batch** that should be handled: missing-BU-period (25-01007270/25-00999714 → Patch 12), ADPUPLOAD object-ref on control account (#1744756), `QPSQCFSImport` DELETE without timeout (#1374816).
- A **field maps wrong** on correct input: QSTAGXLSIM Do-Type/Tier (24-00966324), Quantity/`TRANS_VOL` (25-01004336), one-digit BU (#1789601), classic-vs-web diff (#1729515), $0 QRA netting breaking A/R (22-00552670).
- A **vendor-table corruption** from the BA screen (25-01020116 / Patch 15), SM093 SOD bypass (26-01107018 / HF 11).
- Provide: **PQID + process/step + exact error**, client + BU + accounting month, the source module (QRA/JIB/QLS/Open Invoice/Excel template), and a repro. Confirm fix availability in the Upstream release notes and the linked WI's target build.

**Handle as Configuration / Cloud Ops (most of the volume) when:**
- **File path / SFTP / FTP** changed: blank IMP/EXP path, wrong process-definition Override path, `FTPR→SFTPR`, `USE_SSH_NET`, FTP Host Definition password/host, FTP 1.0→1.5 (§4, §8) — then **QPEC restart**.
- **Bank adaptor / PGP** format & key: char widths/implied decimal (24-00980402), key casing/name/TRUST (24-00966526), derived-zip null (24-00993395).
- **Master setup** for the interface: BA Use-as-vendor/customer flag, vendor/GLOBAL_BUSINESS rows, missing BA-Suf, auto-number sequence (§10).
- **Period/BU/GL105** blocking a posted import (§12).
- **Stale process locks** (release in QP110, §9) and **scheduled-job active indicators** off after upgrade.
- **Archive/purge (`PRGCOREINT`)** mis-defined (§6).

**Route to Cloud Ops / IT (infrastructure) when:**
- "Can't reach SQL/Oracle/secure gateway" — **IP/ACL range, VPN route (bounce the tunnel), firewall policy expiry** (§13).
- **After a refresh/upgrade** — apply post-refresh connection scripts; re-point process Override paths; re-check param check-in into the client metadata repo.

**Wrong skill (re-route):** Maintenance Groups, PPNs, DOI setup, owner/funds transfers, recoup → **QDO / QRA** skills (these share the Integration category but are not QCFS core financials — §2).

---

*Skill created: 2026-06-14.*
*Based on: 742 closed QCFS Import/Export/Integration SF cases — 139 actionable (Application Configuration 84 + Software Defect 46 + ChangeConfig 9) mined for fix recipes, plus a Training/Customer-Error sample for the FAQ. ADO work items #1699577, #1710825, #1374816, #1565787, #1683641, #1724602, #1752121, #1729515, #1789601, #1809078, #1700169, #1744756, #1766026, #1820238. Code: `QPSQCFSImport.cs` (Quorum.Upstream.QCFS.Batch), `QSTAG_CORE_INTFC_IMP` + `QCFSUpstreamDBExternalDataAccess.cs` (Quorum.Upstream.QCFS.Web), `QFrmQSTAGXLSIM.cs` (Quorum.Upstream.QCFS.ClassicGUI), `<CLIENT>.Upstream.Metadata`.*
*Companion skills: QCFS core-financials posting/period-close; QRA Revenue Accounting; QDO Division Orders.*
