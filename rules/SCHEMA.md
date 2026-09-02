# Auto-Bot Lite — Rule / SQL-pack / Recipe Schema

> The binding contract between the rule tables and `autobot.py`. Anything outside this schema is ignored by the engine. Part of Auto-Bot by Aditya Bhagat.

## 1. Rules — `rules/<PRODUCT>.yaml`

```yaml
product: QPTM
rules:
  - id: QPTM-BILL-041            # unique, <PRODUCT>-<AREA>-<NNN>
    gate: G5                     # G1 | G2 | G3 | G4 | G5
    priority: 10                 # optional; lower runs first within its gate (default 100)
    match:                       # a rule fires when: all of `all`, ≥1 of `any` (if present), none of `none`
      all: ["SQL 208", "BLSTAG_PAL_EXT"]
      any: []
      none: []
    batch: NORMAL                # optional: NORMAL | SEGREGATED — sets the batch flag when fired
    sql_pack: pal_ext_missing    # optional: sqlpacks/<PRODUCT>/<name>.yaml (verification step)
    recipe: deploy_blstag_pal_ext# optional: recipes/<PRODUCT>/<name>.md (known fix)
    verdict: "CORE table BLSTAG_PAL_EXT dropped by 3.1.00.0069 while invoice generation still joins it — no PEX billing line for {contract}"
    source: "SKILL_Billing.md §4.4"    # mandatory audit anchor (skill file + section)
    ado_refs: ["1836277"]        # optional ADO ids
```

Match term semantics (evaluated against subject + description + comments + emails + extracted log lines, case-insensitive):
- plain string → substring match
- `/…/` delimited → regex (Python `re`, IGNORECASE)

Rule quality bar (compiler agents MUST follow):
- Only signatures with **distinctive matchable strings** — error codes, table names, process codes, exact message fragments. No vague word matches ("error", "issue", "slow" alone are forbidden in `all`/`any` unless paired with a distinctive term via `all`).
- Every rule cites its `source` skill section; rules without a source are rejected.
- `verdict` is one sentence; `{placeholders}` allowed: {contract} {invoice} {tsp} {prod_mth} {client} {process} {pqid} {table} {error_code}.

## 2. SQL packs — `sqlpacks/<PRODUCT>/<name>.yaml`

```yaml
name: pal_ext_missing
product: QPTM
queries:
  - id: q1
    sql: "SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT') AS obj_id"
    proves: "whether the PAL staging table exists in this DB"
    interpret:
      - when: "rows[0].obj_id is null"
        verdict: CONFIRMED
        meaning: "object missing — structural defect"
      - when: "rows[0].obj_id is not null"
        verdict: FALLTHROUGH
        meaning: "object present — this rule does not apply, keep evaluating"
```

- Placeholders in `sql`: {tsp} {prod_mth} {contract} {invoice} {pqid} {client} — substituted from extracted entities; a query whose placeholder has no value is skipped with a note.
- SELECT-only. The engine refuses to run anything containing INSERT/UPDATE/DELETE/DROP/ALTER/EXEC.
- `when` DSL — ONLY these forms are understood (anything else = query runs but is reported "manual interpretation needed"):
  - `rowcount == 0` · `rowcount > 0` · `rowcount >= N`
  - `rows[0].<col> is null` · `rows[0].<col> is not null`
  - `rows[0].<col> == <number|'string'>` · `rows[0].<col> >= <number>` · `rows[0].<col> <= <number>`
- `verdict` values: `CONFIRMED` (rule's root cause proven) | `REFUTED` (rule wrong — engine falls through to next rule) | `FALLTHROUGH` (same as refuted, softer) | `INFERRED` (supporting but not decisive).

## 3. Recipes — `recipes/<PRODUCT>/<name>.md`

Markdown with the same {placeholders}. Required sections:
```markdown
# Fix: <title>
## Steps            (numbered, operator-ready; scripts in ```sql blocks)
## Verification     (query/steps proving the fix took)
## Workaround       (customer-usable until the fix lands; plain language)
## Source           (skill §, case ids, ADO ids)
```

## 4. Engine behavior guarantees

- Gate ladder order: G1 → G2 → G3 → G4 → G5, priority ascending within a gate; first rule that fires AND survives its sql_pack (no REFUTED/FALLTHROUGH) wins.
- No rule fired → outcome NOVEL → investigation packet (never a guessed answer).
- DB unreachable → sql_pack emitted as `NOT YET RUN`; the rule may still win but its confidence caps at INFERRED.
- Every report line carries: rule id, source skill §, SQL results or NOT YET RUN, record ids.
