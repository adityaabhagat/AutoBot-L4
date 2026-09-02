# Midstream (QPTM + TIPS) — ADO Defect / Fix Knowledge Base (Master Index)

**Source:** Azure DevOps Bugs for Quorum's midstream products, mined 2026-06-14.
**Purpose:** The **defect-and-fix** companion to the Salesforce symptom skills (QPTM → `..\Mid L4 Assistant`, TIPS → `..\TIPS Assitant`). Answers: *is this a known bug, what was the dev root cause, which PR fixed it, and which build contains the fix?*

> **Use alongside the SF skills, not instead.** Start from the customer symptom → find the cluster in the SF skill → then come here to confirm the underlying defect, the fix, and whether the client's build has it. Search everything at once: `python "..\Mid L4 Assistant\kb.py" search "<symptom / process / bug#>"`.

---

## 1. Where the bugs live (ADO area paths)

ADO has **no product field**. Midstream bugs span three Engineering area branches:

| Area Path | Bugs | Product |
|---|---|---|
| `Engineering\Energy Transportation` (Pirates of Pipeline, Pipeline Galaxy/Titans, Infinite Refresh) | ~2,654 | **QPTM** (clean) |
| `Engineering\Midstream` (Guardians of TIPS, TIPS Samurai, TIPS'n Tricks) | ~3,204 | **TIPS** (clean) |
| `Engineering\Maintenance\Midstream and Transportation` (Customer Service, Professional Service + the team leaves) | ~5,888 | **QPTM + TIPS mixed** — the customer-case goldmine |

Each skill was scoped to its product's **dev area + the Maintenance branch**, filtered by product-specific functional keywords, with cross-product titles dropped (noted per skill).

---

## 2. Skill Lookup

### QPTM (8)
| Area | Skill |
|---|---|
| Nominations, EDI (NMST/NMQR/RRFC), cycle, late nom, ENMQR, autogen, nom upload | [SKILL_ADO_QPTM_Nominations_EDI.md](SKILL_ADO_QPTM_Nominations_EDI.md) |
| Contract Maintenance, RFS, Offer/Bid/Award, Capacity Release, MDQ/ratchet | [SKILL_ADO_QPTM_Contracts_RFS_Offer_CapacityRelease.md](SKILL_ADO_QPTM_Contracts_RFS_Offer_CapacityRelease.md) |
| Confirmations, RQCF, scheduling, CAS, path balancing, autoconf | [SKILL_ADO_QPTM_Confirmations_Scheduling_CAS.md](SKILL_ADO_QPTM_Confirmations_Scheduling_CAS.md) |
| Allocation/ALALLOCATE, PPA, imbalance, reallocation, PTR overlay, PDA | [SKILL_ADO_QPTM_Allocations_PPA_Imbalance.md](SKILL_ADO_QPTM_Allocations_PPA_Imbalance.md) |
| Invoice/BLINVGEN, billing, rates, SOA, invoice group, cashout, PANIGHTLY | [SKILL_ADO_QPTM_Billing_Invoice_Rates.md](SKILL_ADO_QPTM_Billing_Invoice_Rates.md) |
| Reports, IPWS/EBB postings, FERC/549D/RR30, notifications | [SKILL_ADO_QPTM_Reporting_Postings_Regulatory.md](SKILL_ADO_QPTM_Reporting_Postings_Regulatory.md) |
| Security, user/login/SSO, BA, config, integration, batch process, location/meter admin | [SKILL_ADO_QPTM_Security_Admin_Config_Integration.md](SKILL_ADO_QPTM_Security_Admin_Config_Integration.md) |
| Widgets, dashboards, grids/picklists, eSuite, Design Studio, Web parity | [SKILL_ADO_QPTM_UI_Widgets_Web.md](SKILL_ADO_QPTM_UI_Widgets_Web.md) |

### TIPS (8)
| Area | Skill |
|---|---|
| Allocation groups, PPA, imbalance, Facility/Company Batch Jobs (FBJS/CBJS), plant | [SKILL_ADO_TIPS_Allocations_PPA_Imbalance_FBJS.md](SKILL_ADO_TIPS_Allocations_PPA_Imbalance_FBJS.md) |
| Settlement/SETTLEMGR, revenue, gas statements, query screens, reporting, journal views | [SKILL_ADO_TIPS_Settlement_Revenue_Statements_Reporting.md](SKILL_ADO_TIPS_Settlement_Revenue_Statements_Reporting.md) |
| Measurement, volume import, FLOWCAL, WHMEASIMP, analysis, tickets | [SKILL_ADO_TIPS_Measurement_VolumeImport_FlowCal.md](SKILL_ADO_TIPS_Measurement_VolumeImport_FlowCal.md) |
| Contracts/CCT, contract meter, meter definition/split, paystation, master data, gas lift | [SKILL_ADO_TIPS_MasterData_Contracts_CCT_Meter.md](SKILL_ADO_TIPS_MasterData_Contracts_CCT_Meter.md) |
| Invoice, billing, rates, fees, CICO, settlement invoice, escalation | [SKILL_ADO_TIPS_Invoice_Billing_Rates.md](SKILL_ADO_TIPS_Invoice_Billing_Rates.md) |
| CAW, external users, OKTA/QCloud, CAWDATA replication, integration/DataSync, API host, SAP, QQM, Exago | [SKILL_ADO_TIPS_CAW_ExternalUsers_Integration_DataSync.md](SKILL_ADO_TIPS_CAW_ExternalUsers_Integration_DataSync.md) |
| Batch/QPEC, API host, reseed, purge/archive, environment/refresh, config, Citrix, TRNX_ID, SFTP | [SKILL_ADO_TIPS_Batch_Processing_SystemConfig_Env.md](SKILL_ADO_TIPS_Batch_Processing_SystemConfig_Env.md) |
| Web query screens, interactive reports, grids/picklists, eSuite, Excel export, Web-vs-Classic | [SKILL_ADO_TIPS_UI_Web_InteractiveReports_eSuite.md](SKILL_ADO_TIPS_UI_Web_InteractiveReports_eSuite.md) |

Each skill = Quick Triage → Decision Tree → clusters (Symptom / Root cause / Fix + fixed-in-build / Workaround / Bug IDs / linked SF cases) → **fix-version matrix** → escalation.

---

## 3. Critical caveats (carry into every answer)

1. **⚠️ Fixed-in-build numbers are INFERRED.** `Microsoft.VSTS.Build.IntegrationBuild` was empty on every analyzed bug and iteration paths hold only a dev sprint (YY.NN), not a release. Release/patch targets (2024.04, 2024.10, 2025.04, 2025.10, 2026.04, client HFs) were read from **dev comment threads / PR cherry-pick notes** and marked "(inferred)". **Confirm in Quorum.QPTM / TIPS release notes (or the linked patch WI) before promising a client a build.**
2. **No product field → keyword scoping → some overlap.** The Maintenance branch is mixed; agents dropped cross-product titles (~43 QPTM bugs dropped from the TIPS allocation skill, ~17 TIPS bugs from the QPTM nom skill, etc.). A bug can legitimately appear in two skills — follow the symptom.
3. **"PPA" means different things by product.** QPTM PPA = Prior-Period Adjustment (billing, `BLTRAN_PPA_EVENT`); TIPS PPA = prior-period allocation restate. Do not cross-wire, and neither is the *upstream* JIB-rebill PPA.
4. **Many "bugs" resolve as data/config/by-design, not code** — sequence resync, eff-date/dup-row delete scripts, PDA setup, stale-optimizer-stats (add CALC_STATS), client Allocate-DLL rule registration. The skills label disposition so you don't chase a non-fix.
5. **Recurring infra signatures:** intermittent batch failures that "rerun clean" = QPEC crash / dropped DB connection / index fragmentation / stale stats → route to QCloud/DBA, not Engineering. Statement value bugs = a fix landing on only one of the posted (`QPOST_RPTS_*`) vs non-posted (`QRPTS_*`) views, or core-vs-client `.RPT` — fix all four places.

---

## 4. Relationship to the other knowledge bases

| Question | Use |
|---|---|
| QPTM customer symptom → troubleshoot/fix | `..\Mid L4 Assistant\SKILL_*` + `QPTM_Issue_Knowledge_Base.md` |
| TIPS customer symptom → troubleshoot/fix | `..\TIPS Assitant\SKILL_TIPS_*` + `TIPS_Issue_Knowledge_Base.md` |
| **Known defect? root cause / PR / fixed-in-build?** | **this folder** (ADO defect skills) |
| Upstream (QRA/QCA/QDO/QCFS) equivalents | `..\Upstream Assistant` (symptoms) + `..\Upstream ADO Assistant` (defects) |
| Config keys | `..\Mid L4 Assistant\CONFIG_REFERENCE.md` |
| Repos / code | `..\Mid L4 Assistant\REPO_INVENTORY.md` |

---

*Index created 2026-06-14 from the midstream ADO mining run (16 functional areas across QPTM + TIPS, two batches, ~4M tokens, ~5,800 bugs in scope). Fixed-in-build values inferred from comments/PRs — verify in release notes before quoting to clients.*
