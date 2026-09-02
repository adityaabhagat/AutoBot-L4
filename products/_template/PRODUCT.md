# PRODUCT — <CODE> (<full name>)

| | |
|---|---|
| **Code** | <CODE> |
| **Salesforce `Product_list__c`** | <exact literal — discover via ONBOARD Phase 0> |
| **Domain** | <one-line business domain + the main workflow chain> |
| **UI stack** | <Web/Classic/portal notes> |
| **Knowledge status** | SCAFFOLD → PARTIAL → FULL |

## Vocabulary table (drives product detection + KB queries — keep current)

| Kind | Terms |
|---|---|
| Batch/process codes | |
| Table prefixes | |
| Error-code patterns | |
| Screens/concepts | |

## Routing rules

- Router: `knowledge/<CODE>_Issue_Knowledge_Base.md` (symptom→skill table).
- Repos: `knowledge/code_logic/REPO_REFERENCE_<CODE>.md` — client overrides `<CLIENT>.<CODE>.*` FIRST.
- Config: `knowledge/config_logic/CONFIG_REFERENCE_<CODE>.md`.
- Batch engine notes: <QPEC? segregated processes? log locations?>
- Triage priors: <Root_Cause__c patterns, category distributions from the coverage plan>

## Knowledge categories (`knowledge/`)

business_logic · functional_logic · code_logic · screen_logic · config_logic · metadata_logic · table_logic · module_logic · domain_logic · architecture_logic · steps_to_reproduce
