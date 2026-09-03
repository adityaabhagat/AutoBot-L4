# QCFS Issue Knowledge Base (Master Index)

**Product:** QCFS — Salesforce `Product_list__c = 'My Quorum Financial Accounting'` (7,120 cases all-history; actionable pool = Software Defect 509 + Application Configuration 653 = **1,162**, +46 `ChangeConfig` on the wider definition).
**Purpose:** Route a new QCFS case to the right skill § fast — including the withholding-tax family (new skill, 2026-09-02) and the cases that belong to QCA, QRA or the shared QPEC runbook.

> **How to use:** Match the case symptom/keyword in §1 → open the linked skill at the cited § → follow its Quick Triage + Decision Tree. Or search everything at once: `python engine/kb.py search "<symptom>" --product QCFS -k 8`. All § anchors below were verified against the live skill headings on 2026-09-03.

---

## 1. Symptom → Skill Lookup

### 1.1 Core QCFS skills

| If the case mentions… | Go to |
|---|---|
| Posted/paid/rejected voucher **still "Awaiting Approval"** in an AP Inbox (ghost/phantom voucher) · voucher stuck "In Progress"/"Waiting for Approval" · "Workflow instance is no longer available or does not exist" · vouchers in **Could Not Post** after final approval · **POSTWKFL** erroring continuously · **ADPUPLOAD / ADPIMPALLV / APDUPLOAD** import fails or "completed on error" · OpenInvoice / JIBLINK invoices with bad coding · **AP055** intercompany lines disappear (`AutoDeleteOffset`) · AP055 code-block / owner / cost-center grid clears on tab · duplicate vouchers · single invoice **paid on multiple checks** · void/reissue payment-type change · positive-pay rounding · check ZIP missing hyphen / signature line missing · **AP155** state in the ZIP column · BA "Use as Vendor" flag won't save · **1099** amounts doubled (AP170) / wrong box (7 vs 17) | [SKILL_QCFS_Accounts_Payable.md](../skills/SKILL_QCFS_Accounts_Payable.md) §4 A ghost/stuck vouchers · §5 B Could-Not-Post/POSTWKFL · §6 C invoice imports · §7 D AP055 defects · §8 E payments (check/ACH/positive pay/void) · §9 F vendor & BA master · §10 G 1099 · §11 H vendor address/ZIP (§12 ADO · §13 SQL · §14 FAQ) |
| JE / AP / BJE batch **stuck in Post Pending** · POSTWKFL "Initialize Function Failed. Duplicate process found" · batch goes to **Could Not Post (CNP)** · AP voucher duplicated in inbox / orphaned **WFID** · "Account does not have JE Code Type" / FK constraint / null on equity accounts · **ADPUPLOAD** doubles amounts · QRA export shows in QRA but **not in QCFS GL** / out of balance · **GL025** copy/paste of cost centers fails or screen clears · GL025 can't delete a batch or detail row · canned / **financial-statement reports won't run** (`SSRS_ENDPOINT_URL`) · reports won't email (Event Detector 227 / `BRPTEMAIL`) · Trial Balance won't zero / FS mapping (GL232/GL016) · **GL095/GL096/GL097** query returns no data / DW stale · vendor checks returned by bank / ZIP-State misaligned · close or re-open the year | [SKILL_QCFS_General_Ledger.md](../skills/SKILL_QCFS_General_Ledger.md) §4 A posting stuck · §5 B AP voucher workflow · §6 C JE Code Type / code block · §7 D import defects · §8 E GL025 batch JE · §9 F chart of accounts/GL013 · §10 G JE inquiry & GL DW · §11 H financial statements & canned reports · §12 I vendor check & positive pay (§13 ADO · §14 SQL · §15 FAQ) |
| AR076 / QRANET batch **Could Not Post** — "The applied amount + current amount must approach zero" · batch (BI…/BD…) stuck **Post Pending**, stale lock, future `DATETOPOST` · **AR308** "Deposit Journal Definition not set" (BR036) · AR308/AR076 **DocumentManagement** attach error · AR308 "Unable to delete" deposit/receipt (`FIRE_ENTITY_EVENTS`) · **BR005** GL balance wrong / spans two months / void date blank / forced GL-account picklist · BR005 batch creation **times out** or "failed to enable constraints" · can't void a **"reconciled" ACH** · cleared dates show **1926 instead of 2026** · AR076 prepayment requires owner / not in JB340 · Open Apply ID picklist pulls wrong customer · **AR173** accounting-date filter stops working (grid 36062) · Deposit Batch Review / ARR003 / cash-call print wrong | [SKILL_QCFS_AR_BankRecon.md](../skills/SKILL_QCFS_AR_BankRecon.md) §4 A $0 netting/approach-zero · §5 B Post Pending & locks · §6 C AR308 deposit setup · §7 D attachments · §8 E deposit delete · §9 F BR005 defects · §10 G BR005 timeout · §11 H void reconciled ACH / CW005 · §12 I import-driven bad data · §13 J AR076 prepayment/grids · §14 K AR173 grid 36062 · §15 L AR/BR reports (§16 ADO · §17 SQL · §18 FAQ) |
| "No path or filename passed in / defined for this process to imp/exp" · "Date Type import without a specified column format" · **"Algorithm negotiation fail"** / SFTP won't connect after a patch (`USE_SSH_NET`, `FTPR`→`SFTPR`) · files sit in SFTP, never reach `Unprocessed` · **Open Invoice / ADP invoices doubled** (`QSTAG_CORE_INTFC_EXTERNAL_IMP`) · doubled batches from **QCFSIMPCYC** · **QSTAGXLSIM** Excel upload ignores a field / posts to wrong BU · batch stuck Post Pending because SM006 period/BU missing · process won't start, previous run still **locked** (QP110/QP073) · "Business Associate … is not valid" / "Expected 1 instance of Customer … found 0" · **1099 export** errors / `INT1099EXP` path · "can't connect to SQL/Oracle gateway" / secure-gateway ACL · after a UAT refresh the import/export paths still point at PROD | [SKILL_QCFS_Import_Export_Integration.md](../skills/SKILL_QCFS_Import_Export_Integration.md) §4 A SFTP/paths · §5 B QSTAGXLSIM Excel · §6 C QCFSIMPCYC · §7 D ADPUPLOAD/OpenInvoice · §8 E check export/positive pay/encryption · §9 F process locks & QPEC scheduler · §10 G BA/vendor not set up for the interface · §11 H 1099 export/staging · §12 I period/BU/fiscal config · §13 J connectivity & refresh (§14 ADO · §15 SQL · §16 FAQ) |
| Stale/orphaned **workflow locks** blocking approval · POSTWKFL stuck after a maintenance window (QCFSIMPCYC killed mid-run) · POSTWKFL "Specified cast is not valid" / "Nullable object must have a value" · **SM006** not set up for the new year / DELETE-REFERENCE-constraint on opening-closing periods · Business Unit missing from a picklist after MF035/SM006 · "Failed to load the report … filename was empty" after a refresh · report calls the **DEV server** from UBT/UAT (`SRRS_ENDPOINT_URL`, `REPORT_SERVICE_URL`) · Excel export → sign-in fails (Citrix VDA) · report shows **duplicate / pseudo-duplicate rows** or wrong segment · new BA **autonumbers** start at an existing number (`QARCH_TRAN_SEQ`) · "Cannot insert NULL into BANKACCOUNT" in MF035 · **AFE_IMPORT locks every month** · "Not an active JIB property" on an AP invoice · "Cannot add job code" / hidden mandatory column (code-table grid definition) · zip/masked field won't save (`ZIPCODE_MASK_WEB`) · 1099 export option missing (QSTG1099EX vs **QSTG1099OVR**) | [SKILL_QCFS_MasterData_Workflow_Reporting.md](../skills/SKILL_QCFS_MasterData_Workflow_Reporting.md) §4 A workflow locks & POSTWKFL (A1 locks · A2 stale locks · A3 posting defects) · §5 B fiscal period & BU (SM006) · §6 C reports not found/path · §7 D report data wrong · §8 E BA creation & autonumbering · §9 F bank account & ACH setup · §10 G AFE/cost-center/JIB property master · §11 H code tables & grid definitions · §12 I 1099 processes · §13 J environment/path config (§14 ADO · §15 SQL · §16 FAQ) |
| BA "**Saved Successfully**" but the change disappears / VENDOR row missing the Global-BU record (NEW/COPY button) · "The Tax Type (FED) and Tax ID (…) must have an Effective Date To value" · BA state/province dropdown "**No Data Found**" until F5 · "Use as Vendor" recheck → `Violation of UNIQUE KEY constraint 'IX_Vendor_Key'` · **PUBBA** fails / BA not sent to QLS (lock 30022, `PUBBA_LK`, missing `Quorum.ESuite.Integration.QLS`) · "Password Expired" every Monday / Okta account state · no apps in **Citrix Storefront** · wrong access (persona, posting, JE-type edit, AP reverse) · **SOD violation** despite SM093 · **QQM** session timeout / report errors / "Web Intelligence Applet cannot be loaded" · missing SEC group or `SARCH_CNFG_INT_MODULE` entitlement · JEs stuck post-pending after upgrade (scheduler server name removed) | [SKILL_QCFS_Platform_Security.md](../skills/SKILL_QCFS_Platform_Security.md) §4 A Global-BU unsync · §5 B Tax-ID effective date · §6 C other BA/vendor maintenance · §7 D PUBBA→QLS · §8 E login/password/Okta/Citrix · §9 F roles/personas/SOD · §10 G QQM · §11 H GL/JE/AP/check-register screen errors · §12 I platform processes & patch deployment (§13 ADO · §14 SQL · §15 FAQ) |

### 1.2 Withholding tax (new skill — `SKILL_QCFS_Withholding_Tax.md`)

| If the case mentions… | Go to |
|---|---|
| state tax WH lines deleted on Validate/Approve, imported voucher, ICOFFSET_IND, AutoDeleteOffset | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §A1 (Bug 1831243, `APImportDataHandler.cs:719`, 2026.04) |
| no withholding line generated, Post to BU, intercompany, property is not on business unit | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §A2 (Bug 1832480 / SF 26-01110470, 2026.04 Hotfix) |
| no WH line when Property blank, cost center coding, allocation, G&A | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §A3 (Bug 1832726, PR 129569) |
| AP055 voucher not created, AUTO_CREATE_STATE_TAX_WH business rule exception | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §A4 (Bug 1795333, 2026.04) |
| AP200 missing/not visible, PA withholding config, code tables 63019 63020 63021, MT100 Auto Create State Tax WH Entries, QCTRL_AP_ST_TAX_WITHHOLDING, global replication | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §B (SF 26-01107186; Bug 1852050 + DB 1860092/1863368) |
| check run did not deduct federal withholding, single pay ignored, ADP_UPDATE_SINGLE_PAY, SINGLE_PAYMENT_IND | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §C (SF 26-01093081 → Bug 1801422) |
| withholding journalized but check/ACH/positive pay shows gross amount, AP043 withholding percent, backup withholding no Tax ID | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §C (SF 22-00684349, 22-00690458, 24-00979234) |
| INT1099EXP error, 1099MISCINT, OVERRIDE IMP/EXP PATH 265 NULL, QSTG 1099 export retired, QSTG1099OV contiguous memory, QSTG_1099_MISC_OVR | [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) §D (SF 23-00935283, 22-00559099, 24-00937123, 25-00996019) |
| owner state/backup withholding on revenue checks, batch type 18, CW010, CW011 | route to **QRA — not QCFS** (SF 25-01006246, ADO 1716410) — noted in [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) scope note |

Diagnostic SQL for the whole family: `SKILL_QCFS_Withholding_Tax.md` §E · expected-behavior answers: §F · ADO index: §G · escalation: §H.
**Boundary:** 1099 amounts doubled, AP151/`XREF_1099` box overrides, QSTG1099 timeouts and BA/vendor/Tax-ID master setup stay in `SKILL_QCFS_Accounts_Payable.md` §10–§11 — the withholding skill owns only the *calculation and remittance* recipes.

### 1.3 ADO defect-and-fix references (use when the question is "is this already fixed, and in what build?")

| If the case mentions… | Go to |
|---|---|
| POSTWKFL/PSTWKSPLT **"deadlock victim"** / balances not updated (#1739552) · batch stuck **Post In Progress** (#1669576, #1747642, `PSTPRGFIX` #1749964) · POSTWKFL fails when ARCCOREINT or fiscal close is running (by design, #1667696) · POSTWKFL fails posting a **check run** (#1708039) · reversal voucher "no accounts payable configurations set up for this BU" · Web voucher **double-submitted / deletable in workflow** · Validate/Delete/Reclass buttons wrongly enabled · voucher auto-populates wrong Property / wipes AFE coding · **Bulk Voucher Handling** count mismatch · **check prints blank PDF** / duplicate vendor combined · AP155/AP158 wrong company or state-in-zip (#1795190) · **AP150 ACH/EFT** export exception or SSRS down (#1725807) · BA005 vendor edits don't save / PUBBA metadata priority · 1099 box wrong / AP170 columns missing / QP073 override · inter-company voucher won't post with Account Xref · **Fast Track** skips final approval | [SKILL_ADO_QCFS_Accounts_Payable.md](../skills/SKILL_ADO_QCFS_Accounts_Payable.md) §3 A POSTWKFL (A1–A6) · §4 B voucher screen (B1–B4) · §5 C bulk voucher · §6 D reclass/reversal · §7 E AP061 check run/print · §8 F AP150 ACH/EFT · §9 G BA005/vendor master · §10 H 1099/AP170/AP151/QP073 · §11 I IC offset · §12 J Fast Track (§13 fix-version matrix · §14 diagnostics) |
| `Transaction (Process ID NNN) was deadlocked … chosen as the deadlock victim` on POSTWKFL/PSTWKSPLT · batch posted **twice** (fast-track + POSTWKFL) · POSTWKFL "Could Not Post" on an AR076 / netting batch (approach-zero) · `Cannot find column [IDOPENITEM_APPLY]` · `@ba_no` param error on a voucher reversal · check-run batch errors when the vendor has **>1 BA contact** · POSTWKFL "stops processing on error" on the scheduler (DEBUG) · POSTWKFL "could not acquire lock"/"invalid objects" after upgrade · GL025 attachment won't open / AR076 delete-attachment error · POSTWKFL / JBPREPROOF / 1099 / Close-All slow | [SKILL_ADO_QCFS_AR_GL_BankRecon.md](../skills/SKILL_ADO_QCFS_AR_GL_BankRecon.md) §4 A deadlocks · §5 B double-post/Post-In-Progress · §6 C Could-Not-Post data failures · §7 D $0 netting (QRA→QCFS) · §8 E not-code-defects · §9 F GL025/AR076 UI & attachments · §10 G performance (§11 fix-version matrix · §12 diagnostics) |
| POSTWKFL/PSTWKSPLT fails only on the **scheduler** ("unable to establish a connection with any endpoint") · POSTWKFL "Execution Timeout Expired" / blocking DB session · "Workflow: Instance ID … no longer available" on Approve (desk Notice Delivery = Widget, #1552303) · voucher stays PENDING after approve · WF_* events not triggering · load-test perf regressions vs real defects (AP055 Validate, AFE Search by Cost Center) · **frowny face** / console 500 · **Kendo** UI regressions after 2024.10 · XSS hardening pop-ups · password reset with blank email · attachment deletable after submit-to-workflow · ORGCOSTGEN launch pop-up | [SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md](../skills/SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md) §3 A (A1–A5) · §4 B workflow engine (B1–B3) · §5 C performance (C1–C2) · §6 D V2UI/Kendo · §7 E XSS/login · §8 F attachments · §9 G process launch (§10 fix-version matrix · §11 diagnostics) |

---

## 2. CROSS-PRODUCT ROUTING — QPEC engine / scheduler

Any product's QPEC symptom routes to **[../../_shared/skills/SKILL_QPEC_Ops_Runbook.md](../../_shared/skills/SKILL_QPEC_Ops_Runbook.md)**. The runbook is indexed into every product's vector KB, so `kb.py search --product QCFS` already reaches it.

| Product | Symptom | Go to |
|---|---|---|
| QCFS | Batch stuck in Post Pending / POSTWKFL 'Initialize Function Failed. Duplicate process found' / POSTWKFL not scheduled | _shared/SKILL_QPEC_Ops_Runbook.md §3 |
| QRA | BKRVNU / OFR / JEPOSTONLY / CW stuck at PRC or 'Queued for Processing'; POSTWKFL stuck (APP_SERVER_GRP_CD) | _shared/SKILL_QPEC_Ops_Runbook.md §3–§4 |
| QCA | JIB step 'Stopped Processing on Error' / 'Query timeout expired' right after a patch (JBREBILL, JBOWNERALLOC, JBLDJE2CAS, LOSLOAD) | _shared/SKILL_QPEC_Ops_Runbook.md §5 |
| QDO | COPY_DVD_W 'QPEC SYSTEM ERROR' / maintenance group or transfer stuck in Processing / MEG-search QPEC crashes | _shared/SKILL_QPEC_Ops_Runbook.md §3.6 + §4 |
| QPTM | QPEC EXE crash / memory leak (NNCALCFUEL); EDI errors in qtrace.QPTM.QPEC.*.segregated.log; PANIGHTLY dies at exactly 1 hr | _shared/SKILL_QPEC_Ops_Runbook.md §4–§6 |
| TIPS | GMASLDVOLS / segregated child never spawned post-upgrade (QPEC csproj packaging); processes stuck in queue | _shared/SKILL_QPEC_Ops_Runbook.md §6–§7 |
| ALL | 'Gracefully restart the QPECs' / engines down / scheduler service in STPER / 'Unable to establish a connection with any endpoint' | _shared/SKILL_QPEC_Ops_Runbook.md §4c |
| ALL | Post-patch mass timeouts — QPEC.ini/QPEC.exe.config CommandTimeout + COMMAND_TIMEOUT_SECONDS reset by deployment | _shared/SKILL_QPEC_Ops_Runbook.md §5 |
| ALL | Scheduled run fails but manual run of the same process works (SM093 draft/approve/post exclusivity, scheduler identity) | _shared/SKILL_QPEC_Ops_Runbook.md §3.8 |

**Anchor-format note:** `SKILL_QPEC_Ops_Runbook.md` §3 is a numbered 8-step runbook, not sub-headings — `§3.6` / `§3.8` mean **step 6** / **step 8** inside §3 (the runbook's own internal citation style). §4a/§4b/§4c *are* real sub-headings.

**QCFS-specific:** POSTWKFL is the QCFS segregated post-after-workflow drainer (~5-min cycle, `QSegregatedPostWkflBalanceUpdate.cs` in `Quorum.Upstream.QCFS.Batch`, monitored in QP045). "Records stuck in Post Pending" is *always* a POSTWKFL-drainer question first — runbook §3 steps 1–5 (prove it is stuck → service health → scheduler config → locks in QP110 → stuck PQID in QP045) before any product skill.

---

## 3. CROSS-PRODUCT ROUTING — other products

| If the case (filed under QCFS) is really about… | Go to |
|---|---|
| Owner **state/backup withholding on revenue checks** — batch type 18, CW010, CW011, NM 4.9% | **QRA** (SF 25-01006246, ADO Bug 1716410); scope note in [SKILL_QCFS_Withholding_Tax.md](../skills/SKILL_QCFS_Withholding_Tax.md) |
| **JIB** billing cycle, owner/property allocation, rebill, JB0xx screens, EnergyLink/JIBLink, CTF holds — even when the symptom lands in the GL | **QCA** — [../../QCA/skills/SKILL_QCA_Joint_Interest_Billing.md](../../QCA/skills/SKILL_QCA_Joint_Interest_Billing.md); JIB→QCFS tie-out and "Missing Vendor Suffix" posting failures: [../../QCA/skills/SKILL_ADO_QCA_JIB_FixedAssets_LOS.md](../../QCA/skills/SKILL_ADO_QCA_JIB_FixedAssets_LOS.md) §9 |
| **AFE** lifecycle, AFE import, AFE subledger, AFE approval routing | **QCA** — [../../QCA/skills/SKILL_QCA_AFE.md](../../QCA/skills/SKILL_QCA_AFE.md) + [../../QCA/skills/SKILL_ADO_QCA_AFE.md](../../QCA/skills/SKILL_ADO_QCA_AFE.md) (the AFE_IMPORT *lock* stays in QCFS MasterData §4/§10) |
| **Fixed assets / material transfer / DD&A**, FAGLEXPORT code-block rejections | **QCA** — [../../QCA/skills/SKILL_QCA_FixedAssets_Inventory.md](../../QCA/skills/SKILL_QCA_FixedAssets_Inventory.md) |
| **LOS** reports, LOSDD_IMP / LOSLOAD, JEA→GL export | **QCA** — [../../QCA/skills/SKILL_QCA_LOS_Reporting.md](../../QCA/skills/SKILL_QCA_LOS_Reporting.md) |
| **QLS land payments** arriving as AP invoices; PUBBA publishing BAs to QLS | QCFS side = `SKILL_QCFS_Accounts_Payable.md` §6 (Cluster C) and `SKILL_QCFS_Platform_Security.md` §7 (Cluster D); the Land-side defect is **QLS** |
| **QRA→QCFS** journal export / netting ($0 AR lines, QRANET, JE100/JEPOST) | QCFS side = `SKILL_QCFS_AR_BankRecon.md` §4 + `SKILL_ADO_QCFS_AR_GL_BankRecon.md` §7; the export/JE-generation side is **QRA** |

---

## 4. Coverage Map (from `QCFS_Coverage_Plan.md` §4, survey 2026-09-02)

| # | Group | Categories | Est. cases | Actionable | Status |
|---|-------|------------|-----------:|-----------:|--------|
| 1 | AP voucher entry / approval workflow / posting | AP, Workflow | ~1,300 | ~240 | ✅ SKILL_QCFS_Accounts_Payable.md §4–§7 + SKILL_ADO_QCFS_Accounts_Payable.md §3–§6, §12 |
| 2 | AP payments: check run / ACH / positive pay | AP | ~600 | ~105 | ✅ SKILL_QCFS_Accounts_Payable.md §8 + SKILL_ADO_QCFS_Accounts_Payable.md §7–§8 |
| 3 | Vendor/BA master + 1099 + **withholding** | AP, Master Data, eSuite | ~500 | ~90 | ✅ SKILL_QCFS_Platform_Security.md §4–§6 + SKILL_QCFS_Accounts_Payable.md §9–§11 · **PARTIAL GAP now CLOSED → SKILL_QCFS_Withholding_Tax.md** |
| 4 | GL journal entries / balances / fiscal close | GL, (null) | ~800 | ~140 | ✅ SKILL_QCFS_General_Ledger.md + SKILL_ADO_QCFS_AR_GL_BankRecon.md |
| 5 | AR deposits / netting + Bank Recon | AR, BR | ~476 | ~80 | ✅ SKILL_QCFS_AR_BankRecon.md + SKILL_ADO_QCFS_AR_GL_BankRecon.md |
| 6 | Import/Export & cross-product interfaces | Integration, Import/Export, Data Hub, AP | ~800 | ~175 | ✅ SKILL_QCFS_Import_Export_Integration.md |
| 7 | Platform access & security (login/roles) | Security, eSuite | ~700 | ~110 | ✅ SKILL_QCFS_Platform_Security.md §8–§9 |
| 8 | eSuite/V2UI web framework, environment & **QPEC infra** | eSuite, All, (null) | ~500 | ~90 | ✅ SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md + SKILL_QCFS_Platform_Security.md §12 · **PARTIAL GAP now CLOSED → _shared/SKILL_QPEC_Ops_Runbook.md** |
| 9 | QQM & Ad Hoc / SSRS reporting | QQM, Ad Hoc Reporting | ~329 | ~48 | ✅ SKILL_QCFS_Platform_Security.md §10 + SKILL_QCFS_MasterData_Workflow_Reporting.md §6–§7 |
| 10 | Master data & workflow config setup | Master Data, Workflow | ~406 | ~65 | ✅ SKILL_QCFS_MasterData_Workflow_Reporting.md |

Groups 1–10 = **~1,143 / 1,162 actionable (98%)**. Both partial gaps flagged in the survey are now closed: withholding tax (own skill) and QPEC ops (shared runbook). Residual = Other/misc one-offs.

---

## 5. Cross-cutting QCFS patterns (check on every case)

1. **POSTWKFL owns the "stuck" family.** Post Pending, "Could Not Post", "Post In Progress", batches that never appear in the GL — all start at the drainer, not the screen. Cheap ladder: designed wait (future `DATETOPOST`, SM006 period closed) → service/scheduler health → stale lock (QP110) → stuck PQID (QP045) → data/defect. Runbook §3; product-specific detail in GL §4, AP §5, AR/BR §5, MasterData §4.
2. **Locks are the #1 self-service fix.** A failed run leaves its lock and every later cycle fails. Known defect: locks are not released when a job fails to obtain *other* locks — fixed Upstream 2020.09 Hotfix Patch 3 (July 2021); clients below that build hit it repeatedly.
3. **"Account does not have a JE Code Type" is the most common config root cause in GL/AP posting.** GL013 assigns the type; GL105 sets which code-block columns are Allowed/Optional/Required. The same rule shape rejects QCA FAGLEXPORT and JIB-close postings.
4. **BA/vendor master defects cascade into AP, AR, 1099 and QLS.** Global-BU unsync from the NEW/COPY button, trailing spaces, Tax-ID effective dates, ZIP masks, autonumber seeds. Check `Platform_Security` §4–§6 before blaming the transaction screen.
5. **Post-refresh / post-patch config drift** — import/export override paths still pointing at PROD, `SSRS_ENDPOINT_URL` / `REPORT_SERVICE_URL` on the wrong environment, scheduled-job active indicators silently off, `CommandTimeout` reset. Any "it worked last week / works in another env" case starts here.
6. **Category values have legacy duplicates** (`Import/Export` vs `Import / Export`) and ~168 null + 285 "All" cases route by vocabulary — mostly to groups 1, 4 and 6.
7. **Root-cause triage first.** `Software Defect` (509) / `Application Configuration` (653) → real investigation. `Training` (702) / `Customer Error` (475) → expected-behavior answer from the skill's FAQ §. `User Administration Request` (319) / `Cloud Outage` (164) / `Database Refresh Request` → service request, close without investigation.
8. **Fixed-in version is often INFERRED.** Financials work items frequently have an empty build field — infer from `IterationPath` + release tags and confirm against the PR target branch; label the claim INFERRED. Two ADO projects hold QCFS bugs: `QuorumSoftware` (bulk) and `Quorum` (some 2026+, e.g. 1831243).

---

## 6. Standard data sources

- **Salesforce:** connector `soqlQuery`; filter `Product_list__c = 'My Quorum Financial Accounting'`. `LIMIT ≤ 25`. Fix detail lives in Description + CaseComment + EmailMessage, not just `Resolution__c`.
- **Azure DevOps:** org `QuorumSoftware`, projects `QuorumSoftware` + `Quorum`. Area paths `QuorumSoftware\Engineering\Financials\Committed Backlog[\Performance]` (product dev) and `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Financials` (client escalations). Repos: `Quorum.Upstream.QCFS.Web`, `Quorum.QCFS.BL` (`CustomCodeBlockData.cs`, `VoucherBatchBuilder.cs`), classic `Quorum.QCFS.AP` (`QFrmBatchVoucherMaster.cs`), framework `Quorum.QFC.*`, release notes `Quorum.Upstream.QCFS.ReleaseNotes`, import handler `Quorum.QCFS.QCFSExternalImport` (`APImportDataHandler.cs`). Detail: [code_logic/REPO_REFERENCE_UPSTREAM.md](code_logic/REPO_REFERENCE_UPSTREAM.md).
- **Key tables seen in repro text:** `BATCHVOUCHERMASTER`, `BATCHVOUCHERDETAIL`, `BATCHVOUCHERGLDISTRIBUTION` (incl. `ICOFFSET_IND`), `BUSINESSENTITYPERIOD`, `QXREF_AP_DOC`, `QARCH_LOCK_MASTER_PROCESS`, `QCTRL_AP_ST_TAX_WITHHOLDING`; columns `DATEACCT`, `IDBATCHMASTER`, `IDWFINSTANCE`, `IDLINETYPE`, `SINGLE_PAYMENT_IND`.
- **Vector KB:** `python engine/kb.py search "<symptom>" --product QCFS -k 8` (includes `_shared` skills).
- **Coverage survey:** [QCFS_Coverage_Plan.md](QCFS_Coverage_Plan.md) — volumes, category/root-cause distributions, per-group keywords, ADO notes.
- **Legacy routers (still valid for upstream-wide rows):** [UPSTREAM_Issue_Knowledge_Base.md](UPSTREAM_Issue_Knowledge_Base.md), [UPSTREAM_ADO_Defect_Index.md](UPSTREAM_ADO_Defect_Index.md).

---

*Index created 2026-09-03 from `QCFS_Coverage_Plan.md` (survey 2026-09-02) + the 10 live QCFS skills (incl. the new withholding-tax skill) + the shared QPEC runbook. § anchors verified against live skill headings.*

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
