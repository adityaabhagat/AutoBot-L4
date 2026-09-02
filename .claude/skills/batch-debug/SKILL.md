---
name: batch-debug
description: Debug a Quorum batch process directly (stuck, failed, wrong results) — normal batch runs or segregated QPEC processes — without a full case investigation. Use for "ALALLOCATE failed", "records stuck in Post Pending", "POSTWKFL not draining", etc.
---

# /batch-debug <process-or-symptom> [product]

1. If the product is not given, infer it from the process code via `products/*/PRODUCT.md` vocabulary (ALALLOCATE/PANIGHTLY/BLINVGEN→QPTM; SETTLEMAIN/GMASLDVOLS/QPEC+TIPS terms→TIPS; POSTWKFL/BKRVNU→upstream products); ask if genuinely ambiguous.
2. Launch the `batch-debugger` agent with what you know (process code, symptom, product, any PQID/log lines the user pasted).
3. Relay its finding: batch family (NORMAL vs SEGREGATED), failure mode with first-error evidence, and the underlying gate (config/data/version/code/expected).
4. If the user wants the underlying cause chased: launch the corresponding investigator agent, then `hallucination-checker` on its verdict before presenting conclusions. If this belongs to a Salesforce case, recommend `/solve-case` so the finding gets a proper report + writeback.
