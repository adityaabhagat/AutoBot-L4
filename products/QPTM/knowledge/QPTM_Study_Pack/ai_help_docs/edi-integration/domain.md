---
title: QPTM EDI Integration (EDI) - Domain Concepts
category: domain
feature: QPTM EDI Integration (EDI)
related_repos: Web, Batch
keywords: EDI, Electronic Data Interchange, NAESB, trading partner, TPA, TPA maintenance, EDI transaction, dataset family, DUNS, ISA segment, inbound, outbound, EDIServ, EDINCOMING, GPG, encryption, transaction viewer, status code, direction code
last_updated: 2026-03-03
---

# QPTM EDI Integration (EDI) - Domain Concepts

## Overview

This document explains the **business concepts** behind Electronic Data Interchange (EDI) in the QPTM system. The Web repo provides a **lightweight view** into EDI activity: transaction history viewing, trading partner configuration, and outbound file management. The **primary EDI processing** -- parsing, translation, encryption/decryption, and batch file handling -- resides in the **Quorum.QPTM.Batch** repo.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [What is EDI in QPTM?](#what-is-edi-in-qptm)
2. [Web Repo vs. Batch Repo Responsibilities](#web-repo-vs-batch-repo-responsibilities)
3. [Transaction Types and Dataset Families](#transaction-types-and-dataset-families)
4. [Trading Partner Agreements (TPA)](#trading-partner-agreements-tpa)
5. [EDI Transaction Lifecycle](#edi-transaction-lifecycle)
6. [Inbound EDI Flow](#inbound-edi-flow)
7. [Outbound EDI Flow](#outbound-edi-flow)
8. [EDI File Structure](#edi-file-structure)
9. [Security and Encryption](#security-and-encryption)
10. [Key Screens and User Functions](#key-screens-and-user-functions)
11. [Glossary](#glossary)

---

## What is EDI in QPTM?

**Electronic Data Interchange (EDI)** is the automated, computer-to-computer exchange of structured business documents between trading partners in the natural gas pipeline industry. In QPTM, EDI enables the electronic submission and receipt of nominations, confirmations, scheduled quantities, allocation data, capacity release information, and other NAESB-defined datasets between shippers, operators, and pipeline companies.

**Business Purpose:**
- Automate the exchange of pipeline transportation data between business partners
- Comply with FERC and NAESB standards for electronic communication
- Replace manual data entry with reliable, auditable electronic transactions
- Maintain a complete history of all inbound and outbound EDI communications
- Support multiple NAESB dataset families (nominations, confirmations, allocations, etc.)

**Key Business Value:**
- **Regulatory Compliance**: Meets NAESB and FERC requirements for electronic data exchange
- **Operational Efficiency**: Eliminates manual re-keying of data received from trading partners
- **Auditability**: Every EDI transaction is logged with status, timestamps, and file content
- **Reliability**: Supports primary and secondary connection endpoints for failover

---

## Web Repo vs. Batch Repo Responsibilities

The EDI functionality is intentionally split across two repositories:

| Responsibility | Web Repo | Batch Repo |
|---|---|---|
| Transaction history viewing | Yes | No |
| EDI file content viewer | Yes | No |
| Trading partner (TPA) configuration | Yes | No |
| Outbound file list monitoring | Yes | No |
| Outbound file content retrieval | Yes | No |
| File move after send (sent/error) | Yes | No |
| Inbound file save and queue | Yes (via EDIService) | No |
| TPA header record retrieval for EDIServ | Yes (via EDIService) | No |
| EDI transaction ID generation | Yes (via EDIService) | No |
| Inbound file parsing/translation | No | Yes (EDINCOMING) |
| Outbound file generation | No | Yes (QPEC) |
| GPG encryption/decryption | No | Yes |
| Batch scheduling of EDI jobs | No | Yes |
| EDI dataset translation | No | Yes |

> **Important**: For detailed documentation on EDI processing logic (EDINCOMING, QPEC, file parsing, and encryption workflows), refer to the **Quorum.QPTM.Batch** repository documentation.

---

## Transaction Types and Dataset Families

EDI transactions in QPTM are organized by **Dataset Family** codes. Each dataset family corresponds to a type of business data exchanged between trading partners.

Common dataset families include:

| Dataset Family Code | Description | Direction |
|---|---|---|
| NOM | Nominations | Inbound / Outbound |
| CONF | Confirmations | Inbound / Outbound |
| SCHED | Scheduled Quantities | Outbound |
| ALLOC | Allocations | Outbound |
| CR | Capacity Release | Inbound / Outbound |
| FA | Functional Acknowledgment (997) | Inbound / Outbound |
| INV | Invoicing | Outbound |

The `EdDatasetFamilyCode` field on the `EDTRAN_TRANSACTION` table identifies which dataset family a given transaction belongs to. Users can filter by dataset family on the EDI Transaction Viewer screen.

---

## Trading Partner Agreements (TPA)

A **Trading Partner Agreement (TPA)** defines the technical and authentication parameters for EDI communication with a specific business partner. TPA records are managed through the **TPA Maintenance** screen (EDI Serv tab).

Each TPA record includes:

- **General Settings**:
  - `PartUser` / `PartPwd` -- Basic authentication credentials
  - `NaesbVersion` -- NAESB protocol version

- **Primary Connection**:
  - `PrimDuns` -- Primary DUNS number for routing
  - `PrimIp` -- Primary server IP/hostname
  - `PrimCgiExec` -- CGI executable path
  - `PrimPort` -- Connection port
  - `PrimUser` / `PrimPwd` -- Primary connection credentials
  - `PrimUsessl` -- Whether to use SSL

- **Secondary Connection** (failover):
  - Same fields as primary (`SecIp`, `SecPort`, `SecUser`, `SecPwd`, `SecUsessl`, etc.)

- **HTTP Response Configuration**:
  - `HttpResponseExtraLines` -- Number of extra lines in HTTP response
  - `HttpResponseSignature` -- Whether response includes signature
  - `HttpResponseContentLength` -- Whether response includes content-length header

TPA records are filtered by effective dates (`EffDateFrom` / `EffDateTo`) to ensure only currently active trading partners are used for communication.

---

## EDI Transaction Lifecycle

Each EDI transaction passes through several states tracked by the `StatusCode` field:

1. **Received/Created** -- Transaction record created when a file is received (inbound) or generated (outbound)
2. **Processing** -- File is being parsed, translated, or encrypted/decrypted
3. **Completed** -- Transaction successfully processed
4. **Error** -- Transaction encountered an error during processing

Additional tracking fields:
- `TransactionDate` -- When the transaction occurred
- `DirCode` -- Direction code indicating inbound or outbound
- `IsTest` -- Flag indicating whether this is a test transaction
- `ErrorCode` -- Specific error code if the transaction failed
- `RefNo` -- Reference number for the transaction
- `ParentTransId` / `ParentRefNo` -- Links to parent transaction (e.g., a 997 FA links back to the original transaction)
- `FilePath` / `FileNm` -- Location and name of the EDI file on disk

---

## Inbound EDI Flow

1. **File Received**: An EDI file arrives from a trading partner (typically via HTTP/HTTPS)
2. **File Saved**: `EDIService.SaveEdiFile()` writes the file to the `ProcessInEncryptedPath` directory
3. **Queue for Processing**: `EDIService.QueueEdiFile()` launches the `EDINCOMING` batch process via `IQPTMBatchProcessService.LaunchEDINCOMING_EDIncomingFileHandler()`
4. **Batch Processing** (in Batch repo): EDINCOMING decrypts, parses, and translates the file into QPTM data
5. **Transaction Logged**: A record is written to `EDTRAN_TRANSACTION` with status and file information

---

## Outbound EDI Flow

1. **File Generated** (in Batch repo): QPEC creates an outbound EDI file, writing to the Decrypted, then Encrypted, then Monitor directories
2. **Monitor Check**: `EDIService.GetOutboundMonitorFileList()` retrieves the list of files in the `ProcessOutMonitorPath` directory
3. **File Retrieved**: `EDIService.GetOutboundFileContents()` reads the encrypted file content and atomically deletes the monitor file (with file locking) to prevent reprocessing
4. **File Held**: The encrypted file is moved to the `ProcessOutHoldfilesPath` directory
5. **File Sent**: External EDI communication sends the file to the trading partner
6. **Post-Send**: `EDIService.MoveSentFile()` moves the hold file to either `ProcessOutSentfilesPath` (success) or `ProcessOutErrorholdPath` (failure). If a file with the same name already exists, a timestamp suffix is appended.

---

## EDI File Structure

EDI files in QPTM follow the ANSI X12 standard format. The file viewer in the Web UI parses and displays the file content with proper segment separation.

Key structural elements:
- **ISA Segment** -- Interchange control header (first segment in every EDI file)
  - Character at position 4 is the element delimiter (typically `*`)
  - The 16th element's second character is the segment delimiter
- **GS Segment** -- Functional group header
- **ST Segment** -- Transaction set header
- **SE Segment** -- Transaction set trailer
- **GE Segment** -- Functional group trailer
- **IEA Segment** -- Interchange control trailer

The `ParseEDIFile()` method in the UI controller detects the segment delimiter from the ISA segment and replaces it with line feeds for readable display.

---

## Security and Encryption

EDI communication uses several security layers:

- **GPG Encryption**: Files are encrypted/decrypted using GPG (GNU Privacy Guard) via the `Quorum.EDI.GPGInterface` library
- **Privacy Service**: The `Quorum.EDI.PrivacyService` library handles encryption/decryption operations
- **SSL/TLS**: Trading partner connections can be configured to use SSL (`PrimUsessl` / `SecUsessl`)
- **Basic Authentication**: HTTP connections use basic auth credentials (`PartUser` / `PartPwd`)
- **File Locking**: Outbound file retrieval uses thread-safe locking (`DeleteMonitorFileWithLock`) to prevent race conditions in multi-threaded environments

---

## Key Screens and User Functions

### EDI Transaction Viewer

- **Screen Name**: `EDTransaction`
- **Security Object**: `QVPEDITRANSACTIONS` (EDITransactionViewer)
- **Purpose**: Read-only viewer for EDI transaction history
- **Features**:
  - Filter by TSP, Dataset Family, Status Code, and date range (As Of Date From / To)
  - Default date range is last 7 days
  - Grid displays transaction history sorted by transaction date (newest first)
  - Selecting a row shows the EDI file content in the EDI Viewer panel
  - Copy button copies file content to clipboard
  - Excel export of transaction history
  - No Save, Validate, All, or More buttons (read-only screen)

### TPA Maintenance -- EDI Serv Tab

- **Screen Name**: `TPAMaintenance` (EDI Serv tab)
- **Purpose**: Configure trading partner connection parameters for EDI communication
- **Sections**: General, Primary Connection, Secondary Connection, HTTP Response

---

## Glossary

| Term | Definition |
|---|---|
| **EDI** | Electronic Data Interchange -- automated exchange of structured business documents |
| **NAESB** | North American Energy Standards Board -- defines EDI standards for the natural gas industry |
| **DUNS** | Data Universal Numbering System -- unique identifier for business entities |
| **TPA** | Trading Partner Agreement -- configuration defining how to communicate with a specific partner |
| **TSP** | Transporting Service Provider -- the pipeline company |
| **Dataset Family** | Category of EDI data (e.g., NOM for nominations, CONF for confirmations) |
| **ISA Segment** | Interchange control header -- the first segment in an X12 EDI file |
| **997 / FA** | Functional Acknowledgment -- an EDI response confirming receipt of a transaction |
| **GPG** | GNU Privacy Guard -- encryption software used for EDI file security |
| **EDINCOMING** | Batch process that handles inbound EDI file processing |
| **QPEC** | Batch process that generates outbound EDI files (creates Decrypted, Encrypted, and Monitor files) |
| **Monitor File** | A marker file in the outbound monitor directory indicating a file is ready to send |
| **Hold File** | A file waiting in the holdfiles directory after retrieval but before final send confirmation |
| **Direction Code** | Indicates whether a transaction is inbound or outbound |
| **Status Code** | The processing state of an EDI transaction (e.g., received, processing, completed, error) |
| **Element Delimiter** | Character separating data elements within an EDI segment (typically `*`) |
| **Segment Delimiter** | Character separating EDI segments (varies; detected from ISA segment) |
| **EDIServ** | The external EDI communication service that reads TPA records and sends/receives files |

---

*See also: [Architecture Documentation](./architecture.md) | [Troubleshooting Guide](./troubleshooting.md)*

*Last updated: 2026-03-03*

*Document version: 1.0*
