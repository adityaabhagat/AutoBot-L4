# CONFIG REFERENCE — QPTM & TIPS Master Configuration Key Reference

**Version:** 1.1 | **Created:** 2026-06-11 | **Updated:** 2026-06-13 | **Products:** QPTM (My Quorum Gas Pipeline) & My Quorum TIPS
**Purpose:** One place to look up the config keys that actually show up in L4 cases — what each key does, where the code reads it, and what a misconfiguration looks like from the customer's side.
**Evidence base:** Quorum.QPTM.Web config-constants classes (`QPTMGlobalConfigs.cs` / `QPTMTspConfigs.cs` / `QPTMTspOrGlobalConfigs.cs`), the standard metadata seed (`QARCH_CNFG_CTRL.json`, ~863 keys), `Quorum.QFC.Core` config manager, TIPS TurboTips `ALLOCATE` + `SETTLEMAIN` `ConfigSettingsUsed` adapters, and closed SF cases with Root Cause = **Application Configuration** *or* **ChangeConfig** across BOTH products (sampled 2026-06-13: ~1,065 QPTM Application-Config + 96 QPTM ChangeConfig + 563 TIPS Application-Config + 81 TIPS ChangeConfig cases in scope; ~115 read in detail).
**Companions:** `SKILL_Pipeline_Admin_Config.md` (config-control table, code tables, location admin), `SKILL_EDI_Troubleshooting.md` §16, `SKILL_Capacity_Release.md` §8, `SKILL_Billing.md`, `SKILL_Allocations.md`, `SKILL_Security_UserAdmin.md`.

> **Scope note.** This is the *config-key* reference. Non-key configuration that L4 sees constantly — env file paths / FTP / SFTP creds / service passwords / SSL/PGP certs, metadata check-ins (missing screens/tabs after a hotfix), code-table Displayed-Column-Order, location attributes (`PACTRL_LOC_ATTR`) — lives in `SKILL_Pipeline_Admin_Config.md` §10/§11/§6/§4. Those are summarised in §12 here so you don't mistake them for a key, but not duplicated.

---

## 1. How configuration works in QPTM

### 1.1 Where keys are stored

- Physical store: **`QARCH_CNFG_CTRL`** (middletier logs name it lowercase `qarch_cnfg_ctrl`; older docs/skills call the same store `QARCH_GLOBAL_CONFIG` / `QARCH_TSP_CONFIG`). Each row = one key, with columns observed in the metadata seed: `KEY_GRP_NM`, `KEY_NM`, `APP_LAYER_CD`, `KEY_DESCR`, `KEY_VALUE`, `KEY_VALUE_TYPE_CD`, `KEY_VALUE_MIN/MAX`, `KEY_VALUE_CODETABLE_ID`, `ALLOW_USER_OVERRIDE_IND`, `ENVIRONMENT_SPECIFIC_IND` (source: `<CLIENT>.QPTM.Metadata` repo, `/STANDARD 16.0/QARCH_CNFG_CTRL.json`).
- The **standard seed ships ~863 keys**; each client has its own metadata layer (`<CLIENT>.QPTM.Metadata`, same file path) that overrides/extends the standard values. This is why two clients on the same build behave differently with "no code difference."
- Keys are **grouped** by `KEY_GRP_NM`. Biggest groups in the standard seed: NOMINATIONS (~108), TSP (~51), ALLOCATIONS (~43), CAPACITY_RELEASE (~43), SCHEDULING (~42), CONTRACTS (~38), BILLING (~35), CONFIRMATIONS (~27), EDI (~22), INVENTORY (~22), RATES (~21), CAS (~20), TSP OVERRIDABLE (~20), SECURITY (~10).

### 1.2 How the code reads keys (resolution order)

- Core reader: `Quorum.QFC.Core` repo, `/Quorum.QFC.Core/ConfigSettings/QConfigMgrBase.cs`. Verified signature:
  `public virtual QConfigKeyBase GetConfigKey(string moduleCode, string userId, string keyGroupName, string keyName, ref bool isMissing, bool logMissingToMsgLog)`.
  A **user-specific entry wins over the global value only if the key is overridable** (`ALLOW_USER_OVERRIDE_IND`). A **missing key is non-fatal**: it sets `isMissing` and (if `logMissingToMsgLog`) traces `QConfigMgrBase.GetConfigKey.Missing`; the caller substitutes a hard-coded default. This is the "missing config key" log-flood pattern — SF 25-01031118 / ADO #1744270.
- QPTM typed wrappers live in `Quorum.QPTM.Web` repo, `/Quorum.QPTM.Common/ConfigSettings/`:
  - **`QPTMGlobalConfigs.cs`** (G) — ~101 global-only keys.
  - **`QPTMTspConfigs.cs`** (T) — ~33 per-TSP keys.
  - **`QPTMTspOrGlobalConfigs.cs`** (TG) — ~157 keys with **TSP override → global fallback → code default**: each accessor carries a `[QPTMConfigSettingAttribute(group, key, descr, default)]` and calls `IQPTMMetadataService.GetTspOrGlobalConfigSettingDefault(profile, module, tspNo, keyGroup, keyName, defaultValue, …)` — TSP-scoped value first, then global, then the attribute default. (Accessor map: `/Quorum.QPTM.Common/ConfigSettings/ConfigSettingsAccess/QPTMTspOrGlobalConfigsAccess.cs`.)
  - Boolean parsing accepts `TRUE/FALSE` or `1/0`.
- **Caution:** the *code default* and the *standard seed value* are not always the same (e.g., `AUTO_CALCULATE_EVERGREEN_NOTICE_DATE` code default 0, seed value 1). When a client **deletes** a key instead of setting it, behavior snaps to the **code** default, not the seed.
- **Caching:** config is cached in the middletier; `PIPELINE / STALE_CONFIG_CACHE_TIME` (minutes, 0 = immediate) controls staleness. After a config change, a cache refresh / service recycle may be needed before it takes effect (a recurring "I changed it but nothing happened" symptom).

### 1.3 How changes are made

- UI: **Global Configuration / System Preferences** screen (internal users). In managed-cloud environments the screen can be locked ("UAT Global Config Cannot be Modified" — SF 26-01089759, no self-serve resolution recorded); changes then go through **Cloud Ops** as a config script or a metadata check-in to `<CLIENT>.QPTM.Metadata` + deployment.
- Keys flagged `ENVIRONMENT_SPECIFIC_IND` (file paths, URLs, FTP endpoints) are deliberately **not** copied between environments; missing ones after an upgrade/refresh are fixed by running the environment-specific config script (SF 26-01094015 "Ran script to add missing environment specific configs", 26-01094002, 26-01104783 "configuration changes were applied into the environment").

### 1.4 How configuration works in TIPS

TIPS (TurboTips batch engine) reads config at **three scopes — global, company, plant** — wired per-process in `Quorum.TIPS.Batch` `/Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/<PROCESS>.cs` (`BuildConfigSettings`), reading via `data.GetGlobalConfigSetting / GetCompanyConfigKeyBoolVal / GetPlantConfigKeyBoolVal / GetPlantConfigKeyStringVal / GetPlantConfigKeyIntVal` (defined in `/Quorum.TIPS.Batch.QPDllTurboTips/Data/QTurboTipsData.cs` and the Classic shared lib `Quorum.TIPS.ClassicBatch /Common/QTipsSharedLib/QTipsUtility.cpp`).
- **Each batch process documents its keys in a `ps<PROCESS>_ConfigSettingsUsed.cs` class** in repo `Quorum.Tips.TurboTips` — defaults and behavior in the XML doc-comments, and **each comment states the Level (Global/Plant/Company) and Key Group**. Verified files: `/Quorum.Tips.TurboTips.Allocate/ALLOCATE/psALLOCATE_ConfigSettingsUsed.cs`, `/Quorum.Tips.TurboTips.Settle/SETTLEMAIN/psSETTLEMAIN_ConfigSettingsUsed.cs` (others exist for DAYVOLS, CTRREV, FIXEDFUELS, REVERSAL). **This is the single best authority for TIPS keys — read the matching `ps*_ConfigSettingsUsed.cs` before changing anything.**
- Company config has its own service/DAL (`Quorum.TIPS.Web` `/Quorum.TIPS.ServiceCore/QTIPSServiceCore_TipsUtility.cs`, `/Quorum.TIPS.DAL/CodeGen/CompanyConfigDAL.cs`).
- Real-world example: setting `ACCOUNTING_PERIOD_MODE` to Plant (PLT) level was done by **inserting the key into the global config table in the client's layer** (SF 26-01096195, client QHEC — verbatim: *"Included the configuration 'ACCOUNTING_PERIOD_MODE' in the global config table and set it to Plant (PLT) level in the client's layer (QHEC)."*).
- **Caveat on doc-comment defaults:** a few XML comments say "Default: false" but the C# initializer is `= true` (e.g. `ENABLE_SET_OPTION_APPLIED_CD`, `DEFINE_INFINITY_ZERO`, `WRITE_ALL_RATE_RES_TIER_DETAIL` in SETTLEMAIN). Trust the **initializer** over the prose; both are noted below where they diverge.

---

## 2. Contracts (QPTM)

Defined in `Quorum.QPTM.Web` `/Quorum.QPTM.Common/ConfigSettings/QPTMGlobalConfigs.cs` (G), `QPTMTspConfigs.cs` (T), `QPTMTspOrGlobalConfigs.cs` (TG) unless noted. "Seed" = standard `QARCH_CNFG_CTRL.json` value.

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `VALIDATE_MDQ_REC_DEL` | CONTRACTS | bool; code default empty, **seed 1** | Validates receipt vs delivery MDQ on the contract Locations tab | TG (`QPTMTspOrGlobalConfigs.cs`); consumed by `Quorum.QPTM.ClassicGUI` `/Native/PipelineMgrKInt/QVpContractMaintenance_Locations.cpp` & Web contract maint (`Quorum.QPTM.UnitTests/ContractMaintenance/ContractMaintenanceTests.cs`) | MDQ save blocked / unexpected MDQ validation error on Location tab |
| `ALLOW_DUAL_MDIQ_MDWQ` | CONTRACTS | bool, default 1 | Allows both MDIQ and MDWQ on a contract | TG | Storage contract can't carry both injection and withdrawal max quantities |
| `MDIQ_MDWQ_BASIS` | CONTRACTS | string, default `AVL` | Which basis to use for MDIQ/MDWQ when both a fixed quantity and a ratchet exist | T (`QPTMTspConfigs.cs`) | "MDIQ/MDWQ wrong when ratchets exist" |
| `CALCULATE_MAX_MSQ_BASED_ON_SEASONAL_PROF` | CONTRACTS | bool; code 0, seed 1 | Auto-sets Fixed MSQ / MSQ Seasonal Profile on Contract Maintenance | G | Max MSQ not calculating from seasonal profile |
| `AUTO_CALCULATE_EVERGREEN_NOTICE_DATE` | CONTRACTS | bool; code 0, seed 1 | Auto-calculates Evergreen Notice Date | G | "Invalid Evergreen" error on save (cf. SF 26-01099193 — unchecking evergreen attr disables validation) |
| `ALLOW_MDQ_NA_VALUES` | CONTRACTS | bool, 0 | Allow MDQ value entry when MDQ type 'Not Applicable' selected | G | MDQ field locked/unlocked unexpectedly for NA-type contracts |
| `USE_TSP_TOS_CTR_PREFIX` | CONTRACTS | bool, 0 | New contract numbers get TSP+TOS-specific prefix | G | Contract autonumbering format complaints (cf. SF 25-01003753) |
| `PROP_CTR_NO_IND` | TSP | bool, 0 | Use proposed contract number only | TG | Wrong contract numbering on RFS award |
| `NEW_AMEND_NUM_FOR_ATTR_UPDATE` | CONTRACTS | bool, 0 | Bump amendment # when a contract attribute is updated | G | "Why did/didn't an amendment get created when I changed an attribute" (cf. SF 25-01061791 — PAL tab "additive" amendment handling) |
| `DISABLE_NNS_IMBAL_K_VALIDATION` | CONTRACTS | bool, default 1 | Disables imbalance-tab validations for NNS contracts | G | NNS contract imbalance tab blocking saves when set to 0 |
| `RFS_AUTO_APPROVE_SEC_USER` | CONTRACTS | bool, 0 | Auto-approve RFS for departments at/below submitter's highest department | G | RFS stuck waiting for approval / approved unexpectedly |
| `AUTO_AWARD_RFS_ON_APPROVAL` | RFS | bool, 0 | Award the RFS automatically when approved | TG | RFS approved but contract not generated (cf. SF 26-01088173 — "Automated RFS Award Process Upon last department approval") |
| `VALIDATE_CTR_TOS_FACILITY` | CONTRACTS | string, default empty | Gates a TOS/facility validation on contracts (the KEY_DESCR in code is a copy-paste of VALIDATE_MDQ_REC_DEL — **behavior inferred, verify in code**) | TG | TOS-facility validation firing/not firing |

> Other contract cases that are config-but-not-a-key: rate-sequence mismatches preventing rate resolution (SF 26-01102601 "Updated the sequences on the rates", 26-01101441 "Remove the TOS from Rate ID 169"), contract effective-date corrections (SF 26-01103577), and amendment/aggregate-meter cleanup (SF 26-01103642). Those are *data* fixes on the contract/rate records, not `QARCH_CNFG_CTRL` keys.

## 3. Nominations & Cycles (QPTM)

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `BLOCK_BI_NOM_SUBMISSION` | NOMINATIONS | bool, seed 0 | When 1, Business-Invalid (BI) nomination records are **not** submitted (BI treated like LI); when 0 they submit anyway | `Quorum.QPTM.Web` `/Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService.cs`; `Quorum.QPTM.Batch` `/Quorum.QPTM.QPDllNominations/Zero Out Nominations/QZeroOutNomsSeg.cs`, `/AutoGen/QPSNomAutoGenSeg.cs` | "One bad line blocked my whole batch" vs "errored noms went through" (see SKILL_EDI_Troubleshooting §16) |
| `DEFAULT_NOMS_SUBS_CYCLE_IND` | NOMINATIONS | bool, seed 1 | Default for "generate subsequent cycle nominations" flag (EDI-side: the `IsNomSubsCycle` default when inbound NMST has no specifier) | seed; EDI path in `Quorum.QPTM.Batch` G873NMST processing | Noms unexpectedly (not) rolling to later cycles |
| `CHECK_OPEN_NOM_CYCLE_FOR_EXTERNAL_USERS` | NOMINATIONS | bool, 0 | Validates the cycle is open before external users can submit | seed | External shipper can submit after deadline / blocked when they shouldn't be |
| `LOG_LATE_NOM_CHANGES` | NOMINATIONS | bool, 0 | Log before/after snapshot for late-nom rule NN00009015 | seed | Needed evidence for late-nom disputes; turn on to capture snapshots |
| `DISABLE_NOMINATION_SUBMISSION_BY_CONTRACT` | NOMINATIONS | bool, 0 | Disables nom submission by contract | G; also `Quorum.QLNG.Web` `/Quorum.QLNG.Common/ConfigSettings/QLNGGlobalConfigs.cs` | Contract-level submission path missing; one of the 4 keys in the ETC missing-key flood (SF 25-01031118) |
| `NUM_STREAMING_OBJECTS` | NOMINATIONS | int, seed 0 | Number of streaming objects for nom retrieval/streaming | `Quorum.QPTM.Web` `/Quorum.QPTM.ServiceInterface/QPTMNomStreaming.cs` | Missing-key log flood (SF 25-01031118); nom screen retrieval performance |
| `AUTOBALANCE` | NOMINATIONS | int, seed 1 | Auto-balance behavior: 1 = always, 2 = never, 3 = only before Confirm deadline | TG (`QPTMTspOrGlobalConfigs.cs`); `Quorum.QPTM.ClassicGUI` `/Managed/Quorum.QPTM.UserControls/QCntlMaintenance.cs` | Noms (not) auto-balancing after edits |
| `ALLOW_EXTERNAL_USERS_DELETE_NOMS` | NOMINATIONS | bool, 0 | Whether external users may delete nominations | T | Shipper can't delete a nom row |
| `ALLOW_RECALC_HEATING_FACTOR` | NOMINATIONS | bool, 0 | External user may recalc heating factor from toolstrip; TSP-specific, adds EDI processing time | TG; EDI usage per SKILL_EDI_Troubleshooting §16 | Heating-factor menu item missing; EDI processing slower when on |
| `ALLOW_WITHDRAW_TO_ZERO` | NOMINATIONS | bool, 0 | Withdrawal noms may go to zero rather than MinSQ | G | Withdrawal nom blocked at MinSQ |
| `SHOW_PT_TAB` / `SHOW_PNT_TAB` | NOMINATIONS | bool, both default 1 | Show/hide the PT / PNT tab on Nomination Submission | TG | "Tab missing on nom screen" (check before assuming metadata loss; cf. SF 26-01102716 — PT tab only shows MDQ, not extra contract qtys) |
| `SHOW_UP_DN_CONTRACT_PICKLIST_IN_GRID` | TSP | bool, 0 | Show Up/Dn contract picklist on Receipt/Delivery/PT grids | TG | Picklist absent in nom grid; missing-key flood (SF 25-01031118) |
| `ASSIGN_PDA` | NOMINATIONS | bool, 0 | Attach PDA method to noms at submission | TG | PDA methods (not) defaulting onto noms |
| `AUTOGEN_UNIQUE_PKG_ID` | TSP | bool, 0 | Autogen noms get unique Up PKG ID (incl. Svc Req Name, Up K) | T | Autogen noms colliding/merging into one package |
| `RULENN00009521_LOC_ATTR` | NOMINATIONS | string, empty | Location-attribute filter for validation rule NN00009521 | TG | Rule NN00009521 firing at the wrong locations |
| `MAX_CYCLE_ID` | TSP | int, seed null | Max cycle for the TSP used in nomination reports | seed | Nom reports missing late cycles |

## 4. EDI (QPTM)

All seeds from `QARCH_CNFG_CTRL.json` group `EDI` (plus NAESB). Inbound NMST consumers: `Quorum.QPTM.Batch` `/Quorum.QPTM.EDI.DataSets/G873NMST/QEdiNMSTIn18.cs`, `/Quorum.QPTM.QPDLLEDI/QEdiSegregatedProcess.cs`, `/Quorum.QPTM.EDI.Framework/QEdiControlDataQPTM.cs`.

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `SEND_NMST_QUICK_RESPONSE` | EDI | bool, seed 1 | Send NMQR quick response on inbound NMST; if 0, no NMQR is sent but errors still log | `QEdiNMSTIn18.cs`, `QEdiSegregatedProcess.cs` | TP says "we got no response file" / unexpected NMQRs |
| `USE_TT_BUY_SELL` | EDI | bool, seed 0 | Inbound NMST maps Transaction Type "01" to "Buy/Sell" vs "TTBUY/TTSELL" (Issue 111430 comment in code) | `QEdiControlDataQPTM.cs`, `QEdiNMSTIn18.cs` | Title-transfer noms land with the wrong TT/ActnCode |
| `GET_TRADING_PARTY_INFO_FROM_ISA_SEGMENT` | EDI | bool, 0 | Match the TPA from ISA06 instead of the default lookup | G (`QPTMGlobalConfigs.cs`) | Inbound file matched to wrong/no trading partner |
| `EDI_DO_NOT_USE_DUNS_NO` | EDI | bool, seed 0 | When 1, EDI processes don't use DUNS number when creating noms | seed | DUNS-based BA matching failures on inbound noms |
| `LOG_QR_ERRORS_AS_WARNING` | EDI | bool, seed 1 | Log a processing warning if NMQR/CRQR quick responses contain errors | seed | QR errors silently ignored when off |
| `SEND_EDI_NOM_CTRS_ONLY` | EDI | bool, seed 0 | Outbound ALLC/SQTS only send quantities tied to contracts with the EDI attribute | seed | TP receives allocations for contracts they don't expect (or missing ones) |
| `USE_SCHED_QTY_FOR_ALLOC_QTY` | EDI | bool, seed 0 | ALLC dataset sends scheduled qty in place of allocated qty | seed | Allocation EDI quantities don't match screen allocations |
| `RED_RSN_ALWAYS_CPR` | EDI | bool, seed 0 | Force all EDI reduction reasons to CPR | seed | Reduction-reason mismatches on outbound confirmations |
| `USE_INTERCONNECT_LOC_FOR_RQCF` / `_RRFC` / `_SQOP` | EDI | bool, each seed 0 | Those datasets return the Interconnect location ID instead of the location ID | seed | TP complains location IDs in RQCF/RRFC/SQOP aren't the interconnect IDs |
| `PROCESS_BASE_PATH` | EDI | string (env-specific UNC path) | Base folder for EDI file paths used by QPEC and EDIServ | seed (`ENVIRONMENT_SPECIFIC`) | EDI jobs failing after upgrade/refresh — file path not set for the environment (SF 26-01094002/26-01094015) |
| `NAESB30` | NAESB | bool, seed 1 | NAESB 3.0 standard toggle ("will be removed later") | seed; flagged in ETC missing-key case | Missing-key log flood (SF 25-01031118); NAESB-version-dependent dataset behavior |

> The EDI group also contains GPG/encryption plumbing (`ENCRYPTION_EXE_LOCATION`, `PROCESS_TIME_OUT`, `MONITOR_WAIT_TIME`, and a **GPG passphrase key whose value is a secret — never paste it into a case or report**). Most "EDI broke after refresh" cases are env config: SSL/PGP cert updates (SF 26-01087807/26-01087197/26-01084137 "Update PGP Key"), SFTP creds (26-01089631, 26-01084956), new-TP onboarding (26-01089777 BHE GT&S on REX, 26-01086072 Squarepoint) — not key changes.

## 5. Scheduling, Confirmations & CAS/Balancing (QPTM)

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `DEFAULT_TO_OPEN_CONFIRMATION_CYCLE` | CONFIRMATIONS | bool; seed 1 (global accessor default false) | Confirmation screens default to the current open cycle for the gas day | G + TG | "Confirmation screen opens on the wrong cycle" |
| `SHOW_PREV_CYCLE_DATA_ENABLED` | CONFIRMATIONS | bool, 0 | Show previous-cycle data on the confirmation response screen | TG | Operator can't see prior-cycle quantities |
| `AUTO_CONFIRM_SUB_CYCLE_RSNS` | CONFIRMATIONS | CSV of reduction reasons, seed null | Reasons that auto-check "confirm sub cycle" on confirmations | TG | Cuts unexpectedly (not) rolling into subsequent cycles (cf. SF 26-01089630 — "Confirmed Noms not Appearing in CAS for later cycles") |
| `NOM_OVRD_CONF_SUB_CYC_RSNS` | CONFIRMATIONS | CSV, seed `CPR` | Reduction reasons whose confirmed qtys get overridden by nom qtys on resubmission, even if confirmed | seed | "My confirmed cut got wiped out when shipper renominated" |
| `CONF_METHODS_ALLOWED_FOR_EXT` | CONFIRMATIONS | CSV, seed `EDI,EXT` | Confirmation methods external users may use | seed | External confirming party can't confirm on screen |
| `CALC_EPSQ` | CONFIRMATIONS | bool, seed 1 | Calculate Elapsed Prorated Scheduled Quantity | seed | EPSQ blank / intraday cut math disputes (cf. SF 26-01088719 — "EPSQ to 0 when expecting to see an error") |
| `AUTO_CONF_TSP_ONLY` | CONFIRMATIONS | bool, seed 0 | CFAUTOCONF only runs for locations whose DRNs match TSP locations | seed | Auto-confirm running (or not) at interconnects |
| `RUN_CFAUTOCONF_ON_CAS_SUBMIT` | CONFIRMATIONS | bool, seed 0 | Launch CFAUTOCONF whenever CAS Maintenance submit is hit | seed | Confirmations appearing "by themselves" after scheduling |
| `CONF_BIDIRECTIONAL_POS_DIR` | TSP | string `R`/`D`, default R | How confirmation quantities are signed for bidirectional locations | T (`QPTMTspConfigs.cs`) | Bidirectional meter confirmations signed backwards |
| `CONF_UPD_CALL_BALANCING_AFTER` / `CONF_RUN_PATH_BAL_FOR_PNT` | TSP | bool, both default 1 | Run balancing (and PNT path balancing) after the confirmation response update process | TG | Scheduled quantities stale after confirmation cuts |
| `DEADLINE_CATEGORY` / `DEADLINE_TYPE` | CONFIRMATIONS / SCHEDULING / PATHBALANCE | seed `CNF`/`ONT` (conf), `SCH`/`ONT` (sched & pathbal) | Which `PACTRL_CYCLE_DEADLINE` category/type each screen family uses to decide open/closed | seed | Screens lock at the wrong time vs tariff deadlines (cycle table itself: SKILL_Cycle_Deadline_Reference) |
| `SEGMENT_CAPACITY_SOURCE` | SCHEDULING | string, default `I` | Source of segment path capacity in scheduling: I = location path, R/D = loc-group associated quantities | TG; `Quorum.QPTM.Web` `/Quorum.QPTM.ServiceCore.Scheduling/QPTMSchedulingServiceExt_RoutePath.cs`, `Quorum.QPTM.Batch` `/Quorum.QPTM.QPDllScheduling/TransGrpNomHelper.cs` | Segment capacity wrong → over/under-scheduling at segments (cf. SF 26-01088716 — "CAS not scheduling based on IT rates") |
| `ALL_METERS_MAJOR_FLOW` | SCHEDULING | bool, 0 | Treat normal meters like bidirectional when setting POV from major flow direction | TG | POV codes flip on normal meters |
| `CONTRACT_MDQ_SEGMENTATION` | SCHEDULING | bool, 0 | Split contract MDQ using pipe segmentation | T + TG | MDQ checks per segment vs whole-contract disputes |
| `USE_TRAVEL_DIRECTION_FOR_IN_PATH` | SCHEDULING | bool, 0 | Nom only "in path" if same travel direction as the contract path | TG | Backhauls misclassified in/out of path |
| `SEGMENTATION_NOM_CONTAINS_CTR` | SCHEDULING | bool, 0 | Nom must be entirely contained within the contract path for segmentation | TG | Partial-path noms classified unexpectedly |
| `USE_REC_DEL_RANK` | CAS | bool, default 1 | Classify nominations by rec/del rank (true) vs path rank (false) | TG | Scheduling-cut priority disputes |
| `ENABLE_CAS_PATH_BALANCING` / `CAS_DISABLE_BALANCING` | CAS | bool, 1 / bool, 0 | Enable CAS path balancing; master kill-switch for CAS balancing | TG | Path imbalances persisting after CAS runs |
| `ZONE_CLASSIFICATION_ENABLED` | SCHEDULING | bool, 0 | Factor zones into nomination classification | TG | Zone-based scheduling not applying |

## 6. Capacity Release (QPTM)

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `USE_SEASNL_DATES` | TSP | bool, 0 | Seasonal-date columns hidden when false; when false, seasonal start/end forced to release start/end (code fix after SF 24-00990888/24-00991839) | TG; SKILL_Capacity_Release §8 | Seasonal dates wrong on replacement contract; RuleCROF000250 blocking offers (SF 26-01080121) |
| `USE_AUTO_POPULATE_SEASNL_DATES` | CAPACITY_RELEASE | bool, 0 | Auto-populate seasonal date columns for clients who show but don't use them | TG | Blank seasonal columns on offers |
| `VALIDATE_PERM_REL_OFFERS` | CAPACITY_RELEASE | bool, seed 1 | Run FERC Order 712 validations for permanent releases | G | Permanent-release offers failing/passing 712 checks unexpectedly |
| `REQUIRE_APPROVALS` | CAPACITY_RELEASE | bool, 0 | Department-level approvals required to award bids | TG | Award button blocked pending approval |
| `BID_PERIOD_DATES_MUST_BE_BUSINESS_DAY` | CAPACITY_RELEASE | bool, 0 | Bid-period dates must fall on business days | TG | Offer save rejected on weekend dates (bid-window/NAESB timing cases like SF 24-00940053) |
| `CHECK_UMBRELLA_AGREEMENT` | CAPACITY_RELEASE | bool, 0 | Bidder must hold a valid umbrella agreement | G + TG | Bid rejected "no umbrella agreement" |
| `ALLOW_EARLY_PREARRANGED_BIDDING` | CAPACITY_RELEASE | bool, 0 | Permit prearranged bids before the bid window | TG | Prearranged bid blocked before window opens |
| `REQUIRE_MATCH_BID_IN_PERIOD` | CAPACITY_RELEASE | bool, 0 | Match bid only between match-award end and match/response period | TG | Match bids rejected as out-of-window |
| `REPUT_ON_BUSINESS_DAY_ONLY` / `VALIDATE_RECALL_REPUT_SINGLE_DAY` | CAPACITY_RELEASE | bool, 0 / bool, 0 | Reputs restricted to business days; non-timely recalls must be single-day | TG | Recall/reput submissions failing validation (recall cases: SKILL_Capacity_Release §6) |
| `VOLUMETRIC_RERELEASE` | CAPACITY_RELEASE | bool, 0 | Allow volumetric re-release | TG | Re-release option missing on volumetric deals |
| `CR_BID_CREDIT_VALID` / `CR_CREDIT_VLD_PRD` | CAPACITY_RELEASE / TSP | bool 0 / int days | Run bid credit validation; credit validation look-back period | G / T | Bids failing credit validation; credit window disputes |
| `SYNCH_BID_TO_OFFER` | CAPACITY_RELEASE | bool, 0 | On offer submit, synchronize bid values to offer values | TG | Prearranged bid values diverging from offer (**latent bug:** `RUN_NNS_BID_GEN`'s accessor in `QPTMTspOrGlobalConfigs.cs` mistakenly reads `SYNCH_BID_TO_OFFER` — be aware when NNS bid-gen "ignores" its config) |

## 7. Allocations, PDAs & Imbalance (QPTM)

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `ALLOW_EXTERNAL_PDA_UPDATE_FOR_CURRENT_MONTH` | ALLOCATIONS | bool, 0 | External users may submit PDAs for the current production month | TG (`QPTMTspOrGlobalConfigs.cs`) | Shipper can't update PDA mid-month |
| `ALLOC_PDA_CALC_SCHD` / `ALLOC_PDA_CALC_ALLOC_QTY` | ALLOCATIONS | bool, 0 / bool, 0 | Calculate scheduled / allocated qty on PDA Maintenance & Submission screens | G + TG | PDA screen totals blank or "wrong" |
| `USE_PDA_DUR_FOR_SCHED_QTY` | ALLOCATIONS | bool, 0 (+ `MAX_PDA_DUR_FOR_SCHED_QTY` months cap) | Scheduled qty calculated across the PDA's effective-date duration | TG | PDA scheduled qty ignores effective dates |
| `MEAS_RESULTS_BY_POV` | ALLOCATIONS | bool, 0 | Measurement Results signs values by location POV (receipt +, delivery −) | G + TG | Measurement screen signs flipped |
| `CHECK_PREVIOUS_TIER_ALLOC_VS_OVERRIDE` | ALLOCATIONS | bool, 0 | Net alloc qty must equal total energy from previous tier | G | Tiered allocation override validation errors |
| `IMBALANCE_TRADING_WINDOW_OPEN` / `DAILY_IMBALANCE_TRADING_WINDOW_OPEN` | TSP | flag, 0 | State of the monthly / daily imbalance trading window | TG | "Imbalance trading window closed" complaints — toggled on a schedule by ops |
| `POST_PRODUCTION_PDA_WINDOW_OPEN` | TSP | flag, 0 | Open the PDA window for post-production PDAs by external users | TG | Post-production PDA submissions blocked |
| `ALLOW_MANUAL_POST` | INVENTORY | bool, 0 | Imbalance accounts may set a posted imbalance quantity manually | TG | Manual posting field read-only |
| `AUTH_TO_POST_IMB_START_DT` / `AUTH_TO_POST_IMB_END_DT` | TSP | int business-day, defaults 3 / 5 | Business-day window for authorization-to-post imbalance | TG | Auth-to-post opens/closes on the wrong day |
| `FUTURE_TRANSFER_MONTHS_ALLOWED` / `FORCE_TRANSFER_PERIOD_DAILY` | TSP | short 0 / bool 0 | Months allowed for future imbalance transfers; force transfer period daily | TG | Imbalance transfer rejected for a future month |
| `TIPS_PROCESS_CONTROLS_PRM` | (TSP config) | per-TSP value in `QARCH_TSP_CONFIG` | Gates QPTM↔TIPS integrated approval/sync checks (client-specific) | `ENT.QPTM.Batch` `/ENT.QPTM.QPDllInterfaces/Close Approval/QCloseApproval.cs`, `/Alloc Approval Check/QPermAllocApprovalCheck.cs`, `/Billing Imbalance Approval Check/QPermBLImbalanceApproval.cs` | Close/approval checks failing in integrated QPTM-TIPS clients |

## 8. Billing (QPTM)

Seeds from `QARCH_CNFG_CTRL.json` group `BILLING`; billing batch lives in `Quorum.QPTM.ClassicBatch` `/QPDllPipelineMgrBL/` (verify exact consumer per process).

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `DETAIL_ROUNDING` | BILLING | `NON`/`PRG`/`SDO`, seed `PRG` | Invoice-generation detail rounding: None, Progressive, or Subdetail Offset | `Quorum.QPTM.ClassicBatch` `/QPDllPipelineMgrBL/QPSGenerateHeadersDetails.cpp` | Invoice detail rounding/penny differences |
| `TIEBREAK_TOC` | BILLING | TOC code, seed null | TOC used to break ties in the Greater-of-Overrun process step | TG (`QPTMTspOrGlobalConfigs.cs`) + seed | Overrun billed to the "wrong" TOC when two tie |
| `INVOICE_CONTACT_TYPE` | BILLING | contact type, seed `INV` | Contact type used in invoice generation | seed | Invoices going to the wrong contact |
| `PAL_TOS` | BILLING | TOS code, seed `INTBALNC` | TOS used to calculate PAL extension fees | seed | PAL extension fees missing/miscalculated |
| `QUANTITY_GATHERING_VERSION` | BILLING | `OLD`/`NEW`/`BOTH`, seed `NEW` | Which quantity-gathering implementation invoice gen uses | seed | Invoice quantities differ after upgrade |
| `INV_GEN_SPLIT1_*` / `INV_GEN_SPLIT2_*` / `INV_GEN_PPA_*` family | BILLING | int throttles (e.g. SPLIT1_MAX_REC_CNT 200) | Record-count/weight splits for invoice generation across QPEC workers | seed | BLGEN long-running/timeout; tuning knobs, not correctness |
| `JDE_EXPORT_FILE_PATH` / `JDE_EXPORT_FILE_NAME` | BILLING | env-specific path/name | Where the JD Edwards journal export lands | seed (`ENVIRONMENT_SPECIFIC`) | JE export failing after env refresh — path points at the old server |
| `ACCTG_MTH_LAG_TIME` | TSP / CONFIRMATIONS | int months, 0 | Lag between current accounting month and production month | T + TG | Accounting-month defaults wrong on screens (open/expired month issues: SKILL_Pipeline_Admin_Config §9) |
| `NNS_STORAGE_COMPONENT` | TSP (also BILLING `NNS STORAGE COMPONENT`, seed 0.3079) | decimal rate / rate ID, default −1 | Rate (ID) used by supplemental process for NNS storage price | TG + seed | NNS supplemental/CR supp calc pricing wrong |

> Frequent billing-config-but-not-a-key cases: rate-sequence mismatch blocking rate resolution / reservation rate not billing (SF 26-01102601, 26-01090579 "BLINVGEN rate-resolution errors"), and default-bill-record errors in BLJRNALL (26-01090580). These are rate/sequence *data* fixes, not `QARCH_CNFG_CTRL` keys — see SKILL_Billing.md.

## 9. TIPS — Plant Allocation (TurboTips ALLOCATE)

Defaults verified in `Quorum.Tips.TurboTips` `/Quorum.Tips.TurboTips.Allocate/ALLOCATE/psALLOCATE_ConfigSettingsUsed.cs`; scope (global/plant/company) from `Quorum.TIPS.Batch` `/Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/ALLOCATE.cs` `BuildConfigSettings`.

| Key | Group (scope) | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `ACCOUNTING_PERIOD_MODE` | BATCH (global; keyable to plant) | string, default `GBL` | Global vs Plant (`PLT`) accounting-period mode | `ALLOCATE.cs`, `psALLOCATE.cs`, `Quorum.TIPS.Web` `/Quorum.TIPS.Web.Controllers/UIControllers/QUIControllerCurrentAcctDt.cs` | Plants forced to share one open accounting period (SF 26-01096195 — key added at PLT level in client layer QHEC) |
| `ADJUST_WHAV_DERIVED_VOLUMES` | BATCH (global) | bool, false | Adjust wellhead-average derived volumes using **progressive rounding** | `psALLOCATE_ConfigSettingsUsed.cs` | Allocated WHAV slightly off vs physical WHDV; large negative fuel allocations (SF 26-01068082 "Updated the allocation rounding check in the global config settings…", 26-01104466) |
| `PROGESSIVE_ROUNDER_NO_BOUND_CHECK` | ALLOCATE (global) | bool, false | Progressive rounder without bound checks (note in-code spelling "PROGESSIVE") | same | Rounding bound-check rejections on edge volumes |
| `USE_DOUBLE_PROGRESSIVE_ROUNDER` | (global) | bool, false | Double-precision progressive rounder instead of decimal | `psALLOCATE_ConfigSettingsUsed.cs` | Tiny last-decimal allocation differences vs legacy |
| `GAS_VOL_PRECISION` / `HEAT_VAL_PRECISION` / `LIQ_VOL_PRECISION` / `OTHER_QTY_PRECISION` | BATCH (**plant**) | int factor, default 100 (= 2 decimals) | Rounding precision per quantity family, overridable per plant | `ALLOCATE.cs` / SETTLEMAIN (`GetPlantConfigKeyIntVal`) | Volumes/heat rounding to wrong decimals at one plant only |
| `GATH_ROUNDING_FACTOR` | ALLOCATE (global) | int, default 1 (integers) | Overrides the precision keys for gathering/nomination-rank allocation methods | same | Gathering allocation showing integer-only volumes |
| `DONT_ALLOC_RULE_RETURN_NEGATIVE` | BATCH (global) | bool, false | Forbid allocation rules from returning negative volumes | same | Negative allocated volumes appearing/being blocked (negative-liquids workaround: SF 26-01086773 — zero-out via allocation group) |
| `INCLUDE_ALLOCATION_NEGATIVE_BASIS` | BATCH (**plant**) | bool, false | Include negative basis values in merit allocation | same | Merit allocation excluding negative-basis meters |
| `SPLIT_BY_PROD` | BATCH (global) | bool, false | Split allocations by product using 20 product split-decimal columns on `QCTRL_PLANT_CTR_PROD` (ContractSplitAllocationMethod) | same | Product-level contract splits not applying |
| `SPLIT_BY_CTRCTGRY` | BATCH (global) | bool, false | Split allocations by contract category | same | Category split ignored |
| `COMP_SPLIT_IND` | BATCH (global) | bool, false | Split at component level (true) vs product level (false) | same | Component-level statements not splitting |
| `THEO_VS_ACTUAL_CAPACITY` | BATCH (global) | bool, false | Theoretical vs actual capacity calculations | same | Capacity-based allocation disputes |
| `AVERAGE_THEORETICALS` | ALLOCATE (global) | bool, **true** | Average theoretical values in allocations | same | Theoretical averaging differences vs expectations |
| `LIMIT_MOD_GAS_FAC` (+ `LOWER_MOD_GAS_FAC` 0.9579 / `UPPER_MOD_GAS_FAC` 0.999999) | ALLOCATE (global) | bool, false; decimal bounds | Clamp the modified gas factor in WAGA calc between the bounds | `psALLOCATE_ConfigSettingsUsed.cs` (DerivedMeterAllocationMethod.CalculateWAGA) | Gas factors clamped/not clamped — shrink results off |
| `SUPPRESS_ZERO_VOLUME_DER_MTR` | BATCH (global) | bool, false | Suppress zero volumes for derived meters | same | Zero-volume derived-meter rows cluttering results |
| `DECOUPLED_MONTHLY_SCHEDULING` | BATCH (**company**) | bool, false | Decouple monthly scheduling at company level | `ALLOCATE.cs` (`GetCompanyConfigKeyBoolVal`) | Monthly scheduling coupling behavior per company |
| `ENABLE_BALANCING` | CRUDE (global) | bool, false | Enable crude gathering balancing | same | Crude balancing not running |
| `USE_PRE_401_BUILD46_PRECISION` | ALLOCATE (global) | bool, false | Legacy (pre-TIPS 4.01 b46) rounding precision (1e8) for back-compat | same | Post-upgrade allocation diffs vs historical results |
| `COMMIT_ALLOC_INTERVAL` | ALLOCATE (global) | int, 0 = no intermediate commits | DB commit interval for allocation records | same | ALLOCATE long-running/locking on huge plants |

## 10. TIPS — Settlement (TurboTips SETTLEMAIN)

All keys + scope + defaults verified in `Quorum.Tips.TurboTips` `/Quorum.Tips.TurboTips.Settle/SETTLEMAIN/psSETTLEMAIN_ConfigSettingsUsed.cs` (XML doc-comments state Level + Key Group per key); consumed via `Quorum.TIPS.Batch` `/Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/SETTLEMAIN.cs`. **Where the doc-comment "Default" and the C# initializer disagree, the initializer wins — noted below.**

| Key | Group (scope) | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `DEDUCT_FEE_BEFORE_POP` | SETTLE (global) | bool, false | Deduct fees before POP (percentage-of-proceeds) calculation | `psSETTLEMAIN_ConfigSettingsUsed.cs`, `SETTLEMAIN.cs` | POP statement values off because fees applied in wrong order (cf. SF 26-01069474 POP ethane recovery) |
| `ALT_POP_STMT_CD` | SETTLE (global) | bool, false | Use alternate POP statement code | same | POP statement using wrong/old statement code |
| `ALLOW_MULT_FEES_FOR_SAME_TYPE_GRP` | SETTLE (global) | bool, false | Allow multiple fees with the same FEE_TYPE_CD in ProcessFees | same | Second fee of same type silently dropped |
| `EXLR_ADJUSTMENT_IND` | SETTLE (global) | bool, false | Enable EXLR adjustment indicator | same | EXLR adjustment not applied on settlement |
| `BILLING_IND_ROLLUP` | SETTLE (**plant**) | bool, false | Controls whether daily records get `BILLING_IND=false` on rollup | same | Daily records (not) flagged billable as expected |
| `MARGIN_DECOUPLE_TIK_CALC` | SETTLE (global) | bool, false | Decouple TIK margin calculation from the main margin | same | TIK margin moving with main margin when it shouldn't |
| `DEDUCT_RES_RETURNED` | SETTLE (**plant**) | bool, false | Deduct residue returned from settlement | same | Returned residue not deducted in statement |
| `MTR_ORDER_BY_CLAUSE_IN_SEL_PAYSTATION` | SETTLE (**plant**) | bool, default **true** | Order meters by `MTR_NO` in paystation select (read in Initialize) | same | Paystation meter ordering differs at one plant |
| `ALLOW_ZERO_VOL_PCT_ADJUSTMENT` | SETTLE (global) | bool, false | Allow zero-volume percentage adjustment in SettleEngine | `QSettleMain::InitializeVariables` | Zero-volume rows (not) getting pct adjustment |
| `ENABLE_SET_OPTION_APPLIED_CD` | SETTLE (global) | bool — comment says false, **initializer true** | Write `SET_OPTION_APPLIED_CD` on settle summary | same | Settle option code missing/present unexpectedly |
| `WRITE_ALL_RATE_RES_TIER_DETAIL` | SETTLE (global) | bool — comment false, **initializer true** | Write all rate-resolution tier detail records | same | Tier detail rows missing/extra in rate resolution |
| `DAILY_ROLLUP_SIMPLE_AVG` | SETTLE (**plant**) | bool, false | Use simple average for daily prod rollup when no volumes exist | same | Daily rollup average differs at one plant |
| `ROUND_FIXED_FUELS` | BATCH (global) | bool, false | Round fixed-fuel calculations | `psSETTLEMAIN…`; also `StepExecution/FIXEDFUELS.cs` | Fixed-fuel penny/rounding differences |
| `CCT_STANDARIZATION_TYPE` | BATCH (global) | string, default `HEAT_VALUE` (or PRESSURE) | CCT standardization basis | same | CCT standardized on wrong basis (heat value vs pressure) |
| `CCT_PRES_STANDARDIZATION_BASED_ON_STANDARDIZE_IND` | SETTLE (global) | bool, false | Pressure standardization driven by the standardize indicator | same | Pressure standardization (not) applied per-meter |
| `CCT_TIK_WH_PRODUCT_ONLY` | BATCH (global) | bool, false | Check only WH product for TIK (false = WH + RES) | same | TIK checks the wrong product set |
| `H2O_Content_LIQ_CONVRSN_2` | BATCH (global) | bool, false | Enable H2O-content liquid conversion v2 | same | Water-content liquid conversion using old method |
| `DO_NOT_INCLUDE_VOLUME_TAX_IN_REIMB` | BATCH (global) | bool, false (read in Initialize) | Exclude volume tax from reimbursement | same | Volume tax wrongly in/out of reimbursement |
| `INCLUDE_TOT_TAX_REIMB_VAL_IN_TOT_NET_VAL_PR` | PLANT (**plant**) | bool, false | Add `TOT_TAX_REIMB_VALUE` to `TOT_NET_VALUE_PR` | same | Net producer value off by the tax-reimb amount |
| `USE_DEAL_DED_LOC_FUNC` | BATCH (global) | bool, false (read in Initialize) | Use the deal-deduction-location function | same | Deal deductions hitting the wrong location |
| `RES_BTU_DISP` | BATCH (**plant**) | string, default `NA` | Residue BTU display mode | same | Residue BTU display differs at one plant |
| `DEDUCT_BYPASSKW` | BATCH (**plant**) | bool, default **true** | Deduct bypass KW from settlement | same | Bypass KW not deducted when expected |
| `ROUND SETTLE PROD VOL` / `ROUND SETTLE PROD PRICE` / `ROUND SETTLE FEE VOL` | BATCH (**plant**) | bool, false (note: keys contain spaces) | Round settlement product volumes / prices / fee volumes | same | Settlement rounding differences at one plant |
| `CTR_TYPE_CDS_TO_EXCLUDE` | BATCH (**plant**) | CSV, empty (no exclusions) | Contract types excluded from settlement | same | A contract type settling that should be excluded (or vice-versa) |
| `PRODUCER_PRICE_PRECISION` | BATCH (**plant**) | int factor, default 10,000,000 (7 dp) | Producer price rounding precision | same | Producer price rounded to wrong decimals |
| `PSIG_SIMPLE_AVERAGE_EXCLUDE_ZERO_QTY` | BATCH (**plant**) | bool, false | Exclude zero-qty records from PSIG simple average | same | PSIG average skewed by zero-qty rows |
| `USE_POST_VOL_PPA_SMV` | BATCH (global) | bool, false | Use posted volume for PPA specific-meter-volume lookup | same | PPA SMV using nominated instead of posted volume |
| `ENABLE_NOM_TOT_QTY_LOOKUP` | NOMINATIONS (**plant**) | bool, false | Enable nomination total-quantity lookup | `psSETTLEMAIN…`; `Quorum.Tips.TurboTips.Common/Utilities/VolumeResolver.cs` | Nom total qty not picked up in settlement |
| `DEFINE_INFINITY_ZERO` | QFCFormula (global) | bool — comment false, **initializer true** | Formula engine: treat infinity as zero | same | Formula div-by-zero producing error vs zero |
| `DEFINE_FASTCALC_EXCEPTION_VALUE` | QFCFormula (global) | decimal (initializer `decimal.MaxValue`) | Formula exception sentinel value | same | Formula exceptions surfacing as a huge number |
| `PERFORM_ALT_HV_CONV_CCT_BASIS` | BATCH (global) | bool, false | Alternate heat-value conversion on CCT basis | same | Heat-value conversion differs from expected |
| `PERFORM_INTERMEDIATE_ROUNDING_FOR_CTRSHK` / `POPULATE_LIQ_VOL_FOR_CTRSHK` | BATCH (global) | bool false / bool true | Intermediate rounding for CTRSHK UOM rule; populate liquid volumes for CTRSHK | same | CTRSHK UOM rounding / liquid-volume population issues |
| `USE_START_DT_FOR_YY_PERIOD_CALC` | ESCALATION (global) | bool, default true | Use start date for YY (current-year-on-prior-year) period calc | same | Escalation period boundaries off by a period |
| `DELIVERY_FUEL_GROSS_UP` | COMPANY (**company**) | bool, default true | Gross-up adjustment on delivery-direction fixed-fuel terms | `Quorum.Tips.TurboTips.SettleEngine/ContractTerms/ContractTermVolume.cs`; `GetCompanyConfigKeyBoolVal` | Delivery fuel not grossed up per company policy |
| `PENALTY_OVERRIDE_LOOKUP_YEARS` / `PROD_DT_MTHS_BACK_LIMIT` | BATCH (global) | int, 1 / 12 | Penalty-override lookback (years); production-date months-back limit | `psSETTLEMAIN…` | Penalty override / back-month data not found |

## 11. Security, UI & Platform (QPTM / QFC)

| Key | Group | Values & default | Business logic | Where read | Typical case symptom |
|---|---|---|---|---|---|
| `DISABLE_TSP_SECURITY` | SECURITY | bool, seed 0 | Disable TSP-level security scoping | seed `QARCH_CNFG_CTRL.json` | Users seeing (or losing) TSPs they shouldn't |
| `ENABLE_INACTIVE_USER_CHECK` | SECURITY | bool, seed 1 | Security check rejecting inactive users (.NET only) | seed | Inactive user still logging in / valid user blocked |
| `AUTOADDUSER_FIRSTLOGIN` | SECURITY | bool, seed 0 | Auto-create the user on first login (no privileges without a default group) | seed; `Quorum.QFC.CPP.GUI` `/QFC/QAppManager.cpp` | "User Unauthorized" for new SSO users (SF 26-01102044 "Security user updated", 26-01089784 Okta auto-provisioning) |
| `ENABLE AUD SECURITY` / `ENABLE GROUP MENU SECURITY` | SECURITY | bool, seed 1 / 1 | Separate Add/Update/Delete security on bulk-update screens / grids | seed | Buttons greyed out per-action for some groups (cf. SF 26-01088304 Contract Maintenance Security, 26-01086739 BA Contact screen) |
| `ENABLE_REPORTS_SECURITY` | SECURITY | bool, seed 1 | Enforce security on reports | seed | Users can't run reports they previously could (SF 26-01089048 operator can't pull RPT_ALRX04, 26-01087697 grant report scheduling) |
| `USE_REGIONS_FOR_SCOPED_SECURITY` | SECURITY | bool, seed 0 | Module-scoped security hierarchy via regions | seed | Region-scoped data visibility issues |
| `VALIDATE_BROWSER` | (QFC web) | bool; set false to disable | Browser allowlist for myQuorum Web / IPWS | `Quorum.QFC.Web` `/Quorum.QFC.Web.Core/Filters/ValidateBrowserAttribute.cs` | "Unsupported browser" block on IPWS (SF 25-01018386); see SKILL_UI_Widgets §10 |
| `DEFAULT_GRID_PAGE_SIZE` | WEB_GRID | int, 100 | Rows per page for all web grids without a CSHTML override | G (`QPTMGlobalConfigs.cs`) | "Grid only shows N rows" |
| `STALE_CONFIG_CACHE_TIME` | PIPELINE | int minutes, 0 = immediate | Minutes before cached config is considered stale and refreshed | G | Config change "didn't take effect" until recycle |
| `SHOW_LINKS_FOR_EXT_USERS` | PIPELINE | bool, 0 | Show links to external users | G | External users missing navigation links (hamburger/IPWS link cases like SF 26-01097781) |
| `SEPARATE_TRANS_REPORT_TOCS` | CAW | bool, seed 0 | Separate TOC surcharges in CAW transactional reports (CWFIRMTRAN, CWINTRTRAN, CWCAPRTRAN) | `Quorum.QPTM.ClassicBatch` `/QPDllPipelineMgrCW/QPSFirmTranspRpt.cpp`, `QPSIntrTransRpt.cpp`, `QPSCapRelTransRpt.cpp` | IPWS rates not displaying / can't add code-table values (SF 25-01015916 — verbatim: "set to true") |
| `INFORMATIONAL_POSTING_SITE_GLOBAL` | INVENTORY | URL, empty | URL to the pipeline's IPWS | G + TG | IPWS links broken from app screens |

> TIPS security/SSO and access cases (SF 26-01091774 SSO stopped working, 26-01094597 read-only group update error, 26-01083650/25-01057283 grant external/UAT access, 26-01086102/26-01084754 group review) are resolved on **security groups / personas / SSO/Okta config**, not `QARCH_CNFG_CTRL` keys — see SKILL_Security_UserAdmin.md.

---

## 12. Config that is NOT a `QARCH_CNFG_CTRL` key (so you don't chase a phantom key)

These dominate the "Application Configuration / ChangeConfig" case volume but are **not** config keys. Recognise them and route accordingly (detail in `SKILL_Pipeline_Admin_Config.md`):

| Looks like a config issue, actually is… | Tell-tale | Fix path | Example case |
|---|---|---|---|
| **Env file paths / FTP / SFTP creds / service pwds / SSL/PGP certs** (`ENVIRONMENT_SPECIFIC_IND` keys + non-key infra) | Job/transfer fails right after an upgrade/refresh | Cloud Ops env-specific config script / cert/cred update | 26-01089498 (PALOCEXP), 26-01089624 (CWNIGHTLY), 26-01084956 (SFTP), 26-01084137 (PGP), 26-01103060 (SFTP creds) |
| **Missing screen/tab/menu/process/report after a build** | Worked before the hotfix | Metadata check-in / sysgen in CLIENT layer | 26-01102793 (Credit Rating tab → "Added metadata check-ins … into QNJR"), 26-01105732 ("Missing grid control definitions … added to the client-client layer") |
| **Dropdown won't retain / empty** | Has values but won't stick, or is blank | Code Table Definition Maintenance: Displayed Column Order / add definition | 24-00984137, 24-00967113 |
| **Location absent from nom picklist / "appearing where it shouldn't"** | Meter attribute issue | `PACTRL_LOC_ATTR` (Nominatable/Interruptible) — script or screen | 26-01097568, 26-01102037 ("Meters … inactive or not nominatable") |
| **"Cannot delete" a loc-group / zone / child meter** | UI blocks deletes by design | Cloud Ops delete script | 26-01064296, 26-01104931 |
| **Rate not resolving / wrong sequence** | Reservation rate not billing, BLINVGEN rate errors | Update rate sequences / remove TOS on rate | 26-01102601, 26-01101441, 26-01090579 |
| **Notification / email not sending** | RCA emails missing | Notification config / mail relay (Cloud Ops) | 26-01066701, 26-01066599, 26-01089517 |

---

## 13. How to investigate a suspected config issue (runbook)

```
1. PIN THE KEY. From the symptom, find the candidate key in the tables above.
   - QPTM screen behavior: search the three QPTM config classes in Quorum.QPTM.Web
     /Quorum.QPTM.Common/ConfigSettings/*.cs — the [QPTMConfigSettingAttribute]
     string gives group, key, description and CODE default.
   - TIPS batch behavior: open the matching ps<PROCESS>_ConfigSettingsUsed.cs in
     Quorum.Tips.TurboTips (ALLOCATE, SETTLEMAIN, DAYVOLS, CTRREV, FIXEDFUELS, …) —
     each property's XML comment states Level (Global/Plant/Company), Key Group,
     Key Name and default. (Trust the C# initializer over the prose default.)
   - Or grep the seed: <CLIENT>.QPTM.Metadata /STANDARD 16.0/QARCH_CNFG_CTRL.json.

   BEFORE going further, rule out the §12 non-key lookalikes — most "config" cases
   are env file paths, metadata check-ins, code tables, location attributes, rate
   sequences, security groups, or notification config, NOT a QARCH_CNFG_CTRL key.

2. CHECK WHAT THE CLIENT ACTUALLY HAS (env-appropriate DB).
   SELECT KEY_GRP_NM, KEY_NM, KEY_VALUE, TSP_NO
   FROM   QARCH_CNFG_CTRL              -- physical name may be qarch_cnfg_ctrl
   WHERE  KEY_NM = '<KEY>';
   -- No row  => middletier uses the CODE default (non-fatal; logs
   --            QConfigMgrBase.GetConfigKey.Missing — SF 25-01031118).
   -- Row     => compare against the standard seed AND the code default.
   For TSP-or-global keys, check both the TSP-scoped row and the global row:
   the TSP row wins (QPTMTspOrGlobalConfigs.cs resolution).
   For TIPS, remember the THREE scopes — global, company, plant
   (ALLOCATE.cs / SETTLEMAIN.cs BuildConfigSettings:
    GetGlobalConfigSetting / GetCompanyConfigKeyBoolVal / GetPlantConfigKeyBoolVal).

3. CONFIRM THE CONSUMER. ADO code search the key name ({"searchText":"<KEY>"})
   to find which service/batch reads it, and read the call site to confirm the
   value's effect — do not trust KEY_DESCR alone (several descriptions are stale
   or copy-pasted, e.g. VALIDATE_CTR_TOS_FACILITY; and some TIPS doc-comment
   defaults disagree with the initializer — see §10).

4. CHANGE SAFELY.
   - Confirm environment (UAT first unless P1), TSP_NO/plant/company, and whether
     the key is TSP-scoped, global, plant/company, user-overridable
     (ALLOW_USER_OVERRIDE_IND) or environment-specific (ENVIRONMENT_SPECIFIC_IND).
   - Make the change via the Global Config screen, or hand Cloud Ops an
     insert/update against QARCH_CNFG_CTRL (and the client metadata layer
     <CLIENT>.QPTM.Metadata / TIPS client layer if it must survive redeployment —
     SF 26-01096195 added ACCOUNTING_PERIOD_MODE in the QHEC client layer).
   - If the screen errors "cannot be modified" in a managed env, it must go through
     Cloud Ops (SF 26-01089759).
   - Refresh the config cache / recycle the service (STALE_CONFIG_CACHE_TIME=0 =
     immediate; otherwise wait or recycle), then retest.

5. CLOSE THE LOOP. Record key, old value -> new value, scope (TSP/global/plant/
   company), environment, and the SF case # in the resolution. If the standard
   seed default looks wrong for the whole client base, raise a product ticket
   instead of patching every client layer.
```

---

*Sources (all verified 2026-06-13 via ADO code search / file fetch unless noted): Quorum.QPTM.Web `/Quorum.QPTM.Common/ConfigSettings/QPTMGlobalConfigs.cs`, `QPTMTspConfigs.cs`, `QPTMTspOrGlobalConfigs.cs` (+ `ConfigSettingsAccess/QPTMTspOrGlobalConfigsAccess.cs`); `<CLIENT>.QPTM.Metadata` `/STANDARD 16.0/QARCH_CNFG_CTRL.json`; Quorum.QFC.Core `/Quorum.QFC.Core/ConfigSettings/QConfigMgrBase.cs` (GetConfigKey signature verified); Quorum.QPTM.Batch EDI files; Quorum.QPTM.ClassicBatch CAW/billing (`QPSGenerateHeadersDetails.cpp`, CAW report cpp); Quorum.Tips.TurboTips `/…/ALLOCATE/psALLOCATE_ConfigSettingsUsed.cs` and `/…/SETTLEMAIN/psSETTLEMAIN_ConfigSettingsUsed.cs`; Quorum.TIPS.Batch `/Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/ALLOCATE.cs` + `SETTLEMAIN.cs` + `Data/QTurboTipsData.cs`. SF grounding: closed cases Root Cause = Application Configuration OR ChangeConfig, both products (sampled 2026-06-13). Behaviors not traced to a call site are marked "(behavior inferred, verify in code)". No credentials or secret key VALUES are reproduced in this document.*
