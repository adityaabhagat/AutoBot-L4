#!/usr/bin/env python3
"""
autobot.py — Auto-Bot Lite: the deterministic (no-LLM) L4 pipeline.
Built by Aditya Bhagat · Quorum Business Solutions.

Pipeline: load raw case data -> extract signals -> TF-IDF recall -> rule-based
gate ladder -> SQL-pack diagnosis -> recipe or human packet -> templated report.
Every conclusion carries a machine-checkable anchor (rule id, skill section,
SQL result, record id). Zero LLM calls.

Input contract: cases/<CASE>/raw/ populated by the /lite-solve Claude skill
(pure MCP plumbing) or any other dump: case.json, comments.json, emails.json,
similar.json, ado.json, attachments/*.txt|*.log.

Usage:
  python autobot.py solve 26-01106039 [--product QPTM] [--env EQCU_HD_DEV17] [--offline] [--remember]
  python autobot.py check                       # validate all rules/sqlpacks
  python autobot.py learn 26-01106039           # scaffold a rule from a solved case
"""
import argparse
import configparser
import glob
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

__version__ = "1.0.0"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine"
PRODUCTS = ROOT / "products"
RULES_DIR = ROOT / "rules"
PACKS_DIR = ROOT / "sqlpacks"
RECIPES_DIR = ROOT / "recipes"
CASES = Path(os.environ.get("AUTOBOT_CASES_DIR", ROOT / "cases"))
DBCONFIG = ROOT / "QuorumMetadataMCP" / "dbconfig.json"
CONFIG_INI = ROOT / "lite_config.ini"

sys.path.insert(0, str(ENGINE))
try:
    import kb  # engine/kb.py — TF-IDF knowledge base (non-LLM)
except Exception:
    kb = None

PRODUCT_LIST_MAP = {
    "my quorum gas pipeline": "QPTM",
    "my quorum tips": "TIPS",
    "my quorum division order": "QDO",
    "my quorum land": "QLS",
}

GATES = ["G1", "G2", "G3", "G4", "G5"]
GATE_NAMES = {
    "G1": "Expected Behavior", "G2": "Configuration", "G3": "Version (already fixed)",
    "G4": "Bad Data", "G5": "Code Change",
}
FORBIDDEN_SQL = re.compile(r"\b(insert|update|delete|drop|alter|truncate|exec|execute|merge|grant)\b", re.I)

ERROR_PATTERNS = [
    r"ENMQR\d{3}", r"EEDM1\d{2}", r"ORA-\d{3,5}", r"SQLState\s*\S+",
    r"NativeError\s*\d+", r"\bSQL\s?\d{3}\b", r"Rule[A-Z]{2,4}\d{4,}",
    r"Invalid object name '([A-Za-z0-9_]+)'", r"Violation of (?:PRIMARY KEY|UNIQUE KEY) constraint '\w+'",
]
ENTITY_PATTERNS = {
    "contract": r"\b(\d{3,5}\.\d{3,5})\b",
    "invoice": r"\binvoice\s*#?\s*(\d{4,})\b",
    "tsp": r"\bTSP\s*#?\s*(\d{1,5})\b",
    "pqid": r"\bPQID\s*#?\s*(\d{3,})\b",
    "gas_day": r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
}


def log(msg):
    print(f"[autobot] {msg}")


# ---------------------------------------------------------------- load raw
def load_raw(case_dir: Path):
    raw = case_dir / "raw"
    case_file = raw / "case.json"
    if not case_file.exists():
        sys.exit(f"No raw data at {raw}. Run the /lite-solve skill (or drop case.json) first.")
    def jload(name, default):
        p = raw / name
        if not p.exists():
            return default
        try:
            return json.loads(p.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            log(f"WARN: {name} unparseable ({e}) — ignored")
            return default
    data = {
        "case": jload("case.json", {}),
        "comments": jload("comments.json", []),
        "emails": jload("emails.json", []),
        "similar": jload("similar.json", []),
        "ado": jload("ado.json", []),
        "logs": {},
    }
    att = raw / "attachments"
    if att.exists():
        for p in att.glob("*"):
            if p.suffix.lower() in (".txt", ".log", ".csv"):
                data["logs"][p.name] = p.read_text(encoding="utf-8", errors="replace")[:200_000]
    return data


def build_corpus(data):
    c = data["case"]
    parts = [c.get("Subject", ""), c.get("Description", "")]
    parts += [x.get("CommentBody", "") for x in data["comments"]]
    parts += [f"{x.get('Subject','')} {x.get('TextBody','')}" for x in data["emails"]]
    parts += [f"{x.get('title','')} {x.get('description','')}" for x in data["ado"]]
    parts += list(data["logs"].values())
    return "\n".join(p for p in parts if p)


# ------------------------------------------------------- product detection
def parse_vocab(product):
    """Terms + table prefixes from products/<P>/PRODUCT.md vocabulary table."""
    md = PRODUCTS / product / "PRODUCT.md"
    terms, prefixes = [], []
    if not md.exists():
        return terms, prefixes
    for line in md.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [x.strip() for x in line.strip("|").split("|")]
        if len(cells) != 2 or cells[0] in ("Kind", ""):
            continue
        for tok in re.split(r"[,;]", re.sub(r"\(.*?\)", "", cells[1])):
            tok = tok.strip()
            if not tok or " " in tok and len(tok) > 40:
                continue
            if tok.endswith("_*"):
                prefixes.append(tok[:-1])
            elif re.fullmatch(r"[A-Za-z0-9_#*/.-]{3,30}", tok.replace(" ", "")):
                terms.append(tok)
    return terms, prefixes


def detect_product(case, corpus, override=None):
    if override:
        return override, "flag"
    plc = (case.get("Product_list__c") or "").strip().lower()
    if plc in PRODUCT_LIST_MAP:
        return PRODUCT_LIST_MAP[plc], f"Product_list__c='{case.get('Product_list__c')}'"
    scores = {}
    for pdir in PRODUCTS.iterdir():
        if not pdir.is_dir() or pdir.name.startswith("_"):
            continue
        terms, _ = parse_vocab(pdir.name)
        n = sum(1 for t in terms if re.search(re.escape(t), corpus, re.I))
        if n:
            scores[pdir.name] = n
    if scores:
        best = max(scores, key=scores.get)
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        if len(ranked) == 1 or ranked[0][1] >= 2 * ranked[1][1]:
            return best, f"vocabulary match ({scores[best]} terms)"
    sys.exit(f"Cannot detect product (Product_list__c='{case.get('Product_list__c')}', "
             f"vocab scores={scores}). Re-run with --product <P>.")


# --------------------------------------------------------- signal extraction
def extract_signals(corpus, product):
    sig = {"error_codes": [], "tables": [], "processes": [], "entities": {}, "first_errors": []}
    for pat in ERROR_PATTERNS:
        for m in re.finditer(pat, corpus, re.I):
            v = m.group(0).strip()
            if v not in sig["error_codes"]:
                sig["error_codes"].append(v)
    terms, prefixes = parse_vocab(product)
    for m in re.finditer(r"\b[A-Z][A-Z0-9]{1,9}_[A-Z0-9_]{2,40}\b", corpus):
        t = m.group(0)
        if any(t.startswith(p) for p in prefixes) and t not in sig["tables"]:
            sig["tables"].append(t)
    for t in terms:
        if re.fullmatch(r"[A-Z0-9_]{4,20}", t) and re.search(rf"\b{re.escape(t)}\b", corpus):
            if t not in sig["processes"]:
                sig["processes"].append(t)
    for name, pat in ENTITY_PATTERNS.items():
        m = re.search(pat, corpus, re.I)
        if m:
            sig["entities"][name] = m.group(1)
    return sig


def first_error_lines(data):
    out = []
    for fname, text in data["logs"].items():
        for line in text.splitlines():
            if re.search(r"\bERROR\b", line, re.I):
                out.append((fname, line.strip()[:300]))
                break
    return out


# ------------------------------------------------------------------ recall
def recall(product, sig, case):
    if kb is None:
        return []
    queries = []
    if sig["error_codes"] or sig["tables"]:
        queries.append(" ".join(sig["error_codes"][:4] + sig["tables"][:4]))
    if sig["processes"]:
        queries.append(" ".join(sig["processes"][:5] + sig["error_codes"][:2]))
    subj = case.get("Subject", "")
    if subj:
        queries.append(subj)
    hits = {}
    for q in [q for q in queries if q.strip()]:
        try:
            for score, prod, chunk in kb._search_one(product, q, 8):
                key = (chunk["file"], chunk["loc"])
                if key not in hits or hits[key][0] < score:
                    hits[key] = (score, chunk)
        except Exception as e:
            log(f"WARN: recall failed ({e}) — run: python engine/kb.py build --product {product}")
            return []
    ranked = sorted(hits.values(), key=lambda h: -h[0])[:8]
    return [{"score": round(s, 3), "file": os.path.relpath(c["file"], ROOT),
             "loc": c["loc"], "preview": c["preview"][:200]} for s, c in ranked]


# ------------------------------------------------------------------- rules
def load_rules(product):
    rules = []
    sources = []
    single = RULES_DIR / f"{product}.yaml"
    if single.exists():
        sources.append(single)
    sources += sorted((RULES_DIR / product).glob("*.yaml")) if (RULES_DIR / product).exists() else []
    for f in sources:
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            log(f"WARN: {f.name} invalid YAML — skipped ({e})")
            continue
        for r in doc.get("rules", []):
            if not r.get("id") or r.get("gate") not in GATES or not r.get("match") or not r.get("source"):
                log(f"WARN: malformed rule skipped in {f.name}: {r.get('id','<no id>')}")
                continue
            r["_file"] = f.name
            rules.append(r)
    return rules


def term_hit(term, corpus):
    t = str(term)
    if len(t) > 2 and t.startswith("/") and t.endswith("/"):
        return re.search(t[1:-1], corpus, re.I) is not None
    # plain terms match on word boundaries so "allocation" can't hit "reallocation"
    pat = re.escape(t)
    if t and (t[0].isalnum() or t[0] == "_"):
        pat = r"\b" + pat
    if t and (t[-1].isalnum() or t[-1] == "_"):
        pat = pat + r"\b"
    return re.search(pat, corpus, re.I) is not None


def rule_matches(rule, corpus):
    m = rule["match"] or {}
    alls, anys, nones = m.get("all") or [], m.get("any") or [], m.get("none") or []
    if not alls and not anys:
        return False
    if any(not term_hit(t, corpus) for t in alls):
        return False
    if anys and not any(term_hit(t, corpus) for t in anys):
        return False
    if any(term_hit(t, corpus) for t in nones):
        return False
    return True


def near_misses(rules, corpus, limit=5):
    out = []
    for r in rules:
        alls = (r["match"] or {}).get("all") or []
        if len(alls) >= 2:
            hits = sum(1 for t in alls if term_hit(t, corpus))
            if 0 < hits < len(alls) and hits / len(alls) >= 0.5:
                missing = [t for t in alls if not term_hit(t, corpus)]
                out.append({"id": r["id"], "gate": r["gate"], "matched": hits,
                            "of": len(alls), "missing": missing, "source": r["source"]})
    return sorted(out, key=lambda x: -(x["matched"] / x["of"]))[:limit]


# ---------------------------------------------------------------- diagnose
def pick_driver():
    import pyodbc
    for d in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
        if d in pyodbc.drivers():
            return d
    return None


def resolve_env(case, env_flag):
    if env_flag:
        name = env_flag
    else:
        cfg = configparser.ConfigParser()
        if CONFIG_INI.exists():
            cfg.read(CONFIG_INI, encoding="utf-8")
        acct = (case.get("Account") or {}).get("Name") or case.get("AccountName") or ""
        code = cfg.get("clients", acct, fallback=None) if cfg.has_section("clients") else None
        if not code:
            return None, f"no client->code mapping for '{acct}' in lite_config.ini [clients]"
        envs = json.loads(DBCONFIG.read_text(encoding="utf-8"))["environments"]
        cands = [e for e in envs if e.upper().startswith(code.upper())]
        if not cands:
            return None, f"no dbconfig environment starts with '{code}'"
        name = sorted(cands)[0]
    envs = json.loads(DBCONFIG.read_text(encoding="utf-8"))["environments"]
    if name not in envs:
        return None, f"environment '{name}' not in dbconfig.json"
    return {"name": name, **envs[name]}, None


def run_pack(pack_name, product, entities, env, offline):
    pack_file = PACKS_DIR / product / f"{pack_name}.yaml"
    result = {"pack": pack_name, "queries": [], "verdict": "NOT YET RUN", "env": env["name"] if env else None}
    if not pack_file.exists():
        result["verdict"] = "PACK MISSING"
        return result
    pack = yaml.safe_load(pack_file.read_text(encoding="utf-8"))
    conn = None
    if not offline and env and env.get("type") == "sqlserver":
        try:
            import pyodbc
            drv = pick_driver()
            cs = (f"Driver={{{drv}}};Server={env['server']};Database={env['database']};"
                  f"Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes")
            conn = pyodbc.connect(cs, timeout=15)
        except Exception as e:
            result["conn_error"] = str(e)[:200]
    verdicts = []
    for q in pack.get("queries", []):
        entry = {"id": q.get("id"), "proves": q.get("proves"), "sql": q.get("sql"), "status": "NOT YET RUN"}
        sql = q.get("sql", "")
        if FORBIDDEN_SQL.search(sql):
            entry["status"] = "REFUSED (non-SELECT)"
            result["queries"].append(entry)
            continue
        try:
            sql_filled = sql.format_map(SafeDict(entities))
        except Exception:
            sql_filled = sql
        if "{" in sql_filled and "}" in sql_filled:
            entry["status"] = "SKIPPED (missing placeholder value)"
            result["queries"].append(entry)
            continue
        entry["sql"] = sql_filled
        if conn is None:
            result["queries"].append(entry)
            continue
        try:
            cur = conn.cursor()
            cur.execute(sql_filled)
            cols = [d[0].lower() for d in cur.description] if cur.description else []
            rows = [dict(zip(cols, r)) for r in cur.fetchmany(25)]
            entry["rowcount"] = len(rows)
            entry["rows"] = [{k: str(v)[:80] for k, v in r.items()} for r in rows[:5]]
            entry["status"] = "RAN"
            hit = evaluate_interpret(q.get("interpret") or [], rows)
            if hit:
                entry["meaning"], v = hit
                verdicts.append(v)
        except Exception as e:
            entry["status"] = f"ERROR: {str(e)[:150]}"
        result["queries"].append(entry)
    if conn:
        conn.close()
    if any(v in ("REFUTED", "FALLTHROUGH") for v in verdicts):
        result["verdict"] = "REFUTED"
    elif "CONFIRMED" in verdicts:
        result["verdict"] = "CONFIRMED"
    elif verdicts:
        result["verdict"] = "INFERRED"
    elif any(x["status"] == "RAN" for x in result["queries"]):
        result["verdict"] = "MANUAL REVIEW"
    return result


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


WHEN_FORMS = [
    (re.compile(r"^rowcount\s*(==|>=|>)\s*(\d+)$"), "rowcount"),
    (re.compile(r"^rows\[0\]\.(\w+)\s+is\s+null$"), "isnull"),
    (re.compile(r"^rows\[0\]\.(\w+)\s+is\s+not\s+null$"), "notnull"),
    (re.compile(r"^rows\[0\]\.(\w+)\s*(==|>=|<=)\s*(.+)$"), "cmp"),
]


def evaluate_interpret(interps, rows):
    for it in interps:
        when = (it.get("when") or "").strip()
        meaning, verdict = it.get("meaning", ""), it.get("verdict", "INFERRED")
        for rx, kind in WHEN_FORMS:
            m = rx.match(when)
            if not m:
                continue
            ok = False
            if kind == "rowcount":
                op, n = m.group(1), int(m.group(2))
                ok = {"==": len(rows) == n, ">=": len(rows) >= n, ">": len(rows) > n}[op]
            elif rows:
                col = m.group(1).lower()
                val = rows[0].get(col)
                if kind == "isnull":
                    ok = val is None
                elif kind == "notnull":
                    ok = val is not None
                elif kind == "cmp":
                    op, target = m.group(2), m.group(3).strip().strip("'\"")
                    try:
                        v, t = float(val), float(target)
                    except (TypeError, ValueError):
                        v, t = str(val), target
                    ok = {"==": v == t, ">=": v >= t, "<=": v <= t}[op]
            elif kind in ("isnull",):
                ok = False
            if ok:
                return meaning, verdict
            break
    return None


# ---------------------------------------------------------------- classify
def classify(rules, corpus, case, sig, product, env, offline):
    prior = (case.get("Root_Cause__c") or "").lower()
    skip_g1 = "software defect" in prior
    fired, diagnostics = None, []
    ordered = sorted(rules, key=lambda r: (GATES.index(r["gate"]), r.get("priority", 100), r["id"]))
    for r in ordered:
        if skip_g1 and r["gate"] == "G1":
            continue
        if not rule_matches(r, corpus):
            continue
        diag = None
        if r.get("sql_pack"):
            diag = run_pack(r["sql_pack"], product, sig["entities"], env, offline)
            diagnostics.append(diag)
            if diag["verdict"] == "REFUTED":
                continue
        fired = (r, diag)
        break
    return fired, diagnostics


# ------------------------------------------------------------------ report
def fill(text, mapping):
    try:
        return text.format_map(SafeDict(mapping))
    except (ValueError, KeyError):
        # unbalanced braces (e.g. SQL snippets) — substitute known keys only
        for k, v in mapping.items():
            text = text.replace("{" + k + "}", str(v))
        return text


def write_report(case_dir, product, case, sig, kb_hits, fired, diagnostics, nears, batch, data, env):
    c = case
    ents = dict(sig["entities"])
    ents.update({"client": (c.get("Account") or {}).get("Name", "?"), "case": c.get("CaseNumber", "?")})
    today = date.today().isoformat()
    lines = []
    if fired:
        rule, diag = fired
        gate = rule["gate"]
        conf = "INFERRED"
        if gate in ("G1", "G3"):
            conf = "INFERRED" if not rule.get("ado_refs") else "CONFIRMED (per cited ADO/skill record)"
        if diag:
            conf = {"CONFIRMED": "CONFIRMED (SQL verified)", "INFERRED": "INFERRED",
                    "NOT YET RUN": "INFERRED (verification SQL NOT YET RUN)",
                    "MANUAL REVIEW": "INFERRED (SQL needs manual reading)"}.get(diag["verdict"], "INFERRED")
        title = f"report_Lite_{gate}.md"
        nots = ", ".join(f"not {GATE_NAMES[g]}" for g in GATES if g != gate)
        lines += [f"# Auto-Bot Lite — Case {ents['case']} ({gate} {GATE_NAMES[gate]})", "",
                  f"| Case | {ents['case']} | Client | {ents['client']} | Product | {product} |",
                  "|---|---|---|---|---|---|",
                  f"| Date | {today} | Rule | `{rule['id']}` | Confidence | {conf} |", "",
                  f"**Classification:** {GATE_NAMES[gate]} — ({nots})",
                  f"**Root cause:** {fill(rule.get('verdict',''), ents)}",
                  f"**Anchor:** {rule['source']}" + (f" · ADO {', '.join(map(str, rule.get('ado_refs', [])))}" if rule.get("ado_refs") else ""), ""]
        if rule.get("recipe"):
            rp = RECIPES_DIR / product / f"{rule['recipe']}.md"
            if rp.exists():
                lines += ["## Fix (recipe)", fill(rp.read_text(encoding='utf-8'), ents), ""]
            else:
                lines += ["## Fix", f"Recipe `{rule['recipe']}` referenced but not found — see {rule['source']}.", ""]
    else:
        title = "report_Lite_NOVEL.md"
        lines += [f"# Auto-Bot Lite — Case {ents['case']} (NOVEL — human investigation packet)", "",
                  f"| Case | {ents['case']} | Client | {ents['client']} | Product | {product} | Date | {today} |",
                  "|---|---|---|---|---|---|---|---|", "",
                  "No deterministic rule matched. Everything below is pre-gathered for the human L4",
                  "(or run the full Auto-Bot agent graph: `/solve-case`).", ""]
        if nears:
            lines += ["## Near-miss rules (what almost fired)"]
            lines += [f"- `{n['id']}` ({n['gate']}) matched {n['matched']}/{n['of']} — missing: {n['missing']} · {n['source']}" for n in nears]
            lines.append("")
    lines += ["## Extracted signals",
              f"- Error codes: {', '.join(sig['error_codes']) or '—'}",
              f"- Tables: {', '.join(sig['tables']) or '—'}",
              f"- Processes: {', '.join(sig['processes']) or '—'}",
              f"- Entities: {json.dumps(sig['entities'])}", ""]
    if batch:
        lines += ["## Batch triage", f"- Batch flag: {batch['flag']}"]
        lines += [f"- First error [{f}]: `{l}`" for f, l in batch["first_errors"]] or ["- No ERROR line found in attached logs"]
        lines.append("")
    lines += ["## KB recall (TF-IDF)"]
    lines += [f"- {h['score']} · {h['file']} [{h['loc']}]" for h in kb_hits] or ["- no hits (index built?)"]
    lines.append("")
    if diagnostics:
        lines += ["## Diagnostic SQL"]
        for d in diagnostics:
            lines.append(f"### pack `{d['pack']}` — verdict {d['verdict']} (env: {d.get('env') or 'none'})")
            if d.get("conn_error"):
                lines.append(f"- connection error: {d['conn_error']}")
            for q in d["queries"]:
                lines += [f"- **{q.get('id')}** [{q['status']}] — {q.get('proves','')}",
                          f"  ```sql\n  {q.get('sql','').strip()}\n  ```"]
                if q.get("meaning"):
                    lines.append(f"  → {q['meaning']}")
                if q.get("rows"):
                    lines.append(f"  rows: {json.dumps(q['rows'][:3])}")
        lines.append("")
    lines += ["## Sources", f"- SF case {c.get('Id','?')} · {len(data['comments'])} comments · "
              f"{len(data['emails'])} emails · {len(data['ado'])} ADO items · {len(data['logs'])} logs parsed", "",
              "---", "*Investigated by Auto-Bot Lite — the deterministic L4 pipeline built by Aditya Bhagat. "
              "Zero LLM calls; every claim anchored to a rule id, SQL result, or record id.*"]
    out = case_dir / title
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ------------------------------------------------------------------- solve
def solve(args):
    case_dir = CASES / args.case
    data = load_raw(case_dir)
    corpus = build_corpus(data)
    case = data["case"]
    product, how = detect_product(case, corpus, args.product)
    log(f"product: {product} ({how})")
    sig = extract_signals(corpus, product)
    log(f"signals: {len(sig['error_codes'])} errors, {len(sig['tables'])} tables, "
        f"{len(sig['processes'])} processes, entities {list(sig['entities'])}")
    kb_hits = recall(product, sig, case)
    if kb_hits:
        log(f"recall: top hit {kb_hits[0]['score']} {kb_hits[0]['file']}")
    rules = load_rules(product)
    if not rules:
        log(f"WARN: no rules loaded for {product} (rules/{product}/*.yaml)")
    env, env_err = (None, "offline") if args.offline else resolve_env(case, args.env)
    if env_err and not args.offline:
        log(f"DB env unresolved: {env_err} — diagnostics will be NOT YET RUN")
    batch = None
    fe = first_error_lines(data)
    batch_procs = [p for p in sig["processes"]]
    fired, diagnostics = classify(rules, corpus, case, sig, product, env, args.offline)
    if fired and fired[0].get("batch") or fe:
        flag = (fired[0].get("batch") if fired else None) or ("NORMAL" if batch_procs else "unknown")
        batch = {"flag": flag, "first_errors": fe}
    nears = near_misses(rules, corpus) if not fired else []
    out = write_report(case_dir, product, case, sig, kb_hits, fired, diagnostics, nears, batch, data, env)
    if fired:
        log(f"SOLVED via {fired[0]['id']} ({fired[0]['gate']}) -> {out}")
    else:
        log(f"NOVEL -> investigation packet {out}")
    if args.remember:
        subprocess.run([sys.executable, str(ENGINE / "kb.py"), "remember",
                        "--product", product, str(out)], check=False)
    else:
        log(f"to memorize: python engine/kb.py remember --product {product} \"{out}\"")
    return 0


# ------------------------------------------------------------------- check
def check(_args):
    n_rules = n_bad = 0
    ids = set()
    for pdir in sorted(RULES_DIR.glob("*")):
        if pdir.is_file() and pdir.suffix == ".yaml" or pdir.is_dir():
            product = pdir.stem if pdir.is_file() else pdir.name
            if product == "SCHEMA":
                continue
            rules = load_rules(product)
            for r in rules:
                n_rules += 1
                if r["id"] in ids:
                    log(f"DUPLICATE id {r['id']}")
                    n_bad += 1
                ids.add(r["id"])
                if r.get("sql_pack") and not (PACKS_DIR / product / f"{r['sql_pack']}.yaml").exists():
                    log(f"{r['id']}: sql_pack '{r['sql_pack']}' missing")
                    n_bad += 1
                if r.get("recipe") and not (RECIPES_DIR / product / f"{r['recipe']}.md").exists():
                    log(f"{r['id']}: recipe '{r['recipe']}' missing")
                    n_bad += 1
            for pf in (PACKS_DIR / product).glob("*.yaml") if (PACKS_DIR / product).exists() else []:
                pack = yaml.safe_load(pf.read_text(encoding="utf-8"))
                for q in pack.get("queries", []):
                    if FORBIDDEN_SQL.search(q.get("sql", "")):
                        log(f"{pf.name}/{q.get('id')}: FORBIDDEN non-SELECT SQL")
                        n_bad += 1
                    for it in q.get("interpret", []):
                        if not any(rx.match((it.get("when") or "").strip()) for rx, _ in WHEN_FORMS):
                            log(f"{pf.name}/{q.get('id')}: unparseable when '{it.get('when')}'")
                            n_bad += 1
            if rules:
                log(f"{product}: {len(rules)} rules OK")
    log(f"check done: {n_rules} rules, {n_bad} problems")
    return 1 if n_bad else 0


# ------------------------------------------------------------------- learn
def learn(args):
    case_dir = CASES / args.case
    data = load_raw(case_dir)
    corpus = build_corpus(data)
    product, _ = detect_product(data["case"], corpus, args.product)
    sig = extract_signals(corpus, product)
    terms = (sig["error_codes"][:2] + sig["tables"][:2]) or sig["processes"][:2]
    scaffold = {
        "product": product,
        "rules": [{
            "id": f"{product}-NEW-000",
            "gate": "G5",
            "match": {"all": terms},
            "verdict": "<one-line root cause — fill from the solved case>",
            "source": f"case {args.case} — <skill §, add after curating>",
        }],
    }
    out = RULES_DIR / product / f"pending_{args.case}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(scaffold, sort_keys=False, allow_unicode=True), encoding="utf-8")
    log(f"rule scaffold -> {out} — review, complete, rename id, then merge into the product rules file")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("solve")
    s.add_argument("case")
    s.add_argument("--product")
    s.add_argument("--env")
    s.add_argument("--offline", action="store_true")
    s.add_argument("--remember", action="store_true")
    s.set_defaults(fn=solve)
    c = sub.add_parser("check")
    c.set_defaults(fn=check)
    l = sub.add_parser("learn")
    l.add_argument("case")
    l.add_argument("--product")
    l.set_defaults(fn=learn)
    a = ap.parse_args()
    sys.exit(a.fn(a))
