#!/usr/bin/env python3
"""rank.py — content-based ranking of NEW/uncertain candidates by embedding similarity.

Approach (no fulltext needed):
  1. Backfill missing abstracts (many OpenAlex/S2 records lack them) from Crossref/OpenAlex/S2.
  2. Embed each candidate's "title. abstract" and a QUERY vector (topic + seed-paper abstracts).
  3. Rank by cosine similarity. Blend a small citation/recency tie-breaker.
  4. Candidates with NO abstract can't be ranked on content → flagged no_abstract:true and kept in a
     SEPARATE bucket so weak ranking never hides them.

Embeddings mirror zotero-mcp: OpenAI text-embedding-3-small by default (key read at call time from
~/.claude.json's zotero env, or OPENAI_API_KEY), or a local sentence-transformers model with --local.

Usage:
  rank.py --run <run> --topic "synaptic tagging and capture" [--seeds-abstracts] [--local [MODEL]]

Reads classified.json, writes it back with per-candidate {rank_score, no_abstract} and re-sorted
'new' (ranked; no-abstract items appended after, still visible) + a separate 'new_no_abstract' list.
"""
import argparse, json, sys, math, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

# ---------- OpenAI key: mirror zotero-mcp (OPENAI_API_KEY, else ~/.claude.json zotero env) ----------
def openai_key():
    import os
    k = os.getenv("OPENAI_API_KEY")
    if k: return k
    try:
        cfg = json.loads((Path.home()/".claude.json").read_text())
        env = cfg.get("mcpServers", {}).get("zotero", {}).get("env", {})
        return env.get("OPENAI_API_KEY")
    except Exception:
        return None

def embed_openai(texts, log, model="text-embedding-3-small"):
    import urllib.request
    key = openai_key()
    if not key: sys.exit("no OpenAI key (set OPENAI_API_KEY or ~/.claude.json zotero env)")
    out = []
    for i in range(0, len(texts), 256):  # batch
        batch = [t[:8000] or " " for t in texts[i:i+256]]
        req = urllib.request.Request("https://api.openai.com/v1/embeddings",
            data=json.dumps({"model": model, "input": batch}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        out.extend(d["embedding"] for d in data["data"])
        log.info(f"embedded {min(i+256,len(texts))}/{len(texts)}")
    return out

def embed_local(texts, log, model="Qwen/Qwen3-Embedding-0.6B"):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        sys.exit("sentence-transformers not installed; run with the zotero-mcp env python, or use OpenAI")
    log.info(f"loading local model {model}")
    m = SentenceTransformer(model, trust_remote_code=True)
    return [v.tolist() for v in m.encode([t[:4000] or " " for t in texts], show_progress_bar=False)]

def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

# ---------- abstract backfill ----------
def backfill_abstract(http, c, s2key=None):
    """Fetch a missing abstract by DOI, trying sources in order of yield for biomedical work.
    Crossref → OpenAlex → Europe PMC (great for Elsevier/Springer life-sci) → PubMed → S2 abstract
    → S2 TLDR (AI one-liner, last resort — enough for ranking + a gist). Returns (text, via)."""
    d = L.norm_doi(c.get("doi"))
    if not d: return ("", None)
    # Crossref
    r = http.get(f"https://api.crossref.org/works/{d}")
    if r is not None and r.status_code == 200:
        ab = r.json().get("message", {}).get("abstract")
        if ab: return (re.sub(r"<[^>]+>", "", ab).strip(), "crossref")
    # OpenAlex
    r = http.get(f"https://api.openalex.org/works/https://doi.org/{d}?select=abstract_inverted_index")
    if r is not None and r.status_code == 200:
        inv = r.json().get("abstract_inverted_index")
        if inv: return (L.reconstruct_abstract(inv), "openalex")
    # Europe PMC (strong for biomedical Elsevier/Springer that Crossref withholds)
    r = http.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{d}&resultType=core&format=json")
    if r is not None and r.status_code == 200:
        res = (r.json().get("resultList") or {}).get("result") or []
        if res and res[0].get("abstractText"):
            return (re.sub(r"<[^>]+>", "", res[0]["abstractText"]).strip(), "europepmc")
    # S2 abstract, then TLDR
    hdr = {"x-api-key": s2key} if s2key else None
    r = http.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{d}?fields=abstract,tldr", headers=hdr)
    if r is not None and r.status_code == 200:
        j = r.json()
        if j.get("abstract"): return (j["abstract"], "s2")
        if j.get("tldr") and j["tldr"].get("text"): return (j["tldr"]["text"], "s2-tldr")
    return ("", None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--topic", required=True)
    ap.add_argument("--seeds-abstracts", action="store_true",
                    help="include known-set abstracts in the query vector")
    ap.add_argument("--local", nargs="?", const="Qwen/Qwen3-Embedding-0.6B", default=None)
    ap.add_argument("--no-backfill", action="store_true")
    a = ap.parse_args()
    run = Path(a.run); log = L.Log(run)
    b = json.loads((run/"classified.json").read_text())
    cands = b.get("new", []) + b.get("uncertain", [])
    log.info(f"rank start · candidates={len(cands)} · topic={a.topic!r} · backend={'local:'+a.local if a.local else 'openai'}")

    # 1. backfill missing abstracts (CONCURRENT — independent per-DOI lookups)
    if not a.no_backfill:
        from concurrent.futures import ThreadPoolExecutor
        missing = [c for c in cands if not (c.get("abstract") or "").strip()]
        s2k = L.s2_key()
        log.info(f"backfilling {len(missing)} missing abstracts (concurrent, incl. Europe PMC + TLDR)")
        # each worker gets its own Http (no shared throttle → real parallelism); modest pool size
        def work(c):
            h = L.Http(log, min_interval=0.0, max_retries=2, source="backfill")
            try:
                ab, via = backfill_abstract(h, c, s2k)
                if ab: c["abstract"] = ab; c["abstract_via"] = via
            except Exception as e: log.warn(f"backfill fail {c.get('doi')}: {e}")
        done = 0
        with ThreadPoolExecutor(max_workers=12) as ex:
            for _ in ex.map(work, missing):
                done += 1
                if done % 25 == 0: log.info(f"backfilled {done}/{len(missing)}")
        still = sum(1 for c in cands if not (c.get("abstract") or "").strip())
        from collections import Counter
        via_counts = Counter(c.get("abstract_via") for c in missing if c.get("abstract_via"))
        log.ok(f"backfill done · recovered={len(missing)-still} still_missing={still} · via={dict(via_counts)}")

    # 2. split: rankable (has abstract) vs no-abstract
    rankable = [c for c in cands if (c.get("abstract") or "").strip()]
    noabs = [c for c in cands if not (c.get("abstract") or "").strip()]
    for c in noabs: c["no_abstract"] = True

    # 3. embed query + candidates
    embed = (lambda t: embed_local(t, log, a.local)) if a.local else (lambda t: embed_openai(t, log))
    query_parts = [a.topic]
    if a.seeds_abstracts:
        known = b.get("known", [])
        query_parts += [k.get("abstract","") for k in known if k.get("abstract")]
    doc_texts = [f"{c.get('title','')}. {c.get('abstract','')}" for c in rankable]
    vecs = embed(query_parts + doc_texts)
    qvec = [sum(col)/len(query_parts) for col in zip(*vecs[:len(query_parts)])]  # centroid
    dvecs = vecs[len(query_parts):]

    # 4. score = cosine + small citation/recency tie-breaker
    import datetime
    yr_now = 2026
    def cite_boost(c):
        cb = c.get("cited_by") or 0
        return math.log1p(cb) / 15.0  # ~0..0.5
    def rec_boost(c):
        y = c.get("year") or 0
        return max(0.0, (y - (yr_now-15)) / 15.0) * 0.1 if y else 0.0
    for c, dv in zip(rankable, dvecs):
        sim = cosine(qvec, dv)
        c["rank_score"] = round(sim + 0.15*cite_boost(c) + rec_boost(c), 4)
        c["sim"] = round(sim, 4); c["no_abstract"] = False
    rankable.sort(key=lambda c: c["rank_score"], reverse=True)
    noabs.sort(key=lambda c: (c.get("cited_by") or 0), reverse=True)  # cite-sort the no-abstract ones

    # write back: ranked ones as 'new', no-abstract separately; drop the merged 'uncertain' (folded in)
    b["new"] = rankable
    b["new_no_abstract"] = noabs
    b["uncertain"] = []  # they were merged into cands and ranked/split above
    L.write_json(run/"classified.json", b)
    log.ok(f"rank done · ranked={len(rankable)} no_abstract={len(noabs)} "
           f"top_score={rankable[0]['rank_score'] if rankable else 'n/a'}")

if __name__ == "__main__":
    main()
