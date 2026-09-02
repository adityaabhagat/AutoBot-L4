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
---

# PART 2 — ClassicGUI (C++/MFC desktop app, Citrix-delivered)

**Sources:** Quorum.QPTM.ClassicGUI (repo `e6d98ba8`, branch `develop`), APL.QPTM.ClassicGUI (`5da2b9cd`), Quorum.QPTM.Application.ClassicGUI (`b651f0cf`), `.github/copilot-instructions.md` in-repo. **Verification:** full REST-API census of `/Native` (1,722 items) — **158 parent `QVp*` screen classes across folders (~151 unique after cross-folder dedup: ContractMaintenance/EDIDatasetDefinition/EDITPAMaintenance/EDIViewer/Timeline/ReallocationPPAPopUp appear in 2–3 folders)**. QFC framework maintenance screens (Object Usage, security, code tables…) ship separately in the QFCMaintScreens NuGet and are NOT counted here.

## 10. Classic architecture

- **App shell:** `/Native/QPTM/QPipelineMgrApp` (`GetApplicationCode()="PLTM"`, app name "Quorum PTM"), classic QFC MDI doc/view — one `QPipelineMgrDoc`, many views (screens). Menus are MFC resources in `/Native/Include/PipelineMgrCommon.rc`.
- **Plugin screen registration:** each module is an MFC extension DLL (`PipelineMgr<XX>.dll`, `SOA<Feature>.dll`) exporting `RegisterScreensApi` (+ `GetQFCVersion`, `InitAddInDLL`, `IsCAWRegistrationAllowed`). `QPipelineMgrDoc::RegisterDocumentViews` loads: core QFC DLLs → **client DLLs (registered BEFORE core — "first screens registered win" = the Classic client-override mechanism)** → core module DLLs. Each screen registers via macro `QREGISTERSCREENSAPI(QVpClass, ID_<menu resource id>, "dll")` (in `/Native/Include/QPipelineMgrShared.h`) → `QDocViewBroker` with MFC `CRuntimeClass` factory. **Screen identity = C++ class name = security object ID** (`GetSecurityObjectID()` returns the class name, e.g. `QVpSOANomTemplate`); menu binding = command resource ID.
- **Two screen generations:**
  - **Legacy MFC screens** — `QVp<Name>` deriving from `QDBVp*PipelineMgr` bases in `/Native/PipelineMgrShared` (`QDBVpSimple/FilterDetail/FilterHeaderDetail/HeaderDetail/MultiRowQryEdit/AvailSel/TabGridEdit/TabHeaderDetail/TabSimpleEdit...PipelineMgr`, popup base `QDlgPipelineMgr`). Tab pages = separate files `QVp<Screen>_<Tab>.cpp`. Data access = **direct SQL** through `QDBManager` + registered `QDBQuery` classes (`/Native/PipelineMgrShared/Queries/QQryReg*.cpp`, `/Native/QPTM/QueryRegistration.cpp`).
  - **SOA screens** (modern) — thin C++/CLI viewports generated by `QTWinFormsViewM(QViewportSOAQPTMBase, QWinFormsViewQPTM, QCntl<X>Screen, ...)` hosting **.NET WinForms controls** from `/Managed/Quorum.QPTM.UserControls` (`QCntl*Screen : QPTMUserControlBase`). The managed side calls the **same WCF QPTM middle tier as the Web app** (`QServiceContainer.GetService<IQPTM*Service>`, `IQPTMSecurityService.GetPrivileges`, DataObjects). Native↔managed events via `BEGIN_DELEGATE_MAP`/`EVENT_DELEGATE_ENTRY`. So Classic is a **dual-path client: legacy screens = direct DB SQL; SOA screens = middle tier**.
- **Grid/picklist metadata:** Classic grids read **`QARCH_CNFG_GRIDCTRL_COL`** (per SCREEN_ID; CDTBL_ID per column; code tables preloaded at startup via registered query `SelectCodeTablesUsedByScreenGrid`). `QARCH_CNFG_GRIDCTRL_COL_NET` appears nowhere in Classic — it is Web-only. Picklists via `QPikListDefinitionMgr` + `PickID_PipelineMgrCommon.h`.
- **CAW build** (`/Native/QPTMCAW`, define `CAW_BUILD`, exe "Quorum PTM_CAW.exe") = the restricted **external-customer edition**: DLLs must export `IsCAWRegistrationAllowed()=true` or their screens don't load; **QFC architecture/maintenance screens (incl. Object Usage) are compiled out**; trimmed CAW menus; `CAW_BUILD_GS` rebrands as "Quantium".
- **QFC maintenance screens** (Object Usage, security-object admin, code-table/config maintenance) come from NuGet `Quorum.QFC.CPP.GUI.QFCMaintScreens` (QFCS1600.dll) via `RegisterArchitectureScreens` — internal builds only, source not in this repo.
- **Client/host repos (mirror of Web pattern):** `<CLIENT>.QPTM.ClassicGUI` builds client DLLs loaded via `GetClientDLLInstanceMap()` (APL's contains only splash branding; screen-override DLLs follow the same shape). `<CLIENT>.QPTM.Application.ClassicGUI` = deployable packaging repo: aggregates GUI NuGets + per-environment `Quorum PTM*.ini` variants (Cloud / OnPremDirect / OnPremNI), ODBC `.dsn` files, app.config transforms, secret manifests — how the Citrix-published exe is pointed at DB + middle tier per environment.
- **Quirks:** `PipelineMgrSC`, `PipelineMgrCW`, `PipelineMgrPB`, `PipelineMgrRR` are **empty shell DLLs** (no screens; RegisterScreensApi no-ops). CP = "Corporate" module. Several screens are compiled but NOT menu-registered (`QVpSOAMultiGroupSchedulingScreen`, `QVpSOARoutePathMaintScreen`, `QVpCapRelWithdrawalSummary`) — reachable via security-object/runtime-class launch or dormant. `QVpSOALCNominationSubmission.cpp` defines class `QVpLCSOANominationSubmission`. `QvpSOAHourlyPenaltySchedule` has lowercase 'v'.

## 11. Classic screen catalog (by module; ✔ = Web equivalent exists, ✖ = Classic-only)

### Nominations (PipelineMgrNN / NNInt / SOANominations / SOAAutoGen)
| Screen (QVp class) | Web | Notes |
|---|---|---|
| QVpSOANominationSubmission | ✔ NominationSubmission | .NET-hosted; ID_DOTNET_NOMINATION_SUBMISSION |
| QVpSOALCNominationSubmission (class QVpLCSOANominationSubmission) | ✔ LCNominationSubmission | import, bulk copy, clear zero-qty |
| QVpSOANominationMaintenance | ✔ NominationMaintenance | |
| QVpSOANomTemplate | ✔ PostNominationSubmissionTemplate | display name "Post Nomination Submission Template" |
| QVpSOANominationAutoGen | ✔ NominationAutogen | own DLL SOAAutoGen (CAW-disallowed) |
| QVpSOANominationNavigation | ✖ | nomination navigation pane |
| QVpSOAMiddleTierRefresh | ✖ | middle-tier cache refresh utility |
| QVpNominationConfigurationUserPreferences | ✔ NominationConfigureUserPreference | tabs General, CashForFuel |
| QVpNominationErrorOverrides | ✔ NominationErrorOverrides | |
| QVpNominationConfigurationSystemPreferences (NNInt) | ✖ | system-level nom config |
| QVpValidationRuleAssignment (NNInt) | ✔ ValidationRuleAssignment | |
| QVpValidationRuleMaintenance (NNInt) | ✖ | define validation rules |
| QVpValidationRuleXRef (NNInt) | ✖ | rule cross-reference (PAXREF_VALD_RULE*) |

### EDI (PipelineMgrED / EDInt) — mostly Classic-only config
QVpDatasetLoopDefinition ✖, QVpDatasetSegmentDefinition ✖, QVpEDIDependentRule ✖, QVpEDITPAElementUsage ✖, QVpEDITemplateDefinition ✖ (tabs Elements/Segments), QVpEDITransactionSubmittal ✖, QVpEDIDatasetDefinition ✖ (tabs General/Segments; parent in EDInt), QVpEDITPAMaintenance ✔ TPAMaintenance, QVpEDIViewer ✖ (tab Translated), QVpEDITransactions ✔ EDTransaction. *(RegisterScreensED.cpp is empty — ED screens register from EDInt.)*

### Contracts / RFS (PipelineMgrK / KInt / SOAContracts / SOARequestForService)
| Screen | Web | Notes |
|---|---|---|
| QVpContractMaintenance (parent in KInt) | ✔ ContractMaintenance | tabs contributed from 3 folders; SOAContracts adds .NET-hosted tabs Rates (QCntlRatesTab), LocPathMDQ, LocZoneMDQ; K adds SOPLDLimits/SOPLDSetup/SOPLocations |
| QVpLongTermBidViewer | ✔ LongTermBidViewer | competing-bids grid, auto-refresh |
| QVpSOARequestForService | ✔ RFSWizardV2 / NewRFSActivity | hosts QCntlRFSContractScreen; RFS→Contract creation events |
| QVpRequestForService (KInt) | ✔ (legacy of RFS) | |
| QVpRequestForServiceApprovalQueue (KInt) | ✔ RFSApproval | |
| QVpContractContactMassChange (KInt) | ✔ CtrCntctOvrdMassChange | |
| QVpContractsDefaultAgents (KInt) | ✔ DefaultAgents | |
| QVpRatchetMaintenance (KInt) | ✔ RatchetSchedule | |
| QVpSeasonalProfileMaintenance (KInt) | ✔ SeasonalProfile | |
| QVpTOSMaintenance (KInt) | ✔ TypeOfServiceSetup/TOSSetup | |
| QVpAggregateQuantitySplitDlg, QVpCurrentMDIQAndMDWQDlg (KInt) | — | popups |

### Scheduling / Confirmations (PipelineMgrCF / CFInt / SCInt / PBInt / SOAScheduling / SOAConfirmations)
| Screen | Web | Notes |
|---|---|---|
| QVpSOAGraphicalTabularScreen | ✔ CASummaryMaintenance | "Scheduling - CAS Maintenance"; launches CANOMCLTG/RPT_CA29/CFPSTRESP/CFAUTOCONF |
| QVpSOAMultiGroupSchedulingScreen | ✖ | compiled, not menu-registered |
| QVpSOARoutePathMaintScreen | ✖ | Route Path Maintenance |
| QVpSOAConfirmation | ✔ ConfirmationResponse | post-submit CFPSTRESP with retry loop |
| QVpSOAConfirmationSummary | ✔ ConfirmationSummary | drill to Confirmation via context link |
| QVpConfirmationLocationQuickView | ~ ConfirmationSummaryQuickView | read-only loc inquiry (pactrl_loc*) |
| QVpLifeCycle | ✔ LifeCycle | nnctrl_lifecycle trace; ext users 1-month cap |
| QVpConfirmationResponseFilterDlg / QVpConfResponseOnlineRptDlg | — | popups |
| QVpConfirmationLevel, QVpConfirmationPlanLocation/Security/Setup (CFInt) | ✖ | confirmation-plan config set |
| QVpCASVolApprovalMaintenance (SCInt) | ✖ | CAS volume approval |
| QVpLeaseSchedulingMaintenance (SCInt) | ✔ LeaseSchedulingConfigurationMaintenance | |
| QVpSchedulingGroupEntryMaintenance (SCInt) | ✖ | |
| QVpEPSQMaintenance (PBInt) | ✔ EPSQMaintenance | PB = path balancing |
| QVpPathBalanceVolApproval (PBInt) | ✔ PathBalanceVolumeApproval | |

### Capacity Release (PipelineMgrCR / CRInt)
QVpCapRelOffer ✔ OfferWizardV2 (11 tabs), QVpCapRelBid ✔ BidWizardV2/CRBid (7 tabs), QVpCapRelAward ✔ CRAward (3 tabs), QVpCapRelAwardAmendments ✔ AwardAmendments, QVpCapRelOfferViewer ✔ OfferViewer, QVpBidViewer ✔ BidViewer, QVpRecallReput ✔ RecallReput, QVpCapRelWithdrawalSummary ✔ WithdrawalSummary (not menu-registered), QVpTimeline + QVpTimelineResults ✖ (CR timeline, parent in CRInt; CR contributes Bid tab).

### Allocation / Measurement / PDA (PipelineMgrAL / ALInt / SOAPDASubmission)
QVpDailyAllocatedQuantityMaintenance ✔ (tabs Daily/Summary), QVpMonthlyAllocatedQuantityMaintenance ✔, QVpPreDeterminedAllocationSubmission ✔ PdaSubmission (+FormDlg popup), QVpSOAPDASubmission ✔ PdaSubmission (.NET), QVpSOAHourlyMeasurementEntry ✔ HourlyMeasurementMaintenance, QvpSOAHourlyPenaltySchedule ✔ HourlyPenaltySchedule, QVpMeasurementEntry ✔ (ALInt), QVpMeasurementResults ✔ (ALInt), QVpGasAnalysis ✔ GasAnalysisSearch (ALInt), QVpReallocationStatus ~ ReallocationMaintenance (ALInt), QVpAllocationPlanMaintenance ✖, QVpAllocationTransactionType ✖, QVpFuelTypeOfChargeRanking ✖, QVpMonthlyVolumeQuantitiesDlg (popup).

### Inventory / Imbalance (PipelineMgrIN / INInt)
QVpCustomerAccount ✔ CustomerAccountSummary (6 tabs: Activity/Adjustments/Authorize/Balance/Contracts/Details), QVpCustomerAcctQuery ✔ CustomerAccountQuery, QVpImbalanceTradingMaintenance + QVpImbalanceTradingMaintenanceForm ✔ ImbalTradingMaintForm, QVpShipperImbalanceSummary ~ PostedImbalance/AuthToPostImbal, QVpStorageTransferMaintenance + QVpStorageTransferGrid ✔ StorageTransferMaintForm, QVpInventory ✔ InventoryAccounts (INInt), QVpInventoryAdjustments ✔ (INInt), QVpTradingRulesMaintenance ✖ (INInt), QVpManualPostingQuantityDlg (popup).

### Billing / Invoicing / Penalties (PipelineMgrBL / BLInt)
QVpInvoiceHeaderMaintenance ✔ InvoiceMaintenance (+ unregistered RIL client variant), QVpInvoiceHeaderByContractTOS ✔, QVpInvoiceDetailMaintenance ✔, QVpInvoiceSubDetailMaintenance(+TOC) ✔, QVpSubAccount ✖, QVpBillPeriodMaintenance ✖ (BLInt), QVpChartOfAccount ✔ ChartOfAccounts, QVpInvoiceGroup ✔ InvoiceGroupMaintenance, QVpInvoiceMsgMaintenance ✔, QVpPPAEventMaintenance ✔, QVpPenaltyResults ✔, QVpPenaltySubmission ✔, QVpTSPBillingConfigurations ✔ TspBillingConfiguration, QVpPenaltyTierDetailDlg + QVpReallocationPPAPopUp (popups; latter ✔ PPAReallocationDialog).

### Rates (PipelineMgrRT / RTInt)
QVpRateQuery ✔, QVpRateMaintenance ✔, QVpRateSeasonalProfileMaintenance ✔, QVpIndexMaintenance ✔, QVpTierMaintenance ✔, QVpTypeOfChargeMaintenance ✔ TypeOfChargeMaintenance, QVpTOSChargeBasisMaintenance ✔ TOSChargeBasisSetup, QVpDiscountOfferMaintenance ✖, QVpTOCProcessAssociation ✖ (~RateTocObjectAssociation), QVpTOCTOSRuleMaintenance ✖.

### Pipeline Admin / Corporate / Shared (PipelineMgrPA / PAInt / SOAPipelineAdmin / CP / CWInt / Shared)
| Screen | Web | Notes |
|---|---|---|
| QVpLocationMaintenance, QVpLocationGroupMaintenance, QVpLocationGroupPathMaintenance, QVpLocationPathMaintenance, QVpLocationGroupLookup, QVpLocationContactMassChange (PAInt/PA) | ✔ same names | |
| QVpTSPConfigurationSettings (PAInt) | ✔ TspConfigurationSettings | config keys |
| QVpSchedulingCapacityOverride (PAInt) | ✔ SchedulingCapacityOverrideMaint | |
| QVpCASReductionOrder, QVpClassificationRulesEntryMaintenance, QVpNomClassificationMaint (PAInt) | ✔ | |
| QVpAfterHrsOnCallCal (PAInt) | ✔ OnCallCalendar | |
| QVpNotificationPreferences (PA) | ✔ NotificationPreference | PACTRL_CONTACT_NOTICE_PREF |
| **QVpCycles (PAInt)** | ✖ | **cycle/deadline configuration (PACTRL_CYCLE / PACTRL_CYCLE_DEADLINE) — Classic-only** |
| QVpTSPMaintenance (PAInt) + QVpSOATSPMaintenance | ✖ | TSP setup (native legacy + .NET SOA versions) |
| QVpFacilityMaintenance, QVpHolidayMaintenance, QVpELIRuleMaintenance, QVpLocationDefaultHeatingFactor, QVpClassificationRuleSetTransGrp, QVpSchedObjectRuleSetMaint, QVpPreapprovedText, QVpNoticeSetup(+PLTM) (PAInt) | ✖ | Classic-only admin/config set |
| QVpSOAAdvancedArchive | ✖ | Advanced Archive Setup (requires QPTM Service) |
| QVpUserNotificationSubscriptionManager, QVpUserNotificationContactAssignment (CP="Corporate") | ✖ | event-notification subscriptions (qarch_event_notify_contact) |
| QVpIndexOfCustomersContracts, QVpIndexOfCustomersLocations (CWInt) | ✔ IndexOfCustomers | FERC IoC |
| QVpSecurityUserPLTM (Shared) | ✖ | Security User Setup (tabs Group/ContactInfo/BP/TSP) |
| QVpTreeNavigationTSP (Shared) | ✖ | dockable TSP nav tree pane (CAW variant tab for external builds) |

## 12. Classic↔Web L4 rules of thumb

- **Config lives in Classic**: cycles/deadlines (QVpCycles), TSP maintenance, validation rule definition/xref, confirmation plans, EDI dataset/template/TPA-element config, holiday/facility/heating-factor, notice setup, discount offers, TOC/TOS rules, bill periods, security user setup, Object Usage (QFC maintenance screen). "Can we do X on the Web?" for these → No, Classic-only (matches SKILL_UI_Widgets case 24-00987383 pattern).
- **Operational entry is dual** (SOA Classic + Web): nominations, confirmations, CAS scheduling, RFS/contracts, CR offers/bids/awards, PDA, measurement, invoices, imbalance/storage — SOA Classic screens and Web screens call the SAME middle-tier services, so business-logic defects usually reproduce in both; **rendering/metadata defects don't** (Classic reads QARCH_CNFG_GRIDCTRL_COL, Web reads _COL_NET/QPTMGridDefs.cs — the root of most "works in Classic, broken in Web" cases).
- **Legacy MFC screens (direct SQL)**: grid/query issues on these (LifeCycle, CustomerAccount, CapRel*, Invoice*, most *Int screens) trace to registered QDBQuery SQL in `/Native/PipelineMgrShared/Queries/` or the module folder — not middle-tier services.
- **External (CAW) users**: missing screens/menus in the customer build are usually by design — `IsCAWRegistrationAllowed`, `#ifndef CAW_BUILD`, or CAW menu resources, not security config.
- **Client override**: a screen behaving differently for one client on Classic → client DLL registered first wins (check `<CLIENT>.QPTM.ClassicGUI`), or client `<CLIENT>.QPTM.Metadata` QARCH rows.


---
---

# PART 3 — Navigation map (how a user reaches each screen)

**Sources:** `/Native/Include/PipelineMgrCommon.rc` (Classic menu chrome, Quorum.QPTM.ClassicGUI), `QARCH_CNFG_MENU.json` (510 rows) + `QARCH_CNFG_DYNUC.json` (persona menus) from Quorum.QPTM.Metadata `/STANDARD 16.0/`. These are the STANDARD trees — every client's `<CLIENT>.QPTM.Metadata` repo can add/hide/re-arrange items, so a client's menus may differ.

## 13. How navigation is assembled

**Classic (desktop/Citrix):** the menu bar chrome is a static MFC resource (`IDR_PIPELINEMGRDRTYPE`): `System | Edit | View | <SCREENS> | Maintenance | Window | Help`. The `<SCREENS>` placeholder (and `<SYS_MENU1>`, `<SYS_MENU2>`, `<QARCH_MAINT_MENU>` inside System/Maintenance) are replaced at startup from **`QARCH_CNFG_MENU`** rows: anchor rows carry `LOCATION_TAG` (SCREENS, SYS_MENU1, SYS_MENU2, QARCH_MAINT_MENU, CAW_SCREENS, CAW_SYS_MENU2), children link via `PARENT_MENU_ID`, ordered by `MENU_SEQ`; leaves have `TO_OBJECT_TYPE_CD='SCRN'` and `TO_OBJECT_ID` = the screen's QVP* security id. Items are then security-trimmed per user and `HIDDEN_IND`/`ACTIVE_IND` filtered. The static System menu already hardcodes Login/Logout, TSP Maintenance, **Batch Process Execution…**, Report Execution…, Schedule Creation…, Scheduled Process Viewer…, Message Log Viewer…, Cache Maintenance…; Maintenance hardcodes Tools/Context Data/DocGen Wizard/SQL Log Viewer etc. The per-screen **Links menu** (right-click/Links dropdown) comes from `QARCH_CNFG_MENU` rows with `LOCATION_TAG='<QVPSOURCESCREEN>_LINK'` (73 screens have Links menus, 191 link rows).

**Web (myQuorum):** user → assigned **persona** (`QARCH_CNFG_DYNUC` Persona row) → that persona's **Menu** row = the left-nav tree (leaves reference screens by SecurityId — a mix of `QVP*` ids shared with Classic-SOA screens and `QUC*` ids for Web-only UIControllers) → security-trimmed → click resolves SecurityId → registered MVC route (ScreenRegistrationSpecs). The persona's **Dashboard** row defines the widget layout on Home.

## 14. Classic menu tree (internal build — what a user clicks)

Menu bar: **System | Edit | View | Screens | Maintenance | Window | Help**

System menu (static + SYS_MENU1/2 injected): Login/Logout/Reconnect, Open TSP…, TSP Maintenance…, **Batch Process Execution…**, Report Execution…, Schedule Creation…, Scheduled Process Viewer…, Screen Message Log Viewer…, Cache Maintenance…, [injected: Organizational Hierarchy Maintenance…, Company Address…, Batch Process Message Log Viewer…, Generated Report Finder…], Reload Code Table, User Default Values…, [injected: User Configuration Parameters…, Event Subscription Manager…, User Notification Profile…, Notification Preferences…], Change User Password…, Print…, Exit.

Maintenance menu (internal only; QFC architecture screens like **Object Usage** are injected here from QFCMaintScreens + `QARCH_MAINT_MENU` rows e.g. Registered SQL): Tools (Customize/Shortcuts/Commands/DB Table Data Transfer), Context Data, Document Generation Wizard, Login Setup, SQL Log Viewer…, Show Messages, Log All SQL, SystemRecorder.

Screens menu (from QARCH_CNFG_MENU, LOCATION_TAG=SCREENS — (HIDDEN)/(INACTIVE) shown as flagged in standard metadata):

```
===== LOCATION_TAG: SCREENS =====
+ Screens
  + Allocations
    - Daily Allocated Quantity Maintenance...   [QVPDAILYALLOCATEDQUANTITYMAINTENANCE]
    - Gas Analysis Viewer...   [QVPGASANALYSIS]
    - Hourly Measurement Entry...   [QVPSOAHOURLYMEASUREMENTENTRY]
    - Measurement Entry...   [QVPMEASUREMENTENTRY]
    - Measurement Results...   [QVPMEASUREMENTRESULTS]
    - Monthly Allocated Quantity Maintenance...   [QVPMONTHLYALLOCATEDQUANTITYMAINTENANCE]
    - PDA Submission...   [QVPPREDETERMINEDALLOCATIONSUBMISSION]
    - PDA Maintenance...   [QVPSOAPDASUBMISSION]
    - Reallocation Status...   [QVPREALLOCATIONSTATUS]
  + Billing
    - Demand Charge Determination...   [QVPDEMANDCHARGEDETERMINATION]   (HIDDEN)
    - Invoice Detail Maintenance...   [QVPINVOICEDETAILMAINTENANCE]
    - Invoice Group Maintenance...   [QVPINVOICEGROUP]
    - Invoice Header Maintenance...   [QVPINVOICEHEADERMAINTENANCE]
    - Invoice Header by Contract/TOS...   [QVPINVOICEHEADERBYCONTRACTTOS]
    - Invoice Sub TOC Detail Summary...   [QVPINVOICESUBDETAILMAINTENANCETOC]
    - Invoice Sub-Detail Summary...   [QVPINVOICESUBDETAILMAINTENANCE]
    - Penalty Results...   [QVPPENALTYRESULTS]
    - Penalty Submission...   [QVPPENALTYSUBMISSION]
    - PPA Event Maintenance...   [QVPPPAEVENTMAINTENANCE]
  + Business Associates
    - Business Associate Contact...   [QVPBUSINESSPARTYCONTACT]
    - Business Associate - Entity...   [QVPBAENTITYTABVW]
    - Contact Mass Change...   [QVPBUSINESSPARTYCONTACTMASSCHANGE]
    - Contact Search...   [QVPBUSINESSPARTYCONTACTSEARCH]
    - Credit Maintenance...   [QVPCREDITMAINTENANCE]
    - Default Agents...   [QVPCONTRACTSDEFAULTAGENTS]
    - Global Contact Search...   [QVPCONTACTSEARCH]
  + Capacity Release
    - Award...   [QVPCAPRELAWARD]
    - Award Amendments...   [QVPCAPRELAWARDAMENDMENTS]
    - Bid...   [QVPCAPRELBID]
    - Bid Summary...   [QVPBIDVIEWER]
    - Offer...   [QVPCAPRELOFFER]
    - Offer Summary...   [QVPCAPRELOFFERVIEWER]
    - Recall/Reput...   [QVPRECALLREPUT]
    - Timeline Results...   [QVPTIMELINERESULTS]
    - Withdrawal Summary...   [QVPCAPRELWITHDRAWALSUMMARY]
  + Confirmations
    - Confirmation Response...   [QVPSOACONFIRMATION]
    - Confirmation Summary...   [QVPSOACONFIRMATIONSUMMARY]
    - EPSQ Maintenance...   [QVPEPSQMAINTENANCE]
    - Life Cycle...   [QVPLIFECYCLE]
    - Location Quick View...   [QVPCONFIRMATIONLOCATIONQUICKVIEW]
    - Path Balance Volume Approval...   [QVPPATHBALANCEVOLAPPROVAL]
  + Contracts
    - Contract Maintenance...   [QVPCONTRACTMAINTENANCE]
    - Contract-Contact Override Mass Change...   [QVPCONTRACTCONTACTMASSCHANGE]
    - Long Term Bid Viewer...   [QVPLONGTERMBIDVIEWER]
    - Ratchet Maintenance...   [QVPRATCHETMAINTENANCE]
    - Request For Service...   [QVPSOAREQUESTFORSERVICE]
    - Request For Service Approval Queue...   [QVPREQUESTFORSERVICEAPPROVALQUEUE]
    - Seasonal Profile Maintenance...   [QVPSEASONALPROFILEMAINTENANCE]
  + Corporate   (HIDDEN)
    - User Notification Contact Assignment...   [QVPUSERNOTIFICATIONCONTACTASSIGNMENT]
    - User Notification Subscription Manager...   [QVPUSERNOTIFICATIONSUBSCRIPTIONMANAGER]
  + EDI
    - Dataset Viewer...   [QVPEDIVIEWER]
    - TPA Element Usage...   [QVPEDITPAELEMENTUSAGE]   (HIDDEN,INACTIVE)
    - TPA Maintenance...   [QVPEDITPAMAINTENANCE]
    - Transaction History...   [QVPEDITRANSACTIONS]
    - Transaction Submittal...   [QVPEDITRANSACTIONSUBMITTAL]   (HIDDEN,INACTIVE)
  + Inventory Accounts
    - Customer Account Query...   [QVPCUSTOMERACCTQUERY]
    + Customer Accounts
      - Customer Account Maintenance...   [QVPCUSTOMERACCOUNT]
      - Customer Account Summary...   [QVPSHIPPERIMBALANCESUMMARY]
    + Imbalance Trades
      - Imbalance Trading Form...   [QVPIMBALANCETRADINGMAINTENANCEFORM]
      - Imbalance Trading Summary...   [QVPIMBALANCETRADINGMAINTENANCE]
    - Inventory Accounts...   [QVPINVENTORY]
    - Inventory Adjustments...   [QVPINVENTORYADJUSTMENTS]
    + Storage Transfers
      - Storage Transfer Summary...   [QVPSTORAGETRANSFERGRID]
      - Storage Transfer Maintenance Form...   [QVPSTORAGETRANSFERMAINTENANCE]
  + Locations
    - Location Contact Mass Change...   [QVPLOCATIONCONTACTMASSCHANGE]
    - Location Default Heating Factor...   [QVPLOCATIONDEFAULTHEATINGFACTOR]
    - Location Group Lookup...   [QVPLOCATIONGROUPLOOKUP]
    - Location Group Maintenance...   [QVPLOCATIONGROUPMAINTENANCE]
    - Location Maintenance...   [QVPLOCATIONMAINTENANCE]
    - Parallel Scheduling...   [QVPSOAMULTIGROUPSCHEDULINGSCREEN]
  + NAESB   (HIDDEN)
  + Nominations
    - <NEW> Schematics...   [QVPSOASCHEMATICS]   (HIDDEN)
    - Location-Centric Nomination Submission...   [QVPLCSOANOMINATIONSUBMISSION]   (HIDDEN)
    - Nomination Error Overrides...   [QVPNOMINATIONERROROVERRIDES]
    - Nomination Maintenance...   [QVPSOANOMINATIONMAINTENANCE]
    - Nomination Navigation...   [QVPSOANOMINATIONNAVIGATION]
    - Nomination Submission...   [QVPSOANOMINATIONSUBMISSION]
    - On Call Calendar...   [QVPAFTERHRSONCALLCAL]
    - Post Nomination Submission Template...   [QVPSOANOMTEMPLATE]
    + Submission / Maintenance   (HIDDEN)
  + Rates
    - Discount Offer Maintenance...   [QVPDISCOUNTOFFERMAINTENANCE]
    - Index Maintenance...   [QVPINDEXMAINTENANCE]
    - Rate Maintenance...   [QVPRATEMAINTENANCE]
    - Rate Query...   [QVPRATEQUERY]
    - Seasonal Profile Maintenance...   [QVPRATESEASONALPROFILEMAINTENANCE]
    - Tier Maintenance...   [QVPTIERMAINTENANCE]
  + Regulatory Reporting   (HIDDEN)
  - Reporting   [QVPBATCHPROCESSREPORTEXECUTION]   (HIDDEN)
  + Revenue Details   (HIDDEN)
    - Plan Data Update...   [QVPPLANDATAUPDATE]
    - Top Side Entry...   [QVPREVENUEDETAILTOPSIDEENTRY]
  + Scheduling
    - CAS Maintenance   [QVPSOAGRAPHICALTABULARSCREEN]   (HIDDEN,INACTIVE)
    - Scheduling Volume Approval / Maintenance...   [QVPCASVOLAPPROVALMAINTENANCE]   (HIDDEN)
    - CAS Maintenance...   [QVPSOAGRAPHICALTABULARSCREEN]
    - Location Scheduling Capacity Override...   [QVPSCHEDULINGCAPACITYOVERRIDE]
  + System Setup
    + Allocations
      - Allocation Plan Maintenance...   [QVPALLOCATIONPLANMAINTENANCE]
      - Allocation Transaction Type...   [QVPALLOCATIONTRANSACTIONTYPE]
      - Fuel Type Of Charge Ranking...   [QVPFUELTYPEOFCHARGERANKING]
      - Hourly Penalty Schedule...   [QVPSOAHOURLYPENALTYSCHEDULE]
    + Billing
      - Bill Period Maintenance...   [QVPBILLPERIODMAINTENANCE]
      - Billing Configurations...   [QVPTSPBILLINGCONFIGURATIONS]
      - Chart of Accounts...   [QVPCHARTOFACCOUNT]
      - Invoice Messages...   [QVPINVOICEMSGMAINTENANCE]
      - Sub Account Maintenance...   [QVPSUBACCOUNT]
    + Capacity Release
      - Timeline...   [QVPTIMELINE]
    + Configuration Settings
      - Global...   [QVPCONFIGURATIONSETTINGGLOBAL]
      - TSP...   [QVPTSPCONFIGURATIONSETTINGS]
      - User...   [QVPCONFIGURATIONSETTINGUSER]
    + Confirmations
      - Confirmation Level...   [QVPCONFIRMATIONLEVEL]
      - Confirmation Plan...   [QVPCONFIRMATIONPLANSETUP]
      - Confirmation Plan Location...   [QVPCONFIRMATIONPLANLOCATION]
      - Confirmation Plan Security...   [QVPCONFIRMATIONPLANSECURITY]
    + Contracts
      - TOS Maintenance...   [QVPTOSMAINTENANCE]
      - Org - Contract Type - Sub Contract Type - Settlement Type...   [QVPCTRTYPE_CTRSUBTYPE_SETTLETYPE_INTEGRATION]
    + EDI
      - Dataset Loop Definition...   [QVPDATASETLOOPDEFINITION]   (HIDDEN,INACTIVE)
      - Dataset Definition...   [QVPEDIDATASETDEFINITION]
      - EDI Dependent Rule...   [QVPEDIDEPENDENTRULE]   (HIDDEN,INACTIVE)
      - Segment Definition...   [QVPDATASETSEGMENTDEFINITION]   (HIDDEN,INACTIVE)
      - Template Definition...   [QVPEDITEMPLATEDEFINITION]   (HIDDEN,INACTIVE)
    + Inventory Accounts
      - Trading Rules Maintenance...   [QVPTRADINGRULESMAINTENANCE]
    + NAESB
      - Index Of Customers - Contracts...   [QVPINDEXOFCUSTOMERSCONTRACTS]
      - Index Of Customers - Locations...   [QVPINDEXOFCUSTOMERSLOCATIONS]
    + Nominations
      - Nomination AutoGen Maintenance...   [QVPSOANOMINATIONAUTOGEN]
      - Nomination Configuration System Preferences...   [QVPNOMINATIONCONFIGURATIONSYSTEMPREFERENCES]
      - Nomination Configuration User Preferences...   [QVPNOMINATIONCONFIGURATIONUSERPREFERENCES]
    + Notice
      - Notice Posting...   [QVPNOTICESETUPPLTM]
      - Notice Users...   [QVPNOTICEUSERS]
      - Notification Preferences...   [QVPNOTIFICATIONPREFERENCES]
    + Notifications
      - Event Detector...   [QVPEVENTNOTIFICATIONSETUP]
      - Event Log...   [QVPEVENTDETECTORLOGVIEWER]
      - Event Type...   [QVPEVENTTYPESETUP]
    + Pipeline Administration
      - Cycles...   [QVPCYCLES]
      - Facility Maintenance...   [QVPFACILITYMAINTENANCE]
      - Middle Tier Cache Maintenance...   [QVPSOAMIDDLETIERREFRESH]
      - Preapproved Text...   [QVPPREAPPROVEDTEXT]
      - TSP Configuration Settings...   [QVPTSPCONFIGURATIONSETTINGS]
      - TSP Holiday Maintenance...   [QVPHOLIDAYMAINTENANCE]
      - TSP Inventory Configurations...   [QVPSOATSPMAINTENANCE]
      - TSP Maintenance...   [QVPTSPMAINTENANCE]
      - Validation Rule Assignment...   [QVPVALIDATIONRULEASSIGNMENT]
      - Validation Rule Cross-Reference   [QVPVALIDATIONRULEXREF]
      - Validation Rule Maintenance...   [QVPVALIDATIONRULEMAINTENANCE]
      - Advanced Archive Setup   [QVPSOAADVANCEDARCHIVE]
    + Rates
      - TOC - Object Association...   [QVPTOCPROCESSASSOCIATION]
      - TOS - Charge Basis Maintenance...   [QVPTOSCHARGEBASISMAINTENANCE]
      - Type Of Charge Maintenance...   [QVPTYPEOFCHARGEMAINTENANCE]
      - TOC - TOS Rule Maintenance...   [QVPTOCTOSRULEMAINTENANCE]
    + Scheduling
      + Classification Rule Setup
        - CAS Reduction Order Maintenance   [QVPCASREDUCTIONORDER]
        - Classification Rule Transaction Groups   [QVPCLASSIFICATIONRULESETTRANSGRP]
        - Classification Rules Entry Maintenance   [QVPCLASSIFICATIONRULESENTRYMAINTENANCE]
        - Lease Scheduling Configuration   [QVPLEASESCHEDULINGMAINTENANCE]   (HIDDEN)
        - Nomination Classification Maintenance   [QVPNOMCLASSIFICATIONMAINT]
        - Scheduling Object/Rule Set Maintenance   [QVPSCHEDOBJECTRULESETMAINT]
      - Scheduling Group/Entry Maintenance...   [QVPSCHEDULINGGROUPENTRYMAINTENANCE]   (HIDDEN)
      - Location Group Path Maintenance...   [QVPLOCATIONGROUPPATHMAINTENANCE]
      - Location Path Maintenance...   [QVPLOCATIONPATHMAINTENANCE]
      - Parallel Scheduling...   [QVPSOAMULTIGROUPSCHEDULINGSCREEN]   (HIDDEN)
      - Route Path Maintenance...   [QVPSOAROUTEPATHMAINTSCREEN]
```

SYS_MENU1/SYS_MENU2/QARCH_MAINT_MENU injections and the **CAW (external-customer) menu tree**:

```
===== LOCATION_TAG: NOMINATION_SCREENS =====
+ Nominations
  - Nomination Maintenance   [QVPSOANOMINATIONMAINTENANCE]

===== LOCATION_TAG: SYS_MENU1 =====
- Organizational Hierarchy Maintenance...   [QVPORGHIERARCHYMAINTENANCE]
- Company Address...   [QVPCOMPANYADDRESS]
- Batch Process Execution...   [QVPBATCHPROCESSEXECUTION]   (HIDDEN)
- Batch Process Message Log Viewer...   [QVPPROCESSMESSAGELOG]
- Report Execution...   [QVPBATCHPROCESSREPORTEXECUTION]   (HIDDEN)
- Generated Report Finder...   [QVPREPORTFILEVIEWER]

===== LOCATION_TAG: SYS_MENU2 =====
- User Configuration Parameters...   [QVPCONFIGURATIONSETTINGUSER]
- Event Subscription Manager...   [QVPUSERSUBSCRIPTIONMGR]
- User Notification Profile...   [QVPUSERPROFILESETUP]
- Notification Preferences...   [QVPNOTIFICATIONPREFERENCES]

===== LOCATION_TAG: QARCH_MAINT_MENU =====
- Registered SQL   [QVPSOAREGISTEREDSQL]

===== LOCATION_TAG: CAW_SCREENS =====
+ CAW Screens
  + Allocations   (HIDDEN,INACTIVE)
    - Daily Allocated Quantity Maintenance   [QVPDAILYALLOCATEDQUANTITYMAINTENANCE]
    - PDA Submission   [QVPPREDETERMINEDALLOCATIONSUBMISSION]
  + Nominations
    + Nomination
      - Location-Centric Nomination Submission...   [QVPLCSOANOMINATIONSUBMISSION]   (HIDDEN)
      - Nomination Submission...   [QVPSOANOMINATIONSUBMISSION]
      - Nomination Configuration User Preferences...   [QVPNOMINATIONCONFIGURATIONUSERPREFERENCES]
      - Nomination Maintenance...   [QVPSOANOMINATIONMAINTENANCE]
      - Nomination Navigation...   [QVPSOANOMINATIONNAVIGATION]
    + Confirmation
      - Confirmation Response...   [QVPSOACONFIRMATION]
      - Confirmation Summary...   [QVPSOACONFIRMATIONSUMMARY]
      - Confirmation Location Quick View...   [QVPCONFIRMATIONLOCATIONQUICKVIEW]
      - Life Cycle...   [QVPLIFECYCLE]
    + Scheduled Quantity
      - Scheduled Quantity Reports...   [QVPBATCHPROCESSREPORTEXECUTION]   (HIDDEN)
      - Scheduled Quantity for Operator   [QVPBATCHPROCESSREPORTEXECUTION]
      - Scheduled Quantity for Shipper   [QVPBATCHPROCESSREPORTEXECUTION]
  + Flowing Gas
    + Pre-determined Allocation
      - PDA Submission...   [QVPPREDETERMINEDALLOCATIONSUBMISSION]
    + Allocation
      - Daily Allocated Quantity Maintenance...   [QVPDAILYALLOCATEDQUANTITYMAINTENANCE]
      - Monthly Allocated Quantity Maintenance...   [QVPMONTHLYALLOCATEDQUANTITYMAINTENANCE]
    + Imbalance
      + Customer Accounts
        - Authorization to Post Imbalance...   [QVPCUSTOMERACCOUNT]
        - Customer Account Query...   [QVPCUSTOMERACCTQUERY]
        - Customer Account Summary...   [QVPSHIPPERIMBALANCESUMMARY]
      - Authorization to Post Imbalances...   [QVPCUSTOMERACCOUNT]   (HIDDEN)
      + Imbalance Trades
        - Imbalance Trading Summary...   [QVPIMBALANCETRADINGMAINTENANCE]
        - Imbalance Trading Form...   [QVPIMBALANCETRADINGMAINTENANCEFORM]
      - Imbalance Trade Notification...   [QVPIMBALANCETRADINGMAINTENANCE]   (HIDDEN)
      + Storage Transfers
        - Storage Transfer Summary...   [QVPSTORAGETRANSFERGRID]
        - Storage Transfer Maintenance Form...   [QVPSTORAGETRANSFERMAINTENANCE]
      - Imbalance Account Inquiry...   [QVPCUSTOMERACCOUNT]   (HIDDEN)
      - Customer Account Summary...   [QVPSHIPPERIMBALANCESUMMARY]   (HIDDEN)
    + Measurement
      - Measurement Information...   [QVPBATCHPROCESSREPORTEXECUTION]
  + Invoicing   (INACTIVE)
    + Invoice
      - Invoice Detail Maintenance...   [QVPINVOICEDETAILMAINTENANCE]
      - Invoice Header Maintenance...   [QVPINVOICEHEADERMAINTENANCE]
      - Invoice Header by Contract/TOS...   [QVPINVOICEHEADERBYCONTRACTTOS]
      - Invoice Sub-Detail Summary...   [QVPINVOICESUBDETAILMAINTENANCE]
      - Invoice Sub TOC Detail Summary...   [QVPINVOICESUBDETAILMAINTENANCETOC]
    + Payment Remittance
      - Invoice Documents...   [QVPBATCHPROCESSREPORTEXECUTION]
    - Invoice Group Maintenance   [QVPINVOICEGROUP]   (HIDDEN,INACTIVE)
    + Statement of Account...
      - Invoice Documents...   [QVPBATCHPROCESSREPORTEXECUTION]
  + Capacity Release
    + Offers
      - Offer...   [QVPCAPRELOFFER]
      - Offer Summary...   [QVPCAPRELOFFERVIEWER]
    + Bids
      - Bid...   [QVPCAPRELBID]
      - Bid Summary...   [QVPBIDVIEWER]
    + Awards
      - Award...   [QVPCAPRELAWARD]
      - Recall/Reput...   [QVPRECALLREPUT]
    - Withdrawal Summary...   [QVPCAPRELWITHDRAWALSUMMARY]
  + Confirmations   (HIDDEN,INACTIVE)
    - Confirmation Summary   [QVPSOACONFIRMATIONSUMMARY]
    - Confirmation Response   [QVPSOACONFIRMATION]
  + Inventory Accounts   (HIDDEN,INACTIVE)
    + Customer Accounts
      - Authorization to Post Imbalance   [QVPCUSTOMERACCOUNT]
      - Customer Account Summary   [QVPSHIPPERIMBALANCESUMMARY]
    - Customer Account Summary...   [QVPSHIPPERIMBALANCESUMMARY]
    + Imbalance Trades
      - Imbalance Trading Summary   [QVPIMBALANCETRADINGMAINTENANCE]
      - Imbalance Trading Form   [QVPIMBALANCETRADINGMAINTENANCEFORM]
    + Storage Transfers
      - Storage Transfer Summary   [QVPSTORAGETRANSFERGRID]
      - Storage Transfer Maintenance Form   [QVPSTORAGETRANSFERMAINTENANCE]
  + Contracts
    - Request For Service...   [QVPSOAREQUESTFORSERVICE]   (HIDDEN)
    - Long Term Bid Viewer...   [QVPLONGTERMBIDVIEWER]   (HIDDEN)
    - Contract Reports...   [QVPBATCHPROCESSREPORTEXECUTION]   (HIDDEN)
    - Transportation Contract Brief...   [QVPBATCHPROCESSREPORTEXECUTION]
    - FSS  NNS Contract Brief...   [QVPBATCHPROCESSREPORTEXECUTION]
    - PAL Contract Brief...   [QVPBATCHPROCESSREPORTEXECUTION]
  + IT Discount Reports   (HIDDEN,INACTIVE)
  + Notification Preferences
    - Notification Preferences...   [QVPNOTIFICATIONPREFERENCES]
  + Corporate   (HIDDEN,INACTIVE)
    - E-Mail Documents...   [QVPUSERNOTIFICATIONSUBSCRIPTIONMANAGER]
  - Reporting   [QVPBATCHPROCESSREPORTEXECUTION]
  - Blank Forms   (HIDDEN,INACTIVE)
  - Informational Postings
  - Site Map

===== LOCATION_TAG: CAW_SYS_MENU2 =====
- Event Subscription Manager...   [QVPUSERSUBSCRIPTIONMGR]
- User Notification Profile...   [QVPUSERPROFILESETUP]
- Notification Preferences...   [QVPNOTIFICATIONPREFERENCES]
```

## 15. Web persona menus (left-nav trees from QARCH_CNFG_DYNUC)

### PIPELINE INTERNAL (full internal persona)
```
+ Allocations
  - Daily Allocated Quantity Maintenance   [QVPDAILYALLOCATEDQUANTITYMAINTENANCE]
  - Gas Analysis Search   [QVPGASANALYSIS]
  - Hourly Measurement Maintenance   [QVPSOAHOURLYMEASUREMENTENTRY]
  - Measurement Entry   [QVPMEASUREMENTENTRY]
  - Measurement Results   [QVPMEASUREMENTRESULTS]
  - Monthly Allocated Quantity Maintenance   [QVPMONTHLYALLOCATEDQUANTITYMAINTENANCE]
  - PDA Submission   [QUCPREDETERMINEDALLOCATIONSUBMISSION]
  - Reallocation Maintenance   [QVPREALLOCATIONSTATUS]
+ Billing
  - Invoice Maintenance   [QVPINVOICEHEADERMAINTENANCE]
  - Invoice Group Maintenance   [QVPINVOICEGROUP]
  - PPA Event Maintenance   [QVPPPAEVENTMAINTENANCE]
  - Penalty Submission   [QUCPenaltySubmission]
  - Penalty Results   [QVPPENALTYRESULTS]
+ Business Associate
  - Business Associate   [QUCBusinessAssociate]
  - BA Contact   [QVPBUSINESSPARTYCONTACT]
  - User Contact Information   [QUCUserContactInformation]
  - Credit Maintenance   [QUCBACredit]
  - Contact Mass Change   [QVPBUSINESSPARTYCONTACTMASSCHANGE]
  - Organization Hierarchy Maintenance   [QVPORGHIERARCHYMAINTENANCE]
  - Company Address   [QVPCOMPANYADDRESS]
  - Global Contact Search   [QVPCONTACTSEARCH]
  - Default Agents   [QVPCONTRACTSDEFAULTAGENTS]
+ Capacity Release
  - Offers   [QVpCapRelOfferV2]
  - Offer Summary   [QUCCROfferViewer]
  - Bids   [QVpCapRelBidWizardV2]
  - Bid Summary   [QUCCRBidViewer]
  - Awards   [QUCCRAward]
  - Award Amendments   [QVPCAPRELAWARDAMENDMENTS]
  - Recall / Reput   [QUCCRRecallReput]
  - Withdrawal Summary   [QUCCRWithdrawalSummary]
+ Confirmations
  - Confirmation Response   [QVpSOAConfirmationResponse]
  - EPSQ Maintenance   [QVPEPSQMAINTENANCE]
  - Life Cycle   [QVPLIFECYCLE]
  - Path Balance Volume Approval   [QVPPATHBALANCEVOLAPPROVAL]
  - Confirmation Summary   [QVPSOACONFIRMATIONSUMMARY]
+ Contracts
  - Long Term Bid Viewer   [QUCLongTermBidViewer]
  - Request for Service (RFS)   [QUCRFSWizardScreenV2]
  - RFS Approvals   [QUCRFSApproval]
  - Contract Maintenance   [QVPCONTRACTMAINTENANCE]
  - Contract Seasonal Profile Maintenance   [QVPSEASONALPROFILEMAINTENANCE]
  - Ratchet Maintenance   [QVPRATCHETMAINTENANCE]
  - Contract Contact Mass Change   [QVPCONTRACTCONTACTMASSCHANGE]
+ EDI
  - TPA Maintenance   [QVPEDITPAMAINTENANCE]
  - EDI Transaction Viewer   [QVPEDITRANSACTIONS]
+ Inventory Accounts
  + Customer Accounts
    - Authorization to Post Imbalances   [QVpCustomerAccount]
    - Customer Account Query   [QVPCUSTOMERACCTQUERY]
    - Customer Account Summary   [QVPSHIPPERIMBALANCESUMMARY]
  - Imbalance Trading Form   [QUCImbalanceTradingMaintenanceForm]
  - TSP Inventory   [QVpInventory]
  - Inventory Adjustments   [QVPINVENTORYADJUSTMENTS]
  - Storage Transfer Maintenance Form   [QUCStorageTransferMaintenanceForm]
+ Location
  - Location Group Lookup   [QVPLOCATIONGROUPLOOKUP]
  - Location Maintenance   [QVPLOCATIONMAINTENANCE]
  - Location Group Maintenance   [QVPLocationGroupMaintenance]
  - Location Contact Mass Change   [QUCLocationContactMassChange]
+ Nominations
  - Nomination Error Overrides   [QVPNOMINATIONERROROVERRIDES]
  - Nomination Maintenance   [QVpSOANominationMaintenance]
  - Nomination Submission   [QVpSOANominationSubmission]
  - Location Centric Nominations   [QVpSOALCNominationSubmission]
  - On Call Calendar   [QVpAfterHrsOnCallCal]
  - Nomination Autogen Setup   [QvpSOANominationAutogen]
+ Rates
  - Index Maintenance   [QVPINDEXMAINTENANCE]
  - Rate Maintenance   [QVPRATEMAINTENANCE]
  - Rate/Offer Query   [QVPRATEQUERY]
  - Tier Maintenance   [QVPTIERMAINTENANCE]
  - Rate Seasonal Profile Maintenance   [QVPRATESEASONALPROFILEMAINTENANCE]
+ Scheduling
  - CAS Maintenance   [QVPSOAGRAPHICALTABULARSCREEN]
  - Scheduling Capacity Override Maintenance   [QVPSCHEDULINGCAPACITYOVERRIDE]
+ System Setup
  + Allocations
    - Hourly Penalty Schedule   [QVPSOAHOURLYPENALTYSCHEDULE]
  + Billing
    - TSP Billing Configurations   [QVPTSPBILLINGCONFIGURATIONS]
    - Chart Of Accounts   [QVPCHARTOFACCOUNT]
    - Invoice Message Maintenance   [QVPINVOICEMSGMAINTENANCE]
  + Rates
    - TOC - Object Setup   [QVpTOCProcessAssociation]
    - TOS - Charge Basis Setup   [QVpTOSChargeBasisMaintenance]
    - TOC - TOS Setup   [QVpTOCTOSRuleMaintenance]
    - Type Of Charge Setup   [QVPTYPEOFCHARGEMAINTENANCE]
  + Scheduling
    -  Scheduling Object Rule Set Maintenance   [QVPSCHEDOBJECTRULESETMAINT]
    - Location Path Maintenance   [QVPLOCATIONPATHMAINTENANCE]
    + Classification Rule Setup
      - Nomination Classification Maintenance   [QVPNOMCLASSIFICATIONMAINT]
  + Pipeline Administration
    - Validation Rule Assignment   [QVpValidationRuleAssignment]
    - Tsp Maintenance   [QVPTSPMAINTENANCE]
  + Contracts
    - Type Of Service Setup   [QVPTOSMAINTENANCE]
    - Organization - Contract  XRef Setup   [QVPCTRTYPE_CTRSUBTYPE_SETTLETYPE_INTEGRATION]
  + Confirmations
    - Confirmation Level   [QVPCONFIRMATIONLEVEL]
  + Nominations
    - Nomination Autogen Setup   [QvpSOANominationAutogen]
  - TSP Configuration Settings   [QVPTSPCONFIGURATIONSETTINGS]
  - Contact Notice Preferences   [QVPNOTIFICATIONPREFERENCES]
+ Invoicing
  - Supplemental Documents   [QUCSupplementalDocuments]
+ Informational Postings
  - Informational Postings   [IPWS_SecurityId]
- Sitemap   [QUCSitemap]
+ Local Distribution
  - Aggregate Viewer   [QUCAggregateViewer]
  - Aggregate Location Rules   [QUCAggregateLocationRules]
  - Account Summary   [QUCAccountSummary]
  - Enrollment Management   [QUIControllerEnrollmentWizard]
  - LDC Curtailment Management   [CurtailmentManagementWizard]
```

### PIPELINE SCHEDULER (external shipper/scheduler persona)
```
+ Nominations
  + Nomination
    - Nomination Submission   [QVpSOANominationSubmission]
    - Nomination Maintenance   [QVpSOANominationMaintenance]
  + Confirmation
    - Confirmation Response   [QVpSOAConfirmationResponse]
+ Flowing Gas
  + Pre-determined Allocation
    - PDA Submission   [QUCPREDETERMINEDALLOCATIONSUBMISSION]
  + Imbalance
    + Customer Accounts
      - Authorization to Post Imbalances   [QVpCustomerAccount]
    + Imbalance Trades
      - Imbalance Trading Form   [QUCImbalanceTradingMaintenanceForm]
    + Storage Transfers
      - Storage Transfer Maintenance Form   [QUCStorageTransferMaintenanceForm]
+ Invoicing
  + Supplemental Documents
    - Supplemental Documents   [QUCSupplementalDocuments]
+ Capacity Release
  + Offers
    - Offers   [QVpCapRelOffer]
    - Offer Summary   [QUCCROfferViewer]
  + Bids
    - Bids   [QVpCapRelBidWizard]
    - Bid Summary   [QUCCRBidViewer]
  + Awards
    - Recall / Reput   [QUCCRRecallReput]
  - Withdrawal Summary   [QUCCRWithdrawalSummary]
+ Contracts
  - Request for Service (RFS)   [QUCRFSWizardScreenV2]
  - Long Term Bid Viewer   [QUCLongTermBidViewer]
  - RFS Approvals   [QUCRFSApproval]
+ Reports
  - Reports   [QVpBatchReportExecution]
  - Report Viewer   [QVPReportFileViewer]
```

### PIPELINE OPERATOR (external operator persona — 3 flat items)
```
- Nomination Maintenance   [QVpSOANominationMaintenance]
- Confirmation Response   [QVpSOAConfirmationResponse]
- PDA Submission   [QUCPREDETERMINEDALLOCATIONSUBMISSION]
```

## 16. Example click-paths (training-video style)

| To open… | Classic (internal) | Web (persona) |
|---|---|---|
| Batch Process Execution | **System → Batch Process Execution…** | (not a Web screen — batch via GlobalBatchProcess/ProcessExplorer framework screens) |
| Report Execution | System → Report Execution… | Scheduler persona: Reports → Reports |
| Nomination Submission | Screens → Nominations → Nomination Submission… | Nominations → Nomination (Scheduler) or Nominations → Nomination Submission (Internal) |
| Contract Maintenance | Screens → Contracts → Contract Maintenance… | Contracts → Contract Maintenance (Internal) |
| Confirmation Response | Screens → Confirmations → Confirmation Response… | Confirmations → Confirmation Response |
| CAS (Scheduling) Maintenance | Screens → Scheduling → CAS Maintenance… | Scheduling → CAS Maintenance (Internal) |
| Cycle/deadline config | Screens → System Setup → Pipeline Administration → **Cycles…** | ✖ Classic-only |
| Validation Rule Maintenance / XRef | Screens → System Setup → Pipeline Administration → Validation Rule Maintenance… / Cross-Reference | ✖ Classic-only (Assignment IS on Web: System Setup → Pipeline Administration → Validation Rule Assignment) |
| TSP Maintenance | System → TSP Maintenance… (also Screens → System Setup → Pipeline Administration) | System Setup → Pipeline Administration → Tsp Maintenance |
| Capacity Release Offer | Screens → Capacity Release → Offer… | Capacity Release → Offers (V2 wizard) |
| Object Usage (rule registration) | Maintenance → (QFC architecture screens; internal builds only) | ✖ not on Web |
| Invoice Maintenance | Screens → Billing → Invoice Header Maintenance… | Billing → Invoice Maintenance (Internal) |
| TPA Maintenance (EDI) | Screens → EDI → TPA Maintenance… | EDI → TPA Maintenance (Internal) |
| PDA Submission | Screens → Allocations → PDA Submission… | Flowing Gas → Pre-determined Allocation → PDA Submission (Scheduler) / Allocations → PDA Submission (Internal) |

**L4 note:** the Web persona menu leaves reference security ids that are a MIX of `QVP*` (Classic-shared) and `QUC*` (Web UIController) objects — e.g. Capacity Release Bids maps to `QVpCapRelBidWizardV2` for Internal but `QVpCapRelBidWizard` (V1) for the standard Scheduler persona. When a client says "user can't see screen X in the menu," diff their client DYNUC Menu row + the user's rights on that exact security id.
