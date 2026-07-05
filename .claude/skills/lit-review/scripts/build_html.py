#!/usr/bin/env python3
"""build_html.py — render <run>/classified.json into the interactive review page.

Usage:
  build_html.py --run <run> --name <review-name> --out <path.html> [--search-log "OpenAlex, S2, Crossref"]

Reads the template at ../templates/review.html, fills placeholders, writes the page.
Pulls credit total from search_summary.json + snowball_summary.json if present.
"""
import argparse, json, html, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

TPL = Path(__file__).parent.parent / "templates" / "review.html"

def esc(s): return html.escape(str(s or ""))

AUDIT_CHIP = {
    "core":        ('ok',   '★ core-novelty'),
    "duplicate":   ('warn', '⧉ duplicate'),
    "off-topic":   ('warn', '~ off-topic'),
    "over-claimed":('warn', '~ over-claimed'),
    "notice":      ('warn', '⚠ editorial notice — verify'),
}

def is_owned(c, bucket):
    """Owned = already in Denis's Zotero. Keyed off the record's own flag (set when merged into the
    unified list) OR the legacy bucket=='known'. Owned items render EXACTLY like new candidates
    (same chips/notes/sort) except for the action control (collection/skip vs add/discuss/reject)."""
    return bool(c.get("owned")) or bucket == "known"

def chips(c, bucket):
    out = []
    owned = is_owned(c, bucket)
    if bucket == "uncertain":
        out.append('<span class="chip warn">⚠ possible duplicate</span>')
    if (c.get("discovery") or c.get("origin") == "cross-domain"):
        fld = (c.get("discovery") or {}).get("field") if isinstance(c.get("discovery"), dict) else None
        out.append(f'<span class="chip" style="border-color:#8250df;color:#8250df">🌐 cross-domain{(": "+esc(fld)) if fld else ""}</span>')
    if owned:
        out.append('<span class="chip" style="border-color:#0969da;color:#0969da">📁 in Zotero</span>')
    if c.get("curated"):
        out.append('<span class="chip ok" style="font-weight:600">⭐ curated</span>')
    mv = c.get("merged_versions")
    if mv:  # D3: preprint/version twins collapsed into this row
        vt = "; ".join(esc((m.get("doi") or m.get("title") or "?")) for m in mv)
        out.append(f'<span class="chip" title="{vt}">🔗 {len(mv)} version{"s" if len(mv)!=1 else ""} merged</span>')
    for flag in c.get("audit", []) or []:
        cls, lbl = AUDIT_CHIP.get(flag, ('', esc(flag)))
        out.append(f'<span class="chip {cls}">{lbl}</span>')
    for s in c.get("sources", []):
        out.append(f'<span class="chip">{esc(s)}</span>')
    v = c.get("verification")
    if not owned:  # owned items are real by construction (they're in Zotero) — no verification chip
        if v is None: out.append('<span class="chip">? not checked</span>')
        elif v.get("no_doi"): out.append('<span class="chip warn">✓ real · no DOI (manual add)</span>')
        elif v.get("verified"): out.append('<span class="chip ok">✓ verified</span>')
        else: out.append('<span class="chip warn">⚠ unverified</span>')
    _relscore = c.get("sim")
    if _relscore is None and c.get("rank_score") is not None: _relscore = c.get("rank_score")
    if _relscore is not None: out.insert(0, f'<span class="chip ok">relevance {_relscore:.2f}</span>')
    via = c.get("abstract_via")
    if via == "s2-tldr": out.append('<span class="chip warn">abstract = AI TLDR only</span>')
    elif via in ("europepmc", "s2"): out.append(f'<span class="chip">abstract via {via}</span>')
    if c.get("cited_by") is not None: out.append(f'<span class="chip">cited {c["cited_by"]}×</span>')
    ret = c.get("retraction")
    if ret: out.append('<span class="chip warn">⚠ RETRACTED</span>')
    cl = c.get("classification", {})
    if cl.get("match"): out.append(f'<span class="chip">{esc(cl["match"])}</span>')
    return "".join(out)

def cand_id(c):
    """Stable per-candidate id: normalized DOI if present, else norm(title)|surname|year.
    Used for resume-by-cid so no-DOI decisions survive a reload (P4d)."""
    doi = (c.get("doi") or "").strip().lower()
    if doi: return doi
    t = re.sub(r"[^a-z0-9]+", "", (c.get("title") or "").lower())[:60]
    au = (c.get("authors") or ["?"])[0]
    su = re.sub(r"[^a-z]", "", (au.split(",")[0] if "," in au else au.split(" ")[-1]).lower())
    return f"t:{t}|{su}|{c.get('year') or '?'}"

def provenance_fold(c):
    """Small foldout of which query/seed/direction surfaced this paper (P4c reproducibility)."""
    prov = c.get("provenance") or []
    if not prov and c.get("extra"):
        e = c["extra"]
        one = e.get("query") or e.get("seed") or e.get("direction")
        if one: prov = [str(one)]
    if not prov: return ""
    items = "".join(f"<li>{esc(p)}</li>" for p in prov[:12])
    return (f'<details class="prov"><summary>Provenance ({len(prov)})</summary>'
            f'<ul>{items}</ul></details>')

def row(c, bucket):
    doi = c.get("doi") or ""
    # only allow http(s) links in href; anything else (javascript:, data:, …) → "#"
    raw_link = ("https://doi.org/" + doi) if doi else (c.get("url") or "")
    link = raw_link if raw_link.startswith(("https://", "http://")) else "#"
    authors = ", ".join(esc(a) for a in c.get("authors", []) if a) or "—"  # ESCAPE each author
    meta = f'{authors} · {esc(c.get("year") or "?")}' + (f' · {esc(c.get("venue"))}' if c.get("venue") else "")
    abs = esc(c.get("abstract")) or "(no abstract)"
    rel = c.get("relevance")  # self-generated "why relevant to this review" (Sonnet/Haiku)
    # Addable only if: bucket==new AND has a DOI. Uncertain/possible-dup rows get Discuss/Reject
    # ONLY even when they have a DOI (safety boundary P1b) — same treatment as no-DOI rows.
    owned = is_owned(c, bucket)
    addable = (bucket == "new") and not owned and bool(doi)
    if owned:
        # Already in Denis's Zotero. NOT re-added as a new item — the only action is whether this
        # existing item should be a MEMBER of the review collection. 'collection' vs 'skip'.
        choice = ('<div class="choice">'
                  '<button data-c="collection" onclick="choose(this,\'collection\')">➕ Add to collection</button>'
                  '<button data-c="skip" onclick="choose(this,\'skip\')">Skip</button></div>'
                  '<textarea class="note" placeholder="Note…"></textarea>')
    elif addable:
        choice = ('<div class="choice">'
                  '<button data-c="add" onclick="choose(this,\'add\')">Add</button>'
                  '<button data-c="discuss" onclick="choose(this,\'discuss\')">Discuss</button>'
                  '<button data-c="reject" onclick="choose(this,\'reject\')">Reject</button></div>'
                  '<textarea class="note" placeholder="Note (why / for Zotero / to discuss)…"></textarea>')
    else:
        why = ('possible duplicate — discuss before adding' if bucket == "uncertain"
               else 'no DOI — add manually in Zotero')
        choice = (f'<div class="choice"><span class="chip warn">{why}</span>'
                  '<button data-c="discuss" onclick="choose(this,\'discuss\')">Discuss</button>'
                  '<button data-c="reject" onclick="choose(this,\'reject\')">Reject</button></div>'
                  '<textarea class="note" placeholder="Note…"></textarea>')
    sim = c.get("sim"); cb = c.get("cited_by"); rs = c.get("rank_score")
    cur = "1" if c.get("curated") else "0"
    disc = "1" if (c.get("discovery") or c.get("origin") == "cross-domain") else "0"
    dattrs = (f' data-sim="{sim if sim is not None else -1}"'
              f' data-rank-score="{rs if rs is not None else (sim if sim is not None else -1)}"'
              f' data-cited="{cb if cb is not None else -1}" data-curated="{cur}"'
              f' data-discovery="{disc}" data-cid="{esc(cand_id(c))}"'
              f' data-owned="{"1" if owned else "0"}"'
              f' data-zkey="{esc(c.get("zkey") or "")}"')
    return (f'<article class="paper" data-doi="{esc(doi)}" data-decision="none" data-note=""{dattrs}>'
            f'<div class="ptitle"><a href="{esc(link)}" target="_blank" rel="noopener">{esc(c.get("title"))}</a></div>'
            f'<div class="authors">{meta}</div>'
            f'<div class="chips">{chips(c, bucket)}</div>'
            + (f'<details class="rel" open><summary>Why relevant to this review</summary>'
               f'<p>{esc(rel)}</p></details>' if rel else '')
            + f'<details class="abs"><summary>Abstract</summary><p>{abs}</p></details>'
            + provenance_fold(c)
            + f'{choice}</article>')

def rows(cs, bucket):
    return "\n".join(row(c, bucket) for c in cs) if cs else '<p class="meta">none</p>'

def elapsed_str(run):
    """kickoff→now, from the earliest 'started' across summaries."""
    import datetime as dt
    starts = []
    for f in ("search_summary.json", "snowball_summary.json"):
        p = run/f
        if p.exists():
            s = json.loads(p.read_text()).get("started")
            if s:
                try: starts.append(dt.datetime.fromisoformat(s))
                except Exception: pass
    if not starts: return "n/a"
    delta = dt.datetime.now() - min(starts)
    secs = int(delta.total_seconds())
    return f"{secs//60}m {secs%60}s" if secs >= 60 else f"{secs}s"

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
    # Unify owned (in-Zotero) items INTO the main ranked list. Owned papers flow through the SAME
    # ranking/notes/chips/sort/filter/row rendering as new candidates; the ONLY difference is the
    # action control (collection/skip vs add/discuss/reject), keyed off the `owned` flag on the
    # record. We tag each owned item owned=True and merge by rank_score so the one #new list is
    # globally relevance-ordered. (build_html only READS classified.json here; nothing is written
    # back, so this merge is display-only.)
    new_ranked = list(b.get("new", []))
    owned = list(b.get("known", []))
    for c in owned:
        c["owned"] = True
    merged = new_ranked + owned
    def _score(c):
        s = c.get("rank_score")
        if s is None: s = c.get("sim")
        return s if s is not None else -1
    merged.sort(key=_score, reverse=True)
    new_ranked = merged
    noabs = b.get("new_no_abstract", [])
    tpl = TPL.read_text()
    out = (tpl.replace("{{REVIEW_NAME}}", esc(a.name))
              .replace("{{GENERATED}}", L.now())
              .replace("{{ELAPSED}}", elapsed_str(run))
              .replace("{{SEARCH_LOG}}", esc(a.search_log))
              .replace("{{CREDIT_SPEND}}", str(credits))
              .replace("{{COUNT_NEW}}", str(len(new_ranked)))
              .replace("{{COUNT_OWNED}}", str(len(owned)))
              .replace("{{COUNT_NOABS}}", str(len(noabs)))
              .replace("{{COUNT_UNCERTAIN}}", str(len(b.get("uncertain", []))))
              .replace("{{ROWS_NEW}}", rows(new_ranked, "new"))
              .replace("{{ROWS_NOABS}}", rows(noabs, "noabs"))
              .replace("{{ROWS_UNCERTAIN}}", rows(b.get("uncertain", []), "uncertain")))
    leftover = [ph for ph in ("{{REVIEW_NAME}}","{{GENERATED}}","{{ELAPSED}}","{{SEARCH_LOG}}","{{CREDIT_SPEND}}",
                              "{{COUNT_NEW}}","{{COUNT_OWNED}}","{{COUNT_NOABS}}","{{COUNT_UNCERTAIN}}",
                              "{{ROWS_NEW}}","{{ROWS_NOABS}}",
                              "{{ROWS_UNCERTAIN}}") if ph in out]
    if leftover: sys.exit(f"unfilled placeholders: {leftover}")
    outp = Path(a.out); outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(out)
    print(f"wrote {outp} · ranked(incl. owned)={len(new_ranked)} owned={len(owned)} "
          f"no_abstract={len(noabs)} uncertain={len(b.get('uncertain',[]))} credits≈{credits}")

if __name__ == "__main__":
    main()
