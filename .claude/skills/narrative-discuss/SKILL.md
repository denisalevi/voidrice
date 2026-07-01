---
name: narrative-discuss
description: Step 1 of Denis's narrative-first thesis workflow. Discuss and agree the narrative of a chapter/section/paragraph at the meta level — extract the current argument from existing text, and/or build/extend a new one with content, literature, and links to other chapters. NO LaTeX is written here. Reached via the `narrative` orchestrator, or invoke directly when Denis wants to talk through the argument before drafting.
---

# narrative-discuss — build the narrative (no writing)

This is a **thinking** step, not a writing step. The output is an *agreed narrative* held in
the conversation and saved to a small sidecar note. **Do not write any LaTeX or prose into the
thesis files here.** That is step 2 (`narrative-scaffold`).

## What you do

1. **Scope it.** Confirm the unit under discussion: whole chapter, one section, or one paragraph
   (and whether it's fresh text or a change to existing text). If unclear, ask.

2. **Extract the current narrative (if text exists).** Read the target region. State back, in
   plain meta-level bullets, what each paragraph currently *does* argumentatively (its topic
   sentence / job), and how paragraphs connect. This is a map, not a critique yet.

3. **Build / extend the narrative together.** Discuss:
   - the claim each paragraph should make (candidate topic sentences),
   - what should go in each (evidence, mechanisms, caveats — your suggestions welcome),
   - **connections**: how each paragraph links to the previous and next one (and a candidate
     bridging sentence where useful),
   - **cross-chapter links**: how this ties to other thesis chapters (`\ref{ch:…}`), and where
     the PPT / consolidation throughline runs,
   - **literature**: which papers support each move; flag gaps where a citation is needed.
     Use Zotero MCP to check what a cited paper actually says if a claim leans on it
     (`mcp__zotero__zotero_search_by_citation_key` → `zotero_get_item_fulltext`). Don't read
     papers speculatively — only when a specific narrative claim needs grounding.

4. **Be a critical collaborator.** Push back on weak or missing logic. Denis is the domain
   expert; your value is structure, gaps, and connections — not fluent prose.

5. **Converge and record.** When Denis signals the narrative (or a specific change to it) is
   agreed, record it in the sidecar. The sidecar is **memory + logbook**, split across **two files**
   so routine loads stay small and the (growing) history is only opened when needed:

   - **CURRENT:** `<repo>/.narrative/<slug>.md` — the live agreed spec, and the ONLY file
     `narrative-scaffold` and routine routing need to load. Small.
   - **LOGBOOK:** `<repo>/.narrative/<slug>.log.md` — append-only history of how we argued. Loaded
     only for history questions or reverts.
   - Create `.narrative/` if absent (gitignored; add `.narrative/` to `.gitignore` if missing).
   - `<slug>` = chapter/section/paragraph identifier, kebab-case (e.g. `drosophila-intro`,
     `drosophila-shortcut-motif-p2`).

   **CURRENT file** — per paragraph: the **topic sentence**, **detail bullets**,
   **connect-prev / connect-next** (with any candidate bridge sentence), **citekeys / cross-refs**.
   Terse — it's the spec for step 2, not prose.

   ```markdown
   # Narrative: <slug>   (CURRENT)
   Target: <file path / section / paragraph range>
   Updated: <YYYY-MM-DD>   ·   Log: <slug>.log.md   ·   Generated with Claude (planning notes)

   ### <paragraph id, e.g. p1>
   - **Topic:** <topic sentence>
   - <detail bullet>
   - connect-prev: <link / candidate bridge>
   - connect-next: <link forward>
   - refs: <citekeys / \ref{ch:...}>
   ```

   **LOGBOOK file** — append-only, **newest entry first**. One dated entry per discuss-session.

   ```markdown
   # Narrative logbook: <slug>
   Append-only. Newest first. CURRENT spec lives in <slug>.md.

   ### <YYYY-MM-DD> — <one-line summary>
   - **Changed:** <what moved vs previous, or "initial narrative">
   - **Why:** <the reasoning that convinced us>
   - **Considered & rejected:** <alternative> — <reason>
   - **Superseded CURRENT (archived):**
     <verbatim copy of the CURRENT spec this revision replaced, if any>
   ```

   **How to update (never destroy history):**
   - First narrative: create both files — fill CURRENT, add the first LOGBOOK entry ("initial").
   - Revision: **before overwriting CURRENT, copy its outgoing content verbatim into a new LOGBOOK
     entry** (archived under "Superseded CURRENT"), then overwrite `<slug>.md` with the new spec and
     bump its `Updated:` date. Prepend the new LOGBOOK entry to the top of `<slug>.log.md` — read
     that file first so you preserve every prior entry; you only ever add to the top, never rewrite.
   - Convert any relative dates to absolute.

## Reverting to an earlier argument

If Denis wants to go back to a previous stance ("revert to how we had it before", "use the earlier
version"), read `<slug>.log.md`, find the archived CURRENT block he means, and restore it: archive
the present CURRENT into a fresh LOGBOOK entry, promote the chosen archived version back into
`<slug>.md`, and record the revert as a new LOGBOOK entry with the reason. Never delete history.

## Boundaries

- No `.tex` edits. No prose. This step ends at an agreed narrative + the sidecar note.
- Respect Denis's standing preference: propose options, discuss — never assume.
- When the narrative is agreed, tell him the next step is `narrative-scaffold` (step 2) to write
  it into the `.tex`, and offer to run it (via the `narrative` orchestrator or directly).
