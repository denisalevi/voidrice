#!/usr/bin/env python3
"""build_html.py — render <run>/classified.json into the interactive review page.

Usage:
  build_html.py --run <run> --name <review-name> --out <path.html> [--search-log "OpenAlex, S2, Crossref"]

Reads the template at ../templates/review.html, fills placeholders, writes the page.
Pulls credit total from search_summary.json + snowball_summary.json if present.
"""
import argparse, json, html, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

TPL = Path(__file__).parent.parent / "templates" / "review.html"

def esc(s): return html.escape(str(s or ""))

def chips(c, bucket):
    out = []
    for s in c.get("sources", []):
        out.append(f'<span class="chip">{esc(s)}</span>')
    v = c.get("verification")
    if bucket != "known":
        if v is None: out.append('<span class="chip">? not checked</span>')
        elif v.get("no_doi"): out.append('<span class="chip warn">✓ real · no DOI (manual add)</span>')
        elif v.get("verified"): out.append('<span class="chip ok">✓ verified</span>')
        else: out.append('<span class="chip warn">⚠ unverified</span>')
    if c.get("cited_by") is not None: out.append(f'<span class="chip">cited {c["cited_by"]}×</span>')
    ret = c.get("retraction")
    if ret: out.append('<span class="chip warn">⚠ RETRACTED</span>')
    cl = c.get("classification", {})
    if cl.get("match"): out.append(f'<span class="chip">{esc(cl["match"])}</span>')
    return "".join(out)

def row(c, bucket):
    doi = c.get("doi") or ""
    # only allow http(s) links in href; anything else (javascript:, data:, …) → "#"
    raw_link = ("https://doi.org/" + doi) if doi else (c.get("url") or "")
    link = raw_link if raw_link.startswith(("https://", "http://")) else "#"
    authors = ", ".join(esc(a) for a in c.get("authors", []) if a) or "—"  # ESCAPE each author
    meta = f'{authors} · {esc(c.get("year") or "?")}' + (f' · {esc(c.get("venue"))}' if c.get("venue") else "")
    abs = esc(c.get("abstract")) or "(no abstract)"
    # no-DOI candidates can't be auto-added (Zotero add needs a DOI) → offer Discuss/Reject only
    if bucket == "known":
        choice = ""
    elif doi:
        choice = ('<div class="choice">'
                  '<button data-c="add" onclick="choose(this,\'add\')">Add</button>'
                  '<button data-c="discuss" onclick="choose(this,\'discuss\')">Discuss</button>'
                  '<button data-c="reject" onclick="choose(this,\'reject\')">Reject</button></div>'
                  '<textarea class="note" placeholder="Note (why / for Zotero / to discuss)…"></textarea>')
    else:
        choice = ('<div class="choice"><span class="chip warn">no DOI — add manually in Zotero</span>'
                  '<button data-c="discuss" onclick="choose(this,\'discuss\')">Discuss</button>'
                  '<button data-c="reject" onclick="choose(this,\'reject\')">Reject</button></div>'
                  '<textarea class="note" placeholder="Note…"></textarea>')
    return (f'<article class="paper" data-doi="{esc(doi)}" data-decision="none" data-note="">'
            f'<div class="ptitle"><a href="{esc(link)}" target="_blank" rel="noopener">{esc(c.get("title"))}</a></div>'
            f'<div class="authors">{meta}</div>'
            f'<div class="chips">{chips(c, bucket)}</div>'
            f'<details class="abs"><summary>Abstract</summary><p>{abs}</p></details>'
            f'{choice}</article>')

def rows(cs, bucket):
    return "\n".join(row(c, bucket) for c in cs) if cs else '<p class="meta">none</p>'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--search-log", default="OpenAlex, Semantic Scholar, Crossref")
    a = ap.parse_args()
    run = Path(a.run)
    b = json.loads((run/"classified.json").read_text())
    credits = 0
    for f in ("search_summary.json", "snowball_summary.json"):
        p = run/f
        if p.exists():
            credits += json.loads(p.read_text()).get("openalex_credits", 0)
    tpl = TPL.read_text()
    out = (tpl.replace("{{REVIEW_NAME}}", esc(a.name))
              .replace("{{GENERATED}}", L.now())
              .replace("{{SEARCH_LOG}}", esc(a.search_log))
              .replace("{{CREDIT_SPEND}}", str(credits))
              .replace("{{ROWS_NEW}}", rows(b.get("new", []), "new"))
              .replace("{{ROWS_UNCERTAIN}}", rows(b.get("uncertain", []), "uncertain"))
              .replace("{{ROWS_KNOWN}}", rows(b.get("known", []), "known")))
    # validate BEFORE writing, and only for OUR named placeholders (candidate text may contain "{{")
    leftover = [ph for ph in ("{{REVIEW_NAME}}","{{GENERATED}}","{{SEARCH_LOG}}","{{CREDIT_SPEND}}",
                              "{{ROWS_NEW}}","{{ROWS_UNCERTAIN}}","{{ROWS_KNOWN}}") if ph in out]
    if leftover: sys.exit(f"unfilled placeholders: {leftover}")
    outp = Path(a.out); outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(out)
    print(f"wrote {outp} · new={len(b.get('new',[]))} uncertain={len(b.get('uncertain',[]))} "
          f"known={len(b.get('known',[]))} credits≈{credits}")

if __name__ == "__main__":
    main()
