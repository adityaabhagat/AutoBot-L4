# Onboarding a New Product into Auto-Bot

> Auto-Bot by Aditya Bhagat. QPTM is fully onboarded; TIPS and QDO came pre-loaded from sibling projects. This doc holds the **copy-paste prompts** to bring any other product (QLS, QRD, QRA, QCA, QCFS, …) to the same level.

## Current state

| Product | Skills | Router | Index | Missing |
|---|---|---|---|---|
| QPTM | 23 + 3 shared | ✅ QPTM_Issue_Knowledge_Base.md | ✅ built (skills + knowledge + code cache) | — |
| TIPS | 24 | ✅ TIPS_Issue_Knowledge_Base.md | ✅ built (incl. crude code cache + config reference) | Product_list__c literal TBD |
| QDO | 4 | ⬜ (upstream router copied in) | ✅ built | per-category mining, PRODUCT.md vocabulary growth |
| QLS | 0 | ⬜ | ✅ built (shared skills + PRODUCT.md + upstream repo ref only) | everything (integration touchpoints listed in PRODUCT.md) |
| QRD | 0 | ⬜ | ✅ built (shared skills + PRODUCT.md only) | everything |

## Phase prompts — run these in Auto-Bot, one at a time

### Phase 0 — Scaffold + identity
```
/onboard-product <CODE>
Then: query Salesforce for the exact Product_list__c value:
SELECT Product_list__c, COUNT(Id) FROM Case WHERE Product_list__c LIKE '%<product name fragment>%' GROUP BY Product_list__c
Record the literal in products/<CODE>/PRODUCT.md and in the products table of CLAUDE.md.
```

### Phase 1 — Case-landscape survey (what does this product's support load look like?)
```
Using the Salesforce server, profile the last 24 months of closed <CODE> cases:
count by Case_Category__c and Root_Cause__c (LIMIT 25 per query, aggregate queries preferred).
Produce a coverage plan: the 8–14 category groups that would cover ~90% of actionable cases
(actionable = Root_Cause__c IN ('Software Defect','Application Configuration')).
Save as products/<CODE>/knowledge/<CODE>_Coverage_Plan.md. Do not write skills yet.
```

### Phase 2 — Per-category skill mining (repeat per category from the plan)
```
/new-skill <CODE> <category>
Mine closed Salesforce cases for category "<category>" (SOQL by Case_Category__c + subject keyword clusters;
pull Description + CaseComments + EmailMessages of resolved twins for fix detail).
Cluster on product vocabulary (process codes, table prefixes, screen acronyms), not plain English.
Build the skill with the standard 7-part anatomy; every claim cites SF case ids.
```

### Phase 3 — ADO defect mining
```
Mine Azure DevOps for <CODE> defects: WIQL on the product's Area Path
(find it via: SELECT [System.AreaPath] samples from known <CODE> bugs; upstream products live under
QuorumSoftware\Engineering\Financials). For each major defect cluster: root cause, PR, fixed-in build
(label INFERRED unless in ReleaseNotes). Save as products/<CODE>/skills/SKILL_ADO_<CODE>_<Cluster>.md
+ a <CODE>_ADO_Defect_Index.md in knowledge/.
```

### Phase 4 — Repo + config reference
```
Build products/<CODE>/knowledge/code_logic/REPO_REFERENCE_<CODE>.md: list ADO repos matching
Quorum.<CODE>.* and <CLIENT>.<CODE>.* (mcp__ado__repo_repository), map modules to repos/hotspot paths,
note the client-override-first rule. Then knowledge/config_logic/CONFIG_REFERENCE_<CODE>.md:
where config lives (table/scopes), per-module key tables using the 6-column format from
products/QPTM/knowledge/config_logic/CONFIG_REFERENCE.md.
```

### Phase 5 — Router + vocabulary + index
```
Create products/<CODE>/knowledge/<CODE>_Issue_Knowledge_Base.md (symptom→skill router + coverage map,
pattern: products/QPTM/knowledge/QPTM_Issue_Knowledge_Base.md). Fill PRODUCT.md vocabulary table
(process codes, table prefixes, screens, error-code patterns) from the mined skills.
Then: python engine/kb.py build --product <CODE>, and verify with 3 searches on top error codes.
```

### Phase 6 — Smoke test
```
/intake <a real recent case number for the product>
Verify: product detected correctly, KB recall returns relevant hits, brief is complete.
Then /solve-case it and review the graph's gate choice manually — first case per product gets human review.
```

## Product-specific head starts

- **QLS (Quorum Land System):** no dedicated knowledge exists yet, but integration touchpoints are documented in upstream skills — PUBBA BA-publish (`Quorum.ESuite.Integration.QLS`, QCFS Platform_Security §7), QLS→AP land-payment invoice imports (QCFS Accounts_Payable, Cluster C), GL013 DATAPUBLISH `QLS`/`QLandDataHelper` connections (QCFS General_Ledger), client repos `<CLIENT>.QLS.ESuite.Database`. Start Phase 1 there.
- **QRD:** zero existing knowledge anywhere in the Projects tree — pure Phase 0→6 run. Confirm the official product name/Product_list__c with the team before mining.
- **QRA / QCA / QCFS:** 23 SF-mined + 9 ADO-mined skills already exist in `…\Claude\Projects\Upstream Assistant` and `Upstream ADO Assistant` — copying them (as done for QDO) replaces Phases 1–3 entirely.
