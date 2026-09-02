# QPTM Study Pack — Master Guide

A complete, source-verified learning path for QPTM (Pipeline Transaction Management).
Pulls together **two documentation sets**:

1. **`ai_help_docs/`** — the in-repo AI Agent Help Docs pulled from `Quorum.QPTM.Web`
   (branch `feature/improved_dmain_for_contracts`, commit `555e197b`). 14 feature folders ×
   3 docs (`domain` / `architecture` / `troubleshooting`) + 5 reference docs. **47 files.**
   These are the authoritative, code-evidenced docs (class names, file paths, line numbers,
   table/column names read firsthand from source).
2. **`../SKILL_*.md`** — the L4 support skill files in the project root. Operationally focused:
   symptoms, diagnostic SQL, resolution recipes, past-case patterns.

Read **domain → architecture → troubleshooting** for any feature, and pair the in-repo doc
with its SKILL file for the L4 angle.

> Pulled 2026-07-09. Source of truth is ADO; re-pull if the branch moves. Some values in the
> docs are flagged **(inferred)** / **(external)** — verify physical names against DAL CodeGen
> for the install you are debugging.

---

## How each feature is documented (the 3-doc convention)

| Doc | Contains | Use when |
|-----|----------|----------|
| `domain.md` | Business concepts, rules, workflows, glossary | You need the *business* context |
| `architecture.md` | Classes, methods, DB schema, algorithms, service deps | You need to *find/modify code* |
| `troubleshooting.md` | Error messages, diagnostic SQL, RCA patterns, historical WIs | You're *investigating an issue* |

---

## Study order (dependency-ordered curriculum)

```
TIER 0  FOUNDATIONS         Locations/Admin → Cycles/Deadlines → Contracts → Rates
   │
TIER 1  CORE LIFECYCLE      Nominations → Validation → Confirmations/Scheduling(CAS)
   │                         → Allocations → Invoicing → Penalties
   │
TIER 2  CAPACITY PRODUCTS   Capacity Release → RFS
   │
TIER 3  SUBLEDGERS          Inventory/Storage/Imbalance → Measurement → Reporting/Postings
   │
TIER 4  CROSS-CUTTING       EDI → Integration → Security → UI/Widgets
```

**80/20 shortcut** — if time is short, master these five (highest L4 case volume):
**Contracts, Nominations (+Validation), Confirmations/Scheduling, Cycles/Deadlines, EDI.**

---

## Module map — every module → its docs

Legend: 📘 in-repo AI help docs (this pack) · 🛠️ SKILL file (project root) · ⭐ = highest case volume

### Tier 0 — Foundations

| Module | Code | 📘 ai_help_docs | 🛠️ SKILL file |
|---|---|---|---|
| **Locations / Pipeline Admin / TSP config** | LOC | [location-management/](ai_help_docs/location-management/domain.md) | [../SKILL_Pipeline_Admin_Config.md](../SKILL_Pipeline_Admin_Config.md) |
| **Cycles & Deadlines** (timing engine) | — | *(embedded in nominations & confirmations)* | [../SKILL_Cycle_Deadline_Reference.md](../SKILL_Cycle_Deadline_Reference.md) |
| **Contracts** ⭐ | CTR | [contracts/](ai_help_docs/contracts/domain.md) | [../SKILL_Contracts.md](../SKILL_Contracts.md) |
| **Rates** | RATE | [rate-management/](ai_help_docs/rate-management/domain.md) | *(rates section of [../SKILL_Billing.md](../SKILL_Billing.md))* |

### Tier 1 — Core transaction lifecycle

| Module | Code | 📘 ai_help_docs | 🛠️ SKILL file |
|---|---|---|---|
| **Nominations** ⭐ | NOM | [nominations/](ai_help_docs/nominations/domain.md) | [../SKILL_Nominations.md](../SKILL_Nominations.md) |
| **Nomination Validation** ⭐ | NOM | [nominations/troubleshooting.md](ai_help_docs/nominations/troubleshooting.md) | [../SKILL_QPTM_Nomination_Validation.md](../SKILL_QPTM_Nomination_Validation.md) |
| **Confirmations** ⭐ | CONF | [confirmations/](ai_help_docs/confirmations/domain.md) | [../SKILL_Confirmations_Scheduling.md](../SKILL_Confirmations_Scheduling.md) |
| **Scheduling / Capacity Allocation (CAS)** | CAS | [capacity-scheduling-allocations/](ai_help_docs/capacity-scheduling-allocations/domain.md) | [../SKILL_Confirmations_Scheduling.md](../SKILL_Confirmations_Scheduling.md) |
| **Allocations (PDA/PPA)** | ALLOC | [allocations/](ai_help_docs/allocations/domain.md) | [../SKILL_Allocations.md](../SKILL_Allocations.md) |
| **Invoicing / Billing** | INVC | [invoice-management/](ai_help_docs/invoice-management/domain.md) | [../SKILL_Billing.md](../SKILL_Billing.md) |
| **Penalties** | PEN | [penalties/](ai_help_docs/penalties/domain.md) | *(penalties section of [../SKILL_Billing.md](../SKILL_Billing.md))* |

### Tier 2 — Capacity products

| Module | Code | 📘 ai_help_docs | 🛠️ SKILL file |
|---|---|---|---|
| **Capacity Release** | CR | [capacity-release/](ai_help_docs/capacity-release/domain.md) | [../SKILL_Capacity_Release.md](../SKILL_Capacity_Release.md) |
| **Request For Service** | RFS | [rfs/](ai_help_docs/rfs/domain.md) | *(RFS section of [../SKILL_Contracts.md](../SKILL_Contracts.md))* |

### Tier 3 — Supporting subledgers

| Module | Code | 📘 ai_help_docs | 🛠️ SKILL file |
|---|---|---|---|
| **Inventory / Storage / Imbalance** | INV | [inventory/](ai_help_docs/inventory/domain.md) | [../SKILL_Customer_Accounts_Inventory.md](../SKILL_Customer_Accounts_Inventory.md) |
| **Measurement** | MEAS | [measurement/](ai_help_docs/measurement/domain.md) | *(see Allocations + Integration)* |
| **Reporting / Regulatory Postings** | — | *(no in-repo folder)* | [../SKILL_Reporting_Regulatory_Postings.md](../SKILL_Reporting_Regulatory_Postings.md) |

### Tier 4 — Integration & cross-cutting

| Module | Code | 📘 ai_help_docs | 🛠️ SKILL file |
|---|---|---|---|
| **EDI Integration** ⭐ | EDI | [edi-integration/](ai_help_docs/edi-integration/domain.md) | [../SKILL_EDI_Troubleshooting.md](../SKILL_EDI_Troubleshooting.md) |
| **Integration Processing** (batch/notify) | — | *(no in-repo folder)* | [../SKILL_Integration_Processing.md](../SKILL_Integration_Processing.md) |
| **Security / User Admin** | — | *(no in-repo folder)* | [../SKILL_Security_UserAdmin.md](../SKILL_Security_UserAdmin.md) |
| **UI / Widgets / Screens** | — | *(no in-repo folder)* | [../SKILL_UI_Widgets.md](../SKILL_UI_Widgets.md) + [../QPTM_SCREEN_INFO/](../QPTM_SCREEN_INFO/README.md) |

> **Note on gaps:** the in-repo help docs cover 14 features. *Cycles/Deadlines, Reporting,
> Integration, Security, and UI/Widgets* have no dedicated in-repo folder — use the SKILL files
> (and `QPTM_SCREEN_INFO/` for screens). Conversely, **CTR↔CR MDQ interaction** has an extra
> deep-dive set at [../Quorum.QPTM.Web/AI_Agent_Help_Docs/contract-maintenance/](../Quorum.QPTM.Web/AI_Agent_Help_Docs/contract-maintenance/architecture.md) (the MDQ over-release defect).

---

## The one flow to internalize

```
CONTRACT (K, MDQ ceiling)          created by RFS / Capacity Release award
   │
   ▼
NOMINATION (NOM)                    shipper requests to move gas on a path/cycle
   │   └─ validation rules (RuleNN*), BI/LI status, ENMQR errors
   ▼
CONFIRMATION (CONF)                 operator confirms/reduces at each point
   │
   ▼
SCHEDULING (CAS)                    engine applies capacity + reduction → Scheduled Qty
   │
   ▼
ALLOCATION (ALLOC)                  measured volumes allocated to contracts (PDA/PPA)
   │
   ▼
INVOICING (INVC) + PENALTIES (PEN)  charges from allocated qty → invoice
```
Every stage is gated by a **cycle deadline** (`PACTRL_CYCLE_DEADLINE` + `CalcDeadline()`).
The **LifeCycle** screen traces one transaction across all stages — best single diagnostic.

---

## Reference docs (in `ai_help_docs/_reference/`)

| File | What it's for |
|---|---|
| [README.md](ai_help_docs/_reference/README.md) | How the in-repo docs are organized |
| [QUICK_REFERENCE.md](ai_help_docs/_reference/QUICK_REFERENCE.md) | Keyword → feature mapping (fast lookup) |
| [WORK_ITEM_INVESTIGATION.md](ai_help_docs/_reference/WORK_ITEM_INVESTIGATION.md) | The WI/case investigation workflow |
| [DOCUMENTATION_STRATEGY.md](ai_help_docs/_reference/DOCUMENTATION_STRATEGY.md) | Doc format/authoring standard |
| [TESTING_GUIDE.md](ai_help_docs/_reference/TESTING_GUIDE.md) | How the modules are tested |

## Other project references (root)

- **[../QPTM_SCREEN_INFO/](../QPTM_SCREEN_INFO/README.md)** — every screen in both UIs (Web + Classic), navigation, architecture.
- **[../CONFIG_REFERENCE.md](../CONFIG_REFERENCE.md)** — config keys.
- **[../REPO_INVENTORY.md](../REPO_INVENTORY.md)** / **[../REPO_REFERENCE.md](../REPO_REFERENCE.md)** — which repo holds what.
- **[../SF_KNOWLEDGE_ARTICLES.md](../SF_KNOWLEDGE_ARTICLES.md)** — Salesforce KB articles.
- **`kb.py`** — vector search across all of the above: `python kb.py search "<symptom/error/table>" -k 8`
  (run `python kb.py build` to index this new study pack).

---

## Three recurring L4 root causes (keep in mind while reading every module)

1. **Config vs code** — most behavior is `QARCH_*` metadata, not code. Check config first.
2. **Web vs Classic** — separate grid/field metadata; many fields never ported. "Broken on Web" is often "never migrated."
3. **Client overrides** — `<CLIENT>.QPTM.*` repos can replace base screens/rules. Verify before assuming base behavior.

---

## Official Quorum training (videos + decks)

- **[OFFICIAL_QPTM_101_Training.md](OFFICIAL_QPTM_101_Training.md)** — catalog of the official **QPTM 101** SharePoint library (9 modules, 22 files: recorded videos + client-facing `TRN_##` decks + Brown-Bag recordings), each linked and mapped to the lifecycle stages and deep docs above. **Watch these first** to build intuition, then go code-deep here.

---

*Study pack assembled 2026-07-09 (docs) / 2026-07-13 (lifecycle guide + QPTM 101 catalog). 47 in-repo docs (`ai_help_docs/`) + 15 SKILL files (root) + official QPTM 101 training library (SharePoint).*
