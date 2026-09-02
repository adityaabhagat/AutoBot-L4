# Repository Reference — TIPS (QuorumSoftware)

TIPS repos follow the pattern `<PREFIX>.TIPS.<Layer>`. `Quorum.TIPS.*` = base/standard product. A 3-letter client code prefix (e.g. `DTE.TIPS.*`, `EQT.TIPS.*`) = that client's overrides. **Always check the client repo for an override before assuming base behavior.**

---

## Base / Core (Quorum.TIPS.*) — Gas line

| Repo | Repo ID | Purpose |
|------|---------|---------|
| **Quorum.TIPS.Web** | `483b5c74-5f90-44f4-af05-90f19ff85cd6` | Core web app — ServiceCore, Validation, DataCache, Web.Controllers, EDI |
| **Quorum.TIPS.Batch** | `7c3b1176-1efc-415e-8e68-eecc1565809c` | Batch processing (allocations, statements, EDI jobs) |
| **Quorum.TIPS.ClassicBatch** | `5b7becfb-1d08-4652-956c-ab992b1d762d` | Classic (C++) batch processing |
| **Quorum.TIPS.ClassicGUI** | `a14a0b96-2ca7-41a6-9a68-efc7ee137e0c` | Classic Windows GUI (QPEC) |
| **Quorum.TIPS.Database** | `8698b842-f18c-4c55-a668-32c0b488ba53` | DB schema, packages, migrations |
| **Quorum.TIPS.Metadata** | `b8fb8339-7ecb-4343-8387-8a16559079e8` | Screen/grid/picklist metadata (QARCH-style) |
| **Quorum.TIPS.Reports** | `73bc21b2-4c72-4c83-bd0f-732c02bdcf23` | Reports (statements, settlements, tickets) |
| **Quorum.TIPS.API** | `4c2b7db7-1734-46cd-b6aa-8f44281c5bec` | REST API |
| **Quorum.TIPS.API.Specs** | `d2956be8-58e0-4e2a-803e-9dd6419a050b` | API specifications |
| **Quorum.TIPS.Events** | `f567402f-3834-4b58-b7e9-d2c7e46b8889` | Event/messaging definitions |
| **Quorum.TIPS.Messaging.Publisher** | `f6e81cc2-401e-40dd-bc9f-3ef09617ed94` | Outbound messaging publisher |
| **Quorum.TIPS.AT** | `711b30e7-b9ba-4f70-8413-27c65f7a5616` | Automated tests |
| **Quorum.TIPS.ReleaseNotes** | `24e5841f-4464-4add-b22c-bebe047b3925` | Release notes (use for version/fix availability) |
| **Quorum.TIPS.Help** | `cc34f6d1-e4db-4421-95d5-87e4c28a4848` | In-app help content |

### Application layer (Quorum.TIPS.Application.*)
| Repo | Repo ID |
|------|---------|
| Quorum.TIPS.Application.MiddleTier | `a472c534-c5b0-4c73-bf45-48d4d41d2bb7` |
| Quorum.TIPS.Application.QPEC | `e4b08de3-b0c5-403e-a29c-d64799415159` |
| Quorum.TIPS.Application.Web | `b18aa6fc-56d6-4dd0-af94-e59432b3939a` |
| Quorum.TIPS.Application.ClassicGUI | `b36bd94d-61c5-473d-8e0d-7ffbdea046ed` |
| Quorum.TIPS.Application.APIHost | `4947205e-9300-440e-8ff6-f246cefb4d3d` |

---

## Crude line (Quorum.TIPS.Crude.* / CrudeCommon.*)

Use these when the case is about **truck/marine/pipeline/batch tickets, terminals, crude, water**.

| Repo | Repo ID |
|------|---------|
| Quorum.TIPS.Crude.Web | `d9519a53-2fb9-407e-9420-68a8c04aeab2` |
| Quorum.TIPS.Crude.Batch | `dab3ce23-ebe8-4ef3-a4de-89e531c1fea1` |
| Quorum.TIPS.Crude.Scheduling | `64ee648e-ac87-4dba-9ecb-50fac121d2f2` |
| Quorum.TIPS.Crude.Metadata | `f3d79cb9-9e71-4622-9835-d4bb26d8f5ef` |
| Quorum.TIPS.Crude.Application.Web | `269e3bfe-625b-4de2-b91a-38b557a5b80d` |
| Quorum.TIPS.Crude.Application.MiddleTier | `b75f11ac-9d40-4c91-83f5-6595f0be0906` |
| Quorum.TIPS.Crude.Application.QPEC | `7e97cca6-a3ea-4246-bf10-ff49f9f3dd1a` |
| Quorum.TIPS.Crude.ClassicBatch | `4026363e-3caa-4843-84d5-a5cb2b422d58` |
| Quorum.TIPS.CrudeCommon.Web | `e57e9035-d707-420a-bb47-c4daef53afda` |
| Quorum.TIPS.CrudeCommon.Batch | `c4f6e16d-0e9c-4155-931c-26b7233402e2` |

## TurboTips (analytics/processing engine)
| Repo | Repo ID |
|------|---------|
| Quorum.Tips.TurboTips | `f8bf2c24-dd92-4820-88cc-479503d654de` |
| Quorum.TIPS.TurboTips.Tests | `f81e5ab0-b165-485e-b271-18ce1c521541` |

---

## Quorum.TIPS.Web — internal project layout

```
Quorum.TIPS.Web/
├── Quorum.TIPS.ServiceCore/              ← Main business services
├── Quorum.TIPS.ServiceCore.EDI/          ← EDI inbound/outbound services
├── Quorum.TIPS.ServiceInterface/         ← Service contracts
├── Quorum.TIPS.ServiceClient/            ← Service client proxies
├── Quorum.TIPS.Validation/               ← Validation rules engine
├── Quorum.TIPS.DataCache/                ← Cached/derived config (defs, rates)
├── Quorum.TIPS.DataAccess / .DAL / .DataObject  ← Data access layers
├── Quorum.TIPS.Web.Controllers/          ← UI controllers (screen logic)
├── Quorum.TIPS.Web.Core / .Web/          ← Web host
├── Quorum.TIPS.Config / .Constants / .CoreInterface
├── Quorum.TIPS.Events/                   ← Domain events
├── Quorum.TIPS.SAP.*                     ← SAP integration (service, proxies, web services)
├── Quorum.TIPS.Canada.*                  ← Canada-specific logic (DAL, ServiceCore, Validation)
└── Quorum.TIPS.DQS.DataSource / .QueryView  ← Data Query System (report/query views)
```

---

## Client-Specific Repos

Each client prefix has its own subset of `<CLIENT>.TIPS.*` repos (commonly `Database`, `Metadata`, `Reports`; larger clients also have `Application.Web/QPEC/MiddleTier`, `Batch`, `ClassicBatch`, `Web`).

**Client prefixes seen in repos** (3-letter codes): ACL, ACP, AER, AHS, ALT, AMM, ARM, AZR, BLU, BMD, BMH, BPM, CCI, CHD, CMH, CMP, CRS, DCP, DLP, DTE, DTM, ECM, EDA, EDB, EDC, EDO, EIG, EMP, ENT, EQC, EQT, ETP, FOR, FPL, FRC, GLE, GNM, HEC, HEP, HPE, HVK, HVM, IAC, IME, IPF, KEY, LMD, LVM, MER, MGP, MKW, MOM, NEM, NRM, ONM, OXY, PEM, PEP, PMB, PML, PNR, SCT, SCX, SEM, SPR, SRB, SRC, SRI, TCP, UGI, UTG, VMH, WPC, WTG, XMG. Plus performance clones prefixed `PRF_*` (e.g. `PRF_DCP_PRF.TIPS.*`).

**Account → client-code hints** (confirm per case; not exhaustive):
DTE Gas → `DTE` · EQT → `EQT` · Energy Transfer → `ETP` · MarkWest → `MKW` · AltaGas → `ALT` · NorthRiver Midstream → `NRM` · Steel Reef → `SRB` · IACX/Cimarron → `IAC` · Azure Midstream → `AZR` · Marathon → `MER` · Seneca → `SEM` · Tallgrass → `TCP` · DCP → `DCP`.

### Resolve a client repo id
```bash
curl -s -u ":$PAT" "https://dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/git/repositories?api-version=7.0" \
  | python -c "import sys,json; [print(f\"{r['id']}  {r['name']}\") for r in json.load(sys.stdin)['value'] if r['name'].upper().startswith('DTE.TIPS')]"
```

### Check for a client override before blaming base code
```bash
# If count == 0 → client uses base Quorum.TIPS behavior; if > 0 → client has an override
curl -s -u ":$PAT" "https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults?api-version=7.0" \
  -H "Content-Type: application/json" \
  -d '{"searchText": "GasStatementService repo:DTE.TIPS", "$top": 10}'
```

---

## Finding the right repo — decision flow

1. **Gas or Crude?** Truck/marine/batch tickets, terminals, crude, water → `*.TIPS.Crude.*`. Else gas line.
2. **Base or client?** Identify the client code from the SF Account. Search the client repo first.
3. **Which layer?**
   - Allocation / statements / settlements / business logic → `ServiceCore` (in `*.TIPS.Web`) or `*.TIPS.Batch`
   - Validation error / "cannot save" → `Quorum.TIPS.Validation` (+ client `Validation`)
   - Screen / grid / UI behavior → `Quorum.TIPS.Web.Controllers` + `*.TIPS.Metadata`
   - Report content / column / format → `*.TIPS.Reports` or `Quorum.TIPS.DQS.*`
   - EDI message in/out → `Quorum.TIPS.ServiceCore.EDI`
   - SAP interface → `Quorum.TIPS.SAP.*`
   - Schema / package / data-fix SQL → `*.TIPS.Database`
   - Version / fix shipped? → `Quorum.TIPS.ReleaseNotes`

## List all TIPS repos
```bash
curl -s -u ":$PAT" "https://dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/git/repositories?api-version=7.0" \
  | python -c "import sys,json; [print(f\"{r['id']}  {r['name']}\") for r in sorted(json.load(sys.stdin)['value'], key=lambda x:x['name']) if 'TIPS' in r['name'].upper()]"
```
