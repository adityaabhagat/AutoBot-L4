# REPO REFERENCE — FLOWCAL family (ADO org `QuorumSoftware`)

> Source: coverage-plan ADO survey (2026-09-02) + mining wave 1. For the code-investigator (G5) and version-investigator (G3): where FLOWCAL/TESTit/PROVEit bugs land, which repos hold source, and how port bugs are titled.

## 1. Area paths (verified from real bugs)

| Project | Area Path | What lands there |
|---------|-----------|------------------|
| `Quorum` | `Quorum\North America\Measurement` | Triage-level FLOWCAL/TESTit/PROVEit bugs from support |
| `Quorum` | `Quorum\North America\Measurement\Maintenance` | FLOWCAL maintenance bugs (e.g. 1627121, 1710336) |
| `Quorum` | `Quorum\North America\Measurement\Field Apps and API` | TESTit/PROVEit ("Field Apps") + API bugs (e.g. 1807377 Prover coefficient) |
| `QuorumSoftware` | `QuorumSoftware\Engineering\Measurement\Maintenance` | Engineering-side bug copies/ports (e.g. 1808567 DEV, 1808568 R1090 PORT) |
| `myQuorum Cloud` | (various) | Hosting/provisioning/upgrade tickets — FLOWCloud group; work-item types "Incident/Problem/Request Global Cloud Ops" |

**SF↔ADO join key:** bugs frequently embed the source Salesforce case number in the description (`Case Owner - {name}` + `2x-00xxxxxx` pattern).

## 2. Port-bug convention (`R####`)

Measurement bugs are cloned per release branch with title suffixes: `(DEV)` for trunk, `(R1090 PORT)` for the 10.90 release branch, etc. (`R####` = version with the dot dropped: R1090 = 10.90). For "is it fixed in the client's version" (G3): find the port sibling matching the client's branch — the DEV item's state alone does not prove the client's build has the fix. Fix-version claims derived from port-bug states stay **INFERRED** unless confirmed by release notes.

## 3. Repo catalog (project `QuorumSoftware` unless noted)

| Repo pattern | What it is | Use for |
|---|---|---|
| `measurement-client` (~26 MB) | Likely the FLOWCAL desktop client monorepo; field-apps namespace `FlowCal.FieldApplications.*` (TESTit/PROVEit comms, OMNI) appears in bug stack traces. No repo literally named TESTit/PROVEit exists — confirm exact layout during a case. | G5 desktop-client root cause via `repo_file` |
| `FC.BoolTox` | Services admin tool (confirmed FlowCal.* C# namespaces); `ServicesRepository.cs` is the authoritative FcSrv* executable list | Service-name verification; C# tooling code |
| `FC.DevOps.*` | FlowCal DevOps tooling | Ops context |
| `fc-migration` | DB upgrade scripts: `SQL Scripts\SQLScripts\FLOWCAL Incremental\FLOWCAL 10\__updateDB_<from>_to_<to>.sql` (+ `-archival.sql` variants), e.g. `__updateDB_10.6.0.17_to_10.7.0.0.sql` (FcTextFileExchange→GasTextFileExchange rename) | Upgrade-failure cases (Install skill §3.1); schema-change archaeology |
| `evs-measurement-*` (`-volume-calculation`, `-balancing`, `-summarization`, `-closing`, `-uom`, `-api`) | Next-gen measurement microservices (evs migration; CalcMethod/FpvMethod enums per ADO 1805151) | Next-gen calc parity questions |
| `domain-measurement-api`, `domain-measurement-xchange-api` | Integration/API layer | Integrations & WebSync group (#11) |
| `Quorum.Measurement.Wiki` | Dev wiki (Desktop-Application/Technical-Architecture.md, Testing guides) | High-value KB seed; architecture answers |
| `Measurement-PS-Scripts`, `FieldOps.Scada.Import2.0`, `Flowcal.Automation.Azure.Deployment` | Ops/import tooling | Import-transport & deployment cases |
| `MFC.*` (`MFC.QGM.*`, `MFC.QCM.*`, `MFC.QEMS.*`, `MFC.ESuite.*`) | myQuorum measurement metadata/reports/database repos | eSuite integration (group #11) |
| github `flowcal/R8` (external) | Legacy C++ source refs seen in mining (`oMetAnlRec.CPP`, `CQMeterAnalysis.cpp`) | Legacy calc-engine citations |

## 4. Code-search caveat

ADO code search over `FlowCal.FieldApplications` mostly surfaces `Quorum.Measurement.Wiki` + `FC.BoolTox`; the core desktop source (C++: `CC32C250MT.DLL` runtime hints at C++ Builder) may not be code-search indexed. **Primary ADO evidence channel: wiki + work-item mining (`search_workitem`, `wit_query`); secondary: `repo_file` on `measurement-client` / `evs-measurement-*` / `fc-migration`.**

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
