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
  dedup_verify.py --run <run> [--fuzzy 0.92] [--verify-limit 1000]

known_set.json shape (list): [{"doi":"10.x/y","title":"...","authors":["Surname, Given",...],"year":2020,"key":"ABC"}]
"""
import argparse, json, sys, difflib, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

# ---------- D2: drop non-paper editorial artifacts (eLife peer-review sub-DOIs, versioned
# assessments, Faculty-Opinions recommendations) that snowball/indexes pull in as fake candidates.
_ARTIFACT_DOI_RES = [
    re.compile(r"\.sa\d+$", re.I),                     # eLife peer-review sub-DOI (…​.sa1/.sa2)
    re.compile(r"10\.7554/elife\.\d+\.\d{3}$", re.I),  # eLife versioned assessment DOI (.<3digits>)
    re.compile(r"^10\.3410/f\.", re.I),                # Faculty Opinions recommendation
]
_ARTIFACT_TITLE_RE = re.compile(
    r"^\s*(decision letter|author response|reviewer\s*#|editor'?s?\s+(evaluation|assessment)"
    r"|elife assessment|faculty opinions recommendation)", re.I)

def is_editorial_artifact(c):
    """True if the candidate is an editorial/peer-review artifact, not a real paper (D2)."""
    doi = (c.get("doi") or "").strip()
    if doi and any(rx.search(doi) for rx in _ARTIFACT_DOI_RES):
        return True
    title = c.get("title") or ""
    return bool(_ARTIFACT_TITLE_RE.match(title))


def merge_key(c):
    d = L.norm_doi(c.get("doi"))
    if d: return ("doi", d)
    nt = L.norm_title(c.get("title"))
    if nt: return ("tay", nt, L.first_author_surname(c.get("authors")), c.get("year"))
    # under-identified (no DOI, no title): key on URL so distinct papers don't collapse into one
    return ("url", c.get("url") or id(c))

def build_known_index(known):
    by_doi = {}; titles = []  # titles: list of (normtitle, surname, year, key)
    by_surname = {}           # surname -> list of title tuples (blocking index for fast fuzzy)
    for k in known:
        d = L.norm_doi(k.get("doi"))
        if d: by_doi[d] = k
        tup = (L.norm_title(k.get("title")), L.first_author_surname(k.get("authors")), k.get("year"), k.get("key"))
        titles.append(tup)
        by_surname.setdefault(tup[1], []).append(tup)
    return by_doi, titles, by_surname

def classify(c, by_doi, titles, fuzzy, by_surname=None):
    d = L.norm_doi(c.get("doi"))
    if d and d in by_doi:
        return "known", {"match": "doi", "zotero_key": by_doi[d].get("key")}
    nt = L.norm_title(c.get("title")); sa = L.first_author_surname(c.get("authors")); yr = c.get("year")
    # Blocking: only fuzzy-compare against known titles that share the candidate's first-author
    # surname (plus the no-surname bucket, since known/candidate author lists can be empty). This
    # turns an O(candidates × known) scan into O(candidates × per-surname), ~1000× fewer compares
    # on a large library, without changing which pairs can match (a real dup shares first author).
    if by_surname is not None:
        cand = list(by_surname.get(sa, [])) if sa else list(titles)
        cand += by_surname.get("", [])       # known items with no parseable author
        scan = cand
    else:
        scan = titles
    best = (0.0, None)
    for (ktitle, ksurname, kyear, kkey) in scan:
        if not ktitle or not nt: continue
        ratio = difflib.SequenceMatcher(None, nt, ktitle).ratio()
        if ratio > best[0]: best = (ratio, (ratio, ksurname, kyear, kkey))
    if best[1]:
        ratio, ksurname, kyear, kkey = best[1]
        author_ok = (not sa or not ksurname or sa == ksurname)
        # years must agree (±1 for preprint/version drift); unknown/blank/non-numeric year on either side = can't confirm
        def _yr(v):
            try: return int(str(v).strip())
            except (TypeError, ValueError): return None
        y1, y2 = _yr(yr), _yr(kyear)
        year_ok = (y1 is not None and y2 is not None and abs(y1 - y2) <= 1)
        if ratio >= fuzzy and author_ok and year_ok:
            return "known", {"match": f"title~{ratio:.2f}+year", "zotero_key": kkey}
        if ratio >= 0.80:  # strong title match but year/author not confirmed → human decides
            reason = f"title~{ratio:.2f}" + ("" if year_ok else " (year differs/unknown)")
            return "uncertain", {"match": reason, "zotero_key": kkey}
    return "new", {"match": None}

TRUSTED_SOURCES = ("openalex", "crossref", "s2", "discovery")  # indexes that only return real papers
# ("discovery" candidates come from OpenAlex filter search → real by construction, like "openalex")

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
    Order (SKILL contract): DOI → arXiv → PMID → Crossref title search."""
    d = L.norm_doi(c.get("doi"))
    if d:
        r = http.get(f"https://api.crossref.org/works/{d}")
        if r is not None and r.status_code == 200: return {"verified": True, "via": "crossref-doi"}
        if r is not None and r.status_code == 404: return {"verified": False, "via": "crossref-doi-404"}
        return {"verified": False, "via": "doi-inconclusive"}
    # no DOI → try arXiv / PMID identifiers before falling back to a fuzzy title search
    ax = c.get("arxiv") or (c.get("extra") or {}).get("arxiv")
    if ax:
        r = http.get(f"https://export.arxiv.org/abs/{L.urllib.parse.quote(str(ax))}")
        if r is not None and r.status_code == 200:
            return {"verified": True, "via": "arxiv", "no_doi": True}
    pm = c.get("pmid") or (c.get("extra") or {}).get("pmid")
    if pm:
        r = http.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={L.urllib.parse.quote(str(pm))}&retmode=json")
        if r is not None and r.status_code == 200:
            try:
                res = r.json().get("result", {})
                if str(pm) in res and res[str(pm)].get("title"):
                    return {"verified": True, "via": "pmid", "no_doi": True}
            except Exception:
                pass
    t = c.get("title", "")
    if t:
        r = http.get(f"https://api.crossref.org/works?query.bibliographic={L.urllib.parse.quote(t)}&rows=1&mailto={L.MAILTO}")
        if r is not None and r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            cand_title = (items[0].get("title") or [""])[0] if items else ""
            if items and cand_title and difflib.SequenceMatcher(None, L.norm_title(t), L.norm_title(cand_title)).ratio() > 0.9:
                return {"verified": True, "via": "crossref-title", "found_doi": items[0].get("DOI")}
    return {"verified": False, "via": "no-match"}

# ---------- D3: collapse preprint↔published (and multi-version) twins within a bucket ----------
_PREPRINT_DOI_RE = re.compile(r"^10\.1101/", re.I)       # bioRxiv/medRxiv
_VERSION_DOI_RE  = re.compile(r"10\.7554/elife\.\d+\.\d+$", re.I)  # eLife versioned (…​.1/.2/.4)

def _is_published_doi(doi):
    """Prefer a real journal DOI over a preprint/versioned one when picking a cluster keeper."""
    d = (doi or "").strip()
    if not d: return False
    return not (_PREPRINT_DOI_RE.match(d) or _VERSION_DOI_RE.search(d))

def collapse_twins(items, threshold=0.92):
    """Cluster candidates by first-author surname + high title similarity; within each cluster keep
    ONE row (prefer a published DOI, then highest cited_by), collapse the rest — annotating the kept
    row so the UI can show a 'N versions merged' chip and pointing dropped rows at the keeper (D3).
    Conservative: only same-surname candidates with title ratio >= threshold cluster together."""
    by_surname = {}
    for c in items:
        by_surname.setdefault(L.first_author_surname(c.get("authors")), []).append(c)
    keep, collapsed = [], []
    for surname, group in by_surname.items():
        used = [False] * len(group)
        for i, ci in enumerate(group):
            if used[i]: continue
            cluster = [ci]; used[i] = True
            nti = L.norm_title(ci.get("title"))
            for j in range(i + 1, len(group)):
                if used[j]: continue
                ntj = L.norm_title(group[j].get("title"))
                if not nti or not ntj: continue
                if difflib.SequenceMatcher(None, nti, ntj).ratio() >= threshold:
                    cluster.append(group[j]); used[j] = True
            if len(cluster) == 1:
                keep.append(ci); continue
            # pick keeper: published DOI first, then most-cited, then longest author list
            cluster.sort(key=lambda c: (_is_published_doi(c.get("doi")),
                                        (c.get("cited_by") or 0),
                                        len(c.get("authors") or [])), reverse=True)
            keeper, others = cluster[0], cluster[1:]
            # fold richer metadata from the dropped twins into the keeper
            for o in others:
                for f in ("abstract", "venue", "year", "url"):
                    if not keeper.get(f) and o.get(f): keeper[f] = o[f]
                if (o.get("cited_by") or 0) > (keeper.get("cited_by") or 0):
                    keeper["cited_by"] = o["cited_by"]
                keeper.setdefault("sources", [])
                keeper["sources"] = sorted(set(keeper["sources"]) | set(o.get("sources", [])))
            keeper["merged_versions"] = [
                {"title": o.get("title"), "doi": o.get("doi"), "year": o.get("year")} for o in others]
            keep.append(keeper)
            for o in others:
                o["collapsed_into"] = keeper.get("doi") or keeper.get("title")
                collapsed.append(o)
    return keep, collapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--fuzzy", type=float, default=0.92)
    ap.add_argument("--verify-limit", type=int, default=1000)
    a = ap.parse_args()
    run = Path(a.run); log = L.Log(run)
    raw = L.read_jsonl(run/"raw_candidates.jsonl")
    known = json.loads((run/"known_set.json").read_text()) if (run/"known_set.json").exists() else []
    log.info(f"dedup_verify start · raw={len(raw)} · known_set={len(known)}")

    # 1. merge dups within candidates (dropping editorial artifacts first — D2)
    n_artifacts = 0
    raw_papers = []
    for c in raw:
        if is_editorial_artifact(c):
            n_artifacts += 1
        else:
            raw_papers.append(c)
    if n_artifacts:
        log.info(f"D2: dropped {n_artifacts} editorial artifacts (eLife peer-review/assessment, Faculty Opinions)")
    merged = {}
    for c in raw_papers:
        k = merge_key(c)
        if k in merged:
            m = merged[k]
            m["sources"] = sorted(set(m["sources"]) | set(c.get("sources", [])))
            # P4b: merge best-known value field-by-field, not just abstract+doi.
            if not m.get("abstract") and c.get("abstract"): m["abstract"] = c["abstract"]
            if not m.get("doi") and c.get("doi"): m["doi"] = L.norm_doi(c["doi"])
            if not m.get("arxiv") and c.get("arxiv"): m["arxiv"] = c["arxiv"]
            if not m.get("pmid") and c.get("pmid"): m["pmid"] = c["pmid"]
            if not m.get("venue") and c.get("venue"): m["venue"] = c["venue"]
            if not m.get("url") and c.get("url"): m["url"] = c["url"]
            if not m.get("year") and c.get("year"): m["year"] = c["year"]
            # higher citation count and longer author list are the better records
            if (c.get("cited_by") or 0) > (m.get("cited_by") or 0): m["cited_by"] = c["cited_by"]
            if len(c.get("authors") or []) > len(m.get("authors") or []): m["authors"] = c["authors"]
            m.setdefault("provenance", []).append(c.get("extra", {}))
        else:
            c["doi"] = L.norm_doi(c.get("doi")); c.setdefault("provenance", [c.get("extra", {})])
            merged[k] = c
    log.ok(f"merged {len(raw)} raw → {len(merged)} unique candidates")

    # 2+3. classify
    by_doi, titles, by_surname = build_known_index(known)
    buckets = {"new": [], "uncertain": [], "known": []}
    for c in merged.values():
        b, info = classify(c, by_doi, titles, a.fuzzy, by_surname)
        c["classification"] = info; buckets[b].append(c)
    log.ok(f"classified · new={len(buckets['new'])} uncertain={len(buckets['uncertain'])} known={len(buckets['known'])}")

    # D3: collapse preprint↔published / multi-version twins within the NEW bucket (owned/known
    # twins are deduped separately). Keep one keeper per work; log the collapsed ones.
    buckets["new"], collapsed_twins = collapse_twins(buckets["new"])
    if collapsed_twins:
        log.info(f"D3: collapsed {len(collapsed_twins)} preprint/version twins in NEW → {len(buckets['new'])} distinct works")

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
    # drop those we ATTEMPTED and that FAILED (verification present & not verified) — from BOTH
    # new AND uncertain (P2c). Un-attempted (verification is None) are kept + flagged in the UI.
    dropped = []
    def prune(items, label):
        kept, drp = [], []
        for c in items:
            v = c.get("verification")
            if v is None or v.get("verified"):
                kept.append(c)
            else:
                drp.append({"title": c.get("title"), "doi": c.get("doi"), "reason": v.get("via"), "bucket": label})
        if drp:
            log.warn(f"dropped {len(drp)} {label} candidates that were checked and did NOT resolve (likely fabricated)")
        dropped.extend(drp)
        return kept
    buckets["new"] = prune(buckets["new"], "new")
    buckets["uncertain"] = prune(buckets["uncertain"], "uncertain")

    # sort each bucket by cited_by desc then year desc for a sensible reading order
    for b in buckets.values():
        b.sort(key=lambda c: ((c.get("cited_by") or 0), (c.get("year") or 0)), reverse=True)

    L.write_json(run/"classified.json", buckets)
    summ = {"finished": L.now(), "raw": len(raw), "merged": len(merged),
            "editorial_artifacts_dropped": n_artifacts,
            "version_twins_collapsed": len(collapsed_twins),
            "new": len(buckets["new"]), "uncertain": len(buckets["uncertain"]),
            "known": len(buckets["known"]), "dropped": dropped,
            "http_crossref_requests": http.n_requests}
    L.write_json(run/"dedup_summary.json", summ)
    log.ok(f"dedup_verify done · NEW={summ['new']} uncertain={summ['uncertain']} known={summ['known']} dropped={len(dropped)}")

if __name__ == "__main__":
    main()
