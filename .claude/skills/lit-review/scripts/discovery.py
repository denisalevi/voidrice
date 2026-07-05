#!/usr/bin/env python3
"""discovery.py — cross-domain candidate search from analogy queries (P6a).

The default sideways discovery (S2 recommendations, embedding similarity) is all PROXIMITY: it
finds nearby vocabulary, structurally missing "same mechanism, different field". This stage takes
domain-neutral ANALOGY QUERIES (produced by the orchestrating LLM: "name fields with an isomorphic
problem + query strings") and searches them under TIGHT caps, tagging every hit so the UI can group
and (optionally) note them separately.

Volume control — this must NOT add thousands of papers:
  - each query is a 1-credit OpenAlex title/abstract FILTER (never the 10-credit search=)
  - per_page small, max_pages 1 by default → ≤ per_page hits per query
  - tags each candidate origin="cross-domain" + discovery={field,query} for grouping/capping later

Input --queries JSON: {"fields":[{"field":"econometrics","queries":["structural break detection",
"regime switching model"]}, ...]}

Usage:
  discovery.py --run <run> --queries <analogy.json> [--from 2015-01-01] [--per-page 20] [--max-pages 1]
Appends to <run>/raw_candidates.jsonl, updates <run>/discovery_summary.json.
"""
import argparse, json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

SEL = "id,doi,title,publication_year,authorships,abstract_inverted_index,cited_by_count,primary_location"

def run_query(http, log, run, field, q, frm, per_page, max_pages, key, summ):
    base = "https://api.openalex.org/works"
    # title OR abstract search as a 1-credit filter; date-bounded
    filt = f"title.search:{q}" + (f",from_publication_date:{frm}" if frm else "")
    params = {"filter": filt, "per-page": per_page, "select": SEL, "cursor": "*"}
    if key: params["api_key"] = key
    n, pages = 0, 0
    while pages < max_pages:
        url = base + "?" + urllib.parse.urlencode(params)
        summ["openalex_credits"] += L.oa_credit_cost(url)
        r = http.get(url)
        if r is None or r.status_code != 200:
            log.error(f"[discovery] {field}:{q!r} page {pages}: status {getattr(r,'status_code','ERR')}"); break
        data = r.json()
        for w in data.get("results", []):
            c = L.candidate(
                doi=w.get("doi"), title=w.get("title") or "", authors=L.oa_authors(w),
                year=w.get("publication_year"), venue=L.oa_venue(w),
                abstract=L.reconstruct_abstract(w.get("abstract_inverted_index")),
                cited_by=w.get("cited_by_count"), source="discovery",
                url=w.get("doi") or w.get("id", ""),
                extra={"query": f"analogy:{field}:{q}", "field": field})
            c["origin"] = "cross-domain"
            c["discovery"] = {"field": field, "query": q}
            L.append_jsonl(Path(run)/"raw_candidates.jsonl", c)
            n += 1
        nxt = data.get("meta", {}).get("next_cursor")
        pages += 1
        if not nxt: break
        params["cursor"] = nxt
    log.ok(f"[discovery] {field}:{q!r}: {n} candidates")
    summ["candidates"] += n
    summ["by_field"][field] = summ["by_field"].get(field, 0) + n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--from", dest="frm", default="2015-01-01")
    ap.add_argument("--per-page", type=int, default=20)
    ap.add_argument("--max-pages", type=int, default=1)
    a = ap.parse_args()
    run = Path(a.run); log = L.Log(run)
    spec = json.loads(Path(a.queries).read_text())
    key = L.openalex_key()
    http = L.Http(log, min_interval=0.1, source="discovery")
    summ = {"started": L.now(), "status": "running", "candidates": 0,
            "openalex_credits": 0, "by_field": {}}
    L.write_json(run/"discovery_summary.json", summ)
    fields = spec.get("fields", [])
    log.info(f"discovery.py start · fields={len(fields)} · per_page={a.per_page} max_pages={a.max_pages}")
    for f in fields:
        field = f.get("field", "?")
        for q in f.get("queries", []):
            run_query(http, log, run, field, q, a.frm, a.per_page, a.max_pages, key, summ)
            L.write_json(run/"discovery_summary.json", summ)
    summ["status"] = "done"
    L.write_json(run/"discovery_summary.json", summ)
    log.ok(f"discovery.py done · candidates={summ['candidates']} credits≈{summ['openalex_credits']} "
           f"by_field={summ['by_field']}")

if __name__ == "__main__":
    main()
