---
name: onboard-product
description: Onboard a new Quorum product into Auto-Bot — scaffold its folders, PRODUCT.md, and knowledge categories, then run the knowledge-mining prompts to build its skills and vector index. Use for "add QLS to Auto-Bot", "set up QRD".
---

# /onboard-product <CODE>

Follow `docs/ONBOARD_NEW_PRODUCT.md` (the authority, with copy-paste mining prompts). Summary:

1. **Scaffold** — create `products/<CODE>/{skills,knowledge/<11 categories>,past_cases,kb_index}` (mirror `products/_template/`), and `PRODUCT.md` from the template.
2. **Identify** — first SF case or SOQL sweep to discover the product's `Product_list__c` literal; record it in `PRODUCT.md` AND the products table in root `CLAUDE.md`.
3. **Harvest what exists** — check the sibling Claude Projects folders (`Upstream Assistant`, `* ADO Assistant`) and any team docs for ready skills; copy them in (that's how QDO started with 4).
4. **Mine** — run the phase prompts from `docs/ONBOARD_NEW_PRODUCT.md`: SF closed-case mining → per-category skills; ADO defect mining → SKILL_ADO_* files; repo reference; config reference; vocabulary table.
5. **Index** — `python engine/kb.py build --product <CODE>`; verify with a search for the product's top error code.
6. **Smoke test** — `/intake` one real case; confirm product detection and KB recall fire.

The product is "onboarded" when: PRODUCT.md complete, ≥1 skill per major case category, router file exists, index built, one real case briefed.
