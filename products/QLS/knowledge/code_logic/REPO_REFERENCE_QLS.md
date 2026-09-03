# REPO REFERENCE — QLS (Quorum Land System)

> **Scope:** where QLS code, metadata, and client overrides live in Azure DevOps, plus the branch/tag conventions the version gate (G3) depends on and the Oracle environment naming the metadata connector needs.
> **Sources:** ADO discovery recorded in [../QLS_Coverage_Plan.md](../QLS_Coverage_Plan.md) (§ADO notes, survey 2026-09-02) + repo/branch anchors cited in the 13 QLS skills (2026-09-03). Every repo and area path below was seen on a real work item or PR.
> **Sibling:** [REPO_REFERENCE_UPSTREAM.md](REPO_REFERENCE_UPSTREAM.md) — the QDO/QRA/QCFS (SQL Server) upstream set. QLS is **Oracle** and does not share those repos.

---

## 1. Azure DevOps organisation & projects

**Org:** `QuorumSoftware`.

QLS bugs are split across **two projects** — always search both:

| Project | Era / use | Iteration style |
|---|---|---|
| `QuorumSoftware` | Bulk of QLS history (through ~2025) | classic sprint paths |
| `Quorum` | Current work, 2026+ | PI-based, e.g. `Quorum\PI 26.2\26.2.4` |

## 2. Area paths (verified from real bugs)

| Area path | Project | What lands here | Example work items |
|---|---|---|---|
| `QuorumSoftware\Engineering\Land\Committed Backlog` | QuorumSoftware | Product-development bugs and committed backlog items | #1708512, #1693760 |
| `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` | QuorumSoftware | **L4 / maintenance escalations** — the default path for a new QLS customer defect | #1702244 |
| `Quorum\North America\Upstream\Land RnD` | Quorum | Current escalated maintenance bugs, 2026+ | #1814672, #1808498 |

**New-defect filing rule (from the skills' Escalation sections):** file to `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land`, or the project-`Quorum` path `Quorum\North America\Upstream\Land RnD` for current PI work. Link the SF case, include a repro from a `<CLIENT3>L_HD_DEV17_QLS` environment, and state the client's hotfix train.

**Search order for "is this already fixed?":** ADO bug titles routinely embed the Salesforce case number — search ADO by case number **before** searching by symptom text.

---

## 3. Core repositories (project `QuorumSoftware`)

### 3.1 QLS application

| Repo | Contents / when to search it |
|---|---|
| `Quorum.QLS.Web` | The web application — screens, controllers, JS bundles. **The repo hotfix PRs land in** (see §5). Grid/screen JS defects (e.g. `RelatedWells.js`), controller regressions (`System.MethodAccessException … get_NoteControllers`). |
| `Quorum.QLS.ServiceCore` | Service layer. Confirmed files: `QQLSServiceCore_Financial.cs` (payments, check runs, financial detail), `QQLSServiceCore_EcalBatch.cs` (eCalendar batch/workflow). Start here for payment-processing and ECALWF logic. |
| `Quorum.QLS.Metadata` | Core (non-client) screen/config/security metadata — `QARCH_*` seed data, registered SQL, code-table definitions. |
| `Quorum.QLS.Database` | Oracle DDL, PL/SQL packages, triggers, sequences (`ACRE_CALC`, `PCK_UPDT_MAP_STATUS_CORE`, `TR_LD_METES_BOUNDS_LGL_DTL`, `STIP_SEQ`, `AFIS_GL_XREF_SEQ`). |
| `Quorum.QLS.DataObject` | Data-access/entity layer between ServiceCore and the `lis` schema. |
| `Quorum.QLS.ClassicGUI` | Legacy Windows/Classic client screens (still live for some nodes; "Web ≠ Classic" behaviour differences originate here). |
| `Quorum.QLS.QLandShared` | Shared QLand libraries used by web, classic and batch. |
| `Quorum.QLS.Royalties` | Royalty-specific QLS logic. |
| `QLS.Batch` | Batch process implementations (AFISCRTAE/CREATE_AE, SAPINTJE, PUBBA-side, bank submission, REPOSCRUB, imports). |
| `Quorum.QLS.Conversion` | Conversion/migration scripts — V7→V17, acquisitions, provision-model conversion, OpenText/Documentum link conversion (`CONVERT_IND`). The fix for most "did not convert / converted incorrectly" cases is a script here, not a product defect. |

### 3.2 QGIS / spatial

| Repo | Contents |
|---|---|
| `Quorum.QGIS.ArcGISPro.AddIn` | The ArcGIS Pro Add-In (Quorum GIS tab): Polygen UI, Agreement Linker, Mass Link, Working List, Log Explorer. Hotfix PRs use the **QGIS branch series** (§5.2). |
| `Quorum.QGIS.ArcGISPro.ServiceInterface` | Service layer between the Add-In and QLS/Oracle. |
| `Quorum.QGIS.ArcGISPro.Shared` | Shared polygen engine (`QPolyGeneratorBase`), used by the interactive Add-In and by headless `QPOLYGENCONSOLE.EXE` in the nightly batch. |

Nightly spatial batch is script-driven, not a repo build: `_SDE_Batch_Nightly.bat` + `Run_TM_Python.bat` running Transaction Models (Sync Attributes, Sync QLA Parcel Attributes, rollups, grid loads, `export_all` → SFTP). Fixes are sometimes distributed as an **updated Sync Attributes python file** rather than a build (ADO 1687847).

### 3.3 QLA web suite

| Repo | Contents |
|---|---|
| `Quorum.QLA.Web` / `QLA.App.Web` | QLAE (external/broker) and QLAI (internal) UI; admin console at `/Modules/Admin/admin.aspx` on the QLAI site. |
| `Quorum.QLA.Shared` | DAL — filter builder ("Invalid filter for an IN type query" lives here). |
| `Quorum.QLA.Batch` | Batch jobs plus **`BusinessRules.xml`** — the per-client validation rules (required documents, valid lessor usage types, tax-ID rules). Most QLA validation-error cases are resolved by editing the client's `BusinessRules.xml`, not code. |

QLA→QLS push logic is **PL/SQL in the `QLAI` schema**, not a repo: `QLA_INFC_QLS`, `QLA_INFC_QLS_CORE`, `QLA_INFC_PMT_CORE` (plus client variants such as `QLA_INFC_QLS_CRI`). Code-table sync runs `ESUITE_QAPA.QLA_CODE_TABLE_SYNC[_QAPA]`.

---

## 4. Client override repositories

**Naming:** `<CLIENT3>.QLS.Metadata` — one repo per client, holding that client's metadata/config layer.

**Confirmed set (12):** `AST`, `BPG`, `CHV`, `COP`, `DOM`, `ENR`, `LOD`, `MUR`, `NWD`, `SAV`, `SRC`, `XTO`.

- Config is checked in as JSON under a release folder, e.g. `QARCH_CNFG_CTRL.json` under `STANDARD 16.0/`.
- Related client repo pattern from the upstream set: `<CLIENT>.QLS.ESuite.Database` (see [REPO_REFERENCE_UPSTREAM.md](REPO_REFERENCE_UPSTREAM.md)).
- **Investigation rule:** before declaring a config value or screen behaviour a product default, check the client's `<CLIENT3>.QLS.Metadata` repo. Metadata resolves CORE → ENV → client (`APP_LAYER_CD`), and the GIS side adds `METADATA_PROFILE` (e.g. `QINT`). A missing client layer produces false NullReferenceException-style failures (Copy Agreement notes); a stale one produces post-upgrade dropdown/security drift.
- **Client-custom database code also exists** outside these repos: `ADAMPPFDEO` (client Positive Pay stored procedure), client triggers on `LIS.DEP_REL_WELL`, client registered SQL such as `GET_AGREEMENT_ATTRIBUTES` in `QARCH_SQL`, client code/decode tables such as `GOPL_JEFF_SECTIONS`.

---

## 5. Branch & hotfix conventions

Release train = **`YYYY.MM`**. ADO tags read `2022.04 / 2023.04 / 2024.04 / 2024.10 / 2025.04 / 2026.04 Hotfix` and `… Hotfix Completed`. Because trains are tagged, version-issue (G3) checks are viable directly from the work item.

### 5.1 `Quorum.QLS.Web` branch series — CONFIRMED

| Release train | Hotfix branch | Anchor |
|---|---|---|
| 2023.04 | `hotfix/17.23.35` | ADO **1772699** (SF 25-01060905), hotfix PRs #123531–123534 |
| 2024.04 | `hotfix/17.24.13` | ADO 1772699, same PR set |
| 2024.10 | `hotfix/17.25.9` | ADO 1772699, same PR set |
| 2025.04 | `hotfix/17.26.8` | ADO 1772699, same PR set |
| 2026.04 | `hotfix/17.27.3` | ADO **1836950**, `Quorum.QLS.Web` PR #129879 → hotfix PR #130391 |

### 5.2 `Quorum.QGIS.ArcGISPro.AddIn` branch series — INFERRED

| Release train | Hotfix branch |
|---|---|
| 2023.04 | `hotfix/17.1.26` |
| 2024.04 | `hotfix/17.2.10` |
| 2024.10 | `hotfix/17.3.6` |
| 2025.04 | `hotfix/17.4.5` |

Source: ADO **1777299** automation comment (source PR 123541 → hotfix PRs 123762–123765). **Do not cross-map** the two series — `17.2.10` in the QGIS repo is 2024.04, while `17.2x.y` in `Quorum.QLS.Web` is a different scheme entirely.

### 5.3 Confidence rules

- **CONFIRMED** = the work item carries the hotfix tag, or a hotfix PR to a branch above is linked on the item.
- **INFERRED** = derived from an automation comment, a release-train tag alone, or Salesforce `Resolution__c` text (e.g. "Sept '25 2023.04 HF", "2025.04 May 2026 HF", "2023.04 OCT '25 HF").
- Always re-baseline against the client's exact `hotfix/17.2x.y` build before promising "already fixed" or before writing line numbers into a handoff.

---

## 6. Oracle environments & schemas

**QLS runs on Oracle** — not SQL Server. This is the single most important platform fact when writing diagnostic SQL for this product.

### 6.1 Environment naming

| Pattern | Meaning |
|---|---|
| `<CLIENT>_LND_DEV17_ORACLE` / `<CLIENT>_LND_DEV17HD_ORACLE` | Client Land DEV17 Oracle database (HD variant = hosted-desktop tier) |
| `<CLIENT3>L_HD_DEV17_QLS` (e.g. `DMBL_HD_DEV17_QLS`) | Hosted-desktop QLS application URL / environment label — the repro environment named in escalations |
| `QINT_<CLIENT3>_DEV17QLS`, `QINT_<CLIENT3>_DEVA1QLS` | QFC/internal environment labels seen in security and config cases |
| `QCLD_<CLIENT3>_QLSA1_PRD` | QCloud production environment label |

### 6.2 Schemas

| Schema | Contents |
|---|---|
| **`lis`** (`LIS`) | QLS core: `ALL_AGREEMENTS`, `LEGAL_DESCRIPTION_SEGMENTS`, `DESG_PAYMENTS`, `STIPULATION_OBLIGATIONS`, `FINANCIAL_TRANS_HISTORIES`, `EVENTS`/`ALL_EVENTS`, `PARTICIPANTS`, `PARTICIPANT_ADDRESSES`, `AFIS_GL_CROSS_REF`, `SARCH_CTRL_DOC`, packages and triggers |
| `QLS_QFCONL` | QFC config/control for QLS: `QARCH_CNFG_CTRL`, `QARCH_CTRL_PROCESS[_TYPE]`, `QARCH_CTRL_SCHED`, `QARCH_CTRL_PROC_SCHED_PARAM`, `QARCH_CTRL_CONNECT_INFO`, `QARCH_SQL`, `QARCH_SEC_*`, `QARCH_CTRL_OBJECT_REPOSITORY` |
| `ESUITE_QFC` | eSuite-side QFC control — its own `QARCH_CTRL_CONNECT_INFO` and `QARCH_CTRL_OBJECT_REPOSITORY` (REPOSCRUB scrubs `QLS_QFCONL` only, which is why this one grows) |
| `QGIS` | Spatial feature classes in SDE: `ALL_LGL_SEG_PLY`, `ALL_AGREEMENTS_PLY`, `AGMT_OUTLINES`, `QLA_PLY`, plus `QGIS_LOG_ACTION`, `QGIS_BATCH_REQUEST_QUEUE` |
| `QGIS_ARCH` | Polygen configuration: `QARCH_GIS_POLYGEN` (PK includes `SURVEY_TYPE_CD` + `METADATA_PROFILE`) |
| `QLAI` / `QLAE` | QLA internal / external app schemas; interface packages `QLA_INFC_QLS`, `QLA_INFC_QLS_CORE`, `QLA_INFC_PMT_CORE` live in `QLAI` |
| `ESUITE_QAPA` | QLA code-table sync procedures (`QLA_CODE_TABLE_SYNC[_QAPA]`) |
| `SDE` | Esri geodatabase management (`SDE.COMPRESS_LOG` — stale compress causes minutes-long Legal Description saves) |

### 6.3 Metadata-connector note

The Quorum Metadata MCP `dbconfig.json` environments are the SQL-Server `<CLIENT3>U_HD_DEV17` upstream set. QLS work needs an **Oracle** binding (`<CLIENT>_LND_DEV17[HD]_ORACLE`); if no QLS Oracle environment is bound, the gates must emit verification SQL labeled `NOT YET RUN` rather than asserting data state. DEV-tier caveat applies as usual: schema/config findings are CONFIRMED anchors, client-PRD data-state claims stay INFERRED.

---

*Compiled 2026-09-03 by Auto-Bot from the QLS coverage-plan ADO survey and the repo/branch anchors cited across the 13 QLS skills.*

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
