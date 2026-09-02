# Hallucination Guardrails — the Auto-Bot Evidence Standard

> Authority for Gate H (`hallucination-checker`) and binding on EVERY agent. Auto-Bot by Aditya Bhagat ships verified findings or honest hypotheses — never confident guesses.

## The anchor rule

A claim may state a fact about the system only if it carries an **anchor** the checker can re-open:

| Claim type | Valid anchor | NOT valid |
|---|---|---|
| Code behavior, line numbers | `mcp__ado__repo_file` read of the live file (repo, path, lines) or `products/<P>/code_cache/` file with capture date noted | Code-search snippet alone; memory of "how Quorum code usually looks" |
| Table/column/config key exists | KB hit (skill/CONFIG_REFERENCE section), executed query, or metadata JSON in repo | Plausible-sounding name pattern (QARCH_*, QTRAN_*) |
| Error code meaning | QCODE_* table / Constants.cs read, or skill section | Inference from the code's text alone |
| "Fixed in version X" | ReleaseNotes repo entry or explicit field → `CONFIRMED`; iteration/tag/merge-target → `INFERRED` (label mandatory) | Bare version numbers |
| Data state at client | Executed query result | `NOT YET RUN` SQL (it anchors a *plan*, never a *finding*) |
| Reproduction | Actually executed steps/queries | Thought-experiment (label `WALKTHROUGH (not executed)`) |
| Past-case precedent | SF case number / ADO id with 1-line quote | "We've seen this before" |

## Confidence vocabulary (three words only)

- **CONFIRMED** — anchor re-openable and decisive (live read, executed query, release-notes entry).
- **INFERRED** — chain of anchored facts + one reasoning step; the step is stated.
- **HYPOTHESIS** — plausible mechanism, not yet decisively anchored; must come with the query/read that would decide it.

Forbidden: "probably", "should be", "likely" as load-bearing conclusions without one of the three labels; laundering INFERRED into unlabeled fact in a later document.

## The drift rule (stay on the real issue)

At every gate and in the final report, the chain must hold:
**customer's reported symptom → classified mechanism → root cause → fix/explanation.**
Each arrow must be justified for the *reported* entities and timeframe. A real-but-unrelated bug found on the way is filed as a "latent finding" (own section / spawn suggestion), never substituted for the answer. The checker restates the original complaint verbatim-ish and tests the chain against it.

## The NOT rule

Every classification/root-cause statement names what it is **not**, with the disqualifying evidence: "Software Defect — not configuration (key X verified correct), not customer error (steps followed per training doc), not working-as-designed (contradicts NAESB timeline in skill §4)". Silence is not disqualification.

## Degradation rules (missing access ≠ made-up results)

- Metadata server absent → emit exact SQL labeled `NOT YET RUN` + interpretation table ("if ratio=2.0 → doubled; if 1.0 → look at report layer").
- ADO/SF call fails → say so, retry once, then proceed on KB with the gap listed in "limitations".
- Two hallucination-gate failures on the same claim → downgrade to HYPOTHESIS, ship as Investigation doc (ranked H1–H3), never as Triaged.

## Skill hygiene (writeback side)

New/updated skills follow the same rules: every root-cause claim in a skill cites source case/ADO ids. Uncited entries are marked `FOLKLORE` and queued for verification. This keeps the vector KB from amplifying an early mistake forever — the KB is only as trustworthy as its anchors.
