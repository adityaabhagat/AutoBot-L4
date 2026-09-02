# Engineering Handoff — Case <CASE_NUMBER>

> Self-contained: no other document is required to action this.

| | |
|---|---|
| **Salesforce Case** | <CASE_NUMBER> (<SF_ID>) |
| **Client / TSP** | <client> / <tsp> |
| **Product / Module** | <P> / <module> |
| **Environment / Build** | <env, version> |
| **Classification** | <class> — <NOTs> |
| **L4 / Date** | Auto-Bot (Aditya Bhagat) / <date> |

## 1. Symptom
## 2. Object & file inventory
| Repo | Path | Role | Touch? |
|---|---|---|---|
| … | … | … | EDIT / read-only / **Do NOT change** |
## 3. Root cause
<Mechanism; per-figure effect table if numbers are wrong; explicit "X is NOT at fault" subsection.>
## 4. Domain semantics confirmed from code
## 5. The fix — per-site BEFORE/AFTER
## 6. What NOT to change
## 6A. Repo file change-set
| Action | Repo/Path | Note |
|---|---|---|
| EDIT / ADD / DO-NOT-EDIT | … | migration scaffolding, .csproj registration |
## 7. Pre-ship data checks (DBA SQL)
## 8. Verification — prove the bug, then prove the fix
## 9. Risks & required adjustments (from adversarial review)
## 10. Latent hardening (optional)
## 11. Existing-fix status
## 12. ADO bug — ready to paste
## 13. Current full pre-fix source (verbatim)

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
