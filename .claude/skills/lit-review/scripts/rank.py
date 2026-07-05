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
    import urllib.request, urllib.error
    key = openai_key()
    if not key: sys.exit("no OpenAI key (set OPENAI_API_KEY or ~/.claude.json zotero env)")
    import time as _t, random as _r
    out = []
    for i in range(0, len(texts), 256):  # batch
        batch = [t[:8000] or " " for t in texts[i:i+256]]
        req = urllib.request.Request("https://api.openai.com/v1/embeddings",
            data=json.dumps({"model": model, "input": batch}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        # retry transient 429/5xx with exponential backoff + jitter (mirrors lrlib.Http) so a
        # single blip doesn't kill the whole ranking stage.
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                transient = e.code == 429 or e.code >= 500
                if not transient or attempt == 5:
                    raise
                ra = e.headers.get("Retry-After") if e.headers else None
                delay = float(ra) if (ra and str(ra).isdigit()) else min(60.0, 1.0*2**attempt) + _r.random()
                log.warn(f"[embed] {e.code}; backoff {delay:.1f}s (attempt {attempt+1})"); _t.sleep(delay)
            except urllib.error.URLError as e:
                if attempt == 5: raise
                delay = min(60.0, 1.0*2**attempt) + _r.random()
                log.warn(f"[embed] net {e}; retry {delay:.1f}s"); _t.sleep(delay)
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
    ap.add_argument("--concept-file", default=None,
                    help="JSON list of domain-NEUTRAL rephrasings of the seed's contribution "
                         "(vocabulary stripped). Builds a SECOND 'conceptual resonance' score used to "
                         "surface cross-domain hits that surface terms bury (P6b). Writes concept_sim.")
    ap.add_argument("--local", nargs="?", const="Qwen/Qwen3-Embedding-0.6B", default=None)
    ap.add_argument("--no-backfill", action="store_true")
    a = ap.parse_args()
    run = Path(a.run); log = L.Log(run)
    b = json.loads((run/"classified.json").read_text())
    # Rank NEW and UNCERTAIN together (both need a relevance score) but TAG uncertain so we can
    # re-split them into their own bucket afterwards — they must never land in the addable list.
    for c in b.get("new", []): c["_bucket"] = "new"
    for c in b.get("uncertain", []): c["_bucket"] = "uncertain"
    cands = b.get("new", []) + b.get("uncertain", [])
    log.info(f"rank start · candidates={len(cands)} "
             f"(new={len(b.get('new',[]))}, uncertain={len(b.get('uncertain',[]))}) · "
             f"topic={a.topic!r} · backend={'local:'+a.local if a.local else 'openai'}")

    # 1. backfill missing abstracts (CONCURRENT — independent per-DOI lookups)
    if not a.no_backfill:
        from concurrent.futures import ThreadPoolExecutor
        missing = [c for c in cands if not (c.get("abstract") or "").strip()]
        s2k = L.s2_key()
        log.info(f"backfilling {len(missing)} missing abstracts (concurrent, incl. Europe PMC + TLDR)")
        # SHARED per-host rate limiter so workers stay polite per host (S2 ≤1 req/s cumulative,
        # others throttled) while still parallelising ACROSS hosts. Fixes the old bug where each
        # worker had min_interval=0 and burst every backend.
        host_limiter = L.HostRateLimiter(default_interval=0.34, per_host={
            "api.semanticscholar.org": 1.05,   # ≤1 req/s cumulative
            "api.crossref.org": 0.2,
            "api.openalex.org": 0.15,
            "www.ebi.ac.uk": 0.2,              # Europe PMC
        })
        def work(c):
            h = L.Http(log, min_interval=0.0, max_retries=2, source="backfill",
                       host_limiter=host_limiter)
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
    # optional domain-neutral concept phrases → a SECOND query centroid for cross-domain resonance
    concept_parts = []
    if a.concept_file:
        cj = json.loads(Path(a.concept_file).read_text())
        concept_parts = [str(x) for x in (cj if isinstance(cj, list) else cj.get("concepts", [])) if str(x).strip()]
        if concept_parts: log.info(f"concept vector: {len(concept_parts)} domain-neutral phrases")
    doc_texts = [f"{c.get('title','')}. {c.get('abstract','')}" for c in rankable]
    all_q = query_parts + concept_parts
    vecs = embed(all_q + doc_texts)
    qvec = [sum(col)/len(query_parts) for col in zip(*vecs[:len(query_parts)])]  # topic centroid
    cvec = None
    if concept_parts:
        cslice = vecs[len(query_parts):len(all_q)]
        cvec = [sum(col)/len(cslice) for col in zip(*cslice)]  # concept centroid
    dvecs = vecs[len(all_q):]

    # 4. score = cosine + small citation/recency tie-breaker
    import datetime
    yr_now = datetime.date.today().year
    def cite_boost(c):
        cb = c.get("cited_by") or 0
        return math.log1p(cb) / 15.0  # ~0..0.5
    def rec_boost(c):
        y = c.get("year") or 0
        return max(0.0, (y - (yr_now-15)) / 15.0) * 0.1 if y else 0.0
    for c, dv in zip(rankable, dvecs):
        sim = cosine(qvec, dv)
        c["sim"] = round(sim, 4); c["no_abstract"] = False
        is_disc = bool(c.get("discovery") or c.get("origin") == "cross-domain")
        if cvec is not None:
            csim = cosine(cvec, dv)
            c["concept_sim"] = round(csim, 4)
            # cross-domain hits are judged on CONCEPTUAL resonance (surface terms mismatch by design);
            # in-domain hits keep topic similarity as the driver.
            base = max(sim, csim) if is_disc else sim
        else:
            base = sim
        c["rank_score"] = round(base + 0.15*cite_boost(c) + rec_boost(c), 4)
    rankable.sort(key=lambda c: c["rank_score"], reverse=True)
    noabs.sort(key=lambda c: (c.get("cited_by") or 0), reverse=True)  # cite-sort the no-abstract ones

    # re-split by origin bucket: uncertain candidates were ranked but must stay in their OWN bucket
    # (Discuss/Reject only in the UI) — never folded into the addable 'new' list.
    def pop_bucket(lst, name):
        keep, moved = [], []
        for c in lst:
            (moved if c.get("_bucket") == name else keep).append(c)
        return keep, moved
    rankable, unc_ranked = pop_bucket(rankable, "uncertain")
    noabs, unc_noabs = pop_bucket(noabs, "uncertain")
    uncertain = unc_ranked + unc_noabs
    uncertain.sort(key=lambda c: c.get("rank_score", c.get("sim", -1)), reverse=True)
    for c in cands: c.pop("_bucket", None)  # strip the internal tag before writing

    b["new"] = rankable
    b["new_no_abstract"] = noabs
    b["uncertain"] = uncertain  # kept separate + ranked (P1b safety boundary)
    L.write_json(run/"classified.json", b)
    log.ok(f"rank done · ranked={len(rankable)} no_abstract={len(noabs)} uncertain={len(uncertain)} "
           f"top_score={rankable[0]['rank_score'] if rankable else 'n/a'}")

if __name__ == "__main__":
    main()
