# Auto-Bot — L4 Team Setup Guide

> Built by **Aditya Bhagat**. 15 minutes from clone to first solved case.

## 1. Prerequisites

- Windows (Quorum VPN for client-DB diagnostics), Python 3.11+, Git, Claude Code (for the agent graph and `/lite-solve` plumbing).

## 2. Clone & install

```bash
git clone <REPO_URL> Auto-Bot
cd Auto-Bot
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## 3. Things git does NOT ship (copy once)

| Item | Where to get it | Where to put it |
|---|---|---|
| `QuorumMetadataMCP.exe` + `.dll` + `.pdb` | team share / Aditya | `QuorumMetadataMCP/` |
| `dbconfig.json` | copy `QuorumMetadataMCP/dbconfig.template.json` → `dbconfig.json` (fill Oracle password ONLY locally — file is gitignored) | `QuorumMetadataMCP/` |
| `CONNECTION_CONFIG.md` | copy `CONNECTION_CONFIG.template.md`, fill your ADO PAT | repo root |
| `products/<P>/code_cache/` (optional) | team share — speeds up G5 code lookups | as-is |

## 4. Build the knowledge indexes

```bash
python engine/kb.py build --all
```

## 5. Verify your install

```bash
python autobot.py check      # expect: 280 rules, 0 problems
pytest tests/ -q             # expect: all green (offline, no VPN needed)
```

## 6. Daily use

| Task | Command |
|---|---|
| Fast deterministic solve (known families) | `/lite-solve <case#>` in Claude Code, or `python autobot.py solve <case#>` if `cases/<case#>/raw/` already dumped |
| Deep agent investigation (novel defects) | `/solve-case <case#>` |
| Client DB for diagnostics | `set QUORUM_METADATA_ENV=<env>` (catalog in dbconfig) or `--env` flag |
| After a human solves a NOVEL case | `python autobot.py learn <case#>` → curate the scaffolded rule → PR it |
| Add/refresh knowledge | edit skills → `python engine/kb.py build --product <P>` |

## 7. Contributing rules (the growth loop)

1. `autobot.py learn` scaffolds `rules/<P>/pending_<case>.yaml`.
2. Complete it per `rules/SCHEMA.md` (distinctive match terms, source anchor, SELECT-only SQL, when-DSL only).
3. `python autobot.py check` + `pytest` must pass.
4. PR with the case number in the title — one reviewer from L4.

⚠️ Never commit: filled `dbconfig.json`, `CONNECTION_CONFIG.md`, PATs, client PRD data extracts. The `.gitignore` guards these — do not weaken it.
