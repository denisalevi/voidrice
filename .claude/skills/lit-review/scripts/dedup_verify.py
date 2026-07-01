#!/usr/bin/env python3
"""dedup_verify.py — merge raw candidates, subtract the Zotero known set, verify NEW ones exist.

Steps:
  1. Load <run>/raw_candidates.jsonl; merge duplicates within candidates (by DOI, else title+author+year),
     unioning sources/provenance.
  2. Load <run>/known_set.json (dumped by the LLM via MCP): items already in Zotero.
  3. Classify each merged candidate: known (in Zotero) / uncertain (fuzzy near-match) / new.
  4. Verify NEW candidates resolve via Crossref (DOI HEAD/GET). Unresolvable + no DOI + no title
     match anywhere => dropped as likely-fabricated (logged).
  5. Write <run>/classified.json + <run>/dedup_summary.json.

Uses stdlib difflib for fuzzy title matching (no external deps).

Usage:
  dedup_verify.py --run <run> [--fuzzy 0.92] [--verify-limit 400]

known_set.json shape (list): [{"doi":"10.x/y","title":"...","authors":["Surname, Given",...],"year":2020,"key":"ABC"}]
"""
import argparse, json, sys, difflib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

def merge_key(c):
    d = L.norm_doi(c.get("doi"))
    if d: return ("doi", d)
    nt = L.norm_title(c.get("title"))
    if nt: return ("tay", nt, L.first_author_surname(c.get("authors")), c.get("year"))
    # under-identified (no DOI, no title): key on URL so distinct papers don't collapse into one
    return ("url", c.get("url") or id(c))

def build_known_index(known):
    by_doi = {}; titles = []  # titles: list of (normtitle, surname, year, key)
    for k in known:
        d = L.norm_doi(k.get("doi"))
        if d: by_doi[d] = k
        titles.append((L.norm_title(k.get("title")), L.first_author_surname(k.get("authors")), k.get("year"), k.get("key")))
    return by_doi, titles

def classify(c, by_doi, titles, fuzzy):
    d = L.norm_doi(c.get("doi"))
    if d and d in by_doi:
        return "known", {"match": "doi", "zotero_key": by_doi[d].get("key")}
    nt = L.norm_title(c.get("title")); sa = L.first_author_surname(c.get("authors")); yr = c.get("year")
    best = (0.0, None)
    for (ktitle, ksurname, kyear, kkey) in titles:
        if not ktitle or not nt: continue
        ratio = difflib.SequenceMatcher(None, nt, ktitle).ratio()
        if ratio > best[0]: best = (ratio, (ratio, ksurname, kyear, kkey))
    if best[1]:
        ratio, ksurname, kyear, kkey = best[1]
        author_ok = (not sa or not ksurname or sa == ksurname)
        # years must agree (±1 for preprint/version drift); unknown year on either side = can't confirm
        year_ok = (yr is not None and kyear is not None and abs(int(yr) - int(kyear)) <= 1)
        if ratio >= fuzzy and author_ok and year_ok:
            return "known", {"match": f"title~{ratio:.2f}+year", "zotero_key": kkey}
        if ratio >= 0.80:  # strong title match but year/author not confirmed → human decides
            reason = f"title~{ratio:.2f}" + ("" if year_ok else " (year differs/unknown)")
            return "uncertain", {"match": reason, "zotero_key": kkey}
    return "new", {"match": None}

TRUSTED_SOURCES = ("openalex", "crossref", "s2")  # indexes that only return real papers

def verified_by_source(c):
    """A candidate from a trusted index is real by construction — no HTTP check needed.
    DOI-bearing → fully verified. No DOI but trusted source → verified-but-no-doi (real, yet
    NOT auto-addable to Zotero, which needs a DOI; flagged for the human). Returns a
    verification dict, or None if an active check is warranted (untrusted origin)."""
    trusted = any(s.split(":")[0] in TRUSTED_SOURCES or s.split(":")[0] == "snowball"
                  for s in c.get("sources", []))
    if not trusted:
        return None
    if L.norm_doi(c.get("doi")):
        return {"verified": True, "via": "source"}
    return {"verified": True, "via": "source-no-doi", "no_doi": True}

def verify_active(http, log, c):
    """Active fallback for candidates NOT verifiable by source (no DOI, or untrusted origin).
    DOI → Crossref GET; else Crossref title search."""
    d = L.norm_doi(c.get("doi"))
    if d:
        r = http.get(f"https://api.crossref.org/works/{d}")
        if r is not None and r.status_code == 200: return {"verified": True, "via": "crossref-doi"}
        if r is not None and r.status_code == 404: return {"verified": False, "via": "crossref-doi-404"}
        return {"verified": False, "via": "doi-inconclusive"}
    t = c.get("title", "")
    if t:
        r = http.get(f"https://api.crossref.org/works?query.bibliographic={L.urllib.parse.quote(t)}&rows=1&mailto={L.MAILTO}")
        if r is not None and r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            cand_title = (items[0].get("title") or [""])[0] if items else ""
            if items and cand_title and difflib.SequenceMatcher(None, L.norm_title(t), L.norm_title(cand_title)).ratio() > 0.9:
                return {"verified": True, "via": "crossref-title", "found_doi": items[0].get("DOI")}
    return {"verified": False, "via": "no-match"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--fuzzy", type=float, default=0.92)
    ap.add_argument("--verify-limit", type=int, default=1000)
    a = ap.parse_args()
    run = Path(a.run); log = L.Log(run)
    raw = L.read_jsonl(run/"raw_candidates.jsonl")
    known = json.loads((run/"known_set.json").read_text()) if (run/"known_set.json").exists() else []
    log.info(f"dedup_verify start · raw={len(raw)} · known_set={len(known)}")

    # 1. merge dups within candidates
    merged = {}
    for c in raw:
        k = merge_key(c)
        if k in merged:
            m = merged[k]
            m["sources"] = sorted(set(m["sources"]) | set(c.get("sources", [])))
            if not m.get("abstract") and c.get("abstract"): m["abstract"] = c["abstract"]
            if not m.get("doi") and c.get("doi"): m["doi"] = L.norm_doi(c["doi"])
            m.setdefault("provenance", []).append(c.get("extra", {}))
        else:
            c["doi"] = L.norm_doi(c.get("doi")); c.setdefault("provenance", [c.get("extra", {})])
            merged[k] = c
    log.ok(f"merged {len(raw)} raw → {len(merged)} unique candidates")

    # 2+3. classify
    by_doi, titles = build_known_index(known)
    buckets = {"new": [], "uncertain": [], "known": []}
    for c in merged.values():
        b, info = classify(c, by_doi, titles, a.fuzzy)
        c["classification"] = info; buckets[b].append(c)
    log.ok(f"classified · new={len(buckets['new'])} uncertain={len(buckets['uncertain'])} known={len(buckets['known'])}")

    # 4. verify NEW (and uncertain, so the human sees verification too).
    # IMPORTANT: only candidates we actually ATTEMPT to verify get a verification record.
    # We drop ONLY attempted-and-failed items (likely fabricated). Un-attempted items (beyond
    # --verify-limit) are kept as new with verification=None → shown as "unverified" in the UI,
    # never silently dropped. Candidates WITH a DOI are cheap/reliable to check, so prioritise them.
    http = L.Http(log, min_interval=0.1, source="crossref")
    pool = buckets["new"] + buckets["uncertain"]
    # Fast path: verify-by-source for trusted-index DOIs (no HTTP). Active-check only the rest.
    need_active = []
    n_by_source = 0
    for c in pool:
        v = verified_by_source(c)
        if v is not None:
            c["verification"] = v; n_by_source += 1
        else:
            need_active.append(c)
    log.ok(f"verified-by-source: {n_by_source} · need active check: {len(need_active)}")
    to_verify = need_active[:a.verify_limit]
    for c in to_verify:
        v = verify_active(http, log, c); c["verification"] = v
        if v.get("found_doi") and not c.get("doi"): c["doi"] = L.norm_doi(v["found_doi"])
    n_unattempted = max(0, len(need_active) - len(to_verify))
    if n_unattempted:
        log.info(f"{n_unattempted} candidates beyond --verify-limit left unverified (kept, flagged in UI)")
    # drop from NEW only those we ATTEMPTED and that FAILED (verification present & not verified)
    kept_new, dropped = [], []
    for c in buckets["new"]:
        v = c.get("verification")
        if v is None or v.get("verified"):
            kept_new.append(c)  # keep verified OR not-yet-attempted
        else:
            dropped.append({"title": c.get("title"), "doi": c.get("doi"), "reason": v.get("via")})
    if dropped:
        log.warn(f"dropped {len(dropped)} candidates that were checked and did NOT resolve (likely fabricated)")
    buckets["new"] = kept_new

    # sort each bucket by cited_by desc then year desc for a sensible reading order
    for b in buckets.values():
        b.sort(key=lambda c: ((c.get("cited_by") or 0), (c.get("year") or 0)), reverse=True)

    L.write_json(run/"classified.json", buckets)
    summ = {"finished": L.now(), "raw": len(raw), "merged": len(merged),
            "new": len(buckets["new"]), "uncertain": len(buckets["uncertain"]),
            "known": len(buckets["known"]), "dropped": dropped,
            "http_crossref_requests": http.n_requests}
    L.write_json(run/"dedup_summary.json", summ)
    log.ok(f"dedup_verify done · NEW={summ['new']} uncertain={summ['uncertain']} known={summ['known']} dropped={len(dropped)}")

if __name__ == "__main__":
    main()
