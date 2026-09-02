# SKILL: Salesforce Investigation Queries — TIPS

**Use When:** Starting any new TIPS case investigation — Phase 1 data gathering and historical search.

## MCP Connector
- **Prefix:** `mcp__12c9ae52-5751-4da7-b869-607f03acd2a8`
- **Primary:** `soqlQuery` · **Text search:** `find` (SOSL) · **Schema discovery:** `getObjectSchema`

---

## Phase 1: Case Retrieval

### 1A. Case details
```sql
SELECT Id, CaseNumber, Subject, Description, Status, Priority,
       OwnerId, CreatedDate, ClosedDate, AccountId, Account.Name,
       ContactId, IsEscalated, Resolution__c, Origin, Type
FROM Case WHERE CaseNumber = '<CASE_NUMBER>'
```

### 1B. Attachments
```sql
SELECT Id, ContentDocumentId, ContentDocument.Title, ContentDocument.FileType,
       ContentDocument.ContentSize, ContentDocument.CreatedDate
FROM ContentDocumentLink WHERE LinkedEntityId = '<CASE_ID>'
ORDER BY ContentDocument.CreatedDate DESC
```

### 1C. Comments
```sql
SELECT Id, CommentBody, CreatedDate, CreatedById
FROM CaseComment WHERE ParentId = '<CASE_ID>' ORDER BY CreatedDate DESC
```

### 1D. Emails
```sql
SELECT Id, Subject, TextBody, FromAddress, ToAddress, CreatedDate, Incoming
FROM EmailMessage WHERE ParentId = '<CASE_ID>' ORDER BY CreatedDate DESC LIMIT 20
```

---

## Phase 2: Historical Case Search (TIPS themes)

### By client + module
```sql
SELECT CaseNumber, Subject, Status, Priority, CreatedDate
FROM Case
WHERE Account.Name LIKE '%<CLIENT>%'
  AND (Subject LIKE '%<KEYWORD>%')
  AND CreatedDate > 2024-01-01T00:00:00Z
ORDER BY CreatedDate DESC LIMIT 20
```

### By TIPS module keyword (pick the relevant block)
```sql
-- Measurement / Meter Definitions / FLOWCAL
WHERE Subject LIKE '%meter def%' OR Subject LIKE '%FLOWCAL%' OR Subject LIKE '%measurement%'

-- Inventory & imbalance
WHERE Subject LIKE '%inventory%' OR Subject LIKE '%imbalance%' OR Subject LIKE '%ending oil%'

-- Allocation
WHERE Subject LIKE '%allocat%'

-- Contracts & rates
WHERE Subject LIKE '%contract rate%' OR Subject LIKE '%contractual UOM%' OR Subject LIKE '%rate%'

-- Statements & settlements
WHERE Subject LIKE '%statement%' OR Subject LIKE '%settlement%'

-- Crude truck/batch tickets & terminals
WHERE Subject LIKE '%truck ticket%' OR Subject LIKE '%batch ticket%' OR Subject LIKE '%terminal%'

-- Org hierarchy / screen errors
WHERE Subject LIKE '%hierarchy%' OR Subject LIKE '%organization%'

-- EDI
WHERE Subject LIKE '%EDI%'

-- SAP
WHERE Subject LIKE '%SAP%'

-- Access / refresh / deploy (operational, not code)
WHERE Subject LIKE '%Okta%' OR Subject LIKE '%refresh%' OR Subject LIKE '%add%user%' OR Subject LIKE '%deploy%'
```
Wrap any block with: `SELECT CaseNumber, Subject, Status, Priority, CreatedDate FROM Case WHERE (<block>) AND CreatedDate > 2024-01-01T00:00:00Z ORDER BY CreatedDate DESC LIMIT 20`

### By error text in description
```sql
SELECT CaseNumber, Subject, Status, CreatedDate
FROM Case WHERE Description LIKE '%<ERROR_TEXT>%'
  AND CreatedDate > 2024-01-01T00:00:00Z ORDER BY CreatedDate DESC LIMIT 15
```

---

## Phase 3: Account / Contact / Owner
```sql
SELECT Id, Name, Industry, Type FROM Account WHERE Id = '<ACCOUNT_ID>'
SELECT Id, Name, Email, Phone, Title FROM Contact WHERE Id = '<CONTACT_ID>'
SELECT Id, Name, Email FROM User WHERE Id = '<OWNER_ID>'
```

---

## Tips
1. SOQL `LIKE` is case-insensitive.
2. Always include a `CreatedDate` filter and `LIMIT` to avoid row limits/timeouts.
3. `Description` may be unindexed → those queries can be slow; prefer `Subject` filters first.
4. Use `getObjectSchema` on `Case` to find TIPS product/environment custom fields (`__c`) — many TIPS orgs tag the product/instance, which beats keyword guessing.
5. Map `Account.Name` → client code early (see REPO_REFERENCE.md) so SF history and ADO/code line up.
6. Use the `find` tool (SOSL) when you need cross-object text search across Case + EmailMessage + comments.
