---
name: thesis-review
description: Review PhD thesis writing — scientific reasoning, argumentation, writing style, and citation/literature fit — by getting independent feedback from two strong models (Opus 4.8 and GPT-5.5 via Codex rescue), then integrating the best of both. Use when the user invokes /thesis-review, or asks to review/critique/merge/analyse a passage, argument, or section of their thesis writing.
---

# thesis-review

Get two strong models to independently review the user's PhD-writing task, then **integrate the best of both** into one honest, critical recommendation. The user is Denis, a domain expert writing his PhD thesis in the overleaf repo. The goal is always: **make this document better so it passes PhD thesis review.** Be critical. Do not sugarcoat. If something is genuinely good, say so plainly.

The two reviewers:
- **Reviewer A — Opus** (this skill, via the `Agent` tool, `subagent_type: general-purpose`, `model: opus`). High effort.
- **Reviewer B — GPT-5.5** (via the `codex:rescue` skill / `/codex:rescue` subagent, `--model gpt-5.5 --effort high`, run in the background).

Model defaults are **Opus 4.8** and **gpt-5.5 / high effort**. If the user names different models or efforts in their request, use those instead.

---

## Step 0 — Classify the request

From the user's task text, determine two things.

**A. Mode** (what the reviewers should actually do):
- **Specific task** — e.g. "merge these two versions into one good one", "analyse these two intros", "which argument is stronger". The job is just: get both models' take on *that specific question*, compare, integrate. No paper reading required unless the task itself is about citations.
- **Open / writing review** — the user gives you a passage/section and asks for a general writing review, or asks about scientific writing / literature-based checking, or is unspecific ("review this"). Here you **also do literature & citation checking** (Step 2).

When in doubt between the two, treat it as **Open / writing review** (the more thorough path) — but don't read papers if the text under review has no citations.

**B. Granularity:**
- **Default (synthesis mode)** — both reviewers review the *whole* task; you integrate. This is almost always what to do.
- **Per-paper workflow mode** — ONLY when the user explicitly asks for a workflow / parallelization / "one paper per agent". Then fan out: each agent takes one citation/paper, reads it, and checks (1) does the citation fit where used, (2) are the paper's actual claims represented correctly, (3) is this paper relevant somewhere else it isn't cited. See Step 4. Do **not** do this by default — it is slower and more expensive.

If the user asks for **related-work expansion or searching for papers not in the library**, STOP and run the questionnaire in Step 3 first.

Don't over-engineer. Denis has limited time. Pick the lightest path that does the job well.

---

## Step 1 — Gather the material

Read the passage(s) / file(s) / versions the task refers to from the overleaf repo so you can brief both reviewers with the same concrete material. If the task references "these two versions" or selected text, locate them precisely. Quote the exact text in the briefs so both reviewers review the *same* thing.

---

## Step 2 — Literature & citation checking (Open / writing-review mode only)

Only when Step 0 put you in Open / writing-review mode **and** the text under review contains citations. For each citation in the passage, get the paper's full text so a reviewer can verify the citation actually supports the claim it's attached to. Default scope: **only papers actually cited in the passage.** (Related-work / external search → Step 3.)

Try these in order until one yields the full text:

1. **Zotero MCP fulltext.** Resolve the BibTeX citekey to a Zotero item, then read its fulltext:
   - `mcp__zotero__zotero_search_by_citation_key` with the citekey (e.g. `Remme2021`) → gives the item key.
   - `mcp__zotero__zotero_get_item_fulltext` with that item key → full text.
2. **Read the PDF directly.** If fulltext fails or is empty, get the item metadata / attachment path via `mcp__zotero__zotero_get_item_metadata` (or item children), then `Read` the PDF file at the attachment path.
3. **bib4llm fallback.** If both fail, convert the PDF/bib entry to LLM-readable markdown with bib4llm (env: `~/.conda/envs/bib4llm/bin/bib4llm`):
   ```bash
   ~/.conda/envs/bib4llm/bin/bib4llm convert <path-to-pdf-or-bibfile>
   ```
   - `convert` accepts a PDF file, a `.bib` file, or a directory. It writes LLM-readable markdown (plus extracted figures) into a generated data directory next to the input. Add `--force` to reprocess, `-p N` to set parallelism, `--dry-run` to preview. Then `Read` the generated markdown.

The subagents themselves should use Zotero MCP first (they have access). Only fall back to PDF read / bib4llm if Zotero fulltext fails. Reading full papers is expensive — only read the papers that are actually cited in the passage under review, and don't re-read the same paper twice.

When briefing reviewers, give them the citekeys, the exact claim each is attached to, and tell them to verify fit (does the source actually say this? is it the right strength? is it the best source? is anything mis-attributed or overclaimed?).

---

## Step 3 — Related-work / external-paper search (only if requested) — STOP AND ASK

If the user asks to also check *related* papers (beyond those cited) or to search for papers **not in the Zotero library**, do not improvise a method. Use `AskUserQuestion` to ask how they want to do it.

> **TODO / not yet designed:** the external-search backends are undecided. Candidate approaches to offer and refine with Denis when this comes up: **antigravity** (reportedly fast/good), **Semantic Scholar** API, **Connected Papers**, plain web search. This needs to be figured out *with Denis* — present the options, capture his choice, and (if it becomes routine) fold the chosen method into this skill later. For now: ask, don't guess.

For checking *related papers already in the Zotero library*, you may use `mcp__zotero__zotero_semantic_search` / `zotero_search_items` to surface neighbors — but only when the user asked for related-work checking, not by default.

---

## Step 4 — Dispatch the two reviewers

Write **one shared brief** containing: the exact passage(s)/task, what to evaluate (scientific reasoning, argumentation, writing style, and — if applicable — citation/literature fit), the relevant paper material or instructions to fetch it via Zotero, and the standing instruction: *be critical, this must pass PhD thesis review; flag weak reasoning, unsupported claims, mis-fitted citations, sloppy or unclear writing; if it's good, say so.*

### Default (synthesis mode)

Dispatch both reviewers on the **same** full brief, in parallel:

- **Reviewer A (Opus):** `Agent` tool, `subagent_type: general-purpose`, `model: opus`, with the shared brief. Instruct it to use Zotero MCP for any paper fulltext it needs (fallbacks per Step 2).
- **Reviewer B (GPT-5.5):** invoke the `codex:rescue` skill in the **background** with `--model gpt-5.5 --effort high`, passing the shared brief as the task. (Equivalent to `/codex:rescue --background --model gpt-5.5 --effort high <brief>`.) Override model/effort only if the user specified different ones.

Run both concurrently. Wait for both to finish.

### Per-paper workflow mode (only when explicitly requested)

Fan out one citation/paper per agent to parallelize. For each paper, an agent (Opus via `Agent`, and/or GPT via `codex:rescue`) reads that one paper and reports: (1) does the citation fit where used, (2) are all the paper's relevant claims represented faithfully, (3) is the paper important somewhere else in the text where it's not currently cited. Codex/GPT can spawn its own sub-work via the rescue subagent; if GPT cannot reliably fan out, run the GPT side sequentially over papers and keep the Opus side parallel. Then synthesize across all papers as in the default mode.

---

## Step 5 — Integrate and present

Synthesize both reviews into **one** result for Denis:

1. **Integrated recommendation** — the best of both models combined. If the task was "merge/produce one good version", give that version. If it was "critique", give the consolidated critique with concrete, actionable fixes (specific wording, specific reasoning gaps, specific citation problems).
2. **Where the models diverged** — flag points where Opus and GPT-5.5 disagreed or emphasized different things, so Denis can adjudicate. Don't bury real disagreement inside the synthesis.
3. **Honest verdict** — is the passage thesis-ready? What are the must-fixes vs nice-to-haves? No sugarcoating.

Per Denis's standing preference, for thesis *prose* changes, propose options / discuss before directly editing the overleaf files — don't silently rewrite his text.

---

## Notes

- Models: default Opus 4.8 (Reviewer A) + gpt-5.5 high effort (Reviewer B). User can override either.
- Don't over-engineer; pick the lightest sufficient path. Per-paper fan-out and external search are opt-in only.
- bib4llm env: `~/.conda/envs/bib4llm/bin/bib4llm` (subcommands: `convert`, `watch`, `clean`).
- If `codex:rescue` reports Codex is missing/unauthenticated, tell Denis to run `/codex:setup` and proceed with the Opus review alone, noting the GPT side was skipped.
