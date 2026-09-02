# Auto-Bot Lite — Detailed Workflow (No-LLM Edition)

> **Built by Aditya Bhagat** · Quorum Business Solutions
> Hackathon-safe variant of Auto-Bot: a deterministic pipeline that solves known L4 symptom families with **zero LLM calls and no third-party AI services**. All intelligence lives in rule tables, SQL packs, and recipes mined from solved-case history. Shares the same folder structure, vector KB, and templates as full Auto-Bot.

```
python autobot.py solve <CASE_NUMBER> [--product P] [--env <DB_ENV>]
```

Pipeline: **fetch → recall → rule-classify → diagnose → resolve → report → remember**

---

## Stage 0 — Input & configuration

| Item | Detail |
|---|---|
| Entry | Single CLI: `autobot.py solve <case#>` |
| Config | `config.ini`: Salesforce credentials, ADO PAT, client→DB-environment map (from `QuorumMetadataMCP/dbconfig.json`) |
| Client DB selection | `--env` flag wins; else client→env map; ambiguous → print candidates, ask operator |
| Dependencies | Python stdlib + `requests` + `pyodbc` + scikit-learn (or hand-rolled TF-IDF if libraries are restricted). No AI/LLM dependency anywhere. |

## Stage 1 — FETCH (fixed REST queries, no interpretation)

**1a. Salesforce REST** (company's own org):
- Case core: `Subject, Description, Status, Priority, Product_list__c, Root_Cause__c, Case_Category__c, Account.Name, CreatedDate` by CaseNumber. Not found → exit with message.
- CaseComments + EmailMessages (`LIMIT 25` each, chronological).
- Attachment list; download only text-parseable types (`.log .txt .csv`) — binaries are listed, not read.

**1b. Product detection (deterministic):**
1. `Product_list__c` dictionary: `My Quorum Gas Pipeline`→QPTM · `My Quorum TIPS`→TIPS · `My Quorum Division Order`→QDO · `My Quorum Land`→QLS.
2. Blank/unknown → regex scan of case text against each `products/<P>/PRODUCT.md` vocabulary table; highest hit count wins (ties → ask operator).

**1c. Signal extraction (regex library, per product):**
- Error codes: `ENMQR\d{3}`, `EEDM1\d\d`, `SQL \d+`, `ORA-\d+`, `Rule[A-Z]{2}\d+`, `Invalid object name '(\w+)'`
- Tables: `[A-Z]+(_[A-Z0-9]+)+` filtered by known prefixes (NNCTRL_, BLSTAG_, QTRAN_, PACTRL_, …)
- Process codes: dictionary match (BLINVGEN, ALALLOCATE, PANIGHTLY, SETTLEMAIN, POSTWKFL, …)
- Entities: contract `K#`/`\d+\.\d+`, invoice no, TSP no, PQID, gas day / prod month dates

**1d. ADO REST**: WIQL `CONTAINS` on case number + each error code → work item state, tags, iteration, linked PR merge targets. **1e. Similar cases**: SOQL `Subject LIKE` on the 2 strongest signals + product filter.

**Output:** `cases/<CASE>/case_brief.json` — every fact carries its source record ID.

## Stage 2 — RECALL (TF-IDF vector KB — already non-LLM)

- 3 query variants from extracted signals: error-led, table-led, process-led → `engine/kb.py search --product <P> -k 8` each; merge + dedupe.
- Thresholds: **≥ 0.25 on a past-case report = precedent found** (load its recipe reference) · 0.15–0.25 = strong skill lead · < 0.05 = ignore.
- **Output:** `recall.json` (ranked: score, file, section).

## Stage 3 — RULE CLASSIFY (gate ladder as literal if/elif)

Rules compiled from mined skills into `rules/<PRODUCT>.yaml`:
```yaml
- id: QPTM-BILL-041
  gate: G5
  match: { all: ["SQL 208", "BLSTAG_PAL_EXT"] }     # any:/all: of regex/literals
  sql_pack: pal_ext_missing                          # optional verification
  recipe: deploy_blstag_pal_ext                      # optional known fix
  source: SKILL_Billing.md §4.4                      # audit anchor
```
- **Strict cheapest-first evaluation:** all G1 rules → G2 → G3 → G4 → G5. First fired rule wins; its `id` + `source` go into the report (the no-LLM audit anchor).
- **Priors:** `Root_Cause__c` = Customer Error/Training → G1 bias; = Software Defect → skip G1.
- **Batch subroutine** (when a process code matches the batch dictionary): PQID/status query + first-`ERROR`-line regex over log attachments → extracted first error is re-fed through the rules. Segregated processes (POSTWKFL, BKRVNU, GMASLDVOLS) get the QPEC checklist pack (service up, backlog depth, CommandTimeout after patch).
- **G3 logic:** matched ADO bug Closed/Resolved with fixed-in build → version tuple compare vs client build → "fixed in X, upgrade" verdict (build labeled INFERRED unless from ReleaseNotes).
- **No rule fires → gate = NOVEL.**

## Stage 4 — DIAGNOSE (SQL packs with declared interpretations)

`sqlpacks/<PRODUCT>/<pack>.yaml` — parameterized read-only queries, each with a machine-checkable meaning table:
```yaml
- query: "SELECT OBJECT_ID('dbo.{table}')"
  interpret:
    - when: "value IS NULL"   → "object missing — structural defect CONFIRMED"
    - when: "value NOT NULL"  → "object present — fall through to next rule"
- query: "SELECT COUNT(*) FROM BLTRAN_INVOICE_GEN_QTY WHERE CHARGE_BASIS_CD='PEX' AND TSP_NO={tsp} AND PROD_MTH='{month}'"
  interpret:
    - when: "count = 0 AND ppa_events > 0" → "billing line never written — chain break CONFIRMED"
```
- Executed via `pyodbc` (Windows auth) against the selected env. Interpretation ONLY by declared conditions (rowcounts, null checks, thresholds, ratios) — no free-form judgment.
- DB unreachable → pack emitted verbatim, labeled `NOT YET RUN`, run continues (graceful degradation).

## Stage 5 — RESOLVE (the fork)

| Path | Condition | Output |
|---|---|---|
| **Known symptom** (auto-solved) | rule fired AND (no pack needed OR pack interpretation matched) | `recipes/<PRODUCT>/<name>.md` filled with real case entities: fix steps, verification SQL, customer workaround |
| **Novel symptom** (human handoff) | gate = NOVEL, or pack contradicted the rule | **Investigation packet**: brief + top KB hits + near-miss rules (what almost fired, what was missing) + all SQL results + SF/ADO links |

## Stage 6 — REPORT (template slot-filling)

- Existing `templates/` skeletons; string templating only.
- Confidence is mechanical: `CONFIRMED` = declared SQL interpretation matched OR ADO fixed-in compared; else `INFERRED`. `NOT YET RUN` can never back CONFIRMED.
- Classification line carries rule IDs + skill sources; footer: *"Investigated by Auto-Bot Lite — built by Aditya Bhagat."*

## Stage 7 — REMEMBER (growth loop)

- `python engine/kb.py remember --product <P> cases/<CASE>/report_*.md` (archive + reindex).
- Novel case solved by a human → `autobot.py learn <case#>` scaffolds a new rule + recipe from the case's extracted signals; operator reviews and commits. The handoff path shrinks with every solved case.

---

## Worked example — real case 26-01106039 (EQT, QPTM)

1. FETCH: case pulled; product = QPTM (`My Quorum Gas Pipeline`); regex extracts `SQL 208`, `BLSTAG_PAL_EXT`, `BLINVGEN`, contract `1269.2278`, TSP 24.
2. RECALL: past-case report scores 0.31 → precedent found.
3. CLASSIFY: rule `QPTM-BILL-041` fires (all: SQL 208 + BLSTAG_PAL_EXT) → G5.
4. DIAGNOSE: `OBJECT_ID('dbo.BLSTAG_PAL_EXT')` returns NULL on EQC → CONFIRMED.
5. RESOLVE: recipe `deploy_blstag_pal_ext` filled (deploy object per WI 1836679 precedent, rerun "Run All PPAs" May 2026→current TSP 24/241, reverse manual LGAs).
6. REPORT: L4 Triaged doc, anchors = rule ID + SQL result + ADO Bug 1836277. Runtime: seconds. LLM calls: zero.

## What Lite cannot do (by design)

- No novel root-cause reasoning (new defects → human packet, not an answer).
- No free-text understanding beyond keywords/TF-IDF.
- No automatic skill authoring (rules are human-committed via `learn`).

## Folder layout (additions to the existing Auto-Bot tree)

```
Auto-Bot/
├── autobot.py            # the pipeline CLI
├── rules/<PRODUCT>.yaml  # gate-ladder rule tables (compiled from skills)
├── sqlpacks/<PRODUCT>/   # diagnostic queries + declared interpretations
├── recipes/<PRODUCT>/    # known-fix templates
└── (reuses) engine/kb.py · templates/ · products/ KB · cases/
```
