#!/usr/bin/env python3
"""
kb.py — Auto-Bot multi-product vector knowledge base.
Part of Auto-Bot, the centralized L4 issue solver — built by Aditya Bhagat.

One TF-IDF vector index PER PRODUCT (QPTM, TIPS, QLS, QDO, QRD, ...), each
covering that product's PRODUCT.md, knowledge/ tree (all 11 logic categories),
skills/, past_cases/ (case memory), code_cache/, plus the cross-product
_shared/ skills. Fully offline — no API keys, fast, token-cheap: search returns
compact chunk previews so the agent reads only what matters.

Usage:
  python kb.py build   --product QPTM          # (re)build one product index
  python kb.py build   --all                   # rebuild every product index
  python kb.py search  "query" --product QPTM [-k 8]
  python kb.py search  "query" [-k 8]          # federated (all products, deduped)
  python kb.py stats   [--product QPTM]
  python kb.py remember --product QPTM <file> [<file> ...]
                                               # save finished case doc(s) into
                                               # past_cases/ and reindex (case memory);
                                               # names are prefixed with the case id
                                               # from the cases/<CASE>/ path so reports
                                               # from different cases never overwrite
  python kb.py products                        # list products with index status

Security: any file whose name contains CONNECTION_CONFIG or SECRET is never
indexed — including inside code_cache/.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# Windows consoles default to cp1252 — force UTF-8 so symbols in skills print
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENGINE_DIR = Path(__file__).resolve().parent
ROOT = ENGINE_DIR.parent                     # Auto-Bot root
PRODUCTS_DIR = ROOT / "products"
SHARED_DIR = PRODUCTS_DIR / "_shared"

MD_EXT = {".md", ".txt", ".csv"}
CODE_EXT = {".cs", ".sql", ".js", ".ts", ".cpp", ".h", ".json", ".txt", ".xml"}
EXCLUDE_SUBSTR = ("connection_config", "secret")     # never index credentials
EXCLUDE_DIRS = {"kb_index", ".claude", "__pycache__", "node_modules"}
MAX_CHUNK_CHARS = 6000
CODE_CHUNK_LINES = 150
PREVIEW_CHARS = 400


def list_products():
    if not PRODUCTS_DIR.exists():
        return []
    return sorted(p.name for p in PRODUCTS_DIR.iterdir()
                  if p.is_dir() and not p.name.startswith("_"))


def product_dir(product):
    d = PRODUCTS_DIR / product
    if not d.exists():
        sys.exit(f"Unknown product '{product}'. Available: {', '.join(list_products())}")
    return d


def _allowed(p):
    """Shared exclusion predicate: never credentials, never generated/vendored dirs."""
    if {q.name.lower() for q in p.parents} & EXCLUDE_DIRS:
        return False
    return not any(s in p.name.lower() for s in EXCLUDE_SUBSTR)


def iter_files(product):
    """Yield (path, kind) for every indexable file of a product (+ shared)."""
    pdir = product_dir(product)
    prod_md = pdir / "PRODUCT.md"
    if prod_md.exists():
        yield prod_md, "doc"               # vocabulary table aids detection searches
    doc_roots = [pdir / "knowledge", pdir / "skills", pdir / "past_cases",
                 SHARED_DIR / "skills"]
    for root in doc_roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or not _allowed(p):
                continue
            if p.suffix.lower() in MD_EXT:
                yield p, "doc"
            elif p.suffix.lower() in CODE_EXT:
                yield p, "code"     # sql/xml snippets inside knowledge dirs
    code_cache = pdir / "code_cache"
    if code_cache.exists():
        for p in code_cache.rglob("*"):
            if not p.is_file() or not _allowed(p):
                continue
            if p.suffix.lower() == ".md":
                yield p, "doc"      # cache manifests/readmes index as docs
            elif p.suffix.lower() in CODE_EXT:
                yield p, "code"


def chunk_markdown(path):
    """Split a markdown file into chunks at #..### headings, capped in size."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    sections = re.split(r"(?m)^(#{1,3} .*)$", text)
    heading = path.stem
    buf = ""
    for part in sections:
        if re.match(r"^#{1,3} ", part or ""):
            new = part.lstrip("# ").strip()
            if buf.strip():
                yield from _emit(path, heading, buf)
                heading = new
            elif heading != path.stem:
                # heading-only section: chain it so the heading text stays searchable
                heading = f"{heading} > {new}"
            else:
                heading = new
            buf = ""
        else:
            buf += part or ""
    if buf.strip():
        yield from _emit(path, heading, buf)


def _emit(path, heading, buf):
    buf = buf.strip()
    for i in range(0, len(buf), MAX_CHUNK_CHARS):
        piece = buf[i:i + MAX_CHUNK_CHARS]
        yield {"file": str(path),
               "loc": heading + (f" (part {i // MAX_CHUNK_CHARS + 1})" if i else ""),
               "text": f"{path.stem} — {heading}\n{piece}"}


def chunk_code(path):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for i in range(0, len(lines), CODE_CHUNK_LINES):
        piece = "\n".join(lines[i:i + CODE_CHUNK_LINES]).strip()
        if len(piece) < 50:
            continue
        yield {"file": str(path),
               "loc": f"lines {i + 1}-{min(i + CODE_CHUNK_LINES, len(lines))}",
               "text": f"{path.name}\n{piece}"}


def build(product):
    index_dir = product_dir(product) / "kb_index"
    chunks = []
    n_docs = n_code = 0
    for path, kind in iter_files(product):
        before = len(chunks)
        if kind == "doc":
            chunks.extend(chunk_markdown(path))
        else:
            chunks.extend(chunk_code(path))
        if len(chunks) > before:
            n_docs += kind == "doc"
            n_code += kind == "code"
    if not chunks:
        if (index_dir / "meta.json").exists():
            shutil.rmtree(index_dir)        # don't leave a stale index behind
            print(f"[{product}] no content — removed stale index.")
        else:
            print(f"[{product}] nothing to index yet (empty knowledge base).")
        return
    texts = [c["text"] for c in chunks]
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1,
                          max_features=200_000,
                          token_pattern=r"[A-Za-z_][A-Za-z0-9_]+")
    matrix = vec.fit_transform(texts)
    index_dir.mkdir(exist_ok=True)
    joblib.dump(vec, index_dir / "vectorizer.joblib")
    joblib.dump(matrix, index_dir / "matrix.joblib")
    with open(index_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({"file": c["file"], "loc": c["loc"],
                                "preview": c["text"][:PREVIEW_CHARS]}) + "\n")
    meta = {"product": product, "chunks": len(chunks), "doc_files": n_docs,
            "code_files": n_code, "vocab": len(vec.vocabulary_)}
    (index_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[{product}] indexed {len(chunks)} chunks from {n_docs} docs + "
          f"{n_code} code files (vocab {meta['vocab']:,}).")


def _search_one(product, query, k):
    index_dir = product_dir(product) / "kb_index"
    artifacts = [index_dir / "vectorizer.joblib", index_dir / "matrix.joblib",
                 index_dir / "chunks.jsonl"]
    if not all(f.exists() for f in artifacts):
        return []
    try:
        vec = joblib.load(artifacts[0])
        matrix = joblib.load(artifacts[1])
        chunks = [json.loads(l) for l in
                  artifacts[2].read_text(encoding="utf-8").splitlines()]
        sims = linear_kernel(vec.transform([query]), matrix).ravel()
    except (OSError, EOFError, ValueError) as e:
        print(f"[{product}] index unreadable ({e.__class__.__name__}) — "
              f"rebuild: python kb.py build --product {product}")
        return []
    order = sims.argsort()[::-1][:k]
    return [(float(sims[i]), product, chunks[i]) for i in order if sims[i] > 0]


def search(query, products, k):
    hits = []
    for prod in products:
        hits.extend(_search_one(prod, query, k))
    hits.sort(key=lambda h: -h[0])
    best = {}                    # dedupe _shared chunks that live in every index
    for score, prod, c in hits:
        key = (c["file"], c["loc"])
        if key not in best:
            best[key] = (score, prod, c)
    hits = list(best.values())[:k]
    if not hits:
        print("No index built or no matches. Run: python kb.py build --product <P>")
        return
    for rank, (score, prod, c) in enumerate(hits, 1):
        rel = os.path.relpath(c["file"], ROOT)
        tag = "shared" if f"{os.sep}_shared{os.sep}" in c["file"] else prod
        print(f"\n#{rank}  score={score:.3f}  [{tag}]  {rel}  [{c['loc']}]")
        print("    " + c["preview"].replace("\n", "\n    "))
    if hits[0][0] < 0.05:
        print("\n(weak matches — try product-specific vocabulary: process codes, "
              "table names, error codes, screen names)")


def stats(products):
    if not products:
        print(f"no products found under {PRODUCTS_DIR}")
        return
    for prod in products:
        index_dir = product_dir(prod) / "kb_index"
        meta_file = index_dir / "meta.json"
        if not meta_file.exists():
            print(f"[{prod}] no index built")
            continue
        meta = json.loads(meta_file.read_text())
        print(f"[{prod}] {meta['chunks']} chunks, {meta['doc_files']} docs, "
              f"{meta['code_files']} code files, vocab {meta['vocab']:,}")


def _case_id(src):
    """Case id from a .../cases/<CASE>/... or .../cases/_archive/<CASE>/... path.

    Uses the LAST 'cases' segment so ancestor dirs named 'cases' outside the
    workspace can't mislead it. Returns None if no case folder is in the path.
    """
    lowered = [p.lower() for p in src.parts]
    if "cases" not in lowered:
        return None
    i = len(lowered) - 1 - lowered[::-1].index("cases") + 1
    if i < len(src.parts) and lowered[i] == "_archive":
        i += 1
    # must be a directory segment, not the file itself
    return src.parts[i] if i < len(src.parts) - 1 else None


def remember(product, file_paths):
    """Case memory writeback: archive finished case doc(s) and reindex once.

    Reports use generic names (report_L4_Triaged.md), so the destination is
    prefixed with the case id derived from the source path (cases/<CASE>/ or
    cases/_archive/<CASE>/) — e.g. 26-01106039_report_L4_Triaged.md — matching
    the existing past_cases/ convention. Re-remembering the same case updates
    its file in place; if no case id can be derived and the name is already
    taken, the copy is uniquified (-2, -3, ...) instead of overwriting.
    """
    dest_dir = product_dir(product) / "past_cases"
    dest_dir.mkdir(exist_ok=True)
    for file_path in file_paths:
        src = Path(file_path).resolve()
        if not src.exists():
            sys.exit(f"File not found: {file_path}")
        dest_name = src.name
        case_id = _case_id(src)
        if case_id and not dest_name.startswith(case_id):
            dest_name = f"{case_id}_{dest_name}"
        dest = dest_dir / dest_name
        if src == dest.resolve():
            print(f"[{product}] {src.name} already in past_cases — reindexing only")
        else:
            if dest.exists() and not case_id:
                stem, suffix, n = dest.stem, dest.suffix, 2
                while dest.exists():
                    dest = dest_dir / f"{stem}-{n}{suffix}"
                    n += 1
                print(f"[{product}] WARNING: {dest_name} already exists and no "
                      f"case id found in source path — saving as {dest.name}")
            shutil.copy2(src, dest)
            print(f"[{product}] remembered {src.name} -> "
                  f"{os.path.relpath(dest, ROOT)}")
    build(product)


def products_cmd():
    prods = list_products()
    if not prods:
        print(f"no products found under {PRODUCTS_DIR}")
        return
    for prod in prods:
        index_dir = PRODUCTS_DIR / prod / "kb_index"
        status = "indexed" if (index_dir / "meta.json").exists() else "NO INDEX"
        n_skills = len(list((PRODUCTS_DIR / prod / "skills").glob("*.md"))) \
            if (PRODUCTS_DIR / prod / "skills").exists() else 0
        print(f"{prod:8s}  {status:9s}  {n_skills} skills")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    bg = b.add_mutually_exclusive_group(required=True)
    bg.add_argument("--product")
    bg.add_argument("--all", action="store_true")

    s = sub.add_parser("search")
    s.add_argument("query")
    sg = s.add_mutually_exclusive_group()
    sg.add_argument("--product")
    sg.add_argument("--all", action="store_true",
                    help="search every product (this is also the default)")
    s.add_argument("-k", type=int, default=8)

    st = sub.add_parser("stats")
    st.add_argument("--product")

    r = sub.add_parser(
        "remember",
        help="archive case doc(s) into past_cases/ (case-id-prefixed) and reindex")
    r.add_argument("files", nargs="+",
                   help="doc path(s); a cases/<CASE>/ segment supplies the "
                        "case-id filename prefix")
    r.add_argument("--product", required=True)

    sub.add_parser("products")

    a = ap.parse_args()
    if a.cmd == "build":
        for prod in (list_products() if a.all else [a.product]):
            build(prod)
    elif a.cmd == "search":
        prods = [a.product] if a.product else list_products()
        search(a.query, prods, a.k)
    elif a.cmd == "stats":
        stats([a.product] if a.product else list_products())
    elif a.cmd == "remember":
        remember(a.product, a.files)
    else:
        products_cmd()
