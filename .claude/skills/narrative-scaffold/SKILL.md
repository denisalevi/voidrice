---
name: narrative-scaffold
description: Step 2 of Denis's narrative-first thesis workflow. Write an agreed narrative into a thesis .tex file as a dual block — a commented-out `[Claude]` reference copy (for later comparison against his prose) plus a compilable `\scaffold{}` scaffold he writes on. Handles fresh text and edit-blocks placed above an existing paragraph. Reached via the `narrative` orchestrator, or invoke directly once a narrative is agreed.
---

# narrative-scaffold — write the narrative into the .tex

Turn an **agreed** narrative (from `narrative-discuss` / the conversation / a `.narrative/<slug>.md`
note) into LaTeX Denis can write on. You write **scaffolding**, never prose. Do not invent new
narrative here — if the narrative isn't settled, stop and go back to `narrative-discuss`.

## The dual block

For each paragraph, emit TWO things in the `.tex`:

**(A) A commented-out reference copy** — plain text for Denis to read and later diff against his
prose. Not LaTeX-rendered. Machine-findable delimiters so a later skill can extract it:

```
% >>> NARRATIVE [Claude] id:<slug>-pN
% Topic: <the agreed topic sentence, plain prose>
% - <detail bullet>
% - <detail bullet>
% - connect-prev: <how it links back; candidate bridge sentence if any>
% - connect-next: <how it links forward>
% - refs: <citekeys / \ref{ch:...}>
% <<< NARRATIVE
```

**(B) A compilable scaffold** Denis writes on, using the `\scaffold` macro (defined in
`Preamble/commands.tex`). One `\sbullet{...}` per line:

```latex
\scaffold{<Topic sentence, as a bold run-in he can keep or rewrite>}{
  \sbullet{<detail bullet>}
  \sbullet{<detail bullet>}
  \sbullet{connect-prev: <link / candidate bridge sentence>}
  \sbullet{connect-next: <link forward>}
}
```

Denis replaces each `\scaffold{...}` with real prose as he drafts, leaving the `% >>> NARRATIVE`
block untouched above it for later comparison.

### Macro facts (do not re-derive)
- `\scaffold{topic}{body of \sbullet lines}` and `\sbullet{...}` are the drafting macros. In the
  thesis repo they live in `Preamble/commands.tex`. **Do not check for them each time** — assume
  present and just write scaffolds.
- Draft rendering is gated on `\scaffolddraft` (set by `\scaffolddrafttrue`). When the flag is
  off/commented, any leftover `\scaffold` raises a **hard compile error** — so scaffolding cannot
  silently ship. You do not need to touch the flag; it's on during drafting.
- **One `\sbullet{}` per line** — Denis requires this for editability.
- Escape LaTeX specials in scaffold/`\sbullet` text (`%`, `&`, `_`, `#`, `~`, `^`). In quotes,
  use `` ``…'' ``.

### If the macro isn't defined (undefined \scaffold in the compile log)
The canonical macro source ships **with this skill** at `scaffold-macro.tex` (in the skill's own
directory). Only when a compile fails with `Undefined control sequence ... \scaffold` (macro not
installed in this repo): append the contents of that `scaffold-macro.tex` to the repo's preamble —
in the thesis repo, `Preamble/commands.tex`; in an unknown repo, the main preamble file, after
`\usepackage{xcolor}`. Then recompile. Don't re-add it if `\scaffold` already compiles.

## Two modes

**Fresh text** — you're scaffolding a new section/paragraph run. Place each dual block where the
paragraph will go, in narrative order.

**Edit block (adding to / changing existing text)** — place the dual block **ABOVE** the existing
paragraph it concerns, and mark it clearly as an edit:

```
% >>> NARRATIVE [Claude] id:<slug>-pN  KIND:edit
% EDIT: <what we're changing/adding and why — one line>
% Topic: ...
% - ...
% <<< NARRATIVE
\scaffold{EDIT — <short label>}{
  \sbullet{<what to change/add>}
  ...
}
```
Leave the existing paragraph below intact; Denis merges the change in himself.

## Procedure

1. Confirm the target file + insertion point(s). Read that region so you match surrounding
   indentation and section structure. Load `.narrative/<slug>.md` if it exists.
2. Insert the dual block(s) with the Edit/Write tools. Match the chapter's existing formatting.
   Keep topic sentences aligned to what was agreed — do not upgrade them into finished prose.
3. **Compile** with `./compile.sh thesis.tex` to confirm the scaffolds render (draft mode on) and
   nothing broke. If it fails, inspect `output/output.log` and fix the LaTeX (usually an unescaped
   special char).
4. Tell Denis where the blocks are, and that step 3 is his: replace each `\scaffold{}` with prose,
   leave the `% >>> NARRATIVE` reference untouched. When done, he comes back for review (4a/4b).

## Boundaries
- Scaffolding only — no finished prose. Denis writes the prose (step 3).
- Never delete or rewrite his existing prose; edit-mode blocks go *above*, non-destructively.
