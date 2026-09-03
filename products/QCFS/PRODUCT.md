# PRODUCT — QCFS (Quorum Financial Accounting)

| | |
|---|---|
| **Code** | QCFS |
| **Salesforce `Product_list__c`** | `My Quorum Financial Accounting` (7,118 cases, confirmed via aggregate SOQL 2026-09-02) |
| **Domain** | Upstream financial accounting: accounts payable → AR/bank reconciliation → general ledger → master data/workflow/reporting → imports/exports & integration → platform security |
| **Platform** | eSuite / V2UI; QPEC segregated processes — incl. **POSTWKFL** (segregated post-after-workflow drainer, ~5-min cycle, `QSegregatedPostWkflBalanceUpdate.cs` in Quorum.Upstream.QCFS.Batch, monitored in QP045) |
| **Knowledge status** | GOOD — 10 harvested skills (7 SF-mined incl. Withholding Tax + 2 ADO defect + shared eSuite/V2UI) + shared QPEC ops runbook; gap survey complete 2026-09-02 (`knowledge/QCFS_Coverage_Plan.md`), router built (`knowledge/QCFS_Issue_Knowledge_Base.md`). Both survey gaps closed |

## Vocabulary table (grow via survey + cases)

Seeded from `knowledge/QCFS_Coverage_Plan.md` §4 per-group keywords + §5 ADO notes, survey 2026-09-02.

| Kind | Terms |
|---|---|
| Batch/process codes | `POSTWKFL` (Post Pending → Posted), `PSTWKSPLT`, `PSTPRGFIX`, `QCFSIMPCYC` / `QCFSIMP`, `QCFSEXPORT` (inbound from QRA), `ARCCOREINT`, `ADPUPLOAD` / `ADPIMPALLV` / `APDUPLOAD`, `QSTAGXLSIM` / `QSAGXLSIMP`, `QSTG1099EX` / `QSTG1099OVR`, `INT1099EXP`, `GL013 DATAPUBLISH`, `PUBBA`, `AFE_IMPORT`, `QP073` (run process), `QP045` (process monitor), `QP110` (lock release), `BRPTEMAIL`, `QEMAIL`, `QRPTLAUNCH` |
| AP screens & terms | `AP043` `AP048` `AP055` `AP056` `AP061` `AP150` `AP151` `AP155`/`AP156`/`AP157`/`AP158` `AP170` `AP175` `AP200` · voucher, batch voucher, Post Pending, Could Not Post, approval inbox, reject/resubmit, reversal, reclass, WFID, Approved Final, Fast Track, check run, check print, ACH, NACHA, EFT, remit advice, positive pay, void/reissue, wire, single pay, cleared date |
| GL / AR / BR screens | `GL013` `GL014` `GL025` `GL092` `GL095` `GL096` `GL097` `GL105` `GL232` · BJE, MJE, journal entry, JE Code Type, code block, fiscal year, balance refresh, out of balance, trial balance, retained earnings, accrual reversal, intercompany, `LSEALLOC`, `JBPREPROOF` · `AR076` `AR086` `AR090` `AR173` `AR308` `AR044` · deposit, deposit with match, JIB netting, pre-check write (PCW), cash call · `BR005` `BR036` `BR037` `CW005`, bank recon, outstanding checks |
| Withholding tax | `AP200`, `AP043`, code tables `63019`/`63020`/`63021`, `QCTRL_AP_ST_TAX_WITHHOLDING`, `ICOFFSET_IND`, `AutoDeleteOffset`, `AUTO_CREATE_STATE_TAX_WH`, `SINGLE_PAYMENT_IND`, `ADP_UPDATE_SINGLE_PAY`, MT100 "Auto Create State Tax WH Entries", PA withholding, backup withholding, `1099MISCINT`, `QSTG_1099_MISC_OVR` |
| Master data / workflow / security | `SM002` `SM006` `SM021` `SM093` `SM270`/`SM275`/`SM400` `MF035` `WF005` `QP045` · business unit, company, fiscal period, cost center, AFE, code table, autonumber (`QARCH_TRAN_SEQ`, `AUTONUMBERINGMASTER`), grid definition, field mask (`ZIPCODE_MASK_WEB`), workflow lock, `PUBORGCC`, consolidated BU · Okta, OpenID, Citrix/Storefront, QCloud, persona, SOD, MFA, secure gateway |
| Concepts | AP invoice imports (incl. QLS land payments — AP Cluster C), bank recon, GL post, PUBBA BA-publish (`Quorum.ESuite.Integration.QLS`), Connection Mgmt entries (QLS/QLandDataHelper), OpenInvoice, JIBLINK, EnergyLink, Corcentric, CONCUR, `QRANET`/`QRAREV`, `HFMACCTBAL`, `APDYNEXP`, SFTP/FTP drop folder, `USE_SSH_NET` · QQM universe, SSRS, `SSRS_ENDPOINT_URL` / `REPORT_SERVICE_URL`, `RPT_`, `ARR003`/`ARR005`/`APR004` |
| Key tables | `BATCHVOUCHERMASTER` `BATCHVOUCHERDETAIL` `BATCHVOUCHERGLDISTRIBUTION` `BUSINESSENTITYPERIOD` `QXREF_AP_DOC` `QARCH_LOCK_MASTER_PROCESS` `QSTAG_CORE_INTFC_IMP` / `_EXTERNAL_IMP` `GENERALLEDGERTRANSACTION` `VENDOR` · columns `DATEACCT` `IDBATCHMASTER` `IDWFINSTANCE` `IDLINETYPE` `ICOFFSET_IND` `APP_SERVER_GRP_CD` |
| Repos | `Quorum.Upstream.QCFS.Web`, `Quorum.QCFS.BL` (`CustomCodeBlockData.cs`, `VoucherBatchBuilder.cs`), `Quorum.QCFS.AP` (`QFrmBatchVoucherMaster.cs`), `Quorum.QCFS.QCFSExternalImport` (`APImportDataHandler.cs`), `Quorum.Upstream.QCFS.Batch` (`QSegregatedPostWkflBalanceUpdate.cs`), framework `Quorum.QFC.*`, `Quorum.Upstream.QCFS.ReleaseNotes`. ADO Area Paths `QuorumSoftware\Engineering\Financials\Committed Backlog[\Performance]` and `...\Maintenance\Upstream\Professional Services\Financials`; projects `QuorumSoftware` + `Quorum` |

## Routing rules

- **Router: `knowledge/QCFS_Issue_Knowledge_Base.md`** (symptom → skill §, withholding-tax rows, coverage map, cross-product routing). Legacy upstream-wide rows: `knowledge/UPSTREAM_Issue_Knowledge_Base.md` + `knowledge/UPSTREAM_ADO_Defect_Index.md`.
- Repos: `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`; client overrides first.
- Cross-product touchpoints: QLS→AP invoice imports, QRA→QCFS journal export (JE100/JEPOST side lives in QRA skills), JIB/AFE/FA/LOS symptoms → QCA skills, **owner state/backup withholding on revenue checks (batch type 18, CW010/CW011) → QRA, not QCFS**. Router §3.
- QPEC engine/scheduler symptoms (any product) → `products/_shared/skills/SKILL_QPEC_Ops_Runbook.md` — router §2.
- "Records stuck in Post Pending" = POSTWKFL segregated drainer symptom → batch-debugger SEGREGATED family + runbook §3 steps 1–5.
- Caveat: SF category has legacy duplicates (`Import/Export` vs `Import / Export`); ~168 null + 285 "All" cases route by vocabulary.
