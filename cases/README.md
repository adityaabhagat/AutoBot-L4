# cases/ — active case workspaces

One folder per case: `cases/<CASE_NUMBER>/`

| File | Written by | Purpose |
|---|---|---|
| `case_brief.md` | intake-agent (N0), appended by repro (N1) + classifier (N2) | The single working memory — agents read this, never re-pull Salesforce |
| `evidence.md` | investigators (G2–G5, batch-debugger) | Append-only anchored findings: `claim → anchor` |
| `report_<type>.md` | report-writer (N4) | Final deliverable(s) from `templates/` |

Lifecycle: solved → `python engine/kb.py remember --product <P> cases/<CASE>/report_<type>.md` (each report file explicitly; knowledge-curator does this) → move folder to `cases/_archive/` after delivery.

*Auto-Bot by Aditya Bhagat.*
