# llm-wiki — improvement backlog & change log

**Purpose.** The *living* record of the `/llm-wiki` skill's evolution: open backlog,
change log, and rejected ideas with reasons.

> **RULE FOR ANY AGENT EDITING THIS SKILL.** Whenever you change anything under
> `~/.claude/skills/llm-wiki/` (SKILL.md, templates, reference), you MUST update this file
> in the same pass: move the item from **Open backlog** to **Implemented**, or add a new
> **Implemented**/**Rejected** entry with what you did and why. An undocumented skill change is an
> incomplete change. Don't delete history — mark things done.

---

## Implemented

- **I6 — Renamed to `llm-wiki`; unified single skill with 3 operations (2026-07-03).** Denis chose
  ONE skill (`llm-wiki`) over splitting into integrate/lint/query, on the reasoning that (a) the
  three operations share ~80% of context (AGENTS.md-is-truth, link/naming conventions, plugin-vault
  detection, commit/push) so one skill avoids duplication/drift, and (b) naming the operation
  ("lint my wiki") makes the task unambiguous, so a separate trigger isn't needed. Changes:
  - `git mv wiki-integrate llm-wiki`; renamed `name:` and rewrote the description to name all three
    operations (INGEST / LINT / QUERY) with their trigger phrases, so `/llm-wiki` + "lint…" +
    "ask the wiki…" all match.
  - Restructured SKILL.md: shared context up top + a "Which operation? (route first)" selector, then
    three distinct top-level sections (`# Operation: INGEST/LINT/QUERY`). Ingest close-out now calls
    a quick Lint over touched pages.
  - **Promoted Query to a real (lightweight) operation** instead of a footnote: answer FROM the
    wiki's synthesis (not raw papers), cite pages, flag gaps, and OFFER to file a valuable answer
    back as a page (Karpathy's rule). Deep beyond-wiki questions routed to /lit-review + Ingest.
  - **Lint** expanded into its own section: added one-directional-edge and naming-drift checks
    (fallout of the cite-key + reciprocal-link decisions); noted it parallelizes (per-page checks
    fan out, cross-page reconciliation after).
  - Rejected a `/wiki` umbrella orchestrator (narrative-style) — unnecessary for a single skill.
  - Fixed a stray `</content></invoke>` tail left in the original SKILL.md.

- **I1 — Initial skill (2026-07-02).** Portable "integrate Zotero papers into an LLM wiki" skill.
  Design decisions taken with Denis:
  - **Per-wiki AGENTS.md is the source of truth** (not the skill). Skill reads/applies an existing
    wiki's AGENTS.md; generates one from `templates/AGENTS.template.md` for fresh wikis. Modeled on
    the thesis LLM wiki's own AGENTS.md but stripped of openclaw-host paths / single remote.
  - **Three paper-source modes, offered and asked**: Zotero collection/tag, explicit list, wiki's
    own reading queue (e.g. an `agent-only/<topic>-inventory`). Default = the `/lit-review` handoff
    collection.
  - **Full-text synthesis per paper, one at a time** (Denis's chosen default) via
    `zotero_get_item_fulltext` (MCP), archived to raw-input before synthesizing.
  - **bib4llm is fallback-only and NOT assumed installed** — on Denis's machine it's absent
    (the AGENTS.md's bib4llm setup lives on the openclaw host). `reference/bib4llm-setup.md` has a
    detect-first check and a from-GitHub micromamba install, gated on the user asking.
  - Uses the `mcp__zotero__*` MCP tools directly (available in-session), not `mcporter` (absent here).

- **I2 — Karpathy LLM-wiki alignment + env-agnostic bib4llm (2026-07-02).** After Denis shared the
  reference links:
  - Reframed SKILL.md + AGENTS.template around the canonical **LLM wiki** concept: three layers
    (raw sources / wiki / schema=AGENTS.md) and three operations (Ingest / Query / Lint), citing the
    Karpathy gist and the Obsidian `karpathywiki` plugin.
  - Added a **Lint step** (Step 4) — periodic health-check for contradictions, stale claims, orphan
    pages, missing cross-refs, uncertainty drift — to both the skill and the AGENTS template. The
    skill previously only did Ingest.
  - Rewrote `reference/bib4llm-setup.md` to **detect the user's env manager and match it** (uv /
    pipx / micromamba·mamba·conda / plain venv) instead of hardcoding micromamba. On Denis's machine
    both `uv` and `micromamba` are present (no conda/pipx) — so the skill must ask when ambiguous.

- **I3 — Plugin-managed-vault conformance (2026-07-02).** Denis shared
  `github.com/green-dalii/obsidian-llm-wiki` (the plugin behind the community `karpathywiki` page).
  It has a fixed on-disk contract (`sources/`+`wiki/`+`schema/`; `wiki/entities/` vs
  `wiki/concepts/`; `[[wikilinks]]`; frontmatter `type/sources/aliases/reviewed`; "Mentions in
  Source" quote blocks; `reviewed: true` overwrite guard). Decision: **do NOT retarget the skill to
  that format** (it's entity-extraction oriented; Denis's need is deep per-paper synthesis, which the
  plugin doesn't do). Instead added a **detect-and-conform** note to Step 0-A so the skill respects a
  plugin-managed vault (wikilinks, frontmatter, `reviewed` guard) rather than scaffolding its own
  layout beside it. Per-wiki-AGENTS.md-is-truth already made this mostly free; this makes it explicit.

- **I4 — Graph-view link connectivity (2026-07-02).** Verified against Denis's live wiki: it uses
  **standard relative Markdown links with `.md`** (105 of them) and **no frontmatter** — NOT
  `[[wikilinks]]`. `log.md` shows Denis explicitly reverted an earlier agent's switch to `[[…]]` and
  mandated Markdown links in AGENTS.md. So the skill's defaults already match; no change needed there.
  The real graph concern is orphan pages: Obsidian resolves relative `.md` links to notes and draws
  edges, but only if pages are linked. Made **reciprocal internal linking (paper↔topic) a required
  step, not polish**, in Step 2.7 + the AGENTS template, and noted Zotero `zotero://` URIs are not
  graph nodes. This reinforces the existing orphan-page lint check.

- **I5 — Citation/concept graph + cite-key filenames (2026-07-02).** Denis clarified the wiki's
  value is the *link structure*: one page per paper, papers linked to each other (references,
  important-to, contradicting) and to concepts, concepts back to papers — all links correct.
  - **Paper-page filename = Zotero citation key exactly** (`Felsenberg2018.md`, `Aso2014a.md`), so
    page name == cite key == LaTeX `\cite{}` key → one identifier, guessable cross-links. Get the
    key via `zotero_get_item_metadata`/`zotero_search_by_citation_key`; mirror Zotero's a/b/c.
    Existing hyphenated pages (`Adams-MacKay-2007.md`) left as-is unless Denis renames; link to
    their real filename. Added a *Paper-page naming* subsection.
  - **Typed, reciprocal cross-links are now a first-class ingest deliverable** (Step 2.7), not
    hub-and-spoke: paper↔paper (builds-on / contradicts / supersedes / shares-mechanism /
    evidence-for, one-clause reason, mirrored), paper↔concept, concept↔concept. Orphan or
    one-directional = lint failure. I earlier (I4) called paper↔paper links "noise / toggle only" —
    **reversed** for a literature/thesis wiki, where the typed edge IS the knowledge.
  - Karpathy check: the gist endorses "cross-referencing" + "no missing cross-refs / no orphans"
    generically (entities/concepts) but does NOT specify typed literature edges — those are our
    domain refinement. Recorded so it's not re-litigated.
  - **Added `templates/concept.md`** (was backlog B1) and a typed "Related pages" section to
    `paper.md`; topic template notes reciprocal linking. Fresh-wiki scaffold now copies concept.md.

## Open backlog (proposed, not yet done)

- **B2 — First real run on the drosophila collection.** Validate the skill end-to-end on the
  thesis wiki's drosophila inventory (Tier-1 papers first) and fold back any friction. In
  particular: confirm cite-key filenames resolve against the inventory's `[Zotero key]` list and
  that typed cross-links land in the Obsidian graph as expected.
- **B3 — Batch/parallel ingest option.** For large collections, consider a Workflow that ingests
  independent papers in parallel (each writes its own paper page; topic-synthesis merge stays
  sequential). Deferred until the one-at-a-time path is proven; parallelism risks shallow synthesis.
  - **First real parallel run (2026-07-04, engram-drift-consolidation, 54 papers).** Lessons:
    - A single `pipeline()`/`parallel()` over all 54 fans out to the concurrency cap
      (`min(16, cores−2)` ≈ 10–14 agents), each a full model context streaming Zotero fulltext —
      **this exhausted Denis's RAM** and he had to hard-reset. Fix: process in explicit **batches
      with a barrier between them** (`for` loop + `parallel(batch)`), so only `batch_size` agents are
      alive at once. Batch size is a **RAM knob** — Denis chose 6; offer 2/3/4/6 and let him pick.
    - Make the run **crash-resumable by construction**: each paper writes its own page + archives its
      own fulltext, and the final topic-page/gap-report synthesis runs *only after all pages exist*.
      On restart, recompute done-vs-remaining by checking `papers/<citekey>.md` on disk (the wiki repo
      is the source of truth) rather than trusting workflow state — the run stopped/lost transcript
      twice and we resumed cleanly each time from the pages that existed.
    - **Zotero collection ≫ lit-review run JSON as the ingest source.** The `/lit-review` handoff is a
      Zotero *collection* (e.g. `LLM-literature-reviews/<topic>`, tag `lit-review/<topic>`); it carries
      item keys, PDF keys, and fulltext. Resolve it first (`zotero_search_collections` →
      `zotero_get_collection_items` → `zotero_get_items_children` for PDF keys). Papers with **no PDF
      child** (fulltext-index-only or linked_file HTML) get a lighter abstract-only page flagged
      `⚠️ fulltext-missing` for later deepening — surface that list to the user.
- **B4 — Scratchpad location for long ingests: use `$HOME`, not `/tmp`.** The harness scratchpad
  lives under `/tmp/claude-.../scratchpad`, which is **wiped on reboot/hard-reset** — during the
  engram-drift run we lost the prepared worklist/args/workflow-script three times to resets (no data
  loss to the wiki itself, but re-derivation cost). For multi-hour/batched ingests, write prep files
  (worklists, generated workflow scripts, args JSON) under a durable `$HOME` path
  (e.g. `~/.claude/llm-wiki-work/<topic>/`) instead, and **clean it up manually at the end**. The
  wiki repo remains the true source of truth for progress; scratch is only for in-flight tooling.

## Rejected

- **Baking conventions into the skill instead of per-wiki AGENTS.md.** Rejected: would force one
  fixed convention on every wiki and override existing wikis' own AGENTS.md. Per-wiki file wins.
- **Assuming bib4llm/mcporter on PATH.** Rejected: neither is on Denis's machine; the Zotero MCP is
  reachable directly and full text via `zotero_get_item_fulltext` covers the default path.
