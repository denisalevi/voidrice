#!/usr/bin/env python3
"""zotero_add.py — programmatic, keyless, batched Zotero add for the chosen "add" decisions (A1).

Replaces the ~2×N sequential MCP hops (zotero_add_by_doi + zotero_create_note) at the END of the
lit-review pipeline with a handful of HTTP calls to the RUNNING Zotero desktop's LOCAL connector
API (http://localhost:23119) — no API key, no LLM. It is metadata-only (NO PDF attachment), so the
Zotmoov flow is untouched, same intent as the old attach_mode="none".

What it does (mechanics only — the human approval gate upstream is unchanged):
  1. Read <review-folder>/decisions.json; take decision=="add" entries (always DOI-bearing).
  2. D1 dedup: exact-DOI check against the WHOLE library via the local READ API (with casing
     variants), so items living anywhere in Zotero aren't re-added as duplicates. Split into
     already_owned (skip add, report for MCP collection-membership) vs to_add.
  3. For each to_add DOI: fetch CSL-JSON via Crossref content negotiation (doi.org). 404 → dead DOI,
     skipped and reported (never add a dead DOI). Map CSL → a Zotero item template.
  4. Attach tags ["added-by-claude", "lit-review/<name>"] + a child "LLM lit-review notes" note
     (dated block, incl. Denis's decisions.json note + the why/about text if provided).
  5. Batch-save via POST /connector/saveItems (chunked), targeting the review subcollection.
  6. Write <review-folder>/zotero_add_report.json and print a summary.

WHAT IT DOES NOT DO (left to the orchestrator/MCP — cheap, not the bottleneck):
  - Creating the review subcollection (do that first via MCP zotero_create_collection).
  - Adding ALREADY-OWNED items (chosen "collection"/dedup-owned) to the subcollection — the connector
    has no add-existing-to-collection endpoint; use MCP zotero_manage_collections. This script REPORTS
    which keys need it (report["owned_needs_collection"]).
  - Prepend-merging into a pre-existing note (idempotent multi-review case) — this script creates a
    fresh child note. Re-adds of the SAME paper are prevented by D1 dedup, so that's fine for adds;
    if a paper is somehow already present with a note, prefer the MCP prepend path.

Usage:
  zotero_add.py --review-dir <folder> --name <review-name> --collection <subcollection-key>
                [--host http://localhost:23119] [--dry-run] [--chunk 20]

Requires: Zotero desktop RUNNING (connector on :23119). Verify with /connector/ping first.
"""
import argparse, json, sys, time, re, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import lrlib as L

HOST_DEFAULT = "http://localhost:23119"
# connector needs a browser-ish UA + the connector API version header, else it rejects the write.
CONN_HEADERS = {"Content-Type": "application/json", "X-Zotero-Connector-API-Version": "3",
                "User-Agent": "Mozilla/5.0 (lit-review zotero_add.py)"}

# ---------- local read API: exact-DOI dedup against the whole library (D1) ----------
def _doi_variants(doi):
    """Zotero stores DOIs with mixed casing. Yield the forms worth checking (deduped, order-preserved)."""
    d = (doi or "").strip()
    out = []
    for v in (d, d.lower(), d.upper(),
              re.sub(r"(?i)^10\.7554/elife\.", "10.7554/eLife.", d)):  # common eLife casing
        if v and v not in out:
            out.append(v)
    return out

def library_doi_index(http, host, uid, log):
    """One pass over the whole library's top-level items → {normalized_doi: zotero_key}. Cheaper and
    more reliable than N per-DOI searches, and immune to the search endpoint's casing quirks."""
    idx = {}
    start, page = 0, 100
    while True:
        r = http.get(f"{host}/api/users/{uid}/items/top?limit={page}&start={start}&format=json")
        if r is None or r.status_code != 200:
            log.warn(f"library dump stopped at start={start} (HTTP {r.status_code if r else 'none'})")
            break
        items = r.json()
        if not items:
            break
        for it in items:
            d = L.norm_doi((it.get("data") or {}).get("DOI"))
            if d and d not in idx:
                idx[d] = it["key"]
        total = int(r.headers.get("Total-Results", "0") or 0)
        start += page
        if start >= total:
            break
    log.ok(f"library DOI index built: {len(idx)} DOIs across {total} top-level items")
    return idx

def resolve_uid(http, host, log):
    """The local API self-alias users/0 works for reads, but writes/report want the real numeric uid."""
    r = http.get(f"{host}/api/users/0/items?limit=1&format=json")
    if r is not None and r.status_code == 200:
        try:
            lib = r.json()[0].get("library", {})
            if lib.get("type") == "user" and lib.get("id"):
                return int(lib["id"])
        except Exception:
            pass
    return 0  # fall back to the self-alias

# ---------- CSL-JSON (Crossref content negotiation) → Zotero item ----------
CSL2ZOT_TYPE = {
    "journal-article": "journalArticle", "proceedings-article": "conferencePaper",
    "posted-content": "preprint", "book": "book", "book-chapter": "bookSection",
    "monograph": "book", "report": "report", "dataset": "dataset", "thesis": "thesis",
    "reference-entry": "encyclopediaArticle", "review": "journalArticle",
}
def _csl_date(csl):
    for k in ("issued", "published", "published-online", "published-print", "created"):
        dp = ((csl.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            # zero-pad month/day so it reads YYYY-MM-DD (year alone stays "YYYY")
            return "-".join(f"{int(x):02d}" if i else str(x) for i, x in enumerate(dp[0]))
    return ""

def _strip_jats(abstract):
    """Crossref abstracts arrive as JATS XML; drop tags for a plain-text Zotero abstract."""
    if not abstract:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", abstract)).strip()

def csl_to_zotero(csl, tags, note_html):
    """Map a CSL-JSON record to a Zotero item template understood by /connector/saveItems.
    Conservative: fills the fields Zotero's journalArticle/preprint/etc. actually use; unknown CSL
    types fall back to journalArticle (safe, editable). Notes go as child items via `notes`."""
    zt = CSL2ZOT_TYPE.get(csl.get("type", ""), "journalArticle")
    creators = []
    for role, ct in (("author", "author"), ("editor", "editor")):
        for a in csl.get(role, []) or []:
            if a.get("family") or a.get("given"):
                creators.append({"creatorType": ct, "firstName": a.get("given", ""),
                                 "lastName": a.get("family", "")})
            elif a.get("literal"):
                creators.append({"creatorType": ct, "name": a["literal"]})
    container = (csl.get("container-title") or "")
    if isinstance(container, list):
        container = container[0] if container else ""
    title = csl.get("title") or ""
    if isinstance(title, list):
        title = title[0] if title else ""
    item = {
        "itemType": zt,
        "title": title,
        "creators": creators,
        "date": _csl_date(csl),
        "DOI": csl.get("DOI", ""),
        "url": csl.get("URL", ""),
        "abstractNote": _strip_jats(csl.get("abstract", "")),
        "tags": [{"tag": t} for t in tags],
        "collections": [],  # target is set via the saveItems envelope, not per-item
    }
    # container field name differs by item type
    if zt in ("journalArticle", "review"):
        item["publicationTitle"] = container
        item["volume"] = csl.get("volume", ""); item["issue"] = csl.get("issue", "")
        item["pages"] = csl.get("page", "")
        item["ISSN"] = (csl.get("ISSN") or [""])[0] if isinstance(csl.get("ISSN"), list) else csl.get("ISSN", "")
    elif zt == "conferencePaper":
        item["proceedingsTitle"] = container
    elif zt == "bookSection":
        item["bookTitle"] = container
    elif zt == "preprint":
        item["repository"] = container or (csl.get("institution", [{}])[0].get("name", "") if csl.get("institution") else "")
    if csl.get("publisher"):
        item["publisher"] = csl["publisher"]
    if note_html:
        item["notes"] = [{"itemType": "note", "note": note_html}]
    return item

# ---------- note block (mirrors SKILL "Per-paper notes" format) ----------
def note_block(review_name, why, about, user_note):
    today = L.now()[:10]
    parts = [f'<div data-review="{html.escape(review_name)}">',
             f'<h1>LLM lit-review notes</h1>',
             f'<p><strong>[{today} · {html.escape(review_name)}]</strong></p>']
    if why:   parts.append(f'<p><em>Why added:</em> {html.escape(why)}</p>')
    if about: parts.append(f'<p><em>About:</em> {html.escape(about)}</p>')
    if user_note: parts.append(f'<p><em>Denis&#39;s note:</em> {html.escape(user_note)}</p>')
    parts.append('</div>')
    return "".join(parts)

# ---------- connector save ----------
def save_batch(http, host, collection_key, items, log, dry_run):
    """POST one chunk of items to /connector/saveItems, into `collection_key`. Returns HTTP status."""
    sid = f"litrev-{int(time.time()*1000)}-{len(items)}"
    body = {"sessionID": sid, "target": None, "items": items}
    # target must be the connector collection id form "C<key>"; the connector maps it to the collection.
    if collection_key:
        body["target"] = collection_key if collection_key.startswith("C") else f"C{collection_key}"
    if dry_run:
        log.info(f"[dry-run] would POST {len(items)} items to {body['target']}")
        return 0
    r = http.post(f"{host}/connector/saveItems", headers=CONN_HEADERS, json_body=body)
    return r.status_code if r is not None else -1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-dir", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--collection", default="", help="review subcollection key (e.g. 2S432WWF child); items land here")
    ap.add_argument("--host", default=HOST_DEFAULT)
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rd = Path(a.review_dir); log = L.Log(rd)
    dec = json.loads((rd/"decisions.json").read_text())
    decisions = dec.get("decisions", dec if isinstance(dec, list) else [])

    # connector alive?
    http = L.Http(log, min_interval=0.0, source="zotero-add")
    ping = http.get(f"{a.host}/connector/ping")
    if ping is None or ping.status_code != 200:
        sys.exit(f"Zotero connector not reachable at {a.host} (is Zotero desktop running?)")
    uid = resolve_uid(http, a.host, log)
    log.info(f"connector OK · uid={uid} · review='{a.name}' · collection='{a.collection}'")

    adds = [d for d in decisions if d.get("decision") == "add" and d.get("doi")]
    owned_coll = [d for d in decisions if d.get("owned") and d.get("decision") == "collection"]
    log.ok(f"decisions: {len(adds)} to-add · {len(owned_coll)} owned→collection (MCP handles those)")

    # D1 dedup against the whole library
    doi_idx = library_doi_index(http, a.host, uid, log)
    to_add, already_owned = [], []
    for d in adds:
        hit = None
        for v in _doi_variants(d["doi"]):
            k = doi_idx.get(L.norm_doi(v))
            if k: hit = k; break
        (already_owned if hit else to_add).append({**d, "zkey": hit} if hit else d)
    if already_owned:
        log.warn(f"D1: {len(already_owned)} chosen-adds ALREADY in library (skip add; add to collection via MCP): "
                 + ", ".join(f"{d['doi']}→{d['zkey']}" for d in already_owned))

    # Fetch CSL + build items
    cross = L.Http(log, min_interval=0.05, source="crossref-csl")
    built, dead = [], []
    for d in to_add:
        doi = d["doi"]
        r = cross.get(f"https://doi.org/{doi}", headers={"Accept": "application/vnd.citationstyles.csl+json"})
        if r is None or r.status_code == 404:
            dead.append(doi); log.warn(f"dead/unresolvable DOI, skipped: {doi}"); continue
        if r.status_code != 200:
            dead.append(doi); log.warn(f"DOI fetch {r.status_code}, skipped: {doi}"); continue
        try:
            csl = r.json()
        except Exception:
            dead.append(doi); log.warn(f"non-JSON CSL, skipped: {doi}"); continue
        note = note_block(a.name, d.get("why", ""), d.get("about", ""), d.get("note", ""))
        tags = ["added-by-claude", f"lit-review/{a.name}"]
        built.append((doi, csl_to_zotero(csl, tags, note)))
    log.ok(f"built {len(built)} Zotero items · dead DOIs {len(dead)}")

    # Batch save
    saved, save_errors = 0, []
    for i in range(0, len(built), a.chunk):
        chunk = [it for (_doi, it) in built[i:i+a.chunk]]
        code = save_batch(http, a.host, a.collection, chunk, log, a.dry_run)
        if code in (200, 201) or (a.dry_run and code == 0):
            saved += len(chunk); log.ok(f"saved chunk {i//a.chunk+1}: {len(chunk)} items (HTTP {code})")
        else:
            save_errors.append({"chunk": i//a.chunk+1, "http": code, "dois": [d for (d,_it) in built[i:i+a.chunk]]})
            log.error(f"save chunk {i//a.chunk+1} FAILED (HTTP {code})")

    report = {
        "finished": L.now(), "review": a.name, "collection": a.collection, "dry_run": a.dry_run,
        "requested_adds": len(adds), "saved": saved if not a.dry_run else 0,
        "would_save": len(built) if a.dry_run else None,
        "already_owned": [{"doi": d["doi"], "zkey": d["zkey"]} for d in already_owned],
        "owned_needs_collection": [d.get("zkey") or d.get("doi") for d in owned_coll],
        "dead_dois": dead, "save_errors": save_errors,
    }
    L.write_json(rd/"zotero_add_report.json", report)
    log.ok(f"DONE · saved={report['saved']} dead={len(dead)} already_owned={len(already_owned)} "
           f"owned→collection(MCP)={len(owned_coll)} errors={len(save_errors)}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
