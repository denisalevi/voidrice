#!/usr/bin/env python3
"""notes_todo.py — emit the candidates that still need a relevance note (P5d note-cache diff).

"Reuse existing notes" is only cheap if we never re-send already-noted papers to a subagent.
This helper takes classified.json + one-or-more existing {id: note} maps and writes a compact
JSON array of the candidates (WITH abstracts) that are NOT yet noted, so a fan-out only processes
the missing ones. Optionally splits the todo list into batch files.

Usage:
  notes_todo.py --run <run> [--notes notes1.json,notes2.json] [--abstract-chars 900]
                [--top N] [--out todo.json] [--batch-dir DIR --batch-size 40]

- --top N: only consider the top-N ranked 'new' candidates (relevance cutoff), + always include
  curated ones regardless of rank. Mirrors the "note only top-K + curated" option.
- --abstract-chars: truncate the abstract per paper in the payload (cost lever P5c).
Prints how many still need notes.
"""
import argparse, json, re, sys
from pathlib import Path

def norm_doi(doi):
    if not doi: return None
    d = str(doi).strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d); d = re.sub(r"^doi:\s*", "", d)
    return d or None

def cand_id(c):
    doi = (c.get("doi") or "").strip().lower()
    if doi: return doi
    t = re.sub(r"[^a-z0-9]+", "", (c.get("title") or "").lower())[:60]
    au = (c.get("authors") or ["?"])[0]
    su = re.sub(r"[^a-z]", "", (au.split(",")[0] if "," in au else au.split(" ")[-1]).lower())
    return f"t:{t}|{su}|{c.get('year') or '?'}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--notes", default="", help="comma-separated existing {id:note} json files")
    ap.add_argument("--abstract-chars", type=int, default=900)
    ap.add_argument("--top", type=int, default=0, help="only top-N ranked new (0 = all); curated always kept")
    ap.add_argument("--out", default=None)
    ap.add_argument("--batch-dir", default=None)
    ap.add_argument("--batch-size", type=int, default=40)
    a = ap.parse_args()
    run = Path(a.run)
    cl = json.loads((run / "classified.json").read_text())

    have = set()
    for f in [x for x in a.notes.split(",") if x.strip()]:
        m = json.loads(Path(f).read_text())
        for k in m:
            have.add(norm_doi(k) if not str(k).startswith("t:") else k)

    new = cl.get("new", [])
    pool = new if a.top <= 0 else (new[:a.top] + [c for c in new[a.top:] if c.get("curated")])
    # only abstracted candidates can be noted
    todo = []
    for c in pool:
        if not (c.get("abstract") or "").strip():
            continue
        cid = norm_doi(c.get("doi")) or cand_id(c)
        if cid in have or c.get("relevance"):
            continue
        todo.append({"id": cid, "title": c.get("title") or "", "year": c.get("year"),
                     "abstract": (c.get("abstract") or "")[:a.abstract_chars]})

    if a.out:
        Path(a.out).write_text(json.dumps(todo, ensure_ascii=False))
    if a.batch_dir:
        bd = Path(a.batch_dir); bd.mkdir(parents=True, exist_ok=True)
        for f in bd.glob("todo_*.json"): f.unlink()
        n = 0
        for i in range(0, len(todo), a.batch_size):
            (bd / f"todo_{n:03d}.json").write_text(json.dumps(todo[i:i+a.batch_size], ensure_ascii=False)); n += 1
        print(f"notes_todo: {len(todo)} papers still need notes → {n} batch files in {bd}")
    else:
        print(f"notes_todo: {len(todo)} papers still need notes"
              + (f" (written to {a.out})" if a.out else ""))

if __name__ == "__main__":
    main()
