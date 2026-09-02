# Quick Feature Reference - QPTM Web

**Purpose**: Map keywords from WI tickets to feature documentation. Use this to identify which docs to load.

---

## Feature Map

| Code | Feature | Keywords | Docs Path | Status | Related Batch Processes |
|------|---------|----------|-----------|--------|------------------------|
| CAS | Capacity Scheduling Allocations | CAS, scheduling, allocations, scheduled capacity, transaction groups, nomination classification, reduction, OAC, rule sets, MDQ | [capacity-scheduling-allocations/](capacity-scheduling-allocations/) | Documented | NNCLASSFY, SCREDUCE, SCOAC |
| NOM | Nominations | nomination, submit, validate, cycle, gas day, activity, receipt, delivery, shipper, intraday | [nominations/](nominations/) | Documented | NNSUBMIT, NNVALIDATE |
| ALLOC | Allocations | allocation, PDA, priority, measurement, aggregate location, penalty schedule | [allocations/](allocations/) | Documented | ALALLOCATE |
| CR | Capacity Release | capacity release, bidding, offers, awards, CR, seasonal, prearranged | [capacity-release/](capacity-release/) | Documented | CRPROCESS, CRMDQMSQVL, CROFFRTIML, CRBIDGEN |
| CONF | Confirmations | confirmation, confirmed quantity, variance, TSP, reconciliation | [confirmations/](confirmations/) | Documented | CFPROCESS |
| CTR | Contracts | contract, TOS, service requester, MDQ, terms of service, attributes, amendment | [contracts/](contracts/) | Documented | - |
| RATE | Rate Management | rate, tariff, pricing, TOC, type of charge, tier, seasonal profile, fuel | [rate-management/](rate-management/) | Documented | - |
| INV | Inventory | inventory, balance, account, storage, PAL, injection, withdrawal, imbalance, trading | [inventory/](inventory/) | Documented | INACCTACCM, INTRDPEND, INCONFTRADE |
| EDI | EDI Integration | EDI, 810, 867, NAESB, transmission, TSQ, electronic, trading partner | [edi-integration/](edi-integration/) | Documented | EDIPROCESS |
| RFS | Request For Service | RFS, request for service, capacity request, RFS-to-contract, award | [rfs/](rfs/) | Documented | - |
| LOC | Location Management | location, operator ID, confirm party, contact, location group, path, aggregate | [location-management/](location-management/) | Documented | - |
| INVC | Invoice Management | invoice, billing group, invoice message, sub-detail, charge basis, posting | [invoice-management/](invoice-management/) | Documented | - |
| PEN | Penalties | penalty, submission, hourly penalty, penalty results, tolerance | [penalties/](penalties/) | Documented | - |
| MEAS | Measurement | measurement, hourly, daily, gas analysis, close schedule, SCADA | [measurement/](measurement/) | Documented | - |

---

## Keyword-to-Feature Lookup

| Keyword | Primary Feature (Code) | Secondary Feature |
|---------|------------------------|-------------------|
| CAS | CAS | - |
| scheduled capacity | CAS | - |
| transaction group | CAS | - |
| classification | CAS | NOM |
| reduction | CAS | - |
| OAC | CAS | - |
| MDQ | CAS | CTR |
| nomination | NOM | CAS |
| gas day | NOM | - |
| cycle (timely/evening/intraday) | NOM | - |
| confirmation | CONF | - |
| variance | CONF | - |
| allocation | ALLOC | - |
| PDA | ALLOC | - |
| capacity release | CR | - |
| bid / offer / award | CR | - |
| contract | CTR | - |
| TOS / terms of service | CTR | RATE |
| rate / tariff | RATE | - |
| TOC / type of charge | RATE | - |
| inventory | INV | - |
| PAL / storage balance | INV | - |
| imbalance | INV | ALLOC |
| EDI / NAESB | EDI | - |
| RFS | RFS | CTR |
| location | LOC | - |
| invoice / billing | INVC | - |
| penalty | PEN | - |
| measurement | MEAS | ALLOC |

---

## Web Controllers

| Controller | Feature (Code) |
|------------|----------------|
| CASummaryMaintenanceController | CAS |
| NominationMaintenanceController | NOM |
| ConfirmationResponseController | CONF |
| ConfirmationSummaryController | CONF |
| DailyAllocatedQuantityMaintenanceController | ALLOC |
| MonthlyAllocatedQuantityMaintenanceController | ALLOC |
| BidWizardV2Controller | CR |
| OfferWizardV2Controller | CR |
| CRAwardController | CR |
| ContractMaintenanceController | CTR |
| RateMaintenanceController | RATE |
| InventoryAccountsController | INV |
| InventoryAdjustmentsController | INV |
| EDTransactionController | EDI |
| RFSWizardV2Controller | RFS |
| LocationMaintenanceController | LOC |
| InvoiceMaintenanceController | INVC |
| PenaltySubmissionController | PEN |
| PenaltyResultsController | PEN |
| MeasurementEntryController | MEAS |
| MeasurementResultsController | MEAS |

---

## Database Table Prefixes

| Prefix | Feature (Code) |
|--------|----------------|
| SCTRL_CA_*, CASTAG_* | CAS |
| PACTRL_TRANS_GRP, PACTRL_RULE_SET | CAS |
| NNCTRL_NOM_* | NOM |
| CFCTRL_CONF_* | CONF |
| ALCTRL_ALLOC_*, ALTRAN_* | ALLOC |
| CRTRAN_* | CR |
| KCTRL_CTR_* | CTR |
| RTCTRL_TOC | RATE |
| INCTRL_ACCT_*, INTRAN_* | INV |
| BLTRAN_INVOICE_* | INVC |
| PACTRL_LOC*, PACTRL_FACILITY | LOC |

---

## Related Documentation

- [README.md](README.md) - Navigation guide
- [WORK_ITEM_INVESTIGATION.md](WORK_ITEM_INVESTIGATION.md) - WI investigation workflow
- Feature docs: `{feature}/domain.md`, `{feature}/architecture.md`, `{feature}/troubleshooting.md`

---

*Last updated: 2026-03-03*
