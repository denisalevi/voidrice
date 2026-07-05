---
name: llm-wiki
description: >-
  Build and maintain an LLM wiki — a persistent, compounding knowledge base of paper pages,
  topic/concept syntheses, contradictions, and open questions, linked into a citation/concept
  graph (viewable in Obsidian). Three operations: INGEST papers from Zotero into the wiki
  (from a collection/tag, an explicit list of keys/DOIs, or the wiki's own reading queue);
  LINT the wiki (health-check for contradictions, stale claims, orphan pages, broken/missing
  cross-links); QUERY the wiki (answer a hard question from its synthesis, optionally filing the
  answer back as a page). Works on ANY wiki or scaffolds a fresh one. Use on /llm-wiki or requests
  like "integrate these papers into my wiki", "build a wiki from this Zotero collection", "lint my
  wiki", "health-check the wiki", "ask the wiki about X". Pairs with /lit-review, which fills a
  Zotero collection this skill then turns into knowledge.
---

# llm-wiki

Build and maintain an **LLM wiki**: a persistent, compounding knowledge base — paper pages,
topic/concept syntheses, contradictions, open questions — linked into a citation/concept graph
that is useful for *writing*, not just for remembering literature.

This skill is **portable**: it works on any wiki and creates a fresh one when asked. It is the
natural next step after `/lit-review` — that skill leaves you with a curated Zotero collection;
this one integrates that collection into knowledge, keeps it healthy, and answers questions from it.

## Which operation? (route first)

This skill has **three operations**. Pick the one the user asked for; if it's ambiguous, ask.
- **Ingest** — add papers to the wiki. Triggers: "integrate…", "add this collection/these papers",
  "build a wiki from…". → go to **Ingest**.
- **Lint** — health-check an existing wiki, no new papers. Triggers: "lint…", "health-check…",
  "find orphans/contradictions/broken links". → go to **Lint**.
- **Query** — answer a question *from* the wiki. Triggers: "ask the wiki…", "what does the wiki
  say about…", "answer X from the wiki". → go to **Query**.

All three share the context below (mental model, AGENTS.md-is-truth, non-negotiable rules). Read
that, then jump to your operation's section.

## Mental model — an LLM wiki (Karpathy's three layers)

Implementation of the **"LLM wiki"** idea
(`https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`): instead of re-synthesizing
knowledge from scratch on every question (RAG), build **a persistent, compounding artifact** that
gets richer with every source. The human sources and asks the right questions; the LLM does the
grunt work — summarizing, cross-referencing, filing, bookkeeping — which is the part humans
abandon. Three layers, kept separate:

- **Raw sources (Zotero).** Every paper, its metadata, PDF, notes, annotations, full text.
  Immutable; do not mirror or bulk-summarize it.
- **The wiki.** The compiled conceptual layer: integrated claims, concepts, evidence,
  contradictions, open questions, synthesis. A paper earns a page **only** if it matters to a
  topic/concept — papers merely in Zotero do NOT get pages.
- **The schema (the wiki's `AGENTS.md`).** The config document defining structure, conventions,
  and workflow for *this* wiki. It is authoritative — see below.

Karpathy's three operations map to this skill's three sections: **Ingest** (add a source),
**Lint** (health-check), **Query** (answer from the wiki, file good answers back).

## The wiki's own AGENTS.md is the source of truth

**Each wiki carries its own conventions in an `AGENTS.md` at its root** — link style, page types,
math notation, ingest workflow, Zotero-link format, raw-input/provenance rules, and git remote/sync.
This skill is generic: it knows *how* to read and apply a wiki's AGENTS.md, and how to *create* one
for a fresh wiki. It does not hardcode any single wiki's paths or remote.

**Before doing anything on an existing wiki: read its `AGENTS.md` and follow it.** If its rules
differ from the defaults below, the wiki's AGENTS.md wins. The defaults are only for (a) fresh wikis
and (b) filling gaps a terse AGENTS.md leaves open.

**Detect a plugin-managed vault before imposing your own layout.** Some wikis are maintained by an
Obsidian LLM-wiki plugin (e.g. `green-dalii/obsidian-llm-wiki`) and have a fixed on-disk contract
you must conform to rather than restructure: a `sources/` + `wiki/` + `schema/` root split; pages
under `wiki/entities/` and `wiki/concepts/`; `[[wikilinks]]` (often `[[path|Display]]`); YAML
frontmatter with `type:`, `sources:` (backlinks to source pages), `aliases:`, and a **`reviewed:
true` guard that must NOT be overwritten**; a "Mentions in Source" section preserving original
quotes; and `wiki/index.md` / `wiki/log.md`. If you see this layout (or `schema/` instead of a root
`AGENTS.md`), match it exactly — wikilinks, frontmatter, entity/concept split, and the `reviewed`
guard — and do not scaffold the flat markdown-link structure alongside it. Prefer the plugin for
bulk auto-extraction; use this skill for the deep per-paper synthesis it doesn't do.

## Non-negotiable rules (all operations)

1. **Zotero is read-only** unless the user explicitly asks otherwise. This skill reads metadata,
   full text, notes, and annotations from Zotero and *writes to the wiki*. It does not add, edit, or
   delete Zotero items, and it never touches any `.bib` file (those are auto-generated from Zotero).
2. **One paper at a time, synthesis over summary.** Never bulk-dump. Each paper page must answer
   *"why does this matter for this wiki's purpose?"* and feed the topic/concept synthesis, not just
   restate the abstract.
3. **Preserve uncertainty.** Label claims as established / plausible / speculative / open. When a
   paper contradicts the current synthesis, update the synthesis page and **name the conflict**
   explicitly — don't smooth it over.
4. **Provenance is append-only.** Archive the exact full text you actually read under the wiki's
   raw-input area and record it in the manifest before synthesizing from it. Never overwrite an
   archived raw file; add dated copies/rows.
5. **Commit AND push after every meaningful edit** if the wiki is a git repo with a remote — never
   leave it committed-but-unpushed. Follow the wiki's AGENTS.md for the exact remote/branch.
6. **Keep `IMPROVEMENTS.md` current whenever you edit this skill.**
   `~/.claude/skills/llm-wiki/IMPROVEMENTS.md` is the living backlog + change log + rejected-ideas
   list. Any change to a file under this skill must update it in the same pass. An undocumented skill
   change is an incomplete change. Read it before proposing "new" ideas.

---

# Operation: INGEST

Move selected papers from Zotero into the wiki, one at a time, with real synthesis.

## Ingest Step 0 — Pick the wiki and the paper source (ask; don't assume)

**A. Which wiki?**
- **Existing wiki** — the user gives a path (e.g. the thesis LLM wiki). Read its `AGENTS.md`,
  `README.md`/`index.md`, and skim `log.md` and the relevant `topics/` page so you integrate *into*
  the existing synthesis rather than beside it.
- **Fresh wiki** — the user wants a new one. See **Creating a fresh wiki** below. Confirm the target
  directory and whether it should be a git repo.

**B. Which papers? — offer all three, ask which** (they can combine):
- **Zotero collection or tag** — the direct `/lit-review` handoff. Pull items via the `zotero` MCP:
  `zotero_get_collections` / `zotero_search_collections` to resolve the collection key, then
  `zotero_get_collection_items`; or `zotero_search_by_tag` for a tag. Default after a lit-review.
- **Explicit list** — the user names citation keys, DOIs, or titles. Resolve each in Zotero
  (`zotero_search_by_citation_key`, `zotero_advanced_search` on DOI, or `zotero_search_items`).
- **Wiki's own reading queue** — an existing inventory/queue page in the wiki (e.g. an
  `agent-only/<topic>-inventory/inventory.md` tiered by relevance). Work through it in tier order,
  highest-relevance first.

Also settle **scope/order**: which topic the papers feed, and — for a large source — whether to do
all of them or a top slice first. Default to relevance order and checking in after the most
load-bearing papers.

## Ingest Step 1 — Orient in the wiki (existing wikis)

Before the first paper, read the map so synthesis lands in the right place:
1. `AGENTS.md` (authoritative), then `README.md`/`index.md` (current map).
2. The **target topic page** in `topics/` if it exists, plus any concept/paper pages it links.
3. Skim `log.md` for what was last done and any open threads.
4. Check for a **personal-notes source** the wiki's AGENTS.md points to (e.g. vimwiki) and any
   existing reading queue for these papers.

If the target topic page doesn't exist yet, create it from `templates/topic.md` as the first
synthesis target — the paper pages hang off it.

## Ingest Step 2 — Per-paper loop (full-text synthesis, one at a time)

For **each** paper, in relevance order. This is the core; do not batch it.

1. **Why does this paper matter?** State, in one line, its role for the wiki's purpose *before*
   reading deeply. If the honest answer is "it doesn't," skip it — no page. (An inventory/lit-review
   relevance note is a starting hypothesis; confirm it against the full text.)
2. **Read existing wiki pages first** — the topic page and any linked concept/paper pages — so you
   extend the synthesis rather than duplicate it.
3. **Check personal notes** (if the wiki's AGENTS.md names a notes source) for prior thinking.
4. **Get the full text and archive it (provenance FIRST).**
   - Preferred: `zotero_get_item_fulltext(item_key=…)` via the MCP. Save the exact returned text
     under the wiki's raw-input fulltext area (default `raw-input/files/zotero-fulltext/`) with a
     dated, descriptive filename, and record the row in the Zotero manifest (item key, PDF key, raw
     path, tool, date, wiki output). **Then read from the archived file.**
   - Also pull `zotero_get_notes` / `zotero_get_annotations` when those are the relevant source.
   - **Fallback** only if MCP full text is unavailable/insufficient (or you need figures): `bib4llm`
     (extracts figures/images too). **Detect it first — `command -v bib4llm` — do NOT assume it
     exists on this machine** (it often won't). If missing and the user wants figure extraction,
     `reference/bib4llm-setup.md` has the install (adapts to the user's env manager: uv / pipx /
     micromamba / venv); only install when the user asks. Save output under the wiki's extra-extracts
     area and record the run + reason in the manifest. If neither MCP full text nor bib4llm is
     available, tell the user rather than improvising ad-hoc PDF extraction.
5. **Extract only wiki-relevant material** — claims, methods, models, equations, caveats — tied to
   the wiki's purpose. Label each claim's confidence (established/plausible/speculative/open).
6. **Write/update the paper page** from `templates/paper.md`, named by the paper's **Zotero citation
   key** (see *Paper-page naming* below). Include the wiki's required Zotero links (one item + one
   PDF link, per its AGENTS.md — get the PDF attachment key via `zotero_get_item_children`). Use the
   wiki's math and link conventions.
7. **Wire the page into the graph — first-class deliverable, not polish.** The value of this wiki is
   the *link structure* (a citation/concept graph), so every page must be a connected node. Add,
   using the wiki's link convention:
   - **paper ↔ topic** — reciprocal (paper links to its topic page; the topic page links back).
   - **paper ↔ paper** — link this paper to others already in the wiki when the relationship is
     **load-bearing**, with a **typed, one-clause reason**: *builds on / extends*, *contradicts / in
     tension with*, *supersedes / superseded by* (preprint↔journal, newer result), *shares
     mechanism/method with*, *provides evidence for*. Make the edge **reciprocal** (mirror on the
     other page). Do **not** link two papers just because they share a topic — only genuine, nameable
     relationships.
   - **paper ↔ concept** — if the paper turns on a reusable concept, link to its `concepts/` page
     (create from the concept template if absent) and link back. Concepts may link to other concepts.
   For markdown-link wikis use relative `../papers/Key.md` / `../concepts/foo.md`; for wikilink wikis
   use `[[Key]]`. A page that is an orphan, or linked in only one direction, is a **lint failure**.
   (Realizes the Karpathy wiki's "cross-referencing / no orphans" rule, specialized to typed edges.)
8. **Update the topic/concept synthesis** — how this paper changes, supports, extends, or challenges
   the current picture. Not "paper X says Y"; rather "the picture is now Z, because…"
9. **Flag contradictions, weak evidence, missing citations, open questions** on the synthesis page.
   A contradiction between two papers is BOTH a typed `contradicts` cross-link (step 7) AND named in
   the topic-page synthesis.
10. **Update `index.md`, append to `log.md`.**
11. **Commit AND push** (if a git repo) — per the wiki's AGENTS.md remote/branch. Commit the raw
    archived full text too. Do not commit PDFs or large binaries unless the user asks.

Then move to the next paper. Check in after the most load-bearing papers rather than silently
grinding a long list.

### Paper-page naming — the Zotero citation key

Name each paper page **exactly its Zotero (Better BibTeX) citation key**: `Felsenberg2018.md`,
`Aso2014.md`, `Aso2014a.md`. This makes **page name == cite key == the thesis `\cite{}` key** — one
identifier across the wiki graph, Zotero, and the LaTeX — so cross-links are guessable and never
drift from the bibliography. Get the key from the Zotero item (`zotero_get_item_metadata` /
`zotero_search_by_citation_key`); do not invent one. Disambiguation (`a`/`b`/`c`) comes from Zotero;
mirror it. If an item genuinely has no cite key, fall back to `AuthorYEAR` (+`a`/`b`) and note it.

**Existing pages** may predate this rule (e.g. `Author-Coauthor-Year.md`). Leave them unless the
user asks to rename — but link to their real filename. New pages always use the cite key.

## Ingest Step 3 — Close out

- Refresh the target topic page's synthesis so it reads as one coherent picture, not a pile of
  per-paper additions.
- Update `README.md`/`index.md` content map and the `log.md` entry for the run.
- **Run a quick Lint** (below) over the pages you touched — orphans/broken links/one-directional
  edges introduced this run — and fix them before finishing.
- Summarize for the user: which papers got pages, what the synthesis now says, the contradictions
  and open questions surfaced, and anything skipped (with why). Final commit + push.

## Creating a fresh wiki

When the user wants a new wiki (or none exists yet):
1. Confirm the target directory and whether it should be a git repo with a remote.
2. Scaffold the structure and copy `templates/AGENTS.template.md` → `<wiki>/AGENTS.md`, filling its
   placeholders (`{{WIKI_PURPOSE}}`, `{{RAW_SOURCES}}`, `{{GIT_REMOTE}}`, notes source, etc.) from
   what the user tells you. This portable AGENTS.md — not this skill — becomes that wiki's standing
   source of truth, so future runs (and other agents) follow it without the skill.
3. Create the standard layout and seed pages:
   - `README.md` (+ `index.md` as a copy or symlink), `log.md` (append-only), `.gitignore`.
   - `topics/`, `concepts/`, `papers/`, `sources/`, `templates/`, `raw-input/`.
   - Copy `templates/paper.md`, `templates/topic.md`, `templates/concept.md` into `<wiki>/templates/`.
   - `raw-input/` with `files/` (`zotero-fulltext/`, `zotero-extra-extracts/`) and `manifests/`
     (`zotero-papers.md`, `non-zotero-files.md`), plus a `raw-input/README.md` explaining the
     append-only provenance rule.
4. If a git repo: `git init`, initial commit, and (if a remote was given) push.
5. Then proceed to Ingest Step 0-B (paper source), now driven by the new AGENTS.md.

---

# Operation: LINT

Health-check an existing wiki. Runs standalone ("lint my wiki") or automatically over touched pages
at the end of an ingest. No Zotero fetching and no new papers — this is about the wiki's internal
integrity. Read the wiki's `AGENTS.md` first (link/naming conventions define what "broken" means).

Sweep for the failure modes a compounding artifact accumulates, and fix the safe ones / flag the rest:
- **Contradictions** — two pages asserting incompatible claims. Reconcile on the synthesis page and
  name the conflict; don't silently pick a winner. Ensure it's also a typed `contradicts` cross-link.
- **Stale claims** — a claim a newer ingested paper has since qualified or overturned.
- **Orphan pages** — paper/concept pages not linked from any topic/concept. Wire them in, or if the
  page doesn't actually matter, question why it exists.
- **One-directional edges** — a link that exists on one page but not its mirror (paper→topic without
  topic→paper, or a `contradicts` named on only one of the two papers). Add the missing mirror.
- **Broken / missing cross-references** — dead internal links (wrong filename — often a paper page
  not named by its cite key), and pages that clearly *should* link but don't.
- **Uncertainty drift** — confidence labels (established/plausible/speculative/open) that no longer
  match the evidence now in the wiki.
- **Naming drift** — paper pages not named by their Zotero cite key (flag; rename only if asked).

Report findings first (grouped by type, most-severe first). Apply the safe fixes (add missing mirror
links, fix dead internal links, wire in orphans). Leave judgment calls (which side of a contradiction
is right, whether to rename legacy pages) for the user. Commit + push and append a lint entry to
`log.md` summarizing what was found and fixed.

For a large wiki, this parallelizes well: independent per-page checks can fan out, with the
cross-page reconciliation (contradictions, mirror edges) done after. Keep it read-mostly.

---

# Operation: QUERY

Answer a hard question **from the wiki's synthesis**, not by re-reading raw papers — that's the whole
point of having built the wiki. Lightweight; no ingest.

1. Read the wiki's `AGENTS.md`, then `index.md` to locate the relevant topic/concept/paper pages.
2. Answer **from those pages** — follow the cross-links to assemble the picture. Prefer the wiki's
   own synthesis and its confidence labels; if the wiki is thin or silent on the question, say so
   plainly rather than inventing an answer (and note it as a gap — a candidate for a future ingest).
3. Cite the pages you drew on with internal links, so the answer is traceable and navigable.
4. **File a valuable answer back as a page** (Karpathy's rule: good query answers become wiki pages).
   If the question is one worth answering again — a synthesis, a comparison, an open-question
   writeup — write it as a new `topics/` or `concepts/` page (or extend an existing one), wire it
   into the graph reciprocally, update `index.md`/`log.md`, and commit + push. Offer this rather than
   always doing it; a one-off lookup doesn't need a page.

Deep, multi-source questions that go *beyond* what the wiki contains are a different job — that's
research (e.g. `/lit-review` to find missing papers, then Ingest). Query answers from what's already
integrated.

---

## Defaults (fresh wikis; and to fill gaps in a terse AGENTS.md)

Mirror the conventions of Denis's thesis LLM wiki; a wiki's own AGENTS.md overrides them.

- **Links:** relative Markdown links with `.md` for internal pages (Obsidian/GitHub-repo friendly),
  reciprocal. `zotero://select/…` item + `zotero://open-pdf/…` PDF link for every paper reference,
  inline `[Open in Zotero](…) · [Open PDF](…)`.
- **Paper filenames:** the Zotero cite key (`Felsenberg2018.md`).
- **Math:** `$…$` inline, `$$…$$` display. Backticks only for code/paths/keys, never inline math.
- **Page types:** `README.md`/`index.md`, `log.md`, `topics/`, `concepts/`, `papers/`, `sources/`,
  `templates/`, `raw-input/`. Paper pages only for papers that matter to a topic/concept.
- **Quality:** synthesis over summary; preserve uncertainty; every paper page answers "why does this
  matter for this wiki?"; name contradictions explicitly.
- **Provenance:** archive exact MCP full text before synthesizing; manifests are append-only.
- **Git:** commit and push after every meaningful edit; commit raw text inputs, not PDFs.

## Reference
- The LLM wiki concept: `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`
  (Ingest/Lint/Query; raw-sources / wiki / schema). Obsidian implementation for comparison:
  `https://community.obsidian.md/plugins/karpathywiki` and `github.com/green-dalii/obsidian-llm-wiki`.
- `templates/AGENTS.template.md` — portable per-wiki conventions file (the "schema" layer) for fresh wikis.
- `templates/paper.md`, `templates/topic.md`, `templates/concept.md` — page templates (paper pages
  carry a typed "Related pages" section; concept pages link back to papers).
- `reference/bib4llm-setup.md` — detect/install/use bib4llm; install adapts to the env manager
  (uv / pipx / micromamba / venv).
- `IMPROVEMENTS.md` — backlog + change log for this skill.
