# Azure DevOps Repository Inventory — Quorum (QPTM & TIPS focus)

> Generated 2026-06-13 for L4 support. Complete enumeration of all Git repositories across the three accessible ADO projects.
> Credentials are NOT included here — see `CONNECTION_CONFIG.md` for the PAT.

## Summary Counts

| Project | Repositories |
|---------|-------------:|
| QuorumSoftware (main) | 3,342 |
| QuorumServices | 33 |
| myQuorum Cloud | 4 |
| **Total** | **3,379** |

### Breakdown of QuorumSoftware repos by category

| Category | Count |
|----------|------:|
| QPTM base (`Quorum.QPTM.*`, `APL.QPTM.*`) | 35 |
| TIPS base (`Quorum.TIPS.*`) | 38 |
| TIPS client-prefixed (`<CLIENT>.TIPS.*`) | 412 |
| EDI / framework (shared) | 6 |
| Core gas DB backbone (`Quorum.QGM.*`, `Quorum.QEMS.*`) | 32 |
| Client-prefixed gas (`<CLIENT>.QPTM/QGM/QEMS.*`) | 368 |
| Distinct client codes (QPTM/TIPS/QGM/QEMS) | 124 |
| Other repos (other products / infra — not enumerated below) | 2451 |

---

## 1. QPTM Base (`Quorum.QPTM.*`, `APL.QPTM.*`)

35 repositories.

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| APL.QPTM.Application.ClassicGUI | `61459842-3a16-4f44-9fc6-7c806e3dc509` | 50.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Application.ClassicGUI |
| APL.QPTM.Application.ClassicGUICAW | `9858c3ff-8b13-4f39-ac04-ebc31ce38aa3` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Application.ClassicGUICAW |
| APL.QPTM.Application.MiddleTier | `d45a6e0f-5c7d-4a18-bc42-47f8728fc445` | 666 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Application.MiddleTier |
| APL.QPTM.Application.QPEC | `d8402baa-bb33-44cb-950d-3cef9e0da1b9` | 689 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Application.QPEC |
| APL.QPTM.Application.Web | `2ddf8637-1641-43e6-a72d-fe2f597058ad` | 42.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Application.Web |
| APL.QPTM.Batch | `98d13405-7cea-4fe8-9d6e-8f684f59dee9` | 36 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Batch |
| APL.QPTM.ClassicBatch | `420797cd-833f-4846-b29f-540cece36ad1` | 126 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.ClassicBatch |
| APL.QPTM.ClassicGUI | `5da2b9cd-4504-45f3-a8f7-b74689519a57` | 705 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.ClassicGUI |
| APL.QPTM.Database | `2e1fb9e5-a46a-4257-b99a-fd47721dd399` | 96 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Database |
| APL.QPTM.Metadata | `30db596b-2d1e-469a-b3a0-6ef2db3f8bee` | 47.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Metadata |
| APL.QPTM.Reports | `bc15dff3-38cb-44ae-ae2e-ebcaa0e1842f` | 19.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Reports |
| APL.QPTM.Web | `ffa5745e-d1c5-410c-bb42-75b1efa87a58` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/APL.QPTM.Web |
| Quorum.QPTM.API | `bc4a8a91-803f-4280-84fa-f0c3f884d1e9` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.API |
| Quorum.QPTM.API.Specs | `cefe7237-9a66-41e9-8d25-bf9b61beba3e` | 3.6 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.API.Specs |
| Quorum.QPTM.Application.APIHost | `c61c2fa0-7446-4d46-80c6-9e805980824e` | 5.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Application.APIHost |
| Quorum.QPTM.Application.ClassicGUI | `b651f0cf-1d15-4bbb-a941-548fdee0a0cd` | 55.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Application.ClassicGUI |
| Quorum.QPTM.Application.ClassicGUICAW | `ac553ace-40b0-455f-b833-3a7f8cd9ed60` | 4.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Application.ClassicGUICAW |
| Quorum.QPTM.Application.MiddleTier | `247f86d5-4704-4919-816b-119cdd4eea4d` | 4.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Application.MiddleTier |
| Quorum.QPTM.Application.QPEC | `34a2b9f6-344f-4419-b988-421cc0d3412c` | 7.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Application.QPEC |
| Quorum.QPTM.Application.Web | `9b4768dd-df6a-4990-a82c-197951aa49b0` | 97.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Application.Web |
| Quorum.QPTM.AT | `cf9d975f-c0b4-4e08-ab4c-6d0537b3d8d9` | 22.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.AT |
| Quorum.QPTM.Batch | `e024d80b-5c45-411c-93e1-78e2798ed885` | 9.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Batch |
| Quorum.QPTM.ClassicBatch | `0587e2fb-0f37-4614-991b-1d4072eb0255` | 14.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.ClassicBatch |
| Quorum.QPTM.ClassicGUI | `e6d98ba8-ff7f-441c-bdbb-3c9a4605d5a9` | 6.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.ClassicGUI |
| Quorum.QPTM.Database | `8480c004-5b4f-4d7c-b94f-37af8cfd4aa5` | 13.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Database |
| Quorum.QPTM.DesignStudio.PackageSource | `99723dbc-58ee-4e1b-943d-07303f3426f8` | 923 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.DesignStudio.PackageSource |
| Quorum.QPTM.Help | `22910aa4-ebdd-411a-9b37-7cc8baf9616e` | 39.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Help |
| Quorum.QPTM.LDC.Batch | `3e5446c0-d0da-4438-ba4f-383b3cd73910` | 785 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.LDC.Batch |
| Quorum.QPTM.LDC.Database (deprecated) | `4ed127c5-d86f-43c5-94ab-80bf80f2bbc8` | 50 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.LDC.Database%20%28deprecated%29 |
| Quorum.QPTM.LDC.Metadata (deprecated) | `70fe9879-3db0-4067-b718-d49a7b3afb26` | 17.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.LDC.Metadata%20%28deprecated%29 |
| Quorum.QPTM.LDC.Web | `5a2bf830-4dc2-4170-a5a8-73746c659aa4` | 16.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.LDC.Web |
| Quorum.QPTM.Metadata | `1ae5387f-7703-4db6-9f27-7e5f5202ca6e` | 1390.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Metadata |
| Quorum.QPTM.ReleaseNotes | `a19ddb5a-9e9f-4f1e-b766-8c57204e7d7e` | 2.8 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.ReleaseNotes |
| Quorum.QPTM.Reports | `a2244083-73c8-4399-8292-d7cf0d888602` | 50.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Reports |
| Quorum.QPTM.Web | `41e317c0-844c-4728-98da-529092957738` | 203.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QPTM.Web |

## 2. TIPS

### 2a. TIPS Base / Core (`Quorum.TIPS.*`) — 38 repos

Includes Crude (`Quorum.TIPS.Crude.*`), CrudeCommon, API, and shared TIPS layers.

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| Quorum.PerformanceTesting.TIPS | `84006201-1e77-4035-be07-a85cfa0790df` | 1.7 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.PerformanceTesting.TIPS |
| Quorum.TIPS.API | `4c2b7db7-1734-46cd-b6aa-8f44281c5bec` | 2.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.API |
| Quorum.TIPS.API.Specs | `d2956be8-58e0-4e2a-803e-9dd6419a050b` | 2.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.API.Specs |
| Quorum.TIPS.Application.APIHost | `4947205e-9300-440e-8ff6-f246cefb4d3d` | 559 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.APIHost |
| Quorum.TIPS.Application.ClassicGUI | `b36bd94d-61c5-473d-8e0d-7ffbdea046ed` | 4.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.ClassicGUI |
| Quorum.TIPS.Application.ClassicGUICAW | `24e654d2-960c-4185-b473-5a4bfe1aac34` | 4.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.ClassicGUICAW |
| Quorum.TIPS.Application.MiddleTier | `a472c534-c5b0-4c73-bf45-48d4d41d2bb7` | 3.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.MiddleTier |
| Quorum.TIPS.Application.QPEC | `e4b08de3-b0c5-403e-a29c-d64799415159` | 8.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.QPEC |
| Quorum.TIPS.Application.Web | `b18aa6fc-56d6-4dd0-af94-e59432b3939a` | 84.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.Web |
| Quorum.TIPS.Application.WebCrude | `1eeae5db-dc88-4472-a784-423aebf571b1` | 59.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Application.WebCrude |
| Quorum.TIPS.AT | `711b30e7-b9ba-4f70-8413-27c65f7a5616` | 6.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.AT |
| Quorum.TIPS.Batch | `7c3b1176-1efc-415e-8e68-eecc1565809c` | 18.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Batch |
| Quorum.TIPS.ClassicBatch | `5b7becfb-1d08-4652-956c-ab992b1d762d` | 24.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.ClassicBatch |
| Quorum.TIPS.ClassicGUI | `a14a0b96-2ca7-41a6-9a68-efc7ee137e0c` | 6.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.ClassicGUI |
| Quorum.TIPS.Crude.API | `0fb22927-7e2f-4a32-9a72-7f176d2daab7` | 272 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.API |
| Quorum.TIPS.Crude.API.Specs | `f95360c3-6866-46e0-bea6-74997f5f0495` | 2.5 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.API.Specs |
| Quorum.TIPS.Crude.Application.MiddleTier | `b75f11ac-9d40-4c91-83f5-6595f0be0906` | 154 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Application.MiddleTier |
| Quorum.TIPS.Crude.Application.QPEC | `7e97cca6-a3ea-4246-bf10-ff49f9f3dd1a` | 134 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Application.QPEC |
| Quorum.TIPS.Crude.Application.Web | `269e3bfe-625b-4de2-b91a-38b557a5b80d` | 15.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Application.Web |
| Quorum.TIPS.Crude.Batch | `dab3ce23-ebe8-4ef3-a4de-89e531c1fea1` | 929 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Batch |
| Quorum.TIPS.Crude.ClassicBatch | `4026363e-3caa-4843-84d5-a5cb2b422d58` | 66 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.ClassicBatch |
| Quorum.TIPS.Crude.DesignStudio.PackageSource | `99671398-7c37-4292-847e-b71181c7d9f6` | 23 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.DesignStudio.PackageSource |
| Quorum.TIPS.Crude.Metadata | `f3d79cb9-9e71-4622-9835-d4bb26d8f5ef` | 7 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Metadata |
| Quorum.TIPS.Crude.Scheduling | `64ee648e-ac87-4dba-9ecb-50fac121d2f2` | 5.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Scheduling |
| Quorum.TIPS.Crude.Web | `d9519a53-2fb9-407e-9420-68a8c04aeab2` | 7.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Crude.Web |
| Quorum.TIPS.CrudeCommon.Batch | `c4f6e16d-0e9c-4155-931c-26b7233402e2` | 566 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.CrudeCommon.Batch |
| Quorum.TIPS.CrudeCommon.ClassicBatch | `3d9f1476-2b74-4fb6-86d1-cab7b373b3ff` | 967 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.CrudeCommon.ClassicBatch |
| Quorum.TIPS.CrudeCommon.Web | `e57e9035-d707-420a-bb47-c4daef53afda` | 2.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.CrudeCommon.Web |
| Quorum.TIPS.Database | `8698b842-f18c-4c55-a668-32c0b488ba53` | 43.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Database |
| Quorum.TIPS.DesignStudio.PackageSource | `b9204654-4176-43b9-9521-873b307b42f3` | 191 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.DesignStudio.PackageSource |
| Quorum.TIPS.Events | `f567402f-3834-4b58-b7e9-d2c7e46b8889` | 40 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Events |
| Quorum.TIPS.Help | `cc34f6d1-e4db-4421-95d5-87e4c28a4848` | 32.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Help |
| Quorum.TIPS.Messaging.Publisher | `f6e81cc2-401e-40dd-bc9f-3ef09617ed94` | 91 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Messaging.Publisher |
| Quorum.TIPS.Metadata | `b8fb8339-7ecb-4343-8387-8a16559079e8` | 3012.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Metadata |
| Quorum.TIPS.ReleaseNotes | `24e5841f-4464-4add-b22c-bebe047b3925` | 2.4 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.ReleaseNotes |
| Quorum.TIPS.Reports | `73bc21b2-4c72-4c83-bd0f-732c02bdcf23` | 195.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Reports |
| Quorum.TIPS.TurboTips.Tests | `f81e5ab0-b165-485e-b271-18ce1c521541` | 7799.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.TurboTips.Tests |
| Quorum.TIPS.Web | `483b5c74-5f90-44f4-af05-90f19ff85cd6` | 114.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.TIPS.Web |

### 2b. TIPS Client-Prefixed (`<CLIENT>.TIPS.*`) — 412 repos

Includes IPF, ACL, ACP (incl. `ACP.TIPS.Crude.*`), and all other client TIPS instances. 
Listed by client code in **Section 5** (per-client tables). Flat list below.

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ACL.TIPS.Application.QPEC | `417cbfe3-764c-432a-9dc6-9caf5e6a0f75` | 5.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Application.QPEC |
| ACL.TIPS.ClassicBatch | `e5d984fe-2615-4c85-98bd-fdbb3d7aa1ad` | 125 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.ClassicBatch |
| ACL.TIPS.Database | `0f691c97-901e-49bb-b95e-f9106e6d9d04` | 174 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Database |
| ACL.TIPS.Metadata | `7acd0c60-5a5e-47a3-a2a4-763b66ab2e77` | 326 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Metadata |
| ACL.TIPS.Reports | `5f34d474-cd8c-4bc1-b172-2eaf33c8da02` | 46.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Reports |
| ACP.TIPS.Application.QPEC | `668797dd-6950-4134-8c29-044295efc4b2` | 694 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Application.QPEC |
| ACP.TIPS.Batch | `76dc3d78-d26a-4371-94f5-0ad1d4d66dc8` | 254 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Batch |
| ACP.TIPS.ClassicBatch | `c02ce310-4ef9-4d73-99eb-e4c50d96fab6` | 22 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.ClassicBatch |
| ACP.TIPS.ClassicGUI | `7ca39d2d-b924-439d-865c-0afe28a66348` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.ClassicGUI |
| ACP.TIPS.Crude.Application.MiddleTier | `0e5b1988-d490-4fef-a63c-66359e7b6056` | 196 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Crude.Application.MiddleTier |
| ACP.TIPS.Crude.Application.QPEC | `d5956f5d-1dfb-43b0-9a9c-a964d72fee33` | 243 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Crude.Application.QPEC |
| ACP.TIPS.Crude.Application.Web | `16f02a10-bf3e-469e-9edf-96f096e42332` | 16.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Crude.Application.Web |
| ACP.TIPS.CrudeCommon.Batch | `411cfa37-dc69-404a-a486-3d31b3f11795` | 12 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.CrudeCommon.Batch |
| ACP.TIPS.CrudeCommon.Web | `5234271a-61dd-482a-a1e7-18f4e5284674` | 224 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.CrudeCommon.Web |
| ACP.TIPS.Database | `4fb64249-0e05-4e90-9291-a91eb4e8604d` | 42 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Database |
| ACP.TIPS.Metadata | `55135c2a-8bee-4ae4-8056-56f66d0939b7` | 8.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Metadata |
| ACP.TIPS.Reports | `bf8d59bc-8536-4d1c-9d17-f25fbda20ec5` | 14.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Reports |
| ACP.TIPS.Web | `86f2c59b-1931-4e57-9159-974400d912a4` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Web |
| AER.TIPS.Database | `2fc36149-7342-4905-b8ee-c57be20fd5c6` | 1.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AER.TIPS.Database |
| AER.TIPS.Metadata | `b7b8638b-73f2-4c09-9355-e2cfa48cb43f` | 6.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AER.TIPS.Metadata |
| AER.TIPS.Reports | `ca7b5ed9-a8ba-4284-a150-bef2a4dcba64` | 11.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AER.TIPS.Reports |
| AHS.TIPS.Application.QPEC | `60064159-0b03-4fb2-8863-191bf4742975` | 360 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Application.QPEC |
| AHS.TIPS.ClassicBatch | `978987e2-8aaf-4d57-9f53-4b36143d8d4a` | 286 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.ClassicBatch |
| AHS.TIPS.Database | `cee5c476-5feb-4a99-b132-5016b56cc13d` | 443 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Database |
| AHS.TIPS.Metadata | `7c4a5aad-a2c7-4c67-9c64-40b990667da3` | 17.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Metadata |
| AHS.TIPS.Reports | `9e642263-7272-4021-8d10-f482d3e2b890` | 46.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Reports |
| ALT.TIPS.Application.QPEC | `bacf6af7-2535-4f3a-bdac-6d9fd85ae259` | 4.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Application.QPEC |
| ALT.TIPS.ClassicBatch | `492948c4-7518-4f40-8a2b-09ea86a991c5` | 740 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.ClassicBatch |
| ALT.TIPS.Database | `0fd00a69-982e-45ec-a4df-d526f8151712` | 156 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Database |
| ALT.TIPS.Metadata | `9c58ff24-e1fb-4307-8988-bbf6b19c7894` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Metadata |
| ALT.TIPS.Reports | `2c27ddb4-09e4-4429-a585-c218fb6a9625` | 35.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Reports |
| AMM.TIPS.Application.QPEC | `22073bee-38ca-41a9-924c-0407cefd191f` | 956 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Application.QPEC |
| AMM.TIPS.Batch | `2b5ec220-f04c-4591-9862-9cf01c4dd434` | 12 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Batch |
| AMM.TIPS.ClassicBatch | `6b44e891-2dfd-4fab-befe-b94706bc5aaa` | 51 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.ClassicBatch |
| AMM.TIPS.Database | `ccfff629-515e-4cd8-b35c-1fe0e02ad7df` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Database |
| AMM.TIPS.Metadata | `d12f3561-6c55-4c20-9acc-e8631c5a72a8` | 7 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Metadata |
| AMM.TIPS.Reports | `dc928e9b-06dd-4bf1-8ff6-a3abce36f088` | 11.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Reports |
| ARM.TIPS.Database | `25ac9466-38c1-49ec-8ad6-0e08c3133810` | 46 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ARM.TIPS.Database |
| ARM.TIPS.Metadata | `353f263f-d7e9-46d3-baba-93aeb53272ed` | 32 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ARM.TIPS.Metadata |
| ARM.TIPS.Reports | `3309dc98-24c8-4f6d-a86f-2b81092abfa8` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ARM.TIPS.Reports |
| AZR.TIPS.Database | `2cd1e8e4-560e-49ea-8e5f-abb5c41ac195` | 368 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AZR.TIPS.Database |
| AZR.TIPS.Metadata | `30ee6967-7e5e-4fa6-8e01-dd4f7a2654bb` | 200 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AZR.TIPS.Metadata |
| AZR.TIPS.Reports | `8c719a1a-f18e-40a1-a16b-039969c6b765` | 44.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AZR.TIPS.Reports |
| BLU.TIPS.Database | `a2299d16-6a6a-42b6-97f8-a1b0b0e1542a` | 42 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLU.TIPS.Database |
| BLU.TIPS.Metadata | `fc664dbc-d95f-4ebd-ab63-6ecbeed4acf0` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLU.TIPS.Metadata |
| BLU.TIPS.Reports | `826d4c22-b111-4cff-a3e0-dba12a2ebdb3` | 12.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLU.TIPS.Reports |
| BMD.TIPS.Database | `e91637e7-52eb-4192-af67-5a637a6da44a` | 103 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMD.TIPS.Database |
| BMD.TIPS.Metadata | `9a2b705d-7edc-4317-9fd3-4bde760fe432` | 34 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMD.TIPS.Metadata |
| BMD.TIPS.Reports | `bbb2d039-c162-4c5d-a764-4b49be0f7494` | 16.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMD.TIPS.Reports |
| BMH.TIPS.Database | `2df0099f-d6bc-4bed-864b-6b2722b1daf5` | 102 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMH.TIPS.Database |
| BMH.TIPS.Metadata | `b634d0ff-9e59-44ef-b4ce-75d54fefdad4` | 362 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMH.TIPS.Metadata |
| BMH.TIPS.Reports | `1d118be8-b80a-4b4e-9702-6ba822f4a0bd` | 25.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMH.TIPS.Reports |
| BPM.TIPS.Database | `6d90a5b0-78da-4bba-ad81-6c75e1722562` | 53 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BPM.TIPS.Database |
| BPM.TIPS.Metadata | `7f8b3c30-91db-4465-90cf-1378349f0a5a` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BPM.TIPS.Metadata |
| BPM.TIPS.Reports | `782102b8-401c-4b9d-8cec-59d9872990b3` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BPM.TIPS.Reports |
| CCI.TIPS.Database | `15d8f685-c958-4ffa-a053-bf053cb4d917` | 82 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CCI.TIPS.Database |
| CCI.TIPS.Metadata | `42cf26d4-a732-4b20-88f9-c66e2525005e` | 491 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CCI.TIPS.Metadata |
| CCI.TIPS.Reports | `cf4c058e-ab27-4812-85c6-11ba5a3b4031` | 24.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CCI.TIPS.Reports |
| CHD.TIPS.Database | `90fb54ef-d440-4fa9-8319-ca04f452678f` | 158 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHD.TIPS.Database |
| CHD.TIPS.Metadata | `747a56e9-d3bb-4827-b190-4e68e1c6166c` | 58 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHD.TIPS.Metadata |
| CHD.TIPS.Reports | `53957010-cbdd-4aaf-8fa3-4caa6fc2f947` | 17.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHD.TIPS.Reports |
| CMH.TIPS.Application.QPEC | `78c352a4-81a5-4f08-9ed9-dd4089b99bd7` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Application.QPEC |
| CMH.TIPS.ClassicBatch | `af0533ce-cd2c-4628-8e8a-d706e3d686f4` | 35 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.ClassicBatch |
| CMH.TIPS.Database | `832d5a15-f149-4e50-a33e-a955a2992a3d` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Database |
| CMH.TIPS.Metadata | `db081444-fa23-44b0-b085-207a6ded2f92` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Metadata |
| CMH.TIPS.Reports | `34d97a9e-edf5-4dbe-8f0a-3be4fcc1a418` | 14.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Reports |
| CMP.TIPS.Application.ClassicGUI | `caed5526-9510-456d-896b-c83cbe8d0e84` | 290 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Application.ClassicGUI |
| CMP.TIPS.Application.QPEC | `c28823d9-a5e9-4879-8951-66cacd93e763` | 513 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Application.QPEC |
| CMP.TIPS.ClassicBatch | `1c16f102-bfed-4275-9dd3-a49df743db2a` | 617 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.ClassicBatch |
| CMP.TIPS.ClassicGUI | `9eab0ea5-72af-4f91-833f-592b3e074b9b` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.ClassicGUI |
| CMP.TIPS.Database | `d1264b58-4ad6-4e89-972a-bcbeaac5c32f` | 394 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Database |
| CMP.TIPS.Metadata | `fac3fc29-6127-4d75-93f0-34739a028bcf` | 10.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Metadata |
| CMP.TIPS.Reports | `f23a2e6e-ea9a-4a76-875a-81ee999dfb47` | 21.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Reports |
| CRS.TIPS.Application.QPEC | `ec399d91-a530-4935-8fb3-7a5c483e2b99` | 3.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Application.QPEC |
| CRS.TIPS.Batch | `9cc70268-8220-4d40-bb74-10f272797921` | 15 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Batch |
| CRS.TIPS.ClassicBatch | `8bf8ae45-44f4-491a-a41e-a602a2438262` | 144 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.ClassicBatch |
| CRS.TIPS.Database | `dd145f26-9a48-492f-9961-c3a21b8064f0` | 166 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Database |
| CRS.TIPS.Metadata | `e6f199b6-48ae-4c27-8269-fdd080b6d17a` | 60 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Metadata |
| CRS.TIPS.Reports | `770df692-d179-4f00-8bed-8b1c8186e5f9` | 29.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Reports |
| DCP.TIPS.Application.ClassicGUI | `fa26396e-fd32-4474-83f6-552929547563` | 652 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.ClassicGUI |
| DCP.TIPS.Application.MiddleTier | `e0aa6862-7b8c-4e4c-a125-a68331688c61` | 504 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.MiddleTier |
| DCP.TIPS.Application.QPEC | `ca4e8169-78c7-4775-b6bf-f4035ec631a9` | 810 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.QPEC |
| DCP.TIPS.Application.Web | `d8412bed-416a-4d21-a3d2-a1c5beb18e0c` | 31.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.Web |
| DCP.TIPS.Batch | `c963e1df-935d-4892-8b6c-48a0cbabf0cc` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Batch |
| DCP.TIPS.ClassicBatch | `eb54f1a3-52f5-4b1c-92b4-00b1feba535f` | 4.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.ClassicBatch |
| DCP.TIPS.ClassicGUI | `36cf4c9a-a2cd-4ba2-a4da-c6eb0f723207` | 339 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.ClassicGUI |
| DCP.TIPS.Database | `5698ced4-8d65-4ca7-9533-47732abedf3c` | 788 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Database |
| DCP.TIPS.Metadata | `b9190fb4-a453-4b98-86ab-0a9bfec7843b` | 48.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Metadata |
| DCP.TIPS.Reports | `671a3f6d-ce43-4fbd-b2af-16bc7fa72c9e` | 107.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Reports |
| DCP.TIPS.Web | `a66f8a18-3dfc-401d-8225-3c47e1b01b9e` | 626 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Web |
| DLP.TIPS.Database | `2f8ec76d-29d7-4067-a156-3347a4e47298` | 62 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DLP.TIPS.Database |
| DLP.TIPS.Metadata | `b70d6388-0c3c-4458-8bd5-f46cb73bb9ae` | 28 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DLP.TIPS.Metadata |
| DLP.TIPS.Reports | `70dece0b-9f31-4117-b230-78f64e53fe7e` | 24.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DLP.TIPS.Reports |
| DTE.TIPS.Application.MiddleTier | `8b30c863-46ab-4a3b-a6ce-13c76812ce75` | 458 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Application.MiddleTier |
| DTE.TIPS.Application.QPEC | `89a3ca8d-6e47-4df5-bf3c-ea1bba2e6207` | 583 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Application.QPEC |
| DTE.TIPS.Application.Web | `e429f3ba-2a48-42a4-9396-884825aba61f` | 35.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Application.Web |
| DTE.TIPS.ClassicBatch | `a4e3f4ec-9d83-4bdf-9d9e-390a35fe52c6` | 173 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.ClassicBatch |
| DTE.TIPS.Database | `34cfee41-8c69-4192-b2a8-0f5b8010efcb` | 421 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Database |
| DTE.TIPS.Metadata | `c0ae54c6-5c8c-4e68-ac2b-88b5f8309726` | 2.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Metadata |
| DTE.TIPS.Reports | `be65eeda-cc34-4831-8175-7c411fdac3b6` | 37.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Reports |
| DTE.TIPS.Web | `64864a86-bce8-4fe4-847d-7f047c4e7f95` | 707 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Web |
| DTM.TIPS.Application.MiddleTier | `398fb3e2-c450-4957-a6f2-83e04a9fd857` | 1.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Application.MiddleTier |
| DTM.TIPS.Application.QPEC | `e50c0d43-1a29-49ba-94f5-9e4782235584` | 3.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Application.QPEC |
| DTM.TIPS.Application.Web | `2b2c1495-470d-4012-8afd-e4fa5302dfac` | 50.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Application.Web |
| DTM.TIPS.ClassicBatch | `ad183215-a10a-46ec-b486-c134b3065a63` | 376 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.ClassicBatch |
| DTM.TIPS.Database | `9b936e7b-9ac3-42e4-9133-04c8795cc998` | 103 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Database |
| DTM.TIPS.Metadata | `7f3bcb6c-8cdc-4076-b1c5-19dc7ca8821b` | 126 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Metadata |
| DTM.TIPS.Reports | `7c542086-04c8-4ffb-91b1-dac2342cced7` | 18.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Reports |
| DTM.TIPS.Web | `84002827-69f3-48de-866b-61cbaef37b52` | 568 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Web |
| ECM.TIPS.Database | `1aab7ccf-3d86-4a3a-b81f-4f07b271b9a3` | 63 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ECM.TIPS.Database |
| ECM.TIPS.Metadata | `38ea38dc-5db6-41e0-9714-36f034da9c25` | 34 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ECM.TIPS.Metadata |
| EDA.TIPS.Database | `5fef0c8f-b8b2-4bbc-95fb-9dd4c95517e7` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDA.TIPS.Database |
| EDA.TIPS.Metadata | `f173b431-59f7-4a2f-9933-4fe0973d3f05` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDA.TIPS.Metadata |
| EDB.TIPS.Database | `d0189a60-912c-4020-9408-078d0d4f545a` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDB.TIPS.Database |
| EDB.TIPS.Metadata | `73f506ab-10c3-497c-8842-0651ff65c7fc` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDB.TIPS.Metadata |
| EDC.TIPS.Database | `dea16f8f-c77a-455b-bdd1-7d0669fd9537` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDC.TIPS.Database |
| EDC.TIPS.Metadata | `6cb2939b-a32b-4527-af5e-489af8b9afc4` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDC.TIPS.Metadata |
| EDO.TIPS.Application.QPEC | `6efa450a-965b-432d-9c17-5074764c2b1c` | 4.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDO.TIPS.Application.QPEC |
| EDO.TIPS.Metadata | `65c0c74f-f24a-4b29-81e7-858f11309d88` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDO.TIPS.Metadata |
| EIG.TIPS.Application.QPEC | `12443307-1964-4c96-a3cb-46943069db9a` | 8.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Application.QPEC |
| EIG.TIPS.ClassicBatch | `b2548ca7-13e7-4517-883f-ff4e4c349570` | 18 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.ClassicBatch |
| EIG.TIPS.Database | `c88d325d-5bce-4f06-a20c-9a0a7cb0125c` | 75 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Database |
| EIG.TIPS.Metadata | `d068d46b-8a97-468a-bb7d-2d584332ff0a` | 40 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Metadata |
| EIG.TIPS.Reports | `919b78c3-91cf-4580-9d72-82e46fa91c18` | 22.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Reports |
| EMP.TIPS.Application.ClassicGUI | `bc4910e7-6d26-4ea4-aa93-f81630ca0edf` | 256 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.ClassicGUI |
| EMP.TIPS.Application.MiddleTier | `11c701ac-b385-42eb-a25b-3a43e5bf8f96` | 272 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.MiddleTier |
| EMP.TIPS.Application.QPEC | `62cce34c-7a89-4765-afdf-58b0a6a02da8` | 357 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.QPEC |
| EMP.TIPS.Application.Web | `d2ce2b93-d164-4627-95ae-c300127a539b` | 23.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.Web |
| EMP.TIPS.Batch | `4741fd1b-4efa-4bbb-94a4-80b59bafe4af` | 34 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Batch |
| EMP.TIPS.ClassicBatch | `29b85a5a-51a6-4715-9a60-b463e9019814` | 17.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.ClassicBatch |
| EMP.TIPS.ClassicGUI | `a42c204a-eafe-44b6-88f2-5e73a3ec8923` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.ClassicGUI |
| EMP.TIPS.Database | `f801ad5f-b11a-4f23-b49e-128bfe907e12` | 527 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Database |
| EMP.TIPS.Metadata | `9c3fd19b-b975-487b-ba4d-ac7dced55c38` | 23.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Metadata |
| EMP.TIPS.Reports | `7affad29-d217-4a57-958c-089bad66e9a9` | 14.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Reports |
| EMP.TIPS.Web | `87c957a7-6d20-4c27-a67c-c9b88cc62803` | 747 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Web |
| ENT.TIPS.Application.QPEC | `85fec4e2-ea80-4775-a369-fbe6e834c877` | 1.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Application.QPEC |
| ENT.TIPS.Batch | `a1bfc0c6-6ee2-4e0b-b57e-6c4960106437` | 408 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Batch |
| ENT.TIPS.ClassicBatch | `e9010747-4b9d-4061-bde2-66b3b1ba685d` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.ClassicBatch |
| ENT.TIPS.Database | `8b1edc20-c380-4b2a-8186-8fa8f5d95f7a` | 315 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Database |
| ENT.TIPS.Metadata | `57bd4096-e9b9-47c0-a5b5-528f85a87dda` | 12.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Metadata |
| ENT.TIPS.Reports | `84244722-01d7-45bb-8181-fab6e7b4cf6e` | 65.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Reports |
| ENT.TIPS.Web | `86495096-f878-4dc5-be3c-483f24c58a49` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Web |
| EOI.TIPS.Database | `e36b8e61-d079-447f-9a3d-64578b90ef05` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EOI.TIPS.Database |
| EOI.TIPS.Metadata | `3985f8cf-724c-4bd4-8309-abe165ba1be3` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EOI.TIPS.Metadata |
| EQC.TIPS.API | `fd4a272c-6a61-4283-a749-eeb13a5d556c` | 120 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.API |
| EQC.TIPS.API.Specs | `81e784d3-9105-4644-b158-0dbb90f2e47f` | 2.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.API.Specs |
| EQC.TIPS.Application.ClassicGUI | `8c207325-fc64-4c86-a1b0-1ffa55e337b0` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.ClassicGUI |
| EQC.TIPS.Application.MiddleTier | `7604f471-f834-4e20-b755-59dd404266c6` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.MiddleTier |
| EQC.TIPS.Application.QPEC | `b4a384c9-dc87-4588-ba30-cb203ea8f075` | 2.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.QPEC |
| EQC.TIPS.Application.Web | `a1f78e5d-eb8d-4f22-8954-c11fcff8d8aa` | 55.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.Web |
| EQC.TIPS.Batch | `7c44c133-8838-494f-9937-e448e6c39e93` | 20 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Batch |
| EQC.TIPS.ClassicBatch | `bda03b52-6a82-4f85-b38b-5f79fc41cae7` | 83 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.ClassicBatch |
| EQC.TIPS.ClassicGUI | `da7927a4-8e0f-4a60-af5a-1062f749cb82` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.ClassicGUI |
| EQC.TIPS.Database | `1c916ee6-e791-4ae3-8e05-6bdbecf49beb` | 297 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Database |
| EQC.TIPS.Metadata | `9e64727f-1918-45e2-b871-0c7208cbc1d1` | 415 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Metadata |
| EQC.TIPS.Reports | `f7465311-9d26-422c-8396-d72db11c1097` | 39.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Reports |
| EQC.TIPS.Web | `137d2c25-4e55-478c-8533-0fb4b54f1826` | 457 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Web |
| EQT.TIPS.Application.MiddleTier | `3eb4a8e5-ac53-4492-a1d8-13933685d991` | 669 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Application.MiddleTier |
| EQT.TIPS.Application.QPEC | `6ca8fb54-cc63-4be5-b938-3d7c6295525f` | 237 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Application.QPEC |
| EQT.TIPS.Application.Web | `90843511-0a46-4a10-9cd9-6422c28fbf68` | 25.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Application.Web |
| EQT.TIPS.ClassicBatch | `beecb4da-a196-48a6-9d6a-d0b8dc061d0b` | 78 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.ClassicBatch |
| EQT.TIPS.Database | `1641f9c1-3079-4747-9bea-c8cb44180fdc` | 81 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Database |
| EQT.TIPS.Metadata | `07a49083-c5d6-433c-9866-0b38d99a9f4e` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Metadata |
| EQT.TIPS.Reports | `209a301f-d987-4f8e-b7e7-c843b31c8998` | 15.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Reports |
| EQT.TIPS.Web | `340c7b09-2f4c-475d-8bb1-202b6d19a355` | 825 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Web |
| ETP.TIPS.Application.MiddleTier | `57d6df92-244a-439e-bd1b-c99c01bd7511` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Application.MiddleTier |
| ETP.TIPS.Application.QPEC | `3c8000ef-2ac0-4d89-9efc-f37d0ac3d25c` | 3.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Application.QPEC |
| ETP.TIPS.Application.Web | `829f3069-2be1-4516-97f2-6ae4071a9e4b` | 56.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Application.Web |
| ETP.TIPS.Batch | `40a812a4-2fcb-4a17-8b64-f563b940cfcb` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Batch |
| ETP.TIPS.ClassicBatch | `756915be-e373-4c61-831b-38dd94558c55` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.ClassicBatch |
| ETP.TIPS.Database | `732844c0-ef92-427a-9a93-e3d01a91d69e` | 523 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Database |
| ETP.TIPS.Metadata | `7a35b308-42aa-4451-8164-789ba4c6ed06` | 26.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Metadata |
| ETP.TIPS.Reports | `951dc268-0ccb-42a5-9214-2a8974f5f1de` | 51.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Reports |
| ETP.TIPS.Web | `3d6ae1d3-01bd-49cb-83c5-234861abbca6` | 599 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Web |
| EVO.TIPS.Metadata | `59a64b5a-0fd8-4982-8aef-4f1ef3e302e5` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EVO.TIPS.Metadata |
| EVO.TIPS.Reports | `6ab65d4a-aa15-4730-be78-da9611db20e6` | 10.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EVO.TIPS.Reports |
| FOR.TIPS.Database | `235212d8-ddfd-4ed7-adfc-656e39485c04` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FOR.TIPS.Database |
| FOR.TIPS.Metadata | `fe78dd8d-8c5f-4271-8218-c4f5fb3d3f09` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FOR.TIPS.Metadata |
| FPL.TIPS.Crude.Metadata | `24c685d2-40e1-4ecd-882d-a59ef43437f8` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FPL.TIPS.Crude.Metadata |
| FPL.TIPS.Database | `20ce5a3f-0ad0-47b5-abd0-056d1f299d4f` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FPL.TIPS.Database |
| FPL.TIPS.Metadata | `87619858-5c71-4239-a000-460373d4010a` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FPL.TIPS.Metadata |
| FRC.TIPS.Database | `9bd947a5-a4c1-4e3c-9f29-d1dc4b17fbfc` | 62 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FRC.TIPS.Database |
| FRC.TIPS.Metadata | `91911e31-05b9-49e5-a05f-918af95a843b` | 59 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FRC.TIPS.Metadata |
| FRC.TIPS.Reports | `f23bd2d6-f289-4d81-8131-3494ce262775` | 15.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FRC.TIPS.Reports |
| GLE.TIPS.Database | `8d62e21f-5b34-4b36-9536-5cfbabf3e1b4` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.TIPS.Database |
| GLE.TIPS.Metadata | `d1400d72-7903-45de-9a85-f73aee6d8520` | 5.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.TIPS.Metadata |
| GLE.TIPS.Reports | `a1c83452-4c86-49ee-90b8-bc8b26a2af4a` | 46.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.TIPS.Reports |
| GNM.TIPS.Database | `89514301-4a72-47dd-82a8-b524c9931d4b` | 164 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNM.TIPS.Database |
| GNM.TIPS.Metadata | `aaadcb4c-c61c-4554-abff-e96980393ac9` | 137 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNM.TIPS.Metadata |
| GNM.TIPS.Reports | `22263197-c22c-4533-a96f-6d5bdce574ab` | 31.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNM.TIPS.Reports |
| HEC.TIPS.Database | `a211d45c-8b0e-4c57-b2cb-ee067085932a` | 68 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEC.TIPS.Database |
| HEC.TIPS.Metadata | `44284678-b317-40ac-b894-2b986634eb96` | 41 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEC.TIPS.Metadata |
| HEC.TIPS.Reports | `5236feb9-d7f7-48bf-aa2f-51f0282abbc8` | 20.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEC.TIPS.Reports |
| HEP.TIPS.Database | `185d3f3f-38a6-46b7-834a-dcadca63e154` | 280 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.TIPS.Database |
| HEP.TIPS.Metadata | `9446543d-9ec0-4754-9ec0-1cf2cfa01611` | 71 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.TIPS.Metadata |
| HEP.TIPS.Reports | `05876f5a-ed4f-472e-972d-6eb20a33b06b` | 44.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.TIPS.Reports |
| HPE.TIPS.Application.QPEC | `823213c9-3b49-4a73-9c95-1ec367607367` | 642 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Application.QPEC |
| HPE.TIPS.ClassicBatch | `9f455a31-e14c-4078-aafa-7fa583031753` | 78 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.ClassicBatch |
| HPE.TIPS.Database | `3792bc28-bc0e-4b91-b141-8c57518f6772` | 169 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Database |
| HPE.TIPS.Metadata | `e573745c-d36d-47bf-969c-925ff0c4168f` | 13.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Metadata |
| HPE.TIPS.Reports | `c931c89f-bedd-45bd-9d1b-9f5edbdb69f6` | 51.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Reports |
| HVK.TIPS.Database | `db1ac339-479b-436b-8c73-e0dec60a7994` | 131 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVK.TIPS.Database |
| HVK.TIPS.Metadata | `1ec1f932-45d4-412a-b2fb-ea7be1dff372` | 662 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVK.TIPS.Metadata |
| HVK.TIPS.Reports | `87be4f59-4137-4fba-a415-3f1e3fda00bc` | 31.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVK.TIPS.Reports |
| HVM.TIPS.Database | `f8837a41-27d2-43dd-b967-724a51e21e9e` | 735 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVM.TIPS.Database |
| HVM.TIPS.Metadata | `e9c62d47-607e-441b-8fa4-398ee6b22571` | 24.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVM.TIPS.Metadata |
| HVM.TIPS.Reports | `55346d6b-fd1d-4c47-9dc7-22065525e0de` | 45.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVM.TIPS.Reports |
| IAC.TIPS.Application.ClassicGUI | `16d54541-6be9-4de6-86b3-0fadc878d0ce` | 591 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Application.ClassicGUI |
| IAC.TIPS.Application.MiddleTier | `0c2f9b00-8ff2-443d-88a5-85fb703d510f` | 638 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Application.MiddleTier |
| IAC.TIPS.Application.QPEC | `f3644c08-cc95-4725-bfc8-8546760467fb` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Application.QPEC |
| IAC.TIPS.ClassicBatch | `743051a8-2d1b-4415-bde3-5599e5da4af1` | 2.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.ClassicBatch |
| IAC.TIPS.ClassicGUI | `775196cd-a023-4e93-b014-4341e234d4a8` | 222 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.ClassicGUI |
| IAC.TIPS.Database | `3b90546d-27a8-43ab-b73c-6fe8b0211f39` | 637 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Database |
| IAC.TIPS.Metadata | `32d9a64d-c517-4564-8a98-74b7013473d8` | 18.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Metadata |
| IAC.TIPS.Reports | `d58683b7-a98e-46a1-b9dd-83b1ffc36208` | 49.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Reports |
| IAC.TIPS.Web | `823f0c9d-0d64-478f-9655-54b890b6cceb` | 515 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Web |
| IME.TIPS.Application.QPEC | `5a206913-7a37-4d1a-82b6-e7b314519a29` | 3.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Application.QPEC |
| IME.TIPS.Batch | `e2319909-0db9-496e-8a41-efd88892e72b` | 35 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Batch |
| IME.TIPS.ClassicBatch | `068ada17-ce32-49e4-bcda-f5d01bdfa023` | 22 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.ClassicBatch |
| IME.TIPS.Database | `006b3905-5c36-4fa1-bcb1-8ba13cb2cd58` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Database |
| IME.TIPS.Metadata | `8776ddfa-e66f-4a9f-8d54-ca409da6d1f5` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Metadata |
| IME.TIPS.Reports | `967d87ea-ba7e-45e2-acc2-ea90bbcdcce0` | 14.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Reports |
| IPF.TIPS.Database | `4faa286e-18b1-4126-b2a8-90fc109e8cac` | 8.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IPF.TIPS.Database |
| IPF.TIPS.Metadata | `4d45530c-40f8-45de-8203-e842af0ef04f` | 184 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IPF.TIPS.Metadata |
| IPF.TIPS.Reports | `d7bff4d5-2559-44cf-bb24-cf0f41d467c9` | 24.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IPF.TIPS.Reports |
| KEY.TIPS.Application.QPEC | `08f03d8a-67ac-48fd-97d0-dab0ace52baa` | 256 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Application.QPEC |
| KEY.TIPS.ClassicBatch | `17feec75-8fba-47c8-8cd7-69f11ef5cc26` | 47 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.ClassicBatch |
| KEY.TIPS.Database | `5b9147bc-b276-456b-8142-83f9e689825f` | 604 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Database |
| KEY.TIPS.Metadata | `fa118cf8-bd5d-4bdf-bdba-9052509a4ee5` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Metadata |
| KEY.TIPS.Reports | `0dd62312-3749-49d9-b51c-c57f599b9079` | 39.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Reports |
| LMD.TIPS.ClassicBatch | `947150cd-4d0c-48ff-9361-46b2fac9e254` | 22 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.ClassicBatch |
| LMD.TIPS.Database | `da31e213-5adc-48b3-98ce-5c9104db57ae` | 69 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.Database |
| LMD.TIPS.Metadata | `ed52990f-7bb0-4fc8-bf3b-fc94bb033e44` | 226 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.Metadata |
| LMD.TIPS.Reports | `752d96dc-cb6f-4786-bff5-4337a71030cd` | 11.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.Reports |
| LVM.TIPS.Application.MiddleTier | `37bb5da0-6f2b-41a7-a183-b7425863d9d8` | 601 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Application.MiddleTier |
| LVM.TIPS.Application.QPEC | `336dc000-521d-4f7c-8ec9-d977d1e59221` | 908 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Application.QPEC |
| LVM.TIPS.ClassicBatch | `a609a4e8-ef13-4ae5-ba3c-f330e5db6026` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.ClassicBatch |
| LVM.TIPS.Database | `552891d1-e15e-42d7-8b23-dbf0c894f6a5` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Database |
| LVM.TIPS.Metadata | `aa82bd52-869e-484e-be9d-69d248d0bc9f` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Metadata |
| LVM.TIPS.Reports | `48b2bee4-689b-4de4-9b97-641aaebee657` | 15.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Reports |
| MER.TIPS.Application.QPEC | `eef1f4df-9722-4ea9-9581-b6a101ff592c` | 811 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Application.QPEC |
| MER.TIPS.ClassicBatch | `cc9064b4-b47a-4da3-bdae-3fc9eb93dadd` | 270 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.ClassicBatch |
| MER.TIPS.Crude.Metadata | `9f4b3a0d-af6f-4d5c-a90e-ecdb59870940` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Crude.Metadata |
| MER.TIPS.Database | `50f0de05-6bc4-43cf-b45e-8cd9d99053e5` | 435 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Database |
| MER.TIPS.Metadata | `52677e7f-a813-4232-a04f-4c5d8eeb5ecb` | 14.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Metadata |
| MER.TIPS.Reports | `542c3986-f65a-4c25-9a61-11cc0eeebd70` | 32.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Reports |
| MER.TIPS.SAP.Application.WebService | `bbd85f3d-72a5-4996-b5c6-b14f8283f856` | 85 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.SAP.Application.WebService |
| MGP.TIPS.Application.QPEC | `0833d6b2-b8eb-4525-bc10-cea23b7d95a4` | 226 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Application.QPEC |
| MGP.TIPS.ClassicBatch | `8c3c6023-7584-4f83-b76e-5bc89ee36465` | 140 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.ClassicBatch |
| MGP.TIPS.Database | `c700592e-3c8b-4e1b-b35c-2abf9016f570` | 111 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Database |
| MGP.TIPS.Metadata | `456d5e25-d6f8-4451-a774-cb7a846bdd0e` | 48.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Metadata |
| MGP.TIPS.Reports | `94b096c0-e5ae-451a-b146-def955ea3d4d` | 20.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Reports |
| MKW.TIPS.Application.MiddleTier | `42dacd1e-6bf3-4cb6-93a2-3fdbcda72fbd` | 332 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Application.MiddleTier |
| MKW.TIPS.Application.QPEC | `26deafe1-5944-4116-afb8-7241479ef634` | 558 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Application.QPEC |
| MKW.TIPS.Application.Web | `1b0f3eef-c740-479b-ad9c-f63619339b80` | 30.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Application.Web |
| MKW.TIPS.ClassicBatch | `84c62990-03c3-46dc-8ce9-6c2facab9f12` | 437 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.ClassicBatch |
| MKW.TIPS.Database | `bb8d8c92-be7d-419a-b2e9-059687d96422` | 519 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Database |
| MKW.TIPS.Metadata | `36e5afc7-3df6-4572-b9f2-7e89f55c3764` | 50.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Metadata |
| MKW.TIPS.Reports | `eb528a6c-9ffa-4d0d-a05f-cfc5b0ff0357` | 33.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Reports |
| MKW.TIPS.Web | `847431ed-714c-4200-8dfb-011939b4a716` | 735 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Web |
| MOM.TIPS.Application.QPEC | `ee796dd1-28d3-4ee5-8635-fbaaac94eb14` | 4.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Application.QPEC |
| MOM.TIPS.ClassicBatch | `81598829-567b-42ba-91d8-14a30ce8c4db` | 104 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.ClassicBatch |
| MOM.TIPS.Database | `1ce1a962-0d13-40b1-bd50-10a45693189f` | 170 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Database |
| MOM.TIPS.Metadata | `7d570f16-c67b-41e1-bba3-085dfad8cf67` | 53 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Metadata |
| MOM.TIPS.Reports | `6b5bd9ee-8022-463b-885d-117501723b6b` | 24.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Reports |
| NEM.TIPS.Database | `76f38886-b214-4ffb-aa43-2f0a9aa86822` | 76 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NEM.TIPS.Database |
| NEM.TIPS.Metadata | `879a32e6-71d4-4fd2-9347-769b2877fb40` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NEM.TIPS.Metadata |
| NRM.TIPS.Application.QPEC | `ea9304c8-c2bb-46b2-9cf8-0c611f59bf0b` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Application.QPEC |
| NRM.TIPS.Batch | `e23b0224-bc14-499f-9bc7-d3e659ceaa8c` | 99 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Batch |
| NRM.TIPS.ClassicBatch | `9144e155-e4dd-4f2c-94cf-447d226ca9b9` | 300 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.ClassicBatch |
| NRM.TIPS.Database | `ec08db4c-8663-4621-914f-8398595a63f9` | 629 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Database |
| NRM.TIPS.Metadata | `3a28d529-d923-45ac-be94-c6090c46e976` | 42.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Metadata |
| NRM.TIPS.Reports | `0185afed-8906-40f9-9a43-b5c343e84f7a` | 39.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Reports |
| ONM.TIPS.Application.MiddleTier | `801b49be-e35f-429d-bc1b-3f48b2abe90e` | 1016 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Application.MiddleTier |
| ONM.TIPS.Application.QPEC | `5b8d6efe-ae2f-4fd2-8816-def487d45c1a` | 940 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Application.QPEC |
| ONM.TIPS.Application.Web | `90a0ba07-2873-423c-aed3-417c405fd30a` | 34.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Application.Web |
| ONM.TIPS.ClassicBatch | `91497497-6020-4448-bdc7-83cabce729af` | 373 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.ClassicBatch |
| ONM.TIPS.Database | `3d9692e2-5b57-437b-89ef-8b0e126b5a7a` | 724 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Database |
| ONM.TIPS.Metadata | `54a61637-084c-43aa-a7e3-afb3a943e32f` | 47.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Metadata |
| ONM.TIPS.Reports | `f1852bec-8e10-475c-b24c-3476be70976b` | 35.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Reports |
| ONM.TIPS.Web | `a9ddebe9-0807-439c-b390-ddb5348c1d96` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Web |
| OXY.TIPS.Application.QPEC | `c9f5931e-09aa-4df7-b9ba-fe5af3a669fa` | 4.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Application.QPEC |
| OXY.TIPS.ClassicBatch | `cf7fa0b9-1c65-4f12-abf7-e4537e542280` | 156 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.ClassicBatch |
| OXY.TIPS.Database | `2bb7cf13-4a85-427c-857c-9cfac3836ff5` | 190 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Database |
| OXY.TIPS.Metadata | `e724d35d-1bb3-43ab-abf9-5d0391f45727` | 216 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Metadata |
| OXY.TIPS.Reports | `2e5df180-07bc-4a1d-a66d-dbe69f8a0ade` | 19.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Reports |
| PEM.TIPS.Application.QPEC | `b110cb7c-ee3e-4c7f-b083-6968812facf0` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Application.QPEC |
| PEM.TIPS.ClassicBatch | `22a3a525-cdcc-4db4-b5cf-d68f6e9f7682` | 135 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.ClassicBatch |
| PEM.TIPS.Database | `6d2c8b11-6295-45d0-b36b-a0f8f25411b6` | 256 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Database |
| PEM.TIPS.Metadata | `12bffa88-137f-4211-8faa-61f4fe3fd3f9` | 106.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Metadata |
| PEM.TIPS.Reports | `323b3c86-a0be-44c6-bdc9-71bf4687b22f` | 49.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Reports |
| Pembina.TIPS.Application.Web | `db5da9a1-b724-4cb1-b1c0-c2270e01a260` | 21.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Pembina.TIPS.Application.Web |
| Pembina.TIPS.Web | `e10c9ae2-1f52-4fc2-94ba-8062e9dcfb69` | 216 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Pembina.TIPS.Web |
| PEP.TIPS.Application.QPEC | `b6fffff2-8975-43a7-9889-839a35a93924` | 573 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Application.QPEC |
| PEP.TIPS.ClassicBatch | `964946d6-71c6-472a-910a-7ca6171de67a` | 696 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.ClassicBatch |
| PEP.TIPS.Database | `cad24b7a-fc8a-4b83-ab84-ef4a7d775caf` | 127 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Database |
| PEP.TIPS.Metadata | `f151a040-4a1b-4c3b-972c-14fe52337a33` | 561 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Metadata |
| PEP.TIPS.Reports | `9986cb19-8349-491e-b28f-dc89506d7298` | 26.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Reports |
| PMB.TIPS.Application.QPEC | `1479ea70-e86c-4f23-92dc-b9f6a7090305` | 659 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Application.QPEC |
| PMB.TIPS.ClassicBatch | `248373f6-bcbd-4329-898c-53f8ff49c0c4` | 64 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.ClassicBatch |
| PMB.TIPS.Database | `d5128ed7-d80d-400e-8430-ada53613baee` | 14 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Database |
| PMB.TIPS.Metadata | `9645938a-4618-41d6-bbfd-efba710bad32` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Metadata |
| PMB.TIPS.Reports | `f316abb1-b1a8-42e1-b563-beb62584e227` | 17.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Reports |
| PML.TIPS.Application.QPEC | `f2b1e610-9214-403e-b687-343a0322ad00` | 3.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Application.QPEC |
| PML.TIPS.Batch | `da1e1cdc-4fe6-40f3-a490-c9d1f45eb104` | 16 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Batch |
| PML.TIPS.ClassicBatch | `ee05a121-a444-4d81-ab86-3a2223437010` | 84 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.ClassicBatch |
| PML.TIPS.Database | `fa46fb0d-5429-426b-932c-233522767fe5` | 66 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Database |
| PML.TIPS.Metadata | `e23e2aba-31ad-41c7-b3c3-bd90a6934124` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Metadata |
| PML.TIPS.Reports | `9a47b525-0a1a-4d7d-897e-cf0e5e41d600` | 29.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Reports |
| PNR.TIPS.Database | `a9ac6e81-daaa-4813-ba1b-50a524d7f322` | 86 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PNR.TIPS.Database |
| PNR.TIPS.Metadata | `c9b66312-32c8-4dbd-a4ff-8ab7da1a5582` | 124 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PNR.TIPS.Metadata |
| PNR.TIPS.Reports | `1b6efc11-a3ec-4b1f-92f0-141ecc30e959` | 19.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PNR.TIPS.Reports |
| PRF_DCP_PRF.TIPS.Application.ClassicGUI | `f3b85501-23cb-48c1-82db-0badf0cb7c8f` | 768 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.ClassicGUI |
| PRF_DCP_PRF.TIPS.Application.MiddleTier | `dd537374-5136-474d-aba5-8dcbdb9bc5a9` | 741 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.MiddleTier |
| PRF_DCP_PRF.TIPS.Application.QPEC | `30760a1d-b293-4cdc-b6dc-360d381e5238` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.QPEC |
| PRF_DCP_PRF.TIPS.Application.Web | `d215a2ba-f2b0-45be-b741-53faa33c8636` | 45.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.Web |
| PRF_DCP_PRF.TIPS.Batch | `e8b336da-104b-41ae-9b79-b949deec1766` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Batch |
| PRF_DCP_PRF.TIPS.ClassicBatch | `eda280b4-251a-4a05-9794-353d827cad84` | 4.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.ClassicBatch |
| PRF_DCP_PRF.TIPS.ClassicGUI | `87903efc-bb06-4b12-86bb-4060f9cc7531` | 301 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.ClassicGUI |
| PRF_DCP_PRF.TIPS.Database | `d4f82c84-315b-496f-88da-5ca6c69d272d` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Database |
| PRF_DCP_PRF.TIPS.Metadata | `72d8a9df-dcb6-4201-be31-d301dc200c2e` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Metadata |
| PRF_DCP_PRF.TIPS.Reports | `8d3116f3-bea7-43de-8099-fd1e67d6d975` | 49.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Reports |
| PRF_DCP_PRF.TIPS.Web | `079745b8-12ee-4039-aea7-991565864e49` | 874 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Web |
| PRF_ENT_PRT.TIPS.Application.MiddleTier | `06fefd6c-1cc8-47d1-8b60-bb721d5d7092` | 690 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Application.MiddleTier |
| PRF_ENT_PRT.TIPS.Application.QPEC | `918acb88-e7db-4602-a8ed-9b52338bb831` | 446 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Application.QPEC |
| PRF_ENT_PRT.TIPS.Application.Web | `521bc66a-01bd-48d2-b266-d6a291a6010c` | 38.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Application.Web |
| PRF_ENT_PRT.TIPS.Batch | `ea15086d-c510-4ad2-8a01-9af660d897af` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Batch |
| PRF_ENT_PRT.TIPS.ClassicBatch | `c5ce42ec-dabd-44c2-b538-158bf4e39234` | 821 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.ClassicBatch |
| PRF_ENT_PRT.TIPS.Database | `7bfb325f-0fee-41a8-b807-dc6ce89c4d74` | 27 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Database |
| PRF_ENT_PRT.TIPS.Metadata | `a3089149-d867-41d4-9d8d-e5c334a4d1b4` | 4.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Metadata |
| PRF_ENT_PRT.TIPS.Reports | `68dc7e4c-853a-451f-8258-8489e003b185` | 31.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Reports |
| PRF_ENT_PRT.TIPS.Web | `c06b262b-bec0-4c9c-8c88-92ae8b3bd6fc` | 368 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Web |
| PRF_ONM_PRF.TIPS.Application.MiddleTier | `08ed3785-3239-48cf-8750-6f4648bdd721` | 982 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Application.MiddleTier |
| PRF_ONM_PRF.TIPS.Application.QPEC | `ef841915-7b19-4a45-a4c1-ba0ef533065d` | 897 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Application.QPEC |
| PRF_ONM_PRF.TIPS.Application.Web | `bdbeaf29-cf13-4ef8-92fc-da1f029b3c80` | 54.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Application.Web |
| PRF_ONM_PRF.TIPS.ClassicBatch | `84d03d44-02fe-4a69-9128-d90d63154959` | 326 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.ClassicBatch |
| PRF_ONM_PRF.TIPS.Database | `2532a82e-d686-44e9-b56c-025b6e7b5e36` | 384 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Database |
| PRF_ONM_PRF.TIPS.Metadata | `e862f052-3b02-409a-a8ac-259af1127fa8` | 39.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Metadata |
| PRF_ONM_PRF.TIPS.Reports | `5a82bb27-4119-4a23-aff9-dfa3df68da83` | 63.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Reports |
| PRF_ONM_PRF.TIPS.Web | `17963959-116c-4b7a-9dcf-833ac0bf9350` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Web |
| PRF_PEM_PRT.TIPS.Application.QPEC | `e3d25616-7c66-4a59-87e6-159c9207caaf` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Application.QPEC |
| PRF_PEM_PRT.TIPS.ClassicBatch | `31350062-9c72-42e6-9074-b811424e77d8` | 147 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.ClassicBatch |
| PRF_PEM_PRT.TIPS.Database | `51bbafec-1d80-4410-a822-d8d857f2c24a` | 199 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Database |
| PRF_PEM_PRT.TIPS.Metadata | `20442c4b-724c-4a2e-bb6a-2200aa6803a7` | 106.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Metadata |
| PRF_PEM_PRT.TIPS.Reports | `616d5ed7-3001-44ff-ab2e-04aa3b90b839` | 57.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Reports |
| SCT.TIPS.Application.QPEC | `e5535a6b-7f83-4b8f-887e-3f6d1b2a400e` | 943 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Application.QPEC |
| SCT.TIPS.ClassicBatch | `83a85419-656f-4fc0-a5cb-ecf8b9733565` | 149 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.ClassicBatch |
| SCT.TIPS.Database | `38e93458-32a4-49d1-81be-1a9d7f17ceb1` | 346 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Database |
| SCT.TIPS.Metadata | `79207347-1aac-425e-aadb-f99df3755543` | 253 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Metadata |
| SCT.TIPS.Reports | `2c4c2e32-c3f4-4195-820f-e5faf9900d8b` | 53.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Reports |
| SCX.TIPS.Application.MiddleTier | `a3edc915-4c8a-43c1-9842-265f87e72386` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Application.MiddleTier |
| SCX.TIPS.Application.QPEC | `714e6e5a-5942-4503-9753-d7787c3de984` | 2.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Application.QPEC |
| SCX.TIPS.Application.Web | `37334184-dd46-44f0-b08a-d969146e2b45` | 49.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Application.Web |
| SCX.TIPS.Batch | `107a5944-dc0c-4c21-8928-f870d61ce1c9` | 36 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Batch |
| SCX.TIPS.Database | `0c50a049-7b76-43d1-a282-d031001114c7` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Database |
| SCX.TIPS.Metadata | `ce517e9f-a7b2-4da0-a279-35bedfb76e3b` | 23.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Metadata |
| SCX.TIPS.Reports | `a10935a2-32d2-4977-bb01-1b72e0ef03f1` | 21.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Reports |
| SCX.TIPS.Web | `91bd0b58-ddd2-48a2-a501-3a606b94ca50` | 280 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Web |
| SEM.TIPS.Application.QPEC | `7acde4ed-1e7f-4925-917a-1334e1f64c61` | 2.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Application.QPEC |
| SEM.TIPS.ClassicBatch | `44acaf4b-7b89-4cf1-aff1-072a7a3ef0d6` | 289 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.ClassicBatch |
| SEM.TIPS.Database | `089c2776-dd7b-4aa5-918c-28a725e7b918` | 257 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Database |
| SEM.TIPS.Metadata | `bd0e5861-7721-4ba3-935a-9d518484fa54` | 845 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Metadata |
| SEM.TIPS.Reports | `8a16915a-98a7-4906-8888-ea6c84ea5a73` | 25.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Reports |
| SPR.TIPS.Application.QPEC | `b19969f9-9b49-4b7a-b05b-f68d88d96ff1` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Application.QPEC |
| SPR.TIPS.ClassicBatch | `902c2a62-2b42-46d1-9aae-f366d6ffc388` | 69 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.ClassicBatch |
| SPR.TIPS.Database | `48e1209e-e25a-47ab-b61c-381cbc0285b8` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Database |
| SPR.TIPS.Metadata | `3843b44f-a235-45c5-9219-1bf8e099dd9a` | 45 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Metadata |
| SPR.TIPS.Reports | `401c8fda-b884-43d5-9f52-cde9486177f4` | 15.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Reports |
| SRB.TIPS.Database | `72be6380-ba2b-4fd0-917c-071954fd9cb2` | 226 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRB.TIPS.Database |
| SRB.TIPS.Metadata | `4a8bc3fc-b4a0-4b33-a278-350c78704db6` | 6.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRB.TIPS.Metadata |
| SRB.TIPS.Reports | `f432d9e8-084c-43ee-a818-d70aa750467f` | 26.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRB.TIPS.Reports |
| SRC.TIPS.Application.QPEC | `478d2384-022e-48ee-a614-4c037ee20cc9` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Application.QPEC |
| SRC.TIPS.ClassicBatch | `f2a968cd-86f5-41ee-bc55-74c3985b1a27` | 66 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.ClassicBatch |
| SRC.TIPS.Database | `c553d2ba-e873-4bf8-ac60-c22dacf8eddd` | 50 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Database |
| SRC.TIPS.Metadata | `2a71cfbc-f451-43bd-bb03-82969d2112ef` | 886 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Metadata |
| SRC.TIPS.Reports | `e8e9df93-a315-4b28-bece-c9acd1b34391` | 17.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Reports |
| SRI.TIPS.Database | `79139198-42f3-474e-b80f-4dfcbc94b01b` | 89 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRI.TIPS.Database |
| SRI.TIPS.Metadata | `6fc0f754-27c9-463b-8445-0f49c2a51c6a` | 64 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRI.TIPS.Metadata |
| TCP.TIPS.Crude.Application.MiddleTier | `084ea748-4a1e-4e27-98c4-3f8195628259` | 547 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Application.MiddleTier |
| TCP.TIPS.Crude.Application.QPEC | `a52aabeb-7f12-40b9-a12f-fa2a04c2121f` | 804 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Application.QPEC |
| TCP.TIPS.Crude.Application.Web | `f621ba6a-ef11-47d0-b92b-b3788cf934f1` | 33.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Application.Web |
| TCP.TIPS.Crude.Batch | `6958943e-bb97-4c4a-98de-7656e2a00a9d` | 244 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Batch |
| TCP.TIPS.Crude.ClassicBatch | `2e811fe6-3b7d-4c00-83e9-82cacef0f877` | 81 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.ClassicBatch |
| TCP.TIPS.Crude.Database | `0c53f195-e40c-423f-aede-dfbb10874261` | 71 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Database |
| TCP.TIPS.Crude.Metadata | `72115373-7986-4579-bfa5-8a1cd6990dda` | 62.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Metadata |
| TCP.TIPS.Crude.Reports | `a4a6a0cf-16fb-4d41-b80d-11508f08d7f9` | 23.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Reports |
| TCP.TIPS.Crude.Web | `9618a384-dfd3-4001-940f-3a69c6fc7d32` | 209 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Web |
| UGI.TIPS.Database | `3bb1a103-6657-417a-8143-873dc4a4928d` | 149 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UGI.TIPS.Database |
| UGI.TIPS.Metadata | `1d4101b7-896b-4fd1-8aa9-a7f68952a32e` | 6.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UGI.TIPS.Metadata |
| UGI.TIPS.Reports | `1d4ca847-bfe6-4f8f-baf6-7af2d6418291` | 22.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UGI.TIPS.Reports |
| UTG.TIPS.Database | `533a51d8-6c79-44d2-8898-829c713b40ac` | 56 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTG.TIPS.Database |
| UTG.TIPS.Metadata | `ca7b393a-007b-4801-bf8d-be7639970094` | 39 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTG.TIPS.Metadata |
| UTG.TIPS.Reports | `f64d5ef0-4fba-4f56-9115-82e61e7537e9` | 46.1 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTG.TIPS.Reports |
| VMH.TIPS.Application.QPEC | `41430fc5-d663-4788-9c24-4f4f4ec49a02` | 6.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Application.QPEC |
| VMH.TIPS.ClassicBatch | `618abd14-73ff-4c5d-94a5-9b56fe2d87ff` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.ClassicBatch |
| VMH.TIPS.Database | `de6eca19-6339-4531-881a-50536e7cd8fa` | 592 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Database |
| VMH.TIPS.Metadata | `beff584a-a62d-4dc2-8a20-8cc7af7b805b` | 154 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Metadata |
| VMH.TIPS.Reports | `ebc8c91c-fcd5-44fc-abc0-efe96963f0bf` | 23.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Reports |
| WPC.TIPS.Database | `bf067244-377f-42a9-9f79-cbf3348f8895` | 13 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WPC.TIPS.Database |
| WPC.TIPS.Metadata | `bef963ed-d5f4-44a7-a709-368e6259546e` | 40 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WPC.TIPS.Metadata |
| WPC.TIPS.Reports | `5c3f93b5-38b5-4c82-a326-5c0a0236f0b7` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WPC.TIPS.Reports |
| WTG.TIPS.Application.MiddleTier | `14b708f9-e22a-4cbe-977a-71062ff9d41d` | 2.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Application.MiddleTier |
| WTG.TIPS.Application.QPEC | `24377e00-9d44-4f88-bf34-4a12e17567b4` | 5.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Application.QPEC |
| WTG.TIPS.Application.Web | `0187266e-06b5-49e4-aea5-a02c8093989e` | 61.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Application.Web |
| WTG.TIPS.ClassicBatch | `0e0280a5-f8ee-4098-9667-a1ae8c1bb87c` | 120 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.ClassicBatch |
| WTG.TIPS.Database | `98a322ba-9e86-4408-bb18-94be58c5f0a0` | 99 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Database |
| WTG.TIPS.Metadata | `8a20b27b-51e2-4149-96a9-8361aa3e5d95` | 146 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Metadata |
| WTG.TIPS.Reports | `2cb327cd-1264-4858-8c47-e447593b7f33` | 19.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Reports |
| WTG.TIPS.Web | `f5e9d712-3a0d-483b-a5d1-6b52d6389a4b` | 500 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Web |
| XMG.TIPS.Database | `9c6f2f5e-5b01-41d0-a6ee-10b53f43d944` | 26 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XMG.TIPS.Database |
| XMG.TIPS.Metadata | `ec4ed5fa-5f08-4849-ba22-b793b4114fff` | 5.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XMG.TIPS.Metadata |
| XMG.TIPS.Reports | `468f3012-ef31-4f78-8cfb-7111ae7bbe88` | 18.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XMG.TIPS.Reports |

## 3. EDI / Framework (shared)

6 repositories. Core EDI processing + shared service/test frameworks used by QPTM & TIPS.

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| Quorum.AT.Framework | `741c1649-cbc5-4554-be4a-9242deed6a17` | 4.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.AT.Framework |
| Quorum.EDI.Framework | `02742829-b8c5-4531-bb27-163f9a501621` | 239 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.EDI.Framework |
| Quorum.EDIServ | `30cdad90-e4ae-405c-8d67-747955bcf870` | 20.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.EDIServ |
| Quorum.EDIServ.ReleaseNotes | `b1a0422e-d3d1-4d7b-84cb-050436bff6fd` | 0 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.EDIServ.ReleaseNotes |
| Quorum.PT.Framework | `ee15e146-7f9a-4e49-8dbe-dd68569b4780` | 152 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.PT.Framework |
| Quorum.QFC.ServiceFramework | `5b1e89df-a211-46a5-b217-0c69c5fc4bee` | 600 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QFC.ServiceFramework |

## 4. Core Gas Database Backbone (`Quorum.QGM.*`, `Quorum.QEMS.*`)

32 repositories. QGM/QEMS hold the shared gas-pipeline schema, QCODE/EDI error-code tables, and NAESB message definitions that QPTM rides on. 
Client-prefixed QGM/QEMS repos are grouped under their client in Section 5.

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| Quorum.QEMS.API.Specs | `58f7393e-bbf1-424b-8ca5-6c4986ded5cd` | 130 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.API.Specs |
| Quorum.QEMS.Application.ClassicGUI | `31e61717-3a0f-4415-8cee-44bfd893a1a7` | 130 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Application.ClassicGUI |
| Quorum.QEMS.Application.Listeners | `0e4a08db-2c43-498b-a776-d3994bc69d9d` | 388 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Application.Listeners |
| Quorum.QEMS.Application.MiddleTier | `04a3471b-a4c8-411c-a572-a8d957550965` | 553 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Application.MiddleTier |
| Quorum.QEMS.Application.QPEC | `f0520e58-432f-4695-9014-a8461e0d9dc6` | 415 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Application.QPEC |
| Quorum.QEMS.Application.Web | `0cc437a6-b262-4a14-8186-a95dbe69af30` | 26.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Application.Web |
| Quorum.QEMS.Application.WPF | `57f3caed-73a1-4211-b62e-b8f11d0d8c8a` | 21.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Application.WPF |
| Quorum.QEMS.Batch | `7815367b-fbed-4853-a4f2-3752fb480794` | 703 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Batch |
| Quorum.QEMS.Common | `65d615fb-63b9-4e7c-80b0-66005bfd5e5a` | 6.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Common |
| Quorum.QEMS.Database | `f07741aa-59e8-4095-80e4-070457ce26b3` | 8.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Database |
| Quorum.QEMS.Deprecated | `b7591f83-1533-4f67-8738-3de01e4db109` | 38.6 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Deprecated |
| Quorum.QEMS.Help | `1ab85b06-2c79-4b6e-b56f-a5cc559470d6` | 62.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Help |
| Quorum.QEMS.Listeners | `a55e06d5-9cbe-416b-8f85-e8dd78e0ddb6` | 802 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Listeners |
| Quorum.QEMS.Metadata | `dbe4c43d-991e-4087-bf4c-69ed4aa7999e` | 47.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Metadata |
| Quorum.QEMS.ReleaseNotes | `cbcdfe98-bbf4-4176-bfef-a45f740c809c` | 182 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.ReleaseNotes |
| Quorum.QEMS.Reports | `c0e90b1c-eec2-44af-b5de-7d46d89c2afb` | 6.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Reports |
| Quorum.QEMS.Services | `b0999b63-9e9a-4b4e-a86f-659279e292d1` | 25.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Services |
| Quorum.QEMS.Web | `6b08db02-4531-4896-bc11-ee7a602bb5b7` | 26.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.Web |
| Quorum.QEMS.WPF | `6cd62478-9364-459c-92a9-c38dc2e94d18` | 2.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QEMS.WPF |
| Quorum.QGM.Application.ClassicGUI | `4a51abf9-6e87-4e68-a52c-e35d81aa4a4e` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Application.ClassicGUI |
| Quorum.QGM.Application.MiddleTier | `a9f94a14-0f9e-4d63-986b-583fa3331a7d` | 141 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Application.MiddleTier |
| Quorum.QGM.Application.QPEC | `19cbe09e-7dc3-47bb-b76e-975cac0ab266` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Application.QPEC |
| Quorum.QGM.Batch | `f6a6c380-ed74-4860-835b-d58c462c3e9f` | 3.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Batch |
| Quorum.QGM.ClassicBatch | `9add0df8-b39c-4149-8b4b-a50c3478c0a1` | 4.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.ClassicBatch |
| Quorum.QGM.ClassicBatch.QGMSharedLib | `313fd9c9-695e-4d93-83a0-706f5c4bf08b` | 4.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.ClassicBatch.QGMSharedLib |
| Quorum.QGM.ClassicGUI | `d440727e-280d-4b2b-b854-c2cdf058ab34` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.ClassicGUI |
| Quorum.QGM.Database | `8bfba59c-f3dd-46ea-8d0a-f2687a763258` | 2.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Database |
| Quorum.QGM.Help | `3ef9f957-d87c-45e1-8959-8f93cbc587d8` | 16.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Help |
| Quorum.QGM.Metadata | `ca8b9fc9-4692-4b56-b79b-6cf1a3438f1f` | 62.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Metadata |
| Quorum.QGM.ReleaseNotes | `b5ea511d-24a7-461e-b6c0-96f3b2648578` | 140 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.ReleaseNotes |
| Quorum.QGM.Reports | `aa0b4a2d-1a10-4939-83a1-ea1f6f15ba02` | 10.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Reports |
| Quorum.QGM.Web | `c88efb06-448a-4957-a332-8748442732cf` | 382 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Quorum.QGM.Web |

## 5. Client-Prefixed Repos (grouped by client code)

124 distinct client codes spanning QPTM, TIPS, QGM, and QEMS product families. 
Each client may carry Web / Application.* / Batch / ClassicBatch / ClassicGUI / Database / Metadata / Reports overrides.

### EQT  (16 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EQT.QPTM.Application.MiddleTier | `9d67f45c-b344-4735-ba48-76eb1d97be9e` | 316 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Application.MiddleTier |
| EQT.QPTM.Application.QPEC | `463a8b03-38f9-45b4-823d-e72065400471` | 271 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Application.QPEC |
| EQT.QPTM.Application.Web | `2b914517-e219-4371-93da-95d2dce8c097` | 29.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Application.Web |
| EQT.QPTM.ClassicBatch | `0c62692c-f66b-4f15-9d7c-d53fed6af0e5` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.ClassicBatch |
| EQT.QPTM.Database | `ba49f3c7-fca0-47ff-87c8-bb5805128f29` | 44 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Database |
| EQT.QPTM.Metadata | `9a588432-ca22-47d9-b925-bff6f7025550` | 11.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Metadata |
| EQT.QPTM.Reports | `92bdfe07-46d0-41fc-be8f-ef82d6dabb42` | 14.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Reports |
| EQT.QPTM.Web | `f29cf1be-dcaa-45ec-b721-dc4a5f06bfa8` | 9.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.QPTM.Web |
| EQT.TIPS.Application.MiddleTier | `3eb4a8e5-ac53-4492-a1d8-13933685d991` | 669 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Application.MiddleTier |
| EQT.TIPS.Application.QPEC | `6ca8fb54-cc63-4be5-b938-3d7c6295525f` | 237 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Application.QPEC |
| EQT.TIPS.Application.Web | `90843511-0a46-4a10-9cd9-6422c28fbf68` | 25.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Application.Web |
| EQT.TIPS.ClassicBatch | `beecb4da-a196-48a6-9d6a-d0b8dc061d0b` | 78 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.ClassicBatch |
| EQT.TIPS.Database | `1641f9c1-3079-4747-9bea-c8cb44180fdc` | 81 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Database |
| EQT.TIPS.Metadata | `07a49083-c5d6-433c-9866-0b38d99a9f4e` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Metadata |
| EQT.TIPS.Reports | `209a301f-d987-4f8e-b7e7-c843b31c8998` | 15.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Reports |
| EQT.TIPS.Web | `340c7b09-2f4c-475d-8bb1-202b6d19a355` | 825 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQT.TIPS.Web |

### ENT  (19 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ENT.QPTM.Application.ClassicGUI | `99a9135c-762b-4296-947a-a4343c4538ce` | 52.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Application.ClassicGUI |
| ENT.QPTM.Application.ClassicGUICAW | `b8833bdb-4d8d-40ce-8f22-7d2e8ce539a8` | 718 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Application.ClassicGUICAW |
| ENT.QPTM.Application.MiddleTier | `ada8431e-3085-498f-b7d9-e024d530c468` | 851 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Application.MiddleTier |
| ENT.QPTM.Application.QPEC | `48057066-c291-4676-aacd-55d7e4ccd55e` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Application.QPEC |
| ENT.QPTM.Application.Web | `59cef753-1d4d-456f-a526-18da757e3212` | 87.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Application.Web |
| ENT.QPTM.Batch | `16d42ed9-1ffc-4fe8-9402-446d3778edf4` | 401 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Batch |
| ENT.QPTM.ClassicBatch | `3be6f2b9-48fc-4999-b873-a37a0cce97ac` | 613 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.ClassicBatch |
| ENT.QPTM.ClassicGUI | `b0dc7780-399e-4864-a33a-d50bf5d9e0d5` | 107 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.ClassicGUI |
| ENT.QPTM.Database | `02054e0d-633f-4989-ac0e-9911861961f9` | 770 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Database |
| ENT.QPTM.Metadata | `248b68c4-4f49-453b-9d32-10708d98a46d` | 11.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Metadata |
| ENT.QPTM.Reports | `8d2c526d-b41c-4fc2-a6d7-d629c2f81f41` | 41.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Reports |
| ENT.QPTM.Web | `12e21544-0649-4b2d-b4a0-27a63ccf6eea` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.QPTM.Web |
| ENT.TIPS.Application.QPEC | `85fec4e2-ea80-4775-a369-fbe6e834c877` | 1.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Application.QPEC |
| ENT.TIPS.Batch | `a1bfc0c6-6ee2-4e0b-b57e-6c4960106437` | 408 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Batch |
| ENT.TIPS.ClassicBatch | `e9010747-4b9d-4061-bde2-66b3b1ba685d` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.ClassicBatch |
| ENT.TIPS.Database | `8b1edc20-c380-4b2a-8186-8fa8f5d95f7a` | 315 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Database |
| ENT.TIPS.Metadata | `57bd4096-e9b9-47c0-a5b5-528f85a87dda` | 12.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Metadata |
| ENT.TIPS.Reports | `84244722-01d7-45bb-8181-fab6e7b4cf6e` | 65.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Reports |
| ENT.TIPS.Web | `86495096-f878-4dc5-be3c-483f24c58a49` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ENT.TIPS.Web |

### DUT  (11 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DUT.QPTM.Application.ClassicGUI | `4a13c597-fd86-4cac-9156-7e9f1b90e728` | 52.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Application.ClassicGUI |
| DUT.QPTM.Application.MiddleTier | `780cca15-8a81-46d7-9d0f-1e683f6d61bd` | 2.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Application.MiddleTier |
| DUT.QPTM.Application.QPEC | `e76060bf-af47-4968-84f7-f6dde8f6cfd4` | 3.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Application.QPEC |
| DUT.QPTM.Application.Web | `9421e385-eb7b-4923-8e1d-e4bd9fba6e16` | 64.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Application.Web |
| DUT.QPTM.Batch | `600c1938-8b68-41da-b1e7-9875c2a8471f` | 32 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Batch |
| DUT.QPTM.ClassicBatch | `49075dbf-1e59-425b-a0a6-9540b120d21f` | 344 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.ClassicBatch |
| DUT.QPTM.ClassicGUI | `a261ac5b-5590-4713-a4a4-ecf86856b55d` | 190 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.ClassicGUI |
| DUT.QPTM.Database | `c8589ced-cc66-4b6d-bb4d-c67f0c1139dc` | 47 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Database |
| DUT.QPTM.Metadata | `27f137d9-22d9-440a-be9d-5f16872a1bd8` | 176 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Metadata |
| DUT.QPTM.Reports | `3146bdda-36e8-4926-bd7f-e38df1737162` | 15.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Reports |
| DUT.QPTM.Web | `58c3259a-05f9-4dec-919a-4c4b4f672514` | 854 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DUT.QPTM.Web |

### NMGC  (14 repos — families: QEMS, QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| NMGC.QEMS.Database | `024deb60-6612-4b68-ae19-286e508128f0` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QEMS.Database |
| NMGC.QEMS.Metadata | `e368fb6a-3f02-447c-9a6b-80d94a99bea5` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QEMS.Metadata |
| NMGC.QEMS.Reports | `bbd72ef5-9ab8-46e3-b568-9c2150722986` | 2.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QEMS.Reports |
| NMGC.QGM.Database | `33d21181-b4ac-4e1a-b465-ba912322935e` | 15 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QGM.Database |
| NMGC.QGM.Metadata | `debb20f0-a16a-4fe7-a755-5753269fe3bf` | 4.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QGM.Metadata |
| NMGC.QGM.Reports | `21d08ca7-840b-4a9e-99b3-ff4eef15a972` | 4.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QGM.Reports |
| NMGC.QPTM.Application.MiddleTier | `d297c88a-65e9-4c13-aa4b-1aaf06521201` | 3.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Application.MiddleTier |
| NMGC.QPTM.Application.QPEC | `a6a2ef90-344f-4eef-9e0f-ec325160293e` | 4.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Application.QPEC |
| NMGC.QPTM.Application.Web | `22539997-f175-4489-9897-04618e85ca4b` | 65.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Application.Web |
| NMGC.QPTM.ClassicBatch | `241d43e4-2ba9-4603-8f5a-5601ae17df20` | 87 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.ClassicBatch |
| NMGC.QPTM.Database | `d7f222bd-44f6-4287-b6cd-1752ffa910aa` | 31 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Database |
| NMGC.QPTM.Metadata | `69d0ec23-7729-455a-8c29-4943c2ff5433` | 6.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Metadata |
| NMGC.QPTM.Reports | `30953b2b-45b3-4997-92f9-51f5e948ba7c` | 14.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Reports |
| NMGC.QPTM.Web | `118b3c20-04ad-436f-a20a-36b39b1f9e87` | 233 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMGC.QPTM.Web |

### NMG  (14 repos — families: QEMS, QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| NMG.QEMS.Database | `1e16416f-c5b8-4841-be46-af0eaf692dca` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QEMS.Database |
| NMG.QEMS.Metadata | `6767974c-29e2-4555-90cd-14f6fbd9de88` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QEMS.Metadata |
| NMG.QEMS.Reports | `c370a442-e2b5-4b30-9f39-88d26b804d69` | 2.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QEMS.Reports |
| NMG.QGM.Database | `f3548529-f79d-4a4f-8f5c-5561da77d5cd` | 104 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QGM.Database |
| NMG.QGM.Metadata | `f989417f-5d85-4db2-9c2a-b0b1d7e030bb` | 4.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QGM.Metadata |
| NMG.QGM.Reports | `cbbfa776-59a1-41b0-997b-dd4e41bf34ae` | 8.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QGM.Reports |
| NMG.QPTM.Application.MiddleTier | `804a27c3-c9fa-4d61-9fce-a789f6ad9878` | 489 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Application.MiddleTier |
| NMG.QPTM.Application.QPEC | `23fed63c-e27a-4532-a180-7270e009d661` | 317 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Application.QPEC |
| NMG.QPTM.Application.Web | `ef76d632-350d-43e4-8108-11e7a4b4cb5c` | 62.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Application.Web |
| NMG.QPTM.ClassicBatch | `4042b3f0-64ae-4151-8d5b-342384ba5ef9` | 143 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.ClassicBatch |
| NMG.QPTM.Database | `4d0a41dc-4ba4-4b1e-b488-67dad708c631` | 168 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Database |
| NMG.QPTM.Metadata | `de026f4b-cd42-4639-a41c-8ee5997799f7` | 6.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Metadata |
| NMG.QPTM.Reports | `df5bbfe9-e8f1-412b-8c5e-c5435b12a8b3` | 28.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Reports |
| NMG.QPTM.Web | `c7e7e19f-9fab-40d9-ae28-a247321a9647` | 270 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NMG.QPTM.Web |

### DOH  (9 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DOH.QPTM.Application.MiddleTier | `333f8d5e-0865-465b-a9fa-60d331addf52` | 1.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Application.MiddleTier |
| DOH.QPTM.Application.QPEC | `4a2ff8ab-ff18-49e4-a1b0-cb27c2f79617` | 2.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Application.QPEC |
| DOH.QPTM.Application.Web | `1f63ef82-bb48-4bd4-97bd-eb894faa17a3` | 55.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Application.Web |
| DOH.QPTM.AT | `fca5f58c-2aa0-43ea-9728-9e14e658bd0d` | 12.2 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.AT |
| DOH.QPTM.Batch | `3e703b68-2b6f-416c-82a7-cafe33d70780` | 651 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Batch |
| DOH.QPTM.Database | `0f640045-180d-4ac4-9af5-6957d06c8a89` | 134 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Database |
| DOH.QPTM.Metadata | `3449d7dd-b11e-464a-bff4-cb974c6e18db` | 250 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Metadata |
| DOH.QPTM.Reports | `29c9d566-11d4-463c-b58e-28c3ac82c376` | 14.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Reports |
| DOH.QPTM.Web | `0f6acd2e-ac51-41b9-b9be-d88dfa8e38be` | 2.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DOH.QPTM.Web |

### DRS  (9 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DRS.QPTM.Application.MiddleTier | `c5193178-5d2d-48e8-adf5-e87566a73ed4` | 1.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Application.MiddleTier |
| DRS.QPTM.Application.QPEC | `53878e18-6282-4844-af1b-f2b0320813c8` | 2.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Application.QPEC |
| DRS.QPTM.Application.Web | `595e318d-5121-405b-955d-ad53824c51c6` | 55.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Application.Web |
| DRS.QPTM.AT | `b930b788-bf4a-4eb2-8c7c-dfd2003ba2ed` | 12.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.AT |
| DRS.QPTM.Batch | `bcf16524-d2b4-484f-8a28-b8ec6f1b4363` | 456 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Batch |
| DRS.QPTM.Database | `60920384-97c2-4635-8009-494466c13ebe` | 94 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Database |
| DRS.QPTM.Metadata | `1efef699-1265-44d2-9789-7b22b1ace5ff` | 173 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Metadata |
| DRS.QPTM.Reports | `89371a4a-0172-458c-9a60-d3f10bde3e81` | 14.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Reports |
| DRS.QPTM.Web | `a6968e36-8ecf-4107-b9f0-cf2778ef2dd1` | 7.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DRS.QPTM.Web |

### ONG  (14 repos — families: QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ONG.QGM.Application.QPEC | `95d55f8e-10c9-430e-9ec1-ed6329f05c24` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QGM.Application.QPEC |
| ONG.QGM.ClassicBatch | `f4b97324-9491-4946-933f-e3861f69ed24` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QGM.ClassicBatch |
| ONG.QGM.Database | `576daa79-66cf-4a17-b118-8ae2741b1c77` | 47 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QGM.Database |
| ONG.QGM.Metadata | `69fb8fc6-6c2e-4cae-a269-0cd784d80aa2` | 36 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QGM.Metadata |
| ONG.QGM.Reports | `d6c4438c-ef41-4541-bf4a-acc15ec5f381` | 6.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QGM.Reports |
| ONG.QPTM.Application.MiddleTier | `446b90c8-459a-4c43-a590-c04acf3ca91b` | 862 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Application.MiddleTier |
| ONG.QPTM.Application.QPEC | `fe4e478e-c959-452f-99e6-bcd66d2e8e4e` | 866 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Application.QPEC |
| ONG.QPTM.Application.Web | `3ce10c47-e2d8-4a36-8b00-bd279b013c44` | 52.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Application.Web |
| ONG.QPTM.Batch | `1c9e3e41-2569-4f3a-8aa6-2eaa8cf7fa65` | 115 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Batch |
| ONG.QPTM.ClassicBatch | `c4bebab6-a2f6-4cd0-b0fb-a1537c342648` | 80 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.ClassicBatch |
| ONG.QPTM.Database | `5ca508fb-463f-4285-b924-629daaf6f6d1` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Database |
| ONG.QPTM.Metadata | `d0909425-4788-4649-a1fa-9aae6238c7f2` | 43.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Metadata |
| ONG.QPTM.Reports | `d1001e32-6017-4876-9f46-25ad948c9c38` | 27.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Reports |
| ONG.QPTM.Web | `54c52e8d-de64-4386-805c-fc0f654c2961` | 967 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONG.QPTM.Web |

### ONK  (8 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ONK.QPTM.Application.MiddleTier | `bb7f8774-b41f-4ea0-825a-6bb5e78721c3` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Application.MiddleTier |
| ONK.QPTM.Application.QPEC | `0e2ed28d-d105-4195-864d-4be31eafaa0d` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Application.QPEC |
| ONK.QPTM.Application.Web | `fbea7607-078e-42bf-aa7d-9a919b5e25e1` | 48.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Application.Web |
| ONK.QPTM.Batch | `71411864-5e3c-4dcd-bb4e-78975371d75c` | 162 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Batch |
| ONK.QPTM.Database | `e0f2e587-3043-4dc3-986a-b04209cf588f` | 284 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Database |
| ONK.QPTM.Metadata | `9c22f188-4f0b-41b4-a35c-c96af44ef66a` | 144.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Metadata |
| ONK.QPTM.Reports | `8f3fbafd-8b20-41b1-a333-32c7d32a652a` | 19.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Reports |
| ONK.QPTM.Web | `59eda16f-9765-40f5-b46f-a55ff76407c4` | 10.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONK.QPTM.Web |

### QTR  (12 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| QTR.QPTM.Application.ClassicGUI | `a247311b-71d7-42a1-b1d5-7fc1d8274cc1` | 64.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Application.ClassicGUI |
| QTR.QPTM.Application.ClassicGUICAW | `5d76d572-bbac-4953-9fff-a910d441fcd0` | 918 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Application.ClassicGUICAW |
| QTR.QPTM.Application.MiddleTier | `a9b5c9fb-6140-4ee7-b323-9374f2724d53` | 2.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Application.MiddleTier |
| QTR.QPTM.Application.QPEC | `7496dd2c-8d0d-47fd-a72d-5eed574a4abf` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Application.QPEC |
| QTR.QPTM.Application.Web | `4579d3b0-fe55-4dc9-8954-54c452ba8241` | 71.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Application.Web |
| QTR.QPTM.Batch | `4c0d4e0a-c925-403d-94bb-6890d11c29bc` | 121 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Batch |
| QTR.QPTM.ClassicBatch | `dbffe94d-1748-45c4-aaa1-9f60d780efcf` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.ClassicBatch |
| QTR.QPTM.ClassicGUI | `8354979d-3131-417d-82bb-307dfd070417` | 747 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.ClassicGUI |
| QTR.QPTM.Database | `fb50860a-81f0-4354-92fb-2037268c3563` | 170 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Database |
| QTR.QPTM.Metadata | `c1a160cf-ce38-4c30-a7a3-2ebebeab1db4` | 7.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Metadata |
| QTR.QPTM.Reports | `050b25c6-6ce5-43f2-a865-2b21d119cb9b` | 31.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Reports |
| QTR.QPTM.Web | `f88e203c-e566-46d5-a868-8f714bc01b19` | 1.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QTR.QPTM.Web |

### ACL  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ACL.TIPS.Application.QPEC | `417cbfe3-764c-432a-9dc6-9caf5e6a0f75` | 5.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Application.QPEC |
| ACL.TIPS.ClassicBatch | `e5d984fe-2615-4c85-98bd-fdbb3d7aa1ad` | 125 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.ClassicBatch |
| ACL.TIPS.Database | `0f691c97-901e-49bb-b95e-f9106e6d9d04` | 174 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Database |
| ACL.TIPS.Metadata | `7acd0c60-5a5e-47a3-a2a4-763b66ab2e77` | 326 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Metadata |
| ACL.TIPS.Reports | `5f34d474-cd8c-4bc1-b172-2eaf33c8da02` | 46.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACL.TIPS.Reports |

### ACP  (13 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ACP.TIPS.Application.QPEC | `668797dd-6950-4134-8c29-044295efc4b2` | 694 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Application.QPEC |
| ACP.TIPS.Batch | `76dc3d78-d26a-4371-94f5-0ad1d4d66dc8` | 254 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Batch |
| ACP.TIPS.ClassicBatch | `c02ce310-4ef9-4d73-99eb-e4c50d96fab6` | 22 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.ClassicBatch |
| ACP.TIPS.ClassicGUI | `7ca39d2d-b924-439d-865c-0afe28a66348` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.ClassicGUI |
| ACP.TIPS.Crude.Application.MiddleTier | `0e5b1988-d490-4fef-a63c-66359e7b6056` | 196 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Crude.Application.MiddleTier |
| ACP.TIPS.Crude.Application.QPEC | `d5956f5d-1dfb-43b0-9a9c-a964d72fee33` | 243 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Crude.Application.QPEC |
| ACP.TIPS.Crude.Application.Web | `16f02a10-bf3e-469e-9edf-96f096e42332` | 16.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Crude.Application.Web |
| ACP.TIPS.CrudeCommon.Batch | `411cfa37-dc69-404a-a486-3d31b3f11795` | 12 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.CrudeCommon.Batch |
| ACP.TIPS.CrudeCommon.Web | `5234271a-61dd-482a-a1e7-18f4e5284674` | 224 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.CrudeCommon.Web |
| ACP.TIPS.Database | `4fb64249-0e05-4e90-9291-a91eb4e8604d` | 42 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Database |
| ACP.TIPS.Metadata | `55135c2a-8bee-4ae4-8056-56f66d0939b7` | 8.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Metadata |
| ACP.TIPS.Reports | `bf8d59bc-8536-4d1c-9d17-f25fbda20ec5` | 14.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Reports |
| ACP.TIPS.Web | `86f2c59b-1931-4e57-9159-974400d912a4` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ACP.TIPS.Web |

### DCP  (13 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DCP.QPTM.Database | `86b379c5-aa91-4b33-8af4-aa1bbac76ea4` | 53 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.QPTM.Database |
| DCP.QPTM.Metadata | `049ba36a-743f-47b8-a3fc-8bbe41f869e2` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.QPTM.Metadata |
| DCP.TIPS.Application.ClassicGUI | `fa26396e-fd32-4474-83f6-552929547563` | 652 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.ClassicGUI |
| DCP.TIPS.Application.MiddleTier | `e0aa6862-7b8c-4e4c-a125-a68331688c61` | 504 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.MiddleTier |
| DCP.TIPS.Application.QPEC | `ca4e8169-78c7-4775-b6bf-f4035ec631a9` | 810 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.QPEC |
| DCP.TIPS.Application.Web | `d8412bed-416a-4d21-a3d2-a1c5beb18e0c` | 31.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Application.Web |
| DCP.TIPS.Batch | `c963e1df-935d-4892-8b6c-48a0cbabf0cc` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Batch |
| DCP.TIPS.ClassicBatch | `eb54f1a3-52f5-4b1c-92b4-00b1feba535f` | 4.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.ClassicBatch |
| DCP.TIPS.ClassicGUI | `36cf4c9a-a2cd-4ba2-a4da-c6eb0f723207` | 339 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.ClassicGUI |
| DCP.TIPS.Database | `5698ced4-8d65-4ca7-9533-47732abedf3c` | 788 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Database |
| DCP.TIPS.Metadata | `b9190fb4-a453-4b98-86ab-0a9bfec7843b` | 48.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Metadata |
| DCP.TIPS.Reports | `671a3f6d-ce43-4fbd-b2af-16bc7fa72c9e` | 107.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Reports |
| DCP.TIPS.Web | `a66f8a18-3dfc-401d-8225-3c47e1b01b9e` | 626 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DCP.TIPS.Web |

### DTE  (19 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DTE.QPTM.Application.ClassicGUI | `0d604912-e0bc-4b79-bf98-65b5ac3dca04` | 50.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Application.ClassicGUI |
| DTE.QPTM.Application.ClassicGUICAW | `c710bec4-d05d-4e86-ab85-bee6d4b078ef` | 394 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Application.ClassicGUICAW |
| DTE.QPTM.Application.MiddleTier | `255d006f-f524-478d-91a1-8f084f379ab9` | 718 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Application.MiddleTier |
| DTE.QPTM.Application.QPEC | `7a011834-764d-4a90-a970-ecb061b136f4` | 620 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Application.QPEC |
| DTE.QPTM.Application.Web | `1f09abf5-bc1b-4b79-9aac-cf6450add185` | 53.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Application.Web |
| DTE.QPTM.ClassicBatch | `3b356fe7-77be-46bb-b43d-6d80bbd99c5e` | 728 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.ClassicBatch |
| DTE.QPTM.ClassicGUI | `a8fe4b56-fc49-467b-8214-39d182e6365f` | 105 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.ClassicGUI |
| DTE.QPTM.Database | `a4b08149-b108-4eec-9cae-937df72a38fa` | 104 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Database |
| DTE.QPTM.Metadata | `d685b82e-02c3-48c7-b2d2-948a05121b6c` | 20.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Metadata |
| DTE.QPTM.Reports | `6f71b361-3c95-4048-9a9d-bad16144b696` | 37.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Reports |
| DTE.QPTM.Web | `eeebc0a6-73a5-4d48-8e8b-c38e9f5e9510` | 13.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.QPTM.Web |
| DTE.TIPS.Application.MiddleTier | `8b30c863-46ab-4a3b-a6ce-13c76812ce75` | 458 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Application.MiddleTier |
| DTE.TIPS.Application.QPEC | `89a3ca8d-6e47-4df5-bf3c-ea1bba2e6207` | 583 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Application.QPEC |
| DTE.TIPS.Application.Web | `e429f3ba-2a48-42a4-9396-884825aba61f` | 35.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Application.Web |
| DTE.TIPS.ClassicBatch | `a4e3f4ec-9d83-4bdf-9d9e-390a35fe52c6` | 173 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.ClassicBatch |
| DTE.TIPS.Database | `34cfee41-8c69-4192-b2a8-0f5b8010efcb` | 421 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Database |
| DTE.TIPS.Metadata | `c0ae54c6-5c8c-4e68-ac2b-88b5f8309726` | 2.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Metadata |
| DTE.TIPS.Reports | `be65eeda-cc34-4831-8175-7c411fdac3b6` | 37.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Reports |
| DTE.TIPS.Web | `64864a86-bce8-4fe4-847d-7f047c4e7f95` | 707 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTE.TIPS.Web |

### DTM  (8 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DTM.TIPS.Application.MiddleTier | `398fb3e2-c450-4957-a6f2-83e04a9fd857` | 1.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Application.MiddleTier |
| DTM.TIPS.Application.QPEC | `e50c0d43-1a29-49ba-94f5-9e4782235584` | 3.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Application.QPEC |
| DTM.TIPS.Application.Web | `2b2c1495-470d-4012-8afd-e4fa5302dfac` | 50.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Application.Web |
| DTM.TIPS.ClassicBatch | `ad183215-a10a-46ec-b486-c134b3065a63` | 376 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.ClassicBatch |
| DTM.TIPS.Database | `9b936e7b-9ac3-42e4-9133-04c8795cc998` | 103 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Database |
| DTM.TIPS.Metadata | `7f3bcb6c-8cdc-4076-b1c5-19dc7ca8821b` | 126 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Metadata |
| DTM.TIPS.Reports | `7c542086-04c8-4ffb-91b1-dac2342cced7` | 18.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Reports |
| DTM.TIPS.Web | `84002827-69f3-48de-866b-61cbaef37b52` | 568 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DTM.TIPS.Web |

### ETP  (9 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ETP.TIPS.Application.MiddleTier | `57d6df92-244a-439e-bd1b-c99c01bd7511` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Application.MiddleTier |
| ETP.TIPS.Application.QPEC | `3c8000ef-2ac0-4d89-9efc-f37d0ac3d25c` | 3.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Application.QPEC |
| ETP.TIPS.Application.Web | `829f3069-2be1-4516-97f2-6ae4071a9e4b` | 56.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Application.Web |
| ETP.TIPS.Batch | `40a812a4-2fcb-4a17-8b64-f563b940cfcb` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Batch |
| ETP.TIPS.ClassicBatch | `756915be-e373-4c61-831b-38dd94558c55` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.ClassicBatch |
| ETP.TIPS.Database | `732844c0-ef92-427a-9a93-e3d01a91d69e` | 523 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Database |
| ETP.TIPS.Metadata | `7a35b308-42aa-4451-8164-789ba4c6ed06` | 26.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Metadata |
| ETP.TIPS.Reports | `951dc268-0ccb-42a5-9214-2a8974f5f1de` | 51.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Reports |
| ETP.TIPS.Web | `3d6ae1d3-01bd-49cb-83c5-234861abbca6` | 599 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETP.TIPS.Web |

### EQC  (20 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EQC.QPTM.Application.MiddleTier | `1a670cde-b72a-4689-9dcf-92ee042a9843` | 3.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.Application.MiddleTier |
| EQC.QPTM.Application.QPEC | `840ddada-aa30-4af0-ae2a-0746a56a2e17` | 5.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.Application.QPEC |
| EQC.QPTM.ClassicBatch | `0770c776-c29f-4702-882b-e9484b032ad4` | 69 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.ClassicBatch |
| EQC.QPTM.Database | `e9d59374-3c65-4ade-983d-612ba4c3bf9a` | 111 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.Database |
| EQC.QPTM.Metadata | `73bc93e8-4c77-4145-8c17-94ff47c2c5cc` | 315 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.Metadata |
| EQC.QPTM.Reports | `e6676aa0-ef85-48fe-9ebd-3fd7a3f15b2f` | 24.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.Reports |
| EQC.QPTM.Web | `268f0c2e-844d-4a97-aace-ac3189a9dec1` | 358 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.QPTM.Web |
| EQC.TIPS.API | `fd4a272c-6a61-4283-a749-eeb13a5d556c` | 120 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.API |
| EQC.TIPS.API.Specs | `81e784d3-9105-4644-b158-0dbb90f2e47f` | 2.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.API.Specs |
| EQC.TIPS.Application.ClassicGUI | `8c207325-fc64-4c86-a1b0-1ffa55e337b0` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.ClassicGUI |
| EQC.TIPS.Application.MiddleTier | `7604f471-f834-4e20-b755-59dd404266c6` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.MiddleTier |
| EQC.TIPS.Application.QPEC | `b4a384c9-dc87-4588-ba30-cb203ea8f075` | 2.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.QPEC |
| EQC.TIPS.Application.Web | `a1f78e5d-eb8d-4f22-8954-c11fcff8d8aa` | 55.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Application.Web |
| EQC.TIPS.Batch | `7c44c133-8838-494f-9937-e448e6c39e93` | 20 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Batch |
| EQC.TIPS.ClassicBatch | `bda03b52-6a82-4f85-b38b-5f79fc41cae7` | 83 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.ClassicBatch |
| EQC.TIPS.ClassicGUI | `da7927a4-8e0f-4a60-af5a-1062f749cb82` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.ClassicGUI |
| EQC.TIPS.Database | `1c916ee6-e791-4ae3-8e05-6bdbecf49beb` | 297 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Database |
| EQC.TIPS.Metadata | `9e64727f-1918-45e2-b871-0c7208cbc1d1` | 415 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Metadata |
| EQC.TIPS.Reports | `f7465311-9d26-422c-8396-d72db11c1097` | 39.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Reports |
| EQC.TIPS.Web | `137d2c25-4e55-478c-8533-0fb4b54f1826` | 457 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EQC.TIPS.Web |

### EMP  (11 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EMP.TIPS.Application.ClassicGUI | `bc4910e7-6d26-4ea4-aa93-f81630ca0edf` | 256 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.ClassicGUI |
| EMP.TIPS.Application.MiddleTier | `11c701ac-b385-42eb-a25b-3a43e5bf8f96` | 272 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.MiddleTier |
| EMP.TIPS.Application.QPEC | `62cce34c-7a89-4765-afdf-58b0a6a02da8` | 357 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.QPEC |
| EMP.TIPS.Application.Web | `d2ce2b93-d164-4627-95ae-c300127a539b` | 23.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Application.Web |
| EMP.TIPS.Batch | `4741fd1b-4efa-4bbb-94a4-80b59bafe4af` | 34 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Batch |
| EMP.TIPS.ClassicBatch | `29b85a5a-51a6-4715-9a60-b463e9019814` | 17.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.ClassicBatch |
| EMP.TIPS.ClassicGUI | `a42c204a-eafe-44b6-88f2-5e73a3ec8923` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.ClassicGUI |
| EMP.TIPS.Database | `f801ad5f-b11a-4f23-b49e-128bfe907e12` | 527 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Database |
| EMP.TIPS.Metadata | `9c3fd19b-b975-487b-ba4d-ac7dced55c38` | 23.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Metadata |
| EMP.TIPS.Reports | `7affad29-d217-4a57-958c-089bad66e9a9` | 14.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Reports |
| EMP.TIPS.Web | `87c957a7-6d20-4c27-a67c-c9b88cc62803` | 747 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMP.TIPS.Web |

### ONM  (8 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ONM.TIPS.Application.MiddleTier | `801b49be-e35f-429d-bc1b-3f48b2abe90e` | 1016 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Application.MiddleTier |
| ONM.TIPS.Application.QPEC | `5b8d6efe-ae2f-4fd2-8816-def487d45c1a` | 940 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Application.QPEC |
| ONM.TIPS.Application.Web | `90a0ba07-2873-423c-aed3-417c405fd30a` | 34.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Application.Web |
| ONM.TIPS.ClassicBatch | `91497497-6020-4448-bdc7-83cabce729af` | 373 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.ClassicBatch |
| ONM.TIPS.Database | `3d9692e2-5b57-437b-89ef-8b0e126b5a7a` | 724 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Database |
| ONM.TIPS.Metadata | `54a61637-084c-43aa-a7e3-afb3a943e32f` | 47.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Metadata |
| ONM.TIPS.Reports | `f1852bec-8e10-475c-b24c-3476be70976b` | 35.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Reports |
| ONM.TIPS.Web | `a9ddebe9-0807-439c-b390-ddb5348c1d96` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONM.TIPS.Web |

### AER  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| AER.TIPS.Database | `2fc36149-7342-4905-b8ee-c57be20fd5c6` | 1.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AER.TIPS.Database |
| AER.TIPS.Metadata | `b7b8638b-73f2-4c09-9355-e2cfa48cb43f` | 6.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AER.TIPS.Metadata |
| AER.TIPS.Reports | `ca7b5ed9-a8ba-4284-a150-bef2a4dcba64` | 11.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AER.TIPS.Reports |

### AHS  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| AHS.TIPS.Application.QPEC | `60064159-0b03-4fb2-8863-191bf4742975` | 360 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Application.QPEC |
| AHS.TIPS.ClassicBatch | `978987e2-8aaf-4d57-9f53-4b36143d8d4a` | 286 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.ClassicBatch |
| AHS.TIPS.Database | `cee5c476-5feb-4a99-b132-5016b56cc13d` | 443 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Database |
| AHS.TIPS.Metadata | `7c4a5aad-a2c7-4c67-9c64-40b990667da3` | 17.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Metadata |
| AHS.TIPS.Reports | `9e642263-7272-4021-8d10-f482d3e2b890` | 46.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AHS.TIPS.Reports |

### ALT  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ALT.TIPS.Application.QPEC | `bacf6af7-2535-4f3a-bdac-6d9fd85ae259` | 4.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Application.QPEC |
| ALT.TIPS.ClassicBatch | `492948c4-7518-4f40-8a2b-09ea86a991c5` | 740 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.ClassicBatch |
| ALT.TIPS.Database | `0fd00a69-982e-45ec-a4df-d526f8151712` | 156 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Database |
| ALT.TIPS.Metadata | `9c58ff24-e1fb-4307-8988-bbf6b19c7894` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Metadata |
| ALT.TIPS.Reports | `2c27ddb4-09e4-4429-a585-c218fb6a9625` | 35.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ALT.TIPS.Reports |

### AMM  (6 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| AMM.TIPS.Application.QPEC | `22073bee-38ca-41a9-924c-0407cefd191f` | 956 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Application.QPEC |
| AMM.TIPS.Batch | `2b5ec220-f04c-4591-9862-9cf01c4dd434` | 12 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Batch |
| AMM.TIPS.ClassicBatch | `6b44e891-2dfd-4fab-befe-b94706bc5aaa` | 51 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.ClassicBatch |
| AMM.TIPS.Database | `ccfff629-515e-4cd8-b35c-1fe0e02ad7df` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Database |
| AMM.TIPS.Metadata | `d12f3561-6c55-4c20-9acc-e8631c5a72a8` | 7 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Metadata |
| AMM.TIPS.Reports | `dc928e9b-06dd-4bf1-8ff6-a3abce36f088` | 11.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AMM.TIPS.Reports |

### ARM  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ARM.TIPS.Database | `25ac9466-38c1-49ec-8ad6-0e08c3133810` | 46 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ARM.TIPS.Database |
| ARM.TIPS.Metadata | `353f263f-d7e9-46d3-baba-93aeb53272ed` | 32 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ARM.TIPS.Metadata |
| ARM.TIPS.Reports | `3309dc98-24c8-4f6d-a86f-2b81092abfa8` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ARM.TIPS.Reports |

### AZR  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| AZR.TIPS.Database | `2cd1e8e4-560e-49ea-8e5f-abb5c41ac195` | 368 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AZR.TIPS.Database |
| AZR.TIPS.Metadata | `30ee6967-7e5e-4fa6-8e01-dd4f7a2654bb` | 200 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AZR.TIPS.Metadata |
| AZR.TIPS.Reports | `8c719a1a-f18e-40a1-a16b-039969c6b765` | 44.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/AZR.TIPS.Reports |

### BBT  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| BBT.QPTM.Database | `23c4238f-9f86-4086-a271-fbfa2a8e3d7a` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BBT.QPTM.Database |
| BBT.QPTM.Metadata | `46b6b207-197f-43ed-8191-b682f384429a` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BBT.QPTM.Metadata |
| BBT.QPTM.Reports | `72d24b76-dae0-467d-a5b5-e46d1b309c39` | 12.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BBT.QPTM.Reports |

### BLH  (11 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| BLH.QPTM.Application.ClassicGUI | `664df3aa-a95d-4a29-92be-d4bdcb2300e5` | 53.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Application.ClassicGUI |
| BLH.QPTM.Application.MiddleTier | `480d238f-29a0-4a66-b082-9ec93f78f6e3` | 3.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Application.MiddleTier |
| BLH.QPTM.Application.QPEC | `d195385e-f85e-40a1-98fb-93a763adc112` | 6.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Application.QPEC |
| BLH.QPTM.Application.Web | `ab4b8c65-e156-4231-8843-e47aab228aa4` | 83.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Application.Web |
| BLH.QPTM.Batch | `f35648dc-72b4-42af-8063-d90ecd7e58ae` | 349 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Batch |
| BLH.QPTM.ClassicBatch | `5ebe8a11-ff1a-4b5f-9d80-a029e555bd6f` | 159 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.ClassicBatch |
| BLH.QPTM.ClassicGUI | `0d02f90d-33b3-4d33-b248-333ffcfda3b6` | 77 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.ClassicGUI |
| BLH.QPTM.Database | `f75a0999-490b-44bc-9090-bdf68650f50d` | 301 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Database |
| BLH.QPTM.Metadata | `8f65f076-0ded-4343-aa08-788acdb2db43` | 8.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Metadata |
| BLH.QPTM.Reports | `03a8c889-ca99-47b4-a607-eda04a2e06ee` | 31.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Reports |
| BLH.QPTM.Web | `7702ccb9-6606-4fe9-a1a0-330d8ad894e3` | 12.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLH.QPTM.Web |

### BLU  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| BLU.TIPS.Database | `a2299d16-6a6a-42b6-97f8-a1b0b0e1542a` | 42 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLU.TIPS.Database |
| BLU.TIPS.Metadata | `fc664dbc-d95f-4ebd-ab63-6ecbeed4acf0` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLU.TIPS.Metadata |
| BLU.TIPS.Reports | `826d4c22-b111-4cff-a3e0-dba12a2ebdb3` | 12.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BLU.TIPS.Reports |

### BMD  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| BMD.TIPS.Database | `e91637e7-52eb-4192-af67-5a637a6da44a` | 103 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMD.TIPS.Database |
| BMD.TIPS.Metadata | `9a2b705d-7edc-4317-9fd3-4bde760fe432` | 34 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMD.TIPS.Metadata |
| BMD.TIPS.Reports | `bbb2d039-c162-4c5d-a764-4b49be0f7494` | 16.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMD.TIPS.Reports |

### BMH  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| BMH.TIPS.Database | `2df0099f-d6bc-4bed-864b-6b2722b1daf5` | 102 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMH.TIPS.Database |
| BMH.TIPS.Metadata | `b634d0ff-9e59-44ef-b4ce-75d54fefdad4` | 362 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMH.TIPS.Metadata |
| BMH.TIPS.Reports | `1d118be8-b80a-4b4e-9702-6ba822f4a0bd` | 25.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BMH.TIPS.Reports |

### BPM  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| BPM.TIPS.Database | `6d90a5b0-78da-4bba-ad81-6c75e1722562` | 53 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BPM.TIPS.Database |
| BPM.TIPS.Metadata | `7f8b3c30-91db-4465-90cf-1378349f0a5a` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BPM.TIPS.Metadata |
| BPM.TIPS.Reports | `782102b8-401c-4b9d-8cec-59d9872990b3` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/BPM.TIPS.Reports |

### CCI  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CCI.TIPS.Database | `15d8f685-c958-4ffa-a053-bf053cb4d917` | 82 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CCI.TIPS.Database |
| CCI.TIPS.Metadata | `42cf26d4-a732-4b20-88f9-c66e2525005e` | 491 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CCI.TIPS.Metadata |
| CCI.TIPS.Reports | `cf4c058e-ab27-4812-85c6-11ba5a3b4031` | 24.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CCI.TIPS.Reports |

### CHD  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CHD.TIPS.Database | `90fb54ef-d440-4fa9-8319-ca04f452678f` | 158 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHD.TIPS.Database |
| CHD.TIPS.Metadata | `747a56e9-d3bb-4827-b190-4e68e1c6166c` | 58 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHD.TIPS.Metadata |
| CHD.TIPS.Reports | `53957010-cbdd-4aaf-8fa3-4caa6fc2f947` | 17.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHD.TIPS.Reports |

### CHN  (8 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CHN.QPTM.Application.MiddleTier | `09a6b51a-be47-4d75-b986-a45baef0ca6e` | 445 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Application.MiddleTier |
| CHN.QPTM.Application.QPEC | `994cb1a0-9096-4f67-b2cf-6fc33884c8d7` | 515 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Application.QPEC |
| CHN.QPTM.Application.Web | `93109c14-b801-44bc-afba-38801a467cc4` | 51.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Application.Web |
| CHN.QPTM.ClassicBatch | `cf2df44f-7427-431c-8a5d-f2dee0848c31` | 243 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.ClassicBatch |
| CHN.QPTM.Database | `6616081f-a9bf-4a1f-a447-229ef465c89a` | 57 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Database |
| CHN.QPTM.Metadata | `ee0f526d-f2c1-4afb-8efb-39e520b66a9c` | 948 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Metadata |
| CHN.QPTM.Reports | `c299eb9f-4d00-43ed-9028-0daf62679c01` | 26.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Reports |
| CHN.QPTM.Web | `5a10d029-618f-40da-8854-403e288acd67` | 383 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CHN.QPTM.Web |

### CMH  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CMH.TIPS.Application.QPEC | `78c352a4-81a5-4f08-9ed9-dd4089b99bd7` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Application.QPEC |
| CMH.TIPS.ClassicBatch | `af0533ce-cd2c-4628-8e8a-d706e3d686f4` | 35 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.ClassicBatch |
| CMH.TIPS.Database | `832d5a15-f149-4e50-a33e-a955a2992a3d` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Database |
| CMH.TIPS.Metadata | `db081444-fa23-44b0-b085-207a6ded2f92` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Metadata |
| CMH.TIPS.Reports | `34d97a9e-edf5-4dbe-8f0a-3be4fcc1a418` | 14.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMH.TIPS.Reports |

### CMP  (7 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CMP.TIPS.Application.ClassicGUI | `caed5526-9510-456d-896b-c83cbe8d0e84` | 290 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Application.ClassicGUI |
| CMP.TIPS.Application.QPEC | `c28823d9-a5e9-4879-8951-66cacd93e763` | 513 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Application.QPEC |
| CMP.TIPS.ClassicBatch | `1c16f102-bfed-4275-9dd3-a49df743db2a` | 617 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.ClassicBatch |
| CMP.TIPS.ClassicGUI | `9eab0ea5-72af-4f91-833f-592b3e074b9b` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.ClassicGUI |
| CMP.TIPS.Database | `d1264b58-4ad6-4e89-972a-bcbeaac5c32f` | 394 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Database |
| CMP.TIPS.Metadata | `fac3fc29-6127-4d75-93f0-34739a028bcf` | 10.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Metadata |
| CMP.TIPS.Reports | `f23a2e6e-ea9a-4a76-875a-81ee999dfb47` | 21.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMP.TIPS.Reports |

### CMX  (11 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CMX.QPTM.Application.ClassicGUI | `23c42fe7-bab9-4e96-813c-b1b87c087124` | 52.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Application.ClassicGUI |
| CMX.QPTM.Application.MiddleTier | `460e2d9d-8fcb-4240-9b4a-ceeecfb92498` | 2.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Application.MiddleTier |
| CMX.QPTM.Application.QPEC | `f792bdfb-7a7f-44a1-b677-341e566b6fff` | 3.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Application.QPEC |
| CMX.QPTM.Application.Web | `482c4795-225f-470b-87f6-c9de4992fc76` | 62.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Application.Web |
| CMX.QPTM.Batch | `6015925b-c9b9-4de9-8036-8a2959625423` | 104 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Batch |
| CMX.QPTM.ClassicBatch | `602933ab-a74e-46a3-9f86-f7d683c15532` | 70 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.ClassicBatch |
| CMX.QPTM.ClassicGUI | `9eb4e1bb-784e-4cc4-9852-5bb26b1c1d1c` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.ClassicGUI |
| CMX.QPTM.Database | `e9c6ca78-aff2-4c6c-a4c8-2871d597da20` | 147 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Database |
| CMX.QPTM.Metadata | `01849a41-b311-463e-baf8-9ac62a0b2387` | 182 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Metadata |
| CMX.QPTM.Reports | `06889625-b74e-4700-82f2-0f62dfab2df2` | 13.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Reports |
| CMX.QPTM.Web | `b5945876-49ae-42b2-a6cd-b26a4ec0045d` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CMX.QPTM.Web |

### CNP  (16 repos — families: QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CNP.QGM.Application.QPEC | `18315ed3-ac94-404f-9b40-5bc6f395718e` | 390 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QGM.Application.QPEC |
| CNP.QGM.ClassicBatch | `e1537d71-c1e1-456b-a61c-df8b73e21bb9` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QGM.ClassicBatch |
| CNP.QGM.Database | `9bfc0aef-d318-47f5-8971-a6cdeb25f132` | 26 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QGM.Database |
| CNP.QGM.Metadata | `7efc7055-dd6a-41e9-98dc-6af708339ef7` | 574 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QGM.Metadata |
| CNP.QGM.Reports | `1f5cd772-02bd-4a87-8e53-4a654390fa93` | 4.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QGM.Reports |
| CNP.QPTM.Application.ClassicGUI | `53f08dfb-e74e-48f7-86cd-3749be762f0f` | 57.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Application.ClassicGUI |
| CNP.QPTM.Application.MiddleTier | `b2f2a44c-ee23-4f83-b1a2-e5cbe11774fc` | 890 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Application.MiddleTier |
| CNP.QPTM.Application.QPEC | `92984d85-81b3-4654-97e8-c1ec3245d9a6` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Application.QPEC |
| CNP.QPTM.Application.Web | `a421c171-b5a3-475c-8f71-80ca78e58162` | 40.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Application.Web |
| CNP.QPTM.Batch | `92357e36-4f3a-4bbb-8970-a97ff6680c29` | 55 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Batch |
| CNP.QPTM.ClassicBatch | `3cea639f-d90b-49da-8d44-52559c131b59` | 193 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.ClassicBatch |
| CNP.QPTM.ClassicGUI | `3ea2e9ee-6d4b-4b0e-bb63-145fee927e52` | 58 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.ClassicGUI |
| CNP.QPTM.Database | `01ae92dc-b14a-41e7-b741-2c9407d4a716` | 268 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Database |
| CNP.QPTM.Metadata | `932e0023-95e7-4fab-b09e-bfa5ee4fa4be` | 4.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Metadata |
| CNP.QPTM.Reports | `ee0ab0d3-50f0-40fa-9ff1-f057421ed22a` | 15.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Reports |
| CNP.QPTM.Web | `96c1e408-61cc-40ea-bd49-1f4d71d7709f` | 500 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CNP.QPTM.Web |

### CRS  (6 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CRS.TIPS.Application.QPEC | `ec399d91-a530-4935-8fb3-7a5c483e2b99` | 3.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Application.QPEC |
| CRS.TIPS.Batch | `9cc70268-8220-4d40-bb74-10f272797921` | 15 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Batch |
| CRS.TIPS.ClassicBatch | `8bf8ae45-44f4-491a-a41e-a602a2438262` | 144 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.ClassicBatch |
| CRS.TIPS.Database | `dd145f26-9a48-492f-9961-c3a21b8064f0` | 166 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Database |
| CRS.TIPS.Metadata | `e6f199b6-48ae-4c27-8269-fdd080b6d17a` | 60 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Metadata |
| CRS.TIPS.Reports | `770df692-d179-4f00-8bed-8b1c8186e5f9` | 29.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRS.TIPS.Reports |

### CRW  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CRW.QPTM.Database | `4a78cf78-8863-424b-8621-d67667abee21` | 51 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRW.QPTM.Database |
| CRW.QPTM.Metadata | `b0fce9e7-2a78-44e8-aaa6-59f2a5b30924` | 11.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRW.QPTM.Metadata |
| CRW.QPTM.Reports | `a9884107-de38-4d74-a874-9429a0b6e891` | 14.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CRW.QPTM.Reports |

### CSU  (5 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| CSU.QPTM.Application.QPEC | `057b7b18-4e85-4997-9960-840582ffff1e` | 4.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CSU.QPTM.Application.QPEC |
| CSU.QPTM.ClassicBatch | `fd457cd3-2782-4635-8c00-1c31d5d2a2d5` | 43 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CSU.QPTM.ClassicBatch |
| CSU.QPTM.Database | `542d3e76-8b8e-4bb0-b12d-4486ae1a1a5a` | 65 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CSU.QPTM.Database |
| CSU.QPTM.Metadata | `c5fb277e-9b6e-4eae-994e-de6c6a99032c` | 153 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CSU.QPTM.Metadata |
| CSU.QPTM.Reports | `00dd95f1-03f5-43e7-a975-e71b400dcd48` | 11.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/CSU.QPTM.Reports |

### DLP  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DLP.TIPS.Database | `2f8ec76d-29d7-4067-a156-3347a4e47298` | 62 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DLP.TIPS.Database |
| DLP.TIPS.Metadata | `b70d6388-0c3c-4458-8bd5-f46cb73bb9ae` | 28 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DLP.TIPS.Metadata |
| DLP.TIPS.Reports | `70dece0b-9f31-4117-b230-78f64e53fe7e` | 24.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DLP.TIPS.Reports |

### DSU  (6 repos — families: QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| DSU.QGM.Database | `ce8d7d05-bc8d-4056-ae3c-643349a17785` | 91 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DSU.QGM.Database |
| DSU.QGM.Metadata | `38d3f4d7-7302-4bcb-8020-92cb2ed4209e` | 80 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DSU.QGM.Metadata |
| DSU.QGM.Reports | `019814ee-876c-4336-9fbf-5629e0a92164` | 4.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DSU.QGM.Reports |
| DSU.QPTM.Database | `28c9033a-3f66-4381-9d28-82ec87d25d01` | 188 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DSU.QPTM.Database |
| DSU.QPTM.Metadata | `22abf684-bb0a-432c-ad54-5dbcba045fd0` | 116 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DSU.QPTM.Metadata |
| DSU.QPTM.Reports | `3a9badca-9ff8-4a82-9baa-086e3f020f98` | 14.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/DSU.QPTM.Reports |

### ECM  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ECM.TIPS.Database | `1aab7ccf-3d86-4a3a-b81f-4f07b271b9a3` | 63 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ECM.TIPS.Database |
| ECM.TIPS.Metadata | `38ea38dc-5db6-41e0-9714-36f034da9c25` | 34 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ECM.TIPS.Metadata |

### EDA  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EDA.TIPS.Database | `5fef0c8f-b8b2-4bbc-95fb-9dd4c95517e7` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDA.TIPS.Database |
| EDA.TIPS.Metadata | `f173b431-59f7-4a2f-9933-4fe0973d3f05` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDA.TIPS.Metadata |

### EDB  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EDB.TIPS.Database | `d0189a60-912c-4020-9408-078d0d4f545a` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDB.TIPS.Database |
| EDB.TIPS.Metadata | `73f506ab-10c3-497c-8842-0651ff65c7fc` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDB.TIPS.Metadata |

### EDC  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EDC.TIPS.Database | `dea16f8f-c77a-455b-bdd1-7d0669fd9537` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDC.TIPS.Database |
| EDC.TIPS.Metadata | `6cb2939b-a32b-4527-af5e-489af8b9afc4` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDC.TIPS.Metadata |

### EDO  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EDO.TIPS.Application.QPEC | `6efa450a-965b-432d-9c17-5074764c2b1c` | 4.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDO.TIPS.Application.QPEC |
| EDO.TIPS.Metadata | `65c0c74f-f24a-4b29-81e7-858f11309d88` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EDO.TIPS.Metadata |

### EIG  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EIG.TIPS.Application.QPEC | `12443307-1964-4c96-a3cb-46943069db9a` | 8.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Application.QPEC |
| EIG.TIPS.ClassicBatch | `b2548ca7-13e7-4517-883f-ff4e4c349570` | 18 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.ClassicBatch |
| EIG.TIPS.Database | `c88d325d-5bce-4f06-a20c-9a0a7cb0125c` | 75 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Database |
| EIG.TIPS.Metadata | `d068d46b-8a97-468a-bb7d-2d584332ff0a` | 40 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Metadata |
| EIG.TIPS.Reports | `919b78c3-91cf-4580-9d72-82e46fa91c18` | 22.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EIG.TIPS.Reports |

### EMT  (9 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EMT.QPTM.Application.MiddleTier | `39844d8a-8d5d-4e01-b6ed-c32e7882dbe5` | 163 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Application.MiddleTier |
| EMT.QPTM.Application.QPEC | `8e6a41da-33f7-427d-b055-d4d00990acad` | 156 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Application.QPEC |
| EMT.QPTM.Application.Web | `ca3886c0-4cef-41e5-b19b-fbaf816ef8e4` | 37.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Application.Web |
| EMT.QPTM.Batch | `106ea455-ad20-4489-bfee-04ae79296342` | 68 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Batch |
| EMT.QPTM.ClassicBatch | `99b5106c-aecf-4ddc-b6a1-0967725b6d74` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.ClassicBatch |
| EMT.QPTM.Database | `82c519bf-4c4c-4bb4-9bae-a0f3e0f87aee` | 27 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Database |
| EMT.QPTM.Metadata | `d5a5d496-ee8a-48c1-83c2-43138a537279` | 1.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Metadata |
| EMT.QPTM.Reports | `ebfcb830-871e-4bd5-9806-1fabfd4ad332` | 12.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Reports |
| EMT.QPTM.Web | `c3e177d4-24e0-4e9d-a6a4-6346407dce65` | 427 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EMT.QPTM.Web |

### EOI  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EOI.TIPS.Database | `e36b8e61-d079-447f-9a3d-64578b90ef05` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EOI.TIPS.Database |
| EOI.TIPS.Metadata | `3985f8cf-724c-4bd4-8309-abe165ba1be3` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EOI.TIPS.Metadata |

### ESG  (2 repos — families: QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ESG.QGM.Database | `44802365-7ad0-41dc-a2fc-1424e3c0c64b` | 53 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ESG.QGM.Database |
| ESG.QGM.Metadata | `0dfa3064-cb0c-476f-9ea6-354f3b465898` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ESG.QGM.Metadata |

### ETC  (9 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ETC.QPTM.Application.MiddleTier | `2a814da8-088d-4d88-8c45-08dc0759be14` | 1.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Application.MiddleTier |
| ETC.QPTM.Application.QPEC | `9a63e926-049d-4cb4-b2fd-0cad0bdd9343` | 2.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Application.QPEC |
| ETC.QPTM.Application.Web | `5252e763-62b1-4f47-b8e8-13f9478c9a4a` | 77.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Application.Web |
| ETC.QPTM.Batch | `7922434d-7aa0-48b1-8b48-d7c3442cd440` | 102 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Batch |
| ETC.QPTM.ClassicBatch | `657ffe7e-3849-42fd-9d2a-bea2486da5f5` | 273 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.ClassicBatch |
| ETC.QPTM.Database | `b6d13ddf-ac82-427c-92b8-36048a93e29b` | 86 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Database |
| ETC.QPTM.Metadata | `ca5326d7-b40e-4b85-918a-b00a645ff910` | 252 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Metadata |
| ETC.QPTM.Reports | `4ab38431-ad91-4213-96ed-149b22953408` | 27.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Reports |
| ETC.QPTM.Web | `90d009f9-8dff-4b5a-bde6-bc2c9898348a` | 833 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ETC.QPTM.Web |

### EVO  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| EVO.TIPS.Metadata | `59a64b5a-0fd8-4982-8aef-4f1ef3e302e5` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EVO.TIPS.Metadata |
| EVO.TIPS.Reports | `6ab65d4a-aa15-4730-be78-da9611db20e6` | 10.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/EVO.TIPS.Reports |

### FOR  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| FOR.TIPS.Database | `235212d8-ddfd-4ed7-adfc-656e39485c04` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FOR.TIPS.Database |
| FOR.TIPS.Metadata | `fe78dd8d-8c5f-4271-8218-c4f5fb3d3f09` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FOR.TIPS.Metadata |

### FPL  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| FPL.TIPS.Crude.Metadata | `24c685d2-40e1-4ecd-882d-a59ef43437f8` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FPL.TIPS.Crude.Metadata |
| FPL.TIPS.Database | `20ce5a3f-0ad0-47b5-abd0-056d1f299d4f` | 54 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FPL.TIPS.Database |
| FPL.TIPS.Metadata | `87619858-5c71-4239-a000-460373d4010a` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FPL.TIPS.Metadata |

### FRC  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| FRC.TIPS.Database | `9bd947a5-a4c1-4e3c-9f29-d1dc4b17fbfc` | 62 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FRC.TIPS.Database |
| FRC.TIPS.Metadata | `91911e31-05b9-49e5-a05f-918af95a843b` | 59 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FRC.TIPS.Metadata |
| FRC.TIPS.Reports | `f23bd2d6-f289-4d81-8131-3494ce262775` | 15.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/FRC.TIPS.Reports |

### GBG  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| GBG.QPTM.Database | `3ee0f1a7-0f5e-4d25-a4f9-16a8dcac7635` | 341 KB | feature/1809611_BuildUpgrade_2026.04 | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GBG.QPTM.Database |
| GBG.QPTM.Metadata | `89b0937b-28d7-4be0-9db3-386e5ecd38b0` | 107 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GBG.QPTM.Metadata |
| GBG.QPTM.Reports | `91092228-ed9a-42b1-a7cf-461acb66c537` | 26.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GBG.QPTM.Reports |

### GLE  (6 repos — families: QGM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| GLE.QGM.Database | `4e87b9d1-a9bf-40da-8676-d078590b3cec` | 56 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.QGM.Database |
| GLE.QGM.Metadata | `babc3964-b8f6-44c1-85e3-d1f9137230be` | 42 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.QGM.Metadata |
| GLE.QGM.Reports | `f7b55bd8-4536-48b8-8a2b-1866d5367699` | 6.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.QGM.Reports |
| GLE.TIPS.Database | `8d62e21f-5b34-4b36-9536-5cfbabf3e1b4` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.TIPS.Database |
| GLE.TIPS.Metadata | `d1400d72-7903-45de-9a85-f73aee6d8520` | 5.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.TIPS.Metadata |
| GLE.TIPS.Reports | `a1c83452-4c86-49ee-90b8-bc8b26a2af4a` | 46.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GLE.TIPS.Reports |

### GNM  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| GNM.TIPS.Database | `89514301-4a72-47dd-82a8-b524c9931d4b` | 164 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNM.TIPS.Database |
| GNM.TIPS.Metadata | `aaadcb4c-c61c-4554-abff-e96980393ac9` | 137 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNM.TIPS.Metadata |
| GNM.TIPS.Reports | `22263197-c22c-4533-a96f-6d5bdce574ab` | 31.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNM.TIPS.Reports |

### GNP  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| GNP.QPTM.Database | `acb495c8-3993-4948-9738-2202361ab731` | 143 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNP.QPTM.Database |
| GNP.QPTM.Metadata | `89c82a12-adb0-466c-a628-57f4cfb53e32` | 122 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNP.QPTM.Metadata |
| GNP.QPTM.Reports | `b39de800-9804-40c6-8f99-0deb5b7bea02` | 26.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/GNP.QPTM.Reports |

### HEC  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| HEC.TIPS.Database | `a211d45c-8b0e-4c57-b2cb-ee067085932a` | 68 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEC.TIPS.Database |
| HEC.TIPS.Metadata | `44284678-b317-40ac-b894-2b986634eb96` | 41 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEC.TIPS.Metadata |
| HEC.TIPS.Reports | `5236feb9-d7f7-48bf-aa2f-51f0282abbc8` | 20.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEC.TIPS.Reports |

### HEP  (6 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| HEP.QPTM.Database | `e65da1f8-1a63-4579-a8dc-148c3b717a7b` | 78 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.QPTM.Database |
| HEP.QPTM.Metadata | `96e34f3a-c73c-4d3c-898d-af7398bb688f` | 46 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.QPTM.Metadata |
| HEP.QPTM.Reports | `d66a09a0-e7ac-4fd9-a1ad-1983cf812038` | 13.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.QPTM.Reports |
| HEP.TIPS.Database | `185d3f3f-38a6-46b7-834a-dcadca63e154` | 280 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.TIPS.Database |
| HEP.TIPS.Metadata | `9446543d-9ec0-4754-9ec0-1cf2cfa01611` | 71 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.TIPS.Metadata |
| HEP.TIPS.Reports | `05876f5a-ed4f-472e-972d-6eb20a33b06b` | 44.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HEP.TIPS.Reports |

### HPE  (14 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| HPE.QPTM.Application.ClassicGUI | `9e6b2014-34a6-4964-ba95-a68c6cbf4e8e` | 50.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Application.ClassicGUI |
| HPE.QPTM.Application.ClassicGUICAW | `6c9349a1-a429-4252-b26f-58126dca5eb9` | 315 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Application.ClassicGUICAW |
| HPE.QPTM.Application.QPEC | `f8438209-cbd8-4c8f-9548-8c9df3904e2c` | 563 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Application.QPEC |
| HPE.QPTM.Batch | `55cd8655-5af0-411d-9b46-a50ed74c7152` | 66 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Batch |
| HPE.QPTM.ClassicBatch | `eecac4b4-2d46-48c1-85e3-817bbda1c9bd` | 142 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.ClassicBatch |
| HPE.QPTM.ClassicGUI | `15c4f0d4-7578-4b05-ab4d-f358140b36a9` | 70 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.ClassicGUI |
| HPE.QPTM.Database | `e7631e94-3cba-4bef-98a6-cddd6433892c` | 124 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Database |
| HPE.QPTM.Metadata | `14d870f6-8779-43fe-8d34-2f608b2680b2` | 5.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Metadata |
| HPE.QPTM.Reports | `4d544894-7fee-4f82-8cc1-432933bddd84` | 29.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.QPTM.Reports |
| HPE.TIPS.Application.QPEC | `823213c9-3b49-4a73-9c95-1ec367607367` | 642 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Application.QPEC |
| HPE.TIPS.ClassicBatch | `9f455a31-e14c-4078-aafa-7fa583031753` | 78 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.ClassicBatch |
| HPE.TIPS.Database | `3792bc28-bc0e-4b91-b141-8c57518f6772` | 169 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Database |
| HPE.TIPS.Metadata | `e573745c-d36d-47bf-969c-925ff0c4168f` | 13.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Metadata |
| HPE.TIPS.Reports | `c931c89f-bedd-45bd-9d1b-9f5edbdb69f6` | 51.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HPE.TIPS.Reports |

### HVK  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| HVK.TIPS.Database | `db1ac339-479b-436b-8c73-e0dec60a7994` | 131 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVK.TIPS.Database |
| HVK.TIPS.Metadata | `1ec1f932-45d4-412a-b2fb-ea7be1dff372` | 662 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVK.TIPS.Metadata |
| HVK.TIPS.Reports | `87be4f59-4137-4fba-a415-3f1e3fda00bc` | 31.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVK.TIPS.Reports |

### HVM  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| HVM.TIPS.Database | `f8837a41-27d2-43dd-b967-724a51e21e9e` | 735 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVM.TIPS.Database |
| HVM.TIPS.Metadata | `e9c62d47-607e-441b-8fa4-398ee6b22571` | 24.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVM.TIPS.Metadata |
| HVM.TIPS.Reports | `55346d6b-fd1d-4c47-9dc7-22065525e0de` | 45.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/HVM.TIPS.Reports |

### IAC  (9 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| IAC.TIPS.Application.ClassicGUI | `16d54541-6be9-4de6-86b3-0fadc878d0ce` | 591 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Application.ClassicGUI |
| IAC.TIPS.Application.MiddleTier | `0c2f9b00-8ff2-443d-88a5-85fb703d510f` | 638 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Application.MiddleTier |
| IAC.TIPS.Application.QPEC | `f3644c08-cc95-4725-bfc8-8546760467fb` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Application.QPEC |
| IAC.TIPS.ClassicBatch | `743051a8-2d1b-4415-bde3-5599e5da4af1` | 2.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.ClassicBatch |
| IAC.TIPS.ClassicGUI | `775196cd-a023-4e93-b014-4341e234d4a8` | 222 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.ClassicGUI |
| IAC.TIPS.Database | `3b90546d-27a8-43ab-b73c-6fe8b0211f39` | 637 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Database |
| IAC.TIPS.Metadata | `32d9a64d-c517-4564-8a98-74b7013473d8` | 18.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Metadata |
| IAC.TIPS.Reports | `d58683b7-a98e-46a1-b9dd-83b1ffc36208` | 49.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Reports |
| IAC.TIPS.Web | `823f0c9d-0d64-478f-9655-54b890b6cceb` | 515 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IAC.TIPS.Web |

### IME  (6 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| IME.TIPS.Application.QPEC | `5a206913-7a37-4d1a-82b6-e7b314519a29` | 3.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Application.QPEC |
| IME.TIPS.Batch | `e2319909-0db9-496e-8a41-efd88892e72b` | 35 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Batch |
| IME.TIPS.ClassicBatch | `068ada17-ce32-49e4-bcda-f5d01bdfa023` | 22 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.ClassicBatch |
| IME.TIPS.Database | `006b3905-5c36-4fa1-bcb1-8ba13cb2cd58` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Database |
| IME.TIPS.Metadata | `8776ddfa-e66f-4a9f-8d54-ca409da6d1f5` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Metadata |
| IME.TIPS.Reports | `967d87ea-ba7e-45e2-acc2-ea90bbcdcce0` | 14.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IME.TIPS.Reports |

### IMM  (3 repos — families: QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| IMM.QGM.Database | `47e37e6c-3c9a-4aaf-9b71-92c8cfb277c4` | 62 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IMM.QGM.Database |
| IMM.QGM.Metadata | `7476133e-b9b3-436d-ac6b-79723b10a622` | 26 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IMM.QGM.Metadata |
| IMM.QGM.Reports | `4cd5e108-1653-4c84-8459-a6def3d62ab3` | 4.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IMM.QGM.Reports |

### IPF  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| IPF.TIPS.Database | `4faa286e-18b1-4126-b2a8-90fc109e8cac` | 8.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IPF.TIPS.Database |
| IPF.TIPS.Metadata | `4d45530c-40f8-45de-8203-e842af0ef04f` | 184 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IPF.TIPS.Metadata |
| IPF.TIPS.Reports | `d7bff4d5-2559-44cf-bb24-cf0f41d467c9` | 24.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/IPF.TIPS.Reports |

### KEY  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| KEY.TIPS.Application.QPEC | `08f03d8a-67ac-48fd-97d0-dab0ace52baa` | 256 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Application.QPEC |
| KEY.TIPS.ClassicBatch | `17feec75-8fba-47c8-8cd7-69f11ef5cc26` | 47 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.ClassicBatch |
| KEY.TIPS.Database | `5b9147bc-b276-456b-8142-83f9e689825f` | 604 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Database |
| KEY.TIPS.Metadata | `fa118cf8-bd5d-4bdf-bdba-9052509a4ee5` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Metadata |
| KEY.TIPS.Reports | `0dd62312-3749-49d9-b51c-c57f599b9079` | 39.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/KEY.TIPS.Reports |

### LMD  (4 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| LMD.TIPS.ClassicBatch | `947150cd-4d0c-48ff-9361-46b2fac9e254` | 22 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.ClassicBatch |
| LMD.TIPS.Database | `da31e213-5adc-48b3-98ce-5c9104db57ae` | 69 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.Database |
| LMD.TIPS.Metadata | `ed52990f-7bb0-4fc8-bf3b-fc94bb033e44` | 226 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.Metadata |
| LMD.TIPS.Reports | `752d96dc-cb6f-4786-bff5-4337a71030cd` | 11.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LMD.TIPS.Reports |

### LVM  (6 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| LVM.TIPS.Application.MiddleTier | `37bb5da0-6f2b-41a7-a183-b7425863d9d8` | 601 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Application.MiddleTier |
| LVM.TIPS.Application.QPEC | `336dc000-521d-4f7c-8ec9-d977d1e59221` | 908 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Application.QPEC |
| LVM.TIPS.ClassicBatch | `a609a4e8-ef13-4ae5-ba3c-f330e5db6026` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.ClassicBatch |
| LVM.TIPS.Database | `552891d1-e15e-42d7-8b23-dbf0c894f6a5` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Database |
| LVM.TIPS.Metadata | `aa82bd52-869e-484e-be9d-69d248d0bc9f` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Metadata |
| LVM.TIPS.Reports | `48b2bee4-689b-4de4-9b97-641aaebee657` | 15.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/LVM.TIPS.Reports |

### MER  (7 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| MER.TIPS.Application.QPEC | `eef1f4df-9722-4ea9-9581-b6a101ff592c` | 811 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Application.QPEC |
| MER.TIPS.ClassicBatch | `cc9064b4-b47a-4da3-bdae-3fc9eb93dadd` | 270 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.ClassicBatch |
| MER.TIPS.Crude.Metadata | `9f4b3a0d-af6f-4d5c-a90e-ecdb59870940` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Crude.Metadata |
| MER.TIPS.Database | `50f0de05-6bc4-43cf-b45e-8cd9d99053e5` | 435 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Database |
| MER.TIPS.Metadata | `52677e7f-a813-4232-a04f-4c5d8eeb5ecb` | 14.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Metadata |
| MER.TIPS.Reports | `542c3986-f65a-4c25-9a61-11cc0eeebd70` | 32.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.Reports |
| MER.TIPS.SAP.Application.WebService | `bbd85f3d-72a5-4996-b5c6-b14f8283f856` | 85 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MER.TIPS.SAP.Application.WebService |

### MFC  (8 repos — families: QEMS, QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| MFC.QEMS.Database | `347572b4-2cae-4190-9df5-20fdbde95525` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QEMS.Database |
| MFC.QEMS.Metadata | `c9f29d50-5dbb-4822-ba39-77b266a13813` | 3.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QEMS.Metadata |
| MFC.QEMS.Reports | `fe1f6498-d2bc-4e21-b2a5-c13e102b3f82` | 3.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QEMS.Reports |
| MFC.QGM.Application.QPEC | `1b2dcd27-fc75-4aef-85ca-0663c1c42c4e` | 483 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QGM.Application.QPEC |
| MFC.QGM.ClassicBatch | `7e6834cb-7aad-418b-a57d-ad3ab568a83d` | 71 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QGM.ClassicBatch |
| MFC.QGM.Database | `45d3ab50-a3aa-4a00-bc3f-cfe846304a06` | 13 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QGM.Database |
| MFC.QGM.Metadata | `4128db39-809d-4453-884d-602e5b1d2fda` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QGM.Metadata |
| MFC.QGM.Reports | `88c2d54a-b124-45f3-836d-288f7202a13d` | 4.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MFC.QGM.Reports |

### MGP  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| MGP.TIPS.Application.QPEC | `0833d6b2-b8eb-4525-bc10-cea23b7d95a4` | 226 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Application.QPEC |
| MGP.TIPS.ClassicBatch | `8c3c6023-7584-4f83-b76e-5bc89ee36465` | 140 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.ClassicBatch |
| MGP.TIPS.Database | `c700592e-3c8b-4e1b-b35c-2abf9016f570` | 111 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Database |
| MGP.TIPS.Metadata | `456d5e25-d6f8-4451-a774-cb7a846bdd0e` | 48.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Metadata |
| MGP.TIPS.Reports | `94b096c0-e5ae-451a-b146-def955ea3d4d` | 20.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MGP.TIPS.Reports |

### MKW  (8 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| MKW.TIPS.Application.MiddleTier | `42dacd1e-6bf3-4cb6-93a2-3fdbcda72fbd` | 332 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Application.MiddleTier |
| MKW.TIPS.Application.QPEC | `26deafe1-5944-4116-afb8-7241479ef634` | 558 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Application.QPEC |
| MKW.TIPS.Application.Web | `1b0f3eef-c740-479b-ad9c-f63619339b80` | 30.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Application.Web |
| MKW.TIPS.ClassicBatch | `84c62990-03c3-46dc-8ce9-6c2facab9f12` | 437 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.ClassicBatch |
| MKW.TIPS.Database | `bb8d8c92-be7d-419a-b2e9-059687d96422` | 519 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Database |
| MKW.TIPS.Metadata | `36e5afc7-3df6-4572-b9f2-7e89f55c3764` | 50.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Metadata |
| MKW.TIPS.Reports | `eb528a6c-9ffa-4d0d-a05f-cfc5b0ff0357` | 33.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Reports |
| MKW.TIPS.Web | `847431ed-714c-4200-8dfb-011939b4a716` | 735 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MKW.TIPS.Web |

### MOM  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| MOM.TIPS.Application.QPEC | `ee796dd1-28d3-4ee5-8635-fbaaac94eb14` | 4.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Application.QPEC |
| MOM.TIPS.ClassicBatch | `81598829-567b-42ba-91d8-14a30ce8c4db` | 104 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.ClassicBatch |
| MOM.TIPS.Database | `1ce1a962-0d13-40b1-bd50-10a45693189f` | 170 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Database |
| MOM.TIPS.Metadata | `7d570f16-c67b-41e1-bba3-085dfad8cf67` | 53 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Metadata |
| MOM.TIPS.Reports | `6b5bd9ee-8022-463b-885d-117501723b6b` | 24.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MOM.TIPS.Reports |

### MRE  (3 repos — families: QEMS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| MRE.QEMS.Database | `3b44e0a5-7f16-448a-8c07-f601cd60bade` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MRE.QEMS.Database |
| MRE.QEMS.Metadata | `f57ce277-78f7-49d9-aa29-b12bebf09379` | 3.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MRE.QEMS.Metadata |
| MRE.QEMS.Reports | `53bbed91-e26f-4fc0-a5b9-b7ebf6c646c2` | 3.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/MRE.QEMS.Reports |

### NCG  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| NCG.QPTM.Database | `e7a01825-5592-4aa8-b465-73315c7d1e99` | 75 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NCG.QPTM.Database |
| NCG.QPTM.Metadata | `7f2167d0-48e1-4fc2-a48c-8771a839a2bd` | 39 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NCG.QPTM.Metadata |
| NCG.QPTM.Reports | `00d012bb-811e-4f8e-8f3f-55220a3e2f83` | 15.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NCG.QPTM.Reports |

### NEM  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| NEM.TIPS.Database | `76f38886-b214-4ffb-aa43-2f0a9aa86822` | 76 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NEM.TIPS.Database |
| NEM.TIPS.Metadata | `879a32e6-71d4-4fd2-9347-769b2877fb40` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NEM.TIPS.Metadata |

### NJR  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| NJR.QPTM.Database | `e6e6ef3f-4363-4086-b9e0-03048fc0e3f4` | 101 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NJR.QPTM.Database |
| NJR.QPTM.Metadata | `20fdfe06-6f52-43f1-934d-3309f41c0ccd` | 28 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NJR.QPTM.Metadata |
| NJR.QPTM.Reports | `9909ca75-e4a9-4307-839c-7268102ef103` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NJR.QPTM.Reports |

### NRM  (6 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| NRM.TIPS.Application.QPEC | `ea9304c8-c2bb-46b2-9cf8-0c611f59bf0b` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Application.QPEC |
| NRM.TIPS.Batch | `e23b0224-bc14-499f-9bc7-d3e659ceaa8c` | 99 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Batch |
| NRM.TIPS.ClassicBatch | `9144e155-e4dd-4f2c-94cf-447d226ca9b9` | 300 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.ClassicBatch |
| NRM.TIPS.Database | `ec08db4c-8663-4621-914f-8398595a63f9` | 629 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Database |
| NRM.TIPS.Metadata | `3a28d529-d923-45ac-be94-c6090c46e976` | 42.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Metadata |
| NRM.TIPS.Reports | `0185afed-8906-40f9-9a43-b5c343e84f7a` | 39.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/NRM.TIPS.Reports |

### ONI  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| ONI.QPTM.Database | `a8c45697-60ae-4064-9215-48c80f201bb3` | 96 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONI.QPTM.Database |
| ONI.QPTM.Metadata | `91d94d56-e874-4f62-b9b4-09a7ec8f3f4a` | 35 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONI.QPTM.Metadata |
| ONI.QPTM.Reports | `a9824dd8-9f45-44c2-aa2f-31dd55fc4820` | 28.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/ONI.QPTM.Reports |

### OXY  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| OXY.TIPS.Application.QPEC | `c9f5931e-09aa-4df7-b9ba-fe5af3a669fa` | 4.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Application.QPEC |
| OXY.TIPS.ClassicBatch | `cf7fa0b9-1c65-4f12-abf7-e4537e542280` | 156 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.ClassicBatch |
| OXY.TIPS.Database | `2bb7cf13-4a85-427c-857c-9cfac3836ff5` | 190 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Database |
| OXY.TIPS.Metadata | `e724d35d-1bb3-43ab-abf9-5d0391f45727` | 216 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Metadata |
| OXY.TIPS.Reports | `2e5df180-07bc-4a1d-a66d-dbe69f8a0ade` | 19.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/OXY.TIPS.Reports |

### PEM  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PEM.TIPS.Application.QPEC | `b110cb7c-ee3e-4c7f-b083-6968812facf0` | 1.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Application.QPEC |
| PEM.TIPS.ClassicBatch | `22a3a525-cdcc-4db4-b5cf-d68f6e9f7682` | 135 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.ClassicBatch |
| PEM.TIPS.Database | `6d2c8b11-6295-45d0-b36b-a0f8f25411b6` | 256 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Database |
| PEM.TIPS.Metadata | `12bffa88-137f-4211-8faa-61f4fe3fd3f9` | 106.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Metadata |
| PEM.TIPS.Reports | `323b3c86-a0be-44c6-bdc9-71bf4687b22f` | 49.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEM.TIPS.Reports |

### PEP  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PEP.TIPS.Application.QPEC | `b6fffff2-8975-43a7-9889-839a35a93924` | 573 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Application.QPEC |
| PEP.TIPS.ClassicBatch | `964946d6-71c6-472a-910a-7ca6171de67a` | 696 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.ClassicBatch |
| PEP.TIPS.Database | `cad24b7a-fc8a-4b83-ab84-ef4a7d775caf` | 127 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Database |
| PEP.TIPS.Metadata | `f151a040-4a1b-4c3b-972c-14fe52337a33` | 561 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Metadata |
| PEP.TIPS.Reports | `9986cb19-8349-491e-b28f-dc89506d7298` | 26.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PEP.TIPS.Reports |

### PMB  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PMB.TIPS.Application.QPEC | `1479ea70-e86c-4f23-92dc-b9f6a7090305` | 659 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Application.QPEC |
| PMB.TIPS.ClassicBatch | `248373f6-bcbd-4329-898c-53f8ff49c0c4` | 64 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.ClassicBatch |
| PMB.TIPS.Database | `d5128ed7-d80d-400e-8430-ada53613baee` | 14 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Database |
| PMB.TIPS.Metadata | `9645938a-4618-41d6-bbfd-efba710bad32` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Metadata |
| PMB.TIPS.Reports | `f316abb1-b1a8-42e1-b563-beb62584e227` | 17.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PMB.TIPS.Reports |

### PML  (6 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PML.TIPS.Application.QPEC | `f2b1e610-9214-403e-b687-343a0322ad00` | 3.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Application.QPEC |
| PML.TIPS.Batch | `da1e1cdc-4fe6-40f3-a490-c9d1f45eb104` | 16 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Batch |
| PML.TIPS.ClassicBatch | `ee05a121-a444-4d81-ab86-3a2223437010` | 84 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.ClassicBatch |
| PML.TIPS.Database | `fa46fb0d-5429-426b-932c-233522767fe5` | 66 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Database |
| PML.TIPS.Metadata | `e23e2aba-31ad-41c7-b3c3-bd90a6934124` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Metadata |
| PML.TIPS.Reports | `9a47b525-0a1a-4d7d-897e-cf0e5e41d600` | 29.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PML.TIPS.Reports |

### PNR  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PNR.TIPS.Database | `a9ac6e81-daaa-4813-ba1b-50a524d7f322` | 86 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PNR.TIPS.Database |
| PNR.TIPS.Metadata | `c9b66312-32c8-4dbd-a4ff-8ab7da1a5582` | 124 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PNR.TIPS.Metadata |
| PNR.TIPS.Reports | `1b6efc11-a3ec-4b1f-92f0-141ecc30e959` | 19.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PNR.TIPS.Reports |

### PRF_DCP_PRF  (11 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PRF_DCP_PRF.TIPS.Application.ClassicGUI | `f3b85501-23cb-48c1-82db-0badf0cb7c8f` | 768 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.ClassicGUI |
| PRF_DCP_PRF.TIPS.Application.MiddleTier | `dd537374-5136-474d-aba5-8dcbdb9bc5a9` | 741 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.MiddleTier |
| PRF_DCP_PRF.TIPS.Application.QPEC | `30760a1d-b293-4cdc-b6dc-360d381e5238` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.QPEC |
| PRF_DCP_PRF.TIPS.Application.Web | `d215a2ba-f2b0-45be-b741-53faa33c8636` | 45.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Application.Web |
| PRF_DCP_PRF.TIPS.Batch | `e8b336da-104b-41ae-9b79-b949deec1766` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Batch |
| PRF_DCP_PRF.TIPS.ClassicBatch | `eda280b4-251a-4a05-9794-353d827cad84` | 4.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.ClassicBatch |
| PRF_DCP_PRF.TIPS.ClassicGUI | `87903efc-bb06-4b12-86bb-4060f9cc7531` | 301 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.ClassicGUI |
| PRF_DCP_PRF.TIPS.Database | `d4f82c84-315b-496f-88da-5ca6c69d272d` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Database |
| PRF_DCP_PRF.TIPS.Metadata | `72d8a9df-dcb6-4201-be31-d301dc200c2e` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Metadata |
| PRF_DCP_PRF.TIPS.Reports | `8d3116f3-bea7-43de-8099-fd1e67d6d975` | 49.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Reports |
| PRF_DCP_PRF.TIPS.Web | `079745b8-12ee-4039-aea7-991565864e49` | 874 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_DCP_PRF.TIPS.Web |

### PRF_ENT_PRT  (21 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PRF_ENT_PRT.QPTM.Application.ClassicGUI | `19d2016b-cf8f-4e41-ad2d-ad4eb78150fc` | 50.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Application.ClassicGUI |
| PRF_ENT_PRT.QPTM.Application.ClassicGUICAW | `80f6bec4-28bf-4842-9c7e-6c50dcedf974` | 398 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Application.ClassicGUICAW |
| PRF_ENT_PRT.QPTM.Application.MiddleTier | `cf4529e6-51b5-40f8-b8ea-061a45636707` | 510 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Application.MiddleTier |
| PRF_ENT_PRT.QPTM.Application.QPEC | `6483ae61-386e-499b-ab4e-7306dc262a71` | 695 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Application.QPEC |
| PRF_ENT_PRT.QPTM.Application.Web | `16092162-0af8-46b6-a444-e7d1c36d9b5a` | 60.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Application.Web |
| PRF_ENT_PRT.QPTM.Batch | `9aa3d8e9-b286-41ee-9728-096d5e9512ce` | 153 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Batch |
| PRF_ENT_PRT.QPTM.ClassicBatch | `5479d0f4-aaa3-4242-ad97-ed350544b29b` | 452 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.ClassicBatch |
| PRF_ENT_PRT.QPTM.ClassicGUI | `18aebb5d-6015-4a51-b19e-9100cdff8dba` | 126 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.ClassicGUI |
| PRF_ENT_PRT.QPTM.Database | `0a23c241-ad45-4e16-864f-623017850874` | 30 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Database |
| PRF_ENT_PRT.QPTM.Metadata | `e7b0e01a-b537-4b47-b5d4-4e780864753b` | 3.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Metadata |
| PRF_ENT_PRT.QPTM.Reports | `858f6212-ace2-4a01-b606-c8413384fe56` | 32.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Reports |
| PRF_ENT_PRT.QPTM.Web | `e6e80abb-dcb0-45f3-9013-cd32b73ad619` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.QPTM.Web |
| PRF_ENT_PRT.TIPS.Application.MiddleTier | `06fefd6c-1cc8-47d1-8b60-bb721d5d7092` | 690 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Application.MiddleTier |
| PRF_ENT_PRT.TIPS.Application.QPEC | `918acb88-e7db-4602-a8ed-9b52338bb831` | 446 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Application.QPEC |
| PRF_ENT_PRT.TIPS.Application.Web | `521bc66a-01bd-48d2-b266-d6a291a6010c` | 38.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Application.Web |
| PRF_ENT_PRT.TIPS.Batch | `ea15086d-c510-4ad2-8a01-9af660d897af` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Batch |
| PRF_ENT_PRT.TIPS.ClassicBatch | `c5ce42ec-dabd-44c2-b538-158bf4e39234` | 821 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.ClassicBatch |
| PRF_ENT_PRT.TIPS.Database | `7bfb325f-0fee-41a8-b807-dc6ce89c4d74` | 27 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Database |
| PRF_ENT_PRT.TIPS.Metadata | `a3089149-d867-41d4-9d8d-e5c334a4d1b4` | 4.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Metadata |
| PRF_ENT_PRT.TIPS.Reports | `68dc7e4c-853a-451f-8258-8489e003b185` | 31.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Reports |
| PRF_ENT_PRT.TIPS.Web | `c06b262b-bec0-4c9c-8c88-92ae8b3bd6fc` | 368 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ENT_PRT.TIPS.Web |

### PRF_ONM_PRF  (8 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PRF_ONM_PRF.TIPS.Application.MiddleTier | `08ed3785-3239-48cf-8750-6f4648bdd721` | 982 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Application.MiddleTier |
| PRF_ONM_PRF.TIPS.Application.QPEC | `ef841915-7b19-4a45-a4c1-ba0ef533065d` | 897 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Application.QPEC |
| PRF_ONM_PRF.TIPS.Application.Web | `bdbeaf29-cf13-4ef8-92fc-da1f029b3c80` | 54.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Application.Web |
| PRF_ONM_PRF.TIPS.ClassicBatch | `84d03d44-02fe-4a69-9128-d90d63154959` | 326 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.ClassicBatch |
| PRF_ONM_PRF.TIPS.Database | `2532a82e-d686-44e9-b56c-025b6e7b5e36` | 384 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Database |
| PRF_ONM_PRF.TIPS.Metadata | `e862f052-3b02-409a-a8ac-259af1127fa8` | 39.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Metadata |
| PRF_ONM_PRF.TIPS.Reports | `5a82bb27-4119-4a23-aff9-dfa3df68da83` | 63.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Reports |
| PRF_ONM_PRF.TIPS.Web | `17963959-116c-4b7a-9dcf-833ac0bf9350` | 1.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_ONM_PRF.TIPS.Web |

### PRF_PEM_PRT  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| PRF_PEM_PRT.TIPS.Application.QPEC | `e3d25616-7c66-4a59-87e6-159c9207caaf` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Application.QPEC |
| PRF_PEM_PRT.TIPS.ClassicBatch | `31350062-9c72-42e6-9074-b811424e77d8` | 147 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.ClassicBatch |
| PRF_PEM_PRT.TIPS.Database | `51bbafec-1d80-4410-a822-d8d857f2c24a` | 199 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Database |
| PRF_PEM_PRT.TIPS.Metadata | `20442c4b-724c-4a2e-bb6a-2200aa6803a7` | 106.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Metadata |
| PRF_PEM_PRT.TIPS.Reports | `616d5ed7-3001-44ff-ab2e-04aa3b90b839` | 57.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/PRF_PEM_PRT.TIPS.Reports |

### Pembina  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| Pembina.TIPS.Application.Web | `db5da9a1-b724-4cb1-b1c0-c2270e01a260` | 21.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Pembina.TIPS.Application.Web |
| Pembina.TIPS.Web | `e10c9ae2-1f52-4fc2-94ba-8062e9dcfb69` | 216 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/Pembina.TIPS.Web |

### QSM  (3 repos — families: QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| QSM.QGM.Database | `0a03e9c5-76c2-4975-9f42-40b01de02652` | 52 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QSM.QGM.Database |
| QSM.QGM.Metadata | `b4384c87-e1aa-4450-92b8-623e1839be05` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QSM.QGM.Metadata |
| QSM.QGM.Reports | `18f8c46b-78ac-45d0-90e6-f63d7b5dc66b` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QSM.QGM.Reports |

### QXT  (2 repos — families: QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| QXT.QGM.Database | `df2647e5-a2d0-44be-ab67-a1d4459c34fd` | 10 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QXT.QGM.Database |
| QXT.QGM.Metadata | `3dd4dd6b-4999-4589-a616-45caeeaaa589` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/QXT.QGM.Metadata |

### SCT  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SCT.TIPS.Application.QPEC | `e5535a6b-7f83-4b8f-887e-3f6d1b2a400e` | 943 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Application.QPEC |
| SCT.TIPS.ClassicBatch | `83a85419-656f-4fc0-a5cb-ecf8b9733565` | 149 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.ClassicBatch |
| SCT.TIPS.Database | `38e93458-32a4-49d1-81be-1a9d7f17ceb1` | 346 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Database |
| SCT.TIPS.Metadata | `79207347-1aac-425e-aadb-f99df3755543` | 253 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Metadata |
| SCT.TIPS.Reports | `2c4c2e32-c3f4-4195-820f-e5faf9900d8b` | 53.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCT.TIPS.Reports |

### SCX  (11 repos — families: QGM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SCX.QGM.Database | `427a388f-ddae-4fef-aa1b-8055ab5752e6` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.QGM.Database |
| SCX.QGM.Metadata | `92763626-93a0-4a49-94f1-189c9f65dd8c` | 2.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.QGM.Metadata |
| SCX.QGM.Reports | `29fcbaec-32b7-4756-9797-c02908903539` | 4.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.QGM.Reports |
| SCX.TIPS.Application.MiddleTier | `a3edc915-4c8a-43c1-9842-265f87e72386` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Application.MiddleTier |
| SCX.TIPS.Application.QPEC | `714e6e5a-5942-4503-9753-d7787c3de984` | 2.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Application.QPEC |
| SCX.TIPS.Application.Web | `37334184-dd46-44f0-b08a-d969146e2b45` | 49.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Application.Web |
| SCX.TIPS.Batch | `107a5944-dc0c-4c21-8928-f870d61ce1c9` | 36 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Batch |
| SCX.TIPS.Database | `0c50a049-7b76-43d1-a282-d031001114c7` | 67 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Database |
| SCX.TIPS.Metadata | `ce517e9f-a7b2-4da0-a279-35bedfb76e3b` | 23.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Metadata |
| SCX.TIPS.Reports | `a10935a2-32d2-4977-bb01-1b72e0ef03f1` | 21.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Reports |
| SCX.TIPS.Web | `91bd0b58-ddd2-48a2-a501-3a606b94ca50` | 280 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SCX.TIPS.Web |

### SEM  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SEM.TIPS.Application.QPEC | `7acde4ed-1e7f-4925-917a-1334e1f64c61` | 2.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Application.QPEC |
| SEM.TIPS.ClassicBatch | `44acaf4b-7b89-4cf1-aff1-072a7a3ef0d6` | 289 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.ClassicBatch |
| SEM.TIPS.Database | `089c2776-dd7b-4aa5-918c-28a725e7b918` | 257 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Database |
| SEM.TIPS.Metadata | `bd0e5861-7721-4ba3-935a-9d518484fa54` | 845 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Metadata |
| SEM.TIPS.Reports | `8a16915a-98a7-4906-8888-ea6c84ea5a73` | 25.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SEM.TIPS.Reports |

### SPR  (5 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SPR.TIPS.Application.QPEC | `b19969f9-9b49-4b7a-b05b-f68d88d96ff1` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Application.QPEC |
| SPR.TIPS.ClassicBatch | `902c2a62-2b42-46d1-9aae-f366d6ffc388` | 69 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.ClassicBatch |
| SPR.TIPS.Database | `48e1209e-e25a-47ab-b61c-381cbc0285b8` | 11 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Database |
| SPR.TIPS.Metadata | `3843b44f-a235-45c5-9219-1bf8e099dd9a` | 45 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Metadata |
| SPR.TIPS.Reports | `401c8fda-b884-43d5-9f52-cde9486177f4` | 15.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SPR.TIPS.Reports |

### SRB  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SRB.TIPS.Database | `72be6380-ba2b-4fd0-917c-071954fd9cb2` | 226 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRB.TIPS.Database |
| SRB.TIPS.Metadata | `4a8bc3fc-b4a0-4b33-a278-350c78704db6` | 6.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRB.TIPS.Metadata |
| SRB.TIPS.Reports | `f432d9e8-084c-43ee-a818-d70aa750467f` | 26.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRB.TIPS.Reports |

### SRC  (11 repos — families: QEMS, QGM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SRC.QEMS.Database | `54423d23-d857-4a66-8ce8-32c4cbb54d9d` | 37 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.QEMS.Database |
| SRC.QEMS.Metadata | `ccd6abb7-63b6-41fc-af3b-317afbe306a3` | 56 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.QEMS.Metadata |
| SRC.QEMS.Reports | `63f42b91-6499-4440-a454-8b625c76a9e7` | 4.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.QEMS.Reports |
| SRC.QGM.Database | `ce9a5869-af89-4487-b444-07e81b3dcc1c` | 42 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.QGM.Database |
| SRC.QGM.Metadata | `c8d06dba-10f9-4d0f-aac9-19ef9e86f21b` | 38 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.QGM.Metadata |
| SRC.QGM.Reports | `d4e18efd-c46b-4950-8ea9-159fb5f43ff6` | 4.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.QGM.Reports |
| SRC.TIPS.Application.QPEC | `478d2384-022e-48ee-a614-4c037ee20cc9` | 2.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Application.QPEC |
| SRC.TIPS.ClassicBatch | `f2a968cd-86f5-41ee-bc55-74c3985b1a27` | 66 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.ClassicBatch |
| SRC.TIPS.Database | `c553d2ba-e873-4bf8-ac60-c22dacf8eddd` | 50 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Database |
| SRC.TIPS.Metadata | `2a71cfbc-f451-43bd-bb03-82969d2112ef` | 886 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Metadata |
| SRC.TIPS.Reports | `e8e9df93-a315-4b28-bece-c9acd1b34391` | 17.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRC.TIPS.Reports |

### SRI  (2 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SRI.TIPS.Database | `79139198-42f3-474e-b80f-4dfcbc94b01b` | 89 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRI.TIPS.Database |
| SRI.TIPS.Metadata | `6fc0f754-27c9-463b-8445-0f49c2a51c6a` | 64 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SRI.TIPS.Metadata |

### SUI  (8 repos — families: QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| SUI.QGM.Database | `0800f8cd-adac-4203-8ec5-dc6ddaaba9e8` | 64 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QGM.Database |
| SUI.QGM.Metadata | `b9eb6ff2-440a-463c-8f1d-8d59dbb21aeb` | 46 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QGM.Metadata |
| SUI.QGM.Reports | `46e4c9e7-ebad-46ab-8de0-6c262807196a` | 6.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QGM.Reports |
| SUI.QPTM.Application.QPEC | `2615f953-afd1-438a-90c7-6f6ae62a30a8` | 3.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QPTM.Application.QPEC |
| SUI.QPTM.ClassicBatch | `b148dbc6-fb6f-4cb6-86d4-9442e6f675dc` | 194 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QPTM.ClassicBatch |
| SUI.QPTM.Database | `ad7d3407-6269-4d04-bde6-8d406d274df9` | 3.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QPTM.Database |
| SUI.QPTM.Metadata | `4da8dbe2-4c6d-44c7-8654-479dec4c4a73` | 136 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QPTM.Metadata |
| SUI.QPTM.Reports | `2c5870e7-a7fa-44c3-a506-9ba25e23ce05` | 24.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/SUI.QPTM.Reports |

### TAU  (3 repos — families: QEMS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| TAU.QEMS.Database | `d6d72639-7a2f-4287-ac8e-7ede6864fd11` | 14 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TAU.QEMS.Database |
| TAU.QEMS.Metadata | `8ccf1389-85fe-435e-ac0f-aafe595ff229` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TAU.QEMS.Metadata |
| TAU.QEMS.Reports | `83ef32c2-0682-4779-8f50-9eff809cd3ef` | 13.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TAU.QEMS.Reports |

### TCP  (9 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| TCP.TIPS.Crude.Application.MiddleTier | `084ea748-4a1e-4e27-98c4-3f8195628259` | 547 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Application.MiddleTier |
| TCP.TIPS.Crude.Application.QPEC | `a52aabeb-7f12-40b9-a12f-fa2a04c2121f` | 804 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Application.QPEC |
| TCP.TIPS.Crude.Application.Web | `f621ba6a-ef11-47d0-b92b-b3788cf934f1` | 33.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Application.Web |
| TCP.TIPS.Crude.Batch | `6958943e-bb97-4c4a-98de-7656e2a00a9d` | 244 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Batch |
| TCP.TIPS.Crude.ClassicBatch | `2e811fe6-3b7d-4c00-83e9-82cacef0f877` | 81 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.ClassicBatch |
| TCP.TIPS.Crude.Database | `0c53f195-e40c-423f-aede-dfbb10874261` | 71 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Database |
| TCP.TIPS.Crude.Metadata | `72115373-7986-4579-bfa5-8a1cd6990dda` | 62.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Metadata |
| TCP.TIPS.Crude.Reports | `a4a6a0cf-16fb-4d41-b80d-11508f08d7f9` | 23.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Reports |
| TCP.TIPS.Crude.Web | `9618a384-dfd3-4001-940f-3a69c6fc7d32` | 209 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TCP.TIPS.Crude.Web |

### TEC  (8 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| TEC.QPTM.Application.MiddleTier | `5f762ed6-9df4-45d7-b23e-ddb87ad89274` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Application.MiddleTier |
| TEC.QPTM.Application.QPEC | `17c2f1c4-43d8-483d-9039-e67531cfc374` | 996 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Application.QPEC |
| TEC.QPTM.Application.Web | `9efe117a-5892-41ff-90b2-5b6fabebc627` | 84.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Application.Web |
| TEC.QPTM.Batch | `a448f26e-4331-45bf-b3ca-45c5f7f60736` | 426 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Batch |
| TEC.QPTM.Database | `232c7447-e06d-41cb-bc29-3399affe0335` | 196.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Database |
| TEC.QPTM.Metadata | `f66a6872-f0c9-4630-888a-cb195c78f256` | 13.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Metadata |
| TEC.QPTM.Reports | `6630e45d-40bf-4f9d-97cd-d539d06675c1` | 27.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Reports |
| TEC.QPTM.Web | `c8d40342-0161-4a3f-8924-8c0ca8899c49` | 11.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEC.QPTM.Web |

### TEP  (10 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| TEP.QPTM.Application.MiddleTier | `a343ef51-a8f1-4e49-8f28-883563a813b1` | 1.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Application.MiddleTier |
| TEP.QPTM.Application.QPEC | `b1912ae9-2764-454e-8f50-1ff5e748c0b6` | 2.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Application.QPEC |
| TEP.QPTM.Application.Web | `53d185a8-32db-4bb1-9488-2be6f145e746` | 76.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Application.Web |
| TEP.QPTM.Batch | `f8d0ce56-b497-406a-880a-4f47134e3c39` | 701 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Batch |
| TEP.QPTM.ClassicBatch | `2d3d351f-0409-485c-82c3-3853dd0f2501` | 314 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.ClassicBatch |
| TEP.QPTM.ClassicGUI | `aafb7c40-6a47-458a-8951-5a9db7f72469` | 16 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.ClassicGUI |
| TEP.QPTM.Database | `eef218c3-9e4d-41d4-8768-543bafbdcd3c` | 557 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Database |
| TEP.QPTM.Metadata | `c5587b2a-060e-44e0-9a80-33b5e601c374` | 3.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Metadata |
| TEP.QPTM.Reports | `7079db2a-6668-46d1-97d8-359d80f8b55b` | 48.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Reports |
| TEP.QPTM.Web | `346eaa60-6bb6-46a4-9670-0ae8dfa251aa` | 1.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TEP.QPTM.Web |

### TGL  (9 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| TGL.QPTM.Application.MiddleTier | `9ca1f13b-45bf-4b5d-8f94-cf4ed89da19f` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Application.MiddleTier |
| TGL.QPTM.Application.QPEC | `16dddb55-e0d0-4b70-9eec-0bdd558ad258` | 1.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Application.QPEC |
| TGL.QPTM.Application.Web | `813fb12f-f1f1-4fc7-9c0d-2f1ec8f96478` | 70.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Application.Web |
| TGL.QPTM.Batch | `4267307b-3f09-46d6-9e04-4e54478c10a4` | 127 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Batch |
| TGL.QPTM.ClassicBatch | `93cb1bc0-db8c-4d5e-a830-a0511ce3ed80` | 102 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.ClassicBatch |
| TGL.QPTM.Database | `62b2a2a9-dbc2-4781-aed0-b279d19b789a` | 82 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Database |
| TGL.QPTM.Metadata | `b23f7e96-a975-4cf9-a1f1-9702dda757ae` | 1.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Metadata |
| TGL.QPTM.Reports | `032066b4-0c56-42bc-9ed1-6112fb7f9793` | 26.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Reports |
| TGL.QPTM.Web | `3ac1d43f-0d15-4ec9-bf52-ce985b0c40a6` | 1.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGL.QPTM.Web |

### TGO  (16 repos — families: QEMS, QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| TGO.QEMS.Application.Listeners | `55b261ca-ed89-4230-b4be-abba23ac136d` | 299 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Application.Listeners |
| TGO.QEMS.Application.MiddleTier | `062aebb6-56b3-43ec-a532-a4957e1cf18d` | 434 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Application.MiddleTier |
| TGO.QEMS.Application.QPEC | `c226d8d6-ae9e-408f-b12f-340b9a3d02c0` | 269 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Application.QPEC |
| TGO.QEMS.Application.Web | `91d786ce-7c08-4ea5-96fd-384b4d481d28` | 19.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Application.Web |
| TGO.QEMS.Application.WPF | `2dbc05fe-ceb9-4a35-be2f-bba62b439095` | 21.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Application.WPF |
| TGO.QEMS.Batch | `d1466e73-b9c0-4f8a-a5ff-7c57e9f72014` | 35 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Batch |
| TGO.QEMS.Common | `db411aba-97f7-4e7e-b537-3dfd0edc853c` | 4.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Common |
| TGO.QEMS.Database | `85952b33-a9c7-4b40-b9e8-e19d037b08cd` | 38 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Database |
| TGO.QEMS.Metadata | `2605136e-4a73-4e5e-b36c-53e00e3f81e9` | 2.6 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Metadata |
| TGO.QEMS.Reports | `cf70301a-6b11-4019-867a-f7c8ace5ca20` | 14.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Reports |
| TGO.QEMS.Web | `f030a1d1-2c4a-4957-a987-080fd5e15f36` | 205 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QEMS.Web |
| TGO.QGM.Application.QPEC | `5da5738d-c5a1-4ec3-8af5-8f85af9dd760` | 572 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QGM.Application.QPEC |
| TGO.QGM.ClassicBatch | `990bf890-93ec-4536-b43a-e69c06215010` | 63 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QGM.ClassicBatch |
| TGO.QGM.Database | `cca3ce5b-298a-4d3d-b37e-3484938cbdb1` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QGM.Database |
| TGO.QGM.Metadata | `d1605351-99c5-40c7-941a-16913704a230` | 5 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QGM.Metadata |
| TGO.QGM.Reports | `73cdf30c-29d4-4f73-b78e-830d50f2d262` | 3.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/TGO.QGM.Reports |

### UGI  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| UGI.TIPS.Database | `3bb1a103-6657-417a-8143-873dc4a4928d` | 149 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UGI.TIPS.Database |
| UGI.TIPS.Metadata | `1d4101b7-896b-4fd1-8aa9-a7f68952a32e` | 6.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UGI.TIPS.Metadata |
| UGI.TIPS.Reports | `1d4ca847-bfe6-4f8f-baf6-7af2d6418291` | 22.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UGI.TIPS.Reports |

### UPC  (3 repos — families: QGM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| UPC.QGM.Database | `12581fd3-cdc9-4f10-bb08-c292059568a4` | 9 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UPC.QGM.Database |
| UPC.QGM.Metadata | `18979b38-1007-4b12-a7f0-55e274c7dab8` | 6 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UPC.QGM.Metadata |
| UPC.QGM.Reports | `adc67a3d-41fe-49ec-9b7c-7e7fd5df6d5b` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UPC.QGM.Reports |

### UTG  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| UTG.TIPS.Database | `533a51d8-6c79-44d2-8898-829c713b40ac` | 56 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTG.TIPS.Database |
| UTG.TIPS.Metadata | `ca7b393a-007b-4801-bf8d-be7639970094` | 39 KB | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTG.TIPS.Metadata |
| UTG.TIPS.Reports | `f64d5ef0-4fba-4f56-9115-82e61e7537e9` | 46.1 | master | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTG.TIPS.Reports |

### UTL  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| UTL.QPTM.Database | `687cf99b-539c-4620-ab11-c8eb3e605c46` | 38 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTL.QPTM.Database |
| UTL.QPTM.Metadata | `1db14d38-3d93-4ccb-86d8-1c9978df68a2` | 2.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTL.QPTM.Metadata |
| UTL.QPTM.Reports | `17297530-e97a-4aa1-a9c3-09e756fc889b` | 14.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/UTL.QPTM.Reports |

### VGL  (3 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| VGL.QPTM.Database | `a74c4008-7041-445d-8cab-33b1ee942c64` | 24 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VGL.QPTM.Database |
| VGL.QPTM.Metadata | `2d74d285-0f8e-4aca-ac0e-4ff4a8dabde1` | 2.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VGL.QPTM.Metadata |
| VGL.QPTM.Reports | `c56825aa-5b9d-4378-bdd7-ffd04ffd40c6` | 11.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VGL.QPTM.Reports |

### VGP  (2 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| VGP.QPTM.Database | `030b7b9b-5c94-4214-affd-828d85b8ff7b` | 55 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VGP.QPTM.Database |
| VGP.QPTM.Metadata | `0569a51a-e0da-42a0-8af4-482b615c7e57` | 250 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VGP.QPTM.Metadata |

### VMH  (8 repos — families: QPTM, TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| VMH.QPTM.Database | `2b6bbfff-78ec-4c89-929b-5c6e12dac80b` | 81 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.QPTM.Database |
| VMH.QPTM.Metadata | `7ca0a7aa-eaa4-490b-8215-cb41b5553c4f` | 33 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.QPTM.Metadata |
| VMH.QPTM.Reports | `5e49a2af-8ec8-47bf-a2a3-617f8d295fef` | 1.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.QPTM.Reports |
| VMH.TIPS.Application.QPEC | `41430fc5-d663-4788-9c24-4f4f4ec49a02` | 6.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Application.QPEC |
| VMH.TIPS.ClassicBatch | `618abd14-73ff-4c5d-94a5-9b56fe2d87ff` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.ClassicBatch |
| VMH.TIPS.Database | `de6eca19-6339-4531-881a-50536e7cd8fa` | 592 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Database |
| VMH.TIPS.Metadata | `beff584a-a62d-4dc2-8a20-8cc7af7b805b` | 154 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Metadata |
| VMH.TIPS.Reports | `ebc8c91c-fcd5-44fc-abc0-efe96963f0bf` | 23.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/VMH.TIPS.Reports |

### WIT  (2 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| WIT.QPTM.Database | `aaf7cdd1-b507-4d86-934c-8125a747354c` | 75 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WIT.QPTM.Database |
| WIT.QPTM.Metadata | `c70d306c-24cc-4da0-bfcc-1c738cda5252` | 28 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WIT.QPTM.Metadata |

### WPC  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| WPC.TIPS.Database | `bf067244-377f-42a9-9f79-cbf3348f8895` | 13 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WPC.TIPS.Database |
| WPC.TIPS.Metadata | `bef963ed-d5f4-44a7-a709-368e6259546e` | 40 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WPC.TIPS.Metadata |
| WPC.TIPS.Reports | `5c3f93b5-38b5-4c82-a326-5c0a0236f0b7` | 1.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WPC.TIPS.Reports |

### WTG  (8 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| WTG.TIPS.Application.MiddleTier | `14b708f9-e22a-4cbe-977a-71062ff9d41d` | 2.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Application.MiddleTier |
| WTG.TIPS.Application.QPEC | `24377e00-9d44-4f88-bf34-4a12e17567b4` | 5.8 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Application.QPEC |
| WTG.TIPS.Application.Web | `0187266e-06b5-49e4-aea5-a02c8093989e` | 61.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Application.Web |
| WTG.TIPS.ClassicBatch | `0e0280a5-f8ee-4098-9667-a1ae8c1bb87c` | 120 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.ClassicBatch |
| WTG.TIPS.Database | `98a322ba-9e86-4408-bb18-94be58c5f0a0` | 99 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Database |
| WTG.TIPS.Metadata | `8a20b27b-51e2-4149-96a9-8361aa3e5d95` | 146 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Metadata |
| WTG.TIPS.Reports | `2cb327cd-1264-4858-8c47-e447593b7f33` | 19.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Reports |
| WTG.TIPS.Web | `f5e9d712-3a0d-483b-a5d1-6b52d6389a4b` | 500 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WTG.TIPS.Web |

### WWM  (6 repos — families: QGM, QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| WWM.QGM.Database | `ca87c056-4b7f-4dac-9710-92668e6b681f` | 57 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WWM.QGM.Database |
| WWM.QGM.Metadata | `e3e2fdab-fcd6-40a0-82c4-69ef36d6cbb8` | 25 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WWM.QGM.Metadata |
| WWM.QGM.Reports | `aabd4d8e-c04e-4971-9a33-e8c3071c2779` | 4.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WWM.QGM.Reports |
| WWM.QPTM.Database | `d47cc2d6-f37a-49bd-8c95-b9ec655cf8e7` | 296 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WWM.QPTM.Database |
| WWM.QPTM.Metadata | `7c6b83f8-1463-4cfa-a799-de0d548d7aaf` | 24.5 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WWM.QPTM.Metadata |
| WWM.QPTM.Reports | `2dfa42f3-cce3-4420-aefc-ccb0f10353a7` | 32.7 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/WWM.QPTM.Reports |

### XCL  (8 repos — families: QPTM)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| XCL.QPTM.Application.MiddleTier | `892d07c7-e644-48ac-9767-76b802674a2a` | 740 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Application.MiddleTier |
| XCL.QPTM.Application.QPEC | `da9dfa47-3885-4651-992d-14e26c05e916` | 554 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Application.QPEC |
| XCL.QPTM.Application.Web | `e6973d61-3560-4567-bc7d-7996c29a7357` | 34.4 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Application.Web |
| XCL.QPTM.Batch | `d866d0cd-8f71-4c6d-a756-1ec1978b60be` | 75 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Batch |
| XCL.QPTM.Database | `bd2abeb2-207b-41bc-8b59-dba763ed7847` | 392 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Database |
| XCL.QPTM.Metadata | `b70bf900-e207-4122-820a-2871bc578655` | 77.9 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Metadata |
| XCL.QPTM.Reports | `42172488-f151-4761-8e9e-1cde5f2b5ba0` | 19.3 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Reports |
| XCL.QPTM.Web | `43c9fe4f-e14b-44fc-a1e7-3069e01e91f9` | 11.1 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XCL.QPTM.Web |

### XMG  (3 repos — families: TIPS)

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| XMG.TIPS.Database | `9c6f2f5e-5b01-41d0-a6ee-10b53f43d944` | 26 KB | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XMG.TIPS.Database |
| XMG.TIPS.Metadata | `ec4ed5fa-5f08-4849-ba22-b793b4114fff` | 5.2 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XMG.TIPS.Metadata |
| XMG.TIPS.Reports | `468f3012-ef31-4f78-8cfb-7111ae7bbe88` | 18.0 | develop | https://dev.azure.com/QuorumSoftware/QuorumSoftware/_git/XMG.TIPS.Reports |

## 6. Resolved Gaps from `REPO_REFERENCE.md`

`REPO_REFERENCE.md` had several repo IDs marked **(search needed)**. Resolved below from the live API.

### 6a. QPTM base gaps

| Repo | Status in REPO_REFERENCE | Resolved Repo ID |
|------|--------------------------|------------------|
| Quorum.QPTM.ClassicGUI | (search needed) | `e6d98ba8-ff7f-441c-bdbb-3c9a4605d5a9` |
| Quorum.QPTM.Metadata | (search needed) | `1ae5387f-7703-4db6-9f27-7e5f5202ca6e` |

### 6b. Client QPTM Web repo gaps

`REPO_REFERENCE.md` only had EQT's Web ID. Resolved `<CLIENT>.QPTM.Web` IDs (where the repo exists):

| Client | `<CLIENT>.QPTM.Web` Repo ID |
|--------|------------------------------|
| EQT (already known) | `f29cf1be-dcaa-45ec-b721-dc4a5f06bfa8` |
| DUT | `58c3259a-05f9-4dec-919a-4c4b4f672514` |
| QTR | `f88e203c-e566-46d5-a868-8f714bc01b19` |
| NMGC | `118b3c20-04ad-436f-a20a-36b39b1f9e87` |
| NMG | `c7e7e19f-9fab-40d9-ae28-a247321a9647` |
| DOH | `0f6acd2e-ac51-41b9-b9be-d88dfa8e38be` |
| ENT | `12e21544-0649-4b2d-b4a0-27a63ccf6eea` |
| DRS | `a6968e36-8ecf-4107-b9f0-cf2778ef2dd1` |
| ONG | `54c52e8d-de64-4386-805c-fc0f654c2961` |
| ONK | `59eda16f-9765-40f5-b46f-a55ff76407c4` |

### 6c. Already-resolved IDs in `REPO_REFERENCE.md` (verified against live API)

| Repo | REPO_REFERENCE ID | Live API ID | Match |
|------|-------------------|-------------|-------|
| Quorum.QPTM.Web | `41e317c0-844c-4728-98da-529092957738` | `41e317c0-844c-4728-98da-529092957738` | yes |
| Quorum.QPTM.Batch | `e024d80b-5c45-411c-93e1-78e2798ed885` | `e024d80b-5c45-411c-93e1-78e2798ed885` | yes |
| Quorum.QPTM.ClassicBatch | `0587e2fb-0f37-4614-991b-1d4072eb0255` | `0587e2fb-0f37-4614-991b-1d4072eb0255` | yes |
| Quorum.QPTM.AT | `cf9d975f-c0b4-4e08-ab4c-6d0537b3d8d9` | `cf9d975f-c0b4-4e08-ab4c-6d0537b3d8d9` | yes |
| APL.QPTM.Application.Web | `2ddf8637-1641-43e6-a72d-fe2f597058ad` | `2ddf8637-1641-43e6-a72d-fe2f597058ad` | yes |
| APL.QPTM.Application.MiddleTier | `d45a6e0f-5c7d-4a18-bc42-47f8728fc445` | `d45a6e0f-5c7d-4a18-bc42-47f8728fc445` | yes |
| APL.QPTM.Application.QPEC | `d8402baa-bb33-44cb-950d-3cef9e0da1b9` | `d8402baa-bb33-44cb-950d-3cef9e0da1b9` | yes |
| APL.QPTM.Batch | `98d13405-7cea-4fe8-9d6e-8f684f59dee9` | `98d13405-7cea-4fe8-9d6e-8f684f59dee9` | yes |
| APL.QPTM.Database | `2e1fb9e5-a46a-4257-b99a-fd47721dd399` | `2e1fb9e5-a46a-4257-b99a-fd47721dd399` | yes |
| APL.QPTM.Metadata | `30db596b-2d1e-469a-b3a0-6ef2db3f8bee` | `30db596b-2d1e-469a-b3a0-6ef2db3f8bee` | yes |
| APL.QPTM.Web | `ffa5745e-d1c5-410c-bb42-75b1efa87a58` | `ffa5745e-d1c5-410c-bb42-75b1efa87a58` | yes |
| Quorum.EDI.Framework | `02742829-b8c5-4531-bb27-163f9a501621` | `02742829-b8c5-4531-bb27-163f9a501621` | yes |
| Quorum.EDIServ | `30cdad90-e4ae-405c-8d67-747955bcf870` | `30cdad90-e4ae-405c-8d67-747955bcf870` | yes |
| Quorum.QGM.Database | `8bfba59c-f3dd-46ea-8d0a-f2687a763258` | `8bfba59c-f3dd-46ea-8d0a-f2687a763258` | yes |
| Quorum.QGM.Batch | `f6a6c380-ed74-4860-835b-d58c462c3e9f` | `f6a6c380-ed74-4860-835b-d58c462c3e9f` | yes |
| EQT.QPTM.Web | `f29cf1be-dcaa-45ec-b721-dc4a5f06bfa8` | `f29cf1be-dcaa-45ec-b721-dc4a5f06bfa8` | yes |

## 7. Other Projects (full enumeration)

### 7a. QuorumServices — 33 repos

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| Midstream - Dev Team | `2f0c5df8-0838-4a76-9fcc-0ec473e32c88` | 12 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Midstream%20-%20Dev%20Team |
| PS Dashboard | `8f2099d8-edbf-49b1-91e6-97f2e6bb2d0e` | 1.5 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/PS%20Dashboard |
| Quorum.COE.Environments | `8bf16f91-62dc-4497-a15f-a700c4d77a49` | 4.5 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.COE.Environments |
| Quorum.Conversion | `ea237419-f23c-4b53-a33c-f334d9ea62ea` | 5 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Conversion |
| Quorum.DaWinci.Conversion | `8353c15f-2ae9-4ddf-bc5a-275be83a3c76` | 8.3 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.DaWinci.Conversion |
| Quorum.Integration.Documentation | `95602bdd-a190-488a-9c95-e72a3a18c629` | 54.2 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Integration.Documentation |
| Quorum.Landdox.Conversion | `3923a95a-3b03-413a-ba77-6c896748135b` | 47 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Landdox.Conversion |
| Quorum.ODA.Conversion | `4dcae24d-3d1f-4412-b81e-5db3a698def2` | 9.3 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.ODA.Conversion |
| Quorum.ODL.Conversion.Scripts | `644a8492-822e-4067-a33c-bb9d0c411bd4` | 6.7 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.ODL.Conversion.Scripts |
| Quorum.QGM.Conversion | `9729176e-1aba-463d-9656-6477bdf041c7` | 21 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.QGM.Conversion |
| Quorum.QLS.Conversion | `29010c80-7646-4330-9b20-4d75e7c91dff` | 73.0 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.QLS.Conversion |
| Quorum.QPTM.Conversion | `01610f11-9d52-410c-ac44-9289cece8b3a` | 7.7 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.QPTM.Conversion |
| Quorum.QQM.Documentation | `f0182d78-9f18-4b1d-8b5f-69f4a1b1a0fe` | 1 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.QQM.Documentation |
| Quorum.RapidConversionTeam | `d234505b-43a0-497f-a113-2e4998d6fb4b` | 1 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.RapidConversionTeam |
| Quorum.TIPS.Conversion | `f9001756-ac82-4020-a267-c26e73dd8b11` | 252.0 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.TIPS.Conversion |
| Quorum.Tools.AI | `61e44996-999d-46a7-811c-ea5a03ab06b4` | 14 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.AI |
| Quorum.Tools.DataComparison | `ec370dc1-ef22-440f-a7ae-e93200ff2375` | 13.7 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.DataComparison |
| Quorum.Tools.DataConversionInitiatives | `6356434c-c7c7-4ac8-82aa-2a33d3f7aba6` | 18.6 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.DataConversionInitiatives |
| Quorum.Tools.DataYanker | `7a1de2d4-fea4-4f5a-bfad-fb26ff31f340` | 1.9 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.DataYanker |
| Quorum.Tools.DBPasswordChangeTool | `73b6b557-4445-44c1-91ab-4d4e08b6331f` | 3.7 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.DBPasswordChangeTool |
| Quorum.Tools.EnvironmentValidation | `8b3f920c-233a-4b17-9d10-d6502e73196a` | 8 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.EnvironmentValidation |
| Quorum.Tools.FastDataCopy | `68394168-a882-4831-85d4-c95174b66a00` | 2.5 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.FastDataCopy |
| Quorum.Tools.ImportExport | `020a7cc1-6999-43a0-acbb-3bcf274ffc0d` | 6.8 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.ImportExport |
| Quorum.Tools.ServicesSubscription | `74c7f138-4348-4531-bf99-53f6e189fb6c` | 0 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.ServicesSubscription |
| Quorum.Tools.SQLBlaster | `e95a1d91-a280-4fcf-b9db-f75f26de5ef4` | 63 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.SQLBlaster |
| Quorum.Tools.SQLBuilder | `9d62b72d-f287-4d6b-be40-a50657982d02` | 44 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Tools.SQLBuilder |
| Quorum.UpgradeTeam.NFLBAnalysis | `2283512c-a5ab-4116-86b3-56ec51455bd5` | 121 KB | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.UpgradeTeam.NFLBAnalysis |
| Quorum.UpgradeTeam.Scripts | `57c59210-ce17-48a0-98f9-92cc701684c5` | 8.9 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.UpgradeTeam.Scripts |
| Quorum.UpgradeTeam.TechnicalAssessment | `364d644a-a168-4148-bc7c-b99c94675bd9` | 1.3 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.UpgradeTeam.TechnicalAssessment |
| Quorum.UpgradeTeam.TechnicalAssessment.Results | `556747ab-f5ec-484d-bcd7-7c36181be7f8` | 3984.5 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.UpgradeTeam.TechnicalAssessment.Results |
| Quorum.UpgradeTeam.UpgradeToolManager | `d438c0e8-3b47-490e-a98a-015e864824d9` | 8.9 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.UpgradeTeam.UpgradeToolManager |
| Quorum.Upstream.Conversion | `69442914-8c4a-46a7-9a8e-33aab80cc682` | 133.6 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/Quorum.Upstream.Conversion |
| QuorumServices | `cf64e3da-501c-4e23-825d-fbf218449468` | 7.3 | master | https://dev.azure.com/QuorumSoftware/QuorumServices/_git/QuorumServices |

### 7b. myQuorum Cloud — 4 repos

| Repo Name | Repo ID | Size (MB) | Default Branch | Web URL |
|-----------|---------|-----------|----------------|---------|
| Cloud Delivery Automation | `19588d37-74f0-40f8-a69f-63dcbe1d188a` | 134 KB | master | https://dev.azure.com/QuorumSoftware/myQuorum%20Cloud/_git/Cloud%20Delivery%20Automation |
| Global Cloud Operations Center | `96cb668f-cc18-4028-bcb7-6c66f77cf743` | 1 KB | master | https://dev.azure.com/QuorumSoftware/myQuorum%20Cloud/_git/Global%20Cloud%20Operations%20Center |
| myQuorum Cloud | `7295eedc-cbf0-4465-93ca-0a0dbdf4aa6a` | 327 KB | master | https://dev.azure.com/QuorumSoftware/myQuorum%20Cloud/_git/myQuorum%20Cloud |
| myQuorum Scripts | `1a636044-eec4-486f-9264-1126d27e9501` | 51 KB | master | https://dev.azure.com/QuorumSoftware/myQuorum%20Cloud/_git/myQuorum%20Scripts |

---

## Notes

- **Repos enumerated in this document (QPTM/TIPS/EDI/DB/client + other projects): 928.**
- QuorumSoftware contains 3,342 total repos; the 2451 not listed belong to unrelated products (Upstream, QEMS-only utilities, QGIS, QFC, ESuite, DataHub, etc.) and infra/tooling.
- To regenerate: `GET /_apis/git/repositories?api-version=7.0` per project (URL-encode `myQuorum Cloud` as `myQuorum%20Cloud`).