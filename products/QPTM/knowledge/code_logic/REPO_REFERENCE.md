# Repository Reference — QuorumSoftware

## How to Find a Repo

### By Product Module
When investigating an issue, use this mapping to find the right repos:

---

## QPTM Repositories

### Base / Core (Quorum.QPTM.*)
| Repo Name | Repo ID | Purpose |
|-----------|---------|---------|
| **Quorum.QPTM.Web** | `41e317c0-844c-4728-98da-529092957738` | Core web app — Services, Validation Rules, Controllers, DataCache |
| **Quorum.QPTM.Batch** | `e024d80b-5c45-411c-93e1-78e2798ed885` | Batch processing — EDI inbound/outbound, batch jobs |
| **Quorum.QPTM.ClassicBatch** | `0587e2fb-0f37-4614-991b-1d4072eb0255` | Classic (C++) batch processing |
| **Quorum.QPTM.ClassicGUI** | (search needed) | Classic Windows GUI |
| **Quorum.QPTM.AT** | `cf9d975f-c0b4-4e08-ab4c-6d0537b3d8d9` | Automated tests |
| **Quorum.QPTM.Metadata** | (search needed) | Metadata JSON files (QARCH tables) |

### Application Layer (APL.QPTM.*)
| Repo Name | Repo ID | Purpose |
|-----------|---------|---------|
| **APL.QPTM.Application.Web** | `2ddf8637-1641-43e6-a72d-fe2f597058ad` | Application web layer |
| **APL.QPTM.Application.MiddleTier** | `d45a6e0f-5c7d-4a18-bc42-47f8728fc445` | Middle tier services |
| **APL.QPTM.Application.QPEC** | `d8402baa-bb33-44cb-950d-3cef9e0da1b9` | QPEC application |
| **APL.QPTM.Batch** | `98d13405-7cea-4fe8-9d6e-8f684f59dee9` | APL batch processing |
| **APL.QPTM.Database** | `2e1fb9e5-a46a-4257-b99a-fd47721dd399` | Database schema & migrations |
| **APL.QPTM.Metadata** | `30db596b-2d1e-469a-b3a0-6ef2db3f8bee` | Metadata definitions |
| **APL.QPTM.Web** | `ffa5745e-d1c5-410c-bb42-75b1efa87a58` | APL web layer |

### EDI / Framework
| Repo Name | Repo ID | Purpose |
|-----------|---------|---------|
| **Quorum.EDI.Framework** | `02742829-b8c5-4531-bb27-163f9a501621` | Core EDI framework, base classes |
| **Quorum.EDIServ** | `30cdad90-e4ae-405c-8d67-747955bcf870` | EDI transport service (InboundServer/OutboundServer) |

### Database
| Repo Name | Repo ID | Purpose |
|-----------|---------|---------|
| **Quorum.QGM.Database** | `8bfba59c-f3dd-46ea-8d0a-f2687a763258` | QGM database — QCODE tables, EDI error codes |
| **Quorum.QGM.Batch** | `f6a6c380-ed74-4860-835b-d58c462c3e9f` | QGM batch — NAESB message definitions |

---

## Client-Specific QPTM Repos

Each client has their own set of repos that may override base behavior:

### Pattern: `<CLIENT>.QPTM.*`

| Client Code | Full Name | Web Repo ID |
|-------------|-----------|-------------|
| **EQT** | EQT Corporation | `f29cf1be-dcaa-45ec-b721-dc4a5f06bfa8` |
| **DUT** | (Duke/DUT) | (search needed) |
| **QTR** | (QTR) | (search needed) |
| **NMGC** | New Mexico Gas Co | (search needed) |
| **NMG** | (NMG) | (search needed) |
| **DOH** | (DOH) | (search needed) |
| **ENT** | (Enterprise) | (search needed) |
| **DRS** | (DRS) | (search needed) |
| **ONG** | (ONEOK) | (search needed) |
| **ONK** | (ONEOK) | (search needed) |

### Client Repo Structure
```
<CLIENT>.QPTM.Web           — Custom validation rules, services, controllers
<CLIENT>.QPTM.Database       — Custom DB scripts
<CLIENT>.QPTM.Metadata       — Custom metadata/config overrides
<CLIENT>.QPTM.Application.*  — Custom app layer code
<CLIENT>.QPTM.Batch          — Custom batch processing (rare)
<CLIENT>.QPTM.ClassicBatch   — Custom classic batch
<CLIENT>.QPTM.Reports        — Custom reports
```

### Finding Client-Specific Overrides
```bash
# Check if client has a custom validation rule:
curl -s -u ":$PAT" "https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults?api-version=7.0" \
  -H "Content-Type: application/json" \
  -d '{"searchText": "class RuleNN00009011 repo:<CLIENT>.QPTM", "$top": 10}'

# If count = 0 → client uses base Quorum.QPTM rules
# If count > 0 → client has custom override
```

---

## TIPS Repositories

### Base / Core (Quorum.TIPS.*)
| Repo Name | Purpose |
|-----------|---------|
| Quorum.TIPS.Crude.Web | Crude TIPS web services |
| Quorum.TIPS.Crude.Batch | Crude TIPS batch processing |

### Client-Specific (ACL.TIPS.*, ACP.TIPS.*, etc.)
Same pattern as QPTM — each client prefix has its own TIPS repos.

---

## Key File Locations by Module

### Nomination Submission
```
Quorum.QPTM.Web/
├── Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService.cs  ← Main nomination service
├── Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerNominationSubmissionBase.cs
├── Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/     ← Business validation rules
├── Quorum.QPTM.Validations/                                     ← Validation engine base
├── Quorum.QPTM.DataCache/CycleManager.cs                        ← Cycle deadline evaluation
└── Quorum.QPTM.ServiceInterface/Interfaces/IQPTMNominationService.cs
```

### EDI Processing
```
Quorum.QPTM.Batch/
├── Quorum.QPTM.EDI.DataSets/G873NMST/QEdiNMSTIn18.cs  ← Inbound NMST parser
├── Quorum.QPTM.EDI.DataSets/G874NMQR/                  ← Outbound NMQR writer
├── Quorum.QPTM.EDI.Framework/                           ← EDI framework for QPTM
└── Quorum.QPTM.EDI.DataSets/                            ← All EDI dataset implementations

Quorum.EDI.Framework/
├── Quorum.EDI.Framework/EdiBase/EdiGlobals.cs            ← NAESB constants
├── Quorum.EDI.Framework/EdiBase/EdiUtility.cs            ← EDI utilities
└── Quorum.EDI.Framework/Dataset/AEdiInboundDataset.cs    ← Base inbound class

Quorum.EDIServ/
├── Quorum.EDIServ/InboundServer.cs                       ← HTTP inbound handler
└── Quorum.EDIServ/OutboundServer.cs                      ← HTTP outbound handler
```

### Scheduling & Confirmation
```
Quorum.QPTM.Web/
├── Quorum.QPTM.ServiceCore/QPTMServiceCore.cs            ← Scheduling service
├── Quorum.QPTM.ServiceCore.Confirmation/                 ← Confirmation service
└── Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerConfirmationSummary.cs
```

### Error Codes & Metadata
```
Quorum.QGM.Database/Common/Oracle/EDI Base Data Setup/CodeTables/QCODE_ED_ERROR.sql
Quorum.QPTM.Metadata/STANDARD 16.0/QARCH_CODE_MSG_TITLE.json
Quorum.QPTM.Metadata/STANDARD 16.0/QARCH_EVENT_TYPE.json
Quorum.QGM.Batch/Quorum.QEMS.EDI.DataSets/G874NMQR/NAESB_1_8_NMQR_Msgs.txt
```

---

## Searching for a Repo by Name

```bash
# List ALL repos in QuorumSoftware project:
curl -s -u ":$PAT" \
  "https://dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/git/repositories?api-version=7.0" \
  | python -c "import sys,json; [print(f\"{r['id']}  {r['name']}\") for r in sorted(json.load(sys.stdin)['value'], key=lambda x: x['name'])]"

# Filter by name pattern:
... | grep -i "EQT\|QPTM\|EDI"
```
