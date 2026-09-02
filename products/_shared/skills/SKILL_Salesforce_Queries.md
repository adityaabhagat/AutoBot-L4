# SKILL: Salesforce Investigation Queries

**Version:** 1.0 | **Created:** 2026-05-26
**Use When:** Starting any new case investigation — Phase 1 data gathering

---

## MCP Connector
- **Prefix:** `mcp__12c9ae52-5751-4da7-b869-607f03acd2a8`
- **Primary Tool:** `soqlQuery` (for structured queries)
- **Secondary Tool:** `find` (for text search / SOSL)

---

## Phase 1: Case Retrieval

### 1A. Get Case Details
```sql
SELECT Id, CaseNumber, Subject, Description, Status, Priority,
       OwnerId, CreatedDate, ClosedDate, AccountId, ContactId,
       Resolution__c, Origin, Type
FROM Case
WHERE CaseNumber = '<CASE_NUMBER>'
```

### 1B. Get Case Attachments
```sql
SELECT Id, ContentDocumentId,
       ContentDocument.Title, ContentDocument.FileType,
       ContentDocument.ContentSize, ContentDocument.CreatedDate
FROM ContentDocumentLink
WHERE LinkedEntityId = '<CASE_ID>'
ORDER BY ContentDocument.CreatedDate DESC
```

### 1C. Get Case Comments
```sql
SELECT Id, CommentBody, CreatedDate, CreatedById
FROM CaseComment
WHERE ParentId = '<CASE_ID>'
ORDER BY CreatedDate DESC
```

### 1D. Get Case Emails
```sql
SELECT Id, Subject, TextBody, FromAddress, ToAddress,
       CreatedDate, Incoming
FROM EmailMessage
WHERE ParentId = '<CASE_ID>'
ORDER BY CreatedDate DESC
LIMIT 20
```

### 1E. Get Case Tasks
```sql
SELECT Id, Subject, Description, Status, ActivityDate,
       OwnerId, CreatedDate
FROM Task
WHERE WhatId = '<CASE_ID>'
ORDER BY CreatedDate DESC
```

---

## Phase 2: Historical Case Search

### 2A. Search by Error Code
```sql
SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate
FROM Case
WHERE (Subject LIKE '%<ERROR_CODE>%' OR Description LIKE '%<ERROR_CODE>%')
  AND CreatedDate > 2024-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 20
```

### 2B. Search by Client/TSP
```sql
SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate
FROM Case
WHERE (Subject LIKE '%<CLIENT_NAME>%' OR Subject LIKE '%<TSP_NAME>%')
  AND (Subject LIKE '%<KEYWORD>%')
  AND CreatedDate > 2023-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 20
```

### 2C. Search by Product Module
```sql
SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate
FROM Case
WHERE (Subject LIKE '%EDI%' AND Subject LIKE '%nomination%')
  AND CreatedDate > 2024-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 20
```

### 2D. Search by Error Message Text
```sql
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE Description LIKE '%<ERROR_TEXT>%'
  AND CreatedDate > 2024-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 15
```

---

## Phase 3: Account & Contact Info

### 3A. Get Account Details
```sql
SELECT Id, Name, Industry, Type
FROM Account
WHERE Id = '<ACCOUNT_ID>'
```

### 3B. Get Contact
```sql
SELECT Id, Name, Email, Phone, Title
FROM Contact
WHERE Id = '<CONTACT_ID>'
```

### 3C. Get Case Owner
```sql
SELECT Id, Name, Email
FROM User
WHERE Id = '<OWNER_ID>'
```

---

## Common Search Patterns

### EDI Issues
```sql
-- All EDI-related cases for a client
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE (Subject LIKE '%EDI%' OR Subject LIKE '%NMST%' OR Subject LIKE '%NMQR%')
  AND (Subject LIKE '%<CLIENT>%' OR Subject LIKE '%<TSP>%')
ORDER BY CreatedDate DESC
LIMIT 20

-- ENMQR error cases
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE (Subject LIKE '%ENMQR%' OR Description LIKE '%ENMQR%')
ORDER BY CreatedDate DESC
LIMIT 20
```

### Nomination Issues
```sql
-- Nomination validation errors
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE (Subject LIKE '%nomination%' AND
       (Subject LIKE '%error%' OR Subject LIKE '%validation%' OR Subject LIKE '%BI%' OR Subject LIKE '%LI%'))
ORDER BY CreatedDate DESC
LIMIT 20

-- Late nomination / retroactive
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE (Subject LIKE '%late nomination%' OR Subject LIKE '%retroactive%'
       OR Subject LIKE '%ENMQR315%' OR Subject LIKE '%cycle%indicator%')
ORDER BY CreatedDate DESC
LIMIT 20
```

### MDQ / Quantity Issues
```sql
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE (Subject LIKE '%MDQ%' OR Subject LIKE '%shared MDQ%'
       OR Subject LIKE '%ENMQR504%' OR Subject LIKE '%quantity%exceed%')
ORDER BY CreatedDate DESC
LIMIT 20
```

### Contract / Location Issues
```sql
SELECT Id, CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE (Subject LIKE '%contract%' AND (Subject LIKE '%invalid%' OR Subject LIKE '%locked%'))
  OR Subject LIKE '%ENMQR301%' OR Subject LIKE '%ENMQR525%'
ORDER BY CreatedDate DESC
LIMIT 20
```

---

## Tips

1. **SOQL LIKE is case-insensitive** — `LIKE '%edi%'` matches "EDI", "edi", "Edi"
2. **Use CreatedDate filter** to limit results — SF has row limits
3. **LIMIT clause is important** — prevent timeout on large result sets
4. **Description field** may not be indexed — queries on it can be slow
5. **ContentDocumentLink** is the way to get attachments (not the old Attachment object)
6. **FeedItem** requires filtering by ParentId — can't query all feed items
7. **Use `find` tool for SOSL** when you need cross-object text search

---

## Salesforce Object Schema Discovery

When you encounter unknown fields or need to find what's available:
```
Use: mcp__12c9ae52-5751-4da7-b869-607f03acd2a8__getObjectSchema
With object name: Case, Account, Contact, etc.
```

This returns all fields on the object including custom fields (`__c` suffix).
