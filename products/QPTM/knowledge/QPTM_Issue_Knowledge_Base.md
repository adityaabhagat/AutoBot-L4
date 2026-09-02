# QPTM Issue Knowledge Base (Master Index)

**Product:** QPTM = Salesforce `Product_list__c = 'My Quorum Gas Pipeline'` (17,176 closed cases as of 2026-06-01)
**Purpose:** Route a new QPTM case to the right skill fast. Built by mining resolved Salesforce cases + cross-referencing Azure DevOps.

> **How to use:** Match the case's symptom/keyword in the lookup table below → open the linked skill → follow its Quick Triage + Decision Tree. If no skill exists yet for the category, see "Coverage Map" for status.

---

## 1. Symptom → Skill Lookup

| If the case mentions… | Go to |
|---|---|
| EDI error code (ENMQR/WNMQR/EEDM/SUBDTL), NMST/NMQR, inbound/outbound nom file | [SKILL_EDI_Troubleshooting.md](SKILL_EDI_Troubleshooting.md) |
| "Late nomination", retroactive nom, cycle closed/deadline, ENMQR315 | [SKILL_EDI_Troubleshooting.md](SKILL_EDI_Troubleshooting.md) §4/§6/§11 |
| "Dates that overlap", "duplicate key", duplicate nom, ghost nom, can't delete/zero a nom | [SKILL_Nominations.md](SKILL_Nominations.md) §4 |
| Nom won't submit, validation blocking (BI/LI), MDQ exceeded, TT/TOS | [SKILL_Nominations.md](SKILL_Nominations.md) §5/§7 |
| Nom upload, NNNOMLOAD, import template, copy-paste noms, 30-day window | [SKILL_Nominations.md](SKILL_Nominations.md) §8 |
| AutoGen creating wrong/excess/late noms, activity codes instead of noms | [SKILL_Nominations.md](SKILL_Nominations.md) §9 |
| Nom deletion request | [SKILL_Nominations.md](SKILL_Nominations.md) §10 |
| Cycle timing, cycle deadline config | [SKILL_Cycle_Deadline_Reference.md](SKILL_Cycle_Deadline_Reference.md) |
| Validation rule investigation (RuleNN*), BI/LI status meaning | [SKILL_QPTM_Nomination_Validation.md](SKILL_QPTM_Nomination_Validation.md) |
| Daily queue triage / "what to work on next" / SLO | [SKILL_Queue_Prioritization.md](SKILL_Queue_Prioritization.md) |
| Allocation/ALALLOCATE failure, PDA, PTR/PPA overlay, OBA/imbalance, wellhead/shared alloc | [SKILL_Allocations.md](SKILL_Allocations.md) |
| Contract (K) maintenance, RFS/offer, TOS/path, MDQ/ratchet, amendment/enrollment, storage/PAL | [SKILL_Contracts.md](SKILL_Contracts.md) |
| Invoice wrong/recalc, BLINVGEN/PANIGHTLY failure, rate config/orphan rates, PPA/cashout, SOA | [SKILL_Billing.md](SKILL_Billing.md) |
| LPS/PAL (park-and-loan) PPA processed but no billing adjustment, "Invalid object name 'BLSTAG_PAL_EXT'" (SQL 208), PEX charge basis, manual LGA workaround | [SKILL_Billing.md](SKILL_Billing.md) §4.4 |
| Capacity release: offer/posting, bid/award/prearranged, recall/reput, IPWS postings, replacement K | [SKILL_Capacity_Release.md](SKILL_Capacity_Release.md) |
| Confirmation not flowing/auto-confirm, scheduled qty/cuts, CAS run/batch, EPSQ, path balancing | [SKILL_Confirmations_Scheduling.md](SKILL_Confirmations_Scheduling.md) |
| User access, login/SSO/MFA, password reset, roles/permissions, external/TPA user provisioning, BA name change | [SKILL_Security_UserAdmin.md](SKILL_Security_UserAdmin.md) |
| Location/meter admin, location groups/zones, code tables/picklists, global/TSP config keys, install/upgrade/hotfix, file paths | [SKILL_Pipeline_Admin_Config.md](SKILL_Pipeline_Admin_Config.md) |
| Customer/BA account balances, storage/pipeline inventory, imbalance trading, cashout/CICO, measurement/meter volumes, INACCTACCM | [SKILL_Customer_Accounts_Inventory.md](SKILL_Customer_Accounts_Inventory.md) |
| Report won't run/wrong data/scheduling, IPWS/EBB postings, FERC RR30/549D/IOC, notifications/emails, audit logging | [SKILL_Reporting_Regulatory_Postings.md](SKILL_Reporting_Regulatory_Postings.md) |
| Non-EDI integrations/APIs, file import/export, batch/job failures, FlowCal/MV90, SFTP, PTR/TIPS sync, QQM (Query Manager) | [SKILL_Integration_Processing.md](SKILL_Integration_Processing.md) |
| Page not loading/spinning, widget not loading/wrong data, grid/column/picklist display, Design Studio, browser, Web-vs-Classic | [SKILL_UI_Widgets.md](SKILL_UI_Widgets.md) |

---

## 2. Coverage Map (skill-build status by category)

Categories ranked by closed-case volume. "Actionable" = `Root_Cause__c IN ('Software Defect','Application Configuration')` — the cases worth encoding.

| Category (`Case_Category__c`) | Closed | Skill status |
|---|---|---|
| Security (+Business Associates) | 3,750 (+47) | ✅ [SKILL_Security_UserAdmin.md](SKILL_Security_UserAdmin.md) (~78% routine User Admin → runbook; ~123 actionable) |
| Allocations | 1,634 | ✅ [SKILL_Allocations.md](SKILL_Allocations.md) (~286 actionable mined) |
| Nominations | 1,462 | ✅ [SKILL_Nominations.md](SKILL_Nominations.md) (~390 actionable mined) |
| Contracts | 776 | ✅ [SKILL_Contracts.md](SKILL_Contracts.md) (~263 actionable mined) |
| Pipeline Admin | 719 | ⬜ Planned |
| Customer Accounts | 716 | ⬜ Planned |
| Billing (+Invoice Gen +Rates) | 631 (+85+170) | ✅ [SKILL_Billing.md](SKILL_Billing.md) (~191 actionable mined; folds in Invoice Generation + Rates) |
| Capacity Release | 377 (+54) | ✅ [SKILL_Capacity_Release.md](SKILL_Capacity_Release.md) (~124 actionable mined) |
| EDI | 297 (+247) | ✅ [SKILL_EDI_Troubleshooting.md](SKILL_EDI_Troubleshooting.md) |
| Confirmations + Scheduling (CAS) | 251 + 242 (+92) | ✅ [SKILL_Confirmations_Scheduling.md](SKILL_Confirmations_Scheduling.md) (~181 actionable mined) |
| Pipeline Admin (+System Config +Location Admin +Installation) | 719 (+414+70+45) | ✅ [SKILL_Pipeline_Admin_Config.md](SKILL_Pipeline_Admin_Config.md) (~323 actionable) |
| Customer Accounts (+Inventory +Pipeline Inventory +Measurement) | 716 (+264+85+71) | ✅ [SKILL_Customer_Accounts_Inventory.md](SKILL_Customer_Accounts_Inventory.md) (~176 actionable; ~654 are User Admin → Security skill) |
| Reporting (+Informational Postings +Regulatory Reporting +Logging +Compliance +Notifications) | 410 (+460+234+389+59+70) | ✅ [SKILL_Reporting_Regulatory_Postings.md](SKILL_Reporting_Regulatory_Postings.md) |
| Integration (+Processing +QQM) | 224 (+294+134) | ✅ [SKILL_Integration_Processing.md](SKILL_Integration_Processing.md) (~138 actionable) |
| User Interface (+Widgets +Design Studio) | 262 (+129+25) | ✅ [SKILL_UI_Widgets.md](SKILL_UI_Widgets.md) |

---

## 3. Cross-cutting patterns (apply to every category)

These came out of the Nominations pilot and should be checked for any QPTM case:

1. **Root-Cause triage first.** Before deep diagnosis, the `Root_Cause__c` distribution predicts the disposition:
   - `Software Defect` / `Application Configuration` → real investigation (the skill content).
   - `Customer Error` / `Training` → likely **Expected Behavior**, user education, no code/config fix.
   - `User Administration Request` → routine access ops.
2. **Ops-runbook clusters are first-class.** High-volume, deadline-driven fixes deployed by Cloud Ops via a **standardized data script** (e.g., the nom-delete / "ghost nomination" script). These rarely have a linked ADO bug — they recur. Capture the *script recipe*, not a one-off.
3. **`Azure_DevOps_Module__c` is unreliable** (null on ~60% of cases). Cluster by **Subject keywords**, not this field.
4. **Client overrides exist.** Many clients have `<CLIENT>.QPTM.Web` repos with custom validation rules — always check for an override before assuming standard behavior.
5. **Enhancement vs Defect.** Some "defect" cases are really enhancement requests (notably AutoGen / load-following). Flag, don't force a code RCA.
6. **Cluster on Quorum's batch/screen acronyms, not generic domain terms.** Subject-keyword clustering with plain English ("imbalance", "swing") misses ~55% of cases. The real vocabulary is process/screen codes: ALALLOCATE, PANIGHTLY, PDA, PTR, PPA, WGT, CUSTACCTACCUM (allocations); BLINVGEN, BLSOAIMP, PANIGHTLY (billing); CRKLCLGEN, NETMDQRES, IPWS, RuleCROF* (capacity release); PBBALCHAIN, EPSQ, CAS (confirmations/scheduling); QCM (contracts). Build the keyword list from these acronyms.
7. **Web vs Classic divergence is a recurring root cause.** myQuorum Web and the legacy Classic (QCM/desktop) screens diverge — Web is often more permissive or fails to persist IDs correctly. When a case says "works in Classic, fails in Web" (or vice versa), suspect a parity bug.
8. **Per-client config layer.** Some categories (esp. Scheduling/CAS) are dominated by client-specific config (REX/Ruby/TREX/TEP) rather than product bugs — check the client's setup before tracing code.

---

## 4. Standard data sources

- **Salesforce:** MCP connector `mcp__12c9ae52-5751-4da7-b869-607f03acd2a8` (`soqlQuery`). QPTM filter: `Product_list__c = 'My Quorum Gas Pipeline'`. Fix detail lives in `Description` + `CaseComment` + `EmailMessage` (not just terse `Resolution__c`).
- **Azure DevOps:** org `QuorumSoftware`; PAT + API cheat sheet in [CONNECTION_CONFIG.md](CONNECTION_CONFIG.md). WIQL by Subject keyword/case number; code search for class/rule names.

---

*Index created: 2026-06-01. Update the Coverage Map and Lookup table as each new SKILL_<Category>.md lands.*
