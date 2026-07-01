---
name: latexdiff
description: Generate a compiled latexdiff PDF of thesis changes using the repo's CI latexdiff pipeline. By default diffs uncommitted working-tree changes against HEAD; if the working tree is clean, diffs the last commit against its parent. Use when the user invokes /latexdiff or asks for a latexdiff / change-marked / tracked-changes PDF of the thesis.
---

# latexdiff

Produce a compiled **latexdiff** PDF (additions in blue underline, deletions in red
strikethrough) for the PhD thesis, using the repository's own CI pipeline so the
result matches what GitHub Actions produces on a PR.

The user is Denis, working in the thesis Overleaf repo
(`/home/denis/writing/phd_thesis/overleaf`). The heavy lifting is done by
[scripts/generate_latexdiff.py](../../../writing/phd_thesis/overleaf/scripts/generate_latexdiff.py),
which snapshots two Git revisions (or the working tree), rewrites the custom
`\cfchapter` macro, flattens `\input`/`\include`, and runs `latexdiff`. The output
`.tex` is then compiled with `./compile.sh`.

**Never re-implement the diff logic.** Always call `scripts/generate_latexdiff.py`
and `./compile.sh`. Run everything from the repo root.

---

## Step 0 — Resolve what to diff

Pick the base/head from the user's request. If they name what to diff against
(e.g. "against origin/master", "between commit A and B", "against the tag
submitted-v1"), use that. Otherwise apply this default cascade:

1. **Working tree dirty** (there are uncommitted changes to tracked `.tex`/build
   files) → diff **working tree against `HEAD`**:
   `--base-ref HEAD --head-working-tree`
   This is the common case — it shows exactly the edits not yet committed.
2. **Working tree clean** → diff the **last commit against its parent**:
   `--base-ref HEAD~1 --head-ref HEAD`
   This shows what the most recent commit changed.

Check dirtiness by looking only at **tracked** files with staged or unstaged
modifications — untracked scratch (`??`) does not count, because latexdiff needs
two committed-or-working states of the *same* file. Use `--porcelain` and keep
only `M`/`A`/`R`/`D`-status lines (drop `??`):

```bash
git status --porcelain --untracked-files=no -- '*.tex' '*.bib' '*.cls' '*.sty' Preamble Classes
```

`--untracked-files=no` suppresses the `??` noise (this repo has many untracked
scratch chapters). If that command prints anything, tracked build files are
modified → treat the tree as dirty (case 1). If it prints nothing, the tree is
clean for our purposes → case 2 (last commit vs parent).

When the request is ambiguous about the base but clearly wants a specific commit
range, prefer asking one short question over guessing. For the plain "make a
latexdiff" request, just apply the cascade and state which case you used.

## Step 1 — Generate the diff `.tex`

From the repo root:

```bash
python3 scripts/generate_latexdiff.py <base/head flags> --output thesis-latexdiff.tex
```

Flag forms:
- Uncommitted vs HEAD:      `--base-ref HEAD --head-working-tree`
- Last commit vs parent:    `--base-ref HEAD~1 --head-ref HEAD`
- Arbitrary two refs:       `--base-ref <BASE> --head-ref <HEAD>`
- Working tree vs a ref:    `--base-ref <BASE> --head-working-tree`

Exactly one of `--head-ref` / `--head-working-tree` must be given (the script
enforces this). `<BASE>`/`<HEAD>` are any Git refs: SHAs, branches, tags,
`origin/master`, `HEAD~3`, etc. Resolve merge bases yourself if the user wants a
branch-vs-master diff the way CI does it:

```bash
base=$(git merge-base origin/master HEAD)
python3 scripts/generate_latexdiff.py --base-ref "$base" --head-ref HEAD --output thesis-latexdiff.tex
```

## Step 2 — Compile the diff

Use the repo's build script (same as CI), never a bare `pdflatex`:

```bash
rm -rf output-thesis-latexdiff thesis-latexdiff.pdf
./compile.sh thesis-latexdiff.tex
```

`compile.sh` treats exit codes 0 and 12 as success and deletes the target PDF on
failure — so the presence of `thesis-latexdiff.pdf` is the success signal. On
failure, inspect `output-thesis-latexdiff/output.log`.

## Step 3 — Verify and report

- Confirm `thesis-latexdiff.pdf` exists.
- Sanity-check that the diff actually marked the expected changes, e.g.
  `grep -c 'DIFadd\|DIFdel' thesis-latexdiff.tex` (0 means nothing changed
  between the chosen base/head — say so plainly rather than presenting an empty
  diff as success).
- Report to the user: which base/head was used and *why* (which cascade case),
  the output path [thesis-latexdiff.pdf], and any pre-existing LaTeX warnings that
  are unrelated to the change.

Do not commit `thesis-latexdiff.tex` / `.pdf` or the `ci_artifacts/latexdiff-work/`
scratch unless the user asks — these are derived artifacts.

---

## Notes

- Requires `latexdiff` on PATH (`which latexdiff`) and a working TeX install. If
  `latexdiff` is missing, tell the user rather than trying to hand-roll a diff.
- The script writes scratch to `ci_artifacts/latexdiff-work/` and wipes it each
  run; that's expected.
- If the repo path differs from the default, run from wherever
  `scripts/generate_latexdiff.py` and `compile.sh` live — this skill assumes the
  thesis repo is the working directory.
