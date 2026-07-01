---
name: lit-review
description: >-
  Literature review that finds papers MISSING from Denis's Zotero on a topic (or
  citing/related to a seed paper), verifies they are real, and presents them in an
  interactive HTML page for per-paper approval before adding the chosen ones to Zotero.
  Use when Denis wants to discover new literature, find derivative/citing work for a
  seed paper, or fill gaps in his library. Invoke on /lit-review or requests like
  "find papers I'm missing on X", "what cites paper Y", "literature review on Z".
---

# lit-review

Find literature **missing from Denis's Zotero** for a topic or seed paper, verify it is
real, and hand Denis an interactive HTML page to approve papers one by one. Only approved
papers are added to Zotero. This skill is **add-only** — it never deletes anything and never
edits `references.bib`.

## Non-negotiable rules

1. **NEVER write `9_backmatter/references.bib`** (or any `.bib`). It is auto-generated from
   Zotero via Better BibTeX. The only write target is Zotero itself; the bib regenerates from there.
2. **Nothing is added to Zotero without explicit per-paper approval** from the HTML review page.
   When in doubt about a paper, put it in "needs discussion" — do NOT add it. The MCP has **no
   delete tool**, so a wrong add costs Denis a manual desktop cleanup. Be conservative.
3. **Every candidate presented as NEW must be verified real** (DOI/ID resolves) before it reaches
   the HTML page. Never present a paper you have not confirmed exists via an API.
4. **API keys are read at call time, never into context.** OpenAlex key:
   `$(tr -d '\n' < ~/.config/openalex.key)`. Semantic Scholar key (if present):
   `$(tr -d '\n' < ~/.config/semanticscholar.key)` → `x-api-key` header. Do NOT cat/print keys.

## Architecture: scripts do the work, you orchestrate

The mechanical, high-iteration work (paginated queries, 429 backoff, dedup, verification, HTML
assembly) lives in **deterministic scripts under `scripts/`** so you don't burn context/tokens on
tool-pingpong. You (the LLM) decide *what* to run and adjudicate results; the scripts run to
completion and write introspectable files to a **run directory**.

- **Run dir:** `literature-reviews/<review-name>/run/` in the repo (create it).
- **Run long stages (search, snowball) in the BACKGROUND**, then POLL their files:
  `run/run.log` (timestamped, grep-able) and `run/*_summary.json` (machine-readable, updated live).
  Only intervene if the log shows repeated failures. Verification (dedup_verify) is fast (source-trust
  fast path) and can run foreground.
- Scripts read API keys at call time from files — never pass keys as args.
- **Refine the scripts as you use them.** If a query pattern, backoff, or dedup threshold misbehaves
  in a real review, edit the script — that's the point of having them.

Scripts (all take `--run <dir>`; see `reference/apis.md` and each script's docstring):
- `scripts/search.py --queries <q.json>` → OpenAlex + S2 search → `raw_candidates.jsonl` + `search_summary.json`
- `scripts/snowball.py --seeds <s.json> --directions forward,backward,sideways` → appends candidates
- `scripts/dedup_verify.py` → reads `raw_candidates.jsonl` + `known_set.json` → `classified.json` (new/uncertain/known)
- `scripts/build_html.py --name <n> --out <path>` → renders the review page from `classified.json`

The **Zotero known-set dump** (`run/known_set.json`) is written by YOU via MCP (scripts can't call MCP):
after Zotero-first search, emit a JSON list of `{doi,title,authors,year,key}` for the relevant items.
The **Zotero adds** at the end are also YOU via MCP (the irreversible step stays under your eye).

## Pipeline

Keep a running **search log** (queries, source, date, result counts, credit spend) — scripts capture
most of it in the summary JSONs; it flows into the HTML page for reproducibility.

### 0. Scope
If the request is vague, ask 1–3 questions: topic vs seed-paper mode, timeframe, depth, subfield.
Name the review (kebab-case, e.g. `engram-drift-mechanisms`) — used for the tag, subcollection,
and HTML filename. Convert relative dates to absolute.

### 1. Zotero-first — build the KNOWN SET
Before any web search, find what Denis already has so it can be excluded from the NEW list.
- `zotero_semantic_search` on the topic (semantic recall over his library).
- `zotero_search_items` with short `Author Year` / keyword queries (substring match — keep queries
  SHORT; more words = stricter, not broader).
- For seed-paper mode, resolve the seed in Zotero if present.
Record each hit's DOI + normalized title+first-author+year → the KNOWN SET. These become the
"Already in your Zotero" section (context only, no action).

### 2. Discover — web candidates
Use **all available sources** and log which surfaced each paper (provenance). See
`reference/apis.md` for exact call patterns, cost model, and 429 handling.
- **OpenAlex** (keyed, reliable, cheap filters) — broad recall + structured filters
  (year/venue/OA/concept). Denis runs ≤1 review/day and is fine spending the whole daily
  budget on it → use it GENEROUSLY (many filter variants, deep snowballing). Prefer
  `filter=title.search:`/`abstract.search:` (1 credit) over `search=` (10 credits); hydrate
  by ID for free. Track and report credit spend.
- **Semantic Scholar** — semantic relevance (SPECTER2), Recommendations ("papers like these
  seeds"), and citation-graph. Its unique strength. Handle 429s (keyless is 429-prone until the
  key is approved): honor Retry-After, else exp-backoff + jitter, self-throttle ~1 req/s,
  prefer bulk/batch, minimal fields. On exhaustion, fall back to OpenAlex/Crossref rather than failing.
- **Crossref** — keyless, for verification and metadata-of-record.

### 3. Snowball — first-class (this is often where the value is)
From the strongest seeds (Denis's seed paper, and/or the top candidates):
- **Forward (derivative/citing work):** OpenAlex `filter=cites:<id>` (1 credit, sortable by
  date/citations) and/or S2 `/paper/{id}/citations`. This is the "what cites paper X" use case.
- **Backward (foundations):** `referenced_works` / S2 `/paper/{id}/references`.
- **Sideways (thematic siblings):** S2 Recommendations API; optionally OpenAlex
  bibliographic-coupling (papers sharing the seed's references).
Loop until a round yields nothing new (loop-until-dry), within reason.

### 4. Dedup against the KNOWN SET — the core step
Compute `{candidates} − {Zotero}`:
- **DOI exact match** (normalized, lowercase) = authoritative → already-owned, exclude from NEW.
- No DOI or DOI mismatch → fuzzy match on normalized-title + first-author + year.
- **Uncertain matches → "possible duplicate / needs discussion", never silently dropped.**
Result: three buckets — Already-in-Zotero, NEW candidates, Uncertain.

### 5. Verify — every NEW + Uncertain candidate
- Resolve identifier: DOI via Crossref (`https://api.crossref.org/works/<doi>`) or `doi.org`;
  else arXiv/PMID; else fuzzy-match title across Crossref + OpenAlex. Zero hits anywhere → drop
  as likely fabricated (do not present it).
- **Retraction/quality check:** `scite_enrich_item(doi=…)` → surface retraction alerts +
  support/contrast counts on the HTML page. A retracted paper must be flagged prominently.

### 6. Present — interactive HTML review page
Render `templates/review.html` filled with the three buckets. Write to
**`literature-reviews/<review-name>/<review-name>.html`** in the current repo (create the folder).
Each NEW/Uncertain paper row must have: full author list, foldable abstract, `doi.org/<doi>`
hyperlink (fallback to best available URL if no DOI), source-provenance chip(s), verification +
retraction status, a free-text note field, and a per-paper choice (add / discuss / reject).
Include top-level "select all add / none" buttons and a header with the search log + credit spend.
Tell Denis to open it in his browser, make choices, write notes, and click **Save decisions** —
which DOWNLOADS a `decisions.json` (browsers can't persist DOM edits back to the .html on Ctrl+S).
Ask him to move `decisions.json` into the review folder next to the .html and tell you it's ready.

Then STOP and hand off to Denis. Do not add anything yet.

### 6b. Retraction enrichment (before or after HTML)
Before adds (and ideally reflected in the HTML), run `scite_enrich_item(doi=…)` on the NEW
candidates and write a `retraction` field into `classified.json` for any flagged item, then
re-run `build_html.py` so retraction warnings show. At minimum, retraction-check the papers Denis
chose to add, and refuse/flag any that are retracted.

### 7. Add — only after Denis returns his choices
Read `decisions.json` from the review folder. For every entry with `decision=="add"` (these always
have a DOI — the UI only offers Add to DOI-bearing papers; no-DOI papers are Discuss/Reject only):
- Ensure the review subcollection exists: `zotero_create_collection("<review-name>",
  parent_collection="2S432WWF")` (parent `LLM-literature-reviews` = key `2S432WWF`).
- `zotero_add_by_doi(doi, collections=<subcollection key>,
  tags=["added-by-claude", "lit-review/<review-name>"], attach_mode="none")`.
  `attach_mode="none"` = metadata only, NO cloud PDF (protects the Zotmoov flow).
- Add the per-paper note (see below).
- Also add the **already-owned** papers for this review to the subcollection (so it is the
  complete picture of the review) via `zotero_manage_collections`.
After the batch, print: (a) a summary of what was added, (b) the explicit **desktop PDF step**:
"In Zotero, select the newly added items (tag `added-by-claude`) → right-click → *Zotmoov:
Move selected to Directory* to fetch/relocate PDFs locally." (No API hook exists for this.)

## Per-paper notes (prepend pattern)
One note per paper, titled **"LLM lit-review notes"**, each review prepends a dated block.
- Check for an existing note: `zotero_get_notes(item_key, raw_html=True)`.
- If none: `zotero_create_note(item_key, "LLM lit-review notes", <block>, tags=["added-by-claude"])`.
- If one exists: build `<h1>LLM lit-review notes</h1>` + NEW block + existing blocks (minus the
  `<h1>`), then `zotero_update_note(note_key, new_html, append=False)` (replace — append puts
  content at the END; we want newest on TOP). Skip if a `data-review="<review-name>"` block
  already exists (idempotent re-runs).
- Block format:
  `<div data-review="<review-name>"><p><strong>[<YYYY-MM-DD> · <review-name>]</strong></p>`
  `<p><em>Why added:</em> …</p><p><em>About:</em> …</p></div>`
  Include Denis's note from the HTML if he wrote one.

## Refine as we go
Source roles are provisional. The HTML page logs which source surfaced each KEPT paper and the
credit spend. After reviews, note which source is pulling its weight (e.g. is OpenAlex relevance
good enough, or is S2 semantic ranking worth the 429 hassle?) and adjust. If a review's OpenAlex
spend approaches the daily budget and coverage still feels thin, tell Denis — he can top up paid credits.

## Reference
- `reference/apis.md` — exact OpenAlex/S2/Crossref call patterns, cost model, 429 backoff, dedup
  normalization, verified Zotero add/note mechanics.
- `templates/review.html` — the reusable review-page template.
