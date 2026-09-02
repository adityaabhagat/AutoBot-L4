# L4 Triaged — Case <CASE_NUMBER>

| | |
|---|---|
| **Salesforce Case** | <CASE_NUMBER> (<SF_ID>) |
| **Client / TSP** | <client> / <tsp> |
| **Contact** | <name> |
| **Product / Module** | <P> / <module> |
| **Environment** | <env, client build version> |
| **Priority** | <P1..P3> |
| **Classification** | <class> — confirmed at <level> (not <ruled-out-1>, not <ruled-out-2>, not <ruled-out-3>) |
| **L4 / Date** | Auto-Bot (Aditya Bhagat) / <date> |

## 1. Issue Summary
<2–4 lines: what the customer reported, verbatim error codes, business impact.>

## 2. Reproduction
<Environment-specific numbered steps + observed evidence. Label DERIVED steps. Reproducibility verdict with anchor.>

## 3. Root Cause (code level)
<Defect mechanism in one bolded sentence. Then the trace: repo/file:line citations (each CONFIRMED via live read or dated code_cache), the decision point that misfires, and what is explicitly NOT at fault.>

## 4. Suggested Code Fix (ranked)
### Primary (Recommended)
<BEFORE/AFTER code blocks, exact file:line.>
### Alternative (Rejected)
<The option considered and WHY rejected.>
**Recommendation:** <one line.>

## 5. Expected Result After Fix
<Observable behavior change, per affected entity/report. What was never affected.>

## 6. Diagnostic SQL
```sql
-- <what this result proves, e.g. "ratio ~2.0 = doubled volumes">
<query>
```

## 7. Related Items
<ADO bugs (id, state, fixed-in [CONFIRMED|INFERRED]), sibling SF cases, PR coordination needs, latent risks. Suggested ADO bug title.>

## 8. ADO Bug — ready to paste
| Field | Value |
|---|---|
| Work Item Type | Bug |
| Title | <title> |
| Area Path | <area> |
| Severity | <sev> |
| Found in Version | <ver> |
| Customer / Case | <client> / <CASE_NUMBER> |
| Root Cause category | <category> |

**Repro Steps:** …
**Expected / Actual:** …
**Root Cause:** …
**Proposed Fix:** …
**Regression Risk:** …
**Test / Verification:** <prove bug → prove fix>
**Release Note (draft, customer-plain):** <what was corrected; what was never affected; no code symbols.>

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
