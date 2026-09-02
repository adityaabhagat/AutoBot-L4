---
name: lite-solve
description: Run Auto-Bot Lite (the deterministic no-LLM pipeline) on a Salesforce case. Claude does ONLY data plumbing — fixed MCP queries dumped to raw JSON, then autobot.py decides everything. Use for fast, cheap, auditable solving of known symptom families (e.g. /lite-solve 26-01106039).
---

# /lite-solve <CASE_NUMBER>

You are a data pipe, not an investigator. Do NOT analyze, classify, or interpret the case — `autobot.py` does that deterministically. Your only judgment calls are query mechanics.

## Step 1 — Dump raw data to `cases/<CASE>/raw/`

Using the Salesforce connector (`soqlQuery`), run these fixed queries and save results as JSON (create the folders):

1. `raw/case.json` — the single record from:
   `SELECT Id, CaseNumber, Subject, Description, Status, Priority, Product_list__c, Root_Cause__c, Case_Category__c, Azure_DevOps_Module__c, Resolution__c, CreatedDate, Account.Name FROM Case WHERE CaseNumber='<CASE>'`
   (not found → stop, tell the user)
2. `raw/comments.json` — array from: `SELECT CommentBody, CreatedDate, CreatedBy.Name FROM CaseComment WHERE ParentId='<ID>' ORDER BY CreatedDate LIMIT 25`
3. `raw/emails.json` — array from: `SELECT Subject, TextBody, FromAddress, CreatedDate FROM EmailMessage WHERE ParentId='<ID>' ORDER BY CreatedDate LIMIT 25`
4. `raw/similar.json` — array from a Subject-keyword sweep (2 strongest distinctive terms from the subject, verbatim): `SELECT CaseNumber, Subject, Status, Root_Cause__c FROM Case WHERE Subject LIKE '%<kw>%' AND Product_list__c='<value from case>' ORDER BY CreatedDate DESC LIMIT 25`
5. `raw/ado.json` — array of work items: `mcp__ado__wit_query` (WIQL CONTAINS on the case number, plus each error-code-looking token you can literally see in the subject/description — copy tokens verbatim, do not invent). For each hit include: id, title, state, tags, iteration, description (first 2000 chars).
6. `raw/attachments/` — list case ContentDocuments; download ONLY `.txt`/`.log`/`.csv` ones (≤5, one at a time) as text files. Binary files: skip, but append their names to `raw/attachments/_skipped.txt`.

Formatting rule: save records as plain JSON arrays/objects (strip SF `attributes` keys). No summaries, no edits, no omissions beyond the stated limits.

## Step 2 — Run the engine

```
python autobot.py solve <CASE>
```
(add `--env <ENV>` if the user named a client DB environment; `--offline` if they said no DB)

## Step 3 — Relay

Read the report file the engine printed and show the user:
- the engine's stdout lines (product, signals, rule fired or NOVEL),
- the report path,
- the report's classification + root-cause + fix section VERBATIM (do not rephrase, do not add your own analysis).
If the outcome is NOVEL, mention the near-miss rules and offer: full agent graph via `/solve-case <CASE>`, or `python autobot.py learn <CASE>` after a human solves it.
