# Global user instructions (Denis)

## Committing home-directory files: use `dotfiles`, not plain `git`

All of Denis's dotfiles and home-directory config on this machine are tracked in ONE git
repository via the `dotfiles` wrapper (`~/.local/bin/dotfiles` → `~/git/dotfiles.sh/dotfiles`).
It is a thin git wrapper with a custom `GIT_DIR` so `$HOME` itself is the work-tree of a bare
repo. This repo tracks **all** of Denis's dotfiles: `~/.claude/**` (skills like lit-review,
narrative, llm-wiki; settings), `~/.config/**`, shell rc files, etc.

**Rule:** any file under `$HOME` that is NOT inside a project/repo of its own is versioned with
`dotfiles`, and I must commit such edits with `dotfiles`, from `$HOME`:

```sh
dotfiles status --short          # what changed
dotfiles add <path> ...          # stage
dotfiles commit -m "..."         # commit
```

Plain `git` run in `$HOME` does NOT see these files (wrong GIT_DIR) — so skill/config edits
committed with plain `git` would silently never get versioned. Always use `dotfiles` for them.

This is SEPARATE from project repos (e.g. the PhD thesis at
`/home/denis/writing/phd_thesis/overleaf`), which use normal `git` with their own workflow.
Rule of thumb: file inside a project repo → `git`; home file outside any project repo →
`dotfiles`. (Denis has typed the wrapper name as "doftilfes" — it means `dotfiles`.)
