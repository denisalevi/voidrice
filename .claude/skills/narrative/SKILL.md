---
name: narrative
description: Orchestrator for Denis's narrative-first thesis-writing workflow. Invoke this when Denis wants to build or revise the argument/narrative of a chapter, section, or paragraph before writing prose — or is anywhere in that loop and wants to be guided to the right next step. Routes to the atomic skills narrative-discuss, narrative-scaffold, narrative-review-content, narrative-review-style. This is the ONLY skill Denis invokes by name; everything else is reached through here.
---

# narrative — meta-orchestrator

Denis writes his PhD thesis narrative-first: **build the argument together, freeze it as a
LaTeX scaffold, he writes the prose himself, then we review.** Your job here is to figure
out where he is in that loop and hand off to exactly one atomic skill — or to explain the
loop if he's just starting.

This skill does NOT do the work itself. It routes. Keep it light.

## The loop (not strictly linear — expect 1,2,1,2 or 1,2,3,4 cycles)

| Step | Skill | The one thing |
|------|-------|---------------|
| 1 | `narrative-discuss` | Discuss & agree the narrative. Meta level. **No LaTeX written.** Extract an existing narrative and/or build/extend a new one (content, literature, links to other chapters). |
| 2 | `narrative-scaffold` | Write the agreed narrative into the `.tex` as a dual block: a commented `[Claude]` reference + a compilable `\scaffold{}` he writes on. Works for fresh text or as an edit block above an existing paragraph. |
| 3 | *(none — Denis writes prose himself)* | He replaces `\scaffold{}` with real prose. You are not involved. |
| 4a | `narrative-review-content` | Content-conformance: does his prose say what the frozen narrative said it should? Two fresh-context models. |
| 4b | `narrative-review-style` | Style / copy-edit of the drafted prose against `writing-style/STYLE.md`. Two fresh-context models. |

Step 3 has no skill by design. `thesis-review` (separate, global) is the heavier standalone
full review for later — not part of this working loop; mention it only if he asks for a full pass.

## How to route

1. **Read the situation.** Look at what Denis just said and, if useful, the target `.tex`
   region. Determine which step he's at:
   - Nothing agreed yet, or he wants to talk through the argument → **step 1** (`narrative-discuss`).
   - Narrative agreed (this session or a saved narrative note exists) but not yet in the `.tex`,
     or he says "write it down / scaffold it" → **step 2** (`narrative-scaffold`).
   - He says he's written the draft and wants it checked → ask **content or style first**;
     default to **content** (4a) before style (4b). His stated instinct is content-first.
   - Ambiguous → ask him with `AskUserQuestion` (one short question, options = the steps).

2. **Hand off** by invoking the chosen atomic skill via the Skill tool. Pass along the target
   (chapter/section/paragraph, file path if known) and any narrative already agreed.

3. **After** the atomic skill returns, tell Denis concisely what happened and offer the natural
   next step in the loop (e.g. after scaffold → "go write; ping me for review when done").

## Cross-session memory & logbook

Two sidecar files per unit (in `.narrative/`, gitignored), maintained by `narrative-discuss`:
- `<slug>.md` — **CURRENT** live spec. Small. Load this for routine routing / scaffolding.
- `<slug>.log.md` — **append-only logbook** of how we argued (each revision archives the prior
  version + the why + rejected alternatives). Only load this for history or reverts — keep routine
  loads cheap.

When routing, check for a relevant `<slug>.md` and load it so a `1,2,1,2` loop doesn't lose the
narrative. If Denis asks *"why did we decide X"*, *"how did we argue this"*, or *"go back to the
earlier version"*, that's when you open `<slug>.log.md`. To revert, route to `narrative-discuss`,
which restores an archived CURRENT from the logbook (recording the revert as a new logbook entry so
nothing is lost).

## Standing constraints (apply to every step)

- Denis's standing preference: **discuss / propose options before editing thesis prose.** The
  scaffold step writes *scaffolding*, not prose — that's allowed. Never silently rewrite his prose.
- Prose work must respect `writing-style/STYLE.md` and the `writing-style/` learning system
  (capture reusable style signals to `writing-style/INBOX.md`).
- Keep Denis's time cheap. Pick the lightest path. Don't over-orchestrate.
