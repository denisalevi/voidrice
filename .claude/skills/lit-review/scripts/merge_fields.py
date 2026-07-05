#!/usr/bin/env python3
"""merge_fields.py — safely join an LLM-produced {id: {fields}} map into classified.json.

The §6 audit pipeline (relevance notes, curated flag, audit flags, retraction) is the most
expensive stage's output and used to be hand-merged by the orchestrating LLM — if that merge
slipped, the page silently showed zero curated/relevance. This script makes the write path
deterministic and REPORTS matched/unmatched so a bad merge is loud, not silent.

Input map shape (JSON object). Keys are DOI (normalized) OR the candidate id from build_html's
cand_id() (norm-title|surname|year), values are the fields to set:
  { "10.1/aaa": {"relevance":"…","curated":true,"audit":["core"]},
    "t:sometitle|smith|2020": {"relevance":"…"} }

Usage:
  merge_fields.py --run <run> --map <fields.json> [--fields relevance,curated,audit,retraction,relevance_model,discovery,origin]
  # or pass the map on stdin with --map -

Writes classified.json in place. Prints matched / unmatched counts and any map keys that hit nothing.
"""
import argparse, json, re, sys
from pathlib import Path

DEFAULT_FIELDS = ["relevance", "relevance_model", "curated", "audit",
                  "retraction", "discovery", "origin", "provenance"]

def norm_doi(doi):
    if not doi: return None
    d = str(doi).strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d or None

def cand_id(c):
    """MUST match build_html.cand_id(): DOI if present, else t:normtitle|surname|year."""
    doi = (c.get("doi") or "").strip().lower()
    if doi: return doi
    t = re.sub(r"[^a-z0-9]+", "", (c.get("title") or "").lower())[:60]
    au = (c.get("authors") or ["?"])[0]
    su = re.sub(r"[^a-z]", "", (au.split(",")[0] if "," in au else au.split(" ")[-1]).lower())
    return f"t:{t}|{su}|{c.get('year') or '?'}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--map", required=True, help="path to {id: {fields}} JSON, or '-' for stdin")
    ap.add_argument("--fields", default=",".join(DEFAULT_FIELDS),
                    help="comma-separated fields allowed to be written")
    a = ap.parse_args()
    run = Path(a.run)
    fields = [f.strip() for f in a.fields.split(",") if f.strip()]

    raw = sys.stdin.read() if a.map == "-" else Path(a.map).read_text()
    fmap = json.loads(raw)
    if not isinstance(fmap, dict):
        sys.exit("map must be a JSON object {id: {fields}}")
    # normalize map keys: DOIs get norm_doi; t:… keys pass through
    norm_map = {}
    for k, v in fmap.items():
        nk = norm_doi(k) if not str(k).startswith("t:") else k
        norm_map[nk or k] = v

    cl = json.loads((run / "classified.json").read_text())
    buckets = [b for b in ("new", "new_no_abstract", "uncertain") if b in cl]

    matched, hit_keys = 0, set()
    for b in buckets:
        for c in cl[b]:
            for key in (norm_doi(c.get("doi")), cand_id(c)):
                if key and key in norm_map:
                    vals = norm_map[key]
                    for f in fields:
                        if f in vals:
                            c[f] = vals[f]
                    matched += 1
                    hit_keys.add(key)
                    break  # DOI preferred; don't double-apply

    unmatched = [k for k in norm_map if k not in hit_keys]
    (run / "classified.json").write_text(json.dumps(cl, ensure_ascii=False, indent=1))
    print(f"merge_fields: map_entries={len(norm_map)} matched_candidates={matched} "
          f"unmatched_map_keys={len(unmatched)}")
    if unmatched:
        print("  UNMATCHED (first 15 — these fields were NOT applied to any candidate):")
        for k in unmatched[:15]:
            print(f"    {k}")
    # loud signal if a big write silently hit nothing
    if norm_map and matched == 0:
        sys.exit("ERROR: 0 candidates matched — check id format (DOI vs t:… ) before trusting the page")

if __name__ == "__main__":
    main()
