---
name: narrative-review-content
description: Step 4a of Denis's narrative-first thesis workflow. Content-conformance review — does the prose Denis just wrote actually say what the frozen narrative said it should? Uses the `% >>> NARRATIVE [Claude]` block as the rubric and gets two fresh-context models (Opus 4.8 + GPT-5.5 via Codex) to check conformance, then integrates. Content only, NOT style. Reached via the `narrative` orchestrator, or invoke directly after Denis has drafted prose against a scaffold.
---

# narrative-review-content — did the prose match the agreed narrative?

This is a **conformance** check, not a general writing review. The spec is Denis's own frozen
narrative. The question is singular: **does his drafted prose say what we agreed it would say?**
Style, wording, and copy-edit are explicitly out of scope here — that's `narrative-review-style` (4b).

## Step 1 — Gather spec + prose

Read the target `.tex` region. For each paragraph, extract the pair:
- **Spec** = the commented `% >>> NARRATIVE [Claude] ... <<< NARRATIVE` block (topic, detail
  bullets, connect-prev/next, refs). This is the rubric.
- **Prose** = the finished paragraph Denis wrote where the `\scaffold{}` used to be.

If a paragraph still has a `\scaffold{}` (not yet written), note it as "not drafted" and skip its
conformance check. If a `% >>> NARRATIVE` block is missing for written prose, flag that we can't
conformance-check it (no frozen spec).

If the spec references citations and a conformance question depends on what a paper says, fetch
fulltext via Zotero MCP (`zotero_search_by_citation_key` → `zotero_get_item_fulltext`); only when
needed.

## Step 2 — Build one shared brief

Give both reviewers, per paragraph: the **spec block verbatim** and the **prose verbatim**, and
this rubric:
1. **Coverage** — does the prose make every claim / move the spec lists? What's missing?
2. **Fidelity** — does it say what the spec meant, or did it drift / overclaim / soften?
3. **Additions** — did new claims appear that aren't in the spec? Are they justified, or scope creep?
4. **Connections** — are the agreed connect-prev / connect-next links actually present in the prose?
5. **Citations** — are the refs the spec called for used, and used where they belong?

Standing instruction: *be critical; this must pass PhD thesis review. Judge ONLY content
conformance against the spec — do not comment on style, phrasing, or copy-edit. If the prose
faithfully realizes the spec, say so plainly. Where it deviates, say exactly which paragraph,
which spec point, and what's wrong.*

## Step 3 — Dispatch two fresh-context reviewers (parallel)

- **Reviewer A — Opus:** `Agent` tool, `subagent_type: general-purpose`, `model: opus`, high
  effort, with the shared brief. Tell it to use Zotero MCP for any fulltext it needs.
- **Reviewer B — GPT-5.5:** invoke `codex:rescue` in the **background** with
  `--model gpt-5.5 --effort high`, passing the same brief.

Run both concurrently; wait for both. (If `codex:rescue` reports Codex missing/unauthenticated,
tell Denis to run `/codex:setup` and proceed with Opus alone, noting GPT was skipped.)

## Step 4 — Integrate and present

One result for Denis:
1. **Per-paragraph conformance verdict** — matches spec / deviates (with the specific gap).
2. **Consolidated must-fixes** — concrete content gaps to close, keyed to paragraph + spec point.
3. **Where the two models diverged** — don't bury real disagreement.
4. **Verdict** — is the content faithful to the agreed narrative? No sugarcoating.

Per Denis's standing preference, **propose fixes / discuss — do not silently rewrite his prose.**
When content is agreed, the natural next step is `narrative-review-style` (4b), then his copy-edit.
