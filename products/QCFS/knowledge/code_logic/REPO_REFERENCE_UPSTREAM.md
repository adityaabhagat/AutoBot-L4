# Repository & Architecture Orientation — Quorum Upstream Accounting

> Products covered: **Revenue Accounting (QRA)**, **Cost Accounting (QCA)**, **Division Order (QDO)**, **Financial Accounting (QCFS)** — the myQuorum / On Demand upstream suite, plus the **eSuite** classic platform and the **QDOD** (Division Order Desktop) classic product.
> Generated 2026-06-14 for L4 support, from live Azure DevOps API enumeration of projects `QuorumSoftware`, `QuorumServices`, and `myQuorum Cloud`.
> Credentials are NOT in this file — see `CONNECTION_CONFIG.md` (Mid L4 Assistant project) for the PAT.
> Repo IDs and default branches below are exactly as returned by `GET /_apis/git/repositories`. Only repos that actually exist in the org are listed; nothing is fabricated.

---

## 0. Is upstream-accounting code in this ADO org?

**Yes.** Upstream accounting is fully present in `QuorumSoftware` ADO. It is NOT a separate org or a hosted-only product. The code lives under three naming families in the `QuorumSoftware` project:

- `Quorum.Upstream.*` — the modern **myQuorum / On Demand** web suite (shared platform + QRA / QCA / QDO / QCFS modules).
- `Quorum.ESuite.*` — the **eSuite** classic platform that underpins the suite.
- `Quorum.QDOD.*` — the standalone **Division Order Desktop** classic product.

`QuorumServices` holds only conversion/migration tooling (e.g. `Quorum.Upstream.Conversion`, `Quorum.ODA.Conversion`, `Quorum.Landdox.Conversion`) — no product source. `myQuorum Cloud` (4 repos) holds cloud delivery/ops automation, not upstream product code.

### Counts (accounting-relevant repos only)

| Family | Repos |
|--------|------:|
| `Quorum.*` base / platform (Upstream + ESuite + QDOD + product AT/Events) | 124 |
| Client-prefixed (`<CLIENT>.Upstream.*`, `<CLIENT>.ESuite.*`, `<CLIENT>.QDOD.*`) | ~1,052 across **215** distinct client codes |
| Upstream tooling in `QuorumServices` | `Quorum.Upstream.Conversion` (+ shared conversion repos) |

> The 124 `Quorum.*` base repos are the ones you read for product behavior/root cause. Client-prefixed repos hold per-tenant `Database` / `Metadata` / `Reports` overrides (occasionally `Application.*` customizations) — analogous to QPTM/TIPS client repos.

---

## 1. How the upstream suite is structured

It is a **shared platform with per-module products**, mirroring the QPTM/TIPS layering you already know but with an extra layer (eSuite classic underneath the modern web modules).

```
Quorum.Upstream.*                  ← modern myQuorum / On Demand web suite
├── Quorum.Upstream.Shared.*       ← cross-module business logic (Batch, ClassicBatch, ClassicGUI, Web)
├── Quorum.Upstream.Database       ← shared upstream DB schema (the common backbone)
├── Quorum.Upstream.Metadata       ← shared metadata (grids, picklists, screens) — 4 GB, largest repo
├── Quorum.Upstream.Reports        ← shared report definitions
├── Quorum.Upstream.Application.*  ← shared app shells: MiddleTier, ClassicGUI, QPEC, MaintenanceApp
└── per-module products:
    ├── Quorum.Upstream.QRA.*      ← Revenue Accounting
    ├── Quorum.Upstream.QCA.*      ← Cost Accounting
    ├── Quorum.Upstream.QDO.*      ← Division Order (web)
    └── Quorum.Upstream.QCFS.*     ← Financial Accounting (Cash/Financials)

Quorum.ESuite.*                    ← eSuite classic platform (older GUI + services the suite builds on)
Quorum.QDOD.*                      ← Division Order Desktop (standalone classic product, full stack)
```

Every product module repeats the **same per-module repo set** (the "tier" pattern). For module `M` ∈ {QRA, QCA, QDO, QCFS} you will find:

| Repo suffix | Layer / purpose |
|-------------|-----------------|
| `.Application.Web` | ASP.NET MVC web front end (Views, Scripts, APIControllers, DesignStudio components) |
| `.Application.MiddleTier` | Service host / middle-tier process (hosts business services; `dms-*.csgrp` service-group configs, app.*.config per env) |
| `.Application.APIHost` | REST API host process |
| `.API` / `.API.Specs` | API implementation + OpenAPI/Swagger specs |
| `.Web` | Module web component library (shared MVC/UI building blocks consumed by `.Application.Web`) |
| `.Batch` | Modern batch jobs |
| `.ClassicBatch` | Legacy/classic batch jobs |
| `.ClassicGUI` | Classic Windows GUI screens for the module |
| `.Database` | Module DB schema (tables, packages, views) |
| `.Metadata` | Module metadata (grids, picklists, screen defs) |
| `.Reports` | Module reports (where present) |
| `.Events` / `.EventServices` | Event message contracts + event handlers |
| `.Messaging.Publisher` | Outbound messaging/integration publisher |
| `.DocumentManagement.EventHandlers` | DMS hooks (check images, JE docs, well-completion docs) |
| `.DesignStudio.PackageSource` | DesignStudio low-code package source |
| `.ReleaseNotes` | Per-module release notes (branch: `master`) |

> **Web vs Classic.** Two front-end generations coexist. `*.Application.Web` / `*.Web` is the **modern myQuorum web** UI (the On Demand experience). `*.ClassicGUI` / `*.ClassicBatch` plus the entire `Quorum.QDOD.*` and `Quorum.ESuite.Application.ClassicGUI` family are the **classic** thick-client/legacy generation. When a case screenshot shows a browser, look in `*.Application.Web` / `*.Web`; when it's a desktop form, look in `*.ClassicGUI` / `Quorum.QDOD.*`.
>
> **Where business logic lives.** Service/business logic is hosted from `*.Application.MiddleTier` (and `*.Application.APIHost` for API paths). The MiddleTier solution's source folder (`/<RepoName>/`) holds the host project + service-group (`.csgrp`) configs; the actual service classes are pulled in as referenced projects/packages. Cross-module shared logic is in `Quorum.Upstream.Shared.*`. For UI-layer logic, read `*.Application.Web/{APIControllers,Views,Scripts}` and `*.Web`.

---

## 2. Shared platform repos (`Quorum.Upstream.*`, not module-specific)

Read these first for anything cross-cutting (shared schema, shared batch, common GUI, metadata, document management).

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.Upstream.Database | `a7ab4c86-8968-4094-8d89-fc4c14dd93bc` | 31.5 MB | develop |
| Quorum.Upstream.Metadata | `3c54aeee-6b04-453f-9167-04d2a72361fc` | 4.0 GB | develop |
| Quorum.Upstream.Reports | `c53c13a9-963d-4a3c-90e6-6744db57aac5` | 55.8 MB | develop |
| Quorum.Upstream.Shared.Batch | `5a929509-d66e-4138-8c50-c283b4d79950` | 8.2 MB | develop |
| Quorum.Upstream.Shared.ClassicBatch | `5c630451-62f4-4e7c-ad26-73ccce3404ba` | 560 KB | develop |
| Quorum.Upstream.Shared.ClassicGUI | `cefec727-7c4a-4142-8980-27a9bf971033` | 2.4 MB | develop |
| Quorum.Upstream.Shared.Web | `dfd1999f-84c1-4247-99f5-3feb049da053` | 30.6 MB | develop |
| Quorum.Upstream.Application.MiddleTier | `42b7d994-bd86-48cd-b76b-08812b5cd696` | 508 KB | develop |
| Quorum.Upstream.Application.QPEC | `803312d3-75e9-4a7e-b24c-24c56b219aba` | 12.4 MB | develop |
| Quorum.Upstream.Application.ClassicGUI | `783d819b-c8c2-4140-9ce5-c09380f51382` | 4.2 MB | develop |
| Quorum.Upstream.Application.MaintenanceApp | `154f0932-3d7c-4d06-a78d-2dff8c644ea2` | 612 KB | develop |
| Quorum.Upstream.CheckSignature | `ab27bf39-375d-4c5f-8827-1b0df431e77c` | 69 KB | develop |
| Quorum.Upstream.ESuite.Database | `5336ff92-c75f-4bb8-bef8-850165d68624` | (empty) | master |
| Quorum.Upstream.ESuite.DocumentManagement.EventHandlers | `fc77161b-31e0-4018-afe6-a45312c7ed1c` | 62 KB | develop |
| Quorum.Upstream.Help | `0a484030-3492-44aa-abf3-12175f061644` | 51.3 MB | develop |
| Quorum.Upstream.Platform.Help | `8b63e7b1-9dc3-4dd3-a47c-375848574769` | 1.6 MB | master |
| Quorum.Upstream.Tools | `085a275f-1e83-4197-8c70-8b830b4eda33` | 1.2 MB | master |
| Quorum.Upstream.WebServices_Deprecated | `c0d2cea9-893b-4ec1-9062-2011a81e3621` | 7 KB | master |
| Quorum.Upstream.FailedBuilds | `0c17baa4-cade-424e-88dc-324f2d363ce1` | 8 KB | master |

**Integration / cross-product:**

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.UpstreamOnDemandIntegration.AT | `70080fe1-0fe8-48ba-bb88-172e7c5c93e0` | 595 KB | develop |
| Quorum.UpstreamOnDemandIntegration.PT | `32bbfe52-df4a-44b3-b07c-febb910c8e6c` | 9 KB | master |

---

## 3. QRA — Revenue Accounting

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.Upstream.QRA.Application.Web | `d50d8e16-d33c-4ec0-9602-9a62f604914d` | 56.0 MB | develop |
| Quorum.Upstream.QRA.Web | `213c1de0-fdc3-48ed-ba7d-8e8b468b02b3` | 14.2 MB | develop |
| Quorum.Upstream.QRA.Application.MiddleTier | `263d46a1-66a9-4e78-9211-ff6e8474b09d` | 1.7 MB | develop |
| Quorum.Upstream.QRA.Application.APIHost | `f1da3e84-8338-4478-be79-4a2e1d31a099` | 396 KB | develop |
| Quorum.Upstream.QRA.API | `564e9f88-7bfe-4720-b067-7bef9f34858e` | 3.1 MB | develop |
| Quorum.Upstream.QRA.API.Specs | `243ac085-b4ac-403d-876d-1adab6b63ba4` | 2.6 MB | master |
| Quorum.Upstream.QRA.Batch | `4224bae5-003f-485d-878b-d8e2de5a1528` | 76.3 MB | develop |
| Quorum.Upstream.QRA.ClassicBatch | `18204fa3-fb1c-4414-9054-cba97e6c465b` | 25.9 MB | develop |
| Quorum.Upstream.QRA.ClassicGUI | `d48787c1-a9a6-4d9f-8abe-8a94bee90e6b` | 14.9 MB | develop |
| Quorum.Upstream.QRA.ClassicGui.Tax | `c18bed24-0f68-4607-9f8e-c8ab54b0d4dd` | 141 KB | develop |
| Quorum.Upstream.QRA.Tax | `e3e469b2-27ce-408d-810f-434a47cadceb` | 192 KB | develop |
| Quorum.Upstream.QRA.Database | `f7016d3c-a6ca-411a-aa0c-3653b7d3eac7` | 10.6 MB | develop |
| Quorum.Upstream.QRA.DesignStudio.PackageSource | `29db848f-c763-4dfd-82e1-07a8fe9c772b` | 80 KB | develop |
| Quorum.Upstream.QRA.DocumentManagement.EventHandlers | `03fca8bc-4d95-4f7f-bfda-e14696abe987` | 166 KB | develop |
| Quorum.Upstream.QRA.Events | `24af366f-7513-4fc4-ac95-361c506cc549` | 40 KB | develop |
| Quorum.Upstream.QRA.Messaging.Publisher | `a6962a52-6b45-4691-93e3-178a1193fea7` | 61 KB | develop |
| Quorum.Upstream.QRA.ReleaseNotes | `882d166f-3967-43ab-9689-9bbc44b6898a` | 1.0 MB | master |
| Quorum.QRA.AT | `f0380929-11aa-4114-bd32-cbbb7ca31116` | 426 KB | develop |

> QRA carries a dedicated **Tax** sub-stack (`Quorum.Upstream.QRA.Tax`, `.ClassicGui.Tax`) for severance/production tax — start there for tax-calculation cases.

---

## 4. QCA — Cost Accounting

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.Upstream.QCA.Application.Web | `1dbd1730-3d51-48dc-80bd-e92925c8fe82` | 58.3 MB | develop |
| Quorum.Upstream.QCA.Web | `19df8709-32dd-4219-a4db-1e136195993f` | 9.2 MB | develop |
| Quorum.Upstream.QCA.Application.MiddleTier | `2806d011-8922-4d20-8213-7635ce746c34` | 2.4 MB | develop |
| Quorum.Upstream.QCA.Application.APIHost | `c4fcf962-34fe-4b1c-9572-6f8990026650` | 404 KB | develop |
| Quorum.Upstream.QCA.API.Specs | `62d38a7f-4418-4e65-9d7b-a8e2581695ee` | 2.6 MB | master |
| Quorum.Upstream.QCA.Batch | `bfd56416-a1e4-4d65-af4f-2c12aaa90736` | 567 KB | develop |
| Quorum.Upstream.QCA.ClassicBatch | `7f9632f5-9496-40e3-908d-2f0b3f8c3081` | 3.6 MB | develop |
| Quorum.Upstream.QCA.ClassicGUI | `b815d52d-a2f9-4239-ae0a-cc0e17ef34fd` | 2.0 MB | develop |
| Quorum.Upstream.QCA.Database | `726b610b-4be7-46d7-a77d-1eb2e4e62ae0` | 4.5 MB | develop |
| Quorum.Upstream.QCA.DesignStudio.PackageSource | `7752427a-326f-4e72-9862-d8c8ddc236f4` | 63 KB | develop |
| Quorum.Upstream.QCA.DocumentManagement.EventHandlers | `26ae36de-182c-4c31-9b51-a143576b4309` | 173 KB | develop |
| Quorum.Upstream.QCA.Events | `8a0275ca-71ea-4cc7-b8ed-d27a603b1b8a` | 48 KB | develop |
| Quorum.Upstream.QCA.ReleaseNotes | `d21b74da-46f3-45cc-9934-72b820a0d188` | 682 KB | master |
| Quorum.QCA.AT | `96a3fd20-de92-42ee-8697-cf01159e9ec3` | 271 KB | develop |

> No standalone `.API` impl repo enumerated for QCA (only `.API.Specs` + `.Application.APIHost`); API surface is hosted from APIHost.

---

## 5. QDO — Division Order (modern web)

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.Upstream.QDO.Application.Web | `4e3ebd4d-8115-4891-a6f6-7a4700ec0d4f` | 55.8 MB | develop |
| Quorum.Upstream.QDO.Web | `29f50430-1df2-4d95-bf4e-924c369cb8db` | 26.6 MB | develop |
| Quorum.Upstream.QDO.Application.MiddleTier | `7241cf42-8076-4eea-b23f-914d8b3e030c` | 2.3 MB | develop |
| Quorum.Upstream.QDO.Application.APIHost | `83a5a867-0f33-4c18-b07f-60abfcd329ca` | 368 KB | develop |
| Quorum.Upstream.QDO.API | `9c531f19-8f38-43b6-8ce4-90d556a34286` | 1.0 MB | develop |
| Quorum.Upstream.QDO.DivisionOrder | `6f683799-4908-493f-8fdf-c338ba329ee9` | 39 KB | develop |
| Quorum.Upstream.QDO.Batch | `fed297e7-074c-4cde-b846-5ca3ed02ec2a` | 84 KB | develop |
| Quorum.Upstream.QDO.ClassicBatch | `88a00e07-f265-4d67-8f17-b25fd03a9a7b` | (empty) | — |
| Quorum.Upstream.QDO.ClassicGUI | `780d4d6d-a2c8-4999-ac08-80926907b0a7` | (empty) | — |
| Quorum.Upstream.QDO.Database | `c37f9552-cd09-47d7-84ca-ea80f2b1aeaf` | (empty) | — |
| Quorum.Upstream.QDO.DesignStudio.PackageSource | `ca59c586-355c-4e16-be17-68289d6590c7` | 32 KB | develop |
| Quorum.Upstream.QDO.DocumentManagement.EventHandlers | `ff875f0e-7ab3-4616-b159-cc7499fe4b9c` | 117 KB | develop |
| Quorum.Upstream.QDO.Events | `b87d7a58-6365-41d4-a25f-c8c95952e54c` | 27 KB | develop |
| Quorum.Upstream.QDO.ReleaseNotes | `eeddb0cc-12ec-4191-916d-c445038d8901` | 1.0 MB | master |
| Quorum.QDO.EventServices | `14e7fc0e-760c-4c78-a334-93a5b9d0da7e` | 29 KB | develop |
| Quorum.QDO.EventServices.EventMessage | `ed28c87d-e2a8-44e2-9893-92f8b96eb889` | 18 KB | develop |
| Quorum.QDO.AT | `c15fd3a9-11e0-43ea-8502-734c7b2c4309` | 3.2 MB | develop |
| Quorum.PerformanceTesting.QDO | `7620bd9f-5104-412b-b7a2-ee0ee32d9faf` | 1.3 MB | master |

> **Caution:** `Quorum.Upstream.QDO.Database`, `.ClassicBatch`, and `.ClassicGUI` are **empty (0 B, no default branch)** in ADO — QDO web reuses the shared `Quorum.Upstream.Database`/metadata rather than module-specific copies. For QDO classic/desktop, use the `Quorum.QDOD.*` family (Section 7), not these. The core DO logic lives in `Quorum.Upstream.QDO.DivisionOrder` (the `DivisionOrder.Workspace` project) and `Quorum.Upstream.QDO.Web`.

---

## 6. QCFS — Financial / Cash Accounting (Financial Accounting)

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.Upstream.QCFS.Application.Web | `d8c2edc0-b3e9-4d3f-8744-533047af4792` | 57.0 MB | develop |
| Quorum.Upstream.QCFS.Web | `6eeec009-d872-4cbb-8c74-bc5daad8aec1` | 26.1 MB | develop |
| Quorum.Upstream.QCFS.Application.MiddleTier | `dba4a811-44f4-4ab1-8c80-9b698a8e1277` | 2.5 MB | develop |
| Quorum.Upstream.QCFS.Application.APIHost | `925540ab-fff5-4fd6-aaa9-461949673b03` | 384 KB | develop |
| Quorum.Upstream.QCFS.API | `8bf01957-a2fe-4a05-b323-685f4cb4ede5` | 3.3 MB | develop |
| Quorum.Upstream.QCFS.API.Specs | `abf6b9b0-5cb1-4181-a70d-5c76644d9b03` | 2.5 MB | develop |
| Quorum.Upstream.QCFS.Batch | `bb284f70-75de-4266-ba4c-7d509416d92e` | 1022 KB | develop |
| Quorum.Upstream.QCFS.ClassicGUI | `66ff8d68-21ff-4072-8dd1-c3aaa3644a27` | 4.4 MB | develop |
| Quorum.Upstream.QCFS.Database | `1c592c7a-ef9c-4a01-ab80-f8d4c947b0dd` | 5.1 MB | develop |
| Quorum.Upstream.QCFS.DesignStudio.PackageSource | `0a29e392-d97e-47a3-9350-12d48c10b447` | 67 KB | develop |
| Quorum.Upstream.QCFS.DocumentManagement.EventHandlers | `5e7bc8fd-9867-4b27-9416-4aaa340f8fa5` | 203 KB | develop |
| Quorum.Upstream.QCFS.Events | `4a718667-50f6-41d1-9da3-b3f6709d9144` | 47 KB | develop |
| Quorum.Upstream.QCFS.Messaging.Publisher | `213af850-15fd-4db6-ab48-82ba5bf65875` | 70 KB | develop |
| Quorum.Upstream.QCFS.ReleaseNotes | `66ca38ac-e258-43d3-aad1-8798b0276a9f` | 984 KB | master |
| Quorum.QCFS.AT | `eb2ec854-b3a7-4f1a-98d3-c83176209b21` | 368 KB | develop |

> QCFS has no `.ClassicBatch` repo enumerated (modern `.Batch` only). It is the financials/GL/cash-management module of the suite.

---

## 7. QDOD — Division Order Desktop (classic, standalone)

The classic thick-client Division Order product. Full self-contained stack (own DB, metadata, reports, GUI). Distinct from the modern web `Quorum.Upstream.QDO.*` in Section 5.

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.QDOD.Application.ClassicGUI | `aebc40dc-bfa9-431b-bc54-3f153e3b64da` | 1.6 MB | develop |
| Quorum.QDOD.Application.MiddleTier | `1e8181f6-a3b6-4efb-a691-f9d41e336c68` | 1.2 MB | develop |
| Quorum.QDOD.Application.QPEC | `f5ef75a8-a989-465e-a2c1-9f5b41517079` | 2.2 MB | develop |
| Quorum.QDOD.ClassicGUI | `50797ec6-0aff-4adc-bb4c-9bef6076b829` | 1.5 MB | develop |
| Quorum.QDOD.ClassicBatch | `b62ea37e-0b03-4e72-b0c2-872fd58d1a76` | 2.9 MB | develop |
| Quorum.QDOD.Batch | `20850bac-d216-4c80-b844-8a6b471818c8` | 236 KB | develop |
| Quorum.QDOD.Database | `19a2c172-f3b8-4b46-a1c5-ab607f19f8b0` | 2.7 MB | develop |
| Quorum.QDOD.Metadata | `4f8f2d07-7d6f-4931-b606-8c54e277f441` | 72.9 MB | develop |
| Quorum.QDOD.Reports | `4804f667-d46b-46f8-9fdd-f379391da66f` | 14.6 MB | develop |
| Quorum.QDOD.Web | `c0aac567-db3c-4928-9437-819de606fe4c` | 4.0 MB | develop |
| Quorum.QDOD.Help | `3ca7f628-feed-4ea1-b944-6192813061fe` | 44.8 MB | develop |
| Quorum.QDOD.ReleaseNotes | `f7c15fa9-65b8-48f2-98f5-48aea777723b` | 119 KB | master |

---

## 8. eSuite — classic platform (`Quorum.ESuite.*`)

The eSuite classic application platform the upstream suite builds on (shared GUI, services, events, document management, metadata). When a case touches classic screens, workflow API, or shared DMS/event plumbing, look here.

| Repo Name | Repo ID | Size | Branch |
|-----------|---------|------|--------|
| Quorum.ESuite.Application.Web | `d763f32e-eb5d-4b27-8815-50e50afbb96e` | 71.9 MB | develop |
| Quorum.ESuite.Web | `289015cf-8a18-4c6c-8af7-b7d4663c79f7` | 31.4 MB | develop |
| Quorum.ESuite.Application.MiddleTier | `d9ccbdce-8bea-4d93-b84d-4dab315e7a98` | 2.6 MB | develop |
| Quorum.ESuite.Application.APIHost | `85c1bcbe-f10d-4c87-b5b9-57b43e3fd451` | 537 KB | develop |
| Quorum.ESuite.Application.ClassicGUI | `4062f2b4-bdf6-47ec-b6dc-531503d8dbe4` | 2.1 MB | develop |
| Quorum.ESuite.Application.QPEC | `49926f8b-05d4-4060-8218-b8ed8c4c1316` | 2.8 MB | develop |
| Quorum.ESuite.Application.WebWorkflowAPI | `99e9b210-f95f-4fa8-941b-48529a3ba5bf` | 51 KB | develop |
| Quorum.ESuite.API | `ac2b4e0f-2d92-44ac-ba78-0046f44037d4` | 4.6 MB | develop |
| Quorum.ESuite.API.Specs | `a0ab7996-1b92-4544-913f-67e1c7118978` | 5.6 MB | master |
| Quorum.ESuite.Batch | `93eeadfd-f613-4619-b805-861476b05ed7` | 1.7 MB | develop |
| Quorum.ESuite.ClassicBatch | `48c01156-377c-4080-82ec-3c8426ad7627` | 570 KB | develop |
| Quorum.ESuite.ClassicGUI | `023cbda9-53eb-4d71-82b9-f14005adc311` | 1.9 MB | develop |
| Quorum.ESuite.Database | `9708cebd-be5e-4678-9a48-d950139d2a23` | 7.0 MB | develop |
| Quorum.ESuite.Metadata | `2692788b-6bc0-4f05-9013-c4125675b82a` | 483.9 MB | develop |
| Quorum.ESuite.Shared.Metadata | `49c86c3c-5378-4a01-8ec6-2e7b5e0cd866` | 426.6 MB | develop |
| Quorum.ESuite.Reports | `f66e75df-2f07-457e-aeec-04f4ae7a21c9` | 2.9 MB | develop |
| Quorum.ESuite.DesignStudio.PackageSource | `d8b2dc96-8e5f-4f00-a37a-b8c096a9f3c8` | 57 KB | develop |
| Quorum.ESuite.DocumentManagement.EventHandlers | `075b056d-9805-4f7e-baf2-f3f588c87165` | 161 KB | develop |
| Quorum.ESuite.EventServices | `5ff24e99-b6cb-4d91-9371-d89bb7a1cd37` | 135 KB | develop |
| Quorum.ESuite.EventServices.EventMessage | `cbc967d4-6b2a-4ed3-8b8c-5f8470b499f9` | 87 KB | develop |
| Quorum.Esuite.Events | `9f834219-45cc-4b8f-8aab-51c6e0b6e242` | 67 KB | develop |
| Quorum.ESuite.Messaging.Publisher | `85c97d6c-18cf-42ad-b41e-3bf1356cb3b6` | 120 KB | develop |
| Quorum.Esuite.Messaging.Subscriber | `8b383ac1-f7ac-496f-b4d7-d9b75ccb403f` | 82 KB | develop |
| Quorum.ESuite.AT | `01691c37-de46-487a-b117-45d9ba973637` | 1.2 MB | develop |
| Quorum.ESuite.Help | `b4026b03-0965-4d6e-b2c6-7fc9a45088df` | 19.5 MB | develop |
| Quorum.ESuite.ReleaseNotes | `727c9a96-a590-4e28-926c-ed3925ccdd4b` | 749 KB | master |

> Note inconsistent casing in the org: most repos are `Quorum.ESuite.*` but a few are `Quorum.Esuite.*` (Events, Messaging.Subscriber). Match exact casing when calling the items API.

---

## 9. Client-prefixed (per-tenant) repos

~1,052 client-prefixed accounting repos across **215** distinct client codes. They follow the same suffix conventions but hold only the per-tenant overrides — almost always `.Database`, `.Metadata`, `.Reports` (and `.ESuite.Database`/`.ESuite.Metadata`); a minority of larger clients also carry `.Application.*`/`.QPEC`/`.ClassicBatch` customizations.

Common per-client suffix patterns observed (`<CLIENT>` = 2–5 char code, e.g. `GLE`, `APA`, `ERF`, `MRO`, `DCP`, `CEN`):

| Pattern | Meaning |
|---------|---------|
| `<CLIENT>.Upstream.Metadata` / `.Reports` / `.Database` | tenant overrides on the modern suite |
| `<CLIENT>.Upstream.QRA.Database` / `.QCA.Database` / `.QDO.Database` / `.QCFS.Database` | per-module tenant schema overrides |
| `<CLIENT>.Upstream.ESuite.Database` / `.ESuite.Metadata` | tenant eSuite-layer overrides |
| `<CLIENT>.ESuite.Database` / `.ESuite.Metadata` | tenant classic eSuite overrides |
| `<CLIENT>.QDOD.Database` / `.Metadata` / `.Reports` | tenant Division Order Desktop overrides |
| `<CLIENT>.QLS.ESuite.Database` / `.Metadata` | QLS (Land System) tenant repos that ride the eSuite layer |

Top clients by repo count: GLE (21), APA (16), ERF (16), NOG (16), MAC (14), APH (13), EQC (13), RRC (13), SPR (13), CCI/DOM/ENR/MEW/MRO/PNR/SRC/TEP (12 each).

**To resolve the exact repo for a specific client + module**, query the API rather than guessing the name:
```bash
# List a client's accounting repos (replace GLE):
curl -s -u ":$PAT" \
  "https://dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/git/repositories?api-version=7.0" \
  | python -c "import sys,json; d=json.load(sys.stdin); [print(r['name'],r['id']) for r in d['value'] if r['name'].startswith('GLE.') and ('Upstream' in r['name'] or 'ESuite' in r['name'] or 'QDOD' in r['name'])]"
```

---

## 10. Tooling / conversion (`QuorumServices` project)

No upstream product source here — migration/conversion tooling only. Relevant when a case involves a client data conversion or upgrade.

| Repo Name | Repo ID |
|-----------|---------|
| Quorum.Upstream.Conversion | `69442914-8c4a-46a7-9a8e-33aab80cc682` |
| Quorum.ODA.Conversion | `4dcae24d-3d1f-4412-b81e-5db3a698def2` |
| Quorum.ODL.Conversion.Scripts | `644a8492-822e-4067-a33c-bb9d0c411bd4` |
| Quorum.Landdox.Conversion | `3923a95a-3b03-413a-ba77-6c896748135b` |
| Quorum.DaWinci.Conversion | `8353c15f-2ae9-4ddf-bc5a-275be83a3c76` |

> `myQuorum Cloud` project (4 repos: Cloud Delivery Automation, Global Cloud Operations Center, myQuorum Cloud, myQuorum Scripts) is cloud delivery/ops — not upstream product code.

---

## 11. Quick L4 routing cheat-sheet

| Symptom / area | Start in |
|----------------|----------|
| Revenue/owner payments, severance/production tax | `Quorum.Upstream.QRA.*` (Tax: `.QRA.Tax`, `.QRA.ClassicGui.Tax`) |
| AFE / joint-interest / cost allocation | `Quorum.Upstream.QCA.*` |
| Division of interest, ownership decks, DO transfers (web) | `Quorum.Upstream.QDO.DivisionOrder`, `.QDO.Web`, `.QDO.Application.Web` |
| Division Order classic/desktop | `Quorum.QDOD.*` |
| GL / cash / financial statements | `Quorum.Upstream.QCFS.*` |
| Cross-module batch / shared posting logic | `Quorum.Upstream.Shared.Batch`, `.Shared.ClassicBatch` |
| Shared DB tables / common schema | `Quorum.Upstream.Database` (then module `.Database`) |
| Grid / picklist / screen definition | `Quorum.Upstream.Metadata` (4 GB; module `.Metadata` for module screens) |
| Browser/web screen behavior | `*.Application.Web/{APIControllers,Views,Scripts}` + `*.Web` |
| Desktop/classic screen behavior | `*.ClassicGUI`, `Quorum.QDOD.*`, `Quorum.ESuite.Application.ClassicGUI` |
| Service / middle-tier business logic | `*.Application.MiddleTier` (host + `.csgrp` service groups) / `*.Application.APIHost` |
| REST API contract questions | `*.API` + `*.API.Specs` (Swagger) |
| Document attachments (checks, JE docs, well-completion) | `*.DocumentManagement.EventHandlers` |
| Events / async integration | `*.Events`, `*.EventServices`, `*.Messaging.Publisher` |
| Per-client data/config override | `<CLIENT>.Upstream.*` / `<CLIENT>.ESuite.*` / `<CLIENT>.QDOD.*` (query API for exact name) |
| Code search across all upstream repos | `POST almsearch .../codesearchresults` with `repo:Quorum.Upstream.QRA.Application.Web` etc. |

### Folder structure reference (verified via API)
- **MiddleTier** (`*.Application.MiddleTier`): root has the `.sln` + a source folder `/<RepoName>/` containing the host project, `app.<Env>.config` (Cloud / OnPremDirect / OnPremNI / Debug / Release), and `dms-*.csgrp` service-group configs (e.g. `dms-document-management`, `dms-manual-je-document`, `dms-Property`, `dms-WellCompletion`).
- **Web** (`*.Application.Web`): source folder `/<RepoName>/` with `APIControllers`, `App_Start`, `ApplicationStart`, `Content`, `DesignStudio-MvcComponents`, `DesignStudioRoot`, `Scripts`, `Views`.
- **QDO core**: `Quorum.Upstream.QDO.DivisionOrder` root has `Quorum.Upstream.QDO.DivisionOrder.Workspace` (with a `DVD` subfolder) + `.UnitTest`.
