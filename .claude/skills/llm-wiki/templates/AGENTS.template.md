# {{WIKI_NAME}} — Agent Instructions

This is an **LLM wiki** (Karpathy's idea:
`https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`) — a persistent, compounding
knowledge artifact — and this file is its **schema layer**: the standing source of truth for its
conventions and workflow. Any agent (with or without the `llm-wiki` skill) reads and follows
it before editing the wiki. This wiki is the compiled conceptual layer for {{WIKI_PURPOSE}}.

## Purpose

Do not mirror Zotero and do not bulk-summarize the entire library. Zotero is the raw
source/search database. This wiki contains **integrated knowledge**: claims, concepts, paper
evidence, contradictions, open questions, and topic-level synthesis. A paper earns a page here
only when it matters to a topic or concept — not because it is in Zotero. Three layers, kept
separate: **raw sources (Zotero)** · **the wiki** (this repo) · **the schema** (this file).

The wiki grows through three operations: **Ingest** (add a source — the workflow below), **Query**
(answer a hard question from the wiki; file valuable answers back as new pages), and **Lint** (see
the health-check section).

## Raw sources

Primary inputs (read-only unless the owner explicitly asks otherwise):
- Zotero MCP server `zotero` — preferred source for Zotero metadata, notes, annotations, and
  full text. {{RAW_SOURCES}}
- Personal notes (if any): {{NOTES_SOURCE}}

## Link convention

Use relative Markdown links with `.md` for internal pages (best for Obsidian / normal GitHub
repo rendering / local navigation):

```md
[Some topic](topics/some-topic.md)
[Some paper](papers/Author-Year.md)
```

- Prefer relative filesystem paths to the real file; include `.md`. Obsidian resolves these to
  notes and draws graph-view edges for them.
- **The link structure is the payload — build a citation/concept graph, not just a hub.** Link
  every new page reciprocally, and not only to its topic:
  - **paper ↔ topic** (both ways) — never leave a paper page an orphan.
  - **paper ↔ paper** — only for **load-bearing** relationships, each with a typed one-clause
    reason: *builds on / extends*, *contradicts / in tension with*, *supersedes / superseded by*
    (preprint↔journal, newer result), *shares mechanism/method with*, *provides evidence for*.
    Mirror the link on both pages. Do not link two papers just because they share a topic.
  - **paper ↔ concept** and **concept ↔ concept** — both ways.
  A page that is an orphan or linked in only one direction is a lint failure.
- `index.md` mirrors `README.md` (copy or symlink); do not duplicate content.
- External URLs, Zotero links (`zotero://…`), anchors, and image links are fine as usual, but note
  they are NOT graph nodes — papers connect to each other through the topic page, not their Zotero URIs.
- Images live under `images/` near the wiki root.

## Math notation

- Inline math: `$...$` (not backticks). Display math: `$$...$$`.
- Backticks only for code, commands, file paths, citation keys, and literal identifiers.
- Do not use `\[ ... \]` display delimiters — they don't render reliably in GitHub/Slack previews.

## Page types

- `README.md` — entry point and current map. `index.md` — mirror of README.
- `log.md` — append-only chronological log.
- `topics/` — topic syntheses. `concepts/` — reusable concepts across topics.
- `papers/` — one page per paper, only when the paper matters to a topic/concept. **Name each
  page exactly the paper's Zotero citation key** (`Felsenberg2018.md`, `Aso2014a.md`) so page name
  == cite key == LaTeX `\cite{}` key and cross-links stay guessable.
- `sources/` — curated source lists exported/discovered from Zotero.
- `templates/` — page templates. `raw-input/` — append-only provenance layer.

## Ingest workflow (one paper/source at a time)

1. Identify why the source matters before reading deeply. If it doesn't, no page.
2. Read existing relevant wiki pages first (`index.md`, topic page, linked concepts/papers).
3. Check personal notes for the paper/topic.
4. Get the full text via `zotero_get_item_fulltext`; archive the exact text under
   `raw-input/files/zotero-fulltext/` and record it in `raw-input/manifests/zotero-papers.md`
   BEFORE synthesizing; then read from the archived file. Fallback (MCP full text missing, or you
   need figures): `bib4llm` if present (`command -v bib4llm`) — save under
   `raw-input/files/zotero-extra-extracts/` and note the reason in the manifest.
5. Extract only relevant claims, methods, models, equations, caveats. Label confidence.
6. Create/update the paper page.
7. Update affected topic/concept pages with **synthesis, not summary**.
8. Flag contradictions, weak evidence, missing citations, open questions.
9. Update `index.md`; append to `log.md`. Commit and push.

## Lint (periodic health-check)

After a big ingest, or on request, sweep the wiki for: contradictions between pages (reconcile and
name the conflict), stale claims a newer source has overturned, orphan paper pages (not linked
from any topic/concept), missing/broken cross-references, and confidence labels that no longer
match the evidence. Fix the safe ones, flag the rest, and log it.

## Quality rules

- Synthesis over summaries. Preserve uncertainty: established / plausible / speculative / open.
- Every paper page answers: "Why does this matter for {{WIKI_PURPOSE}}?"
- Do not create pages for irrelevant papers just because they are in Zotero.
- If a paper contradicts the current synthesis, update the synthesis page and name the conflict.
- Keep pages useful for writing, not just for remembering literature.

## Zotero links

Every paper reference must be directly openable in Zotero — one item link and one PDF link:

```md
[Open in Zotero](zotero://select/library/items/ITEMKEY) · [Open PDF](zotero://open-pdf/library/items/PDFKEY)
```

- Prefer the compact inline form (item · PDF) at the end of each entry.
- Get the PDF attachment key from `zotero_get_item_children`; use the first `application/pdf`
  attachment. If none, write `· (no PDF)`.

## Raw input provenance (append-only)

- Zotero papers: do not copy PDFs by default. Archive the exact `zotero_get_item_fulltext`
  output under `raw-input/files/zotero-fulltext/`, commit it, then read from it. Record every
  used item in `raw-input/manifests/zotero-papers.md` (item key, PDF key, raw path, tool, date,
  wiki output).
- Auxiliary extracts (e.g. `bib4llm`): save under `raw-input/files/zotero-extra-extracts/` and
  record in the Zotero manifest with the reason for the fallback.
- Non-Zotero sources: copy into `raw-input/files/` when licensing allows; record in
  `raw-input/manifests/non-zotero-files.md`.
- Never overwrite archived files; add new dated copies or manifest rows.

## Git remote and sync

{{GIT_REMOTE}}

**Commit AND push after every meaningful edit** — never leave the wiki committed-but-unpushed:

```bash
git add -A
git commit -m "Update wiki"
git push
```

Commit raw text inputs under `raw-input/files/` when used for synthesis. Do not commit original
PDFs or large binaries unless the owner explicitly asks.
