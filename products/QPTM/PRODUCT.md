# PRODUCT — QPTM (Pipeline Transaction Management)

| | |
|---|---|
| **Code** | QPTM |
| **Salesforce `Product_list__c`** | `My Quorum Gas Pipeline` |
| **Domain** | Gas pipeline: nominations → confirmations/scheduling → allocations → inventory/imbalance → billing/invoicing → capacity release → regulatory postings |
| **UI stack** | myQuorum Web + Classic (Citrix) — Web-vs-Classic parity gaps are a recurring root-cause family |
| **Knowledge status** | FULL — 23 skills (15 SF-mined + 8 ADO defect), study pack, screen info, code cache |

## Vocabulary table (product detection + KB query terms)

| Kind | Terms |
|---|---|
| Batch/process codes | ALALLOCATE, PANIGHTLY, BLINVGEN(1) (incl. "Run All PPAs"), NNNOMLOAD, CFAUTOCONF, CANOMCLTG, PBBALCHAIN, EPSQ, INACCTACCM, CUSTACCTACCUM, ALESVOLIMP, WHMEASIMP, CSUDAILOAD, BLSOAIMP, QRPTLAUNCH, QEMAIL, CW* (exports), CWINDXCUST, CWUNSUBCAP, GSWHALLOC, GSWHALLAPP, CICO, PAN (PPA Approval Nightly), CalcPALExtension (DTE/QLNG) |
| Table prefixes | NNCTRL_* (noms), QTRAN_*, PACTRL_* (pipeline admin, CYCLE_DEADLINE, LOC*), SCTRL_/KCTRL_/KVALD_ (contracts), CRCTRL_* (capacity release), RTCTRL_* (rates), BLTRAN_* (billing, incl. BLTRAN_PPA_EVENT / BLTRAN_INVOICE_GEN_QTY), BLSTAG_* (billing staging, e.g. BLSTAG_PAL_EXT), BLRPTS_* (billing report staging), INTRAN_* (inventory), ALCTRL_* (allocations), QARCH_* (config/metadata), QCODE_* (codes) |
| Error-code patterns | ENMQR### (EDI nom responses, e.g. ENMQR315 late nom), EEDM1xx, Rule failures RuleNN########, RuleCROF###### |
| Screens/concepts | Contract Maintenance, CAS Maintenance, Confirmation Response/Summary, Design Studio, dashboard widgets, IPWS/EBB postings, RR30/549D, IOC, K# contracts, BI/LI/VI nom statuses, TOS (FT/IT/FSS/PAL/ISS/OBA, LPS-F park-and-loan), MDQ/MDIQ/MDWQ, PEX charge basis (PAL Extension), LGA (manual billing adjustment entry), Customer Account Main, Reallocation/PPA Event Maintenance |
| EDI | G873NMST inbound, G874NMQR outbound, NAESB cycles (Timely/Evening/ID1-ID3) |

## Routing rules

- Router: `knowledge/QPTM_Issue_Knowledge_Base.md` (symptom→skill table with § anchors — use it before opening any skill).
- Repos: `knowledge/code_logic/REPO_REFERENCE.md`; client overrides `<CLIENT>.QPTM.*` FIRST; error codes in Quorum.QGM.Database `QCODE_*`.
- Config: `knowledge/config_logic/CONFIG_REFERENCE.md` — `QARCH_CNFG_CTRL`, scopes G/T/TG, typed wrappers in Quorum.QPTM.Common/ConfigSettings.
- Segregated batch: QPEC executor; logs `qtrace.QPTM.QPEC.*.segregated.log`; CommandTimeout resets after every patch.
- Triage priors: `Root_Cause__c` first; `Azure_DevOps_Module__c` ~60% null — cluster on Subject acronyms; Security/UserAdmin is ~78% routine ops runbook.
