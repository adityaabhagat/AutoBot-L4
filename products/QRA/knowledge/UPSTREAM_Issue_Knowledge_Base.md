# Upstream Accounting Issue Knowledge Base (Master Index)

**Products (Salesforce `Product_list__c`):**
- **QRA** = `My Quorum Revenue Accounting` (~8,600 closed)
- **QCA** = `My Quorum Cost Accounting` (~4,000 closed)
- **QDO** = `My Quorum Division Order` (~2,600 closed)
- **QCFS** = `My Quorum Financial Accounting` (~6,800 closed)

**Purpose:** Route a new upstream-accounting case to the right skill fast. Built by mining resolved Salesforce cases + cross-referencing Azure DevOps. Mirrors the QPTM/TIPS knowledge bases.

> **How to use:** Match the symptom/keyword below → open the linked skill → follow its Quick Triage + Decision Tree. Or search everything at once: `python "..\Mid L4 Assistant\kb.py" search "<symptom>"`.

---

## 1. Symptom → Skill Lookup

### QRA — Revenue Accounting
| If the case mentions… | Go to |
|---|---|
| Check Write/Run (CW), negative checks, ACH/EnergyLink, voids, escheat checks, PCW posting | [SKILL_QRA_Check_Processing.md](SKILL_QRA_Check_Processing.md) |
| VL100/BKRVNU/RDCALCNEW revenue-distribution failures, contractual allocation (CA), SOD owner pay, market groups, DRI links | [SKILL_QRA_Revenue_Distribution.md](SKILL_QRA_Revenue_Distribution.md) |
| Prior-period adjustments, impairment reason codes (301/302/305/310/311/314), reverse/rebook not tying, recoup PPNs | [SKILL_QRA_Prior_Period_Adjustments.md](SKILL_QRA_Prior_Period_Adjustments.md) |
| Owner/DOI master data, decimal interest, ownership/property setup, suspense master data | [SKILL_QRA_Ownership_MasterData.md](SKILL_QRA_Ownership_MasterData.md) |
| Severance/production tax (TX/ND/OK/ONRR), 1099 reporting, NAUPA/escheat reporting, tax e-file/EDI | [SKILL_QRA_Tax_Regulatory.md](SKILL_QRA_Tax_Regulatory.md) |
| Revenue journal entries, GL posting from revenue, JE balancing | [SKILL_QRA_Journal.md](SKILL_QRA_Journal.md) |
| Acquisitions & dispositions, payouts, owner funds release (OFR), escheat funds | [SKILL_QRA_AcqDisp_Payouts.md](SKILL_QRA_AcqDisp_Payouts.md) |
| Production/volume allocation, volumetric reporting, gas balancing, royalty volumes | [SKILL_QRA_Volume_Allocation.md](SKILL_QRA_Volume_Allocation.md) |
| eSuite / owner web portal: BA web screens (Contacts/Addresses/Documents tabs), "Factory QCFSDataHelper does not exist", zip/postal mask (`ZIPCODE_MASK_WEB` / `SCODE_COUNTRY.ZIP_CD_MASK_WEB`), V17 web down after refresh, `/EQCU17QRAAPI` 500, owner check-detail contact info | [SKILL_QRA_eSuite_OwnerPortal.md](../skills/SKILL_QRA_eSuite_OwnerPortal.md) |
| Integration, security, QQM, system config, non-eSuite platform/infra for QRA | [SKILL_QRA_Platform_Integration_Security.md](SKILL_QRA_Platform_Integration_Security.md) |

**No `Case_Category__c` (387 cases; sampled 3 pages 2026-09-03 — mis-filed PPA + check-write symptoms, route by vocabulary):**

| If the uncategorized case mentions… | Go to |
|---|---|
| `Impaired Reason 301`/`311`, PPN not generated, rejected Land PPN, PPA duplicate payment, `LD18` PPNs from paycode changes (SF 26-01087692/26-01117981, 25-01023975, 24-00994991, 26-01071081, 23-00897334, 23-00894089 — LD18 "Resolved in v17."), PPN errors after rebuilding masterlink (26-01104139) | [SKILL_QRA_Prior_Period_Adjustments.md](../skills/SKILL_QRA_Prior_Period_Adjustments.md) |
| Escheat reversal / suspense listing for escheat, negative check amounts, `CW_MAIN` `TRANS_VAL_AMT` footing error, void checks with foreign withholding, escheat-state wrong after BA address change (SF 26-01114255, 26-01092353, 26-01083190, 23-00883589, 23-00924119, 24-00958182) | [SKILL_QRA_Check_Processing.md](../skills/SKILL_QRA_Check_Processing.md) |
| `CWONRFNDRL` fails "cannot insert NULL into column 'ORIG_BUS_UNIT_CD'... `JSTG_JE_INPUT`", `OFR stuck in Queued` (SF 24-00968735, 24-00995401, 26-01102265) | [SKILL_QRA_Check_Processing.md](../skills/SKILL_QRA_Check_Processing.md) |
| `VL100` MaxLength/processing errors, `RRID` results not landing in `RD031` (SF 26-01066422, 25-01043564, 23-00924646, 26-01065631) | [SKILL_QRA_Revenue_Distribution.md](SKILL_QRA_Revenue_Distribution.md) |
| 1099 process errors `QP043` / `CW1099EXPG` filed without category (SF 23-00877080, 22-00565012, 22-00584887) | [SKILL_QRA_Tax_Regulatory.md](SKILL_QRA_Tax_Regulatory.md) |

### QCA — Cost Accounting
| If the case mentions… | Go to |
|---|---|
| Joint Interest Billing (JIB), billing decks, JB screens, rebill, JIB-to-revenue | [SKILL_QCA_Joint_Interest_Billing.md](SKILL_QCA_Joint_Interest_Billing.md) |
| AFE (Authorization for Expenditure), AFE approval/workflow, capital authorization | [SKILL_QCA_AFE.md](SKILL_QCA_AFE.md) |
| Fixed assets, inventory (FA), DD&A, capital tracking | [SKILL_QCA_FixedAssets_Inventory.md](SKILL_QCA_FixedAssets_Inventory.md) |
| Lease Operating Statement (LOS), ad hoc reporting, journal entry allocations (JEA) | [SKILL_QCA_LOS_Reporting.md](SKILL_QCA_LOS_Reporting.md) |
| eSuite/web, workflow, integration, security, QQM for QCA | [SKILL_QCA_Platform_Workflow_Integration.md](SKILL_QCA_Platform_Workflow_Integration.md) |

### QDO — Division Order
| If the case mentions… | Go to |
|---|---|
| Division orders, DOI build, decimal interest, owner relations, conveyance | [SKILL_QDO_Division_Orders.md](SKILL_QDO_Division_Orders.md) |
| Ownership transfers, suspend/release, query screens | [SKILL_QDO_Transfers_SuspendRelease.md](SKILL_QDO_Transfers_SuspendRelease.md) |
| eSuite/web, integration, Design Studio, security, QQM for QDO | [SKILL_QDO_Platform_Integration.md](SKILL_QDO_Platform_Integration.md) |

### QCFS — Financial Accounting
| If the case mentions… | Go to |
|---|---|
| Accounts Payable (AP), vouchers, vendor invoices, payment runs | [SKILL_QCFS_Accounts_Payable.md](SKILL_QCFS_Accounts_Payable.md) |
| General Ledger (GL), journal entries, period close, chart of accounts, financial statements | [SKILL_QCFS_General_Ledger.md](SKILL_QCFS_General_Ledger.md) |
| Accounts Receivable (AR), bank reconciliation (BR) | [SKILL_QCFS_AR_BankRecon.md](SKILL_QCFS_AR_BankRecon.md) |
| Import/export, integration, Data Hub feeds into financials | [SKILL_QCFS_Import_Export_Integration.md](SKILL_QCFS_Import_Export_Integration.md) |
| Financial master data, workflow, ad hoc reporting | [SKILL_QCFS_MasterData_Workflow_Reporting.md](SKILL_QCFS_MasterData_Workflow_Reporting.md) |
| eSuite/web platform, security, QQM for QCFS | [SKILL_QCFS_Platform_Security.md](SKILL_QCFS_Platform_Security.md) |

**Cross-product:** repo/architecture orientation → [REPO_REFERENCE_UPSTREAM.md](REPO_REFERENCE_UPSTREAM.md); config keys → `..\Mid L4 Assistant\CONFIG_REFERENCE.md`; queue triage → adapt `..\TIPS Assitant\SKILL_Queue_Prioritization.md`.

---

## 2. Coverage Map (all ✅ — mined 2026-06-14)

| Product | Skill | Actionable mined |
|---|---|---|
| QRA | Check_Processing | 268 |
| QRA | Revenue_Distribution | 199 |
| QRA | Prior_Period_Adjustments | 158 |
| QRA | Ownership_MasterData | ~187 |
| QRA | Tax_Regulatory | 71 |
| QRA | Journal | ~76 |
| QRA | AcqDisp_Payouts | ~59 |
| QRA | Volume_Allocation | ~44 |
| QRA | Platform_Integration_Security | ~169 |
| QCA | Joint_Interest_Billing | 213 |
| QCA | AFE | 145 |
| QCA | FixedAssets_Inventory | 33 |
| QCA | LOS_Reporting | 38 |
| QCA | Platform_Workflow_Integration | 133 |
| QDO | Division_Orders | 333 |
| QDO | Transfers_SuspendRelease | 99 |
| QDO | Platform_Integration | 77 |
| QCFS | Accounts_Payable | 446 |
| QCFS | General_Ledger | 117 |
| QCFS | AR_BankRecon | 72 |
| QCFS | Import_Export_Integration | 139 |
| QCFS | MasterData_Workflow_Reporting | 66 |
| QCFS | Platform_Security | 208 |

23 skills, ~3,300 actionable cases mined.

---

## 3. Cross-cutting upstream patterns (check on every case)

1. **Repo structure** — upstream code lives in the **same `QuorumSoftware` ADO org** as QPTM/TIPS, under `Quorum.Upstream.<MODULE>.*` (e.g. `Quorum.Upstream.QRA.ClassicBatch`, `.ClassicGUI`, `Quorum.Upstream.Shared.Web`) plus per-client overrides `<CLIENT>.Upstream.<MODULE>.*` and `<CLIENT>.Upstream.Metadata`. Always check the client override layer before assuming base behavior. See [REPO_REFERENCE_UPSTREAM.md](REPO_REFERENCE_UPSTREAM.md).
2. **Post-upgrade metadata-layer drift** — the single most common config root cause: after an upgrade/hotfix, metadata (grid defs, registered SQL, dynamic export defs, processes) lands in the wrong layer, or dynamic export definitions point at client `ESUITE_Q*` views instead of core. Suspect this for any "worked before the upgrade" report/screen/export failure.
3. **Config store is shared with QPTM** — `QARCH_CNFG_CTRL` (global + per-client). Keys like `WRITE_TO_DB_ONLY_AT_END` (RD locking), `AUTO_POST_OFR`, `TOLERANTDEC`/`DISTRIBUTION.TOLERANTDEC`. See `..\Mid L4 Assistant\CONFIG_REFERENCE.md`.
4. **Process diagnostics start with PQID + first ERROR + SQLID/ORA** — upstream batch (QPEC seg-processes) failures: get the Process Queue ID, the first ERROR line, and the impairment/reason code, then map via the cluster tables. Don't read past the first real error.
5. **Suspense & DOI are the spine of QRA/QDO** — most revenue/owner symptoms trace back to DOI setup (interest type, accounting rule CUR-vs-HIS, decimal interest) or suspense rules. Verify master data before tracing code.
6. **Reverse/rebook & PPA** — like TIPS, restates generate reversal+rebook pairs; missing reversal-source rows (`RTRN_VL_RVSL_SRC`) or wrong RRID (`RONL_MI_STAT`) cause PPAs not to tie. Reversal-doubling is a recurring code defect family.
7. **eSuite is the web layer** — "works in Classic, fails in Web/eSuite" parity bugs recur, same as QPTM/TIPS.
8. **Root-Cause triage first** — `Software Defect`/`Application Configuration`/`ChangeConfig` → real investigation; `Training`/`Customer Error` → expected-behavior answer; `User Administration Request`/`Database Refresh Request` → ops runbook. Note: QRA/QCFS often have **no `ChangeConfig` value** at all and **high blank-Resolution rates** on legacy defect tickets (recipes reconstructed from Description + ADO).

---

## 4. Standard data sources

- **Salesforce:** the Salesforce connector (`soqlQuery`). Product filters above. Fix detail lives in `Description` + `Resolution__c` (legacy upstream defect cases are frequently blank — reconstruct from Description + ADO, and say so).
- **Azure DevOps:** org `QuorumSoftware`; connection details in `..\Mid L4 Assistant\CONNECTION_CONFIG.md`. Code search for `Quorum.Upstream.*` classes/procs/screens.
- **Vector KB:** `python "..\Mid L4 Assistant\kb.py" search "<symptom>"` — indexes QPTM + TIPS + Upstream skills + cached code.

---

*Index created 2026-06-14 from the upstream mining run (23 category groups across 4 products, two batches, ~5.5M tokens of case analysis). Coverage map fully ✅.*
