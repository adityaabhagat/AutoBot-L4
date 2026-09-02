---
title: Inventory (INV) - Domain Concepts
category: domain
feature: Inventory (INV)
related_repos: Web, Batch
keywords: INV, inventory, balance, account, storage, PAL, injection, withdrawal, imbalance, IMB, INK, STO, OBA, trade, transfer, CICO, NNS, tolerance, accumulation, INACCTACCM
last_updated: 2026-03-03
---

# Inventory (INV) - Domain Concepts

## Overview

This document explains the **business concepts** behind the Inventory (INV) feature in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows for gas pipeline inventory management.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Inventory Account Types](#inventory-account-types)
3. [Imbalance Trading](#imbalance-trading)
4. [Imbalance Trading State Machine](#imbalance-trading-state-machine)
5. [Trade Quantity Availability](#trade-quantity-availability)
6. [Storage Accounts](#storage-accounts)
7. [Previously Allocated (PAL) Concepts](#previously-allocated-pal-concepts)
8. [Inventory Adjustments](#inventory-adjustments)
9. [Manual Posting](#manual-posting)
10. [Inventory Account Balances](#inventory-account-balances)
11. [Imbalance Tolerance](#imbalance-tolerance)
12. [Production Month and Accounting Month](#production-month-and-accounting-month)
13. [Account Rolling Behavior](#account-rolling-behavior)
14. [Key Business Rules](#key-business-rules)
15. [Glossary](#glossary)

---

## System Overview

### What is Inventory (INV)?

**Inventory (INV)** is the QPTM module responsible for tracking gas quantities held in shipper accounts on a pipeline. It maintains running balances of gas imbalances (the difference between gas receipts and deliveries), storage balances (gas injected into or withdrawn from storage facilities), and provides mechanisms for shippers to trade or transfer imbalances between accounts.

**Business Purpose:**
- Track shipper gas balances (imbalances) on the pipeline over time
- Maintain storage account balances with injection/withdrawal tracking
- Enable imbalance trading between shippers to resolve overages and shortages
- Support storage transfers between accounts
- Provide inventory adjustments for corrections and reconciliation
- Calculate tolerance thresholds for imbalance monitoring
- Support both monthly and daily imbalance periods

### Key Business Value

- **Balance Accuracy**: Maintains precise tracking of gas volumes owed to or owed by shippers
- **Imbalance Resolution**: Enables shippers to trade imbalances, reducing pipeline operational risk
- **Storage Management**: Tracks injection/withdrawal quantities against contracted storage limits (MSQ, MDIQ, MDWQ)
- **Regulatory Compliance**: Supports FERC Order 637 imbalance management and OFO requirements
- **Financial Settlement**: Provides the basis for cashout (CICO) and balancing charges

---

## Inventory Account Types

Each inventory account has an **account type** (`ACCT_TYPE_CD`) that determines its behavior, screen format, and business rules. The primary account types are:

### IMB - Imbalance

The most common account type. Tracks the cumulative difference between allocated receipt quantities and allocated delivery quantities for a shipper on the pipeline.

- **Screen Format**: Imbalance (`IMB`)
- **Category**: Imbalance (`IMB`)
- **Key Metric**: `REC_DEL_DIFF_QTY` (Receipt-Delivery Difference Quantity)
- **Usage**: Standard shipper imbalance tracking

### INK - In-Kind Imbalance

Tracks imbalances that are settled "in-kind" (i.e., resolved through physical gas deliveries rather than cash payments).

- **Screen Format**: Imbalance (`IMB`)
- **Category**: Imbalance (`IMB`)
- **Usage**: In-kind settlement tracking

### STO - Storage

Tracks gas volumes injected into and withdrawn from storage facilities. Storage accounts have additional contractual limits.

- **Screen Format**: Storage (`STG`) or NNS
- **Category**: Balance (`BAL`)
- **Key Metrics**: Injection Qty, Withdrawal Qty, MSQ (Maximum Storage Quantity), MDIQ (Maximum Daily Injection Quantity), MDWQ (Maximum Daily Withdrawal Quantity)
- **Usage**: Storage facility balance tracking

### PAL - Previously Allocated

Tracks quantities that were previously allocated in prior accounting months. PAL accounts carry forward imbalances from closed months into the current period.

- **Screen Format**: Imbalance (`IMB`)
- **Category**: Imbalance (`IMB`)
- **Usage**: Historical imbalance carryforward

### OBA - Operator Balancing Account

A special account type used by pipeline operators (as opposed to shippers) to track operational balances. OBA accounts are filtered separately based on the `OperationalBalance` contract attribute.

- **Screen Format**: Imbalance (`IMB`)
- **Category**: Imbalance (`IMB`)
- **Usage**: Operator-level balancing

### Additional Account Types

| Code | Name | Description |
|------|------|-------------|
| `NNI` | NNS Imbalance | No-Notice Service imbalance |
| `DLY` | Daily Imbalance | Daily-period imbalance tracking |
| `MTH` | Monthly Imbalance | Monthly-period imbalance tracking |
| `IT3` | ITS-3 | Interruptible Transportation Service Type 3 |
| `JDE` | ERP JD Edwards | Integration with JD Edwards ERP |
| `SAP` | ERP SAP | Integration with SAP ERP |

### Account Type Categories

Account types are grouped into two categories (`ACCT_TYPE_CTGRY_CD`):

- **IMB (Imbalance)**: For accounts that track receipt/delivery differences
- **BAL (Balance)**: For accounts that track absolute storage balances

---

## Imbalance Trading

### What is Imbalance Trading?

Imbalance trading allows shippers to **trade gas imbalances** between their accounts. If one shipper has a long (excess) imbalance and another has a short (deficit) imbalance, they can trade quantities to reduce both imbalances toward zero.

### Trade Structure

A trade involves two parties:
- **Initiating Trader**: The shipper who creates and submits the trade request
- **Confirming Trader**: The counterparty who must accept or reject the trade

### Trade Properties

| Property | Description |
|----------|-------------|
| `ReqTradeQty` | Requested trade quantity |
| `ApprTradeQty` | Approved trade quantity (set equal to requested on submit) |
| `InitTradeQty` | Initiating trader's quantity |
| `ConfTradeQty` | Confirming trader's quantity |
| `TradeTransTypeCode` | Either `TRAD` (Trade) or `XFER` (Transfer) |
| `ImbalPeriodCode` | Either `MTH` (Monthly) or `DAY` (Daily) |
| `TradeDirCode` | Trade direction |
| `TradeStatCode` | Current status in the state machine |
| `InitAcctType` | Initiating account type |
| `ConfAcctType` | Confirming account type |
| `ProdMth` | Production month of the imbalance |
| `AcctgMth` | Accounting month |
| `GasDay` | Gas day (for daily trades) |

### Trade Types

| Code | Name | Description |
|------|------|-------------|
| `LONG` | Long | Shipper has excess gas (positive imbalance) |
| `SHORT` | Short | Shipper has a gas deficit (negative imbalance) |
| `AGENT` | Agent | Agent-initiated trade |
| `STO` | Storage | Storage-related trade |

### Trade vs Transfer

- **Trade** (`TRAD`): An imbalance trade between two different shippers' accounts
- **Transfer** (`XFER`): A storage transfer between two accounts, typically within the same shipper's portfolio

---

## Imbalance Trading State Machine

Trade status transitions follow a defined state machine governed by `QCODE_TRADE_STAT` and `QCODE_TRADE_ACTN` code tables.

### Trade Statuses

| Code | Status | Description |
|------|--------|-------------|
| `NEW` | New | Trade record created but not yet submitted |
| `PEN` | Pending | Trade submitted and awaiting confirmation |
| `PAP` | Pending Approval | Trade awaiting internal approval |
| `VLD` | Valid | Trade validated successfully |
| `CON` | Confirmed | Both parties confirmed the trade |
| `PRC` | Processed | Trade has been processed and balances updated |
| `REJ` | Rejected | Trade was rejected by the confirming party |
| `WTH` | Withdrawn | Trade was withdrawn by the initiating party |
| `INV` | Invalid | Trade failed validation |
| `INC` | Invalid Confirming | Trade failed confirming-side validation |
| `INP` | Invalid Processing | Trade failed during processing |

### Trade Actions

| Code | Action | Description |
|------|--------|-------------|
| `SUB` | Submit Request | Initiate the trade and set to Pending |
| `CON` | Confirm | Confirming party confirms the trade |
| `ACC` | Accept | Accept the trade for processing |
| `PRC` | Process | Process the trade and update balances |
| `PRP` | Process Pending | Mark trade for pending processing |
| `REJ` | Reject | Reject the trade |
| `WTH` | Withdraw | Withdraw the submitted trade |

### State Machine Flow

```
                                     +-------+
                                     |  REJ  |
                                     +---^---+
                                         |
                                    [Reject]
                                         |
+-----+    [Submit]    +-----+    [Confirm]    +-----+    [Accept]    +-----+    [Process]    +-----+
| NEW | ------------> | PEN | ------------->  | CON | ------------>  | VLD | -------------> | PRC |
+-----+               +--+--+                +-----+               +-----+                +-----+
                          |                                            |
                     [Withdraw]                                   [Process]
                          |                                            |
                       +--v--+                                     +---v---+
                       | WTH |                                     | PRC   |
                       +-----+                                     +-------+
```

**Detailed Flow:**

1. **New --> Pending (Submit)**: Initiating trader creates and submits the trade. Fuel quantities are set to 0, approved/init/conf quantities are set equal to requested. The `INTRDPEND` batch process is NOT launched on submit.
2. **Pending --> Confirmed (Confirm)**: Confirming party reviews and confirms. The `INTRDPEND` (Trade Pending) batch process is launched to validate and move to Confirmed status.
3. **Confirmed --> Processed (Accept/Process)**: After acceptance, the `INCONFTRADE` (Trade Confirmation) batch process is launched to update account balances.
4. **Pending --> Rejected (Reject)**: Confirming party rejects the trade.
5. **Pending --> Withdrawn (Withdraw)**: Initiating party withdraws. The `INTRDWITH` (Trade Withdrawal) batch process is launched to reverse any pending changes.

### Batch Processes for Trading

| Process ID | Name | Trigger |
|------------|------|---------|
| `INTRDPEND` | Trade Pending | Launched on Confirm action |
| `INTRDTRANS` | Trade Confirmation | Launched on Accept/Process action |
| `INTRDWITH` | Trade Withdrawal | Launched on Withdraw action |

---

## Trade Quantity Availability

### Monthly Trade Availability Formula

The quantity available for trade is calculated using a configurable formula (stored in `PACTRL_TSP_CNFG_CTRL`). The formula operates on balance quantities from `INTRAN_ACCT_BAL` across multiple accounting month perspectives:

**Formula Variables (3 sets of balance queries):**

| Variable Set | ProdMth | AcctgMth | Description |
|-------------|---------|----------|-------------|
| Set 1 (`_QTY`) | Trade.ProdMth | OpenAcctMth - MonthlyTradeLagTime | Lagged balance |
| Set 2 (`_QTY2`) | Trade.ProdMth | OpenAcctMth | Current open month balance |
| Set 3 (`_QTY3`) | Trade.ProdMth | Trade.ProdMth | Production month balance |

**Variables per set:**
- `REC_DEL_DIFF_QTY` - Receipt/Delivery Difference
- `TRADE_QTY` - Already traded quantity
- `TRANSFER_QTY` - Already transferred quantity
- `ADJ_QTY` - Adjustment quantity
- `CICO_QTY` - Cashout quantity
- `END_BAL_QTY` - Ending balance

The formula is evaluated by the User-Defined Formula Service (`IQUserDefinedFormulaSvc`), configured per TSP via `FormulaIdInvRecDelDiffQty`.

### Daily Trade Availability Formula

For daily imbalance trades, a separate formula is used (configured via `FormulaIdInvRecDelDiffQtyDaily`). It queries `INTRAN_ACCT_BAL_DAILY` for the specific gas day and sums:
- `RecDelDiffQty`, `TradeQty`, `TransferQty`, `AdjQty`, `CicoQty`, `EndBalQty`

### Trade Quantity Validation

- For **Imbalance category** accounts: `ReqTradeQty` must not exceed `|RecDelDiffQty|` (absolute value of available quantity). External users are blocked; internal users may override.
- The `MonthlyTradeLagTime` on the contract header determines which accounting months are used for the availability calculation.

---

## Storage Accounts

### Storage Balance Tracking

Storage accounts track gas volumes in underground storage facilities or LNG tanks. Key metrics include:

| Metric | Description |
|--------|-------------|
| **Daily Injection Qty** | Gas injected into storage on a given day (`AllocRecQty`) |
| **Daily Withdrawal Qty** | Gas withdrawn from storage on a given day (`AllocDelQty`) |
| **MTD Balance** | Month-to-date ending balance (`EndBalQty`) |
| **MSQ (Min)** | Minimum Storage Quantity - contractual floor |
| **MSQ (Max)** | Maximum Storage Quantity - contractual ceiling |
| **MDIQ** | Maximum Daily Injection Quantity |
| **MDWQ** | Maximum Daily Withdrawal Quantity |

### Storage Ratchets

MSQ, MDIQ, and MDWQ quantities may be subject to **ratchets** -- adjustable limits based on current storage levels. The `ResolverMdq` class computes effective MDIQ/MDWQ using `tRatchetStartPct` and `tRatchetEndPct` parameters.

### Storage Transfers

Storage transfers (`XFER` transaction type) allow moving gas between storage accounts. They follow the same state machine as imbalance trades but use the **Storage Transfer** validation rule set (`RuleINST*`).

Key storage transfer validations:
- Confirming contact name, phone number, and contract number are required
- Transfer quantities must not exceed available storage capacity
- Both from and to accounts must be valid storage accounts

---

## Previously Allocated (PAL) Concepts

**PAL (Previously Allocated)** quantities represent imbalances from prior production or accounting months that are carried forward. When an accounting month closes, any remaining imbalance becomes a PAL quantity in subsequent months.

- PAL accounts have type code `PAL`
- PAL quantities appear in the `INTRAN_ACCT_BAL` table with the relevant production month and accounting month
- The PPA (Previously Posted Allocation) quantity field on balances (`PPA_QTY`, `PPA_DEL_QTY`, `PPA_REC_QTY`) tracks these carryforward amounts

---

## Inventory Adjustments

### What are Inventory Adjustments?

Inventory adjustments allow authorized users to manually adjust inventory account balances. Common reasons include:
- Correction of erroneous allocations
- True-up after measurement revisions
- Inter-company transfers
- Regulatory-mandated adjustments

### Adjustment Structure

An adjustment record (`INCTRL_INV_ADJ` table) specifies:

| Field | Description |
|-------|-------------|
| `ActivityDate` | Date of the adjustment |
| `ProdMth` | Production month affected |
| `AcctgMth` | Accounting month affected |
| `FromCtrNo` | Source contract number |
| `ToCtrNo` | Destination contract number |
| `FromOperImpAreaCode` | Source Operator Impact Area |
| `ToOperImpAreaCode` | Destination Operator Impact Area |
| `FromInvQtyCode` | Source inventory quantity code |
| `ToInvQtyCode` | Destination inventory quantity code |
| `InvAdjTypeCode` | Adjustment type code |
| `AdjQty` | Adjustment quantity (energy) |
| `AdjQtyVol` | Adjustment quantity (volume) |
| `SubmitInd` | Submit indicator |
| `DeleteInd` | Delete indicator |
| `IsProc` | Whether the adjustment has been processed |

### Adjustment Rules

- **Processed adjustments are read-only**: Once `IsProc = true`, all fields become read-only except the delete indicator
- **Delete indicator for processed records**: May still be toggled if the accounting month is no longer valid
- **Required fields**: `ActivityDate`, `ProdMth`, `AcctgMth`, `InvAdjTypeCode`
- **Cloning**: Users can clone an existing adjustment to create a new one with the same parameters

---

## Manual Posting

### What is Manual Posting?

Manual posting allows authorized users to post inventory balance updates directly to an account. This is typically used when automated processes (like the INACCTACCM batch) need to be supplemented or corrected.

### Manual Posting Validation

- **Account balance must exist**: The system validates that an `INTRAN_ACCT_BAL` record exists for the specified inventory account, production month, and accounting month before allowing a manual post
- **Open accounting month required**: The billing accounting month must be open
- **Accounting month lagtime**: The production month is calculated by subtracting the TSP's `ACCTG_MTH_LAG_TIME` from the open accounting month

---

## Inventory Account Balances

### Monthly Balance (`INTRAN_ACCT_BAL`)

The monthly balance table stores cumulative quantities for each inventory account per production month and accounting month:

| Column | Description |
|--------|-------------|
| `BEG_BAL_QTY` | Beginning balance quantity |
| `ALLOC_REC_QTY` | Allocated receipt quantity |
| `ALLOC_DEL_QTY` | Allocated delivery quantity |
| `REC_DEL_DIFF_QTY` | Receipt minus delivery difference |
| `TRADE_QTY` | Quantity traded |
| `TRANSFER_QTY` | Quantity transferred |
| `ADJ_QTY` | Adjustment quantity |
| `CICO_QTY` | Cash-in/Cash-out quantity |
| `END_BAL_QTY` | Ending balance quantity |
| `NNS_IMB_QTY` | No-Notice Service imbalance quantity |
| `PREV_IMB_QTY` | Previous imbalance quantity |
| `PPA_QTY` | Previously Posted Allocation quantity |
| `GROSS_REC_QTY` | Gross receipt quantity (before fuel) |
| `GROSS_DEL_QTY` | Gross delivery quantity (before fuel) |
| `REC_FUEL_QTY` | Receipt fuel quantity |
| `DEL_FUEL_QTY` | Delivery fuel quantity |
| `RETAINED_QTY` | Retained quantity |
| `RETAINED_PCT` | Retained percentage |
| `PAYBACK_QTY` | Payback quantity |
| `CUV_QTY` | Cumulative Unauthorized Volume |
| `CICO_CUV_QTY` | CICO CUV quantity |

### Daily Balance (`INTRAN_ACCT_BAL_DAILY`)

Similar to monthly but tracked at the gas-day level. Used for daily imbalance period accounts and daily trade availability calculations.

### Balance Formula

```
END_BAL_QTY = BEG_BAL_QTY + REC_DEL_DIFF_QTY + TRADE_QTY + TRANSFER_QTY + ADJ_QTY + CICO_QTY
```

---

## Imbalance Tolerance

### Tolerance Calculation

Imbalance tolerance determines how much imbalance is acceptable before penalties or actions are required:

```
ToleranceQty = Round(ToleranceBasis * TolerancePct, VolScale)
```

Where:
- **ToleranceBasis**: Based on TSP configuration (`GetImbalanceToleranceBasis`), either:
  - `REC` - Sum of allocated receipt quantities
  - Otherwise - Sum of allocated delivery quantities
- **TolerancePct**: TSP-configured tolerance percentage (`GetImbalanceTolerancePercent`)
- **VolScale**: TSP volume precision scale from preferences

### Daily Imbalance Calculation

For non-rolling accounts on the first day of a production month, the daily imbalance is reset to zero. Otherwise:

```
DailyImbalQty = Sum(RecDelDiffQty) for the previous gas day
```

---

## Production Month and Accounting Month

### Production Month (ProdMth)

The calendar month in which gas physically flowed. Production month determines which physical flows are included in balance calculations.

### Accounting Month (AcctgMth)

The calendar month in which the accounting entries are recorded. The accounting month may lag behind the production month based on the TSP configuration:

```
ProdMth = OpenAcctMth - ACCTG_MTH_LAG_TIME
```

### Open Accounting Month

The current open billing accounting month, retrieved from `QCTRL_ACCTG_MTH` where `OPEN_IND = true` and `ACCTG_ROLL_TYPE_CD = 'Billing'`.

---

## Account Rolling Behavior

### Rolling vs Non-Rolling Accounts

Each account type has an `IsRollProdMth` property that determines month-boundary behavior:

- **Rolling accounts** (`IsRollProdMth = true`): Imbalances carry forward from the previous month. The daily imbalance is continuous across month boundaries.
- **Non-rolling accounts** (`IsRollProdMth = false`): Imbalances reset at the start of each production month. On the 1st day of a month, `DailyImbalQty = 0`.

This affects:
- Dashboard widget calculations (daily imbalance display)
- Beginning balance calculations for new production months
- Tolerance basis calculations

---

## Key Business Rules

1. **Only new trade records can be submitted**: Existing records must be copied to create a new submission (RuleINTR000020)
2. **Monthly Trade Lag Time required**: For monthly-period trades, the contract must have a `MonthlyTradeLagTime` value (RuleINTR000010)
3. **Trade quantity cannot exceed available**: For imbalance category accounts, `ReqTradeQty <= |RecDelDiffQty|` for external users (RuleINTR000050)
4. **External users cannot add inventory accounts**: Only internal users can create new inventory account headers (RuleINCA000010)
5. **Manual posting requires existing balance**: An `INTRAN_ACCT_BAL` record must exist for the account/prod month/acctg month combination (RuleINMP000010)
6. **Storage transfer requires confirming details**: Contact name, phone, and contract are required for storage transfers (RuleINST000010)
7. **Processed adjustments are read-only**: Fields on processed adjustments cannot be modified
8. **Tolerance is TSP-configurable**: Each TSP can configure its own tolerance percentage and basis source

---

## Glossary

| Term | Definition |
|------|-----------|
| **Imbalance** | The difference between gas received and gas delivered for an account |
| **CICO** | Cash-In/Cash-Out - financial settlement of imbalances |
| **MSQ** | Maximum Storage Quantity - contractual storage capacity limit |
| **MDIQ** | Maximum Daily Injection Quantity - daily gas injection limit |
| **MDWQ** | Maximum Daily Withdrawal Quantity - daily gas withdrawal limit |
| **PAL** | Previously Allocated - carryforward of prior-period imbalances |
| **PPA** | Previously Posted Allocation - allocation quantity from a prior accounting month |
| **OIA** | Operator Impact Area - geographic/operational area code |
| **NNS** | No-Notice Service - a type of firm storage service |
| **CUV** | Cumulative Unauthorized Volume - volume exceeding authorized limits |
| **RecDelDiffQty** | Receipt-Delivery Difference Quantity - net imbalance |
| **TSP** | Transportation Service Provider - the pipeline company |
| **Production Month** | The month gas physically flowed |
| **Accounting Month** | The month the accounting entry is recorded |
| **Trade Lag Time** | Months between production and trade eligibility |
| **Ratchet** | Adjustable storage injection/withdrawal limits based on current balance |
| **Gas Day** | The 24-hour period used for pipeline operations (may differ from calendar day) |
| **Tolerance** | Acceptable imbalance threshold before penalties apply |
| **Fuel** | Gas retained by the pipeline for compressor fuel and operational use |
| **Retained Qty** | Quantity retained by the pipeline (fuel, shrinkage) |
| **Payback** | Quantity to be returned in future periods to resolve imbalances |

---

*Cross-references:*
- [Architecture Documentation](./architecture.md) - Technical implementation details
- [Troubleshooting Guide](./troubleshooting.md) - Known issues and diagnostic queries

*Last updated: 2026-03-03*

*Document version: 1.0*
