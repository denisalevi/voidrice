# lit-review — improvement backlog & change log

**Purpose.** This is the *living* record of the `/lit-review` skill's evolution. It has
three roles:

1. **Open backlog** — proposed fixes not yet implemented, ranked, each with enough
   detail to act on.
2. **Change log** — what has already been implemented (so we don't redo it) and what was
   **deliberately rejected, with the reason** (so we don't re-propose it).
3. **Contract for editors** — see the rule below.

> **RULE FOR ANY AGENT EDITING THIS SKILL.** Whenever you change anything in this skill's
> folder (scripts, SKILL.md, templates, reference), you MUST update
> this file in the same pass: move the item from **Open backlog** to **Implemented**, or add
> a new **Implemented**/**Rejected** entry describing what you did and why. An undocumented
> skill change is an incomplete change. Keep entries short; link to the file/function you
> touched. Do not delete history — mark things done, don't erase them.

The older `literature-reviews/lit-review-improvement-brief.md` (in the thesis repo) is the
2026-07-02 review that seeded the first batch of Implemented items; this file supersedes it
as the place new work is tracked.

---

## Open backlog (proposed, not yet done)

Ranked roughly by value/effort. Ticket IDs are stable so we can reference them.

### Attachment / PDF handling (BUG — found 2026-07-02, drosophila-chapter)

- **A2 — `zotero_add_by_doi(attach_mode="none")` is NOT honored; it still creates PDF attachment
  records, and those land as broken local pointers.** *Incident:* after the drosophila-chapter adds,
  13 items had 15 `imported_file` PDF attachments with `md5:None`/`mtime:None` and NO local file
  (storage folder absent; local API 302-redirects to a non-existent `file://…/storage/<key>/<f>.pdf`).
  Several were on items explicitly added with `attach_mode="none"` (RKHQXCA7, V26TP8XS, HM8RP7F5), so
  `none` did not suppress attachment creation. The MCP appears to fetch the OA PDF and register/upload
  it (Denis saw the PDFs in the Zotero *web* view = cloud copy exists) but this desktop client never
  got the file-sync md5/mtime, so it can't download them back → "attached file could not be found".
  Also saw duplicate temp-named attachments like `_tmp_tmpmvlo2upr_<file>.pdf` = a half-completed
  download/import.
  **Why it matters:** the skill's whole point of `attach_mode="none"` is to keep metadata-only and
  let **Zotmoov** move real PDFs to Denis's local linked-file storage. Cloud-uploaded PDFs with broken
  local pointers defeat that and clutter every item with a dead paperclip.
  **Fixes to pursue:**
  1. Verify what `attach_mode` values the MCP actually respects; if `none` is ignored, either (a) use
     the programmatic batch-write path (A1) which creates NO attachment at all, or (b) after adding,
     detect+delete any auto-created attachment whose local file is missing (md5/mtime null AND no file
     in storage/<attKey>/). A cleanup pass = list children, drop `imported_file` atts with no backing
     file. Deterministic, no LLM → Haiku or a script.
  2. Distinguish "cloud-uploaded, not synced down" (recoverable by a Zotero desktop file-sync) from
     "never stored" (md5 null). If cloud copy exists, the fix is a desktop **Sync** (can't be triggered
     via API from here) — tell Denis to enable "Sync attachment files … using Zotero storage" and hit
     Sync. Only delete+refetch if a full sync leaves them null.
  3. Do NOT upload PDFs to Zotero cloud storage at all in the add flow — it competes with Zotmoov and
     burns Denis's cloud quota. Metadata-only add + Zotmoov is the intended pipeline (see zotero-setup
     memory).

- **A3 — Do NOT try to fetch/attach PDFs from the agent side; the add flow is metadata-only and the
  USER runs Zotero's "Find Full Text" + Zotmoov.** *Evidence (drosophila-chapter-v2, 2026-07-02):* of
  31 PDF-less items, Unpaywall reported an OA `url_for_pdf` for 15, but direct scripted download of
  those URLs **403'd** (publishers block non-browser user-agents / need session cookies) — only the
  eLife known-URL pattern (`elifesciences.org/articles/<id>.pdf`) downloaded a real `%PDF`. Then Denis
  ran Zotero's **Find Full Text** (right-click items) and it fetched **23 PDFs in one go** — because the
  desktop client uses site-specific translators, browser-like headers, and Denis's library
  proxy/OpenURL, which a plain script cannot replicate. Final state: 41/49 with PDFs; the ~8 left are
  genuinely paywalled (Science, some Cell Press/Wiley) and need the browser **Zotero Connector**.
  **Takeaways for the skill:**
  - The intended pipeline is: skill adds **metadata-only** → USER runs Zotero *Find Full Text* on the
    new items (tag `added-by-claude` makes them selectable) → USER runs *Zotmoov: Move to Directory*.
    Say this in the §7 hand-off text (it already mentions Zotmoov; add the Find-Full-Text step before it).
  - There is **NO API/endpoint to trigger "Find Available PDF" / "Find Full Text"** — it's a desktop-UI
    action. Probed `localhost:23119` (`/findAvailablePDF`, `/connector/findAvailablePDF`, `/connector/savePDF`
    all 404). Do not spend tokens hunting for one.
  - Agent-side OA fetch is low-yield (403s) and competes with the far-better client Find Full Text.
    If ever worth doing, restrict to publishers with clean scriptable PDF URLs (eLife pattern; bioRxiv
    `.full.pdf`) and skip Cell Press/Wiley/Science. Not worth building unless Denis asks.

### Dedup / correctness

- **D1 layer-1 (add-time exact-DOI gate) — DONE, folded into A1** (see Implemented 2026-07-05).
  `zotero_add.py` builds a DOI→key index over the WHOLE library and skips any chosen-add already
  owned, with casing variants. **D1 layer-2 still OPEN (optional nicety):** run the same exact-DOI
  pass over top-N + curated DURING classification and show an "already in library" chip on the HTML
  page, so Denis sees it BEFORE choosing. Layer-1 is the safety net; layer-2 is just earlier signal.
  Caveat preserved: an exact-DOI miss doesn't rule out owning the published twin of a preprint — the
  fuzzy title pass (dedup_verify) stays as the second signal, and D3 collapses the twins.

---

## Implemented

### 2026-07-05 — A1 + D1(layer-1): programmatic keyless batched Zotero add (Fable 5, live-tested)
New `scripts/zotero_add.py` replaces the ~2×N sequential MCP hops (`zotero_add_by_doi` +
`zotero_create_note`) at the END of the pipeline with a handful of HTTP calls to the RUNNING Zotero
desktop's **local connector API** (`http://localhost:23119`) — **no API key, no LLM**.
- **Write path discovered this session (better than the ticket's plan).** The ticket assumed the
  web API (`api.zotero.org` + `~/.config/zotero-api.key`, which does NOT exist here). Probed the
  live Zotero **9.0** instead:
  - Local **read** API `/api/users/<uid>/items…` mirrors Web API v3, keyless (uid resolved to 5685020
    from `users/0` self-alias). But its `/items` collection endpoint is **read-only** (`POST` → 400
    "Endpoint does not support method"; `DELETE` → 501). So no batch write there.
  - **Local connector `/connector/saveItems` DOES write, keyless** (needs a browser-ish User-Agent +
    `X-Zotero-Connector-API-Version: 3`). Verified: single + batch item creation → HTTP 201, items
    land in the library; `target:"C<collectionKey>"` routes into a specific collection (tested
    `C2S432WWF` → landed in `2S432WWF`); `tags:[{tag}]` and child `notes:[{note}]` both honored
    (numChildren:1). `/connector/import` also works (translates RIS authoritatively) but ignores
    tags/target/notes, so `saveItems` is the right path. There is **NO connector endpoint to add an
    EXISTING item to a collection** (`/connector/collections|addToCollection` → 404) — so owned→
    collection membership STAYS on MCP `zotero_manage_collections` (cheap, not the bottleneck).
- **What zotero_add.py does:** read decisions.json → take `decision=="add"` (DOI-bearing) → **D1
  layer-1 dedup** (build DOI→key index over ALL top-level library items via the local read API, with
  casing variants; skip already-owned, report them) → resolve each surviving DOI via **Crossref
  CSL-JSON content negotiation** (`https://doi.org/<doi>`, `Accept: …csl+json`; 404/non-JSON = dead
  DOI, skipped, reported) → **`csl_to_zotero()`** maps CSL→Zotero item (journalArticle/preprint/
  conferencePaper/bookSection/… with per-type container field; zero-padded date; JATS-stripped
  abstract) → attach tags `["added-by-claude","lit-review/<name>"]` + a dated "LLM lit-review notes"
  child note → **batch `POST /connector/saveItems`** (chunked, default 20) into the subcollection.
  **Metadata-only — NO PDF attachment** (same intent as old `attach_mode="none"`; protects Zotmoov).
  Writes `zotero_add_report.json` (saved / already_owned / dead_dois / owned_needs_collection /
  save_errors). `--dry-run` previews without writing.
- **Live-tested end-to-end** against Denis's running Zotero (synthetic decisions.json): real DOI
  `10.1038/nature12373` added as item 6NGSHRDN — correct type/title/DOI/Nature/vol 500/date/creators,
  tags `[added-by-claude, lit-review/a1-selftest]`, collection `2S432WWF`, child note with the dated
  block + Denis's note; owned DOI `10.1016/j.tics.2022.10.004` correctly caught by D1 as owned
  (→ZMMBHNUU, library index = 1431 DOIs / 1650 items — exactly the whole-library coverage the
  known-set missed); dead DOI skipped; `reject` ignored; `owned→collection` reported for MCP. Report:
  saved 1, errors 0. Unit-tested date-padding + CSL type mapping separately.
- **SKILL §7 rewritten** to call the script (create subcollection via MCP first → run zotero_add.py →
  then MCP `zotero_manage_collections` for the report's `already_owned` + `owned_needs_collection`).
  Per-paper-notes section clarified: new adds get their note from the script; the MCP prepend pattern
  is now only for owned/multi-review/manual cases.
- **Cleanup owed:** the write-path probing left ~5 `ZZZ-litreview-…-DELETE-ME` test items in the
  library (searchable by "ZZZ-litreview"); the local API can't delete (501) — remove manually in
  Zotero desktop. Future: probe into a throwaway collection or gate probes behind `--dry-run`.

### 2026-07-05 — U1 floating nav widget + U2 verified (Fable 5, browser-tested)
- **U1 — always-on-screen floating nav.** New `#navwidget` (fixed bottom-left, so it never collides
  with `#banner` bottom-center or `#themetoggle` top-right) in `templates/review.html`:
  **↧ Next undecided** (blue; scrolls to the next undecided row in on-screen/sort order, skipping
  filtered+decided rows, wraps to top if none below, flashes the target via `.flash` keyframe;
  auto-disables at 0 undecided), **↥ Top** / **↧ Bottom**, a **live counter** (`N undecided / Total`
  + `add·disc·rej·coll`), and a **collapse** toggle (`–`/`+`). Counter is refreshed inside the
  existing `updateCounts()`; "undecided" spans new+owned so it matches what Next-undecided jumps to
  (the header `#counts` stays new-only — intentional). Visualization-only: never touches
  decisions.json / the add pipeline.
- **U2 — already existed (`#filterbar`), now VERIFIED.** The filter bar (All/Undecided/Add/Discuss/
  Reject/Collection/Curated/Owned/New/No-abstract/Cross-domain) was shipped 2026-07-02. This session
  confirmed in-browser (claude-in-chrome) that each filter shows the right subset AND — the key U2
  invariant — **filtering never reorders the list** (DOM order identical before/after; sort and
  visibility are orthogonal). Add→1, Curated→5 (all curated), Owned→12 (all owned), Cross-domain→3
  (all discovery), All→reset. No new code needed for U2.
- **Browser verification (claude-in-chrome, port 8791, 52-row synthetic fixture):** widget renders on
  load and on resume; making Add/Discuss updates header + widget counters in lockstep; autosave still
  fires ("✅ Auto-saved (2 decisions)"); Next-undecided scrolls to + flashes the correct next row and
  skips decided ones; collapse toggles; Next disables when all decided; prior decisions.json restores
  on reload with widget reflecting it; the D3 `🔗 1 version merged` chip renders. **No console errors**
  on load or interaction. decisions.json stayed clean (only the 2 real decisions). Lesson from prior
  sessions honored: verified by DRIVING the page, not grepping — and used the `javascript_tool` DOM
  probe when screenshot capture (CDP) intermittently timed out, which is more reliable for asserting
  filter/counter state anyway.

### 2026-07-05 — D2 + D3 shipped in dedup_verify.py (Fable 5)
Both are pure-Python, deterministic, browser-independent — unit-tested in isolation (see the test
block run this session; all D2/D3 assertions pass). File: `scripts/dedup_verify.py` (+`re` import
added; +chip in `scripts/build_html.py`).
- **D2 — editorial-artifact drop.** New `is_editorial_artifact(c)` + module-level compiled regexes:
  DOI matches `\.sa\d+$`, `10\.7554/elife\.\d+\.\d{3}$`, or `^10\.3410/f\.`; OR title starts with
  `decision letter|author response|reviewer #|editor'?s? (evaluation|assessment)|elife assessment|
  faculty opinions recommendation`. Applied as a pre-merge filter in `main()` (drops BEFORE the
  merge/classify, so artifacts never reach any bucket). Count logged (`D2: dropped N …`) and written
  to `dedup_summary.json` as `editorial_artifacts_dropped`.
- **D3 — preprint/version twin collapse.** New `collapse_twins(items, threshold=0.92)`: blocks by
  first-author surname, clusters within a block on title `SequenceMatcher ≥ 0.92`, keeps ONE row per
  cluster preferring a *published* DOI (`_is_published_doi` rejects `^10\.1101/` and
  `10\.7554/elife\.\d+\.\d+$` versioned), then most-cited, then longest author list. Folds
  abstract/venue/year/url/cited_by/sources from dropped twins into the keeper; annotates keeper with
  `merged_versions:[{title,doi,year}]` and each dropped twin with `collapsed_into`. Applied to the
  **NEW bucket only** (owned/known twins are already deduped separately — see BUGFIX 5), right after
  classification and BEFORE verification (so we don't spend verify calls on collapsed twins). Count in
  summary as `version_twins_collapsed`. `build_html.chips()` renders a `🔗 N versions merged` chip
  (hover = the merged DOIs/titles).
- **NOT yet browser-verified** (they don't touch interactive JS — the only UI surface is the static
  `🔗` chip string). If a real review run surfaces the chip, eyeball it once.

### 2026-07-03 — dedup_verify: blank/non-numeric year crash in fuzzy matcher (Fable 5, change-point-detection review)
`classify()` did `int(kyear)` after only a `kyear is not None` guard, so a known-set item with an
empty-string year (`""`) — common when the full-library dump can't parse a `date` field — raised
`ValueError: invalid literal for int()`. Replaced the inline `int()` with a local `_yr()` helper that
returns `None` on `TypeError`/`ValueError`, applied to BOTH candidate and known year, so an
unparseable year on either side just means "year unconfirmed" (matches the existing intent in the
comment). File: `scripts/dedup_verify.py`, `classify()` ~line 55. No behavior change for numeric years.

### 2026-07-02 — D4 REFINED: owned items fully unified with new (one list) + cited_by backfill (Fable 5)
Denis asked to stop special-casing owned ("known") items and treat them EXACTLY like new candidates,
distinguished only by an `📁 in Zotero` chip and an `owned` flag — the sole behavioral difference being
the action (collection/skip vs add/discuss/reject). Done and verified in-browser (claude-in-chrome):
- **Missing-metadata parity — new `scripts/backfill_owned_citedby.py`.** Owned items had `cited_by=None`
  (Zotero stores no cite counts), so Citations-sort was a no-op for them. The script fetches `cited_by`
  per DOI from **OpenAlex** (`works/https://doi.org/<doi>?select=cited_by_count`, same path
  search.py/snowball.py use) with **Semantic Scholar** fallback, concurrent + host-rate-limited, only for
  items still null, and writes it back into the `known` bucket. Idempotent. drosophila-chapter-v2 result:
  **55/62 with-DOI owned resolved**; 7 have DOIs that 404 in OpenAlex AND S2 AND Crossref (stale/invalid
  — same class as the fabricated DOIs fixed in BUGFIX 5, can't help without correcting the Zotero DOI);
  28 have no DOI (left null, unavoidable). Now added to §7/§6d as a required pre-build step.
- **Unified rendering — `build_html.py`.** Replaced the `bucket=="known"` special-casing with an
  `is_owned(c,bucket)` helper (keys off `owned:true` on the record, legacy `known` still honored). Owned
  rows now render through the IDENTICAL `row()`/`chips()` path as new ones — same relevance / cited N× /
  ⭐ curated / abstract / why-relevant / provenance — PLUS a `📁 in Zotero` chip and `data-owned="1"`.
  Only divergence: the action control (collection/skip). In `main()`, owned items are tagged `owned=True`
  and **merged INTO the `new` ranked list**, re-sorted by `rank_score`, so the page has ONE unified list
  (`{{ROWS_KNOWN}}`/`{{COUNT_KNOWN}}` removed; new `{{COUNT_OWNED}}` reports the owned subset).
- **One list, not a bottom section — `templates/review.html`.** Deleted the separate `#known` section;
  owned rows live interleaved in `#newlist`. `SORT_LISTS` collapsed to `['newlist']` (owned + new sort
  TOGETHER now — Relevance/Citations/Mix/Custom all order them uniformly). All `.known`/`#known` JS refs
  (`rowMatches`, `updateCounts`, `collectDecisions`, `setAll`, `reorderList`) rewritten to key off
  `data-owned`. "hide Owned" changed from hiding a section to hiding owned ROWS in place (body
  `.hide-owned` + CSS). Removed the `.known .paper{opacity:.85}` dimming so owned rows look identical.
  The `📁 Owned` / `New only` visibility filters + "hide Owned rows" toggle isolate the subsets.
- **In-browser verification (claude-in-chrome, 2026-07-02).** 90/90 owned rows interleaved in #newlist;
  each carries relevance + 📁 in Zotero + (55×) cited chips + collection/skip. **Citations sort is now
  monotonic across the whole 1950-row list and the top-cited owned item (1168×) sorts to global index 26**
  — previously a no-op. Owned filter → 90 rows, both sticky bars stay visible; New-only excludes owned;
  hide-owned hides owned rows. Collection button = blue highlight + blue row border, Skip = dark, mutually
  exclusive. Sticky bars stacked 0–170 / 170–267 / 267–333, zero overlap at scrollY 3000. Prior decisions
  restored (50 add / 25 owned-collection), all 78 anchored to a live row (0 unmatched). **No page JS
  console errors** (only unrelated Zotero-Connector extension errors). SKILL §1/§6d/§7 updated; §7
  collection-membership now follows per-paper `decision:"collection"` choices instead of blanket
  add-the-whole-known-set (that was the old auto-include behavior D4-refined replaces).

### 2026-07-02 — owned-items-in-pipeline + visibility filters (this session)
- **D4 done** (SUPERSEDED by "D4 REFINED" above — owned items are no longer a separate "Already in
  your Zotero" group; they're merged into the one ranked list. History kept for context.) — the
  known-set now serves both jobs correctly: still broad for dedup (exclusion), but owned items are ALSO
  ranked (embedding sim to topic), Sonnet-noted, curation-flagged, and (originally) rendered on the page
  in a separate "Already in your Zotero" group with `📁 in Zotero` chip + **➕ Add to collection /
  Skip** actions (not auto-added). Only user-picked owned items enter the collection (membership-only,
  no `added-by-claude`). SKILL §1 + §7 updated; `build_html.py` known-row rendering + `data-zkey`;
  template known-section actions; decisions.json now carries `owned:true` + `decision:"collection"`.
- **U2 done (partial)** — page-wide visibility filter bar (All / Undecided / Add / Discuss / Reject /
  ➕ Collection / ⭐ Curated / 📁 Owned / New only / No-abstract / 🌐 Cross-domain) that hides rows
  WITHOUT changing sort, plus "hide Owned section" toggle.
- **BUGFIX (found via in-browser test with claude-in-chrome):** the filter bar was originally placed
  INSIDE `<section id="new">`. `setFilter` hides any section with no visible rows → clicking "Owned"
  hid `#new` and took the filter bar (incl. the "All" reset) with it, trapping the user in Owned-only
  with no way back. Fix: moved the filter bar OUT into a standalone `#filterbar` div that is
  `position:sticky; top:0` so it's never filtered and always reachable; added a "showing N … — click
  All to reset" hint and auto-scroll to the first still-visible section on filter.
- **BUGFIX 2 (same root cause):** the Sort/Grouping bar was ALSO inside `#new` and vanished under the
  Owned filter. Moved it out into its own sticky `#sortbar2`. AND extended sort to apply to the Owned
  list too: `applySort`/`applyCustom`/`reorder` now loop over `SORT_LISTS=['newlist','known']`, sorting
  and grouping each list independently (curated-first / mix / custom all work per-list; discovery
  grouping stays New-only). Verified in-browser: Owned re-sorts live, Mix-all → globally
  relevance-descending, Curated-first → 44 curated block leads.
  **Lesson for future template work: (1) any always-needed control (reset, nav, sort) must live OUTSIDE
  the filterable/collapsible regions; (2) VERIFY interactive template changes by actually driving the
  page in a browser (claude-in-chrome / CDP), not by grepping the HTML — multiple regressions here
  shipped from grep-only "verification".**
- **BUGFIX 3:** the new `collection`/`skip` decision buttons got the `.sel` class on click but had NO
  visual style — the CSS only colored `.choice button.sel[data-c=add|discuss|reject]` and only bordered
  `.paper[data-decision=add|discuss|reject]`. Added `.sel` styles for `collection` (blue) and `skip`
  (dark), plus row border-left for `data-decision=collection|skip`. Rule: whenever a NEW decision value
  is introduced, add BOTH the `.choice button.sel[data-c=X]` and the `.paper[data-decision=X]` styles,
  or the selection is invisible.



### 2026-07-02 — owned-rows audit & fixes (this session, Fable 5)
Audit of the owned-papers feature above; verified by reading files AND driving the page in
claude-in-chrome. Four things were actually broken; all fixed:
- **BUGFIX 4 — owned rows showed only the FIRST author (often a lone surname).** Root cause: the
  `known`-bucket items carried `authors` from `known_set.json`, which stores only a first-author
  surname string. `build_html.row()` joins the author list, so a 1-element list rendered one name;
  worse, had it been a bare string it would have char-split. **Fix (data-side):** fetched full
  `data.creators` for each owned item from the Zotero local API
  (`GET http://localhost:23119/api/users/0/items/<zkey>?format=json`), built `"Firstname Lastname"`
  strings (matching how `new` rows render full author lists), and wrote them back into
  `classified.json`'s `known` items as a **list of strings**. Now 84/90 owned rows show all authors
  (6 are genuinely single-author). No template change needed — `row()` already handled a proper list.
- **BUGFIX 5 — duplicate owned papers (preprint↔published, and one triple).** The known-set held 7
  same-work clusters (8 redundant rows): Jiang dopamine (bioRxiv+PLoS), Springer model (bioRxiv +
  eNeuro + a webpage stub), Pribbenow (bioRxiv+eLife), Bennett + its "Correction to" note, Li
  connectome (bioRxiv+eLife), Gkanias incentive (bioRxiv+eLife), Eschbach (bioRxiv+Nat Neurosci).
  **Fix (data-side, display-dedup only — Zotero untouched):** clustered the `known` bucket by
  fuzzy normalized title (SequenceMatcher ≥0.82, preprint/correction words stripped), kept ONE row
  per work — the **published** version (real journal DOI, from Zotero's own `data.DOI`, over a
  `10.1101/`/bioRxiv DOI or empty-DOI webpage stub) — and **merged the richest metadata** into the
  keeper (relevance/relevance_model preferred-or-borrowed, `curated` OR'd, `rank_score` = max across
  cluster, abstract kept). Also **corrected two stale/fabricated DOIs** on kept items from Zotero
  truth: `GBIX7KN6` `10.7554/eLife.62576-dopamine`(fake) → `10.1371/journal.pcbi.1009205`;
  `YEB98L8I` → `10.1186/s12868-018-0451-y`. Result: known 98 → 90. This is the D3 idea applied to
  the owned bucket (see D3 backlog for doing it generically in dedup).
- **BUGFIX 6 — the three sticky bars (`header`, `#filterbar`, `#sortbar2`) all had `top:0` and
  piled up / overlapped when scrolled.** They didn't *disappear* (BUGFIX 1/2 fixed that) but they
  stacked on top of each other. **Fix (template):** `#filterbar` now sticks at `top:var(--hdr-h)`
  and `#sortbar2` at `top:calc(var(--hdr-h) + var(--flt-h))`; a small `updateStickyOffsets()` JS
  measures header + filterbar heights on load/resize (and once after 300ms for emoji/font settle)
  and sets those CSS vars — robust to the bars wrapping on narrow widths. Verified in-browser at
  scrollY=3000: header 0–170, filterbar 170–267, sortbar2 267–333, zero overlap.
- **Re-verified (browser) the prior BUGFIX 1/2/3 still hold** after these changes: Owned filter
  keeps both bars visible + "All" clickable + New hidden/Owned shown; owned list re-sorts by
  relevance (rank_score desc; citations is a no-op for owned since they carry no cite counts);
  collection/skip buttons are mutually exclusive with blue/gray highlight + row border; **no JS
  console errors** on load. `decisions.json` left intact (55 real decisions; no orphan pointed at a
  dropped preprint zkey). **Lesson reinforced:** when items come from `known_set.json`, hydrate full
  author lists from Zotero before rendering, and dedup preprint/published twins — both are structural,
  not one-offs, so consider doing them in the pipeline (D3 + a known-set author-hydration step).

### 2026-07-02 — first review (fresh Opus/Fable 5 + Codex GPT-5.5), by Opus 4.8
Full detail in `literature-reviews/lit-review-improvement-brief.md`. Summary of what shipped:
P1a All→Add skips no-DOI rows; P1b uncertain bucket kept separate through ranking & rendered
Discuss/Reject-only; P2a arXiv/PMID in verify + as candidate fields; P2b add-time DOI-existence
check for the chosen subset; P2c attempted-and-failed drop for uncertain too; P3a shared
per-host rate limiter; P3b S2 stages sequential; P3c Retry-After HTTP-date parse; P3d OpenAI
embed retry/backoff; P4a `merge_fields.py` deterministic keyed join w/ matched/unmatched report;
P4b field-by-field best-of merge in dedup; P4c provenance foldout; P4d resume-by-cid; P4e
rank_score-driven default sort; P5a/P5c one-shot inline notes + abstract truncation; P5d
`notes_todo.py` note-cache diff + `--top`; P6a `discovery.py` cross-domain analogy queries;
P6b `rank.py --concept-file` concept centroid + top-40 volume control + 🌐 UI; P7 misc cleanups.

---

## Deliberately rejected (do not re-propose without new reason)

- **P2a (broad) — full arXiv/PMID resolution machinery beyond the verify fallback.** Trusted-
  index candidates are real by construction; only wire deeper if a no-DOI paper is actually
  chosen for add. (2026-07-02)
- **P5b — fold the audit into the note pass.** Loses the cross-batch view (dup detection,
  over-claim pattern, curation with the whole set visible). Audit stays a separate cheap
  notes-only read. (2026-07-02)
- **P3b (option ii) — cross-process S2 lockfile.** Over-engineered for a ≤1-review/day tool;
  documented sequential-stages instead. (2026-07-02)
- **P6c — concept/co-citation bridges.** Deferred, lower priority. (2026-07-02)

---

## Invariants (never break these)
Add-only; **never write `9_backmatter/references.bib`** or any `.bib`; nothing added to Zotero
without explicit per-paper approval from the served page; served-page autosave design; Zotero
MCP add mechanics (`attach_mode="none"`, `added-by-claude` + `lit-review/<name>` tags, review
subcollection under `LLM-literature-reviews` = `2S432WWF`).
