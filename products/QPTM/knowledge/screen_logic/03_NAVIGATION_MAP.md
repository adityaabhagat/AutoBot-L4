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
