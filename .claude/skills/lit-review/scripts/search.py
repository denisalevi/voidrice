#!/usr/bin/env python3
"""search.py — run a batch of queries against OpenAlex + Semantic Scholar.

Handles pagination, cursors, 429 backoff, abstract reconstruction, credit tracking.
Writes candidates to <run>/raw_candidates.jsonl (append) and a live <run>/search_summary.json
so the orchestrator can POLL progress. Idempotent-ish: re-running appends; dedup happens later.

Usage:
  search.py --run <run_dir> --queries <queries.json> [--per-page 50] [--max-pages 4]

queries.json shape:
  {
    "openalex": [
      {"mode":"filter","q":"title.search:hippocampal replay","from":"2020-01-01","label":"replay-title"},
      {"mode":"search","q":"memory consolidation replay","label":"consolidation-broad"}
    ],
    "s2": [
      {"mode":"bulk","q":"replay consolidation","label":"replay-bulk"}
    ]
  }
Log: <run>/run.log   Summary: <run>/search_summary.json
"""
import argparse, json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

def oa_run(http, log, run, q, per_page, max_pages, key, summ):
    cands = 0
    base = "https://api.openalex.org/works"
    sel = "id,doi,title,publication_year,authorships,abstract_inverted_index,cited_by_count,primary_location"
    if q["mode"] == "search":
        params = {"search": q["q"]}
    elif q["mode"] == "filter":
        filt = q["q"] + (f",from_publication_date:{q['from']}" if q.get("from") else "")
        params = {"filter": filt}
    else:
        log.error(f"[openalex] {q.get('label')}: unknown mode {q['mode']!r} (use search|filter); skipped"); return
    params.update({"per-page": per_page, "select": sel, "cursor": "*"})
    if key: params["api_key"] = key
    pages = 0
    while pages < max_pages:
        url = base + "?" + urllib.parse.urlencode(params)
        summ["openalex_credits"] += L.oa_credit_cost(url)
        r = http.get(url)
        if r is None or r.status_code != 200:
            log.error(f"[openalex] {q.get('label')} page {pages}: status {getattr(r,'status_code','ERR')}"); break
        data = r.json()
        results = data.get("results", [])
        if pages == 0:
            log.info(f"[openalex] {q.get('label')} total={data.get('meta',{}).get('count')} ({q['mode']})")
        for w in results:
            L.append_jsonl(Path(run)/"raw_candidates.jsonl", L.candidate(
                doi=w.get("doi"), title=w.get("title") or "", authors=L.oa_authors(w),
                year=w.get("publication_year"),
                venue=L.oa_venue(w),
                abstract=L.reconstruct_abstract(w.get("abstract_inverted_index")),
                cited_by=w.get("cited_by_count"), source="openalex",
                url=w.get("doi") or w.get("id",""), extra={"query": q.get("label")}))
            cands += 1
        cursor = data.get("meta", {}).get("next_cursor")
        pages += 1
        if not cursor or not results: break
        params["cursor"] = cursor
    log.ok(f"[openalex] {q.get('label')}: {cands} candidates over {pages} page(s)")
    summ["openalex_candidates"] += cands

def _s2_emit(run, w, q):
    ext = w.get("externalIds") or {}
    L.append_jsonl(Path(run)/"raw_candidates.jsonl", L.candidate(
        doi=ext.get("DOI"), title=w.get("title") or "",
        authors=[a.get("name","") for a in (w.get("authors") or [])],
        year=w.get("year"), venue=w.get("venue",""), abstract=w.get("abstract") or "",
        cited_by=w.get("citationCount"), source="s2",
        url=("https://doi.org/"+ext["DOI"]) if ext.get("DOI") else "",
        extra={"query": q.get("label"), "arxiv": ext.get("ArXiv"), "pmid": ext.get("PubMed")}))

def s2_run(http, log, run, q, per_page, max_pages, key, summ):
    cands = 0
    fields = "title,year,externalIds,abstract,authors,citationCount,venue"
    headers = {"x-api-key": key} if key else None
    qq = urllib.parse.quote(q["q"])
    if q["mode"] == "bulk":
        # bulk: token-paginated
        url = f"https://api.semanticscholar.org/graph/v1/paper/search/bulk?query={qq}&fields={fields}"
        for page in range(max_pages):
            r = http.get(url, headers=headers)
            if r is None or r.status_code != 200:
                log.error(f"[s2] {q.get('label')} page {page}: status {getattr(r,'status_code','ERR')}"); break
            data = r.json()
            for w in data.get("data", []) or []: _s2_emit(run, w, q); cands += 1
            tok = data.get("token")
            if not tok or not data.get("data"): break
            url = f"https://api.semanticscholar.org/graph/v1/paper/search/bulk?query={qq}&fields={fields}&token={tok}"
    else:
        # relevance: offset-paginated (offset+limit capped at 1000 by the API)
        for page in range(max_pages):
            offset = page * per_page
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={qq}&offset={offset}&limit={per_page}&fields={fields}"
            r = http.get(url, headers=headers)
            if r is None or r.status_code != 200:
                log.error(f"[s2] {q.get('label')} page {page}: status {getattr(r,'status_code','ERR')}"); break
            data = r.json()
            batch = data.get("data", []) or []
            for w in batch: _s2_emit(run, w, q); cands += 1
            if not batch or data.get("next") is None: break
    log.ok(f"[s2] {q.get('label')}: {cands} candidates")
    summ["s2_candidates"] += cands

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--queries", required=True)
    ap.add_argument("--per-page", type=int, default=50); ap.add_argument("--max-pages", type=int, default=4)
    a = ap.parse_args()
    run = Path(a.run); run.mkdir(parents=True, exist_ok=True)
    log = L.Log(run)
    queries = json.loads(Path(a.queries).read_text())
    summ = {"started": L.now(), "status": "running", "openalex_candidates": 0, "s2_candidates": 0,
            "openalex_credits": 0, "queries": queries}
    L.write_json(run/"search_summary.json", summ)
    log.info(f"search.py start · OA queries={len(queries.get('openalex',[]))} · S2 queries={len(queries.get('s2',[]))}")

    oa_http = L.Http(log, min_interval=0.15, source="openalex")
    s2_http = L.Http(log, min_interval=1.25, source="s2")  # self-throttle ~1 req/s
    oakey, s2key = L.openalex_key(), L.s2_key()
    log.info(f"keys: openalex={'yes' if oakey else 'NO'} s2={'yes' if s2key else 'keyless'}")

    for q in queries.get("openalex", []):
        oa_run(oa_http, log, run, q, a.per_page, a.max_pages, oakey, summ)
        L.write_json(run/"search_summary.json", summ)
    for q in queries.get("s2", []):
        if q.get("mode") not in ("bulk", "relevance"):
            log.error(f"[s2] {q.get('label')}: unknown mode {q.get('mode')!r} (use bulk|relevance); skipped"); continue
        s2_run(s2_http, log, run, q, a.per_page, a.max_pages, s2key, summ)
        L.write_json(run/"search_summary.json", summ)

    summ.update({"status": "done", "finished": L.now(),
                 "http_openalex_requests": oa_http.n_requests, "http_s2_requests": s2_http.n_requests,
                 "http_429s": oa_http.n_429 + s2_http.n_429})
    L.write_json(run/"search_summary.json", summ)
    log.ok(f"search.py done · OA={summ['openalex_candidates']} S2={summ['s2_candidates']} "
           f"credits≈{summ['openalex_credits']} 429s={summ['http_429s']}")

if __name__ == "__main__":
    main()
