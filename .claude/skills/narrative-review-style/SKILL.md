---
name: narrative-review-style
description: Step 4b of Denis's narrative-first thesis workflow. Style and copy-edit review of the prose Denis drafted, against the thesis `writing-style/STYLE.md` rules and voice. Uses two fresh-context models (Opus 4.8 + GPT-5.5 via Codex), integrates, and captures reusable style signals to writing-style/INBOX.md. Style only, assumes content is already agreed (via narrative-review-content). Reached via the `narrative` orchestrator, or invoke directly for a style pass on drafted prose.
---

# narrative-review-style — style & copy-edit against Denis's voice

A **style** pass on prose whose content is assumed already agreed (ideally after
`narrative-review-content`, 4a). Judge writing quality, clarity, flow, and fit to Denis's
established voice — **not** whether the content is right (that's 4a). Do not re-open the argument.

## Step 0 — Load the canon

Read `writing-style/STYLE.md` (the curated numbered rules). Scan `writing-style/examples/INDEX.md`
and open only the example files relevant to the passage. Follow `writing-style/REVIEW.md` if present
for how Denis wants prose reviewed. These are the rubric.

## Step 1 — Gather the prose

Read the target `.tex` region — the finished paragraphs Denis wrote. Ignore the commented
`% >>> NARRATIVE` blocks and any `\scaffold{}` (content, not style). Quote the exact prose so both
reviewers judge the same text.

## Step 2 — One shared brief

Give both reviewers the prose verbatim and the STYLE rules (cite rule IDs like `S3`), asking them to:
- flag violations of specific `STYLE.md` rules (name the rule ID),
- flag unclear, clunky, wordy, or hedge-heavy sentences; passive where active is better; buried
  topic sentences; awkward transitions,
- check flow and connective tissue between paragraphs,
- suggest concrete rewrites (specific wording), not vague advice,
- respect Denis's voice — tighten, don't homogenize.

Standing instruction: *be critical; this must read as strong PhD-thesis prose. Comment on STYLE and
clarity ONLY, not on whether claims are correct. If a passage is already good, say so.*

## Step 3 — Dispatch two fresh-context reviewers (parallel)

- **Reviewer A — Opus:** `Agent`, `subagent_type: general-purpose`, `model: opus`, high effort.
- **Reviewer B — GPT-5.5:** `codex:rescue` in the **background**, `--model gpt-5.5 --effort high`.

Run both concurrently; wait for both. (Codex missing → tell Denis `/codex:setup`, proceed with
Opus alone, note GPT skipped.)

## Step 4 — Integrate and present

1. **Consolidated edits** — concrete, per-sentence, keyed to STYLE rule IDs where they apply.
2. **Where the models diverged** — surface real disagreement.
3. **Verdict** — is the prose thesis-ready stylistically? Must-fixes vs nice-to-haves.

Per Denis's standing preference, **propose the edits / discuss — do not silently rewrite his prose.**
If he then asks you to apply them, do the copy-edit directly.

## Step 5 — Feed the style learning system

Per `AGENTS.md`: if the review surfaces a *general, reusable* style preference (from Denis's
correction or your confident judgement) not already covered by an `S`-rule, append a short note to
`writing-style/INBOX.md` in that file's format. Bias toward capturing. **Never edit `STYLE.md`
directly** — that's a separate, gated consolidation.
