# QCA Issue Knowledge Base (Master Index)

**Product:** QCA — Salesforce `Product_list__c = 'My Quorum Cost Accounting'` (4,235 cases all-history; actionable pool = Software Defect 279 + Application Configuration 354 = **633**, ~15%).
**Purpose:** Route a new QCA case to the right skill § fast — including the cases that are *filed* under QCA but *owned* by QCFS or the shared QPEC runbook.

> **How to use:** Match the case symptom/keyword in §1 → open the linked skill at the cited § → follow its Quick Triage + Decision Tree. Or search everything at once: `python engine/kb.py search "<symptom>" --product QCA -k 8`. All § anchors below were verified against the live skill headings on 2026-09-03.

---

## 1. Symptom → Skill Lookup

| If the case mentions… | Go to |
|---|---|
| AFE stuck in **Pending/PEN** after final approval · "Workflow Instance ID no longer available" · AFE route fully approved but won't Open · **AFERECLASS** / WIP-to-NET failing · "DOI KEY is invalid" · AFE approval **emails not generating** · **AFEEXTIMP / AFE_IMPORT** failing / Event Detector missing · Working Interest **doubling** vs DOI (`AFE_SYNCDOI`) · "Query returned no results" opening an AFE · `AFEMaintNNNNNN` validation firing wrongly · `ValidatePropBusUnit` · post-upgrade blank AFE Inbox / no widget count · `.PNG not supported` attachment · "No Personas" in AFE Web · AFE **Subledger** account / line-category blank · can't inactivate an AFE Route / delete a desk · approval limits · reopen/close/cancel AFE blocked | [SKILL_QCA_AFE.md](../skills/SKILL_QCA_AFE.md) §4 A stuck-Pending · §5 B Reclass · §6 C notifications · §7 D import · §8 E V17/QCloud fallout · §9 F WI doubling · §10 G attachments · §11 H security/personas · §12 I subledger · §13 J route/desk/limits · §14 K status changes (§15 ADO · §16 SQL · §17 FAQ) |
| JIB step **"Stopped Processing on Error"** / "Timeout exceeded while waiting for execution of this Batch" (JBREBILL, JBLDJE2CAS, JBROLLDATE, JBJOURNAL) · `JBXRF_KEYWORD_DERIVATION` event not defined · "code block item not allowed for account" · amounts do not sum to zero · JIB **out of balance** / `GL014` ≠ `JB080` · `STRAN_CORE_INTFC` restage · **Owner Allocation** CE/SPE "Failed to retrieve DO info" / doubled decimals · **Property Allocation / rebill** DOI validation · producing/drilling/completion **overhead** rebill wrong or triplicated · duplicate reversals · duplicate `JBTRN_CTF` rows · **EnergyLink / JIBLink** export missing an owner (no PRT line) / out of memory · **prepay / cash call** not on JB340 · **CTF failure hold** JB390 reason I or D · odd only after a V16/V17/Permian/MEW upgrade (client-layer drift) | [SKILL_QCA_Joint_Interest_Billing.md](../skills/SKILL_QCA_Joint_Interest_Billing.md) §4 A timeouts · §5 B keyword derivation · §6 C out-of-balance · §7 D owner alloc · §8 E property alloc/rebill · §9 F overhead · §10 G duplicates · §11 H EnergyLink/JIBLink · §12 I prepay/cash calls · §13 J CTF holds · §14 K upgrade drift (§15 ADO · §16 SQL · §17 FAQ) |
| **FAGLEXPORT** "fields not allowed for code block on account" (Inventory ID, Material Transfer No, Serial No, UOM Code) · MT **Post to Subledger** failing · MT imported JE in **Could Not Post** / GL025 Vendor No not editable (FA110) · MT posted to GL but **no AFE subledger records** (`MT100` mapping) · MT data **duplicated** in GL · **DD&A** schedule wrong method / UOP vs **UOPLWE** / template reload · DD&A post "month already closed in DDA module" · inventory quantity / **average cost** mismatch · FA Inventory property filter / company droplist not sorted · can't save Inventory **grid layout** · FA010 missing a Business Unit · DDA security groups | [SKILL_QCA_FixedAssets_Inventory.md](../skills/SKILL_QCA_FixedAssets_Inventory.md) §4 A FAGLEXPORT code block · §5 B MT post/subledger · §6 C MT→AFE subledger · §7 D DD&A config · §8 E DD&A post/divest · §9 F inventory qty/cost · §10 G screens/picklists/layouts · §11 H FA master data (§12 ADO · §13 SQL · §14 FAQ) |
| `LOSDD_IMP` fails in a **registered SQL** (`Sel_PRDN_VOL`, `Sel_Intfc_Trans…`, `m_sel_prdn_vol failed`) · `LOSDD_IMP` **ODBC error** on a scheduled run · `LOSLOAD` Stopped-Processing-on-Error / FULL-refresh timeout · LOS report **$0** or missing recent months · LOS report **duplicated** 2x–6x · LOS values wrong after V16→V17 (custom view override) · LOS scheduled job **not running** · `QTRAN_LOS_CUSTOM_SL` blank · **JEGLEXPORT** "succeeds" but no GL095 batch (NULL in IN-clause) · `COREIMPJE` timeout · JEA setup/upload config · AFE01 overhead doubled · QQM **JIB Subject Area universe missing** · check register / AP061 print or numbering error (as reported in QCA) · WF_QUEUE email hyperlink cut off · invoice stuck in no-one's inbox | [SKILL_QCA_LOS_Reporting.md](../skills/SKILL_QCA_LOS_Reporting.md) §4 A LOSDD_IMP/LOSLOAD (A1 reg-SQL · A2 ODBC · A3 timeout) · §5 B LOS values wrong · §6 C schedules · §7 D JEA→GL (D1 JEGLEXPORT · D2 COREIMPJE · D3 setup) · §8 E report accuracy/access · §9 F workflow inbox (§10 ADO · §11 SQL · §12 FAQ) |
| "Can't log in" / no apps, widgets, personas, desks · SEC_USER_ID vs email mismatch · Okta/SSO out of sync · client-prefixed username (`GLE_`/`CEN_`/`REP_`) · can't open a screen (AP055, GL025, JB200, CI022, Manual JE) · **BA won't save** / "two BAs with same name" / BA fields clear / BA Entity ID autofill · vendor name **disappears from voucher** (trailing space on BA) · invoice "fully approved but still in workflow" / **workflow lock not released** · stuck process lock after one bad run · document attach/open/delete · **FTP Transfer Definition** missing for image export · **MT100 Core Interface Cross Reference** missing · ADP / Open-Invoice import errors · QCFS import cycle errors after patch · post-cutover config drift / "Collision with nonsysgen object trigger" · Web ≠ Classic · process timeouts (QSTG1099EX, JBOWNERALLOC, LOSDD_IMP) · "Max retries hit for lock type" · **QQM** report won't launch / "Statement(s) could not be prepared" · positive-pay file won't generate · Citrix memory / app crashing | [SKILL_QCA_Platform_Workflow_Integration.md](../skills/SKILL_QCA_Platform_Workflow_Integration.md) §4 A security/Okta · §5 B BA screen · §6 C workflow stuck & locks · §7 D attachments/export · §8 E integration/MT100 · §9 F upgrade drift · §10 G timeouts/restarts/lock config · §11 H QQM · §12 I check/payment file (§13 ADO · §14 SQL · §15 FAQ) |
| **ADO-side AFE defect lookup** — AFE status stays PENDING (#1583340) · orphan WF inbox (#1555429, #1710580) · "Workflow no longer available" from desk Notice Delivery = Widget (#1552303) · duplicate REJECT rows · AFERECLASS "Conversion failed converting varchar to int" (#1624997) · AFEEXTIMP re-import not inserting (#1372042) · cost-center SQL error on AR076/AP055 (#1718881) · cost-center coding not populating Internal BA/Tier/DOI (#1640913) · budget = N× actual cartesian · AFE **Search by Cost Center slow** (#1566911) · AP055 Validate runs hours (#1721402) · AFE Type save FK error · final-approve email data/URL · V2UI/Kendo AFE screens · QDO **ORGCOSTGEN** process failed | [SKILL_ADO_QCA_AFE.md](../skills/SKILL_ADO_QCA_AFE.md) §4 A workflow/inbox · §5 B inbox display · §6 C cost center · §7 D import/QP053 · §8 E reports · §9 F budget/WI/DOI · §10 G AFE type/numbering · §11 H notifications · §12 I V2UI · §13 J performance · §14 K ORGCOSTGEN (§15 fix-version matrix · §16 diagnostics) |
| **ADO-side JIB/FA/LOS defect lookup** — JB005 `Invalid column name` / `m_INS_SEXT_CORE_INTFC` / IDENTITY at BIGINT limit · "Create billing journal entries" / "Finalize and Post Results" stops on error · missing `JBCDE_FAILURE` code · JIB launching **hundreds of child jobs that do nothing** · `JBOACHILD`/`LOSEXTCHLD` "not enough Contiguous Memory" / UCALC error · LOSDD_IMP "Row cannot be located for updating" (two properties on one `ID_COST_CNTR`) · duplicate rows in `QTRAN_LOS_CUSTOM_SL`/`QFACT_LOS` · **JEA003** invalid SQL · JIBLink excludes/duplicates prepayment-only rebills · JIB JE won't post in QCFS "Missing Vendor Suffix" (`USP_JIB_COMPRESSOR` space vs NULL) · **JBR030/031/036/037** report cosmetics · **FAR012 / MT Proof** picklist filter · Close Reconciliation Report not reconciling · "works in CORE_SUP but not here" / script missing at deployment | [SKILL_ADO_QCA_JIB_FixedAssets_LOS.md](../skills/SKILL_ADO_QCA_JIB_FixedAssets_LOS.md) §4 A JB005 · §5 B child-job splitting · §6 C LOSDD/LOSLOAD · §7 D JEA · §8 E JIBLink · §9 F JIB⇄QCFS tie-out · §10 G JBR0xx reports · §11 H FA reports/imports · §12 I close recon · §13 J deployment gaps (§14 fix-version matrix · §15 diagnostics) |
| **Shared platform defect lookup** — POSTWKFL/PSTWKSPLT fails only on the **scheduler** ("unable to establish a connection with any endpoint") · POSTWKFL "Execution Timeout Expired" / blocking DB session · PSTWKSPLT fails on upgrade · "Workflow: Instance ID … no longer available" on Approve · AFE/voucher stays PENDING after approve · WF_* events not triggering · dashboard / View Full Inbox load-test regressions · AP055 Validate hours / AFE Search by Cost Center 40s+ · **frowny face** page / console 500 · **Kendo** UI regressions after 2024.10 · XSS hardening pop-ups · password reset with blank email · attachment deletable after submit-to-workflow · ORGCOSTGEN launch pop-up | [SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md](../skills/SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md) §3 A POSTWKFL scheduler (A1 DEBUG/impersonation · A2 blocking session · A3 index · A4 sysgen · A5 data-driven) · §4 B workflow engine (B1–B3) · §5 C performance (C1–C2) · §6 D V2UI/Kendo · §7 E XSS/login · §8 F attachments · §9 G process launch (§10 fix-version matrix · §11 diagnostics) |

---

## 2. Coverage Map (from `QCA_Coverage_Plan.md` §3, survey 2026-09-02)

| # | Group | SF categories | Est. cases | Actionable | Status |
|---|-------|---------------|-----------:|-----------:|--------|
| 1 | JIB billing cycle & allocations | Joint Interest Billing (JIB) | 1,349 | 231 | ✅ SKILL_QCA_Joint_Interest_Billing.md + SKILL_ADO_QCA_JIB_FixedAssets_LOS.md |
| 2 | AFE lifecycle, import & approval | Authorization for Expenditure (AFE) | 1,152 | 163 | ✅ SKILL_QCA_AFE.md + SKILL_ADO_QCA_AFE.md |
| 3 | eSuite / Web UI & screens | eSuite | 194 | 46 | ✅ SKILL_QCA_Platform_Workflow_Integration.md + SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md |
| 4 | Workflow engine (AP/AFE routing, locks, batch post) | Workflow | 196 | 43 | ✅ SKILL_QCA_Platform_Workflow_Integration.md §6 + shared eSuite skill §3–§4 |
| 5 | Integration & file exchange | Integration, Data Hub | 138 | 37 | ✅ SKILL_QCA_Platform_Workflow_Integration.md §8 |
| 6 | Fixed Assets / Inventory / DD&A / MT | Inventory (FA), DD&A (FA), Capital Tracking | 201 | 36 | ✅ SKILL_QCA_FixedAssets_Inventory.md + SKILL_ADO_QCA_JIB_FixedAssets_LOS.md §11 |
| 7 | LOS, Ad-Hoc Reporting & JEA | LOS, Ad Hoc Reporting, JEA | 398 | 40 | ✅ SKILL_QCA_LOS_Reporting.md |
| 8 | Security / access / SSO | Security | 190 | 15 | ✅ SKILL_QCA_Platform_Workflow_Integration.md §4 |
| 9 | QQM report plumbing | QQM | 63 | 9 | ✅ SKILL_QCA_Platform_Workflow_Integration.md §11 |
| 10 | **GL/AP/AR core transactions filed under QCA** (check write, void check, AP vouchers, deposit batches, AR balances) | subset of null / All / Other / Workflow | ~60 | ~12 | ↗ **Cross-product — owned by QCFS**, see §3 below (no QCA-side skill needed; the "SKILL_QCA_GL_AP.md (planned)" pointers in the QCA skills resolve here) |
| 11 | Environment & deployment ops (refreshes, QPEC restarts, hotfixes, Citrix/QCloud) | All, null, Other (remainder) | ~290 | ~10 | ↗ Partly SKILL_QCA_Platform_Workflow_Integration.md §9/§10; QPEC engine/scheduler symptoms → **[../../_shared/skills/SKILL_QPEC_Ops_Runbook.md](../../_shared/skills/SKILL_QPEC_Ops_Runbook.md)**; the rest are service requests, not investigations |

Groups 1–9 alone = **620 / 633 actionable (98%)**. Groups 10–11 are routed, not built.

---

## 3. CROSS-PRODUCT ROUTING (read before opening any QCA skill)

### 3.1 The misfiled GL/AP/AR group — filed under QCA, owned by **QCFS**

Coverage-plan group 10. These cases arrive with `Product_list__c = 'My Quorum Cost Accounting'` (usually null/`All`/`Other` category) but every recipe lives in the QCFS skills. Do **not** open a QCA skill for them.

| If the case mentions… | Go to (QCFS) |
|---|---|
| **check write** · check run · AP061 · check print blank/wrong · reissue · positive pay · ACH/EFT/NACHA · remittance advice | [../../QCFS/skills/SKILL_QCFS_Accounts_Payable.md](../../QCFS/skills/SKILL_QCFS_Accounts_Payable.md) §8 (Cluster E payments) · ADO detail: [../../QCFS/skills/SKILL_ADO_QCFS_Accounts_Payable.md](../../QCFS/skills/SKILL_ADO_QCFS_Accounts_Payable.md) §7 (E check run/print) · §8 (F AP150 ACH/EFT) |
| **void check** · void/reissue changes payment type · voiding a "reconciled" ACH · CW005 check register · cleared/void date blank | SKILL_QCFS_Accounts_Payable.md §8 · [../../QCFS/skills/SKILL_QCFS_AR_BankRecon.md](../../QCFS/skills/SKILL_QCFS_AR_BankRecon.md) §11 (Cluster H void reconciled ACH / CW005) · §9 (Cluster F BR005 void date) |
| **AP voucher** creation / approval / import / ghost or phantom voucher · "Awaiting Approval" on a posted voucher · Could Not Post · AP055 grid clears · duplicate vouchers · voucher back to Draft · Post Pending | SKILL_QCFS_Accounts_Payable.md §4 (A ghost/stuck) · §5 (B Could-Not-Post/POSTWKFL) · §6 (C invoice imports) · §7 (D AP055 defects) · ADO: SKILL_ADO_QCFS_Accounts_Payable.md §3 (A), §4 (B), §5 (C bulk), §6 (D reclass/reversal) |
| **deposit batch** · AR308 deposit / deposit-with-match · "Deposit Journal Definition not set" · deposit delete / `FIRE_ENTITY_EVENTS` · Deposit Batch Review Report · deposit batch deleted leaves items locked | SKILL_QCFS_AR_BankRecon.md §6 (C AR308 setup / BR036) · §8 (E deposit delete) · §15 (L AR/BR reports) |
| **AR173** · customer item inquiry · AR balances / open items wrong · AR173 accounting-date filter stops working (grid 36062) · AR076 prepayment lines · AR netting "must approach zero" | SKILL_QCFS_AR_BankRecon.md §14 (K AR173 / grid 36062) · §13 (J AR076 prepayment) · §4 (A $0 netting) · ADO: [../../QCFS/skills/SKILL_ADO_QCFS_AR_GL_BankRecon.md](../../QCFS/skills/SKILL_ADO_QCFS_AR_GL_BankRecon.md) §7 (D $0 netting) |
| **GL batch activity date** / accounting-date wrong on a GL batch · **GL025 greyed out** commands · GL025 can't delete a batch or detail row · GL025 copy/paste of cost centers fails · batch in non-Normal control type · GL025 attachment won't open | [../../QCFS/skills/SKILL_QCFS_General_Ledger.md](../../QCFS/skills/SKILL_QCFS_General_Ledger.md) §8 (E GL025 batch JE creation) · §9 (F COA/GL013 maintenance) · §15 (FAQ — batch control type is often expected behavior) · ADO: SKILL_ADO_QCFS_AR_GL_BankRecon.md §9 (F GL025/AR076 UI) |
| **SM275** / SM270 / SM400 import-xref & voucher-template config · import cross-reference missing for a voucher template | [../../QCFS/skills/SKILL_QCFS_Import_Export_Integration.md](../../QCFS/skills/SKILL_QCFS_Import_Export_Integration.md) §2 (screen map) + §6 (C QCFSIMPCYC) · master-data angle: [../../QCFS/skills/SKILL_QCFS_MasterData_Workflow_Reporting.md](../../QCFS/skills/SKILL_QCFS_MasterData_Workflow_Reporting.md) §11 (H code tables/grid definitions) |
| GL account has **no JE Code Type** / "code block item not allowed for account" raised from a **QCFS** batch (not the JIB close) | SKILL_QCFS_General_Ledger.md §6 (C JE Code Type / code block) — the JIB-close variant stays in SKILL_QCA_Joint_Interest_Billing.md §5–§6 |

**Boundary rule:** if the failing artifact is a **JIB/AFE/FA/LOS** object (JB*, AFE*, FA*, LOS*), it is QCA. If it is a **voucher, check, deposit, AR open item, or GL025 batch**, it is QCFS even when the case is filed under QCA. State the re-route explicitly in the report; do not silently investigate in the wrong product.

### 3.2 QPEC engine / scheduler symptoms → **[../../_shared/skills/SKILL_QPEC_Ops_Runbook.md](../../_shared/skills/SKILL_QPEC_Ops_Runbook.md)**

The runbook is indexed into every product's vector KB, so `kb.py search --product QCA` already reaches it.

| Product | Symptom | Runbook § |
|---|---|---|
| QCFS | Batch stuck in Post Pending / POSTWKFL "Initialize Function Failed. Duplicate process found" / POSTWKFL not scheduled | §3 |
| QRA | BKRVNU / OFR / JEPOSTONLY / CW stuck at PRC or "Queued for Processing"; POSTWKFL stuck (`APP_SERVER_GRP_CD`) | §3–§4 |
| **QCA** | JIB step **"Stopped Processing on Error"** / "Query timeout expired" right after a patch (JBREBILL, JBOWNERALLOC, JBLDJE2CAS, LOSLOAD) | §5 |
| QDO | `COPY_DVD_W` "QPEC SYSTEM ERROR" / maintenance group or transfer stuck in Processing / MEG-search QPEC crashes | §3.6 + §4 |
| QPTM | QPEC EXE crash / memory leak (NNCALCFUEL); EDI errors in `qtrace.QPTM.QPEC.*.segregated.log`; PANIGHTLY dies at exactly 1 hr | §4–§6 |
| TIPS | GMASLDVOLS / segregated child never spawned post-upgrade (QPEC csproj packaging); processes stuck in queue | §6–§7 |
| ALL | "Gracefully restart the QPECs" / engines down / scheduler service in STPER / "Unable to establish a connection with any endpoint" | §4c |
| ALL | Post-patch mass timeouts — `QPEC.ini` / `QPEC.exe.config` CommandTimeout + `COMMAND_TIMEOUT_SECONDS` reset by deployment | §5 |
| ALL | Scheduled run fails but a manual run of the same process works (SM093 draft/approve/post exclusivity, scheduler identity) | §3.8 |

**Anchor-format note:** `SKILL_QPEC_Ops_Runbook.md` §3 is a numbered 8-step runbook, not sub-headings — `§3.6` / `§3.8` mean **step 6** / **step 8** inside §3 (the runbook's own internal citation style). §4a/§4b/§4c *are* real sub-headings.

**QCA-specific QPEC note:** the QCA JIB timeout family is the single most common QCA "batch broke after a patch" signature — `CommandTimeout` in `QPEC.ini`/`QPEC.exe.config` (default 3600 → 18000) plus the global `COMMAND_TIMEOUT_SECONDS` are reset by deployments. Cross-referenced from SKILL_QCA_Joint_Interest_Billing.md §4, SKILL_QCA_LOS_Reporting.md §4, SKILL_QCA_Platform_Workflow_Integration.md §10.

---

## 4. Cross-cutting QCA patterns (check on every case)

1. **Client-layer (CEN/QFC) metadata drift is the #1 upgrade cause.** Config re-checked in the *core* layer is wiped by the next patch; rows must be synced from DEVA1 and checked into the **client** layer (JIB §14, Platform §9). Any "worked before the upgrade / works in CORE_SUP but not here" case starts here.
2. **Code-block rules (GL013 JE Code Type + GL105 column flags) cause failures in three modules.** "Field/code block item not allowed for account" surfaces from FAGLEXPORT (FA §4), the JIB close (JIB §5–§6), and QCFS GL posting (QCFS GL §6). Same fix shape: flip the offending column to Optional.
3. **Timeout-after-patch family** — see §3.2. Never deep-dive a "Stopped Processing on Error" before checking CommandTimeout and whether QPEC was restarted after the config edit.
4. **Locks are the cheapest exit.** Stuck process lock (PQID held it), "Max retries hit for lock type", AFE_IMPORT locking monthly — release in QP110/QP073 and raise Lock Setup retries (Platform §6/§10, runbook §3 step 4).
5. **JIB defects live in QCA repos even when reported against another product** — JIB allocation, rebill and owner-allocation bugs are QCA-owned regardless of the filing product (PRODUCT.md vocabulary note).
6. **Fixed-in version is INFERRED on QCA bugs.** `Microsoft.VSTS.Build.IntegrationBuild` is empty on Financials work items — infer from `IterationPath` (e.g. `Product Development\25.19`) + release tags and confirm against the PR target branch. Label the claim INFERRED.
7. **Two ADO projects, two area-path trees.** Search `project IN (QuorumSoftware, Quorum)`; area paths `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Financials` (client escalations, SF case number usually in the title), `...\Upstream\Professional Services`, and the older `QuorumSoftware\Engineering\Financials` tree the ADO skills were mined from. Client prefixes in titles: EQC/EQT, JNE, SGY, GLE, MEW, APHU, SRC, PNR.
8. **Root-cause triage first.** `Software Defect` / `Application Configuration` (633 cases) → real investigation. `Training` (446) / `Customer Error` (317) → expected-behavior answer from the skill's FAQ §. `Database Refresh Request` / `User Administration Request` / `Cloud Outage` → service request, close without investigation.
9. **Category is unreliable on ~345 cases** (null 136 + All 154 + Other 55) — route those by vocabulary, and check §3.1 first because that is where the misfiled GL/AP/AR group hides.

---

## 5. Standard data sources

- **Salesforce:** connector `soqlQuery`; filter `Product_list__c = 'My Quorum Cost Accounting'`. `LIMIT ≤ 25`. Fix detail lives in Description + CaseComment + EmailMessage, not just `Resolution__c`.
- **Azure DevOps:** org `QuorumSoftware`, projects `QuorumSoftware` + `Quorum`. Repos: module tier `Quorum.QCA.{Database, Metadata, Reports, Application.MiddleTier, Application.Web, Application.APIHost, Batch, ClassicBatch}`; shared `Quorum.Upstream.*` and `Quorum.ESuite.*` (watch inconsistent `Esuite` casing); client-prefixed repos hold per-tenant overrides. No standalone `Quorum.QCA.API` repo. Detail: [code_logic/REPO_REFERENCE_UPSTREAM.md](code_logic/REPO_REFERENCE_UPSTREAM.md).
- **Vector KB:** `python engine/kb.py search "<symptom>" --product QCA -k 8` (includes `_shared` skills).
- **Coverage survey:** [QCA_Coverage_Plan.md](QCA_Coverage_Plan.md) — volumes, category/root-cause distributions, per-group keywords, ADO notes.
- **Legacy routers (still valid for upstream-wide rows):** [UPSTREAM_Issue_Knowledge_Base.md](UPSTREAM_Issue_Knowledge_Base.md), [UPSTREAM_ADO_Defect_Index.md](UPSTREAM_ADO_Defect_Index.md).

---

*Index created 2026-09-03 from `QCA_Coverage_Plan.md` (survey 2026-09-02) + the 8 live QCA skills. § anchors verified against live skill headings.*

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
