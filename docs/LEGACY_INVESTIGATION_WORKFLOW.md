# L4 Case Investigation Workflow

How I investigate an issue once you hand me a **Salesforce Case number**.

---

## At a glance

```
Salesforce Case #
      │
  [0] Search the vector knowledge base    →  python kb.py search "..." -k 8
      │                                       (find the recipe first)
  [1] Retrieve the case from Salesforce   →  soqlQuery + curl VersionData
      │                                       (fields, comments, emails, attachments,
      │                                        similar historical cases)
  [2] Classify the issue
      │   Configuration · Data · Code Defect · Enhancement · Expected Behavior
      │
  [3] Azure DevOps investigation          →  WIQL + work item batch
      │                                       (work items by case/error, linked PRs,
      │                                        which build has the fix)
  [4] Code root-cause analysis            →  ADO code search + get file
      │                                       (trace error → rule → service → EDI;
      │                                        pin exact file + line vs. live source)
  [5] Write the investigation report      →  append to L4 investigation.md
                                              (short, hypothesis-ranked, evidence-based)
```

Throughout every phase I pull the matching `SKILL_*` file for the symptom
(EDI Troubleshooting, Cycle Deadline, Nomination Validation, …).

---

## Step 0 — Knowledge base first (before any API call)

Search the local vector KB. It already indexes every skill, past investigations,
config/repo references, and cached source code — so a strong hit often points
straight to a resolution recipe from a past case, and I know what I'm looking for
before I ever touch SF or ADO.

```bash
python kb.py search "<symptom / error code / table / process>" -k 8
```

Use Quorum-specific vocabulary (process codes like `ALALLOCATE`/`BLINVGEN`,
error codes like `ENMQR315`, tables like `QTRAN_*`/`NNCTRL_*`) — that's what the
index discriminates on.

---

## Phase 1 — Retrieve the case from Salesforce

Tool: `soqlQuery` (+ `sf org display` token + curl for attachment binaries)

- **Core fields:** Subject, Description, Status, Priority, Owner, CreatedDate,
  Account, Resolution
- **Attachments** via `ContentDocumentLink` → then download the actual binaries
  (screenshots, EDI files, logs) from `VersionData` and analyze them
- **Case comments / feed items / linked emails**
- **Similar historical cases** — a second SOQL sweep by subject keywords, same
  account, and same error code

```sql
SELECT Id, CaseNumber, Subject, Description, Status, Priority, OwnerId,
       CreatedDate, AccountId, Resolution__c
FROM Case WHERE CaseNumber = '<CASE_NUMBER>'
```

---

## Phase 2 — Classify the issue

Bucket the case into one of five. This decides where the investigation goes next.

| Bucket | Meaning |
|--------|---------|
| **Configuration** | Wrong setup in DB tables, missing config, incorrect deadline/rule setup |
| **Data** | Corrupt or missing records, orphaned references |
| **Code Defect** | Bug in application code requiring a code fix |
| **Enhancement** | Feature gap / new functionality needed |
| **Expected Behavior** | System working as designed — user education needed |

---

## Phase 3 — Azure DevOps investigation

Tool: ADO MCP (WIQL + work item batch)

- WIQL search for work items by case number, error codes, keywords
- For any linked bug/feature: full details, comments, linked PRs, and **which
  build/version contains the fix**
- Search related historical work items

> **Note:** when a fixed-in-build value comes from ADO iteration/tags rather than
> release notes, I flag it as **inferred** so it isn't quoted to a customer as
> confirmed.

---

## Phase 4 — Code root-cause analysis

Tool: ADO Code Search + file fetch

- Use `REPO_REFERENCE.md` to pick the right repo(s)
- Trace the execution path: **error code → validation rule → service logic → EDI dataset**
- Root-cause down to **exact file and line numbers**, verified against live source
  (not memory)

Common patterns:
- Error codes → `QCODE_*` tables or `Constants.cs`
- Validation rules → `*ValidationRules*` folders, `RuleNN*` naming
- EDI → `*.EDI.DataSets/G873NMST/` (inbound) and `G874NMQR/` (outbound)
- Service logic → `*.ServiceCore*/` folders
- Client overrides → `<CLIENT>.QPTM.Web` repos

---

## Phase 5 — Write the report

Append a **short, hypothesis-ranked, evidence-based** investigation to
`L4 investigation.md` (never overwrite prior cases).

Each write-up references exact code lines, ADO items, and SF case data, with
possible root causes ranked by probability.

---

## Boundaries worth knowing

- **Attachment binaries** are retrievable (SF token + curl on `VersionData`), so
  screenshots / EDI / logs get analyzed, not just listed.
- **Fixed-in-build** values from iteration/tags are marked **inferred** until
  confirmed in release notes.
