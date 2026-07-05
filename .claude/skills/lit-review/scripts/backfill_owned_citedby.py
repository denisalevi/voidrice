#!/usr/bin/env python3
"""backfill_owned_citedby.py — fetch cited_by counts for OWNED (in-Zotero) items.

Zotero stores no citation counts, so owned items arrive with cited_by=None and Citations-sort
treats them as a no-op — making them look different from new candidates. This backfills
cited_by for the 'known' bucket the SAME way new candidates get it (OpenAlex cited_by_count by
DOI, Semantic Scholar as fallback), so owned rows carry a real "cited N×" chip and sort like
any new row. Items with no DOI keep cited_by=None (unavoidable).

Usage:
  backfill_owned_citedby.py --run <run> [--bucket known]

Idempotent: only fetches for items whose cited_by is still None. Writes classified.json back.
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

def fetch_cited_by(http, doi, s2key=None):
    """OpenAlex cited_by_count by DOI, S2 citationCount as fallback. Returns int or None."""
    d = L.norm_doi(doi)
    if not d:
        return None
    # OpenAlex — same source new candidates use (search.py / snowball.py)
    r = http.get(f"https://api.openalex.org/works/https://doi.org/{d}?select=cited_by_count")
    if r is not None and r.status_code == 200:
        cb = r.json().get("cited_by_count")
        if cb is not None:
            return int(cb)
    # Semantic Scholar fallback
    hdr = {"x-api-key": s2key} if s2key else None
    r = http.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{d}?fields=citationCount", headers=hdr)
    if r is not None and r.status_code == 200:
        cc = r.json().get("citationCount")
        if cc is not None:
            return int(cc)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--bucket", default="known", help="which bucket to backfill (default: known)")
    a = ap.parse_args()
    run = Path(a.run); log = L.Log(run)
    b = json.loads((run/"classified.json").read_text())
    items = b.get(a.bucket, [])
    todo = [c for c in items if c.get("cited_by") is None and (c.get("doi") or "").strip()]
    nodoi = [c for c in items if not (c.get("doi") or "").strip()]
    log.info(f"backfill cited_by · bucket={a.bucket} total={len(items)} "
             f"need_lookup={len(todo)} no_doi(skipped)={len(nodoi)}")
    oakey, s2key = L.openalex_key(), L.s2_key()
    log.info(f"keys: openalex={'yes' if oakey else 'NO'} s2={'yes' if s2key else 'keyless'}")

    from concurrent.futures import ThreadPoolExecutor
    host_limiter = L.HostRateLimiter(default_interval=0.34, per_host={
        "api.semanticscholar.org": 1.05,
        "api.openalex.org": 0.15,
    })
    def work(c):
        h = L.Http(log, min_interval=0.0, max_retries=2, source="backfill-cited",
                   host_limiter=host_limiter)
        try:
            cb = fetch_cited_by(h, c.get("doi"), s2key)
            if cb is not None:
                c["cited_by"] = cb
                return 1
        except Exception as e:
            log.warn(f"cited_by fail {c.get('doi')}: {e}")
        return 0
    resolved = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        for r in ex.map(work, todo):
            resolved += r
    L.write_json(run/"classified.json", b)
    log.ok(f"cited_by backfill done · resolved={resolved}/{len(todo)} "
           f"still_null={sum(1 for c in items if c.get('cited_by') is None)} "
           f"(incl. {len(nodoi)} no-DOI)")

if __name__ == "__main__":
    main()
