# Upstream Accounting — ADO Defect / Fix Knowledge Base (Master Index)

**Source:** Azure DevOps work items (Bugs) under Area Path `QuorumSoftware\Engineering\Financials` (~2,147 bugs) — the upstream accounting suite (QRA / QCA / QDO / QCFS).
**Purpose:** The **defect-and-fix** companion to the Salesforce symptom skills in `..\Upstream Assistant`. Answers: *is this a known bug, what was the root cause, which PR fixed it, and which build contains the fix?*

> **Use this alongside the SF skills, not instead of them.** A consultant starts from a customer symptom → find the cluster in `..\Upstream Assistant\SKILL_*` → then come here to confirm the underlying defect, the fix, and the fixed-in-build. Search both at once: `python "..\Mid L4 Assistant\kb.py" search "<symptom / process / bug#>"`.

---

## 1. Skill Lookup (ADO-sourced defect skills)

| Area | Skill | ADO bugs analyzed |
|---|---|---|
| QRA — revenue distribution, JIB-allocation splits, PPA/rebill, Exago close | [SKILL_ADO_QRA_Revenue_Distribution_PPA.md](SKILL_ADO_QRA_Revenue_Distribution_PPA.md) | 36 of 126 matched |
| QRA — check write, ACH, void runs, OFR, escheat, 1099-on-void | [SKILL_ADO_QRA_CheckWrite_OFR_Escheat.md](SKILL_ADO_QRA_CheckWrite_OFR_Escheat.md) | 22 of 92 |
| QRA — severance/production tax, ONRR, 1099 export, NAUPA | [SKILL_ADO_QRA_Tax_1099_Regulatory.md](SKILL_ADO_QRA_Tax_1099_Regulatory.md) | — |
| QCA — AFE creation/approval/workflow, cost center, V2UI AFE | [SKILL_ADO_QCA_AFE.md](SKILL_ADO_QCA_AFE.md) | — |
| QCA — JIB billing cycle, fixed assets/DD&A, LOS, JEA | [SKILL_ADO_QCA_JIB_FixedAssets_LOS.md](SKILL_ADO_QCA_JIB_FixedAssets_LOS.md) | — |
| QDO — division orders, DOI build, transfers, suspend/release | [SKILL_ADO_QDO_DivisionOrder_Transfers.md](SKILL_ADO_QDO_DivisionOrder_Transfers.md) | — |
| QCFS — accounts payable, vouchers, POSTWKFL/fast-track, vendor | [SKILL_ADO_QCFS_Accounts_Payable.md](SKILL_ADO_QCFS_Accounts_Payable.md) | — |
| QCFS — AR, GL, bank recon, journal, period close | [SKILL_ADO_QCFS_AR_GL_BankRecon.md](SKILL_ADO_QCFS_AR_GL_BankRecon.md) | — |
| Shared — eSuite/Classic, V2UI, workflow (POSTWKFL/PSTWKSPLT), performance/deadlocks, PII | [SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md](SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md) | — |

Each skill = Quick Triage → Decision Tree → clusters (Symptom / Root cause / Fix + fixed-in-build / Workaround / Bug IDs / linked SF cases) → **fix-version matrix** → escalation.

---

## 2. How ADO upstream defects are organized (read before using)

- **No product field in ADO.** All four products share Area Path `Engineering\Financials`; classification into QRA/QCA/QDO/QCFS is by **title/process keyword**, so there is overlap between skills (a bug can appear in two). That's intentional — follow the symptom.
- **The distribution defect mass lives in JIB, which is built in QCA repos**, not QRA. "QRA revenue distribution" issues are very often JIB Owner/Rebill/Property **allocation-splitter** bugs (`Quorum.Upstream.QCA.ClassicBatch/.Database`, `USP_JIB_*_SPLIT` procs). Treat a QRA distribution case as first a JIB-allocation question.
- **Repos:** `Quorum.Upstream.<MODULE>.ClassicBatch / .ClassicGUI / .Web / .Database` + `Quorum.Upstream.Shared.*` + per-client `<CLIENT>.Upstream.*`. Same org as QPTM/TIPS. See `..\Upstream Assistant\REPO_REFERENCE_UPSTREAM.md`.
- **⚠️ Fixed-in-build numbers are INFERRED.** `Microsoft.VSTS.Build.IntegrationBuild` was empty on every bug, so "fixed in 20XX.NN" was derived from the iteration-path sprint (YY.NN) + release tags (e.g. "2023.04 Regression"). **Confirm against Upstream release notes before quoting a build to a client.**
- **Port-back trap:** perf/allocation fixes tagged "Not 2024.10/2025.04 Ups" were not auto-ported to all branches; old custom client branches (e.g. Pioneer v16) get one-off patches. Always confirm the fix is in the *client's* build line.
- **PPA here = prior-period adjustment via JIB Rebill** — NOT the TIPS plant-product "PPA." Do not cross-wire with TIPS skills.

---

## 3. Cross-cutting ADO defect themes

1. **Allocation-splitter child-count bugs** — `USP_JIB_*_SPLIT` procs sized children by row count but work groups by BA; integer-truncation/grouping bugs launch the wrong number of QPEC children (#1367134, #1416291, #1446592). Recurring family.
2. **32-bit QPEC memory exhaustion** on rebill-to-inception / $0 explosions — mitigate with smaller slice size / `ADOBATCH` / $0 suppression.
3. **Trailing-space / NULL data breaking formulas & syncs** — `ACCTG_CLOSE_STATUS_CD` trailing space (Exago TRIM fix), `CHECKRUNJOURNAL.LASTUPDATE` written without time (QLS void-sync misses). Recurring.
4. **Workflow stability** — POSTWKFL/PSTWKSPLT deadlocks, fast-track/orphan-inbox, "Post In Progress" status gaps.
5. **A large share of "bugs" resolve as Rejected / By-Design / config / test-data**, not code — the skills label disposition so you don't chase a non-fix.

---

## 4. Relationship to the Salesforce skills

| Question | Use |
|---|---|
| "Customer reports symptom X — how do I troubleshoot/fix?" | `..\Upstream Assistant\SKILL_*` (SF symptom skills) |
| "Is this a known defect? what's the root cause / which PR / which build?" | **this folder** (ADO defect skills) |
| Config-key behavior | `..\Mid L4 Assistant\CONFIG_REFERENCE.md` |
| Repos / code locations | `..\Upstream Assistant\REPO_REFERENCE_UPSTREAM.md` |

---

*Index created 2026-06-14 from the ADO Financials mining run (9 functional areas over ~2,147 bugs, ~2M tokens). Fixed-in-build values are inferred from iteration/tags — verify in release notes before quoting to clients.*
