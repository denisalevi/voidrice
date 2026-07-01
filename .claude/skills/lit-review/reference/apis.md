# lit-review — API reference & verified patterns

All commands assume the working dir is a repo. Keys are read at call time and never printed.

## OpenAlex (primary broad-recall + snowballing source)

Base: `https://api.openalex.org`. Key: append `&api_key=$(tr -d '\n' < ~/.config/openalex.key)`.
Required since Feb 2026 (no more polite pool / email param).

### Cost model (Denis = FREE plan: $1/day = 10,000 credits, refills midnight UTC)
- `search=…`  → **10 credits** (~1,000/day). Use SPARINGLY.
- `filter=…` incl. `filter=title.search:` / `filter=abstract.search:`, and facets → **1 credit** each
  (~10,000/day). This is the workhorse — 10× cheaper.
- Fetch a single record by ID/DOI → **FREE**. Hydrate metadata, references, citations for free.
- Policy: Denis runs ≤1 review/day and will spend the whole budget on it — use GENEROUSLY, but
  TRACK spend (roughly: count search× calls ×10 + filter× calls ×1) and report it in the HTML header.

### Patterns (verified working)
```bash
OA_KEY=$(tr -d '\n' < ~/.config/openalex.key)
# Cheap title/abstract filter search, date-bounded (1 credit):
curl -s "https://api.openalex.org/works?filter=title.search:hippocampal%20replay,from_publication_date:2020-01-01&per_page=25&select=id,doi,title,publication_year,authorships,abstract_inverted_index,cited_by_count&api_key=$OA_KEY"
# Broader semantic-ish recall (10 credits) — use a FEW well-crafted queries only:
curl -s "https://api.openalex.org/works?search=memory%20consolidation%20replay&per_page=25&select=id,doi,title,publication_year&api_key=$OA_KEY"
# Resolve a seed's OpenAlex ID from a DOI (FREE):
curl -s "https://api.openalex.org/works/https://doi.org/10.1038/nn.2732?select=id,referenced_works,referenced_works_count"
# FORWARD citations — "what cites paper X" (1 credit), newest first:
curl -s "https://api.openalex.org/works?filter=cites:W1974367810,from_publication_date:2022-01-01&sort=publication_date:desc&per_page=50&select=doi,title,publication_year,authorships&api_key=$OA_KEY"
```
Notes: abstracts come as `abstract_inverted_index` — reconstruct to plain text (word→positions).
Authors are under `authorships[].author.display_name`. Paginate with `per_page` (max 200) + `cursor=*`.

## Semantic Scholar (semantic relevance + recommendations + citations)

Base: `https://api.semanticscholar.org`. Key file `~/.config/semantic-scholar-api.key` (ACTIVE) →
send header `-H "x-api-key: $(tr -d '\n' < ~/.config/semantic-scholar-api.key)"`. Rate limit with
key = **1 req/s cumulative across ALL endpoints** — scripts self-throttle to 1.25s to stay UNDER it.

### 429 handling (mandatory)
- Keyless = shared pool (5,000 req / 5 min across ALL anon users) → expect 429s.
- On 429: honor `Retry-After` header if present; else exponential backoff + full jitter
  (`delay = base*2^attempt + rand`), cap ~60s, ~5 retries. Then fall back to OpenAlex/Crossref.
- Self-throttle to ~1 req/s. Prefer bulk/batch endpoints. Request minimal `fields`.

### Endpoints
```bash
# Prefer BULK search (boolean query, cheaper than relevance):
curl -s "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=replay+consolidation&fields=title,year,externalIds,abstract,authors,citationCount"
# Relevance search (richer, resource-intensive — use for focused queries):
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=hippocampal+replay&limit=25&fields=title,year,externalIds,abstract,authors"
# Batch details (collapse many lookups into one POST):
curl -s -X POST "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,year,externalIds" -d '{"ids":["DOI:10.1038/nn.2732"]}'
# Forward citations / references:
curl -s "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/nn.2732/citations?fields=title,year,externalIds"
# Recommendations ("papers like these seeds") — the CP-substitute for thematic siblings:
curl -s -X POST "https://api.semanticscholar.org/recommendations/v1/papers" -d '{"positivePaperIds":["DOI:10.1038/nn.2732"],"negativePaperIds":[]}'
```
`externalIds` carries DOI/ArXiv/PubMed — use it for dedup + verification.

## Crossref (verification + metadata-of-record, keyless)
```bash
# Verify a DOI resolves (200 = real, 404 = fabricated/typo):
curl -s -o /dev/null -w "%{http_code}" "https://api.crossref.org/works/10.7554/eLife.03970"
# Title search when no DOI (polite: add mailto):
curl -s "https://api.crossref.org/works?query.bibliographic=TITLE+AUTHOR&rows=3&mailto=mail@denisalevi.de"
```

## Dedup normalization
- DOI: lowercase, strip `https://doi.org/` prefix, compare exact. Authoritative.
- Title: lowercase, strip punctuation/whitespace, drop trailing period. Compare title +
  first-author-surname + year. Near-match but not exact → "needs discussion", never auto-drop.

## Verified Zotero mechanics (tested live 2026-07-01)
- Parent collection `LLM-literature-reviews` = key **`2S432WWF`**.
- `zotero_add_by_doi(doi, collections, tags, attach_mode="none")` → Crossref-quality metadata,
  tags + collection applied, NO cloud PDF (returns a URL). Default `"auto"` WOULD fetch OA PDF to
  cloud — avoid (protects Denis's Zotmoov local-file flow).
- Note prepend: `zotero_get_notes(item_key, raw_html=True)` → rebuild `<h1>title</h1>` + newest
  `<div data-review="…">` block + prior blocks → `zotero_update_note(note_key, html, append=False)`.
  (`append=True` concatenates at the END — wrong order.) Idempotent: skip if the review's
  `data-review` block already present.
- Retraction/quality: `scite_enrich_item(doi=…)`.
- **MCP is ADD-ONLY**: no delete-item, no delete-collection tool. All deletion is manual (Denis,
  desktop). Never assume you can undo an add.
- PDFs: after adding (metadata-only), Denis runs desktop **Zotmoov → "Move selected to Directory"**
  on the `added-by-claude` items. No API hook — always print this instruction after a batch add.

## Connected Papers — intentionally NOT integrated
CP is co-citation/bibliographic-coupling similarity ("not a citation tree"), API is early-access +
5 builds/month free. Forward citations are better done via OpenAlex `cites:` / S2 citations;
thematic siblings via S2 Recommendations. CP's visual map = optional manual browser step only.
