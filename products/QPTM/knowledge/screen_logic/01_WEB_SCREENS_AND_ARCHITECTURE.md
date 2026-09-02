# QPTM Web — Screen Catalog & Screen Architecture Reference

**Created:** 2026-07-04 | **Sources:** Quorum.QPTM.Web (repo `41e317c0`, branch `develop`), APL.QPTM.Web (`ffa5745e`), APL.QPTM.Application.Web (`2ddf8637`), Quorum.QPTM.Metadata (`1ae5387f`), in-repo docs (`/.prompts`, `/AI_Agent_Help_Docs` on branch `feature/improved_dmain_for_contracts`), `.github/copilot-instructions.md`.
**Verification:** full `QUIController*` census via ADO code search — 109 production QUIController classes in core (96 in UIControllers/, 13 in Personas/), 12 in APL.QPTM.Web, 0 in the Application.Web host (pure shell). Screen list below is complete for the Web UI; many config screens remain ClassicGUI-only (see §9).

---

## 1. Big picture

- QPTM has **two UIs**: **myQuorum Web** (this document) and legacy **ClassicGUI** (C++/MFC, repo `Quorum.QPTM.ClassicGUI`, screens `QVp*.cpp/.h`). Rule of thumb: Web READS/executes config at runtime; ClassicGUI WRITES/configures much of it. Operational screens (nominations, confirmations, CR bidding, RFS) are migrated to Web; many maintenance/config screens are ClassicGUI-only.
- The deployable web app is a **composition host**: `<CLIENT>.QPTM.Application.Web` (e.g. APL) is an IIS shell with no controllers of its own — it composes NuGet packages: `Quorum.QFC.Web.Core/CoreScreens` (framework screens), `Quorum.QPTM.Web(.Core/.Controllers)` (product screens), `Quorum.QPTM.LDC.Web` (LDC screens), `Quorum.QPTM.Widget.CycleChanges` (packaged widget), `<CLIENT>.QPTM.Web(.Core)` (client screens/overrides). ~160 view folders in the host vs ~112 in core QPTM.
- Views are **RazorGenerator-precompiled** (`__CompiledViews.cs : ExportCompiledViewBase`); client repos layer their compiled views over core.

---

## 2. Core QPTM screen catalog (Quorum.QPTM.Web)

Convention: one folder per screen under `/Quorum.QPTM.Web/Views/<Screen>`; main view `<Screen>.cshtml`; `_*` partials = tabs/popups/grids; `_naesb*Form.cshtml` = NAESB print forms; module landing pages are `Index.cshtml`. JS in `/Quorum.QPTM.Web/Scripts/<Screen>` (naming drift: `BillingTspConfig` vs `TspBillingConfiguration`; `RateSeasonalProfileMaintenace` typo; `PDASubmission` vs `PdaSubmission`).

### Contracts / RFS
| Screen | Notes |
|---|---|
| ContractMaintenance | Biggest screen (UIC 4,263 ln; MVC 3,814 ln); 31 tab partials (_General, _Agents, _AuthorizedOverrun, _Contacts, _ContractQuantity, _Dates, _FSSSchedule, _Imbalance, _InjWthPeriods, _Invoice, _LeaseDetailsGrid, _Locations, _PALISSCumulative/_PALISSTrade, _Rates, _RelatedK, _SchdCapOvrd, _SegmentCapacity, _SegmentRights, _Text, _UserDefined, _ZoneSegmentCapacity); `_ClientFields` client-extension partials |
| ActiveContracts | Active contracts grid/query |
| Contracts (landing) | Module landing Index.cshtml |
| CtrCntctOvrdMassChange | Contract contact override mass change |
| NewRFSActivity | New Request-For-Service activity entry |
| RFSWizardV2 | RFS contract-origination wizard, 30 step/summary partials, QPTM.wizardV2.js |
| RFSApproval | RFS approval queue (14 partials) |
| TypeOfServiceSetup / TOSSetup | TOS config controlling which tabs/rules apply on Contract & RFS screens |
| SeasonalProfile | Contract MDQ seasonal profiling (distinct from RateSeasonalProfileMaintenance) |

### Nominations
| Screen | Notes |
|---|---|
| NominationSubmission | Primary shipper nom entry; PNT + PT (pathed-threaded) tabs, path popups, bulk copy, pending transfer, hourly profile, _naesbNomForm |
| NominationSubmissionBase | Base partial set (10) shared with LCNominationSubmission: _Classification, _Copy, _Delivery/_ReceiptPopup, _Errors*, _Import, _Location/_PathSummaryTab. UIC base 8,665 ln |
| LCNominationSubmission | Location/lease-centric nom submission variant |
| NominationMaintenance | TSP-side nom maintenance (+path/upstream/downstream popups) |
| NominationAutogen | Auto-generation of noms (General/Contract/CustomAccount/SourceNomLocation/TargetNomContracts tabs) |
| NominationErrors | Validation error viewer |
| NominationErrorOverrides | Override nom validation errors |
| NominationCuts | Scheduling cuts applied to noms |
| NominationTitleXfer | Title transfer nominations |
| NomClassificationMaintenance | Nom classification maintenance |
| NominationConfigureUserPreference | User grid/column preferences for nom screens |
| PostNominationSubmissionTemplate | Post-nom submission template |
| ValidationRuleAssignment | Assign validation rules (QCTRL_VALD_RULE) |
| LifeCycle | Transaction life-cycle trace (nom → confirmed → scheduled → allocated) |

### Scheduling / Confirmations
| Screen | Notes |
|---|---|
| ConfirmationSummary | Confirmation summary |
| ConfirmationSummaryQuickView | Quick-view variant (Index.cshtml) |
| ConfirmationResponse | Operator confirmation response entry; _HourlyProfile, _SendMail, _naesbConfForm |
| OperatorConfirmations | Operator-persona confirmations list |
| ScheduledQuantity | Scheduled quantity viewer |
| SchedulingCapacityOverrideMaint | Scheduling capacity overrides |
| EPSQMaintenance | Elapsed Prorated Scheduled Quantity maintenance |
| CASummaryMaintenance | Capacity Allocation summary — scheduling engine rule-set/capacity view; _Graphical/_Tabular/_NomDetail/_RuleSet |
| CASReductionOrder | Scheduling reduction (cut) order config |
| LeaseSchedulingConfigurationMaintenance | Lease scheduling config |
| PathBalanceVolumeApproval | Path balance volume approval (_ProposalTab, _SvcReqSummaryTab) |

### Capacity Release
| Screen | Notes |
|---|---|
| CapacityRelease (landing) | Module landing |
| OfferWizardV2 | Release offer wizard, 27 partials |
| OfferViewer | Posted offers viewer |
| BidWizardV2 | Bid entry wizard, 12 partials |
| CRBid | **Legacy (non-wizard) bid entry** — `QVpCapRelBid`, extends QUIControllerCRBase (found only by controller census; easy to miss) |
| BidViewer | + BidViewer_OLD.cshtml legacy retained |
| LongTermBidViewer | Long-term bids |
| CRAward | Award processing (header/awards tabs, award report) |
| CapacityReleaseAwardedBids | Awarded bids posting |
| CapacityReleaseOffer | CR offer screen (persona drill target) |
| AwardAmendments | Award amendments |
| RecallReput | Recall/reput of released capacity |
| WithdrawalSummary | Offer/bid withdrawal summary |

### Inventory / Storage
InventoryAccounts (daily/monthly activity+balance tabs), InventoryAdjustments, InventoryImbalances, InventoryStorageBalance, StorageTransferMaintForm, RatchetSchedule, TSPInventoryConfigurations, CustomerAccountQuery, CustomerAccountSummary.

### Imbalance
AuthToPostImbal (activity/balance/contracts tabs), PostedImbalance, ImbalTradingMaintForm, OBAInventoryImbalances.

### Invoicing / Billing / Penalties
Invoicing (landing), InvoiceMaintenance (header/detail/sub-detail tabs), InvoiceGroupMaintenance, InvoiceMsgMaintenance, ChartOfAccounts, TypeOfChargeMaintenance (TOC config), TOSChargeBasisSetup, TspBillingConfiguration, PenaltySubmission, PenaltyResults (pool/tier details), HourlyPenaltySchedule.

### Rates
RateMaintenance (general/location details/matrix/contract-inventory-TOS assoc tabs), RateQuery, RateSeasonalProfileMaintenance, RateTocObjectAssociation, IndexMaintenance (price indices), TierMaintenance.

### Measurement / Allocation (Flowing Gas)
FlowingGas (landing), MeasurementEntry, MeasurementResults, HourlyMeasurementMaintenance, HourlyMeasurementResults, OperatorMeasurement, GasAnalysisSearch, DailyAllocatedQuantityMaintenance (incl. _AllocationTransaction_Diagram visual), MonthlyAllocatedQuantityMaintenance, ReallocationMaintenance, PPAEventMaintenance (prior-period adjustments), PdaSubmission (predetermined allocation, _naesbPDAForm), ClassificationRulesEntryMaintenance.

### Locations / Pipeline Admin / TSP config
LocationMaintenance (17 tab partials), LocationGroupMaintenance, LocationGroupLookup, LocationGroupPathMaintenance, LocationPathMaintenance, LocationContactMassChange, DefaultAgents, TspConfigurationSettings (TSP config keys).

### EDI
TPAMaintenance (Trading Partner Agreements — EDCTRL_TPA_HDR; General/EDIServ/Datasets tabs), EDTransaction (EDI transaction viewer — EDTRAN_TRANSACTION).

### Reports / Postings
IndexOfCustomers (FERC IoC posting), QPTMNoticePosting (EBB notices), SupplementalDocuments (current/archive).

### Dashboard / Infrastructure
Home (dashboard host), DashboardQPTM (`QVpDashboardQPTM`, thin subclass of QFC `QUIControllerDashboardViewer`), ContactsWidget host page, Sitemap (registered-screen catalog; also NAESB sitemap helper), Office (Excel/Outlook add-in pages), OnCallCalendar, NotificationPreference, UserContactForm, Shared (_StylesAndScriptsQPTM, _TSPActionHub, PPAReallocationDialog shared popup).

### Persona viewport screens (`QVp*` security ids, `ShowAsScreen=false` — dashboard drill-downs, not menu items)
- **Operator:** Confirmations, OBAInventoryImbalances, OperatorMeasuredVol (KPI NumVariances; quick action launches batch ALRX54)
- **Scheduler:** ActiveContracts, AvailableOffers, BidsAwarded, InventoryImbalances, InventoryStorageBalances, NominationCuts (current+next gas day grids, cycle labels), NominationErrors, NominationTitleXfer, RFSActivity
- Shared base: `QUIControllerMeasuredVolume_Base` (grid registration, read-only — DoSave/DoValidate throw)
- Pattern: read-only; base owns grid/root-bind/persistence plumbing; persona subclass supplies data-retrieval recipe, KPI counts, inline actions.

### Dashboard widgets
- **Core QPTM (16, `/Views/Shared/Widgets`, registered via `QPTMAppStartUtilities.RegisterQPTMWidgets()` → `QWebContext.RegisterWidget`, served by `QPTMWidgetAccessController`):** ApplicationTime, CapacityRelease, Contacts (persona preview variants Accountant/ContractAdmin/Operator/Scheduler), Contracts, Cycles (backs 3 registered variants: NominationCycle/ConfirmationCycle/SchedulingCycle), InvoiceSummary, MeasurementClose, Nominations, NoticePostings, OperatorConfirmations, OperatorInventory, OperatorMeasurement, RFS, SchedulerInventory, StorageBalance, TitleTransfers.
- **QFC host-level:** MessageWidget, QNoticePostingsWidget, QAdvancedSearch/QSearchWidget, _RemoteWidget, DisconnectedWidget (fallback).
- **Design Studio package widgets** (repo `Quorum.QPTM.DesignStudio.PackageSource`, deployed as packages): CycleChanges (`Quorum-QPTM-CycleChangesMvc.CycleChangesWidget`, also NuGet `Quorum.QPTM.Widget.CycleChanges`), ExpiringContracts, Interconnect, MapLink, OperationalSummary, PPASummary.
- **APL client widgets (6, `APLWidgetAccessController : WidgetAccessControllerBase`):** InventoryWidgetAPL (L2=InventoryAPL, IN62 link), BorderNomWidgetAPL (L2=BorderNominations, deep-links NominationSubmission), ImbalanceTradesWidgetAPL (L2=ImbalanceTrades), ITBiddingWidgetAPL (L2=ITDailyFirmBidding), PALWidgetAPL (L2=PAL), YDayWidgetAPL.
- "Planned Service Outage" / "Process Alerts" widgets: no source in these repos (closest: NoticePostingsWidget / MessageWidget); likely other client repos or DS packages.

### QFC framework screens (in host, not in core QPTM repo)
Dashboard, DashboardEditor, MenuEditor, PersonaEditor, Security screens (SecurityUserInfo/GroupInfo/Function), CnfgSettings, MessageLog(Summary), GlobalSearch, ProcessExplorer, UserProfile, ReportExecution, BatchReportViewer, GlobalBatchProcess*/GlobalReport*, DocumentManagement, RouteAdmin, DeskAdmin, BulkMaintenance*, CacheMaintenance, LoggingMonitor, SystemSitemap, VersionInfo, WorkInProgress, EnrollmentWizard, Account/AccountSummary, AggregateViewer, legacy BidWizard/OfferWizard/RFSWizard (V1).

### APL client layer (pattern applies to every `<CLIENT>.QPTM.Web`)
- **APL-only screens:** APLContractMaintenance, BorderNominations, ITDailyFirmBidding, ImbalanceTrades, InventoryAPL, PAL, RFSBidApproval (+ Esuite*InterfaceControllerBase bases).
- **Overrides of core screens:** `QUIControllerNominationMaintenanceAPL : QUIControllerNominationMaintenance` (adds UrlLinkParam deep-link), `QUIControllerImbalTradingMaintFormAPL`, `QUIControllerContractMaintenanceAPL`. Registered in `/APL.QPTM.Web/ScreenRegistration/ClientScreenRegistrationSpecs.cs` — re-registering a screen with the client UIC type replaces the core screen. Quirk: `QUIControllerImbalTradingMaintFormAPL .cs` has a trailing space in the repo filename.

---

## 3. Screen architecture — the three-piece pattern

Every screen = **MVC controller + UIController (UIC) + RootVM**, on .NET Framework 4.8 / ASP.NET MVC / QFC (Quorum Framework Core).

### Class hierarchies (two parallel stacks)
```
UIC (screen state, project Quorum.QPTM.Web.Controllers, ns Quorum.QPTM.Controllers):
  QInterfaceControllerBase (QFC)                     — Query/Save/New/Validate template verbs, Params, streams
    └─ QPTMInterfaceControllerBase                   — TSP context, security, workflow states, background exec
        ├─ QUIController<Screen>                      (e.g. NominationBase → NominationSubmissionBase → …)
        └─ QPTMEffectiveDatedInterfaceControllerBase  — effective-dated screens
            └─ QUIControllerContractMaintenance       [QSecurityObject(SecurityObjectIDs.ContractMaintenance)]
  Family bases: QUIControllerALBase (allocation), QUIControllerCRBase (cap release), QUIControllerINBase
  (inventory/imbalance), QUIControllerNominationBase, + matching *ParamsBase classes.
  Also QPTMBulkInterfaceControllerBase, QPTMDocumentsInterfaceControllerExtension,
  QUIBehavior* companions (Nomination, PDA, RFSWizardV2).

MVC (HTTP endpoints, project Quorum.QPTM.Web.Core/Controllers):
  QMvcBaseScreenController<T_UIC,T_VM> (QFC)
    └─ QMvcQPTMBaseScreenController<T_UIC,T_VM>
        └─ BillingControllerBase / SchedulingControllerBase / …
            └─ ContractMaintenanceController : BillingControllerBase<QUIControllerContractMaintenance, ContractMaintenanceRootVM>
               [QScreenSecurityObject(...)]
```
The MVC controller gets the stateful UIC via `UIControllerAccess(QWebContext.GetUIControllerIdFromContext(id))` and mutates it inside `ReadAccess/WriteAccess` lambdas — the UIC is a **per-user, per-screen server-side state object living between requests** in QWebContext; every AJAX action carries `[QUIWebContextId] string id`.

### Screen lifecycle verbs (UIC "Do" template methods)
- `DoQuery()` — MyParams → request DO → middle-tier `Service.Get*` → results back into params/DOs → post-processing (tab visibility `HiddenTabsList`, calc).
- `PreSave()` → `DoSave()` — DOs to `Service.Update*`; on success `QICService.NotifyOfChange(GenericScreenChange)` (inter-module change notification) + `PostUpdateBatchProcesses`/`LaunchBatchProcess`.
- `DoValidate()` — middle-tier validate; errors return as `ErrorsByProperty` on DOs.
- `DoNew()/DoClone()`, `OnPropertyChanging/Changed`, audit-history hooks, `GetMaintainableObjects()` for change detection.
- Nomination screens: `Save()` wraps `PreSave → CheckSave → PushParams → DoSave/DoSubmit → ClearParams → LogObjectMessages`; `DoSave()` itself throws "Call SaveActivity or Submit".

### Params
`QPTMControllerParams : QControllerParams` — each param registered with `RegisterProperty(enPropertyClass.Key|AutoPush|RequiredForQuery, name, dbColumnAliases, getter, setter)`. Concrete screens nest a params class exposed as `MyParams`. Setting `TspNo` triggers `SetTspInfo()` (TSP header + preferences); a TSP change resets the screen via `Controller.New()`.

### TSP context & config
`IQPTMController`: `TspNo`, `TspPreference`, `IsUserInternal`, `GetCurrentTspNo()`. Per-TSP-or-global config via `QPTMTspOrGlobalConfigs` / `QPTMGlobalConfigs` — dozens of cached bool properties drive tab/field visibility (e.g. `CtrIsIntegratedMode`).

### Wizard state machine (RFSWizardV2 / BidWizardV2 / OfferWizardV2)
- `IQWorkflowState` / `QStateBase` (one class per step; `AddErrorMsg → ErrorsByProperty`), `QStateSetupInfo` factory pairs via `GetStateSetupList()`.
- Base UIC holds `CurrentWorkflowState`, `ValidStates`, `VerifiedOKStates`, `HasBeenValidated`; transitions `TransitionState()` (validate → Commit → next), `"*next"/"*back"` literals from QFWizard, backward nav allowed without validation.
- `QNavStateBase.NavStates : Dictionary<string, IQWizardV2NavItemState>` drives the wizard nav bar (SkipItem/Hidden/Validated/Valid/Visited).

### Grids
- View: `Html.Quorum().QGridBase<TVm>(screenGridName, Constants.GridIDs.X, "GetX", …)` — numeric **Grid ID** backed by metadata; per-column defs incl. UOM token substitution.
- MVC: standard 6-action family per grid — `GetX` (Kendo `DataSourceRequest` → `ToDataSourceResultWithRowNum`), `XGridUpdate` (`FieldDataDictionary`), `XGridAddNewRow`, `XGridDeleteRow`, `XGridBulkEdit`, `XGridExcelImport/Export`.
- Grid column metadata: legacy `QARCH_CNFG_GRIDCTRL_COL_NET` rows, OR (new pattern) compiled `/Quorum.QPTM.Web.Core/QPTMGridDefs.cs` `GetGridDefine(gridId)` — framework falls back to QARCH when null.
- Page size: global config key `<SECURITY_ID>_PAGE_SIZE`; user overrides in `QARCH_SCREEN_SETTING_GRID_USER`.

### Picklists & code tables
`QFSimplePickFieldWithButtonFor(m => m.X, Constants.PickListIDs.*, …)` (scoped/unscoped variants, popup column defs) and `QFCodeTableFor(m => m.X, Constants.CodeTableIDs.*, …)` with client-side `QCodeTableValueDependency` filtering. Metadata: `QARCH_CTRL_PKLIST*`, `QARCH_CDTBL_DEFINE*`.

### Actions / links
`GetActions(uiControllerId)` → `ActionItemVM` (Query/Save/New/Copy/Delete/Close factories, keyboard shortcuts, PostCallback hooks); custom verbs in `DoAction(actionName, id)`. Cross-screen links: `GetLinks()` → `LinkActionItemVM` (own SecurityId per link); receiver implements `DoUICLink(controller, linkParams)` → sets MyParams → `Query()` — this is the L2→L2 navigation mechanism.

### Security
- UIC: `[QSecurityObject(id)]`; MVC: `[QScreenSecurityObject(id)]`; screen ids follow `QVP<SCREENNAME>` / `QUC*` conventions (property `SecrityId` — typo in source).
- Runtime: `ServiceUtility.IsAllowed(QSecurityPrivilege.ObjectForm/ObjectTab, id, PermissionQuery/Update/Delete)`; tab partials set `EnableTabLevelSecurity + TabPageSecurityId`; column-level via `IQRequiredColumn` → `RequiredColumnDO.IsHidden/IsReadOnly`.

### View binding
One RootVM per screen (`<Screen>RootVM : QModelBase`); `InitializeMyViewModel` transfers DO→VM (`TransferData` + `TransferStateToModel` copies values + control-enable/error state); field edits POST `<X>FieldUpdate` with `FieldDataDictionary` model binder → `UpdateUIController`. Tabs = lazy-loaded partial actions via `QFTabStrip`. Popups implement `IQPopupData<T>` (e.g. 31-day ranged-nom quantity popups). Shared PPAReallocationDialog served from base MVC controller.

### Request lifecycle (browser → DB)
```
Browser (Kendo UI + precompiled Razor, carries QUIWebContextId)
  → ASP.NET MVC screen controller (Quorum.QPTM.Web.Core)         Action/DoAction, *FieldUpdate, grid endpoints
  → QWebContext UIC store (ReadAccess/WriteAccess lock-scoped)
  → UIC verb template (PushParams → Do<Verb> → ClearParams → LogObjectMessages; errors to QMsgLogBase + ErrorsByProperty)
  → WCF ServiceClient (QPTMServiceClient : QServiceClientChannelBase — one helper per IQPTM*Service)
  → Middle tier "QPEC" (Quorum.QPTM.ServiceCore*; validation in Quorum.QPTM.Validations.Rules.*;
     events Quorum.QPTM.Events.*; batch via IQProcessLauncherService BATCHID_*)
  → DataObject (BaseDO, DataObjectState Added/Modified/Deleted, *CompleteDO aggregates)
  → DataAccess/DAL → Oracle / SQL Server
```
Hard MSBuild rule (Directory.Build.targets): presentation projects MUST NOT reference DAL/DataAccess — everything goes through the service layer. UICs are streamable (`DoWriteStream/DoReadStream` via `QStreamer`) for unload/rehydrate.

---

## 4. Screen registration, menus, personas (how a screen reaches a user)

1. **Compiled registration:** `/Quorum.QPTM.Web.Core/Screen Registration/ScreenRegistrationSpecs.cs` — one `ScreenRegistration` subclass per screen (~80): MenuPath, UIControllerType, MvcController route, DisplayName, SecurityId (QVP*), ShowAsScreen, Singleton, External/Url (e.g. Informational Postings → IPWS). Wired at app start by `QPTMAppStartUtilities.RegisterQPTMControllers()` into QFC `IScreenRegistrar`. Widgets registered by `RegisterQPTMWidgets()`.
2. **Persona metadata:** `QARCH_CNFG_DYNUC` (JSON in `Quorum.QPTM.Metadata:/STANDARD 16.0/QARCH_CNFG_DYNUC.json`; authored in **Design Studio**). Rows DYNUC_NM ∈ {Persona, Menu, Dashboard, CultureDefinition}, LAYOUT_ID = persona name. Standard ships 3 personas: **PIPELINE INTERNAL, PIPELINE OPERATOR, PIPELINE SCHEDULER**. Menu rows = recursive MenuItems tree whose leaves reference screens purely by **SecurityId**; Dashboard rows = Groups[].Widgets[] (incl. DS package widget types). In-code persona constants: `Constants.Persona` ACT/SCH/OPR/CTA.
3. **Security trimming:** QFC filters menu leaves by user rights on the QVP* object (`QARCH_CODE_SEC_OBJECT` et al.).
4. **In-screen Links menus:** `QARCH_CNFG_MENU(_DETAIL)` — MENU_ID like `X_TO_Y`, LOCATION_TAG `<QVPSOURCE>_LINK`, TO_OBJECT_ID = target QVP*.
5. **Client overrides:** `<CLIENT>.QPTM.Metadata` repos (~44) fork STANDARD metadata; `<CLIENT>.QPTM.Web` re-registers screens with client UIC types.

**Design Studio** (separate product, ~25 `Quorum.DesignStudio.*` repos + `Quorum.QFC.DesignStudioIntegration`) is where personas/menus/dashboards are designed; results persist into `QARCH_CNFG_DYNUC`. QPTM's DS widget packages live in `Quorum.QPTM.DesignStudio.PackageSource`.

---

## 5. Screen/UI metadata table families (`Quorum.QPTM.Metadata:/STANDARD 16.0/`, 286 files)

| Family | Tables |
|---|---|
| Menus/personas | QARCH_CNFG_MENU(_DETAIL), QARCH_CNFG_DYNUC |
| Screens | QARCH_CNFG_SCREEN_NAME, _SCREEN_DBCOL, QARCH_CNFG_TAB, QARCH_SCREEN_DEFAULT/_HELP/_VALIDATION, QARCH_FORM_DEFAULT, QARCH_CTRL_SCREEN_PK_INPUT/RTN(_NET) |
| Grids | QARCH_CNFG_GRIDCTRL + _COL/_COL_NET/_JOIN/_JOINTBL/_NET/_PK_*/_SORTCOLS/_SUM_DEF/_ALT_SQL |
| Picklists | QARCH_CTRL_PKLIST + _ALT_SQL/_JOIN/_NET/_QRYCOLS/_SORTCOLS, QARCH_CTRL_FILEPKLIST |
| Code tables | QARCH_CDTBL_DEFINE(+_COL/_CTX/_FIXED_KEY), QARCH_CDTBL_CATEGORY |
| Security | QARCH_CODE_SEC_OBJECT, QARCH_SEC_ACTION, QARCH_SEC_OBJECT_TYPE_ACTION, QARCH_CTRL_SEC_ACTION_DEF |
| Labels/config | QARCH_CNFG_LABEL_GLOBAL/OBJECT/TABLE, QARCH_CNFG_CTRL, QARCH_CNFG_DBCOL |
| Other | QARCH_CTRL_PROCESS*, QARCH_RPTS_*, QARCH_TV_*, QARCH_WF_*, QARCH_BR_* |

---

## 6. REST API surface (not screens, but part of the web layer)

`/Quorum.QPTM.Web.Controllers/APIControllers/` — 15 Web-API controllers, routes `api/v1/{Feature}`, `[Authorize]`, data-shaping (`filter`, `embed`, `include/exclude`, `asOfDate`): AccountingDates, Allocations, CapacityAllocations, CapacityRelease, ConfirmationChange, Confirmations, Contracts, Inventory, Invoices, Locations, NominationChange, Nominations, OnCallNumbers, ShutInLocations, TransportServiceProvider. Backed by APIService classes + NSwag-generated models from APISpecifications/*.json.

---

## 7. Feature → controller/service routing (from in-repo CLAUDE.md)

| Code | Feature | Key Service / Controller |
|---|---|---|
| CAS | Capacity Scheduling Allocations | QPTMSchedulingService / CASummaryMaintenanceController |
| NOM | Nominations | QPTMNominationService / NominationMaintenance-, NominationSubmission-, LCNominationSubmission-, NominationErrorOverrides-, NominationAutogenController |
| ALLOC | Allocations | QPTMAllocationServiceExt_PDA / Daily-/MonthlyAllocatedQuantityMaintenanceController |
| CR | Capacity Release | QPTMCapacityReleaseService / BidWizardV2-, OfferWizardV2-, CRAwardController |
| CONF | Confirmations | QPTMConfirmationResponseServiceExt / ConfirmationResponse-, ConfirmationSummaryController |
| CTR | Contracts | QPTMServiceCore_ContractMaintenance / ContractMaintenanceController |
| RATE | Rates | RateResolutionMgr / RateMaintenanceController |
| INV | Inventory | QPTMInventoryService / InventoryAccounts-, InventoryAdjustmentsController |
| EDI | EDI | EDIService / EDTransactionController |
| RFS | Request For Service | QPTMRFSService / RFSWizardV2Controller |
| LOC | Locations | QPTMServiceCore_LocationMaintenance / LocationMaintenanceController |
| INVC | Invoicing | QPTMServiceCore_InvoiceMaintenance / InvoiceMaintenanceController |
| PEN | Penalties | QPTMServiceCore_PenaltySubmission / PenaltySubmission-, PenaltyResultsController |
| MEAS | Measurement | QPTMServiceCore_MeasurementEntry / MeasurementEntry-, MeasurementResultsController |

Batch↔Web mapping: NNCLASSFY/SCREDUCE/SCOAC→CAS; NNSUBMIT/NNVALIDATE→NOM; ALALLOCATE→ALLOC; CFPROCESS→CONF; CRPROCESS→CR; INACCTACCM/INTRDPEND/INCONFTRADE→INV; EDIPROCESS→EDI.

---

## 8. In-repo documentation locations

- Default branch: `/.github/copilot-instructions.md` (main architecture doc), `/.prompts/{architecture,domain,troubleshooting}` (only CAS documented), `/.prompts/QUICK_REFERENCE.md`.
- Branch `feature/improved_dmain_for_contracts`: `/AI_Agent_Help_Docs/` — 14 feature folders (allocations, capacity-release, capacity-scheduling-allocations, confirmations, contracts, edi-integration, inventory, invoice-management, location-management, measurement, nominations, penalties, rate-management, rfs), each with domain.md + architecture.md + troubleshooting.md; plus DOCUMENTATION_STRATEGY.md, TESTING_GUIDE.md.

---

## 9. L4 triage implications

| Symptom | First look |
|---|---|
| Screen missing from a user's menu | Persona/menu DYNUC config (`QARCH_CNFG_DYNUC`) or QVP* security — NOT code |
| Column/dropdown wrong or missing on Web | QARCH grid/CDTBL metadata (check `<CLIENT>.QPTM.Metadata` override) unless screen migrated to compiled `QPTMGridDefs.cs` |
| "Works in Classic, broken in Web" | Web grid/field config is separate metadata from Classic; also many fields never ported |
| Screen behaves differently for one client | `<CLIENT>.QPTM.Web` UIC override (check `ClientScreenRegistrationSpecs.cs`) or metadata fork |
| Config screen "not on web" | Expected — ClassicGUI-only maintenance screen (`QVp*.cpp` in Quorum.QPTM.ClassicGUI) |
| Wizard stuck / step won't advance | `TransitionState` validation result (Validated/Valid/Continue), `QNavStateBase.NavStates` flags |
| Grid Links jump broken | `QARCH_CNFG_MENU(_DETAIL)` rows + target screen `DoUICLink` param handling |
| Widget missing/blank | Persona dashboard row + widget-access security; widget registration in `RegisterQPTMWidgets()` (or DS package deployment for CycleChanges etc.) |

---