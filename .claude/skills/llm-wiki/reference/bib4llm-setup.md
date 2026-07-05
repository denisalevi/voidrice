# bib4llm — fallback full-text / figure extraction

`bib4llm` converts a PDF or a `.bib` library into LLM-friendly Markdown, and (unlike the Zotero
MCP `zotero_get_item_fulltext`) can extract **figures/images**. Use it only as a **fallback**:
when MCP full text is unavailable or insufficient, or when figure extraction is genuinely useful.
Do not reach for it by default — the MCP full text is the primary path.

## Detect before use — never assume it exists

`bib4llm` is not guaranteed to be installed on the current machine. Always check first:

```bash
command -v bib4llm && bib4llm --version
```

If it prints a path, use it (see **Typical use** below). If it prints nothing, either fall back
to the Zotero MCP full text (preferred, no install), tell the user extraction is unavailable, or
— if the user wants figure extraction and asks you to — install it as below.

## Install (only if missing AND the user wants it)

`bib4llm` is Denis's tool: `https://github.com/denisalevi/bib4llm.git`. It's a Python package, so
install it into an **isolated environment** — never the system/base Python.

**Pick the env manager to match what the user already uses. Detect first; if more than one is
present or it's ambiguous, ask rather than guess:**

```bash
for t in uv micromamba mamba conda pipx virtualenv; do
  command -v "$t" >/dev/null 2>&1 && echo "have: $t"
done
python3 --version   # for the plain-venv fallback
```

Then use the matching recipe below. All install from
`git+https://github.com/denisalevi/bib4llm.git` and end with `command -v bib4llm && bib4llm
--version`. Ensure `~/.local/bin` is on PATH (`export PATH="$HOME/.local/bin:$PATH"`) or call the
tool by absolute path.

### uv (fastest; good default if present)

```bash
uv tool install "git+https://github.com/denisalevi/bib4llm.git"   # puts `bib4llm` on PATH
```

### pipx (also gives a clean isolated CLI on PATH)

```bash
pipx install "git+https://github.com/denisalevi/bib4llm.git"
```

### micromamba / mamba / conda (env + thin PATH wrapper)

```bash
# swap `micromamba` for `mamba`/`conda` as available
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$HOME/.local/share/micromamba}"
micromamba create -y -n bib4llm python=3.12
micromamba run -n bib4llm pip install "git+https://github.com/denisalevi/bib4llm.git"
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/bib4llm" <<EOF
#!/usr/bin/env bash
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX}"
exec micromamba run -n bib4llm bib4llm "\$@"
EOF
chmod +x "$HOME/.local/bin/bib4llm"
```

### plain venv (no extra tooling; always works)

```bash
python3 -m venv "$HOME/.venvs/bib4llm"
"$HOME/.venvs/bib4llm/bin/pip" install "git+https://github.com/denisalevi/bib4llm.git"
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/.venvs/bib4llm/bin/bib4llm" "$HOME/.local/bin/bib4llm"
```

Record the install (date, env manager, source repo/commit) in the wiki's Zotero manifest the
first time you use it, so the provenance is traceable.

## Typical use

```bash
bib4llm convert path/to/paper.pdf          # one PDF -> Markdown + extracted images
bib4llm convert path/to/library.bib        # a whole .bib library
bib4llm watch   path/to/library.bib        # re-convert on change
```

Save the generated Markdown + images under the wiki's
`raw-input/files/zotero-extra-extracts/`, and record the run in
`raw-input/manifests/zotero-papers.md` with: source PDF path, command, date, output path, and why
the MCP fallback was needed. Prefer a later MCP-derived full text if one becomes available.
