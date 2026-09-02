# Prompting Playbook — getting accurate outcomes out of Auto-Bot

> Auto-Bot by Aditya Bhagat. How the orchestrator and users should phrase queries and agent prompts so the investigation converges on the REAL outcome instead of a plausible one. Pairs with `docs/HALLUCINATION_GUARDRAILS.md` (which governs what may be claimed; this file governs how to ask).

## 1. KB search queries (the #1 token lever)

- Use **Quorum vocabulary**, never plain English: `"ENMQR315 PACTRL_CYCLE_DEADLINE timely cycle"` beats `"nomination submitted late error"` (plain terms miss ~55% of matches).
- Compose queries from: error codes + table names + process codes + screen acronyms **taken verbatim from the case text**.
- Run 2–3 variants (symptom-led, table-led, process-led); strong hits (>0.2) usually point at a resolution recipe — read that section only.
- Federated `--all` search when the product is uncertain; `--product` otherwise (sharper, cheaper).

## 2. Prompting investigator agents (orchestrator rules)

- **One question per agent.** "Is the cycle deadline config wrong for TSP 24?" — not "figure out what's wrong".
- **Give the brief path, not the facts.** Agents read `cases/<CASE>/case_brief.md`; repeating facts in the prompt duplicates tokens and drifts from the single source of truth.
- **Demand the verdict block** (root_cause / anchors / action / confidence / residual_risk) — free-text conclusions don't survive the hallucination gate.
- **Name the exit condition**: "return HYPOTHESIS with the deciding query if you cannot confirm" — forbids both endless digging and false confidence.
- **Scope re-runs to refuted claims only** ("address ONLY these claims: …") — full re-investigations reintroduce drift.

## 3. Outcome-shaping (what "solved" means per gate)

| Gate | The outcome prompt must produce |
|---|---|
| G1 | Explanation a customer can read + a workaround they can perform + "what to send back if this doesn't match intent" |
| G2 | Exact key/table/scope, from→to value, WHERE clause, cache-refresh step, blast radius |
| G3 | Fixed-in version with CONFIRMED/INFERRED label + upgrade path + interim workaround |
| G4 | Preview SELECT → transactional correction script → verification query + recurrence cause |
| G5 | Mechanism sentence + file:line + BEFORE/AFTER + rejected alternative + regression risk + prove-bug/prove-fix steps |

If a deliverable is missing one of these elements, the outcome is incomplete — ask the owning agent for the missing element by name.

## 4. Anti-drift phrasing

- Start every investigator prompt with the customer's symptom restated in one line ("Customer reports: settlement statement doubled for July"). The agent's conclusion must connect back to that line.
- Ban solution-first prompts ("prove it's the config key X") — ask evidence-first ("which config keys could produce <symptom>? verify each").
- When two gates compete, prompt them **in parallel with the same symptom line** and let evidence decide — never sequentially with the second biased by the first's failure.

## 5. Token discipline in prompts

- Never paste whole skills/briefs into prompts — reference paths and section anchors.
- Cap SF/ADO pulls in the prompt itself ("LIMIT 25, one body at a time").
- Ask for compressed returns: "return the verdict block + max 10 lines of narrative".
