"profile start syntastic.log
"profile! file */syntastic/*

" ----- Plugins {{{1
  call plug#begin('~/.config/nvim/plugged')
  " ----- Making Vim look good ------------------------------------- {{{2
  "X Plugin 'altercation/vim-colors-solarized'
  Plug 'vim-airline/vim-airline'
  Plug 'vim-airline/vim-airline-themes'
  Plug 'morhetz/gruvbox'
  " Set gruvbox with wal and use automatically in vim
  Plug 'dylanaraps/wal.vim'
  " Distraction free centered vim mode:
  Plug 'junegunn/goyo.vim'
  Plug 'mikewest/vimroom'

  "Plugin 'tomasr/molokai'
  " TODO whats this doing?
  "Powerline with good infos (virtenv, branch etc)
  "Plugin 'Lokaltog/powerline', {'rtp': 'powerline/bindings/vim/'}

  " ----- Vim as a programmer's text editor ------------------------ {{{2
  Plug 'scrooloose/nerdtree'
  Plug 'jistr/vim-nerdtree-tabs'
  " Toggle line commenting
  Plug 'scrooloose/nerdcommenter'
  Plug 'xolox/vim-misc'
  "Plug 'xolox/vim-easytags'
  Plug 'ludovicchabant/vim-gutentags'
  "Plug 'vim-scripts/TagHighlight'
  "Plug 'majutsushi/tagbar'
  Plug 'ctrlpvim/ctrlp.vim'
  Plug 'FelikZ/ctrlp-py-matcher'
  Plug '/usr/bin/fzf'
  Plug 'junegunn/fzf.vim'
  Plug 'jeetsukumaran/vim-buffergator'
  Plug 'vim-scripts/a.vim'
  " MY STUFF
  " mappings for next / previous mappings
  Plug 'tpope/vim-unimpaired'
  " show changes to saved file using vimdiff
  Plug 'jmcantrell/vim-diffchanges'
  Plug 'nvim-tree/nvim-web-devicons'
  Plug 'sindrets/diffview.nvim'
  "Plug 'sjl/gundo.vim'  " XXX needs python2
  Plug 'simnalamburt/vim-mundo'  " Fork of gundo
  " markdown preview, needs npm installed and instand-markdown-d
  " `sudo npm -g install instant-markdown-d`, see github install instructions
  " or better use pacman AUR script (see system setup notes)
  Plug 'suan/vim-instant-markdown', {'for': 'markdown'}
  " rst file viewer
  Plug 'Rykka/InstantRst'
  " Make tabular looking stuff in vim (alignment etc.), check out vimcast
  Plug 'godlygeek/tabular'
  Plug 'plasticboy/vim-markdown'
  Plug 'vimwiki/vimwiki'
  " similar to ctrlp or fuzzyfinder, needed for citation.vim
  Plug 'Shougo/unite.vim'
  " Open Zotero links and paste citations from within vim
  Plug 'rafaqz/citation.vim'
  " Hide ANSI sequences (there is a more up to date version here:
  " http://www.drchip.org/astronaut/vim/index.html#ANSIESC
  Plug 'powerman/vim-plugin-AnsiEsc'
  Plug 'github/copilot.vim'

  " ----- Working with Git ----------------------------------------- {{{2
  Plug 'airblade/vim-gitgutter'
  Plug 'tpope/vim-fugitive'
  " Allow working with symlinks in vim
  Plug 'aymericbeaumet/vim-symlink'
  Plug 'moll/vim-bbye' " optional dependency

  " ---- Other stuff without own section --------------------------- {{{2
  " automatic closing of brackets
  "X Plug 'Raimondi/delimitMate'
  "Plug 'tomtom/tinykeymap_vim'
  " local vimrc
  Plug 'MarcWeber/vim-addon-local-vimrc'
  " directory specific vim settings
  "Plug 'chazy/dirsettings'

  " ----- Syntax plugins ------------------------------------------- {{{2
  " TODO XXX: get something useful and fast for neovim!
  " TODO do I need the indent vim?
  "X Plug 'vim-scripts/indentpython.vim'
  Plug 'Vimjas/vim-python-pep8-indent'
  "Plug 'denisalevi/vim-pydocstring'
  Plug 'heavenshell/vim-pydocstring', { 'do': 'make install', 'for': 'python' }
  " Use either syntastic + flake8 isntalled or vim-flake8
  "Plug 'vim-syntastic/syntastic'
  " TODO: check out w0rp/ale for asynchronous checking
  "Plug 'nvie/vim-flake8'
  Plug 'denisalevi/Vim-Jinja2-Syntax'
  " Plug 'niftylettuce/Vim-Jinja2-Syntax'
  Plug 'rhysd/vim-clang-format'
  " Markers at indent levels
  "Plug 'nathanaelkane/vim-indent-guides'
  Plug 'vim-python/python-syntax'
  " Add syntax plugins above polyglot to be loaded first
  Plug 'sheerun/vim-polyglot'
  " i3 config syntax
  Plug 'PotatoesMaster/i3-vim-syntax'
  " latex support
  Plug 'vim-latex/vim-latex'
  " json highlighting and folding (already in polyglot)
  "Plug 'elzr/vim-json'
  "Plug 'lazywei/vim-matlab'
  Plug 'yinflying/matlab.vim'
  " support for R code (including execution)
  "Plug 'jalvesaq/Nvim-R', {'branch': 'stable'}

  " ----- man pages, tmux ------------------------------------------ {{{2
  Plug 'jez/vim-superman'
  Plug 'christoomey/vim-tmux-navigator'

  " ----- Notes plugins -------------------------------------------- {{{2
  Plug 'xolox/vim-notes'
  " interact with shell to open e.g. image under cursor
  Plug 'xolox/vim-shell'

  " ---- Extras/Advanced plugins ----------------------------------- {{{2
  " Highlight and strip trailing whitespace
  Plug 'ntpeters/vim-better-whitespace'
  " Easily surround chunks of text
  Plug 'tpope/vim-surround'
  " comment out stuff with gcc
  Plug 'tpope/vim-commentary'
  " Store/restore vim sessions
  Plug 'tpope/vim-obsession'
  " Align CSV files at commas, align Markdown tables, and more
  "Plug 'godlygeek/tabular'
  " Automaticall insert the closing HTML tag
  "Plug 'HTML-AutoCloseTag'
  " Make tmux look like vim-airline (read README for extra instructions)
  " either this or just install powerline and source in .tmux.conf
  Plug 'edkolev/tmuxline.vim'
  " All the other syntax plugins I use
  "Plug 'ekalinin/Dockerfile.vim'
  "Plug 'digitaltoad/vim-jade'
  "Plug 'tpope/vim-liquid'
  "Plug 'cakebaker/scss-syntax.vim'
  Plug 'anufrievroman/vim-angry-reviewer'

  " ------ My old stuff --------------------------------------------- {{{2
  "DirDiff directory diff
  Plug 'will133/vim-dirdiff'
  "Lindiff visual blocks diff
  Plug 'AndrewRadev/linediff.vim'
  " Ack from inside vim
  Plug 'mileszs/ack.vim'
  " TODO autocompletion!
  " Conquerer of Completion
  Plug 'neoclide/coc.nvim', {'branch': 'release'}
  " language server plugin for deoplete
  "Plug 'autozimu/LanguageClient-neovim', {
  "  \ 'branch': 'next',
  "  \ 'do': 'bash install.sh',
  "  \ }
  " Asynchronous linting/fixing for Vim and Language Server Protocol (LSP) integration
  "Plug 'dense-analysis/ale'
  Plug 'psf/black', { 'branch': 'stable' }
  " async make (disabled sinc it does the same as ale?
  " Plug 'neomake/neomake'
  " async execution of external commands
  Plug 'skywind3000/asyncrun.vim'
  Plug 'preservim/vimux'
  " Smart Pthon Syntax
  "Plug 'numirias/semshi', {'do': ':UpdateRemotePlugins'}

  "Python autocompletion
  "Plug 'davidhalter/jedi-vim' "YouCompleteMe incorporates this for Python?
  "Autocompletion
  "Plug 'Valloric/YouCompleteMe'
  "Python code folding
  "Plug 'tmhedberg/SimpylFold'
  "Syntax checking
  " TODO neomake (automatic make while modfying file)
  " XXX: This gives super slow vim startup times when an env is active already...
  "Plug 'cjrh/vim-conda'

  call plug#end()


" ----- Vim Options {{{1

  runtime macros/matchit.vim

  "let mapleader="\<space>"
  " this way we get showcmd will show the command
  " and space does not move the curser
  map <space> <leader>

  "Use UTF8 encoding
  set encoding=utf-8

  " We need this for plugins like Syntastic and vim-gitgutter which put symbols
  " in the sign column.
  hi clear SignColumn

  "Make code pretty
  " Uncomment if not using vim-python/python-syntax plugin
  "let python_highlight_all = 1
  syntax on

  " *** GENERAL OPTS ***
  set hidden                              " Make it possible to hide modified buffers
  set modeline                            " last line of file has file specific vim options
  set backspace=indent,eol,start
  set number                              " show line numbering
  set mouse=a                             " Enable mouse in terminal
  set wildmenu                            " fancier completion
  set scrolloff=3                         " move the screen when 3 lines from border
  set splitright
  set splitbelow
  set tildeop                             " use ~ to change letter case
  set wildignore=*.o,*.obj,*~,*.pyc       " ignore while tab completing
  set showcmd                             " show cmd in status line
  set showmatch                           " show matching brackets
  set tabpagemax=30                       " max number of tabs ( -p cmdline option )
  set ruler                               " status line stuff
  set hlsearch                            " highlights search matches
  set incsearch                           " jump to first match while typing
  set ignorecase                          " ignore case in search pattern
  set smartcase                           " ignore ignorecase if search pattern has uppercase
  set showbreak=+                         " line wrapping sign
  if !has('nvim')
    " neovim defaults to ~/.local/share/nvim/swap
    set directory=~/.vim/tmp/               " swap directory (*.sw? files)
  endif
  "set cursorline                          " highlights active cursor line
  "set t_Co=16                             " proper color themes in terminal mode
  set notitle                             " suppress 'Thanks for flying vim' message
  set timeoutlen=1000 ttimeoutlen=10      " less delay after pressing ESC
  set nojoinspaces                        " avoids to 2 spaces after dots when joining lines
  set foldmethod=syntax                   " code folding
  set breakindent                         " Indent wrapped lines up to the same level
  set foldnestmax=1                       " only fold up to one level deep
  set nospell
  set formatoptions-=t                     " turn off automatic line breaks
  " Enable persistent undo so that undo history persists across vim sessions
  set undofile
  set undodir=~/.vim/undo
  autocmd FileType txt, markdown set formatoptions+=t " turn automatic line breaks on for text files

  " Read documents directory from xdg user dir config
  let g:documents_dir=substitute(system('xdg-user-dir DOCUMENTS'), '\n', '', 'g')

  if has("nvim")
    " use system python as python provider for neovim plugins
    let g:python3_host_prog = '/usr/bin/python3'
    let g:python_host_prog = '/usr/bin/python2'
    " Enable embedded syntax highlighting (for Python e.g.)
    let g:vimsyn_embed = 'P'
  endif

  " Remember fold states after closing vim
  set viewoptions-=options                " Don't save window / buffer local options
  " XXX: This is important if you rely on correct pwd, e.g. for autocommits
  set viewoptions-=curdir                 " Don't save local pwd of window
  augroup AutoSaveFolds
    autocmd!
    autocmd BufWinLeave ?* mkview 1
    autocmd BufWinEnter ?* silent! loadview 1
  augroup END
  set nofoldenable                        " disable folding by default

" " OmniComplete
" if has("autocmd") && exists("+omnifunc")
"   autocmd Filetype *
"         \if &omnifunc == "" |
"         \setlocal omnifunc=syntaxcomplete#Complete |
"         \endif
" endif
"
" hi Pmenu  guifg=#000000 guibg=#F8F8F8 ctermfg=black ctermbg=Lightgray
" hi PmenuSbar  guifg=#8A95A7 guibg=#F8F8F8 gui=NONE ctermfg=darkcyan ctermbg=lightgray cterm=NONE
" hi PmenuThumb  guifg=#F8F8F8 guibg=#8A95A7 gui=NONE ctermfg=lightgray ctermbg=darkcyan cterm=NONE
"
" " Some convenient mappings
" inoremap <expr> <Esc>      pumvisible() ? "\<C-e>" : "\<Esc>"
" inoremap <expr> <CR>       pumvisible() ? "\<C-y>" : "\<CR>"
" "inoremap <expr> <Down>     pumvisible() ? "\<C-n>" : "\<Down>"
" "inoremap <expr> <Up>       pumvisible() ? "\<C-p>" : "\<Up>"
" "inoremap <expr> <C-d>      pumvisible() ? "\<PageDown>\<C-p>\<C-n>" : "\<C-d>"
" "inoremap <expr> <C-u>      pumvisible() ? "\<PageUp>\<C-p>\<C-n>" : "\<C-u>"
"
" " Automatically open and close the popup menu / preview window
" au CursorMovedI,InsertLeave * if pumvisible() == 0|silent! pclose|endif
" set completeopt=menu,preview,longest
"
" " Enable omni-completion.
" autocmd FileType css setlocal omnifunc=csscomplete#CompleteCSS
" autocmd FileType html,markdown setlocal omnifunc=htmlcomplete#CompleteTags
" autocmd FileType javascript setlocal omnifunc=javascriptcomplete#CompleteJS
" autocmd FileType python setlocal omnifunc=pythoncomplete#Complete
" autocmd FileType xml setlocal omnifunc=xmlcomplete#CompleteTags
" autocmd FileType ruby setlocal omnifunc=rubycomplete#Complete
" autocmd FileType haskell setlocal omnifunc=necoghc#omnifunc


" ----- Plugin-Specific Settings {{{1

  " tpope/vim-fugitive {{{2
  " Add support for bare dotfiles repo with working tree in $HOME
  " Adapted from https://github.com/tpope/vim-fugitive/discussions/1656#discussioncomment-6616748
  augroup dotfiles
    autocmd VimEnter * call InitDotfileRepo()
    autocmd BufReadPost * call InitDotfileRepo(bufnr(''))
  augroup END

  function InitDotfileRepo(...)
    " Get user home directory
    let user_home = fnamemodify($HOME, ':p')
    let dotfile_dir = $HOME
    let dotfile_repo = $HOME . '/git/dotfiles'

    " Did fugitive detect a git repo? Then do nothing
    if (len(FugitiveGitDir()))
      return
    endif

    " Else check if we are in the dotfile worktree
    let path = fnamemodify(a:0 ? bufname(a:1) : getcwd(), ':p:h')
    let dotfile_len = len(dotfile_dir)
    if (len(path) >= dotfile_len && path[0:dotfile_len - 1] ==# dotfile_dir)
      call FugitiveDetect(dotfile_repo)
    endif
  endfunction

  " 'anufrievroman/vim-angry-reviewer' {{{2
  let g:AngryReviewerEnglish = 'american'

  " vimroom
  " Replace the end of buffer ~ signs with space (there should be a white
  " space after \ )
  set fcs=eob:\ 

  " goyo
  let g:goyo_linenr=1
"  let g:goyo_height="100%"

" function! s:goyo_enter()
"   "silent! GitGutterEnable
"   AirlineToggle
"   " For some reason, Airline requires two refreshes to avoid display
"   " artifacts
"   silent! AirlineRefresh
"   silent! AirlineRefresh

"   silent! call lightline#enable()
" endfunction
" autocmd! User GoyoEnter nested call <SID>goyo_enter()

"  function! s:goyo_leave()
"  endfunction
"  autocmd! User GoyoLeave nested call <SID>goyo_leave()


  " -----'numirias/semshi'  {{{2
  "let g:semshi#simplify_markup = v:false

  " -----'mileszs/ack.vim'  {{{2
  nmap <leader>a :Ack<CR>


  " ----- rafaqz/citation.vim  {{{2
  let g:citation_vim_mode="zotero"
  let g:citation_vim_zotero_path="~/.local/share/data/zotero"
  let g:citation_vim_zotero_version=5
  let g:citation_vim_zotero_attachment_path="~/zotero"
  let g:citation_vim_cache_path='~/.config/nvim/citation.vim.cache/'
  " change citation style here (pandoc default is [@...])
  let g:citation_vim_outer_prefix="["
  let g:citation_vim_inner_prefix="@"
  let g:citation_vim_suffix="]"
  " other citations options
  let g:citation_vim_et_al_limit=1



  " ----- xolox/vim-shell  {{{2
  "  disable default mappings
  let g:shell_mappings_enabled = 0

  " F11 maximizes only within vim (removing buffer/tab bars)
  " for fullscreen use i3
  inoremap <F11> <C-o>:Maximize<CR>
  nnoremap <F11> :Maximize<CR>

  " Make open work with relative paths in files
  fun! s:open_with_rel_path()
    " test if cursor under file starts with ./ (there is a relative path)
    if expand("<cfile>") =~ '^\./' || expand("<cfile>") =~ 'images'
      " % path of current file; %:h head removed (gives directory);
      " <cfile>: file under cursor
      :Open %:h/<cfile>
    else
      :Open
    endif
  endfun

  "command! -bar -nargs=? -complete=file OpenWithRelPath call s:open_with_rel_path(<q-args>)
  " disable netrw gx (XXX problem when opening remote files!)
  let g:netrw_nogx = 1
  " set gx to use vim-shell's open (does not block vim due to async)
  nnoremap gx :call <SID>open_with_rel_path()<CR>
  " make it work with visual selection (side effect: yanks visual selection)
  xnoremap gx y:Open <C-r>=fnameescape(@")<CR><CR>


  " ----- xolox/vim-notes  {{{2
  let g:notes_directories = [g:documents_dir . '/notes/vim-notes']
  let g:notes_suffix = '.txt'
	" open files created with vim-notes plugin as correct filetype
	for notes_dir in g:notes_directories
		autocmd BufRead,BufNewFile notes_dir/*.txt set filetype=notes
    " for how to make if clause with path (if suffix is not txt)
    " autocmd BufRead,BufNewFile notes_dir/* if expand("%:p:h") !~ '^/images' | set filetype=notes | endif
	endfor

  " ----- altercation/vim-colors-solarized settings  {{{2
  " Set the colorscheme
  "colorscheme solarized

  " gruvbox
  colorscheme gruvbox
  set termguicolors

  " wal
  "colorscheme wal
  " don't set termguicolors as it messes up wal colorscheme in neovim

  " Colorscheme background
  " my_terminal_bg is set in ~/.config/aliasrc nvim()
  if exists('my_terminal_bg') && my_terminal_bg == 'light'
    set background=light
  else
    set background=dark
  endif

  " Not needed when terminal uses 16 Solarized colors
  "let g:solarized_termcolors=256

  " needs to be set after colorscheme (which resets SpellBad)
  " XXX: nvim is gui, not cterm!
  hi clear SpellBad
  hi SpellBad cterm=bold,underline ctermfg=red gui=bold,underline guifg=red
  " Different color for regional errors (e.g. behavior vs. behaviour)
  "hi SpellLocal cterm=bold,underline ctermfg=yellow gui=bold,underline guifg=orange

  " ----- vim-airline/vim-airline settings  {{{2
  " Always show statusbar
  set laststatus=2
  set showtabline=1  " Set to 2 if using tabline extension
  " dont show INSERT / VISUAL in statusline (shown by powerline already)
  "set noshowmode

  " Fancy arrow symbols, requires a patched font
  let g:airline_powerline_fonts = 0

  " Show PASTE if in paste mode
  let g:airline_detect_paste=1

  " Show airline for tabs too
  " > Disabled this since it slows down vim many tabs...
  "let g:airline#extensions#tabline#enabled = 1

  " Show vim-obsession status
  let g:airline#extensions#obsession#enabled = 1
  "let g:airline#extensions#obsession#indicator_text = ''

  " Show just the filename
  " > Makes only sense if tabline is used, else full path is fine
  "let g:airline#extensions#tabline#fnamemod = ':t'

  " Use the solarized theme for the Airline status bar
  let g:airline_theme='gruvbox'

  let g:airline#extensions#tabline#show_tabs = 0
  let g:airline#extensions#tabline#show_buffers = 1

  " Show numbers in tabline
  let g:airline#extensions#tabline#buffer_nr_show = 1

  " ----- edkolev/tmuxline {{{2
  "  turn off powerline symbols
  let g:tmuxline_powerline_separators = 0

  " ----- 'neoclide/coc.nvim' {{{2

  set updatetime=300                      " default 4000 ms
  set shortmess+=c                        " Don't pass messages to |ins-completion-menu|
  " Always show the signcolumn, otherwise it would shift the text each time
  " diagnostics appear/become resolved.
  if has("patch-8.1.1564")
    " Recently vim can merge signcolumn and number column into one
    set signcolumn=number
  else
    set signcolumn=yes
  endif


  " use <tab> for trigger completion and navigate to next complete item
  function! s:check_back_space() abort
    let col = col('.') - 1
    return !col || getline('.')[col - 1]  =~ '\s'
  endfunction

  " tab for next item or completion trigger
  inoremap <silent><expr> <TAB>
        \ pumvisible() ? "\<C-n>" :
        \ <SID>check_back_space() ? "\<TAB>" :
        \ coc#refresh()

  " S-tab for previous item in list
  "inoremap <expr> <S-Tab> pumvisible() ? "\<C-p>" : "\<S-Tab>"
  inoremap <expr> <S-Tab> pumvisible() ? "\<C-p>" : "\<C-h>"

  " enter confirm completion
  inoremap <expr> <cr> pumvisible() ? "\<C-y>" : "\<C-g>u\<CR>"

  " close preview window when completion is done
  autocmd! CompleteDone * if pumvisible() == 0 | pclose | endif

  " --- coc extentions
  let g:coc_global_extensions = ['coc-json', 'coc-pyright']

  " --- airline stuff
	" if you want to disable auto detect, comment out those two lines
	"let g:airline#extensions#disable_rtp_load = 1
	"let g:airline_extensions = ['branch', 'hunks', 'coc']

	let g:airline_section_error = '%{airline#util#wrap(airline#extensions#coc#get_error(),0)}'
	let g:airline_section_warning = '%{airline#util#wrap(airline#extensions#coc#get_warning(),0)}'

  " Change error symbol:
	let airline#extensions#coc#error_symbol = 'Error:'
  " Change warning symbol:
	let airline#extensions#coc#warning_symbol = 'Warning:'
  " Change error format:
	let airline#extensions#coc#stl_format_err = '%E{[%e(#%fe)]}'
  " Change warning format:
	let airline#extensions#coc#stl_format_warn = '%W{[%w(#%fw)]}'

  " Choose correct interpreter
  if $CONDA_PREFIX == ""
    let s:current_python_path='/usr/bin/python'
  else
    let s:current_python_path=$CONDA_PREFIX.'/bin/python'
  endif
  call coc#config('python', {'pythonPath': s:current_python_path})

  " GoTo code navigation.
  nmap <silent> gd <Plug>(coc-definition)
  nmap <silent> gy <Plug>(coc-type-definition)
  nmap <silent> gi <Plug>(coc-implementation)
  nmap <silent> gr <Plug>(coc-references)

  " Use K to show documentation in preview window.
  nnoremap <silent> K :call <SID>show_documentation()<CR>

  function! s:show_documentation()
    if (index(['vim','help'], &filetype) >= 0)
      execute 'h '.expand('<cword>')
    elseif (coc#rpc#ready())
      call CocActionAsync('doHover')
    else
      execute '!' . &keywordprg . " " . expand('<cword>')
    endif
  endfunction

  nmap <leader>R <Plug>(coc-rename)

  " " Highlight the symbol and its references when holding the cursor.
  " autocmd CursorHold * silent call CocActionAsync('highlight')

  " Remap <C-f> and <C-b> for scroll float windows/popups.
  if has('nvim-0.4.0') || has('patch-8.2.0750')
    nnoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
    nnoremap <silent><nowait><expr> <C-b> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-b>"
    inoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? "\<c-r>=coc#float#scroll(1)\<cr>" : "\<Right>"
    inoremap <silent><nowait><expr> <C-b> coc#float#has_scroll() ? "\<c-r>=coc#float#scroll(0)\<cr>" : "\<Left>"
    vnoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
    vnoremap <silent><nowait><expr> <C-b> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-b>"
  endif

  " ----- 'w0rp/ale' {{{2
  " Disable ALE by default
  let g:ale_enables = 0

  let g:ale_fixers = {
  \   '*': ['remove_trailing_lines', 'trim_whitespace'],
  \   'python': ['black'],
  \}
  let g:ale_linters = {
  \   'python': ['flake8', 'pylint'],
  \}
  " Pyling warns against using f-string in logging message, readability > useless optimization
  let g:ale_python_pylint_options = '--disable logging-fstring-interpolation'

  nmap <F10> :ALEFix<CR>

  function! LinterStatus() abort
    let l:counts = ale#statusline#Count(bufnr(''))

    let l:all_errors = l:counts.error + l:counts.style_error
    let l:all_non_errors = l:counts.total - l:all_errors

    return l:counts.total == 0 ? '✨ all good ✨' : printf(
          \   '😞 %dW %dE',
          \   all_non_errors,
          \   all_errors
          \)
  endfunction

  set statusline=
  set statusline+=%m
  set statusline+=\ %f
  set statusline+=%=
  set statusline+=\ %{LinterStatus()}

  " " ----- neomake/neomake {{{2
  " function! MyOnBattery()
  "   return readfile('/sys/class/power_supply/AC/online') == ['0']
  " endfunction

  " if MyOnBattery()
  "   call neomake#configure#automake('w')
  " else
  "   call neomake#configure#automake('nw', 1000)
  " endif

  " ----- skywind3000/asyncrun.vim {{{2
  " <leader>o -> Load brian2cuda and brian2 from current directory
  autocmd FileType python nmap <leader>o :call RunPythonAsync()<CR>
  " <leader>O -> Don't load anything, just run current Python env
  autocmd FileType python nmap <leader>O :AsyncRun -raw python %<CR>
  autocmd FileType matlab nmap <leader>o :AsyncRun matlab -batch %:r<CR>
  autocmd BufEnter *.m compiler mlint
  " automatically open quick-fix window with 6 lines
  let g:asyncrun_open = 6
  " disable Python buffering of stdout for background processes
  let $PYTHONUNBUFFERED=1
  " vim fugitive Gpull and Gpatch async
  command! -bang -nargs=* -complete=file Make AsyncRun -program=make @ <args>
  " Display asyncrun status with vim-airline
  let g:asyncrun_status = ''
  let g:airline_section_error = airline#section#create_right(['%{g:asyncrun_status}'])

	" -----  'ctrlpvim/ctrlp.vim'  {{{2
  " Use the nearest .git directory as the cwd
  " This makes a lot of sense if you are working on a project that is in
  " version control. It also supports works with .svn, .hg, .bzr.
  let g:ctrlp_working_path_mode = 'ra'
	" cache the file indexing
	let g:ctrlp_cache_dir = $HOME . '/.cache/ctrlp'
	" use ag (faster)
	"if executable('ag')
  "  " Use Ag over Grep
  "  " Use ag in CtrlP for listing files. Lightning fast and respects
  "  " .gitignore
  "  set grepprg=ag\ --nogroup\ --nocolor
	"	let g:ctrlp_user_command = 'ag %s -l --nocolor -g ""'
  "elseif executable('junest')
	"	let g:ctrlp_user_command = 'junest -u -- ag %s -l --nocolor -g ""'
	"endif
  let g:ctrlp_user_command = ['.git/', 'git --git-dir=%s/.git ls-files -oc --exclude-standard']
	" Setup some default ignores
	let g:ctrlp_custom_ignore = {
				\ 'dir':  '\v[\/](\.(git|hg|svn)|\_site|\/home\/denis)$',
				\ 'file': '\v\.(exe|so|dll|class|png|jpg|jpeg)$',
				\}
  " faster match function ('FelikZ/ctrlp-py-matcher')
  let g:ctrlp_match_func = { 'match': 'pymatcher#PyMatch' }

  " ----- 'jeetsukumaran/vim-buffergator'  {{{2
  " don't use buffergator key mappings
  let g:buffergator_suppress_keymaps = 1
  " my own keybindings (partly copied from buffergator defaults)
  nnoremap <silent> <Leader>b :BuffergatorOpen<CR>
  "nnoremap <silent> <Leader>B :BuffergatorClose<CR>
  nnoremap <silent> <Leader>T :BuffergatorTabsOpen<CR>
  "nnoremap <silent> <Leader>T :BuffergatorTabsClose<CR>
  nnoremap <silent> gb :BuffergatorMruCyclePrev<CR>
  nnoremap <silent> gB :BuffergatorMruCycleNext<CR>
  nnoremap <silent> <Leader><LEFT> :BuffergatorMruCyclePrev leftabove vert sbuffer<CR>
  nnoremap <silent> <Leader><UP> :BuffergatorMruCyclePrev leftabove sbuffer<CR>
  nnoremap <silent> <Leader><RIGHT> :BuffergatorMruCyclePrev rightbelow vert sbuffer<CR>
  nnoremap <silent> <Leader><DOWN> :BuffergatorMruCyclePrev rightbelow sbuffer<CR>
  nnoremap <silent> <Leader><S-LEFT> :BuffergatorMruCycleNext leftabove vert sbuffer<CR>
  nnoremap <silent> <Leader><S-UP> :BuffergatorMruCycleNext leftabove sbuffer<CR>
  nnoremap <silent> <Leader><S-RIGHT> :BuffergatorMruCycleNext rightbelow vert sbuffer<CR>
  nnoremap <silent> <Leader><S-DOWN> :BuffergatorMruCycleNext rightbelow sbuffer<CR>

  " ----- scrooloose/nerdtree  {{{2
  "hide .pyc files in NERDTree
  let NERDTreeIgnore=['\.pyc$', '\~$'] "ignore files in NERDTree


  " ----- jistr/vim-nerdtree-tabs  {{{2
  " To have NERDTree always open on startup
  "let g:nerdtree_tabs_open_on_console_startup = 1


  " ----- scrooloose/syntastic settings  {{{2
"  let g:syntastic_error_symbol = '✘'
"  let g:syntastic_warning_symbol = "▲"
"  " Turn of automatic checking at write
"  "let g:syntastic_mode = "passive"
"  let g:syntastic_check_on_wq = 0
"  " make :lnext work after running check (might conflict with loc list plugins)
"  let g:syntastic_always_populate_loc_list = 1
"  augroup mySyntastic
"    au!
"    au FileType tex let b:syntastic_mode = "passive"
"  augroup END
"  " Use flake8 for python files
"  let g:syntastic_python_checkers = ['flake8']
"  " active filtypes are checked automatically at file writing
"  "let g:syntastic_mode_map = { 'mode': 'active',
"  "            \ 'active_filetypes': ['python'],
"  "            \ 'passive_filetypes': [] }


"  " ----- xolox/vim-easytags settings  {{{2
"  " ./tags uses tag file in current dir instead of current file
"  set cpoptions+=d
"  " Where to look for tags files
"  set tags=./.tags,.tags
"  "TODO set tags=./tags;$HOME (walk directory tree upto $HOME looking for tags)
"  " Sensible defaults
"  let g:easytags_events = ['BufReadPost', 'BufWritePost']
"  let g:easytags_async = 1
"  let g:easytags_dynamic_files = 1
"  let g:easytags_resolve_links = 1
"  "let g:easytags_auto_highlight = 0
"  "let g:easytags_suppress_ctags_warning = 1


  " ----- majutsushi/tagbar settings  {{{2
  " Uncomment to open tagbar automatically whenever possible
  "autocmd BufEnter * nested :call tagbar#autoopen(0)
  " tagbar TOC support for vimwiki files, see vwtags.py for instructions
  " https://raw.githubusercontent.com/vimwiki/utils/master/vwtags.py
  let g:tagbar_type_vimwiki = {
          \   'ctagstype':'vimwiki'
          \ , 'kinds':['h:header']
          \ , 'sro':'&&&'
          \ , 'kind2scope':{'h':'header'}
          \ , 'sort':0
          \ , 'ctagsbin':g:documents_dir . '/notes/vimwiki/vwtags.py'
          \ , 'ctagsargs': 'markdown'
          \ }

  " ----- 'MarcWeber/vim-addon-local-vimrc'  {{{2
  " Use .local-vimrc file for folder specific options
  let g:local_vimrc = {'names':['.local-vimrc'],'hash_fun':'LVRHashOfFile'}

  " ----- 'ludovicchabant/vim-gutentags'  {{{2
  " home directory is a git directory, don't generate tag files for that
  " ['/usr/local'] is the default (see help:gutentags)
  let g:gutentags_exclude_project_root = ['/usr/local', '~']
  " create tagfiles for brian2 generated projects
  let g:gutentags_project_root = ['code_objects']
  " put tag files in cache dir
  let g:gutentags_cache_dir = '~/.cache/gutentags'
  " print TAGS in statusline when gutentags is generating
  set statusline+=%{gutentags#statusline()}


  " ----- airblade/vim-gitgutter settings  {{{2
  " In vim-airline, only display "hunks" if the diff is non-zero
  let g:airline#extensions#hunks#non_zero_only = 1


  " ----- Raimondi/delimitMate settings  {{{2
  let delimitMate_expand_cr = 1
  augroup mydelimitMate
    au!
    au FileType markdown let b:delimitMate_nesting_quotes = ["`"]
    au FileType tex let b:delimitMate_quotes = ""
    au FileType tex let b:delimitMate_matchpairs = "(:),[:],{:},`:'"
    " Uncomment to have matching tripple quotes
    "au FileType python let b:delimitMate_nesting_quotes = ['"', "'"]
  augroup END


  " ----- jez/vim-superman settings  {{{2
  " better man page support
  "noremap K :SuperMan <cword><CR>


  " ----- nvie/vim-flake8 settings  {{{2
  " Show signs in gutter
  "let g:flake8_show_in_gutter=1


  " ----- SimplyFold  {{{2
  "autocmd BufWinEnter *.py setlocal foldexpr=SimpylFold(v:lnum) foldmethod=expr
  "autocmd BufWinLeave *.py setlocal foldexpr< foldmethod<
  ""Show docstring of foled code
  "let g:SimpylFold_docstring_preview=1

  " ----- vim-python/python-syntax {{{2
  let g:python_highlight_all = 1

  " ----- denisalevi/Vim-Jinja2-Syntax'
  " turn on/off Jinja syntax highlighting and matchit support
  let g:enable_jinja_matchit = 1
  let g:enable_jinja_highlighting = 1

  " ----- sjl/gundo.vim {{{2
  " turn of autmatic diff preview (manual with r)
  let g:gundo_auto_preview = 0

  " ----- suan/vim-instant-markdown {{{2
  "  don't autostart markdown preview
  let g:instant_markdown_autostart = 0
  " start new browser window to view markdown
  "let g:instant_markdown_browser = "firefox --new-window"
  let g:instant_markdown_browser = "chromium"
  let g:instant_markdown_allow_external_content = 1
  " mappings to open and close markdown preview
  autocmd FileType markdown nnoremap <leader>lv :InstantMarkdownPreview<CR>
  autocmd FileType markdown nnoremap <leader>lq :InstantMarkdownStop<CR>
  " log file
  let g:instant_markdown_logfile = '/tmp/instant_markdown.log'

  " ----- vimwiki/vimwiki {{{2
  let g:vimwiki_list = [{'path': g:documents_dir . '/notes/vimwiki/',
        \ 'syntax': 'markdown', 'ext': '.md'},
        \ {'path': '~/git/sprekelerlab/wiki.wiki/',
        \ 'syntax': 'markdown', 'ext': '.md'},
        \ {'path': '~/projects/brian2cuda/brian2cuda-wiki/',
        \ 'syntax': 'markdown', 'ext': '.md'}]
  " define preview command in vimwiki to first change directory to wiki root
  " if multiple wikis are used, the index of g:vimwiki_list has to be adapted
  autocmd FileType vimwiki nnoremap <leader>lv :execute 'cd' fnameescape(g:vimwiki_list[0].path) <BAR> :InstantMarkdownPreview<CR> <BAR> :cd -<CR>
  autocmd FileType vimwiki nnoremap <leader>lq :InstantMarkdownStop<CR>

  " Open github style relative links that start with "images/" in vimwiki filetypes with
  " xdg-open correctly (avoids need to use file: or local:, which github
  " doesn't understand)
  " TODO: instead of matching folder names, check if relative path exists in
  " wiki root directory
  function! VimwikiLinkHandler(link)
    let link = a:link
    let wiki_nr = 0
    if wiki_nr == 1
      " TODO use link parser of mediawiki syntax to get correct link if there
      " are comments (mediawiki: [[description|filename]], but vimwiki:
      " [[filename| description]])
      let link = substitute(link, " ", "-", "g")
      " cmd can be different if split is used (see vimwiki#base#follow_link())
      let cmd = ':e'
      call vimwiki#base#open_link(cmd, link)
      return 1
    endif
    if link =~# '^images/\|^./images'  "XXX add more match cases here
      let wiki_nr = 0
      let root_directory = vimwiki#vars#get_wikilocal('path', wiki_nr)
      call vimwiki#base#system_open_link(root_directory . link)
      return 1
    elseif link =~# '^pdfs/\|^./pdfs'  "XXX add more match cases here
      let wiki_nr = 0
      let root_directory = vimwiki#vars#get_wikilocal('path', wiki_nr)
      execute "AsyncRun -silent zathura "root_directory . link
      return 1
    elseif link =~# '^zotero:'
      call vimwiki#base#system_open_link(link)
      "execute "AsyncRun -silent xdg-open "link
      return 1
    else
      return 0
    endif
  endfunction

  " Generate markdown links to GitHub issues/commits on
  " /user/repository#issue or /user/repository@sha
  autocmd fileType markdown nmap <leader>g :py3 CreateGithubLink()<CR>


  " ----- vim-latex/vim-latex {{{2
  " Set default filteyp for .tex files to 'tex'
  let g:tex_flavor = "latex"

  " Default compiling format
  let g:Tex_DefaultTargetFormat='pdf'

  " Never Forget, To set the default viewer:: Very Important
  let g:Tex_ViewRule_pdf = 'zathura'

  " disable folding
  let g:Tex_FoldedSections=""
  let g:Tex_FoldedEnvironments=""
  let g:Tex_FoldedMisc=""

  " Trying to add same for pdfs, hoping that package SynTex is installed
  "let g:Tex_CompileRule_dvi = 'latex -src-specials -interaction=nonstopmode $*'
  let g:Tex_CompileRule_pdf = 'pdflatex -synctex=1 -interaction=nonstopmode $*'

  " Get the correct servername, which should be the filename of the tex file,
  " without the extension.
  " Using the filename, without the extension, not in uppercase though, but
  " that's okay for a servername, it automatically get uppercased
  let theuniqueserv = expand("%:r")

  " Working!!!, when we run vim appropriately
  " TODO: does neovim work with --remote? If not, use nvr instead of (n)vim?
  "       see system-setup notes for nvr installation (neovim-remote)
  let g:Tex_ViewRuleComplete_pdf = 'zathura -x "vim --servername '.theuniqueserv.' --remote +\%{line} \%{input}" $*.pdf 2>/dev/null &'

  " Forward search
  " syntax for zathura: zathura --synctex-forward 193:1:paper.tex paper.pdf
  function! SyncTexForward()
          let execstr = 'silent! !zathura --synctex-forward '.line('.').':1:"'.expand('%').'" "'.expand("%:p:r").'".pdf'
          execute execstr
  endfunction
  nmap <leader>lf :call SyncTexForward()<CR>

  let g:Tex_IgnoredWarnings =
  \'Underfull'."\n".
  \'Overfull'."\n".
  \'specifier changed to'."\n".
  \'You have requested'."\n".
  \'Missing number, treated as zero.'."\n".
  \'There were undefined references'."\n".
  \'Latex Warning:'."\n".
  \'Citation %.%# undefined'
  let g:Tex_IgnoreLevel = 8


" ----- Keyboard Mappings {{{1

  " 'cjrh/vim-conda'
  map <leader>E :CondaChangeEnv<CR>

  " shortcuts to open config files, taken from ~/.config/shortcutrc
  nmap <leader>cbf :e ~/.config/bmfiles<CR>
  nmap <leader>cbd :e ~/.config/bmdirs<CR>
  nmap <leader>cfb :e ~/.bashrc<CR>
  nmap <leader>cfa :e ~/.config/aliasrc<CR>
  nmap <leader>cfz :e ~/.zshrc<CR>
  nmap <leader>cfv :e ~/.config/nvim/init.vim<CR>
  nmap <leader>cfr :e ~/.config/ranger/rc.conf<CR>
  nmap <leader>cfi :e ~/.config/i3/config<CR>
  nmap <leader>cfm :e ~/.config/mutt/muttrc<CR>
  nmap <leader>cfd :e ~/.Xdefaults<CR>
  nmap <leader>cfu :e ~/.config/newsboat/urls<CR>
  nmap <leader>cfn :e ~/.config/newsboat/config<CR>
  nmap <leader>cfmb :e ~/.config/ncmpcpp/bindings<CR>
  nmap <leader>cfmc :e ~/.config/ncmpcpp/config<CR>

  " Pydocstring
  nmap <leader>z <Plug>(pydocstring)
  nmap <leader>Z :PydocstringFormat<CR>
  let g:pydocstring_formatter = 'numpy'

  " ----- jmcantrell/vim-diffchanges  {{{2
  " show the changes made to the saved file
  nnoremap <leader>D :DiffChangesDiffToggle<CR>
  "show the patch of the current changes
  nnoremap <leader>S :DiffChangesPatchToggle<CR>

  " Syntax checking
  nnoremap <F7> :SyntasticCheck<CR>

  " Toggle undo tree (simnalamburt/vim-mundo)
  nnoremap <leader>u :MundoToggle<CR>

  " Open/close NERDTree tabs (Mirror only opens Tree in current tab)
  "nmap <leader>e :NERDTreeTabsToggle<CR>
  nmap <leader>e :NERDTreeMirrorToggle<CR>

  " Open/close tagbar
  nmap <leader>r :TagbarToggle<CR>

  " Toggle relative line numbers
  nmap <silent> <leader>n :call ToggleNumber()<CR>

  " diffput and diffget
  map <leader>dp :diffput <CR>
  map <leader>dg :diffget <CR>

  " Buffer navigation
  " Close the current buffer and move to the most recently used
  nmap <leader>dd :bd<CR>
"  " Buffer navigation
"  " open buffer list for selection
"  nnoremap <leader>b :ls<CR>:b<Space>
"  " Move to the next buffer
"  nmap <leader>n :bnext<CR>
"  " Move to the previous buffer
"  nmap <leader>h :bprev<CR>

  " CtrlP mappings
  nnoremap <leader>p :CtrlPBuffer<CR>
  nnoremap <leader>P :CtrlPMRU<CR>
  "nnoremap <leader>t :CtrlPTag<CR>
  nnoremap <leader>t :Tags<CR>

  " Toggle paste / nopaste mode
  set pastetoggle=<F2>

  " Update ctags
  "augroup keybinding
  "  au!
  "  autocmd FileType c,cpp,cuda         map <F8> :!/usr/bin/ctags -R --c++-kinds=+p --fields=+iaS --extra=+q .<CR>
  "  "autocmd FileType cuda               map <F8> :!/usr/bin/ctags -R --langmap=c++:+.cu --c++-kinds=+p --fields=+iaS --extra=+q .<CR>
  "augroup END

  " Switch btwn dark and light theme solarized
  "call togglebg#map("<F9>")

  " Enable folding f
  nnoremap <leader>f za
  " Code folding options
  nmap <leader>0f :set foldlevel=0<CR>
  nmap <leader>1f :set foldlevel=1<CR>
  nmap <leader>2f :set foldlevel=2<CR>
  nmap <leader>3f :set foldlevel=3<CR>
  nmap <leader>4f :set foldlevel=4<CR>
  nmap <leader>5f :set foldlevel=5<CR>
  nmap <leader>6f :set foldlevel=6<CR>
  nmap <leader>7f :set foldlevel=7<CR>
  nmap <leader>8f :set foldlevel=8<CR>
  nmap <leader>9f :set foldlevel=9<CR>

  " Force write readonly files using sudo
  command! Sw w !sudo tee %

  " Make these commonly mistyped commands still work
  command! WQ wq
  command! Wq wq
  command! Wqa wqa
  command! W w
  command! Q q
  command! Qa qa
  command! SW Sw

  " To clear hlsearch
  nmap <leader>/ :nohlsearch<CR>

  " run current script in python
  " (using asyncrun instead)
  "nmap <leader>o :!python %<CR>

  " Make navigating long, wrapped lines behave like normal lines
  noremap <silent> k gk
  noremap <silent> j gj
  noremap <silent> 0 g0
  noremap <silent> $ g$
  noremap <silent> ^ g^
  noremap <silent> _ g_

  " linediff
  vmap <leader>l :Linediff<CR>


" ----- Custom Functions {{{1

  " Load Session.vim when present (Obsession will remain active)
  " From tpope: https://github.com/tpope/vim-obsession/issues/17#issuecomment-229144719
  autocmd VimEnter * nested
        \ if !argc() && empty(v:this_session) && filereadable('Session.vim') && !&modified |
        \   source Session.vim |
        \ endif

  """ https://github.com/tpope/vim-fugitive/issues/132#issuecomment-649516204
  command! DiffHistory call s:view_git_history()

  function! s:view_git_history() abort
    Git difftool --name-only ! !^@
    call s:diff_current_quickfix_entry()
    " Bind <CR> for current quickfix window to properly set up diff split layout after selecting an item
    " There's probably a better way to map this without changing the window
    copen
    nnoremap <buffer> <CR> <CR><BAR>:call <sid>diff_current_quickfix_entry()<CR>
    wincmd p
  endfunction

  function s:diff_current_quickfix_entry() abort
    " Cleanup windows
    for window in getwininfo()
      if window.winnr !=? winnr() && bufname(window.bufnr) =~? '^fugitive:'
        exe 'bdelete' window.bufnr
      endif
    endfor
    cc
    call s:add_mappings()
    let qf = getqflist({'context': 0, 'idx': 0})
    if get(qf, 'idx') && type(get(qf, 'context')) == type({}) && type(get(qf.context, 'items')) == type([])
      let diff = get(qf.context.items[qf.idx - 1], 'diff', [])
      echom string(reverse(range(len(diff))))
      for i in reverse(range(len(diff)))
        exe (i ? 'leftabove' : 'rightbelow') 'vert diffsplit' fnameescape(diff[i].filename)
        call s:add_mappings()
      endfor
    endif
  endfunction

  function! s:add_mappings() abort
    nnoremap <buffer>]q :cnext <BAR> :call <sid>diff_current_quickfix_entry()<CR>
    nnoremap <buffer>[q :cprevious <BAR> :call <sid>diff_current_quickfix_entry()<CR>
    " Reset quickfix height. Sometimes it messes up after selecting another item
    11copen
    wincmd p
  endfunction

  " ----- Python Functions {{{2
  " Collection of Python functions used instead of vimscript

python3 << ENDPY

def CreateGithubLink():
    import vim
    current_word = vim.eval('expand("<cWORD>")')
    link = "https://github.com/"
    if current_word.startswith('brian2'):
      # Allow brian2#666 or brian2cuda#666 instead of brian-team/brian2...
      link += 'brian-team/'
    elif current_word.count('/') == 0:
      # Assume user=denisalevi if no user is given
      link += 'denisalevi/'
    if '#' in current_word:
      assert '@' not in current_word, "Can only have @ or #, not both"
      link += current_word.replace('#', '/issues/')
    elif '@' in current_word:
      repo, sha = current_word.split('@')
      # add full sha to url link
      link += current_word.replace('@', '/commit/')
      # truncate sha to length 7 for displayed link
      current_word = f'{repo}@{sha[:7]}'
    new_word = f"[{current_word}]({link})"
    # ciW: Delete current WORD and continue in insert mode
    #      NOTE: WORD is limited by spaces, word depends on iskeyword option
    vim.command(f"normal ciW{new_word}")


def set_brian_pythonpath():
    import os
    import subprocess
    import shlex
    import pathlib
    import vim

    git_root = subprocess.check_output(
        shlex.split(f"git rev-parse --show-toplevel"),
        encoding='UTF-8'
    ).rstrip()
    worktree_dir = '~/projects/brian2cuda/brian2cuda_repository/worktrees'
    pythonpath = ""
    if pathlib.PurePath(git_root).is_relative_to(worktree_dir):
        dirs = os.listdir(git_root)
        if 'brian2cuda' in dirs:
            b2c_dir = git_root
            brian2_dir = os.path.join(git_root, "frozen_repos", "brian2")
            if 'brian2' not in os.listdir(brian2_dir):
                print(f"WARNING {brian2_dir} is not initialized.")
                brian2_dir = None
        elif 'brian2' in dirs:
            brian2_dir = git_root
            b2c_dir = os.path.join(git_root, '..', '..')
            if 'brian2cuda' not in os.listdir(b2c_dir):
                b2c_dir = None

        pythonpath = ""
        if brian2_dir is not None or b2c_dir is not None:
            paths = []
            if brian2_dir is not None:
                paths.append(f"{brian2_dir}")
            if b2c_dir is not None:
                paths.append(f"{b2c_dir}")
            pythonpath = "PYTHONPATH=" + ':'.join(paths) + ":$PYTHONPATH"

    vim.command(f'let pythonpath = "{pythonpath}"')

def set_brian_pythonpath():
    import os
    import subprocess
    import shlex
    import pathlib
    import vim

    git_root = os.path.realpath(
        subprocess.check_output(
            shlex.split(f"git rev-parse --show-toplevel"),
            encoding='UTF-8'
        )
    ).rstrip()
    worktree_dir = os.path.realpath(
        os.path.expanduser(
            '~/projects/brian2cuda/brian2cuda_repository/worktrees'
        )
    )
    pythonpath = ""
    vim.command('if exists("g:pythonpath") | unlet g:pythonpath | endif')
    if pathlib.PurePath(git_root).is_relative_to(worktree_dir):
        print("B")
        dirs = os.listdir(git_root)
        if 'brian2cuda' in dirs:
            b2c_dir = git_root
            brian2_dir = os.path.join(git_root, "frozen_repos", "brian2")
            if 'brian2' not in os.listdir(brian2_dir):
                print(f"WARNING {brian2_dir} is not initialized.")
                brian2_dir = None
        elif 'brian2' in dirs:
            brian2_dir = git_root
            b2c_dir = os.path.join(git_root, '..', '..')
            if 'brian2cuda' not in os.listdir(b2c_dir):
                b2c_dir = None

        if brian2_dir is not None or b2c_dir is not None:
            paths = []
            if brian2_dir is not None:
                paths.append(f"{brian2_dir}")
            if b2c_dir is not None:
                paths.append(f"{b2c_dir}")
            pythonpath = "PYTHONPATH=" + ':'.join(paths) + ":$PYTHONPATH"
            print("C")

        vim.command(f'let g:pythonpath = "{pythonpath}"')

ENDPY

  " ----- Vimscript Functions {{{2

  "  Set PYTHONPATH when inside brian2cuda directory
  function! RunPythonAsync()
python3 << ENDPY
set_brian_pythonpath()
ENDPY

    " Detect if buffer is inside a Python module and execute it via module specification
    " to allow executing module files with relative imports
    "
    " Example:
    "   pwd -> /absolute/path/to/dir
    "   expand('%') -> relative/path/to/file.py
    "
    "   full path of buffer is then
    "   expand('%:p') -> /absolute/path/to/dir/relative/path/to/file.py
    "
    "   and we want to execute it via
    "     python -m relative.path.to.file
    "
    " Test if open buffer is inside a Python module
    " (has an __init__.py file in same directory; expand('%:h') -> /relative/path/to)
    if !empty(glob(expand('%:h').'/__init__.py'))
      " buffer is inside a module
      " now test if pwd is the first directory outside the module, i.e. pwd is not a
      " Python module (no __init__.py) and ./relative is one (has __init__.py)
      " Get the first folder in expand('%') by removing everything after the first /
      " g:module_dir = relative
      let g:module_dir = substitute(expand('%'), '\(.\{-}\)/.*', '\1', '')
      " Now test for the __init__.py files
      if empty(glob('__init__.py')) && !empty(glob(g:module_dir . '/__init__.py'))
        " pwd is not a module and realtive is a module
        " Now get the correct expression for python -m <g:module_path>
        " substitute all / with . in buffer path (without extension, :r)
        " relative/path/to/file.py -> relative.path.to.file
        let g:module_path = substitute(expand('%:r'), '/', '.', 'g')
      endif
    endif

    " By default, just execute buffer with python
    "   python relative/path/to/file.py
    let g:python_argument = "%"
    if exists("g:module_path")
      " Use module specification:
      "   python -m relative.path.to.file
      let g:python_argument = "-m " . g:module_path
    endif

    if exists("g:pythonpath")
      " This uses CPU threads 0-7 (P-CPUs on my system)
      execute "AsyncRun -raw -mode=term -pos=tmux taskset -c 0,1,2,3,4,5,6,7" . g:pythonpath . " python " . g:python_argument
    else
      execute "AsyncRun -raw -mode=term -pos=tmux taskset -c 0,1,2,3,4,5,6,7 python " . g:python_argument
    endif
  endfunction

  " Remember last curser position in file
  function RememberLastPosition()
    if &ft =~ 'gitcommit'
      return
    endif
    if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
  endfunction

  " Toggle between number and relativenumber
  function! ToggleNumber()
      if(&relativenumber == 1)
          set norelativenumber
          set number
      else
          set relativenumber
      endif
  endfunc

  " Different syntax highlighting within regions of a file
  " http://vim.wikia.com/wiki/Different_syntax_highlighting_within_regions_of_a_file
  " Important changes:
  " * Add keepend, otherwise nested C++/Jinja doesn't work!
  " * Add containedin=ALL, so also highlighted in C comments and strings.
  " * Remove the textSnipHl section (since want to include the delimiters
  "   for Jinja).
  "
  " ...and using syntax from:
  " http://www.vim.org/scripts/script.php?script_id=1856
""  function! TextEnableCodeSnip(filetype,start,end) abort
""    echo "DEBUG: calling TextEnableCodeSnip"
""    let ft=toupper(a:filetype)
""    let group='textGroup'.ft
""    if exists('b:current_syntax')
""      let s:current_syntax=b:current_syntax
""      " Remove current syntax definition, as some syntax files (e.g. cpp.vim)
""      " do nothing if b:current_syntax is defined.
""      unlet b:current_syntax
""    endif
""    execute 'syntax include @'.group.' syntax/'.a:filetype.'.vim'
""    try
""      execute 'syntax include @'.group.' after/syntax/'.a:filetype.'.vim'
""    catch
""    endtry
""    if exists('s:current_syntax')
""      let b:current_syntax=s:current_syntax
""    else
""      unlet b:current_syntax
""    endif
""    execute 'syntax region textSnip'.ft.'
""    \ start="'.a:start.'" end="'.a:end.'"
""    \ keepend
""    \ containedin=ALL
""    \ contains=@'.group
""  endfunction

  " Profile vim
  function! MyProf(file)
    execute "profile start " . a:file
    execute "profile func *"
    execute "profile file *"
  endfunc

  command! -nargs=1 Prof call MyProf(<f-args>)

  " Tex formatexpr for one line per sentence
  function! MyFormatExpr(start, end)
    silent execute a:start.','.a:end.'s/[.!?]\zs /\r/g'
  endfunction

" ----- Autocommands (indentation settings) {{{1
  " Indention stuff
  augroup indention
    au!
    autocmd FileType lua                set tabstop=4 shiftwidth=4 expandtab smarttab smartindent
    autocmd FileType matlab             set tabstop=4 shiftwidth=4 expandtab smarttab smartindent
    "PEP8 standards
    " vim-scripts/indenpython Plugin takes care of it
    autocmd FileType python             set colorcolumn=89 textwidth=88 
    autocmd FileType make               set tabstop=8 shiftwidth=8 noexpandtab list
    autocmd FileType man                set tabstop=8 shiftwidth=8 noexpandtab
    autocmd FileType c,cpp,cuda         set tabstop=4 shiftwidth=4 softtabstop=4 textwidth=79 expandtab nolist
    autocmd FileType tex                set tabstop=2 shiftwidth=2 wrap expandtab iskeyword+=: formatexpr=MyFormatExpr(v:lnum,v:lnum+v:count-1) linebreak nofoldenable "textwidth=79
    autocmd FileType tex,markdown,gitcommit,vimwiki,mail  setlocal spell spelllang=en_us
    "autocmd FileType plaintex,tex,latex syntax spell toplevel
    "autocmd FileType tex                set makeprg=pdflatex\ \"%\"&&evince\ \"%<.pdf\"
    autocmd FileType vimwiki            set ts=2 sw=2 tw=78 wrap lbr et
    autocmd FileType vim,tmux           set ts=2 sw=2 expandtab
    autocmd FileType mail               set tw=72
    autocmd FileType gitcommit          set tw=72 sw=2 tabstop=2 et
    autocmd FileType sh                 set tw=79 ts=4 softtabstop=4 shiftwidth=4 expandtab
  augroup misc
    au!
    autocmd BufNewFile,BufRead wscript* set filetype=python
    "autocmd FileType notmuch*           set foldmethod=manual
    autocmd BufReadPost *               call RememberLastPosition()
    autocmd BufEnter *                  let &titlestring = "vim(" . expand("%:t") . ")" " set window title
  augroup jinja
    " Jinja template highlighting
    " Assuming files inside a folder called 'templates' are Jinja templates.
    " Default delimiters are {{ }}, {% %}, and {# #}, per:
    " http://jinja.pocoo.org/docs/templates/
    au!
    "au BufNewFile,BufRead */templates/* call TextEnableCodeSnip('jinja', '{{', '}}')
""    au FileType jinja call TextEnableCodeSnip('jinja', '{{', '}}')
""    au FileType jinja call TextEnableCodeSnip('jinja', '{%', '%}')
""    au FileType jinja call TextEnableCodeSnip('jinja', '{#', '#}')
""    au FileType jinja.* :echo "DEBUG: detected jinja.* for " . expand("<amatch>")
""    au FileType *.jinja.* :echo "DEBUG: detected *.jinja.* for " . expand("<amatch>")
""    au FileType jinja :echo "DEBUG: detected jinja for " . expand("<amatch>")
""    au FileType *.jinja :echo "DEBUG: detected *.jinja for " . expand("<amatch>")
"    au FileType jinja :echo "DEBUG: detected jinja"
"    au FileType cuda :echo "DEBUG: detected cuda"
"    au FileType jinja.cuda :echo "DEBUG: detected jinja.cuda"
"    au FileType cuda.jinja :echo "DEBUG: detected cuda.jinja"
  augroup END

" TODO: YouCompleteMe {{{1
"TODO
"Ensure autocomplete window goes away when done with it
"let g:ycm_autoclose_preview_window_after_completion=1
" For YouCompleteMe to find the correct python interpreter
"let g:ycm_path_to_python_interpreter='~/anaconda2/bin/python'

"Shortcut for GoTo definition
"map <leader>g  :YcmCompleter GoToDefinitionElseDeclaration<CR>

"TODO
""Python with VIRTUALENV support: sets up system path for YCM and goto
"py << EOF
"import os
"import sys
"if 'VIRTUAL_ENV' in os.environ:
"  project_base_dir = os.environ['VIRTUAL_ENV']
"  activate_this = os.path.join(project_base_dir, 'bin/activate_this.py')
"  execfile(activate_this, dict(__file__=activate_this))
"EOF

" ----- Unused snippets {{{1
  " mark lines with more then 80 chars at 81 chars in magenta
  "highlight ColorColumn ctermbg=magenta
  "call matchadd('ColorColumn', '\%81v', 100)
  " create a colorcolumn at char 81
  "set colorcolumn=81

" vim:foldmethod=marker
