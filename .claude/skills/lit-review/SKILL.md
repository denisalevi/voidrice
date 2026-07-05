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
   `$(tr -d '\n' < ~/.config/semantic-scholar-api.key)` → `x-api-key` header. Do NOT cat/print keys.
5. **Keep `IMPROVEMENTS.md` current whenever you edit this skill.** `IMPROVEMENTS.md` (in this
   skill's folder) is the living backlog + change log + rejected-ideas list. If you change ANY file under this skill
   (scripts, SKILL.md, templates, reference), update `IMPROVEMENTS.md` in the same pass: move the item
   from Open backlog → Implemented, or add a new Implemented/Rejected entry with the reason. An
   undocumented skill change is an incomplete change. Read it before proposing "new" improvements —
   it may already be done or deliberately rejected.

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

**Explain the plan up front (before spending budget).** In a few plain sentences, tell Denis how
this review will work so he can redirect it before tokens are spent:
- **Ranking is embedding-based** (deterministic cosine similarity of each paper's title+abstract to
  the review topic) — that drives the sort, not an LLM.
- **Each paper gets a one-line "what it's about + why relevant to this review" note.** These are
  written by subagents: **the top ~100 by relevance use Sonnet; the long tail uses Haiku.**
- **What the split means for quality (say this in one sentence):** *Sonnet gives sharper "core vs.
  only-adjacent" relevance verdicts and is more honest about weak links; Haiku reliably says what a
  paper is about and why it's relevant but tends to over-claim relevance and name fewer of the
  review's specific themes.* Hence Sonnet where discrimination matters most (the top), Haiku for the
  skim-and-reject tail.
- **Denis can change the split** — different cutoff (top 50 / 200 / all-Sonnet / all-Haiku), or one
  model throughout. Offer it; don't assume top-100 is fixed.

### 1. Zotero-first — build the KNOWN SET (broad; serves TWO different jobs — keep them separate)
Before any web search, find what Denis already has.
- `zotero_semantic_search` on the topic (semantic recall over his library).
- `zotero_search_items` with short `Author Year` / keyword queries (substring match — keep queries
  SHORT; more words = stricter, not broader).
- For seed-paper mode, resolve the seed in Zotero if present.
Record each hit's DOI + normalized title+first-author+year + **abstract + zotero item key** → the KNOWN SET.

**The known-set does two jobs; do NOT conflate them (this bit us — see D4):**
- **Job A — EXCLUSION (dedup).** Keep the known-set BROAD/over-inclusive so nothing Denis already owns
  gets re-presented as a "new" paper. Loosely-related is fine here.
- **Job B — INCLUSION (collection membership).** The review collection should contain only the owned
  papers that are *genuinely relevant*, NOT every loosely-related known-set item. So owned items are
  **not** auto-added. Instead they flow through the pipeline EXACTLY like new candidates and are
  rendered in the SAME unified ranked list — one list, not a separate section (see D4-refined). Treat
  them identically: rank by embedding similarity (§6/rank), Sonnet "why relevant" notes + curation
  flags, **backfill their missing metadata the same way** (Zotero has no citation counts, so run
  `scripts/backfill_owned_citedby.py --run <run>` to fetch `cited_by` per DOI from OpenAlex / S2 —
  same source new candidates use — so owned rows carry a real "cited N×" chip and sort by Citations
  like anything else), and render each with the identical row renderer. The **only** differences: an
  extra `📁 in Zotero` chip (`owned:true` on the record) and the action control — owned →
  **"Add to collection" / "Skip"** (it's already in Zotero, so no new-item add); new →
  **Add / Discuss / Reject**. Only the owned items Denis picks (`decision:"collection"`) enter the
  review subcollection; tangential owned items simply sink in the ranking. Isolate them on the page
  with the `📁 Owned` / `New only` visibility filters or the "hide Owned rows" toggle. (Fetching owned
  abstracts + full author lists for this: pull them from Zotero via the local API `…/items/<key>`
  `data.abstractNote` / `data.creators`.)

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

**S2 rate note:** `search.py` and `snowball.py` both use Semantic Scholar and each self-throttle to
~1.25s, but S2's limit is 1 req/s *cumulative*. Run the S2-using stages SEQUENTIALLY, not as
overlapping background jobs, or the combined rate trips 429s. (OpenAlex-only stages can overlap.)

### 3b. Cross-domain discovery — OPT-IN (`--discovery`), off by default
Default sideways discovery is all proximity (nearby vocabulary); it structurally misses "same
mechanism, different field". Turn this on only when Denis asks for cross-domain / serendipitous
discovery. It trades precision for reach and is kept bounded so it doesn't add thousands of papers:
- **Analogy queries (6a).** One small LLM call: "State this seed's core mechanism abstractly and
  domain-neutrally; name ~5 fields with an isomorphic problem and 2–3 query strings each." Prime it
  with mechanism categories (drift/reorganization, credit assignment, consolidation, attractor
  instability, replay-like offline update, memory allocation). Write `{fields:[{field,queries}]}` and
  run `scripts/discovery.py --run <run> --queries <analogy.json>` — it searches each as a 1-credit
  title filter, `--max-pages 1`, small `--per-page`, tagging every hit `origin:"cross-domain"` +
  `discovery:{field,query}`. Ceiling ≈ per_page × #queries (~a few hundred raw), not thousands.
- **Concept-abstracted retrieval (6b).** Write domain-neutral rephrasings of the seed's contribution
  (vocabulary stripped) to a JSON list and pass `rank.py --concept-file <f>`. It builds a second
  "conceptual resonance" centroid; cross-domain candidates are scored on `max(topic_sim, concept_sim)`
  so remote-but-relevant papers aren't buried under nearest-neighbors. Writes `concept_sim` per paper.
- **Volume control (the key question).** Cross-domain candidates flow through the normal
  dedup/verify/rank. Then KEEP ONLY the top ~40 cross-domain by rank_score and drop the rest (past the
  top slice they're noise) — `log()` how many were dropped. Give that top slice **Sonnet** "why
  relevant" notes (they're the surprising ones that most need explaining, and Sonnet's cross-domain
  judgment is sharper); the dropped tail gets no notes because it's not on the page. Net: ~40 tagged,
  Sonnet-noted, separately-groupable papers — bounded and cheap. On the page they carry a
  `🌐 cross-domain` chip and are reachable via the "Cross-domain only" grouping button.

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

### 6. Relevance notes → audit → ONE interactive page

**Order matters: notes FIRST, then you audit from the notes.** This is deliberately not redundant.
The per-paper notes are the durable user-facing artifact; your audit reads the *distilled notes*
(~20 words each), not the raw abstracts, so it is cheap (one pass over ~30K tokens, not 600K+ of
abstracts) and better-targeted than re-reading everything.

**6a. Generate per-paper relevance notes (subagents, Sonnet/Haiku split).** For every NEW/Uncertain
candidate WITH an abstract, generate one grounded sentence: *what the paper is about AND why it is
relevant to THIS review question* (≤30 words; honest about weak links; no invented findings; tie to
the review's specific themes where possible). Fan out via `Workflow` (or `Agent`), returning
`{id, why_relevant}` via schema, keyed by DOI. **Top ~100 by relevance → `model:'sonnet'`; the tail
→ `model:'haiku'`** (see §0 for what the split means; honor any cutoff Denis chose). Papers with NO
abstract get no note (title only — don't hallucinate). Reuse existing notes: if a paper already has
a Sonnet note, don't regenerate it with Haiku. Write the merged `{id: note}` map to disk and merge
it into `classified.json` as a `relevance` field per candidate.

**Batching: ~40 papers per subagent** (default; validated as reliable — Haiku rarely drops items at
this size). Prep the batches with `scripts/notes_todo.py` (it emits ONLY papers still missing a note
— honoring "reuse existing notes" — truncates each abstract to ~900 chars to cut re-billed context,
and can split into batch files; `--top N` limits to the top-N ranked + all curated). One-shot each
agent: paste the batch data INLINE and instruct "emit only the schema JSON in one turn, no tool
calls, no file reads" (a file read is an extra billed turn). Run a small cleanup Agent for any
stragglers (compare returned ids to the batch; re-note the missing few). Then join the `{id: note}`
map into `classified.json` with `scripts/merge_fields.py --run <run> --map <notes.json>` — it matches
by DOI *and* by candidate-id (so no-DOI papers merge too) and REPORTS matched/unmatched so a slipped
merge is loud, not a silently empty page.

Cost note (measured): each note-agent re-bills its whole transcript every turn (LLMs are stateless
per call) and agents took ~4 turns each, so cost ≈ `agents × (fixed_load≈15K + batch_data × turns)`.
Only the ~15K fixed load (system prompt + tool schemas) is truly per-agent; the bulk is batch-data
re-billed per turn and scales with total papers, NOT batch size — so making batches fatter saves
only the fixed portion (~20–35%) while making each agent's transcript longer, and Denis prefers the
validated 40. The real lever if cost ever matters is fewer TURNS (prompt agents to read-and-emit in
one shot), not bigger batches. Speed is irrelevant to token cost. Most re-billed context is
cache-read (~10% of input rate), so $ saving < raw-token saving; on token-quota plans raw tokens =
headroom.

**6b. YOU audit the notes and set flags + curated.** Read ALL the `relevance` notes (cheap) and,
per paper, set:
- `curated: true` for the papers genuinely on-topic for the review — this REPLACES any earlier
  top-slice curation; re-derive it from the full notes so recall isn't limited to what you skimmed.
- `audit` flags (array), at minimum: `duplicate` (preprint↔published or near-dup — name the twin),
  `off-topic` / `over-claimed` (note oversells a weak link — common with Haiku), `core` (touches the
  review's specific novelty — the must-reads). Carry through any retraction/editorial-notice concern.
Write these back into `classified.json` via `merge_fields.py` (same DOI/cid-keyed merge as the notes),
not by hand. `build_html.py` renders `curated`→⭐ chip, `audit` flags→chips, `duplicate` etc. Keep it
honest and conservative — `curated` is a suggestion, the final call is Denis's, which is why the full
set stays on the page.

**6c. Retraction enrichment.** Run `scite_enrich_item(doi=…)` on candidates (at least the curated +
top ones), write a `retraction` field for anything flagged. A retracted paper must be flagged
prominently.

**6d. Build ONE page (no more separate curated/full pages).** FIRST backfill owned citation counts:
`python3 scripts/backfill_owned_citedby.py --run <run>` (fills `cited_by` on the `known` bucket from
OpenAlex/S2 by DOI, so owned rows aren't a Citations-sort no-op). Then render `templates/review.html`
from `classified.json` with `build_html.py`. **Owned (in-Zotero) items are merged INTO the single
ranked list** and render with the identical row renderer as new candidates — same full authors,
**"why relevant"** fold (open by default), foldable **abstract**, **provenance** fold, link,
relevance score, `cited N×`, `⭐` — the ONLY additions being a `📁 in Zotero` chip and an
**"Add to collection" / "Skip"** action instead of Add/Discuss/Reject (build_html keys this off
`owned:true`). New rows show verification + retraction + audit chips too. **Uncertain /
possible-duplicate rows render in their OWN section with Discuss/Reject only — no Add button even if
they have a DOI** (safety boundary). No-DOI rows likewise get Discuss/Reject only. The unified list
defaults to **relevance sort + curated-first grouping**, with grouping buttons **"⭐ Curated first" /
"Mix all" / "🌐 Cross-domain only"** and Relevance/Citations/Mix/Custom sorts that order owned and new
rows together. Visibility filters (incl. `📁 Owned`, `New only`, "hide Owned rows") isolate subsets
without changing sort. No-abstract items are appended in their own section. (build_html handles all of
this; you just supply `classified.json` + run the backfill first.)

**6e. Serve it and hand Denis the link.** A `file://` page can't auto-save, so always serve. Run
`scripts/serve.py --dir <review-folder> [--port <p>]` in the BACKGROUND. `serve.py` falls back to a
random free port if the requested one is taken, so DO NOT trust the port you asked for — read the
actual `OPEN: http://127.0.0.1:<port>/…` line from the log and `curl` it (expect 200) before quoting
it. Give Denis the one link. Served pages **auto-save** each choice to `decisions.json` in the
folder — no button needed (the 💾 button is only a `file://` fallback that downloads the file).

Then STOP and hand off to Denis. Do not add anything yet.

### 7. Add — only after Denis returns his choices
Read `decisions.json` from the review folder. The mechanical add of the chosen NEW papers (the
`decision=="add"` entries, always DOI-bearing) is now done PROGRAMMATICALLY by **`scripts/zotero_add.py`**
— no per-item MCP hops, no LLM. It talks to the RUNNING Zotero desktop's **local connector API**
(`http://localhost:23119`, keyless) and does D1 dedup + DOI resolution + batched save + note-attach in
a few HTTP calls (A1). Zotero desktop must be running — check `/connector/ping` first.

- Ensure the review subcollection exists (still MCP — the connector can't create collections):
  `zotero_create_collection("<review-name>", parent_collection="2S432WWF")` (parent
  `LLM-literature-reviews` = key `2S432WWF`). Grab the new subcollection KEY.
- Run the add:
  `python3 scripts/zotero_add.py --review-dir <folder> --name "<review-name>" --collection <subcollection-key>`
  (add `--dry-run` first to preview). It:
  - **D1 dedup against the WHOLE library** — builds a DOI→key index over every top-level item via the
    local read API (`/api/users/<uid>/items/top`), with casing variants, so items living anywhere in
    Denis's library are caught (the `known_set.json` alone missed 6/50 in drosophila-chapter-v2). Matches
    are SKIPPED from the add and reported in `zotero_add_report.json → already_owned` for you to add to
    the collection via MCP (below).
  - **Resolves each surviving DOI** via Crossref CSL-JSON content-negotiation (`https://doi.org/<doi>`,
    `Accept: application/vnd.citationstyles.csl+json`); a 404/non-JSON DOI is a dead DOI — skipped, never
    added, reported in `dead_dois`.
  - **Batch-saves** the built items via `POST /connector/saveItems` (chunked), each with tags
    `["added-by-claude","lit-review/<review-name>"]`, targeted into the subcollection, with a child
    **"LLM lit-review notes"** note (dated block + Denis's decisions.json note). It is **metadata-only —
    NO PDF attachment** (same intent as the old `attach_mode="none"`; protects the Zotmoov flow).
  - Writes `zotero_add_report.json` (saved / already_owned / dead_dois / owned_needs_collection /
    save_errors). Read it and relay the numbers.
- **Then, via MCP (cheap, not the bottleneck):** add the ALREADY-OWNED items to the subcollection —
  both the report's `already_owned` (chosen-adds found in the library) AND `owned_needs_collection`
  (owned rows Denis marked `decision:"collection"`). The connector has no add-existing-to-collection
  endpoint, so use `zotero_manage_collections(item_keys=[...], add_to=<subcollection key>)`, chunked ~25.
  **Membership-only: these existing items get NO new tags — must NOT get `added-by-claude` or
  `lit-review/<review-name>`.**
  This membership step is what makes the collection the COMPLETE picture of the review: owned items
  now flow through the page like new ones and are judged per-paper, so membership follows Denis's
  choices, NOT a blanket add-the-whole-known-set. `decision:"skip"` / undecided owned items are left
  out (that per-paper judgement is the point). After doing it, VERIFY: paginate the collection
  (`/collections/<key>/items/top`, default page is 100 — read the `Total-Results` header, don't trust
  one page) and confirm zero owned items carry `added-by-claude` (only the genuinely-new papers do).
After the batch, print: (a) a summary of what was added (new items) vs. added-to-collection (owned),
(b) the explicit **desktop PDF steps** (no API hook exists for either — they are desktop-UI only; see
tickets A2/A3). Give them as an ordered, first-timer-proof sequence, and stress that ORDER matters
(Zotmoov only moves PDFs that already exist, so fetch them first):
"In Zotero desktop — Claude can't do these, they're desktop-only. Select the new items (click the
`added-by-claude` tag in the tag selector, or search it, then Ctrl/Cmd-A):
 (1) Right-click → **Find Available PDF** (older Zotero: *Find Full Text*) — fetches the missing PDFs.
     Do this FIRST; Zotero's resolver uses your library proxy and beats any scripted OA fetch (agents
     get publisher 403s). For the few it can't find (Science, some Cell/Wiley), **add the PDF manually**
     where possible: download it to your Downloads folder, then select the item → right-click →
     **ZotMoov: Attach New File** (attaches your last-downloaded file). The browser **Zotero Connector**
     on the article page also works.
 (2) THEN, with the items still selected, right-click → **Zotmoov: Move selected to Directory** —
     relocates the downloaded PDFs into your local linked-file storage."

## Per-paper notes (prepend pattern)
One note per paper, titled **"LLM lit-review notes"**, each review prepends a dated block.
**For the NEW papers added by `zotero_add.py`, the note is created for you** (fresh child note, dated
block, Denis's decisions.json note) — D1 dedup guarantees these are new, so there is no pre-existing
note to merge. The MCP prepend pattern below is for the OTHER cases: adding/updating a note on an
already-OWNED item (multi-review overlap), or a manual one-off.
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
