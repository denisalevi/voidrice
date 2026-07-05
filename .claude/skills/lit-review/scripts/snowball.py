#!/usr/bin/env python3
"""snowball.py — expand from seed papers via the citation graph.

  forward  : papers that CITE the seed (derivative work)     [OpenAlex filter=cites:]
  backward : the seed's REFERENCES (foundations)             [OpenAlex referenced_works, id-hydrated]
  sideways : thematic siblings                               [S2 Recommendations API]

Appends to <run>/raw_candidates.jsonl, updates <run>/snowball_summary.json. Poll-friendly logs.

Usage:
  snowball.py --run <run> --seeds <seeds.json> --directions forward,backward,sideways [--from 2020-01-01] [--max-pages 5]

seeds.json: {"dois": ["10.1038/nn.2732", ...]}
"""
import argparse, json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

def oa_id_for_doi(http, log, doi, key, summ):
    url = f"https://api.openalex.org/works/https://doi.org/{doi}?select=id,referenced_works"
    if key: url += "&api_key=" + key
    summ["openalex_credits"] += L.oa_credit_cost(url)  # 0 (single record)
    r = http.get(url)
    if r is None or r.status_code != 200:
        log.warn(f"[snowball] no OpenAlex id for {doi}"); return None, []
    d = r.json()
    return d.get("id","").split("/")[-1], d.get("referenced_works", [])

def emit(run, w_doi, title, authors, year, venue, abstract, cited, direction, seed):
    L.append_jsonl(Path(run)/"raw_candidates.jsonl", L.candidate(
        doi=w_doi, title=title or "", authors=authors or [], year=year, venue=venue or "",
        abstract=abstract or "", cited_by=cited, source=f"snowball:{direction}",
        url=("https://doi.org/"+L.norm_doi(w_doi)) if w_doi else "",
        extra={"seed": seed, "direction": direction}))

def forward_oa(http, log, run, oaid, seed, frm, max_pages, key, summ):
    n = 0; base = "https://api.openalex.org/works"
    sel = "doi,title,publication_year,authorships,abstract_inverted_index,cited_by_count,primary_location"
    filt = f"cites:{oaid}" + (f",from_publication_date:{frm}" if frm else "")
    params = {"filter": filt, "per-page": 100, "select": sel, "sort": "publication_date:desc", "cursor": "*"}
    if key: params["api_key"] = key
    pages = 0
    while pages < max_pages:
        url = base + "?" + urllib.parse.urlencode(params)
        summ["openalex_credits"] += L.oa_credit_cost(url)
        r = http.get(url)
        if r is None or r.status_code != 200: break
        data = r.json(); res = data.get("results", [])
        for w in res:
            emit(run, w.get("doi"), w.get("title"), L.oa_authors(w), w.get("publication_year"),
                 L.oa_venue(w),
                 L.reconstruct_abstract(w.get("abstract_inverted_index")), w.get("cited_by_count"), "forward", seed)
            n += 1
        cur = data.get("meta",{}).get("next_cursor"); pages += 1
        if not cur or not res: break
        params["cursor"] = cur
    log.ok(f"[snowball/forward] {seed}: {n} citing papers"); summ["forward"] += n

def backward_oa(http, log, run, ref_ids, seed, key, summ):
    # hydrate referenced_works by id (FREE), batched via filter=openalex_id (1 credit/page)
    n = 0
    for i in range(0, len(ref_ids), 50):
        chunk = "|".join(rid.split("/")[-1] for rid in ref_ids[i:i+50])
        url = ("https://api.openalex.org/works?filter=openalex_id:" + chunk +
               "&per-page=50&select=doi,title,publication_year,authorships,abstract_inverted_index,cited_by_count,primary_location")
        if key: url += "&api_key=" + key
        summ["openalex_credits"] += L.oa_credit_cost(url)
        r = http.get(url)
        if r is None or r.status_code != 200: continue
        for w in r.json().get("results", []):
            emit(run, w.get("doi"), w.get("title"), L.oa_authors(w), w.get("publication_year"),
                 L.oa_venue(w),
                 L.reconstruct_abstract(w.get("abstract_inverted_index")), w.get("cited_by_count"), "backward", seed)
            n += 1
    log.ok(f"[snowball/backward] {seed}: {n} references"); summ["backward"] += n

def sideways_s2(http, log, run, seed, s2key, summ):
    n = 0
    headers = {"x-api-key": s2key} if s2key else None
    url = "https://api.semanticscholar.org/recommendations/v1/papers?fields=title,year,externalIds,abstract,authors,citationCount,venue"
    r = http.post(url, headers=headers, json_body={"positivePaperIds": [f"DOI:{seed}"], "negativePaperIds": []})
    if r is None or r.status_code != 200:
        log.warn(f"[snowball/sideways] {seed}: status {getattr(r,'status_code','ERR')}"); return
    for w in r.json().get("recommendedPapers", []) or []:
        ext = w.get("externalIds") or {}
        emit(run, ext.get("DOI"), w.get("title"), [a.get("name","") for a in (w.get("authors") or [])],
             w.get("year"), w.get("venue",""), w.get("abstract"), w.get("citationCount"), "sideways", seed)
        n += 1
    log.ok(f"[snowball/sideways] {seed}: {n} recommendations"); summ["sideways"] += n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--seeds", required=True)
    ap.add_argument("--directions", default="forward,backward,sideways")
    ap.add_argument("--from", dest="frm", default=None); ap.add_argument("--max-pages", type=int, default=5)
    a = ap.parse_args()
    run = Path(a.run); run.mkdir(parents=True, exist_ok=True)
    log = L.Log(run)
    dirs = set(d.strip() for d in a.directions.split(","))
    unknown = dirs - {"forward", "backward", "sideways"}
    if unknown: sys.exit(f"unknown --directions: {unknown} (use forward,backward,sideways)")
    seeds = json.loads(Path(a.seeds).read_text()).get("dois", [])
    seeds = [L.norm_doi(d) for d in seeds if d]
    summ = {"started": L.now(), "status": "running", "seeds": seeds, "directions": sorted(dirs),
            "forward": 0, "backward": 0, "sideways": 0, "openalex_credits": 0}
    L.write_json(run/"snowball_summary.json", summ)
    log.info(f"snowball.py start · seeds={len(seeds)} · directions={sorted(dirs)}")

    oa = L.Http(log, min_interval=0.15, source="openalex")
    s2 = L.Http(log, min_interval=1.25, source="s2")
    oakey, s2key = L.openalex_key(), L.s2_key()

    for seed in seeds:
        oaid, refs = (None, [])
        if {"forward","backward"} & dirs:
            oaid, refs = oa_id_for_doi(oa, log, seed, oakey, summ)
        if "forward" in dirs and oaid:
            forward_oa(oa, log, run, oaid, seed, a.frm, a.max_pages, oakey, summ)
        if "backward" in dirs and refs:
            backward_oa(oa, log, run, refs, seed, oakey, summ)
        if "sideways" in dirs:
            sideways_s2(s2, log, run, seed, s2key, summ)
        L.write_json(run/"snowball_summary.json", summ)

    summ.update({"status": "done", "finished": L.now(),
                 "http_429s": oa.n_429 + s2.n_429})
    L.write_json(run/"snowball_summary.json", summ)
    log.ok(f"snowball.py done · fwd={summ['forward']} back={summ['backward']} side={summ['sideways']} "
           f"credits≈{summ['openalex_credits']} 429s={summ['http_429s']}")

if __name__ == "__main__":
    main()
