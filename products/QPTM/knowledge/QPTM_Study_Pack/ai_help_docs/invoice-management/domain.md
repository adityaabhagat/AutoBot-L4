---
title: "Invoice Management (INVC) - Domain Knowledge"
category: "domain"
feature: "INVC"
related_repos:
  - "Quorum.QPTM.Web"
  - "Quorum.QPTM.Batch"
keywords:
  - invoice
  - billing
  - invoice maintenance
  - invoice header
  - invoice detail
  - invoice sub-detail
  - invoice group
  - invoice status
  - billing period
  - accounting month
  - charge basis
  - type of charge
  - TOC
  - TOS
  - PPA
  - prior period adjustment
  - posting
  - finalize
  - BLROLLPER
  - invoice report
last_updated: 2026-03-03
---

# Invoice Management (INVC) - Domain Knowledge

## Table of Contents

- [Overview](#overview)
- [Invoice Lifecycle](#invoice-lifecycle)
- [Invoice Status Codes](#invoice-status-codes)
- [Invoice Data Hierarchy](#invoice-data-hierarchy)
- [Billing Groups](#billing-groups)
- [Invoice Messages and Sub-Details](#invoice-messages-and-sub-details)
- [Charge Basis Types](#charge-basis-types)
- [Type of Charge (TOC)](#type-of-charge-toc)
- [Type of Service (TOS)](#type-of-service-tos)
- [Prior Period Adjustments (PPA)](#prior-period-adjustments-ppa)
- [Accounting Month and Billing Periods](#accounting-month-and-billing-periods)
- [Internal vs External Users](#internal-vs-external-users)
- [Invoice Posting and Batch Processing](#invoice-posting-and-batch-processing)
- [Key Business Rules](#key-business-rules)
- [Glossary](#glossary)
- [Related Documentation](#related-documentation)

---

## Overview

The Invoice Management (INVC) feature in QPTM provides the ability to view, manage, and process billing invoices for natural gas pipeline transportation services. Invoices are generated as part of the billing cycle and represent charges owed by Service Requesters (shippers) to Transportation Service Providers (TSPs) for gas transportation services.

The Invoice Maintenance screen is the primary interface for reviewing invoice data across five tabs: Invoice Header, Header by Contract, Detail, Sub-Detail by TOC, and Sub-Detail by Contract. Internal users can modify invoice statuses and post invoices, while external users have read-only access restricted to their own business associate data.

---

## Invoice Lifecycle

The typical lifecycle of an invoice in QPTM follows this flow:

```
Billing Run -> Preliminary (PRE) -> Approved (APP) -> Final (FIN) -> Posted (PST)
                    |                                       |
                    v                                       v
               Modified (MOD)                        Superseded (SS)
                                                     Written Off (WO)
```

1. **Generation**: Invoices are generated during the billing run process by the batch system. The billing engine calculates charges based on contracts, rates, nominations, allocations, and related data.

2. **Preliminary Review (PRE)**: Newly generated invoices start in Preliminary status. At this stage, they can be reviewed and modified by internal pipeline users.

3. **Approval (APP)**: Once reviewed, invoices are moved to Approved status, indicating they have been verified by the billing team.

4. **Finalization (FIN)**: Approved invoices are finalized, locking them from further modification. This is required before an invoice can be posted/closed.

5. **Posting (PST)**: Final invoices in the current open accounting month are posted via the BLROLLPER batch process, which closes them for the accounting period. Once posted, the accounting month can be rolled forward.

6. **Superseded (SS)**: An invoice that has been replaced by a corrected version.

7. **Written Off (WO)**: An invoice that has been written off and is no longer collectible.

---

## Invoice Status Codes

| Code | Name | Description |
|------|------|-------------|
| `PRE` | Preliminary | Initial status after billing run generation. Editable by internal users. |
| `MOD` | Modified | Invoice has been modified after initial generation. |
| `APP` | Approved | Invoice has been reviewed and approved for finalization. |
| `FIN` | Final | Invoice is finalized and locked. Required status before posting. |
| `PST` | Posted | Invoice has been posted/closed for the accounting period. |
| `SS` | Superseded | Invoice has been replaced by a corrected version. |
| `WO` | Written Off | Invoice has been written off. |

### Status Transition Rules

- Once an invoice is in **Final** (`FIN`) status, its status **cannot** be changed. This is enforced by validation rule `001_ValidateHeaderStatusCode`.
- An invoice must be in **Final** status before it can be posted (closed). This is enforced by validation rule `004_ValidateInvoice`.
- Detail-level status codes cannot be set directly to **Final** by users. This is enforced by validation rule `005_ValidateDetailStatusCode`.
- When a header status is changed to **Approved** or **Preliminary**, all associated detail records are automatically updated to match (`PostUpdateAction`).

---

## Invoice Data Hierarchy

Invoices follow a three-level hierarchy:

```
Invoice Header (BLTRAN_INVOICE_HDR)
  |
  +-- Invoice Detail (BLTRAN_INVOICE_DTL)
  |     |
  |     +-- Invoice Sub-Detail (BLTRAN_INVOICE_SUB_DTL)
  |     +-- Invoice Sub-Detail Revision (BLTRAN_INVOICE_SUB_DTL_REV)
  |
  +-- Header by Contract (BLRPTS_10_INVOICE_DOC_SUM)
        (summary view joining header with contract/TOS breakdown)
```

### Invoice Header

The top-level record representing a single invoice. Key fields include:

- **InvoiceHdrId**: Unique identifier for the invoice header
- **InvoiceId**: Human-readable invoice number
- **InvoiceGrpId**: Billing group the invoice belongs to
- **AcctgMth**: Accounting month the invoice belongs to
- **BpNo / BpNm**: Business Partner number and name (the party being billed)
- **AgentBpNo / AgentBpNm**: Agent business partner (if applicable)
- **InvoiceAmt**: Total invoice amount
- **InvoiceStatCode**: Current status code
- **InvoiceDate / NetDueDate**: Invoice date and payment due date
- **ProcessQueueId**: Batch process queue identifier
- **BillPeriodId**: Billing period identifier
- **PostedDate / PostDate**: When the invoice was posted
- **IsOpen**: Whether the invoice is in an open (not yet closed) accounting period
- **IsPost**: Whether the user has flagged this invoice for posting

### Invoice Detail

Line-item breakdown of the invoice charges. Key fields include:

- **InvoiceDtlId**: Detail line identifier
- **InvoiceHdrId**: Parent header reference
- **LineNum**: Line number for ordering
- **CtrNo**: Contract number
- **TocCode / TocDescr**: Type of Charge code and description
- **TosCode**: Type of Service code
- **TransAmt**: Transaction amount
- **VolQty / EngQty**: Volume and energy quantities
- **SchdFuelPct**: Scheduled fuel percentage
- **InvoiceStatCode**: Detail-level status code

### Invoice Sub-Detail

The most granular level of invoice data, showing daily activity-level charges. Key fields include:

- **InvoiceSubDtlId**: Sub-detail identifier
- **ActivityDate**: Date of the gas flow activity
- **Rate / RateUnrounded**: Applied rate values
- **RateHdrId / RateDtlId**: References to the rate schedule
- **RateTypeCode**: Type of rate applied
- **TocCode / TocDescr**: Type of Charge
- **TierDtlId / TierDescr**: Rate tier information
- **LocId1 / LocId2**: Receipt and delivery location identifiers
- **FlowDirection**: Direction of gas flow
- **ChargeBasisCode**: Basis for the charge calculation
- **AllocFuelVolQty / AllocFuelEngQty**: Allocated fuel quantities
- **CtrQty / AllocQty**: Contract and allocated quantities
- **BtuFactor / ConvFactor**: Energy conversion factors

---

## Billing Groups

Invoice Groups define how invoices are organized and generated during the billing process. Each invoice belongs to exactly one billing group identified by `InvoiceGrpId`.

- **BillingInvoiceGroup (BLCTRL_INVOICE_GRP)**: Defines the billing group configuration, including effective date ranges (`EffDateFrom` / `EffDateTo`).
- **BillingInvoiceGroupContract (BLCTRL_INVOICE_GRP_CTR)**: Links contracts to billing groups, defining which contracts are included in a particular group.
- **BlctrlInvoiceGrpCopy**: Controls invoice delivery methods. Groups with an `Internal` delivery method only (no external copies) are filtered from external user views.
- **BillingLastInvoiceGrpRunXref (BLXREF_LAST_INVOICE_GRP_RUN)**: Cross-reference table linking invoice headers to the most recent billing run for each group/month/period combination. This is used to determine the `IsOpen` flag and to filter valid sub-details.

The Invoice Group Maintenance screen (linked from Invoice Maintenance) allows configuration of billing groups.

---

## Invoice Messages and Sub-Details

### Sub-Detail by TOC (Tab 4)

Sub-details grouped/aggregated by Type of Charge. The grouping algorithm (`GetGroupedBillingInvoiceSubDetailList`) aggregates daily sub-detail records into summary rows based on a composite key that includes:

- InvoiceHdrId, InvoiceDtlId, BP info, AcctgMth, ProdMth
- Contract, TOS, locations, zones, route
- TOC code, rate info, status, flow direction, capacity type

Aggregated fields: ActivityDate (min/max as date range), energy/volume quantities (summed), amounts (summed), fuel percentages (averaged).

### Sub-Detail by Contract (Tab 5)

The full granular sub-detail records at the daily activity level, not aggregated. This view combines:
- Current sub-details from `BLTRAN_INVOICE_SUB_DTL`
- Revision sub-details from `BLTRAN_INVOICE_SUB_DTL_REV` (converted via `CopyBillingInvoiceSubDetailRevList`)

Both are joined against `BLXREF_LAST_INVOICE_GRP_RUN` to ensure only records from the latest billing run are displayed.

### Sub-Detail Enrichment (FillSubDetails)

The `InvoiceMaintenance_FillSubDetails` class enriches sub-detail records with:
1. **Rate Type Code**: Looked up from the Rate table based on `RateHdrId` and `ActivityDate` effective date range
2. **TOC Description**: Looked up from the Rate Type of Charge table based on `TocCode`
3. **Tier Description**: Looked up from the Rate Tier Detail cache based on `RateTierId` and `TierDtlId`

---

## Charge Basis Types

The `ChargeBasisCode` field on sub-detail records indicates the basis used for calculating the charge. Common charge basis types in pipeline transportation billing include:

- **Capacity-based charges**: Based on contracted maximum daily quantities (MDQ)
- **Commodity/usage-based charges**: Based on actual gas volumes transported
- **Fuel charges**: Based on fuel consumption (percentage of scheduled or allocated quantities)
- **Surcharges**: Additional fees applied on top of base charges

The specific charge basis codes are TSP-configurable and tied to the rate schedule structure.

---

## Type of Charge (TOC)

Type of Charge (`TocCode`) categorizes individual invoice line items and sub-detail records by the nature of the charge. TOC codes are defined per TSP in the `RT_TYPE_OF_CHARGE` table. Examples include:

- Reservation/demand charges
- Usage/commodity charges
- Fuel retention charges
- Surcharges and penalties
- Balancing charges
- ACA (Annual Charge Adjustment) surcharges

The TOC description (`TocDescr`) is looked up during sub-detail enrichment and displayed in the Sub-Detail by TOC and Sub-Detail by Contract grids.

---

## Type of Service (TOS)

Type of Service (`TosCode`) identifies the type of transportation service under which the invoice charges were incurred. Common TOS types include firm transportation, interruptible transportation, park and loan, and others. TOS is a key grouping field in the Header by Contract view.

---

## Prior Period Adjustments (PPA)

Prior Period Adjustments handle corrections to previously billed amounts. Key PPA-related fields include:

- **PpaSrcCode**: Source code identifying the origin of the PPA
- **PpaAmt**: The PPA adjustment amount on the header
- **PrevInvoiceId / PrevInvoiceLineNo / PrevInvoiceSubDtlId**: References to the original invoice line being adjusted
- **AcctAdjMethCode**: Accounting adjustment method code
- **InvAdjTypeCode**: Invoice adjustment type code

PPA amounts are tracked separately from current-period amounts at the header level (`CurrentAmt` vs `PpaAmt`), and the total transaction amount (`TransAmt`) is the sum of both.

---

## Accounting Month and Billing Periods

### Accounting Month (AcctgMth)

The accounting month determines the financial period for the invoice. Key behaviors:

- The **Current Open Accounting Month** is retrieved from the `AccountingMonth` table filtered by `RollTypeCode = 'Billing'`
- Invoices can only be posted if their `AcctgMth` is greater than or equal to the current open accounting month
- The TSP configuration `AllowCloseFutureAcctgOnHdr` controls whether invoices for future accounting months can be closed
- A query requires at least an Accounting Month or BA# (Business Associate number) to execute

### Billing Period (BillPeriodId)

Billing periods represent the actual time span covered by an invoice. A single accounting month may contain multiple billing periods (e.g., for mid-month billing cycles). The `BillPeriodId` is used as part of the composite key when joining invoice data with the billing run cross-reference.

---

## Internal vs External Users

The system distinguishes between internal (pipeline) and external (shipper/agent) users:

### Internal Users

- Can view all invoices for the TSP
- Can modify invoice status codes (header and detail level)
- Can post/close invoices (set `IsPost` flag)
- Can trigger invoice report generation
- Save button is visible

### External Users

- View is restricted to invoices related to their Business Associate (BP)
- BpNo is automatically set to the user's default BP on initialization
- Cannot modify any data (Save button is hidden)
- Cannot delete records (enforced by validation rule `002_ValidateDeletePermission`)
- Cannot update records (enforced by validation rule `003_ValidateUpdatePermission`)
- Data filtering is performed through a complex contract/agent chain:
  1. User's BP list is retrieved
  2. Contract agents matching the user's BPs are found
  3. Contract amendments and headers are joined to validate effective date ranges
  4. Only invoices matching the contract chain are shown

---

## Invoice Posting and Batch Processing

When an internal user marks invoices for posting (via the `IsPost` checkbox in the header grid):

1. **Pre-save Validation**: The system validates that `InvoiceStatCode` is not null for all header and detail records
2. **Service-level Validation**: All five validation rules are executed (status code, permissions, invoice finalization)
3. **Batch Process Launch**: If any headers are marked as Final + Open + IsPost and their AcctgMth >= current open month, the `BLROLLPER` batch process is launched synchronously with parameters:
   - `PARAM_TSP_NO`: The TSP number
   - `PARAMID_INVOICE_HDR_ID`: Comma-separated list of invoice header IDs
   - `PARAM_ACCTG_MONTH`: Current open accounting month
4. **Post-save Update**: After successful save, detail records are updated to match the header status for Approved or Preliminary headers
5. **Process Monitoring**: The batch process ID is added to the UI process monitor for tracking

### Invoice Report Generation

Users can generate invoice reports (PDF documents) by clicking the report action on a selected header row. This launches the `BLRX00` batch process with the TSP, accounting month, and invoice group ID.

---

## Key Business Rules

1. **Query Requirements**: At least an Accounting Month or Business Associate # must be provided to query invoices.
2. **Final Status is Immutable**: Once a header or detail record reaches Final status, its status cannot be changed.
3. **Final Required for Posting**: An invoice must be in Final status before it can be posted/closed.
4. **Accounting Month Validation**: Only invoices in the current (or future, if configured) open accounting month can be posted. Invoices from closed accounting months cannot be posted.
5. **Status Cascade**: When a header status is changed to Approved or Preliminary, all associated detail records are automatically updated to match.
6. **Detail Cannot Be Set to Final Directly**: Detail-level status codes cannot be manually set to Final by the user.
7. **External User Restrictions**: External users cannot modify, delete, or post invoices. They can only view data related to their business associate.
8. **Sub-Detail Revision Inclusion**: Both current sub-details and revision sub-details are combined and displayed together, joined against the billing run cross-reference.
9. **Invoice Group Filtering for External Users**: Invoice groups that only have internal delivery methods are excluded from external user views.
10. **Open Indicator**: The `IsOpen` flag is derived from the `BLXREF_LAST_INVOICE_GRP_RUN` cross-reference and determines whether an invoice can still be modified/posted.

---

## Glossary

| Term | Definition |
|------|-----------|
| **AcctgMth** | Accounting Month - the financial period an invoice belongs to |
| **AgentBpNo** | Agent Business Partner Number - the agent acting on behalf of the shipper |
| **BillPeriodId** | Billing Period Identifier - sub-period within an accounting month |
| **BLROLLPER** | Billing Roll Period - batch process that posts/closes invoices |
| **BLRX00** | Batch process for generating invoice report documents |
| **BpNo** | Business Partner Number - unique identifier for a shipper/customer |
| **ChargeBasisCode** | Code indicating the basis for calculating a charge (capacity, commodity, etc.) |
| **CtrNo** | Contract Number - reference to the transportation service agreement |
| **EngQty** | Energy Quantity - amount in energy units (e.g., Dth) |
| **InvoiceGrpId** | Invoice Group Identifier - groups invoices for billing run organization |
| **InvoiceHdrId** | Invoice Header Identifier - unique key for an invoice |
| **InvoiceStatCode** | Invoice Status Code (PRE, MOD, APP, FIN, PST, SS, WO) |
| **IsOpen** | Flag indicating the invoice is in an open (not yet closed) accounting period |
| **IsPost** | User-set flag indicating the invoice should be posted during save |
| **MDQ** | Maximum Daily Quantity - the contracted capacity amount |
| **PPA** | Prior Period Adjustment - corrections to previously billed amounts |
| **ProcessQueueId** | Batch process queue identifier linking to the billing run |
| **RateHdrId** | Rate Header Identifier - reference to the rate schedule |
| **TocCode** | Type of Charge Code - categorizes the nature of the charge |
| **TosCode** | Type of Service Code - categorizes the transportation service type |
| **TransAmt** | Transaction Amount - the monetary value of a charge |
| **TSP** | Transportation Service Provider - the pipeline company |
| **VolQty** | Volume Quantity - amount in volume units (e.g., Mcf) |

---

## Related Documentation

- [Architecture Documentation](./architecture.md) - Technical details of service methods, controllers, database tables, and the FillSubDetails algorithm
- [Troubleshooting Guide](./troubleshooting.md) - Common issues, diagnostic SQL queries, and resolution patterns

---

*Last updated: 2026-03-03*

*Document version: 1.0*
