---
name: new-skill
description: Create or update an Auto-Bot product skill — for a symptom family not yet in the knowledge base, from a just-solved case, or by mining SF/ADO history for a topic. Use for "create a skill for X", "we keep seeing this issue, capture it".
---

# /new-skill <product> <topic>

1. **Dedupe first**: `python engine/kb.py search "<topic>" --product <P> -k 8`. If an existing skill covers ≥70% of the topic, this becomes a skill UPDATE — tell the user and extend that file instead.
2. Launch `knowledge-curator` with: product, topic, and available sources (a solved case folder under `cases/`, pasted material, or an instruction to mine SF/ADO).
   - For mining runs, the curator should pull closed cases (`Status='Closed'`, `Product_list__c='<value>'`, subject/category keywords, `LIMIT 25` pages) and related ADO bugs, clustering on Quorum vocabulary (process codes/tables/error codes — not plain English).
3. The curator follows the standard 7-part skill anatomy (Quick Triage → Decision Tree → clusters → Known ADO items → Diagnostic SQL → Expected-Behavior FAQ → Escalation), updates the product's `*_Issue_Knowledge_Base.md` router, and rebuilds the index (`kb.py build --product <P>`).
4. Report to the user: skill path, router entry added, index chunk delta (`kb.py stats --product <P>` before/after).

Cross-product topics (queue triage, SF query recipes, customer-followup patterns) go to `products/_shared/skills/` — shared skills are indexed into EVERY product's KB automatically.
